"""Bilecik Şeyh Edebali Üniversitesi ikili anlaşma ayrıştırıcısı."""
import re

from .common import (
    ERASMUS_ULKE,
    ISCED_FAMILY,
    aile_tahminle_bulundu,
    clean,
    fam_fields,
    make_search,
    parse_validity,
    tr_upper,
    ulke_onekten,
)

BILECIK_HEADERS = {
    2: "SÜRE", 6: "Üniversite Adı", 7: "Ülke/Şehir", 8: "Erasmus Kodu",
    9: "ISCED(Uluslar arası alan kodu ve isimleri)", 10: "Fakülte", 11: "Bölüm/Program",
    12: "Lisansüstü Eğitim Enstitüsü", 13: "Meslek Yüksekokulu",
    14: "(Lisans) Öğrenim Oğrenci sayısı*ay(Ön lisans,YL ve Dr dahil, kontenjanları var ise)",
    15: "(Lisans) Staj Oğrenci sayısı*ay(Ön lisans,YL ve Dr dahil, kontenjanları var ise)",
    16: "Ders verme Personel sayısı*gün", 17: "Eğitim Alma Personel sayısı*gün", 19: "websitesi",
}


def parse_bilecik(ws):
    """Birleştirilmiş hücreleri kendi sınırları içinde açar; boşluğu tahmin etmez.

    Kontenjanlar kişi*ay ve kişi*gün biçiminde korunur. Bir kontenjan hücresi
    birden çok satırı kapsıyorsa bunlar ayrı kontenjanlar gibi toplanamaz.
    Birden fazla ISCED ailesi taşıyan hücre tek bir aileye zorlanmaz.
    """
    for col, title in BILECIK_HEADERS.items():
        if clean(ws.cell(2, col).value) != title:
            raise ValueError(f"Bilecik: {col}. sütun başlığı değişti: {title}")
    merged = {}
    for area in ws.merged_cells.ranges:
        for row in range(area.min_row, area.max_row + 1):
            for col in range(area.min_col, min(area.max_col, 19) + 1):
                merged[row, col] = (area.min_row, area.min_col, area.max_row)

    def value(row, col):
        start = merged.get((row, col), (row, col, row))
        return clean(ws.cell(start[0], start[1]).value)

    agreements = []
    for row in range(3, ws.max_row + 1):
        # Fully merged blank rows are visual spacing, not additional records.
        if not any(clean(ws.cell(row, col).value) for col in (6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17)):
            continue
        university, code = value(row, 6), value(row, 8)
        if not university or not code:
            continue
        department, faculty, field = value(row, 11), value(row, 10), value(row, 9)
        trace = {}
        raw_country = value(row, 7).split("/")[0].strip()
        aliases = {"Latvia": "Letonya", "luxembourg": "Lüksemburg", "Çek Cumhuriyeti": "Çekya"}
        country = aliases.get(raw_country, raw_country)
        from_code = ulke_onekten(code)
        if from_code and country != from_code:
            trace["country"] = {"kaynakta": raw_country, "sebep": "erasmus-kodu"}
            country = from_code
        if country not in ERASMUS_ULKE.values():
            raise ValueError(f"Bilecik: {row}. satırın ülkesi okunamadı: {code}")
        if not department:
            department = faculty or field
            trace["department"] = {"kaynakta": None, "sebep": "fakulte-adi" if faculty else "isced-etiketi"}
        codes = re.findall(r"\b\d{3,4}\b", field)
        families = {c[:2] if c[:2] in ISCED_FAMILY else None for c in codes}
        field_code = codes[0] if len(families) == 1 and None not in families else ""
        quota, masters, associate = value(row, 14), value(row, 12), value(row, 13)
        levels = {}
        study_shared = merged.get((row, 14), (row, 14, row))[2] > merged.get((row, 14), (row, 14, row))[0]
        # Only explicit source columns establish levels; no counts are invented.
        if re.match(r"^[1-9]\d*", quota):
            levels["lisans"] = "shared" if study_shared or masters not in ("", "0") or associate not in ("", "0") else re.match(r"\d+", quota).group()
        if masters and masters != "0":
            levels["yukseklisans"] = "shared"
            if "DR" in masters.upper():
                levels["doktora"] = "shared"
        if associate and associate != "0":
            levels["onlisans"] = "shared"
        shared = any(merged.get((row, col), (row, col, row))[2] >
                     merged.get((row, col), (row, col, row))[0] for col in range(14, 18))
        # Keep the complete field label, including additional codes, searchable.
        rec = {
            "country": tr_upper(country), "erasmusCode": code,
            "university": university, "department": department,
            "validity": parse_validity(value(row, 2)), "iscedCode": field_code,
            "levels": levels, "quotaStudy": quota, "quotaInternship": value(row, 15),
            "quotaStaffTeach": value(row, 16), "quotaStaffTrain": value(row, 17),
            "quotaNote": "", "language": None,
            "quotaFormat": "person-duration", "quotaGraduate": masters, "quotaAssociate": associate,
            "sourceRow": row, "sharedQuota": shared,
            "sourceField": field,
            **({"sourceDiff": trace} if trace else {}),
        }
        website = value(row, 19)
        if website.startswith(("https://", "http://")):
            rec["website"] = website
        rec.update(fam_fields(field_code))
        if rec["iscedFamily"] and aile_tahminle_bulundu(field_code):
            rec.setdefault("sourceDiff", {})["iscedFamily"] = {"kaynakta": field_code, "sebep": "eksik-sifir"}
        rec["search"] = make_search(rec, extra=faculty + " " + field)
        agreements.append(rec)
    return agreements
