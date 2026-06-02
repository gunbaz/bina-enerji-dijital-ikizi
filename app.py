import math
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

st.set_page_config(page_title="Bina Enerji Dijital İkizi", layout="wide")

st.markdown("""
<style>
.kpi-box {
    background: #1e2a3a; border-radius: 12px;
    padding: 20px 24px; text-align: center; border: 1px solid #2e4060;
}
.kpi-title { color: #8ab4d4; font-size: 14px; margin-bottom: 6px; }
.kpi-value { color: #ffffff; font-size: 36px; font-weight: 700; }
.kpi-delta { font-size: 13px; margin-top: 4px; }
.green { color: #4caf50; } .red { color: #ef5350; }
.section-title {
    font-size: 20px; font-weight: 600; color: #cfe2ff;
    margin: 28px 0 12px 0; border-bottom: 1px solid #2e4060; padding-bottom: 6px;
}
.badge {
    display:inline-block; padding:3px 10px; border-radius:20px;
    font-size:12px; font-weight:600;
}
.badge-ml  { background:#1565c0; color:#fff; }
.badge-kural { background:#4a148c; color:#fff; }
</style>
""", unsafe_allow_html=True)

st.title("🏢 Bina Enerji Yönetimi — Dijital İkiz")

# ── SOL PANEL ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🌡️ Hava & Bina Koşulları")
    temel_sicaklik   = st.slider("Gün Temel Sıcaklığı (°C)",  10, 42, 26)
    sicaklik_amplitud = st.slider("Sıcaklık Dalgalanması (±°C)", 0, 10, 5)

    st.divider()
    st.header("👥 Bina Kullanım Profili")
    mesai_baslangic = st.slider("Mesai Başlangıcı (saat)", 6, 10, 8)
    mesai_bitis     = st.slider("Mesai Bitişi (saat)",     14, 22, 18)
    maks_kisi       = st.slider("Maksimum Kişi Sayısı",    5, 100, 45)

    st.divider()
    st.header("⚡ Klima & Maliyet")
    klima_gucu   = st.slider("Klima Maks. Gücü (kW)",  1.0, 5.0, 2.5, 0.5)
    standby_gucu = st.slider("Standby Gücü (kW)",      0.01, 0.20, 0.05, 0.01)
    fiyat_normal = st.slider("Normal Tarife (TL/kWh)", 1.0, 4.0, 2.5, 0.5)
    fiyat_pik    = st.slider("Pik Tarife (TL/kWh)",    2.0, 8.0, 4.5, 0.5)

    st.divider()
    st.header("🤖 ML Modeli")
    n_trees   = st.slider("Karar Ağacı Sayısı",  10, 200, 80, 10,
                          help="Random Forest'taki ağaç sayısı. Artırdıkça model daha güçlü ama yavaş eğitilir.")
    max_depth = st.slider("Ağaç Derinliği",       2,  20,  8,
                          help="Her ağacın ne kadar derin öğreneceği. Fazla derin = ezber riski.")

# ── 24 SAATLIK SENARYO VERİSİ ─────────────────────────────────────────────────
saatler = list(range(24))

dis_sicakliklar = [
    round(temel_sicaklik + sicaklik_amplitud * math.sin(math.pi * (h - 5) / 9), 1)
    if 5 <= h <= 14
    else round(temel_sicaklik - sicaklik_amplitud * abs(math.sin(math.pi * (h - 14) / 14)), 1)
    for h in saatler
]

doluluk = []
for h in saatler:
    if h < mesai_baslangic or h >= mesai_bitis:
        doluluk.append(0)
    else:
        mid   = (mesai_baslangic + mesai_bitis) / 2
        sigma = (mesai_bitis - mesai_baslangic) / 4
        doluluk.append(max(2, int(maks_kisi * math.exp(-0.5 * ((h - mid) / sigma) ** 2))))

elektrik_fiyatlari = [
    fiyat_pik if (12 <= h <= 15) or (18 <= h <= 22) else fiyat_normal
    for h in saatler
]

df = pd.DataFrame({
    "Saat":         saatler,
    "Dis_Sicaklik": dis_sicakliklar,
    "Insan_Sayisi": doluluk,
    "Fiyat":        elektrik_fiyatlari,
})

# ── GELENEKSEL SİSTEM (If/Else) ────────────────────────────────────────────────
def geleneksel_sim(row):
    if row.Insan_Sayisi > 0 or row.Dis_Sicaklik > 24:
        return klima_gucu
    return standby_gucu

df["Gel_kWh"] = df.apply(geleneksel_sim, axis=1)
df["Gel_TL"]  = df["Gel_kWh"] * df["Fiyat"]

# ── ML MODELİ EĞİTİMİ ─────────────────────────────────────────────────────────
# Eğitim verisi: 365 günlük sentetik geçmiş
# Özellikler: saat, dış sıcaklık, kişi sayısı, tarife
# Hedef: optimal enerji tüketimi (geleneksel sisteme göre %20-40 daha az, akıllı kurallara göre)

@st.cache_resource(show_spinner="🤖 ML modeli eğitiliyor...")
def model_egit(n_trees, max_depth, klima_gucu, standby_gucu, fiyat_pik):
    np.random.seed(42)
    n_days   = 365
    gun_guvec = []

    for _ in range(n_days):
        base_T = np.random.uniform(10, 40)
        amp_T  = np.random.uniform(2, 10)
        for h in range(24):
            T   = base_T + amp_T * math.sin(math.pi * (h - 5) / 9) if 5 <= h <= 14 \
                  else base_T - amp_T * abs(math.sin(math.pi * (h - 14) / 14))
            N   = int(np.random.randint(0, 50) * (1 if 8 <= h <= 18 else 0))
            f   = fiyat_pik if (12 <= h <= 15) or (18 <= h <= 22) else 2.5
            # Optimal güç: uzman tarafından belirlenmiş hedef (ML'in öğreneceği şey)
            if N == 0:
                optimal = standby_gucu
            elif T >= 32 and N >= 30:
                optimal = klima_gucu                        # çok sıcak + kalabalık → tam güç
            elif f == fiyat_pik and N < 15:
                optimal = klima_gucu * 0.30 + np.random.normal(0, 0.03)  # pahalı + boş → eko
            elif f == fiyat_pik:
                optimal = klima_gucu * 0.65 + np.random.normal(0, 0.05)  # pahalı + dolu → normal
            elif T >= 28:
                optimal = klima_gucu * 0.80 + np.random.normal(0, 0.05)
            elif T >= 24:
                optimal = klima_gucu * 0.55 + np.random.normal(0, 0.04)
            else:
                optimal = klima_gucu * 0.35 + np.random.normal(0, 0.03)

            optimal = float(np.clip(optimal, standby_gucu, klima_gucu))
            gun_guvec.append([h, T, N, f, optimal])

    egitim = pd.DataFrame(gun_guvec, columns=["Saat", "Sicaklik", "Kisi", "Fiyat", "OptimalGuc"])
    X = egitim[["Saat", "Sicaklik", "Kisi", "Fiyat"]].values
    y = egitim["OptimalGuc"].values

    model = RandomForestRegressor(
        n_estimators=n_trees,
        max_depth=max_depth,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X, y)
    return model

model = model_egit(n_trees, max_depth, klima_gucu, standby_gucu, fiyat_pik)

# ── ML TAHMİNLERİ ──────────────────────────────────────────────────────────────
X_pred      = df[["Saat", "Dis_Sicaklik", "Insan_Sayisi", "Fiyat"]].values
ml_tahminler = model.predict(X_pred)
ml_tahminler = np.clip(ml_tahminler, standby_gucu, klima_gucu)

df["ML_kWh"] = ml_tahminler
df["ML_TL"]  = df["ML_kWh"] * df["Fiyat"]

# Özellik önem skoru
onem = model.feature_importances_
onem_df = pd.DataFrame({
    "Özellik": ["Saat", "Dış Sıcaklık", "Kişi Sayısı", "Elektrik Tarife"],
    "Önem (%)": (onem * 100).round(1)
}).sort_values("Önem (%)", ascending=True)

# ── KPI ───────────────────────────────────────────────────────────────────────
gel_enerji  = df["Gel_kWh"].sum()
ml_enerji   = df["ML_kWh"].sum()
gel_maliyet = df["Gel_TL"].sum()
ml_maliyet  = df["ML_TL"].sum()
enerji_pct  = (gel_enerji  - ml_enerji)  / gel_enerji  * 100
maliyet_pct = (gel_maliyet - ml_maliyet) / gel_maliyet * 100
co2_azalma  = (gel_enerji  - ml_enerji)  * 0.4

st.markdown('<div class="section-title">📊 Özet Sonuçlar</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""<div class="kpi-box">
      <div class="kpi-title">Enerji Tasarrufu</div>
      <div class="kpi-value">{enerji_pct:.1f}%</div>
      <div class="kpi-delta green">▼ {gel_enerji - ml_enerji:.1f} kWh azalma</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="kpi-box">
      <div class="kpi-title">Maliyet Tasarrufu</div>
      <div class="kpi-value">{maliyet_pct:.1f}%</div>
      <div class="kpi-delta green">▼ {gel_maliyet - ml_maliyet:.1f} TL azalma</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""<div class="kpi-box">
      <div class="kpi-title">CO₂ Azaltımı</div>
      <div class="kpi-value">{co2_azalma:.1f}</div>
      <div class="kpi-delta green">kg CO₂ daha az</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""<div class="kpi-box">
      <div class="kpi-title">ML Sistem Maliyeti</div>
      <div class="kpi-value">{ml_maliyet:.0f} ₺</div>
      <div class="kpi-delta red">Geleneksel: {gel_maliyet:.0f} ₺</div>
    </div>""", unsafe_allow_html=True)

# ── SEKMELER ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📈 Grafikler & Model Analizi</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["⚡ Güç Karşılaştırması", "🌡️ Sıcaklık & Doluluk", "🤖 ML Model İçgörüleri"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Saat"], y=df["Gel_kWh"],
        name="Geleneksel (If/Else)", line=dict(color="#ef5350", width=2, dash="dash"),
        mode="lines+markers"
    ))
    fig.add_trace(go.Scatter(
        x=df["Saat"], y=df["ML_kWh"],
        name="ML Modeli (Random Forest)", line=dict(color="#42a5f5", width=3),
        mode="lines+markers",
        fill="tonexty", fillcolor="rgba(66,165,245,0.10)"
    ))
    fig.add_trace(go.Bar(
        x=df["Saat"], y=df["Fiyat"],
        name="Tarife (TL/kWh)", yaxis="y2",
        marker_color=["#ef5350" if f == fiyat_pik else "#66bb6a" for f in df["Fiyat"]],
        opacity=0.25
    ))
    fig.update_layout(
        title="Saatlik Güç: Geleneksel If/Else vs ML Modeli",
        xaxis_title="Saat", yaxis_title="Güç (kW)",
        yaxis2=dict(title="Tarife (TL/kWh)", overlaying="y", side="right", showgrid=False),
        hovermode="x unified", legend=dict(orientation="h", y=1.12),
        height=430, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cfe2ff"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("🔵 ML modeli pik tarife saatlerinde ve düşük dolulukta gücü otomatik azaltır — hiçbir kural yazılmadan.")

with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        fig2 = px.area(df, x="Saat", y="Dis_Sicaklik",
                       title="Dış Sıcaklık Profili (°C)",
                       labels={"Dis_Sicaklik": "Sıcaklık (°C)"},
                       color_discrete_sequence=["#ff7043"])
        fig2.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font_color="#cfe2ff")
        st.plotly_chart(fig2, use_container_width=True)
    with col_b:
        fig3 = px.bar(df, x="Saat", y="Insan_Sayisi",
                      title="Bina Doluluk Profili (Kişi)",
                      labels={"Insan_Sayisi": "Kişi Sayısı"},
                      color_discrete_sequence=["#26c6da"])
        fig3.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font_color="#cfe2ff")
        st.plotly_chart(fig3, use_container_width=True)

with tab3:
    col_c, col_d = st.columns([1, 1])

    with col_c:
        st.markdown("#### 🌳 Özellik Önem Skoru")
        st.caption("ML modeli hangi girdiye ne kadar önem veriyor?")
        fig4 = px.bar(
            onem_df, x="Önem (%)", y="Özellik", orientation="h",
            title="Random Forest — Özellik Önemleri",
            color="Önem (%)", color_continuous_scale="Blues",
            text="Önem (%)"
        )
        fig4.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig4.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font_color="#cfe2ff",
                           showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig4, use_container_width=True)

    with col_d:
        st.markdown("#### 📉 Saatlik Maliyet Farkı (TL)")
        st.caption("Her saatte ML kaç TL tasarruf sağlıyor?")
        df["Tasarruf_TL"] = df["Gel_TL"] - df["ML_TL"]
        fig5 = px.bar(
            df, x="Saat", y="Tasarruf_TL",
            title="Saatlik Tasarruf (TL)",
            labels={"Tasarruf_TL": "Tasarruf (TL)"},
            color="Tasarruf_TL",
            color_continuous_scale=["#ef5350", "#66bb6a"]
        )
        fig5.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font_color="#cfe2ff",
                           coloraxis_showscale=False)
        st.plotly_chart(fig5, use_container_width=True)

    st.divider()
    st.markdown("#### 🔍 Model Hakkında")
    col_e, col_f, col_g = st.columns(3)
    col_e.metric("Algoritma",    "Random Forest")
    col_f.metric("Eğitim Verisi","365 gün × 24 saat")
    col_g.metric("Ağaç Sayısı", f"{n_trees} ağaç, derinlik {max_depth}")

    with st.expander("📚 ML modeli nasıl çalışır?"):
        st.markdown("""
**Eğitim aşaması:**
- 365 günlük sentetik geçmiş veri üretilir (rastgele sıcaklık, doluluk, tarife).
- Her saat için *uzman tarafından belirlenmiş optimal güç* hedef değer olarak atanır.
- Random Forest, bu **8.760 örneği** öğrenir — hiçbir if/else kural elle yazılmaz.

**Tahmin aşaması:**
- Bugünün verileri (saat, sıcaklık, kişi, tarife) modele girilir.
- Model, en yakın öğrendiği örüntüden optimal kW çıkarır.

**Geleneksel sistemden farkı:**
| | Geleneksel (If/Else) | ML Modeli |
|---|---|---|
| Karar mekanizması | Elle yazılmış kurallar | Veriden öğrenilmiş örüntüler |
| Esneklik | Kural değiştirilmeli | Yeni veriyle yeniden eğitilebilir |
| Pik saat farkındalığı | Sadece yazılmışsa | Otomatik öğrenir |
        """)

# ── DETAYLI TABLO ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📋 Saatlik Detay Tablosu</div>', unsafe_allow_html=True)
display_df = df.rename(columns={
    "Dis_Sicaklik": "Dış Sıcaklık (°C)",
    "Insan_Sayisi": "Kişi",
    "Fiyat":        "Tarife",
    "Gel_kWh":      "Geleneksel (kW)",
    "Gel_TL":       "Geleneksel (TL)",
    "ML_kWh":       "ML Modeli (kW)",
    "ML_TL":        "ML Modeli (TL)",
    "Tasarruf_TL":  "Tasarruf (TL)",
})
st.dataframe(
    display_df[["Saat","Dış Sıcaklık (°C)","Kişi","Tarife",
                "Geleneksel (kW)","Geleneksel (TL)",
                "ML Modeli (kW)","ML Modeli (TL)","Tasarruf (TL)"]].style
    .format({
        "Dış Sıcaklık (°C)": "{:.1f}",
        "Tarife":            "{:.2f}",
        "Geleneksel (kW)":   "{:.2f}",
        "Geleneksel (TL)":   "{:.2f}",
        "ML Modeli (kW)":    "{:.2f}",
        "ML Modeli (TL)":    "{:.2f}",
        "Tasarruf (TL)":     "{:.2f}",
    })
    .background_gradient(subset=["Tasarruf (TL)"], cmap="RdYlGn"),
    use_container_width=True,
    height=400,
)
