"""MAKÜ (Burdur Mehmet Akif Ersoy Üniversitesi) ikili anlaşma ayrıştırıcısı."""
import re
import sys

from .common import (
    _bosluk_sadelestir,
    aile_tahminle_bulundu,
    clean,
    eposta_ayikla,
    fam_fields,
    isced_kodu,
    make_search,
    parse_validity,
    tr_upper,
    ulke_onekten,
)

# Columns are located by NAME, not by index. The reason was learned by
# measurement: when a column is inserted into the source sheet, index-based code
# does not crash, it **produces meaningless data** -- it finds a department name
# in the country column and upper-cases it.
#
# This debt was paid twice. The ISCED code was read from the wrong column (243
# records ended up with no field) and so was the country (4 records appeared in
# the wrong country, 2 did not appear at all). In both cases reading by index
# made the question "what is in which column" hard to even ask.
MAKU_BASLIKLAR = {
    "universite":   "İkili Anlaşma Yapılan Yüksek Öğretim Kurumu",
    "gecerlilik":   "Geçerlilik Süresi",
    "erasmus_kodu": "Üniversite ID Kodu",
    "aciklama":     "Açıklama",
    "isced_kodu":   "Ders Alan Kodu",
    "dil":          "Eğitim Dili",
    "ulke":         "Ülke",
    "kont_ogrenim": "Öğrenim Hareketliliği Kontenjanı",
    "kont_ders":    "Ders Verme Kontenjanı",
    "kont_staj":    "Staj Hareketliliği Kontenjanı",
    "kont_egitim":  "Eğitim Alma Kontenjanı",
}

# The EQF header is long and carries an explanation inside it
# ("... EQF 5: ... EQF 6: ..."), so exact matching would be brittle; a prefix
# match is enough.
MAKU_BASLIK_ONEK = {"eqf": "Öğrenim Kademesi"}


def maku_sutunlari(ws):
    """Başlık satırından ada göre sütun numaralarını bulur.

    İki sütun **birebir aynı başlığı** taşıyor: F ve H, ikisi de "İkili Anlaşma
    Yapılan Bölüm Ders Alan Kodu (ISCED)". Bu, borcun neden uzun süre
    ödenmediğinin de sebebi; ad tek başına yetmiyor.

    İkisi içerikleriyle ayrılıyor: F resmî İngilizce ISCED etiketini taşıyor
    (Türkçe harf oranı %1), H ise bölümün Türkçe adını (%72). Oran ölçüldü ve
    aradaki fark tesadüfe yer bırakmayacak kadar büyük.
    """
    baslik = {}
    ikili_isced = []
    for c in range(1, ws.max_column + 1):
        ad = _bosluk_sadelestir(ws.cell(1, c).value)
        if not ad:
            continue
        if "Bölüm Ders Alan Kodu" in ad:
            ikili_isced.append(c)
        else:
            baslik.setdefault(ad, c)

    sutun = {}
    for anahtar, ad in MAKU_BASLIKLAR.items():
        if ad not in baslik:
            raise SystemExit(f"maku: '{ad}' başlıklı sütun bulunamadı. Kaynak "
                             f"tablonun başlıkları değişmiş olabilir; "
                             f"scripts/build_data.py içindeki MAKU_BASLIKLAR "
                             f"gözden geçirilmeli.")
        sutun[anahtar] = baslik[ad]
    for anahtar, onek in MAKU_BASLIK_ONEK.items():
        eslesen = [c for a, c in baslik.items() if a.startswith(onek)]
        if not eslesen:
            raise SystemExit(f"maku: '{onek}...' ile başlayan sütun yok.")
        sutun[anahtar] = eslesen[0]

    if len(ikili_isced) != 2:
        raise SystemExit(f"maku: ISCED başlıklı sütun sayısı {len(ikili_isced)}, "
                         f"beklenen 2. Tablo düzeni değişmiş.")

    # Which one is the Turkish department name? Decided by the ratio of
    # Turkish-specific letters.
    TR_HARF = set("çğıöşüÇĞİÖŞÜ")
    oran = []
    for c in ikili_isced:
        trli = toplam = 0
        for r in range(2, ws.max_row + 1):
            ad = re.sub(r"^\s*\d{3,4}[\s.\-]*", "", clean(ws.cell(r, c).value))
            if not ad:
                continue
            toplam += 1
            if TR_HARF & set(ad):
                trli += 1
        oran.append(trli / toplam if toplam else 0)
    if abs(oran[0] - oran[1]) < 0.2:
        raise SystemExit(f"maku: İki ISCED sütunu içerikle ayrılamadı "
                         f"(Türkçe harf oranları {oran[0]:.2f} ve {oran[1]:.2f}). "
                         f"Ayrım belirsiz; elle bakılmalı.")
    tr_index = 0 if oran[0] > oran[1] else 1
    sutun["bolum_tr"] = ikili_isced[tr_index]
    sutun["isced_etiket_en"] = ikili_isced[1 - tr_index]
    return sutun


def parse_maku(ws):
    """KA131 'Güncel Anlaşmalar': 19 sütun, satır 2'den itibaren.

    Sütunlar: C üni, D geçerlilik, E kod, F ISCED etiketi (EN), G açıklama,
    H bölüm adı (TR), I ISCED kodu, J eğitim dili, K EQF seviyeleri, L ülke,
    M öğrenim, N ders verme, O staj, P eğitim alma.

    Q ve R sütunları
    (imzalayan kişi ve e-postası) BİLEREK okunmuyor · bkz. `KAYNAK.md §5`.

    F ile H'nin başında da ISCED kodu duruyor ve I çoğu satırda boş; kod
    üçünden birlikte okunuyor (bkz. isced_kodu)."""
    S = maku_sutunlari(ws)
    agreements = []
    skipped = 0
    struck_out = 0
    ulke_duzeltme, ulke_tamamlama = [], []
    for r in range(2, ws.max_row + 1):
        def col(ad):
            return ws.cell(row=r, column=S[ad]).value
        university = clean(col("universite"))
        # A name with no letters is a data error (the source has a cell holding '0')
        if not university or not re.search(r"[A-Za-zĞÜŞİÖÇğüşıöç]", university):
            continue

        # A struck-through row is an agreement deleted at the source. The row was
        # never removed from the sheet, only marked by formatting, so a reader
        # looking at cell values cannot see it. This reached production once: an
        # agreement no longer valid sat in the list and a student could apply.
        if any((ws.cell(row=r, column=c).font or {}) and ws.cell(row=r, column=c).font.strike
               for c in (S["isced_etiket_en"], S["bolum_tr"])):
            struck_out += 1
            continue

        # Country can be read from two places: the country column and the prefix
        # of the Erasmus code. The prefix follows a fixed convention while the
        # column is typed by hand, so when they disagree the prefix wins and the
        # correction is recorded.
        country = clean(col("ulke"))
        onekten = ulke_onekten(clean(col("erasmus_kodu")))
        # Every departure from the source is recorded; the student sees it on the card
        iz = {}
        if onekten and country and tr_upper(onekten) != tr_upper(country):
            ulke_duzeltme.append((clean(col("universite"))[:44], country, onekten))
            iz["country"] = {"kaynakta": country, "sebep": "erasmus-kodu"}
            country = onekten
        elif not country:
            if not onekten:
                skipped += 1
                continue
            ulke_tamamlama.append((clean(col("universite"))[:44], onekten))
            iz["country"] = {"kaynakta": None, "sebep": "erasmus-kodu"}
            country = onekten
        country = tr_upper(country)

        # EQF -> level flags (look at digits only, to survive typos like 'QQF 6')
        #
        # Cancelled levels are stripped first: the source has a cell reading
        # "EQF 6 / EQF 7 (EQF 7 CANCELLED)". A plain digit scan would also find 7
        # and make the master's level look open. Any level marked cancelled inside
        # parentheses is dropped.
        eqf_raw = clean(col("eqf"))
        cancelled = set()
        for chunk in re.findall(r"\(([^)]*)\)", eqf_raw):
            # The source sheet is in Turkish; the searched words are its own text.
            if re.search(r"iptal|geçersiz|kaldır", chunk, re.I):
                cancelled.update(re.findall(r"[5678]", chunk))
        eqf = set(re.findall(r"[5678]", re.sub(r"\([^)]*\)", "", eqf_raw))) - cancelled
        if cancelled:
            iz["levels"] = {"kaynakta": eqf_raw, "sebep": "iptal-notu"}
        levels = {}
        for d, key in (("5", "onlisans"), ("6", "lisans"),
                       ("7", "yukseklisans"), ("8", "doktora")):
            if d in eqf:
                levels[key] = True

        # Strip the ISCED code prefix from names ("0610-Computer Eng." ->
        # "Computer Eng."); the code is read separately and shown as a chip.
        #
        # The two columns do not carry the same thing: the Turkish column holds
        # the real department name, while the English column holds the official
        # ISCED
        # etiketi ("Training for pre-school teachers", "Veterinary", "Education").
        # Measured: across 468 filled cells there are only 117 distinct values and
        # the most frequent ones are ISCED labels. Hence the name is not "dept_en".
        dept_tr = re.sub(r"^\s*\d{3,4}\s*-\s*", "", clean(col("bolum_tr")).strip())
        isced_label_en = re.sub(r"^\s*\d{3,4}\s*-\s*", "", clean(col("isced_etiket_en")).strip())
        lang_raw = re.sub(r"\s*\n\s*", " ", clean(col("dil"))).strip()
        not_temiz, eposta_vardi = eposta_ayikla(clean(col("aciklama")))
        if eposta_vardi:
            iz["quotaNote"] = {"kaynakta": None, "sebep": "eposta-ayiklandi"}

        # When the Turkish department name is empty we fall back to the English
        # ISCED label. This fallback used to be SILENT: what looked like a
        # department name on the card was actually a field label, and the reader
        # could not tell. It now leaves a trace.
        if not dept_tr and isced_label_en:
            iz["department"] = {"kaynakta": None, "sebep": "isced-etiketi"}

        # Only FILLED fields are written. A missing field means "no data"; writing
        # a fixed empty value would add useless bytes to every record. The site
        # already reads a missing field correctly (a.website && ...).
        rec = {
            "country": country,
            "erasmusCode": clean(col("erasmus_kodu")),
            "validity": parse_validity(col("gecerlilik")),
            "university": university,
            "iscedCode": isced_kodu(col("bolum_tr"), col("isced_etiket_en"), col("isced_kodu")),
            "department": dept_tr or isced_label_en,
            "levels": levels,
            "quotaStudy": clean(col("kont_ogrenim")),
            "quotaInternship": clean(col("kont_staj")),
            "quotaStaffTeach": clean(col("kont_ders")),
            "quotaStaffTrain": clean(col("kont_egitim")),
            "quotaNote": not_temiz,
            # The 'language of instruction' column: not a requirement, shown raw
            "language": {"raw": lang_raw} if lang_raw else None,
            # Fields where we departed from the source. When empty the field is
            # omitted entirely: 461 of 468 records have no departure, so it should
            # not take up space.
            **({"sourceDiff": iz} if iz else {}),
        }
        rec.update(fam_fields(rec["iscedCode"]))
        # If the family was inferred, leave a trace: the student should know that
        # the field it appears under rests on an assumption.
        if rec["iscedFamily"] and aile_tahminle_bulundu(rec["iscedCode"]):
            rec.setdefault("sourceDiff", {})["iscedFamily"] = {
                "kaynakta": rec["iscedCode"], "sebep": "eksik-sifir",
            }
        rec["search"] = make_search(rec, extra=isced_label_en)
        agreements.append(rec)
    # Country corrections are recorded: fixing them silently would hide an error
    # that ought to be reported back to the source.
    for ad, yazan, dogru in ulke_duzeltme:
        print(f"  maku: ülke düzeltildi · {ad}: {yazan} -> {dogru} "
              f"(Erasmus kodunun ön eki esas alındı)", file=sys.stderr)
    for ad, dogru in ulke_tamamlama:
        print(f"  maku: ülke boştu, ön ekten dolduruldu · {ad}: {dogru}",
              file=sys.stderr)
    if skipped:
        print(f"  maku: ülkesi hiçbir yerden okunamayan {skipped} satır atlandı",
              file=sys.stderr)
    if struck_out:
        print(f"  maku: üstü çizili {struck_out} satır atlandı (kaynakta silinmiş)",
              file=sys.stderr)
    return agreements
