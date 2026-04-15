import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64
import urllib.parse

# Konfigurasi Halaman
st.set_page_config(page_title="Gudang Epidemi", page_icon="", layout="centered")

# --- DATABASE FILES ---
DB_RIWAYAT = "riwayat_transaksi.csv"
DB_STOK = "stok_barang.csv" 
LOGO_FILE = "458630371_496384856460695_7166325097110089328_n.jpg"

# --- FUNGSI DATA ---
def load_riwayat():
    if os.path.exists(DB_RIWAYAT):
        df = pd.read_csv(DB_RIWAYAT)
        df['Tgl_Murni'] = pd.to_datetime(df['Waktu'], format="%d/%m/%Y %H:%M").dt.strftime("%Y-%m-%d")
        return df
    return pd.DataFrame(columns=["ID", "Waktu", "User", "Jenis", "Kategori", "Barang", "Jumlah", "Satuan", "Tgl_Murni"])

def load_stok():
    if os.path.exists(DB_STOK):
        df = pd.read_csv(DB_STOK)
        df["Sisa Stok"] = df["Sisa Stok"].astype(int)
        return df
    return pd.DataFrame(columns=["Kategori", "Barang", "Satuan", "Sisa Stok"])

def save_all(df_riwayat, df_stok):
    if 'Tgl_Murni' in df_riwayat.columns:
        df_riwayat = df_riwayat.drop(columns=['Tgl_Murni'])
    df_riwayat.to_csv(DB_RIWAYAT, index=False)
    df_stok.to_csv(DB_STOK, index=False)

def display_centered_logo(file_path, width=80):
    try:
        with open(file_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        st.markdown(f'<div style="display: flex; justify-content: center; margin-bottom: 10px;"><img src="data:image/jpeg;base64,{data}" width="{width}"></div>', unsafe_allow_html=True)
    except: pass

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None})

if not st.session_state['logged_in']:
    display_centered_logo(LOGO_FILE)
    st.markdown("<h3 style='text-align: center;'>Login Sistem Gudang</h3>", unsafe_allow_html=True)
    role = st.selectbox("Siapa Anda?", ["Staff Shift 1", "Staff Shift 2", "Owner"])
    pw = st.text_input(f"Password {role}", type="password")
    if st.button("Masuk"):
        if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
            st.session_state.update({'logged_in': True, 'role': role})
            st.rerun()
else:
    with st.sidebar:
        display_centered_logo(LOGO_FILE)
        st.markdown(f"<p style='text-align: center;'>Logged in:<br><b>{st.session_state['role']}</b></p>", unsafe_allow_html=True)
        if st.sidebar.button("Logout"):
            st.session_state.update({'logged_in': False, 'role': None})
            st.rerun()

    st.title("📦 Inventaris Gudang")
    df_r = load_riwayat()
    df_s = load_stok()

    # Navigasi Tab
    if st.session_state['role'] == "Owner":
        tabs = st.tabs(["📊 Stok", "📜 Riwayat", "📱 Laporan Grup"])
    else:
        tabs = st.tabs(["➕ Masuk", "➖ Keluar", "📊 Stok", "📜 Riwayat", "📱 Laporan Grup"])
    
    t_in, t_out, t_stok, t_riwayat, t_wa = (tabs if len(tabs) == 5 else [None, None] + tabs)

    # --- TAB MASUK (Singkat) ---
    if st.session_state['role'] != "Owner":
        with t_in:
            mode = st.radio("Tipe:", ["Barang Baru", "Tambah Stok Lama"], horizontal=True)
            with st.form("in"):
                if mode == "Barang Baru":
                    nama = st.text_input("Nama Barang").upper()
                    kat = st.selectbox("Kategori", ["BAR", "KITCHEN"])
                    sat = st.selectbox("Satuan", ["pcs", "kg", "box"])
                else:
                    nama = st.selectbox("Pilih Barang", df_s['Barang'].unique()) if not df_s.empty else None
                    if nama:
                        kat = df_s[df_s['Barang'] == nama]['Kategori'].values[0]
                        sat = df_s[df_s['Barang'] == nama]['Satuan'].values[0]
                jml = st.number_input("Jumlah", min_value=1, step=1)
                if st.form_submit_button("Simpan"):
                    if nama:
                        new_r = {"ID": str(int(datetime.now().timestamp())), "Waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "User": st.session_state['role'], "Jenis": "MASUK", "Kategori": kat, "Barang": nama, "Jumlah": int(jml), "Satuan": sat}
                        df_r = pd.concat([df_r, pd.DataFrame([new_r])], ignore_index=True)
                        if nama in df_s['Barang'].values: df_s.loc[df_s['Barang'] == nama, 'Sisa Stok'] += int(jml)
                        else: df_s = pd.concat([df_s, pd.DataFrame([{"Kategori": kat, "Barang": nama, "Satuan": sat, "Sisa Stok": int(jml)}])], ignore_index=True)
                        save_all(df_r, df_s); st.rerun()

        with t_out:
            if not df_s.empty:
                with st.form("out"):
                    nama_o = st.selectbox("Barang Keluar", df_s['Barang'].unique())
                    r_s = df_s[df_s['Barang'] == nama_o].iloc[0]
                    jml_o = st.number_input(f"Jumlah ({r_s['Sisa Stok']} {r_s['Satuan']} tersedia)", min_value=1, max_value=int(r_s['Sisa Stok']), step=1)
                    if st.form_submit_button("Keluarkan"):
                        new_r = {"ID": str(int(datetime.now().timestamp()) + 1), "Waktu": datetime.now().strftime("%d/%m/%Y %H:%M"), "User": st.session_state['role'], "Jenis": "KELUAR", "Kategori": r_s['Kategori'], "Barang": nama_o, "Jumlah": int(jml_o), "Satuan": r_s['Satuan']}
                        df_r = pd.concat([df_r, pd.DataFrame([new_r])], ignore_index=True)
                        df_s.loc[df_s['Barang'] == nama_o, 'Sisa Stok'] -= int(jml_o); save_all(df_r, df_s); st.rerun()

    # --- TAB STOK & RIWAYAT (Hapus Kontekstual) ---
    with t_stok:
        st.dataframe(df_s.sort_values("Kategori"), use_container_width=True, hide_index=True)
        if st.session_state['role'] != "Owner" and not df_s.empty:
            with st.expander("🗑️ Hapus Kesalahan Produk"):
                p_del = st.selectbox("Pilih Produk:", ["-- Pilih --"] + list(df_s['Barang'].unique()))
                if p_del != "-- Pilih --" and st.button(f"Hapus {p_del}"):
                    df_s = df_s[df_s['Barang'] != p_del]; save_all(df_r, df_s); st.rerun()

    with t_riwayat:
        if not df_r.empty:
            st.dataframe(df_r.drop(columns=["ID", "Tgl_Murni"]).sort_index(ascending=False), use_container_width=True, hide_index=True)
            if st.session_state['role'] != "Owner":
                with st.expander("🗑️ Hapus Riwayat"):
                    r_list = df_r.tail(15).iloc[::-1]
                    sel_r = st.selectbox("Pilih baris:", ["-- Pilih --"] + [f"{row['Waktu']} | {row['Barang']}" for _, row in r_list.iterrows()])
                    if sel_r != "-- Pilih --":
                        idx = [f"{row['Waktu']} | {row['Barang']}" for _, row in r_list.iterrows()].index(sel_r)
                        if st.button("Hapus Baris Ini"):
                            df_r = df_r[df_r['ID'] != r_list.iloc[idx]['ID']]; save_all(df_r, df_s); st.rerun()

    # --- TAB LAPORAN GRUP (Sesuai Request Baru) ---
    with t_wa:
        st.subheader("📱 Kirim Laporan ke Grup")
        shift_l = st.selectbox("Laporan Shift", ["Staff Shift 1", "Staff Shift 2"])
        
        if st.button("Generate & Kirim Laporan"):
            tgl_now = datetime.now().strftime("%Y-%m-%d")
            mask = (df_r['Tgl_Murni'] == tgl_now) & (df_r['User'] == shift_l)
            df_h = df_r[mask]
            
            if not df_h.empty:
                pesan = f"*LAPORAN GUDANG - {shift_l.upper()}*\n"
                pesan += f"Tgl: {datetime.now().strftime('%d/%m/%Y')}\n"
                pesan += "--------------------------------\n\n"
                
                m = df_h[df_h['Jenis']=='MASUK']
                if not m.empty:
                    pesan += "*[MASUK]*\n" + "\n".join([f"• {r['Barang']}: {r['Jumlah']} {r['Satuan']}" for _, r in m.iterrows()]) + "\n\n"
                
                k = df_h[df_h['Jenis']=='KELUAR']
                if not k.empty:
                    pesan += "*[KELUAR]*\n" + "\n".join([f"• {r['Barang']}: {r['Jumlah']} {r['Satuan']}" for _, r in k.iterrows()])
                
                pesan += "\n--------------------------------\n"
                pesan += "_Sent from Inventory System_"

                # Link WhatsApp tanpa nomor = Membuka daftar chat/grup
                url_wa = f"https://wa.me/?text={urllib.parse.quote(pesan)}"
                
                st.markdown(f"""
                    <a href="{url_wa}" target="_blank">
                        <div style="text-align: center; padding: 15px; background-color: #25D366; color: white; border-radius: 10px; font-weight: bold; text-decoration: none;">
                            KLIK UNTUK PILIH GRUP WHATSAPP
                        </div>
                    </a>
                """, unsafe_allow_html=True)
                st.info("Setelah klik, silakan pilih grup yang dituju di WhatsApp.")
            else:
                st.warning("Data transaksi shift ini masih kosong hari ini.")
