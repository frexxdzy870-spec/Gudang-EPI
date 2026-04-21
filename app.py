import streamlit as st
from supabase import create_client
import pandas as pd
import urllib.parse

# ==========================================
# 1. SETUP
# ==========================================
SUPABASE_URL = "ISI_URL_LU"
SUPABASE_KEY = "ISI_KEY_LU"
LOGO_URL = "https://raw.githubusercontent.com/username/repo/main/logo.png"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

st.set_page_config(page_title="THANKS.EPIDEMi! Gudang", layout="centered")

# CSS Fix: Paksa Logo Tengah & Warna Terang
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    [data-testid="stImage"] { display: block; margin-left: auto; margin-right: auto; }
    h1, h2, h3, h4, p, label { color: #FFFFFF !important; text-align: center; }
    .stButton>button { width: 100%; background-color: #FFFFFF !important; color: #000000 !important; font-weight: bold; border-radius: 8px; }
    div[data-testid="stForm"] { border: 1px solid #444; border-radius: 10px; padding: 25px; background-color: #161922; }
    </style>
""", unsafe_allow_html=True)

# Inisialisasi awal
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
            masuk = b_df[b_df['jenis'] == 'MASUK']['jumlah'].sum()
            keluar = b_df[b_df['jenis'] == 'KELUAR']['jumlah'].sum()
            row = b_df.iloc[0]
            summary.append({"Barang": b, "Kategori": row['kategori'], "Sisa Stok": masuk - keluar, "Satuan": row['satuan']})
        return pd.DataFrame(summary), df_raw
    except: return pd.DataFrame(), pd.DataFrame()

# ==========================================
# 3. HALAMAN LOGIN
# ==========================================
if st.session_state.user is None:
    st.write("##") 
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image(LOGO_URL, use_container_width=True)
    
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
                else: st.error("Password Salah!")

# ==========================================
# 4. HALAMAN UTAMA (DASHBOARD)
# ==========================================
else:
    # Logo Sidebar
    st.sidebar.image(LOGO_URL, use_container_width=True)
    st.sidebar.markdown(f"User: **{st.session_state.user}**")
    st.sidebar.markdown("---")
    
    df_summary, df_raw_history = get_stock_data()

    # Logika Penentuan Tab agar tidak hilang
    if st.session_state.user == "Owner":
        menu = ["📊 DATA", "📜 RIWAYAT", "➕ MASUK", "➖ KELUAR", "📱 WA"]
    else:
        menu = ["➕ MASUK", "➖ KELUAR", "📱 WA"]
    
    tabs = st.tabs(menu)

    for i, tab in enumerate(tabs):
        with tab:
            nama_tab = menu[i]
            
            if nama_tab == "📊 DATA":
                st.dataframe(df_summary, use_container_width=True, hide_index=True)
                if st.button("🔄 REFRESH"): st.rerun()

            elif nama_tab == "📜 RIWAYAT":
                st.dataframe(df_raw_history, use_container_width=True)

            elif nama_tab == "➕ MASUK":
                with st.form("in", clear_on_submit=True):
                    st.subheader("Input Barang")
                    nm = st.text_input("Nama Barang:").upper().strip()
                    jml = st.number_input("Jumlah:", min_value=1)
                    if st.form_submit_button("SIMPAN"):
                        supabase.table("inventory").insert({
                            "barang": nm, "jumlah": jml, "jenis": "MASUK", 
                            "user_input": st.session_state.user, "kategori": "BAR", "satuan": "pcs"
                        }).execute()
                        st.session_state.report_wa += f"• {nm}: +{jml}\n"
                        st.rerun()

            elif nama_tab == "➖ KELUAR":
                if not df_summary.empty:
                    with st.form("out"):
                        sel = st.selectbox("Pilih Barang:", df_summary['Barang'].unique())
                        jml_o = st.number_input("Jumlah Keluar:", min_value=1)
                        if st.form_submit_button("KELUARKAN"):
                            supabase.table("inventory").insert({
                                "barang": sel, "jumlah": jml_o, "jenis": "KELUAR", 
                                "user_input": st.session_state.user
                            }).execute()
                            st.session_state.report_wa += f"• {sel}: -{jml_o}\n"
                            st.rerun()

            elif nama_tab == "📱 WA":
                st.text_area("Draft Laporan:", st.session_state.report_wa)
                if st.button("Kirim WA"):
                    url = f"https://wa.me/?text={urllib.parse.quote(st.session_state.report_wa)}"
                    st.markdown(f'[KLIK DI SINI]({url})')

    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        st.rerun()
