import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SAW & WP Cloud Computing", layout="wide")
st.title("Analisis Metode SAW & WP untuk Pemilihan Layanan Cloud Computing")

# ============================================================
# 1. DEFINISI KRITERIA (Disesuaikan dari Excel)
# ============================================================
# Kriteria: C1-C4 (Biaya, Kinerja, Keamanan, Skalabilitas)
kriteria = ["C1", "C2", "C3", "C4"]
nama_kriteria = {
    "C1": "Biaya",
    "C2": "Kinerja",
    "C3": "Keamanan",
    "C4": "Skalabilitas"
}
atribut = {"C1": "cost", "C2": "benefit", "C3": "benefit", "C4": "benefit"}

# Bobot Normalisasi (wj) dari Excel: 0.35, 0.3, 0.15, 0.2
bobot = {"C1": 0.35, "C2": 0.30, "C3": 0.15, "C4": 0.20}

# ============================================================
# 2. FUNGSI KONVERSI NILAI CRIPS (Dibuat Sendiri Berdasarkan Data Excel)
# ============================================================
def konversi_crips(kode, nilai):
    """
    Konversi nilai crips (raw data) ke nilai bobot (40, 60, 80, 100).
    """
    # C1 Biaya (Cost) - Input: Harga ($/bln)
    # Rentang berdasarkan data: $50(100), $90/$100(80), $140/$150(60)
    if kode == "C1":
        if nilai <= 50: return 100 # Sangat Murah -> 100
        if nilai <= 100: return 80 # Murah (50 < Harga <= 100) -> 80
        if nilai <= 150: return 60 # Cukup Mahal (100 < Harga <= 150) -> 60
        return 40 # Mahal/Sangat Mahal (Harga > 150) -> 40

    # C2, C3, C4 (Benefit) - Input: Skor (0-100)
    # Rentang berdasarkan data: 90-100(100), 80-85(80), 60-65(60)
    if kode in ["C2", "C3", "C4"]:
        if nilai >= 90: return 100 # Sangat Baik (Skor >= 90) -> 100
        if nilai >= 80: return 80  # Baik (80 <= Skor < 90) -> 80
        if nilai >= 60: return 60  # Cukup (60 <= Skor < 80) -> 60
        return 40 # Kurang (Skor < 60) -> 40

    return None

# ============================================================
# INPUT JUMLAH ALTERNATIF
# ============================================================
st.subheader("Input Alternatif yang Akan Dianalisis")

jumlah_alt = st.selectbox("Jumlah Alternatif:", [1, 2, 3, 4, 5], index=4)

# DataFrame penampung
data_input = []

for i in range(jumlah_alt):
    st.markdown(f"### Alternatif A{i+1}")
    nama = st.text_input(f"Nama Alternatif A{i+1}", key=f"nama_{i}")

    # C1 Biaya ($/bln)
    c1_harga = st.number_input(
        f"C1 Biaya ($\$/bulan)",
        min_value=0.0,
        step=1.0,
        format="%.2f",
        key=f"c1_{i}"
    )

    # C2 Kinerja (Skor 0-100)
    c2_skor = st.number_input(
        f"C2 Kinerja (Skor 0-100)",
        min_value=0,
        max_value=100,
        step=1,
        key=f"c2_{i}"
    )
    
    # C3 Keamanan (Skor 0-100)
    c3_skor = st.number_input(
        f"C3 Keamanan (Skor 0-100)",
        min_value=0,
        max_value=100,
        step=1,
        key=f"c3_{i}"
    )
    
    # C4 Skalabilitas (Skor 0-100)
    c4_skor = st.number_input(
        f"C4 Skalabilitas (Skor 0-100)",
        min_value=0,
        max_value=100,
        step=1,
        key=f"c4_{i}"
    )

    data_input.append([
        nama,
        konversi_crips("C1", c1_harga),
        konversi_crips("C2", c2_skor),
        konversi_crips("C3", c3_skor),
        konversi_crips("C4", c4_skor),
    ])


# ============================================================
# HITUNG SAW & WP
# ============================================================
if st.button("Hitung SAW dan WP"):
    df = pd.DataFrame(data_input, columns=["Alternatif"] + kriteria)
    st.subheader("📌 Tabel Nilai Crips")
    
    # Filter dan tampilkan hanya data dengan nilai crips valid
    df_valid = df.dropna(subset=kriteria)
    st.dataframe(df_valid)

    # ============================================================
    # -------------------------- SAW -----------------------------
    # ============================================================
    st.header("📘 Perhitungan Metode SAW")

    # --- Normalisasi SAW ---
    st.subheader("Tahap Normalisasi SAW")

    df_saw_norm = df_valid.copy()
    X = df_saw_norm[kriteria].astype(float)

    for c in kriteria:
        if atribut[c] == "benefit":
            # Benefit: x_ij / max(x_j)
            df_saw_norm[c] = X[c] / X[c].max()
        else:
            # Cost: min(x_j) / x_ij
            df_saw_norm[c] = X[c].min() / X[c]

    df_saw_norm_display = df_saw_norm.copy()
    df_saw_norm_display.index = [f"A{i+1}" for i in range(len(df_valid))]

    st.dataframe(df_saw_norm_display[kriteria])

    # --- Nilai Akhir SAW ---
    st.subheader("Nilai Akhir SAW dan Ranking")

    df_saw = df_saw_norm.copy()
    # Hitung Skor SAW: sum(R_ij * w_j)
    df_saw["Skor_SAW"] = sum(df_saw[c] * bobot[c] for c in kriteria)
    df_saw = df_saw.sort_values("Skor_SAW", ascending=False)
    df_saw["Ranking"] = range(1, len(df_saw) + 1)

    st.dataframe(df_saw[["Alternatif", "Skor_SAW", "Ranking"]])

    # ============================================================
    # -------------------------- WP ------------------------------
    # ============================================================
    st.header("📗 Perhitungan Metode WP")
    
    df_wp = df_valid.copy()
    df_wp.set_index("Alternatif", inplace=True)
    X_wp = df_wp[kriteria].astype(float)
    
    # 1. Hitung Vektor Bobot W (sudah tersedia di 'bobot')
    # Bobot sudah normalisasi, dan semua positif karena nilai crips (X_ij) sudah diubah menjadi Benefit.
    bobot_array = np.array(list(bobot.values()))

    # 2. Hitung Vektor S_i: S_i = Product(X_ij^w_j)
    st.subheader("Vektor Bobot dan Vektor $S_i$")
    
    # S_i = X_i1^w1 * X_i2^w2 * ... * X_in^wn
    S_i = (X_wp ** bobot_array).prod(axis=1)
    
    # Tampilkan S_i dalam DataFrame
    df_wp_result = pd.DataFrame(S_i, columns=["S_i"])
    df_wp_result.index.name = "Alternatif"
    st.dataframe(df_wp_result)

    # 3. Hitung Vektor V_i: V_i = S_i / Sum(S_k)
    st.subheader("Nilai Preferensi $V_i$ dan Ranking")
    
    sum_S = S_i.sum()
    V_i = S_i / sum_S
    
    df_wp_result["Skor_WP"] = V_i
    df_wp_result = df_wp_result.sort_values("Skor_WP", ascending=False)
    df_wp_result["Ranking"] = range(1, len(df_wp_result) + 1)
    
    st.dataframe(df_wp_result[["Skor_WP", "Ranking"]])

    # ============================================================
    # -------------- PERBANDINGAN RANKING SAW VS WP --------------
    # ============================================================
    st.header("📊 Perbandingan Hasil Ranking SAW dan WP")
    
    # Ambil ranking SAW
    df_saw_rank = df_saw[["Alternatif", "Ranking"]].copy()
    df_saw_rank.rename(columns={"Ranking": "Ranking_SAW"}, inplace=True)
    
    # Ambil ranking WP
    df_wp_rank = df_wp_result.copy()
    df_wp_rank.reset_index(inplace=True)
    df_wp_rank.rename(columns={"index": "Alternatif", "Ranking": "Ranking_WP"}, inplace=True)
    
    # Gabungkan
    df_compare = pd.merge(df_saw_rank, df_wp_rank[["Alternatif", "Ranking_WP"]], on="Alternatif")
    
    # Hitung selisih peringkat
    df_compare["Selisih"] = df_compare["Ranking_WP"] - df_compare["Ranking_SAW"]
    
    # Urutkan berdasarkan ranking SAW
    df_compare = df_compare.sort_values("Ranking_SAW").reset_index(drop=True)
    
    st.dataframe(df_compare)
    
    # Kesimpulan otomatis
    st.subheader("📌 Analisis Singkat Konsistensi Ranking")
    
    jumlah_sama = sum(df_compare["Ranking_SAW"] == df_compare["Ranking_WP"])
    total_alt = len(df_compare)
    
    if jumlah_sama == total_alt:
        st.success("🎉 **Kedua metode menghasilkan urutan ranking yang sama persis.** Ini menunjukkan konsistensi penuh antara SAW dan WP.")
    elif jumlah_sama > 0:
        st.warning(f"⚠ **Sebagian alternatif memiliki ranking yang sama**, tetapi tidak semuanya.\n\n"
                    f"- Jumlah peringkat yang sama: **{jumlah_sama}/{total_alt}**\n"
                    f"- Ada perbedaan yang berarti antara metode SAW dan WP.")
    else:
        st.error("❗ **Tidak ada ranking yang sama antara SAW dan WP.** "
                  "Ini menunjukkan kedua metode memberikan perspektif berbeda dalam evaluasi alternatif.")
