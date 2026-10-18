#!/usr/bin/env python3
"""
İkili anlaşma listeleri -> site/data-<uni>.json + site/universities.json

Çok üniversiteli: her üniversitenin kendi Excel formatı için ayrı parser var,
hepsi aynı kayıt şemasına normalize edilir. Yeni üniversite =
config/universities.json içinde kayıt + scripts/parsers/ altında ayrıştırıcı.

  Yerel snapshot'lardan (varsayılan, demo için güvenli):
      python3 scripts/build_data.py
  Canlı kaynaklardan çek:
      python3 scripts/build_data.py --pull
"""
import argparse
import hashlib
import io
import json
import re
import sys
import urllib.request
from collections import Counter
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit
from zipfile import BadZipFile, ZipFile, is_zipfile

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.parsers import (  # noqa: E402,F401
    BILECIK_HEADERS,
    EPOSTA,
    ERASMUS_ULKE,
    ESOGU_SEVIYE,
    FOLD_EXCEPTIONS,
    ISCED_FAMILY,
    KKU_HEADERS,
    KKU_SEVIYE,
    MAKU_BASLIK_ONEK,
    MAKU_BASLIKLAR,
    MARMARA_LEJANT_BASI,
    MARMARA_PARCA,
    MARMARA_SEVIYE,
    PARSERS,
    _bosluk_sadelestir,
    aile_tahminle_bulundu,
    clean,
    eposta_ayikla,
    fam_fields,
    fold,
    isced_family,
    isced_kodu,
    make_search,
    maku_sutunlari,
    marmara_dil_sozlugu,
    marmara_kontenjan_bol,
    marmara_seviyeler,
    parse_bilecik,
    parse_esogu,
    parse_kku,
    parse_maku,
    parse_marmara,
    parse_validity,
    tr_upper,
    ulke_onekten,
    unify_department_spelling,
)


# ═══════════════════════════ University registry ════════════════════

def load_registry():
    """Kurum eklerken kimlik ve kaynak bilgisi tek dosyada tutulur."""
    entries = json.loads((ROOT / "config" / "universities.json").read_text(encoding="utf-8"))
    parsers = {p.__name__: p for p in (parse_maku, parse_marmara, parse_esogu, parse_bilecik, parse_kku)}
    seen = set()
    for entry in entries:
        uid = entry["id"]
        if not re.fullmatch(r"[a-z][a-z0-9-]*", uid) or uid in seen:
            raise ValueError(f"Geçersiz ya da yinelenen kurum kimliği: {uid}")
        seen.add(uid)
        local = (ROOT / entry["local"]).resolve()
        if not local.is_relative_to(ROOT / "lokal"):
            raise ValueError(f"{uid}: kaynak dosya lokal/ altında olmalı")
        entry["local"] = local
        entry["parser"] = parsers[entry["parser"]]
    return entries


UNIVERSITIES = load_registry()
MAX_SOURCE_BYTES = 20 * 1024 * 1024


class SourceLinks(HTMLParser):
    def __init__(self, base):
        super().__init__()
        self.base, self.links = base, set()

    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get("href", "")
        if tag == "a" and urlsplit(href).path.lower().endswith(".xlsx"):
            self.links.add(urljoin(self.base, href))


def fetch_bytes(url):
    """İndirmeyi boyut ve süreyle sınırlar; başarısız isteği gizlemez."""
    if urlsplit(url).scheme not in ("https", "http"):
        raise ValueError("Kaynak adresi HTTP(S) olmalı")
    url = quote(url, safe=":/?&=%()+,;@")
    req = urllib.request.Request(url, headers={"User-Agent": "ExchangeAtlas-source-check/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read(MAX_SOURCE_BYTES + 1)
        final_url = response.url
    if len(data) > MAX_SOURCE_BYTES:
        raise ValueError("Kaynak dosya 20 MB sınırını aşıyor")
    return data, final_url


def download_source(uni):
    """Resmî sayfadaki tek Excel'i veya paylaşım arşivindeki tek Excel'i alır.

    Birden fazla aday varsa ilkini seçmez. Kaynak biçimi değiştiğinde işlem
    durur; bakımcı hangi listenin kullanılacağına karar verir.
    """
    mode = uni["downloadMode"]
    if mode == "page-xlsx":
        page, page_url = fetch_bytes(uni["listUrl"])
        links = SourceLinks(page_url)
        links.feed(page.decode("utf-8-sig"))
        candidates = {quote(url, safe=":/?&=%()+,;@") for url in links.links}
        if uni.get("fileContains"):
            candidates = {url for url in candidates if uni["fileContains"] in url}
        if len(candidates) != 1:
            raise ValueError(f"{uni['id']}: resmî sayfada {len(candidates)} Excel bulundu; kaynak seçimi gerekli")
        url = candidates.pop()
    elif mode in ("share-zip", "direct"):
        url = uni["pullUrl"]
    else:
        raise ValueError(f"Bilinmeyen indirme yöntemi: {mode}")
    data, url = fetch_bytes(url)
    member = None
    if mode == "share-zip":
        with ZipFile(io.BytesIO(data)) as archive:
            candidates = [info for info in archive.infolist()
                          if not info.is_dir() and info.filename.lower().endswith(".xlsx")
                          and not Path(info.filename).name.startswith("~$")]
            if len(candidates) != 1:
                raise ValueError(f"{uni['id']}: paylaşımda {len(candidates)} Excel bulundu")
            info = candidates[0]
            if info.file_size > MAX_SOURCE_BYTES:
                raise ValueError("Arşivdeki Excel 20 MB sınırını aşıyor")
            member = info.filename
            data = archive.read(info)
    if not is_zipfile(io.BytesIO(data)):
        raise ValueError(f"{uni['id']}: yanıt bir Excel dosyası değil")
    return data, url, member


def parse_source(uni, data):
    """Kaynak açılmadan ya da ayrıştırma bitmeden hiçbir çıktı değiştirilmez."""
    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    try:
        sheet = uni["sheet"]
        ws = wb if sheet is None else wb[sheet] if isinstance(sheet, str) else wb.worksheets[sheet]
        # Guard every positional column before interpreting a refreshed file.
        if uni["parser"] is parse_marmara:
            expected = ["ERASMUS ID", "ÜNİVERSİTE ADI", "BAŞLANGIÇ", "BİTİŞ", "BÖLÜM", "ÖĞRENİM KONTENJAN", "STAJ KONTENJAN", "DERS VERME", "EĞİTİM ALMA", "YABANCI DİL", "AÇIKLAMA", "ANLAŞMA TÜRÜ"]
            for tab in wb.worksheets:
                if [clean(tab.cell(1, c).value) for c in range(1, 13)] != expected:
                    raise ValueError(f"{uni['id']}: {tab.title} sütun başlıkları değişti")
        elif uni["parser"] is parse_esogu:
            expected = {1: "FAKÜLTE", 2: "BÖLÜM", 3: "ERASMUS ID", 4: "ÜNİVERSİTE", 5: "ÜLKE", 7: "ÖN LİSANS", 8: "LİSANS", 9: "YÜKSEK LİSANS", 10: "DOKTORA", 11: "DERS VERME", 12: "EĞİTİM ALMA"}
            if any(clean(ws.cell(1, c).value) != label for c, label in expected.items()):
                raise ValueError(f"{uni['id']}: sütun başlıkları değişti")
        agreements = uni["parser"](ws)
    finally:
        wb.close()
    unify_department_spelling(agreements)
    validate_agreements(uni["id"], agreements)
    return agreements


def validate_agreements(uid, agreements):
    """Boş ya da şeması bozuk yeni bir kaynağın mevcut listeyi silmesini önler."""
    required = {"country", "erasmusCode", "university", "department", "search", "levels",
                "iscedCode", "iscedFamily", "iscedFamilyTr", "iscedFamilyEn", "validity",
                "quotaStudy", "quotaInternship", "quotaStaffTeach", "quotaStaffTrain", "quotaNote", "language"}
    if not agreements:
        raise ValueError(f"{uid}: ayrıştırıcı hiç kayıt üretmedi")
    for index, rec in enumerate(agreements, 1):
        if required - rec.keys() or not all(rec.get(k) for k in ("country", "university", "department")):
            raise ValueError(f"{uid}: {index}. kayıt eksik veya boş alan taşıyor")
        if not isinstance(rec["levels"], dict) or set(rec["levels"]) - {"onlisans", "lisans", "yukseklisans", "doktora"}:
            raise ValueError(f"{uid}: {index}. kayıt geçersiz derece taşıyor")
        if re.search(r"[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}", json.dumps(rec, ensure_ascii=False)):
            raise ValueError(f"{uid}: {index}. kayıt e-posta içeriyor")


def record_delta(previous, current):
    """Tekrarlanan satırları kaybetmeden eklenen ve çıkarılan kayıtları sayar."""
    def bag(records):
        return Counter(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in records)
    old, new = bag(previous), bag(current)
    return {"added": sum((new - old).values()), "removed": sum((old - new).values())}


def build(pull=False, university_ids=None, dry_run=False, report_path=None):
    """Seçili kurumları hazırlar; tümü doğrulandıktan sonra kaynak ve siteyi yazar."""
    selected = set(university_ids or [u["id"] for u in UNIVERSITIES])
    unknown = selected - {u["id"] for u in UNIVERSITIES}
    if unknown:
        raise ValueError(f"Bilinmeyen kurum: {', '.join(sorted(unknown))}")
    catalogue_path = SITE / "kaynak-kunyesi.json"
    catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
    sources = {s["id"]: s for s in catalogue["kaynaklar"]}
    registry_path = SITE / "universities.json"
    registry = {u["id"]: u for u in json.loads(registry_path.read_text(encoding="utf-8"))}
    now = datetime.now().isoformat(timespec="seconds")
    today = date.today().isoformat()
    pending, reports = [], []
    for uni in UNIVERSITIES:
        uid = uni["id"]
        if uid not in selected:
            continue
        old_source = sources.get(uid, {})
        if pull:
            data, url, member = download_source(uni)
        else:
            if not uni["local"].exists():
                raise ValueError(f"{uid}: kaynak dosya yok; --pull --university {uid} kullanın")
            data, url, member = uni["local"].read_bytes(), old_source.get("dosya_adresi"), old_source.get("arsiv_uyesi")
        digest = hashlib.sha256(data).hexdigest()
        if not pull and digest != old_source.get("sha256"):
            raise ValueError(f"{uid}: yerel dosya kayıtlı kaynakla uyuşmuyor; resmî kaynaktan --pull ile doğrulayın")
        agreements = parse_source(uni, data)
        source = dict(old_source)
        source.update({"id": uid, "kurum": uni["nameTr"], "birim": uni["creditTr"].removeprefix("Veri: "),
                       "liste_sayfasi": uni["listUrl"], "dosya_adresi": url,
                       "yerel_ad": str(uni["local"].relative_to(ROOT)),
                       "sha256": digest, "boyut_bayt": len(data), "kayit_sayisi": len(agreements)})
        if pull:
            source["son_kontrol_tarihi"] = today
            if digest != old_source.get("sha256"):
                source["indirme_tarihi"] = today
        if member:
            source["arsiv_uyesi"] = member
        source["adres_notu"] = ("Paylaşım arşivindeki tek Excel otomatik alınır; birden çok Excel varsa işlem durur."
                                 if uni["downloadMode"] == "share-zip" else
                                 "Dosya adresi değişebilir; resmî liste sayfasındaki tek Excel bağlantısı yeniden bulunur."
                                 if uni["downloadMode"] == "page-xlsx" else "Doğrudan adres kurum kaydında tutulur; adres değişirse güncellenir.")
        metadata = {"sourceDownloadedAt": source.get("indirme_tarihi"),
                    "sourceCheckedAt": source.get("son_kontrol_tarihi"), "sourceSha256": digest}
        countries = sorted({a["country"] for a in agreements})
        families = Counter(a["iscedFamily"] for a in agreements if a["iscedFamily"])
        out = {"generatedAt": now, "source": "live" if pull else "local-snapshot", **metadata,
               "count": len(agreements), "countries": countries,
               "iscedFamilies": [{"code": k, "tr": ISCED_FAMILY[k][0], "en": ISCED_FAMILY[k][1], "count": v}
                                 for k, v in sorted(families.items())], "agreements": agreements}
        target = SITE / f"data-{uid}.json"
        previous = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {"agreements": []}
        report = {"id": uid, "previousCount": len(previous["agreements"]), "count": len(agreements),
                  "sourceChanged": digest != old_source.get("sha256"), **record_delta(previous["agreements"], agreements)}
        reports.append(report)
        print(f"{uid}: {report['previousCount']} → {report['count']} kayıt · +{report['added']} / -{report['removed']} · kaynak {'değişti' if report['sourceChanged'] else 'aynı'}")
        registry[uid] = {k: uni[k] for k in ("id", "nameTr", "nameEn", "abbr", "monogram", "creditTr", "creditEn", "hasGuide")}
        if uni.get("countUnit"):
            registry[uid]["countUnit"] = uni["countUnit"]
        registry[uid].update({"sourceUrl": uni["listUrl"], "diffCount": sum(bool(a.get("sourceDiff")) for a in agreements),
                              "count": len(agreements), "countries": len(countries),
                              "universities": len({a["university"] for a in agreements}), "generatedAt": now, **metadata})
        sources[uid] = source
        pending.append((uni["local"], data, target, out))
    if report_path:
        Path(report_path).write_text(json.dumps({"checkedAt": now, "dryRun": dry_run, "universities": reports}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if dry_run:
        print("Önizleme: kaynak dosyaları ve site değiştirilmedi.")
        return reports
    ordered = [registry[u["id"]] for u in UNIVERSITIES if u["id"] in registry]
    catalogue["kaynaklar"] = [sources[u["id"]] for u in UNIVERSITIES if u["id"] in sources]
    SITE.mkdir(parents=True, exist_ok=True)
    for local, data, target, out in pending:
        local.parent.mkdir(parents=True, exist_ok=True)
        if pull:
            local.write_bytes(data)
        target.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    registry_path.write_text(json.dumps(ordered, ensure_ascii=False), encoding="utf-8")
    catalogue_path.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_sitemap(ordered)
    return reports


ALAN_ADI = "https://exchangeatlas.org"


def write_sitemap(registry):
    """Arama motorlarına sayfa listesi · kayıttan üretiliyor.

    Elle yazılsa üniversite eklendiğinde güncellenmesi unutulurdu ve unutulduğu
    gün hiçbir şey kırılmazdı: Site çalışmaya devam eder, yalnız yeni sayfalar
    aranamaz olurdu. Kayıttan üretmek o boşluğu tümüyle kaldırıyor.
    """
    # Adresler UZANTISIZ · ölçüldü, kanonik yayın `.html`'i uzantısıza 308
    # ile yönlendiriyor:
    #
    #   /agreements.html?uni=maku  →  308  →  /agreements?uni=maku
    #
    # Yani sitemap'teki her adres bir yönlendirmeydi ve arama motoruna
    # sayfanın gerçek adresi hiç bildirilmiyordu. Giriş sayfası da öyleydi:
    # `/index.html` → 308 → `/`, üstelik sayfanın kendi `canonical`'ı zaten
    # `/` diyordu · sitemap ile sayfa birbirini yalanlıyordu.
    #
    # Adresler mutlak ve `ALAN_ADI` ile üretiliyor, yani bu liste KANONİK
    # YAYINI tarif ediyor · deponun herhangi bir statik sunucuya kopyalanmış
    # hâlini değil. Uzantısız biçim o yayının gerçek biçimi.
    yollar = ["/"]
    for uni in registry:
        yollar.append(f"/agreements?uni={uni['id']}")
        if uni.get("hasGuide"):
            yollar.append(f"/guide?uni={uni['id']}")

    bugun = datetime.now().date().isoformat()
    # `if y != "/"` KALDIRILDI. Giriş sayfası listeden atılıp yerine
    # `/index.html` konuyordu; o adres de yönlendiriliyordu. Artık giriş
    # sayfası gerçek adresiyle bildiriliyor.
    satirlar = "\n".join(
        f"  <url><loc>{ALAN_ADI}{y.replace('&', '&amp;')}</loc>"
        f"<lastmod>{bugun}</lastmod></url>"
        for y in yollar
    )
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{satirlar}\n</urlset>\n", encoding="utf-8")
    print(f"sitemap.xml: {len(yollar)} adres", file=sys.stderr)


def check_guide_links():
    """guide.html'deki dış linklere HEAD at; kırık olanları uyar (build'i durdurmaz).

    Linkler guide.html'den okunur ki betik ile sayfa arasında liste drift'i olmasın.

    Yalnız `<a href>` bakılıyor. `<link rel="canonical">` de bir href taşıyor ama
    kullanıcının tıklayacağı bir bağlantı değil, sayfanın kendi adresini bildiren
    üstveri · üstelik site yayına çıkana kadar 404 veriyor ve her derlemede
    yanlış alarm üretiyordu.
    """
    guide = SITE / "guide.html"
    if not guide.exists():
        return
    urls = sorted(set(re.findall(r'<a[^>]+href="(https?://[^"]+)"',
                                 guide.read_text(encoding="utf-8"))))
    broken = 0
    for url in urls:
        try:
            req = urllib.request.Request(url, method="HEAD",
                                         headers={"User-Agent": "Mozilla/5.0 (atlas-linkcheck)"})
            code = urllib.request.urlopen(req, timeout=15).status
        except urllib.error.HTTPError as e:
            if e.code == 405:
                try:
                    code = urllib.request.urlopen(url, timeout=15).status
                except Exception:
                    code = e.code
            else:
                code = e.code
        except Exception as e:
            print(f"  UYARI erişilemedi: {url} ({e})", file=sys.stderr)
            broken += 1
            continue
        if code >= 400:
            print(f"  KIRIK LINK ({code}): {url}", file=sys.stderr)
            broken += 1
    status = f"{broken} kırık" if broken else "hepsi sağlam"
    print(f"rehber link kontrolü: {len(urls)} dış link, {status}", file=sys.stderr)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description="Anlaşma verisini doğrula ve üret")
    cli.add_argument("--pull", action="store_true", help="Resmî kaynaklardan indir; başarısızsa dur")
    cli.add_argument("--university", action="append", dest="university_ids", help="Yalnız bu kurum (tekrarlanabilir)")
    cli.add_argument("--dry-run", action="store_true", help="Farkları göster, kaynak veya site dosyalarını değiştirme")
    cli.add_argument("--report", type=Path, help="İnceleme raporunun JSON dosyası")
    cli.add_argument("--check-links", action="store_true", help="Rehber bağlantılarını ayrıca kontrol et")
    args = cli.parse_args()
    try:
        build(args.pull, args.university_ids, args.dry_run, args.report)
        if args.check_links:
            check_guide_links()
    except (ValueError, OSError, KeyError, BadZipFile) as error:
        cli.exit(1, f"Veri üretilemedi: {error}\n")
