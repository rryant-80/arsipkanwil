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
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# ---------------------------------------------------------
# FUNGSI HELPER: UPLOAD DOKUMEN KE GOOGLE DRIVE
# ---------------------------------------------------------
def upload_to_drive(file_bytes, file_name, folder_id):
    """Mengunggah file PDF ke Google Drive menggunakan kredensial Service Account"""
    creds_dict = dict(st.secrets["connections"]["gsheets"])
    # Hapus kunci non-GCP jika ada
    creds_dict.pop("spreadsheet", None)
    creds_dict.pop("drive_folder_id", None)
    
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )
    
    service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='application/pdf', resumable=True)
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    return uploaded_file.get('webViewLink')

# ---------------------------------------------------------
# LOGIKA MENU KATALOG & PEMUTAKHIRAN DATA
# ---------------------------------------------------------
if st.session_state.active_menu == "Katalog":
    st.title("🔍 Katalog & Pemutakhiran Arsip")
    st.markdown("---")

    # =========================================================
    # SECTION 1: MENU PENCARIAN DOKUMEN
    # =========================================================
    st.subheader("🔎 Pencarian Dokumen")
    
    # Input Pencarian Teks
    search_query = st.text_input(
        "Cari berdasarkan Nomor Item Arsip, Subyek, atau Data Spasial:",
        placeholder="Ketik kata kunci di sini..."
    )
    
    # Filter Kabupaten, Kecamatan, Tahun
    c_filt1, c_filt2, c_filt3 = st.columns(3)
    
    with c_filt1:
        kab_opts = ["Semua Kabupaten"] + sorted(df['kab_kota'].dropna().astype(str).unique().tolist()) if 'kab_kota' in df.columns else ["Semua"]
        sel_kab = st.selectbox("Filter Kabupaten/Kota:", kab_opts)
        
    with c_filt2:
        if sel_kab != "Semua Kabupaten" and 'kab_kota' in df.columns:
            kec_opts = ["Semua Kecamatan"] + sorted(df[df['kab_kota'].astype(str) == sel_kab]['kecamatan'].dropna().astype(str).unique().tolist())
        else:
            kec_opts = ["Semua Kecamatan"] + sorted(df['kecamatan'].dropna().astype(str).unique().tolist()) if 'kecamatan' in df.columns else ["Semua"]
        sel_kec = st.selectbox("Filter Kecamatan:", kec_opts)
        
    with c_filt3:
        thn_opts = ["Semua Tahun"] + sorted(df['tahun'].dropna().astype(str).unique().tolist()) if 'tahun' in df.columns else ["Semua"]
        sel_thn = st.selectbox("Filter Tahun:", thn_opts)

    # Memproses Filter Pencarian
    df_search = df.copy()
    
    if search_query:
        cols_to_search = ['nomoritem_arsip', 'subyek', 'data_spasial']
        existing_cols = [c for c in cols_to_search if c in df_search.columns]
        
        # Match query pada salah satu kolom
        mask = df_search[existing_cols].astype(str).apply(
            lambda x: x.str.contains(search_query, case=False, na=False)
        ).any(axis=1)
        df_search = df_search[mask]
        
    if sel_kab != "Semua Kabupaten" and 'kab_kota' in df_search.columns:
        df_search = df_search[df_search['kab_kota'].astype(str) == sel_kab]
        
    if sel_kec != "Semua Kecamatan" and 'kecamatan' in df_search.columns:
        df_search = df_search[df_search['kecamatan'].astype(str) == sel_kec]
        
    if sel_thn != "Semua Tahun" and 'tahun' in df_search.columns:
        df_search = df_search[df_search['tahun'].astype(str) == sel_thn]

    st.caption(f"Menampilkan {len(df_search)} data dari hasil pencarian.")
    st.dataframe(df_search, use_container_width=True)

    st.markdown("---")

    # =========================================================
    # SECTION 2: MENU PEMUTAKHIRAN DATA
    # =========================================================
    st.subheader("✏️ Pemutakhiran Data Arsip")
    
    # Filter Lemari, Rak, dan Bundel
    cf1, cf2, cf3 = st.columns(3)
    
    with cf1:
        lem_opts = ["-- Pilih Lemari --"] + sorted(df['lemari'].dropna().astype(str).unique().tolist()) if 'lemari' in df.columns else []
        edit_lemari = st.selectbox("Lemari:", lem_opts, key="ed_lemari")
        
    with cf2:
        if edit_lemari != "-- Pilih Lemari --":
            rak_opts = ["-- Pilih Rak --"] + sorted(df[df['lemari'].astype(str) == edit_lemari]['rak'].dropna().astype(str).unique().tolist())
        else:
            rak_opts = ["-- Pilih Rak --"]
        edit_rak = st.selectbox("Rak:", rak_opts, key="ed_rak")
        
    with cf3:
        if edit_rak != "-- Pilih Rak --":
            bundel_opts = ["-- Pilih Bundel --"] + sorted(df[(df['lemari'].astype(str) == edit_lemari) & (df['rak'].astype(str) == edit_rak)]['bundel'].dropna().astype(str).unique().tolist())
        else:
            bundel_opts = ["-- Pilih Bundel --"]
        edit_bundel = st.selectbox("Bundel:", bundel_opts, key="ed_bundel")

    # Tampilkan Tabel & Form Pemutakhiran jika Filter Bundel Sudah Dipilih
    if edit_bundel != "-- Pilih Bundel --":
        # Filter Data Spesifik
        mask_target = (df['lemari'].astype(str) == edit_lemari) & \
                      (df['rak'].astype(str) == edit_rak) & \
                      (df['bundel'].astype(str) == edit_bundel)
        
        df_target = df[mask_target].copy()
        
        st.write(f"**Daftar Dokumen di Lemari {edit_lemari} - Rak {edit_rak} - Bundel {edit_bundel}:**")

        # Pilih item mana yang ingin diperbarui
        doc_options = df_target.apply(lambda r: f"{r.get('nomoritem_arsip', '')} | {r.get('subyek', '')}", axis=1).tolist()
        selected_doc_str = st.selectbox("Pilih Dokumen yang akan di-update:", doc_options)
        
        # Ambil Index Baris Terpilih
        selected_idx = doc_options.index(selected_doc_str)
        target_row = df_target.iloc[selected_idx]

        st.markdown("#### Form Input Pemutakhiran")
        
        with st.form("form_pemutakhiran", clear_on_submit=False):
            # --- KOLOM TERKUNCI (READ ONLY) ---
            col_lock1, col_lock2 = st.columns(2)
            with col_lock1:
                st.text_input("Kode Klasifikasi (Terkunci)", value=target_row.get('kodeklasifikasi', ''), disabled=True)
                st.text_input("Nomor Item Arsip (Terkunci)", value=target_row.get('nomoritem_arsip', ''), disabled=True)
                st.text_input("Subyek (Terkunci)", value=target_row.get('subyek', ''), disabled=True)
                st.text_input("Data Spasial (Terkunci)", value=target_row.get('data_spasial', ''), disabled=True)
            with col_lock2:
                st.text_input("Kabupaten/Kota (Terkunci)", value=target_row.get('kab_kota', ''), disabled=True)
                st.text_input("Kecamatan (Terkunci)", value=target_row.get('kecamatan', ''), disabled=True)
                st.text_input("Desa/Kelurahan (Terkunci)", value=target_row.get('desa_kelurahan', ''), disabled=True)

            st.markdown("---")
            # --- KOLOM BISA DIEDIT (EDITABLE) ---
            col_edit1, col_edit2 = st.columns(2)
            
            with col_edit1:
                # 1. Lembar Halaman (Numerik)
                val_halaman = int(target_row.get('lembar_halaman', 0)) if pd.notna(target_row.get('lembar_halaman')) and str(target_row.get('lembar_halaman')).isdigit() else 0
                new_halaman = st.number_input("Lembar Halaman:", min_value=0, value=val_halaman, step=1)
                
                # 2. Keamanan (Dropdown Select)
                keamanan_options = ["Biasa", "Sangat Rahasia", "Rahasia", "Terbatas"]
                curr_keamanan = str(target_row.get('keamanan', 'Biasa'))
                idx_keamanan = keamanan_options.index(curr_keamanan) if curr_keamanan in keamanan_options else 0
                new_keamanan = st.selectbox("Tingkat Keamanan:", keamanan_options, index=idx_keamanan)

            with col_edit2:
                # 3. Keterangan (Dropdown Select)
                ket_options = ["Lengkap", "hilang sebagian", "robek/terbakar sebagian"]
                curr_ket = str(target_row.get('keterangan', 'Lengkap'))
                idx_ket = ket_options.index(curr_ket) if curr_ket in ket_options else 0
                new_keterangan = st.selectbox("Keterangan Kondisi:", ket_options, index=idx_ket)

                # 4. Upload File PDF Data Digital
                uploaded_pdf = st.file_uploader("Upload Data Digital (File PDF):", type=["pdf"])

            submit_btn = st.form_submit_button("💾 Simpan Pemutakhiran Data", type="primary")

            if submit_btn:
                try:
                    # Ambil koneksi gsheets
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    
                    # 1. Proses Rename & Upload PDF ke Drive jika ada file diunggah
                    pdf_link = target_row.get('datadigital', '') # default nilai lama
                    if uploaded_pdf is not None:
                        subyek_clean = str(target_row.get('subyek', '')).replace('/', '-').strip()
                        kode_clean = str(target_row.get('kodeklasifikasi', '')).replace('/', '-').strip()
                        
                        # Format Nama File: subyek-kodeklasifikasi.pdf
                        new_filename = f"{subyek_clean}-{kode_clean}.pdf"
                        
                        folder_id = st.secrets["connections"]["gsheets"].get("drive_folder_id")
                        
                        with st.spinner("Mengunggah PDF ke Google Drive..."):
                            pdf_link = upload_to_drive(uploaded_pdf.getvalue(), new_filename, folder_id)
                            st.success(f"File berhasil diunggah dengan nama: **{new_filename}**")

                    # 2. Update Data Frame Lokal & Google Sheet
                    row_id_in_df = target_row.name # Index asli di dataframe
                    
                    df.at[row_id_in_df, 'lembar_halaman'] = new_halaman
                    df.at[row_id_in_df, 'keamanan'] = new_keamanan
                    df.at[row_id_in_df, 'keterangan'] = new_keterangan
                    df.at[row_id_in_df, 'datadigital'] = pdf_link
                    
                    # Simpan kembali dataframe yang sudah diupdate ke Google Sheets
                    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
                    conn.update(spreadsheet=sheet_url, data=df)
                    
                    st.cache_data.clear() # Clear cache agar data baru langsung tampil
                    st.success("✅ Pemutakhiran data berhasil disimpan!")
                    st.rerun()
                    
                except Exception as err:
                    st.error(f"Gagal memperbarui data: {err}")
    else:
        st.info("💡 Silakan pilih Lemari, Rak, dan Bundel terlebih dahulu untuk menampilkan form pemutakhiran data.")
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
