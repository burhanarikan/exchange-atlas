/* =========================================================================
   Exchange Atlas · Erasmus · istemci mantığı (vanilla JS, statik)
   data.json'u fetch eder, tarayıcıda arar/filtreler. Tasarım: Atlas handoff.
   ========================================================================= */

const PAGE = 24;

const COUNTRY = {
  "ALMANYA": { en: "Germany", flag: "🇩🇪" },
  "DANİMARKA": { en: "Denmark", flag: "🇩🇰" },
  "ESTONYA": { en: "Estonia", flag: "🇪🇪" },
  "İSVEÇ": { en: "Sweden", flag: "🇸🇪" },
  "BULGARİSTAN": { en: "Bulgaria", flag: "🇧🇬" },
  "FİNLANDİYA": { en: "Finland", flag: "🇫🇮" }, "BELÇİKA": { en: "Belgium", flag: "🇧🇪" }, "AVUSTURYA": { en: "Austria", flag: "🇦🇹" },
  "FRANSA": { en: "France", flag: "🇫🇷" }, "HIRVATİSTAN": { en: "Croatia", flag: "🇭🇷" },
  "HOLLANDA": { en: "Netherlands", flag: "🇳🇱" }, "KUZEY MAKEDONYA": { en: "North Macedonia", flag: "🇲🇰" },
  "LETONYA": { en: "Latvia", flag: "🇱🇻" }, "LİTVANYA": { en: "Lithuania", flag: "🇱🇹" },
  "MACARİSTAN": { en: "Hungary", flag: "🇭🇺" }, "MALTA": { en: "Malta", flag: "🇲🇹" },
  "POLONYA": { en: "Poland", flag: "🇵🇱" }, "PORTEKİZ": { en: "Portugal", flag: "🇵🇹" },
  "ROMANYA": { en: "Romania", flag: "🇷🇴" }, "SIRBİSTAN": { en: "Serbia", flag: "🇷🇸" },
  "SLOVAKYA": { en: "Slovakia", flag: "🇸🇰" }, "SLOVENYA": { en: "Slovenia", flag: "🇸🇮" },
  "YUNANİSTAN": { en: "Greece", flag: "🇬🇷" }, "ÇEKYA": { en: "Czechia", flag: "🇨🇿" },
  "İSPANYA": { en: "Spain", flag: "🇪🇸" }, "İTALYA": { en: "Italy", flag: "🇮🇹" },
};

// Short ISCED family labels, used by the filter chips
const FAMILY_SHORT = {
  "01": { tr: "Eğitim", en: "Education" }, "02": { tr: "Sanat", en: "Arts" },
  "03": { tr: "Sosyal", en: "Social sci." }, "04": { tr: "İşletme", en: "Business" },
  "05": { tr: "Doğa bilimleri", en: "Sciences" }, "06": { tr: "Bilişim (BİT)", en: "ICT" },
  "07": { tr: "Mühendislik", en: "Engineering" }, "08": { tr: "Tarım", en: "Agriculture" },
  "09": { tr: "Sağlık", en: "Health" }, "10": { tr: "Hizmetler", en: "Services" },
};

const LEVELS = [
  { key: "onlisans", tr: "Ön Lisans", en: "Associate" },
  { key: "lisans", tr: "Lisans", en: "Bachelor" },
  { key: "yukseklisans", tr: "Y. Lisans", en: "Master" },
  { key: "doktora", tr: "Doktora", en: "PhD" },
];

const I18N = {
  tr: {
    descriptor: "Erasmus+ İkili Anlaşmalar", credit: "Veri: ilgili üniversite koordinatörlüğü",
    navList: "Anlaşmalar", navGuide: "Başvuru Rehberi", uniChange: "değiştir",
    searchPlaceholder: "Bölüm, üniversite veya ülke ara",
    filters: "Filtrele", filterBtn: "⚙ Filtrele", clear: "Temizle",
    country: "Ülke", field: "ISCED alan", degree: "Derece",
    onlyQuota: "Sadece öğrenim kontenjanı",
    noResult: "Aramanıza uygun anlaşma bulunamadı.",
    loadError: "Anlaşma listesi şu an yüklenemedi. Bu genelde geçici bir bağlantı sorunudur, sayfayı yenilemeyi deneyin. Site kapanmadı, veriler yerinde duruyor.",
    loadErrorSubject: "Exchange Atlas: liste yüklenmiyor",
    loadErrorWrite: "Sorun sürüyorsa bize yazın",
    results: "sonuç", showN: (n) => `${n} sonucu göster`,
    alansiz: (n) => `Kaynak veride alanı belirtilmemiş ${n} anlaşma bu filtreye giremiyor.`,
    shared: "Ortak kontenjan",
    diffCountryFixed: "Kaynak listede ülke {0} yazıyor; Erasmus kodu bu ülkeyi gösterdiği için düzeltildi.",
    diffCountryFilled: "Kaynak listede ülke boştu; Erasmus kodundan tamamlandı.",
    diffLevel: "İptal edildiği yazılı bir öğrenim kademesi listeden çıkarıldı. Kaynakta yazan: {0}",
    uniUnknown: "Bu platformda \u201c{0}\u201d diye bir üniversite yok.",
    uniMissing: "Hangi üniversitenin anlaşmalarını görmek istiyorsunuz?",
    uniPick: "Aşağıdakilerden birini seçebilirsiniz.",
    diffDept: "Kaynak listede Türkçe bölüm adı boştu, burada görünen alanın ISCED etiketi.",
    diffDeptFaculty: "Kaynak listede bölüm yazılmamış; anlaşma fakülte geneline ait görünüyor ve burada fakülte adı gösteriliyor.",
    diffDeptSpelling: "Bu bölüm kaynak listede birden çok yazımla geçiyor. Burada en sık kullanılan yazım gösteriliyor. Bu kayıtta yazan: {0}",
    diffFamily: "Alan kodu kaynakta üç haneli ({0}); baştaki sıfırın düştüğü varsayılarak sınıflandırıldı.",
    diffNote: "Bu nottan bir e-posta adresi çıkarıldı · yayımlanan veriye kişisel ya da kurumsal adres konmuyor.",
    noField: "Bu üniversitenin kaynak listesinde ISCED alan kodu yok, o yüzden alana göre süzemiyorsunuz. Bölüm adıyla arayabilirsiniz.",
    expired: "süresi doldu",
    // Öğrencinin bu listeyi kurumun listesiyle AYNI sanması, bu projenin en
    // somut zarar senaryosu · kurumun kendi adresi tek tık ötede duruyor.
    srcNotice: 'Bu liste {0} tarafından yayımlanan listeden derlendi ve <strong>birebir aynı değil</strong>: {1} kayıtta kaynaktan farklı bir bilgi gösteriliyor, hepsi kartta ⓘ ile işaretli. Resmî başvuru için <a href="{2}" target="_blank" rel="noopener">kurumun kendi listesine</a> bakın · <a href="{3}" target="_blank" rel="noopener">neyi neden değiştirdiğimiz</a>.',
    srcNoticeClean: 'Bu liste {0} tarafından yayımlanan listeden derlendi. Gösterim biçimi değişti, veriye dokunulmadı. Resmî başvuru için <a href="{2}" target="_blank" rel="noopener">kurumun kendi listesine</a> bakın · <a href="{3}" target="_blank" rel="noopener">nasıl okuduğumuz</a>.',
    study: "Öğrenim", intern: "Staj", personnel: "Personel",
    website: "Web sitesi", langLabel: "Dil",
    loadMore: (a, b) => `Daha fazla göster (${a} / ${b})`,
    stats: { anlasma: "anlaşma", ulke: "ülke", uni: "üniversite", alan: "alan" },
    footer: (d, credit) => `${credit} · Erasmus+ ikili anlaşma listesi (veri çekimi: ${d}).`,
    independence: `<strong>Exchange Atlas bağımsız bir platformdur; resmî bir üniversite hizmeti değildir.</strong> Veri, üniversitelerin kamuya açık listelerinden derlenir ve o listelerle birebir aynı değildir: Okurken verdiğimiz kararlar kartlarda ⓘ ile işaretlidir, ayrıca hata da içerebilir. Bağlayıcı olan kurumun kendi listesidir. Resmî başvuru için üniversitenizin Erasmus veya uluslararası ilişkiler birimine danışın.`,
  },
  en: {
    descriptor: "Erasmus+ Bilateral Agreements", credit: "Data: the relevant university office",
    navList: "Agreements", navGuide: "Application Guide", uniChange: "change",
    searchPlaceholder: "Search department, university or country",
    filters: "Filter", filterBtn: "⚙ Filter", clear: "Clear",
    country: "Country", field: "ISCED field", degree: "Degree",
    onlyQuota: "Only with study places",
    noResult: "No agreement matches your search.",
    loadError: "The agreement list could not be loaded right now. This is usually a temporary connection issue — try reloading the page. The site is not down and the data is still there.",
    loadErrorSubject: "Exchange Atlas: list not loading",
    loadErrorWrite: "Write to us if it keeps happening",
    results: "results", showN: (n) => `Show ${n} results`,
    alansiz: (n) => `${n} agreements have no field code in the source data and cannot appear in this filter.`,
    shared: "Shared quota",
    diffCountryFixed: "The source list says {0}; corrected because the Erasmus code indicates this country.",
    diffCountryFilled: "The source list left the country blank; filled in from the Erasmus code.",
    diffLevel: "A study level marked as cancelled in the source was removed. The source reads: {0}",
    uniUnknown: "There is no university called \u201c{0}\u201d on this platform.",
    uniMissing: "Which university's agreements would you like to see?",
    uniPick: "You can choose one below.",
    diffDept: "The source list had no Turkish department name; what you see is the field's ISCED label.",
    diffDeptFaculty: "The source list has no department here; the agreement appears to belong to the faculty as a whole, so the faculty name is shown.",
    diffDeptSpelling: "This department appears with more than one spelling in the source list. The most frequent one is shown here. This record reads: {0}",
    diffFamily: "The field code is three digits in the source ({0}); classified assuming a dropped leading zero.",
    diffNote: "An e-mail address was removed from this note · published data carries no personal or institutional addresses.",
    noField: "This university's source list has no ISCED field codes, so field filtering is unavailable. You can search by department name.",
    expired: "expired",
    srcNotice: 'This list is compiled from the list published by {0} and is <strong>not identical to it</strong>: {1} records show something different from the source, each marked with ⓘ on its card. For official applications see <a href="{2}" target="_blank" rel="noopener">the institution\'s own list</a> · <a href="{3}" target="_blank" rel="noopener">what we changed and why</a>.',
    srcNoticeClean: 'This list is compiled from the list published by {0}. The presentation changed; the data did not. For official applications see <a href="{2}" target="_blank" rel="noopener">the institution\'s own list</a> · <a href="{3}" target="_blank" rel="noopener">how we read it</a>.',
    study: "Study", intern: "Traineeship", personnel: "Staff",
    website: "Website", langLabel: "Language",
    loadMore: (a, b) => `Show more (${a} / ${b})`,
    stats: { anlasma: "agreements", ulke: "countries", uni: "universities", alan: "fields" },
    footer: (d, credit) => `${credit} — Erasmus+ bilateral agreements list (data as of: ${d}).`,
    independence: `<strong>Exchange Atlas is an independent platform, not an official university service.</strong> Data is compiled from universities' publicly available lists and is not identical to them: the decisions we made while reading are marked with ⓘ on each card, and errors are possible. The institution's own list is the authoritative one. For official applications, contact your university's Erasmus or international relations office.`,
  },
};

const UNI_ID = (new URLSearchParams(location.search).get("uni") || "").toLowerCase();
let UNI = null; // universities.json'daki aktif üniversite kaydı
let DATA = null;
// In browsers that block cookies, localStorage does not go "missing": it THROWS.
// An unguarded read would take the whole script down and leave the page blank.
// The write side (setLang) was already guarded; index.html and guide.html apply
// the same guard when reading.
let lang = (() => {
  try { return localStorage.getItem("atlas-lang") === "en" ? "en" : "tr"; }
  catch (e) { return "tr"; }
})();
let shown = PAGE;
const state = { q: "", qWords: [], countries: new Set(), families: new Set(), levels: new Set(), onlyQuota: false };

// The address is assembled from parts: scrapers look for plain-text e-mail.
const GERI_BILDIRIM = "burhanarikan" + "@" + "yaani" + ".com";
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]));
const oneLine = (s) => String(s || "").replace(/\s*\n\s*/g, " ").trim();
/* Unicode ayrıştırması "harf + işaret" karakterlerini çözer (ä -> a + ¨); aşağıdakiler
   ayrı harf olduğu için elle eşlenir. build_data.py'daki eşi ile aynı kalmalı
   (bkz. tests/test_couplings.py). */
const FOLD_EXCEPTIONS = { "ı": "i", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D", "ø": "o", "Ø": "O", "ß": "ss" };
const fold = (s) => String(s == null ? "" : s)
  .replace(/[^\x00-\x7F]/g, (c) => FOLD_EXCEPTIONS[c] || c)
  .normalize("NFD").replace(/[̀-ͯ]/g, "")
  .toLowerCase();
const t = () => I18N[lang];

/* Üniversite belirlenemedi: sessizce başka bir listeye düşmek yerine
   durumu söyleyip seçime yönlendiriyoruz. */
function uniSecilemedi(unis) {
  const L = t();
  const ana = $(".app-main");
  if (!ana) return;
  const baslik = UNI_ID ? L.uniUnknown.replace("{0}", esc(UNI_ID)) : L.uniMissing;
  const secenekler = unis.map((u) =>
    `<li><a href="agreements.html?uni=${esc(u.id)}">${esc(u.nameTr === u.nameEn || lang !== "en" ? u.nameTr : u.nameEn)}</a></li>`
  ).join("");
  ana.innerHTML =
    `<div class="uni-missing">` +
    `<h1>${baslik}</h1>` +
    `<p>${L.uniPick}</p>` +
    `<ul>${secenekler}</ul>` +
    `</div>`;
  document.title = baslik;
}

/* ── init ───────────────────────────────── */
async function init() {
  const unis = await (await fetch("universities.json")).json();

  // An unrecognised ?uni= value must NEVER fall back to a different university.
  // This used to read `|| unis[0]`. Invisible while there was only one university,
  // it would have become "the student mistakes another university's list for
  // their own" as soon as a second one arrived, with no warning at all.
  //
  // A MISSING parameter is a different case: nothing was requested. With a single
  // university on the platform there is no ambiguity, so that one is used.
  UNI = UNI_ID
    ? unis.find((u) => u.id === UNI_ID)
    : (unis.length === 1 ? unis[0] : null);
  if (!UNI) { uniSecilemedi(unis); return; }

  DATA = await (await fetch(`data-${UNI.id}.json`)).json();

  // University badge, plus hide the guide tab for universities without a guide
  const abbrEl = $("#uniAbbr");
  if (abbrEl) abbrEl.textContent = UNI.abbr;
  const guideLink = document.querySelector('.header-nav a[href="guide.html"]');
  if (guideLink) {
    if (UNI.hasGuide) guideLink.href = `guide.html?uni=${UNI.id}`;
    else guideLink.style.display = "none";
  }
  // nav self-link ?uni= parametresini korusun
  const self = document.querySelector('.header-nav a[href="agreements.html"]');
  if (self) self.href = `agreements.html?uni=${UNI.id}`;

  cizSourceNotice();
  buildStatRow();
  buildCountryChips();
  buildFamilyChips();
  buildDegreeChips();
  bindControls();
  document.documentElement.lang = lang;
  document.querySelectorAll(".lang-toggle button").forEach((b) => b.classList.toggle("active", b.dataset.lang === lang));
  applyLang();
  render();
}

const KAYNAK_BELGESI =
  "https://github.com/burhanarikan/exchange-atlas/blob/main/KAYNAK.md";

function cizSourceNotice() {
  const el = $("#sourceNotice");
  if (!el || !UNI || !UNI.sourceUrl) return;
  const L = t();
  const n = UNI.diffCount || 0;
  // Sayı SIFIRSA başka cümle kuruluyor: "0 kayıtta fark var" demek, farkın
  // olmadığını söylemenin en kötü yolu.
  el.innerHTML = (n > 0 ? L.srcNotice : L.srcNoticeClean)
    .replace("{0}", esc(lang === "en" ? UNI.nameEn : UNI.nameTr))
    .replace("{1}", String(n))
    .replace("{2}", esc(UNI.sourceUrl))
    .replace("{3}", KAYNAK_BELGESI);
  el.hidden = false;
}

function buildStatRow() {
  const uni = new Set(DATA.agreements.map((a) => a.university)).size;
  const s = [
    [DATA.count, "anlasma"], [DATA.countries.length, "ulke"], [uni, "uni"],
  ];
  // "0 alan" okunduğunda veri kaybı gibi görünüyor, oysa kaynakta o bilgi hiç
  // yok. Sıfır olduğunda sayı gösterilmiyor · sebebi alan süzgecinde yazılı.
  if (DATA.iscedFamilies.length) s.push([DATA.iscedFamilies.length, "alan"]);
  $("#statRow").innerHTML = s.map(([n, k]) =>
    `<div class="stat"><b>${n}</b><span data-stat="${k}">${t().stats[k]}</span></div>`).join("");
}

function countryName(c) { return lang === "en" && COUNTRY[c] ? COUNTRY[c].en : c; }
function famShort(code) { return FAMILY_SHORT[code] ? FAMILY_SHORT[code][lang] : code; }

function buildCountryChips() {
  const counts = {};
  DATA.agreements.forEach((a) => (counts[a.country] = (counts[a.country] || 0) + 1));
  const box = $("#countryChips");
  box.innerHTML = DATA.countries.slice().sort((a, b) => counts[b] - counts[a]).map((c) =>
    `<button type="button" class="chip-select" data-kind="country" data-val="${esc(c)}">${COUNTRY[c] ? COUNTRY[c].flag + " " : ""}<span class="cname">${esc(countryName(c))}</span> <span class="n">${counts[c]}</span></button>`
  ).join("");
}

function buildFamilyChips() {
  const box = $("#familyChips");
  // Not every source carries ISCED codes. When none do, the filter would be a
  // labelled empty box, which reads as a broken page. Saying WHY is better than
  // hiding it: a student who expected to filter by field gets an answer instead
  // of a blank.
  if (!DATA.iscedFamilies.length) {
    box.innerHTML = `<p class="filter-note">${esc(t().noField)}</p>`;
    return;
  }
  box.innerHTML = DATA.iscedFamilies.slice().sort((a, b) => b.count - a.count).map((f) =>
    `<button type="button" class="chip-select" data-kind="family" data-val="${f.code}"><span class="fname">${esc(famShort(f.code))}</span> <span class="n">${f.count}</span></button>`
  ).join("");
}

function buildDegreeChips() {
  $("#degreeChips").innerHTML = LEVELS.map((l) =>
    `<button type="button" class="chip-select" data-kind="level" data-val="${l.key}">${l[lang]}</button>`).join("");
}

/* ── events ─────────────────────────────── */
function bindControls() {
  let dt;
  $("#search").addEventListener("input", (e) => {
    clearTimeout(dt);
    dt = setTimeout(() => {
      state.q = fold(e.target.value.trim());
      state.qWords = state.q.split(/\s+/).filter(Boolean);
      shown = PAGE; render();
    }, 120);
  });

  $("#filters").addEventListener("click", (e) => {
    const chip = e.target.closest(".chip-select");
    if (chip) {
      const set = { country: state.countries, family: state.families, level: state.levels }[chip.dataset.kind];
      const v = chip.dataset.val;
      set.has(v) ? set.delete(v) : set.add(v);
      shown = PAGE; render();
      return;
    }
    if (e.target.closest("#quotaToggle")) {
      state.onlyQuota = !state.onlyQuota; shown = PAGE; render();
    }
  });

  
  $("#clearBtn").addEventListener("click", clearAll);
  $("#clearBtnSheet").addEventListener("click", clearAll);
  $("#loadMore").addEventListener("click", () => { shown += PAGE; render(); });

  // mobile sheet
  $("#filterTrigger").addEventListener("click", openSheet);
  $("#applyBtn").addEventListener("click", closeSheet);
  $("#sheetBackdrop").addEventListener("click", closeSheet);

  document.querySelectorAll(".lang-toggle button").forEach((b) =>
    b.addEventListener("click", () => setLang(b.dataset.lang)));
}

function openSheet() { document.body.classList.add("sheet-open"); $("#sheetBackdrop").hidden = false; }
function closeSheet() { document.body.classList.remove("sheet-open"); $("#sheetBackdrop").hidden = true; }

function clearAll() {
  state.q = ""; state.qWords = [];
  state.countries.clear(); state.families.clear(); state.levels.clear(); state.onlyQuota = false;
  $("#search").value = ""; shown = PAGE; render();
}

/* ── filtering ──────────────────────────── */
function hasStudyQuota(a) {
  const n = parseInt(a.quotaStudy, 10);
  if (!isNaN(n) && n > 0) return true;
  return Object.values(a.levels || {}).some((v) => v === "shared" || parseInt(v, 10) > 0);
}
function match(a, alanKosuluAtla) {
  // Each word is matched SEPARATELY and order does not matter, so that someone
  // typing "Lublin University" still finds "University of Life Sciences in Lublin".
  if (state.qWords.length && !state.qWords.every((w) => a.search.includes(w))) return false;
  if (state.countries.size && !state.countries.has(a.country)) return false;
  // alanKosuluAtla: to count records dropped for having no field, the same filter
  // is run once more without the field condition (see render).
  if (!alanKosuluAtla && state.families.size && !state.families.has(a.iscedFamily)) return false;
  if (state.levels.size && !LEVELS.some((l) => state.levels.has(l.key) && a.levels && a.levels[l.key])) return false;
  if (state.onlyQuota && !hasStudyQuota(a)) return false;
  return true;
}
function activeCount() {
  return state.countries.size + state.families.size + state.levels.size + (state.onlyQuota ? 1 : 0);
}

/* ── render ─────────────────────────────── */
function render() {
  // Do NOT pass match straight to filter: filter hands the callback
  // (item, index, array), the index lands in match's second parameter and
  // silently skips the field condition.
  const filtered = DATA.agreements.filter((a) => match(a));
  $("#grid").innerHTML = filtered.slice(0, shown).map(card).join("");

  const L = t();
  $("#resultCount").innerHTML = `<span class="n">${filtered.length}</span> ${L.results}`;

  // Records with an unknown field are dropped silently while the field filter is
  // on, and the user concludes "there are few agreements in this field". We state
  // the count instead of hiding it: declare the limit rather than conceal it.
  // Today that count is 1; it was once 243, and the cause was not the source data
  // but reading the ISCED code from the wrong column (see build_data.py).
  const alansizGizli = state.families.size
    ? DATA.agreements.filter((a) => !a.iscedFamily && match(a, true)).length
    : 0;
  const uyari = $("#fieldNotice");
  uyari.hidden = alansizGizli === 0;
  if (alansizGizli) uyari.textContent = L.alansiz(alansizGizli);
  const active = state.q || activeCount();
  $("#clearBtn").hidden = !active;
  $("#empty").hidden = filtered.length > 0;

  const lm = $("#loadMore");
  if (filtered.length > shown) { lm.hidden = false; lm.textContent = L.loadMore(Math.min(shown, filtered.length), filtered.length); }
  else lm.hidden = true;

  // reflect selected chips
  document.querySelectorAll("#filters .chip-select").forEach((c) => {
    const set = { country: state.countries, family: state.families, level: state.levels }[c.dataset.kind];
    c.classList.toggle("active", set.has(c.dataset.val));
  });
  $("#quotaSwitch").classList.toggle("on", state.onlyQuota);
  $("#quotaToggle").setAttribute("aria-pressed", String(state.onlyQuota));

  // mobile: filter count + active chips + apply button
  const n = activeCount();
  const fc = $("#filterCount"); fc.textContent = n; fc.hidden = n === 0;
  $("#applyBtn").textContent = L.showN(filtered.length);
  renderActiveChips();
}

function renderActiveChips() {
  const chips = [];
  state.countries.forEach((c) => chips.push(`<span class="chip-select active">${COUNTRY[c] ? COUNTRY[c].flag + " " : ""}${esc(countryName(c))}</span>`));
  state.families.forEach((f) => chips.push(`<span class="chip-select active">${esc(famShort(f))}</span>`));
  state.levels.forEach((k) => { const l = LEVELS.find((x) => x.key === k); if (l) chips.push(`<span class="chip-select active">${l[lang]}</span>`); });
  $("#activeChips").innerHTML = chips.join("");
}

// Every place we depart from the source is shown on the card. Hiding it would
// contradict the claim "we take the data from the university": we do take it,
// but we make decisions while reading, and those decisions change what the
// student sees.
function sourceNote(a) {
  if (!a.sourceDiff) return "";
  const L = t();
  const parcalar = [];
  const d = a.sourceDiff;
  if (d.country) {
    parcalar.push(d.country.kaynakta
      ? L.diffCountryFixed.replace("{0}", esc(d.country.kaynakta))
      : L.diffCountryFilled);
  }
  if (d.levels) {
    // The source cell can span several lines; the card collapses it to one.
    const ham = String(d.levels.kaynakta || "").replace(/\s*\n\s*/g, " / ").trim();
    parcalar.push(L.diffLevel.replace("{0}", esc(ham)));
  }
  if (d.iscedFamily) parcalar.push(L.diffFamily.replace("{0}", esc(d.iscedFamily.kaynakta)));
  if (d.quotaNote) parcalar.push(L.diffNote);
  if (d.department) {
    // Her sebebin kendi cümlesi var. Eskiden sebebe bakılmadan tek cümle
    // basılıyordu ve üçüncü bir sebep eklendiğinde öğrenciye YANLIŞ açıklama
    // gösterdi: ESOGÜ kartında "ISCED etiketi" yazıyordu, oysa orada fakülte
    // adı duruyordu. Sebebi tanınmayan bir iz artık cümle uydurmuyor.
    const cumle = {
      "yazim-birligi": () => L.diffDeptSpelling.replace("{0}", esc(d.department.kaynakta)),
      "isced-etiketi": () => L.diffDept,
      "fakulte-adi": () => L.diffDeptFaculty,
    }[d.department.sebep];
    if (cumle) parcalar.push(cumle());
  }
  if (!parcalar.length) return "";
  return `<p class="source-diff"><span class="source-diff-mark">i</span>${parcalar.join(" ")}</p>`;
}

// Süresi dolmuş anlaşma, dolmamış olandan ayırt edilemiyordu: Kart geçerlilik
// aralığını yazıyor ama "2022/2024" ile "2022/2029" aynı görünüyor ve okuyan
// kişi yılı kendisi hesaplamak zorunda kalıyor.
//
// HESAP ÇALIŞMA ANINDA YAPILIYOR, derlemede değil. Derlemede hesaplansaydı
// bayrak dosyayla birlikte donardı ve bir sonraki yıl sessizce yanlış olurdu ·
// veri her gün yeniden üretilmiyor.
//
// Bitiş yılının iki yazımı var ve ikisi de kaynakta geçiyor: "2022/2027" ve
// "2022/27". İkincisi ilk denemede yanlış okundu (2027 yerine 2022 sanıldı) ve
// otuz üç anlaşma "dolmuş" göründü · iki haneli son ek ayrıca ele alınıyor.
function bitisYili(ham) {
  const parca = String(ham).split(/[/\-–]/);
  if (parca.length < 2) {
    const t = String(ham).match(/\b(20\d{2})\b/g);
    return t ? parseInt(t[t.length - 1], 10) : null;
  }
  const son = parca[parca.length - 1].trim();
  if (/^20\d{2}$/.test(son)) return parseInt(son, 10);
  if (/^\d{2}$/.test(son)) return 2000 + parseInt(son, 10);
  return null;
}

function bitmisMi(ham) {
  const y = bitisYili(ham);
  return y !== null && y < new Date().getFullYear();
}

function card(a) {
  const L = t();
  const flag = COUNTRY[a.country] ? COUNTRY[a.country].flag : "🏳️";
  const fam = lang === "en" ? a.iscedFamilyEn : a.iscedFamilyTr;

  const degrees = LEVELS.filter((l) => a.levels && a.levels[l.key]).map((l) => {
    const shared = a.levels[l.key] === "shared";
    return `<span class="chip chip-degree${shared ? " joint" : ""}">${l[lang]}${shared ? " *" : ""}</span>`;
  }).join("");

  const quota = [];
  if (parseInt(a.quotaStudy, 10) > 0) quota.push(`<span class="chip chip-quota">${L.study} · ${esc(a.quotaStudy)}</span>`);
  if (parseInt(a.quotaInternship, 10) > 0) quota.push(`<span class="chip chip-quota">${L.intern} · ${esc(a.quotaInternship)}</span>`);
  const staff = parseInt(a.quotaStaffTeach, 10) || parseInt(a.quotaStaffTrain, 10);
  if (staff > 0) quota.push(`<span class="chip chip-quota">${L.personnel} · ${staff}</span>`);

  // The source gives the language requirement as one string ("Eng. B1"); we do
  // not parse it.
  const langs = [];
  if (a.language && a.language.raw) {
    langs.push(`<span class="chip chip-lang">${L.langLabel} · ${esc(a.language.raw).slice(0, 34)}</span>`);
  }

  const metaLeft = a.validity && a.validity.raw
    ? `${esc(a.validity.raw)}${bitmisMi(a.validity.raw) ? ` <span class="expired">${L.expired}</span>` : ""}`
    : "";
  // The real note from the source sheet wins: it can be critical ("applies only to X")
  const noteText = a.quotaNote ? esc(oneLine(a.quotaNote)) : (a.sharedQuota ? L.shared : "");
  const note = noteText ? `<span class="note">${noteText}</span>` : "";

  const extIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><path d="M15 3h6v6"/><path d="M10 14 21 3"/></svg>`;
  let web = "";
  if (a.website && /^https?:\/\//i.test(a.website)) {
    web = `<a href="${esc(a.website)}" target="_blank" rel="noopener">${L.website} ${extIcon}</a>`;
  }

  return `<article class="agr-card">
    <div class="top-row"><span class="flag">${flag}</span><span class="country">${esc(countryName(a.country))}</span></div>
    <h3 class="uni">${esc(oneLine(a.university))}</h3>
    ${a.department ? `<p class="dept">${esc(oneLine(a.department))}</p>` : ""}
    ${fam ? `<div class="isced-line"><span class="chip chip-isced">${esc(fam)}${a.iscedCode ? ` · ${esc(a.iscedCode)}` : ""}</span></div>` : ""}
    ${(degrees || quota.length || langs.length) ? `<div class="badges">${degrees}${quota.join("")}${langs.join("")}</div>` : ""}
    <div class="meta-row"><span>${metaLeft}</span>${note}</div>
    ${sourceNote(a)}
    ${web ? `<div class="foot-row">${web}</div>` : ""}
  </article>`;
}

/* ── i18n ───────────────────────────────── */
function setLang(l) {
  if (l === lang) return;
  lang = l;
  try { localStorage.setItem("atlas-lang", l); } catch (e) {}
  document.documentElement.lang = l;
  document.querySelectorAll(".lang-toggle button").forEach((b) => b.classList.toggle("active", b.dataset.lang === l));
  // rebuild label-bearing chips
  buildCountryChips(); buildFamilyChips(); buildDegreeChips();
  applyLang();
  render();
}

function applyLang() {
  const L = t();
  document.querySelectorAll("[data-i18n]").forEach((e) => { const k = e.dataset.i18n; if (L[k]) e.textContent = L[k]; });
  document.querySelectorAll("[data-i18n-ph]").forEach((e) => { const k = e.dataset.i18nPh; if (L[k]) { e.placeholder = L[k]; e.setAttribute("aria-label", L[k]); } });
  document.querySelectorAll("[data-stat]").forEach((e) => { e.textContent = L.stats[e.dataset.stat]; });
  const credit = lang === "en" ? UNI.creditEn : UNI.creditTr;
  const t3 = document.querySelector(".brand-text .t3");
  if (t3) t3.textContent = credit;
  // The independence notice is the first footer line on all three pages (guarded by tests).
  $("#independenceLine").innerHTML = L.independence;
  $("#footerText").innerHTML = L.footer((DATA.generatedAt || "").slice(0, 10), esc(credit));
  // İletişim satırı üç sayfada da AYNI şeyi söylüyor. Eskiden burada yalnız
  // "Geri bildirim" yazıyordu; index ve guide "düzeltme ve kaldırma
  // talepleri" diyordu · yani anlaşma listesine bakan kurum, kaldırma
  // talebinde bulunabileceğini o sayfadan öğrenemiyordu.
  //
  // Koşulsuz kaldırma sözü KAYNAK.md'de yazılıydı ama SİTEDE görünmüyordu.
  // Kurumun okuyacağı yer burası, depo değil.
  const ft = $("#footerText");
  ft.appendChild(document.createTextNode(
    " · " + (lang === "en" ? "Feedback, university additions, corrections and removal requests: " : "Geri bildirim, üniversite ekleme, düzeltme ve kaldırma talepleri: ")));
  const fb = document.createElement("a");
  fb.href = "mail" + "to:" + GERI_BILDIRIM;
  fb.textContent = GERI_BILDIRIM;
  ft.appendChild(fb);
  const soz = document.createElement("span");
  soz.className = "removal-promise";
  soz.textContent = " · " + (lang === "en"
    ? "If you are an institution whose data appears here: correction and removal requests are honoured without asking for a reason."
    : "Verisi burada görünen bir kurumsanız: Düzeltme ya da kaldırma talebiniz gerekçe sorulmadan yerine getirilir.");
  ft.appendChild(soz);
  document.title = `Exchange Atlas · Erasmus · ${UNI.abbr} ` + L.descriptor;
}

// Without data the page would stay an empty shell: no list, no result count, no
// warning. The user says "it is broken" and never learns why. We make the failure
// visible instead.
init().catch((hata) => {
  // The real error goes to the developer console only: technical detail does not
  // help the user and needlessly exposes information about the system.
  console.error("Veri yüklenemedi:", hata);

  const kap = $("#empty");
  if (!kap) return;
  const L = t();
  // The feedback link is built HERE as well: the footer link is written by init(),
  // which has already failed at this point. Saying "write to us" without showing
  // where would leave the user with no way out.
  const konu = encodeURIComponent(L.loadErrorSubject);
  kap.hidden = false;
  kap.innerHTML =
    `<div class="big">⚠️</div>` +
    `<p>${esc(L.loadError)}</p>` +
    `<p><a href="mail${"to"}:${esc(GERI_BILDIRIM)}?subject=${konu}">${esc(L.loadErrorWrite)}</a></p>`;
});
