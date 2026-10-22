#!/usr/bin/env python3
"""Haftalık kaynak denetiminin sonucunu tek bir GitHub issue'suyla bildirir.

Denetim kaynak/site dosyalarına dokunmaz; bu betik de dokunmaz. Yalnız şunu yapar:
Bir kaynak değiştiyse, kontrol tarihi sitedeki 30 günlük uyarıya yaklaştıysa
ya da denetim raporu üretilemediyse açık issue'yu oluşturur veya günceller.
Her şey yolundaysa açık issue'yu kapatır. Böylece GitHub e-postası hatırlatma olur.
"""
import argparse
import json
import os
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# site/veri.js bu eşikten sonra "yeniden kontrol edin" uyarısı gösterir;
# ikisinin aynı kalması testle korunuyor.
STALE_DAYS = 30
# Denetim haftada bir koşuyor: 23. günde uyarmak en az bir hafta pay bırakır.
WARN_DAYS = STALE_DAYS - 7

LABEL = "kaynak-denetimi"
TITLE = "Kaynak denetimi: veri yenilemesi gerekiyor"


def evaluate(report, universities, today):
    """Dikkat gerektiren bulguları döndürür; boş liste her şeyin yolunda olduğunu söyler."""
    findings = []
    if report is None:
        findings.append("Denetim raporu üretilemedi: bir kaynak indirilemedi veya "
                        "ayrıştırılamadı. İş akışının günlüğüne bakın.")
        report = {"universities": []}
    for u in report.get("universities", []):
        if u.get("sourceChanged"):
            findings.append(
                f"`{u['id']}` kaynağı değişti: {u['previousCount']} → {u['count']} kayıt "
                f"(+{u['added']} / -{u['removed']})."
            )
    for u in universities:
        raw = u.get("sourceCheckedAt") or u.get("sourceDownloadedAt")
        try:
            age = (today - date.fromisoformat(raw)).days
        except (TypeError, ValueError):
            findings.append(f"`{u['id']}` için kaynak kontrol tarihi okunamadı.")
            continue
        # veri.js gece yarısından ölçer: 30. günün içinde uyarı zaten görünür.
        if age >= STALE_DAYS:
            findings.append(f"`{u['id']}` son kontrolünün üzerinden {age} gün geçti; "
                            "sitede yeniden kontrol uyarısı görünüyor.")
        elif age >= WARN_DAYS:
            findings.append(f"`{u['id']}` son kontrolünün üzerinden {age} gün geçti; "
                            f"{STALE_DAYS - age} gün içinde sitede uyarı görünecek.")
    return findings


def issue_body(findings, today, run_url):
    # Depo adı GitHub'dan gelir; sabit yazılırsa devirde (scripts/handover.py) kalır.
    repo = os.environ.get("GITHUB_REPOSITORY")
    guide = (f"[`VERI-BAKIMI.md`]({os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}/blob/main/VERI-BAKIMI.md)"
             if repo else "`VERI-BAKIMI.md`")
    lines = [f"Haftalık kaynak denetimi ({today.isoformat()}) dikkat gerektiren durum buldu:", ""]
    lines += [f"- {f}" for f in findings]
    lines += [
        "",
        f"Yapılacaklar: {guide} içindeki önizleme, "
        "inceleme ve yenileme adımları bakımcının makinesinde uygulanır, değişiklik PR ile yayımlanır.",
        "",
        "Bu issue otomatik açıldı. Sonraki denetimde her şey yolundaysa kendiliğinden kapanır.",
    ]
    if run_url:
        lines += ["", f"Denetim çalışması: {run_url}"]
    return "\n".join(lines)


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def sync_issue(findings, today, run_url):
    gh("label", "create", LABEL, "--color", "D93F0B", "--force",
       "--description", "Haftalık kaynak denetiminin otomatik bildirimi")
    open_issues = json.loads(gh("issue", "list", "--label", LABEL, "--state", "open",
                                "--json", "number", "--limit", "1"))
    number = str(open_issues[0]["number"]) if open_issues else None
    if findings:
        body = issue_body(findings, today, run_url)
        if number:
            gh("issue", "edit", number, "--body", body)
            # Gövde düzenlemesi bildirim göndermez; yorum gönderir.
            gh("issue", "comment", number, "--body", body)
            return f"güncellendi #{number}"
        return "açıldı " + gh("issue", "create", "--title", TITLE, "--label", LABEL,
                              "--body", body).strip()
    if number:
        gh("issue", "close", number, "--comment",
           f"{today.isoformat()} denetiminde bütün kaynaklar güncel; kapatılıyor.")
        return f"kapatıldı #{number}"
    return "işlem yok"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    parser.add_argument("--run-url", default="")
    parser.add_argument("--apply", action="store_true", help="Issue'yu gerçekten aç/güncelle/kapat")
    args = parser.parse_args()

    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        report = None
    universities = json.loads((ROOT / "site" / "universities.json").read_text(encoding="utf-8"))
    findings = evaluate(report, universities, args.today)
    if not args.apply:
        print(issue_body(findings, args.today, args.run_url) if findings else "Dikkat gerektiren durum yok.")
        return
    print(sync_issue(findings, args.today, args.run_url))


if __name__ == "__main__":
    main()
