# Exchange Atlas · Erasmus

Üniversitelerin Erasmus+ kurumlar arası ikili anlaşmalarını **aranabilir ve
filtrelenebilir** biçimde sunan bağımsız, statik platform. Binlerce satırlık
Excel tablosu yerine: Bölümünü yaz, ülkeni seç, kontenjanı ve dil şartını tek
bakışta gör.

**Canlı site:** [exchangeatlas.org](https://exchangeatlas.org) · **Durum:** yayında.
Depo public ve katkıya açık. Kanonik yayın Cloudflare Pages üzerinde; yayın doğrulama
ve geri dönüş prosedürü [`README-DEPLOY.md`](README-DEPLOY.md)'de yazılıdır.

[![Live site](https://img.shields.io/website?url=https%3A%2F%2Fexchangeatlas.org&label=live%20site)](https://exchangeatlas.org)
[![Quality checks](https://github.com/burhanarikan/exchange-atlas/actions/workflows/pages.yml/badge.svg?branch=main)](https://github.com/burhanarikan/exchange-atlas/actions/workflows/pages.yml)
[![License: MIT](https://img.shields.io/badge/Code-MIT-blue.svg)](LICENSE)

**Hızlı bağlantılar:** [Canlı site](https://exchangeatlas.org) · [Katkı rehberi](CONTRIBUTING.md) · [Güvenlik bildirimi](SECURITY.md) · [Davranış kuralları](CODE_OF_CONDUCT.md) · [Değişiklik günlüğü](CHANGELOG.md) · [Atıf](CITATION.cff)

Şu an platformdaki üniversiteler:

| Üniversite | Anlaşma | Kaynak |
|---|---|---|
| MAKÜ · Burdur Mehmet Akif Ersoy Üniversitesi | 468 | Uluslararası İlişkiler Koordinatörlüğü'nün kamuya açık KA131 listesi |
| MÜ · Marmara Üniversitesi | 785 | Uluslararası İlişkiler Koordinatörlüğü'nün kamuya açık KA131 listesi |
| ESOGÜ · Eskişehir Osmangazi Üniversitesi | 259 | Uluslararası İlişkiler Birimi'nin kamuya açık ikili anlaşma listesi |

Kaynak çekim tarihleri kurum bazında değişir; her dosyanın tarihi, özeti ve yapısı
[`site/kaynak-kunyesi.json`](site/kaynak-kunyesi.json)'da yazılıdır. Üretilen JSON'un
`generatedAt` alanı ise son veri üretim zamanını gösterir.

Yeni üniversiteler topluluk katkılarıyla eklenecek · katkıda bulunmak için [aşağıya](#katkı) bakın.

## Nasıl çalışır

Tamamen statik: sunucu kodu yok, veri tabanı yok, çerez/izleme yok, çalışma
anında dış istek yok (fontlar dahil her şey pakette). Veri, üniversitelerin
kamuya açık Excel listelerinden derleme anında JSON'a çevrilir:

```bash
# canlı kaynaklardan çek ve site/ altındaki json'ları yeniden üret
python3 scripts/build_data.py --pull
```

Cloudflare Pages, `main`'e push sonrasında siteyi otomatik yayımlar. GitHub Actions
workflow'u (`.github/workflows/pages.yml`) testleri, yayın paketi kontrollerini ve
`LIVE_SITE_URL` tanımlıysa kanonik canlı adresin response header doğrulamasını çalıştırır.

## Verisini kullandığımız kurumlar için

Tablonuzdan ne aldığımızı, tabloda ne gördüğümüzü ve sizin adınıza hangi
kararları verdiğimizi anlatan belge: **[`KAYNAK.md`](KAYNAK.md)** · programlama
bilmek gerekmiyor.

Doğrudan ilgili bölüme gidin: [ne okuyoruz](KAYNAK.md#1--tablonuzdan-ne-okuyoruz) ·
[verdiğimiz kararlar](KAYNAK.md#3--okurken-verdiğimiz-kararlar) ·
[bir şey yanlışsa](KAYNAK.md#4--bir-şey-yanlışsa)

## Kurmak

İndirilecek paket, çalıştırılacak derleme yok. `site/` klasörünün **içeriğini**
herhangi bir statik sunucuya (ya da alt dizine) kopyalamak yeterli · bütün
yollar göreli.

Yerelde bakmak için:

```bash
python3 -m http.server 8765 --directory site
```

### Yayın ve bakım kontrolü

Cloudflare Pages kurulumu, gerçek HTTP response header'ları, HTTPS/DNS, canlı smoke-test
ve rollback adımları [`README-DEPLOY.md`](README-DEPLOY.md) belgesinde açıklanır.
Veri yenilemeleri bakımcı makinesinde yapılır; canlıya geçmeden önce iki test keşif
komutu ve `git diff --check` çalıştırılır.

### Bilgi İşlem için güvenlik özeti

| Konu | Durum |
|---|---|
| Sunucu tarafı kod (PHP, Node, Python…) | **Yok** · çalışan süreç yok |
| Veri tabanı | **Yok** · veri, derleme anında üretilen `data-*.json` |
| Kullanıcı girişi, form, sunucuya gönderim | **Yok** · salt okunur |
| Çalışma anında dış istek (CDN, font, analitik) | **Yok** · fontlar dahil her şey pakette |
| Çerez / izleme | **Yok** · yalnız dil tercihi `localStorage`'da |

Saldırı yüzeyi, sunucudaki herhangi bir statik HTML sayfasıyla aynı: Sunucu
diskteki dosyaları `GET` isteğine yanıt olarak gönderiyor, kullanıcıdan gelen
hiçbir girdi sunucuda işlenmiyor ya da diske yazılmıyor.

**Dış istek olmaması denetleniyor** (`tests/test_site.py::DisIstekYasagi`) ·
işaretleme tarafı kadar JavaScript tarafı da: `fetch`, `XMLHttpRequest`,
dinamik `import`, `WebSocket`, `sendBeacon` ve `.src` ataması. Yani üçüncü
taraf tedarik zinciri riski yok.

### Tarayıcı tarafı · CSP

Üç sayfa da katı bir içerik güvenliği politikası taşıyor ve politika **ödün
vermiyor** · ne `unsafe-inline` ne `unsafe-eval`:

```
default-src 'none'; script-src 'self'; style-src 'self';
font-src 'self'; img-src 'self' data:; connect-src 'self';
form-action 'none'; base-uri 'none'
```

Bunu ödünsüz yazabilmek için satır içi betikler ayrı dosyalara taşındı ·
satır içi `<style>` ve `style=` özniteliği zaten hiç yoktu. Dördü de teste
bağlı (`IcerikGuvenligiPolitikasi`): Biri satır içi script eklerse ya da
politikaya `unsafe-inline` koyarsa test kırılıyor.

Pratik sonucu: Veriden gelen bir metin bir gün kaçırılmadan ekrana bassa bile
tarayıcı onu **çalıştırmıyor.** Site bir üniversitenin kendi alan adı altında
dururken bu önemli · orada bir XSS, o alan adına ait çerezlere erişim demek
olurdu.

### Sunucuya konurken · üç HTTP başlığı

CSP `<meta>` ile taşınıyor ama üç şey **yalnız HTTP başlığıyla** çalışıyor.
Barındıran birim şunları ekleyebilir:

```nginx
add_header Content-Security-Policy "frame-ancestors 'none'" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

Birincisi neden `<meta>`'da değil: Tarayıcı `frame-ancestors` yönergesini
`<meta>` ile **yok sayıyor** ve konsola uyarı basıyor · ölçüldü, o yüzden
politikadan çıkarıldı.

Sunucu tarafında betik yürütmeyi kapatmak da istenirse:

```nginx
location /erasmus-atlas/ {
    limit_except GET HEAD OPTIONS { deny all; }
    location ~ \.(php|py|sh|cgi)$ { deny all; }
}
```

Bu satır bir şeyi düzeltmiyor · pakette çalıştırılabilir bir dosya zaten yok.
Yaptığı şey **ileride konulmasını** engellemek.

## Testler

```bash
python3 -m unittest discover tests
```

Kurulum yok, bağımlılık yok, ağ yok. Beş dosya, işlerine göre ayrılmış:

| Dosya | Ne denetliyor |
|---|---|
| `test_veri.py` | Kaynak veri ve üretilen JSON doğru mu |
| `test_site.py` | İki dil, marka, erişilebilirlik, renk, sıfır dış istek |
| `test_belgeler.py` | Belgelerdeki bağlantılar, sayılar ve yazım |
| `test_yayin.py` | Yayın önkoşulları · biri eksikse yayını durdurur |
| `test_acik_kaynak.py` | Public depo belgeleri, şablonları ve bariz gizli anahtar kalıpları |

## Yeni üniversite eklemek

`scripts/build_data.py` içindeki `UNIVERSITIES` listesine kayıt + o
üniversitenin Excel formatı için bir ayrıştırıcı işlev. Giriş sayfası kartı
kendiliğinden gelir.

Veri güncelleme tek komut ve **bakımcının makinesinde** çalışır, sunucuda
değil:

```bash
python3 scripts/build_data.py --pull
```

Çekimden sonra testleri koşturun · `test_veri.py` kaynak verinin bilinen
durumunu sabitliyor, sayılardan biri değişirse kırılıyor.

## Katkı

Ayrıntılı yol: [`CONTRIBUTING.md`](CONTRIBUTING.md) · üniversite personeli,
öğrenci ve kod yazan için üç ayrı bölüm. Davranış kuralları [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md),
güvenlik bildirimleri [`SECURITY.md`](SECURITY.md) ve değişiklik geçmişi [`CHANGELOG.md`](CHANGELOG.md)
içinde tutulur.

Açık kaynak · kod [MIT](LICENSE), veri ve içerik ayrı koşullarda
([`NOTICE.md`](NOTICE.md)). Katkıya açığız:

- **Üniversite personeli / alan uzmanları:** biriminizin güncel listesini
  paylaşın, veriniz için düzeltme-güncelleme talep edin ya da süreç bilgisiyle
  (rehber içerikleri) destek olun · issue ya da e-posta yeterli.
- **Sahadaki problemler:** Değişim programlarıyla ilgili işinizde sizi yoran
  başka bir şey mi var (anlaşma takibi, süre bitimi, nominasyon takvimleri,
  raporlama…)? Anlatın · çözülebilir olanları yol haritasına alalım, birlikte
  tasarlayalım. Bu proje de böyle bir dertten doğdu.
- **Hata / öneri:** issue açın ya da yazın: burhanarikan@yaani.com
- **Yeni üniversite:** üniversitenizin kamuya açık ikili anlaşma listesinin
  linkiyle issue açın, parser'ı birlikte ekleyelim (ya da PR gönderin).
- **PR akışı:** `feat/`, `fix/` önekli branch + kısa açıklama yeterli.

## Önemli notlar

- Exchange Atlas **resmî bir üniversite hizmeti değildir**. Veri ve içerikler
  üniversitelerin kamuya açık kaynaklarından (anlaşma listeleri, resmî sayfa
  ve belgeler) kaynak atfıyla derlenir. Resmî başvuru için üniversitenizin
  Erasmus+ koordinatörlüğüne, uluslararası ilişkiler birimine veya diğer ilgili birime danışın.
- Bir üniversite kendi verisiyle ilgili düzeltme ya da kaldırma talep ederse
  tartışmasız yerine getirilir. Talepler: burhanarikan@yaani.com

## Lisans

[MIT](LICENSE) **yalnız kodu** kapsıyor. Veri ve içerikler ilgili
üniversitelerin kamuya açık kaynaklarından derlenmiştir, sahipleri o
üniversitelerin ilgili birimleridir (her sayfada kaynak atfı yapılır).

Kapsam dışında kalanlar ve sebepleri [`NOTICE.md`](NOTICE.md)'de: Yazı tipleri
(SIL OFL 1.1 altında, MIT altında yeniden lisanslanamaz) ve üniversite verisi
(derleme bizim, anlaşma bilgilerinin kendisi değil).
