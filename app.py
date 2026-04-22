import streamlit as st
from supabase import create_client
import pandas as pd
import urllib.parse

# ==========================================
# 1. SETUP
# ==========================================
SUPABASE_URL = "https://obrbnenfojqdepqzxain.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9icmJuZW5mb2pxZGVwcXp4YWluIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY2NDU2MDAsImV4cCI6MjA5MjIyMTYwMH0.Ef0uELb-CwYxlKpK_DggIrfX0NZDHiyEHTIcZmseyzk"
LOGO_URL = "https://github.com/frexxdzy870-spec/Gudang-EPI/blob/main/logo.png.jpg?raw=true"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

st.set_page_config(page_title="Gudang Epidemi", layout="centered")

# --- INISIALISASI SESSION STATE (Taruh paling atas setelah import) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'report_wa' not in st.session_state:
    st.session_state.report_wa = ""

st.markdown("""
    <style>
    /* 1. Background Utama */
    .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    /* 2. SIDEBAR GRADASI & LOGO */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #000000 0%, #222222 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    /* Bikin teks di sidebar (kecuali tombol) tetep putih biar kelihatan */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
    }

    /* Logo Center di Sidebar */
    [data-testid="stSidebar"] [data-testid="stImage"] {
        filter: drop-shadow(0px 0px 10px rgba(255,255,255,0.2));
        margin-bottom: 20px;
    }

    /* 3. TOMBOL LOGOUT (SIDEBAR) */
    [data-testid="stSidebar"] .stButton>button {
        background: rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important; /* Teks Putih */
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 10px;
        font-weight: 600;
        transition: 0.3s;
    }

    [data-testid="stSidebar"] .stButton>button:hover {
        background: rgba(255, 0, 0, 0.6) !important; /* Merah transparan pas hover biar dapet feel "exit" */
        border-color: #FF4B4B !important;
    }

    /* 4. TABS NAVIGASI - Gradasi Transparan */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: rgba(0, 0, 0, 0.03);
        color: #444444;
        border-radius: 12px;
        padding: 10px 25px;
        border: 1px solid rgba(0, 0, 0, 0.05);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.6) 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
    }

    /* 5. KOTAK INPUT (NAMA, JUMLAH, KATEGORI, SATUAN) */
    .stTextInput>div>div>input, 
    .stSelectbox>div>div, 
    .stNumberInput>div>div>input,
    .stTextArea>div>div>textarea {
        background-color: transparent !important;
        color: #000000 !important;
        border: 1.5px solid #EEEEEE !important;
        border-radius: 10px !important;
    }

    /* Label & Teks Hitam */
    label, [data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    /* 6. Tombol Submit (Main) */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #000000 0%, #333333 100%) !important;
        color: #FFFFFF !important;
        border-radius: 10px;
        border: none;
        height: 3.5em;
    }

    /* Container Form */
    div[data-testid="stForm"] {
        border: none;
        border-radius: 20px;
        background: #FFFFFF;
        box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.05);
        padding: 30px;
    }
    </style>
""", unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None
if 'report_wa' not in st.session_state: st.session_state.report_wa = ""

# ==========================================
# 2. DATA LOGIC
# ==========================================
def get_stock_data():
    try:
        res = supabase.table("inventory").select("*").execute()
        df = pd.DataFrame(res.data)
        if df.empty: return pd.DataFrame(), pd.DataFrame()
        df_raw = df.sort_values('waktu', ascending=False)
        summary = []
        for b in df['barang'].unique():
            b_df = df[df['barang'] == b]
            summary.append({
                "Barang": b, "Kategori": b_df.iloc[0]['kategori'], 
                "Sisa Stok": b_df[b_df['jenis'] == 'MASUK']['jumlah'].sum() - b_df[b_df['jenis'] == 'KELUAR']['jumlah'].sum(), 
                "Satuan": b_df.iloc[0]['satuan']
            })
        return pd.DataFrame(summary), df_raw
    except: return pd.DataFrame(), pd.DataFrame()

# ==========================================
# 3. LOGIN & MAIN APP
# ==========================================
if st.session_state.user is None:
    st.write("##")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2: st.image(LOGO_URL, use_container_width=True)
    st.markdown("### LOGIN")
    with st.form("login"):
        role = st.selectbox("Role:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
        pw = st.text_input("Password:", type="password")
        if st.form_submit_button("MASUK"):
            if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
                st.session_state.user = role
                st.rerun()
            else: st.error("Salah!")

else:
    st.sidebar.image(LOGO_URL, use_container_width=True)
    df_summary, df_raw_history = get_stock_data()
    menu = ["DATA", "RIWAYAT", "MASUK", "KELUAR", "LAPORAN"] if st.session_state.user == "Owner" else ["MASUK", "KELUAR", "LAPORAN"]
    tabs = st.tabs(menu)

  # Loop Tabs
    for i, tab in enumerate(tabs):
        with tab:
            label = menu[i]
            
            # 1. TAB DATA
            if label == "DATA":
                if not df_summary.empty:
                    st.dataframe(df_summary, use_container_width=True, hide_index=True)
                else:
                    st.info("Gudang kosong.")

            # 2. TAB RIWAYAT
            elif label == "RIWAYAT":
                if not df_raw_history.empty:
                    kolom_tersedia = df_raw_history.columns.tolist()
                    kolom_target = ['waktu', 'barang', 'jenis', 'jumlah', 'user_input']
                    kolom_fix = [c for c in kolom_target if c in kolom_tersedia]
                    st.dataframe(df_raw_history[kolom_fix], use_container_width=True)
                else:
                    st.info("Belum ada riwayat.")

            # 3. TAB MASUK (SINKRON & SEARCH)
            elif label == "MASUK":
                st.subheader("Update Stok / Tambah Barang")
                list_barang = ["+ TAMBAH BARANG BARU"]
                if not df_summary.empty:
                    list_barang += sorted(df_summary['Barang'].tolist())
                
                # Input Selection di luar form biar sinkron
                pilihan = st.selectbox("Cari Barang:", list_barang, key="cari_brg")
                
                with st.form("form_in", clear_on_submit=True):
                    if pilihan == "+ TAMBAH BARANG BARU":
                        nm = st.text_input("Nama Barang Baru:").upper().strip()
                        c1, c2 = st.columns(2)
                        with c1:
                            kt = st.selectbox("Kategori:", ["BAR", "KITCHEN", "STATIONERY", "OTHER"])
                        with c2:
                            stn = st.selectbox("Satuan:", ["pack", "pcs", "box", "gram", "kg", "liter"])
                    else:
                        nm = pilihan
                        row = df_summary[df_summary['Barang'] == nm].iloc[0]
                        kt, stn = row['Kategori'], row['Satuan']
                        st.info(f"Update: {nm} ({kt} - {stn})")
                    
                    jml = st.number_input("Jumlah:", min_value=1)
                    if st.form_submit_button("SIMPAN"):
                        if nm:
                            supabase.table("inventory").insert({
                                "barang": nm, "kategori": kt, "satuan": stn, 
                                "jumlah": jml, "jenis": "MASUK", "user_input": st.session_state.user
                            }).execute()
                            st.session_state.report_wa += f"• {nm}: +{jml} {stn}\n"
                            st.success("Tersimpan!")
                            st.rerun()

           # 4. TAB KELUAR
            elif label == "KELUAR":
                if not df_summary.empty:
                    with st.form("form_out", clear_on_submit=True):
                        sel = st.selectbox("Pilih Barang:", df_summary['Barang'].unique())
                        info = df_summary[df_summary['Barang'] == sel].iloc[0]
                        
                        # HANYA OWNER YANG BISA LIHAT STOK (Sembunyiin buat Staff)
                        if st.session_state.user == "owner":
                            st.warning(f"Stok Saat Ini: {info['Sisa Stok']} {info['Satuan']}")
                        
                        jml_o = st.number_input("Jumlah Keluar:", min_value=1)
                        
                        if st.form_submit_button("KELUARKAN"):
                            # Cek stok dulu biar nggak minus (validasi internal tetap jalan)
                            if jml_o > int(info['Sisa Stok']):
                                st.error(f"Gagal! Stok tidak cukup (Tersedia: {info['Sisa Stok']})")
                            else:
                                supabase.table("inventory").insert({
                                    "barang": sel, "jumlah": jml_o, "jenis": "KELUAR", 
                                    "user_input": st.session_state.user, 
                                    "kategori": info['Kategori'], "satuan": info['Satuan']
                                }).execute()
                                
                                # Update report WA format tabel
                                nama_b = (sel[:12] + '..') if len(sel) > 12 else sel.ljust(14)
                                st.session_state.report_wa += f"| {nama_b} | -{str(jml_o).ljust(3)} | {info['Satuan'].ljust(5)} |\n"
                                
                                st.success(f"Berhasil mengeluarkan {sel}")
                                st.rerun()

# 5. TAB WA (REVISI FIX - NO BLANK)
            elif label == "LAPORAN":
                st.subheader("Kirim Laporan Grup")
                
                # Cek dulu apakah session_state report_wa sudah ada
                if 'report_wa' not in st.session_state:
                    st.session_state.report_wa = ""
                
                # Header Tabel untuk WA biar kayak Excel
                header = "*REKAP STOK EPIDEMI*\n"
                header += "```\n"
                header += "+----------------+-----+-------+\n"
                header += "| Nama Barang    | Qty | Sat   |\n"
                header += "+----------------+-----+-------+\n"
                
                # Isi data
                body = st.session_state.report_wa if st.session_state.report_wa else "  (Belum ada data transaksi)  \n"
                
                footer = "+----------------+-----+-------+```"
                
                full_report = header + body + footer
                
                # Tampilkan Preview
                st.text_area("Preview Laporan:", full_report, height=250)
                
                # Kolom Tombol
                col_a, col_b = st.columns(2)
                
                with col_a:
                    import urllib.parse
                    pesan_wa = urllib.parse.quote(full_report)
                    # Tombol WA Estetik
                    st.markdown(f'''
                        <a href="https://wa.me/?text={pesan_wa}" target="_blank" style="text-decoration:none;">
                            <div style="background-color:#25D366; color:white; padding:10px; border-radius:10px; text-align:center; font-weight:bold; cursor:pointer;">
                                KIRIM KE WHATSAPP
                            </div>
                        </a>
                    ''', unsafe_allow_html=True)
                
                with col_b:
                    if st.button("RESET DRAFT", use_container_width=True):
                        st.session_state.report_wa = ""
                        st.rerun()

# --- AREA SIDEBAR (TARUH DI LUAR LOOP TABS) ---
# --- AREA SIDEBAR ---
with st.sidebar:
    # Tampilkan Logo (Bisa ditaruh di sini biar selalu ada)
    # st.image("logo.png") 

    # CEK APAKAH USER SUDAH LOGIN?
    if st.session_state.authenticated:
        st.write(f"Logged in as: **{st.session_state.user.upper()}**")
        st.write("---")
        
        # Tombol Logout cuma muncul kalau sudah login
        if st.button("LOGOUT", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
    else:
        # Kalau belum login, sidebar dikosongin aja atau kasih teks selamat datang
        st.info("Silahkan login di menu utama.")
