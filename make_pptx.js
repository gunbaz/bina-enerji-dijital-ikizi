const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
pres.title  = "Bina Enerji Yonetimi Dijital Ikizi";

// ─── PALET ────────────────────────────────────────────────────────────────────
const C = {
  bg      : "0B1E35",   // koyu lacivert arka plan
  panel   : "162C47",   // kart arka planı
  accent  : "42A5F5",   // mavi vurgu
  accent2 : "00BFA5",   // yeşil-teal vurgu
  white   : "FFFFFF",
  muted   : "8AB4D4",
  dark    : "061325",
  warn    : "F59E0B",
  bar     : "1A3A5C",   // başlık bar
};

const makeShadow = () => ({
  type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.25
});

// ─── YARDIMCI: renkli kart ────────────────────────────────────────────────────
function card(slide, x, y, w, h, accentColor) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: C.panel },
    line: { color: accentColor || C.accent, width: 1.5 },
    shadow: makeShadow(),
  });
  // sol kenar şerit
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.07, h,
    fill: { color: accentColor || C.accent },
    line: { color: accentColor || C.accent, width: 0 },
  });
}

// ─── SLIDE 1 — PROJE KONUSU ───────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.bg };

  // Dekoratif daireler (arka planda)
  s.addShape(pres.shapes.OVAL, {
    x: 7.8, y: -1.0, w: 4.0, h: 4.0,
    fill: { color: "1A4A7A", transparency: 60 },
    line: { color: "1A4A7A", width: 0 },
  });
  s.addShape(pres.shapes.OVAL, {
    x: -1.2, y: 3.5, w: 3.5, h: 3.5,
    fill: { color: "005B8E", transparency: 70 },
    line: { color: "005B8E", width: 0 },
  });

  // Üst accent çizgisi
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });

  // Bina ikonu (geometrik)
  const bx = 0.55, by = 0.55;
  s.addShape(pres.shapes.RECTANGLE, {
    x: bx, y: by, w: 0.55, h: 0.55,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });
  s.addText("🏢", { x: bx - 0.02, y: by - 0.04, w: 0.6, h: 0.6, fontSize: 24, align: "center" });

  // Başlık
  s.addText("Kural Tabanlı Bina Enerji Yönetimi", {
    x: 0.5, y: 0.55, w: 9, h: 0.75,
    fontSize: 34, bold: true, color: C.white,
    fontFace: "Calibri", align: "left",
  });
  s.addText("Performans Dijital İkizi", {
    x: 0.5, y: 1.25, w: 9, h: 0.6,
    fontSize: 26, bold: false, color: C.accent,
    fontFace: "Calibri", align: "left",
  });
  s.addText("Akıllı Bina Sistemlerinde Makine Öğrenmesi Destekli Enerji Optimizasyonu", {
    x: 0.5, y: 1.82, w: 9, h: 0.4,
    fontSize: 13, color: C.muted, fontFace: "Calibri", align: "left", italic: true,
  });

  // Ayırıcı çizgi
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.3, w: 4.5, h: 0.03,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });

  // 4 madde — kart içinde
  const items = [
    { icon: "🔬", text: "Gerçek bina olmadan enerji yönetimi simülasyonu" },
    { icon: "🌐", text: "Streamlit tabanlı interaktif web arayüzü" },
    { icon: "⚖️", text: "Geleneksel (If/Else) vs ML modeli (Random Forest) karşılaştırması" },
    { icon: "🛠️", text: "Python · Streamlit · Pandas · Plotly · Scikit-learn" },
  ];
  items.forEach((it, i) => {
    const iy = 2.55 + i * 0.62;
    s.addText(it.icon + "  " + it.text, {
      x: 0.5, y: iy, w: 6.5, h: 0.5,
      fontSize: 13.5, color: C.white, fontFace: "Calibri",
      align: "left", valign: "middle",
    });
  });

  // Sağ panel — büyük stat
  card(s, 7.2, 2.3, 2.4, 2.8, C.accent2);
  s.addText("~30%", {
    x: 7.3, y: 2.55, w: 2.2, h: 0.9,
    fontSize: 42, bold: true, color: C.accent2,
    fontFace: "Calibri", align: "center",
  });
  s.addText("Enerji\nTasarrufu", {
    x: 7.3, y: 3.45, w: 2.2, h: 0.7,
    fontSize: 13, color: C.muted,
    fontFace: "Calibri", align: "center",
  });
  s.addText("ML modeli sayesinde", {
    x: 7.3, y: 4.1, w: 2.2, h: 0.4,
    fontSize: 10, color: C.accent2,
    fontFace: "Calibri", align: "center", italic: true,
  });

  // Alt çizgi
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.58, w: 10, h: 0.045,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });
}

// ─── SLIDE 2 — PROBLEM ────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.bg };

  // Başlık bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0,
    fill: { color: C.bar },
    line: { color: C.bar, width: 0 },
  });
  s.addText("⚡  Problem: Binalarda Enerji İsrafı", {
    x: 0.4, y: 0.1, w: 9.2, h: 0.8,
    fontSize: 24, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", valign: "middle",
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0.98, w: 10, h: 0.04,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });

  // Sol — problem maddeleri
  const problems = [
    { icon: "🏭", txt: "Binaların enerji tüketiminin %40'ı HVAC (ısıtma-soğutma) sistemlerinden kaynaklanır" },
    { icon: "🔒", txt: "Geleneksel sistemler sabit If/Else kurallarıyla çalışır — hiç esneklik yoktur" },
    { icon: "💸", txt: "Pik tarife saatlerinde bile tam güçle çalışarak gereksiz maliyet yaratır" },
    { icon: "🌡️", txt: "Dış sıcaklık ve bina doluluk değişimlerine dinamik tepki veremez" },
    { icon: "☁️", txt: "Sonuç: Fazla karbon emisyonu ve yüksek işletme maliyeti" },
  ];

  problems.forEach((p, i) => {
    const py = 1.15 + i * 0.78;
    card(s, 0.4, py, 5.3, 0.65, C.warn);
    s.addText(p.icon, {
      x: 0.55, y: py + 0.08, w: 0.5, h: 0.5,
      fontSize: 18, align: "center",
    });
    s.addText(p.txt, {
      x: 1.1, y: py + 0.08, w: 4.5, h: 0.5,
      fontSize: 11.5, color: C.white, fontFace: "Calibri",
      align: "left", valign: "middle",
    });
  });

  // Sağ — ihtiyaç & çözüm kutusu
  card(s, 6.1, 1.15, 3.5, 4.1, C.accent2);
  s.addText("Çözüm İhtiyacı", {
    x: 6.2, y: 1.25, w: 3.3, h: 0.45,
    fontSize: 15, bold: true, color: C.accent2,
    fontFace: "Calibri", align: "center",
  });

  const solutions = [
    "✅  Veriden öğrenen akıllı sistem",
    "✅  Tarife saatine duyarlı kontrol",
    "✅  Doluluk bazlı güç ayarı",
    "✅  Dinamik sıcaklık tepkisi",
    "✅  Gerçek zamanlı dashboard",
    "✅  CO₂ takibi & raporlama",
  ];
  solutions.forEach((sol, i) => {
    s.addText(sol, {
      x: 6.25, y: 1.75 + i * 0.55, w: 3.2, h: 0.45,
      fontSize: 12, color: C.white, fontFace: "Calibri",
      align: "left", valign: "middle",
    });
  });
}

// ─── SLIDE 3 — SİSTEM MİMARİSİ / AKIŞ DİYAGRAMI ─────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.bg };

  // Başlık bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0,
    fill: { color: C.bar },
    line: { color: C.bar, width: 0 },
  });
  s.addText("🔧  Sistem Mimarisi ve Model Akışı", {
    x: 0.4, y: 0.1, w: 9.2, h: 0.8,
    fontSize: 24, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", valign: "middle",
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0.98, w: 10, h: 0.04,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });

  // ─ AKIŞ DİYAGRAMI (sol sütun — dikey) ────────────────────────────────────
  // Kutu boyutları
  const bw = 3.2, bh = 0.52, bx = 0.35;
  const steps = [
    { y: 1.12, label: "📥  Girdi Verileri", color: C.accent,  sub: "Saat | Dış Sıcaklık | Kişi Sayısı | Tarife" },
    { y: 1.88, label: "🌳  Random Forest ML Modeli", color: "7C3AED", sub: "365 gün × 24 saat eğitim verisi" },
    { y: 2.64, label: "⚡  Optimal Klima Gücü (kW)", color: C.accent2, sub: "Tahmin çıktısı — elle kural yazılmadan" },
    { y: 3.40, label: "📊  KPI Hesaplama", color: C.warn,  sub: "Enerji % | Maliyet TL | CO₂ kg" },
    { y: 4.16, label: "🖥️  Streamlit Dashboard", color: "E11D48", sub: "İnteraktif görselleştirme & raporlama" },
  ];

  steps.forEach((st, i) => {
    // Kutu
    s.addShape(pres.shapes.RECTANGLE, {
      x: bx, y: st.y, w: bw, h: bh,
      fill: { color: C.panel },
      line: { color: st.color, width: 1.8 },
      shadow: makeShadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: bx, y: st.y, w: 0.07, h: bh,
      fill: { color: st.color },
      line: { color: st.color, width: 0 },
    });
    s.addText(st.label, {
      x: bx + 0.15, y: st.y + 0.03, w: bw - 0.2, h: 0.28,
      fontSize: 12, bold: true, color: C.white, fontFace: "Calibri",
    });
    s.addText(st.sub, {
      x: bx + 0.15, y: st.y + 0.28, w: bw - 0.2, h: 0.22,
      fontSize: 9.5, color: C.muted, fontFace: "Calibri",
    });
    // Ok (son kutudan sonra yok)
    if (i < steps.length - 1) {
      s.addShape(pres.shapes.RECTANGLE, {
        x: bx + bw / 2 - 0.025, y: st.y + bh, w: 0.05, h: 0.26,
        fill: { color: C.muted },
        line: { color: C.muted, width: 0 },
      });
      // ok ucu (üçgen simulasyonu — küçük kare eğik)
      s.addText("▼", {
        x: bx + bw / 2 - 0.18, y: st.y + bh + 0.18, w: 0.36, h: 0.2,
        fontSize: 10, color: C.muted, align: "center",
      });
    }
  });

  // ─ SAĞ: Özellik Önem Grafiği + Geleneksel Karşılaştırma ──────────────────
  // Başlık
  s.addText("Özellik Önem Skoru (Random Forest)", {
    x: 4.0, y: 1.1, w: 5.7, h: 0.4,
    fontSize: 13, bold: true, color: C.accent, fontFace: "Calibri", align: "center",
  });

  const features = [
    { name: "Dış Sıcaklık",      pct: 42, color: C.accent },
    { name: "Elektrik Tarifesi", pct: 31, color: C.accent2 },
    { name: "Kişi Sayısı",       pct: 18, color: C.warn },
    { name: "Saat",              pct:  9, color: "E11D48" },
  ];
  const barMaxW = 4.0, barH = 0.44, barX = 5.3, barStartY = 1.6;

  features.forEach((f, i) => {
    const fy = barStartY + i * (barH + 0.2);
    const fw = barMaxW * f.pct / 100;

    // İsim
    s.addText(f.name, {
      x: 4.0, y: fy + 0.05, w: 1.25, h: barH - 0.1,
      fontSize: 11, color: C.white, fontFace: "Calibri",
      align: "right", valign: "middle",
    });
    // Bar arka plan
    s.addShape(pres.shapes.RECTANGLE, {
      x: barX, y: fy, w: barMaxW, h: barH,
      fill: { color: "1E3A5F" },
      line: { color: "1E3A5F", width: 0 },
    });
    // Dolu bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: barX, y: fy, w: fw, h: barH,
      fill: { color: f.color },
      line: { color: f.color, width: 0 },
    });
    // Yüzde
    s.addText(f.pct + "%", {
      x: barX + fw + 0.08, y: fy + 0.05, w: 0.5, h: barH - 0.1,
      fontSize: 12, bold: true, color: f.color, fontFace: "Calibri",
    });
  });

  // Geleneksel vs ML not kutusu
  card(s, 4.0, 4.05, 5.6, 1.45, "7C3AED");
  s.addText("Geleneksel (If/Else)  vs  ML Modeli", {
    x: 4.1, y: 4.12, w: 5.4, h: 0.35,
    fontSize: 12, bold: true, color: "7C3AED", fontFace: "Calibri", align: "center",
  });

  const compare = [
    ["Karar mekanizması", "Elle yazılmış kurallar", "Veriden öğrenilen örüntüler"],
    ["Esneklik",          "Kural değiştirilmeli",   "Yeni veriyle yeniden eğitilir"],
    ["Tarife farkındalığı","Sadece yazılmışsa",      "Otomatik öğrenir"],
  ];
  compare.forEach((row, i) => {
    const ry = 4.52 + i * 0.27;
    s.addText("• " + row[0] + ":", {
      x: 4.1, y: ry, w: 1.6, h: 0.25,
      fontSize: 9.5, bold: true, color: C.muted, fontFace: "Calibri",
    });
    s.addText("❌  " + row[1], {
      x: 5.7, y: ry, w: 1.8, h: 0.25,
      fontSize: 9.5, color: "F87171", fontFace: "Calibri",
    });
    s.addText("✅  " + row[2], {
      x: 7.55, y: ry, w: 2.0, h: 0.25,
      fontSize: 9.5, color: "4ADE80", fontFace: "Calibri",
    });
  });
}

// ─── SLIDE 4 — SONUÇ & ÇIKTI ─────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.bg };

  // Başlık bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0,
    fill: { color: C.bar },
    line: { color: C.bar, width: 0 },
  });
  s.addText("📈  Simülasyon Sonuçları ve Sistem Çıktısı", {
    x: 0.4, y: 0.1, w: 9.2, h: 0.8,
    fontSize: 24, bold: true, color: C.white, fontFace: "Calibri",
    align: "left", valign: "middle",
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0.98, w: 10, h: 0.04,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });

  // 4 büyük KPI kartı
  const kpis = [
    { val: "~30%",   label: "Enerji\nTasarrufu",   sub: "Geleneksele göre",   color: C.accent },
    { val: "~40 ₺",  label: "Günlük Maliyet\nAzaltımı", sub: "TL cinsinden",  color: C.accent2 },
    { val: "~5 kg",  label: "CO₂\nAzaltımı",       sub: "kg / gün",           color: C.warn },
    { val: "8.760",  label: "Eğitim\nÖrneği",      sub: "365gün × 24saat",    color: "7C3AED" },
  ];
  kpis.forEach((k, i) => {
    const kx = 0.35 + i * 2.38;
    s.addShape(pres.shapes.RECTANGLE, {
      x: kx, y: 1.1, w: 2.18, h: 1.8,
      fill: { color: C.panel },
      line: { color: k.color, width: 2 },
      shadow: makeShadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: kx, y: 1.1, w: 2.18, h: 0.07,
      fill: { color: k.color },
      line: { color: k.color, width: 0 },
    });
    s.addText(k.val, {
      x: kx, y: 1.2, w: 2.18, h: 0.72,
      fontSize: 32, bold: true, color: k.color,
      fontFace: "Calibri", align: "center",
    });
    s.addText(k.label, {
      x: kx, y: 1.92, w: 2.18, h: 0.55,
      fontSize: 12, bold: true, color: C.white,
      fontFace: "Calibri", align: "center",
    });
    s.addText(k.sub, {
      x: kx, y: 2.47, w: 2.18, h: 0.35,
      fontSize: 9.5, color: C.muted,
      fontFace: "Calibri", align: "center", italic: true,
    });
  });

  // Sol alt — detay maddeleri
  const details = [
    { icon: "🎯", txt: "Pik tarife saatlerinde güç otomatik %35–65 azaltılır" },
    { icon: "🤖", txt: "Random Forest modeli elle kural yazmadan optimal kararı öğrenir" },
    { icon: "🎛️", txt: "Sidebar parametreleri (sıcaklık, doluluk, tarife) anlık güncellenebilir" },
  ];
  details.forEach((d, i) => {
    const dy = 3.05 + i * 0.72;
    card(s, 0.35, dy, 5.5, 0.6, C.accent);
    s.addText(d.icon, {
      x: 0.48, y: dy + 0.06, w: 0.45, h: 0.45,
      fontSize: 18, align: "center",
    });
    s.addText(d.txt, {
      x: 0.95, y: dy + 0.08, w: 4.75, h: 0.45,
      fontSize: 12, color: C.white, fontFace: "Calibri",
      align: "left", valign: "middle",
    });
  });

  // Sağ alt — dashboard bileşenleri
  card(s, 6.1, 3.0, 3.55, 2.4, C.accent2);
  s.addText("Dashboard Bileşenleri", {
    x: 6.2, y: 3.08, w: 3.35, h: 0.4,
    fontSize: 13, bold: true, color: C.accent2,
    fontFace: "Calibri", align: "center",
  });
  const comps = [
    "📊  4 büyük KPI kartı",
    "📈  Güç profili karşılaştırma grafiği",
    "🔵  Özellik önem çubuk grafiği",
    "🥧  Klima modu pasta grafiği",
    "📋  Renk gradyanlı detay tablosu",
  ];
  comps.forEach((c, i) => {
    s.addText(c, {
      x: 6.25, y: 3.52 + i * 0.36, w: 3.3, h: 0.32,
      fontSize: 11, color: C.white, fontFace: "Calibri",
      align: "left", valign: "middle",
    });
  });

  // Alt çizgi
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.58, w: 10, h: 0.045,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });
}

// ─── KAYDET ───────────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "bina_enerji_dijital_ikiz_sunum.pptx" })
  .then(() => console.log("✅  Sunum oluşturuldu: bina_enerji_dijital_ikiz_sunum.pptx"))
  .catch(err => console.error("❌  Hata:", err));
