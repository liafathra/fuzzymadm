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

st.title("☁️ Fuzzy MADM — Pemilihan Layanan Cloud Computing Terbaik (SAW & WP)")

# Inisialisasi DataFrame default
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

TYPES = ["cost", "benefit", "benefit", "benefit"]
CRITERIA_NAMES = DEFAULT_DF.columns.tolist()


# ---------- FUNCTIONS ----------

def normalize_saw_crisp(df):
    """Normalisasi Fuzzy SAW (Min-Max/Max-Min Normalization)."""
    res = pd.DataFrame(index=df.index, columns=df.columns, dtype=float)
    
    for i, col in enumerate(df.columns):
        if i >= len(TYPES):
            continue

        min_val = df[col].min()
        max_val = df[col].max()
        
        if max_val == min_val:
            res[col] = 1.0
            continue

        if TYPES[i] == "benefit":
            if TYPES[i] == "benefit":
                # BENEFIT: R_ij = x_ij / max(x_j)
                res[col] = df[col] / max_val
            else: # cost
                # COST: R_ij = min(x_j) / x_ij
                res[col] = min_val / df[col]
            # --- SAW STANDAR ---
            if TYPES[i] == "benefit":
                # BENEFIT: R_ij = x_ij / max(x_j)
                res[col] = df[col] / max_val
            else: # cost
                # COST: R_ij = min(x_j) / x_ij
                res[col] = min_val / df[col]
            # --- AKHIR SAW STANDAR ---

    return res

def saw_calc_crisp(df_crisp, weights):
    """Perhitungan SAW (Crisp)."""
    # 1. Normalisasi
    normal = normalize_saw_crisp(df_crisp)
    
    scores = []
    
    # 2. Perhitungan Skor (V_i = Sum(w_j * R_ij))
    for idx in normal.index:
        # Menghitung skor V_i (vektor V)
        score = (normal.loc[idx] * weights).sum()
        scores.append(score)
        
    res = pd.DataFrame({"Score": scores}, index=normal.index)
    res["Rank"] = res["Score"].rank(ascending=False, method='min').astype(int)
    return res, normal

def wp_calc(df_crisp, weights):
    """Perhitungan Weighted Product (WP)."""
    
    S = [] # Nilai Vektor S (S_i)
    
    # 1. Hitung Nilai S_i = Product(x_ij ^ wj)
    for idx in df_crisp.index:
        nilai_S = 1.0
        for j, col in enumerate(df_crisp.columns):
            if j >= len(weights):
                continue
            
            x_ij = df_crisp.loc[idx, col]
            
            if TYPES[j] == "benefit":
                # Benefit: S_i *= x_ij ^ wj
                nilai_S *= x_ij ** weights[j]
            else:
                # Cost: S_i *= x_ij ^ (-wj)
                nilai_S *= x_ij ** (-weights[j])
        
        S.append(nilai_S)

    S = np.array(S)
    
    # 2. Hitung Vektor V (V_i = S_i / Sum(S))
    sum_S = S.sum()
    if sum_S == 0:
        V = np.zeros_like(S)
    else:
        V = S / sum_S

    res = pd.DataFrame({"S": S, "V": V}, index=df_crisp.index)
    res["Rank"] = res["V"].rank(ascending=False, method='min').astype(int)
    return res

# Helper function untuk mendapatkan data (tetap sama)
def get_processed_data():
    """Mengambil data dari session state dan melakukan validasi/konversi."""
    df = st.session_state.df.copy()
    
    try:
        df = df.apply(pd.to_numeric, errors='coerce')
        df.dropna(axis=0, how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
    except Exception as e:
        st.error(f"Error dalam konversi data ke numerik: {e}")
        return pd.DataFrame()
        
    if len(df.columns) > len(CRITERIA_NAMES):
        df = df.iloc[:, :len(CRITERIA_NAMES)]
        df.columns = CRITERIA_NAMES
    elif len(df.columns) < len(CRITERIA_NAMES):
        st.warning("Jumlah kolom data kriteria tidak lengkap. Harap gunakan 4 kolom (Biaya, Kinerja, Keamanan, Skalabilitas).")
        return pd.DataFrame()
    
    return df

# ---------- Pages (DIUBAH) ----------
if page == "Home":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📘 Ringkasan Aplikasi")
    st.write("""
    Aplikasi ini menggunakan metode **Simple Additive Weighting (SAW)** dan **Weighted Product (WP)**  
    untuk menentukan *Layanan Cloud Computing terbaik* berdasarkan empat kriteria Crisp (Crips C1, C2, C3, C4):

    - 💰 **Biaya** (Cost) | Bobot: **{:.2f}**
    - ⚡ **Kinerja** (Benefit) | Bobot: **{:.2f}**
    - 🔐 **Keamanan** (Benefit) | Bobot: **{:.2f}**
    - 📈 **Skalabilitas** (Benefit) | Bobot: **{:.2f}**

   
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
                
                if 'Crisp C1' in uploaded_df.columns:
                    col_map = {
                        'Crisp C1': 'Biaya',
                        'Crisp C2': 'Kinerja',
                        'Crisp C3': 'Keamanan',
                        'Crisp C4': 'Skalabilitas'
                    }
                    uploaded_df = uploaded_df[list(col_map.keys())].rename(columns=col_map)
                else:
                    st.info("Asumsi kolom 1-4 adalah Biaya, Kinerja, Keamanan, Skalabilitas.")
                    uploaded_df = uploaded_df.iloc[:, :4]
                    uploaded_df.columns = CRITERIA_NAMES
                    
            st.session_state.df = uploaded_df
            st.success("File berhasil diunggah dan data dimuat.")
            
        except Exception as e:
            st.error(f"Terjadi error saat memproses file: {e}. Pastikan file memiliki format yang benar.")
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

elif page == "SAW":
    st.header("🔷 Hasil Simple Additive Weighting (SAW)")

    df_crisp = get_processed_data()
    if df_crisp.empty:
        st.warning("Data Crisp tidak tersedia atau tidak valid. Harap periksa halaman Input Data.")
    else:
        if len(df_crisp.columns) != len(ws):
            st.error("Jumlah kolom data Crisp tidak sesuai dengan jumlah bobot (harus 4 kriteria).")
        else:
            try:
                res_saw, normal = saw_calc_crisp(df_crisp, ws)
    
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Matriks Normalisasi SAW (Rij)")
                st.dataframe(normal.style.format("{:.6f}"), use_container_width=True)
                # 
                st.markdown("</div>", unsafe_allow_html=True)
    
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Skor Akhir (Vi) & Ranking")
                st.dataframe(res_saw.style.format("{:.6f}"), use_container_width=True)
    
                # Output Excel yang lengkap (Crisp, Normalisasi, Skor)
                out = pd.concat([df_crisp.add_prefix("Crisp_"), normal.add_prefix("Normalisasi_"), res_saw], axis=1)
                buf = BytesIO()
                out.to_excel(buf, index=True, engine="openpyxl")
                buf.seek(0)
    
                st.download_button("⬇️ Download hasil SAW (.xlsx)", data=buf,
                                   file_name="hasil_saw.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Terjadi kesalahan saat perhitungan SAW: {e}")


elif page == "WP":
    st.header("🔷 Hasil Weighted Product (WP)")

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
                                   file_name="hasil_wp_klasik.xlsx",
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
            res_saw, _ = saw_calc_crisp(df_crisp, ws)
            res_wp = wp_calc(df_crisp, ws)
    
            compare = pd.DataFrame({"SAW Score": res_saw["Score"], "WP Vektor V": res_wp["V"]})
    
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Tabel Perbandingan Skor")
            st.dataframe(compare.style.format("{:.6f}"), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Grafik Perbandingan")
    
            fig, ax = plt.subplots(figsize=(10, 5))
            compare.plot(kind='bar', ax=ax, rot=0)
            ax.set_ylabel("Skor Keputusan")
            ax.set_title("Perbandingan Skor SAW Klasik vs WP Klasik")
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            st.pyplot(fig)
    
            top_saw = compare["SAW Score"].idxmax()
            top_wp = compare["WP Vektor V"].idxmax()
    
            st.subheader("Kesimpulan Ranking")
            if top_saw == top_wp:
                st.success(f"🎉 Kedua metode memilih **{top_saw}** sebagai layanan cloud terbaik!")
            else:
                st.info(f"🏆 Pilihan Terbaik SAW: **{top_saw}** (Skor Tertinggi)\n\n🥇 Pilihan Terbaik WP: **{top_wp}** (Vektor V Tertinggi)")
    
            st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Terjadi kesalahan saat perhitungan perbandingan: {e}")


elif page == "Tentang":
    st.header("ℹ️ Tentang Aplikasi")
    st.markdown("""
    Aplikasi ini menggunakan metode **Multiple Attribute Decision Making (MADM)** yaitu:

    * **Simple Additive Weighting (SAW):** Menggunakan normalisasi Max/Min (untuk Benefit/Cost) diikuti dengan penjumlahan berbobot untuk mendapatkan skor akhir.
    * **Weighted Product (WP):** Menggunakan perkalian berbobot di mana kriteria *Cost* diberi pangkat negatif.

    Dibuat menggunakan **Python + Streamlit**.
    """)
