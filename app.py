import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. KONFIGURASI SUPABASE (Ganti pake punya lu!)
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9icmJuZW5mb2pxZGVwcXp4YWluIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY2NDU2MDAsImV4cCI6MjA5MjIyMTYwMH0.Ef0uELb-CwYxlKpK_DggIrfX0NZDHiyEHTIcZmseyzk"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# 2. CSS DARK MODE & KONTRAST TINGGI (ANTI-ITEM)
st.set_page_config(page_title="Gudang Sahaja Pro", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    h1, h2, h3, p, span, label, [data-testid="stWidgetLabel"] { color: #FFFFFF !important; font-weight: 700 !important; }
    input, [data-baseweb="input"] > div, textarea {
        background-color: #1A1C23 !important; color: #FFFFFF !important;
        border: 1px solid #444444 !important; border-radius: 4px !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    div[data-baseweb="select"] * { color: #FFFFFF !important; }
    .stButton>button {
        background-color: #FFFFFF !important; color: #000000 !important;
        font-weight: bold !important; width: 100% !important; height: 3.5em !important;
    }
    .stButton>button p { color: #000000 !important; }
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# 3. FUNGSI AMBIL DATA (REAL-TIME DARI SUPABASE)
def get_inventory_data():
    # Ambil semua data transaksi
    response = supabase.table("inventory").select("*").execute()
    data = response.data
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    # Hitung Sisa Stok per Barang
    summary = []
    for barang in df['barang'].unique():
        b_data = df[df['barang'] == barang]
        masuk = b_data[b_data['jenis'] == 'MASUK']['jumlah'].sum()
        keluar = b_data[b_data['jenis'] == 'KELUAR']['jumlah'].sum()
        row = b_data.iloc[0]
        summary.append({
            "Barang": barang,
            "Kategori": row['kategori'],
            "Sisa Stok": masuk - keluar,
            "Satuan": row['satuan']
        })
    return pd.DataFrame(summary)

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'report': ""})

# --- LOGIN ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center;'>📦</h2><h3 style='text-align:center;'>GUDANG PRO</h3>", unsafe_allow_html=True)
        role = st.selectbox("Role:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
        pw = st.text_input("Password:", type="password")
        if st.button("MASUK"):
            if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
                st.session_state.update({'logged_in': True, 'role': role})
                st.rerun()
            else: st.error("Akses Ditolak!")

# --- DASHBOARD UTAMA ---
else:
    st.markdown(f"### User: {st.session_state.role}")
    df_stok = get_inventory_data()

    tabs = st.tabs(["📊 DATA", "➕ MASUK", "➖ KELUAR", "📱 WA", "🚪 KELUAR"])
    
    with tabs[0]: # DATA STOK
        if not df_stok.empty:
            st.dataframe(df_stok, use_container_width=True, hide_index=True)
        else:
            st.info("Gudang kosong.")
        if st.button("REFRESH"): st.rerun()

    with tabs[1]: # UPDATE / MASUK STOK
        st.markdown("#### Input Barang Masuk")
        with st.form("in_form", clear_on_submit=True):
            is_existing = not df_stok.empty
            mode = st.radio("Jenis:", ["Stok Lama (Update)", "Barang Baru"], horizontal=True) if is_existing else "Barang Baru"
            
            if mode == "Stok Lama (Update)":
                nama = st.selectbox("Pilih Barang:", df_stok['Barang'].unique())
                info = df_stok[df_stok['Barang'] == nama].iloc[0]
                kat, sat = info['Kategori'], info['Satuan']
            else:
                nama = st.text_input("Nama Barang:").upper()
                kat = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                sat = st.selectbox("Satuan:", ["pcs", "kg", "gram", "box"])
            
            jml = st.number_input("Jumlah Masuk:", min_value=1)
            if st.form_submit_button("SIMPAN KE SUPABASE"):
                data_insert = {
                    "user_input": st.session_state.role,
                    "jenis": "MASUK",
                    "kategori": kat,
                    "barang": nama,
                    "jumlah": int(jml),
                    "satuan": sat
                }
                supabase.table("inventory").insert(data_insert).execute()
                st.session_state.report += f"• {nama}: +{jml} {sat}\n"
                st.success("Data Masuk!")

    with tabs[2]: # KELUARIN STOK
        st.markdown("#### Catat Barang Keluar")
        if not df_stok.empty:
            with st.form("out_form", clear_on_submit=True):
                n_o = st.selectbox("Barang Keluar:", df_stok['Barang'].unique())
                info_o = df_stok[df_stok['Barang'] == n_o].iloc[0]
                st.warning(f"Stok Tersedia: {info_o['Sisa Stok']} {info_o['Satuan']}")
                j_o = st.number_input("Jumlah Keluar:", min_value=1, max_value=int(info_o['Sisa Stok']))
                
                if st.form_submit_button("KONFIRMASI KELUAR"):
                    data_out = {
                        "user_input": st.session_state.role,
                        "jenis": "KELUAR",
                        "kategori": info_o['Kategori'],
                        "barang": n_o,
                        "jumlah": int(j_o),
                        "satuan": info_o['Satuan']
                    }
                    supabase.table("inventory").insert(data_out).execute()
                    st.session_state.report += f"• {n_o}: -{j_o} {info_o['Satuan']}\n"
                    st.success("Tercatat Keluar!")
        else:
            st.error("Gak ada barang buat dikeluarin!")

    with tabs[3]: # LAPORAN WA
        if st.session_state.report:
            msg = f"*LAPORAN GUDANG*\nUser: {st.session_state.role}\n---\n{st.session_state.report}"
            st.text_area("Draft:", msg, height=150)
            url_wa = f"https://wa.me/?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{url_wa}" target="_blank" style="text-decoration:none;"><div style="background-color:#FFFFFF;color:#000000;padding:15px;border-radius:4px;text-align:center;font-weight:bold;">🚀 KIRIM KE WA</div></a>', unsafe_allow_html=True)
            if st.button("Hapus Laporan"): st.session_state.report = ""; st.rerun()
        else: st.info("Belum ada data transaksi.")

    with tabs[4]: # LOGOUT
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
