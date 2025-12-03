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

# ---------- config ----------
PROVIDERS = [
    "Amazon Web Services (AWS)",
    "Google Cloud Platform (GCP)",
    "Microsoft Azure",
    "Alibaba Cloud",
    "DigitalOcean"
]

default_df = pd.DataFrame({
    "Biaya":[60,80,60,80,100],
    "Kinerja":[100,100,80,60,80],
    "Keamanan":[100,80,100,60,60],
    "Skalabilitas":[100,100,80,80,60],
}, index=PROVIDERS)

if "df" not in st.session_state:
    st.session_state.df = default_df.copy()

# ---------- Sidebar ----------
st.sidebar.header("📌 Menu Navigasi")
page = st.sidebar.radio("Pilih halaman", ["Home","Input Data","Fuzzy SAW","Fuzzy WP","Perbandingan","Tentang"])

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚖️ Bobot Kriteria")

w1 = st.sidebar.slider("Biaya (w1)", 0.0, 1.0, 0.35, 0.01)
w2 = st.sidebar.slider("Kinerja (w2)", 0.0, 1.0, 0.30, 0.01)
w3 = st.sidebar.slider("Keamanan (w3)", 0.0, 1.0, 0.15, 0.01)
w4 = st.sidebar.slider("Skalabilitas (w4)", 0.0, 1.0, 0.20, 0.01)

ws = np.array([w1,w2,w3,w4])
ws = ws / ws.sum() if ws.sum() != 0 else np.array([0.35,0.30,0.15,0.20])

TYPES = ["cost","benefit","benefit","benefit"]

# ---------- FUNCTIONS ----------
def normalize_saw(df):
    res = pd.DataFrame(index=df.index, columns=df.columns, dtype=float)
    for i,col in enumerate(df.columns):
        if TYPES[i]=="benefit":
            res[col] = (df[col]-df[col].min())/(df[col].max()-df[col].min())
        else:
            res[col] = (df[col].max()-df[col])/(df[col].max()-df[col].min())
    return res

def tri(v):
    return np.array([max(0, v-0.1), v, min(1, v+0.1)])

def saw_calc(df, weights):
    normal = normalize_saw(df)
    tfn_total = {}
    scores=[]
    for idx in normal.index:
        total = np.array([0.0,0.0,0.0])
        for j,col in enumerate(normal.columns):
            t = tri(normal.loc[idx,col])
            total += t * weights[j]
        tfn_total[idx] = total
        scores.append(total.mean())
    res = pd.DataFrame({"Score":scores}, index=normal.index)
    res["Rank"] = res["Score"].rank(ascending=False).astype(int)
    return res, normal, tfn_total

def wp_calc(df, weights):
    S=[]
    for idx in df.index:
        nilai=1
        for j,col in enumerate(df.columns):
            if TYPES[j]=="benefit":
                nilai *= df.loc[idx,col] ** weights[j]
            else:
                nilai *= df.loc[idx,col] ** (-weights[j])
        S.append(nilai)

    S=np.array(S)
    V=S/S.sum()

    res=pd.DataFrame({"S":S,"V":V}, index=df.index)
    res["Rank"]=res["V"].rank(ascending=False).astype(int)
    return res

# ---------- Pages ----------
if page=="Home":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📘 Ringkasan Aplikasi")
    st.write("""
    Aplikasi ini menggunakan metode **Fuzzy SAW** dan **Fuzzy WP (Weighted Product)**  
    untuk menentukan *layanan Cloud Computing terbaik* berdasarkan empat kriteria:

    - 💰 **Biaya**  
    - ⚡ **Kinerja**  
    - 🔐 **Keamanan**  
    - 📈 **Skalabilitas**

    Silakan buka menu **Input Data** untuk mengisi atau mengedit data alternatif sebelum melakukan perhitungan.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

elif page=="Input Data":
    st.header("📝 Input / Edit Data Alternatif")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    edited = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        use_container_width=True,
    )
    st.session_state.df = edited

    st.download_button("⬇️ Download data (.csv)", edited.to_csv().encode('utf-8'),
                       file_name="data_input.csv")
    st.markdown("</div>", unsafe_allow_html=True)

elif page=="Fuzzy SAW":
    st.header("🔷 Hasil Fuzzy SAW")

    df = st.session_state.df.copy().apply(pd.to_numeric)
    res_saw, normal, tfn_total = saw_calc(df, ws)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Normalisasi SAW")
    st.dataframe(normal.style.format("{:.6f}"), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("TFN Agregat (a, m, b)")
    tfn_df = pd.DataFrame.from_dict(tfn_total, orient='index', columns=["a","m","b"])
    st.dataframe(tfn_df.style.format("{:.6f}"), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Skor & Ranking")
    st.dataframe(res_saw.style.format("{:.6f}"), use_container_width=True)

    out = pd.concat([df, normal.add_prefix("norm_"), tfn_df, res_saw], axis=1)
    buf = BytesIO()
    out.to_excel(buf, index=True, engine="openpyxl")
    buf.seek(0)

    st.download_button("⬇️ Download hasil SAW", data=buf,
                       file_name="hasil_saw.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.markdown("</div>", unsafe_allow_html=True)

elif page=="Fuzzy WP":
    st.header("🔷 Hasil Fuzzy WP (Weighted Product)")

    df = st.session_state.df.copy().apply(pd.to_numeric)
    res_wp = wp_calc(df, ws)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Hasil WP (S, V, Ranking)")
    st.dataframe(res_wp.style.format("{:.6f}"), use_container_width=True)

    buf = BytesIO()
    res_wp.to_excel(buf, index=True, engine="openpyxl")
    buf.seek(0)

    st.download_button("⬇️ Download hasil WP",
                       data=buf,
                       file_name="hasil_wp.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.markdown("</div>", unsafe_allow_html=True)

elif page=="Perbandingan":
    st.header("📊 Perbandingan SAW vs WP")

    df = st.session_state.df.copy().apply(pd.to_numeric)
    res_saw, _, _ = saw_calc(df, ws)
    res_wp = wp_calc(df, ws)

    compare = pd.DataFrame({"SAW":res_saw["Score"], "WP":res_wp["V"]})

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Tabel Perbandingan")
    st.dataframe(compare.style.format("{:.6f}"), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Grafik Perbandingan")

    fig, ax = plt.subplots(figsize=(8,4))
    compare.plot(kind='bar', ax=ax)
    ax.set_ylabel("Skor")
    ax.set_title("Perbandingan Skor Fuzzy SAW vs WP")
    st.pyplot(fig)

    top_saw = compare["SAW"].idxmax()
    top_wp = compare["WP"].idxmax()

    if top_saw == top_wp:
        st.success(f"🎉 Kedua metode memilih **{top_saw}** sebagai layanan terbaik!")
    else:
        st.info(f"SAW memilih: **{top_saw}**\n\nWP memilih: **{top_wp}**")

    st.markdown("</div>", unsafe_allow_html=True)

elif page=="Tentang":
    st.header("ℹ️ Tentang Aplikasi")
    st.markdown("""
    Aplikasi ini dibuat untuk kebutuhan **Projek Akhir Mata Kuliah Logika Fuzzy**  
    dengan topik *Fuzzy Multiple Attribute Decision Making (MADM)* —  
    menggunakan metode **Fuzzy SAW** dan **Weighted Product (WP)**.

    Dibuat dengan ❤️ menggunakan **Python + Streamlit**.
    """)

