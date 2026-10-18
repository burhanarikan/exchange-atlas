"""Kırıkkale Üniversitesi ikili anlaşma ayrıştırıcısı."""
import re

from .common import (
    ERASMUS_ULKE,
    _bosluk_sadelestir,
    clean,
    fam_fields,
    make_search,
    tr_upper,
    ulke_onekten,
)

KKU_HEADERS = {
    2: "Program",
    3: "Akademik Birim",
    4: "Bölüm",
    5: "Üniversite",
    6: "Erasmus Kodu",
    9: "Ülke",
    10: "Şehir",
    11: "Önlisans",
    12: "Süre Ay",
    13: "Lisans",
    14: "Süre Ay",
    15: "Y.Lis",
    16: "Süre Ay",
    17: "Dokt.",
    18: "Süre Ay",
    19: "SAYI",
    20: "SÜRE",
    21: "SAAT",
}

KKU_SEVIYE = [
    (11, "onlisans", "ÖL"),
    (13, "lisans", "L"),
    (15, "yukseklisans", "YL"),
    (17, "doktora", "D"),
]


def parse_kku(ws):
    """Tek sayfa (`KA131_web`), 2 başlık satırı ve satır 3'ten itibaren anlaşmalar.

    Sütunlar: C akademik birim, D bölüm, E üniversite, F Erasmus kodu, I ülke,
    J şehir, K-R kademe bazlı öğrenim kontenjanı ve süreleri, S-U personel ders
    verme (STA) kontenjanı. Kaynakta ISCED alan kodu, geçerlilik aralığı ve dil
    şartı sütunu bulunmuyor; olmayan alanlar tahmin edilmez.
    """
    for col, title in KKU_HEADERS.items():
        if clean(ws.cell(2, col).value) != title:
            raise ValueError(f"Kırıkkale: {col}. sütun başlığı değişti: {title}")

    agreements = []
    for row in range(3, ws.max_row + 1):
        fakulte = _bosluk_sadelestir(clean(ws.cell(row, 3).value))
        bolum = _bosluk_sadelestir(clean(ws.cell(row, 4).value))
        university = _bosluk_sadelestir(clean(ws.cell(row, 5).value))
        kod = _bosluk_sadelestir(clean(ws.cell(row, 6).value))
        if not university or not kod or not re.search(r"[A-Za-zĞÜŞİÖÇğüşıöç]", university):
            continue

        country = clean(ws.cell(row, 9).value)
        onekten = ulke_onekten(kod)
        iz = {}
        if onekten and country and tr_upper(onekten) != tr_upper(country):
            iz["country"] = {"kaynakta": country, "sebep": "erasmus-kodu"}
            country = onekten
        elif not country:
            if not onekten:
                continue
            iz["country"] = {"kaynakta": None, "sebep": "erasmus-kodu"}
            country = onekten
        if country not in ERASMUS_ULKE.values():
            raise ValueError(f"Kırıkkale: {row}. satırın ülkesi okunamadı: {kod}")

        if not bolum and fakulte:
            iz["department"] = {"kaynakta": None, "sebep": "fakulte-adi"}

        seviyeler, kontenjan = {}, []
        for sutun, anahtar, etiket in KKU_SEVIYE:
            ham = clean(ws.cell(row, sutun).value)
            if ham.isdigit() and int(ham) > 0:
                seviyeler[anahtar] = ham
                kontenjan.append(f"{ham}{etiket}")

        sta_sayi = clean(ws.cell(row, 19).value)
        quota_teach = sta_sayi if sta_sayi.isdigit() and int(sta_sayi) > 0 else ""
        sehir = _bosluk_sadelestir(clean(ws.cell(row, 10).value))
        department = bolum or fakulte

        rec = {
            "country": tr_upper(country),
            "erasmusCode": kod,
            "validity": None,
            "university": university,
            "iscedCode": "",
            "department": department,
            "levels": seviyeler,
            "quotaStudy": ", ".join(kontenjan),
            "quotaInternship": "",
            "quotaStaffTeach": quota_teach,
            "quotaStaffTrain": "",
            "quotaNote": "",
            "language": None,
            **({"sourceField": fakulte} if fakulte and department != fakulte else {}),
            **({"sourceDiff": iz} if iz else {}),
        }
        rec.update(fam_fields(rec["iscedCode"]))
        rec["search"] = make_search(rec, extra=f"{fakulte} {sehir}".strip())
        agreements.append(rec)
    return agreements
