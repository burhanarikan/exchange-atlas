/* index.html sayfa betiği · satır içindeydi, dosyaya taşındı.

   Sebep güvenlik: Satır içi script varken CSP ya `unsafe-inline` ile
   zayıflatılmak zorunda kalıyor ya da sayfayı kırıyor. Dosyaya taşınınca
   `script-src 'self'` hiçbir ödün vermeden uygulanabiliyor. */
(function () {
  var lang = (function () { try { return localStorage.getItem("atlas-lang") === "en" ? "en" : "tr"; } catch (e) { return "tr"; } })();
  var UNIS = null;
  // Liste yüklenemediğinde bayrak kalkıyor ve `renderUnis` hata kartını
  // çiziyor. Ayrı bir "hata göster" yolu yazılsaydı dil değiştirildiğinde
  // kart eski dilde kalırdı · tek çizim yolu bu sorunu tümüyle kaldırıyor.
  var YUKLEME_HATASI = false;
  // adres bot taramasına karşı parçalı tutulur
  function adres() { return "burhanarikan" + "@" + "yaani" + ".com"; }
  var MONTHS = {
    tr: ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"],
    en: ["January","February","March","April","May","June","July","August","September","October","November","December"]
  };
  var TPL = {
    stats: { tr: "{c} anlaşma · {u} partner üniversite · {n} ülke", en: "{c} agreements · {u} partner universities · {n} countries" },
    updated: { tr: "Veri üretimi: {d}", en: "Data generated: {d}" },
    loadError: {
      tr: "Üniversite listesi şu an yüklenemedi. Bu genelde geçici bir bağlantı sorunudur, sayfayı yenilemeyi deneyin. Site kapanmadı, veriler yerinde duruyor.",
      en: "The university list could not be loaded right now. This is usually a temporary connection issue, try reloading the page. The site is not down and the data is still there."
    },
    loadErrorWrite: { tr: "Sorun sürüyorsa bize yazın", en: "Write to us if it keeps happening" },
    loadErrorSubject: {
      tr: "Exchange Atlas: üniversite listesi yüklenmiyor",
      en: "Exchange Atlas: university list not loading"
    }
  };
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (m) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]; }); }
  function apply() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-tr]").forEach(function (el) {
      var v = el.getAttribute("data-" + lang);
      if (v == null) return;
      // data-html: metninde biçimlendirme (ör. <strong>) olan öğeler. Varsayılan
      // textContent; çünkü innerHTML'i her yere açmak gereksiz bir yüzey.
      // Değerler bu dosyada elle yazılı sabitler, kullanıcı girdisi değil.
      if (el.hasAttribute("data-html")) el.innerHTML = v; else el.textContent = v;
    });
    document.querySelectorAll(".lang-toggle button").forEach(function (b) {
      b.classList.toggle("active", b.dataset.lang === lang);
    });
    document.title = "Exchange Atlas · Erasmus · " + (lang === "en" ? "Erasmus+ Bilateral Agreements" : "Erasmus+ İkili Anlaşmalar");
    renderUnis();
  }
  function hataKarti() {
    var d = document.createElement("div");
    d.className = "uni-card ghost";
    d.id = "uniLoadError";
    var govde = document.createElement("span");
    govde.className = "uni-body";
    var baslik = document.createElement("span");
    baslik.className = "uni-name";
    baslik.textContent = TPL.loadError[lang];
    govde.appendChild(baslik);
    // Yazışma bağlantısı BURADA da kuruluyor: Alt bilgideki bağlantıyı
    // `renderContact` yazıyor, ama "bize yazın" deyip nereye yazılacağını
    // göstermemek kullanıcıyı çıkışsız bırakır.
    var alt = document.createElement("span");
    alt.className = "uni-stats";
    var a = document.createElement("a");
    a.href = "mail" + "to:" + adres() + "?subject=" + encodeURIComponent(TPL.loadErrorSubject[lang]);
    a.textContent = TPL.loadErrorWrite[lang];
    alt.appendChild(a);
    govde.appendChild(alt);
    var ikon = document.createElement("span");
    ikon.className = "uni-emblem q";
    ikon.setAttribute("aria-hidden", "true");
    ikon.textContent = "!";
    d.appendChild(ikon);
    d.appendChild(govde);
    return d;
  }
  function renderUnis() {
    var ghost = document.getElementById("ghostCard");
    if (!ghost) return;
    document.querySelectorAll("#uniGrid a.uni-card:not(.ghost)").forEach(function (e) { e.remove(); });
    var eskiHata = document.getElementById("uniLoadError");
    if (eskiHata) eskiHata.remove();
    if (YUKLEME_HATASI) { ghost.parentNode.insertBefore(hataKarti(), ghost); return; }
    if (!UNIS) return;
    UNIS.forEach(function (u) {
      var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(u.generatedAt || "");
      var date = m ? (parseInt(m[3], 10) + " " + MONTHS[lang][parseInt(m[2], 10) - 1] + " " + m[1]) : "";
      var a = document.createElement("a");
      a.className = "uni-card";
      a.href = "agreements.html?uni=" + encodeURIComponent(u.id);
      a.innerHTML =
        '<span class="uni-emblem mono" aria-hidden="true">' + esc(u.monogram) + '</span>' +
        '<span class="uni-body">' +
          '<span class="uni-name">' + esc(lang === "en" ? u.nameEn : u.nameTr) + '</span>' +
          '<span class="uni-abbr">' + esc(u.abbr) + '</span>' +
          '<span class="uni-stats">' + TPL.stats[lang].replace("{c}", u.count).replace("{u}", u.universities).replace("{n}", u.countries) + '</span>' +
          (date ? '<span class="uni-updated">' + TPL.updated[lang].replace("{d}", date) + '</span>' : "") +
        '</span>' +
        '<span class="uni-go" aria-hidden="true">→</span>';
      ghost.parentNode.insertBefore(a, ghost);
    });
  }
  document.querySelectorAll(".lang-toggle button").forEach(function (b) {
    b.addEventListener("click", function () {
      lang = b.dataset.lang;
      try { localStorage.setItem("atlas-lang", lang); } catch (e) {}
      apply();
    });
  });
  function renderContact() {
    var addr = adres();
    var el = document.getElementById("contactLine");
    el.innerHTML = "";
    el.appendChild(document.createTextNode(lang === "en"
      ? "Feedback, university additions, corrections and removal requests: "
      : "Geri bildirim, üniversite ekleme, düzeltme ve kaldırma talepleri: "));
    var a = document.createElement("a");
    a.href = "mail" + "to:" + addr;
    a.textContent = addr;
    el.appendChild(a);
    // Koşulsuz kaldırma sözü · KAYNAK.md'de yazılıydı ama SİTEDE
    // görünmüyordu. Kurumun okuyacağı yer burası, depo değil.
    el.appendChild(document.createTextNode(" · "));
    var soz = document.createElement("span");
    soz.className = "removal-promise";
    soz.textContent = lang === "en"
      ? "If you are an institution whose data appears here: correction and removal requests are honoured without asking for a reason."
      : "Verisi burada görünen bir kurumsanız: Düzeltme ya da kaldırma talebiniz gerekçe sorulmadan yerine getirilir.";
    el.appendChild(soz);
    var g = document.getElementById("ghostCard");
    if (g) g.href = "mail" + "to:" + addr + "?subject=" + encodeURIComponent(
      lang === "en" ? "Exchange Atlas: University request" : "Exchange Atlas: Üniversite talebi");
  }
  var _apply0 = apply;
  apply = function () { _apply0(); renderContact(); };
  // Boş bir `catch` vardı: Liste yüklenemediğinde sayfa hiçbir uyarı
  // vermeden boş kalıyordu ve kullanıcı "bozuk" deyip nedenini hiç
  // öğrenemiyordu. `agreements.html` bu durumu zaten görünür kılıyordu,
  // giriş sayfası kılmıyordu · aynı riske iki sayfada iki farklı davranış.
  atlasJson("universities.json")
    .then(function (u) { UNIS = u; YUKLEME_HATASI = false; renderUnis(); })
    .catch(function (hata) {
      // Teknik ayrıntı yalnız konsola · kullanıcıya yardımı yok ve sistem
      // hakkında gereksiz bilgi verir.
      console.error("Üniversite listesi yüklenemedi:", hata);
      YUKLEME_HATASI = true;
      renderUnis();
    });
  apply();
})();
