"""Marmara Üniversitesi ikili anlaşma ayrıştırıcısı."""
import re
import sys

from .common import (
    clean,
    eposta_ayikla,
    fam_fields,
    make_search,
    tr_upper,
    ulke_onekten,
)

# The sheet holds the quota AND the levels in one cell. Grammar, taken from
# the data (68 distinct spellings, all of them parse):
#
#   "4L"          4 places, bachelor's only
#   "2L,1YL"      2 bachelor's + 1 master's, counted separately
#   "2(L,YL,D)"   2 places SHARED across bachelor's, master's and doctorate
#   "0"           no student quota
#
# Commas inside parentheses bind the group, commas outside separate segments.
# A first attempt split on every comma and broke "2(L,YL,D)" into three
# fragments; that is why the split below is depth-aware.
MARMARA_SEVIYE = {"ÖL": "onlisans", "L": "lisans", "YL": "yukseklisans", "D": "doktora"}
MARMARA_PARCA = re.compile(r"^(\d+)\s*(?:\(([^)]*)\)|([A-ZÖ]*))$")


def marmara_kontenjan_bol(s):
    """Splits on commas OUTSIDE parentheses."""
    parcalar, derinlik, son = [], 0, 0
    for i, ch in enumerate(s):
        if ch == "(":
            derinlik += 1
        elif ch == ")":
            derinlik -= 1
        elif ch == "," and derinlik == 0:
            parcalar.append(s[son:i])
            son = i + 1
    parcalar.append(s[son:])
    return [p.strip() for p in parcalar if p.strip()]


def marmara_seviyeler(kontenjan):
    """Reads the level flags out of the quota cell.

    A level inside parentheses gets "shared" instead of a number, because the
    places are not per-level: "2(L,YL)" means two places that bachelor's and
    master's students compete for together. The site already renders that with
    a star, so the distinction reaches the student instead of being flattened
    into "2 for each".
    """
    seviyeler = {}
    for parca in marmara_kontenjan_bol(clean(kontenjan)):
        m = MARMARA_PARCA.match(parca)
        if not m:
            continue
        sayi, grup, tek = m.group(1), m.group(2), m.group(3)
        if int(sayi) <= 0:
            continue
        if grup:
            for kod in re.split(r"[,\s]+", grup):
                if kod in MARMARA_SEVIYE:
                    seviyeler[MARMARA_SEVIYE[kod]] = "shared"
        elif tek in MARMARA_SEVIYE:
            seviyeler[MARMARA_SEVIYE[tek]] = sayi
    return seviyeler


MARMARA_LEJANT_BASI = "Zorunlu Dil ID"


def marmara_dil_sozlugu(wb):
    """The language legend sits BELOW the data in every sheet.

    The 'foreign language' column holds numbers ("1", "1;19"), not names. The
    key is a two-column table appended under each sheet's agreements. Without
    it the field is unreadable, so it is not optional.

    Read from every sheet and cross-checked: 66 entries, no sheet disagrees
    with another. Had they disagreed we would have to say which one wins;
    they do not, so the question does not arise.
    """
    sozluk, catisma = {}, []
    for ws in wb.worksheets:
        lejantta = False
        for satir in ws.iter_rows(min_row=2, values_only=True):
            if not satir or satir[0] is None:
                continue
            if clean(satir[0]) == MARMARA_LEJANT_BASI:
                lejantta = True
                continue
            if not lejantta:
                continue
            kod, ad = clean(satir[0]), clean(satir[1]) if len(satir) > 1 else ""
            if kod and ad:
                if kod in sozluk and sozluk[kod] != ad:
                    catisma.append((ws.title, kod, sozluk[kod], ad))
                sozluk[kod] = ad
    if catisma:
        print(f"  marmara: dil sözlüğü sayfalar arasında ÇELİŞİYOR: {catisma[:3]}",
              file=sys.stderr)
    return sozluk


def parse_marmara(wb):
    """KA131 list: one sheet per faculty, 27 sheets, plus a language legend.

    Columns: A code, B university, C start, D end, E department,
    F study quota, G traineeship quota, H staff teaching, I staff training,
    J language (numeric), K note, L agreement type.

    TWO THINGS THIS SOURCE DOES NOT HAVE, and both are left empty rather
    than guessed:

      · No ISCED code anywhere · not in a column, not in front of the
        department name. So the field filter does not cover these records and
        the site shows them under "no field information". Inferring a code
        from the department name would be a guess presented as data.
      · No country column · the country comes only from the Erasmus code
        prefix. For MAKU the prefix is a cross-check against a column; here it
        is the single source, so a row whose prefix is unreadable is dropped
        rather than shown with a blank country.
    """
    diller = marmara_dil_sozlugu(wb)
    agreements = []
    atlanan = 0
    for ws in wb.worksheets:
        fakulte = ws.title.strip()
        for satir in ws.iter_rows(min_row=2, values_only=True):
            if not satir or satir[0] is None:
                continue
            if clean(satir[0]) == MARMARA_LEJANT_BASI:
                break  # the rest of this sheet is the legend, not agreements
            kod = clean(satir[0])
            university = clean(satir[1])
            if not university or not re.search(r"[A-Za-zĞÜŞİÖÇğüşıöç]", university):
                continue
            country = ulke_onekten(kod)
            if not country:
                atlanan += 1
                continue
            bas, bit = satir[2], satir[3]
            yil = [str(d.year) for d in (bas, bit) if hasattr(d, "year")]
            gecerlilik = "/".join(yil) if len(yil) == 2 else ""

            not_temiz, eposta_vardi = eposta_ayikla(clean(satir[10]))
            dil_ham = clean(satir[9])
            kodlar = [k.strip() for k in re.split(r"[;,]", dil_ham)]
            adlar = [diller[k] for k in kodlar if k in diller]
            rec = {
                "country": tr_upper(country),
                "erasmusCode": kod,
                "validity": {"raw": gecerlilik} if gecerlilik else None,
                "university": university,
                "iscedCode": "",
                "department": clean(satir[4]),
                "levels": marmara_seviyeler(satir[5]),
                "quotaStudy": clean(satir[5]),
                "quotaInternship": clean(satir[6]),
                "quotaStaffTeach": clean(satir[7]),
                "quotaStaffTrain": clean(satir[8]),
                "quotaNote": not_temiz,
                "language": {"raw": ", ".join(adlar)} if adlar else None,
                **({"sourceDiff": {"quotaNote": {"kaynakta": None,
                                                 "sebep": "eposta-ayiklandi"}}}
                   if eposta_vardi else {}),
            }
            rec.update(fam_fields(rec["iscedCode"]))
            # The faculty is not a field of the record (no other source has one)
            # but it is real information the student searches by, so it goes
            # into the search text.
            rec["search"] = make_search(rec, extra=fakulte)
            agreements.append(rec)
    if atlanan:
        print(f"  marmara: Erasmus kodundan ülkesi okunamayan {atlanan} satır atlandı",
              file=sys.stderr)
    return agreements
