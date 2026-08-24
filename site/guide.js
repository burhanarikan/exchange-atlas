/* guide.html sayfa betiği · satır içindeydi, dosyaya taşındı.

   Sebep güvenlik: Satır içi script varken CSP ya `unsafe-inline` ile
   zayıflatılmak zorunda kalıyor ya da sayfayı kırıyor. Dosyaya taşınınca
   `script-src 'self'` hiçbir ödün vermeden uygulanabiliyor. */
(function () {
  var lang = (function () { try { return localStorage.getItem("atlas-lang") === "en" ? "en" : "tr"; } catch (e) { return "tr"; } })();
  var UNI_ID = (new URLSearchParams(location.search).get("uni") || "").toLowerCase();
  var UNIS = null;
  var UNI = null;

  var I18N_GUIDE = {
    tr: {
      title: "Exchange Atlas · Erasmus · {abbr} Başvuru Rehberi",
      titleDefault: "Exchange Atlas · Erasmus · Başvuru Rehberi",
      noGuideTitle: "{name} için rehber henüz eklenmedi",
      noGuideMsg: "Bu üniversitenin öğrencisi ya da koordinatörlük personeliyseniz başvuru rehberinin hazırlanmasına katkıda bulunabilirsiniz.",
      goToAgreements: "Anlaşmaları Gör →",
      unknownUni: "Bu platformda \u201c{0}\u201d diye bir üniversite yok.",
      missingUni: "Hangi üniversitenin rehberini görmek istiyorsunuz?",
      removalPromise: "Verisi burada görünen bir kurumsanız: Düzeltme ya da kaldırma talebiniz gerekçe sorulmadan yerine getirilir.",
      pickUni: "Aşağıdakilerden birini seçebilirsiniz:",
      feedbackPrefix: "Geri bildirim, üniversite ekleme, düzeltme ve kaldırma talepleri: "
    },
    en: {
      title: "Exchange Atlas · Erasmus · {abbr} Application Guide",
      titleDefault: "Exchange Atlas · Erasmus · Application Guide",
      noGuideTitle: "No application guide yet for {name}",
      noGuideMsg: "If you are a student or coordination-office staff at this university, you can contribute to its application guide.",
      goToAgreements: "View Agreements →",
      unknownUni: "There is no university called \u201c{0}\u201d on this platform.",
      missingUni: "Which university's guide would you like to see?",
      removalPromise: "If you are an institution whose data appears here: correction and removal requests are honoured without asking for a reason.",
      pickUni: "You can choose one below:",
      feedbackPrefix: "Feedback, university additions, corrections and removal requests: "
    }
  };

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (m) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]; }); }

  function renderView() {
    var hero = document.getElementById("guideHero");
    var noGuideSec = document.getElementById("noGuideSec");
    var missingUniSec = document.getElementById("missingUniSec");
    var t3 = document.querySelector(".brand-text .t3");
    var abbrEl = document.getElementById("uniAbbr");
    var navA = document.querySelector('.header-nav a[href^="agreements.html"]');
    var navG = document.querySelector('.header-nav a[href^="guide.html"]');

    document.querySelectorAll(".uni-sec").forEach(function (d) { d.hidden = true; });
    if (noGuideSec) noGuideSec.hidden = true;
    if (missingUniSec) missingUniSec.hidden = true;

    if (UNI) {
      if (hero) hero.hidden = false;
      if (abbrEl) abbrEl.textContent = UNI.abbr;
      if (t3) t3.textContent = lang === "en" ? UNI.creditEn : UNI.creditTr;
      if (navA) navA.href = "agreements.html?uni=" + encodeURIComponent(UNI.id);
      if (navG) navG.href = "guide.html?uni=" + encodeURIComponent(UNI.id);

      document.title = I18N_GUIDE[lang].title.replace("{abbr}", UNI.abbr);

      if (UNI.hasGuide) {
        var sec = document.querySelector('.uni-sec[data-uni="' + UNI.id + '"]');
        if (sec) sec.hidden = false;
      } else {
        if (noGuideSec) {
          noGuideSec.hidden = false;
          var uName = lang === "en" ? (UNI.nameEn || UNI.nameTr) : UNI.nameTr;
          var titleEl = document.getElementById("noGuideTitle");
          if (titleEl) titleEl.textContent = I18N_GUIDE[lang].noGuideTitle.replace("{name}", uName);
          var msgEl = document.getElementById("noGuideMsg");
          if (msgEl) msgEl.textContent = I18N_GUIDE[lang].noGuideMsg;
          var agrLink = document.getElementById("noGuideAgrLink");
          if (agrLink) {
            agrLink.href = "agreements.html?uni=" + encodeURIComponent(UNI.id);
            agrLink.textContent = I18N_GUIDE[lang].goToAgreements;
          }
        }
      }
    } else if (UNIS) {
      if (hero) hero.hidden = true;
      if (t3) t3.textContent = "";
      document.title = I18N_GUIDE[lang].titleDefault;

      if (missingUniSec) {
        missingUniSec.hidden = false;
        var hTitle = document.getElementById("missingTitle");
        if (hTitle) {
          hTitle.textContent = UNI_ID
            ? I18N_GUIDE[lang].unknownUni.replace("{0}", UNI_ID)
            : I18N_GUIDE[lang].missingUni;
        }
        var pPick = document.getElementById("missingPick");
        if (pPick) pPick.textContent = I18N_GUIDE[lang].pickUni;

        var listEl = document.getElementById("missingUniList");
        if (listEl) {
          listEl.innerHTML = UNIS.map(function (u) {
            var name = lang === "en" && u.nameEn ? u.nameEn : u.nameTr;
            var target = u.hasGuide ? ("guide.html?uni=" + encodeURIComponent(u.id)) : ("agreements.html?uni=" + encodeURIComponent(u.id));
            return '<li><a href="' + target + '">' + esc(name) + ' (' + esc(u.abbr) + ')</a></li>';
          }).join("");
        }
      }
    }
  }

  function apply() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-tr]").forEach(function (el) {
      var v = el.getAttribute("data-" + lang);
      if (v == null) return;
      if (el.hasAttribute("data-html")) el.innerHTML = v; else el.textContent = v;
    });
    document.querySelectorAll(".lang-toggle button").forEach(function (b) {
      b.classList.toggle("active", b.dataset.lang === lang);
    });

    var cu = "burhanarikan", caddr = cu + "@" + "yaani" + ".com";
    var cl = document.getElementById("contactLine");
    if (cl) {
      cl.innerHTML = "";
      cl.appendChild(document.createTextNode(I18N_GUIDE[lang].feedbackPrefix));
      var ca = document.createElement("a");
      ca.href = "mail" + "to:" + caddr;
      ca.textContent = caddr;
      cl.appendChild(ca);
      // Koşulsuz kaldırma sözü · KAYNAK.md'de yazılıydı ama SİTEDE
      // görünmüyordu. Kurumun okuyacağı yer burası, depo değil.
      var soz = document.createElement("span");
      soz.className = "removal-promise";
      soz.textContent = " · " + I18N_GUIDE[lang].removalPromise;
      cl.appendChild(soz);
    }
    renderView();
  }

  document.querySelectorAll(".lang-toggle button").forEach(function (b) {
    b.addEventListener("click", function () {
      lang = b.dataset.lang;
      try { localStorage.setItem("atlas-lang", lang); } catch (e) {}
      apply();
    });
  });

  fetch("universities.json")
    .then(function (r) { return r.json(); })
    .then(function (unis) {
      UNIS = unis;
      UNI = UNI_ID
        ? unis.find(function (u) { return u.id === UNI_ID; })
        : (unis.find(function (u) { return u.hasGuide; }) || unis[0]);
      apply();
    })
    .catch(function () {
      apply();
    });
})();
