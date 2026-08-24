"""Deponun belgeleri · bağlantılar, sayılar ve yazım.

Bir belgedeki hata sessizce yaşıyor: Bağlantı kırılır, kimse tıklamaz; bir sayı
eskir, kimse saymaz; bir kurumun adı yanlış yazılır, kimse fark etmez.

Buradaki dört denetim de gerçekten yaşanmış birer olaydan doğdu:

  · Başka bir belgeye verilen çapa, hedef başlık yeniden yazılınca kırıldı
  · README'deki anlaşma sayısı veriden ayrıştı
  · Kurumun adı sitede doğru, README'de yanlış yazılıydı
  · Türkçe metinde yasak olan işaret, kural yazıldıktan SONRA iki kez kullanıldı
"""
import json
import re
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def gh_capa(baslik):
    """Bir başlıktan, GitHub'ın ürettiği çapayı hesaplar.

    Kural (github-slugger ile aynı sıra): küçük harfe çevir → noktalamayı at
    (harf, rakam, boşluk, tire, alt çizgi kalır) → **her boşluğu ayrı ayrı** tireye
    çevir.

    Son adımdaki "ayrı ayrı" önemli ve bir kez yanlış yazıldı. Ardışık boşluklar tek
    tireye indirilirse "0.3 · Neden" başlığı `03-neden` verir; GitHub ise noktalamayı
    attıktan sonra geriye kalan **iki** boşluğu iki tireye çevirip `03--neden` üretir.
    Yani başlıkta `·` gibi bir ayraç varsa iki hesap ayrışır.

    Neden elle hesaplıyoruz: Markdown'da `{#özel-ad}` yazarak çapa vermek
    Pandoc/kramdown biçimidir, **GitHub tanımaz**. GitHub'da o süslü parantez
    başlıkta olduğu gibi görünür ve çapa yine başlık metninden üretilir. Bu
    yüzden çapa uydurmuyoruz; başlığın kendisinden türetiyoruz.

    **Birleşen işaretler korunur** ve bunun sebebi ölçüldü. Türkçe büyük "İ"
    küçültülünce `i` + U+0307 (birleşen üstteki nokta) oluyor, tek görünen
    harf, iki kod noktası. İlk yazımda noktalama temizliği bu ikinci kod
    noktasını da atıyordu; GitHub atmıyor.

    Sonuç: "İ" ile başlayan bir başlığa elle yazılan çapa GitHub'da hiçbir
    yere gitmiyor · `### İçerik` başlığının gerçek çapası `#içerik` değil,
    `#i̇çerik`. Fark gözle görülmüyor, iki dize ekranda birebir aynı duruyor.

    Bu bir kez "doğrulanmamış sınır" olarak yazılıydı ve depo GitHub'a
    gönderilince sınandı: 242 çapanın 17'si ayrışıyordu, hepsi aynı sebepten.
    Doğrulama biçimi: `gh api ... -H "Accept: application/vnd.github.html"`
    GitHub'ın kendi ürettiği HTML'i veriyor, çapalar oradan okunuyor. Yani
    artık taklit ediyoruz **ve** kaynağa sorup karşılaştırdık.
    """
    # Başlıkta Markdown bağlantısı olabiliyor ve GitHub çapayı **işlenmiş
    # metinden** üretiyor: `[dinleyici](../GLOSSARY.md#olay-dinleyici)` yalnız
    # "dinleyici" sayılıyor. Ham metni almak, hedefin tamamını çapaya
    # karıştırıyordu.
    #
    # Bu, çapa hesabının GitHub'a sorularak bulunan ÜÇÜNCÜ ayrışması. İlk ikisi
    # ardışık boşluk ve Türkçe "İ" idi. Üçü de aynı sebepten: Bu işlev bir
    # davranışı taklit ediyor ve taklit, kaynağına sorulmadan doğrulanmıyor.
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", baslik.strip()).lower()
    s = "".join(c for c in s
                if c.isalnum() or c in " -_" or unicodedata.combining(c))
    return s.replace(" ", "-")


class BelgelerArasiBaglantilar(unittest.TestCase):
    """Bir belgeden ötekinin bir bölümüne verilen bağlantı gerçekten oraya gitmeli.

    Bir belge ötekinin bölümlerine **düz metinle** atıfta bulunuyordu, bağlantı
    hiç kurulmamıştı. Bağlantı kurulunca yeni bir risk doğdu ve bu sınıf onu
    kapatıyor.

    Bağlantı kurulunca yeni bir risk doğuyor: Hedef başlık yeniden yazılınca
    çapa sessizce kırılıyor ve okuyucu belgenin başına düşüyor. Bu sınıfın işi
    o.
    """

    def belgeler(self):
        """Deponun kök belgeleri · alt klasörlerdeki şablonlar dahil."""
        for p in sorted(ROOT.glob("*.md")):
            yield p
        for p in sorted((ROOT / ".github").rglob("*.md")):
            yield p

    def capalar(self, yol):
        return {gh_capa(m.group(1))
                for satir in yol.read_text(encoding="utf-8").splitlines()
                if (m := re.match(r"^#{1,6} (.*)$", satir))}

    def test_baska_belgeye_verilen_capa_var_olan_bir_baslik(self):
        kirik = []
        for kaynak in self.belgeler():
            metin = kaynak.read_text(encoding="utf-8")
            for hedef_yol, capa in re.findall(r"\]\(([^)#]+\.md)#([^)]+)\)", metin):
                hedef = (kaynak.parent / hedef_yol).resolve()
                if not hedef.exists() or hedef == kaynak.resolve():
                    continue
                if capa not in self.capalar(hedef):
                    kirik.append(f"{kaynak.relative_to(ROOT)} → {hedef_yol}#{capa}")
        self.assertEqual(kirik, [],
                         "Başka belgeye verilen bağlantı bir başlığa gitmiyor:\n  "
                         + "\n  ".join(kirik))

    def test_belgeler_arasi_baglanti_sayisi_makul(self):
        """Alt sınır · kalıp bozulursa üstteki test hiçbir şey bulmaz ve yeşil yanar."""
        n = sum(len(re.findall(r"\]\([^)#]+\.md#[^)]+\)", p.read_text(encoding="utf-8")))
                for p in self.belgeler())
        # Eşik bir kez 10'du ve belge sayısı azalınca düştü · KALIP aynı
        # denetleniyor, yalnız kaç örnek üzerinde denetlendiği değişti.
        # Eşiği düşürmek standardı düşürmek değil; sıfıra inerse bu test
        # hiçbir şey bulamayacağı için yeşil yanardı, esas engellenen o.
        self.assertGreaterEqual(n, 3, f"Yalnız {n} belgeler arası çapa bulundu; kalıp bozulmuş olabilir.")


class UzunCizgi(unittest.TestCase):
    """Türkçe metinde uzun çizgi (—) kullanılmıyor · TDK.

    Kural yazılıydı ve **hiçbir şey onu kontrol etmiyordu.** Sonucu ölçüldü:
    Kural yazıldıktan sonra iki yerde ihlal edildi, biri bu bekçiyi yazan
    oturumda · yani kural okunmuş olsa bile kalıp kontrol edilmediğinde
    tutmuyor. Yöntemin kendi cümlesi: Tanım, kontrol edilmediği sürece niyet
    olarak kalıyor.

    **Kapsam bilerek dar.** İngilizce metin uzun çizgi kullanabiliyor ve
    kullanıyor (`data-en`, app.js'in EN sözlüğü) · onları kapsamak yanlış
    alarm üretirdi ve o, hiç bekçi olmamasından pahalıya gelirdi
    .

    Kapsanan: Türkçe belgeler ve `data-tr` öznitelikleri.
    """

    BELGELER = ("README.md", "CONTRIBUTING.md", "KAYNAK.md", "NOTICE.md")
    # İki yer kuralın KENDİSİNİ anlatırken işareti göstermek zorunda ·
    # yasaklanan şeyi göstermeden yasağı anlatmak mümkün değil.
    # Kuralı ANLATAN satır işareti göstermek zorunda · yasaklanan şeyi
    # göstermeden yasağı anlatmak mümkün değil. Muafiyet dosya adına VE
    # satırın içeriğine bakıyor, yani o dosyada başka bir yerde kullanılırsa
    # yine yakalanıyor.
    MUAF = {("CONTRIBUTING.md", "Türkçe metinde uzun çizgi (—) kullanılmıyor")}

    def test_turkce_belgelerde_uzun_cizgi_yok(self):
        ihlal = []
        for ad in self.BELGELER:
            p = ROOT / ad
            if not p.exists():
                continue
            for i, satir in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if "—" not in satir:
                    continue
                if any(ad == m_ad and m_par in satir for m_ad, m_par in self.MUAF):
                    continue
                ihlal.append(f"{ad}:{i}")
        self.assertEqual(ihlal, [], f"Türkçe metinde uzun çizgi: {ihlal} · TDK, bkz. CONTRIBUTING.md")

    def test_turkce_site_metinlerinde_uzun_cizgi_yok(self):
        """`data-tr` Türkçe · `data-en` bilerek kapsam dışı."""
        ihlal = []
        for p in sorted((ROOT / "site").glob("*.html")):
            for i, satir in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                for deger in re.findall(r'data-tr="([^"]*)"', satir):
                    if "—" in deger:
                        ihlal.append(f"{p.name}:{i}")
        self.assertEqual(ihlal, [], f"data-tr içinde uzun çizgi: {ihlal}")


class TurkceMetindeKisaltma(unittest.TestCase):
    """Türkçe metinde `AI` yerine "yapay zekâ" ya da "araç" kullanılıyor.

    Bu kural iki kez **elle** uygulanmaya çalışıldı ve iki kez eksik kaldı ·
    ilkinde yirmi geçişten dördü, ikincisinde ondan biri atlandı. Sonuncusu
    "sıfır kaldı" diye raporlandığı hâlde on tane duruyordu.

    Ders, bu deponun kendi cümlesi: Bir kalıbı gözle taramak, kalıp birkaç
    farklı biçimde geçtiğinde tutmuyor. Kalıbın kendisi denetlenmeli.

    **Özel adlar muaf** ve muafiyet açıkça listeli · "Agentic AI Foundation"
    bir kurumun adı, çevrilmiyor.
    """

    DOSYALAR = ("README.md", "CONTRIBUTING.md", "KAYNAK.md", "NOTICE.md")
    # Bugün muafiyet yok ve bu bilerek: Muafiyet gerektiren tek ad
    # ("Agentic AI Foundation") onu barındıran belgeyle birlikte gitti.
    # Boş liste testi etkisiz kılmıyor · üstteki test hâlâ her belgeyi tarıyor.
    OZEL_AD = ()
    KALIP = re.compile(r"\bAI\b")

    @staticmethod
    def _duz(metin):
        """Satır sonu boşluk sayılıyor · özel ad iki satıra bölünmüş olabiliyor.

        Bu bekçinin ilk hâli bunu kaçırdı: "Agentic AI Foundation" metinde
        `Agentic AI\nFoundation` diye duruyordu ve muafiyet tutmadı.
        """
        return re.sub(r"\s+", " ", metin)

    def test_turkce_belgelerde_ai_kisaltmasi_yok(self):
        bulgu = []
        for ad in self.DOSYALAR:
            p = ROOT / ad
            if not p.exists():
                continue
            metin = self._duz(p.read_text(encoding="utf-8"))
            for oz in self.OZEL_AD:
                metin = metin.replace(oz, "")
            if self.KALIP.search(metin):
                bulgu.append(ad)
        self.assertEqual(bulgu, [],
                         f"Türkçe metinde 'AI' geçiyor: {bulgu} · "
                         f"'yapay zekâ' ya da 'araç' kullanılmalı.")

    def test_ozel_ad_muafiyeti_hala_gerekli(self):
        """Muafiyet listesi ölü kayıt taşımamalı · taşıyorsa kural gevşemiş demektir."""
        tum = self._duz("\n".join((ROOT / a).read_text(encoding="utf-8")
                                  for a in self.DOSYALAR if (ROOT / a).exists()))
        olu = [o for o in self.OZEL_AD if o not in tum]
        self.assertEqual(olu, [], f"Muafiyet listesinde artık geçmeyen ad var: {olu}")


class KurumAdi(unittest.TestCase):
    """Verinin geldiği birimin adı her yerde aynı ve doğru yazılmalı.

    Marka adı (`Exchange Atlas`) bekçilenmişti, kurumun adı bekçilenmemişti ·
    aynı sınıf, aynı sürüklenme riski. Nitekim sürüklendi: Site dört yerde
    "Uluslararası İlişkiler Koordinatörlüğü" derken README "Dış İlişkiler
    Koordinatörlüğü" diyordu.

    Bu, marka adından daha ağır bir hata: Kendi adımızı yanlış yazmak bizi
    ilgilendiriyor, BAŞKA BİR KURUMUN adını yanlış yazmak onları ilgilendiriyor.
    Üstelik veriyi o birimden alıyoruz ve belgeyi onlara göndereceğiz.

    Doğrusu kurumun kendi adresinden okunuyor: iro.mehmetakif.edu.tr · IRO,
    yani International Relations Office.
    """

    DOGRU = "Uluslararası İlişkiler Koordinatörlüğü"
    YANLIS = "Dış İlişkiler Koordinatörlüğü"

    def metinler(self):
        for yol in ("README.md", "KAYNAK.md", "site/guide.html",
                    "site/index.html", "site/agreements.html", "site/app.js"):
            p = ROOT / yol
            if p.exists():
                yield yol, p.read_text(encoding="utf-8")

    def test_yanlis_kurum_adi_hicbir_yerde_gecmiyor(self):
        gecen = [y for y, m in self.metinler() if self.YANLIS in m]
        self.assertEqual(gecen, [],
                         f"Kurumun adı yanlış yazılmış: {gecen}. "
                         f"Doğrusu '{self.DOGRU}' · kaynak: iro.mehmetakif.edu.tr")

    def test_kurum_adi_en_az_bir_yerde_dogru_yazili(self):
        """Alt sınır · kalıp bozulursa üstteki test hiçbir şey bulmaz ve yeşil yanar."""
        dogru = [y for y, m in self.metinler() if self.DOGRU in m]
        self.assertGreaterEqual(len(dogru), 2,
                                f"Kurumun doğru adı yalnız {len(dogru)} dosyada geçiyor; "
                                f"kalıp bozulmuş olabilir.")


class ReadmedekiAnlasmaSayisi(unittest.TestCase):
    """README tablosundaki anlaşma sayısı üretilen veriyle aynı olmalı.

    `test_kayitli_her_universite_readmede_gecer` üniversitenin **adının**
    geçmesine bakıyor, yanındaki sayıya bakmıyordu. Sonuç: Kaynakta iki
    anlaşma geri kazanıldığında (466 → 468) `KAYNAK.md` ve ayrıştırıcının
    Ayrıştırıcının kendi günlüğü bunu yazdı, **README güncellenmedi.**

    Deponun ön kapısında duran, dışarıdan gelen herkesin ilk gördüğü sayı
    aylarca yanlıştı ve hiçbir test kırılmadı. `CONTRIBUTING.md` bunu zaten
    söylüyor: Metne gömülen sayı, o sayı değiştiği gün sessizce yanlış olur.
    Buradaki sayı gerçekten bir şey anlatıyor, dolayısıyla silinmiyor ·
    **bekçileniyor.**
    """

    def kayitli(self):
        yol = ROOT / "site" / "universities.json"
        return json.loads(yol.read_text(encoding="utf-8"))

    def test_readmedeki_sayi_uretilen_veriyle_ayni(self):
        metin = (ROOT / "README.md").read_text(encoding="utf-8")
        uni = self.kayitli()
        self.assertGreater(len(uni), 0, "universities.json boş: denetim boşa dönüyor.")

        yanlis = []
        for u in uni:
            # Tablo satırı: | <ad içeren hücre> | <sayı> | <kaynak> |
            satir = next((s for s in metin.split("\n")
                          if s.startswith("|") and u["abbr"] in s), None)
            if satir is None:
                yanlis.append(f"{u['abbr']} → README tablosunda satırı yok")
                continue
            hucre = [h.strip() for h in satir.split("|")]
            if str(u["count"]) not in hucre:
                yanlis.append(f"{u['abbr']} → README'de {hucre[2:3]}, veride {u['count']}")

        self.assertEqual(yanlis, [],
                         f"README tablosundaki anlaşma sayısı üretilen veriyle "
                         f"uyuşmuyor: {yanlis}")


class BetikAdi(unittest.TestCase):
    """COUPLINGS §8 · app.js kendini tanıtmaz; onu çağıran sayfa adıyla ister.

    Yeniden adlandırma sessizce bozar: sayfa açılır, başlık ve footer görünür,
    liste hiç gelmez. Tarayıcı bulamadığı betik için hata mesajı yazmaz.
    """

    def test_app_jsi_isteyen_her_sayfa_dogru_adi_yaziyor(self):
        betik = ROOT / "site" / "app.js"
        self.assertTrue(betik.exists(), "site/app.js yok; adı değişmiş olabilir")
        isteyenler = [y for y in sorted((ROOT / "site").glob("*.html"))
                      if re.search(r'<script[^>]+src="([^"]+)"', y.read_text(encoding="utf-8"))]
        self.assertNotEqual(isteyenler, [],
                            "Hiçbir sayfa dış betik istemiyor; app.js yüklenmiyor olabilir")
        for sayfa in isteyenler:
            for m in re.finditer(r'<script[^>]+src="([^"?]+)', sayfa.read_text(encoding="utf-8")):
                with self.subTest(sayfa=sayfa.name, src=m.group(1)):
                    self.assertTrue((ROOT / "site" / m.group(1)).exists(),
                                    f"{sayfa.name} '{m.group(1)}' istiyor ama o dosya yok; "
                                    f"sayfa sessizce boş kalır")


if __name__ == "__main__":
    unittest.main()
