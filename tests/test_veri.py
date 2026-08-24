"""Verinin doğruluğu · kaynaktan üretilen JSON'a kadar.

İki iş bir arada:

  1. `build_data.py`'nin dönüşüm işlevleri doğru çalışıyor mu · her testi
     gerçek bir ölçümden geliyor, uydurma vaka yok.
  2. Kaynak verideki BİLİNEN durum sabitleniyor · sayı değişirse test kırılıyor
     ve "veriye bak" diyor.

İkincisi hata avlamıyor, **pimliyor** ve iki yönlü çalışması kasıtlı:

  - Hata **düzeltilmişse** haberimiz olur. Koordinatörlüğe bildirdiğimiz bir
    şeyin düzeltilip düzeltilmediğini yoksa asla öğrenemeyiz · veri sessizce
    güncellenir, biz belgede hâlâ "bilinen hata" yazmaya devam ederiz.
  - Hata **büyümüşse** (yeni kayıtlarla) haberimiz olur.

`build_data.py --pull` kaynağı yeniden çekiyor. Bildirdiğimiz hata
düzeltilmemişse aynı hata sessizce geri geliyor. Sayı değiştiğinde: farkı
incele, doğruysa buradaki sayıyı ve [`KAYNAK.md`](../KAYNAK.md)'deki kaydı
birlikte güncelle.

Ayrıca üretilen JSON ile onu okuyan `app.js` arasındaki alan adı sözleşmesi
burada denetleniyor · üretici bir alanı yeniden adlandırırsa tüketici sessizce
`undefined` okumaya başlıyor ve sayfa boş görünüyor.
"""
import collections
import importlib.util
import json
import re
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERI = ROOT / "site" / "data-maku.json"
APP_JS = ROOT / "site" / "app.js"
APP_KAYNAK = APP_JS.read_text(encoding="utf-8")

spec = importlib.util.spec_from_file_location("build_data", ROOT / "scripts" / "build_data.py")
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)


def kayitlar():
    return json.loads(VERI.read_text(encoding="utf-8"))["agreements"]


def js_sozluk(ad):
    """app.js içindeki `const <ad> = { ... }` bloğunu anahtar→değer olarak çıkarır."""
    bas = APP_KAYNAK.index(f"const {ad}")
    son = APP_KAYNAK.index("};", bas)
    return dict(re.findall(r'"([^"]+)":\s*(?:\[|")', APP_KAYNAK[bas:son]) or [])


def js_anahtarlar(ad):
    bas = APP_KAYNAK.index(f"const {ad}")
    son = APP_KAYNAK.index("};", bas)
    return set(re.findall(r'"([^"]+)":', APP_KAYNAK[bas:son]))


class FoldTest(unittest.TestCase):
    """fold(): arama anahtarı üretir; aksan/işaret farklarını düzleştirir."""

    def test_turkce_harfler_duzlesir(self):
        for girdi, beklenen in [
            ("ŞİŞLİ", "sisli"), ("Görsel", "gorsel"), ("Çevre", "cevre"),
            ("IĞDIR", "igdir"), ("Işık", "isik"), ("İSTANBUL", "istanbul"),
            ("ÜNİVERSİTE", "universite"),
        ]:
            with self.subTest(girdi=girdi):
                self.assertEqual(bd.fold(girdi), beklenen)

    def test_uluslararasi_harfler_duzlesir(self):
        # Erasmus verisi doğası gereği çok uluslu; ortak üniversiteler
        # Polonya/Romanya/Çekya/Almanya'da. Bu harfler eskiden katlanmıyordu.
        for girdi, beklenen in [
            ("Universität", "universitat"),       # ä · Almanca
            ("Szkoła", "szkola"),                 # ł · Lehçe (ayrıştırılamaz)
            ("Powiślańska", "powislanska"),       # ś, ń · Lehçe
            ("Științe", "stiinte"),               # ș, ț · Romence
            ("Politécnico", "politecnico"),       # é · Portekizce
            ("Škola", "skola"),                   # š · Çekçe
        ]:
            with self.subTest(girdi=girdi):
                self.assertEqual(bd.fold(girdi), beklenen)

    def test_bos_ve_sifir_degerler(self):
        self.assertEqual(bd.fold(None), "")
        self.assertEqual(bd.fold(""), "")
        # 0 boş DEĞİLDİR: JS tarafıyla ayrıştığımız nokta buydu, aynı kalmalı.
        self.assertEqual(bd.fold(0), "0")


class CleanTest(unittest.TestCase):
    """clean(): Excel hücresini kullanılabilir metne indirger."""

    def test_bos_hucre_bos_metin_olur(self):
        self.assertEqual(bd.clean(None), "")

    def test_tarih_iso_bicimine_cevrilir(self):
        # Şu an MAKÜ verisinde tetiklenmiyor ama savunma amaçlı duruyor.
        self.assertEqual(bd.clean(datetime(2026, 3, 15)), "2026-03-15T00:00:00")

    def test_bastaki_sondaki_bosluk_atilir(self):
        self.assertEqual(bd.clean("  Ankara  "), "Ankara")

    def test_bolunmez_bosluk_normal_bosluga_cevrilir(self):
        # \xa0 gözle normal boşluktan ayırt edilemez ama aramayı bozar.
        self.assertEqual(bd.clean("Lublinie\xa0University"), "Lublinie University")
        self.assertEqual(bd.clean("Sondaki\xa0"), "Sondaki")   # strip zaten siler


class IscedFamilyTest(unittest.TestCase):
    """isced_family(): ham ISCED kodundan geniş alan (aile) kodunu çıkarır."""

    def test_dort_haneli_normal_kod(self):
        self.assertEqual(bd.isced_family("0613"), "06")

    def test_excelin_yedigi_sifir_geri_konur(self):
        # Excel "0613" hücresini sayı sanıp baştaki sıfırı atabiliyor.
        self.assertEqual(bd.isced_family("613"), "06")

    def test_10_ailesi_bozulmaz(self):
        # REGRESYON: eski kod "104"ü "0104" yapıp "01" (Eğitim) döndürüyordu.
        # Gerçek kayıtlar: Ulaşım Hizmetleri, Lojistik → doğrusu 10 (Hizmetler).
        self.assertEqual(bd.isced_family("104"), "10")

    def test_iki_haneli_kod_tanınır(self):
        # REGRESYON: eski kod "84" için None döndürüyordu; Veterinerlik
        # anlaşmaları hiçbir aile filtresinde görünmüyordu.
        self.assertEqual(bd.isced_family("84"), "08")

    def test_kodsuz_girdiler_aile_uretmez(self):
        self.assertIsNone(bd.isced_family(None))
        self.assertIsNone(bd.isced_family(""))
        self.assertIsNone(bd.isced_family("bölüm adı"))   # hiç rakam yok

    def test_bilinen_sinir_iki_haneli_cop_kod_aile_uretir(self):
        # Bu bir HATA DEĞİL, bilinçli kuralın kaçınılmaz sonucu: "84" gibi
        # geçerli kısaltmaları kurtarmak için "başa sıfır ekle" kuralı var, ve
        # aynı kural "99" gibi anlamsız bir sayıyı da "09"a çeviriyor.
        # Ayırt etmenin yolu yok: geçerli dar kod listesi elimizde değil.
        # Test bu davranışı SABİTLİYOR ki bir gün değişirse fark edelim.
        self.assertEqual(bd.isced_family("84"), "08")     # istenen kurtarma
        self.assertEqual(bd.isced_family("99"), "09")     # aynı kuralın bedeli

    def test_tek_haneli_koda_sifir_eklenir(self):
        self.assertEqual(bd.isced_family("6"), "06")


class TrUpperTest(unittest.TestCase):
    """tr_upper(): Türkçe-doğru büyük harf (gösterim için; fold'un tersi)."""

    def test_i_harfi_dogru_buyur(self):
        self.assertEqual(bd.tr_upper("Bulgaristan"), "BULGARİSTAN")
        self.assertEqual(bd.tr_upper("Litvanya"), "LİTVANYA")

    def test_noktali_ve_noktasiz_i_ayrimi_korunur(self):
        # 'Hırvatistan' hem ı hem i içerir; düz .upper() ikisini de I yapıp
        # bilgiyi kaybederdi.
        self.assertEqual(bd.tr_upper("Hırvatistan"), "HIRVATİSTAN")
        self.assertNotEqual(bd.tr_upper("Hırvatistan"), "Hırvatistan".upper())


class UretilenVeriTest(unittest.TestCase):
    """Üretilmiş çıktının sağlık kontrolü (kanarya testleri).

    Bu testler kodu değil, kodun ÜRETTİĞİ veriyi denetler. Amaç kesin sayı
    tutturmak değil; sessiz bozulmayı yakalamak.
    """

    @classmethod
    def setUpClass(cls):
        import json
        yol = ROOT / "site" / "data-maku.json"
        if not yol.exists():
            raise unittest.SkipTest("data-maku.json yok; önce build_data.py çalıştırın")
        cls.veri = json.loads(yol.read_text(encoding="utf-8"))

    def test_kayit_sayisi_beklenen_araliкta(self):
        # Kaynak liste güncellenince sayı değişir; ani düşüş bozulma işaretidir.
        self.assertGreater(self.veri["count"], 400)
        self.assertEqual(self.veri["count"], len(self.veri["agreements"]))

    def test_arama_alaninda_gorunmez_karakter_kalmaz(self):
        # Kayıt "id" alanı taşımıyor: dizideki sırasıyla birebir aynı olduğu için
        # gereksizdi ve kaldırıldı. Hangi kaydın kastedildiğini sıra söylüyor.
        kirli = [i for i, r in enumerate(self.veri["agreements"], 1) if "\xa0" in r["search"]]
        self.assertEqual(kirli, [], "arama alanında bölünmez boşluk kalmış (kayıt sırası)")

    def test_arama_alani_katlanmis_durumda(self):
        # search alanı fold()'dan geçmiş olmalı: büyük harf ya da Türkçe
        # karakter kalmışsa bir yerde katlama atlanmış demektir.
        for sira, r in enumerate(self.veri["agreements"][:50], 1):
            with self.subTest(kayit=sira):
                self.assertEqual(r["search"], bd.fold(r["search"]))

    def test_her_kaydin_zorunlu_alanlari_var(self):
        for sira, r in enumerate(self.veri["agreements"][:50], 1):
            with self.subTest(kayit=sira):
                self.assertTrue(r["country"])
                self.assertTrue(r["university"])
                self.assertIn("search", r)


class KaynakVerisiDurumu(unittest.TestCase):

    def setUp(self):
        if not VERI.exists():
            self.skipTest("data-maku.json yok")
        self.kayitlar = kayitlar()

    def test_toplam_kayit_sayisi(self):
        # Diğer sayıların anlamı buna göre. Bu değişmişse hepsini gözden geçir.
        #
        # 467 değil 468: Kaynakta üstü çizilerek silinmiş bir anlaşma var ve
        # artık yayına alınmıyor (bkz. test_silinmis_anlasma_yayina_girmiyor).
        self.assertEqual(len(self.kayitlar), 468,
                         "Kayıt sayısı değişmiş: kaynak veri güncellenmiş olabilir. "
                         "Aşağıdaki bilinen-hata sayılarını da gözden geçir.")

    # Kaynakta üç haneli bir ISCED kodu gördüğümüzde iki ihtimal var: Ya Excel
    # baştaki sıfırı yemiş (`613` aslında `0613`), ya da kod gerçekten öyle
    # (`104`). `isced_family` önce olduğu gibi deniyor, tabloda karşılığı yoksa
    # başa sıfır ekliyor.
    #
    # Bu bir TAHMİN ve tahminin şaşabileceği yer belli: Hem ilk iki hane hem de
    # sıfır eklenmiş hâli tabloda geçerli bir aileye denk gelirse kural sessizce
    # birini seçer.
    #
    # Buradaki liste "incelendi ve kararı verildi" demek. Yeni bir belirsiz kayıt
    # çıkarsa test kırılır ve bir insan bakar. Kural değişmez, karar kaydedilir.
    # Şu an boş ve bu bir başarı kaydı. Tek girdisi `104` idi (Ulaşım Hizmetleri,
    # Lojistik) ve kural doğruyu tesadüfen seçiyordu. Sonra ISCED kodunun doğru
    # sütundan okunması gerektiği anlaşıldı; o kayıtlar artık `1041` taşıyor ve
    # dört haneli kodda tahmin gerekmiyor.
    #
    # Ders: Belirsizliği çözmenin iki yolu var ve karar vermek ikincisi.
    # Birincisi, kararı gereksiz kılan veriyi bulmak.
    #
    # Bekçi duruyor çünkü kaynak veri değişebilir; üç haneli belirsiz bir kod
    # yeniden gelirse yine bir insan bakacak.
    BELIRSIZ_KODLAR = {
        # kod: (seçilen aile, gerekçe)
    }

    def test_belirsiz_isced_kodlari_incelenmis(self):
        """Kural tahmin yürütüyor; tahminin şaşabileceği yerler kayıtlı olmalı.

        `00` (Genel programlar) alternatifi sayılmıyor: O bir toplayıcı aile ve
        `0X1` biçimindeki her kod ona da uyuyor. Gerçek belirsizlik, iki adayın
        da konu ailesi olduğu durum.
        """
        import importlib.util
        spec = importlib.util.spec_from_file_location("bd", ROOT / "scripts" / "build_data.py")
        bd = importlib.util.module_from_spec(spec); spec.loader.exec_module(bd)

        yeni = {}
        for a in self.kayitlar:
            rakam = "".join(c for c in str(a.get("iscedCode") or "") if c.isdigit())
            if len(rakam) != 3:
                continue
            ilk2, sifirli = rakam[:2], "0" + rakam[0]
            if ilk2 in bd.ISCED_FAMILY and sifirli in bd.ISCED_FAMILY and sifirli != "00":
                if rakam not in self.BELIRSIZ_KODLAR:
                    yeni.setdefault(rakam, []).append(a["department"])

        self.assertEqual(
            yeni, {},
            f"İki aileye birden uyan ve daha önce incelenmemiş ISCED kodu:\n  "
            + "\n  ".join(f"{k} → {', '.join(sorted(set(v))[:3])}" for k, v in yeni.items())
            + "\n\nKural bunlardan birini sessizce seçti. Bölüm adına bakıp doğru "
              "olup olmadığına karar verin, sonra BELIRSIZ_KODLAR'a gerekçesiyle "
              "ekleyin. Kural yanlış seçtiyse isced_family düzeltilmeli.")

    def test_belirsiz_kod_kararlari_hala_gecerli(self):
        """Karar verilmiş bir kodun ataması sonradan değişirse haberimiz olsun."""
        for kod, (beklenen, _) in self.BELIRSIZ_KODLAR.items():
            gorulen = {a.get("iscedFamily") for a in self.kayitlar
                       if "".join(c for c in str(a.get("iscedCode") or "") if c.isdigit()) == kod}
            if not gorulen:
                continue
            self.assertEqual(gorulen, {beklenen},
                             f"{kod} kodu için karar {beklenen} idi, şimdi {gorulen}.")

    def test_dahil_yazim_hatasi_hala_duruyor(self):
        """Kontenjan açıklamasında "dahil" yerine "dalil" yazılı.

        Koordinatörlüğe bildirilecek. Sayı DÜŞERSE düzeltilmiş demektir:
        KAYNAK.md'deki kayıt güncellenmeli.
        """
        n = sum(1 for r in self.kayitlar
                for alan in ("quotaStudy", "quotaInternship")
                if "dalil" in str(r.get(alan) or ""))
        self.assertEqual(n, 167,
                         f"'dalil' yazım hatası {n} kayıtta (bekleniyordu: 167). "
                         f"Azaldıysa kaynakta düzeltilmiş olabilir → KAYNAK.md'deki "
                         f"'bilinen hata' kaydını güncelle.")

    def test_silinmis_anlasma_yayina_girmiyor(self):
        """Kaynakta üstü çizili satır = silinmiş anlaşma.

        Satır tablodan kaldırılmıyor, yalnız biçimlendirmeyle işaretleniyor ve
        yanına "SİLDİM LİSTELERDEN" gibi bir not düşülüyor. Hücre değerine bakan
        bir okuyucu bunu göremiyor; biçime bakmak gerekiyor.

        Bir kez yayına çıktı: artık geçerli olmayan bir anlaşma listede duruyordu
        ve öğrenci ona başvurabilirdi. Bu test o kaydın geri gelmediğini
        doğruluyor.
        """
        yasak = "Acil Yardım ve Afet Yönetimi"
        kalan = [r for r in self.kayitlar
                 if yasak in (r.get("department") or "")
                 and "Powislanska" in r.get("university", "")]
        self.assertEqual(kalan, [],
                         "Kaynakta üstü çizilerek silinmiş anlaşma yayında. "
                         "parse_maku'daki üstü çizili satır denetimi çalışmıyor "
                         "olabilir.")

    def test_iptal_edilmis_ogrenim_seviyesi_gosterilmiyor(self):
        """Kaynakta "EQF 7 (EQF 7 İPTAL)" gibi bir hücre var.

        Düz rakam taraması 7'yi de bulur ve yüksek lisans açıkmış gibi görünür.
        Yüksek lisans öğrencisi başvurulamayacak bir anlaşmaya başvurmayı
        deneyebilir.
        """
        for r in self.kayitlar:
            if ("INFORMATYKI" in r.get("university", "").upper()
                    and "Sosyal Hizmet" in (r.get("department") or "")):
                self.assertNotIn(
                    "yukseklisans", r.get("levels", {}),
                    "EQF 7 kaynakta İPTAL edilmiş ama yüksek lisans açık görünüyor.")

    def test_isced_kodu_olmayan_kayit_sayisi(self):
        """Bu sayı uzun süre 243'tü ve sebebi kaynak veri sanılıyordu.

        Alan filtresi etkinleştiğinde kodsuz kayıtlar tamamen eleniyor
        (`app.js`: `state.families.has(a.iscedFamily)`), yani öğrenci alana göre
        süzdüğünde o anlaşmaları göremiyor. 467 kaydın 243'ü demek, listenin
        yarısından fazlası demekti.

        Sebep kaynağın sınırı değil, **bizim okuduğumuz sütundu.** Kod tabloda
        üç yerde geçiyor: iki bölüm adı sütununun önünde ve ayrı bir kod
        sütununda. Yalnız sonuncusu okunuyordu ve o sütun 246 satırda boştu.
        Ölçüldü: boş görünenlerin 245'inde kod bölüm adının önünde duruyordu.

        `isced_kodu` üçünü birden okuyup en ayrıntılısını seçince sayı 1'e
        düştü. Kalan tek kayıtta kod gerçekten hiçbir sütunda yok.

        Bu test artık iki yönlü çalışıyor: sayı ARTARSA kaynakta gerçekten kod
        kaybı olmuş demektir; AZALIRSA kaynak düzelmiş demektir.
        """
        n = sum(1 for r in self.kayitlar if not str(r.get("iscedCode") or "").strip())
        self.assertEqual(n, 1,
                         f"ISCED kodu olmayan kayıt: {n} (bekleniyordu: 1). "
                         f"Bu kayıtlar alan filtresinde görünmez.")

    def test_sira_numarasi_gorunumlu_isced_kodu_yok(self):
        """ISCED sütununa kod yerine satır sıra numarası yazılması.

        Daha önce bir kaynak tabloda görülmüş bir hata türü: kayıtlar sitede
        görünür ama alan filtresine giremez, çünkü 11–22 gibi bir değer geçerli
        bir ISCED kodu değildir. Şu anki veride yok; denetim, aynı hatanın yeni
        bir kaynakla sessizce geri gelmemesi için duruyor.
        """
        cıplak = [r for r in self.kayitlar
                  if (c := str(r.get("iscedCode") or "").strip())
                  and re.fullmatch(r"\d{1,2}", c) and 11 <= int(c) <= 22]
        self.assertEqual(cıplak, [],
                         f"ISCED sütununda sıra numarası görünümlü değer: "
                         f"{[(r['university'], r['iscedCode']) for r in cıplak][:5]}")

    def test_kodu_olup_ailesi_atanamayan_kayit_yok(self):
        # Yukarıdakinin genel hâli: kod var ama tanınmıyorsa filtreye giremez.
        ailesiz = [r for r in self.kayitlar
                   if str(r.get("iscedCode") or "").strip()
                   and not str(r.get("iscedFamily") or "").strip()]
        self.assertEqual(ailesiz, [],
                         f"ISCED kodu tanınmayan kayıt: "
                         f"{[(r['university'], r['iscedCode']) for r in ailesiz][:5]}")


class UlkeOnEki(unittest.TestCase):
    """Yayınlanan her kaydın ülkesi, Erasmus kodunun ön ekiyle tutuyor mu?

    Ön ek kurum kodunun **tanımının** parçası; ülke sütunu ise elle yazılıyor.
    Kaynakta dördü çelişiyordu ve düzeltildi (bkz. `build_data.ulke_onekten`).

    Bu test **üretilen veriye** bakıyor, kaynak Excel'e değil. Sebebi iki
    katmanlı: Excel `lokal/` altında ve depoya girmiyor, yani CI'da yok. Ama
    daha önemlisi, denetlenmesi gereken şey kullanıcının **gördüğü** veri.
    """

    def setUp(self):
        self.kayitlar = kayitlar()

    def test_hicbir_kayit_on_ekiyle_celismiyor(self):
        import importlib.util
        yol = ROOT / "scripts" / "build_data.py"
        spec = importlib.util.spec_from_file_location("build_data", yol)
        bd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bd)

        celisen = []
        for r in self.kayitlar:
            onekten = bd.ulke_onekten(r.get("erasmusCode", ""))
            if onekten and bd.tr_upper(onekten) != r["country"]:
                celisen.append(f"{r['university'][:34]}: {r['country']} "
                               f"≠ {bd.tr_upper(onekten)} ({r['erasmusCode']})")
        self.assertEqual(celisen, [],
                         f"Yayınlanan veride ülke ile Erasmus kodu çelişiyor. "
                         f"Öğrenci yanlış ülke görüyor: {celisen}")

    def test_on_ek_okunabilen_kayit_orani_dusmedi(self):
        """Bekçinin kendi sessizliğini yakalar.

        Kod biçimi değişir ya da kalıp bozulursa `ulke_onekten` hiçbir şey
        döndürmez ve üstteki test **hiçbir şey bulamadığı için** geçer. Alt
        sınır, testin boşalmasını görünür kılıyor.
        """
        import importlib.util
        yol = ROOT / "scripts" / "build_data.py"
        spec = importlib.util.spec_from_file_location("build_data", yol)
        bd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bd)

        okunan = sum(1 for r in self.kayitlar
                     if bd.ulke_onekten(r.get("erasmusCode", "")))
        oran = okunan / len(self.kayitlar)
        self.assertGreater(oran, 0.90,
                           f"Erasmus kodu yalnız {okunan}/{len(self.kayitlar)} "
                           f"kayıtta okunabiliyor (%{100*oran:.0f}). Kod biçimi "
                           f"değişmiş olabilir; ülke denetimi boşa düşüyor.")


class BolumAdiYazimlari(unittest.TestCase):
    """Aynı bölümün kaç farklı yazımla göründüğü pimli.

    **Bu kanarya bir kez yanlış şeyi ölçtü ve düzeltildi.** İlk hâli yayımlanan
    JSON'daki yazımları sayıyordu ve "sayı düşerse kaynakta düzeltilmiş
    demektir" diyordu. O çıkarım, biz yazımları birleştirmeye başlayınca
    geçersiz oldu: Sayı **bizim** yüzümüzden de düşebiliyor.

    Ayrım şimdi açık ve iki ayrı test tutuyor:

    - **Kaynakta kaç tane var** · yalnız kurum düzeltince değişir
    - **Karta kaç tanesi yansıyor** · birleştirme kuralı değişince değişir

    Kaynaktaki yazımı geri okumak mümkün, çünkü değiştirdiğimiz her kayıtta
    `sourceDiff.department.kaynakta` duruyor.
    """

    def _bd(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "build_data", ROOT / "scripts" / "build_data.py")
        bd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bd)
        return bd

    def _gruplar(self, adlar):
        from collections import defaultdict
        bd = self._bd()
        g = defaultdict(set)
        for ad in adlar:
            if ad:
                g[bd.fold(ad)].add(ad)
        return {k: v for k, v in g.items() if len(v) > 1}

    def test_kaynaktaki_yazim_farki_sayisi(self):
        """Kurumun yayımladığı tabloda kaç bölüm birden çok yazımla geçiyor."""
        kaynakta = []
        for r in kayitlar():
            iz = (r.get("sourceDiff") or {}).get("department") or {}
            if iz.get("sebep") == "yazim-birligi":
                kaynakta.append(iz["kaynakta"])       # değiştirdiğimiz kayıt
            elif iz.get("sebep") == "isced-etiketi":
                continue                              # kaynakta boştu
            else:
                kaynakta.append(r["department"])
        cok = self._gruplar(kaynakta)
        self.assertEqual(len(cok), 18,
                         f"Kaynak tabloda yalnız harf büyüklüğüyle ayrışan bölüm "
                         f"adı {len(cok)} (bekleniyordu: 18). Azaldıysa kurum "
                         f"düzeltmiş olabilir → KAYNAK.md §2.6 güncellenmeli.")

    def test_karta_yansiyan_yazim_farki_sayisi(self):
        """Birleştirmeden sonra öğrencinin hâlâ iki biçimde gördüğü bölümler.

        Bugün üç tane ve üçü de **beraberlik**: İki yazım eşit sıklıkta, yani
        hangisinin ağırlıklı olduğunu söyleyecek bir ölçü yok. Orada seçim
        yapmak yazım tercihi dayatmak olurdu, bilerek dokunulmuyor.
        """
        cok = self._gruplar(r["department"] for r in kayitlar())
        self.assertEqual(
            len(cok), 3,
            f"Kartta iki biçimde görünen bölüm sayısı {len(cok)} (bekleniyordu: 3). "
            f"Artmışsa birleştirme kuralı bozulmuş, azalmışsa beraberlik çözülmüş "
            f"olabilir: {[sorted(v) for v in cok.values()]}")

    def test_yazim_farki_aramayi_bozmuyor(self):
        """Asıl güvence bu: Yazım tutarsız olsa da öğrenci bulabiliyor."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "build_data", ROOT / "scripts" / "build_data.py")
        bd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bd)

        bulunamayan = [r["university"] for r in kayitlar()
                       if bd.fold(r["department"]) not in r["search"]]
        self.assertEqual(bulunamayan, [],
                         f"Bölüm adı arama metnine girmemiş: {bulunamayan[:5]}")


class UcHaneliKodlar(unittest.TestCase):
    """Sıfır tamamlama tahmini, tahmin kalan her kayıtta okunmuş olmalı.

    `isced_family` üç haneli bir kod görünce baştaki sıfırın Excel tarafından
    yendiğini varsayıp geri koyuyor. Varsayım güvenli değil ve bu itiraz haklı:
    `104` gibi bir kod hem `10` (Hizmetler) hem `0104` okunabilir.

    Kod bunu körlemesine yapmıyor -- ilk iki hane zaten geçerli bir aileyse
    dokunmuyor -- ama kalan belirsizlik bir insanın bakmasını gerektiriyor.
    Bu test, tahminle aile bulunan kayıtların sayısını ve seçilen aileleri
    pimliyor: Biri değişirse ya da yenisi eklenirse bir insan bakacak.

    Aşağıdaki liste ELLE okundu; her satırın yanında bölüm adı var ve seçilen
    ailenin o bölüme uyup uymadığı gözle doğrulandı.
    """

    # kod -> (seçilen aile, bölüm adı, okundu mu)
    OKUNAN = {
        "061": "06",   # Makine Müh. + Yazılım Müh. -- ilki çelişiyor, §2.9
        "091": "09",   # Hemşirelik, Diyetetik
        "110": "01",   # Education
        "915": "09",   # PDR
        "011": "01",   # Sınıf öğretmenliği
        "023": "02",   # İngilizce öğretmenliği
        "092": "09",   # Sosyal Hizmet
        "710": "07",   # Mühendislik Fakültesi
        "732": "07",   # İnşaat Mühendisliği
        "731": "07",   # Mimarlık
        "114": "01",   # Matematik / Müzik Öğretmenliği
    }

    def test_uc_haneli_kodlarin_hepsi_okunmus(self):
        gorulen = {}
        for r in kayitlar():
            k = r.get("iscedCode") or ""
            if len(k) == 3:
                gorulen.setdefault(k, r.get("iscedFamily"))
        yeni = sorted(set(gorulen) - set(self.OKUNAN))
        self.assertEqual(yeni, [],
                         f"Üç haneli yeni kod(lar) çıktı ve tahminle aile "
                         f"atandı: {yeni}. Bölüm adına bakıp doğruluğu "
                         f"onaylanmalı, sonra bu listeye eklenmeli.")
        kayan = [f"{k}: {self.OKUNAN[k]} -> {v}"
                 for k, v in gorulen.items() if self.OKUNAN.get(k) != v]
        self.assertEqual(kayan, [],
                         f"Tahminin sonucu değişmiş: {kayan}. Kod ya da kaynak "
                         f"değişmiş olabilir; yeniden okunmalı.")


class SutunAdlari(unittest.TestCase):
    """Sütunlar adla bulunuyor; kod numaraya geri dönmemeli.

    Bu borç iki kez bedel ödetti: ISCED kodu ve ülke, ikisi de yanlış sütundan
    okunmuştu. Numarayla okumak "hangi sütunda ne var" sorusunu sormayı
    zorlaştırıyor ve tabloya bir sütun eklendiğinde kod **çökmüyor, anlamsız
    veri üretiyor.**

    Ölçülmüş hâli: Kaynağın kopyasına D konumuna bir sütun eklendiğinde,
    numarayla okuyan eski kod ülke sütununda `"EQF 6\\nEQF7\\nEQF8"` buluyor ve
    onu ülke adı sanıyordu.
    """

    def test_kodda_numarayla_sutun_okuma_kalmamis(self):
        kaynak = (ROOT / "scripts" / "build_data.py").read_text(encoding="utf-8")
        numarali = re.findall(r"col\(\s*\d+\s*\)", kaynak)
        self.assertEqual(numarali, [],
                         f"Sütun numarayla okunuyor: {numarali}. Ada göre "
                         f"okunmalı (bkz. maku_sutunlari); numara, tabloya "
                         f"sütun eklendiğinde sessizce yanlış veri üretiyor.")

    def test_baslik_tablosu_kaynakla_uyusuyor(self):
        """Başlık adları değişirse derleme durmalı, sessizce kaymamalı."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "build_data", ROOT / "scripts" / "build_data.py")
        bd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bd)

        kaynak = ROOT / "lokal" / "maku" / "maku-ka131-ikili-anlasmalar.xlsx"
        if not kaynak.exists():
            self.skipTest("kaynak Excel yok (lokal/ depoya girmiyor)")
        import openpyxl
        ws = openpyxl.load_workbook(kaynak, data_only=True).worksheets[0]
        sutun = bd.maku_sutunlari(ws)

        # Bugünkü tabloda beklenen yerleşim; kayarsa haber ver.
        BEKLENEN = {"universite": 3, "erasmus_kodu": 5, "isced_etiket_en": 6,
                    "bolum_tr": 8, "isced_kodu": 9, "ulke": 12}
        kayan = {k: (v, sutun[k]) for k, v in BEKLENEN.items() if sutun[k] != v}
        self.assertEqual(kayan, {},
                         f"Sütun yerleşimi değişmiş: {kayan}. Kod ada göre "
                         f"okuduğu için ÇALIŞMAYA DEVAM EDİYOR; bu test yalnız "
                         f"haber veriyor, kaynağın değiştiğini bilelim diye.")


class OnEkUlkeTutarliligi(unittest.TestCase):
    """`KAYNAK.md §2.7`'nin dayandığı kalıp gerçekten duruyor mu.

    O bölüm dört satırdaki ülke bilgisini düzeltiyor ve gerekçesi tek bir
    ölçüm: Erasmus kodunun ön eki ile ülke, kalan bütün kayıtlarda birbirini
    tutuyor. Kalıp bozulursa gerekçe de çöker · ama belge yazılı kaldığı için
    kimse fark etmez.

    Kayıtta bu iddia için *"kaynak verelim, bu bir halüsinasyon olmasın"*
    denmişti. Resmî tanıma erişim olmadığı için yapılabilen şey iddiayı
    **ölçüme bağlamak** oldu.

    Eşleme elle yazılmıyor · veriden öğreniliyor. Elle yazılmış bir tablo,
    veriyle birlikte eskiyecek ikinci bir kayıt olurdu.
    """

    def test_her_kayit_kendi_on_ekiyle_uyumlu(self):
        import collections
        veri = json.loads((ROOT / "site" / "data-maku.json").read_text(encoding="utf-8"))
        kayitlar = veri["agreements"] if isinstance(veri, dict) else veri
        self.assertGreater(len(kayitlar), 100, "Kayıt sayısı beklenenden az; kalıp bozulmuş olabilir.")

        esleme = collections.defaultdict(collections.Counter)
        for a in kayitlar:
            on = (a.get("erasmusCode") or "").strip()[:2].upper()
            ulke = (a.get("country") or "").strip().upper()
            if on and ulke:
                esleme[on][ulke] += 1

        self.assertGreaterEqual(len(esleme), 5,
                                f"Yalnız {len(esleme)} ön ek bulundu; alan adları değişmiş olabilir.")
        sapan = []
        for on, sayac in sorted(esleme.items()):
            if len(sayac) > 1:
                sapan.append(f"{on} → {dict(sayac)}")
        self.assertEqual(sapan, [],
                         "Erasmus kodu ön eki ile ülke birbirini tutmuyor:\n  "
                         + "\n  ".join(sapan)
                         + "\n\nKAYNAK.md §2.7'nin gerekçesi bu kalıba dayanıyor.")


class KaynakKunyesi(unittest.TestCase):
    """Kaynak dosyanın künyesi depoda duruyor · dosyanın kendisi durmuyor.

    Kaynak Excel depoya girmiyor (CONTRIBUTING.md, 2. kural) ve bunun bir bedeli var:
    Veriyi yeniden üretmek isteyen biri, elindeki dosyanın **bizim
    kullandığımızla aynı** olduğunu doğrulayamıyordu.

    Dosya adresi de kırılgan · içinde tarih ve sürüm numarası taşıyor, yani
    kurum listeyi güncellediği gün ölüyor. Kalıcı olan liste sayfası.

    Künye ikisini de kayda geçiriyor. Bu sınıf künyenin **veriyle
    ayrışmamasını** sağlıyor · künyedeki kayıt sayısı üretilen veriyle aynı
    olmak zorunda, ve yerel dosya varsa özeti tutmak zorunda.
    """

    KUNYE = ROOT / "site" / "kaynak-kunyesi.json"

    def kunye(self):
        self.assertTrue(self.KUNYE.exists(), "site/kaynak-kunyesi.json yok.")
        return json.loads(self.KUNYE.read_text(encoding="utf-8"))

    def test_her_yayimlanan_veri_kunyede_geciyor(self):
        k = self.kunye()
        kayitli = {x["id"] for x in k["kaynaklar"]}
        self.assertGreaterEqual(len(kayitli), 1, "Künyede hiç kaynak yok; kalıp bozulmuş olabilir.")
        uretilen = {p.stem.replace("data-", "") for p in (ROOT / "site").glob("data-*.json")}
        eksik = sorted(uretilen - kayitli)
        self.assertEqual(eksik, [],
                         f"Yayımlanan veri künyede yok: {eksik}. Kaynağı belirtilmemiş "
                         f"bir veri dosyası yayımlanıyor.")

    def test_kunyedeki_kayit_sayisi_uretilen_veriyle_ayni(self):
        for kaynak in self.kunye()["kaynaklar"]:
            yol = ROOT / "site" / f"data-{kaynak['id']}.json"
            if not yol.exists():
                continue
            d = json.loads(yol.read_text(encoding="utf-8"))
            gercek = len(d["agreements"] if isinstance(d, dict) else d)
            self.assertEqual(kaynak["kayit_sayisi"], gercek,
                             f"{kaynak['id']}: Künye {kaynak['kayit_sayisi']} diyor, "
                             f"üretilen veride {gercek} kayıt var.")

    def test_yerel_dosya_varsa_ozeti_kunyeyle_ayni(self):
        """Yerelde çalışanda koşuyor · CI'da dosya olmadığı için atlanıyor."""
        import hashlib
        denetlenen = 0
        for kaynak in self.kunye()["kaynaklar"]:
            yerel = ROOT / kaynak["yerel_ad"]
            if not yerel.exists():
                continue
            denetlenen += 1
            ozet = hashlib.sha256(yerel.read_bytes()).hexdigest()
            self.assertEqual(kaynak["sha256"], ozet,
                             f"{kaynak['id']}: Yerel dosyanın özeti künyedekinden farklı. "
                             f"Kaynak güncellendiyse künye de güncellenmeli.")
            self.assertEqual(kaynak["boyut_bayt"], yerel.stat().st_size,
                             f"{kaynak['id']}: Dosya boyutu künyedekinden farklı.")
        if not denetlenen:
            self.skipTest("yerel kaynak dosyası yok (lokal/ depoya girmiyor)")

    def test_kirilgan_adres_notu_duruyor(self):
        """Adresin kırılgan olduğu yazılı kalmalı · yoksa sonraki bakımcı bilmiyor."""
        for kaynak in self.kunye()["kaynaklar"]:
            self.assertIn("liste_sayfasi", kaynak,
                          f"{kaynak['id']}: Kalıcı liste sayfası yazılmamış.")
            self.assertTrue(kaynak.get("adres_notu", "").strip(),
                            f"{kaynak['id']}: Dosya adresinin kırılganlığı not edilmemiş.")


class UretilenAlanAdlari(unittest.TestCase):
    """COUPLINGS §5 · Python yazar, app.js okur; ad değişirse site sessizce boşalır."""

    # Aşağıda sayılan alanlar. ELLE tutuluyor, ve bu bilinçli:
    # ilk denemede app.js'i tarayıp `a.<alan>` kalıbını otomatik çıkarmayı
    # denedik, ama `a` bir yerde sıralama geri-çağrısının parametresiydi
    # (`sort((a,b) => b.count - a.count)`) ve test YANLIŞ ALARM verdi.
    # Gürültü üreten denetim, denetime olan güveni bozar, bu yüzden akıllı
    # tarama yerine açık liste tercih edildi. Yeni alan okunmaya başlanırsa
    # buraya eklenir; bu listeyle birlikte güncellenir.
    SITENIN_OKUDUGU = [
        "country", "university", "department", "search", "iscedFamily",
        "iscedFamilyTr", "iscedFamilyEn", "iscedCode",
        "validity", "levels", "quotaStudy", "quotaInternship",
        "quotaStaffTeach", "quotaStaffTrain", "quotaNote",
        "language",
    ]

    # Üretici bunları KOŞULLU yazıyor: alan yalnız durum geçerliyse kayda
    # giriyor. `sourceDiff` bugün 468 kaydın 13'ünde var, çünkü yalnız
    # kaynaktan ayrıldığımız kayıtlara iz düşülüyor. "Her kayıtta olmalı"
    # diye sınamak yanlış alarm üretirdi, "hiç olmamalı" diye saymamak ise
    # üretici susunca izi sessizce kaybettirirdi. Aradaki doğru sınav:
    # EN AZ BİR kayıtta bulunmalı.
    KOSULLU_URETILEN = ["sourceDiff"]

    # Site bu alanı ADIYLA okumaz; alan `search` metninin İÇİNE karışır ve
    # kullanıcı Erasmus kodunu yazarak arama yapabilir. "Kullanılmıyor" sanıp
    # kaldırmak, o aramayı sessizce bozardı.
    DOLAYLI_KULLANILAN = ["erasmusCode"]

    # Tüketicisi CANLI ama bu üniversitenin ayrıştırıcısı doldurmuyor. Alan
    # kayıtta hiç yok; JavaScript tarafı bunu `undefined` olarak okuyup zaten
    # doğru davranıyor (`a.website && ...`). Sabit boş değer yazmak 467 kayda
    # gereksiz bayt eklerdi -- kaldırıldı, tüketici bırakıldı.
    #
    # Yeni bir üniversite bu alanı doldurursa kod değişikliği GEREKMEZ, arayüz
    # kendiliğinden çalışır. O yüzden bu "ölü kod" değil, doldurulmamış şema yuvası.
    URETICI_DOLDURMUYOR = ["website", "sharedQuota"]

    def test_doldurulmayan_alanlarin_tuketicisi_hala_duruyor(self):
        """Şema yuvası boşsa bile tüketicisi silinmemeli.

        Aksi hâlde yeni bir üniversite o alanı doldurduğunda arayüz sessizce
        görmezden gelir. Bu test, tüketici tarafının kazara silinmesini yakalar.
        """
        for alan in self.URETICI_DOLDURMUYOR:
            with self.subTest(alan=alan):
                self.assertIn(f".{alan}", APP_KAYNAK,
                              f"{alan} alanının tüketicisi app.js'ten silinmiş. Üretici "
                              f"bugün doldurmuyor ama yeni bir üniversite doldurabilir; "
                              f"o gün arayüz sessizce görmezden gelirdi.")

    def test_sitenin_okudugu_alanlar_uretilen_veride_var(self):
        """Ölçüm bütün kayıtlara bakıyor, yalnız ilkine değil.

        İlk hâli `agreements[0]`a bakıyordu ve o zayıf bir ölçümdü: Bir alan
        yalnız ilk kayıtta bulunsa da test geçerdi. Ayrım 20 Ağustos 2026'da
        `sourceDiff` eklenince ortaya çıktı · alan gerçekten üretiliyor ama
        ilk kayıtta yok.
        """
        yol = ROOT / "site" / "data-maku.json"
        if not yol.exists():
            self.skipTest("data-maku.json yok")
        kayitlar = json.loads(yol.read_text(encoding="utf-8"))["agreements"]
        self.assertTrue(kayitlar, "Veride hiç kayıt yok")

        eksik = [alan for alan in self.SITENIN_OKUDUGU
                 if any(alan not in k for k in kayitlar)]
        self.assertEqual(eksik, [],
                         f"app.js okuyor ama bazı kayıtlarda yok: {eksik}")

        hic_yok = [alan for alan in self.KOSULLU_URETILEN
                   if not any(alan in k for k in kayitlar)]
        self.assertEqual(hic_yok, [],
                         f"Koşullu alan hiçbir kayıtta yok: {hic_yok}\n"
                         f"Üretici bu alanı yazmayı bırakmış olabilir; "
                         f"tüketicisi app.js'te hâlâ duruyor.")

    def test_listedeki_alanlar_app_jsde_gercekten_geciyor(self):
        # Ters yön: listemiz eskimesin. Bir alan artık okunmuyorsa haberimiz olsun.
        kullanilmayan = [a for a in self.SITENIN_OKUDUGU + self.KOSULLU_URETILEN
                        if f".{a}" not in APP_KAYNAK]
        self.assertEqual(kullanilmayan, [],
                         f"listede var ama app.js'te geçmiyor (liste eskimiş olabilir): "
                         f"{kullanilmayan}")

    def test_dolayli_kullanilan_alanlar_arama_metnine_giriyor(self):
        yol = ROOT / "site" / "data-maku.json"
        if not yol.exists():
            self.skipTest("data-maku.json yok")
        kayitlar = json.loads(yol.read_text(encoding="utf-8"))["agreements"]
        for alan in self.DOLAYLI_KULLANILAN:
            ornek = next((r for r in kayitlar if r.get(alan)), None)
            if ornek is None:
                self.skipTest(f"{alan} hiçbir kayıtta dolu değil")
            with self.subTest(alan=alan):
                self.assertIn(bd.fold(ornek[alan]), ornek["search"],
                              f"{alan} arama metnine katılmıyor; kullanıcı onunla arama yapamaz")


class UniversiteKaydi(unittest.TestCase):
    """COUPLINGS §3 · üniversite adı kodda, veride VE belgelerde yazılı.

    Bu bağ zaten bir kez koptu: Yayın rehberi "ilk üniversite: ISUBÜ" derken
    platformdaki tek üniversite MAKÜ idi; aynı ayrışma rehber sayfasının
    footer'ında yayına da çıktı. Kayıt vardı, denetim yoktu.

    Rehber içeriğinin yeterliliği hâlâ ölçülemiyor (insan işi); ölçülebilen
    kısım burada.
    """

    # Projeyle bir biçimde anılmış üniversite kısaltmaları. Belgede geçen ama
    # kayıtta olmayan bir ad, eskimiş bilgi demektir. Yeni üniversite eklenince
    # kısaltması buraya da yazılır.
    BILINEN_KISALTMALAR = ["MAKÜ", "ISUBÜ", "İSUBÜ"]
    BELGELER = ["README.md", "KAYNAK.md"]

    # Platformda olmayan bir üniversiteden söz etmek meşru olabilir (geçmiş kayıt,
    # "şu an geçerli değil" notu). Ama bunun AÇIKÇA söylenmesi şart: aksi hâlde
    # okuyan onu güncel sanır. ISUBÜ tam olarak böyle kaldı. O yüzden test
    # susturulmuyor, işaret isteniyor.
    GECERSIZ_ISARETLERI = ["platformda değil", "geçerli değildir", "platformda geçerli değil"]

    def kayitli(self):
        yol = ROOT / "site" / "universities.json"
        if not yol.exists():
            self.skipTest("universities.json yok")
        return {u["abbr"] for u in json.loads(yol.read_text(encoding="utf-8"))}

    def test_belgelerde_gecen_universite_kayitta_var(self):
        kayitli = self.kayitli()
        for belge in self.BELGELER:
            metin = (ROOT / belge).read_text(encoding="utf-8")
            # Paragraf paragraf bakılıyor: bir üniversiteden söz eden paragraf,
            # o üniversite kayıtlı değilse durumu açıkça belirtmek zorunda.
            for paragraf in metin.split("\n\n"):
                for kisaltma in self.BILINEN_KISALTMALAR:
                    if kisaltma not in paragraf or kisaltma in kayitli:
                        continue
                    if any(i in paragraf for i in self.GECERSIZ_ISARETLERI):
                        continue
                    with self.subTest(belge=belge, kisaltma=kisaltma):
                        self.fail(
                            f"{belge} '{kisaltma}' diyor ama universities.json'da kayıtlı "
                            f"değil (kayıtlılar: {sorted(kayitli)}) ve paragrafta durumu "
                            f"belirten bir ifade yok. Ya belge eskimiş, ya da "
                            f"{self.GECERSIZ_ISARETLERI} ifadelerinden biri eklenmeli.\n"
                            f"Paragraf: {paragraf.strip()[:160]}…")

    def test_kayitli_her_universite_readmede_gecer(self):
        metin = (ROOT / "README.md").read_text(encoding="utf-8")
        eksik = [a for a in self.kayitli() if a not in metin]
        self.assertEqual(eksik, [],
                         f"universities.json'da var ama README.md tablosunda yok: {eksik}")


class IscedKodlari(unittest.TestCase):
    """COUPLINGS §2 · kodlar aynı olmak zorunda, etiketler değil."""

    def test_sitenin_bildigi_her_kod_pythonda_da_var(self):
        js = js_anahtarlar("FAMILY_SHORT")
        py = set(bd.ISCED_FAMILY)
        eksik = js - py
        self.assertEqual(eksik, set(),
                         f"app.js'te olup build_data.py'da olmayan ISCED kodu: {eksik}")

    def test_uretilen_verideki_her_aile_sitede_karsilaniyor(self):
        yol = ROOT / "site" / "data-maku.json"
        if not yol.exists():
            self.skipTest("data-maku.json yok")
        veri = json.loads(yol.read_text(encoding="utf-8"))
        veride = {f["code"] for f in veri["iscedFamilies"]}
        js = js_anahtarlar("FAMILY_SHORT")
        eksik = veride - js
        self.assertEqual(eksik, set(),
                         f"veride var ama filtre listesinde görünmeyecek aile: {eksik}")


class UlkeAdlari(unittest.TestCase):
    """`tr_upper` çıktısı, `app.js`'teki COUNTRY anahtarıyla birebir aynı olmalı.

    Tabloda karşılığı olmayan bir ülke İngilizce sayfada **Türkçe adıyla ve
    bayraksız** kalıyor. Hata çıkmıyor, sayfa çalışıyor.

    BU BEKÇİ BİR KEZ YARIM KAPSAMLA KALDI VE KAÇIRDI

    İlk hâli yalnız `data-maku.json`'a bakıyordu · tek üniversite varken
    doğruydu. Marmara ve ESOGÜ eklendiğinde kapsam **sessizce yarım kaldı**:
    Üç yeni ülke (Danimarka, Estonya, İsveç) tabloda yoktu ve İngilizce
    sayfada Türkçe göründüler. Test yeşil yanmaya devam etti; hatayı ekranda
    gözle gören biri buldu.

    Aynı arıza bu depoda daha önce de oldu · yayın rehberi sayı denetiminin
    dışındaydı ve aylarca eskimiş bilgi taşıdı. Ders aynı: **Bir bekçinin
    yarım kapsamı, hiç bekçi olmamasından tehlikeli**, çünkü yeşil ışık
    "bakıldı" diye okunuyor.

    Bugün her `data-*.json` taranıyor, yani dördüncü üniversite eklendiğinde
    kendiliğinden kapsanıyor.
    """

    def veriler(self):
        return sorted((ROOT / "site").glob("data-*.json"))

    def test_veride_gecen_her_ulke_ingilizce_karsiligi_var(self):
        dosyalar = self.veriler()
        self.assertGreater(len(dosyalar), 0,
                           "Hiç veri dosyası yok · denetim boşa dönüyor.")
        bilinen = js_anahtarlar("COUNTRY")
        eksik = {}
        for yol in dosyalar:
            veri = json.loads(yol.read_text(encoding="utf-8"))
            yok = set(veri["countries"]) - bilinen
            if yok:
                eksik[yol.stem] = sorted(yok)
        self.assertEqual(eksik, {},
                         f"İngilizce görünümde Türkçe adıyla ve bayraksız kalacak "
                         f"ülkeler: {eksik}\napp.js'teki COUNTRY tablosuna ekleyin.")

    def test_tr_upper_ciktisi_tablo_anahtariyla_uyusuyor(self):
        # HIRVATİSTAN ile HIRVATISTAN farklı anahtarlardır; bu testin amacı
        # tr_upper'ın ürettiği yazımın tabloda karşılanmasını güvenceye almak.
        js = js_anahtarlar("COUNTRY")
        for ad in ["Bulgaristan", "Hırvatistan", "Litvanya", "Çekya", "İtalya"]:
            with self.subTest(ad=ad):
                self.assertIn(bd.tr_upper(ad), js)


class KaynakIzi(unittest.TestCase):
    """Kaynaktan ayrıldığımız her yer kartta görünmeli.

    Veri tarafı (`build_data.py`) `sourceDiff` alanını üretiyor, gösterim tarafı
    (`app.js`) onu okuyup kartta bir satır çiziyor. İkisi ayrışırsa iz sessizce
    kaybolur: Veri düzeltilmeye devam eder ama öğrenci bunu göremez.

    Bu, projenin en çok korktuğu hata sınıfı -- iki yerin sessizce ayrışması --
    ve burada bedeli açık: "Veriyi üniversiteden çekiyoruz" iddiası, çektiğimiz
    hâlden ayrıldığımızı söylemeden doğru olmuyor.
    """

    def test_kaynaktaki_deger_uretiliyorsa_gosteriliyor(self):
        """Üretici `kaynakta` yazıyorsa gösterim onu ekrana koymalı.

        Üstteki test iz **türünün** okunduğuna bakıyor, kaynaktaki değerin
        gösterildiğine bakmıyordu. Aradaki fark ölçüldü: `levels` izinde üretici
        kaynak hücreyi (`"EQF 6 / EQF 7 (EQF 7 İPTAL)"`) kaydediyordu ve
        `app.js` onu hiç okumuyordu. Kartta yalnız "bir kademe çıkarıldı"
        yazıyor, hangisi olduğu görünmüyordu.

        Vaat şu: kaynaktan ayrıldığımız yerde öğrenci **kaynaktaki hâli de**
        görebilmeli. Türü göstermek o vaadin yarısı.
        """
        veri = json.loads((ROOT / "site" / "data-maku.json")
                          .read_text(encoding="utf-8"))["agreements"]
        js = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        bas = js.index("function sourceNote")
        son = js.index("\nfunction ", bas + 10)
        govde = js[bas:son]

        # Yalnız kaynakta gerçekten bir değer olan türler. `country` izinde
        # değer `null` olabiliyor (kaynak hücre boştu) ve orada gösterilecek
        # bir şey yok · o durumun kendi metni var.
        degerli = {k for r in veri
                   for k, v in (r.get("sourceDiff") or {}).items()
                   if isinstance(v, dict) and v.get("kaynakta") is not None}
        self.assertTrue(degerli,
                        "Veride kaynakta değeri taşıyan hiç iz yok; ya kaynak "
                        "düzeldi ya da üretim kırıldı.")

        gizli = [k for k in sorted(degerli) if f"d.{k}.kaynakta" not in govde]
        self.assertEqual(gizli, [],
                         f"Üretici bu izlerde kaynaktaki değeri yazıyor ama "
                         f"sourceNote onu okumuyor, yani kartta görünmüyor: "
                         f"{gizli}")

        # Okumak yetmiyor, **yerine koymak** gerekiyor. `d.country.kaynakta`
        # koşulda da geçiyor (`kaynakta ? şu : bu`), dolayısıyla yalnız adın
        # varlığına bakan bir denetim, değeri göstermeyi bırakan bir
        # değişikliği kaçırıyor · mutasyonla ölçüldü, kaçırdı.
        #
        # Bu, bu sınıfın üstteki testinde zaten yazılı tuzağın bir kat derini:
        # metnin dosyada bulunması, o metnin çalıştığı anlamına gelmiyor.
        yerlestirme = govde.count('replace("{0}"')
        self.assertGreaterEqual(
            yerlestirme, len(degerli),
            f"Kaynaktaki değeri taşıyan {len(degerli)} iz türü var ama "
            f"sourceNote yalnız {yerlestirme} yerine koyma yapıyor. En az "
            f"biri değeri okuyup ekrana koymuyor.")

    def test_veride_iz_varsa_gosterimde_karsiligi_var(self):
        veri = json.loads((ROOT / "site" / "data-maku.json")
                          .read_text(encoding="utf-8"))["agreements"]
        js = (ROOT / "site" / "app.js").read_text(encoding="utf-8")

        alanlar = set()
        for r in veri:
            alanlar.update((r.get("sourceDiff") or {}).keys())
        self.assertTrue(alanlar, "Veride hiç sourceDiff yok; ya kaynak "
                                 "düzeldi ya da izleme kırıldı.")

        self.assertIn("sourceDiff", js,
                      "app.js sourceDiff alanını hiç okumuyor; veri iz "
                      "taşıyor ama kartta görünmüyor.")

        # Metin varlığı yetmiyor: `if (false)` yazılsa da `d.country` dosyada
        # kalıyordu ve ilk yazımda bu test mutasyonu KAÇIRDI. O yüzden üç ayrı
        # halka denetleniyor: kart iz işlevini çağırıyor mu, işlev alanı okuyor
        # mu, okuduğunda bir metin üretiyor mu.
        self.assertIn("${sourceNote(a)}", js,
                      "card() sourceNote'u çağırmıyor; işlev tanımlı olsa da "
                      "kartta hiçbir iz görünmez.")
        bas = js.index("function sourceNote")
        son = js.index("\nfunction ", bas + 10)
        govde = js[bas:son]
        eksik = [a for a in alanlar
                 if f"d.{a}" not in govde or f"parcalar.push" not in govde]
        self.assertEqual(eksik, [],
                         f"sourceNote bu alanı okumuyor ya da metin üretmiyor: "
                         f"{eksik}. Öğrenci o ayrımı göremiyor.")
        for alan in ("country", "levels", "iscedFamily"):
            self.assertIn(f"if (d.{alan})", govde,
                          f"sourceNote '{alan}' izini okumuyor.")

    def test_izlenmeyen_ayrimlar_yazili(self):
        """İz bırakmadığımız ayrım varsa, bunun kayıtlı olması gerekiyor.

        Bugün bir tane var: Bölüm adının başındaki ISCED kodunun ayrılması.
        İzlenmiyor, çünkü 465 kartta olur ve gürültü yaratırdı; kozmetik bir
        ayrım, gösterilen bilgiyi değiştirmiyor.

        Bu testin işi kararı doğrulamak değil, **yazılı olmasını** güvenceye
        almak. Gerekçesiz bir sessizlik ile gerekçeli bir sessizlik arasındaki
        fark, bu projede tekrar tekrar çıkan ayrım.
        """
        kaynak = (ROOT / "KAYNAK.md").read_text(encoding="utf-8")
        self.assertIn("Bölüm adının başındaki kodu ayırıyoruz", kaynak,
                      "İzlenmeyen ayrım KAYNAK.md'de sayılmıyor.")
        self.assertRegex(kaynak, r"iz(i| bırak)[^\n]{0,80}(yok|bırakmıyor)",
                         "İzlenmeyen ayrımın izsiz olduğu açıkça yazılmamış.")

    def test_iz_metinleri_iki_dilde_var(self):
        js = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
        for anahtar in ("diffCountryFixed", "diffCountryFilled", "diffLevel"):
            self.assertEqual(js.count(f"{anahtar}:"), 2,
                             f"'{anahtar}' iki sözlükte birden olmalı "
                             f"(TR + EN); bulunan: {js.count(anahtar + ':')}")


class KisiselVeri(unittest.TestCase):
    """Yayımlanan veride üçüncü kişilerin kimlik bilgisi bulunmuyor.

    Kaynak tabloda iki sütun kişisel veri taşıyor: anlaşmayı imzalayan
    kişinin adı ve e-posta adresi. Bunlar 20 Ağustos 2026'ya kadar
    yayımlanan JSON'a giriyordu · 466 ad, 303 adres.

    Üç sebeple çıkarıldı ve üçü de birbirinden bağımsız:

    1. Bu kişiler partner üniversitelerde çalışıyor, çoğu AB'de. Verinin
       sahibi biz değiliz ve toplayıp yeniden yayımlamak için elimizde bir
       dayanak yok. `KAYNAK.md` zaten "veri sizin" diyor.
    2. Dağınık kurumsal sayfalarda durmakla tek bir JSON'da toplanmış
       olmak farklı şeyler. İkincisi doğrudan hasat vektörü.
    3. Depo açık kaynak. Bir kez girdiğinde git geçmişinde kalıyor;
       sonradan silmek yayımlanmış olmayı geri almıyor.

    Kaybedilen işlev yerine konmadı, çünkü zaten yanlış işlevdi: MAKÜ'de
    okuyan bir öğrenci Bialystok'taki koordinatöre doğrudan yazmaz, kendi
    kurumunun ofisine başvurur. Kartta duran `mailto` bağlantısı yanlış
    davranışı öneriyordu.

    `app.js` kurumsal siteyi (`website`) zaten kişisel e-postaya tercih
    ediyordu; şema yuvası duruyor, tüketicisi bekçili.
    """

    EPOSTA = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    YASAK_ALAN = ["email", "contact"]

    def veri_dosyalari(self):
        return sorted((ROOT / "site").glob("data-*.json"))

    def test_yayimlanan_veride_eposta_yok(self):
        bulgu = []
        for yol in self.veri_dosyalari():
            for adres in set(self.EPOSTA.findall(yol.read_text(encoding="utf-8"))):
                bulgu.append(f"{yol.name}: {adres}")
        self.assertEqual(
            bulgu, [],
            "Yayımlanan veride e-posta adresi var:\n  " + "\n  ".join(bulgu)
            + "\n\nBu adresler üçüncü kişilere ait. Ayrıştırıcı kaynak "
              "tablonun e-posta sütununu okumamalı.")

    def test_yayimlanan_veride_kisisel_alan_yok(self):
        bulgu = []
        for yol in self.veri_dosyalari():
            kayitlar = json.loads(yol.read_text(encoding="utf-8")).get("agreements", [])
            for alan in self.YASAK_ALAN:
                sayi = sum(1 for k in kayitlar if alan in k)
                if sayi:
                    bulgu.append(f"{yol.name}: '{alan}' {sayi} kayıtta")
        self.assertEqual(
            bulgu, [],
            "Yayımlanan veride kişisel alan geri gelmiş:\n  " + "\n  ".join(bulgu)
            + "\n\nKarar KAYNAK.md §5'te yazılı. Değiştirilecekse önce orası "
              "değişmeli, sonra bu bekçi.")

    def test_ayristirici_kisisel_sutunlari_okumuyor(self):
        """Üretici tarafı da bekçili: sütun haritasına geri eklenmesin.

        Yalnız çıktıya bakmak yetmez · alan okunup başka bir ada yazılırsa
        çıktı temiz görünürdü. Bu test kaynağı okuyor.
        """
        kaynak = (ROOT / "scripts" / "build_data.py").read_text(encoding="utf-8")
        # Yalnız sütun haritası ve kayıt sözlüğü aranıyor; docstring'de
        # "okunmuyor" diye geçmesi meşru.
        satirlar = [s for s in kaynak.split("\n")
                    if re.search(r'"(eposta|imzalayan|email|contact)"\s*:', s)]
        self.assertEqual(
            satirlar, [],
            "build_data.py kişisel sütunu geri okumaya başlamış:\n  "
            + "\n  ".join(s.strip() for s in satirlar))


if __name__ == "__main__":
    unittest.main()


class MarmaraKontenjanDilbilgisi(unittest.TestCase):
    """Kontenjan hücresi hem sayıyı hem seviyeyi taşıyor · dilbilgisi ölçüldü.

    Marmara listesinde `2(L,YL,D)` iki şey söylüyor: iki kontenjan, ve bu
    kontenjanın üç kademe arasında **paylaşıldığı.** `2L,1YL` ise ayrı ayrı
    sayılıyor. Ayrımı düzleştirmek öğrenciye yanlış bilgi vermek olurdu ·
    "her kademeye iki" ile "üçü toplam iki" aynı şey değil.

    İlk ayrıştırma denemesi her virgülden bölüyordu ve `2(L,YL,D)` üç parçaya
    dağılıyordu. Bölme artık parantez derinliğini sayıyor.

    Kaynaktaki 68 farklı yazımın hepsi ayrışıyor · bu test onu koruyor.
    """

    def test_bilinen_yazimlar_dogru_cozuluyor(self):
        for ham, beklenen in [
            ("4L", {"lisans": "4"}),
            ("2L,1YL", {"lisans": "2", "yukseklisans": "1"}),
            ("2(L,YL,D)", {"lisans": "shared", "yukseklisans": "shared", "doktora": "shared"}),
            ("3L,1(YL,D)", {"lisans": "3", "yukseklisans": "shared", "doktora": "shared"}),
            ("4(L,YL),2D", {"lisans": "shared", "yukseklisans": "shared", "doktora": "2"}),
            ("2L, 1(YL,D)", {"lisans": "2", "yukseklisans": "shared", "doktora": "shared"}),
            ("0", {}),
            ("", {}),
        ]:
            self.assertEqual(bd.marmara_seviyeler(ham), beklenen, f"yazım: {ham!r}")

    def test_parantez_ici_virgul_bolmuyor(self):
        """İlk hâlin kırıldığı yer · kalıp geri gelmesin."""
        self.assertEqual(bd.marmara_kontenjan_bol("2L,1(YL,D)"), ["2L", "1(YL,D)"])
        self.assertEqual(bd.marmara_kontenjan_bol("4(L,YL),2D"), ["4(L,YL)", "2D"])


class EpostaAyiklama(unittest.TestCase):
    """Serbest metin hücrelerinde e-posta adresi geliyor · yayımlanmıyor.

    Marmara listesinde bir açıklama notu partner kurumun adresini taşıyordu.
    Not gerçek bilgi veriyor ("B1 Almanca"), o yüzden not atılmıyor · yalnız
    adres çıkarılıyor ve karta iz bırakılıyor.

    Bunun bekçisi ikinci bir yerde de var: `KisiselVeri` üretilen JSON'da
    adres arıyor. Bu test kaynağı, o test çıktıyı denetliyor · biri kalıbı,
    öteki sonucu.
    """

    def test_adres_cikiyor_not_kaliyor(self):
        ham = "Karşı kurum B1 seviyesinde Almanca bilgisi talep etti. abc-x@polsoz.fu-berlin.de ID: EWP-15452507"
        temiz, vardi = bd.eposta_ayikla(ham)
        self.assertTrue(vardi)
        self.assertNotIn("@", temiz)
        self.assertIn("B1 seviyesinde Almanca", temiz)
        self.assertIn("EWP-15452507", temiz)

    def test_adressiz_not_degismiyor(self):
        """Yanlış alarm kontrolü · dokunulmaması gereken metne dokunulmuyor."""
        ham = "Anlaşma metninde B2 seviyesi belirtilmektedir."
        self.assertEqual(bd.eposta_ayikla(ham), (ham, False))


class UcKaynakAyniSemayi_Uretiyor(unittest.TestCase):
    """Üç ayrıştırıcı da aynı kayıt şemasını üretmeli.

    Üç üniversitenin tablosu birbirine benzemiyor: biri 19 sütunlu tek sayfa,
    biri 27 sayfa, biri fakülte blokları. Site ise **tek** bir okuyucu ·
    `app.js` hepsini aynı alan adlarıyla okuyor.

    Bir ayrıştırıcı bir alanı unutursa ya da başka adlandırırsa site o alanı
    sessizce `undefined` okuyor: Kart boş görünüyor, hata çıkmıyor. Bu test o
    sessizliği kapatıyor.
    """

    ZORUNLU = {"country", "erasmusCode", "university", "iscedCode", "department",
               "levels", "quotaStudy", "quotaInternship", "quotaStaffTeach",
               "quotaStaffTrain", "quotaNote", "search",
               "iscedFamily", "iscedFamilyTr", "iscedFamilyEn"}
    SEVIYELER = {"onlisans", "lisans", "yukseklisans", "doktora"}

    def veriler(self):
        for yol in sorted((ROOT / "site").glob("data-*.json")):
            yield yol.stem, json.loads(yol.read_text(encoding="utf-8"))

    def test_her_kayitta_zorunlu_alanlar_var(self):
        eksik = []
        for ad, d in self.veriler():
            for r in d["agreements"]:
                yok = self.ZORUNLU - set(r)
                if yok:
                    eksik.append(f"{ad} · {r.get('erasmusCode')} · eksik: {sorted(yok)}")
                    break
        self.assertEqual(eksik, [], "Ayrıştırıcılar aynı şemayı üretmiyor:\n  " + "\n  ".join(eksik))

    def test_seviye_anahtarlari_sitenin_bildikleri(self):
        """`app.js` LEVELS listesindeki anahtarları okuyor; başkası sessizce düşer."""
        bilinmeyen = set()
        for _, d in self.veriler():
            for r in d["agreements"]:
                bilinmeyen |= set(r.get("levels") or {}) - self.SEVIYELER
        self.assertEqual(bilinmeyen, set(), f"app.js'in tanımadığı kademe anahtarı: {bilinmeyen}")

    def test_en_az_uc_kaynak_var(self):
        """Alt sınır · bir veri dosyası üretilmezse üstteki testler boşa döner."""
        n = len(list(self.veriler()))
        self.assertGreaterEqual(n, 3, f"Yalnız {n} veri dosyası bulundu.")


class EsoguFakulteSiniri(unittest.TestCase):
    """Fakülte değişince devralınan bölüm adı düşer.

    ESOGÜ tablosunda fakülte ve bölüm hücreleri blok başında bir kez yazılı,
    sonrası boş · 259 satırın 16'sında fakülte dolu. Okuyan taraf bu yüzden
    son gördüğü değeri taşıyor.

    Tehlike şurada: Yeni bir fakülte bloğu **bölümsüz** başlarsa, taşınan
    değer bir önceki fakültenin bölümü oluyor ve anlaşma yanlış programın
    altında görünüyor. Hiçbir hata çıkmıyor, sayı da değişmiyor.

    BU TEST SENTETİK VERİYLE ÇALIŞIYOR VE SEBEBİ YAZILI

    Bugünkü dosyada kalıbı tetikleyen satır yok · tek bölümsüz satır tablonun
    ilk satırı ve öncesinde devralınacak bir şey yok. Yani koruma kaldırılsa
    üretilen JSON aynı kalıyor, mutasyon bekçinin görüş alanına düşmüyor.

    Ölçüldüğünde kaçan mutasyon buydu. Karşılığı eşiği gevşetmek değil,
    davranışı **veriden bağımsız** sınamak: Aşağıdaki sahte tablo kalıbı
    bilerek kuruyor.
    """

    class SahteSayfa:
        def __init__(self, satirlar):
            self._s = satirlar

        def iter_rows(self, min_row=1, values_only=True):
            return iter(self._s[min_row - 1:])

    def sayfa(self):
        b = ["", ""] * 6
        return self.SahteSayfa([
            tuple(["FAKÜLTE", "BÖLÜM", "ERASMUS ID", "ÜNİVERSİTE", "ÜLKE", "SITE",
                   "ÖL", "L", "YL", "D", "DERS", "EĞİTİM"]),
            ("EĞİTİM FAKÜLTESİ", "MATEMATİK ÖĞRETMENLİĞİ", "PL KRAKOW01",
             "UNIWERSYTET KRAKOW", "POLONYA", "", "0", "2", "0", "0", "1", "1"),
            # Yeni fakülte, bölüm hücresi BOŞ · devralma tam burada olurdu
            ("TIP FAKÜLTESİ", "", "D BERLIN01", "UNIVERSITAET BERLIN",
             "ALMANYA", "", "0", "1", "0", "0", "1", "1"),
        ])

    def test_yeni_fakultenin_bolumu_oncekinden_devralinmiyor(self):
        kayitlar = bd.parse_esogu(self.sayfa())
        self.assertEqual(len(kayitlar), 2)
        ilk, ikinci = kayitlar
        self.assertEqual(ilk["department"], "MATEMATİK ÖĞRETMENLİĞİ")
        self.assertNotEqual(
            ikinci["department"], "MATEMATİK ÖĞRETMENLİĞİ",
            "Yeni fakültenin bölümsüz satırı, önceki fakültenin bölümünü "
            "devraldı. Anlaşma yanlış programın altında görünür ve hiçbir "
            "hata çıkmaz.")
        self.assertEqual(ikinci["department"], "TIP FAKÜLTESİ")

    def test_bolumsuz_satir_iz_birakiyor(self):
        """Fakülte adı bölüm adı sanılmamalı · fark karta yazılıyor."""
        ikinci = bd.parse_esogu(self.sayfa())[1]
        self.assertEqual(ikinci.get("sourceDiff", {}).get("department", {}).get("sebep"),
                         "fakulte-adi")


class SuresiDolmusAnlasmalar(unittest.TestCase):
    """Süresi geçmiş anlaşmaların sayısı sabitleniyor · hiçbir yerde bakılmıyordu.

    Bir anlaşmanın geçerlilik aralığı kartta yazılı ama "2022/2024" ile
    "2022/2029" aynı görünüyor · okuyan kişi yılı kendisi hesaplamak zorunda.
    Süresi dolmuş bir anlaşmaya hazırlanan öğrenci boşuna hazırlanıyor.

    İki karşılık verildi:

      · Kart artık "süresi doldu" yazıyor · hesap ÇALIŞMA ANINDA yapılıyor,
        derlemede değil. Derlemede yapılsaydı bayrak dosyayla donardı ve
        gelecek yıl sessizce yanlış olurdu.
      · Bu test sayıyı pimliyor. Artarsa bakılır: Kaynak eskimiş olabilir ya
        da kurum listesini güncellememiş olabilir · ikisi de kuruma
        söylenecek bir şey.

    **Test kırık DEĞİL, sayı sabit.** Dolmuş anlaşmanın varlığı bizim hatamız
    değil, kaynağın durumu · kalıcı kırmızı bir test bütün dağıtımları bloke
    ederdi (bu depoda bir kez yaşandı ve model değişti).

    BU DENETİM İKİ KEZ YANLIŞ ÖLÇTÜ VE İKİSİ DE KAYDA DEĞER

    İlk hâli bitiş yılını `\\b(20\\d{2})\\b` ile arıyordu. Kaynakta "2022/27"
    yazımı da var ve orada 2027 kastediliyor · tarama 2022'yi bulup otuz üç
    anlaşmayı yanlışlıkla "dolmuş" saydı. İki haneli son ek ayrıca ele
    alınıyor.
    """

    # Ölçüldü 24 Ağustos 2026 · kaynak listeler o gün indirildi.
    BEKLENEN = {"data-maku": 3, "data-marmara": 0, "data-esogu": 0}

    @staticmethod
    def bitis_yili(ham):
        parca = re.split(r"[/\-–]", str(ham).strip())
        if len(parca) < 2:
            t = re.findall(r"\b(20\d{2})\b", str(ham))
            return int(t[-1]) if t else None
        son = parca[-1].strip()
        if re.fullmatch(r"20\d{2}", son):
            return int(son)
        if re.fullmatch(r"\d{2}", son):
            return 2000 + int(son)
        return None

    def say(self, ad):
        d = json.loads((ROOT / "site" / f"{ad}.json").read_text(encoding="utf-8"))
        n = 0
        for a in d["agreements"]:
            ham = (a.get("validity") or {}).get("raw", "")
            y = self.bitis_yili(ham) if ham else None
            if y is not None and y < datetime.now().year:
                n += 1
        return n

    def test_dolmus_sayisi_beklenenle_ayni(self):
        fark = {ad: (bek, self.say(ad)) for ad, bek in self.BEKLENEN.items()
                if self.say(ad) != bek}
        self.assertEqual(fark, {},
                         f"Süresi dolmuş anlaşma sayısı değişti (beklenen, bulunan): {fark}\n"
                         f"Artmışsa kaynak eskimiş ya da kurum listeyi güncellememiş · "
                         f"kuruma bildirilecek bir şey. Azalmışsa kurum düzeltmiş olabilir.\n"
                         f"Doğrulayıp buradaki sayıyı güncelleyin.")

    def test_iki_haneli_yil_dogru_okunuyor(self):
        """Yanlış alarmın kaynağı buydu · kalıp geri gelmesin."""
        self.assertEqual(self.bitis_yili("2022/27"), 2027)
        self.assertEqual(self.bitis_yili("2022/2027"), 2027)
        self.assertEqual(self.bitis_yili("2022-2023"), 2023)
        self.assertEqual(self.bitis_yili("2021/29"), 2029)


class AyniPartnerAyniBolumIkiKez(unittest.TestCase):
    """Aynı kod + aynı bölüm birden çok kez geçiyor · sayısı sabitleniyor.

    Bunlar kopya DEĞİL: Çoğunda geçerlilik aralığı, kontenjan ve dil farklı ·
    yani kaynakta iki ayrı anlaşma kayıtlı. Örnek, Marmara `D GIESSEN02`
    Biyomühendislik: biri 2024/2029 (2 lisans + 1 yüksek lisans, Almanca),
    öteki 2019/2029 (6 lisans, İngilizce + Almanca).

    **Bunu biz çözmüyoruz ve çözmemeliyiz.** Hangisinin geçerli olduğunu
    kurum bilir; birini seçmek öğrenciye var olmayan bir kesinlik sunmak
    olurdu. İkisi de gösteriliyor.

    Ama bir tanesi kuruma sorulmaya değer: MAKÜ `LV REZEKNE02`, aynı yıl
    başlayan iki kayıt taşıyor ve kontenjanları 18 ile 2 · aradaki fark bir
    yazım hatasına benziyor.

    Test sayıyı pimliyor: Artarsa kaynağa yeni bir çift girmiş demek.
    """

    BEKLENEN = {"data-maku": 19, "data-marmara": 6, "data-esogu": 2}

    def say(self, ad):
        d = json.loads((ROOT / "site" / f"{ad}.json").read_text(encoding="utf-8"))["agreements"]
        c = collections.Counter((a["erasmusCode"], a["department"]) for a in d)
        return sum(1 for v in c.values() if v > 1)

    def test_yinelenen_cift_sayisi_beklenenle_ayni(self):
        fark = {ad: (bek, self.say(ad)) for ad, bek in self.BEKLENEN.items()
                if self.say(ad) != bek}
        self.assertEqual(fark, {},
                         f"Aynı partner+bölüm çifti sayısı değişti (beklenen, bulunan): {fark}\n"
                         f"Kaynağa yeni bir çift girmiş olabilir · bakıp buradaki sayıyı "
                         f"güncelleyin.")
