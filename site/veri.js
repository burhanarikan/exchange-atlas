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
    return fetch(url).then(function (res) {
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
})(window);
