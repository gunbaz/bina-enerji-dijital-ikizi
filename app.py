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

# ── KENAR DURUM VALİDASYONU ───────────────────────────────────────────────────
_hatalar = []
if mesai_bitis <= mesai_baslangic:
    _hatalar.append("⛔ Mesai bitişi başlangıçtan önce veya eşit olamaz.")
if klima_gucu <= standby_gucu:
    _hatalar.append("⛔ Klima gücü standby gücünden büyük olmalıdır.")
if fiyat_pik <= fiyat_normal:
    _hatalar.append("⚠️ Pik tarife normal tarifeden büyük olmalı — aksi halde Maliyet Ajanı anlamsızlaşır.")
if _hatalar:
    for hata in _hatalar:
        st.error(hata)
    st.stop()

# ── 24 SAATLIK SENARYO VERİSİ ─────────────────────────────────────────────────
saatler = list(range(24))

# Gerçekçi günlük sıcaklık profili:
# En soğuk: saat 05:00 → T_min = temel - amplitud
# En sıcak : saat 14:00 → T_max = temel + amplitud
# İsınma fazı (05→14, 9 saat): sin eğrisi ile yükseliş
# Soğuma fazı (14→05, 15 saat): sin eğrisi ile iniş
def _dis_sic(h, temel, amp):
    T_min, T_max = temel - amp, temel + amp
    if 5 <= h <= 14:                         # isınma: 9 saat
        p = (h - 5) / 9
        return round(T_min + (T_max - T_min) * math.sin(math.pi / 2 * p), 1)
    else:                                    # soğuma: 15 saat
        gecen = h - 14 if h > 14 else h + 24 - 14
        p = gecen / 15
        return round(T_max - (T_max - T_min) * math.sin(math.pi / 2 * p), 1)

dis_sicakliklar = [_dis_sic(h, temel_sicaklik, sicaklik_amplitud) for h in saatler]

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

    klima_acik = False  # histerezis durumu
    for t in range(n):
        T_ic = ic_sic[t]
        T_dis = dataframe["Dis_Sicaklik"].iloc[t]
        N     = dataframe["Insan_Sayisi"].iloc[t]

        # Histerezis ile karar: aç/kapat için farklı eşikler
        # → titreşimi (bang-bang) önler
        if N > 0:
            if T_ic > 25:          # konfor üst eşiği → klima aç
                klima_acik = True
            elif T_ic < 22:        # konfor alt eşiği → klima kapat
                klima_acik = False
            p = klima_max if klima_acik else standby
        elif T_ic > 28:            # boş ama aşırı sıcak → yarım güç
            p = klima_max * 0.50
        else:
            klima_acik = False
            p = standby

        guc[t] = p
        if t + 1 < n:
            raw = T_ic + alpha * (T_dis - T_ic) + beta * N - SOGUTMA_KATSAYISI * p
            ic_sic[t + 1] = float(np.clip(raw, 5.0, 60.0))  # fiziksel sınırlar
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
def model_egit(n_trees, max_depth, klima_gucu, standby_gucu,
               fiyat_pik, fiyat_normal,           # ← fiyat_normal artık parametre
               mesai_bas, mesai_bit,               # ← mesai saatleri artık parametre
               alpha=0.15, beta=0.05, gamma=2.0):
    """
    Özellikler: [Saat, T_dış, T_iç, Kişi, Fiyat]
    Hedef     : T_iç konfor durumuna dayalı optimal güç
    Düzeltmeler:
      - fiyat_normal ve mesai saatleri artık sidebar'dan geliyor (cache key'e dahil)
      - T_dis, ana simülasyonla aynı _dis_sic() fonksiyonuyla hesaplanıyor
      - T_ic fiziksel sınırlar içinde tutuluyor (5–60°C)
    """
    np.random.seed(42)
    kayitlar = []

    for _ in range(365):
        base_T = np.random.uniform(10, 40)
        amp_T  = np.random.uniform(2, 10)
        T_ic   = _dis_sic(mesai_bas, base_T, amp_T)  # günün başı: sabah sıcaklığı

        for h in range(24):
            T_dis = _dis_sic(h, base_T, amp_T)    # ana simülasyonla aynı formül
            N   = int(np.random.randint(0, 50) * (1 if mesai_bas <= h < mesai_bit else 0))
            f   = fiyat_pik if (12 <= h <= 15) or (18 <= h <= 22) else fiyat_normal

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

            # T_iç'i güncelle — fiziksel sınırlar içinde tut
            raw  = T_ic + alpha * (T_dis - T_ic) + beta * N - gamma * optimal
            T_ic = float(np.clip(raw, 5.0, 60.0))

    egitim = pd.DataFrame(kayitlar,
                          columns=["Saat", "Dis_Sic", "Ic_Sic", "Kisi", "Fiyat", "OptimalGuc"])
    model = RandomForestRegressor(
        n_estimators=n_trees, max_depth=max_depth, random_state=42, n_jobs=-1
    )
    model.fit(egitim[["Saat", "Dis_Sic", "Ic_Sic", "Kisi", "Fiyat"]].values,
              egitim["OptimalGuc"].values)
    return model

model = model_egit(n_trees, max_depth, klima_gucu, standby_gucu,
                   fiyat_pik, fiyat_normal,
                   mesai_baslangic, mesai_bitis,
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
            raw = T_ic + alpha * (T_dis - T_ic) + beta * N - SOGUTMA_KATSAYISI * p
            ic_sic[t + 1] = float(np.clip(raw, 5.0, 60.0))  # fiziksel sınırlar
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
        # Bölен 2.0 → 2°C üstünde tam güce ulaşır (eski 6.0 çok nazikti)
        if T_ic > 26:
            asiri    = T_ic - 26
            p_konfor = min(klima_max,
                           standby + asiri * (klima_max - standby) / 2.0)
        elif T_ic < 20:
            p_konfor = standby           # soğutmaya gerek yok
        else:
            p_konfor = standby           # konfor bandında → minimum güç yeterli

        # ── Maliyet Ajanı ───────────────────────────────────────────────────────
        # Hedef: elektrik maliyetini minimize et
        # Eşik = 26°C (konfor bandı üst sınırı) — Konfor Ajanı ile aynı
        if N == 0 or T_ic <= 26:
            p_maliyet = standby                # konforlu veya boş → standby
        elif f >= pik_fiyat:
            p_maliyet = klima_max * 0.35       # pik + rahatsız → düşük güç (pahalı saat)
        else:
            p_maliyet = klima_max * 0.60       # normal + rahatsız → orta güç

        # ── Sürdürülebilirlik Ajanı ─────────────────────────────────────────────
        # Hedef: toplam enerji ve CO₂ minimize et
        # Eşik = 26°C — zorunlu olmadıkça çalışma
        if N == 0 or T_ic <= 26:
            p_surd = standby                   # konforlu veya boş → standby
        else:
            p_surd = klima_max * 0.35          # rahatsız + dolu → minimum güç

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
            raw = T_ic + alpha * (T_dis - T_ic) + beta * N - SOGUTMA_KATSAYISI * p_final
            ic_sic[t + 1] = float(np.clip(raw, 5.0, 60.0))  # fiziksel sınırlar

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
enerji_pct  = (gel_enerji  - ml_enerji)  / gel_enerji  * 100 if gel_enerji  > 0 else 0.0
maliyet_pct = (gel_maliyet - ml_maliyet) / gel_maliyet * 100 if gel_maliyet > 0 else 0.0
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
ajan_enerji_pct  = (gel_enerji  - ajan_enerji)  / gel_enerji  * 100 if gel_enerji  > 0 else 0.0
ajan_maliyet_pct = (gel_maliyet - ajan_maliyet) / gel_maliyet * 100 if gel_maliyet > 0 else 0.0
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
        marker_color=["#ef5350" if abs(f - fiyat_pik) < 0.01 else "#66bb6a" for f in df["Fiyat"]],
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

# ── TAB 6: IoT Validasyonu — Pecan Street Dataport ───────────────────────────
PECAN_PATH = r"C:\Users\pc\makale_sunum\proje\15minute_data_austin\15minute_data_austin.csv"

@st.cache_data(show_spinner="📡 Pecan Street verisi yükleniyor...")
def pecan_yukle(path):
    """Pecan Street 15-dakikalık veriyi saatlik ortalamaya çevirir."""
    raw = pd.read_csv(path)
    raw["local_15min"] = pd.to_datetime(raw["local_15min"], utc=True).dt.tz_localize(None)
    raw = raw.set_index("local_15min")
    # Saatlik ortalamaya indir
    # dataid dışındaki sayısal kolonları saatlik ortalamaya indir
    raw["dataid"] = raw["dataid"].astype(int)
    sayisal = raw.select_dtypes(include="number")
    saatlik = (
        sayisal
        .groupby(["dataid", pd.Grouper(freq="h")])
        .mean()
        .reset_index()
    )
    saatlik = saatlik.rename(columns={"local_15min": "local_15min"})
    saatlik.columns = ["dataid", "local_15min"] + list(saatlik.columns[2:])
    if "air1" in saatlik.columns:
        saatlik["air1"] = saatlik["air1"].clip(lower=0)
    return saatlik

with tab6:
    st.markdown("#### 📡 Pecan Street IoT Verisiyle Güç Profili Validasyonu")
    st.caption(
        "Pecan Street Dataport — Austin, Texas'ta 25 gerçek ev, 2018 yılı boyunca "
        "15 dakikalık devre seviyesi ölçümler. "
        "**air1** kolonu gerçek AC (klima) gücüdür (kW). "
        "Simüle edilen sistemlerin güç kararları, gerçek evin klima tüketimiyle karşılaştırılır."
    )

    try:
        pecan_df = pecan_yukle(PECAN_PATH)

        # ── Ev ve Gün Seçimi ─────────────────────────────────────────────────
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            ev_listesi = sorted(pecan_df["dataid"].unique())
            secilen_ev = st.selectbox("🏠 Ev Seç (dataid)", ev_listesi,
                                       index=ev_listesi.index(7951) if 7951 in ev_listesi else 0)
        with col_s2:
            ay_map = {6:"Haziran",7:"Temmuz",8:"Ağustos",9:"Eylül"}
            secilen_ay = st.selectbox("📅 Ay Seç (yaz sezonu)",
                                       options=[6,7,8,9],
                                       format_func=lambda x: ay_map[x],
                                       index=1)
        with col_s3:
            ev_ay = pecan_df[
                (pecan_df["dataid"] == secilen_ev) &
                (pecan_df["local_15min"].dt.month == secilen_ay)
            ]
            gunler = sorted(ev_ay["local_15min"].dt.date.unique())
            secilen_gun = st.selectbox("📆 Gün Seç",
                                        options=gunler,
                                        index=min(14, len(gunler)-1))

        # Seçilen günün verisi
        gun_df = ev_ay[ev_ay["local_15min"].dt.date == secilen_gun].copy()
        gun_df = gun_df.sort_values("local_15min").head(24).reset_index(drop=True)

        if len(gun_df) < 24:
            st.warning(f"Seçilen gün için yeterli veri yok ({len(gun_df)} saat). Başka bir gün deneyin.")
        elif "air1" not in gun_df.columns or gun_df["air1"].isna().all():
            st.warning("Seçilen ev ve günde air1 (klima) verisi yok. Başka bir ev/gün seçin.")
        else:
            gercek_air1 = gun_df["air1"].fillna(0).values   # gerçek klima gücü (kW)
            saatler_24  = list(range(24))

            # ── Simüle sistemlerin güç profilleri (mevcut df'den) ─────────────
            sim_gel  = df["Gel_kWh"].values
            sim_ml   = df["ML_kWh"].values
            sim_ajan = df["Ajan_kWh"].values

            # ── Metrikler: her sistem vs gerçek air1 ─────────────────────────
            def metrik(pred, gercek):
                mae  = mean_absolute_error(gercek, pred)
                rmse = mean_squared_error(gercek, pred) ** 0.5
                r2   = r2_score(gercek, pred)
                return mae, rmse, r2

            mae_g,  rmse_g,  r2_g  = metrik(sim_gel,  gercek_air1)
            mae_ml, rmse_ml, r2_ml = metrik(sim_ml,   gercek_air1)
            mae_aj, rmse_aj, r2_aj = metrik(sim_ajan, gercek_air1)

            # ── KPI satırı ───────────────────────────────────────────────────
            st.markdown(f"**Ev {secilen_ev} — {secilen_gun} — Gerçek air1 (ortalama {gercek_air1.mean():.2f} kW)**")
            kc1, kc2, kc3 = st.columns(3)
            kc1.metric("Geleneksel R²", f"{r2_g:.3f}",  f"MAE {mae_g:.3f} kW")
            kc2.metric("ML Modeli R²",  f"{r2_ml:.3f}", f"MAE {mae_ml:.3f} kW")
            kc3.metric("Ajan Sistemi R²",f"{r2_aj:.3f}",f"MAE {mae_aj:.3f} kW")

            st.divider()

            # ── Ana Grafik: gerçek air1 vs 3 sistem ──────────────────────────
            fig_ps = go.Figure()
            fig_ps.add_trace(go.Scatter(
                x=saatler_24, y=gercek_air1,
                name="Gerçek Klima Gücü (air1)",
                line=dict(color="#26c6da", width=3),
                mode="lines+markers",
            ))
            fig_ps.add_trace(go.Scatter(
                x=saatler_24, y=sim_gel,
                name="Geleneksel (simüle)",
                line=dict(color="#ef5350", width=2, dash="dash"),
                mode="lines+markers",
            ))
            fig_ps.add_trace(go.Scatter(
                x=saatler_24, y=sim_ml,
                name="ML Modeli (simüle)",
                line=dict(color="#42a5f5", width=2),
                mode="lines+markers",
            ))
            fig_ps.add_trace(go.Scatter(
                x=saatler_24, y=sim_ajan,
                name="Ajan Sistemi (simüle)",
                line=dict(color="#ab47bc", width=2),
                mode="lines+markers",
            ))
            fig_ps.update_layout(
                title=f"Gerçek Klima Gücü vs Simülasyon — Ev {secilen_ev}, {secilen_gun}",
                xaxis_title="Saat", yaxis_title="Güç (kW)",
                hovermode="x unified",
                legend=dict(orientation="h", y=1.13),
                height=440,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#cfe2ff",
            )
            st.plotly_chart(fig_ps, use_container_width=True)

            # ── Hata grafikleri ───────────────────────────────────────────────
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                hata_df = pd.DataFrame({
                    "Saat": saatler_24 * 3,
                    "Hata (kW)": (
                        list(sim_gel  - gercek_air1) +
                        list(sim_ml   - gercek_air1) +
                        list(sim_ajan - gercek_air1)
                    ),
                    "Sistem": (
                        ["Geleneksel"] * 24 +
                        ["ML Modeli"]  * 24 +
                        ["Ajan"]       * 24
                    ),
                })
                fig_hata = px.bar(
                    hata_df, x="Saat", y="Hata (kW)", color="Sistem",
                    barmode="group",
                    title="Saatlik Güç Hatası (Simüle − Gerçek)",
                    color_discrete_map={
                        "Geleneksel": "#ef5350",
                        "ML Modeli":  "#42a5f5",
                        "Ajan":       "#ab47bc",
                    },
                )
                fig_hata.add_hline(y=0, line_dash="dash",
                                   line_color="#ffffff", opacity=0.3)
                fig_hata.update_layout(
                    height=320,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#cfe2ff",
                )
                st.plotly_chart(fig_hata, use_container_width=True)

            with col_h2:
                # Aylık toplam tüketim karşılaştırması
                ev_ay_toplam = ev_ay.groupby(ev_ay["local_15min"].dt.date)["air1"].sum().reset_index()
                ev_ay_toplam.columns = ["Tarih", "Gerçek air1 (kWh/gün)"]
                fig_ay = px.bar(
                    ev_ay_toplam, x="Tarih", y="Gerçek air1 (kWh/gün)",
                    title=f"Ev {secilen_ev} — {ay_map[secilen_ay]} Günlük Klima Tüketimi",
                    color_discrete_sequence=["#26c6da"],
                )
                if secilen_gun in ev_ay_toplam["Tarih"].values:
                    fig_ay.add_vline(
                        x=str(secilen_gun), line_dash="dash",
                        line_color="#ffa726", annotation_text="Seçili gün",
                        annotation_font_color="#ffa726"
                    )
                fig_ay.update_layout(
                    height=320,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#cfe2ff",
                )
                st.plotly_chart(fig_ay, use_container_width=True)

            # ── Karşılaştırma Tablosu ─────────────────────────────────────────
            st.divider()
            st.markdown("#### 📋 Saat Saat Güç Karşılaştırma Tablosu")
            tablo_ps = pd.DataFrame({
                "Saat":                saatler_24,
                "Gerçek air1 (kW)":    gercek_air1.round(3),
                "Geleneksel (kW)":     [round(v,3) for v in sim_gel],
                "Hata Gel. (kW)":      [round(s-g,3) for s,g in zip(sim_gel, gercek_air1)],
                "ML Modeli (kW)":      [round(v,3) for v in sim_ml],
                "Hata ML (kW)":        [round(s-g,3) for s,g in zip(sim_ml, gercek_air1)],
                "Ajan Sistemi (kW)":   [round(v,3) for v in sim_ajan],
                "Hata Ajan (kW)":      [round(s-g,3) for s,g in zip(sim_ajan, gercek_air1)],
            })
            st.dataframe(
                tablo_ps.style
                .format({c: "{:.3f}" for c in tablo_ps.columns if c != "Saat"})
                .background_gradient(subset=["Hata ML (kW)"],   cmap="RdBu", vmin=-2, vmax=2)
                .background_gradient(subset=["Hata Ajan (kW)"], cmap="RdBu", vmin=-2, vmax=2),
                use_container_width=True,
                height=420,
            )

            with st.expander("📚 Bu validasyon ne anlama geliyor?"):
                st.markdown(f"""
**Pecan Street Validasyonu — Yöntem:**

Bu sekmede UCI'dan farklı bir strateji kullanıyoruz:

| | UCI Validasyonu (eski) | Pecan Street (yeni) |
|--|--|--|
| Karşılaştırılan | İç sıcaklık tahmini vs gerçek sensör | Güç kararı vs gerçek klima tüketimi |
| P_klima sorunu | P_klima = 0 varsayımı vardı | Gerçek air1 doğrudan karşılaştırılıyor |
| Veri kaynağı | Belçika evi, sıcaklık sensörü | Austin TX, devre seviyesi sayaç |

**R² nasıl yorumlanır?**
- R² yüksek → sistemimiz gerçek evin klima davranışına benzer kararlar alıyor
- R² düşük → normal; çünkü farklı bina parametreleri, farklı iklim koşulları
- Sidebar'dan **Gün Temel Sıcaklığı'nı** Austin TX'e göre ayarla (yaz ~34°C, dalgalanma ~7°C)

> Veri seti: *Pecan Street Dataport — 15-Minute Residential Data, Austin TX, 2018*
> [pecanstreet.org/dataport](https://dataport.pecanstreet.org/)
                """)

    except FileNotFoundError:
        st.error(
            f"❌ Veri seti bulunamadı: `{PECAN_PATH}`\n\n"
            "Pecan Street veri setini indirip belirtilen konuma kaydet."
        )
    except Exception as e:
        st.error(f"❌ Veri yüklenirken hata: {e}")

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
