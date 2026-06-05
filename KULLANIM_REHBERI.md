# 📖 Kullanım Rehberi
## Bina Enerji Yönetimi Dijital İkiz Simülatörü

---

## Uygulama Nedir?

Bu uygulama, bir binanın enerji yönetimini **gerçek bir binaya ihtiyaç duymadan** simüle eder.
Sol taraftaki sliderları değiştirince sağdaki tüm grafikler ve sonuçlar anında güncellenir.

Üç farklı sistem karşılaştırılır:
- 🔴 **Geleneksel** → basit açma/kapama kuralları
- 🔵 **ML Modeli** → veriden öğrenilmiş akıllı kararlar
- 🟣 **Ajan Sistemi** → üç ajanın birlikte karar verdiği sistem

---

## Sol Panel — Ne Ayarlanır?

### 🌡️ Hava & Bina Koşulları
| Slider | Ne Yapar |
|--------|----------|
| **Gün Temel Sıcaklığı** | O günün ne kadar sıcak geçeceğini belirler (10–42°C) |
| **Sıcaklık Dalgalanması** | Gece ile öğle arası sıcaklık farkı |

> 📌 Örnek: Yazın sıcak bir gün için → Temel Sıcaklık: 36, Dalgalanma: 6

---

### 👥 Bina Kullanım Profili
| Slider | Ne Yapar |
|--------|----------|
| **Mesai Başlangıcı** | Binaya kaçta girildiği |
| **Mesai Bitişi** | Binadan kaçta çıkıldığı |
| **Maksimum Kişi** | En kalabalık saatteki kişi sayısı |

> 📌 Mesai dışında bina boş sayılır → klimalar standby'a geçer

---

### ⚡ Klima & Maliyet
| Slider | Ne Yapar |
|--------|----------|
| **Klima Maks. Gücü** | Klimanın en yüksek çıkış gücü (kW) |
| **Standby Gücü** | Klima kapalıyken çektiği bekleme gücü |
| **Normal Tarife** | Düşük saatler elektrik fiyatı (TL/kWh) |
| **Pik Tarife** | Yoğun saatler (12:00–15:00, 18:00–22:00) fiyatı |

---

### 🤖 ML Modeli
| Slider | Ne Yapar |
|--------|----------|
| **Karar Ağacı Sayısı** | Modelin karmaşıklığı — artınca daha iyi ama yavaş |
| **Ağaç Derinliği** | Her ağacın öğrenme derinliği |

---

### 🏠 Bina Fiziksel Parametreleri
| Slider | Ne Yapar |
|--------|----------|
| **Yalıtım Katsayısı (α)** | Düşük = iyi yalıtım, yavaş ısınır/soğur. Yüksek = kötü yalıtım |
| **Kişi Başı Isı (β)** | Her kişinin ortama kattığı sıcaklık artışı |

---

### 🤝 Ajan Öncelik Ağırlıkları
Üç ajanın koordinatördeki payını belirler. Toplamı otomatik 1.0'a normalize edilir.

| Slider | Ajan ne ister |
|--------|--------------|
| **Konfor Ağırlığı** | İç sıcaklık 20–26°C bandında kalsın |
| **Maliyet Ağırlığı** | Elektrik faturası düşük olsun |
| **Sürdürülebilirlik** | Mümkün olan en az enerji kullanılsın |

> 📌 Konfor ağırlığını 0.80 yapıp diğerlerini düşür → sistem her zaman serin tutar, maliyet artar

---

## Sağ Taraf — Sonuçlar

### 📊 Özet Sonuç Kartları (KPI)

Sayfanın üstünde **8 kart** var, iki satır halinde:

- **Üst satır** → ML Modeli ne kadar tasarruf etti?
- **Alt satır** → Ajan Sistemi ne kadar tasarruf etti?

Her kart için: enerji %, maliyet TL, CO₂ kg gösterilir.

---

## Sekmeler — 6 Adet

### ⚡ Güç Karşılaştırması
Üç sistemin saatlik klima gücü tek grafikte görünür.
- Kırmızı kesik çizgi → Geleneksel
- Mavi çizgi → ML
- Mor çizgi → Ajan
- Renkli çubuklar → elektrik tarifesi (kırmızı = pik saat)

---

### 🌡️ Sıcaklık & Doluluk
- Sol grafik: dış sıcaklık eğrisi (sinüs dalgası)
- Sağ grafik: saatlik bina doluluk (çan eğrisi)

---

### 🤖 ML Model İçgörüleri
- **Özellik önem grafiği** → model hangi değişkene ne kadar önem veriyor?
  - T_iç ~%35 (en önemli) — model konfor durumuna göre karar veriyor
  - T_dış ~%28, Tarife ~%20, Kişi ~%12, Saat ~%5
- **Saatlik tasarruf grafiği** → ML sistemi her saatte kaç TL kazandırıyor?

---

### 🏠 Dijital İkiz — İç Sıcaklık
Binanın **içinin** saat saat nasıl değiştiğini gösterir.

- Yeşil bant → konfor bölgesi (20–26°C)
- Turuncu noktalı → dış sıcaklık referansı
- Kırmızı kesik → Geleneksel sistem içi
- Mavi → ML sistemi içi
- Mor (kalın) → Ajan sistemi içi

> 📌 **Önemli:** Grafiğin altındaki kutuda ısı dengesi denklemi açıklanıyor.
> Bir sistemin gücü düşürünce iç sıcaklığın nasıl yükseldiği burada görülür.

---

### 🤝 Ajan Kararları
- Üstte üç kartın özeti: her ajanın ağırlığı ve hedefi
- **Gruplu çubuk grafik** → her saatte üç ajanın ayrı önerileri
- **Mor çizgi** → koordinatörün birleşik kararı
- **Alt tablo** → saat saat tüm ajanların oyları

---

### 📡 IoT Validasyonu
Gerçek bir binanın sensör verisiyle modelimizi test eder.

**Nasıl kullanılır:**
1. "🌐 UCI Veri Setini İndir" butonuna bas
2. İndirme tamamlanınca bir slider çıkar → istediğin günü seç
3. Grafik gösterilir: gerçek sensör vs Dijital İkiz tahmini

**Sonuçlar ne anlama gelir:**
| Metrik | İyi değer | Yorumu |
|--------|-----------|--------|
| **MAE** | < 1.5 °C | Ortalama hata az |
| **RMSE** | < 2.0 °C | Büyük sapmalar az |
| **R²** | > 0.70 | Model gerçeği iyi yakalıyor |

> ⚠️ **Not:** R² düşük çıkabilir. Sebep: gerçek evde klima çalışıyordu, simülasyonda onu bilemiyoruz. Bu normal ve beklenen bir sınırlılıktır.

---

## Hızlı Demo Senaryoları

### Senaryo A — "Sistemi anlat"
1. Varsayılan parametrelerle aç
2. KPI kartlarına bak: ML sistemi %30, Ajan %37 tasarruf sağlıyor
3. "⚡ Güç Karşılaştırması" sekmesine geç — pik saatlerde ML ve Ajan gücü nasıl düşürüyor göster
4. "🏠 Dijital İkiz" sekmesine geç — iç sıcaklık farklarını anlat

### Senaryo B — "Sıcak gün testi"
1. Temel Sıcaklık → 38°C yap
2. KPI kartlarındaki tasarruf yüzdelerinin nasıl değiştiğine bak
3. Dijital İkiz sekmesinde iç sıcaklığın konfor bandını nasıl aştığını göster

### Senaryo C — "Ajan önceliği değiştir"
1. Konfor Ağırlığı → 0.70 yap
2. Maliyet ve Sürdürülebilirlik → 0.15'e düşür
3. Ajan Kararları sekmesinde koordinatörün nasıl değiştiğini göster

### Senaryo D — "IoT Validasyonu"
1. 📡 IoT Validasyonu sekmesine geç
2. İndir butonuna bas, bir gün seç
3. MAE/RMSE/R² metriklerini yorumla
4. Yalıtım Katsayısı sliderını değiştirerek R²'nin nasıl değiştiğini göster

---

## Sık Sorulan Sorular

**S: Neden ML modeli her zaman Ajan sisteminden kötü?**
A: ML öğrenilen sabit bir model. Ajan sistemi anlık T_iç'e bakarak daha esnek karar alıyor.

**S: R² skoru neden düşük çıkıyor?**
A: Gerçek evde klima vardı, simülasyonda bilmiyoruz. Bu beklenen bir sınırlılık.

**S: Sliderı değiştirince neden biraz gecikiyor?**
A: ML modeli her parametreden sonra yeniden eğitiliyor (8.760 örnek). Karar ağacı sayısını düşürünce hızlanır.

**S: Geleneksel sistem neden bazen ML'den iyi görünüyor?**
A: Geleneksel sistem T_iç > 24°C olunca tam güç açıyor — çok agresif. Bazı koşullarda bu "tesadüfen" iyi sonuç verebilir ama maliyet çok yüksek olur.
