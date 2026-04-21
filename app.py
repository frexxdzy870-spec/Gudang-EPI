import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. SETUP KONEKSI (PASTIKAN URL & KEY BENER)
SUPABASE_URL = "https://obrbnenfojqdepqzxain.supabase.co"
SUPABASE_KEY = "ISI_ANON_KEY_LU"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# 2. CSS DARK MODE & KONTRAS TINGGI
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

# 3. FUNGSI AMBIL DATA
def get_inventory_data():
    try:
        res = supabase.table("inventory").select("*").execute()
        df = pd.DataFrame(res.data)
        if df.empty: return pd.DataFrame()
        
        summary = []
        for b in df['barang'].unique():
            b_df = df[df['barang'] == b]
            masuk = b_df[b_df['jenis'] == 'MASUK']['jumlah'].sum()
            keluar = b_df[b_df['jenis'] == 'KELUAR']['jumlah'].sum()
            row = b_df.iloc[0]
            summary.append({"Barang": b, "Kategori": row['kategori'], "Sisa Stok": masuk - keluar, "Satuan": row['satuan']})
        return pd.DataFrame(summary)
    except: return pd.DataFrame()

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'report': ""})

# --- LOGIN ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>☕</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>GUDANG SAHAJA</h3>", unsafe_allow_html=True)
        role = st.selectbox("Role:", ["Staff Shift 1", "Staff Shift 2", "Owner"])
        pw = st.text_input("Password:", type="password")
        if st.button("MASUK"):
            if (role == "Owner" and pw == "owner123") or (role.startswith("Staff") and pw == "staff123"):
                st.session_state.update({'logged_in': True, 'role': role})
                st.rerun()
            else: st.error("Password Salah!")

# --- DASHBOARD ---
else:
    st.markdown(f"### 📋 User: {st.session_state.role}")
    df_stok = get_inventory_data()
    
    # Staff GAK BISA LIHAT MENU DATA
    if st.session_state.role == "Owner":
        tabs = st.tabs(["📊 DATA", "➕ UPDATE STOK", "➖ KELUAR STOK", "📱 WA", "🚪 LOGOUT"])
    else:
        tabs = st.tabs(["➕ UPDATE STOK", "➖ KELUAR STOK", "📱 WA", "🚪 LOGOUT"])
    
    tab_list = ["📊 DATA", "➕ UPDATE STOK", "➖ KELUAR STOK", "📱 WA", "🚪 LOGOUT"] if st.session_state.role == "Owner" else ["➕ UPDATE STOK", "➖ KELUAR STOK", "📱 WA", "🚪 LOGOUT"]

    for i, tab in enumerate(tabs):
        t_name = tab_list[i]
        
        with tab:
            if "DATA" in t_name:
                if not df_stok.empty: st.dataframe(df_stok, use_container_width=True, hide_index=True)
                else: st.info("Gudang Kosong.")
                if st.button("REFRESH"): st.rerun()

            elif "UPDATE STOK" in t_name:
                with st.form("form_update", clear_on_submit=True):
                    is_ex = not df_stok.empty
                    mode = st.radio("Metode:", ["Stok Lama (Update)", "Barang Baru"], horizontal=True) if is_ex else "Barang Baru"
                    
                    if mode == "Stok Lama (Update)":
                        nm = st.selectbox("Pilih Barang:", df_stok['Barang'].unique())
                        inf = df_stok[df_stok['Barang'] == nm].iloc[0]
                        kt, stn = inf['Kategori'], inf['Satuan']
                    else:
                        nm = st.text_input("Nama Barang:").upper()
                        kt = st.selectbox("Kategori:", ["BAR", "KITCHEN"])
                        stn = st.selectbox("Satuan:", ["pack", "kg", "box", "pcs", "gram"])
                    
                    jml = st.number_input("Jumlah Tambahan:", min_value=1)
                    if st.form_submit_button("SIMPAN UPDATE"):
                        supabase.table("inventory").insert({
                            "user_input": st.session_state.role, "jenis": "MASUK",
                            "kategori": kt, "barang": nm, "jumlah": int(jml), "satuan": stn
                        }).execute()
                        st.session_state.report += f"• {nm}: +{jml} {stn}\n"
                        st.success("Stok Berhasil Ditambah!")

            elif "KELUAR STOK" in t_name:
                if not df_stok.empty:
                    with st.form("form_keluar", clear_on_submit=True):
                        nm_o = st.selectbox("Barang Keluar:", df_stok['Barang'].unique())
                        inf_o = df_stok[df_stok['Barang'] == nm_o].iloc[0]
                        st.warning(f"Sisa Stok: {inf_o['Sisa Stok']} {inf_o['Satuan']}")
                        jml_o = st.number_input("Jumlah Keluar:", min_value=1, max_value=int(inf_o['Sisa Stok']))
                        
                        if st.form_submit_button("PROSES KELUAR"):
                            supabase.table("inventory").insert({
                                "user_input": st.session_state.role, "jenis": "KELUAR",
                                "kategori": inf_o['Kategori'], "barang": nm_o, "jumlah": int(jml_o), "satuan": inf_o['Satuan']
                            }).execute()
                            st.session_state.report += f"• {nm_o}: -{jml_o} {inf_o['Satuan']}\n"
                            st.success("Barang Keluar Dicatat!")
                else: st.error("Tidak ada data barang untuk dikeluarkan.")

            elif "WA" in t_name:
                if st.session_state.report:
                    msg = f"*LAPORAN GUDANG*\nUser: {st.session_state.role}\n---\n{st.session_state.report}"
                    st.text_area("Preview Laporan:", msg, height=150)
                    st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><div style="background-color:#FFFFFF;color:#000000;padding:15px;border-radius:4px;text-align:center;font-weight:bold;">🚀 KIRIM LAPORAN KE WA</div></a>', unsafe_allow_html=True)
                    if st.button("Hapus Draft"): st.session_state.report = ""; st.rerun()
                else: st.info("Belum ada aktivitas hari ini.")

            elif "LOGOUT" in t_name:
                if st.button("KELUAR AKUN"):
                    st.session_state.logged_in = False
                    st.rerun()
