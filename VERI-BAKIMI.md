# Veri bakımı ve yeni üniversite ekleme

Üniversite kaydı [`config/universities.json`](config/universities.json) içinde,
ayrıştırıcılar [`scripts/build_data.py`](scripts/build_data.py) içindedir.
Kaynak Excel dosyaları yalnız `lokal/` altında tutulur; yayımlanmaz.

## Kaynakları yenileme

Önce bağımlılığı kurun; testlerde JavaScript davranışı için Node.js de gerekir:

```bash
python3 -m pip install -r requirements.txt
```

Önce değişiklikleri görün. Bu komut kaynakları indirir ve ayrıştırır, ancak
kaynak kopyalarını ve siteyi değiştirmez. `--report` yalnız istenen raporu yazar:

```bash
python3 scripts/build_data.py --pull --dry-run --report /tmp/atlas-kaynak-raporu.json
```

Raporda eski/yeni kayıt sayısı, dosya özetinin değişip değişmediği, eklenen ve
çıkarılan satır sayıları bulunur. Bir satırın içeriği değişmişse bir çıkarma ve
bir ekleme olarak sayılır. Sayıların aynı kalması verinin aynı kaldığı anlamına
gelmez; dosya özeti ve satır içerikleri de karşılaştırılır.

Tek kurumu güncellemek veya yeni kurumu sınamak için:

```bash
python3 scripts/build_data.py --pull --university marmara --dry-run
python3 scripts/build_data.py --pull --university marmara
```

Bütün kurumları güncellemek için:

```bash
python3 scripts/build_data.py --pull
python3 -m unittest discover tests
python3 -m unittest discover -s tests
node --check site/app.js
node --check site/home.js
node --check site/veri.js
git diff --check
```

Bir kaynak indirilemezse, birden fazla Excel adayı bulunursa, ayrıştırıcı boş
liste üretirse veya gerekli alanlar bozulursa işlem durur. Tüm seçili kurumlar
hazırlanmadan kaynak/site dosyaları yazılmaz. Eski dosya sessizce kullanılıp
canlı kaynaktan alınmış gibi işaretlenmez. Dosyaya yazma sırasında oluşabilecek
disk hataları için yayın öncesinde testler ve `git diff` yine kontrol edilir.

`--pull` olmadan üretim, yalnız künyedeki SHA-256 ile eşleşen yerel kopyayı
kullanır. Kaynak kontrol tarihi ilerlemez. Yeni bir yerel dosya getirmek yerine
resmî kaynağı kurum kaydında tanımlayıp `--pull` kullanın.

Kaynak yenilendiğinde `README.md`, `KAYNAK.md` ve `site/llms.txt` içindeki
sayıları ve kaynak okuma kararlarını da gözden geçirin. Testler bilinen kaynak
sayılarında değişiklik bulduğunda, gerçek dosyayla karşılaştırmadan beklenen
sayıyı değiştirmeyin. Yayın adımları [`README-DEPLOY.md`](README-DEPLOY.md)'dedir.

## Tarihlerin anlamı

- `sourceDownloadedAt` / `indirme_tarihi`: kullanılan dosya sürümünün alındığı gün.
  Aynı dosya yeniden indirildiğinde bu tarih korunur.
- `sourceCheckedAt` / `son_kontrol_tarihi`: resmî kaynağın başarıyla indirilip
  ayrıştırıldığı son gün. Yerel yeniden üretim bunu değiştirmez.
- `generatedAt`: JSON dosyasının üretildiği an; kaynak güncelliğinin kanıtı değildir.
- `sourceSha256` / `sha256`: kullanılan Excel'in özeti; arşiv kullanılıyorsa
  arşivin değil, içindeki Excel'in özetidir.

Ana sayfa ve anlaşma sayfası kaynak kontrolünü gösterir. Kontrol tarihi yoksa
kaynağın alındığı tarih kullanılır ve bu açıkça etiketlenir. Tarih bilinmiyorsa
veya 30 günden eskiyse kullanıcıya resmî listeyi yeniden kontrol etmesi söylenir.
Bu süre bir bakım eşiğidir; anlaşmanın geçersiz olduğu anlamına gelmez.

En az ayda bir önizleme, inceleme, yenileme ve yayın döngüsünü uygulayın.
Başvuru döneminden önce ayrıca kontrol edin. Kurum dosyayı değiştirmese bile
başarılı yenileme kaynak kontrol tarihini kaydeder.

## Bakımda korunan sözler

Kaynak kontrolü bakımcının makinesinde yürütülür. İleride düzenli kontrol
kurulursa aynı sınır korunur: kontrol raporu hazırlanır, değişiklikler incelenir
ve yayın ayrı adımda yapılır. Şu anda zamanlanmış kontrol kurulmuş değildir.
Siteye sunucu uygulaması, gizli anahtar, analitik veya çalışma anında dış
istek eklenmez. Ham kaynak dosyaları ve kişisel iletişim sütunları yayımlanmaz.

Kaynağın kontrol edilmiş olması başvuru, kontenjan veya kabul garantisi vermez.
Kaynak atfı, okuma kararlarının karttaki açıklamaları ve kurumların gerekçe
sorulmadan kaldırma hakkı yeni kurumlarda da korunur. Kaldırılan bir kurum
sonraki kaynak yenilemesiyle kendiliğinden yeniden eklenmemelidir.

## Yeni üniversite ekleme

1. Kurumun resmî Erasmus+ anlaşma sayfasını ve kamuya açık Excel'ini bulun.
   Liste hangi programa, öğrenci/personel hareketliliğine ve döneme ait, doğrulayın.
2. `config/universities.json` içine benzersiz küçük harfli `id`, iki dilde ad,
   kısaltma, kaynak atfı, `listUrl`, `local`, `sheet`, `parser`, `downloadMode`
   alanlarıyla kayıt ekleyin. Örnek olarak Bilecik kaydını kullanabilirsiniz.
   Kaynak yolu `lokal/<id>/...xlsx` olmalı; rehber hazırlanmamışsa `hasGuide: false`.
3. İndirme yöntemini seçin: `page-xlsx`, resmî sayfadaki tek Excel bağlantısını
   bulur; `share-zip`, paylaşım arşivindeki tek Excel'i okur; `direct`, kayıtlı
   `pullUrl` adresini kullanır. Birden çok bağlantı varsa `fileContains` ile
   seçimi açıkça daraltın. Belirsiz adaylar arasından otomatik seçim yapılmaz.
4. Kurumun sütunlarına uygun ayrıştırıcıyı yazıp `load_registry()` içindeki
   izin verilen ayrıştırıcılara ekleyin. Bütün ayrıştırıcılar aynı kayıt şemasını
   üretir. Aynı biçimde bir liste varsa mevcut ayrıştırıcı yeniden kullanılabilir.
5. Kaynaktaki birkaç satırı uçtan uca karşılaştırın: normal satır, boş bölüm,
   ortak kontenjan, lisansüstü/ön lisans, dil şartı, birleştirilmiş hücre ve
   son satır. Kaynakta olmayan dil veya derece bilgisini tahmin etmeyin.
   Kişi adları ve iletişim sütunlarını okumayın.
6. `python3 scripts/build_data.py --pull --university <id> --dry-run` ile farkı
   inceleyin; ardından aynı komutu `--dry-run` olmadan çalıştırın. Künye,
   üniversite kartı ve sitemap kaydı otomatik hazırlanır. Diğer kurumlar değişmez.
7. `KAYNAK.md` içinde okuma kararlarını, `README.md` tablosunda kurum ve sayısını,
   `site/llms.txt` içinde liste bağlantısını ekleyin. Kaynaktaki özel durumlar
   için davranış testi ekleyin; tüm testleri ve TR/EN arama/filtre akışını çalıştırın.

## Bilecik pilotunun sınırları

Resmî dosyanın ilk sayfasında 79 anlaşma grubu, 79 farklı partner adı
ve 207 yayımlanan bölüm/alan satırı bulunur. Sitedeki 207 sayısı satır sayısıdır;
207 ayrı partner veya bağımsız kontenjan anlamına gelmez.

Birleştirilmiş kontenjan hücresi birden fazla satırda görünür ve kartta ortak
olduğu belirtilir. Öğrenci kontenjanı kişi × ay, personel kontenjanı kişi × gün
biçiminde korunur. Birden fazla alan ailesi olan veya standart dışı kod taşıyan
satıra tek bir ISCED ailesi atanmıyor; kaynak alan metni kartta duruyor.
Dil şartı bu dosyada yoktur ve boş bırakılır. Ayrıntılar `KAYNAK.md` içindedir.
