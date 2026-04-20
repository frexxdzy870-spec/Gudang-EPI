import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. CSS MONOCHROME - FIX KONTRAS INPUT
st.set_page_config(page_title="Gudang Sahaja", layout="centered")

st.markdown("""
    <style>
    /* Background Utama Putih */
    .stApp { background-color: #FFFFFF !important; }
    
    /* Judul & Label Teks Hitam */
    h1, h2, h3, p, span, label, [data-testid="stWidgetLabel"] {
        color: #000000 !important;
        font-weight: 800 !important;
    }

    /* KOTAK INPUT (NAMA, JUMLAH, PASSWORD) */
    /* Gue bikin background PUTIH biar teks HITAM-nya kelihatan jelas pas diketik */
    input, textarea, [data-baseweb="input"] > div {
        background-color: #FFFFFF !important; 
        color: #000000 !important;
        border: 1px solid #000000 !important; 
        border-radius: 4px !important;
        -webkit-text-fill-color: #000000 !important; /* Paksa teks input tetep hitam */
    }

    /* DROPDOWN (SELECTBOX) */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid #000000 !important;
    }
    
    /* Teks di dalem Dropdown & List Opsi */
    div[data-baseweb="select"] *, div[role="listbox"] * {
        color: #000000 !important;
    }

    /* TOMBOL HITAM - TEKS PUTIH (Sudah di-brute force) */
    .stButton>button {
        background-color: #000000 !important;
        border: none !important;
        border-radius: 4px !important;
        height: 3.5em !important;
        width: 100% !important;
    }
    .stButton>button p, .stButton>button span, .stButton>button div {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }

    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzBpJCmQ2ErCu4TsDQ3BUujKOwCvdHxWmU8ZOqhXAu-5_1nYnQU89QxmY0Ckr5UY4-K-A/exec"
LOGO_URL = "https://raw.githubusercontent.com/username/repo/main/logo.png"

def fetch_data_silent():
    try:
        res = requests.get(f"{URL_WEB_APP}?t={datetime.now().timestamp()}", timeout=10)
        data = res.json()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            df.columns = df.columns.str.strip()
            return df
    except: return pd.DataFrame()

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'report': ""})

# --- LOGIN ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center;'>📦</h2>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>LOGIN GUDANG</h3>", unsafe_allow_html=True)
        role = st.selectbox("Akses:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
        pw = st.text_input("Password:", type="password")
        if st.button("MASUK SEKARANG"):
            if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
                st.session_state.update({'logged_in': True, 'role': role})
                st.rerun()
            else: st.error("Sandi Salah!")

# --- HALAMAN UTAMA ---
else:
    st.markdown(f"### {st.session_state.role}")
    df_stok = fetch_data_silent()
    
    # TABS
    if st.session_state.role == "Owner":
        tabs = st.tabs(["📊 DATA", "➕ MASUK", "➖ KELUAR", "🚪 LOGOUT"])
    else:
        tabs = st.tabs(["➕ MASUK", "➖ KELUAR", "📱 WA", "🚪 LOGOUT"])

    for i, tab in enumerate(tabs):
        t_labels = ["📊 DATA", "➕ MASUK", "➖ KELUAR", "📱 WA", "🚪 LOGOUT"] if st.session_state.role == "Owner" else ["➕ MASUK", "➖ KELUAR", "📱 WA", "🚪 LOGOUT"]
        t_name = t_labels[i]
        
        with tab:
            if "DATA" in t_name:
                if not df_stok.empty: st.dataframe(df_stok, use_container_width=True, hide_index=True)
                else: st.info("Gagal muat data.")
                if st.button("REFRESH DATA"): st.rerun()

            elif "MASUK" in t_name:
                with st.form("in", clear_on_submit=True):
                    has_col = not df_stok.empty and "Barang" in df_stok.columns
                    mode = st.radio("Metode:", ["Update Stok", "Barang Baru"], horizontal=True) if has_col else "Barang Baru"
                    if mode == "Update Stok" and has_col:
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

            elif "KELUAR" in t_name:
                if not df_stok.empty and "Barang" in df_stok.columns:
                    with st.form("out", clear_on_submit=True):
                        n_o = st.selectbox("Barang Keluar:", df_stok['Barang'].unique())
                        m_o = df_stok[df_stok['Barang'] == n_o].iloc[0]
                        j_o = st.number_input(f"Jumlah (Stok: {m_o['Sisa Stok']}):", min_value=1)
                        if st.form_submit_button("CATAT KELUAR"):
                            p = {"id": str(int(datetime.now().timestamp())+1), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state.role, "jenis": "KELUAR", "kategori": m_o['Kategori'], "barang": n_o, "jumlah": int(j_o), "satuan": m_o['Satuan']}
                            requests.post(URL_WEB_APP, json=p)
                            st.session_state.report += f"• {n_o}: -{j_o} {m_o['Satuan']}\n"
                            st.success("Berhasil!")
                else: st.warning("Data belum sinkron.")

            elif "WA" in t_name:
                if st.session_state.report:
                    msg = f"*LAPORAN GUDANG*\nUser: {st.session_state.role}\n---\n{st.session_state.report}"
                    st.text_area("Draft:", msg, height=150)
                    url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                    st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#000000;color:white;padding:15px;border-radius:4px;text-align:center;font-weight:bold;">🚀 KIRIM WA</div></a>', unsafe_allow_html=True)
                else: st.info("Belum ada transaksi.")

            elif "LOGOUT" in t_name:
                if st.button("KELUAR"):
                    st.session_state.logged_in = False
                    st.rerun()
