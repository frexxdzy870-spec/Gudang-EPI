import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. CONFIG & CSS REVISI TOTAL (Teks Hitam, Kotak Putih)
st.set_page_config(page_title="Gudang Epidemi", page_icon="", layout="centered")

st.markdown("""
    <style>
    /* Background Putih */
    .stApp {
        background-color: #FFFFFF !important;
    }
    /* Maksa Semua Teks jadi Hitam */
    html, body, [data-testid="stWidgetLabel"], .stText, p, h1, h2, h3, span {
        color: #000000 !important;
    }
    /* Benerin Kotak Input (Input Box) */
    input, div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: #F0F2F6 !important; /* Abu muda biar kotak kelihatan */
        color: #000000 !important; /* Teks di dalam kotak WAJIB HITAM */
        border: 1px solid #D1D1D1 !important;
    }
    /* Benerin Teks di Dropdown/Selectbox */
    div[data-testid="stSelectbox"] * {
        color: #000000 !important;
    }
    /* Ngilangin Header & Footer */
    header, footer {
        visibility: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzBpJCmQ2ErCu4TsDQ3BUujKOwCvdHxWmU8ZOqhXAu-5_1nYnQU89QxmY0Ckr5UY4-K-A/exec"
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/3063/3063822.png" 

# --- FUNGSI CLOUD ---
def fetch_stok():
    try:
        response = requests.get(URL_WEB_APP, timeout=10)
        data = response.json()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame(columns=["Kategori", "Barang", "Satuan", "Sisa Stok"])
    except:
        # Balikin DF kosong biar nggak error merah
        return pd.DataFrame(columns=["Kategori", "Barang", "Satuan", "Sisa Stok"])

def push_data(payload):
    try:
        res = requests.post(URL_WEB_APP, json=payload, timeout=10)
        return res.text
    except:
        return "Gagal Koneksi"

# --- LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'temp_report': ""})

if not st.session_state['logged_in']:
    st.image(LOGO_URL, width=80)
    st.subheader("Login Gudang Sahaja")
    role = st.selectbox("Role:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
    pw = st.text_input("Password:", type="password")
    
    if st.button("Masuk"):
        if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
            st.session_state.update({'logged_in': True, 'role': role})
            st.rerun()
        else:
            st.error("Password Salah!")

else:
    # Header
    st.title("📦 Gudang Epidemi")
    st.write(f"User: **{st.session_state['role']}**")
    
    # Ambil data stok (Silently handle error)
    df_stok = fetch_stok()

    if st.session_state['role'] == "Owner":
        menu = st.tabs(["📊 Stok Gudang", "🚪 Logout"])
        with menu[0]:
            if not df_stok.empty:
                st.dataframe(df_stok, use_container_width=True, hide_index=True)
            else:
                st.info("Data belum tersedia di Google Sheets.")
            if st.button("Refresh Data"): st.rerun()
        with menu[1]:
            if st.button("Keluar"):
                st.session_state.update({'logged_in': False})
                st.rerun()

    else:
        menu = st.tabs(["➕ Masuk", "➖ Keluar", "📱 WA", "🚪 Logout"])
        
        # TAB MASUK
        with menu[0]:
            with st.form("in", clear_on_submit=True):
                opt = st.radio("Metode:", ["Update Stok", "Barang Baru"], horizontal=True)
                if opt == "Update Stok" and not df_stok.empty:
                    nama = st.selectbox("Pilih Barang:", df_stok['Barang'].unique())
                    # Cari kategori/satuan otomatis
                    match = df_stok[df_stok['Barang'] == nama].iloc[0]
                    kat, sat = match['Kategori'], match['Satuan']
                    st.caption(f"Info: {kat} | {sat}")
                else:
                    nama = st.text_input("Nama Barang:").upper()
                    kat = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                    sat = st.selectbox("Satuan:", ["pcs", "kg", "gram", "box"])
                
                jml = st.number_input("Jumlah:", min_value=1, step=1)
                if st.form_submit_button("Simpan"):
                    if nama:
                        p = {"id": str(int(datetime.now().timestamp())), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state['role'], "jenis": "MASUK", "kategori": kat, "barang": nama, "jumlah": int(jml), "satuan": sat}
                        if "Success" in push_data(p):
                            st.success("Tersimpan!")
                            st.session_state['temp_report'] += f"• {nama}: +{jml} {sat}\n"
                        else: st.error("Gagal kirim.")

        # TAB KELUAR
        with menu[1]:
            if not df_stok.empty:
                with st.form("out", clear_on_submit=True):
                    n_o = st.selectbox("Barang Keluar:", df_stok['Barang'].unique())
                    m_o = df_stok[df_stok['Barang'] == n_o].iloc[0]
                    j_o = st.number_input("Jumlah:", min_value=1, max_value=int(m_o['Sisa Stok']), step=1)
                    if st.form_submit_button("Catat"):
                        p = {"id": str(int(datetime.now().timestamp()) + 1), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state['role'], "jenis": "KELUAR", "kategori": m_o['Kategori'], "barang": n_o, "jumlah": int(j_o), "satuan": m_o['Satuan']}
                        if "Success" in push_data(p):
                            st.success("Tercatat!")
                            st.session_state['temp_report'] += f"• {n_o}: -{j_o} {m_o['Satuan']}\n"
                        else: st.error("Gagal.")
            else: st.warning("Stok kosong.")

        # TAB WA
        with menu[2]:
            st.subheader("Kirim Laporan")
            if st.session_state['temp_report']:
                msg = f"*LAPORAN GUDANG*\nUser: {st.session_state['role']}\nTgl: {datetime.now().strftime('%d/%m/%Y')}\n---\n{st.session_state['temp_report']}"
                st.text_area("Draft:", msg, height=120)
                url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:10px;border-radius:8px;text-align:center;font-weight:bold;">KIRIM WA</div></a>', unsafe_allow_html=True)
                if st.button("Hapus Draft"):
                    st.session_state['temp_report'] = ""; st.rerun()
            else: st.info("Belum ada input.")

        with menu[3]:
            if st.button("Logout"):
                st.session_state.update({'logged_in': False}); st.rerun()
