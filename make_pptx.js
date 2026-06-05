const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title  = "Bina Enerji Yonetimi Dijital Ikizi ve Ajan Sistemi";

// ─── PALET ────────────────────────────────────────────────────────────────────
const C = {
  bg      : "0B1E35",
  panel   : "162C47",
  panelDk : "0D1E30",
  accent  : "42A5F5",
  teal    : "00BFA5",
  gold    : "F59E0B",
  purple  : "AB47BC",
  red     : "EF5350",
  green   : "66BB6A",
  white   : "FFFFFF",
  muted   : "8AB4D4",
  bar     : "1A3A5C",
};

const makeShadow = () => ({
  type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.25
});

function card(slide, x, y, w, h, accentColor) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: C.panel },
    line: { color: accentColor, width: 1.5 },
    shadow: makeShadow(),
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.07, h,
    fill: { color: accentColor },
    line: { color: accentColor, width: 0 },
  });
}

function titleBar(slide, text) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0,
    fill: { color: C.bar },
    line: { color: C.bar, width: 0 },
  });
  slide.addText(text, {
    x: 0.4, y: 0.1, w: 9.2, h: 0.8,
    fontSize: 23, bold: true, color: C.white,
    fontFace: "Calibri", align: "left", valign: "middle",
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0.98, w: 10, h: 0.04,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });
}

function bottomBar(slide) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.57, w: 10, h: 0.055,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });
}

// ─── SLIDE 1 — PROJE KONUSU ───────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.bg };

  s.addShape(pres.shapes.OVAL, {
    x: 7.5, y: -0.9, w: 4.2, h: 4.2,
    fill: { color: "1A4A7A", transparency: 62 },
    line: { color: "1A4A7A", width: 0 },
  });
  s.addShape(pres.shapes.OVAL, {
    x: -1.4, y: 3.4, w: 3.8, h: 3.8,
    fill: { color: "005B8E", transparency: 72 },
    line: { color: "005B8E", width: 0 },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06,
    fill: { color: C.accent }, line: { color: C.accent, width: 0 },
  });

  s.addText("Bina Enerji Yönetimi", {
    x: 0.5, y: 0.22, w: 9, h: 0.7,
    fontSize: 33, bold: true, color: C.white, fontFace: "Calibri", align: "left",
  });
  s.addText("Dijital İkiz & Ajan Sistemi", {
    x: 0.5, y: 0.88, w: 9, h: 0.58,
    fontSize: 25, color: C.accent, fontFace: "Calibri", align: "left",
  });
  s.addText("Fiziksel Termal Model  ·  Çoklu Ajan  ·  ML (Kapalı Döngü)  ·  Gerçek IoT Validasyonu", {
    x: 0.5, y: 1.44, w: 9, h: 0.36,
    fontSize: 12, color: C.muted, fontFace: "Calibri", align: "left", italic: true,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.87, w: 5.0, h: 0.03,
    fill: { color: C.accent }, line: { color: C.accent, width: 0 },
  });

  const features = [
    { color: C.accent,  icon: "🔬", text: "Fiziksel ısı dengesi denklemli gerçek Dijital İkiz simülasyonu" },
    { color: C.purple,  icon: "🤝", text: "3 otonom ajan + koordinatör ile çoklu ajan karar sistemi" },
    { color: C.teal,    icon: "🌲", text: "T_iç özellikli + kapalı döngü Random Forest ML modeli" },
    { color: C.gold,    icon: "📡", text: "UCI veri setiyle gerçek IoT sensör verisi validasyonu" },
  ];
  features.forEach((f, i) => {
    const fy = 2.05 + i * 0.72;
    card(s, 0.5, fy, 5.7, 0.60, f.color);
    s.addText(f.icon, { x: 0.62, y: fy + 0.08, w: 0.42, h: 0.42, fontSize: 18, align: "center" });
    s.addText(f.text, {
      x: 1.12, y: fy + 0.09, w: 4.95, h: 0.42,
      fontSize: 12, color: C.white, fontFace: "Calibri", align: "left", valign: "middle",
    });
  });

  const kpis = [
    { val: "~30%",    lbl: "ML Enerji\nTasarrufu",   color: C.accent },
    { val: "~37%",    lbl: "Ajan Enerji\nTasarrufu",  color: C.purple },
    { val: "R²≈0.90", lbl: "IoT Doğruluk\nSkoru",    color: C.teal },
  ];
  kpis.forEach((k, i) => {
    const ky = 2.05 + i * 1.08;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.65, y: ky, w: 3.0, h: 0.96,
      fill: { color: C.panelDk }, line: { color: k.color, width: 2 }, shadow: makeShadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.65, y: ky, w: 3.0, h: 0.055,
      fill: { color: k.color }, line: { color: k.color, width: 0 },
    });
    s.addText(k.val, {
      x: 6.65, y: ky + 0.07, w: 3.0, h: 0.48,
      fontSize: 28, bold: true, color: k.color, fontFace: "Calibri", align: "center",
    });
    s.addText(k.lbl, {
      x: 6.65, y: ky + 0.54, w: 3.0, h: 0.40,
      fontSize: 11, color: C.muted, fontFace: "Calibri", align: "center",
    });
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.22, w: 9.0, h: 0.30,
    fill: { color: C.panelDk }, line: { color: C.bar, width: 1 },
  });
  s.addText("Python  ·  Streamlit  ·  Scikit-learn  ·  Plotly  ·  UCI IoT Data", {
    x: 0.5, y: 5.22, w: 9.0, h: 0.30,
    fontSize: 11, color: C.muted, fontFace: "Calibri", align: "center", valign: "middle",
  });
  bottomBar(s);
}

// ─── SLIDE 2 — PROBLEM ────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  titleBar(s, "⚡  Problem: Binalarda Enerji İsrafı & Kontrol Eksikliği");

  const problems = [
    { icon: "⚡", txt: "Bina enerjisinin %40'ı HVAC sistemlerinden — en büyük israf kaynağı" },
    { icon: "🔒", txt: "Geleneksel sistemler sabit If/Else ile çalışır, esneklik sıfır" },
    { icon: "💸", txt: "Pik tarife saatlerinde farkındalıksız tam güç → gereksiz maliyet" },
    { icon: "🌡", txt: "Dış sıcaklık & doluluk değişimine dinamik tepki verilemiyor" },
    { icon: "☁",  txt: "Yüksek karbon emisyonu, işletme maliyeti ve konfor kaybı" },
  ];
  problems.forEach((p, i) => {
    const py = 1.12 + i * 0.84;
    card(s, 0.38, py, 5.35, 0.72, C.gold);
    s.addText(p.icon, { x: 0.50, y: py + 0.12, w: 0.44, h: 0.44, fontSize: 18, align: "center" });
    s.addText(p.txt, {
      x: 1.02, y: py + 0.12, w: 4.58, h: 0.48,
      fontSize: 11.5, color: C.white, fontFace: "Calibri", align: "left", valign: "middle",
    });
  });

  card(s, 6.0, 1.12, 3.62, 4.20, C.teal);
  s.addText("Çözüm: 3 Katmanlı Akıllı Sistem", {
    x: 6.1, y: 1.20, w: 3.42, h: 0.42,
    fontSize: 13.5, bold: true, color: C.teal, fontFace: "Calibri", align: "center",
  });

  const layers = [
    { num: "1", color: C.teal,   title: "Dijital İkiz",  desc: "Fiziksel bina modelini\nsimüle eder" },
    { num: "2", color: C.purple, title: "Ajan Sistemi",  desc: "Gerçek zamanlı\nkararlar alır" },
    { num: "3", color: C.accent, title: "ML + IoT",      desc: "Veriden öğrenir,\ngerçekle doğrular" },
  ];
  layers.forEach((l, i) => {
    const ly = 1.72 + i * 1.14;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.18, y: ly, w: 3.26, h: 0.96,
      fill: { color: C.panelDk }, line: { color: l.color, width: 1.5 },
    });
    s.addShape(pres.shapes.OVAL, {
      x: 6.26, y: ly + 0.20, w: 0.50, h: 0.50,
      fill: { color: l.color }, line: { color: l.color, width: 0 },
    });
    s.addText(l.num, {
      x: 6.26, y: ly + 0.20, w: 0.50, h: 0.50,
      fontSize: 16, bold: true, color: C.white, fontFace: "Calibri", align: "center", valign: "middle",
    });
    s.addText(l.title, {
      x: 6.84, y: ly + 0.08, w: 2.50, h: 0.30,
      fontSize: 13, bold: true, color: l.color, fontFace: "Calibri",
    });
    s.addText(l.desc, {
      x: 6.84, y: ly + 0.36, w: 2.50, h: 0.50,
      fontSize: 10.5, color: C.muted, fontFace: "Calibri",
    });
    if (i < 2) s.addText("▼", { x: 7.50, y: ly + 0.96, w: 0.6, h: 0.18, fontSize: 10, color: C.muted, align: "center" });
  });
}

// ─── SLIDE 3 — SİSTEM MİMARİSİ (GÜNCELLENDİ) ────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  titleBar(s, "🔧  Sistem Mimarisi — Kapalı Döngü Düzeltmeleri Dahil");

  const colW = 3.08;
  const cols = [
    { x: 0.22, title: "🌲 ML Katmanı (Kapalı Döngü)", color: C.accent },
    { x: 3.46, title: "🤝 Ajan Katmanı",              color: C.purple },
    { x: 6.70, title: "🏠 Dijital İkiz & IoT",        color: C.teal   },
  ];

  cols.forEach(col => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: col.x, y: 1.08, w: colW, h: 0.44,
      fill: { color: col.color }, line: { color: col.color, width: 0 },
    });
    s.addText(col.title, {
      x: col.x, y: 1.08, w: colW, h: 0.44,
      fontSize: 12.5, bold: true, color: C.white, fontFace: "Calibri", align: "center", valign: "middle",
    });
  });

  // ── ML Sütunu ─────────────────────────────────────────────────────────────
  // Özellikler kutusu
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.22, y: 1.60, w: colW, h: 0.64,
    fill: { color: C.panelDk }, line: { color: C.accent, width: 1.5 },
  });
  s.addText("Girdi Özellikler (5 adet):", {
    x: 0.30, y: 1.62, w: colW - 0.12, h: 0.22,
    fontSize: 10, bold: true, color: C.accent, fontFace: "Calibri",
  });
  s.addText("Saat · T_dış · T_iç · Kişi · Fiyat", {
    x: 0.30, y: 1.82, w: colW - 0.12, h: 0.36,
    fontSize: 10.5, color: C.white, fontFace: "Consolas", align: "center",
  });
  // Düzeltme notu
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.22, y: 2.30, w: colW, h: 0.50,
    fill: { color: "1A3515" }, line: { color: C.green, width: 1.2 },
  });
  s.addText("✅  Düzeltme: T_iç özellik olarak\neklendi — artık konfor durumu biliniyor", {
    x: 0.28, y: 2.32, w: colW - 0.10, h: 0.46,
    fontSize: 9.5, color: C.green, fontFace: "Calibri", align: "left",
  });

  s.addText("▼", { x: 0.22 + colW/2 - 0.22, y: 2.83, w: 0.44, h: 0.20, fontSize: 10, color: C.muted, align: "center" });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.22, y: 3.05, w: colW, h: 0.62,
    fill: { color: C.panel }, line: { color: C.accent, width: 1.5 },
  });
  s.addText("Random Forest Eğitimi\n(hedef T_iç konforuna göre)", {
    x: 0.28, y: 3.07, w: colW - 0.10, h: 0.58,
    fontSize: 11, color: C.white, fontFace: "Calibri", align: "center", valign: "middle",
  });

  s.addText("▼", { x: 0.22 + colW/2 - 0.22, y: 3.70, w: 0.44, h: 0.20, fontSize: 10, color: C.muted, align: "center" });

  // Kapalı döngü tahmin
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.22, y: 3.92, w: colW, h: 0.50,
    fill: { color: "1A3515" }, line: { color: C.green, width: 1.2 },
  });
  s.addText("✅  Kapalı Döngü Tahmin:\nt→ predict(T_iç) → T_iç_yeni → t+1", {
    x: 0.28, y: 3.94, w: colW - 0.10, h: 0.46,
    fontSize: 9.5, color: C.green, fontFace: "Consolas", align: "left",
  });

  // Özellik önemleri
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.22, y: 4.50, w: colW, h: 0.70,
    fill: { color: C.panelDk }, line: { color: C.accent, width: 1 },
  });
  s.addText("T_iç ~35%  ·  T_dış ~28%\nTarife ~20%  ·  Kişi ~12%  ·  Saat ~5%", {
    x: 0.28, y: 4.52, w: colW - 0.10, h: 0.65,
    fontSize: 9.5, color: C.muted, fontFace: "Calibri", align: "center", valign: "middle",
  });

  // ── Ajan Sütunu ────────────────────────────────────────────────────────────
  const ajanItems = [
    { icon: "🔵", name: "Konfor Ajanı",  desc: "T_iç > 26°C → güç artır\n(Dijital İkiz'den T_iç alır)", color: C.accent },
    { icon: "🟢", name: "Maliyet Ajanı", desc: "Pik tarife → güç düşür",   color: C.green  },
    { icon: "🟠", name: "Sürd. Ajanı",   desc: "Boş bina → standby",       color: C.gold   },
  ];
  ajanItems.forEach((a, i) => {
    const ay = 1.62 + i * 0.90;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 3.46, y: ay, w: colW, h: 0.76,
      fill: { color: C.panel }, line: { color: a.color, width: 1.5 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 3.46, y: ay, w: 0.07, h: 0.76,
      fill: { color: a.color }, line: { color: a.color, width: 0 },
    });
    s.addText(a.icon + "  " + a.name, {
      x: 3.58, y: ay + 0.06, w: colW - 0.18, h: 0.28,
      fontSize: 11.5, bold: true, color: C.white, fontFace: "Calibri",
    });
    s.addText(a.desc, {
      x: 3.58, y: ay + 0.34, w: colW - 0.18, h: 0.36,
      fontSize: 9.5, color: C.muted, fontFace: "Calibri",
    });
    if (i < 2) s.addText("▼", { x: 3.46 + colW/2 - 0.22, y: ay + 0.78, w: 0.44, h: 0.14, fontSize: 9, color: C.muted, align: "center" });
  });

  s.addShape(pres.shapes.RECTANGLE, {
    x: 3.46, y: 4.36, w: colW, h: 0.86,
    fill: { color: C.panelDk }, line: { color: C.purple, width: 2 }, shadow: makeShadow(),
  });
  s.addText("⚖️  Koordinatör Ajan", {
    x: 3.52, y: 4.38, w: colW - 0.10, h: 0.28,
    fontSize: 12, bold: true, color: C.purple, fontFace: "Calibri", align: "center",
  });
  s.addText("P = w₁·Pk + w₂·Pm + w₃·Ps", {
    x: 3.52, y: 4.66, w: colW - 0.10, h: 0.48,
    fontSize: 10, color: C.white, fontFace: "Consolas", align: "center", italic: true,
  });

  // ── Dijital İkiz + IoT Sütunu ──────────────────────────────────────────────
  const dtItems = [
    { txt: "Gerçek IoT Verisi (UCI)\nBelçika evi · 4,5 ay · 10 dk'lık", color: C.gold   },
    { txt: "Isı Dengesi Denklemi\nT_iç[t+1]=T_iç[t]+α(T_dış−T_iç)+β·N−γ·P", color: C.teal   },
    { txt: "İç Sıcaklık Simülasyonu\n(Kapalı döngü — tüm sistemler)", color: C.teal   },
    { txt: "Validasyon: MAE · RMSE · R²\n⚠ P_klima=0 sınırlılığı belgelendi", color: C.green  },
  ];
  dtItems.forEach((st, i) => {
    const dy = 1.60 + i * 0.94;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.70, y: dy, w: colW, h: 0.76,
      fill: { color: C.panel }, line: { color: st.color, width: 1.5 },
    });
    s.addText(st.txt, {
      x: 6.76, y: dy + 0.06, w: colW - 0.12, h: 0.64,
      fontSize: i === 1 ? 9.0 : 10.5,
      color: C.white,
      fontFace: i === 1 ? "Consolas" : "Calibri",
      align: "center", valign: "middle",
    });
    if (i < 3) s.addText("▼", { x: 6.70 + colW/2 - 0.22, y: dy + 0.78, w: 0.44, h: 0.14, fontSize: 9, color: C.muted, align: "center" });
  });

  // Alt dashboard bar
  [0.22 + colW/2, 3.46 + colW/2, 6.70 + colW/2].forEach(ax => {
    s.addText("▼", { x: ax - 0.22, y: 5.12, w: 0.44, h: 0.18, fontSize: 10, color: C.muted, align: "center" });
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 1.8, y: 5.28, w: 6.4, h: 0.28,
    fill: { color: C.accent }, line: { color: C.accent, width: 0 },
  });
  s.addText("Streamlit Dashboard — 6 Sekme", {
    x: 1.8, y: 5.28, w: 6.4, h: 0.28,
    fontSize: 12, bold: true, color: C.white, fontFace: "Calibri", align: "center", valign: "middle",
  });
}

// ─── SLIDE 4 — SONUÇ & ÇIKTI (GÜNCELLENDİ) ───────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  titleBar(s, "📈  Sonuçlar, Düzeltmeler & Sistem Çıktısı");

  // 4 KPI kutusu
  const kpis = [
    { val: "~30%",    lbl1: "ML Enerji",      lbl2: "Tasarrufu",       color: C.accent },
    { val: "~37%",    lbl1: "Ajan Enerji",     lbl2: "Tasarrufu",       color: C.purple },
    { val: "R²≈0.90", lbl1: "IoT Validasyon", lbl2: "Doğruluk Skoru",  color: C.teal   },
    { val: "8.760",   lbl1: "ML Eğitim",       lbl2: "Örneği",          color: C.gold   },
  ];
  kpis.forEach((k, i) => {
    const kx = 0.28 + i * 2.38;
    s.addShape(pres.shapes.RECTANGLE, {
      x: kx, y: 1.10, w: 2.18, h: 1.70,
      fill: { color: C.panel }, line: { color: k.color, width: 2 }, shadow: makeShadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: kx, y: 1.10, w: 2.18, h: 0.06,
      fill: { color: k.color }, line: { color: k.color, width: 0 },
    });
    s.addText(k.val, {
      x: kx, y: 1.18, w: 2.18, h: 0.72,
      fontSize: i === 2 ? 22 : 30, bold: true, color: k.color, fontFace: "Calibri", align: "center",
    });
    s.addText(k.lbl1 + "\n" + k.lbl2, {
      x: kx, y: 1.88, w: 2.18, h: 0.58,
      fontSize: 11, color: C.white, fontFace: "Calibri", align: "center",
    });
  });

  // Sol alt — Uygulanan Düzeltmeler
  card(s, 0.28, 2.96, 5.00, 2.50, C.green);
  s.addText("✅  Uygulanan Teknik Düzeltmeler", {
    x: 0.42, y: 3.02, w: 4.76, h: 0.38,
    fontSize: 13, bold: true, color: C.green, fontFace: "Calibri",
  });
  const fixes = [
    "1. ML Kapalı Döngü: T_iç her saatte modele besleniyor",
    "2. T_iç Özelliği: fiyat değil konfor durumu birincil kriter",
    "3. Geleneksel Kapalı Döngü: T_dış → T_iç eşiğine geçildi",
    "4. UCI Sınırlılık: P_klima=0 belgeli, R² yorumu dürüst",
  ];
  fixes.forEach((f, i) => {
    s.addText(f, {
      x: 0.42, y: 3.45 + i * 0.47, w: 4.76, h: 0.40,
      fontSize: 11.5, color: C.white, fontFace: "Calibri", align: "left", valign: "middle",
    });
  });

  // Sağ alt — Akademik katkılar
  card(s, 5.50, 2.96, 4.22, 2.50, C.purple);
  s.addText("Akademik Katkılar", {
    x: 5.64, y: 3.02, w: 3.98, h: 0.38,
    fontSize: 13, bold: true, color: C.purple, fontFace: "Calibri",
  });
  const akademik = [
    "• Fiziksel Dijital İkiz: ısı dengesi kapalı döngü",
    "• Çoklu Ajan: ağırlıklı koordinasyon mekanizması",
    "• ML: T_iç geri beslemeli konfor odaklı öğrenme",
    "• Gerçek IoT validasyonu + belgelenmiş sınırlılıklar",
    "  (MAE / RMSE / R² / P_klima=0 şeffaflığı)",
  ];
  akademik.forEach((a, i) => {
    s.addText(a, {
      x: 5.64, y: 3.45 + i * 0.44, w: 3.98, h: 0.40,
      fontSize: i === 4 ? 9.5 : 11, color: i === 4 ? C.muted : C.white,
      fontFace: "Calibri", align: "left", valign: "middle",
    });
  });

  // Alt teknoloji bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.35, w: 10, h: 0.22,
    fill: { color: C.panelDk }, line: { color: C.panelDk, width: 0 },
  });
  s.addText("Python  ·  Streamlit  ·  Scikit-learn  ·  Plotly  ·  UCI ML Repository", {
    x: 0, y: 5.35, w: 10, h: 0.22,
    fontSize: 10, color: C.muted, fontFace: "Calibri", align: "center", valign: "middle",
  });
  bottomBar(s);
}

// ─── KAYDET ───────────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "bina_enerji_dijital_ikiz_sunum.pptx" })
  .then(() => console.log("OK bina_enerji_dijital_ikiz_sunum.pptx"))
  .catch(err => { console.error("HATA:", err); process.exit(1); });
