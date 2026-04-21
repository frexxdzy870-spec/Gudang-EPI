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

st.set_page_config(page_title="THANKS.EPIDEMi!", layout="centered")

st.markdown("""
    <style>
    /* 1. Background & Dasar */
    .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    /* 2. Navigasi TABS - Efek Gradasi Transparan */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
        padding: 10px 0;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: rgba(0, 0, 0, 0.03); /* Hitam sangat tipis */
        color: #444444;
        border-radius: 12px;
        padding: 10px 25px;
        border: 1px solid rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }

    /* Tampilan Pas Tab Dipilih (SINKRON & GRADASI) */
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.6) 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
        border: none !important;
        transform: translateY(-2px);
    }

    /* 3. Container & Form */
    div[data-testid="stForm"] {
        border: none;
        border-radius: 20px;
        background: rgba(255, 255, 255, 1);
        box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.08); /* Shadow halus */
        padding: 30px;
    }

    /* 4. Input Fields */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input {
        background-color: rgba(0, 0, 0, 0.02) !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 10px !important;
        color: #000000 !important;
    }

    /* 5. Tombol Submit - Gradasi */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #000000 0%, #333333 100%) !important;
        color: #FFFFFF !important;
        border-radius: 10px;
        border: none;
        font-weight: 600;
        height: 3.5em;
        transition: 0.3s;
    }

    .stButton>button:hover {
        opacity: 0.8;
        box-shadow: 0px 5px 15px rgba(0,0,0,0.3);
    }

    /* 6. Sidebar & Lainnya */
    [data-testid="stSidebar"] {
        background-color: #FAFAFA;
    }
    
    h1, h2, h3, label {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    
    /* Alert/Error Box biar gak kontras banget */
    .stAlert {
        border-radius: 10px;
        background-color: rgba(255, 0, 0, 0.05);
        color: #cc0000;
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
    st.markdown("### LOGIN SISTEM")
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
    menu = ["📊 DATA", "📜 RIWAYAT", "➕ MASUK", "➖ KELUAR", "📱 WA"] if st.session_state.user == "Owner" else ["➕ MASUK", "➖ KELUAR", "📱 WA"]
    tabs = st.tabs(menu)

    for i, tab in enumerate(tabs):
        with tab:
            label = menu[i]
            
            if label == "➕ MASUK":
                # KUNCI SINKRONISASI DI SINI
                st.subheader("Update Stok / Tambah Barang")
                
                # Sediakan daftar barang yang sudah ada
                list_barang = ["+ TAMBAH BARANG BARU"]
                if not df_summary.empty:
                    list_barang += sorted(df_summary['Barang'].tolist())
                
                # Gunakan key pada selectbox agar state-nya terjaga
                pilihan = st.selectbox("Cari Barang:", list_barang, key="pilih_barang_masuk")
                
                with st.form("form_update_masuk", clear_on_submit=True):
                    if pilihan == "+ TAMBAH BARANG BARU":
                        nm = st.text_input("Nama Barang Baru:").upper().strip()
                        kt = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                        stn = st.selectbox("Satuan:", ["pack", "pcs", "box", "kg"])
                    else:
                        nm = pilihan
                        # Cari data pendukung secara otomatis
                        row = df_summary[df_summary['Barang'] == nm].iloc[0]
                        kt, stn = row['Kategori'], row['Satuan']
                        st.markdown(f"📦 **{nm}** | Kategori: `{kt}` | Satuan: `{stn}`")
                    
                    jml = st.number_input("Jumlah Tambahan:", min_value=1)
                    
                    if st.form_submit_button("SIMPAN DATA"):
                        if nm:
                            supabase.table("inventory").insert({
                                "barang": nm, "kategori": kt, "satuan": stn, 
                                "jumlah": jml, "jenis": "MASUK", "user_input": st.session_state.user
                            }).execute()
                            st.session_state.report_wa += f"• {nm}: +{jml} {stn}\n"
                            st.success(f"Berhasil update {nm}!")
                            st.rerun()
                        else: st.error("Isi nama barangnya!")

            elif label == "📊 DATA":
                st.dataframe(df_summary, use_container_width=True, hide_index=True)

            elif label == "📜 RIWAYAT":
                st.dataframe(df_raw_history[['waktu', 'barang', 'jenis', 'jumlah', 'user_input']], use_container_width=True)

            elif label == "➖ KELUAR":
                if not df_summary.empty:
                    with st.form("out"):
                        sel = st.selectbox("Barang Keluar:", df_summary['Barang'].unique())
                        info = df_summary[df_summary['Barang'] == sel].iloc[0]
                        st.warning(f"Stok: {info['Sisa Stok']} {info['Satuan']}")
                        jml_o = st.number_input("Jumlah:", min_value=1, max_value=int(info['Sisa Stok']))
                        if st.form_submit_button("KELUARKAN"):
                            supabase.table("inventory").insert({
                                "barang": sel, "jumlah": jml_o, "jenis": "KELUAR", 
                                "user_input": st.session_state.user, "kategori": info['Kategori'], "satuan": info['Satuan']
                            }).execute()
                            st.session_state.report_wa += f"• {sel}: -{jml_o} {info['Satuan']}\n"
                            st.rerun()

            elif label == "📱 WA":
                st.text_area("Draft:", st.session_state.report_wa)
                if st.button("Kirim WA"):
                    url = f"https://wa.me/?text={urllib.parse.quote(st.session_state.report_wa)}"
                    st.markdown(f'[KLIK DI SINI]({url})')

    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        st.rerun()
