import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# ---------------------------------------------------------
# 1. KONFIGURASI HALAMAN & LAYOUT RESPONSIF
# ---------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Arsip",
    page_icon="📂",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# 2. INJEKSI CSS UNTUK TAMPILAN MOBILE & STICKY FOOTER NAV
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* Styling Card Metrik (Biru Muda & Outline) */
    .metric-card {
        background-color: #EBF3FA;
        border: 2px solid #3182CE;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        margin-bottom: 12px;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #2B6CB0;
        margin-bottom: 6px;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1A365D;
    }
    
    /* Ruang bagian bawah agar konten tidak tertutup footer navigation */
    .main .block-container {
        padding-bottom: 90px !important;
    }

    /* Container Footer Navigasi Melayang (Sticky Bottom Nav) */
    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #FFFFFF;
        box-shadow: 0px -3px 10px rgba(0,0,0,0.15);
        padding: 8px 16px;
        z-index: 999999;
        display: flex;
        justify-content: space-around;
        align-items: center;
    }

    /* Styling tombol di footer nav */
    div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) button {
        border-radius: 8px;
        font-weight: 600;
        border: 1px solid #CBD5E0;
        height: 48px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. KONEKSI & AMBIL DATA GSHEET (GID: 1110654369)
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Membaca data menggunakan URL dari secrets
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    df = conn.read(spreadsheet=sheet_url, ttl="5m")
    
    # Bersihkan nama kolom dari whitespace berlebih
    df.columns = df.columns.str.strip().str.lower()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Gagal memuat data dari Google Sheets: {e}")
    st.stop()

# ---------------------------------------------------------
# 4. INISIALISASI SESSION STATE UNTUK NAVIGASI
# ---------------------------------------------------------
if 'active_menu' not in st.session_state:
    st.session_state.active_menu = "Dashboard"

# ---------------------------------------------------------
# 5. HALAMAN 1: DASHBOARD
# ---------------------------------------------------------
if st.session_state.active_menu == "Dashboard":
    st.title("📂 Dashboard Monitoring Arsip")
    st.caption("Ringkasan statistik data arsip pertanahan")
    st.markdown("---")

    # Hitung metrik awal dari data
    total_dokumen = len(df)
    
    # Menghitung Jumlah Bundel (unik berdasarkan kolom 'bundel' atau 'id_bundel')
    col_bundel = 'bundel' if 'bundel' in df.columns else ('id_bundel' if 'id_bundel' in df.columns else None)
    total_bundel = df[col_bundel].nunique() if col_bundel and col_bundel in df.columns else 0
    
    # Menghitung Data Digital (filter kolom 'datadigital' yang terisi/ada link)
    col_digital = 'datadigital' if 'datadigital' in df.columns else None
    total_digital = df[col_digital].notna().sum() if col_digital else 0
    
    # Menghitung Dokumen Dipinjam (asumsi dari kolom 'keterangan' atau kolom status)
    total_dipinjam = 0
    if 'keterangan' in df.columns:
        total_dipinjam = df['keterangan'].astype(str).str.contains("Pinjam|Dipinjam", case=False, na=False).sum()

    # --- BARIS 1: 4 CARD METRIK UTAMA ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📦 Total Bundel / Dokumen</div>
                <div class="metric-value">{total_bundel} / {total_dokumen}</div>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">💾 Jml Data Digital</div>
                <div class="metric-value">{total_digital}</div>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📑 Dokumen Dipinjam</div>
                <div class="metric-value">{total_dipinjam}</div>
            </div>
        """, unsafe_allow_html=True)

    with c4:
        # Card 4: breakdown/rasio ketersediaan digital
        pct_digital = f"{(total_digital / total_dokumen * 100):.1f}%" if total_dokumen > 0 else "0%"
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📊 Digitalisasi Ratio</div>
                <div class="metric-value">{pct_digital}</div>
            </div>
        """, unsafe_allow_html=True)

    # --- BARIS 2: 4 CARD METRIK KATEGORI / WILAYAH ---
    c5, c6, c7, c8 = st.columns(4)
    
    # Mengambil rincian per Kategori Arsip jika ada
    kategori_counts = df['kategoriarsip'].value_counts() if 'kategoriarsip' in df.columns else {}
    kat1 = kategori_counts.index[0] if len(kategori_counts) > 0 else "Kategori A"
    val1 = kategori_counts.iloc[0] if len(kategori_counts) > 0 else 0
    
    kat2 = kategori_counts.index[1] if len(kategori_counts) > 1 else "Kategori B"
    val2 = kategori_counts.iloc[1] if len(kategori_counts) > 1 else 0

    with c5:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📁 {kat1}</div>
                <div class="metric-value">{val1} Dok.</div>
            </div>
        """, unsafe_allow_html=True)

    with c6:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📁 {kat2}</div>
                <div class="metric-value">{val2} Dok.</div>
            </div>
        """, unsafe_allow_html=True)

    with c7:
        total_kab = df['kab_kota'].nunique() if 'kab_kota' in df.columns else 0
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">🗺️ Jml Kab/Kota</div>
                <div class="metric-value">{total_kab} Wilayah</div>
            </div>
        """, unsafe_allow_html=True)

    with c8:
        total_kec = df['kecamatan'].nunique() if 'kecamatan' in df.columns else 0
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">📍 Jml Kecamatan</div>
                <div class="metric-value">{total_kec} Wilayah</div>
            </div>
        """, unsafe_allow_html=True)

    # Menampilkan Tabel Ringkas
    st.subheader("📋 Preview Data Terbaru")
    st.dataframe(df.head(10), use_container_width=True)

# ---------------------------------------------------------
# 6. HALAMAN LAIN (KATALOG, SIRKULASI, PELAPORAN)
# ---------------------------------------------------------
elif st.session_state.active_menu == "Katalog":
    st.title("🔍 Katalog Arsip")
    search = st.text_input("Cari uraian, subyek, atau nomor item arsip:")
    if search:
        filtered_df = df[df.astype(str).apply(lambda row: row.str.contains(search, case=False).any(), axis=1)]
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

elif st.session_state.active_menu == "Sirkulasi":
    st.title("🔄 Sirkulasi & Peminjaman Arsip")
    st.info("Fitur pencatatan dan monitoring peminjaman berkas/arsip.")

elif st.session_state.active_menu == "Pelaporan":
    st.title("📈 Pelaporan Arsip")
    st.info("Halaman rekapitulasi dan cetak laporan arsip.")

# ---------------------------------------------------------
# 7. FOOTER NAVIGATION BAR (BOTTOM NAV ALA APP MOBILE)
# ---------------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True) # Spacing agar tidak menutupi tabel

# Menggunakan 4 kolom yang dipaksa di bagian bawah lewat CSS
f1, f2, f3, f4 = st.columns(4)

with f1:
    btn_type = "primary" if st.session_state.active_menu == "Dashboard" else "secondary"
    if st.button("📊 Dashboard", key="nav_dash", use_container_width=True, type=btn_type):
        st.session_state.active_menu = "Dashboard"
        st.rerun()

with f2:
    btn_type = "primary" if st.session_state.active_menu == "Katalog" else "secondary"
    if st.button("🔍 Katalog", key="nav_katalog", use_container_width=True, type=btn_type):
        st.session_state.active_menu = "Katalog"
        st.rerun()

with f3:
    btn_type = "primary" if st.session_state.active_menu == "Sirkulasi" else "secondary"
    if st.button("🔄 Sirkulasi", key="nav_sirkulasi", use_container_width=True, type=btn_type):
        st.session_state.active_menu = "Sirkulasi"
        st.rerun()

with f4:
    btn_type = "primary" if st.session_state.active_menu == "Pelaporan" else "secondary"
    if st.button("📈 Pelaporan", key="nav_laporan", use_container_width=True, type=btn_type):
        st.session_state.active_menu = "Pelaporan"
        st.rerun()
