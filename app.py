import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. CSS DARK MODE TOTAL - BALIK KE SETELAN AWAL
st.set_page_config(page_title="Gudang Sahaja", layout="centered")

st.markdown("""
    <style>
    /* Background Hitam Pekat */
    .stApp { background-color: #0E1117 !important; }
    
    /* Semua Teks & Label Putih */
    h1, h2, h3, p, span, label, [data-testid="stWidgetLabel"] {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Input & Select Box: Teks Putih, Background Gelap */
    input, [data-baseweb="select"] > div, [data-baseweb="input"] > div, textarea {
        background-color: #1A1C23 !important;
        color: #FFFFFF !important;
        border: 1px solid #3E424B !important;
        border-radius: 4px !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Dropdown Text Fix */
    div[data-baseweb="select"] *, div[role="listbox"] * {
        color: #FFFFFF !important;
    }

    /* Tombol: Putih, Tulisan Hitam (Biar Kontras) */
    .stButton>button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: none !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 3.5em !important;
        border-radius: 4px !important;
    }
    .stButton>button p, .stButton>button span { color: #000000 !important; }

    /* Tab Menu */
    button[data-baseweb="tab"] { color: #888888 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { 
        color: #FFFFFF !important; 
        border-bottom-color: #FFFFFF !important;
    }

    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# URL LOGO & API
LOGO_URL = "https://raw.githubusercontent.com/username/repo/main/logo.png"
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzBpJCmQ2ErCu4TsDQ3BUujKOwCvdHxWmU8ZOqhXAu-5_1nYnQU89QxmY0Ckr5UY4-K-A/exec"

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

# --- HALAMAN LOGIN ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # LOGO BALIK LAGI DI ATAS
        try: st.image(LOGO_URL, width=150)
        except: st.markdown("<h1 style='text-align: center;'>☕</h1>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align: center;'>GUDANG SAHAJA</h3>", unsafe_allow_html=True)
        role = st.selectbox("Role:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
        pw = st.text_input("Password:", type="password")
        if st.button("MASUK SISTEM"):
            if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
                st.session_state.update({'logged_in': True, 'role': role})
                st.rerun()
            else: st.error("Salah password!")

# --- DASHBOARD ---
else:
    st.markdown(f"### 📋 {st.session_state.role}")
    df_stok = fetch_data()
    
    # Menu Berdasarkan Role
    if st.session_state.role == "Owner":
        tabs = st.tabs(["📊 DATA", "➕ MASUK", "➖ KELUAR", "🚪 LOGOUT"])
    else:
        tabs = st.tabs(["➕ MASUK", "➖ KELUAR", "📱 WA", "🚪 LOGOUT"])

    for i, tab in enumerate(tabs):
        labels = ["📊 DATA", "➕ MASUK", "➖ KELUAR", "📱 WA", "🚪 LOGOUT"] if st.session_state.role == "Owner" else ["➕ MASUK", "➖ KELUAR", "📱 WA", "🚪 LOGOUT"]
        t_name = labels[i]
        
        with tab:
            if "DATA" in t_name:
                if not df_stok.empty: st.dataframe(df_stok, use_container_width=True, hide_index=True)
                else: st.info("Memuat data... Klik refresh jika lama.")
                if st.button("REFRESH TABEL"): st.rerun()

            elif "MASUK" in t_name:
                with st.form("in_form", clear_on_submit=True):
                    # FITUR UPDATE STOK: Gak bakal ilang, kalau data kosong cuma muncul opsi 'Barang Baru'
                    has_data = not df_stok.empty and "Barang" in df_stok.columns
                    mode = st.radio("Metode:", ["Update Stok Lama", "Input Barang Baru"], horizontal=True) if has_data else "Input Barang Baru"
                    
                    if "Update" in mode and has_data:
                        nama = st.selectbox("Pilih Barang:", df_stok['Barang'].unique())
                        row = df_stok[df_stok['Barang'] == nama].iloc[0]
                        kat, sat = row['Kategori'], row['Satuan']
                    else:
                        nama = st.text_input("Nama Barang (Gunakan Huruf Kapital):").upper()
                        kat = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                        sat = st.selectbox("Satuan:", ["pcs", "kg", "gram", "box"])
                    
                    jml = st.number_input("Jumlah Masuk:", min_value=1)
                    if st.form_submit_button("SIMPAN"):
                        p = {"id": str(int(datetime.now().timestamp())), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state.role, "jenis": "MASUK", "kategori": kat, "barang": nama, "jumlah": int(jml), "satuan": sat}
                        requests.post(URL_WEB_APP, json=p)
                        st.session_state.report += f"• {nama}: +{jml} {sat}\n"
                        st.success("Berhasil disimpan!")

            elif "KELUAR" in t_name:
                # FITUR KELUAR: Tetap ada, kalau data kosong disuruh refresh
                if not df_stok.empty and "Barang" in df_stok.columns:
                    with st.form("out_form", clear_on_submit=True):
                        n_o = st.selectbox("Cari Barang:", df_stok['Barang'].unique())
                        m_o = df_stok[df_stok['Barang'] == n_o].iloc[0]
                        st.info(f"Stok saat ini: {m_o['Sisa Stok']} {m_o['Satuan']}")
                        j_o = st.number_input("Jumlah Keluar:", min_value=1)
                        if st.form_submit_button("KONFIRMASI KELUAR"):
                            p = {"id": str(int(datetime.now().timestamp())+1), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state.role, "jenis": "KELUAR", "kategori": m_o['Kategori'], "barang": n_o, "jumlah": int(j_o), "satuan": m_o['Satuan']}
                            requests.post(URL_WEB_APP, json=p)
                            st.session_state.report += f"• {n_o}: -{j_o} {m_o['Satuan']}\n"
                            st.success("Data keluar tersimpan!")
                else:
                    st.warning("Data stok belum sinkron. Klik tombol Refresh di bawah.")
                    if st.button("🔄 AMBIL DATA ULANG"): st.rerun()

            elif "WA" in t_name:
                if st.session_state.report:
                    msg = f"*LAPORAN GUDANG*\nUser: {st.session_state.role}\n---\n{st.session_state.report}"
                    st.text_area("Draft WA:", msg, height=150)
                    url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                    st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#FFFFFF;color:#000000;padding:15px;border-radius:4px;text-align:center;font-weight:bold;">🚀 KIRIM KE WHATSAPP</div></a>', unsafe_allow_html=True)
                else: st.info("Belum ada laporan transaksi.")

            elif "LOGOUT" in t_name:
                if st.button("KELUAR DARI AKUN"):
                    st.session_state.logged_in = False
                    st.rerun()
