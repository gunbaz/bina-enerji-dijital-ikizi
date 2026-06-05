import math
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

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
.ajan-label {
    background: #1a2744; border-left: 4px solid #ab47bc;
    padding: 10px 16px; border-radius: 6px; font-size: 13px; color: #cfe2ff;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

st.title("🏢 Bina Enerji Yönetimi — Dijital İkiz & Ajan Sistemi")
st.caption("Fiziksel ısı dinamiği + çoklu ajan kararı + ML modeli — üç yaklaşımın gerçek zamanlı karşılaştırması.")

# ── SOL PANEL ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🌡️ Hava & Bina Koşulları")
    temel_sicaklik    = st.slider("Gün Temel Sıcaklığı (°C)",       10, 42, 26)
    sicaklik_amplitud = st.slider("Sıcaklık Dalgalanması (±°C)",     0, 10,  5)

    st.divider()
    st.header("👥 Bina Kullanım Profili")
    mesai_baslangic = st.slider("Mesai Başlangıcı (saat)", 6, 10, 8)
    mesai_bitis     = st.slider("Mesai Bitişi (saat)",    14, 22, 18)
    maks_kisi       = st.slider("Maksimum Kişi Sayısı",    5, 100, 45)

    st.divider()
    st.header("⚡ Klima & Maliyet")
    klima_gucu   = st.slider("Klima Maks. Gücü (kW)",   1.0, 5.0, 2.5, 0.5)
    standby_gucu = st.slider("Standby Gücü (kW)",        0.01, 0.20, 0.05, 0.01)
    fiyat_normal = st.slider("Normal Tarife (TL/kWh)",   1.0, 4.0, 2.5, 0.5)
    fiyat_pik    = st.slider("Pik Tarife (TL/kWh)",      2.0, 8.0, 4.5, 0.5)

    st.divider()
    st.header("🤖 ML Modeli")
    n_trees   = st.slider("Karar Ağacı Sayısı", 10, 200, 80, 10,
                          help="Random Forest'taki ağaç sayısı.")
    max_depth = st.slider("Ağaç Derinliği",      2,  20,  8,
                          help="Her ağacın derinliği. Fazla derin = ezber riski.")

    # ── YENİ: Fiziksel Bina Parametreleri ──────────────────────────────────────
    st.divider()
    st.header("🏠 Bina Fiziksel Parametreleri")
    bina_yalitim = st.slider(
        "Yalıtım Katsayısı (α)",  0.05, 0.30, 0.15, 0.01,
        help="Binanın dış ortamla ısı alışveriş hızı. Yüksek = zayıf yalıtım."
    )
    insan_isi = st.slider(
        "Kişi Başı Isı Katkısı β (°C/kişi)", 0.01, 0.20, 0.05, 0.01,
        help="Her kişinin iç ortama saatte kattığı sıcaklık artışı."
    )

    # ── YENİ: Ajan Öncelik Ağırlıkları ─────────────────────────────────────────
    st.divider()
    st.header("🤝 Ajan Öncelik Ağırlıkları")
    st.caption("Koordinatör ajan bu ağırlıklarla her ajanın önerisini birleştirir.")
    w_konfor  = st.slider("🔵 Konfor Ajanı Ağırlığı",           0.0, 1.0, 0.40, 0.05)
    w_maliyet = st.slider("🟢 Maliyet Ajanı Ağırlığı",          0.0, 1.0, 0.35, 0.05)
    w_surd    = st.slider("🟠 Sürdürülebilirlik Ajanı Ağırlığı", 0.0, 1.0, 0.25, 0.05)
    # Normalize — toplam sıfır koruması
    _w_top = w_konfor + w_maliyet + w_surd
    if _w_top == 0:
        w_konfor = w_maliyet = w_surd = 1 / 3
    else:
        w_konfor  /= _w_top
        w_maliyet /= _w_top
        w_surd    /= _w_top
    st.caption(f"Normalize: {w_konfor:.2f} / {w_maliyet:.2f} / {w_surd:.2f}")

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

SOGUTMA_KATSAYISI = 2.0  # γ: klimanın °C/kW/saat düşürme katsayısı
# Fiziksel dayanak: 2.5 kW klima, COP≈3 → 7.5 kW ısı çekimi,
# ~50 m² ofis termal kütlesi ≈ 0.4 kWh/°C → 7.5/0.4 ≈ 5°C/saat → γ≈2.0/kW

# ── GELENEKSEL SİSTEM — Kapalı Döngü (If/Else + T_iç geri besleme) ────────────
# Düzeltme: T_dış yerine T_iç eşiğine bakıyor;
# her saatin kararı bir sonraki saatin iç sıcaklığını belirliyor.
def geleneksel_kapali_dongu(dataframe, klima_max, standby, alpha, beta):
    n      = len(dataframe)
    ic_sic = [0.0] * n
    guc    = [0.0] * n
    ic_sic[0] = dataframe["Dis_Sicaklik"].iloc[0]

    for t in range(n):
        T_ic = ic_sic[t]
        T_dis = dataframe["Dis_Sicaklik"].iloc[t]
        N     = dataframe["Insan_Sayisi"].iloc[t]

        # Karar: T_iç ve doluluk durumuna göre (artık T_dış değil)
        if N > 0 and T_ic > 24:       # dolu ve sıcak → tam güç
            p = klima_max
        elif N == 0 and T_ic > 28:    # boş ama aşırı sıcak → yarım güç
            p = klima_max * 0.50
        else:                          # konforlu veya boş → standby
            p = standby

        guc[t] = p
        if t + 1 < n:
            ic_sic[t + 1] = (T_ic
                             + alpha * (T_dis - T_ic)
                             + beta  * N
                             - SOGUTMA_KATSAYISI * p)
    return guc, ic_sic

gel_guc, ic_sic_gel = geleneksel_kapali_dongu(
    df, klima_gucu, standby_gucu, bina_yalitim, insan_isi
)
df["Gel_kWh"]   = gel_guc
df["Gel_TL"]    = df["Gel_kWh"] * df["Fiyat"]
df["IcSic_Gel"] = ic_sic_gel

# ── ML MODELİ — T_iç Özellikli Eğitim + Kapalı Döngü Tahmin ──────────────────
# Düzeltme 1: Eğitim sırasında T_iç simüle ediliyor ve özellik olarak kullanılıyor.
# Düzeltme 2: Hedef (OptimalGuc) artık fiyata değil T_iç konfor durumuna göre belirleniyor.
# Düzeltme 3: Tahmin aşamasında her saat T_iç hesaplanıp bir sonraki adıma besleniyor.
@st.cache_resource(show_spinner="🤖 ML modeli eğitiliyor (T_iç kapalı döngü)...")
def model_egit(n_trees, max_depth, klima_gucu, standby_gucu, fiyat_pik,
               alpha=0.15, beta=0.05, gamma=2.0):
    """
    Özellikler: [Saat, T_dış, T_iç, Kişi, Fiyat]
    Hedef     : T_iç konfor durumuna dayalı optimal güç
                (fiyat ikincil faktör — birincil kriter konfor)
    """
    np.random.seed(42)
    kayitlar = []

    for _ in range(365):
        base_T = np.random.uniform(10, 40)
        amp_T  = np.random.uniform(2, 10)
        T_ic   = base_T  # günün başlangıç iç sıcaklığı

        for h in range(24):
            T_dis = (base_T + amp_T * math.sin(math.pi * (h - 5) / 9)
                     if 5 <= h <= 14
                     else base_T - amp_T * abs(math.sin(math.pi * (h - 14) / 14)))
            N   = int(np.random.randint(0, 50) * (1 if 8 <= h <= 18 else 0))
            f   = fiyat_pik if (12 <= h <= 15) or (18 <= h <= 22) else 2.5

            # ── Hedef: T_iç konforuna göre optimal güç ──────────────────────────
            # Birincil kriter: T_iç
            # İkincil kriter: fiyat (konfor bozuluyorsa fiyat göz ardı edilir)
            if N == 0:
                optimal = standby_gucu                          # boş bina → her zaman standby
            elif T_ic > 28:
                optimal = klima_gucu                            # aşırı sıcak → tam güç (fiyat göz ardı)
            elif T_ic > 26:                                     # rahatsız — soğutma gerekli
                if f == fiyat_pik:
                    optimal = klima_gucu * 0.70 + np.random.normal(0, 0.04)
                else:
                    optimal = klima_gucu * 0.85 + np.random.normal(0, 0.04)
            elif T_ic > 24:                                     # sınırda — hafif soğutma
                if f == fiyat_pik:
                    optimal = klima_gucu * 0.30 + np.random.normal(0, 0.03)
                else:
                    optimal = klima_gucu * 0.50 + np.random.normal(0, 0.03)
            else:                                               # konforlu → minimal güç
                optimal = standby_gucu + np.random.normal(0, 0.01)

            optimal = float(np.clip(optimal, standby_gucu, klima_gucu))
            kayitlar.append([h, T_dis, T_ic, N, f, optimal])

            # T_iç'i güncelle (bir sonraki saatin girdisi)
            T_ic = T_ic + alpha * (T_dis - T_ic) + beta * N - gamma * optimal

    egitim = pd.DataFrame(kayitlar,
                          columns=["Saat", "Dis_Sic", "Ic_Sic", "Kisi", "Fiyat", "OptimalGuc"])
    model = RandomForestRegressor(
        n_estimators=n_trees, max_depth=max_depth, random_state=42, n_jobs=-1
    )
    model.fit(egitim[["Saat", "Dis_Sic", "Ic_Sic", "Kisi", "Fiyat"]].values,
              egitim["OptimalGuc"].values)
    return model

model = model_egit(n_trees, max_depth, klima_gucu, standby_gucu, fiyat_pik,
                   alpha=bina_yalitim, beta=insan_isi, gamma=SOGUTMA_KATSAYISI)

# Kapalı döngü ML tahmini: her saat T_iç modele besleniyor
def ml_kapali_dongu(dataframe, model, klima_max, standby, alpha, beta):
    n      = len(dataframe)
    ic_sic = [0.0] * n
    guc    = [0.0] * n
    ic_sic[0] = dataframe["Dis_Sicaklik"].iloc[0]

    for t in range(n):
        T_ic  = ic_sic[t]
        T_dis = dataframe["Dis_Sicaklik"].iloc[t]
        N     = dataframe["Insan_Sayisi"].iloc[t]
        f     = dataframe["Fiyat"].iloc[t]
        h     = dataframe["Saat"].iloc[t]

        X = np.array([[h, T_dis, T_ic, N, f]])
        p = float(np.clip(model.predict(X)[0], standby, klima_max))
        guc[t] = p

        if t + 1 < n:
            ic_sic[t + 1] = (T_ic
                             + alpha * (T_dis - T_ic)
                             + beta  * N
                             - SOGUTMA_KATSAYISI * p)
    return guc, ic_sic

ml_guc, ic_sic_ml = ml_kapali_dongu(
    df, model, klima_gucu, standby_gucu, bina_yalitim, insan_isi
)
df["ML_kWh"]   = ml_guc
df["ML_TL"]    = df["ML_kWh"] * df["Fiyat"]
df["IcSic_ML"] = ic_sic_ml

# Özellik önem skoru (5 özellik)
onem    = model.feature_importances_
onem_df = pd.DataFrame({
    "Özellik":  ["Saat", "Dış Sıcaklık", "İç Sıcaklık (T_iç)", "Kişi Sayısı", "Elektrik Tarife"],
    "Önem (%)": (onem * 100).round(1)
}).sort_values("Önem (%)", ascending=True)

# ── Tasarruf (global — tablo ve tab3 için) ────────────────────────────────────
df["Tasarruf_TL"] = df["Gel_TL"] - df["ML_TL"]

# ── ÇOKLU AJAN + DİJİTAL İKİZ (geri beslemeli döngü) ─────────────────────────
def ajan_ve_ikiz_sim(dataframe, klima_max, standby,
                     pik_fiyat, alpha, beta,
                     w_konfor, w_maliyet, w_surd):
    """
    Saat-saat döngü:
      - Konfor Ajanı  → T_iç durumuna göre güç önerisi
      - Maliyet Ajanı → tarife & doluluk durumuna göre güç önerisi
      - Sürdürülebilirlik Ajanı → minimum enerji hedefi
      - Koordinatör   → ağırlıklı ortalama → final güç
      - Isı dinamiği  → bir sonraki saatin T_iç'ini hesapla (gerçek kapalı döngü)
    """
    n   = len(dataframe)
    ic_sic       = [0.0] * n
    ajan_guc     = [0.0] * n
    konfor_oneri = [0.0] * n
    maliyet_oneri= [0.0] * n
    surd_oneri   = [0.0] * n

    ic_sic[0] = dataframe["Dis_Sicaklik"].iloc[0]

    for t in range(n):
        T_ic  = ic_sic[t]
        T_dis = dataframe["Dis_Sicaklik"].iloc[t]
        N     = dataframe["Insan_Sayisi"].iloc[t]
        f     = dataframe["Fiyat"].iloc[t]

        # ── Konfor Ajanı ────────────────────────────────────────────────────────
        # Hedef: T_iç 20–26 °C konfor bandında kalsın
        if T_ic > 26:
            asiri   = T_ic - 26          # kaç derece konfor bandı üstünde
            p_konfor = min(klima_max,
                           standby + asiri * (klima_max - standby) / 6.0)
        elif T_ic < 20:
            p_konfor = standby           # soğutmaya gerek yok
        else:
            p_konfor = standby           # konfor bandında → minimum güç yeterli

        # ── Maliyet Ajanı ───────────────────────────────────────────────────────
        # Hedef: elektrik maliyetini minimize et
        if f >= pik_fiyat:
            p_maliyet = standby if N == 0 else klima_max * 0.40
        else:
            p_maliyet = standby if N == 0 else klima_max * 0.60

        # ── Sürdürülebilirlik Ajanı ─────────────────────────────────────────────
        # Hedef: toplam enerji ve CO₂ minimize et
        p_surd = standby if N == 0 else klima_max * 0.35

        # ── Koordinatör Ajan ────────────────────────────────────────────────────
        p_final = (w_konfor  * p_konfor
                 + w_maliyet * p_maliyet
                 + w_surd    * p_surd)
        p_final = float(np.clip(p_final, standby, klima_max))

        konfor_oneri[t]  = p_konfor
        maliyet_oneri[t] = p_maliyet
        surd_oneri[t]    = p_surd
        ajan_guc[t]      = p_final

        # ── Isı dinamiği → bir sonraki saat ─────────────────────────────────────
        if t + 1 < n:
            ic_sic[t + 1] = (T_ic
                             + alpha * (T_dis - T_ic)
                             + beta  * N
                             - SOGUTMA_KATSAYISI * p_final)

    return ajan_guc, konfor_oneri, maliyet_oneri, surd_oneri, ic_sic

ajan_guc, konfor_oneri, maliyet_oneri, surd_oneri, ic_sic_ajan = ajan_ve_ikiz_sim(
    df, klima_gucu, standby_gucu, fiyat_pik,
    bina_yalitim, insan_isi,
    w_konfor, w_maliyet, w_surd
)

df["Ajan_kWh"]    = ajan_guc
df["Ajan_TL"]     = df["Ajan_kWh"] * df["Fiyat"]
df["Konfor_kWh"]  = konfor_oneri
df["Maliyet_kWh"] = maliyet_oneri
df["Surd_kWh"]    = surd_oneri
df["IcSic_Ajan"]  = ic_sic_ajan

# ── KPI — SATIR 1: ML vs Geleneksel ──────────────────────────────────────────
gel_enerji  = df["Gel_kWh"].sum()
ml_enerji   = df["ML_kWh"].sum()
gel_maliyet = df["Gel_TL"].sum()
ml_maliyet  = df["ML_TL"].sum()
enerji_pct  = (gel_enerji  - ml_enerji)  / gel_enerji  * 100
maliyet_pct = (gel_maliyet - ml_maliyet) / gel_maliyet * 100
co2_azalma  = (gel_enerji  - ml_enerji)  * 0.4

st.markdown('<div class="section-title">📊 Özet Sonuçlar</div>', unsafe_allow_html=True)
st.caption("**ML Modeli** — Geleneksel If/Else sistemine kıyasla:")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="kpi-box">
      <div class="kpi-title">ML — Enerji Tasarrufu</div>
      <div class="kpi-value">{enerji_pct:.1f}%</div>
      <div class="kpi-delta green">▼ {gel_enerji - ml_enerji:.1f} kWh azalma</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi-box">
      <div class="kpi-title">ML — Maliyet Tasarrufu</div>
      <div class="kpi-value">{maliyet_pct:.1f}%</div>
      <div class="kpi-delta green">▼ {gel_maliyet - ml_maliyet:.1f} TL azalma</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-box">
      <div class="kpi-title">ML — CO₂ Azaltımı</div>
      <div class="kpi-value">{co2_azalma:.1f}</div>
      <div class="kpi-delta green">kg CO₂ daha az</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi-box">
      <div class="kpi-title">ML Sistem Maliyeti</div>
      <div class="kpi-value">{ml_maliyet:.0f} ₺</div>
      <div class="kpi-delta red">Geleneksel: {gel_maliyet:.0f} ₺</div>
    </div>""", unsafe_allow_html=True)

# ── KPI — SATIR 2: Ajan vs Geleneksel ────────────────────────────────────────
ajan_enerji      = df["Ajan_kWh"].sum()
ajan_maliyet     = df["Ajan_TL"].sum()
ajan_enerji_pct  = (gel_enerji  - ajan_enerji)  / gel_enerji  * 100
ajan_maliyet_pct = (gel_maliyet - ajan_maliyet) / gel_maliyet * 100
ajan_co2         = (gel_enerji  - ajan_enerji)  * 0.4

st.markdown("<br>", unsafe_allow_html=True)
st.caption("**Ajan Sistemi** (Koordinatör) — Geleneksel If/Else sistemine kıyasla:")
ca1, ca2, ca3, ca4 = st.columns(4)
with ca1:
    st.markdown(f"""<div class="kpi-box">
      <div class="kpi-title">Ajan — Enerji Tasarrufu</div>
      <div class="kpi-value">{ajan_enerji_pct:.1f}%</div>
      <div class="kpi-delta green">▼ {gel_enerji - ajan_enerji:.1f} kWh azalma</div>
    </div>""", unsafe_allow_html=True)
with ca2:
    st.markdown(f"""<div class="kpi-box">
      <div class="kpi-title">Ajan — Maliyet Tasarrufu</div>
      <div class="kpi-value">{ajan_maliyet_pct:.1f}%</div>
      <div class="kpi-delta green">▼ {gel_maliyet - ajan_maliyet:.1f} TL azalma</div>
    </div>""", unsafe_allow_html=True)
with ca3:
    st.markdown(f"""<div class="kpi-box">
      <div class="kpi-title">Ajan — CO₂ Azaltımı</div>
      <div class="kpi-value">{ajan_co2:.1f}</div>
      <div class="kpi-delta green">kg CO₂ daha az</div>
    </div>""", unsafe_allow_html=True)
with ca4:
    st.markdown(f"""<div class="kpi-box">
      <div class="kpi-title">Ajan Sistem Maliyeti</div>
      <div class="kpi-value">{ajan_maliyet:.0f} ₺</div>
      <div class="kpi-delta red">Geleneksel: {gel_maliyet:.0f} ₺</div>
    </div>""", unsafe_allow_html=True)

# ── SEKMELER (5 adet) ─────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📈 Grafikler & Analizler</div>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "⚡ Güç Karşılaştırması",
    "🌡️ Sıcaklık & Doluluk",
    "🤖 ML Model İçgörüleri",
    "🏠 Dijital İkiz — İç Sıcaklık",
    "🤝 Ajan Kararları",
    "📡 IoT Validasyonu",
])

# ── TAB 1: Güç Karşılaştırması ────────────────────────────────────────────────
with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Saat"], y=df["Gel_kWh"],
        name="Geleneksel (If/Else)",
        line=dict(color="#ef5350", width=2, dash="dash"),
        mode="lines+markers"
    ))
    fig.add_trace(go.Scatter(
        x=df["Saat"], y=df["ML_kWh"],
        name="ML Modeli (Random Forest)",
        line=dict(color="#42a5f5", width=2),
        mode="lines+markers"
    ))
    fig.add_trace(go.Scatter(
        x=df["Saat"], y=df["Ajan_kWh"],
        name="Ajan Sistemi (Koordinatör)",
        line=dict(color="#ab47bc", width=2),
        mode="lines+markers"
    ))
    fig.add_trace(go.Bar(
        x=df["Saat"], y=df["Fiyat"],
        name="Tarife (TL/kWh)", yaxis="y2",
        marker_color=["#ef5350" if f == fiyat_pik else "#66bb6a" for f in df["Fiyat"]],
        opacity=0.20
    ))
    fig.update_layout(
        title="Saatlik Güç: 3 Sistem Karşılaştırması",
        xaxis_title="Saat", yaxis_title="Güç (kW)",
        yaxis2=dict(title="Tarife (TL/kWh)", overlaying="y", side="right", showgrid=False),
        hovermode="x unified", legend=dict(orientation="h", y=1.12),
        height=440, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cfe2ff"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("🟥 Kırmızı çubuklar = pik tarife saatleri. ML ve Ajan sistemi bu saatlerde gücü otomatik düşürür.")

# ── TAB 2: Sıcaklık & Doluluk ─────────────────────────────────────────────────
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

# ── TAB 3: ML İçgörüleri ──────────────────────────────────────────────────────
with tab3:
    col_c, col_d = st.columns([1, 1])
    with col_c:
        st.markdown("#### 🌳 Özellik Önem Skoru")
        st.caption("ML modeli hangi girdiye ne kadar önem veriyor?")
        fig4 = px.bar(onem_df, x="Önem (%)", y="Özellik", orientation="h",
                      title="Random Forest — Özellik Önemleri",
                      color="Önem (%)", color_continuous_scale="Blues", text="Önem (%)")
        fig4.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig4.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font_color="#cfe2ff",
                           showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig4, use_container_width=True)
    with col_d:
        st.markdown("#### 📉 Saatlik Maliyet Farkı (TL)")
        st.caption("Her saatte ML kaç TL tasarruf sağlıyor?")
        fig5 = px.bar(df, x="Saat", y="Tasarruf_TL",
                      title="Saatlik Tasarruf (TL)",
                      labels={"Tasarruf_TL": "Tasarruf (TL)"},
                      color="Tasarruf_TL",
                      color_continuous_scale=["#ef5350", "#66bb6a"])
        fig5.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font_color="#cfe2ff",
                           coloraxis_showscale=False)
        st.plotly_chart(fig5, use_container_width=True)

    st.divider()
    st.markdown("#### 🔍 Model Hakkında")
    col_e, col_f, col_g = st.columns(3)
    col_e.metric("Algoritma",     "Random Forest")
    col_f.metric("Eğitim Verisi", "365 gün × 24 saat")
    col_g.metric("Ağaç Sayısı",  f"{n_trees} ağaç, derinlik {max_depth}")

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

# ── TAB 4: Dijital İkiz — İç Sıcaklık ────────────────────────────────────────
with tab4:
    st.markdown("#### 🏠 Bina İç Sıcaklık Dinamiği — Dijital İkiz Simülasyonu")
    st.caption(
        "Isı dengesi denklemi ile hesaplanan saatlik iç ortam sıcaklığı. "
        "Her sistem farklı klima gücü kullandığından farklı iç sıcaklık profillerine yol açar. "
        "Bu, gerçek bir Dijital İkiz'in özüdür: fiziksel bina davranışının sanal kopyası."
    )

    fig_ikiz = go.Figure()

    # Konfor bölgesi — yeşil şeffaf bant
    fig_ikiz.add_hrect(
        y0=20, y1=26,
        fillcolor="rgba(76,175,80,0.10)",
        line_width=0,
        annotation_text="Konfor Bölgesi (20–26 °C)",
        annotation_position="top right",
        annotation_font_color="#4caf50",
        annotation_font_size=11,
    )
    # Dış sıcaklık referans
    fig_ikiz.add_trace(go.Scatter(
        x=df["Saat"], y=df["Dis_Sicaklik"],
        name="Dış Sıcaklık",
        line=dict(color="#ff7043", width=1, dash="dot"),
        mode="lines"
    ))
    # Geleneksel
    fig_ikiz.add_trace(go.Scatter(
        x=df["Saat"], y=df["IcSic_Gel"],
        name="Geleneksel Sistem (İç)",
        line=dict(color="#ef5350", width=2, dash="dash"),
        mode="lines+markers"
    ))
    # ML
    fig_ikiz.add_trace(go.Scatter(
        x=df["Saat"], y=df["IcSic_ML"],
        name="ML Modeli (İç)",
        line=dict(color="#42a5f5", width=2),
        mode="lines+markers"
    ))
    # Ajan
    fig_ikiz.add_trace(go.Scatter(
        x=df["Saat"], y=df["IcSic_Ajan"],
        name="Ajan Sistemi (İç)",
        line=dict(color="#ab47bc", width=3),
        mode="lines+markers"
    ))

    fig_ikiz.update_layout(
        title="Saatlik İç Ortam Sıcaklığı — 3 Sistem Karşılaştırması",
        xaxis_title="Saat",
        yaxis_title="Sıcaklık (°C)",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.13),
        height=460,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cfe2ff",
    )
    st.plotly_chart(fig_ikiz, use_container_width=True)

    with st.expander("📐 Isı Dengesi Denklemi — Dijital İkiz Modeli"):
        st.markdown(f"""
**Saat-saat güncelleme denklemi:**

$$T_{{iç}}[t+1] = T_{{iç}}[t] \\;+\\; \\alpha \\cdot (T_{{dış}}[t] - T_{{iç}}[t]) \\;+\\; \\beta \\cdot N[t] \\;-\\; \\gamma \\cdot P_{{klima}}[t]$$

| Parametre | Açıklama | Mevcut Değer |
|-----------|----------|--------------|
| **α** | Yalıtım katsayısı (bina dışıyla ısı alışverişi) | `{bina_yalitim}` |
| **β** | Kişi başı ısı katkısı (°C/kişi/saat) | `{insan_isi}` |
| **γ** | Soğutma katsayısı (klimanın verimliliği) | `{SOGUTMA_KATSAYISI}` |
| **N[t]** | t. saatteki kişi sayısı | — |
| **P_klima[t]** | t. saatteki klima gücü (kW) | — |

**Dijital İkiz nedir?**
Geleneksel yazılımdan farkı, binanın fiziksel davranışını (ısı dengesi, termal atalet) gerçek zamanlı
olarak yansıtmasıdır. Sisteme verilen her karar, bir sonraki saatin iç sıcaklığını etkiler —
bu **kapalı döngü geri besleme** dijital ikilerin temel özelliğidir.
        """)

# ── TAB 5: Ajan Kararları ─────────────────────────────────────────────────────
with tab5:
    st.markdown("#### 🤝 Çoklu Ajan Karar Süreci")
    st.caption(
        "Her ajan bağımsız olarak kendi hedefine göre bir güç önerisi üretir. "
        "Koordinatör ajan bu önerileri ağırlıklı ortalamayla birleştirir. "
        "Konfor Ajanı gerçek zamanlı iç sıcaklığı izler — bu nedenle sisteme gerçek geri besleme sağlar."
    )

    # Ajan mimarisi özeti
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.markdown("""
<div class="ajan-label">
🔵 <b>Konfor Ajanı</b><br>
Hedef: T_iç 20–26 °C bandında tut<br>
Girdi: anlık iç sıcaklık (Dijital İkiz)<br>
Ağırlık: <b>{:.2f}</b>
</div>""".format(w_konfor), unsafe_allow_html=True)
    with col_info2:
        st.markdown("""
<div class="ajan-label">
🟢 <b>Maliyet Ajanı</b><br>
Hedef: elektrik maliyetini minimize et<br>
Girdi: anlık tarife + doluluk<br>
Ağırlık: <b>{:.2f}</b>
</div>""".format(w_maliyet), unsafe_allow_html=True)
    with col_info3:
        st.markdown("""
<div class="ajan-label">
🟠 <b>Sürdürülebilirlik Ajanı</b><br>
Hedef: toplam enerji & CO₂ minimize<br>
Girdi: doluluk durumu<br>
Ağırlık: <b>{:.2f}</b>
</div>""".format(w_surd), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Grafik: grouped bar + koordinatör çizgisi
    fig_ajan = go.Figure()
    fig_ajan.add_trace(go.Bar(
        x=df["Saat"], y=df["Konfor_kWh"],
        name="Konfor Ajanı Önerisi",
        marker_color="#42a5f5", opacity=0.80,
    ))
    fig_ajan.add_trace(go.Bar(
        x=df["Saat"], y=df["Maliyet_kWh"],
        name="Maliyet Ajanı Önerisi",
        marker_color="#66bb6a", opacity=0.80,
    ))
    fig_ajan.add_trace(go.Bar(
        x=df["Saat"], y=df["Surd_kWh"],
        name="Sürdürülebilirlik Ajanı Önerisi",
        marker_color="#ffa726", opacity=0.80,
    ))
    fig_ajan.add_trace(go.Scatter(
        x=df["Saat"], y=df["Ajan_kWh"],
        name="⚖️ Koordinatör — Final Karar",
        line=dict(color="#ab47bc", width=3),
        mode="lines+markers",
    ))
    fig_ajan.update_layout(
        barmode="group",
        title="Saatlik Ajan Önerileri & Koordinatör Kararı (kW)",
        xaxis_title="Saat",
        yaxis_title="Güç (kW)",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.14),
        height=460,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cfe2ff",
    )
    st.plotly_chart(fig_ajan, use_container_width=True)

    # Ajan oy tablosu
    st.divider()
    st.markdown("#### 📋 Saatlik Ajan Oy Tablosu")
    ajan_tablo = pd.DataFrame({
        "Saat":                     df["Saat"],
        "Dış Sıcaklık (°C)":        df["Dis_Sicaklik"],
        "İç Sıcaklık °C (Ajan)":    [round(v, 2) for v in df["IcSic_Ajan"]],
        "Kişi":                      df["Insan_Sayisi"],
        "Tarife (TL/kWh)":           df["Fiyat"],
        "Konfor Önerisi (kW)":       df["Konfor_kWh"].round(3),
        "Maliyet Önerisi (kW)":      df["Maliyet_kWh"].round(3),
        "Sürd. Önerisi (kW)":        df["Surd_kWh"].round(3),
        "Koordinatör Kararı (kW)":   df["Ajan_kWh"].round(3),
        "Maliyet (TL)":              df["Ajan_TL"].round(2),
    })
    st.dataframe(
        ajan_tablo.style
        .format({
            "Dış Sıcaklık (°C)":       "{:.1f}",
            "İç Sıcaklık °C (Ajan)":   "{:.2f}",
            "Tarife (TL/kWh)":          "{:.2f}",
            "Konfor Önerisi (kW)":      "{:.3f}",
            "Maliyet Önerisi (kW)":     "{:.3f}",
            "Sürd. Önerisi (kW)":       "{:.3f}",
            "Koordinatör Kararı (kW)":  "{:.3f}",
            "Maliyet (TL)":             "{:.2f}",
        })
        .background_gradient(subset=["Koordinatör Kararı (kW)"], cmap="Purples")
        .background_gradient(subset=["İç Sıcaklık °C (Ajan)"],   cmap="RdYlGn_r"),
        use_container_width=True,
        height=430,
    )

# ── TAB 6: IoT Validasyonu ───────────────────────────────────────────────────
UCI_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases"
    "/00374/energydata_complete.csv"
)

@st.cache_data(show_spinner=False)
def uci_indir():
    """UCI Appliances Energy Prediction veri setini indir ve önişle."""
    raw = pd.read_csv(UCI_URL, parse_dates=["date"])
    raw = raw.set_index("date").resample("h").mean(numeric_only=True)
    raw.index.name = "Tarih"
    # Oda sıcaklıklarının ortalaması (T1-T9)
    oda_sutunlari = [c for c in raw.columns if c.startswith("T") and c != "T_out"]
    raw["T_ic_gercek"] = raw[oda_sutunlari].mean(axis=1)
    return raw

def csv_isle(uploaded):
    """Yüklenen CSV'yi UCI formatına uyumlu hale getir."""
    raw = pd.read_csv(uploaded, parse_dates=["date"])
    raw = raw.set_index("date").resample("h").mean(numeric_only=True)
    raw.index.name = "Tarih"
    oda_sutunlari = [c for c in raw.columns if c.startswith("T") and c != "T_out"]
    if not oda_sutunlari:
        raise ValueError("CSV'de T1–T9 gibi oda sıcaklığı sütunu bulunamadı.")
    raw["T_ic_gercek"] = raw[oda_sutunlari].mean(axis=1)
    return raw

with tab6:
    st.markdown("#### 📡 Gerçek IoT Verisiyle Dijital İkiz Validasyonu")
    st.caption(
        "UCI Appliances Energy Prediction veri seti — Belçika'da gerçek bir evden "
        "4,5 aylık 10 dakikalık ölçümler (2016). "
        "Dijital İkiz modelimizin ürettiği iç sıcaklık tahmini, "
        "gerçek oda sıcaklıklarıyla karşılaştırılır."
    )

    # ── Veri Kaynağı Seçimi ──────────────────────────────────────────────────
    with st.container():
        col_src1, col_src2 = st.columns([1, 1])
        with col_src1:
            st.markdown("**Seçenek 1 — Otomatik İndirme (UCI)**")
            yukle_btn = st.button("🌐 UCI Veri Setini İndir", use_container_width=True)
        with col_src2:
            st.markdown("**Seçenek 2 — Kendi CSV Dosyan**")
            uploaded_file = st.file_uploader(
                "CSV yükle (UCI formatı: date, T1-T9, T_out)",
                type="csv", label_visibility="collapsed"
            )

    iot_df = None
    veri_kaynagi = None

    # Önce upload kontrol et (öncelikli)
    if uploaded_file is not None:
        try:
            with st.spinner("CSV işleniyor..."):
                iot_df = csv_isle(uploaded_file)
            veri_kaynagi = f"📂 Yüklenen dosya: `{uploaded_file.name}`"
            st.success("✅ Dosya başarıyla yüklendi.")
        except Exception as e:
            st.error(f"❌ Dosya okunamadı: {e}")

    # Sonra UCI indirme dene
    elif yukle_btn:
        try:
            with st.spinner("🌐 UCI sunucusundan indiriliyor..."):
                iot_df = uci_indir()
            veri_kaynagi = "🌐 UCI Appliances Energy Prediction Dataset"
            st.success(f"✅ İndirme başarılı — {len(iot_df):,} saatlik kayıt.")
        except Exception as e:
            st.warning(
                f"⚠️ Otomatik indirme başarısız: `{e}`\n\n"
                "UCI sitesine erişilemiyor olabilir. "
                "Veri setini manuel olarak indirip yukarıdan yükleyebilirsin:\n\n"
                "👉 [energydata_complete.csv]"
                "(https://archive.ics.uci.edu/ml/machine-learning-databases/00374/energydata_complete.csv)"
            )

    # ── Validasyon Arayüzü ───────────────────────────────────────────────────
    if iot_df is not None:
        st.divider()
        st.caption(f"Veri kaynağı: {veri_kaynagi}")

        # Gün seçici
        mevcut_gunler = iot_df.index.normalize().unique().sort_values()
        # En az 24 saatlik verisi olan günler
        gun_sayilari  = iot_df.groupby(iot_df.index.normalize()).size()
        tam_gunler    = gun_sayilari[gun_sayilari >= 24].index
        if len(tam_gunler) == 0:
            st.error("Veri setinde 24 saatlik tam gün bulunamadı.")
        else:
            secilen_gun = st.select_slider(
                "📅 Validasyon için gün seçin:",
                options=[str(g.date()) for g in tam_gunler],
                value=str(tam_gunler[len(tam_gunler) // 2].date()),
            )
            gun_filtre = iot_df[iot_df.index.date == pd.Timestamp(secilen_gun).date()]
            gun_filtre = gun_filtre.head(24).reset_index(drop=True)

            if len(gun_filtre) < 24:
                st.warning("Seçilen gün için 24 saatlik tam veri yok, başka bir gün deneyin.")
            else:
                # Gerçek değerler
                t_dis_gercek = gun_filtre["T_out"].values          # dış sıcaklık
                t_ic_gercek  = gun_filtre["T_ic_gercek"].values    # ölçülen iç sıcaklık
                saatler_24   = list(range(24))

                # Digital Twin simülasyonu — gerçek dış sıcaklıkla çalıştır
                # Klima sistemi yok varsayımı (sadece termal dinamik):
                # P_klima = 0 → klimasız doğal ısı değişimi modeli
                ic_sic_val = [0.0] * 24
                ic_sic_val[0] = float(t_dis_gercek[0])
                for t in range(23):
                    ic_sic_val[t + 1] = (
                        ic_sic_val[t]
                        + bina_yalitim * (float(t_dis_gercek[t]) - ic_sic_val[t])
                    )

                # Metrikler
                mae  = mean_absolute_error(t_ic_gercek, ic_sic_val)
                rmse = mean_squared_error(t_ic_gercek, ic_sic_val) ** 0.5
                r2   = r2_score(t_ic_gercek, ic_sic_val)

                # ── KPI: Validasyon Metrikleri ────────────────────────────────
                st.markdown("**Model Doğrulama Metrikleri**")
                vm1, vm2, vm3, vm4 = st.columns(4)
                vm1.metric("MAE (Ortalama Mutlak Hata)", f"{mae:.2f} °C",
                           help="Tahmin ile gerçek arasındaki ortalama mutlak fark.")
                vm2.metric("RMSE (Kök Ortalama Kare Hata)", f"{rmse:.2f} °C",
                           help="Büyük hatalara daha duyarlı hata metriği.")
                vm3.metric("R² Skoru", f"{r2:.3f}",
                           help="1.0 = mükemmel uyum, 0 = rastgele tahmin.")
                vm4.metric("Veri Noktası", "24 saat",
                           help=f"Seçilen gün: {secilen_gun}")

                # Kalite yorumu
                if r2 >= 0.85:
                    st.success(f"🟢 Model başarılı — R² = {r2:.3f}: Dijital İkiz gerçek binayı yüksek doğrulukla taklit ediyor.")
                elif r2 >= 0.60:
                    st.info(f"🟡 Model kabul edilebilir — R² = {r2:.3f}: Yalıtım katsayısını (α) ayarlayarak iyileştirilebilir.")
                else:
                    st.warning(f"🔴 Model zayıf — R² = {r2:.3f}: Sidebar'dan α ve β parametrelerini gerçek binaya göre kalibre edin.")

                st.divider()

                # ── Ana Grafik: Gerçek vs Simüle ─────────────────────────────
                fig_val = go.Figure()

                # Dış sıcaklık referans
                fig_val.add_trace(go.Scatter(
                    x=saatler_24, y=t_dis_gercek,
                    name="Gerçek Dış Sıcaklık (IoT)",
                    line=dict(color="#ff7043", width=1, dash="dot"),
                    mode="lines",
                ))
                # Gerçek iç sıcaklık
                fig_val.add_trace(go.Scatter(
                    x=saatler_24, y=t_ic_gercek,
                    name="Gerçek İç Sıcaklık (IoT Sensörü)",
                    line=dict(color="#26c6da", width=3),
                    mode="lines+markers",
                ))
                # Simüle iç sıcaklık
                fig_val.add_trace(go.Scatter(
                    x=saatler_24, y=ic_sic_val,
                    name="Dijital İkiz Tahmini",
                    line=dict(color="#ab47bc", width=2, dash="dash"),
                    mode="lines+markers",
                ))
                # Hata bandı (±MAE)
                fig_val.add_trace(go.Scatter(
                    x=saatler_24 + saatler_24[::-1],
                    y=[v + mae for v in ic_sic_val] + [v - mae for v in ic_sic_val[::-1]],
                    fill="toself",
                    fillcolor="rgba(171,71,188,0.12)",
                    line=dict(color="rgba(0,0,0,0)"),
                    name=f"±MAE Bandı ({mae:.2f} °C)",
                    hoverinfo="skip",
                ))
                fig_val.update_layout(
                    title=f"Dijital İkiz Validasyonu — {secilen_gun}",
                    xaxis_title="Saat",
                    yaxis_title="Sıcaklık (°C)",
                    hovermode="x unified",
                    legend=dict(orientation="h", y=1.13),
                    height=440,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#cfe2ff",
                )
                st.plotly_chart(fig_val, use_container_width=True)

                # ── Hata Dağılımı Grafiği ─────────────────────────────────────
                hatalar = [s - g for s, g in zip(ic_sic_val, t_ic_gercek)]
                col_hata1, col_hata2 = st.columns(2)
                with col_hata1:
                    fig_hata = px.bar(
                        x=saatler_24, y=hatalar,
                        color=hatalar,
                        color_continuous_scale=["#42a5f5", "#e0e0e0", "#ef5350"],
                        color_continuous_midpoint=0,
                        labels={"x": "Saat", "y": "Hata (°C)", "color": "Hata"},
                        title="Saatlik Tahmin Hatası (Simüle − Gerçek)",
                    )
                    fig_hata.add_hline(y=0, line_dash="dash",
                                       line_color="#ffffff", opacity=0.4)
                    fig_hata.update_layout(
                        height=300,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#cfe2ff",
                        coloraxis_showscale=False,
                    )
                    st.plotly_chart(fig_hata, use_container_width=True)

                with col_hata2:
                    # Scatter: gerçek vs tahmin (ideal = köşegen)
                    fig_scatter = px.scatter(
                        x=t_ic_gercek, y=ic_sic_val,
                        labels={"x": "Gerçek T_iç (°C)", "y": "Tahmin T_iç (°C)"},
                        title="Gerçek vs Tahmin — İdeal: y = x",
                        trendline="ols",
                        trendline_color_override="#42a5f5",
                    )
                    _rng = [min(min(t_ic_gercek), min(ic_sic_val)) - 0.5,
                            max(max(t_ic_gercek), max(ic_sic_val)) + 0.5]
                    fig_scatter.add_shape(type="line",
                        x0=_rng[0], y0=_rng[0], x1=_rng[1], y1=_rng[1],
                        line=dict(color="#ffa726", dash="dash", width=1.5))
                    fig_scatter.update_layout(
                        height=300,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#cfe2ff",
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)

                # ── Karşılaştırma Tablosu ─────────────────────────────────────
                st.divider()
                st.markdown("#### 📋 Saat Saat Karşılaştırma Tablosu")
                tablo_val = pd.DataFrame({
                    "Saat":                    saatler_24,
                    "Dış Sıcaklık (IoT) °C":  t_dis_gercek.round(2),
                    "Gerçek İç Sıcaklık °C":   t_ic_gercek.round(2),
                    "Dijital İkiz Tahmini °C":  [round(v, 2) for v in ic_sic_val],
                    "Hata (°C)":               [round(s - g, 2) for s, g in
                                                zip(ic_sic_val, t_ic_gercek)],
                })
                st.dataframe(
                    tablo_val.style
                    .format({
                        "Dış Sıcaklık (IoT) °C":   "{:.2f}",
                        "Gerçek İç Sıcaklık °C":    "{:.2f}",
                        "Dijital İkiz Tahmini °C":   "{:.2f}",
                        "Hata (°C)":                 "{:+.2f}",
                    })
                    .background_gradient(subset=["Hata (°C)"], cmap="RdBu", vmin=-3, vmax=3),
                    use_container_width=True,
                    height=380,
                )

                # ── Kalibrasyon İpucu ─────────────────────────────────────────
                with st.expander("⚠️ Validasyon Sınırlılıkları & Kalibrasyon"):
                    st.markdown(f"""
**MAE = {mae:.2f} °C | RMSE = {rmse:.2f} °C | R² = {r2:.3f}**

---

### Bilinen Sınırlılık: P_klima = 0 Varsayımı

Bu validasyonda Dijital İkiz **P_klima = 0** kabul ederek çalışıyor.
Yani bina hiç klima/kombi yokmuş gibi simüle ediliyor — sadece doğal ısı değişimi modelleniyor.

**Neden bu sorun?**
UCI veri setindeki Belçika evi gerçekte aktif ısıtma/soğutma sistemine sahipti.
HVAC sistemi çalıştığında iç sıcaklık dış koşullardan bağımsız sabit tutuluyordu.
Bu nedenle simülasyon ile gerçek sensör verisi arasında sapma kaçınılmazdır.

| Durum | R² Beklentisi | Açıklama |
|-------|---------------|----------|
| HVAC kapalı saatler | Yüksek | Doğal termal drift iyi modellenir |
| HVAC aktif saatler | Düşük | Simülasyon HVAC etkisini bilmiyor |

**Gerçek çözüm nedir?**
UCI veri setindeki `Appliances` (Wh) kolonu toplam cihaz enerjisini içeriyor
ancak HVAC gücünü ayrıştırmak mümkün değil. Bunun için ayrı bir enerji alt sayacı gerekir.

**Kalibrasyonu nasıl yaparsın (mevcut model için)?**
Sidebar'dan **Yalıtım Katsayısı (α)** sliderını değiştir →
R² maksimum olduğu noktada binanın termal geçirgenliği kalibre edilmiş demektir
*(yalnızca HVAC-siz saatler için geçerli).*

> Bu veri seti: *Candanedo et al. (2017). Appliances Energy Prediction.*
> UCI ML Repository. DOI: [10.24432/C5VC8G](https://doi.org/10.24432/C5VC8G)
                    """)

    else:
        # Henüz veri yüklenmemiş — yönlendirici bilgi kartları
        st.divider()
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("""
<div style="background:#1e2a3a;border-radius:10px;padding:20px;border:1px solid #2e4060;">
<h4 style="color:#42a5f5;">🌐 UCI Appliances Energy Prediction</h4>
<p style="color:#8ab4d4;font-size:13px;">
Belçika'da gerçek bir evden 4,5 aylık 10 dakikalık ölçümler.<br><br>
<b>İçerik:</b> T_out (dış), T1–T9 (9 oda), RH (nem), enerji<br>
<b>Boyut:</b> ~20.000 satır<br>
<b>Erişim:</b> Ücretsiz, hesap gerekmez
</p>
<p style="color:#42a5f5;font-size:12px;">
UCI ML Repository — Candanedo et al. (2017)
</p>
</div>""", unsafe_allow_html=True)
        with col_g2:
            st.markdown("""
<div style="background:#1e2a3a;border-radius:10px;padding:20px;border:1px solid #2e4060;">
<h4 style="color:#ab47bc;">📂 Kendi CSV Dosyan</h4>
<p style="color:#8ab4d4;font-size:13px;">
Kaggle, ASHRAE veya başka kaynaklardan indirdiğin CSV'yi yükle.<br><br>
<b>Gerekli sütunlar:</b><br>
• <code>date</code> — tarih/saat (örn. 2016-01-11 17:00:00)<br>
• <code>T_out</code> — dış sıcaklık (°C)<br>
• <code>T1</code>–<code>T9</code> — oda sıcaklıkları (en az biri)
</p>
</div>""", unsafe_allow_html=True)
        st.info(
            "👆 Başlamak için yukarıdan **UCI Veri Setini İndir** butonuna bas "
            "veya kendi CSV dosyasını yükle."
        )

# ── DETAYLI TABLO ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📋 Saatlik Detay Tablosu — Tüm Sistemler</div>',
            unsafe_allow_html=True)
display_df = df.rename(columns={
    "Dis_Sicaklik": "Dış Sıcaklık (°C)",
    "Insan_Sayisi": "Kişi",
    "Fiyat":        "Tarife",
    "Gel_kWh":      "Geleneksel (kW)",
    "Gel_TL":       "Geleneksel (TL)",
    "ML_kWh":       "ML Modeli (kW)",
    "ML_TL":        "ML Modeli (TL)",
    "Tasarruf_TL":  "ML Tasarrufu (TL)",
    "Ajan_kWh":     "Ajan Sistemi (kW)",
    "Ajan_TL":      "Ajan Sistemi (TL)",
})
st.dataframe(
    display_df[["Saat", "Dış Sıcaklık (°C)", "Kişi", "Tarife",
                "Geleneksel (kW)", "Geleneksel (TL)",
                "ML Modeli (kW)",  "ML Modeli (TL)",  "ML Tasarrufu (TL)",
                "Ajan Sistemi (kW)", "Ajan Sistemi (TL)"]].style
    .format({
        "Dış Sıcaklık (°C)":   "{:.1f}",
        "Tarife":               "{:.2f}",
        "Geleneksel (kW)":      "{:.2f}",
        "Geleneksel (TL)":      "{:.2f}",
        "ML Modeli (kW)":       "{:.2f}",
        "ML Modeli (TL)":       "{:.2f}",
        "ML Tasarrufu (TL)":    "{:.2f}",
        "Ajan Sistemi (kW)":    "{:.2f}",
        "Ajan Sistemi (TL)":    "{:.2f}",
    })
    .background_gradient(subset=["ML Tasarrufu (TL)"], cmap="RdYlGn")
    .background_gradient(subset=["Ajan Sistemi (kW)"], cmap="Purples"),
    use_container_width=True,
    height=420,
)
