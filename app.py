import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. FIX CSS - PAKSA TEKS HITAM PEKAT
st.set_page_config(page_title="Gudang Sahaja", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    /* Semua teks label & konten wajib HITAM */
    html, body, [data-testid="stWidgetLabel"], .stText, p, h1, h2, h3, span, label, .stMarkdown {
        color: #000000 !important;
        font-weight: 600 !important;
    }
    /* Input Box: Background abu terang, teks HITAM pekat */
    input, div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, textarea {
        background-color: #F0F2F6 !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
    }
    /* Dropdown list biar gak putih di atas putih */
    div[data-baseweb="popover"] div {
        color: #000000 !important;
    }
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzBpJCmQ2ErCu4TsDQ3BUujKOwCvdHxWmU8ZOqhXAu-5_1nYnQU89QxmY0Ckr5UY4-K-A/exec"

# --- FUNGSI AMBIL DATA (DENGAN PROTEKSI) ---
def fetch_stok_safe():
    try:
        # Timeout 5 detik biar gak nunggu kelamaan sampe error merah
        res = requests.get(URL_WEB_APP, timeout=5)
        data = res.json()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            df.columns = df.columns.str.strip() # Hapus spasi gaib di kolom
            return df
    except:
        pass
    return pd.DataFrame()

# --- LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'temp_report': ""})

if not st.session_state['logged_in']:
    st.title("☕ Login Gudang")
    role = st.selectbox("Akses:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
    pw = st.text_input("Sandi:", type="password")
    if st.button("Masuk"):
        if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
            st.session_state.update({'logged_in': True, 'role': role})
            st.rerun()
        else: st.error("Sandi salah!")
else:
    # Ambil data tapi jangan meledak kalo gagal
    df_stok = fetch_stok_safe()
    
    # Cek apakah kolom di sheet bener
    is_ready = not df_stok.empty and all(c in df_stok.columns for c in ["Barang", "Sisa Stok"])

    if st.session_state['role'] == "Owner":
        st.subheader("Pantau Stok (Owner)")
        if is_ready:
            st.dataframe(df_stok, use_container_width=True, hide_index=True)
        else:
            st.warning("Database lemot atau kolom Sheet salah. Coba refresh.")
        if st.button("Logout"):
            st.session_state.logged_in = False; st.rerun()

    else:
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Masuk", "➖ Keluar", "📱 WA", "🚪 Keluar"])
        
        with tab1:
            with st.form("in", clear_on_submit=True):
                # Kalo data sheet gak kekirim, paksa input manual barang baru
                if is_ready:
                    mode = st.radio("Metode:", ["Update Stok", "Barang Baru"], horizontal=True)
                else:
                    mode = "Barang Baru"
                    st.info("Mode Barang Baru Aktif (Sheet sedang sinkronisasi)")

                if mode == "Update Stok":
                    nama = st.selectbox("Pilih Barang:", df_stok['Barang'].unique())
                    row = df_stok[df_stok['Barang'] == nama].iloc[0]
                    kat, sat = row.get('Kategori', 'BAR'), row.get('Satuan', 'pcs')
                else:
                    nama = st.text_input("Nama Barang:").upper()
                    kat = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                    sat = st.selectbox("Satuan:", ["pcs", "kg", "gram", "box"])
                
                jml = st.number_input("Jumlah:", min_value=1)
                if st.form_submit_button("SIMPAN KE CLOUD"):
                    if nama:
                        p = {"id": str(int(datetime.now().timestamp())), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state['role'], "jenis": "MASUK", "kategori": kat, "barang": nama, "jumlah": int(jml), "satuan": sat}
                        try:
                            r = requests.post(URL_WEB_APP, json=p, timeout=10)
                            if "Success" in r.text:
                                st.success(f"Berhasil! {nama} ditambahkan.")
                                st.session_state['temp_report'] += f"• {nama}: +{jml} {sat}\n"
                            else: st.error("Gagal simpan.")
                        except: st.error("Koneksi Google bermasalah.")

        with tab2:
            if is_ready:
                with st.form("out", clear_on_submit=True):
                    n_o = st.selectbox("Barang Keluar:", df_stok['Barang'].unique())
                    m_o = df_stok[df_stok['Barang'] == n_o].iloc[0]
                    j_o = st.number_input("Jumlah:", min_value=1, max_value=int(m_o['Sisa Stok']))
                    if st.form_submit_button("CATAT KELUAR"):
                        p = {"id": str(int(datetime.now().timestamp())+1), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state['role'], "jenis": "KELUAR", "kategori": m_o['Kategori'], "barang": n_o, "jumlah": int(j_o), "satuan": m_o['Satuan']}
                        try:
                            r = requests.post(URL_WEB_APP, json=p, timeout=10)
                            st.success("Tercatat!"); st.session_state['temp_report'] += f"• {n_o}: -{j_o} {m_o['Satuan']}\n"
                        except: st.error("Gagal.")
            else: st.warning("Data stok belum termuat.")

        with tab3:
            if st.session_state['temp_report']:
                msg = f"*LAPORAN GUDANG*\nUser: {st.session_state['role']}\n---\n{st.session_state['temp_report']}"
                st.text_area("Pratinjau:", msg, height=150)
                url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:15px;border-radius:10px;text-align:center;font-weight:bold;">🚀 KIRIM LAPORAN KE WA</div></a>', unsafe_allow_html=True)
            else: st.info("Belum ada data masuk/keluar.")

        with tab4:
            if st.button("Logout Sekarang"):
                st.session_state.logged_in = False; st.rerun()
