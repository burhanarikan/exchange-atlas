# Katkı

Bu projeye üç ayrı yerden katkı gelebiliyor ve **üçünün yolu farklı.** Aşağıda
kendinizi bulun.

---

## Üniversite personeliyseniz

Veriniz burada nasıl okunuyor, hangi kararlar sizin adınıza **verilmedi**, hangi
farklar kartlarda iz bırakıyor · hepsi tek belgede:
[`KAYNAK.md`](KAYNAK.md).

**Kod bilmek gerekmiyor.** Bu belge sizin için yazıldı.

| İstediğiniz | Ne yapın |
|---|---|
| Veriniz kaldırılsın | Yazın · **tartışmasız kaldırılır**, gerekçe sorulmaz |
| Bir kayıt yanlış görünüyor | [`KAYNAK.md §4`](KAYNAK.md#4--bir-şey-yanlışsa) · hangi satır, doğrusu ne |
| Listeniz güncellendi | Yeni listenin bağlantısını gönderin |
| Üniversiteniz eklensin | [Kurum talebi şablonu](.github/ISSUE_TEMPLATE/kurum-talebi.md) |

Düzeltme talepleri sıraya girmeden işleniyor. Bu gönüllü yürüyen bir çalışma,
o yüzden *"anında"* demiyoruz · **talebi aldığımızı ve ne zaman işleyeceğimizi
yazılı bildiriyoruz.** İşlememeye karar verirsek sebebini de yazıyoruz.

---

## Öğrenciyseniz ya da siteyi kullanıyorsanız

| Ne gördünüz | Nereye |
|---|---|
| Bir kayıt yanlış | Issue açın · hangi kart, ne yanlış |
| Bir yer anlaşılmıyor | [Anlaşılmayan yer şablonu](.github/ISSUE_TEMPLATE/anlasilmayan-yer.md) |
| Site bir yerde bozuk | Issue · hangi tarayıcı, hangi sayfa |

**"Anlaşılmayan yer" bildirmek gerçek bir katkı** ve kod bilmeyi gerektirmiyor.
Bir cümleyi anlamadıysanız **sizin eksiğiniz sayılmıyor, metnin eksiği
sayılıyor** · bu projenin başarı ölçütü tam olarak bu.

---

## Kod yazacaksanız

### Bu depoda dört kural var

**1 · Dil.** Kod ve tanımlayıcılar İngilizce, satır yorumları (`#`, `//`)
İngilizce, belge dizgileri (docstring) **Türkçe.** Ayrım keyfi değil: Satır
yorumu kodun ne yaptığını söylüyor ve kodun dilinde duruyor; belge dizgisi
**neden öyle olduğunu** söylüyor ve gerekçe arayan kişiye yazılıyor.

**2 · Kaynak veri depoya girmiyor.** Üniversitelerin Excel dosyaları `lokal/`
altında duruyor. Sebep hukuki değil, sahiplikle ilgili: Veriyi biz üretmiyoruz
ve yeniden yayımlamıyoruz · okuyup düzenlediğimiz hâli yayımlıyoruz.

**3 · Gizli anahtar yok ve bu bir karar.** API anahtarı, token, parola
kullanılmıyor. Site tümüyle statik. Bir gün gerekirse tartışılır, sessizce
eklenmez.

**4 · Dış istek yok.** Yazı tipleri yerel, harita yok, analitik yok, gömülü
içerik yok. Yeni bir dış bağımlılık bu ilkeyi bozar. Rehberdeki bağlantılar
kullanıcının tıkladığı `<a href>` bağlantıları · kaynak yüklemesi değil.
Denetimi `tests/test_site.py::DisIstekYasagi`.

### Önce okuyun

Bir denetimi değiştirmeden önce **belge dizgisini** okuyun. `tests/` altındaki
sınıflar kısa açıklamalar değil, o bekçinin hangi somut arızadan doğduğunu
anlatan kayıtlar taşıyor · çoğu bir kez gerçekten yaşanmış bir hatayı yazıyor.

### Değiştirdikten sonra

```bash
python3 -m unittest discover -s tests
```

Kurulum yok, bağımlılık yok, ağ yok. Hepsi geçmeli.

### Yeni bir denetim yazdıysanız

**Bilerek bozarak sınayın** · kırıldığını ve hata mesajının doğru yeri
gösterdiğini görün, sonra geri alın. Geçen bir test, yakalayan test demek
değil: Yeni yazılmış bir denetim ilk çalıştırmada yeşil yanıyorsa, ya sorun
yoktur ya da denetim boştur · ikisini ayırmanın yolu onu bir kez kırmak.

### Belgeye dokunduysanız

- Bir sayı yazacaksanız **sayarak** yazın
- Türkçe metinde uzun çizgi (—) kullanılmıyor · TDK
- Yerleşik olmayan bir terim kullandıysanız yanında **kaynağını** yazın ·
  yerleşik mi, bizim adlandırmamız mı

### Commit ve pull request

Commit mesajı değişikliğin **nedenini** açıkça taşımalı. Kısa bir biçim kullanmak
isterseniz `feat:`, `fix:`, `docs:`, `test:` ve `chore:` öneklerinden birini seçin;
araç veya üretim yöntemi commit mesajına yazılmak zorunda değildir.

Pull request açarken değişikliğin etkisini, veri kaynağını ve çalıştırdığınız testleri
belirtin. Depodaki [pull request şablonu](.github/PULL_REQUEST_TEMPLATE.md) bu
kontrolleri hatırlatır. Anlamlı kullanıcı veya bakım değişiklikleri ayrıca
[`CHANGELOG.md`](CHANGELOG.md)'ye eklenebilir; veri yenilemelerinin teknik künyesi
[`site/kaynak-kunyesi.json`](site/kaynak-kunyesi.json)'da tutulur.

---

## Veri hakkında

Anlaşma verisi bize ait değil · üniversitelerin kamuya açık listelerinden
derlendi. Ne aldığımız [`KAYNAK.md §1`](KAYNAK.md#1--tablonuzdan-ne-okuyoruz)'de,
sizin adınıza hangi kararları verdiğimiz
[`§3`](KAYNAK.md#3--okurken-verdiğimiz-kararlar)'te, neyi bilerek
düzeltmediğimiz [`§6`](KAYNAK.md#6--neyi-düzeltmiyoruz)'da. Lisans sınırları
[`NOTICE.md`](NOTICE.md)'de.

**Kaynak dosyalar depoya girmiyor** (yukarıdaki 2. kural). Yerine künyesi
giriyor: [`site/kaynak-kunyesi.json`](site/kaynak-kunyesi.json)
· hangi dosyadan üretildiği, özeti, indirme tarihi ve yeniden üretim adımları.

---

## Güvenlik

Site tümüyle statik · sunucu yok, veritabanı yok, çerez yok, dış istek yok ve
gizli anahtar yok. Saldırı yüzeyi düz dosyalardan ibaret.

Yayımlanan veriye kişisel bilgi girmemesi için ayrı bir karar var ve gerekçesi
[`KAYNAK.md §5`](KAYNAK.md#5--kişisel-veriyi-neden-okumuyoruz)'te · denetimi
`tests/test_veri.py::KisiselVeri`.

Yine de bir şey görürseniz **genel bir issue açmadan önce doğrudan yazın.**
Adres [`README.md`](README.md)'de.

---

## Ne yapılmaması rica ediliyor

| Ne | Neden |
|---|---|
| `site/data-*.json` dosyasını elle düzenlemek | Üretilen dosya · düzeltme kaynakta yapılır, yoksa ilk derlemede kayboluyor |
| Dış bağımlılık eklemek | Sıfır dış istek bu projenin mimari kararı |
| Bekçiyi susturmak | Yanlış alarm veriyorsa **daralt**, kaldırma |
| Gerekçesiz muafiyet | Muafiyet listeleri gerekçe istenmediğinde susturma yerine dönüşüyor |
