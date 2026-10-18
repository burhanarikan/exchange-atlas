"""Ortak ayrıştırma, normalleştirme ve doğrulama yardımcıları."""
import re
import unicodedata
from datetime import datetime

# ISCED-F 2013 broad fields (first two digits of the code)
ISCED_FAMILY = {
    "00": ("Genel programlar", "Generic programmes"),
    "01": ("Eğitim", "Education"),
    "02": ("Sanat ve beşeri bilimler", "Arts and humanities"),
    "03": ("Sosyal bilimler, gazetecilik", "Social sciences, journalism"),
    "04": ("İşletme, yönetim, hukuk", "Business, administration, law"),
    "05": ("Doğa bilimleri, matematik", "Natural sciences, mathematics"),
    "06": ("Bilişim ve iletişim (BİT)", "Information and Communication Tech."),
    "07": ("Mühendislik, üretim, inşaat", "Engineering, manufacturing, construction"),
    "08": ("Tarım, ormancılık, veterinerlik", "Agriculture, forestry, veterinary"),
    "09": ("Sağlık ve refah", "Health and welfare"),
    "10": ("Hizmetler", "Services"),
}

# Unicode decomposition handles characters that split into "letter + mark"
# (ä -> a + ¨). The ones below are separate letters, so that route does not work;
# they are mapped by hand. Must stay identical to its twin in app.js
# (see tests/test_couplings.py).
FOLD_EXCEPTIONS = str.maketrans({
    "ı": "i", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D",
    "ø": "o", "Ø": "O", "ß": "ss",
})


def fold(s):
    """Arama anahtarı: aksan ve işaret farklarını düzleştirir."""
    if s is None:
        return ""
    s = str(s).translate(FOLD_EXCEPTIONS)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def tr_upper(s):
    """Türkçe-doğru büyük harf: 'Bulgaristan' -> 'BULGARİSTAN'."""
    return s.replace("i", "İ").replace("ı", "I").upper()


def unify_department_spelling(agreements):
    """Aynı bölümün yalnız büyük/küçük harfle ayrışan yazımlarını birleştirir.

    Kaynak tabloda aynı bölüm birden çok yazımla giriliyor: `İnşaat
    Mühendisliği` ve `İnşaat mühendisliği` gibi. Arama bunu zaten
    düzleştiriyor (`fold` büyük/küçük farkını siliyor), etkilenen tek şey
    **kartta görünen yazım**: Aynı bölüm iki farklı biçimde görünüyor.

    Seçim kuralı: **kurumun kendi yazımlarından en sık kullanılanı.** Yeni bir
    yazım üretilmiyor, hangisinin "doğru" olduğuna karar verilmiyor; yalnız
    kurumun ağırlıklı olarak kullandığı biçim tutarlı gösteriliyor.

    **Beraberlikte dokunulmuyor.** İki yazım eşit sıklıktaysa seçmek için
    elimizde ölçü kalmıyor ve orada tercih yapmak yazım tercihi dayatmak
    olurdu. O gruplar olduğu gibi bırakılıyor ve `KAYNAK.md`'de bildiriliyor.

    Her değişiklik `sourceDiff`'e yazılıyor, yani öğrenci kaynakta ne yazdığını
    kartta görüyor.
    """
    def tr_lower(s):
        return s.replace("I", "ı").replace("İ", "i").lower()

    gruplar = {}
    for a in agreements:
        dep = a.get("department")
        # If the department name already carries a trace (it fell back to the
        # ISCED label), that spelling is not the institution's own; keep it out.
        if not dep or "department" in (a.get("sourceDiff") or {}):
            continue
        gruplar.setdefault(tr_lower(dep), {})
        gruplar[tr_lower(dep)][dep] = gruplar[tr_lower(dep)].get(dep, 0) + 1

    secilen, beraberlik = {}, 0
    for anahtar, sayim in gruplar.items():
        if len(sayim) < 2:
            continue
        sirali = sorted(sayim.items(), key=lambda t: -t[1])
        if sirali[0][1] == sirali[1][1]:
            beraberlik += 1
            continue
        secilen[anahtar] = sirali[0][0]

    degisen = 0
    for a in agreements:
        dep = a.get("department")
        if not dep or "department" in (a.get("sourceDiff") or {}):
            continue
        kazanan = secilen.get(tr_lower(dep))
        if not kazanan or kazanan == dep:
            continue
        a.setdefault("sourceDiff", {})["department"] = {
            "kaynakta": dep, "sebep": "yazim-birligi",
        }
        a["department"] = kazanan
        degisen += 1
    return degisen, beraberlik


def clean(v):
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.isoformat()
    # Non-breaking space (\xa0) becomes a normal space: indistinguishable by eye
    # but it breaks search matching. .strip() already removes it at the START/END;
    # this conversion is for the ones left in the MIDDLE of the text.
    return str(v).replace("\xa0", " ").strip()


def _bosluk_sadelestir(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def isced_family(code):
    if code is None:
        return None
    digits = re.sub(r"\D", "", str(code))
    if not digits:
        return None
    if len(digits) == 1:
        digits = "0" + digits
    # Broad field = first two digits. Excel can eat a leading zero
    # ("0610" -> "610"), so if the first two digits are NOT a valid family we
    # assume a lost zero and prepend "0". If they ARE valid ("104" -> "10",
    # Services) LEAVE IT ALONE: otherwise genuine three-digit codes in family 10
    # would silently shift into "01".
    fam = digits[:2]
    if fam not in ISCED_FAMILY:
        fam = ("0" + digits)[:2]
    return fam if fam in ISCED_FAMILY else None


def aile_tahminle_bulundu(code):
    """Aile, baştaki sıfırın yendiği VARSAYILARAK mı bulundu?

    Üç haneli bir kodda iki okuma mümkün: `104` ya "10" ailesi (Hizmetler) ya da
    baştaki sıfırı yenmiş bir `0104`. Kod ilk okumayı deniyor, tutmazsa sıfır
    ekliyor. İkinci yola düşen kayıtlar **tahminle** sınıflandırılmış oluyor ve
    bunu öğrencinin görmesi gerekiyor.

    Bugün 12 kayıt bu durumda ve on ikisi de bölüm adına bakılarak elle
    doğrulandı (bkz. tests/test_kaynak_verisi.py, UcHaneliKodlar).
    """
    if code is None:
        return False
    digits = re.sub(r"\D", "", str(code))
    if len(digits) != 3:
        return False
    return digits[:2] not in ISCED_FAMILY


def fam_fields(code):
    fam = isced_family(code)
    return {
        "iscedFamily": fam,
        "iscedFamilyTr": ISCED_FAMILY[fam][0] if fam else None,
        "iscedFamilyEn": ISCED_FAMILY[fam][1] if fam else None,
    }


def parse_validity(text):
    raw = clean(text)
    return {"raw": raw} if raw else None


# The prefix of an Erasmus institution code identifies the country. Two shapes
# exist: today's two-letter form (ISO 3166-1, with two EU exceptions: Greece EL,
# United Kingdom UK) and the pre-2014 single-letter form.
#
# NOTE ON EVIDENCE: the two-letter convention is well known, but it was not
# verified here against an official specification. What IS verified is the
# measurement below, taken from the data itself. KAYNAK.md says the same;
# the two must not drift apart.
#
# Measured across the two sources that HAVE a country column (MAKU 468 rows,
# ESOGU 259 rows): 722 rows agree, 4 disagree, 2 have an empty column. The 4
# disagreements are all MAKU's and all documented; ESOGU agrees on every row.
#
# The third source (Marmara) has no country column at all, so there the prefix
# is not a cross-check but the ONLY reading. That is why a Marmara row with an
# unreadable prefix is dropped rather than shown with a blank country.
ERASMUS_ULKE = {
    "AT": "Avusturya", "BE": "Belçika", "BG": "Bulgaristan", "CY": "Kıbrıs",
    "CZ": "Çekya", "DE": "Almanya", "DK": "Danimarka", "EE": "Estonya",
    "EL": "Yunanistan", "ES": "İspanya", "FI": "Finlandiya", "FR": "Fransa",
    "HR": "Hırvatistan", "HU": "Macaristan", "IE": "İrlanda", "IS": "İzlanda",
    "IT": "İtalya", "LT": "Litvanya", "LV": "Letonya", "LU": "Lüksemburg", "MK": "Kuzey Makedonya",
    "MT": "Malta", "NL": "Hollanda", "NO": "Norveç", "PL": "Polonya",
    "PT": "Portekiz", "RO": "Romanya", "RS": "Sırbistan", "SE": "İsveç",
    "SI": "Slovenya", "SK": "Slovakya", "TR": "Türkiye", "UK": "Birleşik Krallık",
    # Pre-2014 single-letter codes
    "A": "Avusturya", "B": "Belçika", "D": "Almanya", "E": "İspanya", "L": "Lüksemburg",
    "F": "Fransa", "G": "Yunanistan", "I": "İtalya", "P": "Portekiz",
    # S (Sverige) was missing until Marmara's list arrived: five rows were
    # dropped for an unreadable country. Three witnesses agree it is Sweden ·
    # the legacy pattern (a letter from the country's own name, like SF for
    # Suomi Finland), and the institution names themselves: Kristianstad,
    # Södertörn, Stockholm, Umeå.
    "S": "İsveç",
    "SF": "Finlandiya",
}


def ulke_onekten(erasmus_kodu):
    """Erasmus kurum kodundan ülkeyi çıkarır; bilinmiyorsa None."""
    m = re.match(r"\s*([A-Z]{1,2})[\s-]", erasmus_kodu or "")
    return ERASMUS_ULKE.get(m.group(1)) if m else None


def isced_kodu(*hucreler):
    """Aynı kodu birden çok sütun taşıyor; en ayrıntılı olanı seçer.

    MAKÜ tablosunda ISCED kodu üç yerde geçiyor: bölüm adlarının önünde
    ("0610-Bilgisayar Mühendisliği") ve ayrı bir kod sütununda. Uzun süre
    yalnız kod sütunu okundu ve o sütun 467 kaydın 246'sında boştu; site de
    o kayıtlar için "alan bilgisi yok" gösteriyordu.

    Ölçüldü: boş görünen 246 kaydın 245'inde kod bölüm adının önünde duruyordu.
    Yani eksik olan veri değil, okuduğumuz sütundu.

    ISCED hiyerarşik: 06 geniş alan, 061 dar alan, 0610 ayrıntılı alan. Üç
    sütun farklı derinlik taşıyabiliyor ve bu bir çelişki değil. En uzun olanı
    seçiyoruz, çünkü ayrıntılı olan dar olanı zaten içeriyor.

    Sıra da önemli: eşit uzunlukta iki aday varsa Türkçe sütun kazanıyor,
    çünkü sitede gösterilen bölüm adı oradan geliyor.
    """
    candidates = []
    for h in hucreler:
        m = re.match(r"\s*(\d{3,4})\b", clean(h))
        if m:
            candidates.append(m.group(1))
    return max(candidates, key=len) if candidates else ""


# Free-text cells sometimes carry an e-mail address. The published data must
# not (KAYNAK.md §5): we do not republish addresses that people did not give
# us, and an address in a partner's note is no different from one in a signer
# column, which is not read at all.
#
# The note itself is kept, because it carries real information ("B1 German
# required"). Only the address is removed, and the removal leaves a trace, so
# a student does not read a truncated sentence and wonder what is missing.
EPOSTA = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")


def eposta_ayikla(metin):
    """Returns (cleaned text, was anything removed)."""
    if not metin or not EPOSTA.search(metin):
        return metin, False
    temiz = re.sub(r"\s{2,}", " ", EPOSTA.sub("", metin)).strip(" ·,;")
    return temiz, True


def make_search(rec, extra=""):
    return fold(" ".join(filter(None, [
        rec["country"], rec["university"], rec["department"],
        rec["iscedCode"], rec["erasmusCode"],
        rec["iscedFamilyTr"] or "", rec["iscedFamilyEn"] or "", extra,
    ])))
