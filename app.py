import streamlit as st
from supabase import create_client
import pandas as pd
import urllib.parse

# ==========================================
# 1. SETUP & KONEKSI
# ==========================================
SUPABASE_URL = "https://obrbnenfojqdepqzxain.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9icmJuZW5mb2pxZGVwcXp4YWluIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY2NDU2MDAsImV4cCI6MjA5MjIyMTYwMH0.Ef0uELb-CwYxlKpK_DggIrfX0NZDHiyEHTIcZmseyzk"
LOGO_URL = "https://raw.githubusercontent.com/username/repo/main/logo.png"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

st.set_page_config(page_title="THANKS.EPIDEMi!", layout="centered")

# CSS: Dark Mode & Center Logo
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    [data-testid="stImage"] { display: block; margin-left: auto; margin-right: auto; }
    h1, h2, h3, h4, p, label { color: #FFFFFF !important; text-align: center; }
    .stButton>button { width: 100%; background-color: #FFFFFF !important; color: #000000 !important; font-weight: bold; border-radius: 8px; }
    div[data-testid="stForm"] { border: 1px solid #444; border-radius: 10px; padding: 25px; background-color: #161922; }
    </style>
""", unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None
if 'report_wa' not in st.session_state: st.session_state.report_wa = ""

# ==========================================
# 2. DATA LOGIC (STOK REALTIME)
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
            summary.append({
                "Barang": b, "Kategori": row['kategori'], 
                "Sisa Stok": masuk - keluar, "Satuan": row['satuan']
            })
        return pd.DataFrame(summary), df_raw
    except: return pd.DataFrame(), pd.DataFrame()

# ==========================================
# 3. HALAMAN LOGIN
# ==========================================
if st.session_state.user is None:
    st.write("##") 
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2: st.image(LOGO_URL, use_container_width=True)
    st.markdown("### LOGIN SISTEM GUDANG")
    
    ca, cb, cc = st.columns([0.1, 0.8, 0.1])
    with cb:
        with st.form("form_login"):
            role = st.selectbox("Role:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
            pw = st.text_input("Password:", type="password")
            if st.form_submit_button("MASUK SISTEM"):
                if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
                    st.session_state.user = role
                    st.rerun()
                else: st.error("Salah!")

# ==========================================
# 4. HALAMAN UTAMA (MENU LENGKAP)
# ==========================================
else:
    st.sidebar.image(LOGO_URL, use_container_width=True)
    st.sidebar.write(f"Logged: **{st.session_state.user}**")
    
    df_summary, df_raw_history = get_stock_data()
    
    menu = ["📊 DATA", "📜 RIWAYAT", "➕ MASUK", "➖ KELUAR", "📱 WA"] if st.session_state.user == "Owner" else ["➕ MASUK", "➖ KELUAR", "📱 WA"]
    tabs = st.tabs(menu)

    for i, tab in enumerate(tabs):
        with tab:
            label = menu[i]
            
            if label == "📊 DATA":
                st.dataframe(df_summary, use_container_width=True, hide_index=True)
                if st.button("🔄 REFRESH"): st.rerun()

            elif label == "📜 RIWAYAT":
                st.dataframe(df_raw_history[['waktu', 'barang', 'jenis', 'jumlah', 'user_input']], use_container_width=True)

            elif label == "➕ MASUK":
                with st.form("in", clear_on_submit=True):
                    st.subheader("Update Stok / Barang Baru")
                    # FITUR UPDATE STOK LAMA VS BARU
                    mode = st.radio("Metode:", ["Input Barang Baru", "Update Stok Lama"], horizontal=True) if not df_summary.empty else "Input Barang Baru"
                    
                    if mode == "Input Barang Baru":
                        nm = st.text_input("Nama Barang:").upper().strip()
                        kt = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                        stn = st.selectbox("Satuan:", ["pack", "pcs", "box", "kg"])
                    else:
                        nm = st.selectbox("Pilih Barang:", df_summary['Barang'].unique())
                        # Ambil data lama biar otomatis
                        old_data = df_summary[df_summary['Barang'] == nm].iloc[0]
                        kt, stn = old_data['Kategori'], old_data['Satuan']
                        st.info(f"Kategori: {kt} | Satuan: {stn}")
                    
                    jml = st.number_input("Jumlah Masuk:", min_value=1)
                    if st.form_submit_button("SIMPAN DATA"):
                        if nm:
                            supabase.table("inventory").insert({
                                "barang": nm, "kategori": kt, "satuan": stn, 
                                "jumlah": jml, "jenis": "MASUK", "user_input": st.session_state.user
                            }).execute()
                            st.session_state.report_wa += f"• {nm}: +{jml} {stn}\n"
                            st.success("Tersimpan!")
                            st.rerun()

            elif label == "➖ KELUAR":
                if not df_summary.empty:
                    with st.form("out"):
                        sel = st.selectbox("Barang Keluar:", df_summary['Barang'].unique())
                        info = df_summary[df_summary['Barang'] == sel].iloc[0]
                        st.warning(f"Sisa Stok: {info['Sisa Stok']} {info['Satuan']}")
                        jml_o = st.number_input("Jumlah Keluar:", min_value=1, max_value=int(info['Sisa Stok']))
                        if st.form_submit_button("KELUARKAN"):
                            supabase.table("inventory").insert({
                                "barang": sel, "jumlah": jml_o, "jenis": "KELUAR", 
                                "user_input": st.session_state.user, "kategori": info['Kategori'], "satuan": info['Satuan']
                            }).execute()
                            st.session_state.report_wa += f"• {sel}: -{jml_o} {info['Satuan']}\n"
                            st.rerun()
                else: st.error("Gudang Kosong!")

            elif label == "📱 WA":
                st.text_area("Laporan:", st.session_state.report_wa, height=200)
                if st.button("Kirim ke Owner"):
                    url = f"https://wa.me/?text={urllib.parse.quote(st.session_state.report_wa)}"
                    st.markdown(f'[KLIK UNTUK KIRIM WA]({url})')

    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        st.rerun()
