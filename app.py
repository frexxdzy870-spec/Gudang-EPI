import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. CSS MONOCHROME FIX (TEKS TOMBOL PUTIH, BORDER TIPIS)
st.set_page_config(page_title="Gudang Sahaja", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    
    /* Semua Teks Luar Jadi Hitam */
    h1, h2, h3, p, span, label, [data-testid="stWidgetLabel"] {
        color: #000000 !important;
        font-weight: 700 !important;
    }

    /* Input & Password Box: Border 1px Hitam Tipis Simetris */
    input, [data-baseweb="select"] > div, [data-baseweb="input"] > div, textarea {
        background-color: #FAFAFA !important;
        color: #000000 !important;
        border: 1px solid #000000 !important; 
        border-radius: 4px !important;
    }

    /* TOMBOL HITAM - TEKS WAJIB PUTIH */
    .stButton>button {
        background-color: #000000 !important;
        color: #FFFFFF !important; /* Paksa teks tombol jadi putih */
        border-radius: 4px !important;
        height: 3em !important;
        width: 100% !important;
        border: none !important;
    }
    
    /* Hover tombol biar ada efek dikit */
    .stButton>button:hover {
        background-color: #333333 !important;
        color: #FFFFFF !important;
    }

    /* Fix Teks Dropdown agar tidak hilang */
    div[data-baseweb="select"] * {
        color: #000000 !important;
    }

    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# URL WEB APP GOOGLE SHEETS
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzBpJCmQ2ErCu4TsDQ3BUujKOwCvdHxWmU8ZOqhXAu-5_1nYnQU89QxmY0Ckr5UY4-K-A/exec"

# CARA PANGGIL LOGO GITHUB (WAJIB PAKE raw.githubusercontent.com)
# Contoh: https://raw.githubusercontent.com/UsernameLu/NamaRepo/main/namafile.png
LOGO_URL = "https://raw.githubusercontent.com/frexxdify/repo-anda/main/logo.png"

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
        # Coba tampilin logo, kalau gagal munculin emoji biar gak berantakan
        if LOGO_URL.startswith("http"):
            st.image(LOGO_URL, width=150)
        else:
            st.markdown("<h1 style='text-align: center;'>📦</h1>", unsafe_allow_html=True)
            
        st.markdown("<h3 style='text-align: center;'>LOGIN</h3>", unsafe_allow_html=True)
        role = st.selectbox("Role:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
        pw = st.text_input("Password:", type="password")
        if st.button("MASUK SISTEM"):
            if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
                st.session_state.update({'logged_in': True, 'role': role})
                st.rerun()
            else: st.error("Password Salah!")
else:
    st.markdown(f"### {st.session_state.role} | GUDANG SAHAJA")
    df_stok = fetch_data()

    # TABS PERMANEN (Gak bakal ngilang)
    if st.session_state.role == "Owner":
        tabs = st.tabs(["📊 DATA", "➕ MASUK", "➖ KELUAR", "🚪 LOGOUT"])
    else:
        tabs = st.tabs(["➕ MASUK", "➖ KELUAR", "📱 LAPORAN", "🚪 LOGOUT"])

    # --- LOGIC DALAM TAB ---
    # Tab Masuk
    t_masuk = tabs[1] if st.session_state.role == "Owner" else tabs[0]
    with t_masuk:
        with st.form("form_in", clear_on_submit=True):
            # Update Stok vs Barang Baru
            mode = "Barang Baru"
            if not df_stok.empty:
                mode = st.radio("Metode:", ["Update Stok", "Barang Baru"], horizontal=True)

            if mode == "Update Stok" and not df_stok.empty:
                nama = st.selectbox("Pilih Barang:", df_stok['Barang'].unique())
                row = df_stok[df_stok['Barang'] == nama].iloc[0]
                kat, sat = row['Kategori'], row['Satuan']
            else:
                nama = st.text_input("Nama Barang:").upper()
                kat = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                sat = st.selectbox("Satuan:", ["pcs", "kg", "gram", "box"])
            
            jml = st.number_input("Jumlah:", min_value=1)
            if st.form_submit_button("SIMPAN DATA"):
                p = {"id": str(int(datetime.now().timestamp())), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state.role, "jenis": "MASUK", "kategori": kat, "barang": nama, "jumlah": int(jml), "satuan": sat}
                requests.post(URL_WEB_APP, json=p)
                st.session_state.report += f"• {nama}: +{jml} {sat}\n"
                st.success("Tersimpan!")

    # Tab Keluar
    t_keluar = tabs[2] if st.session_state.role == "Owner" else tabs[1]
    with t_keluar:
        if not df_stok.empty:
            with st.form("form_out", clear_on_submit=True):
                n_o = st.selectbox("Barang:", df_stok['Barang'].unique())
                m_o = df_stok[df_stok['Barang'] == n_o].iloc[0]
                st.write(f"Sisa: {m_o['Sisa Stok']} {m_o['Satuan']}")
                j_o = st.number_input("Jumlah Keluar:", min_value=1)
                if st.form_submit_button("INPUT KELUAR"):
                    p = {"id": str(int(datetime.now().timestamp())+1), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state.role, "jenis": "KELUAR", "kategori": m_o['Kategori'], "barang": n_o, "jumlah": int(j_o), "satuan": m_o['Satuan']}
                    requests.post(URL_WEB_APP, json=p)
                    st.session_state.report += f"• {n_o}: -{j_o} {m_o['Satuan']}\n"
                    st.success("Tercatat!")
        else:
            st.warning("Data stok kosong. Klik refresh.")
            if st.button("🔄 REFRESH"): st.rerun()

    # Tab Data (Owner)
    if st.session_state.role == "Owner":
        with tabs[0]:
            if not df_stok.empty: st.dataframe(df_stok, use_container_width=True, hide_index=True)
            else: st.info("Memuat data...")
            if st.button("SEGARKAN"): st.rerun()

    # Tab WA (Staff)
    if st.session_state.role != "Owner":
        with tabs[2]:
            if st.session_state.report:
                msg = f"*LAPORAN GUDANG*\nUser: {st.session_state.role}\n---\n{st.session_state.report}"
                st.text_area("Draft:", msg, height=150)
                url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#000000;color:white;padding:15px;border-radius:4px;text-align:center;font-weight:bold;">🚀 KIRIM KE WA</div></a>', unsafe_allow_html=True)
            else: st.info("Belum ada laporan.")

    # Tab Logout
    with tabs[3]:
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
