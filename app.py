import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse
import base64

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Gudang Epidemi", page_icon="", layout="centered")

# URL Web App GSheets kamu
URL_WEB_APP = "https://script.google.com/macros/s/AKfycby9BnSkIzUjvZz-rSmbuTVASvFo0x40OADSL29EgJOxIdebd4jseqqFyjB92HKwKx2HmA/exec"

# HIDE WATERMARK
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- FUNGSI CLOUD ---
def get_stok_from_cloud():
    try:
        response = requests.get(URL_WEB_APP)
        data = response.json()
        # Mengasumsikan baris pertama adalah header
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except:
        return pd.DataFrame(columns=["Kategori", "Barang", "Satuan", "Sisa Stok"])

def send_to_cloud(payload):
    try:
        response = requests.post(URL_WEB_APP, json=payload)
        return response.text
    except Exception as e:
        return str(e)

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None})

if not st.session_state['logged_in']:
    st.markdown("<h3 style='text-align: center;'>Login Gudang Sahaja</h3>", unsafe_allow_html=True)
    role = st.selectbox("Akses:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
    pw = st.text_input(f"Password {role}", type="password")
    if st.button("Masuk Ke Cloud", use_container_width=True):
        if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
            st.session_state.update({'logged_in': True, 'role': role})
            st.rerun()
        else:
            st.error("Password Salah!")
else:
    # Sidebar
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state['role']}**")
        if st.button("Logout"):
            st.session_state.update({'logged_in': False, 'role': None})
            st.rerun()

    st.title("📦 Inventaris Cloud")
    
    # Load Data Stok dari GSheets
    df_s = get_stok_from_cloud()

    # Tab Menu
    if st.session_state['role'] == "Owner":
        tabs = st.tabs(["📊 Stok Real-time", "📱 Laporan Grup"])
        t_stok, t_wa = tabs
    else:
        tabs = st.tabs(["➕ Barang Masuk", "➖ Barang Keluar", "📊 Stok", "📱 Laporan"])
        t_in, t_out, t_stok, t_wa = tabs

    # --- TAB MASUK ---
    if st.session_state['role'] != "Owner":
        with t_in:
            mode = st.radio("Tipe:", ["Barang Baru", "Stok Lama"], horizontal=True)
            with st.form("form_in", clear_on_submit=True):
                if mode == "Barang Baru":
                    nama = st.text_input("Nama Barang").upper()
                    kat = st.selectbox("Kategori", ["BAR", "KITCHEN"])
                    sat = st.selectbox("Satuan", ["pcs", "kg", "box", "gram"])
                else:
                    nama = st.selectbox("Pilih Barang", df_s['Barang'].unique()) if not df_s.empty else None
                    if nama:
                        row_data = df_s[df_s['Barang'] == nama].iloc[0]
                        kat = row_data['Kategori']
                        sat = row_data['Satuan']
                        st.info(f"Kategori: {kat} | Satuan: {sat}")
                
                jml = st.number_input("Jumlah Masuk", min_value=1, step=1)
                
                if st.form_submit_button("Kirim ke Cloud"):
                    if nama:
                        payload = {
                            "id": str(int(datetime.now().timestamp())),
                            "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "user": st.session_state['role'],
                            "jenis": "MASUK",
                            "kategori": kat,
                            "barang": nama,
                            "jumlah": int(jml),
                            "satuan": sat
                        }
                        res = send_to_cloud(payload)
                        if "Success" in res:
                            st.success(f"Berhasil! {nama} masuk ke Google Sheets.")
                            st.rerun()
                        else: st.error(f"Gagal: {res}")

        with t_out:
            if not df_s.empty:
                with st.form("form_out", clear_on_submit=True):
                    nama_o = st.selectbox("Pilih Barang Keluar", df_s['Barang'].unique())
                    curr = df_s[df_s['Barang'] == nama_o].iloc[0]
                    st.write(f"Tersedia: {curr['Sisa Stok']} {curr['Satuan']}")
                    jml_o = st.number_input("Jumlah Keluar", min_value=1, max_value=int(curr['Sisa Stok']), step=1)
                    
                    if st.form_submit_button("Catat Keluar"):
                        payload = {
                            "id": str(int(datetime.now().timestamp()) + 1),
                            "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "user": st.session_state['role'],
                            "jenis": "KELUAR",
                            "kategori": curr['Kategori'],
                            "barang": nama_o,
                            "jumlah": int(jml_o),
                            "satuan": curr['Satuan']
                        }
                        res = send_to_cloud(payload)
                        if "Success" in res:
                            st.success("Data keluar tersimpan di Cloud!")
                            st.rerun()
            else: st.info("Stok kosong di Cloud.")

    # --- TAB STOK ---
    with t_stok:
        st.subheader("Persediaan di Google Sheets")
        st.dataframe(df_s, use_container_width=True, hide_index=True)
        if st.button("Refresh Data"):
            st.rerun()

    # --- TAB WA ---
    with t_wa:
        st.subheader("📱 Laporan WA")
        if st.button("Generate Laporan Shift Ini"):
            # Untuk laporan detail riwayat hari ini, sebaiknya kamu punya fungsi doGet tambahan
            # atau sementara pakai format ringkasan stok.
            tgl = datetime.now().strftime('%d/%m/%Y')
            pesan = f"*LAPORAN GUDANG CLOUD*\nTgl: {tgl}\n\nCek detail stok lengkap di Google Sheets."
            url_wa = f"https://wa.me/?text={urllib.parse.quote(pesan)}"
            st.markdown(f'<a href="{url_wa}" target="_blank"><div style="text-align: center; padding: 15px; background-color: #25D366; color: white; border-radius: 10px; font-weight: bold; text-decoration: none;">KIRIM KE GRUP WA</div></a>', unsafe_allow_html=True)
