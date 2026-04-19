import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. KONFIGURASI HALAMAN & TEMA PUTIH
st.set_page_config(page_title="Gudang Epidemi", page_icon="", layout="centered")

# CSS untuk memaksakan tampilan bersih/putih
st.markdown("""
    <style>
    .stApp {
        background-color: white;
        color: #1E1E1E;
    }
    header, footer {
        visibility: hidden;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
    }
    div[data-testid="stExpander"] {
        border: none !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Ganti dengan URL Web App Apps Script lu yang sudah di-deploy "Anyone"
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzBpJCmQ2ErCu4TsDQ3BUujKOwCvdHxWmU8ZOqhXAu-5_1nYnQU89QxmY0Ckr5UY4-K-A/exec"

# Link Logo (Ganti URL ini dengan link gambar aslimu kalau ada)
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/3063/3063822.png" 

# --- FUNGSI CLOUD ---
def fetch_stok():
    try:
        response = requests.get(URL_WEB_APP)
        data = response.json()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame(columns=["Kategori", "Barang", "Satuan", "Sisa Stok"])
    except:
        return pd.DataFrame(columns=["Kategori", "Barang", "Satuan", "Sisa Stok"])

def push_data(payload):
    try:
        res = requests.post(URL_WEB_APP, json=payload)
        return res.text
    except:
        return "Gagal Koneksi"

# --- LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'temp_report': ""})

if not st.session_state['logged_in']:
    st.image(LOGO_URL, width=100)
    st.subheader("Gudang Epidemi")
    role = st.selectbox("Siapa Anda?", ["Staff Shift 1", "Staff Shift 2", "Owner"])
    pw = st.text_input("Password", type="password")
    
    if st.button("Masuk"):
        if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
            st.session_state.update({'logged_in': True, 'role': role})
            st.rerun()
        else:
            st.error("Password Salah!")

else:
    # Header Aplikasi
    col_l, col_r = st.columns([1, 4])
    with col_l: st.image(LOGO_URL, width=60)
    with col_r: st.title("Gudang Sahaja")
    
    st.write(f"Akses: **{st.session_state['role']}**")
    
    # Ambil data stok (untuk pilihan barang)
    df_stok = fetch_stok()

    # --- LOGIKA TAMPILAN BERDASARKAN ROLE ---
    if st.session_state['role'] == "Owner":
        menu = st.tabs(["📊 Pantau Stok", "⚙️ Update Barang", "Logout"])
        t_view, t_upd, t_out = menu
        
        with t_view:
            st.dataframe(df_stok, use_container_width=True, hide_index=True)
            if st.button("Refresh Data"): st.rerun()
            
        with t_upd:
            st.info("Fitur hapus/edit barang langsung di Google Sheets ya!")
            
        with t_out:
            if st.button("Keluar"):
                st.session_state.update({'logged_in': False})
                st.rerun()

    else:
        # TAMPILAN KARYAWAN (Cukup Masuk, Keluar, dan WA)
        menu = st.tabs(["➕ Masuk", "➖ Keluar", "📱 Laporan WA", "Logout"])
        t_in, t_out, t_wa, t_logout = menu

        with t_in:
            with st.form("form_masuk", clear_on_submit=True):
                # Opsi Tambah Stok Barang Lama atau Barang Baru
                opt = st.radio("Jenis Input:", ["Barang Sudah Ada", "Barang Baru Baru"], horizontal=True)
                
                if opt == "Barang Sudah Ada" and not df_stok.empty:
                    nama = st.selectbox("Pilih Barang:", df_stok['Barang'].unique())
                    # Auto-detect kategori dan satuan
                    row = df_stok[df_stok['Barang'] == nama].iloc[0]
                    kat, sat = row['Kategori'], row['Satuan']
                    st.caption(f"Kategori: {kat} | Satuan: {sat}")
                else:
                    nama = st.text_input("Nama Barang Baru").upper()
                    kat = st.selectbox("Kategori", ["BAR", "KITCHEN"])
                    sat = st.selectbox("Satuan", ["pcs", "kg", "gram", "box"])
                
                jml = st.number_input("Jumlah Masuk", min_value=1, step=1)
                if st.form_submit_button("Simpan Ke Cloud"):
                    payload = {
                        "id": str(int(datetime.now().timestamp())),
                        "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "user": st.session_state['role'],
                        "jenis": "MASUK",
                        "kategori": kat, "barang": nama, "jumlah": int(jml), "satuan": sat
                    }
                    if push_data(payload) == "Success":
                        st.success(f"Berhasil menambah {jml} {sat} {nama}")
                        # Tambahkan ke log laporan sementara
                        st.session_state['temp_report'] += f"- {nama}: +{jml} {sat}\n"
                    else: st.error("Gagal kirim data.")

        with t_out:
            if df_stok.empty:
                st.warning("Belum ada data barang di cloud.")
            else:
                with st.form("form_keluar", clear_on_submit=True):
                    nama_o = st.selectbox("Pilih Barang Keluar:", df_stok['Barang'].unique())
                    row_o = df_stok[df_stok['Barang'] == nama_o].iloc[0]
                    st.write(f"Stok Terakhir: {row_o['Sisa Stok']} {row_o['Satuan']}")
                    
                    jml_o = st.number_input("Jumlah Keluar", min_value=1, max_value=int(row_o['Sisa Stok']), step=1)
                    if st.form_submit_button("Catat Keluar"):
                        payload = {
                            "id": str(int(datetime.now().timestamp()) + 1),
                            "waktu": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "user": st.session_state['role'],
                            "jenis": "KELUAR",
                            "kategori": row_o['Kategori'], "barang": nama_o, "jumlah": int(jml_o), "satuan": row_o['Satuan']
                        }
                        if push_data(payload) == "Success":
                            st.success(f"Berhasil mencatat pengeluaran {nama_o}")
                            st.session_state['temp_report'] += f"- {nama_o}: -{jml_o} {row_o['Satuan']}\n"
                        else: st.error("Gagal.")

        with t_wa:
            st.subheader("Kirim Laporan Shift")
            if st.session_state['temp_report'] == "":
                st.info("Belum ada aktivitas masuk/keluar di sesi ini.")
            else:
                laporan_final = f"*LAPORAN INVENTARIS GUDANG*\n"
                laporan_final += f"User: {st.session_state['role']}\n"
                laporan_final += f"Tgl: {datetime.now().strftime('%d/%m/%Y')}\n"
                laporan_final += f"--------------------------\n"
                laporan_final += st.session_state['temp_report']
                laporan_final += f"--------------------------\n"
                laporan_final += "*Detail stok otomatis terupdate di Cloud.*"
                
                st.text_area("Pratinjau Pesan:", laporan_final, height=150)
                
                encoded_msg = urllib.parse.quote(laporan_final)
                wa_url = f"https://wa.me/?text={encoded_msg}"
                
                st.markdown(f'''
                    <a href="{wa_url}" target="_blank" style="text-decoration: none;">
                        <div style="background-color: #25D366; color: white; padding: 12px; border-radius: 10px; text-align: center; font-weight: bold;">
                             KIRIM KE GRUP WA
                        </div>
                    </a>
                ''', unsafe_allow_html=True)
                
                if st.button("Reset Catatan Laporan"):
                    st.session_state['temp_report'] = ""
                    st.rerun()

        with t_logout:
            if st.button("Log Out"):
                st.session_state.update({'logged_in': False})
                st.rerun()
