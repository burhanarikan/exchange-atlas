/* index.html sayfa betiği · satır içindeydi, dosyaya taşındı.

   Sebep güvenlik: Satır içi script varken CSP ya `unsafe-inline` ile
   zayıflatılmak zorunda kalıyor ya da sayfayı kırıyor. Dosyaya taşınınca
   `script-src 'self'` hiçbir ödün vermeden uygulanabiliyor. */
(function () {
  var lang = (function () { try { return localStorage.getItem("atlas-lang") === "en" ? "en" : "tr"; } catch (e) { return "tr"; } })();
  var UNIS = null;
  var MONTHS = {
    tr: ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"],
    en: ["January","February","March","April","May","June","July","August","September","October","November","December"]
  };
  var TPL = {
    stats: { tr: "{c} anlaşma · {u} partner üniversite · {n} ülke", en: "{c} agreements · {u} partner universities · {n} countries" },
    updated: { tr: "Veri üretimi: {d}", en: "Data generated: {d}" }
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
  function renderUnis() {
    if (!UNIS) return;
    var ghost = document.getElementById("ghostCard");
    document.querySelectorAll("#uniGrid a.uni-card:not(.ghost)").forEach(function (e) { e.remove(); });
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
    // adres bot taramasına karşı parçalı tutulur
    var u = "burhanarikan", d = "yaani" + ".com", addr = u + "@" + d;
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
  fetch("universities.json").then(function (r) { return r.json(); }).then(function (u) { UNIS = u; renderUnis(); }).catch(function () {});
  apply();
})();
