import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. CSS MONOCHROME (HITAM PUTIH, BORDER TIPIS 1PX)
st.set_page_config(page_title="Gudang Sahaja", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, label, [data-testid="stWidgetLabel"] {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    /* Input Box & Password: Border 1px Hitam Tipis Simetris */
    input, [data-baseweb="select"] > div, [data-baseweb="input"] > div, textarea {
        background-color: #FAFAFA !important;
        color: #000000 !important;
        border: 1px solid #000000 !important; 
        border-radius: 4px !important;
    }
    /* Tombol Hitam */
    .stButton>button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border-radius: 4px !important;
        height: 3em !important;
    }
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzBpJCmQ2ErCu4TsDQ3BUujKOwCvdHxWmU8ZOqhXAu-5_1nYnQU89QxmY0Ckr5UY4-K-A/exec"
# GANTI LINK DI BAWAH DENGAN LINK RAW GITHUB LU
LOGO_URL = "https://raw.githubusercontent.com/MuhammadWidyanFerdiansyah/repo/main/logo.png"

def fetch_data():
    try:
        res = requests.get(f"{URL_WEB_APP}?t={datetime.now().timestamp()}", timeout=10)
        data = res.json()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            df.columns = df.columns.str.strip()
            return df
    except: pass
    return pd.DataFrame()

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'report': ""})

if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try: st.image(LOGO_URL, width=150)
        except: st.title("📦")
        role = st.selectbox("Role:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
        pw = st.text_input("Password:", type="password")
        if st.button("MASUK"):
            if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
                st.session_state.update({'logged_in': True, 'role': role})
                st.rerun()
            else: st.error("Password Salah!")
else:
    # Header Tetap
    st.markdown(f"### {st.session_state.role} | GUDANG SAHAJA")
    
    # Ambil data dari Google Sheets
    df_stok = fetch_data()

    # --- TABS: TIDAK AKAN PERNAH HILANG ---
    if st.session_state.role == "Owner":
        tabs = st.tabs(["📊 DATA", "➕ MASUK", "➖ KELUAR", "🚪 LOGOUT"])
    else:
        tabs = st.tabs(["➕ MASUK", "➖ KELUAR", "📱 LAPORAN", "🚪 LOGOUT"])

    # --- TAB DATA (OWNER) ---
    if st.session_state.role == "Owner":
        with tabs[0]:
            if not df_stok.empty:
                st.dataframe(df_stok, use_container_width=True, hide_index=True)
            else:
                st.warning("Data belum ditarik. Klik Refresh.")
            if st.button("REFRESH TABEL"): st.rerun()

    # --- TAB MASUK (STAFF & OWNER) ---
    t_masuk = tabs[1] if st.session_state.role == "Owner" else tabs[0]
    with t_masuk:
        with st.form("form_masuk", clear_on_submit=True):
            # Logika: Kalau data kosong, paksa input manual. Kalau ada, kasih pilihan.
            if not df_stok.empty:
                mode = st.radio("Metode:", ["Update Stok", "Barang Baru"], horizontal=True)
            else:
                mode = "Barang Baru"
                st.info("Mode Barang Baru (Data sheet sedang loading...)")

            if mode == "Update Stok" and not df_stok.empty:
                nama = st.selectbox("Pilih Barang:", df_stok['Barang'].unique())
                row = df_stok[df_stok['Barang'] == nama].iloc[0]
                kat, sat = row['Kategori'], row['Satuan']
            else:
                nama = st.text_input("Nama Barang:").upper()
                kat = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                sat = st.selectbox("Satuan:", ["pcs", "kg", "gram", "box"])
            
            jml = st.number_input("Jumlah:", min_value=1)
            if st.form_submit_button("SIMPAN"):
                p = {"id": str(int(datetime.now().timestamp())), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state.role, "jenis": "MASUK", "kategori": kat, "barang": nama, "jumlah": int(jml), "satuan": sat}
                requests.post(URL_WEB_APP, json=p)
                st.session_state.report += f"• {nama}: +{jml} {sat}\n"
                st.success("Tersimpan!"); st.rerun()

    # --- TAB KELUAR (STAFF & OWNER) ---
    t_keluar = tabs[2] if st.session_state.role == "Owner" else tabs[1]
    with t_keluar:
        if not df_stok.empty:
            with st.form("form_keluar", clear_on_submit=True):
                n_o = st.selectbox("Barang Keluar:", df_stok['Barang'].unique())
                m_o = df_stok[df_stok['Barang'] == n_o].iloc[0]
                st.write(f"Stok: {m_o['Sisa Stok']} {m_o['Satuan']}")
                j_o = st.number_input("Jumlah Keluar:", min_value=1)
                if st.form_submit_button("INPUT KELUAR"):
                    p = {"id": str(int(datetime.now().timestamp())+1), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state.role, "jenis": "KELUAR", "kategori": m_o['Kategori'], "barang": n_o, "jumlah": int(j_o), "satuan": m_o['Satuan']}
                    requests.post(URL_WEB_APP, json=p)
                    st.session_state.report += f"• {n_o}: -{j_o} {m_o['Satuan']}\n"
                    st.success("Tercatat!"); st.rerun()
        else:
            st.warning("Data stok belum termuat.")
            if st.button("MUAT ULANG DATA"): st.rerun()

    # --- TAB WA (STAFF) ---
    if st.session_state.role != "Owner":
        with tabs[2]:
            if st.session_state.report:
                msg = f"*LAPORAN GUDANG*\nUser: {st.session_state.role}\n---\n{st.session_state.report}"
                st.text_area("Draft:", msg, height=150)
                url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#000000;color:white;padding:15px;border-radius:4px;text-align:center;font-weight:bold;">KIRIM WA</div></a>', unsafe_allow_html=True)
                if st.button("RESET"): st.session_state.report = ""; st.rerun()
            else: st.info("Belum ada input.")

    # --- TAB LOGOUT ---
    with tabs[3]:
        if st.button("KELUAR"):
            st.session_state.logged_in = False
            st.rerun()
