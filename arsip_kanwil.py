import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# 1. KONFIGURASI HALAMAN & CSS
# ---------------------------------------------------------
st.set_page_config(page_title="Dashboard Arsip", page_icon="📂", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Card Metrik Umum (Biru Muda & Outline) untuk Card 1-3 */
    .metric-card {
        background-color: #EBF3FA;
        border: 2px solid #3182CE;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        margin-bottom: 12px;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
    }
    .metric-title { font-size: 0.85rem; font-weight: 600; color: #2B6CB0; margin-bottom: 6px; text-transform: uppercase; }
    .metric-value { font-size: 1.4rem; font-weight: 700; color: #1A365D; }
    
    /* Card Jenis Arsip Vital (Sesuai image_72654c.png) untuk Card 4-8 */
    .card-vital {
        background-color: #F4FBFA;
        border-left: 6px solid #009688;
        border-radius: 6px;
        padding: 16px;
        text-align: center;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .card-vital-title {
        color: #006666;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .card-vital-value {
        color: #7B00D3;
        font-size: 1rem;
        font-weight: 700;
    }

    /* Ruang bagian bawah & Footer Navigation */
    .main .block-container { padding-bottom: 90px !important; }
    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) {
        position: fixed; bottom: 0; left: 0; right: 0;
        background-color: #FFFFFF;
        box-shadow: 0px -3px 10px rgba(0,0,0,0.15);
        padding: 8px 16px; z-index: 999999;
        display: flex; justify-content: space-around; align-items: center;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) button {
        border-radius: 8px; font-weight: 600; border: 1px solid #CBD5E0; height: 48px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. INISIALISASI DATA & STATE
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    df = conn.read(spreadsheet=sheet_url, ttl="5m")
    df.columns = df.columns.str.strip().str.lower()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Gagal memuat data: {e}")
    st.stop()

if 'active_menu' not in st.session_state:
    st.session_state.active_menu = "Dashboard"

# ---------------------------------------------------------
# 3. HALAMAN DASHBOARD
# ---------------------------------------------------------
if st.session_state.active_menu == "Dashboard":
    st.title("📂 Dashboard Monitoring Arsip")
    st.markdown("---")

    # --- CARD 1, 2, 3 (Umum) ---
    total_dokumen = len(df)
    total_bundel = df['bundel'].nunique() if 'bundel' in df.columns else 0
    total_digital = df['datadigital'].notna().sum() if 'datadigital' in df.columns else 0
    total_dipinjam = df['keterangan'].astype(str).str.contains("Pinjam|Dipinjam", case=False, na=False).sum() if 'keterangan' in df.columns else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">📦 Jml Bundel / Dokumen</div><div class="metric-value">{total_bundel} / {total_dokumen}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">💾 Jml Data Digital</div><div class="metric-value">{total_digital}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">📑 Dokumen Dipinjam</div><div class="metric-value">{total_dipinjam}</div></div>', unsafe_allow_html=True)

    # --- CARD 4 - 8 (Arsip Vital dengan Desain Khusus) ---
    st.subheader("📊 Capaian Arsip Vital")
    
    target_vital = {
        'SK HAT': 1296,
        'WARKAH': 1944,
        'ORDNER': 1014,
        'BOX BESAR': 360,
        'BOX KECIL': 135
    }

    cols = st.columns(5) # Membagi 5 card ke dalam 5 kolom sejajar
    
    for i, (jenis, target) in enumerate(target_vital.items()):
        # Filter data berdasarkan jenis arsip vital
        df_jenis = df[df['jenisarsip_vital'].astype(str).str.upper() == jenis]
        
        jml_bundel = df_jenis['bundel'].nunique() if 'bundel' in df_jenis.columns else 0
        jml_dokumen = len(df_jenis)
        jml_pdf = df_jenis['datadigital'].notna().sum() if 'datadigital' in df_jenis.columns else 0
        
        persen = (jml_bundel / target * 100) if target > 0 else 0
        
        with cols[i]:
            st.markdown(f"""
                <div class="card-vital">
                    <div class="card-vital-title">{jenis} ({persen:.1f}%)</div>
                    <div class="card-vital-value">{jml_bundel} Bundel - {jml_dokumen} Dok - {jml_pdf} PDF</div>
                </div>
            """, unsafe_allow_html=True)

    # --- GRAFIK DRILL-DOWN (3 Baris ke Bawah: Lemari -> Rak -> Bundel) ---
    st.markdown("---")
    st.subheader("📈 Distribusi Arsip Bertingkat")

    # ---------------------------------------------------------
    # BARIS 1: GRAFIK LEMARI (Selalu Tampil secara Default)
    # ---------------------------------------------------------
    df_lemari = df.groupby('lemari')['bundel'].nunique().reset_index(name='Jumlah Bundel')
    fig_lemari = px.bar(
        df_lemari, 
        x='lemari', 
        y='Jumlah Bundel', 
        text_auto=True, 
        title="1. Jumlah Bundel per Lemari", 
        color_discrete_sequence=['#3182CE']
    )
    # Hilangkan label judul sumbu x dan y
    fig_lemari.update_xaxes(title_text="")
    fig_lemari.update_yaxes(title_text="")
    
    st.plotly_chart(fig_lemari, use_container_width=True)

    # Filter Pilihan Lemari untuk Membuka Grafik Rak
    lemari_options = ["-- Pilih Lemari untuk Detail Rak --"] + sorted(df['lemari'].dropna().astype(str).unique().tolist())
    selected_lemari = st.selectbox("Pilih Lemari:", lemari_options, key="select_lemari")

    # ---------------------------------------------------------
    # BARIS 2: GRAFIK RAK (Hanya muncul jika Lemari dipilih)
    # ---------------------------------------------------------
    if selected_lemari != "-- Pilih Lemari untuk Detail Rak --":
        df_filtered_lemari = df[df['lemari'].astype(str) == selected_lemari]
        df_rak = df_filtered_lemari.groupby('rak')['bundel'].nunique().reset_index(name='Jumlah Bundel')
        
        fig_rak = px.bar(
            df_rak, 
            x='rak', 
            y='Jumlah Bundel', 
            text_auto=True, 
            title=f"2. Jumlah Bundel per Rak (di {selected_lemari})", 
            color_discrete_sequence=['#009688']
        )
        fig_rak.update_xaxes(title_text="")
        fig_rak.update_yaxes(title_text="")
        
        st.plotly_chart(fig_rak, use_container_width=True)

        # Filter Pilihan Rak untuk Membuka Grafik Bundel
        rak_options = ["-- Pilih Rak untuk Detail Bundel --"] + sorted(df_filtered_lemari['rak'].dropna().astype(str).unique().tolist())
        selected_rak = st.selectbox(f"Pilih Rak di {selected_lemari}:", rak_options, key="select_rak")

        # ---------------------------------------------------------
        # BARIS 3: GRAFIK BUNDEL (Hanya muncul jika Rak dipilih)
        # ---------------------------------------------------------
        if selected_rak != "-- Pilih Rak untuk Detail Bundel --":
            df_filtered_rak = df_filtered_lemari[df_filtered_lemari['rak'].astype(str) == selected_rak]
            
            # Menghitung jumlah dokumen di masing-masing bundel
            col_bundel_name = 'bundel' if 'bundel' in df.columns else 'id_bundel'
            df_bundel = df_filtered_rak.groupby(col_bundel_name).size().reset_index(name='Jumlah Dokumen')
            
            fig_bundel = px.bar(
                df_bundel, 
                x=col_bundel_name, 
                y='Jumlah Dokumen', 
                text_auto=True, 
                title=f"3. Jumlah Dokumen per Bundel (Rak {selected_rak} - {selected_lemari})", 
                color_discrete_sequence=['#7B00D3']
            )
            fig_bundel.update_xaxes(title_text="")
            fig_bundel.update_yaxes(title_text="")
            
            st.plotly_chart(fig_bundel, use_container_width=True)

# ---------------------------------------------------------
# 4. HALAMAN LAINNYA
# ---------------------------------------------------------
elif st.session_state.active_menu == "Katalog":
    st.title("🔍 Katalog Arsip")
    # ... (Isi halaman katalog)
elif st.session_state.active_menu == "Sirkulasi":
    st.title("🔄 Sirkulasi")
    # ... (Isi halaman sirkulasi)
elif st.session_state.active_menu == "Pelaporan":
    st.title("📈 Pelaporan")
    # ... (Isi halaman pelaporan)

# ---------------------------------------------------------
# 5. FOOTER NAVIGATION BAR
# ---------------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
f1, f2, f3, f4 = st.columns(4)

with f1:
    if st.button("📊 Dashboard", key="nav_dash", use_container_width=True, type="primary" if st.session_state.active_menu == "Dashboard" else "secondary"):
        st.session_state.active_menu = "Dashboard"
        st.rerun()
with f2:
    if st.button("🔍 Katalog", key="nav_kat", use_container_width=True, type="primary" if st.session_state.active_menu == "Katalog" else "secondary"):
        st.session_state.active_menu = "Katalog"
        st.rerun()
with f3:
    if st.button("🔄 Sirkulasi", key="nav_sir", use_container_width=True, type="primary" if st.session_state.active_menu == "Sirkulasi" else "secondary"):
        st.session_state.active_menu = "Sirkulasi"
        st.rerun()
with f4:
    if st.button("📈 Pelaporan", key="nav_lap", use_container_width=True, type="primary" if st.session_state.active_menu == "Pelaporan" else "secondary"):
        st.session_state.active_menu = "Pelaporan"
        st.rerun()
