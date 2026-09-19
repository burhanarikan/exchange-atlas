/* JSON yükleme · üç sayfa betiği de buradan geçiyor.

   Neden ortak dosya: Aynı politikanın üç kopyası (app.js, guide.js, home.js)
   zamanla birbirinden ayrılırdı ve ayrıldığı gün bir sayfa korunurken öteki
   sessizce korumasız kalırdı. Politika tek yerde duruyor.

   Neden `res.ok` YETMİYOR · ölçüldü: Yayın ortamı bilinmeyen bir adrese
   `404` değil, `200` ve `text/html` dönüyordu (giriş sayfasının kendisi).
   Yani eksik bir veri dosyası istendiğinde `res.ok` DOĞRU oluyor, sonra
   `.json()` anlaşılmaz bir ayrıştırma hatası veriyordu. İçerik türü de
   denetlenince "dosya yok" durumu gerçekten "dosya yok" diye görünüyor.
   `404.html` eklendikten sonra da bu denetim kalıyor: Sunucu davranışına
   güvenmek yerine yanıtın kendisine bakmak, yayın ortamı değişse de
   doğru kalan tek yol. */
(function (global) {
  function atlasJson(url) {
    return fetch(url, { cache: "no-cache" }).then(function (res) {
      if (!res.ok) {
        throw new Error("Veri isteği başarısız · HTTP " + res.status + " · " + url);
      }
      var tur = res.headers.get("content-type") || "";
      if (tur.indexOf("application/json") === -1) {
        throw new Error(
          "Veri adresi JSON döndürmedi · içerik türü: " + (tur || "belirtilmemiş") + " · " + url);
      }
      return res.json();
    });
  }
  global.atlasJson = atlasJson;
  // Freshness is based on the source, never on JSON generation time.
  global.atlasSourceInfo = function (record, lang, today) {
    var en = lang === "en";
    var raw = record.sourceCheckedAt || record.sourceDownloadedAt;
    var time = /^\d{4}-\d{2}-\d{2}$/.test(raw || "") ? Date.parse(raw + "T00:00:00Z") : NaN;
    var now = today == null ? Date.now() : today;
    // Source dates have day precision; allow the builder/visitor timezone gap.
    var valid = Number.isFinite(time) && time <= now + 86400000 && new Date(time).toISOString().slice(0, 10) === raw;
    var stale = !valid || now - time > 30 * 86400000;
    var label = valid ? new Intl.DateTimeFormat(en ? "en-GB" : "tr-TR", {
      day: "numeric", month: "long", year: "numeric", timeZone: "UTC"
    }).format(new Date(time)) : "";
    var prefix = record.sourceCheckedAt
      ? (en ? "Source checked: " : "Kaynak kontrolü: ")
      : (en ? "Source retrieved: " : "Kaynak alındı: ");
    return {
      dateText: valid ? prefix + label : (en ? "Source check date unavailable" : "Kaynak kontrol tarihi bilinmiyor"),
      stale: stale,
      statusText: stale ? (en ? "A new source check is due; consult the official list." : "Kaynağın yeniden kontrolü gerekiyor; resmî listeye bakın.") : ""
    };
  };
})(window);
