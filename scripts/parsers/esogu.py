"""ESOGÜ (Eskişehir Osmangazi Üniversitesi) ikili anlaşma ayrıştırıcısı."""
import re
import sys

from .common import (
    _bosluk_sadelestir,
    clean,
    fam_fields,
    make_search,
    tr_upper,
    ulke_onekten,
)

# Levels arrive as four separate numeric columns instead of one cell. A zero
# means the level is not open; the site needs the number, so it is kept as a
# string rather than flattened to a boolean.
ESOGU_SEVIYE = [(6, "onlisans", "ÖL"), (7, "lisans", "L"),
                (8, "yukseklisans", "YL"), (9, "doktora", "D")]


def parse_esogu(ws):
    """Single sheet, one row per agreement, faculty cells merged per block.

    Columns: A faculty, B department, C code, D university, E country,
    F website, G-J quotas per level, K staff teaching, L staff training.

    The faculty cell is filled only on the first row of each block (16 of 259
    rows), so it is carried forward. The same is true of the department cell.
    Blank rows separate the blocks and are skipped.

    Unlike Marmara this source HAS a country column, so the same cross-check
    as MAKU applies: the Erasmus prefix wins and the correction is recorded.
    """
    agreements = []
    fakulte = bolum = ""
    duzeltme, tamamlama, fakulteden = [], [], 0
    for satir in ws.iter_rows(min_row=2, values_only=True):
        if satir and clean(satir[0]):
            yeni = _bosluk_sadelestir(clean(satir[0]))
            if yeni != fakulte:
                # The carried-over department is dropped at a faculty boundary.
                # Without this, a block whose first row has no department would
                # SILENTLY inherit the last department of the previous faculty
                # and put an agreement under the wrong programme. It has not
                # happened in this file, but nothing in the sheet prevents it.
                bolum = ""
            fakulte = yeni
        if satir and len(satir) > 1 and clean(satir[1]):
            bolum = _bosluk_sadelestir(clean(satir[1]))
        kod = clean(satir[2]) if satir and len(satir) > 2 else ""
        if not kod:
            continue
        university = clean(satir[3])
        if not university or not re.search(r"[A-Za-zĞÜŞİÖÇğüşıöç]", university):
            continue

        country = clean(satir[4])
        onekten = ulke_onekten(kod)
        iz = {}
        if onekten and country and tr_upper(onekten) != tr_upper(country):
            duzeltme.append((university[:44], country, onekten))
            iz["country"] = {"kaynakta": country, "sebep": "erasmus-kodu"}
            country = onekten
        elif not country:
            if not onekten:
                continue
            tamamlama.append((university[:44], onekten))
            iz["country"] = {"kaynakta": None, "sebep": "erasmus-kodu"}
            country = onekten

        seviyeler, kontenjan = {}, []
        for sutun, anahtar, etiket in ESOGU_SEVIYE:
            ham = clean(satir[sutun]) if len(satir) > sutun else ""
            if ham.isdigit() and int(ham) > 0:
                seviyeler[anahtar] = ham
                kontenjan.append(f"{ham}{etiket}")

        # An agreement with no department belongs to the faculty as a whole.
        # Showing the faculty name is the honest reading, but the student must
        # be able to tell it apart from a real department name, so it leaves a
        # trace like every other departure from the source.
        if not bolum and fakulte:
            iz["department"] = {"kaynakta": None, "sebep": "fakulte-adi"}
            fakulteden += 1

        site = clean(satir[5]) if len(satir) > 5 else ""
        rec = {
            "country": tr_upper(country),
            "erasmusCode": kod,
            "validity": None,
            "university": university,
            "iscedCode": "",
            "department": bolum or fakulte,
            "levels": seviyeler,
            # Four columns rendered as one string. This is FORMATTING, not a
            # departure: every number below comes from the sheet unchanged and
            # the notation is the one Marmara's own source uses, so the two
            # universities read alike on the card.
            "quotaStudy": ", ".join(kontenjan),
            "quotaInternship": "",
            "quotaStaffTeach": clean(satir[10]) if len(satir) > 10 else "",
            "quotaStaffTrain": clean(satir[11]) if len(satir) > 11 else "",
            "quotaNote": "",
            "language": None,
            **({"website": site} if site.startswith("http") else {}),
            **({"sourceDiff": iz} if iz else {}),
        }
        rec.update(fam_fields(rec["iscedCode"]))
        rec["search"] = make_search(rec, extra=fakulte)
        agreements.append(rec)
    for ad, yazan, dogru in duzeltme:
        print(f"  esogu: ülke düzeltildi · {ad}: {yazan} -> {dogru} "
              f"(Erasmus kodunun ön eki esas alındı)", file=sys.stderr)
    for ad, dogru in tamamlama:
        print(f"  esogu: ülke boştu, ön ekten dolduruldu · {ad}: {dogru}", file=sys.stderr)
    if fakulteden:
        print(f"  esogu: bölümü yazılmayan {fakulteden} kayıtta fakülte adı gösteriliyor",
              file=sys.stderr)
    return agreements
