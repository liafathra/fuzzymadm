import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SAW & WP Cloud Computing", layout="wide")
st.title("☁️ Analisis Metode SAW & WP untuk Pemilihan Layanan Cloud Computing")
st.markdown("Aplikasi ini membandingkan hasil perangkingan menggunakan metode **Simple Additive Weighted (SAW)** dan **Weighted Product (WP)**.")
st.markdown("---")


# ============================================================
# 1. DEFINISI KRITERIA DAN BOBOT (Fixed)
# ============================================================
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
# 2. FUNGSI KONVERSI NILAI CRIPS (1, 2, 3, 4)
# ============================================================
def konversi_crips(kode, nilai):
    """
    Konversi nilai crips (raw data) ke nilai bobot (1, 2, 3, 4).
    """
    # C1 Biaya (Cost)
    if kode == "C1":
        if nilai <= 50: return 4 # Sangat Murah -> 4
        if nilai <= 100: return 3 # Murah (50 < Harga <= 100) -> 3
        if nilai <= 150: return 2 # Cukup Mahal (100 < Harga <= 150) -> 2
        return 1 # Mahal/Sangat Mahal (Harga > 150) -> 1

    # C2, C3, C4 (Benefit)
    if kode in ["C2", "C3", "C4"]:
        if nilai >= 90: return 4 # Sangat Baik (Skor >= 90) -> 4
        if nilai >= 80: return 3  # Baik (80 <= Skor < 90) -> 3
        if nilai >= 60: return 2  # Cukup (60 <= Skor < 80) -> 2
        return 1 # Kurang (Skor < 60) -> 1

    return None

# ============================================================
# 3. DISPLAY INFORMASI KRITERIA & CRIPS
# ============================================================

# Tampilkan Kriteria dan Bobot
st.header("1. Kriteria dan Bobot (W)")
df_kriteria = pd.DataFrame({
    "Kode": list(kriteria),
    "Kriteria": [nama_kriteria[c] for c in kriteria],
    "Atribut": [atribut[c].capitalize() for c in kriteria],
    "Bobot Normalisasi (w)": list(bobot.values())
})
st.dataframe(df_kriteria, use_container_width=True)


# Tampilkan Aturan Konversi Crips dalam Expander
with st.expander("Lihat Aturan Konversi Nilai Crips (1-4)"):
    st.markdown("**Nilai raw akan dikonversi menjadi nilai Crips (1, 2, 3, atau 4) sebelum perhitungan.**")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.subheader("C1: Biaya (Cost)")
        st.markdown("*(Semakin rendah harga, semakin tinggi Crips)*")
        df_crips_c1 = pd.DataFrame({
            "Rentang Biaya ($/bulan)": ["Harga $\le \$50$", "Harga $\le \$100$", "Harga $\le \$150$", "Harga $>\$150$"],
            "Nilai Crips": [4, 3, 2, 1]
        })
        st.dataframe(df_crips_c1, hide_index=True, use_container_width=True)

    with col_c2:
        st.subheader("C2, C3, C4: Benefit")
        st.markdown("*(Semakin tinggi skor, semakin tinggi Crips)*")
        df_crips_cben = pd.DataFrame({
            "Rentang Skor (0-100)": ["Skor $\ge 90$", "Skor $\ge 80$", "Skor $\ge 60$", "Skor $< 60$"],
            "Nilai Crips": [4, 3, 2, 1]
        })
        st.dataframe(df_crips_cben, hide_index=True, use_container_width=True)

st.markdown("---")

# ============================================================
# 4. INPUT ALTERNATIF
# ============================================================
st.header("2. Input Data Alternatif (A)")

jumlah_alt = st.selectbox("Jumlah Alternatif:", [1, 2, 3, 4, 5], index=4)

data_input = []

for i in range(jumlah_alt):
    st.markdown(f"#### 🏷️ Alternatif A{i+1}")
    
    # Gunakan kolom untuk input yang lebih rapi
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    
    with col_a:
        nama = st.text_input(f"Nama Alternatif", key=f"nama_{i}", value=f"A{i+1}")
    
    with col_b:
        c1_harga = st.number_input(
            f"C1 Biaya ($\$/bln)",
            min_value=0.0,
            step=1.0,
            format="%.2f",
            key=f"c1_{i}"
        )
    
    with col_c:
        c2_skor = st.number_input(
            f"C2 Kinerja (Skor)",
            min_value=0, max_value=100, step=1, key=f"c2_{i}"
        )
    
    with col_d:
        c3_skor = st.number_input(
            f"C3 Keamanan (Skor)",
            min_value=0, max_value=100, step=1, key=f"c3_{i}"
        )
        
    with col_e:
        c4_skor = st.number_input(
            f"C4 Skalabilitas (Skor)",
            min_value=0, max_value=100, step=1, key=f"c4_{i}"
        )

    data_input.append([
        nama,
        konversi_crips("C1", c1_harga),
        konversi_crips("C2", c2_skor),
        konversi_crips("C3", c3_skor),
        konversi_crips("C4", c4_skor),
    ])

st.markdown("---")
# ============================================================
# 5. HITUNG SAW & WP
# ============================================================
if st.button("▶️ Mulai Perhitungan SAW dan WP"):
    
    # Membuat DataFrame Crips awal
    df = pd.DataFrame(data_input, columns=["Alternatif"] + kriteria)
    df_valid = df.dropna(subset=kriteria)
    
    if df_valid.empty:
        st.error("❗ Data input tidak lengkap atau tidak valid. Mohon isi semua kriteria.")
    else:
        st.header("3. Hasil Konversi Nilai Crips")
        st.info("Nilai input (raw data) telah dikonversi menjadi Matriks Keputusan (X) dengan nilai Crips 1, 2, 3, atau 4.")
        st.dataframe(df_valid, hide_index=True, use_container_width=True)
        st.markdown("---")

        # ============================================================
        # -------------------------- SAW -----------------------------
        # ============================================================
        st.header("📘 Perhitungan Metode SAW (Simple Additive Weighted)")

        # --- 1. Normalisasi SAW ---
        st.subheader("Tahap 1: Normalisasi Matriks (R)")
        with st.expander("Lihat Detail Normalisasi"):
            st.markdown(
                """
                Matriks Crips dinormalisasi (R) dengan rumus:
                - **Benefit (C2, C3, C4):** $r_{ij} = x_{ij} / \max(x_{ij})$
                - **Cost (C1):** $r_{ij} = \min(x_{ij}) / x_{ij}$
                """
            )

            df_saw_norm = df_valid.copy()
            X = df_saw_norm[kriteria].astype(float)

            for c in kriteria:
                if atribut[c] == "benefit":
                    df_saw_norm[c] = X[c] / X[c].max()
                else:
                    df_saw_norm[c] = X[c].min() / X[c]
            
            df_saw_norm_display = df_saw_norm.copy()
            df_saw_norm_display.index = df_valid["Alternatif"]
            st.dataframe(df_saw_norm_display[kriteria], use_container_width=True)

        # --- 2. Nilai Akhir SAW ---
        st.subheader("Tahap 2: Hasil Akhir SAW dan Ranking")

        df_saw = df_saw_norm.copy()
        # Hitung Skor SAW: sum(R_ij * w_j)
        df_saw["Skor_SAW"] = sum(df_saw[c] * bobot[c] for c in kriteria)
        df_saw = df_saw.sort_values("Skor_SAW", ascending=False)
        df_saw["Ranking"] = range(1, len(df_saw) + 1)
        
        st.info(
            f"Skor akhir SAW ($V_i$) adalah hasil penjumlahan matriks ternormalisasi ($R$) dikalikan bobot ($W$): $V_i = \sum r_{ij} \cdot w_j$."
        )
        st.dataframe(df_saw[["Alternatif", "Skor_SAW", "Ranking"]], hide_index=True, use_container_width=True)

        st.markdown("---")

        # ============================================================
        # -------------------------- WP ------------------------------
        # ============================================================
        st.header("📗 Perhitungan Metode WP (Weighted Product)")
        
        df_wp = df_valid.copy()
        df_wp.set_index("Alternatif", inplace=True)
        X_wp = df_wp[kriteria].astype(float)
        bobot_array = np.array(list(bobot.values()))

        # --- 1. Vektor S_i ---
        st.subheader("Tahap 1: Perhitungan Vektor $S_i$")
        with st.expander("Lihat Detail Vektor S_i"):
            st.markdown(
                """
                Vektor $S_i$ dihitung sebagai hasil kali nilai Crips ($x_{ij}$) dipangkatkan bobot ($w_j$).
                Karena semua kriteria Crips telah diubah ke Benefit, semua pangkat bobot ($w_j$) adalah positif.
                $$S_i = \prod_{j=1}^{n} (x_{ij})^{w_j}$$
                """
            )
            # S_i = X_i1^w1 * X_i2^w2 * ... * X_in^wn
            S_i = (X_wp ** bobot_array).prod(axis=1)
            
            df_wp_result = pd.DataFrame(S_i, columns=["S_i"])
            df_wp_result.index.name = "Alternatif"
            st.dataframe(df_wp_result, use_container_width=True)

        # --- 2. Nilai Akhir WP ---
        st.subheader("Tahap 2: Nilai Preferensi $V_i$ dan Ranking")
        
        sum_S = S_i.sum()
        V_i = S_i / sum_S
        
        df_wp_result["Skor_WP"] = V_i
        df_wp_result = df_wp_result.sort_values("Skor_WP", ascending=False)
        df_wp_result["Ranking"] = range(1, len(df_wp_result) + 1)
        
        st.info(
            f"Skor akhir WP ($V_i$) adalah hasil normalisasi $S_i$ terhadap total semua $S$: $V_i = S_i / \sum S_k$."
        )
        df_wp_result.reset_index(inplace=True)
        st.dataframe(df_wp_result[["Alternatif", "Skor_WP", "Ranking"]], hide_index=True, use_container_width=True)

        st.markdown("---")

        # ============================================================
        # -------------- PERBANDINGAN RANKING SAW VS WP --------------
        # ============================================================
        st.header("📊 Perbandingan Hasil Ranking SAW dan WP")
        
        # Ambil ranking SAW
        df_saw_rank = df_saw[["Alternatif", "Ranking"]].copy()
        df_saw_rank.rename(columns={"Ranking": "Ranking_SAW"}, inplace=True)
        
        # Ambil ranking WP
        df_wp_rank = df_wp_result.copy()
        df_wp_rank.rename(columns={"Ranking": "Ranking_WP"}, inplace=True)
        
        # Gabungkan
        df_compare = pd.merge(df_saw_rank, df_wp_rank[["Alternatif", "Ranking_WP"]], on="Alternatif")
        
        # Hitung selisih peringkat
        df_compare["Selisih"] = df_compare["Ranking_WP"] - df_compare["Ranking_SAW"]
        
        # Urutkan berdasarkan ranking SAW
        df_compare = df_compare.sort_values("Ranking_SAW").reset_index(drop=True)
        
        st.subheader("Tabel Perbandingan Ranking")
        st.dataframe(df_compare, use_container_width=True)
        
        # Kesimpulan otomatis
        st.subheader("Kesimpulan Konsistensi")
        
        jumlah_sama = sum(df_compare["Ranking_SAW"] == df_compare["Ranking_WP"])
        total_alt = len(df_compare)
        
        if jumlah_sama == total_alt:
            st.success("🎉 **Kedua metode menghasilkan urutan ranking yang sama persis.** Ini menunjukkan konsistensi penuh antara SAW dan WP dalam mengevaluasi alternatif berdasarkan kriteria dan bobot yang ada.")
        elif jumlah_sama > 0:
            st.warning(f"⚠ **Terdapat perbedaan ranking** untuk sebagian alternatif. Jumlah peringkat yang sama: **{jumlah_sama}/{total_alt}**.")
            st.markdown("Perbedaan ini wajar karena metode SAW menggunakan **penjumlahan** (kompensatif), sementara metode WP menggunakan **perkalian** (non-kompensatif) dalam penentuan skor akhir.")
        else:
            st.error("❗ **Tidak ada ranking yang sama antara SAW dan WP.** Kedua metode memberikan hasil evaluasi yang sangat berbeda.")
