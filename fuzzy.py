import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Fuzzy MADM - Cloud Computing", layout="wide")

# ---------- Global CSS ----------
st.markdown("""
<style>
    .main { padding: 20px; }
    .stDataFrame { border-radius: 10px; }
    .card {
        padding: 18px;
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.07);
        margin-bottom: 25px;
    }
    h2, h3 {
        font-weight: 700;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.title("☁️ Fuzzy MADM — Pemilihan Layanan Cloud Computing Terbaik")

# Inisialisasi DataFrame default (digunakan jika tidak ada upload)
DEFAULT_PROVIDERS = [
    "AWS",
    "GCP",
    "Microsoft Azure",
    "Alibaba Cloud",
    "DigitalOcean"
]
DEFAULT_DF = pd.DataFrame({
    "Biaya": [60, 80, 60, 80, 100], # Crisp C1
    "Kinerja": [100, 100, 80, 60, 80], # Crisp C2
    "Keamanan": [100, 80, 100, 60, 60], # Crisp C3
    "Skalabilitas": [100, 100, 80, 80, 60], # Crisp C4
}, index=DEFAULT_PROVIDERS)

if "df" not in st.session_state:
    st.session_state.df = DEFAULT_DF.copy()

# ---------- Sidebar ----------
st.sidebar.header("📌 Menu Navigasi")
page = st.sidebar.radio("Pilih halaman", ["Home", "Input Data", "Fuzzy SAW", "Fuzzy WP", "Perbandingan", "Tentang"])

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚖️ Bobot Kriteria (Berdasarkan Normalisasi wj)")

# Bobot kriteria (C1=0.35, C2=0.3, C3=0.15, C4=0.2)
w1 = st.sidebar.slider("Biaya (C1)", 0.0, 1.0, 0.35, 0.01)
w2 = st.sidebar.slider("Kinerja (C2)", 0.0, 1.0, 0.30, 0.01)
w3 = st.sidebar.slider("Keamanan (C3)", 0.0, 1.0, 0.15, 0.01)
w4 = st.sidebar.slider("Skalabilitas (C4)", 0.0, 1.0, 0.20, 0.01)

# Normalisasi Bobot (untuk memastikan total = 1)
ws_raw = np.array([w1, w2, w3, w4])
ws = ws_raw / ws_raw.sum() if ws_raw.sum() != 0 else np.array([0.35, 0.30, 0.15, 0.20])

# Tipe Kriteria (Cost/Benefit)
# C1=Biaya (Cost), C2=Kinerja (Benefit), C3=Keamanan (Benefit), C4=Skalabilitas (Benefit)
TYPES = ["cost", "benefit", "benefit", "benefit"]
# Pastikan nama kolom sesuai dengan DataFrame
CRITERIA_NAMES = DEFAULT_DF.columns.tolist()

# ---------- FUNCTIONS ----------

# Fungsi Fuzzy TFN (Triangular Fuzzy Number)
def tri(v):
    """Menghitung TFN (a, m, b) dari nilai ternormalisasi v.
       Menggunakan range 0.1 seperti pada kode awal Anda."""
    if pd.isna(v):
        return np.array([0.0, 0.0, 0.0]) # Handle NaN gracefully
    return np.array([max(0, v - 0.1), v, min(1, v + 0.1)])

def normalize_saw(df):
    """Normalisasi Fuzzy SAW (Min-Max Normalization)."""
    res = pd.DataFrame(index=df.index, columns=df.columns, dtype=float)
    
    # Ambil nilai Crisp, jika ada kolom Crisp C1, Crisp C2, dll.
    # Jika tidak ada, gunakan kolom yang tersedia
    
    # Hanya bekerja pada data Crisp yang ada di DataFrame
    for i, col in enumerate(df.columns):
        if i >= len(TYPES):
            # Jika ada kolom lebih, abaikan (misal: kolom nama)
            continue

        min_val = df[col].min()
        max_val = df[col].max()
        
        # Hindari pembagian dengan nol
        if max_val == min_val:
            res[col] = 1.0
            continue

        if TYPES[i] == "benefit":
            res[col] = (df[col] - min_val) / (max_val - min_val)
        else: # cost
            res[col] = (max_val - df[col]) / (max_val - min_val)
    
    return res

def saw_calc(df_crisp, weights):
    """Perhitungan Fuzzy SAW."""
    # 1. Normalisasi
    normal = normalize_saw(df_crisp)
    
    tfn_total = {}
    scores = []
    
    # 2. Pembentukan TFN Agregat (TFN V_i = Sum(w_j * R_ij))
    for idx in normal.index:
        # Inisialisasi TFN V_i = [a, m, b]
        total = np.array([0.0, 0.0, 0.0])
        
        for j, col in enumerate(normal.columns):
            if j >= len(weights):
                continue # Skip if more columns than weights
            
            # Mendapatkan nilai ternormalisasi (R_ij)
            normalized_value = normal.loc[idx, col]
            
            # Mendapatkan TFN dari R_ij
            t = tri(normalized_value)
            
            # TFN * Bobot (w_j * R_ij) - Perkalian skalar
            total += t * weights[j]
            
        tfn_total[idx] = total
        
        # 3. Defuzzifikasi (menggunakan rata-rata TFN)
        # Score = (a + m + b) / 3
        scores.append(total.mean())
        
    res = pd.DataFrame({"Score": scores}, index=normal.index)
    res["Rank"] = res["Score"].rank(ascending=False, method='min').astype(int)
    return res, normal, tfn_total

def wp_calc(df_crisp, weights):
    """Perhitungan Weighted Product (WP) - Non-Fuzzy.
       Perhatian: Karena implementasi SAW menggunakan Fuzzy (TFN), 
       WP ini akan berjalan sebagai WP Crisp biasa, seperti pada kode awal Anda."""
    
    # 1. Hitung Vektor Bobot Pangkat (w_j / Sum(w_j)) sudah dilakukan di ws
    
    S = [] # Nilai Vektor S (S_i)
    
    # 2. Hitung Nilai S_i = Product(x_ij ^ wj)
    for idx in df_crisp.index:
        nilai_S = 1.0
        for j, col in enumerate(df_crisp.columns):
            if j >= len(weights):
                continue
            
            # Ambil nilai Crisp (x_ij)
            x_ij = df_crisp.loc[idx, col]
            
            if TYPES[j] == "benefit":
                # Benefit: S_i *= x_ij ^ wj
                nilai_S *= x_ij ** weights[j]
            else:
                # Cost: S_i *= x_ij ^ (-wj)
                nilai_S *= x_ij ** (-weights[j])
        
        S.append(nilai_S)

    S = np.array(S)
    
    # 3. Hitung Vektor V (V_i = S_i / Sum(S))
    sum_S = S.sum()
    if sum_S == 0:
        V = np.zeros_like(S)
    else:
        V = S / sum_S

    res = pd.DataFrame({"S": S, "V": V}, index=df_crisp.index)
    res["Rank"] = res["V"].rank(ascending=False, method='min').astype(int)
    return res

# Helper function untuk mendapatkan data
def get_processed_data():
    """Mengambil data dari session state dan melakukan validasi/konversi."""
    df = st.session_state.df.copy()
    
    # Coba konversi semua data menjadi numerik, menangani error
    try:
        df = df.apply(pd.to_numeric, errors='coerce')
        # Hapus baris atau kolom yang seluruhnya NaN setelah konversi (jika ada input data kotor)
        df.dropna(axis=0, how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
    except Exception as e:
        st.error(f"Error dalam konversi data ke numerik: {e}")
        return pd.DataFrame()
        
    # Memastikan hanya kriteria Crisp (4 kolom pertama) yang digunakan
    if len(df.columns) > len(CRITERIA_NAMES):
        df = df.iloc[:, :len(CRITERIA_NAMES)]
        df.columns = CRITERIA_NAMES
    elif len(df.columns) < len(CRITERIA_NAMES):
        st.warning("Jumlah kolom data kriteria tidak lengkap. Harap gunakan 4 kolom (Biaya, Kinerja, Keamanan, Skalabilitas).")
        return pd.DataFrame()
    
    return df

# ---------- Pages (Diperbarui) ----------
if page == "Home":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📘 Ringkasan Aplikasi")
    st.write("""
    Aplikasi ini menggunakan metode **Fuzzy Simple Additive Weighting (SAW)** dan **Weighted Product (WP)**  
    untuk menentukan *Layanan Cloud Computing terbaik* berdasarkan empat kriteria Crisp (Crips C1, C2, C3, C4):

    - 💰 **Biaya** (Cost) | Bobot: **{:.2f}**
    - ⚡ **Kinerja** (Benefit) | Bobot: **{:.2f}**
    - 🔐 **Keamanan** (Benefit) | Bobot: **{:.2f}**
    - 📈 **Skalabilitas** (Benefit) | Bobot: **{:.2f}**

    **Perhatian:** Pastikan Anda mengunggah atau mengedit data Crisp (nilai 60, 80, 100, dll.) di halaman **Input Data** sebelum melakukan perhitungan.
    """.format(ws[0], ws[1], ws[2], ws[3]))
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Input Data":
    st.header("📝 Input / Edit Data Alternatif (Nilai Crisp)")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Upload file Excel (.xlsx) atau CSV (.csv)",
        type=["csv", "xlsx"]
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                uploaded_df = pd.read_csv(uploaded_file, index_col=0)
            else: # xlsx
                # Menggunakan baris ke-14 (indeks 13) sebagai header, sesuai format file Anda
                uploaded_df = pd.read_excel(uploaded_file, header=13, index_col=1)
                
                # Coba ambil hanya kolom Crisp C1, C2, C3, C4
                # Di file Anda, kolom Crisp C1, C2, C3, C4 berada di kolom 'Crisp C1', 'Crisp C2', 'Crisp C3', 'Crisp C4'
                # Kolom ke-4, ke-7, ke-10, ke-13 (indeks 4, 7, 10, 13)
                # Dari snippet: [A1, AWS, $150/bln, Cukup Mahal, 60], [95/100, Sangat Baik, 100]...
                # Kolom yang kita butuhkan adalah Crisp C1 (indeks 4), Crisp C2 (indeks 7), Crisp C3 (indeks 10), Crisp C4 (indeks 13)
                
                # Baca ulang dengan skiprows dan usecols jika diperlukan, tapi mari kita coba filter setelah read_excel
                if 'Crisp C1' in uploaded_df.columns:
                    # Ini adalah format dari file Anda
                    col_map = {
                        'Crisp C1': 'Biaya',
                        'Crisp C2': 'Kinerja',
                        'Crisp C3': 'Keamanan',
                        'Crisp C4': 'Skalabilitas'
                    }
                    uploaded_df = uploaded_df[list(col_map.keys())].rename(columns=col_map)
                else:
                    # Asumsi user upload file CSV sederhana dengan kolom pertama sebagai index
                    st.info("Asumsi kolom 1-4 adalah Biaya, Kinerja, Keamanan, Skalabilitas.")
                    uploaded_df = uploaded_df.iloc[:, :4]
                    uploaded_df.columns = CRITERIA_NAMES
                    
            st.session_state.df = uploaded_df
            st.success("File berhasil diunggah dan data dimuat.")
            
        except Exception as e:
            st.error(f"Terjadi error saat memproses file: {e}. Pastikan file memiliki format yang benar (misal, Crisp C1, C2, C3, C4 berada di kolom yang diharapkan).")
            # Kembali ke default jika gagal
            st.session_state.df = DEFAULT_DF.copy()

    
    st.subheader("Tabel Data Crisp (Untuk diedit/diperiksa)")
    edited = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        use_container_width=True,
    )
    st.session_state.df = edited

    st.download_button("⬇️ Download data (.csv)", edited.to_csv().encode('utf-8'),
                       file_name="data_crisp_input.csv")
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Fuzzy SAW":
    st.header("🔷 Hasil Fuzzy SAW")

    df_crisp = get_processed_data()
    if df_crisp.empty:
        st.warning("Data Crisp tidak tersedia atau tidak valid. Harap periksa halaman Input Data.")
    else:
        # Pengecekan jumlah kriteria vs bobot
        if len(df_crisp.columns) != len(ws):
            st.error("Jumlah kolom data Crisp tidak sesuai dengan jumlah bobot (harus 4 kriteria).")
        else:
            try:
                res_saw, normal, tfn_total = saw_calc(df_crisp, ws)
    
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Matriks Normalisasi Fuzzy SAW")
                st.dataframe(normal.style.format("{:.6f}"), use_container_width=True)
                # 
                st.markdown("</div>", unsafe_allow_html=True)
    
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("TFN Agregat (a, m, b) - Vektor V_i")
                tfn_df = pd.DataFrame.from_dict(tfn_total, orient='index', columns=["a", "m", "b"])
                st.dataframe(tfn_df.style.format("{:.6f}"), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
    
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Skor Defuzzifikasi & Ranking")
                st.dataframe(res_saw.style.format("{:.6f}"), use_container_width=True)
    
                out = pd.concat([df_crisp, normal.add_prefix("Norm_"), tfn_df.add_prefix("TFN_"), res_saw], axis=1)
                buf = BytesIO()
                out.to_excel(buf, index=True, engine="openpyxl")
                buf.seek(0)
    
                st.download_button("⬇️ Download hasil SAW (.xlsx)", data=buf,
                                   file_name="hasil_fuzzy_saw.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Terjadi kesalahan saat perhitungan SAW: {e}")


elif page == "Fuzzy WP":
    st.header("🔷 Hasil Weighted Product (WP)")
    st.info("Perhatian: Implementasi WP di sini adalah versi Crisp/Non-Fuzzy, seperti pada kode awal Anda, karena WP standar tidak menggunakan TFN.")

    df_crisp = get_processed_data()
    if df_crisp.empty:
        st.warning("Data Crisp tidak tersedia atau tidak valid. Harap periksa halaman Input Data.")
    else:
        if len(df_crisp.columns) != len(ws):
            st.error("Jumlah kolom data Crisp tidak sesuai dengan jumlah bobot (harus 4 kriteria).")
        else:
            try:
                res_wp = wp_calc(df_crisp, ws)
    
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Hasil WP (Vektor S, Vektor V, Ranking)")
                st.dataframe(res_wp.style.format("{:.6f}"), use_container_width=True)
                # 
    
                buf = BytesIO()
                res_wp.to_excel(buf, index=True, engine="openpyxl")
                buf.seek(0)
    
                st.download_button("⬇️ Download hasil WP (.xlsx)",
                                   data=buf,
                                   file_name="hasil_wp.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Terjadi kesalahan saat perhitungan WP: {e}")

elif page == "Perbandingan":
    st.header("📊 Perbandingan SAW vs WP")
    
    df_crisp = get_processed_data()
    if df_crisp.empty:
        st.warning("Data Crisp tidak tersedia atau tidak valid. Harap periksa halaman Input Data.")
    else:
        try:
            res_saw, _, _ = saw_calc(df_crisp, ws)
            res_wp = wp_calc(df_crisp, ws)
    
            # Ganti nama kolom untuk perbandingan
            compare = pd.DataFrame({"Fuzzy SAW Score": res_saw["Score"], "WP Vektor V": res_wp["V"]})
    
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Tabel Perbandingan Skor")
            st.dataframe(compare.style.format("{:.6f}"), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Grafik Perbandingan")
    
            fig, ax = plt.subplots(figsize=(10, 5))
            compare.plot(kind='bar', ax=ax, rot=0)
            ax.set_ylabel("Skor Keputusan")
            ax.set_title("Perbandingan Skor Fuzzy SAW vs WP")
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            st.pyplot(fig)
    
            top_saw = compare["Fuzzy SAW Score"].idxmax()
            top_wp = compare["WP Vektor V"].idxmax()
    
            st.subheader("Kesimpulan Ranking")
            if top_saw == top_wp:
                st.success(f"🎉 Kedua metode memilih **{top_saw}** sebagai layanan cloud terbaik!")
            else:
                st.info(f"🏆 Pilihan Terbaik Fuzzy SAW: **{top_saw}** (Skor Tertinggi)\n\n🥇 Pilihan Terbaik WP: **{top_wp}** (Vektor V Tertinggi)")
    
            st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Terjadi kesalahan saat perhitungan perbandingan: {e}")


elif page == "Tentang":
    st.header("ℹ️ Tentang Aplikasi")
    st.markdown("""
    Aplikasi ini dibuat untuk kebutuhan demonstrasi **Fuzzy Multiple Attribute Decision Making (MADM)**.

    ### Detail Metode:
    * **Fuzzy Simple Additive Weighting (SAW):** Menggunakan nilai Crisp yang dinormalisasi dan diubah menjadi *Triangular Fuzzy Number* (TFN) untuk perhitungan agregat, kemudian dilakukan defuzzifikasi menggunakan rata-rata TFN untuk mendapatkan skor akhir.
    * **Weighted Product (WP):** Menggunakan perkalian berbobot dari nilai Crisp, di mana bobot untuk kriteria *Cost* diberi pangkat negatif.

    Dibuat menggunakan **Python + Streamlit** untuk antarmuka web interaktif.
    """)
