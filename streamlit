# app_singlefile.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Fuzzy MADM - Cloud Computing", layout="wide")

st.title("Fuzzy MADM — Pemilihan Layanan Cloud Computing Terbaik")

# ---------- config ----------
PROVIDERS = ["Amazon Web Services (AWS)","Google Cloud Platform (GCP)","Microsoft Azure","Alibaba Cloud","DigitalOcean"]
default_df = pd.DataFrame({
    "Biaya":[60,80,60,80,100],
    "Kinerja":[100,100,80,60,80],
    "Keamanan":[100,80,100,60,60],
    "Skalabilitas":[100,100,80,80,60],
}, index=PROVIDERS)

if "df" not in st.session_state:
    st.session_state.df = default_df.copy()

st.sidebar.header("Menu")
page = st.sidebar.radio("Pilih halaman", ["Home","Input Data","Fuzzy SAW","Fuzzy WP","Perbandingan","Tentang"])

# weights (editable)
st.sidebar.markdown("### Bobot Kriteria")
w1 = st.sidebar.slider("Biaya (w1)", 0.0, 1.0, 0.35, 0.01)
w2 = st.sidebar.slider("Kinerja (w2)", 0.0, 1.0, 0.30, 0.01)
w3 = st.sidebar.slider("Keamanan (w3)", 0.0, 1.0, 0.15, 0.01)
w4 = st.sidebar.slider("Skalabilitas (w4)", 0.0, 1.0, 0.20, 0.01)
# normalize weights
ws = np.array([w1,w2,w3,w4])
if ws.sum() == 0:
    ws = np.array([0.35,0.30,0.15,0.20])
else:
    ws = ws / ws.sum()

TYPES = ["cost","benefit","benefit","benefit"]

def normalize_saw(df):
    res = pd.DataFrame(index=df.index, columns=df.columns, dtype=float)
    for i,col in enumerate(df.columns):
        if TYPES[i]=="benefit":
            res[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
        else:
            res[col] = (df[col].max() - df[col]) / (df[col].max() - df[col].min())
    return res

def tri(v):
    a = max(0, v-0.1); m = v; b = min(1, v+0.1)
    return np.array([a,m,b])

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
    # WP tidak butuh normalisasi SAW, langsung pakai nilai asli
    S = []
    for idx in df.index:
        nilai = 1
        for j, col in enumerate(df.columns):
            if TYPES[j] == "benefit":
                nilai *= df.loc[idx, col] ** weights[j]
            else:  # cost
                nilai *= df.loc[idx, col] ** (-weights[j])
        S.append(nilai)

    S = np.array(S)
    V = S / S.sum() if S.sum() != 0 else np.zeros_like(S)

    res = pd.DataFrame({
        "S": S,
        "V": V
    }, index=df.index)

    res["Rank"] = res["V"].rank(ascending=False).astype(int)

    return res

# ---------- Pages ----------
if page=="Home":
    st.header("Ringkasan")
    st.write("Aplikasi membandingkan Fuzzy SAW & WP untuk Pemilihan Layanan Cloud Computing Terbaik.")
    st.write("Gunakan menu Input Data, lalu jalankan perhitungan SAW & WP.")
elif page=="Input Data":
    st.header("Input / Edit Data")
    edited = st.data_editor(st.session_state.df, num_rows="dynamic")
    st.session_state.df = edited
    st.download_button("Download data (.csv)", edited.to_csv().encode('utf-8'), file_name="data_input.csv")
elif page=="Fuzzy SAW":
    st.header("Hasil Fuzzy SAW")
    df = st.session_state.df.copy().apply(pd.to_numeric)
    res_saw, normal, tfn_total = saw_calc(df, ws)
    st.subheader("Normalisasi")
    st.dataframe(normal.style.format("{:.6f}"))
    st.subheader("TFN agregat (a,m,b) per provider")
    tfn_df = pd.DataFrame.from_dict(tfn_total, orient='index', columns=["a","m","b"])
    st.dataframe(tfn_df.style.format("{:.6f}"))
    st.subheader("Score & Ranking (defuzzified)")
    st.dataframe(res_saw.style.format("{:.6f}"))
    # download
    out = pd.concat([df, normal.add_prefix("norm_"), tfn_df, res_saw], axis=1)
    buf = BytesIO()
    out.to_excel(buf, index=True, engine="openpyxl")
    buf.seek(0)
    st.download_button("Download hasil SAW (.xlsx)", data=buf, file_name="hasil_saw.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
elif page=="Fuzzy WP":
    st.header("Hasil Fuzzy WP (Weighted Product)")

    df = st.session_state.df.copy().apply(pd.to_numeric)
    res_wp = wp_calc(df, ws)

    st.subheader("Hasil WP (S, V, Ranking)")
    st.dataframe(res_wp.style.format("{:.6f}"))

    # download
    buf = BytesIO()
    res_wp.to_excel(buf, index=True, engine="openpyxl")
    buf.seek(0)
    st.download_button(
        "Download hasil WP (.xlsx)", 
        data=buf, 
        file_name="hasil_wp.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.header("Perbandingan SAW vs WP")
    df = st.session_state.df.copy().apply(pd.to_numeric)
    res_saw, _, _ = saw_calc(df, ws)
    res_wp = wp_calc(df, ws)
    compare = pd.DataFrame({"SAW":res_saw["Score"], "WP":res_wp["V"]})
    st.dataframe(compare.style.format("{:.6f}"))
    fig,ax = plt.subplots(figsize=(8,4))
    compare.plot(kind='bar', ax=ax)
    ax.set_ylabel("Score")
    st.pyplot(fig)
    top_saw = compare["SAW"].idxmax(); top_top = compare["TOPSIS"].idxmax()
    if top_saw == top_top:
        st.success(f"Kedua metode memilih: {top_saw}")
    else:
        st.info(f"SAW -> {top_saw}, WP -> {top_top}")
elif page=="Tentang":
    st.header("Tentang")
    st.write("Aplikasi untuk Projek MK Logika Fuzzy — Fuzzy SAW & TOPSIS. Dibuat untuk memilih Payment Gateway (UMKM).")
