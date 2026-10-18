# Proje Devir Rehberi (Handover)

Bu belge, Exchange Atlas'ın başka bir kişiye, öğrenci topluluğuna veya kuruma devredilmesi durumunda izlenecek adımları açıklar.

## 1. Tek Komutla Kimlik, İletişim ve Depo Devri

Depodaki GitHub depo yolu (`owner/repo`), geri bildirim/kaldırma e-postası (JS içindeki parçalı yazımlar dahil), telif/atıf sahibi ve kanonik alan adı [`scripts/handover.py`](scripts/handover.py) aracıyla tek komutla güncellenir.

Mevcut durumu ve tüm dosyaların tutarlılığını kontrol etmek için:

```bash
python3 scripts/handover.py --check
```

Değişiklikleri dosyaları değiştirmeden önizlemek için (`--dry-run`):

```bash
python3 scripts/handover.py \
  --repo yeni-sahip/exchange-atlas \
  --email iletisim@ornek.edu.tr \
  --author "Yeni Sahip veya Topluluk" \
  --domain exchangeatlas.org \
  --dry-run
```

Değişiklikleri tüm kod, belge, yapılandırma ve test bekçilerine uygulamak için:

```bash
python3 scripts/handover.py \
  --repo yeni-sahip/exchange-atlas \
  --email iletisim@ornek.edu.tr \
  --author "Yeni Sahip veya Topluluk" \
  --domain exchangeatlas.org
```

Bu komut:
- [`site/app.js`](site/app.js), [`site/home.js`](site/home.js) ve [`site/guide.js`](site/guide.js) içindeki bot taramasına karşı parçalı yazılmış e-posta sabitlerini,
- [`README.md`](README.md), [`KAYNAK.md`](KAYNAK.md), [`SECURITY.md`](SECURITY.md), [`CITATION.cff`](CITATION.cff), [`LICENSE`](LICENSE), [`CHANGELOG.md`](CHANGELOG.md) ve [`README-DEPLOY.md`](README-DEPLOY.md) belgelerini,
- [`site/CNAME`](site/CNAME), [`site/robots.txt`](site/robots.txt), [`site/llms.txt`](site/llms.txt), [`site/sitemap.xml`](site/sitemap.xml) ve HTML canonical/OG etiketlerini,
- [`tests/test_yayin.py`](tests/test_yayin.py) ve [`tests/test_site.py`](tests/test_site.py) içindeki bekçileri (kurumsal e-postaya geçildiyse kişisel sağlayıcı muafiyet listesini boşaltmak dahil),
- Statik JS/CSS önbellek sürüm özetlerini (`?v=<hash>`)

atomik olarak günceller.

## 2. Veri Hattını Devralma (`lokal/` Klasörü Gerekmez)

`lokal/` klasöründeki ham Excel dosyaları kişisel veri (koordinatör ad/e-posta) ve telif ilkeleri gereği git deposunda tutulmaz ve devir sırasında elden ele gönderilmesi **gerekmez**.

Projeyi devralan kişi, 5 üniversitenin resmî kaynak dosyalarını doğrudan kurumların kendi sayfalarından indirmek için yalnızca şu komutu çalıştırır:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/build_data.py --pull
```

## 3. GitHub ve Yayın Altyapısı Devri

1. **GitHub Depo Devri:**
   - **Settings → General → Danger Zone → Transfer ownership** üzerinden depo yeni kullanıcıya veya organizasyona aktarılır.
   - **Settings → Secrets and variables → Actions → Variables** altında `LIVE_SITE_URL` (`https://exchangeatlas.org`) ve gerekiyorsa `PAGES_ENABLED` (`false` / `true`) değerleri kontrol edilir.
   - Haftalık salt-okunur kaynak tazelik denetimi ([`.github/workflows/source-check.yml`](.github/workflows/source-check.yml)) yeni depoda **Actions** sekmesinden etkinleştirilir.

2. **Cloudflare Pages ve Alan Adı (`exchangeatlas.org`):**
   - Cloudflare Pages projesi yeni GitHub deposuna bağlanır (`Production branch: main`, `Build command: boş`, `Build output directory: site`).
   - **Gizlilik kuralı:** Cloudflare Web Analytics / Rum beacon enjeksiyonu **kapalı** tutulmalıdır. Canlı doğrulama işi ([`.github/workflows/pages.yml`](.github/workflows/pages.yml)) sayfaya üçüncü taraf betik enjekte edilirse derlemeyi bilinçli olarak kırar.

## 4. Devir Sonrası Doğrulama Kapısı

Devir tamamlandıktan sonra commit atmadan önce aşağıdaki komutların tamamı sıfır hatayla geçmelidir:

```bash
python3 scripts/handover.py --check
python3 scripts/version_assets.py --check
python3 -m unittest discover -s tests -v
git diff --check
```
