import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="SAW & WP Cloud Computing", layout="wide")
st.title("☁️ Analisis Metode SAW & WP untuk Pemilihan Layanan Cloud Computing")
st.markdown("Aplikasi ini membandingkan hasil perangkingan layanan Cloud Computing menggunakan metode **Simple Additive Weighting (SAW)** dan **Weighted Product (WP)**.")

# ============================================================
# 1. DEFINISI KRITERIA
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

# Tampilkan Ringkasan Kriteria
st.header("📋 Definisi Kriteria")
st.markdown("Berikut adalah kriteria yang digunakan beserta bobot dan tipenya:")

# Buat DataFrame untuk Kriteria
df_kriteria = pd.DataFrame({
    "Kode": kriteria,
    "Nama Kriteria": [nama_kriteria[c] for c in kriteria],
    "Atribut": [atribut[c].capitalize() for c in kriteria],
    "Bobot ($w_j$)": [bobot[c] for c in kriteria]
})
st.dataframe(df_kriteria.set_index("Kode"), use_container_width=True)

# ============================================================
# 2. FUNGSI KONVERSI NILAI CRIPS (Disesuaikan ke 1, 2, 3, 4)
# ============================================================
def konversi_crips(kode, nilai):
    """
    Konversi nilai crips (raw data) ke nilai bobot (1, 2, 3, 4).
    """
    # C1 Biaya (Cost) - Input: Harga ($/bln)
    if kode == "C1":
        if nilai <= 50: return 4
        if nilai <= 100: return 3
        if nilai <= 150: return 2
        return 1

    # C2, C3, C4 (Benefit) - Input: Skor (0-100)
    if kode in ["C2", "C3", "C4"]:
        if nilai >= 90: return 4
        if nilai >= 80: return 3
        if nilai >= 60: return 2
        return 1

    return None

# ============================================================
# INPUT JUMLAH ALTERNATIF
# ============================================================
st.header("📝 Input Data Alternatif")

col1_jumlah, col2_kosong = st.columns([1, 3])
with col1_jumlah:
    jumlah_alt = st.selectbox("Jumlah Alternatif:", [1, 2, 3, 4, 5], index=4)

st.subheader("Masukkan Detail Setiap Alternatif:")

# DataFrame penampung
data_input = []

# Kontainer untuk input alternatif
input_container = st.container()

with input_container:
    cols = st.columns(jumlah_alt)
    
    for i in range(jumlah_alt):
        with cols[i]:
            st.markdown(f"### Alternatif A{i+1}")
            
            # Use a box/container for visual grouping
            with st.container(border=True):
                nama = st.text_input(f"Nama Alternatif A{i+1}", key=f"nama_{i}", value=f"Layanan {i+1}")

                st.markdown("**Nilai Raw Data (Crips)**")

                # C1 Biaya ($/bln)
                c1_harga = st.number_input(
                    f"C1: {nama_kriteria['C1']} ($/bulan)",
                    min_value=0.0,
                    step=1.0,
                    format="%.2f",
                    key=f"c1_{i}",
                    value=float(np.random.randint(40, 200)) # Nilai acak untuk contoh
                )

                # ------------------------------------------------------------------
                # PERUBAHAN: Mengganti st.slider menjadi st.number_input untuk C2, C3, C4
                # St.number_input memberikan rentang min/max, tetapi juga dapat diketik manual.
                # ------------------------------------------------------------------
                
                # C2 Kinerja (Skor 0-100)
                c2_skor = st.number_input(
                    f"C2: {nama_kriteria['C2']} (Skor 0-100)",
                    min_value=0,
                    max_value=100,
                    step=1,
                    key=f"c2_{i}",
                    value=np.random.randint(60, 100) # Nilai acak untuk contoh
                )
                
                # C3 Keamanan (Skor 0-100)
                c3_skor = st.number_input(
                    f"C3: {nama_kriteria['C3']} (Skor 0-100)",
                    min_value=0,
                    max_value=100,
                    step=1,
                    key=f"c3_{i}",
                    value=np.random.randint(60, 100) # Nilai acak untuk contoh
                )
                
                # C4 Skalabilitas (Skor 0-100)
                c4_skor = st.number_input(
                    f"C4: {nama_kriteria['C4']} (Skor 0-100)",
                    min_value=0,
                    max_value=100,
                    step=1,
                    key=f"c4_{i}",
                    value=np.random.randint(60, 100) # Nilai acak untuk contoh
                )
                # ------------------------------------------------------------------
                # AKHIR PERUBAHAN
                # ------------------------------------------------------------------


                data_input.append([
                    nama,
                    konversi_crips("C1", c1_harga),
                    konversi_crips("C2", c2_skor),
                    konversi_crips("C3", c3_skor),
                    konversi_crips("C4", c4_skor),
                ])

st.markdown("---")

# ============================================================
# HITUNG SAW & WP
# ============================================================
if st.button("🚀 Mulai Perhitungan SAW dan WP", type="primary"):
    df = pd.DataFrame(data_input, columns=["Alternatif"] + kriteria)
    
    # Filter dan tampilkan hanya data dengan nilai crips valid
    df_valid = df.dropna(subset=kriteria)
    
    if df_valid.empty:
        st.warning("Tidak ada data alternatif yang valid. Pastikan semua input terisi.")
        st.stop()

    st.subheader("✅ Matriks Keputusan Berdasarkan Nilai Crips (1 - 4)")
    # Ganti nama kolom C1, C2, dst. dengan nama kriteria
    df_crips_display = df_valid.rename(columns=nama_kriteria).set_index("Alternatif")
    df_crips_display.columns.name = "Kriteria"
    st.dataframe(df_crips_display)

    st.markdown("---")

    # ============================================================
    # -------------------------- SAW -----------------------------
    # ============================================================
    st.header("📘 Perhitungan Metode Simple Additive Weighting (SAW)")

    # --- Normalisasi SAW ---
    st.subheader("Tahap 1: Normalisasi Matriks Keputusan ($R$)")
    st.markdown("Nilai normalisasi $r_{ij}$ dihitung dengan rumus:")
    
    col_saw_rumus1, col_saw_rumus2 = st.columns(2)
    with col_saw_rumus1:
        st.markdown("Untuk kriteria **Benefit** (C2, C3, C4):")
        st.latex(r'''r_{ij} = \frac{x_{ij}}{\max_i(x_{ij})}''')
    with col_saw_rumus2:
        st.markdown("Untuk kriteria **Cost** (C1):")
        st.latex(r'''r_{ij} = \frac{\min_i(x_{ij})}{x_{ij}}''')

    df_saw_norm = df_valid.copy()
    X = df_saw_norm[kriteria].astype(float)

    for c in kriteria:
        if atribut[c] == "benefit":
            # Benefit: x_ij / max(x_j)
            df_saw_norm[c] = X[c] / X[c].max()
        else:
            # Cost: min(x_j) / x_ij
            df_saw_norm[c] = X[c].min() / X[c]

    # Tampilkan tabel normalisasi dengan nama kolom yang jelas dan format 3 desimal
    df_saw_norm_display = df_saw_norm.copy()
    df_saw_norm_display = df_saw_norm_display.rename(columns=nama_kriteria)
    df_saw_norm_display.set_index("Alternatif", inplace=True)
    df_saw_norm_display.columns.name = "Kriteria"
    st.dataframe(df_saw_norm_display.apply(lambda x: x.map('{:.3f}'.format)), use_container_width=True)

    # --- Nilai Akhir SAW ---
    st.subheader("Tahap 2: Perhitungan Nilai Preferensi ($V_i$) dan Ranking")
    st.markdown("Skor akhir untuk setiap alternatif ($V_i$) dihitung dengan menjumlahkan hasil kali normalisasi dan bobot kriteria:")
    st.latex(r'''V_i = \sum_{j=1}^n w_j \cdot r_{ij}''')


    df_saw = df_saw_norm.copy()
    # Hitung Skor SAW: sum(R_ij * w_j)
    df_saw["Skor_SAW"] = sum(df_saw[c] * bobot[c] for c in kriteria)
    df_saw = df_saw.sort_values("Skor_SAW", ascending=False)
    df_saw["Ranking"] = range(1, len(df_saw) + 1)

    # Tampilkan hasil SAW dengan Skor format 3 desimal
    df_saw_result_display = df_saw[["Alternatif", "Skor_SAW", "Ranking"]].copy()
    df_saw_result_display["Skor_SAW"] = df_saw_result_display["Skor_SAW"].map('{:.3f}'.format)
    st.dataframe(df_saw_result_display.set_index("Alternatif"), use_container_width=True)

    st.markdown("---")

    # ============================================================
    # -------------------------- WP ------------------------------
    # ============================================================
    st.header("📗 Perhitungan Metode Weighted Product (WP)")
    
    df_wp = df_valid.copy()
    df_wp.set_index("Alternatif", inplace=True)
    X_wp = df_wp[kriteria].astype(float)
    
    # 1. Hitung Bobot W* (Pangkat WP)
    st.subheader("Tahap 1: Vektor Bobot $W^*_j$ (Pangkat)")
    st.markdown("Bobot untuk kriteria **Cost** (C1: Biaya) harus **negatif**.")
    
    # Bobot yang disesuaikan untuk WP (Cost = negatif, Benefit = positif)
    bobot_disesuaikan = {}
    for c in kriteria:
        if atribut[c] == "cost":
            bobot_disesuaikan[c] = -bobot[c]
        else:
            bobot_disesuaikan[c] = bobot[c]
    
    bobot_array_wp = np.array(list(bobot_disesuaikan.values()))
    
    # Tampilkan bobot yang disesuaikan
    df_bobot_wp = pd.DataFrame({
        "Kode": kriteria,
        "Atribut": [atribut[c].capitalize() for c in kriteria],
        "Bobot": [bobot[c] for c in kriteria],
        "Pangkat WP": [f"{v:.2f}" for v in bobot_array_wp]
    })
    st.dataframe(df_bobot_wp.set_index("Kode"), use_container_width=True)

    # 2. Hitung Vektor S_i: S_i = Product(X_ij^w*_j)
    st.subheader("Tahap 2: Perhitungan Vektor $S_i$")
    st.markdown("Nilai $S_i$ dihitung sebagai hasil kali nilai kriteria $x_{ij}$ yang dipangkatkan dengan bobot $w^*_j$:")
    st.latex(r'''S_i = \prod_{j=1}^n x_{ij}^{w^*_j} \text{, di mana } w^*_j = \begin{cases} w_j & \text{untuk benefit} \\ -w_j & \text{untuk cost} \end{cases}''')
    
    # HITUNG S_i MENGGUNAKAN ARRAY BOBOT YANG SUDAH DISESUAIKAN
    S_i = (X_wp ** bobot_array_wp).prod(axis=1)
    
    # Tampilkan S_i dalam DataFrame dengan format 4 desimal
    df_wp_result = pd.DataFrame(S_i, columns=["S_i"])
    df_wp_result.index.name = "Alternatif"
    S_i_float = S_i.copy() 
    df_wp_result["S_i"] = df_wp_result["S_i"].map('{:.4f}'.format)
    st.dataframe(df_wp_result, use_container_width=True)

    # 3. Hitung Vektor V_i: V_i = S_i / Sum(S_k)
    st.subheader("Tahap 3: Perhitungan Nilai Preferensi $V_i$ dan Ranking")
    st.markdown("Nilai preferensi $V_i$ dihitung dengan membagi $S_i$ dengan total $S_k$ dari semua alternatif:")
    st.latex(r'''V_i = \frac{S_i}{\sum_{k=1}^m S_k}''')

    # Gunakan S_i_float untuk perhitungan V_i yang akurat
    sum_S = S_i_float.sum()
    V_i = S_i_float / sum_S
    
    df_wp_result["Skor_WP"] = V_i
    df_wp_result = df_wp_result.sort_values("Skor_WP", ascending=False)
    df_wp_result["Ranking"] = range(1, len(df_wp_result) + 1)
    
    # Tampilkan hasil WP dengan Skor format 4 desimal
    df_wp_final_display = df_wp_result[["Skor_WP", "Ranking"]].copy()
    df_wp_final_display["Skor_WP"] = df_wp_final_display["Skor_WP"].map('{:.4f}'.format)
    st.dataframe(df_wp_final_display, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # -------------- PERBANDINGAN RANKING SAW VS WP --------------
    # ============================================================
    st.header("📊 Perbandingan Hasil Ranking SAW dan WP")
    
    # Ambil ranking SAW
    df_saw_rank = df_saw[["Alternatif", "Ranking"]].copy()
    df_saw_rank.rename(columns={"Ranking": "Ranking_SAW"}, inplace=True)
    
    # Ambil ranking WP
    df_wp_result.reset_index(inplace=True)
    df_wp_rank = df_wp_result.copy()
    df_wp_rank.rename(columns={"Alternatif": "Alternatif", "Ranking": "Ranking_WP"}, inplace=True)
    
    # Gabungkan
    df_compare = pd.merge(df_saw_rank, df_wp_rank[["Alternatif", "Ranking_WP"]], on="Alternatif")
    
    # Hitung selisih peringkat
    df_compare["Selisih"] = df_compare["Ranking_WP"] - df_compare["Ranking_SAW"]
    
    # Urutkan berdasarkan ranking SAW
    df_compare = df_compare.sort_values("Ranking_SAW").reset_index(drop=True)
    df_compare.index = df_compare.index + 1 # Jadikan index sebagai no urut
    df_compare.index.name = "No."

    st.dataframe(df_compare, use_container_width=True)
    
    # Kesimpulan otomatis
    st.subheader("📌 Analisis Singkat Konsistensi Ranking")
    
    jumlah_sama = sum(df_compare["Ranking_SAW"] == df_compare["Ranking_WP"])
    total_alt = len(df_compare)
    
    st.markdown(f"Dari **{total_alt}** alternatif, terdapat **{jumlah_sama}** alternatif yang memiliki urutan ranking yang sama persis antara metode SAW dan WP.")

    if jumlah_sama == total_alt:
        st.success("🎉 **Kedua metode menghasilkan urutan ranking yang sama persis.** Ini menunjukkan konsistensi penuh antara SAW dan WP.")
    elif jumlah_sama > 0:
        st.info(f"**Terdapat perbedaan ranking pada beberapa alternatif** (Sebanyak {total_alt - jumlah_sama} alternatif mengalami perbedaan).")
    else:
        st.error("❗ **Tidak ada ranking yang sama antara SAW dan WP.** "
                  "Ini menunjukkan kedua metode memberikan perspektif berbeda yang signifikan dalam evaluasi alternatif.")

    st.markdown("---")
    # Tampilkan alternatif terbaik
    alt_saw_terbaik = df_saw_rank.loc[df_saw_rank["Ranking_SAW"] == 1, "Alternatif"].iloc[0]
    alt_wp_terbaik = df_wp_rank.loc[df_wp_rank["Ranking_WP"] == 1, "Alternatif"].iloc[0]

    st.subheader("🏆 Kesimpulan Alternatif Terbaik")
    if alt_saw_terbaik == alt_wp_terbaik:
        st.balloons()
        st.success(f"**Alternatif Terbaik** menurut kedua metode (SAW & WP) adalah **{alt_saw_terbaik}**.")
    else:
        st.warning(f"Alternatif terbaik berbeda antara kedua metode:")
        st.markdown(f"* **SAW:** **{alt_saw_terbaik}**")
        st.markdown(f"* **WP:** **{alt_wp_terbaik}**")
        st.markdown("Perbedaan ini mungkin disebabkan oleh fokus WP yang mengalikan bobot kriteria (lebih sensitif terhadap nilai yang sangat rendah/tinggi) dibandingkan SAW yang menjumlahkan.")
