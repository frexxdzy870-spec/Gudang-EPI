import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. FIX CSS TOTAL - KONTRAS TINGGI
st.set_page_config(page_title="Gudang Epidemi", layout="centered")

st.markdown("""
    <style>
    /* Background Putih Bersih */
    .stApp { background-color: #FFFFFF !important; }
    
    /* Maksa Label & Teks Luar jadi Hitam */
    [data-testid="stWidgetLabel"], p, h1, h2, h3, span, label {
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* Benerin Kotak Input & Dropdown */
    input, div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, textarea {
        background-color: #F0F2F6 !important; /* Abu terang biar kotak kelihatan */
        color: #000000 !important; /* Teks wajib HITAM */
        border: 2px solid #000000 !important; /* Kasih border biar tegas */
    }

    /* FIX TOMBOL: Kasih warna Biru biar gak Hitam-Hitam */
    .stButton>button {
        background-color: #007BFF !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        border: none !important;
        height: 3em !important;
    }
    
    /* Fix teks di dalam dropdown biar gak ilang */
    div[data-baseweb="popover"] div {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }

    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzBpJCmQ2ErCu4TsDQ3BUujKOwCvdHxWmU8ZOqhXAu-5_1nYnQU89QxmY0Ckr5UY4-K-A/exec"

def fetch_stok_safe():
    try:
        res = requests.get(URL_WEB_APP, timeout=5)
        data = res.json()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            df.columns = df.columns.str.strip()
            return df
    except:
        pass
    return pd.DataFrame()

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'temp_report': ""})

if not st.session_state['logged_in']:
    st.title("☕ Login Gudang")
    role = st.selectbox("Akses:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
    pw = st.text_input("Sandi:", type="password")
    if st.button("MASUK SEKARANG"):
        if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
            st.session_state.update({'logged_in': True, 'role': role})
            st.rerun()
        else: st.error("Sandi salah!")
else:
    df_stok = fetch_stok_safe()
    is_ready = not df_stok.empty and all(c in df_stok.columns for c in ["Barang", "Sisa Stok"])

    if st.session_state['role'] == "Owner":
        st.subheader("📊 Stok Real-time (Owner)")
        if is_ready:
            st.dataframe(df_stok, use_container_width=True, hide_index=True)
        else:
            st.warning("Database sedang loading atau Sheet salah format.")
        if st.button("LOGOUT"):
            st.session_state.logged_in = False; st.rerun()

    else:
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Masuk", "➖ Keluar", "📱 WA", "🚪 Logout"])
        
        with tab1:
            with st.form("in", clear_on_submit=True):
                if is_ready:
                    mode = st.radio("Metode:", ["Update Stok", "Barang Baru"], horizontal=True)
                else:
                    mode = "Barang Baru"
                    st.info("Mode Barang Baru Aktif (Sinkronisasi...)")

                if mode == "Update Stok":
                    nama = st.selectbox("Pilih Barang:", df_stok['Barang'].unique())
                    row = df_stok[df_stok['Barang'] == nama].iloc[0]
                    kat, sat = row.get('Kategori', 'BAR'), row.get('Satuan', 'pcs')
                else:
                    nama = st.text_input("Nama Barang:").upper()
                    kat = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                    sat = st.selectbox("Satuan:", ["pcs", "kg", "gram", "box"])
                
                jml = st.number_input("Jumlah:", min_value=1)
                if st.form_submit_button("SIMPAN DATA"):
                    if nama:
                        p = {"id": str(int(datetime.now().timestamp())), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state['role'], "jenis": "MASUK", "kategori": kat, "barang": nama, "jumlah": int(jml), "satuan": sat}
                        try:
                            r = requests.post(URL_WEB_APP, json=p, timeout=10)
                            if "Success" in r.text:
                                st.success(f"Berhasil: {nama}")
                                st.session_state['temp_report'] += f"• {nama}: +{jml} {sat}\n"
                            else: st.error("Gagal simpan.")
                        except: st.error("Koneksi Error.")

        with tab2:
            if is_ready:
                with st.form("out", clear_on_submit=True):
                    n_o = st.selectbox("Barang Keluar:", df_stok['Barang'].unique())
                    m_o = df_stok[df_stok['Barang'] == n_o].iloc[0]
                    j_o = st.number_input("Jumlah:", min_value=1, max_value=int(m_o['Sisa Stok']))
                    if st.form_submit_button("CATAT KELUAR"):
                        p = {"id": str(int(datetime.now().timestamp())+1), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state['role'], "jenis": "KELUAR", "kategori": m_o['Kategori'], "barang": n_o, "jumlah": int(j_o), "satuan": m_o['Satuan']}
                        try:
                            requests.post(URL_WEB_APP, json=p, timeout=10)
                            st.success("Tercatat!"); st.session_state['temp_report'] += f"• {n_o}: -{j_o} {m_o['Satuan']}\n"
                        except: st.error("Gagal.")
            else: st.warning("Data stok belum termuat.")

        with tab3:
            if st.session_state['temp_report']:
                msg = f"*LAPORAN GUDANG*\nUser: {st.session_state['role']}\n---\n{st.session_state['temp_report']}"
                st.text_area("Pratinjau:", msg, height=150)
                url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:15px;border-radius:10px;text-align:center;font-weight:bold;">🚀 KIRIM KE WA</div></a>', unsafe_allow_html=True)
            else: st.info("Belum ada input.")

        with tab4:
            if st.button("LOGOUT SEKARANG"):
                st.session_state.logged_in = False; st.rerun()
