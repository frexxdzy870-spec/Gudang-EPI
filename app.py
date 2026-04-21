import streamlit as st
from supabase import create_client
import pandas as pd
import urllib.parse

# ==========================================
# 1. SETUP & KONFIGURASI
# ==========================================

# GANTI DENGAN URL & KEY SUPABASE LU SENDIRI
SUPABASE_URL = "ISI_URL_SUPABASE_LU"
SUPABASE_KEY = "ISI_ANON_KEY_LU"

# Link Logo 'THANKS.EPIDEMi!' (Pake link raw biar stabil)
# Jika lu naro file logo.png di folder yang sama dengan app.py, ganti jadi "logo.png"
LOGO_IMAGE = "https://raw.githubusercontent.com/username/repo/main/logo.png"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# Pengaturan Halaman
st.set_page_config(page_title="THANKS.EPIDEMi! Gudang", layout="centered")

# CSS: Tampilan Dark Mode, Kontras Tinggi, dan Styling Logo
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    h1, h2, h3, p, label, .stMarkdown { color: #FFFFFF !important; }
    
    /* Tombol Style */
    .stButton>button { 
        width: 100%; 
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        font-weight: bold; 
        height: 3.5em; 
        border-radius: 8px;
    }
    .stButton>button:hover { background-color: #DDDDDD !important; }
    
    /* Form Style */
    div[data-testid="stForm"] { border: 1px solid #444; border-radius: 10px; padding: 20px; }
    
    /* Logo Center di Login */
    .login-logo { display: flex; justify-content: center; margin-bottom: 20px; }
    
    /* Sidebar Styling */
    .css-163463a { background-color: #1A1C23; border-right: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI DATA (LOGIKA SOLID)
# ==========================================

def get_stock_data():
    """Ambil sisa stok saat ini dan riwayat lengkap."""
    try:
        res = supabase.table("inventory").select("*").execute()
        df = pd.DataFrame(res.data)
        if df.empty: return pd.DataFrame(), pd.DataFrame()
        
        # Urutkan riwayat dari yang terbaru
        df_raw = df.sort_values('waktu', ascending=False)
        
        # Hitung Sisa Stok per Barang (Groupby)
        summary = []
        for b in df['barang'].unique():
            b_df = df[df['barang'] == b]
            masuk = b_df[b_df['jenis'] == 'MASUK']['jumlah'].sum()
            keluar = b_df[b_df['jenis'] == 'KELUAR']['jumlah'].sum()
            row = b_df.iloc[0] # Ambil Kategori & Satuan dari baris pertama
            summary.append({
                "Barang": b, 
                "Kategori": row['kategori'], 
                "Sisa Stok": masuk - keluar, 
                "Satuan": row['satuan']
            })
        return pd.DataFrame(summary), df_raw
    except: return pd.DataFrame(), pd.DataFrame()

def insert_transaction(data_dict):
    """Insert data transaksi ke Supabase."""
    try:
        supabase.table("inventory").insert(data_dict).execute()
        return True
    except: return False

# ==========================================
# 3. SESSION STATE & LAPORAN WA
# ==========================================

if 'user' not in st.session_state: st.session_state.user = None
if 'report_wa' not in st.session_state: st.session_state.report_wa = ""

# ==========================================
# 4. HALAMAN LOGIN (DENGAN LOGO ATAS)
# ==========================================

if not st.session_state.user:
    # Centering Logo
    st.markdown('<div class="login-logo">', unsafe_allow_html=True)
    try:
        st.image(LOGO_IMAGE, width=180) # Sesuaikan lebar
    except:
        st.markdown("<h1 style='text-align:center;'>☕💀</h1>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align:center;'>LOGIN SISTEM GUDANG</h3>", unsafe_allow_html=True)
    
    with st.form("form_login"):
        role = st.selectbox("Role:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
        pw = st.text_input("Password:", type="password")
        if st.form_submit_button("MASUK SISTEM"):
            # PASSWORD JANGAN DIUMBAR DI SINI JIKA PRODUKSI!
            if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
                st.session_state.user = role
                st.rerun()
            else: st.error("Password Salah, Bjir!")

# ==========================================
# 5. HALAMAN UTAMA (DENGAN LOGO SIDEBAR)
# ==========================================

else:
    # --- LOGO DI SIDEBAR ---
    st.sidebar.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    try:
        st.sidebar.image(LOGO_IMAGE, width=150)
    except: pass
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    st.sidebar.markdown(f"User: **{st.session_state.user}**")
    st.sidebar.markdown(f"EST. 2019")
    
    # Ambil Data Terbaru
    df_summary, df_raw_history = get_stock_data()

    st.markdown(f"## 📦 Gudang: {st.session_state.user}")

    # --- NAVIGASI (STAFF vs OWNER) ---
    if st.session_state.user == "Owner":
        tab_list = ["📊 DATA", "📜 RIWAYAT", "➕ MASUK", "➖ KELUAR", "📱 WA"]
    else:
        tab_list = ["➕ MASUK", "➖ KELUAR", "📱 WA"]
    
    tabs = st.tabs(tab_list)

    # LOOPING LOGIKA TAB
    for i, tab in enumerate(tabs):
        current_tab = tab_list[i]

        with tab:
            if current_tab == "📊 DATA":
                if not df_summary.empty:
                    st.dataframe(df_summary, use_container_width=True, hide_index=True)
                else: st.info("Gudang kosong.")
                if st.button("🔄 REFRESH DATA"): st.rerun()

            elif current_tab == "📜 RIWAYAT":
                if not df_raw_history.empty:
                    # Rapihin format waktu
                    display_raw = df_raw_history.copy()
                    display_raw['waktu'] = pd.to_datetime(display_raw['waktu']).dt.strftime('%d/%m/%Y %H:%M')
                    st.dataframe(display_raw[['waktu', 'barang', 'jenis', 'jumlah', 'user_input']], use_container_width=True)
                else: st.info("Belum ada riwayat.")

            elif current_tab == "➕ MASUK":
                with st.form("form_masuk", clear_on_submit=True):
                    st.subheader("Update Stok / Tambah Barang Baru")
                    # Mode Input: Baru atau Update
                    mode = st.radio("Metode:", ["Baru", "Update Stok Lama"], horizontal=True) if not df_summary.empty else "Baru"
                    
                    if mode == "Baru":
                        nm = st.text_input("Ketik Nama Barang Baru:").upper().strip()
                        kt = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                        stn = st.selectbox("Satuan:", ["pack", "pcs", "box", "gram", "kg"])
                    else:
                        nm = st.selectbox("Pilih Barang:", df_summary['Barang'].unique())
                        # Ambil info satuan/kategori
                        info = df_summary[df_summary['Barang'] == nm].iloc[0]
                        kt, stn = info['Kategori'], info['Satuan']
                        st.info(f"Kategori: {kt}, Satuan: {stn}")
                    
                    jml = st.number_input("Jumlah Tambahan:", min_value=1)
                    if st.form_submit_button("SIMPAN DATA MASUK"):
                        if nm and jml > 0:
                            data_dict = {
                                "barang": nm, "kategori": kt, "satuan": stn, 
                                "jumlah": jml, "jenis": "MASUK", "user_input": st.session_state.user
                            }
                            if insert_transaction(data_dict):
                                st.session_state.report_wa += f"• {nm}: +{jml} {stn}\n"
                                st.success(f"Berhasil: {nm} ditambahkan!")
                                st.rerun()
                        else: st.error("Isi data yang bener!")

            elif current_tab == "➖ KELUAR":
                if not df_summary.empty:
                    with st.form("form_keluar", clear_on_submit=True):
                        st.subheader("Catat Barang Keluar")
                        sel_brg = st.selectbox("Cari Barang:", df_summary['Barang'].unique())
                        
                        # Info Sisa Stok
                        row_info = df_summary[df_summary['Barang'] == sel_brg].iloc[0]
                        sisa = row_info['Sisa Stok']
                        stn_o = row_info['Satuan']
                        
                        st.warning(f"Sisa Stok Saat Ini: {sisa} {stn_o}")
                        
                        # Validasi Input (Jumlah Keluar gak boleh lebih dari sisa)
                        max_out = int(sisa) if sisa > 0 else 1
                        jml_o = st.number_input("Jumlah Keluar:", min_value=1, max_value=max_out)
                        
                        if st.form_submit_button("KONFIRMASI BARANG KELUAR"):
                            if sisa >= jml_o > 0:
                                # Keluar gak perlu kategori/satuan baru, pake yang lama
                                data_dict = {
                                    "barang": sel_brg, "jumlah": jml_o, "jenis": "KELUAR", 
                                    "user_input": st.session_state.user, "kategori": row_info['Kategori'], "satuan": stn_o
                                }
                                if insert_transaction(data_dict):
                                    st.session_state.report_wa += f"• {sel_brg}: -{jml_o} {stn_o}\n"
                                    st.success("Tercatat Keluar!")
                                    st.rerun()
                            else: st.error("Stok gak cukup, bjir!")
                else: st.error("Gudang kosong, gak ada barang keluar.")

            elif current_tab == "WA":
                st.subheader("Laporan Aktivitas ke WA")
                if st.session_state.report_wa:
                    msg = f"*LAPORAN GUDANG THANKS.EPIDEMi!*\nUser: {st.session_state.user}\n---\n{st.session_state.report_wa}"
                    st.text_area("Preview Draft WA:", msg, height=150)
                    # Encode URL WA
                    url_wa = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                    # Button Kustom WA
                    st.markdown(f'<a href="{url_wa}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:15px;border-radius:10px;text-align:center;font-weight:bold;">📲 KIRIM LAPORAN WA</div></a>', unsafe_allow_html=True)
                    if st.button("Reset Laporan"): st.session_state.report_wa = ""; st.rerun()
                else: st.info("Belum ada transaksi hari ini.")

    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        st.rerun()
