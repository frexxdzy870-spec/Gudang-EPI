import streamlit as st
from supabase import create_client
import pandas as pd
import urllib.parse

# ==========================================
# 1. SETUP & KONFIGURASI
# ==========================================
SUPABASE_URL = "https://obrbnenfojqdepqzxain.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9icmJuZW5mb2pxZGVwcXp4YWluIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY2NDU2MDAsImV4cCI6MjA5MjIyMTYwMH0.Ef0uELb-CwYxlKpK_DggIrfX0NZDHiyEHTIcZmseyzk"
LOGO_URL = "https://raw.githubusercontent.com/username/repo/main/logo.png"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

st.set_page_config(page_title="THANKS.EPIDEMi! Gudang", layout="centered")

# CSS Buat Paksa Tampilan Dark & Rapih
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    [data-testid="stImage"] { display: block; margin-left: auto; margin-right: auto; }
    h1, h2, h3, h4, p, label { color: #FFFFFF !important; text-align: center; }
    .stButton>button { width: 100%; background-color: #FFFFFF !important; color: #000000 !important; font-weight: bold; border-radius: 8px; }
    div[data-testid="stForm"] { border: 1px solid #444; border-radius: 10px; padding: 25px; background-color: #161922; }
    </style>
""", unsafe_allow_html=True)

# FIX ERROR: Inisialisasi session state biar gak AttributeError
if 'user' not in st.session_state:
    st.session_state.user = None
if 'report_wa' not in st.session_state:
    st.session_state.report_wa = ""

# ==========================================
# 2. LOGIKA DATA
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
            masuk = b_df[b_df['jenis'] == 'MASUK']['jumlah'].sum()
            keluar = b_df[b_df['jenis'] == 'KELUAR']['jumlah'].sum()
            row = b_df.iloc[0]
            summary.append({"Barang": b, "Kategori": row['kategori'], "Sisa Stok": masuk - keluar, "Satuan": row['satuan']})
        return pd.DataFrame(summary), df_raw
    except: return pd.DataFrame(), pd.DataFrame()

# ==========================================
# 3. HALAMAN LOGIN (FIX CENTER)
# ==========================================
if st.session_state.user is None:
    st.write("##") 
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        try:
            st.image(LOGO_URL, use_container_width=True)
        except:
            st.markdown("<h1 style='text-align:center;'>💀</h1>", unsafe_allow_html=True)
    
    st.markdown("### LOGIN SISTEM GUDANG")
    
    col_a, col_b, col_c = st.columns([0.1, 0.8, 0.1])
    with col_b:
        with st.form("form_login"):
            role = st.selectbox("Role:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
            pw = st.text_input("Password:", type="password")
            if st.form_submit_button("MASUK SISTEM"):
                if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
                    st.session_state.user = role
                    st.rerun()
                else:
                    st.error("Password Salah!")

# ==========================================
# 4. HALAMAN UTAMA
# ==========================================
else:
    st.sidebar.image(LOGO_URL, use_container_width=True)
    st.sidebar.markdown(f"User: **{st.session_state.user}**")
    st.sidebar.markdown("---")
    
    df_summary, df_raw_history = get_stock_data()
    tabs = st.tabs(["📊 DATA", "📜 RIWAYAT", "➕ MASUK", "➖ KELUAR", "📱 WA"]) if st.session_state.user == "Owner" else st.tabs(["➕ MASUK", "➖ KELUAR", "📱 WA"])
    # ... (Sisa kode menu lu taruh di sini sesuai tab)
    
    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        st.rerun()
