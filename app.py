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
