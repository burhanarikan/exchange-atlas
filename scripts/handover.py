#!/usr/bin/env python3
"""Exchange Atlas proje devir (handover) ve kimlik bütünlüğü aracı.

Projeyi yeni bir kişiye, öğrenci topluluğuna veya kuruma devrederken:
  - GitHub depo yolu (`owner/repo`)
  - İletişim ve kaldırma talebi e-postası (`kullanici@alan.uzanti`)
  - Telif ve atıf sahibi (`Ad Soyad` / kurum adı)
  - Kanonik alan adı (`exchangeatlas.org`)

bilgilerini tüm kod, belge, yapılandırma ve test bekçilerinde tek komutla,
atomik olarak günceller veya `--check` ile aralarındaki tutarlılığı denetler.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import version_assets

KISISEL_SAGLAYICILAR = {
    "gmail.com",
    "hotmail.com",
    "outlook.com",
    "yahoo.com",
    "yaani.com",
    "icloud.com",
    "proton.me",
}

REPO_FILES = (
    ".github/ISSUE_TEMPLATE/config.yml",
    "CHANGELOG.md",
    "CITATION.cff",
    "README-DEPLOY.md",
    "README.md",
    "site/404.html",
    "site/app.js",
    "site/guide.html",
    "site/index.html",
    "site/linkedin.html",
    "tests/test_site.py",
)

PLAIN_EMAIL_FILES = (
    "KAYNAK.md",
    "README.md",
    "SECURITY.md",
)

DOMAIN_FILES = (
    ".github/workflows/pages.yml",
    "CITATION.cff",
    "README-DEPLOY.md",
    "README.md",
    "scripts/build_data.py",
    "scripts/check_live_headers.py",
    "site/CNAME",
    "site/agreements.html",
    "site/guide.html",
    "site/index.html",
    "site/linkedin.html",
    "site/llms.txt",
    "site/robots.txt",
    "site/sitemap.xml",
    "tests/test_acik_kaynak.py",
    "tests/test_site.py",
)


def split_email_parts(email: str) -> tuple[str, str, str]:
    """E-postayı JS parçalı yazımı için (kullanıcı, sağlayıcı_kökü, .uzantı) olarak ayırır."""
    m = re.fullmatch(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+)\.([A-Za-z]{2,})", email.strip())
    if not m:
        raise ValueError(f"Geçersiz e-posta biçimi: {email!r}")
    return m.group(1), m.group(2), "." + m.group(3)


def validate_repo(repo: str) -> str:
    repo = repo.strip().strip("/")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError(f"Geçersiz GitHub depo yolu (owner/repo bekleniyor): {repo!r}")
    return repo


def validate_domain(domain: str) -> str:
    domain = re.sub(r"^https?://", "", domain.strip()).rstrip("/")
    if not re.fullmatch(r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}", domain):
        raise ValueError(f"Geçersiz alan adı: {domain!r}")
    return domain.lower()


def detect_current(root: pathlib.Path = ROOT) -> dict[str, str]:
    """Depodaki mevcut kanonik kimlik değerlerini okur."""
    citation = (root / "CITATION.cff").read_text(encoding="utf-8")
    m_repo = re.search(r'repository-code:\s*"https://github\.com/([^"]+)"', citation)
    if not m_repo:
        raise RuntimeError("CITATION.cff içinde repository-code bulunamadı")
    repo = m_repo.group(1)

    yayin = (root / "tests" / "test_yayin.py").read_text(encoding="utf-8")
    m_email = re.search(r'BUGUNKU\s*=\s*"([^"]+)"', yayin)
    if not m_email:
        raise RuntimeError("tests/test_yayin.py içinde BUGUNKU e-posta tanımı bulunamadı")
    email = m_email.group(1)

    lic = (root / "LICENSE").read_text(encoding="utf-8")
    m_author = re.search(r"Copyright \(c\) \d{4}(?:-\d{4})?\s+(.+)", lic)
    if not m_author:
        raise RuntimeError("LICENSE içinde telif satırı bulunamadı")
    author = m_author.group(1).strip()

    cname = (root / "site" / "CNAME").read_text(encoding="utf-8").strip().splitlines()[0].strip()
    return {
        "repo": repo,
        "email": email,
        "author": author,
        "domain": cname,
    }


def check_consistency(root: pathlib.Path = ROOT) -> list[str]:
    """Tüm dosyalarda kimlik, iletişim ve alan adı tutarlılığını denetler."""
    cur = detect_current(root)
    repo = cur["repo"]
    email = cur["email"]
    user, host_root, host_tld = split_email_parts(email)
    domain = cur["domain"]
    errors: list[str] = []

    for rel in REPO_FILES:
        path = root / rel
        if not path.exists():
            errors.append(f"Eksik dosya: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if repo not in text:
            errors.append(f"{rel}: {repo} referansı bulunamadı")

    for rel in PLAIN_EMAIL_FILES:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        if email not in text:
            errors.append(f"{rel}: {email} adresi bulunamadı")

    # Parçalı JS yazımları
    app_js = (root / "site" / "app.js").read_text(encoding="utf-8")
    expected_app = f'const GERI_BILDIRIM = "{user}" + "@" + "{host_root}" + "{host_tld}";'
    if expected_app not in app_js:
        errors.append("site/app.js: GERI_BILDIRIM parçalı e-posta tanımı güncel adresle uyuşmuyor")

    home_js = (root / "site" / "home.js").read_text(encoding="utf-8")
    expected_home = f'function adres() {{ return "{user}" + "@" + "{host_root}" + "{host_tld}"; }}'
    if expected_home not in home_js:
        errors.append("site/home.js: adres() parçalı e-posta tanımı güncel adresle uyuşmuyor")

    guide_js = (root / "site" / "guide.js").read_text(encoding="utf-8")
    expected_guide = f'var cu = "{user}", caddr = cu + "@" + "{host_root}" + "{host_tld}";'
    if expected_guide not in guide_js:
        errors.append("site/guide.js: caddr parçalı e-posta tanımı güncel adresle uyuşmuyor")

    for rel in DOMAIN_FILES:
        path = root / rel
        if not path.exists():
            errors.append(f"Eksik dosya: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if domain not in text:
            errors.append(f"{rel}: kanonik alan adı ({domain}) bulunamadı")

    return errors


def _update_citation_author(citation_text: str, new_author: str) -> str:
    parts = new_author.strip().split()
    if len(parts) >= 2:
        given = " ".join(parts[:-1])
        family = parts[-1]
        replacement = f'  - family-names: "{family}"\n    given-names: "{given}"'
    else:
        replacement = f'  - family-names: "{new_author.strip()}"\n    given-names: ""'
    return re.sub(
        r'  - family-names:\s*"[^"]*"\n\s+given-names:\s*"[^"]*"',
        replacement,
        citation_text,
        count=1,
    )


def apply_handover(
    root: pathlib.Path = ROOT,
    *,
    new_repo: str | None = None,
    new_email: str | None = None,
    new_author: str | None = None,
    new_domain: str | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Verilen yeni kimlik/iletişim/alan adı bilgilerini tüm depoya uygular."""
    cur = detect_current(root)
    old_repo = cur["repo"]
    old_email = cur["email"]
    old_author = cur["author"]
    old_domain = cur["domain"]

    target_repo = validate_repo(new_repo) if new_repo else old_repo
    target_email = new_email.strip() if new_email else old_email
    if new_email:
        split_email_parts(target_email)
    target_author = new_author.strip() if new_author else old_author
    target_domain = validate_domain(new_domain) if new_domain else old_domain

    old_user, old_host_root, old_host_tld = split_email_parts(old_email)
    new_user, new_host_root, new_host_tld = split_email_parts(target_email)

    changed_files: list[str] = []

    def update_file(rel: str, transform) -> None:
        path = root / rel
        if not path.exists():
            return
        before = path.read_text(encoding="utf-8")
        after = transform(before)
        if after != before:
            if rel not in changed_files:
                changed_files.append(rel)
            if not dry_run:
                path.write_text(after, encoding="utf-8")

    # 1. Repo slug güncellemeleri
    if target_repo != old_repo:
        for rel in REPO_FILES:
            update_file(rel, lambda t: t.replace(old_repo, target_repo))

    # 2. E-posta güncellemeleri (düz metin + parçalı JS + test bekçileri)
    if target_email != old_email:
        for rel in PLAIN_EMAIL_FILES:
            update_file(rel, lambda t: t.replace(old_email, target_email))

        update_file(
            "site/app.js",
            lambda t: t.replace(
                f'const GERI_BILDIRIM = "{old_user}" + "@" + "{old_host_root}" + "{old_host_tld}";',
                f'const GERI_BILDIRIM = "{new_user}" + "@" + "{new_host_root}" + "{new_host_tld}";',
            ),
        )
        update_file(
            "site/home.js",
            lambda t: t.replace(
                f'function adres() {{ return "{old_user}" + "@" + "{old_host_root}" + "{old_host_tld}"; }}',
                f'function adres() {{ return "{new_user}" + "@" + "{new_host_root}" + "{new_host_tld}"; }}',
            ),
        )
        update_file(
            "site/guide.js",
            lambda t: t.replace(
                f'var cu = "{old_user}", caddr = cu + "@" + "{old_host_root}" + "{old_host_tld}";',
                f'var cu = "{new_user}", caddr = cu + "@" + "{new_host_root}" + "{new_host_tld}";',
            ),
        )

        def transform_test_yayin(text: str) -> str:
            email_domain = target_email.split("@", 1)[1].lower()
            muaf_str = f'("{target_email}",)' if email_domain in KISISEL_SAGLAYICILAR else "()"
            text = re.sub(r"MUAF\s*=\s*\([^)]*\)", f"MUAF = {muaf_str}", text, count=1)
            text = text.replace(f'BUGUNKU = "{old_email}"', f'BUGUNKU = "{target_email}"')
            return text

        update_file("tests/test_yayin.py", transform_test_yayin)

        def transform_test_site(text: str) -> str:
            text = text.replace(f'if "{old_user}" not in satir:', f'if "{new_user}" not in satir:')
            text = text.replace(f'self.assertNotIn("{old_user}@", metin,', f'self.assertNotIn("{new_user}@", metin,')
            text = text.replace(
                f'if "{old_user}" not in (ROOT / "site" / ad).read_text(encoding="utf-8")]',
                f'if "{new_user}" not in (ROOT / "site" / ad).read_text(encoding="utf-8")]',
            )
            return text

        update_file("tests/test_site.py", transform_test_site)

    # 3. Telif ve yazar güncellemeleri
    if target_author != old_author:
        update_file(
            "LICENSE",
            lambda t: re.sub(
                r"(Copyright \(c\) \d{4}(?:-\d{4})?\s+).+",
                lambda m: m.group(1) + target_author,
                t,
                count=1,
            ),
        )
        update_file("CITATION.cff", lambda t: _update_citation_author(t, target_author))

    # 4. Kanonik alan adı güncellemeleri
    if target_domain != old_domain:
        for rel in DOMAIN_FILES:
            update_file(rel, lambda t: t.replace(old_domain, target_domain))

    # 5. JS/HTML değiştiyse asset hash'lerini güncelle
    if not dry_run and any(f.startswith("site/") for f in changed_files):
        version_assets.update_versions(root / "site", check=False)

    return changed_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Mevcut kimlik/iletişim/alan adı tutarlılığını denetler.")
    parser.add_argument("--repo", help="Yeni GitHub depo yolu (ör. yeni-kurum/exchange-atlas)")
    parser.add_argument("--email", help="Yeni iletişim e-postası (ör. erasmus@ornek.edu.tr)")
    parser.add_argument("--author", help="Yeni telif/atıf adı (ör. 'Ad Soyad' veya topluluk adı)")
    parser.add_argument("--domain", help="Yeni kanonik alan adı (ör. exchangeatlas.org)")
    parser.add_argument("--dry-run", action="store_true", help="Dosyaları değiştirmeden etkilenecek dosyaları listeler.")
    args = parser.parse_args(argv)

    cur = detect_current(ROOT)
    if args.check or not any([args.repo, args.email, args.author, args.domain]):
        errors = check_consistency(ROOT)
        print(f"Depo yolu      : {cur['repo']}")
        print(f"İletişim adresi: {cur['email']}")
        print(f"Telif / Atıf   : {cur['author']}")
        print(f"Kanonik alan   : {cur['domain']}")
        if errors:
            print("\nTUTARSIZLIKLAR:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 1
        print("Durum          : Tutarlı (tüm dosyalar ve bekçiler senkron)")
        return 0

    changed = apply_handover(
        ROOT,
        new_repo=args.repo,
        new_email=args.email,
        new_author=args.author,
        new_domain=args.domain,
        dry_run=args.dry_run,
    )
    prefix = "[ÖNİZLEME] Değişecek dosyalar" if args.dry_run else "Güncellenen dosyalar"
    print(f"{prefix} ({len(changed)}):")
    for rel in changed:
        print(f"  - {rel}")
    if not args.dry_run:
        errors = check_consistency(ROOT)
        if errors:
            print("HATA: Güncelleme sonrası tutarsızlık bulundu:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
