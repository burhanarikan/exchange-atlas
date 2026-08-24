"""Sitenin kendi içindeki sözleşmeler.

Üç sayfa (`index`, `agreements`, `guide`) ortak parçaları **kopya** taşıyor ve
`app.js` onları okuyor. Aynı bilgi birden çok yerde durduğunda biri
değiştirilip öteki unutuluyor · hiçbir hata çıkmıyor, yalnız bir sayfa yanlış
davranıyor.

Buradaki testlerin hepsi böyle bir ayrışmadan doğdu:

  · Aynı arama mantığı hem Python'da hem JavaScript'te yazılı
  · Aynı metin `data-tr` ve `data-en` olarak iki dilde duruyor
  · Aynı adres beş yerde geçiyor
  · Bağımsızlık uyarısı üç sayfanın da altbilgisinde olmak zorunda

Ayrıca sitenin iki mimari kararı burada bekçilenmiş: **sıfır dış istek** ve
**renklerin tek kaynaktan gelmesi.**

Not: Bazı testler `node` gerektiriyor (JavaScript tarafını gerçekten
çalıştırmak için). node yoksa o testler atlanıyor, ötekiler çalışıyor.
"""
import importlib.util
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_JS = ROOT / "site" / "app.js"
APP_KAYNAK = APP_JS.read_text(encoding="utf-8")

spec = importlib.util.spec_from_file_location("build_data", ROOT / "scripts" / "build_data.py")
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)


def js_sozluk(ad):
    """app.js içindeki `const <ad> = { ... }` bloğunu anahtar→değer olarak çıkarır."""
    bas = APP_KAYNAK.index(f"const {ad}")
    son = APP_KAYNAK.index("};", bas)
    blok = APP_KAYNAK[bas:son]
    return dict(re.findall(r'"([^"]+)":\s*(?:\[|")', blok) or [])


def js_anahtarlar(ad):
    bas = APP_KAYNAK.index(f"const {ad}")
    son = APP_KAYNAK.index("};", bas)
    return set(re.findall(r'"([^"]+)":', APP_KAYNAK[bas:son]))


def _srgb(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _isik(hexs):
    h = hexs.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)


def kontrast(on, arka):
    a, b = sorted((_isik(on), _isik(arka)), reverse=True)
    return (a + 0.05) / (b + 0.05)


class AramaKatlamasi(unittest.TestCase):
    """COUPLINGS §1 · fold mantığı iki dilde yaşıyor, aynı sonucu vermek zorunda."""

    def test_istisna_tablolari_ayni_harfleri_tasiyor(self):
        py = {chr(k) for k in bd.FOLD_EXCEPTIONS}
        js = js_anahtarlar("FOLD_EXCEPTIONS")
        self.assertEqual(py, js,
                         "FOLD_EXCEPTIONS tabloları ayrışmış: build_data.py ile app.js "
                         "aynı harfleri katlamıyor")

    @unittest.skipUnless(shutil.which("node"), "node kurulu değil")
    def test_iki_fold_ayni_ciktiyi_veriyor(self):
        girdiler = [
            "ŞİŞLİ", "Görsel", "Çevre", "IĞDIR", "Işık", "İSTANBUL", "ÜNİVERSİTE",
            "Universität Tübingen", "Szkoła", "Powiślańska", "Științe", "Politécnico",
            "Škola", "", "0",
        ]
        betik = """
        const fs = require("fs");
        const src = fs.readFileSync(process.argv[1], "utf8");
        const bas = src.indexOf("const FOLD_EXCEPTIONS");
        const son = src.indexOf("const t =", bas);
        const fold = eval(src.slice(bas, son) + "; fold");
        console.log(JSON.stringify(JSON.parse(process.argv[2]).map(fold)));
        """
        cikti = subprocess.run(
            ["node", "-e", betik, str(APP_JS), json.dumps(girdiler)],
            capture_output=True, text=True, check=True,
        ).stdout
        js_sonuc = json.loads(cikti)
        py_sonuc = [bd.fold(g) for g in girdiler]
        for g, p, j in zip(girdiler, py_sonuc, js_sonuc):
            with self.subTest(girdi=g):
                self.assertEqual(p, j, f"fold({g!r}) Python'da {p!r}, JavaScript'te {j!r}")


class AramaKatlamasiKapsami(unittest.TestCase):
    """COUPLINGS §1 · katlama tablosu, verideki harflere yetiyor mu?

    §1'in öteki testi iki dildeki kopyaların **birbirine** uyduğunu denetliyor.
    Bu test farklı bir soruyu soruyor: ikisi de aynı şeyi yapıyor olabilir ama
    **verideki bir harfi ikisi birden çözemiyor** olabilir.

    Neden mekanik olması gerekiyordu: yeni bir üniversite yeni bir ülke getiriyor,
    o ülkenin adlarında yeni harfler oluyor. Bugüne kadar bunu "insan hatırlasın"
    diye COUPLINGS'e yazmıştık, kayıt kimseyi okumaya zorlamıyor.

    Ayrım önemli, yoksa yanlış alarm verir:

      HARF  → çözülemezse arama bozulur. Kullanıcı `h` yazıp `ħ` bulamaz.
      İŞARET → kıvrık tırnak, uzun tire. Aramayı zorlaştırır ama harf değil;
               bugün veride üç tane var ve kabul edilmiş durumda.
    """

    def test_arama_metninde_cozulmemis_HARF_kalmiyor(self):
        yol = ROOT / "site" / "data-maku.json"
        if not yol.exists():
            self.skipTest("data-maku.json yok")
        import unicodedata
        kalan = {}
        for r in json.loads(yol.read_text(encoding="utf-8"))["agreements"]:
            for c in r["search"]:
                if ord(c) > 127 and unicodedata.category(c).startswith("L"):
                    kalan[c] = kalan.get(c, 0) + 1
        self.assertEqual(
            kalan, {},
            f"Katlama bu harfleri çözemiyor: "
            f"{ {c: f'U+{ord(c):04X} ({n} kez)' for c, n in kalan.items()} }\n"
            f"Kullanıcı bunların ASCII karşılığını yazdığında kaydı bulamaz.\n"
            f"Çözüm: FOLD_EXCEPTIONS tablosuna eklenmeli · build_data.py VE app.js, "
            f"ikisine birden (bkz. COUPLINGS §1).")

    def test_cozulmemis_isaretler_bilinen_listede(self):
        """Harf olmayan ASCII-dışı karakterler: aramayı bozmuyor ama pimleniyor.

        Yeni bir işaret çıkarsa haberimiz olsun diye. Kırıldığında yapılacak:
        gerçekten zararsız mı bak, öyleyse listeye ekle.
        """
        yol = ROOT / "site" / "data-maku.json"
        if not yol.exists():
            self.skipTest("data-maku.json yok")
        import unicodedata
        BILINEN = {"\u201c", "\u201d", "\u2013"}   # kıvrık tırnaklar, uzun tire
        kalan = {c for r in json.loads(yol.read_text(encoding="utf-8"))["agreements"]
                 for c in r["search"]
                 if ord(c) > 127 and not unicodedata.category(c).startswith("L")}
        yeni = kalan - BILINEN
        self.assertEqual(
            yeni, set(),
            f"Arama metninde bilinmeyen işaret: "
            f"{ {c: f'U+{ord(c):04X}' for c in yeni} } · zararsız mı diye bakılmalı.")


class MarkaAdi(unittest.TestCase):
    """COUPLINGS §6 · marka adı üç sayfada ayrı ayrı yazılı, aynı kalmak zorunda.

    Bu denetimin sebebi varsayımsal değil: rehber sayfasının footer'ı bir
    üniversitenin adını taşırken site başka bir üniversiteye hizmet ediyordu ve
    bunu kimse fark etmedi. Aynı metnin birden çok dosyaya elle kopyalandığı her
    yerde aynı sapma mümkün. Marka adı da öyle bir metin.

    Footer'lar bu denetime DAHİL DEĞİL: sayfadan sayfaya bilerek farklılar
    (ana sayfa platform uyarısı, liste dinamik, rehber kendi uyarısı). Onları
    "aynı olmalı" diye bağlamak yanlış alarm üretirdi.
    """

    SAYFALAR = ["index.html", "agreements.html", "guide.html"]
    MARKA = "Exchange Atlas · Erasmus"

    def sayfa(self, ad):
        return (ROOT / "site" / ad).read_text(encoding="utf-8")

    def test_wordmark_uc_sayfada_ayni(self):
        bulunan = {}
        for ad in self.SAYFALAR:
            m = re.search(r'<div class="t1">(.*?)</div>', self.sayfa(ad), re.S)
            self.assertIsNotNone(m, f"{ad}: wordmark (.t1) bulunamadı")
            bulunan[ad] = m.group(1).strip()
        self.assertEqual(len(set(bulunan.values())), 1,
                         f"sayfalar farklı wordmark taşıyor: {bulunan}")

    def test_og_site_name_uc_sayfada_ayni_ve_tam_ad(self):
        for ad in self.SAYFALAR:
            m = re.search(r'<meta property="og:site_name" content="([^"]+)"', self.sayfa(ad))
            self.assertIsNotNone(m, f"{ad}: og:site_name yok")
            with self.subTest(sayfa=ad):
                self.assertEqual(m.group(1), self.MARKA)

    def test_og_gorseli_guncel_surumda_tum_sayfalarda_ayni(self):
        beklenen = "https://exchangeatlas.org/og-cover-v2.png"
        for ad in self.SAYFALAR:
            m = re.search(r'<meta property="og:image" content="([^"]+)"', self.sayfa(ad))
            self.assertIsNotNone(m, f"{ad}: og:image yok")
            with self.subTest(sayfa=ad):
                self.assertEqual(m.group(1), beklenen)
                self.assertIn('og:image:secure_url', self.sayfa(ad))
                self.assertIn('og:image:alt', self.sayfa(ad))

    def test_baslikta_tam_marka_geciyor(self):
        # Sekmede ve arama sonucunda görünen ad; kısa ad ("Atlas") burada yetmez.
        for ad in self.SAYFALAR:
            m = re.search(r"<title>(.*?)</title>", self.sayfa(ad), re.S)
            with self.subTest(sayfa=ad):
                self.assertIn(self.MARKA, m.group(1))


class BagimsizlikUyarisi(unittest.TestCase):
    """COUPLINGS §7 · aynı cümle üç sayfada, iki ayrı mekanizmayla yazılı.

    Cümlenin işlevi hukuki: platformun resmî bir üniversite hizmeti olmadığını
    söylüyor. Uzun süre yalnız ana sayfadaydı; oysa paylaşılan bağlantı hep
    anlaşma listesi ve orada "Veri: ... Koordinatörlüğü" yazdığı için resmî
    izlenim daha güçlü. Yani uyarı en çok gerektiği yerde yoktu.
    """

    IMZA = "bağımsız bir platformdur"

    def js_bagimsizlik(self, dil):
        blok = APP_KAYNAK.split(f"  {dil}: {{", 1)[1]
        m = re.search(r"independence:\s*`([^`]+)`", blok)
        self.assertIsNotNone(m, f"app.js'te {dil}.independence yok")
        return m.group(1)

    def html_bagimsizlik(self, sayfa, oznitelik):
        t = (ROOT / "site" / sayfa).read_text(encoding="utf-8")
        m = re.search(rf'<p data-html data-tr="([^"]+)"\s+data-en="([^"]+)"', t, re.S)
        self.assertIsNotNone(m, f"{sayfa}: data-html işaretli bağımsızlık paragrafı yok")
        return m.group(1 if oznitelik == "tr" else 2)

    def test_uc_sayfada_da_ayni_metin(self):
        for dil, idx in (("tr", "tr"), ("en", "en")):
            metinler = {
                "app.js (agreements)": self.js_bagimsizlik(dil),
                "index.html": self.html_bagimsizlik("index.html", idx),
                "guide.html": self.html_bagimsizlik("guide.html", idx),
            }
            with self.subTest(dil=dil):
                self.assertEqual(len(set(metinler.values())), 1,
                                 f"{dil}: bağımsızlık uyarısı sayfalar arasında ayrışmış → "
                                 f"{ {k: v[:60] for k, v in metinler.items()} }")

    def test_agreements_sayfasinda_kap_var(self):
        # app.js metni buraya yazıyor; kap silinirse uyarı sessizce kaybolur.
        t = (ROOT / "site" / "agreements.html").read_text(encoding="utf-8")
        self.assertIn('id="independenceLine"', t,
                      "agreements.html'de independenceLine kabı yok; app.js uyarıyı "
                      "yazacak yer bulamaz ve sayfa uyarısız kalır")

    def test_app_jsin_aradigi_her_kimlik_sayfada_var(self):
        """HTML ile app.js arasındaki asıl sözleşme: kimlikler.

        app.js sayfadaki öğelere `$("#ad")` ile ulaşıyor. Bir kimlik silinir ya
        da adı değişirse çağrı `null` dönüyor ve hata çoğu yerde **o anda**
        çıkmıyor: Sayfa açılıyor, bir düğme çalışmıyor ya da bir sayı hiç
        yazılmıyor. Yani kullanıcı bozukluğu görüyor, geliştirici görmüyor.

        Bu bağlaşım uzun süre yalnız bir kimlik için (`independenceLine`)
        korunuyordu; ötekiler korumasızdı. Sayı ölçüldüğünde yirmi üçtü.
        """
        js = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        html = (ROOT / "site" / "agreements.html").read_text(encoding="utf-8")
        aranan = set(re.findall(r'\$\("#([A-Za-z][\w-]*)"\)', js))
        aranan |= set(re.findall(r'getElementById\("([A-Za-z][\w-]*)"\)', js))
        varolan = set(re.findall(r'id="([A-Za-z][\w-]*)"', html))
        eksik = sorted(aranan - varolan)
        self.assertEqual(eksik, [],
                         f"app.js bu kimlikleri arıyor ama agreements.html'de yok: "
                         f"{eksik}. Çağrı null döner ve ilgili işlev sessizce çalışmaz.")
        self.assertGreaterEqual(len(aranan), 20,
                                f"Sözleşme beklenmedik biçimde daraldı ({len(aranan)} "
                                f"kimlik). Kalıp bozulmuş olabilir; testin kendisi "
                                f"artık bir şey ölçmüyor olabilir.")

    def test_vurgu_ceviriye_dayaniyor(self):
        # data-tr/data-en textContent yazıyor; <strong> ancak data-html ile korunur.
        for sayfa in ("index.html", "guide.html"):
            t = (ROOT / "site" / sayfa).read_text(encoding="utf-8")
            with self.subTest(sayfa=sayfa):
                self.assertIn("data-html", t,
                              f"{sayfa}: data-html yok · çeviri uygulanınca <strong> silinir")
                self.assertIn(f"<strong>", self.html_bagimsizlik(sayfa, "tr"),
                              f"{sayfa}: çeviri değerinde vurgu yok")


class DilTercihi(unittest.TestCase):
    """COUPLINGS §10 ve §11 · dil tercihi üç sayfada aynı anahtardan okunmalı,
    ve o okuma korumalı olmalı.

    §11 bir kez ayrıştı: app.js yazarken try/catch kullanıyordu ama okurken
    kullanmıyordu. Çerezleri engelleyen tarayıcıda localStorage erişimi hata
    fırlatır; korumasız okuma betiğin tamamını düşürüyordu.
    """

    # Sayfa betikleri 24 Ağustos 2026'da HTML'den ayrı dosyalara taşındı
    # (CSP `script-src 'self'` satır içi script kabul etmiyor). Bekçi
    # metnin yerini izliyor · kural değişmedi, dosya değişti.
    SAYFALAR = ["app.js", "home.js", "guide.js"]

    def kaynak(self, ad):
        return (ROOT / "site" / ad).read_text(encoding="utf-8")

    def test_uc_dosya_ayni_anahtari_kullaniyor(self):
        anahtarlar = {}
        for ad in self.SAYFALAR:
            bulunan = set(re.findall(r'localStorage\.(?:get|set)Item\(\s*"([^"]+)"', self.kaynak(ad)))
            self.assertNotEqual(bulunan, set(), f"{ad}: localStorage anahtarı bulunamadı")
            anahtarlar[ad] = bulunan
        birlesim = set().union(*anahtarlar.values())
        self.assertEqual(len(birlesim), 1,
                         f"Dil tercihi farklı anahtarlarla saklanıyor; sayfalar "
                         f"birbirinin seçimini okuyamaz: {anahtarlar}")

        # Anahtarın ADI da bağlı ve bu ayrı bir iddia. Üstteki denetim üç
        # dosyanın BİRBİRİYLE tutarlı olmasına bakıyor · üçünü birden yeniden
        # adlandıran bir değişiklik oradan geçerdi.
        #
        # Oysa bu adın **değişmemesi** şart:
        # Anahtar ziyaretçinin tarayıcısında duruyor, yani ad değişirse
        # ürünün eski kullanıcıları dil tercihlerini kaybediyor. Marka adı
        # bir kez değişti ve anahtar bilerek eski hâlinde bırakıldı.
        #
        # Boşluk gerçek bir olayla görüldü: Belgeler yeniden adlandırılırken
        # toplu bir değiştirme belgelerdeki anahtarı `atlas-lang-eski` yaptı,
        # kod `atlas-lang` kaldı ve HİÇBİR TEST KIRILMADI.
        self.assertEqual(birlesim, {"atlas-lang"},
                         f"Dil tercihi anahtarının adı değişmiş: {birlesim}. "
                         f"Bu ad ziyaretçinin tarayıcısında duruyor; değişirse "
                         f"mevcut kullanıcılar dil tercihlerini kaybeder. "
                         f"COUPLINGS §10 bu adın korunmasını şart koşuyor.")

    def test_her_localstorage_erisimi_korumali(self):
        """Erişimin try bloğu içinde olduğunu arar.

        Kaba bir denetim: `localStorage` geçen satırın öncesinde bir `try` var mı
        diye bakar. Kesin bir çözümleme değil, ama bu dosyalardaki yazım
        biçiminde yanlış alarm vermiyor ve asıl hatayı (korumasız okuma)
        yakalıyor.
        """
        for ad in self.SAYFALAR:
            satirlar = self.kaynak(ad).splitlines()
            for i, satir in enumerate(satirlar):
                if "localStorage" not in satir or "//" in satir.split("localStorage")[0]:
                    continue
                yakin = "\n".join(satirlar[max(0, i - 3):i + 1])
                with self.subTest(dosya=ad, satir=i + 1):
                    self.assertIn("try", yakin,
                                  f"{ad}:{i+1} localStorage'a korumasız erişiyor. "
                                  f"Çerez engelli tarayıcıda hata fırlatır ve betik düşer.\n"
                                  f"  {satir.strip()}")


class DilSozlukleri(unittest.TestCase):
    """COUPLINGS §12 · I18N.tr ile I18N.en aynı anahtarları taşımalı.

    Eksik anahtar sessizdir: metni yerleştiren satır `if (L[k])` diye kontrol
    ediyor, anahtar yoksa öğeye hiç dokunmuyor ve ekranda önceki dilin metni
    kalıyor. İngilizce sayfada tek bir Türkçe etiket, hata mesajı olmadan.
    """

    @unittest.skipUnless(shutil.which("node"), "node kurulu değil")
    def test_iki_sozluk_ayni_anahtarlari_ve_turleri_tasiyor(self):
        betik = """
        const fs = require("fs");
        const src = fs.readFileSync(process.argv[1], "utf8");
        const bas = src.indexOf("const I18N");
        const son = src.indexOf("\\n};", bas) + 3;
        const I18N = eval(src.slice(bas, son) + "; I18N");
        const tr = Object.keys(I18N.tr), en = Object.keys(I18N.en);
        console.log(JSON.stringify({
          trFazla: tr.filter((k) => !en.includes(k)),
          enFazla: en.filter((k) => !tr.includes(k)),
          turFarki: tr.filter((k) => en.includes(k) && typeof I18N.tr[k] !== typeof I18N.en[k]),
          statsEsit: JSON.stringify(Object.keys(I18N.tr.stats)) === JSON.stringify(Object.keys(I18N.en.stats)),
        }));
        """
        sonuc = json.loads(subprocess.run(
            ["node", "-e", betik, str(APP_JS)],
            capture_output=True, text=True, check=True,
        ).stdout)
        self.assertEqual(sonuc["trFazla"], [],
                         f"Türkçe sözlükte olup İngilizcede olmayan anahtar: "
                         f"{sonuc['trFazla']} · o öğeler İngilizce sayfada Türkçe kalır")
        self.assertEqual(sonuc["enFazla"], [],
                         f"İngilizce sözlükte olup Türkçede olmayan anahtar: {sonuc['enFazla']}")
        self.assertEqual(sonuc["turFarki"], [],
                         f"Değer türü ayrışan anahtar (biri işlev, öteki metin olabilir): "
                         f"{sonuc['turFarki']}")
        self.assertTrue(sonuc["statsEsit"],
                        "stats alt sözlüğü iki dilde aynı anahtarları taşımıyor")


class IkiDilOznitelikleri(unittest.TestCase):
    """`data-tr` yazan her öğe `data-en` de yazmalı, tersi de doğru.

    COUPLINGS §12 `app.js` içindeki sözlüğün iki dilde aynı anahtarları
    taşımasını denetliyor. Sayfaların mekanizması ayrı: Metin HTML
    özniteliğinde duruyor (`data-tr` / `data-en`) ve orada bir bekçi yoktu.

    Sessiz bozulma biçimi şu: Bir cümle güncellenirken yalnız `data-tr`
    değiştirilir ya da yeni bir satıra yalnız Türkçesi konur. Sayfa Türkçe
    kusursuz görünür, İngilizceye geçilince o satır **Türkçe kalır** ve
    hiçbir şey uyarmaz. Türkçe bakan kişi bunu hiç görmez.
    """

    def sayfalar(self):
        return sorted((ROOT / "site").glob("*.html"))

    def test_her_dil_ozniteliginin_esi_var(self):
        # Öznitelikler satıra bölünebiliyor, o yüzden etiketin tamamı okunuyor.
        #
        # Tırnak içi atlanmak ZORUNDA: `data-tr` değerinin içinde HTML var
        # (`<strong>…`), yani `>` karakteri taşıyor. Basit `<[^>]*>` kalıbı
        # etiketi oracıkta kesiyor ve `data-en`'i hiç görmüyor · ilk yazımda
        # tam olarak bu oldu ve bekçi iki yanlış alarm verdi.
        ETIKET = re.compile(r"""<[a-zA-Z](?:[^>"']|"[^"]*"|'[^']*')*>""", re.S)
        eksik, cift_sayisi = [], 0
        for y in self.sayfalar():
            for m in ETIKET.finditer(y.read_text(encoding="utf-8")):
                etiket = m.group()
                tr, en = "data-tr=" in etiket, "data-en=" in etiket
                if tr and en:
                    cift_sayisi += 1
                elif tr or en:
                    kalan = "data-en" if tr else "data-tr"
                    eksik.append(f"{y.name}: {kalan} yok → {etiket[:70]}…")

        self.assertEqual(eksik, [],
                         f"Dil özniteliği eşsiz kalmış: {eksik}")

        # Kalıp bozulursa hiç çift bulunmaz ve test sessizce yeşil yanar.
        self.assertGreater(cift_sayisi, 25,
                           f"Bulunan dil çifti beklenenden az ({cift_sayisi}): "
                           f"kalıp bozulmuş olabilir, denetim boşa dönüyor.")


class GeriBildirimAdresiUcSayfada(unittest.TestCase):
    """COUPLINGS §13 · aynı e-posta adresi üç dosyada, üç farklı biçimde yazılı.

    Parçalı yazımın sebebi bot taramasına karşı korunmak. Ama üç ayrı bölme
    biçimi kullanıldığı için metin karşılaştırması işe yaramıyor; parçaları
    birleştirip sonucu karşılaştırmak gerekiyor.

    Ayrışırsa o sayfadan gelen geri bildirim hiçbir yere ulaşmaz ve kullanıcı
    yazdığını sanır. Projede hata toplama olmadığı için (sıfır dış istek) bu tek
    kanal.
    """

    DOSYALAR = ["app.js", "home.js", "guide.js"]

    def adresler(self):
        """Adresin parçalarını çıkarır: **sırayı değil, malzemeyi**.

        Parçalar kaynakta yazıldığı sırayla birleşmiyor. `index.html`'de
        `var u = "burhanarikan", d = "yaani" + ".com", addr = u + "@" + d`
        yazıyor: `"@"` satırda en sonda geçiyor ama adreste ortada duruyor.
        Bu yüzden parçaları sırayla birleştirmek yanlış sonuç veriyor
        (ilk denemede `burhanarikanyaani.com@` çıktı).

        Sıralı bir karşılaştırma için ifadeyi gerçekten çalıştırmak gerekirdi.
        Onun yerine parçaların **kümesi** karşılaştırılıyor: adres değişirse
        parçalar da değişir. Bölme biçimi değişip adres aynı kalırsa test
        geçer, istenen davranış bu.
        """
        bulunan = {}
        for ad in self.DOSYALAR:
            for satir in (ROOT / "site" / ad).read_text(encoding="utf-8").splitlines():
                if "burhanarikan" not in satir:
                    continue
                # Ad başka bağlamlarda da geçiyor · depo adresi gibi. Adresi
                # KURAN satır "@" parçasını taşıyor, ötekiler taşımıyor.
                # Bu daraltma bir yanlış alarmdan sonra kondu: KAYNAK.md'ye
                # verilen github bağlantısı ikinci bir "adres" sanılmıştı.
                if '"@"' not in satir:
                    continue
                parcalar = tuple(sorted(p for p in re.findall(r'"([^"]*)"', satir) if p))
                bulunan.setdefault(ad, set()).add(parcalar)
        return bulunan

    def test_uc_dosyada_ayni_adres(self):
        bulunan = self.adresler()
        eksik = [a for a in self.DOSYALAR if a not in bulunan]
        self.assertEqual(eksik, [], f"Geri bildirim adresi bulunamadı: {eksik}")
        birlesim = set().union(*bulunan.values())
        self.assertEqual(
            len(birlesim), 1,
            f"Geri bildirim adresi dosyalar arasında ayrışmış, o sayfadan gelen "
            f"geri bildirim hiçbir yere ulaşmaz:\n  "
            + "\n  ".join(f"{k}: {sorted(v)}" for k, v in bulunan.items()))

    def test_adres_duz_metin_yazilmamis(self):
        """Parçalı yazım korumasının kazara kaldırılmasını yakalar."""
        for ad in self.DOSYALAR:
            metin = (ROOT / "site" / ad).read_text(encoding="utf-8")
            with self.subTest(dosya=ad):
                self.assertNotIn("burhanarikan@", metin,
                                 f"{ad}: adres düz metin yazılmış; bot taramasına açık. "
                                 f"Parçalı yazım korunmalı.")


class AppJsTuzaklari(unittest.TestCase):
    """Bağlaşım değil: bir kez düşüp bir daha düşmek istemediğimiz tuzaklar.

    Bu dosyada duruyorlar çünkü mekanizmaları aynı: kaynağı okuyup kalıp arayan
    ucuz denetimler.
    """

    def test_tek_tirnakli_oznitelik_kullanilmiyor(self):
        """`esc` tek tırnağı (`'`) kaçırmıyor, bu yalnız KOŞULLU olarak güvenli.

        Kaçış işlevi `& < > "` karakterlerini değiştiriyor. Çift tırnaklı bir
        özniteliğin içinde bu yeterli. Ama biri `href='${...}'` diye tek tırnak
        kullanırsa, veriden gelen bir `'` özniteliği kapatıp yenisini açabilir:
        `a' onerror='...`

        Bugün dosyada tek tırnaklı öznitelik yok. Denetim, o durumun sessizce
        oluşmasını engelliyor.
        """
        bulunan = re.findall(r"=\s*'\$\{", APP_KAYNAK)
        self.assertEqual(bulunan, [],
                         "Tek tırnaklı öznitelik içinde değer basılmış. esc() tek tırnağı "
                         "kaçırmadığı için bu bir açık oluşturur: ya çift tırnak kullanın "
                         "ya da esc'e ' eklensin.")

    def test_veriden_gelen_baglantilar_protokol_denetiminden_geciyor(self):
        """`href` içine veriden gelen adres konuyorsa şeması denetlenmeli.

        `esc` bir adresi zararsız hâle getirmez: `javascript:alert(1)` kaçış
        işleminden değişmeden geçer ve bağlantıya tıklayan kişide çalışır.
        Koruma kaçıştan değil, **şema denetiminden** geliyor:
        `/^https?:\\/\\//i.test(a.website)`.
        """
        # `href="${esc(...)}"` biçiminde veri basan satırların yakınında
        # ya http(s) denetimi ya da sabit bir şema (mailto:) olmalı.
        for m in re.finditer(r'href="\$\{esc\(([^)]+)\)\}"', APP_KAYNAK):
            baglam = APP_KAYNAK[max(0, m.start() - 300):m.start()]
            with self.subTest(kaynak=m.group(1)):
                self.assertRegex(baglam, r"\^https\?:",
                                 f"`{m.group(1)}` doğrudan href'e basılıyor ama yakınında "
                                 f"protokol denetimi yok. javascript: şeması esc'ten geçer.")

    def test_cok_parametreli_yardimcilar_diziye_dogrudan_verilmiyor(self):
        """`arr.filter(match)` yazma tuzağı.

        Dizi metotları geri çağrıya (öğe, sıra, dizi) geçirir. `match(a, alanAtla)`
        gibi ikinci parametresi olan bir fonksiyon doğrudan verilirse sıra numarası
        o parametreye düşer ve 0 dışındaki her kayıt için doğru sayılır.

        Gerçekten oldu: alan filtresi seçiliyken 39 yerine 466 sonuç göründü,
        çünkü ilk kayıt hariç hepsinde alan koşulu atlandı. Sessizce yanlış
        sonuç veriyordu; hata da vermiyordu.
        """
        COK_PARAMETRELI = ["match"]
        DIZI_METOTLARI = "filter|map|some|every|find|findIndex|flatMap|forEach"
        for ad in COK_PARAMETRELI:
            kalip = rf"\.({DIZI_METOTLARI})\(\s*{ad}\s*\)"
            bulunan = re.findall(kalip, APP_KAYNAK)
            with self.subTest(fonksiyon=ad):
                self.assertEqual(bulunan, [],
                                 f"`{ad}` bir dizi metoduna doğrudan verilmiş "
                                 f"({bulunan}). Sarmalayın: `.filter((a) => {ad}(a))`")


class DisIstekYasagi(unittest.TestCase):
    """Projenin en çok tekrarlanan iddiası, uzun süre bekçisizdi.

    README: "çalışma anında dış istek yok (fontlar dahil her şey pakette)".
    Birinci gerekçe gizlilik: Dış sunucudan yazı tipi çekmek, ziyaretçinin
    adresini o sunucuya bildirmek demek. Yazı tiplerini depoya koymanın lisans
    yükümlülüğü bile bu yüzden üstlenildi.

    İddia her yerde yazılıydı, hiçbir yerde denetlenmiyordu. Boşluk, depoya
    dışarıdan eklenen bir sayfanın Google Fonts çağırmasıyla ortaya çıktı.
    """

    def test_hicbir_yayin_klasoru_dis_istek_yapmiyor(self):
        """Projenin en çok tekrarlanan iddiası, bugüne kadar bekçisizdi.

        README: "çalışma anında dış istek yok (fontlar dahil her şey pakette)".
        Gerekçesi gizlilik: Dış sunucudan yazı tipi çekmek, ziyaretçinin
        adresini o sunucuya bildirmek demek.

        İddia her yerde yazılıydı, **hiçbir yerde denetlenmiyordu.** Boşluk,
        dışarıdan eklenen bir sayfanın Google Fonts çağırmasıyla ortaya çıktı.

        AYRIM ÖNEMLİ, yoksa yanlış alarm verir:

          ÇALIŞMA ANI İSTEĞİ → <link>, <script src>, @import, css url()
                               Sayfa açılırken kendiliğinden gidiyor. İhlal.
          KULLANICI BAĞLANTISI → <a href="https://...">
                               Kullanıcı tıklarsa gidiyor. İhlal DEĞİL.

        İlk ölçüm bu ayrımı yapmadığı için `site/` klasöründe altı "ihlal"
        saymıştı; hepsi rehber sayfasındaki resmî bağlantılardı.
        """
        # JAVASCRIPT TARAFI SONRADAN EKLENDİ VE BİR MUTASYON KAÇTIĞI İÇİN.
        #
        # İlk hâli yalnız işaretlemeye bakıyordu: <link>, <script src>,
        # @import, css url(). Yani app.js'e konan bir fetch("https://...")
        # bekçinin görüş alanının tümüyle dışındaydı · üstelik bugün dış istek
        # eklemenin EN OLASI yolu o.
        #
        # Kapsam adres dizesine değil, İSTEK BAŞLATAN ÇAĞRIYA bakıyor. Sebep
        # yanlış alarm: JavaScript'te üretilen bir <a href="https://..."> dış
        # istek değil, kullanıcı bağlantısı · yukarıdaki ayrımın aynısı.
        # Ölçüldü: site/*.js bugün hiç mutlak adres taşımıyor, yani bu kapsam
        # bugün sıfır yanlış alarm veriyor.
        #
        # `<link>` her zaman istek üretmiyor ve ayrım `rel` değerinde.
        # `stylesheet`, `icon`, `preload`, `preconnect` gibi değerler tarayıcıyı
        # o adrese GÖNDERİYOR · ihlal. `canonical` ise üstveri: Arama motoruna
        # "bu sayfanın asıl adresi budur" diyor, tarayıcı hiçbir şey çekmiyor.
        #
        # Ayrım dar tutuldu: YALNIZ canonical muaf. Yeni bir rel değeri
        # çıktığında bekçi yine ötüyor ve bakan kişi karar veriyor.
        KALIPLAR = [
            (r'<link(?![^>]+rel=["\']canonical["\'])[^>]+href=["\'](https?://[^"\']+)', "<link>"),
            (r'<script[^>]+src=["\'](https?://[^"\']+)', "<script src>"),
            (r'@import\s+url\(["\']?(https?://[^"\')]+)', "@import"),
            (r'url\(["\']?(https?://[^"\')]+)', "css url()"),
            # JavaScript tarafı · bkz. aşağıdaki not
            (r'\bfetch\s*\(\s*["\'`](https?://[^"\'`]+)', "fetch()"),
            (r'\.open\s*\(\s*["\'][A-Z]+["\']\s*,\s*["\'`](https?://[^"\'`]+)', "XMLHttpRequest"),
            (r'\bimport\s*\(\s*["\'`](https?://[^"\'`]+)', "dinamik import()"),
            (r'\bnew\s+(?:WebSocket|EventSource)\s*\(\s*["\'`]((?:wss?|https?)://[^"\'`]+)', "canlı bağlantı"),
            (r'\bsendBeacon\s*\(\s*["\'`](https?://[^"\'`]+)', "sendBeacon()"),
            (r'\bimportScripts\s*\(\s*["\'`](https?://[^"\'`]+)', "importScripts()"),
            (r'\.src\s*=\s*["\'`](https?://[^"\'`]+)', ".src ataması"),
        ]
        bulgu = []
        for klasor in ("site",):
            kok = ROOT / klasor
            if not kok.exists():
                continue
            for yol in sorted(kok.rglob("*")):
                if yol.suffix not in (".html", ".css", ".js"):
                    continue
                metin = yol.read_text(encoding="utf-8")
                for kalip, tur in KALIPLAR:
                    for mm in re.finditer(kalip, metin):
                        bulgu.append(f"{klasor}/{yol.name} · {tur} · {mm.group(1)[:48]}")
        self.assertEqual(sorted(set(bulgu)), [],
                         f"Çalışma anında dış istek yapılıyor: {sorted(set(bulgu))}\n"
                         f"Bu, README'de ve fonts-css.md'de yazılı 'sıfır dış istek' "
                         f"ilkesini çiğniyor ve gerekçesi gizlilik: Ziyaretçinin "
                         f"adresi üçüncü bir tarafa bildirilmiş oluyor.")


class Sitemap(unittest.TestCase):
    """`sitemap.xml` kayıtlı her üniversitenin sayfalarını taşımalı.

    Dosya `build_data.py` tarafından `universities.json`'dan üretiliyor, yani
    elle güncellenmesi gereken bir yer değil. Ama **üretimin doğru olduğu ayrı
    bir iddia** ve denetlenmezse şöyle bozuluyor: Yeni bir üniversite ekleniyor,
    üretici bir sebeple onu atlıyor, site çalışmaya devam ediyor ve o kurumun
    sayfaları **hiçbir aramada çıkmıyor.** Hiçbir hata görünmüyor.

    Rehberi olmayan üniversitenin rehber sayfası bilerek listelenmiyor · o
    sayfa o kurum için boş.
    """

    def kayit(self):
        return json.loads((ROOT / "site" / "universities.json").read_text(encoding="utf-8"))

    def test_her_universitenin_sayfalari_sitemapte(self):
        yol = ROOT / "site" / "sitemap.xml"
        self.assertTrue(yol.exists(), "sitemap.xml üretilmemiş.")
        harita = yol.read_text(encoding="utf-8")
        uni = self.kayit()
        self.assertGreater(len(uni), 0, "universities.json boş: denetim boşa dönüyor.")

        eksik = []
        for u in uni:
            if f"agreements.html?uni={u['id']}" not in harita:
                eksik.append(f"{u['id']} → anlaşma sayfası")
            if u.get("hasGuide") and f"guide.html?uni={u['id']}" not in harita:
                eksik.append(f"{u['id']} → rehber sayfası")
        self.assertEqual(eksik, [],
                         f"sitemap.xml bu sayfaları taşımıyor: {eksik}. "
                         f"O sayfalar aramalarda çıkmaz ve hiçbir hata görünmez.")

        self.assertIn("index.html", harita, "sitemap.xml giriş sayfasını taşımıyor.")

    def test_rehbersiz_universitenin_rehberi_listelenmiyor(self):
        """Yanlış alarmın tersi: Olmayan bir sayfayı bildirmek de hata.

        Arama motoruna var olmayan bir adres bildirmek, o adresi tarayıp boş
        bulmasına yol açıyor. Bekçi iki yöne birden bakıyor.
        """
        harita = (ROOT / "site" / "sitemap.xml").read_text(encoding="utf-8")
        fazla = [u["id"] for u in self.kayit()
                 if not u.get("hasGuide") and f"guide.html?uni={u['id']}" in harita]
        self.assertEqual(fazla, [],
                         f"Rehberi olmayan üniversitenin rehber sayfası sitemap'te: {fazla}")


class RenkKontrasti(unittest.TestCase):
    """Metin/zemin kontrastı WCAG AA eşiğini geçmeli.

    Eşik 4.5:1 · 18.66px'ten küçük normal metin için. Buradaki kullanımların
    hepsi 10–15px arası, yani hiçbiri "büyük metin" istisnasına girmiyor.

    Neden yayın öncesi engel: düşük kontrast, az gören kullanıcılar için bilgiyi
    okunamaz yapar. Etkilenen kişi bunu bize bildiremez -- okuyamadığı şeyin
    orada olduğunu bilmez.

    Değerler tokens.css'ten okunuyor; renk değişince test kendiliğinden yeniden
    ölçüyor.
    """

    ESIK = 4.5
    BEYAZ = "#FFFFFF"

    def tokenlar(self):
        metin = (ROOT / "site" / "tokens.css").read_text(encoding="utf-8")
        return dict(re.findall(r"(--[a-z0-9-]+):\s*(#[0-9A-Fa-f]{6})", metin))

    def test_metin_renkleri_aa_esigini_geciyor(self):
        tk = self.tokenlar()
        kagit = tk.get("--bg-paper", "#F1F4F8")

        # (token, zemin, nerede kullanıldığı, punto)
        kullanimlar = [
            ("--ink",        self.BEYAZ, "gövde metni",                 "15px"),
            ("--ink-2",      self.BEYAZ, "ikincil metin",               "13.5px"),
            ("--ink-3",      self.BEYAZ, "kart alt satırı",             "12px"),
            ("--ink-3",      kagit,      "sonuç sayısı / alan uyarısı", "12.5–13px"),
            ("--ink-4",      self.BEYAZ, "kart notu, arama yer tutucusu", "12–15px"),
            ("--ink-4",      kagit,      "boş sonuç mesajı",            "normal"),
            ("--brand-blue", self.BEYAZ, "kart bağlantıları (beyaz kart)", "12px"),
            ("--brand-blue", kagit,      "Temizle düğmesi (kağıt zemin)",  "13px"),
            # Chip labels sit on their own tinted background, not on white.
            # These two pairs are the reason --success-ink / --warning-ink
            # exist: --success and --warning score 3.71 and 2.92 here.
            ("--success-ink", tk.get("--success-mist", "#E5F3EB"),
             "kontenjan çipi", "11px"),
            ("--warning-ink", tk.get("--warning-mist", "#FBEEDE"),
             "dil çipi", "11px"),
        ]
        # A missing token used to be skipped silently. That made the check
        # green exactly when a color had been deleted or renamed -- the case
        # where it matters most. Now it fails.
        yok = sorted({t for t, *_ in kullanimlar if not tk.get(t)})
        self.assertEqual(yok, [],
                         f"Kontrast denetiminin okuduğu jeton tokens.css'te yok: {yok}\n"
                         f"Yeniden adlandırıldıysa buradaki liste de güncellenmeli · "
                         f"yoksa o renk hiç ölçülmüyor.")

        kusurlu = []
        for token, zemin, yer, punto in kullanimlar:
            renk = tk.get(token)
            o = kontrast(renk, zemin)
            if o < self.ESIK:
                kusurlu.append(f"{token} ({renk}) · {yer} · {punto} · {o:.2f}:1")

        self.assertEqual(
            kusurlu, [],
            "WCAG AA (4.5:1) eşiğinin altında kalan metin renkleri:\n  "
            + "\n  ".join(kusurlu)
            + "\n\nBunlar gerçek içerik: kontenjan notu, boş sonuç mesajı, e-posta "
              "bağlantısı. Düzeltme bir marka kararı olduğu için renkler burada "
              "değiştirilmedi; karar verilince tokens.css güncellenmeli."
        )


class PaletKacagi(unittest.TestCase):
    """Palet rengi yalnız `tokens.css`'te tanımlanır.

    Kural yazılıydı ("hardcoded yeni renk eklemeyin") ve hiçbir şey onu
    denetlemiyordu · üç renk sızmıştı. İkisi daha kötüsüydü: Çipin **zemini**
    jetondan geliyordu, **metni** sabitti. Yani yarısı kayıtlı, yarısı değil.

    Sabit değerlerin bir sebebi vardı ve o sebep hiçbir yerde yazılı değildi:
    `--success` ve `--warning`, kendi puslu zeminlerinde AA'nın altında kalıyor
    (3.71 ve 2.92). Biri "temizlik" yapıp jetona çevirse **kontrast sessizce
    düşecekti** ve kontrast bekçisi bunu göremezdi · o, yalnız `tokens.css`'i
    okuyor, `styles.css`'in hangi jetonu nerede kullandığını değil.

    Bugün üçü de jeton ve ikisi kontrast denetiminin kapsamında.

    **Beyaz ve siyah kapsam dışı ve bu bilerek.** `#fff` ile
    `rgba(255,255,255,.25)` palet rengi değil · koyu marka zemininin üstünde
    metin ve ayraç. Otuz dört kullanımı var ve jetonlamak onları okunur
    yapmazdı, yalnız uzatırdı.
    """

    SAYFA = ("styles.css", "fonts.css")
    RENK = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)")

    def notr(self, deger):
        """Beyaz, siyah ve saydam hâlleri · palet değil."""
        d = deger.lower().replace(" ", "")
        if d in ("#fff", "#ffffff", "#000", "#000000", "transparent"):
            return True
        return bool(re.match(r"rgba?\((255,255,255|0,0,0)", d))

    def test_tokens_disinda_palet_rengi_yok(self):
        kacak = []
        for ad in self.SAYFA:
            p = ROOT / "site" / ad
            if not p.exists():
                continue
            for i, satir in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                for deger in self.RENK.findall(satir):
                    if not self.notr(deger):
                        kacak.append(f"{ad}:{i} · {deger}")
        self.assertEqual(kacak, [],
                         "Palet rengi tokens.css dışında tanımlanmış:\n  "
                         + "\n  ".join(kacak)
                         + "\n\nJeton olarak ekleyin · gerekçesiyle birlikte.")

    def test_tokens_gercekten_palet_tasiyor(self):
        """Alt sınır · kalıp bozulursa üstteki test hiçbir şey bulamaz."""
        metin = (ROOT / "site" / "tokens.css").read_text(encoding="utf-8")
        n = len(re.findall(r"--[a-z0-9-]+:\s*(?:#[0-9A-Fa-f]{3,8}|rgba?\()", metin))
        self.assertGreaterEqual(n, 20,
                                f"tokens.css'te yalnız {n} renk jetonu var; "
                                f"palet başka yere taşınmış olabilir.")


class KarsiliksizDegisken(unittest.TestCase):
    """Tanımı olmayan bir CSS değişkeni sessizce yok sayılır.

    `var(--yok)` yazıldığında tarayıcı hata vermiyor, konsola bir şey düşmüyor:
    bildirim tümüyle atılıyor ve **beklenen görünüm oluşmuyor.** Bu bir süre
    "çözülemez" sayıldı ve yanlıştı: Tanımlar ve kullanımlar aynı dosyalardan
    okunuyor, eşleşmeyen ve yedeği olmayan her kullanım hata.

    Bulunduğunda gerçek bir hata duruyordu: `.source-diff-mark` rozeti
    `var(--bg-2)` istiyordu, o ad hiçbir yerde tanımlı değildi ve rozetin
    dolgusu hiç boyanmıyordu. Rozet, kaynaktan ayrıldığımız kayıtları gösteren
    iz · yani sessizce kaybolan şey, `KAYNAK.md`'nin öğrenciye göstermeyi vaat
    ettiği bilginin kendisiydi.

    Yedekli kullanım (`var(--x, #fff)`) hata değil: Tanım bulunmazsa yedek
    devreye giriyor, yani sessizlik yok.
    """

    # Tanım: `--ad:` · Kullanım: `var(--ad` · ikinci grup yedek olup olmadığı
    TANIM = re.compile(r"(--[a-z0-9-]+)\s*:")
    KULLANIM = re.compile(r"var\(\s*(--[a-z0-9-]+)\s*(,)?")

    def dosyalar(self):
        return sorted((ROOT / "site").glob("*.css")) + sorted((ROOT / "site").glob("*.html"))

    def test_her_degiskenin_karsiligi_var(self):
        dosyalar = self.dosyalar()
        tanimli = set()
        for y in dosyalar:
            tanimli |= set(self.TANIM.findall(y.read_text(encoding="utf-8")))

        karsiliksiz, kullanim_sayisi = [], 0
        for y in dosyalar:
            for m in self.KULLANIM.finditer(y.read_text(encoding="utf-8")):
                kullanim_sayisi += 1
                if m.group(2):          # yedeği var, sessizlik yok
                    continue
                if m.group(1) not in tanimli:
                    karsiliksiz.append(f"{y.name} → var({m.group(1)})")

        self.assertEqual(karsiliksiz, [],
                         f"Tanımı olmayan CSS değişkeni yedeksiz kullanılmış. "
                         f"Tarayıcı bildirimi sessizce atar: {karsiliksiz}")

        # Kalıp bozulursa hiç kullanım bulunmaz ve test sessizce yeşil yanar.
        self.assertGreater(kullanim_sayisi, 150,
                           f"var() kullanımı beklenenden az ({kullanim_sayisi}): "
                           f"kalıp bozulmuş olabilir, denetim boşa dönüyor.")


class EmojiEnvanteri(unittest.TestCase):
    """Emoji üründe var ve kayıtsızdı; bu bekçi kaydı tutuyor.

    Marka kuralı emojiyi tümden yasaklamıyor, kayıtsız büyümesini yasaklıyor.
    Bugün kullanılanların hepsinin bir işi var ve aşağıda gerekçesiyle yazılı.
    Yeni bir emoji eklendiğinde test kırılıyor ve ekleyen kişi ya gerekçesini
    buraya yazıyor ya da vazgeçiyor.

    Ayrım şu: Ülke bayrakları **veri gösteriyor**, ötekiler **arayüz durumu**
    bildiriyor. Süs olan yok. Süs olan biri eklenirse bu liste onu kabul
    etmeyecek, çünkü listeye girmek için gerekçe yazmak gerekiyor.

    Bayraklar tek tek yazılmıyor: Bölgesel gösterge harf çiftleri (U+1F1E6
    → U+1F1FF) blok olarak muaf. Yeni bir ülke eklendiğinde bayrağı da
    kendiliğinden gelsin, bekçi boşuna kırılmasın.
    """

    IZINLI = {
        "⚙": "⚙ · filtre düğmesinin ikonu (agreements.html, app.js I18N)",
        "\U0001F9ED": "🧭 · boş sonuç ve rehber sayfasının durum ikonu",
        "⚠": "⚠ · veri yüklenemedi hatasının durum ikonu",
        "✉": "✉ · giriş sayfasındaki iletişim bağlantısının ikonu",
        "\U0001F3F3": "🏳 · ülke bayrağı bilinmediğinde kullanılan yedek",
    }

    # Bayrak = iki bölgesel gösterge harfi. Blok olarak muaf.
    BAYRAK = re.compile(r"[\U0001F1E6-\U0001F1FF]")

    # Değişken seçici ve sıfır genişlikli birleştirici: emojinin kendisi değil,
    # sunum biçimini belirleyen görünmez işaretler. Sayıma girmiyorlar.
    GORUNMEZ = re.compile(r"[︎️‍]")

    EMOJI = re.compile(
        r"[\U0001F300-\U0001FAFF☀-➿⬀-⯿️]")

    def test_urunde_kayitsiz_emoji_yok(self):
        yabanci = []
        for yol in sorted((ROOT / "site").glob("*.*")):
            if yol.suffix not in (".html", ".js", ".css"):
                continue
            metin = self.GORUNMEZ.sub("", yol.read_text(encoding="utf-8"))
            metin = self.BAYRAK.sub("", metin)
            for n, satir in enumerate(metin.split("\n"), 1):
                for e in self.EMOJI.findall(satir):
                    if e in self.IZINLI:
                        continue
                    yabanci.append(f"{yol.name}:{n} → {e} (U+{ord(e):04X})")
        self.assertEqual(
            yabanci, [],
            "Kayıtlı olmayan emoji ürüne girmiş:\n  "
            + "\n  ".join(yabanci)
            + "\n\nEmoji yasak değil, kayıtsız emoji yasak. Kullanmak "
              "gerekiyorsa EmojiEnvanteri.IZINLI listesine gerekçesiyle "
              "eklensin. Gerekçe yazılamıyorsa emoji de gerekmiyordur.")

    def test_izinli_listesi_olu_kayit_tasimiyor(self):
        """Kaldırılan bir emoji listede kalırsa liste gerçeği anlatmaz.

        `4.4a`nın uygulaması: Bu testin kırılması iyi haber de olabilir,
        emojinin arayüzden çıkarıldığı anlamına gelir. O zaman satır silinir.
        """
        metin = ""
        for yol in sorted((ROOT / "site").glob("*.*")):
            if yol.suffix in (".html", ".js", ".css"):
                metin += yol.read_text(encoding="utf-8")
        metin = self.GORUNMEZ.sub("", metin)
        kullanilmayan = [f"{e} {gerekce}" for e, gerekce in self.IZINLI.items()
                         if e not in metin]
        self.assertEqual(
            kullanilmayan, [],
            "İzinli listesinde artık kullanılmayan emoji var:\n  "
            + "\n  ".join(kullanilmayan)
            + "\n\nArayüzden çıkarıldıysa listeden de çıkarılmalı.")


if __name__ == "__main__":
    unittest.main()


class IcerikGuvenligiPolitikasi(unittest.TestCase):
    """Her sayfa CSP taşıyor ve politika ödün vermiyor.

    Site üçüncü taraf hiçbir şey yüklemiyor, yani CSP'nin maliyeti sıfır ·
    kısıtladığı hiçbir şeyi zaten kullanmıyoruz. Kazancı ise ölçülebilir: Bir
    gün veriden gelen bir metin kaçırılmadan ekrana basılsa bile tarayıcı onu
    çalıştırmıyor.

    Bu özellikle **başka bir kurumun sunucusuna teslim** senaryosunda önemli.
    Site bir üniversitenin kendi alan adı altında dururken bir XSS açığı, o
    alan adına ait çerezlere erişim demek olurdu.

    ÜÇ ŞEY BURADA DENETLENİYOR VE ÜÇÜ DE BİR ÖLÇÜMDEN GELİYOR

    1. Politika her sayfada var.
    2. Satır içi script YOK. `script-src 'self'` satır içi script'i
       engelliyor · biri eklerse sayfa sessizce çalışmayı bırakıyor. Bu
       gerçekten oldu: Politika yazıldığında `index.html` 78, `guide.html` 50
       satır satır içi betik taşıyordu ve ikisi de ayrı dosyaya taşındı.
    3. Politika `unsafe-inline` ya da `unsafe-eval` İÇERMİYOR. İkisinden biri
       eklendiği an politika işlevini büyük ölçüde kaybediyor · ölçüldü,
       bugün hiçbirine ihtiyaç yok (satır içi `<style>` ve `style=` özniteliği
       de sıfır).

    `frame-ancestors` bilerek YOK: Tarayıcı onu `<meta>` ile yok sayıyor ve
    konsola uyarı basıyor. Yeri HTTP başlığı · README'de sunucu tarafı
    başlıklarla birlikte yazılı.
    """

    SAYFALAR = ("index.html", "agreements.html", "guide.html")
    YASAK = ("unsafe-inline", "unsafe-eval", "'*'", "http://", "https://")

    def politika(self, ad):
        metin = (ROOT / "site" / ad).read_text(encoding="utf-8")
        m = re.search(r'http-equiv="Content-Security-Policy"\s+content="([^"]+)"', metin)
        return m.group(1) if m else None

    def test_her_sayfada_politika_var(self):
        eksik = [a for a in self.SAYFALAR if not self.politika(a)]
        self.assertEqual(eksik, [], f"CSP taşımayan sayfa: {eksik}")

    def test_politika_odun_vermiyor(self):
        kusur = []
        for ad in self.SAYFALAR:
            p = self.politika(ad) or ""
            for y in self.YASAK:
                if y in p:
                    kusur.append(f"{ad}: {y}")
            if "default-src 'none'" not in p:
                kusur.append(f"{ad}: default-src 'none' yok")
            if "script-src 'self'" not in p:
                kusur.append(f"{ad}: script-src 'self' yok")
        self.assertEqual(kusur, [],
                         "CSP zayıflatılmış:\n  " + "\n  ".join(kusur)
                         + "\n\nBir yönerge gerekiyorsa sebebi yazılmalı · "
                           "unsafe-inline eklemek politikayı büyük ölçüde iptal eder.")

    def test_satir_ici_script_yok(self):
        """`script-src 'self'` satır içi script'i çalıştırmaz · sayfa sessizce ölür."""
        bulgu = []
        for ad in self.SAYFALAR:
            metin = (ROOT / "site" / ad).read_text(encoding="utf-8")
            for blok in re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", metin, re.S):
                if blok.strip():
                    bulgu.append(f"{ad}: {len(blok.splitlines())} satır")
        self.assertEqual(bulgu, [],
                         f"Satır içi script CSP altında ÇALIŞMAZ ve hata konsola "
                         f"düşer, sayfa boş görünür: {bulgu}\n"
                         f"Ayrı bir .js dosyasına taşıyın.")

    def test_satir_ici_stil_yok(self):
        """`style-src 'self'` ödün vermiyor · öyle kalabilmesi buna bağlı."""
        bulgu = []
        for ad in self.SAYFALAR:
            metin = (ROOT / "site" / ad).read_text(encoding="utf-8")
            n = len(re.findall(r"<style[\s>]", metin)) + len(re.findall(r'\sstyle="', metin))
            if n:
                bulgu.append(f"{ad}: {n}")
        self.assertEqual(bulgu, [],
                         f"Satır içi stil bulundu: {bulgu}\nCSP'ye 'unsafe-inline' "
                         f"eklemek gerekirdi; stil dosyaya taşınmalı.")


class LlmsTxtKapsami(unittest.TestCase):
    """`llms.txt` kayıtlı her üniversiteyi listelemeli.

    Dosya **elle** tutuluyor · `sitemap.xml`'in aksine üretilmiyor, çünkü
    içindeki metnin çoğu anlatı. Ama sayfa listesi anlatı değil, veri: Yeni bir
    üniversite eklendiğinde oraya da girmesi gerekiyor.

    Nitekim girmedi. Marmara ve ESOGÜ eklendikten sonra `llms.txt` hâlâ yalnız
    MAKÜ'nün sayfalarını gösteriyordu · sitemap üretildiği için doğruydu,
    llms.txt elle tutulduğu için eskimişti. Aynı sınıf, aynı risk, farklı
    mekanizma.

    Bekçi üretmiyor, **eksikliği söylüyor.** Dosyayı üretmek anlatıyı da
    üretmek olurdu; asıl istenen o değil.
    """

    def kayit(self):
        return json.loads((ROOT / "site" / "universities.json").read_text(encoding="utf-8"))

    def test_her_universite_llms_txtde(self):
        yol = ROOT / "site" / "llms.txt"
        self.assertTrue(yol.exists(), "llms.txt yok.")
        metin = yol.read_text(encoding="utf-8")
        uni = self.kayit()
        self.assertGreater(len(uni), 0, "universities.json boş: denetim boşa dönüyor.")
        eksik = [u["id"] for u in uni
                 if f"agreements.html?uni={u['id']}" not in metin]
        self.assertEqual(eksik, [],
                         f"llms.txt bu üniversitelerin anlaşma sayfasını "
                         f"listelemiyor: {eksik}\nYeni üniversite eklendiğinde "
                         f"llms.txt de elle güncellenmeli.")

    def test_llms_txt_olmayan_universite_uydurmuyor(self):
        """Ters yön · listeden çıkarılan bir kurum llms.txt'de kalmamalı."""
        metin = (ROOT / "site" / "llms.txt").read_text(encoding="utf-8")
        kayitli = {u["id"] for u in self.kayit()}
        gecen = set(re.findall(r"agreements\.html\?uni=([a-z0-9-]+)", metin))
        fazla = gecen - kayitli
        self.assertEqual(fazla, set(),
                         f"llms.txt kayıtlı olmayan üniversite gösteriyor: {fazla}")


class KaldirmaSozuUcSayfada(unittest.TestCase):
    """Koşulsuz kaldırma sözü üç sayfada da görünmeli.

    `KAYNAK.md` kuruma şunu veriyor: *"Veriniz kaldırılsın · tartışmasız
    kaldırılır, gerekçe sorulmaz."* Söz orada yazılıydı ve **sitede hiçbir
    yerde görünmüyordu** · yani sözü okuyabilecek tek yer depoydu ve kurum
    depoya bakmıyor.

    Bir sözün koruyuculuğu görünürlüğüne bağlı. Altbilgiye gömülü olması bile
    hiç olmamasından iyi; okunmadığı iddia edilebilen bir yerde durması ise
    sözün kendisini zayıflatıyor.

    ÜÇ SAYFA ÇÜNKÜ ÜÇÜ DE AYRI KOD YOLU

    `index.html` → home.js, `guide.html` → guide.js, `agreements.html` →
    app.js. Biri güncellenip öteki unutulduğunda hiçbir şey kırılmıyor ·
    bu depoda tam olarak bu oldu: İletişim satırı iki sayfada "düzeltme ve
    kaldırma talepleri" derken anlaşma sayfasında yalnız "Geri bildirim"
    diyordu. Anlaşma listesine bakan bir kurum, kaldırma talebinde
    bulunabileceğini o sayfadan öğrenemiyordu.
    """

    DOSYALAR = ("home.js", "guide.js", "app.js")
    TR_IZ = "gerekçe sorulmadan"
    EN_IZ = "without asking for a reason"

    def test_soz_uc_kod_yolunda_da_var(self):
        eksik = []
        for ad in self.DOSYALAR:
            metin = (ROOT / "site" / ad).read_text(encoding="utf-8")
            if self.TR_IZ not in metin:
                eksik.append(f"{ad} · Türkçe söz yok")
            if self.EN_IZ not in metin:
                eksik.append(f"{ad} · İngilizce söz yok")
        self.assertEqual(eksik, [],
                         f"Koşulsuz kaldırma sözü eksik: {eksik}\n"
                         f"KAYNAK.md bu sözü veriyor · sitede görünmeyen bir söz, "
                         f"kurumun okuyamadığı bir sözdür.")

    def test_iletisim_adresi_uc_sayfada_da_yaziyor(self):
        """Söz var ama adres yoksa söz işe yaramıyor."""
        eksik = [ad for ad in self.DOSYALAR
                 if "burhanarikan" not in (ROOT / "site" / ad).read_text(encoding="utf-8")]
        self.assertEqual(eksik, [], f"İletişim adresi olmayan sayfa: {eksik}")

    def test_neyin_yazilabilecegi_uc_sayfada_da_ayni(self):
        """Adresin YANINDAKİ cümle de aynı olmalı.

        `guide.js` bir süre yalnız "Geri bildirim:" diyordu, ötekiler
        "düzeltme ve kaldırma talepleri" diyordu. Adres üçünde de vardı, yani
        adres bekçisi yeşildi · ama rehber sayfasına bakan bir kurum, oraya
        KALDIRMA talebi yazabileceğini o cümleden anlayamıyordu.

        Söz bir alt satırda duruyor, dolayısıyla bilgi tümüyle kaybolmuyor.
        Yine de iki cümle aynı şeyi söylemeli · yoksa hangisinin geçerli
        olduğu okuyucuya kalıyor.
        """
        iz = ("düzeltme ve kaldırma talepleri", "corrections and removal requests")
        eksik = []
        for ad in self.DOSYALAR:
            metin = (ROOT / "site" / ad).read_text(encoding="utf-8")
            for parca in iz:
                if parca not in metin:
                    eksik.append(f"{ad} · {parca!r} yok")
        self.assertEqual(eksik, [],
                         f"İletişim satırının açıklaması sayfalar arasında ayrışmış: {eksik}")


class YayinaHazirlikIcerigi(unittest.TestCase):
    """Yayına çıkmadan önce kullanıcıya görünen güven ve yardım metinleri."""

    def test_ana_sayfa_javascript_kapaliyken_aciklama_sunar(self):
        metin = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn("<noscript>", metin)
        self.assertIn("JavaScript", metin)
        self.assertIn("universities", metin)

    def test_anlasma_ekrani_okuma_rehberini_iki_dilde_tasiyor(self):
        metin = (ROOT / "site" / "agreements.html").read_text(encoding="utf-8")
        js = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        self.assertIn('data-i18n="readingGuideTitle"', metin)
        self.assertIn('data-i18n="readingGuideText"', metin)
        self.assertIn("1L", metin)
        self.assertIn("2YL", metin)
        self.assertIn("starred degree", js)

    def test_rehberdeki_maku_sayisi_uretilen_veriyle_eslesiyor(self):
        unis = json.loads((ROOT / "site" / "universities.json").read_text(encoding="utf-8"))
        maku = next(u for u in unis if u["id"] == "maku")
        metin = (ROOT / "site" / "guide.html").read_text(encoding="utf-8")
        self.assertIn(f"yayımlanan {maku['count']}", metin)
        self.assertIn(f"{maku['count']} published", metin)

    def test_rehber_silinen_kaydi_ve_gerekcesini_acikliyor(self):
        metin = (ROOT / "site" / "guide.html").read_text(encoding="utf-8")
        for parca in ("Powislanska Szkola Wyzsza", "Acil Yardım ve Afet Yönetimi",
                      "not included", "listeye alınmamıştır"):
            with self.subTest(parca=parca):
                self.assertIn(parca, metin)

    def test_dinamik_sonuclar_ekran_okuyucuya_duyuruluyor(self):
        metin = (ROOT / "site" / "agreements.html").read_text(encoding="utf-8")
        self.assertIn('id="resultCount" role="status" aria-live="polite"', metin)
        self.assertIn('id="fieldNotice" role="status" aria-live="polite"', metin)
        self.assertIn('aria-controls="filters" aria-expanded="false"', metin)

    def test_tarih_etiketi_uretim_zamanini_soyluyor(self):
        home = (ROOT / "site" / "home.js").read_text(encoding="utf-8")
        app = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        self.assertIn("Veri üretimi: {d}", home)
        self.assertIn("Data generated: {d}", home)
        self.assertIn("veri üretimi: ${d}", app)
        self.assertIn("data generated: ${d}", app)
