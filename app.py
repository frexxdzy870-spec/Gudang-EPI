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

st.set_page_config(page_title="THANKS.EPIDEMi!", layout="centered")

# CSS: Dark Mode & Center
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
                else: st.error("Salah password!")

# ==========================================
# 4. HALAMAN UTAMA
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
                with st.form("form_in", clear_on_submit=True):
                    st.subheader("Update Stok / Barang Baru")
                    
                    # LIST BARANG UNTUK SELECTION
                    list_barang = ["+ TAMBAH BARANG BARU"]
                    if not df_summary.empty:
                        list_barang += sorted(df_summary['Barang'].tolist())
                    
                    pilihan = st.selectbox("Pilih atau Input Barang:", list_barang)
                    
                    # LOGIKA DINAMIS: Kalau pilih "+ TAMBAH BARANG BARU" muncul input manual
                    if pilihan == "+ TAMBAH BARANG BARU":
                        nm = st.text_input("Nama Barang Baru:").upper().strip()
                        kt = st.selectbox("Kategori:", ["BAR", "KITCHEN", "STATIONERY", "OTHER"])
                        stn = st.selectbox("Satuan:", ["pack", "pcs", "box", "gram", "kg", "liter"])
                    else:
                        nm = pilihan
                        # Ambil info kategori & satuan dari barang yang sudah ada
                        data_lama = df_summary[df_summary['Barang'] == nm].iloc[0]
                        kt, stn = data_lama['Kategori'], data_lama['Satuan']
                        st.info(f"Update stok untuk: **{nm}** ({kt} - {stn})")
                    
                    jml = st.number_input("Jumlah Tambahan:", min_value=1)
                    
                    if st.form_submit_button("SIMPAN DATA"):
                        if nm:
                            supabase.table("inventory").insert({
                                "barang": nm, "kategori": kt, "satuan": stn, 
                                "jumlah": jml, "jenis": "MASUK", "user_input": st.session_state.user
                            }).execute()
                            st.session_state.report_wa += f"• {nm}: +{jml} {stn}\n"
                            st.success(f"Berhasil: {nm} +{jml}")
                            st.rerun()
                        else: st.error("Isi Nama Barang dulu!")

            elif label == "➖ KELUAR":
                if not df_summary.empty:
                    with st.form("form_out"):
                        sel = st.selectbox("Pilih Barang Keluar:", df_summary['Barang'].unique())
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
                st.text_area("Laporan Hari Ini:", st.session_state.report_wa, height=200)
                if st.button("Kirim ke WhatsApp"):
                    url = f"https://wa.me/?text={urllib.parse.quote(st.session_state.report_wa)}"
                    st.markdown(f'[KLIK DI SINI UNTUK KIRIM WA]({url})')

    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        st.rerun()
