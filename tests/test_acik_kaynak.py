"""Public depo yüzeyinin duyuru sonrasında da bütün kalmasını denetler."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class PublicDepoDokumantasyonu(unittest.TestCase):
    """Yeni katkıcı ilk bakışta projenin ne olduğunu ve nasıl katkı vereceğini bulmalı."""

    GEREKEN_DOSYALAR = (
        "README.md",
        "LICENSE",
        "NOTICE.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "CHANGELOG.md",
        "README-DEPLOY.md",
        "CITATION.cff",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/dependabot.yml",
    )

    def test_public_depo_belgeleri_var(self):
        eksik = [ad for ad in self.GEREKEN_DOSYALAR if not (ROOT / ad).exists()]
        self.assertEqual(eksik, [], f"Public depo belgesi eksik: {eksik}")

    def test_readme_canli_durum_ve_katki_yollarini_gosteriyor(self):
        metin = (ROOT / "README.md").read_text(encoding="utf-8")
        for parca in (
            "https://exchangeatlas.org",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CODE_OF_CONDUCT.md",
            "CHANGELOG.md",
            "Cloudflare Pages",
        ):
            with self.subTest(parca=parca):
                self.assertIn(parca, metin)
        self.assertNotIn("henüz yayında değil", metin)
        self.assertNotIn("Depo şu an özel", metin)

    def test_issue_sablonlari_gecerli_frontmatter_tasiyor(self):
        klasor = ROOT / ".github" / "ISSUE_TEMPLATE"
        sablonlar = sorted(klasor.glob("*.md"))
        self.assertGreaterEqual(len(sablonlar), 4)
        for yol in sablonlar:
            with self.subTest(sablon=yol.name):
                metin = yol.read_text(encoding="utf-8")
                self.assertTrue(metin.startswith("---\n"))
                self.assertRegex(metin, r"\nname:\s+.+\n")
                self.assertRegex(metin, r"\nabout:\s+.+\n")
                self.assertRegex(metin, r"\ntitle:\s*.*\n")
                self.assertTrue(metin.count("---") >= 2)

    def test_workflow_adi_kanonik_yayini_dogru_anlatiyor(self):
        metin = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("name: Quality checks and live validation", metin)
        self.assertIn("LIVE_SITE_URL", metin)
        self.assertIn("vars.PAGES_ENABLED == 'true'", metin)

    def test_changelog_ilk_surumu_ve_unreleased_bolumunu_tasiyor(self):
        metin = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## [Unreleased]", metin)
        self.assertIn("## [1.0.0] - 2026-08-24", metin)


class PublicDepoGizliAnahtarBekcisi(unittest.TestCase):
    """Yeni açık katkılarda bariz anahtar kalıplarının yanlışlıkla eklenmesini yakalar."""

    KALIPLAR = (
        r"gh[pousr]_[A-Za-z0-9_\-]{20,}",
        r"github_pat_[A-Za-z0-9_]{20,}",
        r"sk-[A-Za-z0-9]{20,}",
        r"AKIA[0-9A-Z]{16}",
        r"-----BEGIN (RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY-----",
        r"xox[baprs]-[A-Za-z0-9-]{20,}",
    )

    def test_bariz_gizli_anahtar_kalibi_yok(self):
        ignore = {".git"}
        dosyalar = [
            yol for yol in ROOT.rglob("*")
            if yol.is_file() and not any(parca in ignore for parca in yol.parts)
        ]
        bulgular = []
        kaliplar = [re.compile(k) for k in self.KALIPLAR]
        for yol in dosyalar:
            try:
                metin = yol.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for satir_no, satir in enumerate(metin.splitlines(), 1):
                if any(k.search(satir) for k in kaliplar):
                    bulgular.append(f"{yol.relative_to(ROOT)}:{satir_no}")
        self.assertEqual(bulgular, [], f"Bariz gizli anahtar kalıbı bulundu: {bulgular}")
