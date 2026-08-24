# Yayımladığınız liste bizde nasıl okunuyor

> Bu belge, verisini kullandığımız kurumlar için yazıldı. Programlama bilmek
> gerekmiyor.
>
> Üç soruya cevap veriyor: tablonuzdan **ne alıyoruz**, tabloda **ne gördük** ve
> onu okurken **hangi kararları verdik?**

Exchange Atlas, üniversitelerin kamuya açık olarak yayımladığı Erasmus+ ikili
anlaşma listelerini öğrencinin arayabileceği bir listeye çeviriyor. Veriyi biz
üretmiyoruz. Siz yayımlıyorsunuz, biz okuyup düzenliyoruz.

Bu, bir sorumluluk doğuruyor: Okurken bazı kararlar vermek zorunda kalıyoruz ve o
kararlar öğrencinin gördüğü şeyi değiştiriyor. **Hepsi burada yazılı.**

Şu an platformda **üç kurum** var. Kaynakların indirme tarihleri kurum bazında
değişiyor ve her biri [`site/kaynak-kunyesi.json`](site/kaynak-kunyesi.json)'da
yazılı. Listenizi ilgili tarihten sonra güncellediyseniz sayılar değişmiş olabilir.

| Kurum | Anlaşma | Listenin biçimi |
|---|---|---|
| Burdur Mehmet Akif Ersoy Üniversitesi | 468 | Tek sayfa, 19 sütun |
| Marmara Üniversitesi | 785 | 27 sayfa, fakülte başına bir sayfa |
| Eskişehir Osmangazi Üniversitesi | 259 | Tek sayfa, fakülte blokları hâlinde |

**Üç liste birbirinden çok farklı** ve bu beklenen bir şey · her kurum kendi
tablosunu kendi ihtiyacına göre kuruyor. Aşağıdaki bölümler ayrımları
gösteriyor; sayılar aksi yazmadıkça MAKÜ listesinden.

---

## 1 · Tablonuzdan ne okuyoruz

| Sütun | Başlığınız | Ne yapıyoruz |
|---|---|---|
| C | İkili Anlaşma Yapılan Yükseköğretim Kurumu | Karşı üniversitenin adı olarak gösteriyoruz |
| D | Geçerlilik Süresi | Kartta olduğu gibi yazıyoruz |
| E | Üniversite ID Kodu | Erasmus kodu olarak gösteriyoruz, aramaya da giriyor |
| F | İkili Anlaşma Yapılan Bölüm Ders Alan Kodu (ISCED) | Baştaki kodu ve İngilizce etiketi alıyoruz |
| G | Açıklama | Kontenjan notu olarak gösteriyoruz |
| H | İkili Anlaşma Yapılan Bölüm Ders Alan Kodu (ISCED) | Bölüm adı olarak gösteriyoruz |
| I | Ders Alan Kodu | ISCED kodu olarak okuyoruz |
| J | Eğitim Dili | Kartta dil şartı olarak gösteriyoruz |
| K | Öğrenim Kademesi (EQF) | Ön lisans / lisans / yüksek lisans / doktora rozetlerine çeviriyoruz |
| L | Ülke | Filtrede ülke olarak kullanıyoruz |
| M, N, O, P | Kontenjanlar | Öğrenim ve personel kontenjanı olarak gösteriyoruz |
| Q, R | İmzalayan, e-posta | **Okumuyoruz** · aşağıda [§6](#6--neyi-düzeltmiyoruz) |
| S | İmzalandığı Tarih | Okumuyoruz |

**Kaynak tablonuza hiç dokunmuyoruz.** Ama gösterirken bazı yerlerde ondan
ayrılıyoruz ve bunu saklamak doğru olmaz. Bugün dört yerde ayrılıyoruz:

| Ne yapıyoruz | Kaç yerde |
|---|---|
| Satırı hiç göstermiyoruz (üstü çizili) | 1 |
| Ülkeyi Erasmus kodundan düzeltiyoruz | 4 |
| Ülkeyi Erasmus kodundan tamamlıyoruz | 2 |
| Bir öğrenim kademesini düşürüyoruz (yanında "iptal" yazdığı için) | 1 |
| Bölüm adının başındaki kodu ayırıyoruz (ad temiz görünsün diye) | çoğu satır |
| Üç haneli kodu dört haneye tamamlıyoruz (baştaki sıfır varsayımı) | 6 |

Her birinin gerekçesi [§3](#3--okurken-verdiğimiz-kararlar)'te yazılı.

> **Bu ayrımlar öğrenciye görünüyor.** Kaynaktan ayrıldığımız kayıtların
> kartında bir satır duruyor ve ne yaptığımızı söylüyor:
>
> *"Kaynak listede ülke Romanya yazıyor, Erasmus kodu bu ülkeyi gösterdiği için
> düzeltildi."*
>
> Bugün yedi kartta görünüyor. Gizlemek, "veriyi üniversiteden çekiyoruz"
> iddiasıyla çelişirdi: Çekiyoruz, ama okurken bazı kararlar veriyoruz.
>
> **Bir ayrımın izi bilerek yok:** Bölüm adının başındaki kodun ayrılması. 465
> kartta olurdu ve gürültü yaratırdı. Ayrıca gösterilen bilgiyi değiştirmiyor,
> kod zaten ayrı bir rozet olarak duruyor. Kararın kendisi burada yazılı olsun
> diye söylüyoruz.

Her sayfada kaynak olarak biriminiz yazılı.

---

## 2 · Tabloda gördüklerimiz

Aşağıdakiler, tabloyu okurken karşılaştığımız durumlar. Her biri için ne
yaptığımız yazılı ve **hiçbiri sistemi durdurmuyor**, liste bugünkü hâliyle
çalışıyor.

Yazılı olmalarının sebebi şu: Her biri bizi bir karar vermeye zorluyor.
Düzeltilirlerse o kararların yerini sizin yazdığınız alır, yani öğrencinin
gördüğü şey doğrudan sizden gelir.

### 2.1 · Alan kodu üç sütunda ve `Ders Alan Kodu` sütunu çoğu satırda boş

Aynı ISCED kodu üç yerde geçiyor: `F` ve `H` sütunlarında bölüm adının önünde
(`0610-Bilgisayar Mühendisliği`), bir de ayrı `Ders Alan Kodu` sütununda.

**Ölçüm:** 468 satırın **246'sında** `Ders Alan Kodu` sütunu boş. Bu 246 satırın
**245'inde** kod bölüm adının önünde duruyor. Yalnız bir satırda hiçbir yerde yok.

Dolu olduğu yerlerde de bazen kısalıyor: `0610` yerine `061` yazılı. Bunun sebebi
büyük olasılıkla Excel'in biçimlendirme davranışı, elle yapılmış bir şey değil.

> **Neden önemli:** Kodu yalnız o sütundan okusaydık 467 anlaşmanın 243'ü alan
> filtresine hiç giremezdi, yani öğrenci "mühendislik" seçtiğinde listenin yarısından
> fazlası görünmezdi.
>
> **Öneri:** Kod tek bir sütunda ve dört haneli tutulursa hem sizin listenizde hem
> bizim tarafımızda belirsizlik kalmıyor. Sütunu Excel'de **metin** olarak
> biçimlendirmek, baştaki sıfırın silinmesini de önlüyor.

### 2.2 · Silinen bir anlaşma tablodan kaldırılmamış

Bir satırda `0914 Medical diagnostic and treatment technology` yazıyor ve yanında
**"SİLDİM LİSTELERDEN"** notu var. Satırın üstü çizilmiş ama satır tabloda duruyor.

Bu satır Powislanska Szkola Wyzsza ile yapılmış, `Acil Yardım ve Afet Yönetimi`
bölümüne ait bir anlaşma.

> **Neden önemli:** Üstü çizili olduğunu ancak biçimlendirmeye bakarak anlıyoruz. Bir
> öğrenci artık geçerli olmayan bir anlaşmaya başvurmaya kalkabilirdi.
>
> **Öneri:** Silinen satırlar tablodan kaldırılırsa ya da ayrı bir "durum" sütunu
> tutulursa, biçimlendirmeye bakmak gerekmez.

### 2.3 · İptal edilen bir öğrenim kademesi serbest metinle yazılmış

Bir satırda öğrenim kademesi şöyle yazılı: `EQF 6 / EQF 7 (EQF 7 İPTAL)`.

WYZSZA SZKOLA INFORMATYKI ile yapılmış, `Sosyal Hizmet` bölümüne ait anlaşma.

> **Neden önemli:** Kademe bilgisini rakamlara bakarak okuyoruz. Parantez içindeki
> iptal notunu ayrıca ayıklamasaydık, yüksek lisans başvurusu açıkmış gibi
> görünecekti.
>
> **Öneri:** İptal edilen kademe satırdan çıkarılırsa not gerekmiyor.

### 2.4 · "dahil" yerine "dalil" yazımı

Kontenjan açıklamalarında **165 kayıtta** `dalil` yazılı, `dahil` olmalı. Muhtemelen
bir kez yazılıp kopyalanmış.

> Bu, gösterimi bozmuyor. Yalnız öğrenci metni okurken tuhaf görünüyor.

### 2.5 · Türkçe bölüm adı olmayan iki satır

İki satırda `H` sütunu boş. Yalnız İngilizce sütun dolu ve orada bölüm adı değil
**ISCED etiketi** yazılı (`Education`, `Education Science`). O iki kartta bölüm adı
olarak bu etiket görünüyor.

| Üniversite | Ülke | Kod | Yazılı olan |
|---|---|---|---|
| University of Patras | Yunanistan | `0111` | `Education Science` |
| Universitatea din Piteşti | Romanya | · | `Education` |

> **Bunu biz çözemeyiz ve sebebi önemli.** `H` sütunu **sizin** bölümünüzü
> yazıyor, karşı üniversitenin değil. Hangi bölümün anlaşması olduğunu ancak siz
> bilirsiniz.
>
> Kodun kendisi de yetmiyor: Tablonuzda `0111` kodu **altı ayrı** MAKÜ bölümüne
> gidiyor (Okul Öncesi Öğretmenliği, Sınıf Öğretmenliği, Eğitim Bilimleri, PDR,
> Özel Eğitim, Rehberlik). Yani tahmin etmek yanlış bir bölüm göstermek olurdu.
>
> **Öteki bulguların çoğunu kendimiz çözebildik, bu ikisini çözemiyoruz.** Ayrım
> şu: Ülke bilgisi tabloda ikinci bir yerde duruyordu, bu duruyor değil.
>
> **Çözemediğimizi artık öğrenci de görüyor.** O iki kartta bölüm adının altında
> şu satır çıkıyor: *"Kaynak listede Türkçe bölüm adı boştu, burada görünen
> alanın ISCED etiketi."* Yani `Education Science` yazan yerin bir bölüm adı
> **olmadığı** yazılı. Bu satır siz `H` sütununu doldurduğunuz gün
> kendiliğinden kalkar.

### 2.6 · Aynı bölüm birçok farklı yazımla girilmiş

Bölüm adları 513 kez yazılmış ve **238 farklı yazım** var. Bunların **18'i** yalnız
büyük/küçük harf farkıyla ayrışıyor:

```
Okul Öncesi Öğretmenliği   ·   Okul Öncesi öğretmenliği
Turizm İşletmeciliği       ·   Turizm işletmeciliği
İnşaat Mühendisliği        ·   İnşaat mühendisliği
```

**Ölçüldü: 468 kaydın 91'i etkileniyor**, yani listenin beşte biri.

> **Aramayı bozmuyor.** Arama metni büyük/küçük harf ve aksan farklarını
> düzleştirdiği için `turizm isletmeciligi` yazan öğrenci ikisini de buluyor.
> Etkilenen tek şey **kartta görünen yazım**: Aynı bölüm iki farklı biçimde
> yazılmış olarak görünüyor.
>
> **Kartta tek bir yazım gösteriyoruz ve seçtiğimiz yazım sizin.** Bir bölümün
> yazımları arasında **en sık kullandığınız** hangisiyse onu gösteriyoruz. Yeni
> bir yazım üretmiyoruz ve hangisinin doğru olduğuna karar vermiyoruz, yalnız
> ağırlıklı kullandığınız biçimi tutarlı hâle getiriyoruz.
>
> Bugün bu, **468 kaydın 22'sinde** bir değişiklik demek. Her birinde kartta şu
> satır çıkıyor: *"Bu bölüm kaynak listede birden çok yazımla geçiyor. Burada en
> sık kullanılan yazım gösteriliyor. Bu kayıtta yazan: …"* Yani öğrenci hem
> tutarlı yazımı görüyor hem sizin o satıra ne yazdığınızı.
>
> **Üç grupta dokunmuyoruz.** İki yazım eşit sıklıktaysa hangisinin ağırlıklı
> olduğunu söyleyecek bir ölçü kalmıyor ve orada seçim yapmak size yazım tercihi
> dayatmak olurdu. Bu üç bölüm kartta iki biçimde görünmeye devam ediyor:
>
> | | |
> |---|---|
> | Bilişim Sistemleri ve Teknolojileri | Bilişim sistemleri ve teknolojileri |
> | Moleküler Biyoloji ve Genetik | Moleküler biyoloji ve genetik |
> | Müzik Teknolojileri | Müzik teknolojileri |
>
> **Tablonuz değişmiyor.** Bu bir gösterim kararı, kaynak listede 18 grubun
> hepsi olduğu gibi duruyor ve düzeltilirse kartlardaki o satır kendiliğinden
> kalkar.

### 2.7 · Dört satırda ülke, Erasmus koduyla çelişiyor

Erasmus kurum kodunun ön eki kurumun ülkesini gösteriyor · listedeki bütün
kodlarda bu böyle. Dört satırda ön ek ile ülke sütunu başka şey söylüyor:

> **Bu bulgunun dayanağı listenin kendisi, resmî bir tanım değil.** Ölçüm şu:
> Listede yirmi farklı ön ek geçiyor ve aşağıdaki dört satır dışında **her
> kayıtta** ön ek ile ülke birbirini tutuyor. Kalıp bu kadar güçlü olunca dört
> istisnanın yazım hatası olduğu sonucuna vardık.
>
> Kodun resmî tanımına bakılmadı ve bu yüzden burada *"kodun tanımının
> parçası"* demiyoruz · demek, doğrulanmamış bir şeyi doğrulanmış gibi yazmak
> olurdu.
>
> Sizin tarafınızdan bakınca bu ayrım önemli olabilir: Aşağıdaki dört satırın
> hangisinin yanlış olduğuna karar verirken, kodu mu ülkeyi mi esas alacağınız
> resmî tanıma bağlı.

| Üniversite | Kod | Ülke sütunu | Kodun söylediği |
|---|---|---|---|
| Latvia University of Life Sciences | `LV JELGAVA01` | Litvanya | **Letonya** |
| Uniwersytet Śląski w Katowicach | `PL KATOWIC01` | Romanya | **Polonya** |
| Universitatea Aurel Vlaicu din Arad | `RO ARAD01` | Polonya | **Romanya** |
| Šiaulių valstybinė kolegija | `LT SIAULIA03` | Romanya | **Litvanya** |

Dördünde de üniversitenin **adı** da kodu doğruluyor: Latvia Letonya'da,
Katowice Polonya'da, Arad Romanya'da, Šiauliai Litvanya'da.

> **Neden önemli:** Bu dört anlaşma öğrenciye **yanlış ülkede** görünüyordu.
> "Romanya" filtresini açan öğrenci bir Polonya ve bir Litvanya üniversitesi
> görüyor, gerçek Romanya anlaşmalarından biri ise listede yok.
>
> **Ne yaptık:** Ön eki esas alıp düzelttik ve düzeltmeyi derleme günlüğüne
> yazdırıyoruz. Kaynağa dokunmuyoruz.

### 2.8 · İki satırda ülke boştu ama koddan okunabiliyordu

`OSTRAVSKA UNIVERZITA` (`CZ OSTRAVA02`) ve `Ss. Cyril and Methodius University`
(`MK SKOPJE01`). Ülke sütunları boştu, bu iki anlaşma **listeye hiç
alınmıyordu.**

Kod ön ekinden okunup dolduruldu, ikisi de geri geldi: 466 → **468 anlaşma.**

> Buradaki ders, alan kodundakiyle aynı: *Veri yok demeden önce doğru yere mi
> bakıyoruz diye sormak gerekiyor.* İki kez aynı sınıf hata çıktı ve ikisinde
> de eksik olan veri değil, okuduğumuz sütundu.

### 2.9 · Bir kayıtta alan kodu bölüm adıyla çelişiyor

`University of Bielsko-Biała` (`PL BIELSKO02`) ile yapılan anlaşmada bölüm
**Makine Mühendisliği** yazılı, alan kodu ise `061` verilmiş. ISCED'de `061`
**bilişim ve iletişim**, makine mühendisliğinin karşılığı `0715`.

Sonuç: Bu anlaşma sitede *"Bilişim ve iletişim"* alanında görünüyor.

> **Düzeltmedik ve sebebi öncekilerden farklı.** Ülke vakasında ikinci bir
> kaynak vardı (Erasmus kodu) ve tanım gereği doğruydu. Burada iki bilgi
> çelişiyor ve **hangisinin doğru olduğunu biz bilemeyiz:** Kod mu yanlış
> yazıldı, yoksa bölüm adı mı? İkisi de sizin.
>
> Kodu esas alıyoruz, çünkü alan filtresi kodla çalışıyor.

**Bu tek örnek, çünkü aranması zor bir sınıf.** Bölüm adıyla kodun uyumunu
makineyle taramayı denedik ve 47 aday çıktı, okununca yalnız biri gerçek hata
çıktı. Sebebi ISCED'in beklenmedik yerlerde doğru olması: *Turizm İşletmeciliği*
`1015` (Hizmetler → Turizm), *Gıda Mühendisliği* `0721` (Gıda işleme),
*Beden Eğitimi Öğretmenliği* `1014` (Spor). Üçü de doğru, kalıp üçünü de yanlış
sanıyordu.

---

---

### 2.10 · Bunları düzeltmek isterseniz

Yukarıdakilerin çoğu, elle düzeltilince **uzun süren** işler. 2.6'daki yazım
farkı tek başına 468 kaydın 91'ine dokunuyor ve her birini tabloda bulup
düzeltmek gerekiyor.

Bizde bu iş zaten yarı yapılmış durumda: Tabloyu okurken hangi hücrenin neden
farklı olduğunu **satır satır biliyoruz**, çünkü kararı verirken kaydettik.
Aynı kayıttan bir düzeltme geçişi üretmek fazladan bir iş değil.

Önerimiz şu ve isterseniz yaparız:

| | |
|---|---|
| **Ne gönderiyoruz** | Tablonuzun bir kopyası · düzeltmeler uygulanmış |
| **Nasıl işaretli** | Yalnız **değişen hücreler** renkli, yanında eski değeri |
| **Ne yapmanız gerekiyor** | Tabloyu baştan sona okumak değil, yalnız işaretli hücrelere bakmak |
| **Aslına ne oluyor** | Hiçbir şey · gönderdiğimiz ayrı bir dosya, kendi listeniz elinizde |

Karar sizin kalıyor: İşaretli her hücreyi kabul ya da reddedersiniz. Biz hangi
yazımın doğru olduğuna karar vermiyoruz, yalnız **aynı olması gerekenleri bir
arada gösteriyoruz.**

Bu bir talep değil. Düzeltme yapılmasa da liste bugünkü hâliyle çalışıyor ve
yukarıdaki her durum için ne yaptığımız yazılı.

> **Dosya hazır.** Bu öneri yazıldığında yalnız bir niyetti, bugün onu üreten
> bir araç var ve çalışıyor. İstediğiniz an gönderebiliriz.

---

## 3 · Okurken verdiğimiz kararlar

Bunlar veriyle ilgili kararlar değil, **okuma kararları**: Tabloda birden çok
okunuş mümkün olduğunda hangisini seçtiğimiz. Yanlış bulduğunuz varsa
değiştiririz.

| Durum | Kararımız | Gerekçe |
|---|---|---|
| Alan kodu üç sütunda farklı ayrıntıda | **En ayrıntılısını** alıyoruz | ISCED basamaklı bir sistem, `0610`, `061`in içinde. Ayrıntılı olan bilgiyi kaybettirmiyor |
| Üç haneli kod | Baştaki sıfırın silindiğini **varsayıyoruz** | Ama önce olduğu gibi deniyoruz, geçerli bir alana denk geliyorsa dokunmuyoruz |
| Üstü çizili satır | Listeye **almıyoruz** | Silindiği yazılı |
| `(… İPTAL)` notu | O kademeyi **düşürüyoruz** | İptal edilmiş bir kademeye başvuru açık görünmemeli |
| Ülkesi olmayan satır | Erasmus kodundan **dolduruyoruz** | Ön ek kodun tanımının parçası, tahmin değil |
| Ülke sütunu koda aykırı | **Kodu** esas alıyoruz | Kod tanım gereği doğru, sütun elle yazılıyor |
| Türkçe adı olmayan satır | İngilizce etiketi **gösteriyoruz** | Boş bırakmaktan iyi |
| Bölüm adının önündeki kod | Addan **ayırıyoruz** | Kart üzerinde kod ayrı bir rozet olarak duruyor |

Bir karar daha var ve bu bir sınır: **Alan kodu bilinmeyen kayıtlar, alan filtresi
açıkken listeden düşüyor.** Bunu gizlemiyoruz, sayfada şöyle bir uyarı çıkıyor:
*"Kaynak veride alanı belirtilmemiş N anlaşma bu filtreye giremiyor."* MAKÜ
listesinde bu sayı **1**.

### 3.1 · Marmara ve ESOGÜ listelerinde alan kodu hiç yok

İki listede de ISCED alan kodu **hiçbir sütunda ve hiçbir bölüm adının önünde**
geçmiyor. Sonucu açık: O iki üniversitenin sayfasında **alana göre süzme
çalışmıyor** ve sayfa bunu yazıyor, boş bir kutu bırakmıyor.

**Bölüm adından kod üretmedik** ve bu bilinçli bir tercih. *"Bilgisayar
Mühendisliği"* yazan bir satıra `0613` yazmak teknik olarak kolay, ama o kod
sizin verdiğiniz bir bilgi olmaz · bizim tahminimiz olur ve öğrenci onu sizin
beyanınız sanar. Tahmini veri diye sunmak, eksik veriden kötü.

Listenize ISCED kodu eklerseniz alan süzgeci kendiliğinden çalışmaya başlar.

### 3.2 · Marmara'da ülke yalnız Erasmus kodundan okunuyor

Marmara listesinde ülke sütunu yok. MAKÜ ve ESOGÜ'de kod ile sütun birbirini
**denetliyor**; Marmara'da kod tek kaynak.

Sonucu: Ön eki okunamayan bir satırı boş ülkeyle göstermek yerine **listeye
almıyoruz.** Bu bir kez yaşandı ve düzeltildi · beş satır `S` ön ekiyle
başlıyordu (2014 öncesi İsveç kodu) ve tablomuzda o kod yoktu. Eklendi, beş
satır listeye girdi.

### 3.3 · Notlardan e-posta adresi çıkarıyoruz

Marmara listesinde bir açıklama notu partner kurumun e-posta adresini
taşıyordu. **Adresi çıkardık, notun kalanını bıraktık** · not gerçek bir bilgi
veriyordu (*"B1 seviyesinde Almanca"*), adres ise
[§5](#5--kişisel-veriyi-neden-okumuyoruz)'teki kurala giriyor.

Çıkarma işlemi karta iz bırakıyor: Öğrenci cümlenin kısaltıldığını görüyor,
eksik bir cümle okuyup ne olduğunu merak etmiyor.

### 3.4 · Süresi dolmuş anlaşmalar işaretleniyor, listeden çıkarılmıyor

Geçerlilik aralığı bitmiş anlaşmalar kartta **"süresi doldu"** yazısıyla
gösteriliyor. Listeden çıkarmıyoruz, çünkü çıkarmak sizin listenizde olan bir
şeyi yok saymak olurdu · anlaşma yenilenmiş de olabilir, listede kalması bir
hata da olabilir. İkisini biz bilemeyiz.

Bugünkü sayı: **MAKÜ listesinde 3 anlaşma** (2023, 2024 ve 2025'te bitmiş
görünüyor). Marmara listesinde yok, ESOGÜ listesinde geçerlilik sütunu yok.

Hesap sayfayı açtığınız günün yılına göre yapılıyor · yani bu işaret zamanla
kendiliğinden güncel kalıyor.

### 3.5 · Aynı partner + aynı bölüm birden çok kez geçiyor

Bazı kayıtlar aynı Erasmus kodunu ve aynı bölümü taşıyor ama içerikleri
farklı · geçerlilik, kontenjan ya da dil ayrı. Yani kaynakta iki ayrı anlaşma
kayıtlı görünüyor.

**Birini seçmiyoruz, ikisini de gösteriyoruz.** Hangisinin geçerli olduğunu
kurum bilir; birini seçmek öğrenciye var olmayan bir kesinlik sunmak olurdu.

Bugünkü sayı: MAKÜ 19 çift, Marmara 6, ESOGÜ 2. Biri sorulmaya değer olabilir ·
MAKÜ listesinde `LV REZEKNE02` için aynı yıl başlayan iki kayıt var ve
kontenjanları **18** ile **2**.

### 3.6 · ESOGÜ'de bölümü yazılmayan satırda fakülte adı gösteriliyor

Bir satırda bölüm boştu, fakülte doluydu. Anlaşma fakülte geneline ait
görünüyor, o yüzden fakülte adını gösteriyoruz **ve iz bırakıyoruz** · öğrenci
bunun bir bölüm adı olmadığını görebiliyor.

---

## 4 · Bir şey yanlışsa

Üç yol var, üçü de yeterli:

- **E-posta:** burhanarikan@yaani.com
- **Bu sayfadaki bir kart yanlışsa** ekran görüntüsü göndermek yeterli, kaydı biz
  buluruz
- **Tablo düzeyinde bir şey söylemek isterseniz** hangi sütun, hangi satır demeniz
  yeterli

**Kaldırma talebi:** Kurumunuz kendi verisiyle ilgili düzeltme ya da kaldırma isterse
kaldırma talebi tartışmasız yerine getirilir ve gerekçe sorulmaz.
Düzeltme talepleri sıraya girmeden işlenir · gönüllü yürüyen bir çalışma
olduğu için "anında" demek yerine, talebi aldığımızı ve ne zaman
işleyeceğimizi yazılı bildiriyoruz.

---

## 5 · Kişisel veriyi neden okumuyoruz

Tablonuzun Q ve R sütunlarında anlaşmayı imzalayan kişinin adı ve e-posta
adresi duruyor. Bir süre bunları okuyup kartta gösterdik. 20 Ağustos 2026'da
okumayı bıraktık ve sebebini burada yazıyoruz, çünkü bu sizin verinizle ilgili
bir karar.

Üç sebep var ve üçü birbirinden bağımsız:

**Veri bizim değil.** Bu kişiler partner üniversitelerde çalışıyor, çoğu
Avrupa Birliği'nde. Adlarını ve adreslerini toplayıp yeniden yayımlamak için
elimizde bir dayanak yok. Bu belgenin başında "veriyi siz yayımlıyorsunuz,
biz okuyup düzenliyoruz" diyoruz, o cümle bunu da kapsıyor.

**Toplanmış hâli farklı bir şey.** Bir adres kurumun kendi sayfasında
durabilir. Dört yüz altmış altı ad ve üç yüz üç adresin tek bir dosyada
toplanmış hâli aynı şey değil, doğrudan hasat edilebilir bir liste.

**Geri alınamıyor.** Proje açık kaynak olarak yayımlanacak. Bir kez girdiğinde
sürüm geçmişinde kalıyor, sonradan silmek yayımlanmış olmayı geri almıyor.

Kaybedilen işlevin yerine bir şey koymadık, çünkü o işlev zaten yanlış yöne
işaret ediyordu: Sizin üniversitenizde okuyan bir öğrenci, karşı üniversitedeki
koordinatöre doğrudan yazmaz, kendi kurumunun ofisine başvurur. Kartta duran
bağlantı yanlış davranışı öneriyordu.

Kurumsal bir adres (bölümün ya da uluslararası ofisin web sayfası) verirseniz
onu memnuniyetle gösteririz, arayüz bunun için hazır duruyor ve kişisel adrese
zaten onu tercih ediyordu.

## 6 · Neyi düzeltmiyoruz

Yukarıdakilerin hiçbirini **kaynağında** düzeltmiyoruz. Sizin tablonuza
dokunmuyoruz ve düzeltilmiş bir kopya da tutmuyoruz.

Sebebi şu: Veri sizin ve doğrusunu siz bilirsiniz. Bir bölümün adının ne olduğunu
tahmin etmek bize düşmez, sormak düşer.

**Ama yardım edebiliriz.** Bu tür düzeltmeler elle günler alıyor, oysa çoğu tek
seferde yapılabilir. İsterseniz düzeltilmiş bir kopya hazırlar ve **değişen her
hücreyi işaretleyerek** göndeririz. Siz de tablonun tamamını değil, yalnız
işaretli yerleri kontrol edersiniz. Karar sizin kalır. Biz yalnız okurken karşılaştığımız
belirsizlikleri **yazılı bir kararla** çözüyoruz. Böylece bir gün "bu neden böyle
görünüyor" diye sorulduğunda cevabı hazır oluyor.

Kararlarımızın hepsi bu belgede ve **başka bir yere bakmak gerekmiyor.**
