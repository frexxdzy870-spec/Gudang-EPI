import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. CSS DARK MODE (BALIK KE AWAL TAPI FIX KONTRAS)
st.set_page_config(page_title="Gudang Sahaja", layout="centered")

st.markdown("""
    <style>
    /* Background Hitam Pekat */
    .stApp { background-color: #0E1117 !important; }
    
    /* Semua Teks & Label Jadi Putih/Terang biar Kelihatan */
    h1, h2, h3, p, span, label, [data-testid="stWidgetLabel"] {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Input Box: Background Gelap, Border Putih Tipis, Teks PUTIH */
    input, [data-baseweb="select"] > div, [data-baseweb="input"] > div, textarea {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border: 1px solid #444444 !important;
        border-radius: 4px !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Dropdown Text Fix */
    div[data-baseweb="select"] *, div[role="listbox"] * {
        color: #FFFFFF !important;
    }

    /* Tombol: Putih Tulisan Hitam (Biar Kontras sama BG) */
    .stButton>button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: none !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 3em !important;
        border-radius: 4px !important;
    }
    
    .stButton>button p, .stButton>button span {
        color: #000000 !important;
    }

    /* Tab Menu */
    button[data-baseweb="tab"] { color: #888888 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #FFFFFF !important; }

    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# URL KONFIGURASI
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

# --- LOGIN ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # LOGO BALIK LAGI
        try: st.image(LOGO_URL, width=120)
        except: st.markdown("<h1 style='text-align: center;'>☕</h1>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align: center;'>LOGIN SISTEM</h3>", unsafe_allow_html=True)
        role = st.selectbox("Pilih Role:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
        pw = st.text_input("Password:", type="password")
        if st.button("MASUK"):
            if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
                st.session_state.update({'logged_in': True, 'role': role})
                st.rerun()
            else: st.error("Password Salah!")
else:
    # --- DASHBOARD ---
    st.markdown(f"### 📦 {st.session_state.role}")
    df_stok = fetch_data()
    
    # Menu Tetap Ada (Sesuai setelan awal)
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
                else: st.info("Gagal muat data Google Sheets.")
                if st.button("REFRESH"): st.rerun()

            elif "MASUK" in t_name:
                with st.form("form_in", clear_on_submit=True):
                    has_data = not df_stok.empty and "Barang" in df_stok.columns
                    mode = st.radio("Opsi:", ["Stok Lama", "Barang Baru"], horizontal=True) if has_data else "Barang Baru"
                    if mode == "Stok Lama" and has_data:
                        nama = st.selectbox("Barang:", df_stok['Barang'].unique())
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
                        st.success("Tersimpan ke Cloud!")

            elif "KELUAR" in t_name:
                if not df_stok.empty and "Barang" in df_stok.columns:
                    with st.form("form_out", clear_on_submit=True):
                        n_o = st.selectbox("Barang:", df_stok['Barang'].unique())
                        m_o = df_stok[df_stok['Barang'] == n_o].iloc[0]
                        j_o = st.number_input(f"Jumlah (Sisa: {m_o['Sisa Stok']}):", min_value=1)
                        if st.form_submit_button("KELUARKAN"):
                            p = {"id": str(int(datetime.now().timestamp())+1), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state.role, "jenis": "KELUAR", "kategori": m_o['Kategori'], "barang": n_o, "jumlah": int(j_o), "satuan": m_o['Satuan']}
                            requests.post(URL_WEB_APP, json=p)
                            st.session_state.report += f"• {n_o}: -{j_o} {m_o['Satuan']}\n"
                            st.success("Tercatat!")
                else: st.warning("Data stok belum sinkron.")

            elif "WA" in t_name:
                if st.session_state.report:
                    msg = f"*LAPORAN GUDANG*\nUser: {st.session_state.role}\n---\n{st.session_state.report}"
                    st.text_area("Preview:", msg, height=150)
                    url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                    st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#FFFFFF;color:#000000;padding:15px;border-radius:4px;text-align:center;font-weight:bold;">🚀 KIRIM KE WA</div></a>', unsafe_allow_html=True)
                else: st.info("Belum ada aktivitas.")

            elif "LOGOUT" in t_name:
                if st.button("LOGOUT SEKARANG"):
                    st.session_state.logged_in = False
                    st.rerun()
