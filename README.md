# 🏢 Bina Enerji Yönetimi — Dijital İkiz & Ajan Sistemi

> Gerçek bir binaya ihtiyaç duymadan, üç farklı kontrol yaklaşımının enerji tüketimi, maliyet ve karbon emisyonu üzerindeki etkilerini fiziksel ısı dinamiğiyle simüle eden interaktif bir **Performans Dijital İkizi**.

---

## 📌 Proje Hakkında

Bu proje, akıllı bina enerji yönetimini üç farklı karar mekanizmasıyla karşılaştıran bir simülatördür. Üç sistemin tamamı da **kapalı döngü** (closed-loop) çalışır: her saatin klima kararı, binanın fiziksel ısı denklemi üzerinden bir sonraki saatin iç sıcaklığını doğrudan etkiler.

| Sistem | Karar Mekanizması | Döngü Tipi | Özellik |
|--------|-------------------|------------|---------|
| **Geleneksel** | If/Else kuralları | Kapalı döngü | T_iç eşiğine göre karar (T_dış değil) |
| **ML Modeli** | Random Forest | Kapalı döngü | T_iç özellikli, konfor odaklı öğrenme |
| **Ajan Sistemi** | Çoklu Otonom Ajan | Kapalı döngü | 3 ajan + koordinatör, Dijital İkiz geri beslemeli |

---

## ✅ Uygulanan Teknik Düzeltmeler

Başlangıç implementasyonundaki üç kritik mimari sorun tespit edilerek düzeltilmiştir:

### Düzeltme 1 — ML Modeline T_iç Özelliği Eklendi
**Sorun:** Orijinal ML modeli `[Saat, T_dış, Kişi, Fiyat]` özelliklerini kullanıyordu. Hedef (`OptimalGuc`) büyük ölçüde elektrik fiyatına göre belirlendiğinden, model aslında bir fiyat-güç kuralını ezberliyordu. Binanın o andaki ısıl durumundan (T_iç) tamamen habersizdi.

**Düzeltme:** Eğitim sırasında T_iç her saat simüle edilerek özellik setine eklendi.
```
Eski özellikler: [Saat, T_dış, Kişi, Fiyat]
Yeni özellikler: [Saat, T_dış, T_iç, Kişi, Fiyat]
```
Hedef güç artık **T_iç konfor durumuna** göre belirleniyor: T_iç > 28°C ise fiyat ne olursa olsun tam güç; T_iç ≤ 24°C ise konforlu sayılıp standby. Fiyat yalnızca ikincil faktör.

### Düzeltme 2 — Geleneksel ve ML Sistemleri Kapalı Döngüye Alındı
**Sorun:** Geleneksel sistem `T_dış > 24°C` eşiğine bakıyordu — içerisi buz kesse bile dışarısı sıcak diye klimayı açmaya devam edebilirdi. ML ise tek seferde 24 tahmini üretip bitiriyordu; kararları T_iç'i değiştirdiğinde bir sonraki saatte bunu göremiyordu.

**Düzeltme:** Her iki sistem de saat-saat döngüyle yeniden yazıldı:

```python
# Geleneksel — artık T_iç eşiği kullanıyor
if N > 0 and T_ic > 24:   # konforlu değil VE dolu → klima aç
    p = klima_gucu
...
T_ic[t+1] = T_ic[t] + α(T_dış−T_ic) + β·N − γ·P  # geri besleme

# ML — her saatin T_ic'ini bir sonraki adıma besliyor
for t in range(24):
    p = model.predict([[saat, T_dış, T_ic, N, fiyat]])
    T_ic[t+1] = T_ic[t] + α(T_dış−T_ic) + β·N − γ·P  # kapalı döngü
```

### Düzeltme 3 — UCI Validasyon Sınırlılığı Belgelendi
**Sorun:** IoT validasyonunda P_klima = 0 kabul ediliyordu. Belçika evinde gerçekte aktif ısıtma/soğutma sistemi çalışıyordu, bu yüzden simülasyon ile gerçek sensör verisi arasındaki sapma kaçınılmazdı ve R² yorumu yanıltıcı olabilirdi.

**Düzeltme:** Uygulama içindeki validasyon bölümüne açık bir sınırlılık notu eklendi. P_klima = 0 varsayımının ne anlama geldiği, hangi saatlerde R²'nin neden düşük çıkacağı ve gerçek çözüm için ne gerektiği (ayrı HVAC sayacı) belgelendi.

---

## 🏗️ Sistem Mimarisi

```
┌──────────────────────────────────────────────────────────────┐
│                    KULLANICI GİRDİLERİ                       │
│  Sıcaklık · Doluluk · Tarife · Yalıtım (α) · Kişi ısısı (β)│
└───────────────┬──────────────────────────────────────────────┘
                │
    ┌───────────┼─────────────────────┐
    ▼           ▼                     ▼
┌──────────┐ ┌──────────────────┐ ┌──────────────────────────┐
│Geleneksel│ │   ML Modeli      │ │     AJAN SİSTEMİ          │
│ If/Else  │ │ Random Forest    │ │  ┌──────────────────────┐ │
│ Kapalı   │ │ [Saat,T_dış,T_iç│ │  │ Konfor Ajanı 🔵      │ │
│ Döngü ✅ │ │  Kişi, Fiyat]   │ │  │ (T_iç → güç önerisi) │ │
│          │ │ Kapalı Döngü ✅ │ │  ├──────────────────────┤ │
│T_iç>24°C│ │                  │ │  │ Maliyet Ajanı 🟢     │ │
│→ klima   │ │ t→predict(T_iç) │ │  │ (tarife → güç öneri) │ │
│  aç      │ │ →T_iç_yeni→t+1  │ │  ├──────────────────────┤ │
└────┬─────┘ └────────┬─────────┘ │  │ Sürdürülebilirlik 🟠 │ │
     │                │           │  │ (enerji minimize)    │ │
     │                │           │  ├──────────────────────┤ │
     ▼                ▼           │  │ Koordinatör ⚖️      │ │
┌──────────────────────────────┐  │  │ (ağırlıklı ortalama) │ │
│   ISI DENGESİ DİJİTAL İKİZ  │◄─┘  └──────────────────────┘ │
│                              │  └──────────────────────────┘
│ T_iç[t+1] = T_iç[t]         │
│  + α·(T_dış[t] − T_iç[t])   │  ← Yalıtım
│  + β·N[t]                    │  ← İnsan ısısı
│  − γ·P_klima[t]              │  ← Soğutma (γ = 0.8)
└──────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│           KPI & GÖRSELLEŞTİRME (6 Sekme)                    │
│  Enerji % · Maliyet TL · CO₂ kg · İç Sıcaklık · IoT Validas│
└──────────────────────────────────────────────────────────────┘
```

---

## 🤖 Çoklu Ajan Mimarisi

### Konfor Ajanı 🔵
- **Hedef:** İç ortam sıcaklığını 20–26 °C konfor bandında tutmak
- **Girdi:** Dijital İkiz'den her saatin anlık T_iç değeri
- **Karar mantığı:**
  - T_iç > 26 °C → sıcaklığa orantılı güç artışı (ne kadar fazla, o kadar güçlü)
  - T_iç < 20 °C → soğutmaya gerek yok, standby
  - 20–26 °C bandında → minimum güç yeterli

### Maliyet Ajanı 🟢
- **Hedef:** Elektrik maliyetini minimize etmek
- **Girdi:** Anlık elektrik tarifesi + bina doluluk durumu
- **Karar mantığı:**
  - Pik tarife + boş bina → standby
  - Pik tarife + dolu bina → %40 güç
  - Normal tarife + dolu → %60 güç

### Sürdürülebilirlik Ajanı 🟠
- **Hedef:** Toplam enerji tüketimi ve CO₂ emisyonunu minimize etmek
- **Girdi:** Bina doluluk durumu
- **Karar mantığı:**
  - Boş bina → standby (her zaman)
  - Dolu bina → sabit %35 güç

### Koordinatör Ajan ⚖️
```
P_final = w_konfor × P_konfor + w_maliyet × P_maliyet + w_surd × P_surd
P_final = clip(P_final, standby_gucu, klima_gucu)
```
Ağırlıklar otomatik normalize edilir: `w_konfor + w_maliyet + w_surd = 1.0`

---

## 🏠 Dijital İkiz — Isı Dengesi Modeli

```
T_iç[t+1] = T_iç[t] + α·(T_dış[t] − T_iç[t]) + β·N[t] − γ·P_klima[t]
```

| Sembol | Açıklama | Varsayılan |
|--------|----------|------------|
| **α** | Yalıtım katsayısı — bina dışıyla ısı alışveriş hızı | 0.15 |
| **β** | Kişi başı ısı katkısı (°C/kişi/saat) | 0.05 |
| **γ** | Soğutma verimliliği (sabit fizik sabiti) | 0.80 |
| **N[t]** | t. saatteki kişi sayısı | — |
| **P[t]** | t. saatteki klima güç çıkışı (kW) | — |

Bu denklem **üç sistemin tamamı** için kapalı döngü olarak çalışır. Her sistemin verdiği klima kararı bir sonraki saatin T_iç değerini değiştirir; bu da bir sonraki kararı etkiler.

---

## 🌲 ML Modeli — Random Forest

### Eğitim Süreci
- **Veri:** 365 gün × 24 saat = 8.760 sentetik örnek
- **Özellikler:** `[Saat, T_dış, T_iç, Kişi, Fiyat]` — T_iç her saat simüle edilerek dahil edilir
- **Hedef:** T_iç konfor durumuna dayalı optimal klima gücü (birincil kriter: konfor; ikincil: fiyat)
- **Algoritma:** `RandomForestRegressor` (scikit-learn)

### Hedef Belirleme Mantığı
| T_iç Durumu | Fiyat | Optimal Güç |
|-------------|-------|-------------|
| N = 0 (boş) | — | Standby (fiyat göz ardı) |
| T_iç > 28°C | Herhangi | **%100** — konfor kritik, fiyat göz ardı |
| T_iç > 26°C | Pik | %70 |
| T_iç > 26°C | Normal | %85 |
| T_iç > 24°C | Pik | %30 |
| T_iç > 24°C | Normal | %50 |
| T_iç ≤ 24°C | — | Standby |

### Özellik Önem Sıralaması (güncel — T_iç dahil)
```
İç Sıcaklık (T_iç) ███████████████░░░░░  ~35%  ← yeni, en önemli
Dış Sıcaklık (T_dış)████████████░░░░░░░░  ~28%
Elektrik Tarife     ████████░░░░░░░░░░░░  ~20%
Kişi Sayısı         █████░░░░░░░░░░░░░░░  ~12%
Saat                ██░░░░░░░░░░░░░░░░░░   ~5%
```

---

## 📡 IoT Validasyonu — UCI Dataset

**Veri seti:** Candanedo et al. (2017), *Appliances Energy Prediction*, UCI ML Repository  
**İçerik:** Belçika'da gerçek bir ev, 4,5 ay, 10 dakikalık ölçümler (~20.000 satır)  
**Değişkenler:** T_out (dış sıcaklık), T1–T9 (9 oda sıcaklığı), enerji tüketimi

### Validasyon Yaklaşımı
Gerçek T_out değerleri Dijital İkiz modelinin girdisi olarak kullanılır. Modelin ürettiği T_iç tahmini, gerçek sensör ortalamasıyla karşılaştırılır. Metrikler: **MAE**, **RMSE**, **R²**.

### ⚠️ Bilinen Sınırlılık: P_klima = 0 Varsayımı

Validasyonda klima gücü sıfır kabul edilerek binanın **doğal termal drifti** modellenmektedir. Gerçek evde aktif HVAC sistemi çalışıyordu; bu nedenle:

- HVAC kapalı saatlerde → R² yüksek çıkar (doğal drift iyi modellenir)
- HVAC aktif saatlerde → R² düşer (simülasyon HVAC etkisini bilmiyor)

Gerçek çözüm için ayrı bir HVAC enerji alt sayacı gerekmektedir.

---

## 📊 Dashboard — 6 Sekme

| Sekme | İçerik |
|-------|--------|
| ⚡ Güç Karşılaştırması | 3 sistemin saatlik güç profili + tarife çubukları |
| 🌡️ Sıcaklık & Doluluk | Dış sıcaklık eğrisi + doluluk bar grafiği |
| 🤖 ML Model İçgörüleri | 5 özellik önem skoru + saatlik tasarruf grafiği |
| 🏠 Dijital İkiz — İç Sıcaklık | 3 sistemin T_iç profili + konfor bandı + denklem |
| 🤝 Ajan Kararları | Ajan önerileri + koordinatör kararı + oy tablosu |
| 📡 IoT Validasyonu | UCI veri seti indirme/yükleme + MAE/RMSE/R² + hata grafikleri |

---

## 🚀 Kurulum & Çalıştırma

```bash
pip install -r requirements.txt
streamlit run app.py
```

`requirements.txt`:
```
streamlit
pandas
plotly
scikit-learn
```

Tarayıcıda `http://localhost:8501` adresinde açılır.

---

## 🎛️ Sidebar Parametreleri

### 🌡️ Hava & Bina Koşulları
| Parametre | Aralık | Açıklama |
|-----------|--------|----------|
| Gün Temel Sıcaklığı | 10–42 °C | Günün ortalama dış sıcaklığı |
| Sıcaklık Dalgalanması | 0–10 °C | Gece en düşük ile öğlen en yüksek farkı |

### 👥 Bina Kullanım Profili
| Parametre | Aralık | Açıklama |
|-----------|--------|----------|
| Mesai Başlangıcı | 6–10 saat | Çalışma saatleri başlangıcı |
| Mesai Bitişi | 14–22 saat | Çalışma saatleri bitişi |
| Maksimum Kişi | 5–100 kişi | En yoğun saatteki kişi sayısı |

### ⚡ Klima & Maliyet
| Parametre | Aralık | Açıklama |
|-----------|--------|----------|
| Klima Maks. Gücü | 1.0–5.0 kW | Klimanın maksimum çıkış gücü |
| Standby Gücü | 0.01–0.20 kW | Bekleme modundaki güç tüketimi |
| Normal Tarife | 1.0–4.0 TL/kWh | Saatlik elektrik birim fiyatı |
| Pik Tarife | 2.0–8.0 TL/kWh | Yoğun saatler elektrik birim fiyatı |

### 🤖 ML Modeli
| Parametre | Aralık | Açıklama |
|-----------|--------|----------|
| Karar Ağacı Sayısı | 10–200 | Random Forest ağaç sayısı |
| Ağaç Derinliği | 2–20 | Her ağacın maksimum derinliği |

### 🏠 Bina Fiziksel Parametreleri
| Parametre | Aralık | Açıklama |
|-----------|--------|----------|
| Yalıtım Katsayısı (α) | 0.05–0.30 | Dış ortamla ısı alışverişi hızı |
| Kişi Başı Isı (β) | 0.01–0.20 | Her kişinin iç ortama ısı katkısı |

### 🤝 Ajan Öncelik Ağırlıkları
| Parametre | Varsayılan | Açıklama |
|-----------|------------|----------|
| Konfor Ağırlığı | 0.40 | Konfor ajanının koordinatördeki payı |
| Maliyet Ağırlığı | 0.35 | Maliyet ajanının koordinatördeki payı |
| Sürdürülebilirlik Ağırlığı | 0.25 | Sürdürülebilirlik ajanının payı |

> Ağırlıklar otomatik normalize edilir.

---

## 📁 Proje Yapısı

```
proje/
├── app.py                              # Ana Streamlit uygulaması
├── requirements.txt                    # Python bağımlılıkları
├── make_pptx.js                        # Sunum üretici script (Node.js)
├── bina_enerji_dijital_ikiz_sunum.pptx # 4 slaytlık akademik sunum
└── README.md                           # Bu dosya
```

---

## 📈 Örnek Çıktılar

```
Gün Sıcaklığı: 26°C  |  Mesai: 08:00–18:00  |  Max Kişi: 45
Klima: 2.5 kW  |  Normal Tarife: 2.5 TL  |  Pik Tarife: 4.5 TL
```

| Metrik | Geleneksel | ML Modeli | Ajan Sistemi |
|--------|------------|-----------|--------------|
| Toplam Enerji (kWh) | ~40 kWh | ~28 kWh | ~25 kWh |
| Toplam Maliyet (TL) | ~130 TL | ~90 TL | ~82 TL |
| CO₂ Emisyonu (kg) | ~16 kg | ~11 kg | ~10 kg |
| Enerji Tasarrufu | — | ~%30 | ~%37 |

---

## 🧪 Senaryo Önerileri

### Senaryo 1 — Sıcak Yaz Günü
```
Temel Sıcaklık: 38°C | Dalgalanma: 6°C | Yalıtım: 0.25
```
T_iç hızla yükseliyor → ML modeli T_iç > 28°C'yi görünce fiyattan bağımsız tam güce geçiyor. Geleneksel sistem de T_iç eşiğini aşınca klima açıyor. Fark: ML pik tarife öncesi önceden soğutuyor.

### Senaryo 2 — Konfor Öncelikli Ajan
```
Konfor Ağırlığı: 0.70 | Maliyet: 0.15 | Sürdürülebilirlik: 0.15
```
Koordinatör Konfor Ajanı'nı baskın dinler → T_iç her zaman 20–26°C bandında kalır, maliyet artabilir.

### Senaryo 3 — Zayıf Yalıtımlı Bina
```
Yalıtım Katsayısı (α): 0.28 | Kişi Başı Isı: 0.15
```
T_iç dış sıcaklığa hızla yaklaşır → Konfor Ajanı çok daha agresif kararlar alır, ML modeli de T_iç'i sık sık eşik üzerinde görür.

### Senaryo 4 — IoT Kalibrasyon
```
IoT Validasyonu sekmesinden bir gün seç → Yalıtım (α) sliderını değiştir → R² maksimum noktayı bul
```
Bu noktada α, gerçek binanın termal geçirgenliğine kalibre edilmiş demektir.

---

## 📚 Akademik Bağlam

| Kavram | Projede Karşılığı |
|--------|------------------|
| **Dijital İkiz** | Fiziksel ısı dengesi denklemli, gerçek IoT ile doğrulanan sanal bina modeli |
| **Kapalı Döngü Kontrol** | T_iç → karar → T_iç döngüsü — 3 sistemin tamamında |
| **Çoklu Ajan Sistemi (MAS)** | 3 bağımsız ajan + koordinatör, ağırlıklı müzakere |
| **BEMS** | Bina Enerji Yönetim Sistemi — projenin uygulama alanı |
| **Random Forest** | T_iç konfor durumunu öğrenen ensemble model |
| **Model Validasyonu** | MAE, RMSE, R² — gerçek UCI IoT verisiyle karşılaştırma |

---

## 🔬 Kullanılan Teknolojiler

| Teknoloji | Kullanım Amacı |
|-----------|----------------|
| Python 3.11+ | Ana dil |
| Streamlit | Web arayüzü |
| Pandas | Veri işleme |
| Plotly | İnteraktif grafikler |
| Scikit-learn | Random Forest ML modeli |
| NumPy | Sayısal hesaplama |
| UCI ML Repository | Gerçek IoT validasyon verisi |
| PptxGenJS 4.0.1 | Sunum oluşturma |

---

## 👤 Geliştirici

**Furkan Günbaş** — GitHub: [@gunbaz](https://github.com/gunbaz)

---

## 📄 Lisans

Bu proje akademik amaçlı geliştirilmiştir. Kaynak göstererek kullanılabilir.
