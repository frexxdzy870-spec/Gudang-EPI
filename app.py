import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. CSS MONOCHROME FIX (Sesuai Request: Hitam Putih & Tipis)
st.set_page_config(page_title="Gudang Sahaja", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, label, [data-testid="stWidgetLabel"] {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    /* Input & Password Box: Border 1px Hitam (Gak Tebal) */
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
        width: 100% !important;
    }
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzBpJCmQ2ErCu4TsDQ3BUujKOwCvdHxWmU8ZOqhXAu-5_1nYnQU89QxmY0Ckr5UY4-K-A/exec"

# Ambil data dari GitHub untuk Logo
LOGO_URL = "https://raw.githubusercontent.com/username/repo/main/logo.png"

def fetch_data():
    try:
        # Pake timeout lebih lama dikit biar gak gampang ilang fiturnya
        res = requests.get(f"{URL_WEB_APP}?t={datetime.now().timestamp()}", timeout=15)
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
        st.image(LOGO_URL, width=150) if "raw.githubusercontent" in LOGO_URL else st.title("☕")
        role = st.selectbox("Akses:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
        pw = st.text_input("Password:", type="password")
        if st.button("MASUK"):
            if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
                st.session_state.update({'logged_in': True, 'role': role})
                st.rerun()
            else: st.error("Salah password!")
else:
    # Header Aplikasi
    st.markdown(f"### {st.session_state.role} | GUDANG SAHAJA")
    
    # Ambil data (Jangan biarkan error ngumpetin menu!)
    df_stok = fetch_data()
    
    # --- LOGIKA MENU ---
    if st.session_state.role == "Owner":
        tab_list = ["📊 DATA", "➕ MASUK", "➖ KELUAR", "🚪 LOGOUT"]
    else:
        tab_list = ["➕ MASUK", "➖ KELUAR", "📱 WA", "🚪 LOGOUT"]
    
    menu = st.tabs(tab_list)

    # Rincian Logic tiap Tab (SAMA UNTUK OWNER & STAFF)
    # Kita pake index biar fleksibel
    
    # --- TAB MASUK (Sama buat semua) ---
    with menu[tab_list.index("➕ MASUK")]:
        with st.form("form_in", clear_on_submit=True):
            # Fitur Update Stok barang lama (Tetep muncul meski data delay)
            opsi = ["Barang Baru"]
            if not df_stok.empty: opsi.insert(0, "Update Stok Lama")
            
            mode = st.radio("Metode:", opsi, horizontal=True)
            
            if mode == "Update Stok Lama" and not df_stok.empty:
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
                st.success("Tersimpan!")

    # --- TAB KELUAR (Sama buat semua) ---
    with menu[tab_list.index("➖ KELUAR")]:
        if not df_stok.empty:
            with st.form("form_out", clear_on_submit=True):
                n_o = st.selectbox("Cari Barang:", df_stok['Barang'].unique())
                m_o = df_stok[df_stok['Barang'] == n_o].iloc[0]
                st.info(f"Sisa stok saat ini: {m_o['Sisa Stok']} {m_o['Satuan']}")
                j_o = st.number_input("Jumlah Keluar:", min_value=1)
                if st.form_submit_button("KONFIRMASI KELUAR"):
                    p = {"id": str(int(datetime.now().timestamp())+1), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state.role, "jenis": "KELUAR", "kategori": m_o['Kategori'], "barang": n_o, "jumlah": int(j_o), "satuan": m_o['Satuan']}
                    requests.post(URL_WEB_APP, json=p)
                    st.session_state.report += f"• {n_o}: -{j_o} {m_o['Satuan']}\n"
                    st.success("Berhasil!")
        else:
            st.warning("Data stok belum termuat. Klik tombol Refresh di bawah.")
            if st.button("🔄 REFRESH DATA SEKARANG"): st.rerun()

    # --- KHUSUS OWNER: LIHAT DATA ---
    if "📊 DATA" in tab_list:
        with menu[tab_list.index("📊 DATA")]:
            if not df_stok.empty:
                st.dataframe(df_stok, use_container_width=True, hide_index=True)
            else:
                st.error("Koneksi Google Sheets terputus. Pastikan Apps Script aktif.")
            if st.button("SEGARKAN TABEL"): st.rerun()

    # --- TAB WA (Staff Only) ---
    if "📱 WA" in tab_list:
        with menu[tab_list.index("📱 WA")]:
            if st.session_state.report:
                msg = f"*LAPORAN GUDANG*\nUser: {st.session_state.role}\n---\n{st.session_state.report}"
                st.text_area("Draft:", msg, height=150)
                url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#000000;color:white;padding:15px;border-radius:4px;text-align:center;font-weight:bold;">🚀 KIRIM KE WA</div></a>', unsafe_allow_html=True)
            else: st.info("Belum ada transaksi.")

    # --- TAB LOGOUT ---
    with menu[tab_list.index("🚪 LOGOUT")]:
        if st.button("KELUAR DARI SISTEM"):
            st.session_state.logged_in = False
            st.rerun()
