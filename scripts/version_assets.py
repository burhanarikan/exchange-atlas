#!/usr/bin/env python3
"""HTML'deki yerel JS/CSS adreslerini dosya özetiyle sürümler; eski kodu ayırır."""
import argparse
import hashlib
import html
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SITE = Path(__file__).resolve().parent.parent / "site"
REFERENCE = re.compile(r'''(?P<start>\b(?:src|href)=["'])(?P<url>[^"']+)(?P<end>["'])''')


def update_versions(site=SITE, check=False):
    """Dosya değişince URL değişir; kontrol kipinde eski başvurular yalnız bildirilir."""
    site = Path(site).resolve()
    pending = []
    for page in sorted(site.rglob("*.html")):
        original = page.read_text(encoding="utf-8")

        def replace(match):
            url = urlsplit(html.unescape(match["url"]))
            if url.scheme or url.netloc or Path(url.path).suffix not in (".js", ".css"):
                return match[0]
            asset = ((site / url.path.lstrip("/")) if url.path.startswith("/") else (page.parent / url.path)).resolve()
            if not asset.is_relative_to(site) or not asset.is_file():
                raise ValueError(f"Yayın paketinde kaynak dosya bulunamadı: {page.name}: {url.path}")
            version = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
            query = [(key, value) for key, value in parse_qsl(url.query) if key != "v"]
            query.append(("v", version))
            updated = urlunsplit(("", "", url.path, urlencode(query), url.fragment))
            return match["start"] + html.escape(updated, quote=True) + match["end"]

        updated = REFERENCE.sub(replace, original)
        if updated != original:
            pending.append((page, updated))
    if not check:
        for page, updated in pending:
            page.write_text(updated, encoding="utf-8")
    return [page.relative_to(site).as_posix() for page, _ in pending]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Dosyaları değiştirmeden eski sürüm başvurularını denetle")
    args = parser.parse_args()
    changed = update_versions(check=args.check)
    if changed:
        print(("Sürüm başvuruları güncel değil: " if args.check else "Sürümlendi: ") + ", ".join(changed))
    raise SystemExit(1 if args.check and changed else 0)
