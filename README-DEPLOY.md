# Exchange Atlas · yayın ve canlı doğrulama

Bu belge, `site/` klasörünün Cloudflare Pages üzerinde güvenli biçimde yayımlanması ve canlı yayın sonrasında doğrulanması için uygulanacak kontrolleri tanımlar. Site statiktir: sunucu tarafında çalışacak bir uygulama, veritabanı veya kullanıcı formu yoktur. Buna rağmen güvenlik başlıkları, TLS/DNS ve gerçek tarayıcı yanıtı ayrıca doğrulanmalıdır.

## 1. Yerel kalite kapısı

Yayın öncesi kök dizinde şu komutların ikisi de hatasız tamamlanmalıdır:

```bash
python3 -m unittest discover tests
python3 -m unittest discover -s tests
```

Ardından yayın paketinde yalnızca `site/` içeriğinin yer alacağı kontrol edilir:

```bash
find site -type f -not -path '*/.git/*' -print | sort
```

Kaynak Excel dosyaları ve kişisel iletişim bilgileri yayın paketine alınmaz. Veri yenilendiyse `site/kaynak-kunyesi.json` içindeki kaynak tarihi, özet bilgisi ve SHA-256 değeri de güncellenir.

## 2. Cloudflare Pages yayın koşulu

Kanonik yayın Cloudflare Pages üzerindedir. Cloudflare projesi GitHub'daki `main` dalına bağlıdır; her push sonrasında `site/` klasörü build output olarak yayımlanır. Framework kullanılmadığı için build command boş bırakılır, root directory `/`, output directory `site` olur.

GitHub Actions workflow'u test işini her push ve pull request'te çalıştırır. Eski GitHub Pages yolu yalnız `PAGES_ENABLED=true` açıkça ayarlanırsa çalışır; kanonik Cloudflare yayında bu değişken `false` bırakılır veya tanımlanmaz. Beklenen CI durumu `test: success`, legacy `deploy: skipped` ve canlı adres tanımlıysa `live_check: success` değeridir.

Canlı response header doğrulaması için repository variable olarak şu adres tanımlı olmalıdır:

```bash
gh variable set LIVE_SITE_URL --body https://exchangeatlas.org -R burhanarikan/exchange-atlas
```

`LIVE_SITE_URL` tanımlandığında workflow ana route'ları, üç üniversite listesini ve MAKÜ rehberini gerçek HTTP yanıtları üzerinden kontrol eder. Cloudflare Pages `_headers` dosyasını parse ederek güvenlik başlıklarını canlı yanıta ekler; başlıklar görünmüyorsa yayın güvenli kabul edilmez.

## 3. Gerçek HTTP response header'ları

HTML içindeki meta CSP, tarayıcı içeriği için ek bir savunmadır; `frame-ancestors` meta etiketiyle güvenilir biçimde uygulanmaz. Aşağıdaki başlıklar seçilen edge/proxy/barındırma katmanından **gerçek response header** olarak gönderilmelidir:

```http
Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'self'; form-action 'none'; base-uri 'none'; frame-ancestors 'none'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

`Strict-Transport-Security` yalnızca alan adı ve dahil edilen bütün alt alan adları HTTPS ile çalışıyorsa gönderilmelidir. `preload` bu ilk yayında eklenmez; geri alınması daha zor bir taahhüttür.

GitHub Pages'te proje dosyasına bir `_headers` dosyası eklemek, GitHub'ın kendi Pages sunucusunda bu başlıkların kesin olarak gönderileceği anlamına gelmez. GitHub Pages kullanılıyorsa önce gerçek yanıtlar kontrol edilir. Başlıklar yoksa Pages'in önüne bu özelliği sağlayan bir reverse proxy/edge katmanı konur veya başlık destekleyen statik barındırmaya geçilir. `_headers` biçimini destekleyen bir sağlayıcı seçilirse `site/_headers` dosyası aşağıdaki gibi tutulabilir:

```text
/*
  Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'self'; form-action 'none'; base-uri 'none'; frame-ancestors 'none'
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## 4. DNS ve TLS

Özel alan adı yönlendirmesi tamamlandıktan sonra aşağıdaki durumlar doğrulanır:

```bash
curl -sS -D - -o /dev/null https://exchangeatlas.org/
curl -sS -D - -o /dev/null https://exchangeatlas.org/
curl -sS -D - -o /dev/null 'https://exchangeatlas.org/agreements?uni=maku'
curl -sS -D - -o /dev/null 'https://exchangeatlas.org/guide?uni=maku'
curl -sS -D - -o /dev/null http://exchangeatlas.org/
```

Beklenen sonuçlar şunlardır: HTTPS istekleri `200` veya platformun normal cache yanıtıyla birlikte başarılı olmalı; HTTP isteği `301` ya da `308` ile HTTPS'e yönlenmeli; sertifika alan adıyla eşleşmeli; sertifika süresi geçerli olmalı; response body içinde beklenmeyen bir sağlayıcı hata sayfası olmamalıdır.

DNS tarafında hem apex alan adı hem de kullanılan `www` varyantı tek bir kanonik adrese yönlenmeli. `site/CNAME`, canonical URL, Open Graph URL'leri, `robots.txt` ve `sitemap.xml` aynı kanonik alan adını göstermelidir.

## 5. Header doğrulama

Her ana route'ta başlıklar tek tek kontrol edilir:

```bash
for url in \
  'https://exchangeatlas.org/' \
  'https://exchangeatlas.org/' \
  'https://exchangeatlas.org/agreements?uni=maku' \
  'https://exchangeatlas.org/agreements.html?uni=marmara' \
  'https://exchangeatlas.org/agreements.html?uni=esogu' \
  'https://exchangeatlas.org/guide?uni=maku'; do
  echo "--- $url"
  curl -sS -D - -o /dev/null "$url" | grep -Ei '^(HTTP/|content-security-policy:|x-frame-options:|x-content-type-options:|referrer-policy:|permissions-policy:|strict-transport-security:)'
done
```

Kabul kriteri: `Content-Security-Policy` içinde `frame-ancestors 'none'`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` ve `Referrer-Policy: strict-origin-when-cross-origin` her route'ta bulunur. Başlık yalnızca `index.html` üzerinde değil, hata yanıtları ve route varyantları üzerinde de kontrol edilir.

`frame-ancestors` testi için sayfayı başka bir origin'deki iframe içine yerleştirme denemesi yapılır; tarayıcı sayfayı göstermemelidir. `X-Content-Type-Options` için JavaScript, CSS, JSON ve SVG dosyalarının `Content-Type` değerleri de kontrol edilir.

## 6. Mixed content ve üçüncü taraf istekleri

Yayın alan adı HTTPS olduktan sonra şunlar kontrol edilir:

```bash
grep -RInE 'http://|//[^/]' site --exclude='*.json'
grep -RInE 'https?://|fetch\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon|import\(' site --exclude='*.json'
```

Resmî üniversite bağlantıları kullanıcı tıklamasıyla açılan dış bağlantılar olabilir; sayfa açılışında otomatik dış istek olmamalıdır. Tarayıcı geliştirici araçlarında Network paneli açıkken ana sayfa, üç anlaşma sayfası ve MAKÜ rehberi yenilenir; üçüncü taraf otomatik istek veya mixed-content uyarısı bulunmamalıdır.

## 7. Manuel smoke-test

Yayınlanan adres üzerinde masaüstü ve mobil görünümde şu akışlar tamamlanır:

- Ana sayfada üç üniversite kartı, anlaşma sayısı ve veri üretim tarihi görünür.
- MAKÜ, Marmara ve ESOGÜ listeleri doğru `uni` parametresiyle açılır.
- Bölüm/üniversite/ülke araması, ülke filtresi, derece filtresi, kontenjan filtresi, temizleme ve “daha fazla göster” çalışır.
- Alan kodu olmayan Marmara ve ESOGÜ listelerinde boş filtre yerine açıklayıcı metin görünür.
- Sonuç bulunamadığında boş durum mesajı ve aktif filtreleri temizleme yolu anlaşılır.
- TR/EN geçişi; başlık, arama placeholder'ı, filtreler, kartlar, kaynak uyarısı ve footer'da tutarlı kalır.
- Kaynak üniversite bağlantısı, karttaki partner bağlantısı ve geri bildirim e-postası doğru hedefe gider.
- Klavye ile tüm düğmelere/bağlantılara ulaşılır; odak göstergesi görünür; mobil filtre paneli açılıp kapatılır.
- JavaScript kapalıyken ana sayfa neden üniversite listesinin görünmediğini, anlaşma sayfası neden listenin oluşturulamadığını açıklar.
- Rehberde MAKÜ için **yayımlanan 468** kayıt bilgisi ve kaynakta kurum tarafından silinen satırın neden dahil edilmediği görünür.

## 8. Yayın sonrası ilk kontrol

Deploy tamamlandıktan hemen sonra workflow sonucu, özel alan adı, HTTPS yönlendirmesi ve header komutları tekrar çalıştırılır. İlk birkaç saat içinde kaynak bağlantılarının durum kodları ve tarayıcı konsolu kontrol edilir. Bir üniversite kendi verisiyle ilgili düzeltme veya kaldırma talebi gönderirse talep kaynağı doğrulanır, kayıt güncellenir ve yeni veri üretimiyle birlikte testler tekrar çalıştırılır.

Yayının canlı olması, anlaşma bilgilerinin başvuru dönemi için kesin veya bağlayıcı olduğu anlamına gelmez. Kullanıcıya her zaman kurumun güncel resmî listesini esas alması gerektiği gösterilmelidir.


## 9. Cloudflare Pages ile kanonik yayın

GitHub Pages response header'ları uygulamıyorsa Cloudflare Pages kanonik yayın katmanı olarak kullanılabilir. Cloudflare dashboard'da **Workers & Pages > Create application > Pages > Connect to Git** akışından `burhanarikan/exchange-atlas` deposunu bağlayın. Production branch `main`, Root directory `/`, Build command boş ve Build output directory `site` olmalıdır. Framework seçmeyin; proje doğrudan statik HTML'dir.

Pages projesi oluşturulduktan sonra **Custom domains > Set up a domain** üzerinden `exchangeatlas.org` alan adını ekleyin. Apex alan adı kullanıldığı için domain Cloudflare hesabında zone olarak bulunmalı ve nameserver'lar Cloudflare'a yönlenmelidir. Cloudflare, custom domain ilişkilendirmesi tamamlandıktan sonra sertifika ve DNS durumunu dashboard'da gösterir. Sadece DNS'e elle CNAME eklemek custom domain ilişkilendirmesinin yerine geçmez.

Cloudflare Pages'te `site/_headers` dosyası build output içinde parse edilir. GitHub Actions tarafında eski GitHub Pages yolunu kapatmak için `PAGES_ENABLED=false` bırakılabilir; `LIVE_SITE_URL=https://exchangeatlas.org` tanımlandığında `live_check`, GitHub Pages deploy'undan bağımsız olarak test işinden sonra kanonik Cloudflare adresini kontrol eder. Beklenen sonuç `test: success`, `deploy: skipped` ve Cloudflare yayınlandıktan sonra `live_check: success` durumudur.
