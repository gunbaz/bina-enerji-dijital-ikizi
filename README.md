# 🏢 Bina Enerji Yönetimi — Dijital İkiz & Ajan Sistemi

> **Kural Tabanlı Bina Enerji Yönetimi Performans Dijital İkizi**  
> Gerçek bir binaya ihtiyaç duymadan, üç farklı kontrol yaklaşımının enerji tüketimi, maliyet ve karbon emisyonu üzerindeki etkilerini simüle eden interaktif bir Performans Dijital İkizi.

---

## 📌 Proje Hakkında

Bu proje, akıllı bina enerji yönetimini üç farklı karar mekanizmasıyla karşılaştıran bir **Performans Dijital İkizi** simülatörüdür:

| Sistem | Karar Mekanizması | Özellik |
|--------|-------------------|---------|
| **Geleneksel** | If/Else kuralları | Sabit eşik değerleri, esneksiz |
| **ML Modeli** | Random Forest | 8.760 örnekten öğrenilmiş örüntüler |
| **Ajan Sistemi** | Çoklu Otonom Ajan | Gerçek zamanlı geri beslemeli kapalı döngü |

Projenin **dijital ikiz** boyutu, binanın fiziksel ısı dinamiğini saat-saat simüle etmesidir: her sistemin klima kararı bir sonraki saatin iç sıcaklığını doğrudan etkiler.

---

## 🎯 Proje Amaçları

- Binalardaki enerji israfının temel nedenlerini simülasyon yoluyla görselleştirmek
- Geleneksel if/else sistemleri ile makine öğrenmesi ve ajan tabanlı sistemleri karşılaştırmak
- Fiziksel ısı dengesi denklemiyle gerçekçi bir Dijital İkiz modeli oluşturmak
- Çoklu ajan mimarisinde koordinasyon ve müzakere mekanizmasını göstermek
- Enerji tasarrufu, maliyet azaltımı ve CO₂ emisyonu KPI'larını interaktif sunmak

---

## 🏗️ Sistem Mimarisi

```
┌─────────────────────────────────────────────────┐
│              KULLANICI GİRDİLERİ                │
│  Sıcaklık · Doluluk · Tarife · Yalıtım · ...   │
└────────────────────┬────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
   ┌──────────┐ ┌─────────┐ ┌──────────────────────────┐
   │Geleneksel│ │  ML     │ │    AJAN SİSTEMİ           │
   │ If/Else  │ │ Random  │ │  ┌─────────────────────┐  │
   │          │ │ Forest  │ │  │ Konfor Ajanı 🔵     │  │
   └────┬─────┘ └────┬────┘ │  │ (T_iç → güç önerisi)│  │
        │            │      │  ├─────────────────────┤  │
        │            │      │  │ Maliyet Ajanı 🟢    │  │
        ▼            ▼      │  │ (tarife → güç öneri)│  │
   ┌─────────────────────┐  │  ├─────────────────────┤  │
   │  ISI DENGESİ        │  │  │ Sürdürülebilirlik 🟠│  │
   │  DİJİTAL İKİZ       │  │  │ (enerji minimize)   │  │
   │                     │  │  ├─────────────────────┤  │
   │ T_iç[t+1] =         │◄─┤  │ Koordinatör ⚖️     │  │
   │  T_iç[t]            │  │  │ (ağırlıklı ortalama)│  │
   │  + α(T_dış - T_iç)  │  │  └─────────────────────┘  │
   │  + β·N              │  └──────────────────────────┘
   │  - γ·P_klima        │
   └─────────────────────┘
                     │
                     ▼
   ┌─────────────────────────────────────────────────┐
   │              KPI & GÖRSELLEŞTİRME              │
   │  Enerji % · Maliyet TL · CO₂ kg · İç Sıcaklık │
   └─────────────────────────────────────────────────┘
```

---

## 🤖 Çoklu Ajan Mimarisi

Ajan sistemi, bağımsız hedeflere sahip üç uzman ajandan ve bir koordinatörden oluşur:

### Konfor Ajanı 🔵
- **Hedef:** İç ortam sıcaklığını 20–26 °C konfor bandında tutmak
- **Girdi:** Dijital İkiz'den anlık iç sıcaklık (T_iç)
- **Karar mantığı:**
  - T_iç > 26 °C → sıcaklığa orantılı güç artışı
  - T_iç < 20 °C → soğutma gerekmez, standby
  - Konfor bandında → minimum güç

### Maliyet Ajanı 🟢
- **Hedef:** Elektrik maliyetini minimize etmek
- **Girdi:** Anlık elektrik tarifesi + bina doluluk durumu
- **Karar mantığı:**
  - Pik tarife + boş bina → standby gücü
  - Pik tarife + dolu bina → %40 güç
  - Normal tarife + dolu → %60 güç

### Sürdürülebilirlik Ajanı 🟠
- **Hedef:** Toplam enerji tüketimi ve CO₂ emisyonunu minimize etmek
- **Girdi:** Bina doluluk durumu
- **Karar mantığı:**
  - Boş bina → standby (her zaman)
  - Dolu bina → sabit %35 güç

### Koordinatör Ajan ⚖️
Her üç ajanın önerisini kullanıcı tanımlı ağırlıklarla birleştirir:

```
P_final = w_konfor × P_konfor + w_maliyet × P_maliyet + w_surd × P_surd
P_final = clip(P_final, standby_gucu, klima_gucu)
```

Ağırlıklar otomatik olarak normalize edilir: `w_konfor + w_maliyet + w_surd = 1.0`

---

## 🏠 Dijital İkiz — Isı Dengesi Modeli

Binanın fiziksel davranışı aşağıdaki diferansiyel denklemle modellenir:

```
T_iç[t+1] = T_iç[t] + α·(T_dış[t] − T_iç[t]) + β·N[t] − γ·P_klima[t]
```

| Parametre | Sembol | Açıklama | Varsayılan |
|-----------|--------|----------|------------|
| Yalıtım katsayısı | α | Bina dışıyla ısı alışveriş hızı | 0.15 |
| Kişi başı ısı | β | Her kişinin iç ortama saat başı katkısı (°C) | 0.05 |
| Soğutma verimliliği | γ | Klimanın °C düşürme katsayısı | 0.80 |
| Kişi sayısı | N[t] | t. saatteki bina doluluk | — |
| Klima gücü | P[t] | t. saatteki klima güç çıkışı (kW) | — |

**Geleneksel yazılımdan farkı:** Her sistemin klima kararı bir sonraki saatin iç sıcaklığını değiştirir. Ajan sistemi bu geri bildirimi gerçek zamanlı olarak kullanır — bu **kapalı döngü kontrol** dijital ikilerin temel özelliğidir.

---

## 🌲 ML Modeli — Random Forest

### Eğitim Süreci
- **Veri:** 365 gün × 24 saat = 8.760 sentetik örnek
- **Özellikler:** Saat, dış sıcaklık, kişi sayısı, elektrik tarifesi
- **Hedef:** Uzman tarafından belirlenmiş optimal klima gücü (kW)
- **Algoritma:** `RandomForestRegressor` (scikit-learn)

### Özellik Önem Sıralaması (tipik)
```
Dış Sıcaklık    ████████████████░░░░  ~42%
Elektrik Tarife ████████████░░░░░░░░  ~31%
Kişi Sayısı     ███████░░░░░░░░░░░░░  ~18%
Saat            ████░░░░░░░░░░░░░░░░   ~9%
```

---

## 📊 Dashboard Özellikleri

### KPI Kartları (2 Satır)
- **Satır 1 — ML vs Geleneksel:** Enerji tasarrufu %, maliyet tasarrufu, CO₂ azaltımı, toplam maliyet
- **Satır 2 — Ajan vs Geleneksel:** Aynı metrikler ajan sistemi için

### Sekmeler
| Sekme | İçerik |
|-------|--------|
| ⚡ Güç Karşılaştırması | 3 sistemin saatlik güç profili + tarife çubukları |
| 🌡️ Sıcaklık & Doluluk | Dış sıcaklık eğrisi + doluluk bar grafiği |
| 🤖 ML Model İçgörüleri | Özellik önem skoru + saatlik tasarruf grafiği |
| 🏠 Dijital İkiz — İç Sıcaklık | İç sıcaklık dinamiği + konfor bandı + denklem |
| 🤝 Ajan Kararları | Ajan önerileri grouped bar + koordinatör + oy tablosu |

---

## 🚀 Kurulum & Çalıştırma

### 1. Gereksinimler

```bash
pip install -r requirements.txt
```

`requirements.txt`:
```
streamlit
pandas
plotly
scikit-learn
```

### 2. Uygulamayı Başlatma

```bash
streamlit run app.py
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

> Ağırlıklar otomatik normalize edilir, toplamları her zaman 1.0'dır.

---

## 📁 Proje Yapısı

```
proje/
│
├── app.py                              # Ana Streamlit uygulaması
├── requirements.txt                    # Python bağımlılıkları
├── make_pptx.js                        # Sunum üretici script (Node.js)
├── bina_enerji_dijital_ikiz_sunum.pptx # 4 slaytlık akademik sunum
└── README.md                           # Bu dosya
```

---

## 🔬 Kullanılan Teknolojiler

| Teknoloji | Sürüm | Kullanım Amacı |
|-----------|-------|----------------|
| Python | 3.11+ | Ana dil |
| Streamlit | latest | Web arayüzü |
| Pandas | latest | Veri işleme |
| Plotly | latest | İnteraktif grafikler |
| Scikit-learn | latest | Random Forest ML modeli |
| NumPy | latest | Sayısal hesaplama |
| PptxGenJS | 4.0.1 | Sunum oluşturma |

---

## 📈 Örnek Çıktılar (Varsayılan Parametreler)

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

### Senaryo 1 — Yazın Sıcak Gün
```
Temel Sıcaklık: 38°C | Dalgalanma: 6°C | Yalıtım: 0.25
```
Geleneksel sistem sürekli tam güçte çalışırken, ajan sistemi pik tarife saatlerinde gücü düşürür.

### Senaryo 2 — Düşük Ağırlıklı Maliyet Ajanı
```
Konfor: 0.70 | Maliyet: 0.15 | Sürdürülebilirlik: 0.15
```
Koordinatör ağırlıklı olarak konfor ajanını dinler → iç sıcaklık her zaman 20–26°C bandında.

### Senaryo 3 — Zayıf Yalıtımlı Bina
```
Yalıtım Katsayısı: 0.28 | Kişi Başı Isı: 0.15
```
İç sıcaklık dış sıcaklığa daha hızlı yaklaşır → Konfor Ajanı çok daha agresif kararlar alır.

---

## 📚 Akademik Bağlam

Bu proje aşağıdaki kavramları pratik olarak göstermektedir:

- **Dijital İkiz (Digital Twin):** Fiziksel bir varlığın (bina) gerçek zamanlı sanal kopyası
- **Çoklu Ajan Sistemi (MAS):** Bağımsız hedeflere sahip ajanların koordinasyonu
- **BEMS (Building Energy Management System):** Bina enerji yönetim sistemi
- **Kapalı Döngü Kontrol:** Çıktının (iç sıcaklık) bir sonraki girdiyi (klima kararı) etkilemesi
- **Random Forest:** Ensemble öğrenme yöntemi ile kural yazmaksızın optimizasyon

---

## 👤 Geliştirici

**Furkan Günbaş**  
GitHub: [@gunbaz](https://github.com/gunbaz)

---

## 📄 Lisans

Bu proje akademik amaçlı geliştirilmiştir. Kaynak göstererek kullanılabilir.
