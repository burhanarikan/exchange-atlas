#!/usr/bin/env python3
"""Canlı yayında eski tarayıcı önbelleğini ve otomatik ağ raporlamasını denetler."""
import argparse
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def header_errors(headers):
    """Sıfır ömürlü raporlama başlıkları eski politikayı siler; etkin raporlama reddedilir."""
    headers = {key.lower(): value for key, value in headers.items()}
    errors = []
    cache = {part.strip().lower() for part in headers.get("cache-control", "").split(",")}
    if not ({"no-cache", "no-store"} & cache or {"max-age=0", "must-revalidate"} <= cache):
        errors.append("Tarayıcı dosyayı yeniden doğrulamadan kullanabiliyor")
    for name in ("nel", "report-to"):
        if name not in headers:
            continue
        try:
            policy = json.loads(headers[name])
            if not isinstance(policy, dict) or policy.get("max_age") != 0:
                errors.append(f"Etkin raporlama politikası: {name}")
        except (ValueError, TypeError):
            errors.append(f"Raporlama başlığı okunamadı: {name}")
    if headers.get("reporting-endpoints"):
        errors.append("Raporlama hedefi tanımlı: reporting-endpoints")
    return errors


def check_live(base):
    """Bütün kurum sayfaları ve değişebilen kaynaklar gerçek yanıtlarıyla kontrol edilir."""
    universities = json.loads((ROOT / "config/universities.json").read_text(encoding="utf-8"))
    paths = ["/", "/guide?uni=maku", "/universities.json", "/app.js", "/home.js", "/veri.js", "/styles.css"]
    paths += [f"/agreements?uni={uni['id']}" for uni in universities]
    paths += [f"/data-{uni['id']}.json" for uni in universities]

    def fetch(path):
        request = urllib.request.Request(base.rstrip("/") + path, headers={
            "User-Agent": "Mozilla/5.0 ExchangeAtlas-live-check",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        with urllib.request.urlopen(request, timeout=30) as response:
            errors = header_errors(response.headers)
            if response.status != 200:
                errors.append(f"HTTP {response.status}")
        return path, errors

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, paths))
    for path, errors in results:
        print(f"{path}: " + ("; ".join(errors) if errors else "OK"))
    return not any(errors for _, errors in results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="https://exchangeatlas.org")
    raise SystemExit(0 if check_live(parser.parse_args().base) else 1)
