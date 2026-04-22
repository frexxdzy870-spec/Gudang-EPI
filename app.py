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

    for i, tab in enumerate(tabs):
        with tab:
            label = menu[i]
            
            if label == "DATA":
                st.dataframe(df_summary, use_container_width=True)

            elif label == "RIWAYAT":
                st.dataframe(df_raw_history, use_container_width=True)

           elif label == "MASUK":  # <--- SEJAJARIN SAMA IF/ELIF DI ATASNYA
                st.subheader("Update Stok / Tambah Barang")
                elif label == "➕ MASUK":
                st.subheader("Update Stok / Tambah Barang")
                
                # List barang yang sudah ada untuk fitur pencarian
                list_barang = ["+ TAMBAH BARANG BARU"]
                if not df_summary.empty:
                    # Diurutkan abjad biar makin gampang dicarinya
                    list_barang += sorted(df_summary['Barang'].tolist())
                
                # Fitur Search Otomatis ada di sini (tinggal ketik di dalam box)
                pilihan = st.selectbox(
                    "Cari Nama Barang (Ketik untuk mencari):", 
                    list_barang, 
                    key="search_barang_masuk",
                    help="Ketik nama barang untuk mempercepat pencarian"
                )
                
                with st.form("form_update_masuk", clear_on_submit=True):
                    if pilihan == "+ TAMBAH BARANG BARU":
                        nm = st.text_input("Nama Barang Baru:").upper().strip()
                        col1, col2 = st.columns(2)
                        with col1:
                            kt = st.selectbox("Kategori:", ["BAR", "KITCHEN", "STATIONERY", "OTHER"])
                        with col2:
                            stn = st.selectbox("Satuan:", ["pack", "pcs", "box", "gram", "kg", "liter"])
                    else:
                        nm = pilihan
                        # Cari data pendukung secara otomatis
                        row = df_summary[df_summary['Barang'] == nm].iloc[0]
                        kt, stn = row['Kategori'], row['Satuan']
                        
                        # Info Ringkas Barang yang dipilih
                        st.markdown(f"""
                        <div style="background-color: rgba(0,0,0,0.05); padding: 10px; border-radius: 10px; border-left: 5px solid #000;">
                            <p style="margin:0; text-align:left;">📦 <b>Barang:</b> {nm}</p>
                            <p style="margin:0; text-align:left;">🏷️ <b>Kategori:</b> {kt} | 📏 <b>Satuan:</b> {stn}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.write("##") # Spasi
                    
                    jml = st.number_input("Jumlah Tambahan:", min_value=1)
                    
                    if st.form_submit_button("SIMPAN DATA"):
                        if nm:
                            supabase.table("inventory").insert({
                                "barang": nm, "kategori": kt, "satuan": stn, 
                                "jumlah": jml, "jenis": "MASUK", "user_input": st.session_state.user
                            }).execute()
                            # Update report WA
                            st.session_state.report_wa += f"• {nm}: +{jml} {stn}\n"
                            st.success(f"Berhasil update {nm}!")
                            st.rerun()
                        else:
                            st.error("Nama barang tidak boleh kosong!")
           elif label == "KELUAR":
                # ... kode keluar ...
             
           elif label == "MASUK":
                st.subheader("Update Stok / Tambah Barang")
                
                # List barang yang sudah ada untuk fitur pencarian
                list_barang = ["+ TAMBAH BARANG BARU"]
                if not df_summary.empty:
                    # Diurutkan abjad biar makin gampang dicarinya
                    list_barang += sorted(df_summary['Barang'].tolist())
                
                # Fitur Search Otomatis ada di sini (tinggal ketik di dalam box)
                pilihan = st.selectbox(
                    "Cari Nama Barang (Ketik untuk mencari):", 
                    list_barang, 
                    key="search_barang_masuk",
                    help="Ketik nama barang untuk mempercepat pencarian"
                )
                
                with st.form("form_update_masuk", clear_on_submit=True):
                    if pilihan == "+ TAMBAH BARANG BARU":
                        nm = st.text_input("Nama Barang Baru:").upper().strip()
                        col1, col2 = st.columns(2)
                        with col1:
                            kt = st.selectbox("Kategori:", ["BAR", "KITCHEN", "STATIONERY", "OTHER"])
                        with col2:
                            stn = st.selectbox("Satuan:", ["pack", "pcs", "box", "gram", "kg", "liter"])
                    else:
                        nm = pilihan
                        # Cari data pendukung secara otomatis
                        row = df_summary[df_summary['Barang'] == nm].iloc[0]
                        kt, stn = row['Kategori'], row['Satuan']
                        
                        # Info Ringkas Barang yang dipilih
                        st.markdown(f"""
                        <div style="background-color: rgba(0,0,0,0.05); padding: 10px; border-radius: 10px; border-left: 5px solid #000;">
                            <p style="margin:0; text-align:left;">📦 <b>Barang:</b> {nm}</p>
                            <p style="margin:0; text-align:left;">🏷️ <b>Kategori:</b> {kt} | 📏 <b>Satuan:</b> {stn}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.write("##") # Spasi
                    
                    jml = st.number_input("Jumlah Tambahan:", min_value=1)
                    
                    if st.form_submit_button("SIMPAN DATA"):
                        if nm:
                            supabase.table("inventory").insert({
                                "barang": nm, "kategori": kt, "satuan": stn, 
                                "jumlah": jml, "jenis": "MASUK", "user_input": st.session_state.user
                            }).execute()
                            # Update report WA
                            st.session_state.report_wa += f"• {nm}: +{jml} {stn}\n"
                            st.success(f"Berhasil update {nm}!")
                            st.rerun()
                        else:
                            st.error("Nama barang tidak boleh kosong!")

            elif label == "DATA":
                st.dataframe(df_summary, use_container_width=True, hide_index=True)

            elif label == "RIWAYAT":
                st.dataframe(df_raw_history[['waktu', 'barang', 'jenis', 'jumlah', 'user_input']], use_container_width=True)

            elif label == "KELUAR":
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

            elif label == "LAPORAN":
                st.text_area("Draft:", st.session_state.report_wa)
                if st.button("Kirim WA"):
                    url = f"https://wa.me/?text={urllib.parse.quote(st.session_state.report_wa)}"
                    st.markdown(f'[KLIK DI SINI]({url})')

    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        st.rerun()
