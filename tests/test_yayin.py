"""Yayın bütünlüğü · biri eksikse yayını durdurur.

Buradaki testler "kod çalışıyor mu" diye bakmıyor, **yayın bütünlüğünü**
ve canlıya çıkmadan önce tamamlanması gereken koşulları denetliyor.

Neden test olarak: Bu tür eksikler belgeye yazıldığında kimse okumadığı için
unutuluyor. Bir kez yaşandı · bir belgede aylarca duran eskimiş bir bilgi
kimsenin dikkatini çekmedi.

BORÇ NASIL İFADE EDİLİYOR

Bu dosya bir kez model değiştirdi. İlk hâlinde kırık test = ödenmemiş borç
demekti. O model CI'ya bağlanınca çöktü: Kalıcı kırmızı bir "borç
hatırlatması" bütün dağıtımları bloke ediyor.

Yerine geçen model: Bir borç, **koşulu gerçekleşince** kırılan bir testle
ifade ediliyor. `UniversiteEklemeOnKosulu` bunu yapıyor · bugün yeşil, ikinci
üniversite eklendiği gün kırmızı. Borç, ödenmesi gereken ana kadar sessiz
duruyor.

`YayinKapisi` aynı kalıbın en büyüğü: README yayın durumunu açıkça bildiriyor;
kapı, dokümantasyon ve makinenin görebildiği yayın koşulları ayrıştığında kırılıyor.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class YayinKapisi(unittest.TestCase):
    """Yayın bütünlüğünü koruyan makinece görülebilir koşullar.

    **Buraya yalnız makinenin görebildiği şey giriyor.** DNS sağlayıcısına
    bildirim gönderildiği veya bir kurumla iletişim kurulduğu görülemiyor;
    görünmeyen işleri test kapısına yazmak, kapıyı susturulabilir bir hatırlatma
    listesine çevirirdi.
    """

    KISISEL_SAGLAYICI = ("gmail.com", "hotmail.com", "outlook.com", "yahoo.com",
                         "yaani.com", "icloud.com", "proton.me")
    EPOSTA = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")

    # KARAR · 24 Ağustos 2026
    #
    # Açık kaynak ve canlı yayın iletişim adresi olarak bu adres bilinçli biçimde
    # kullanılıyor. Adres parça parça yazıldığı için basit toplayıcılara karşı
    # küçük bir koruma sağlanıyor; güvenlik bildirimi için ayrıca SECURITY.md
    # doğrudan iletişim kanalını tarif ediyor.
    #
    # MUAF listesi kaldırılmadı: Kişisel sağlayıcıya ait başka bir adresin
    # belgelerde kazara yayımlanmasını engelliyor. İleride kurumsal adrese
    # geçilirse adres ve bu liste birlikte güncellenmeli.
    MUAF = ("burhanarikan@yaani.com",)

    def yayinda_mi(self):
        return "**Durum:** yayında." in (ROOT / "README.md").read_text(encoding="utf-8")

    def metinler(self):
        for ad in ("README.md", "KAYNAK.md", "NOTICE.md"):
            p = ROOT / ad
            if p.exists():
                yield ad, p.read_text(encoding="utf-8")
        for p in sorted((ROOT / "site").glob("*.html")):
            yield p.name, p.read_text(encoding="utf-8")

    def test_yayinda_muaf_olmayan_kisisel_adres_yok(self):
        """Muaf tutulan adres dışında kişisel sağlayıcı yayına çıkamaz."""
        if not self.yayinda_mi():
            return
        tam = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        bulgu = []
        for ad, metin in self.metinler():
            for adres in set(tam.findall(metin)):
                if adres.lower() in (m.lower() for m in self.MUAF):
                    continue
                alan = adres.split("@")[1].lower()
                if alan in self.KISISEL_SAGLAYICI:
                    bulgu.append(f"{ad}: {adres}")
        self.assertEqual(sorted(bulgu), [],
                         f"Muaf listesinde olmayan kişisel adres yayında: {bulgu}\n"
                         f"Bilerek konduysa MUAF listesine gerekçesiyle ekleyin; "
                         f"yoksa kurumsal adresle değiştirin.")

    def test_muafiyet_hala_gerekli(self):
        """Ölü muafiyet birikmesin · kurumsal adrese geçilince liste boşalmalı.

        Bu deponun tekrar eden dersi: Muafiyet listeleri gerekçe sorulmadığında
        susturma yerine dönüşüyor. Kullanılmayan bir muafiyet, listede kaldığı
        sürece bekçiyi olduğundan geniş gösteriyor.
        """
        tum = "".join(m for _, m in self.metinler())
        olu = [a for a in self.MUAF if a not in tum]
        self.assertEqual(olu, [],
                         f"Muaf listesinde artık hiçbir yerde geçmeyen adres var: "
                         f"{olu} · kaldırın.")

    def test_iletisim_adresi_en_az_bir_yerde_duruyor(self):
        """Alt sınır · adres tümüyle silinirse üstteki test hiçbir şey bulmaz."""
        var = [ad for ad, m in self.metinler() if self.EPOSTA.search(m)]
        self.assertGreaterEqual(len(var), 1,
                                "Hiçbir belgede iletişim adresi yok; kalıp bozulmuş olabilir.")


class YaziTipiLisanslari(unittest.TestCase):
    """SIL OFL 1.1, dağıtılan her kopyanın lisans metnini taşımasını şart koşuyor.

    Bu klasördeki .woff2 dosyaları Inter ve Manrope'un alt kümeleri. Alt küme
    üretimi sırasında dosyaların içindeki telif kayıtları düşmüş; yani dosyalar
    kendi başlarına lisansı taşımıyor. Lisans metni ayrı dosya olarak bulunmak
    zorunda.

    `fonts.css` içinde "OFL lisansı" diye bir cümle var: O bir beyan, lisans
    değil. Beyan hukuki bir belge yerine geçmez.
    """

    FONT_KLASORU = ROOT / "site" / "fonts"
    GEREKEN = ["OFL-Inter.txt", "OFL-Manrope.txt"]

    def test_lisans_metinleri_klasorde(self):
        eksik = [ad for ad in self.GEREKEN if not (self.FONT_KLASORU / ad).exists()]
        self.assertEqual(
            eksik, [],
            f"Yazı tipi lisans metni eksik: {eksik}\n"
            f"OFL 1.1, dağıtılan her kopyanın lisans metnini taşımasını şart koşar.\n"
            f"Kaynak depolarından indirilip {self.FONT_KLASORU.relative_to(ROOT)}/ "
            f"içine konmalı. Ezberden yazılmamalı.\n"
            f"Ayrıntı: site/fonts/README.md")

    def test_her_yazi_tipi_ailesinin_lisansi_var(self):
        """Liste elle yazılı olduğu için **büyümüyor.**

        Üstteki test `GEREKEN` listesindeki iki dosyaya bakıyor. Üçüncü bir
        yazı tipi ailesi eklense liste kendiliğinden büyümez, yani yeni aile
        lisanssız gelir ve hiçbir test kırılmaz · korumanın tam da yeni
        eklenende olmadığı durum.

        Bu test listeyi değil **klasörün kendisini** okuyor: Dosya adının ilk
        parçası aileyi veriyor (`manrope-700-latin.woff2` → `manrope`) ve her
        aile için adında o aileyi taşıyan bir OFL metni aranıyor.
        """
        aileler = sorted({y.name.split("-")[0].lower()
                          for y in self.FONT_KLASORU.glob("*.woff2")})
        self.assertTrue(aileler,
                        f"{self.FONT_KLASORU.relative_to(ROOT)} içinde hiç .woff2 yok; "
                        f"denetim boşa dönüyor.")

        lisanslar = [y.name.lower() for y in self.FONT_KLASORU.glob("OFL-*.txt")]
        lisanssiz = [a for a in aileler
                     if not any(a in ad for ad in lisanslar)]
        self.assertEqual(
            lisanssiz, [],
            f"Bu yazı tipi ailelerinin OFL metni yok: {lisanssiz}\n"
            f"OFL 1.1, dağıtılan her kopyanın lisans metnini taşımasını şart koşar. "
            f"Kaynak deposundan indirilip OFL-<Aile>.txt olarak konmalı.")

    def test_lisans_metinleri_bos_degil(self):
        for ad in self.GEREKEN:
            yol = self.FONT_KLASORU / ad
            if not yol.exists():
                self.skipTest(f"{ad} henüz yok (üstteki test bunu bildiriyor)")
            with self.subTest(dosya=ad):
                metin = yol.read_text(encoding="utf-8", errors="replace")
                self.assertIn("SIL OPEN FONT LICENSE", metin.upper(),
                              f"{ad} bir OFL metni gibi görünmüyor")
                self.assertIn("Copyright", metin,
                              f"{ad} telif satırı taşımıyor; OFL bunu şart koşuyor")

    def test_kapsam_disi_beyani_duruyor(self):
        """MIT lisansı deponun tamamını kapsıyormuş gibi okunmamalı.

        İki ayrı şey kapsam dışı ve ikisi de ayrı sebeple:

        **Yazı tipleri.** OFL altında dağıtılan bir yazı tipi MIT altında
        yeniden lisanslanamaz.

        **Üniversite verisi.** Bu daha ağır, çünkü hak bizde değil. MIT metni
        "satabilirsin, alt lisanslayabilirsin, sınırsız kullanabilirsin" diyor.
        Biz üniversitelerin kamuya açık anlaşma listeleri için bu hakları
        veremeyiz · derleme ve biçimlendirme bizim, veri değil.

        Bu uzun süre yalnız README'de yazılıydı ve README bir açıklama, hukuki
        belge değil. Sonra `LICENSE`'ın içine, MIT metninin altına kondu. Bugün
        ayrı bir dosyada: Kanonik lisans metni değiştirilmeden durur, ek bilgi
        yanına gider.
        """
        metin = (ROOT / "NOTICE.md").read_text(encoding="utf-8")
        for parca, ne in [("site/fonts", "yazı tipleri"),
                          ("site/data-", "üniversite verisi"),
                          ("universities.json", "üniversite listesi")]:
            with self.subTest(kapsam=ne):
                self.assertIn(parca, metin,
                              f"NOTICE.md {ne} için kapsam dışı beyanı taşımıyor. "
                              f"MIT metni onu da kapsıyormuş gibi okunuyor.")

    def test_lisans_metni_bozulmamis(self):
        """`LICENSE` yalnız kanonik MIT metnini taşımalı.

        Ayrımın anlamı burada: Ek bir bölüm eklemek MIT'yi ihlal etmiyor, ama
        okuyucuyu neyin bağlayıcı olduğunu ayırmaya zorluyor. Dosya sade
        kalırsa o soru hiç doğmuyor.
        """
        metin = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", metin)
        self.assertIn("THE SOFTWARE IS PROVIDED", metin,
                      "MIT metninin sorumluluk reddi bölümü eksik.")
        for yabanci in ("KAPSAM DIŞI", "site/fonts", "site/data-", "OFL"):
            with self.subTest(parca=yabanci):
                self.assertNotIn(yabanci, metin,
                                 f"LICENSE kanonik MIT metni dışında içerik taşıyor "
                                 f"({yabanci}). Kapsam notları NOTICE.md'ye ait.")


class UniversiteEklemeOnKosulu(unittest.TestCase):
    """Sessiz geri düşüş · **ödendi**, bekçi gerilemeye karşı duruyor.

    `app.js` adresteki `?uni=` değerini tanımadığında **sessizce listedeki ilk
    üniversiteye** düşüyordu:

        UNI = unis.find((u) => u.id === UNI_ID) || unis[0];

    Tek üniversiteyle görünmeyen bu davranış, ikincisiyle birlikte "öğrenci
    başka bir üniversitenin listesini kendininki sanıyor" hâline geliyordu ve
    hiçbir uyarı yoktu.

    Bu test bir **borç bekçisiydi**: Kayıt sayısı biri geçtiği gün kırılacak
    biçimde yazılmıştı, yani borcun ödenmesi gereken ana kadar sessiz durdu.
    Borç 21 Ağustos 2026'da ödendi · tanınmayan bir değer artık durumu söyleyip
    üniversite seçimine yönlendiriyor.

    Bekçi kaldırılmadı, çünkü artık farklı bir iş yapıyor: Geri düşüşün
    **yeniden** eklenmesini engelliyor. Ödenmiş bir borcun bekçisi, aynı borcun
    tekrar doğmasına karşı koruma.
    """

    def test_ikinci_universite_once_sessiz_geri_dusus_cozulmeli(self):
        yol = ROOT / "site" / "universities.json"
        if not yol.exists():
            self.skipTest("universities.json yok")
        sayi = len(json.loads(yol.read_text(encoding="utf-8")))
        if sayi <= 1:
            return  # tek üniversite: sorun görünmez, bugün engel yok

        kaynak = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        sessiz = re.search(r"unis\.find\([^)]*\)\s*\|\|\s*unis\[0\]", kaynak)
        self.assertIsNone(
            sessiz,
            f"Platformda {sayi} üniversite var ama tanınmayan ?uni= değeri hâlâ "
            f"sessizce ilk üniversiteye düşüyor. Kullanıcı yanlış üniversitenin "
            f"listesini kendi üniversitesininki sanabilir.\n"
            f"Çözülmeden ikinci üniversite eklenmemeliydi; ya kullanıcıya bildirin "
            f"ya da üniversite seçimine yönlendirin.")


def _srgb(c):
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _isik(hexs):
    h = hexs.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)


def kontrast(on, arka):
    """WCAG 2.1 kontrast oranı: (parlak + 0.05) / (koyu + 0.05)."""
    a, b = _isik(on), _isik(arka)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


class GeriBildirimAdresi(unittest.TestCase):
    """Adresin tüm kullanıcıya dönük kopyalarını bilinçli tutar.

    Sıfır dış istek ilkesi yüzünden uygulama içi hata toplama yok; kullanıcı,
    kurum veya katkıcı bir şey bildirecekse bu kanalı kullanıyor. Adresin
    değiştirilmesi bilinçli bir ürün/operasyon kararıdır ve bu bekçi kazara
    yapılan tekil kopya değişikliklerini yakalar.
    """

    BUGUNKU = "burhanarikan@yaani.com"
    DURUM = ("Public depoda ve canlı sitede bilinçli kullanılan geri bildirim "
             "adresi. Kurumsal adrese geçilirse tüm kopyalar birlikte güncellenmeli.")

    def test_adres_kayitli_olanla_ayni(self):
        parcali = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        m = re.search(r'GERI_BILDIRIM\s*=\s*(.+?);', parcali)
        self.assertIsNotNone(m, "app.js içinde GERI_BILDIRIM tanımı bulunamadı.")
        # Adres parça parça yazılı (basit tarayıcılara karşı); parçaları birleştir.
        kurulu = "".join(re.findall(r'"([^"]*)"', m.group(1)))
        self.assertEqual(
            kurulu, self.BUGUNKU,
            f"Geri bildirim adresi değişmiş: {kurulu}\n"
            f"Kayıtlı olan: {self.BUGUNKU}\n"
            f"Durum notu: {self.DURUM}\n"
            f"Değişiklik bilinçliyse BUGUNKU ve DURUM güncellenmeli; ayrıca "
            f"index.html, guide.html ve README'deki üç kopya da.")


class TestKesfi(unittest.TestCase):
    """`python3 -m unittest discover` depo kökünden test bulmalı.

    Bulmadığında **"NO TESTS RAN" diyor ve çıkış kodu başarılı oluyor** · yani
    hiçbir şey denetlenmiyor ama her şey yolunda görünüyor. Bu deponun
    bekçilediği hata sınıfının ta kendisi: yeşil yanan boşluk.

    Sebebi `tests/__init__.py`'nin yokluğu · keşif klasörü paket olarak
    görmüyor.

    **Aynı eksik önce yöntem deposunda bulunup düzeltildi ve buraya
    dönülmedi.** Bir sınıfın tek örneğini düzeltip ötekini bırakmanın bedeli ·
    dışarıdan bir okuyucu yakaladı. Bu bekçi o dönüşün yerine geçiyor.
    """

    def test_tests_klasoru_paket(self):
        self.assertTrue((ROOT / "tests" / "__init__.py").exists(),
                        "tests/__init__.py yok · kökten `unittest discover` "
                        "sessizce sıfır test bulur ve başarılı döner.")

    # KEŞFİN KENDİSİNİ BURADA ÇALIŞTIRMIYORUZ · bir kez denendi ve geri alındı.
    #
    # Test içinde `unittest.discover` çağırmak, test koşucusunu testin içinden
    # yeniden çalıştırmak demek. İki yan etkisi var: `defaultTestLoader` modül
    # düzeyinde bir tekil ve durum taşıyor, ayrıca içe aktarma önbelleği
    # çağrılar arasında paylaşılıyor. Sonuç, koşma sırasına ve önbellek
    # durumuna bağlı **kararsız** bir denetim oldu · bir kez kırıldı, sonra
    # aynı komut aynı ağaçta geçti.
    #
    # Kararsız bir bekçi, bu deponun ölçütüne göre en ağır kusur: Yanlış alarm
    # veriyor ve güveni kendisi tüketiyor.
    #
    # Yerine ikisi kondu:
    #   · Mekanizma burada denetleniyor · `tests/__init__.py` var mı
    #   · DAVRANIŞ CI'da denetleniyor · her iki komut da ayrı ayrı koşuyor
    #
    # "Bu komut çalışıyor mu" sorusunun yeri zaten testin içi değil, CI.


if __name__ == "__main__":
    unittest.main()


class ResponseHeaderYapilandirmasi(unittest.TestCase):
    """Başlık destekleyen barındırmalarda kullanılacak güvenlik politikası."""

    def test_headers_dosyasinda_gerekli_basliklar_var(self):
        yol = ROOT / "site" / "_headers"
        self.assertTrue(yol.exists(), "site/_headers yok; destekleyen edge katmanı için yapılandırma kaybolmuş.")
        metin = yol.read_text(encoding="utf-8")
        gerekli = {
            "Content-Security-Policy": "frame-ancestors 'none'",
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        }
        for baslik, deger in gerekli.items():
            with self.subTest(baslik=baslik):
                self.assertIn(baslik + ":", metin)
                self.assertIn(deger, metin)

    def test_csp_headers_meta_politikayla_tutarlilik_gerektiriyor(self):
        metin = (ROOT / "site" / "_headers").read_text(encoding="utf-8")
        self.assertIn("default-src 'none'", metin)
        self.assertIn("script-src 'self'", metin)
        self.assertNotIn("unsafe-inline", metin)
        self.assertNotIn("unsafe-eval", metin)
