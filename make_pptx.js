const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
pres.title  = "Bina Enerji Yonetimi Dijital Ikizi ve Ajan Sistemi";

// ─── PALET ────────────────────────────────────────────────────────────────────
const C = {
  bg      : "0B1E35",
  panel   : "162C47",
  panelDk : "0D1E30",
  accent  : "42A5F5",   // mavi
  teal    : "00BFA5",   // teal
  gold    : "F59E0B",   // sarı
  purple  : "AB47BC",   // mor
  red     : "EF5350",
  green   : "66BB6A",
  white   : "FFFFFF",
  muted   : "8AB4D4",
  bar     : "1A3A5C",
};

const makeShadow = () => ({
  type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.25
});

// Sol kenar şeritli kart
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

// Başlık bar fonksiyonu
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

// Alt çizgi
function bottomBar(slide, color) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.57, w: 10, h: 0.055,
    fill: { color: color || C.accent },
    line: { color: color || C.accent, width: 0 },
  });
}

// ─── SLIDE 1 — PROJE KONUSU ───────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.bg };

  // Dekoratif daireler
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

  // Üst accent çizgisi
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.06,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });

  // Başlık
  s.addText("Bina Enerji Yönetimi", {
    x: 0.5, y: 0.22, w: 9, h: 0.7,
    fontSize: 33, bold: true, color: C.white,
    fontFace: "Calibri", align: "left",
  });
  s.addText("Dijital İkiz & Ajan Sistemi", {
    x: 0.5, y: 0.88, w: 9, h: 0.58,
    fontSize: 25, bold: false, color: C.accent,
    fontFace: "Calibri", align: "left",
  });
  s.addText("Fiziksel Termal Model  ·  Çoklu Ajan  ·  ML  ·  Gerçek IoT Validasyonu", {
    x: 0.5, y: 1.44, w: 9, h: 0.36,
    fontSize: 12.5, color: C.muted, fontFace: "Calibri", align: "left", italic: true,
  });

  // Ayırıcı
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.87, w: 5.0, h: 0.03,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });

  // Sol — 4 özellik kartı
  const features = [
    { icon: "🔬", color: C.accent,  text: "Fiziksel ısı dengesi denklemli gerçek Dijital İkiz simülasyonu" },
    { icon: "🤝", color: C.purple,  text: "3 otonom ajan + koordinatör ile çoklu ajan karar sistemi" },
    { icon: "🌲", color: C.teal,    text: "8.760 örnekle eğitilmiş Random Forest ML modeli" },
    { icon: "📡", color: C.gold,    text: "UCI veri setiyle gerçek IoT sensör verisi validasyonu" },
  ];
  features.forEach((f, i) => {
    const fy = 2.05 + i * 0.72;
    card(s, 0.5, fy, 5.7, 0.60, f.color);
    s.addText(f.icon, { x: 0.62, y: fy + 0.08, w: 0.42, h: 0.42, fontSize: 18, align: "center" });
    s.addText(f.text, {
      x: 1.12, y: fy + 0.09, w: 4.95, h: 0.42,
      fontSize: 12, color: C.white, fontFace: "Calibri",
      align: "left", valign: "middle",
    });
  });

  // Sağ — 3 KPI kutusu
  const kpis = [
    { val: "~30%",    lbl: "ML Enerji\nTasarrufu",  color: C.accent },
    { val: "~37%",    lbl: "Ajan Enerji\nTasarrufu", color: C.purple },
    { val: "R²≈0.90", lbl: "IoT Doğruluk\nSkoru",   color: C.teal },
  ];
  kpis.forEach((k, i) => {
    const ky = 2.05 + i * 1.08;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.65, y: ky, w: 3.0, h: 0.96,
      fill: { color: C.panelDk },
      line: { color: k.color, width: 2 },
      shadow: makeShadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.65, y: ky, w: 3.0, h: 0.055,
      fill: { color: k.color },
      line: { color: k.color, width: 0 },
    });
    s.addText(k.val, {
      x: 6.65, y: ky + 0.07, w: 3.0, h: 0.48,
      fontSize: 28, bold: true, color: k.color,
      fontFace: "Calibri", align: "center",
    });
    s.addText(k.lbl, {
      x: 6.65, y: ky + 0.54, w: 3.0, h: 0.40,
      fontSize: 11, color: C.muted, fontFace: "Calibri", align: "center",
    });
  });

  // Alt tech badge bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.22, w: 9.0, h: 0.30,
    fill: { color: C.panelDk },
    line: { color: C.bar, width: 1 },
  });
  s.addText("Python  ·  Streamlit  ·  Scikit-learn  ·  Plotly  ·  UCI IoT Data", {
    x: 0.5, y: 5.22, w: 9.0, h: 0.30,
    fontSize: 11, color: C.muted, fontFace: "Calibri", align: "center", valign: "middle",
  });
  bottomBar(s, C.accent);
}

// ─── SLIDE 2 — PROBLEM ────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  titleBar(s, "⚡  Problem: Binalarda Enerji İsrafı & Kontrol Eksikliği");

  // Sol — 5 problem kartı
  const problems = [
    { icon: "⚡", txt: "Bina enerjisinin %40'ı HVAC sistemlerinden — en büyük israf kaynağı" },
    { icon: "🔒", txt: "Geleneksel sistemler sabit If/Else ile çalışır, esneklik sıfır" },
    { icon: "💸", txt: "Pik tarife saatlerinde farkındalıksız tam güç → gereksiz maliyet" },
    { icon: "🌡", txt: "Dış sıcaklık & doluluk değişimine dinamik tepki verilemiyor" },
    { icon: "☁", txt: "Yüksek karbon emisyonu, işletme maliyeti ve konfor kaybı" },
  ];
  problems.forEach((p, i) => {
    const py = 1.12 + i * 0.84;
    card(s, 0.38, py, 5.35, 0.72, C.gold);
    s.addText(p.icon, { x: 0.50, y: py + 0.12, w: 0.44, h: 0.44, fontSize: 18, align: "center" });
    s.addText(p.txt, {
      x: 1.02, y: py + 0.12, w: 4.58, h: 0.48,
      fontSize: 11.5, color: C.white, fontFace: "Calibri",
      align: "left", valign: "middle",
    });
  });

  // Sağ — çözüm kutusu
  card(s, 6.0, 1.12, 3.62, 4.20, C.teal);
  s.addText("Çözüm: 3 Katmanlı Akıllı Sistem", {
    x: 6.1, y: 1.20, w: 3.42, h: 0.42,
    fontSize: 13.5, bold: true, color: C.teal,
    fontFace: "Calibri", align: "center",
  });

  const layers = [
    { num: "1", color: C.teal,   title: "Dijital İkiz",    desc: "Fiziksel bina modelini\nsimüle eder" },
    { num: "2", color: C.purple, title: "Ajan Sistemi",    desc: "Gerçek zamanlı\nkararlar alır" },
    { num: "3", color: C.accent, title: "ML + IoT",        desc: "Veriden öğrenir,\ngerçekle doğrular" },
  ];
  layers.forEach((l, i) => {
    const ly = 1.72 + i * 1.14;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.18, y: ly, w: 3.26, h: 0.96,
      fill: { color: C.panelDk },
      line: { color: l.color, width: 1.5 },
    });
    // Numara dairesi
    s.addShape(pres.shapes.OVAL, {
      x: 6.26, y: ly + 0.20, w: 0.50, h: 0.50,
      fill: { color: l.color },
      line: { color: l.color, width: 0 },
    });
    s.addText(l.num, {
      x: 6.26, y: ly + 0.20, w: 0.50, h: 0.50,
      fontSize: 16, bold: true, color: C.white,
      fontFace: "Calibri", align: "center", valign: "middle",
    });
    s.addText(l.title, {
      x: 6.84, y: ly + 0.08, w: 2.50, h: 0.30,
      fontSize: 13, bold: true, color: l.color, fontFace: "Calibri",
    });
    s.addText(l.desc, {
      x: 6.84, y: ly + 0.36, w: 2.50, h: 0.50,
      fontSize: 10.5, color: C.muted, fontFace: "Calibri",
    });
    // Ok (son hariç)
    if (i < 2) {
      s.addText("▼", {
        x: 7.50, y: ly + 0.96, w: 0.6, h: 0.18,
        fontSize: 10, color: C.muted, align: "center",
      });
    }
  });
}

// ─── SLIDE 3 — SİSTEM MİMARİSİ ────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  titleBar(s, "🔧  Sistem Mimarisi — 3 Katmanlı Yapı");

  // 3 sütun başlıkları
  const cols = [
    { x: 0.25, title: "🌲 ML Katmanı",      color: C.accent },
    { x: 3.55, title: "🤝 Ajan Katmanı",    color: C.purple },
    { x: 6.85, title: "🏠 Dijital İkiz",    color: C.teal   },
  ];
  const colW = 3.10;

  cols.forEach(col => {
    // Sütun başlık kutusu
    s.addShape(pres.shapes.RECTANGLE, {
      x: col.x, y: 1.08, w: colW, h: 0.44,
      fill: { color: col.color },
      line: { color: col.color, width: 0 },
    });
    s.addText(col.title, {
      x: col.x, y: 1.08, w: colW, h: 0.44,
      fontSize: 13.5, bold: true, color: C.white,
      fontFace: "Calibri", align: "center", valign: "middle",
    });
  });

  // ── ML Sütunu ──────────────────────────────────────────────────────────────
  const mlSteps = [
    { txt: "365 Gün × 24 Saat\nSentetik Veri" },
    { txt: "Random Forest\nEğitimi" },
    { txt: "Optimal Güç\nTahmini (kW)" },
  ];
  mlSteps.forEach((st, i) => {
    const sy = 1.62 + i * 1.02;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.25, y: sy, w: colW, h: 0.72,
      fill: { color: C.panel },
      line: { color: C.accent, width: 1.5 },
    });
    s.addText(st.txt, {
      x: 0.30, y: sy + 0.06, w: colW - 0.1, h: 0.60,
      fontSize: 11.5, color: C.white, fontFace: "Calibri",
      align: "center", valign: "middle",
    });
    if (i < 2) s.addText("▼", { x: 0.25 + colW / 2 - 0.22, y: sy + 0.75, w: 0.44, h: 0.22, fontSize: 10, color: C.muted, align: "center" });
  });
  // Özellik önemleri
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.25, y: 4.70, w: colW, h: 0.70,
    fill: { color: C.panelDk },
    line: { color: C.accent, width: 1 },
  });
  s.addText("Sıcaklık 42%  ·  Tarife 31%\nKişi 18%  ·  Saat 9%", {
    x: 0.30, y: 4.72, w: colW - 0.10, h: 0.65,
    fontSize: 10, color: C.muted, fontFace: "Calibri", align: "center", valign: "middle",
  });

  // ── Ajan Sütunu ───────────────────────────────────────────────────────────
  const ajanItems = [
    { icon: "🔵", name: "Konfor Ajanı",   desc: "T_iç > 26°C → güç artır",   color: C.accent },
    { icon: "🟢", name: "Maliyet Ajanı",  desc: "Pik tarife → güç düşür",    color: C.green  },
    { icon: "🟠", name: "Sürd. Ajanı",    desc: "Boş bina → standby",        color: C.gold   },
  ];
  ajanItems.forEach((a, i) => {
    const ay = 1.62 + i * 0.82;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 3.55, y: ay, w: colW, h: 0.68,
      fill: { color: C.panel },
      line: { color: a.color, width: 1.5 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 3.55, y: ay, w: 0.07, h: 0.68,
      fill: { color: a.color },
      line: { color: a.color, width: 0 },
    });
    s.addText(a.icon + "  " + a.name, {
      x: 3.68, y: ay + 0.04, w: colW - 0.20, h: 0.28,
      fontSize: 11.5, bold: true, color: C.white, fontFace: "Calibri",
    });
    s.addText(a.desc, {
      x: 3.68, y: ay + 0.32, w: colW - 0.20, h: 0.28,
      fontSize: 10.5, color: C.muted, fontFace: "Calibri",
    });
    if (i < 2) s.addText("▼", { x: 3.55 + colW / 2 - 0.22, y: ay + 0.70, w: 0.44, h: 0.20, fontSize: 9, color: C.muted, align: "center" });
  });
  // Koordinatör kutusu
  s.addShape(pres.shapes.RECTANGLE, {
    x: 3.55, y: 4.12, w: colW, h: 0.82,
    fill: { color: C.panelDk },
    line: { color: C.purple, width: 2 },
    shadow: makeShadow(),
  });
  s.addText("⚖️  Koordinatör Ajan", {
    x: 3.60, y: 4.14, w: colW - 0.10, h: 0.28,
    fontSize: 12, bold: true, color: C.purple, fontFace: "Calibri", align: "center",
  });
  s.addText("P = w₁·Pkonfor + w₂·Pmaliyet + w₃·Psürd", {
    x: 3.60, y: 4.42, w: colW - 0.10, h: 0.44,
    fontSize: 10, color: C.white, fontFace: "Calibri", align: "center", italic: true,
  });

  // ── Dijital İkiz Sütunu ───────────────────────────────────────────────────
  const dtSteps = [
    { txt: "Gerçek IoT Verisi\n(UCI Dataset)", color: C.gold },
    { txt: "Isı Dengesi Denklemi\nT_iç[t+1] = T_iç[t] + α(T_dış−T_iç) + β·N − γ·P", color: C.teal },
    { txt: "İç Sıcaklık\nSimülasyonu", color: C.teal },
    { txt: "Validasyon\nMAE  ·  RMSE  ·  R²", color: C.green },
  ];
  dtSteps.forEach((st, i) => {
    const dy = 1.62 + i * 0.88;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.85, y: dy, w: colW, h: 0.72,
      fill: { color: C.panel },
      line: { color: st.color, width: 1.5 },
    });
    s.addText(st.txt, {
      x: 6.90, y: dy + 0.05, w: colW - 0.10, h: 0.62,
      fontSize: i === 1 ? 9.5 : 11.5, color: C.white,
      fontFace: i === 1 ? "Consolas" : "Calibri",
      align: "center", valign: "middle",
    });
    if (i < 3) s.addText("▼", { x: 6.85 + colW / 2 - 0.22, y: dy + 0.74, w: 0.44, h: 0.18, fontSize: 9, color: C.muted, align: "center" });
  });

  // Alt birleşme okları ve dashboard kutusu
  const arrowY = 5.10;
  [0.25 + colW / 2, 3.55 + colW / 2, 6.85 + colW / 2].forEach(ax => {
    s.addText("▼", { x: ax - 0.22, y: arrowY, w: 0.44, h: 0.20, fontSize: 10, color: C.muted, align: "center" });
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 1.8, y: 5.26, w: 6.4, h: 0.30,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });
  s.addText("Streamlit Dashboard — 6 Sekme", {
    x: 1.8, y: 5.26, w: 6.4, h: 0.30,
    fontSize: 12, bold: true, color: C.white,
    fontFace: "Calibri", align: "center", valign: "middle",
  });
}

// ─── SLIDE 4 — SONUÇ & ÇIKTI ─────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  titleBar(s, "📈  Sonuçlar & Sistem Çıktısı");

  // 4 KPI kutusu
  const kpis = [
    { val: "~30%",    lbl1: "ML Enerji",     lbl2: "Tasarrufu",          color: C.accent },
    { val: "~37%",    lbl1: "Ajan Enerji",   lbl2: "Tasarrufu",          color: C.purple },
    { val: "R²≈0.90", lbl1: "IoT Validasyon",lbl2: "Doğruluk Skoru",    color: C.teal   },
    { val: "8.760",   lbl1: "ML Eğitim",     lbl2: "Örneği",             color: C.gold   },
  ];
  kpis.forEach((k, i) => {
    const kx = 0.28 + i * 2.38;
    s.addShape(pres.shapes.RECTANGLE, {
      x: kx, y: 1.10, w: 2.18, h: 1.70,
      fill: { color: C.panel },
      line: { color: k.color, width: 2 },
      shadow: makeShadow(),
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: kx, y: 1.10, w: 2.18, h: 0.06,
      fill: { color: k.color },
      line: { color: k.color, width: 0 },
    });
    s.addText(k.val, {
      x: kx, y: 1.18, w: 2.18, h: 0.72,
      fontSize: i === 2 ? 22 : 30, bold: true, color: k.color,
      fontFace: "Calibri", align: "center",
    });
    s.addText(k.lbl1 + "\n" + k.lbl2, {
      x: kx, y: 1.88, w: 2.18, h: 0.58,
      fontSize: 11, bold: false, color: C.white,
      fontFace: "Calibri", align: "center",
    });
  });

  // Sol alt — Dashboard özellikleri
  card(s, 0.28, 2.96, 5.30, 2.50, C.accent);
  s.addText("Dashboard Özellikleri", {
    x: 0.42, y: 3.02, w: 5.0, h: 0.36,
    fontSize: 13, bold: true, color: C.accent, fontFace: "Calibri",
  });
  const dash = [
    "⚡  3 sistemin güç profili karşılaştırması",
    "🏠  Dijital İkiz iç sıcaklık dinamiği + konfor bandı",
    "🤝  Ajan oy tablosu + koordinatör kararı",
    "🤖  Random Forest özellik önem analizi",
    "📡  UCI IoT verisiyle gerçek zamanlı validasyon",
    "📋  Tüm sistemlerin saatlik detay tablosu",
  ];
  dash.forEach((d, i) => {
    s.addText(d, {
      x: 0.42, y: 3.42 + i * 0.34, w: 5.0, h: 0.30,
      fontSize: 11, color: C.white, fontFace: "Calibri",
      align: "left", valign: "middle",
    });
  });

  // Sağ alt — Akademik katkılar
  card(s, 5.80, 2.96, 3.92, 2.50, C.purple);
  s.addText("Akademik Katkılar", {
    x: 5.94, y: 3.02, w: 3.70, h: 0.36,
    fontSize: 13, bold: true, color: C.purple, fontFace: "Calibri",
  });
  const akademik = [
    "• Fiziksel Dijital İkiz: ısı dengesi\n  kapalı döngü kontrolü",
    "• Çoklu Ajan: ağırlıklı koordinasyon\n  mekanizması",
    "• ML ile kural-öğrenme karşılaştırması",
    "• Gerçek IoT verisiyle model\n  validasyonu (MAE/RMSE/R²)",
  ];
  akademik.forEach((a, i) => {
    s.addText(a, {
      x: 5.94, y: 3.42 + i * 0.55, w: 3.70, h: 0.50,
      fontSize: 10.5, color: C.white, fontFace: "Calibri",
      align: "left", valign: "top",
    });
  });

  // Alt teknoloji bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.57, w: 10, h: 0.055,
    fill: { color: C.accent },
    line: { color: C.accent, width: 0 },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.35, w: 10, h: 0.22,
    fill: { color: C.panelDk },
    line: { color: C.panelDk, width: 0 },
  });
  s.addText("Teknoloji: Python  ·  Streamlit  ·  Scikit-learn  ·  Plotly  ·  UCI ML Repository", {
    x: 0, y: 5.35, w: 10, h: 0.22,
    fontSize: 10, color: C.muted, fontFace: "Calibri", align: "center", valign: "middle",
  });
}

// ─── KAYDET ───────────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "bina_enerji_dijital_ikiz_sunum.pptx" })
  .then(() => console.log("OK bina_enerji_dijital_ikiz_sunum.pptx"))
  .catch(err => { console.error("HATA:", err); process.exit(1); });
