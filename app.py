import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. CSS REVISI - PUTIH BERSIH, TEKS TEGAS, KOTAK JELAS
st.set_page_config(page_title="Gudang Sahaja", layout="centered")

st.markdown("""
    <style>
    /* Background Putih */
    .stApp { background-color: #FFFFFF !important; }
    
    /* Header & Teks Hitam Pekat */
    h1, h2, h3, p, span, label, [data-testid="stWidgetLabel"] {
        color: #000000 !important;
        font-weight: 800 !important;
    }

    /* Kotak Input & Dropdown - Kasih Border Biru biar Gak Berantakan */
    input, [data-baseweb="select"] > div, [data-baseweb="input"] > div, textarea {
        background-color: #F8F9FA !important;
        color: #000000 !important;
        border: 2px solid #007BFF !important;
        border-radius: 10px !important;
    }

    /* Tombol Biru Kontras */
    .stButton>button {
        background-color: #007BFF !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: none !important;
        width: 100% !important;
        height: 3.5em !important;
        box-shadow: 0px 4px 10px rgba(0,123,255,0.3) !important;
    }

    /* Tab Menu - Kasih Warna Hitam biar Kelihatan */
    button[data-baseweb="tab"] {
        color: #000000 !important;
        font-weight: bold !important;
    }

    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# URL Logo dari GitHub (Ganti 'username' dan 'repo' lu)
# PENTING: Gunakan link RAW (raw.githubusercontent.com)
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

# --- LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'report': ""})

if not st.session_state['logged_in']:
    try: st.image(LOGO_URL, width=120)
    except: st.title("☕ Gudang Sahaja")
    
    role = st.selectbox("Pilih Akses:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
    pw = st.text_input("Password:", type="password")
    if st.button("MASUK SISTEM"):
        if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
            st.session_state.update({'logged_in': True, 'role': role})
            st.rerun()
        else: st.error("Password Salah!")
else:
    # --- TAMPILAN HEADER ---
    col1, col2 = st.columns([1, 4])
    with col1: 
        try: st.image(LOGO_URL, width=80)
        except: st.write("📦")
    with col2: 
        st.title("Sistem Gudang")
        st.write(f"User: **{st.session_state.role}**")

    df_stok = fetch_data()
    has_data = not df_stok.empty and "Barang" in df_stok.columns

    # --- FITUR OWNER (LENGKAP) ---
    if st.session_state.role == "Owner":
        menu = st.tabs(["📊 Data Gudang", "➕ Barang Masuk", "➖ Barang Keluar", "🚪 Keluar"])
        
        with menu[0]:
            st.subheader("Semua Data Gudang")
            if has_data: st.dataframe(df_stok, use_container_width=True, hide_index=True)
            else: st.warning("Data kosong atau Google Sheets belum siap.")
            if st.button("🔄 Segarkan Data"): st.rerun()

        # Fitur Input buat Owner (Sama kayak Staff)
        with menu[1]:
            with st.form("in_owner"):
                mode = st.radio("Metode:", ["Update Stok", "Barang Baru"], horizontal=True) if has_data else "Barang Baru"
                if mode == "Update Stok":
                    nama = st.selectbox("Pilih Barang:", df_stok['Barang'].unique())
                    row = df_stok[df_stok['Barang'] == nama].iloc[0]
                    kat, sat = row['Kategori'], row['Satuan']
                else:
                    nama = st.text_input("Nama Barang Baru:").upper()
                    kat = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                    sat = st.selectbox("Satuan:", ["pcs", "kg", "gram", "box"])
                jml = st.number_input("Jumlah:", min_value=1)
                if st.form_submit_button("SIMPAN DATA"):
                    p = {"id": str(int(datetime.now().timestamp())), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": "Owner", "jenis": "MASUK", "kategori": kat, "barang": nama, "jumlah": int(jml), "satuan": sat}
                    requests.post(URL_WEB_APP, json=p); st.success("Tersimpan!"); st.rerun()

        with menu[2]:
            if has_data:
                with st.form("out_owner"):
                    n_o = st.selectbox("Barang Keluar:", df_stok['Barang'].unique())
                    m_o = df_stok[df_stok['Barang'] == n_o].iloc[0]
                    j_o = st.number_input("Jumlah:", min_value=1, max_value=int(m_o['Sisa Stok']))
                    if st.form_submit_button("CATAT KELUAR"):
                        p = {"id": str(int(datetime.now().timestamp())+1), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": "Owner", "jenis": "KELUAR", "kategori": m_o['Kategori'], "barang": n_o, "jumlah": int(j_o), "satuan": m_o['Satuan']}
                        requests.post(URL_WEB_APP, json=p); st.success("Berhasil!"); st.rerun()

        with menu[3]:
            if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

    # --- FITUR STAFF (TERBATAS) ---
    else:
        menu = st.tabs(["➕ Masuk", "➖ Keluar", "📱 Laporan", "🚪 Logout"])
        
        with menu[0]:
            with st.form("in_staff"):
                mode = st.radio("Metode:", ["Update Stok", "Barang Baru"], horizontal=True) if has_data else "Barang Baru"
                if mode == "Update Stok":
                    nama = st.selectbox("Barang:", df_stok['Barang'].unique())
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
                    st.session_state.report += f"• {nama}: +{jml} {sat}\n"; st.success("Sip!"); st.rerun()

        with menu[1]:
            if has_data:
                with st.form("out_staff"):
                    n_o = st.selectbox("Barang Keluar:", df_stok['Barang'].unique())
                    m_o = df_stok[df_stok['Barang'] == n_o].iloc[0]
                    j_o = st.number_input("Jumlah:", min_value=1, max_value=int(m_o['Sisa Stok']))
                    if st.form_submit_button("CATAT"):
                        p = {"id": str(int(datetime.now().timestamp())+1), "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "user": st.session_state.role, "jenis": "KELUAR", "kategori": m_o['Kategori'], "barang": n_o, "jumlah": int(j_o), "satuan": m_o['Satuan']}
                        requests.post(URL_WEB_APP, json=p)
                        st.session_state.report += f"• {n_o}: -{j_o} {m_o['Satuan']}\n"; st.success("Tercatat!"); st.rerun()

        with menu[2]:
            if st.session_state.report:
                msg = f"*LAPORAN GUDANG*\nUser: {st.session_state.role}\n---\n{st.session_state.report}"
                st.text_area("Draft:", msg, height=150)
                url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:15px;border-radius:10px;text-align:center;font-weight:bold;">🚀 KIRIM KE WA</div></a>', unsafe_allow_html=True)
                if st.button("Hapus Draft"): st.session_state.report = ""; st.rerun()
            else: st.info("Belum ada input.")

        with menu[3]:
            if st.button("Logout"): st.session_state.logged_in = False; st.rerun()
