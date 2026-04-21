import streamlit as st
from supabase import create_client
import pandas as pd
import urllib.parse

# 1. KONEKSI
SUPABASE_URL = "ISI_URL_LU"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9icmJuZW5mb2pxZGVwcXp4YWluIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY2NDU2MDAsImV4cCI6MjA5MjIyMTYwMH0.Ef0uELb-CwYxlKpK_DggIrfX0NZDHiyEHTIcZmseyzk"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Gudang Sahaja", layout="centered")

# CSS: Tampilan Dark & Elegan
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    h1, h2, h3, p, label { color: #FFFFFF !important; }
    .stButton>button { width: 100%; background-color: #FFFFFF !important; color: #000000 !important; font-weight: bold; }
    div[data-testid="stForm"] { border: 1px solid #444; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# 2. LOGIKA DATA (HITUNG STOK REALTIME)
def get_stock_data():
    try:
        res = supabase.table("inventory").select("*").execute()
        df = pd.DataFrame(res.data)
        if df.empty: return pd.DataFrame(), pd.DataFrame()
        
        # Hitung Sisa Stok
        summary = []
        for b in df['barang'].unique():
            b_df = df[df['barang'] == b]
            masuk = b_df[b_df['jenis'] == 'MASUK']['jumlah'].sum()
            keluar = b_df[b_df['jenis'] == 'KELUAR']['jumlah'].sum()
            row = b_df.iloc[0]
            summary.append({
                "Barang": b, "Kategori": row['kategori'], 
                "Stok": masuk - keluar, "Satuan": row['satuan']
            })
        return pd.DataFrame(summary), df.sort_values('waktu', ascending=False)
    except: return pd.DataFrame(), pd.DataFrame()

# 3. SESSION & LOGIN
if 'user' not in st.session_state: st.session_state.user = None
if 'report' not in st.session_state: st.session_state.report = ""

if not st.session_state.user:
    st.markdown("<h2 style='text-align:center;'>📦 LOGIN GUDANG</h2>", unsafe_allow_html=True)
    role = st.selectbox("Pilih Role:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
    pw = st.text_input("Password:", type="password")
    if st.button("MASUK"):
        if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
            st.session_state.user = role
            st.rerun()
        else: st.error("Salah password, bjir!")
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.user}**")
    df_stok, df_raw = get_stock_data()

    # 4. NAVIGASI (STAFF VS OWNER)
    if st.session_state.user == "Owner":
        tabs = st.tabs(["📊 DATA", "📜 RIWAYAT", "➕ MASUK", "➖ KELUAR", "📱 WA"])
    else:
        tabs = st.tabs(["➕ MASUK", "➖ KELUAR", "📱 WA"])

    # LOGIKA SETIAP TAB
    for i, tab in enumerate(tabs):
        t_label = ["DATA", "RIWAYAT", "MASUK", "KELUAR", "WA"] if st.session_state.user == "Owner" else ["MASUK", "KELUAR", "WA"]
        current = t_label[i]

        with tab:
            if current == "DATA":
                st.dataframe(df_stok, use_container_width=True, hide_index=True)
                if st.button("🔄 REFRESH"): st.rerun()

            elif current == "RIWAYAT":
                if not df_raw.empty:
                    st.dataframe(df_raw[['waktu', 'barang', 'jenis', 'jumlah', 'user_input']], use_container_width=True)
                else: st.info("Belum ada riwayat.")

            elif current == "MASUK":
                with st.form("form_masuk", clear_on_submit=True):
                    st.subheader("Tambah / Update Stok")
                    # Opsi: Pilih yang ada atau ketik baru
                    mode = st.radio("Tipe:", ["Baru", "Update Stok Lama"], horizontal=True) if not df_stok.empty else "Baru"
                    
                    if mode == "Baru":
                        nm = st.text_input("Nama Barang Baru:").upper()
                        kt = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                        stn = st.selectbox("Satuan:", ["pack", "pcs", "box", "gram", "kg"])
                    else:
                        nm = st.selectbox("Pilih Barang:", df_stok['Barang'].unique())
                        info = df_stok[df_stok['Barang'] == nm].iloc[0]
                        kt, stn = info['Kategori'], info['Satuan']
                    
                    jml = st.number_input("Jumlah:", min_value=1)
                    if st.form_submit_button("SIMPAN DATA"):
                        if nm:
                            supabase.table("inventory").insert({
                                "barang": nm, "kategori": kt, "satuan": stn, 
                                "jumlah": jml, "jenis": "MASUK", "user_input": st.session_state.user
                            }).execute()
                            st.session_state.report += f"• {nm}: +{jml} {stn}\n"
                            st.success(f"Berhasil: {nm} +{jml}")
                            st.rerun()

            elif current == "KELUAR":
                if not df_stok.empty:
                    with st.form("form_keluar", clear_on_submit=True):
                        st.subheader("Barang Keluar")
                        sel_brg = st.selectbox("Pilih Barang:", df_stok['Barang'].unique())
                        sisa = df_stok[df_stok['Barang'] == sel_brg].iloc[0]['Stok']
                        stn_o = df_stok[df_stok['Barang'] == sel_brg].iloc[0]['Satuan']
                        st.warning(f"Sisa stok saat ini: {sisa} {stn_o}")
                        
                        jml_o = st.number_input("Jumlah Keluar:", min_value=1, max_value=int(sisa) if sisa > 0 else 1)
                        if st.form_submit_button("KELUARKAN"):
                            if sisa >= jml_o:
                                supabase.table("inventory").insert({
                                    "barang": sel_brg, "jumlah": jml_o, "jenis": "KELUAR", 
                                    "user_input": st.session_state.user, "kategori": "-", "satuan": stn_o
                                }).execute()
                                st.session_state.report += f"• {sel_brg}: -{jml_o} {stn_o}\n"
                                st.success("Data Keluar Dicatat!")
                                st.rerun()
                            else: st.error("Stok gak cukup!")
                else: st.error("Gudang kosong, gak ada yang bisa keluar.")

            elif current == "WA":
                if st.session_state.report:
                    msg = f"*LAPORAN GUDANG*\nUser: {st.session_state.user}\n---\n{st.session_state.report}"
                    st.text_area("Preview:", msg, height=150)
                    st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:15px;border-radius:10px;text-align:center;font-weight:bold;">📲 KIRIM KE WHATSAPP</div></a>', unsafe_allow_html=True)
                    if st.button("Hapus Laporan"): st.session_state.report = ""; st.rerun()
                else: st.info("Belum ada aktivitas.")

    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        st.rerun()
