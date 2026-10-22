"""Haftalık kaynak denetiminin bildirim issue'su doğru zamanda açılıp kapanıyor mu."""

import importlib.util
import json
import re
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("source_check_issue", ROOT / "scripts/source_check_issue.py")
sci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sci)

KONTROL = "2026-10-22"
DEGISMEDI = {"universities": [{"id": "maku", "previousCount": 1, "count": 1,
                               "added": 0, "removed": 0, "sourceChanged": False}]}


def kurum(tarih=KONTROL):
    return [{"id": "maku", "sourceCheckedAt": tarih}]


def gun_sonra(n):
    return date.fromordinal(date.fromisoformat(KONTROL).toordinal() + n)


class Degerlendirme(unittest.TestCase):
    def test_her_sey_guncelse_bulgu_yok(self):
        self.assertEqual(sci.evaluate(DEGISMEDI, kurum(), gun_sonra(22)), [])

    def test_uyari_esiginden_bir_hafta_once_haber_verir(self):
        bulgu = sci.evaluate(DEGISMEDI, kurum(), gun_sonra(23))
        self.assertEqual(len(bulgu), 1)
        self.assertIn("7 gün içinde", bulgu[0])

    def test_sitede_uyari_gorunen_gun_eskimis_sayilir(self):
        bulgu = sci.evaluate(DEGISMEDI, kurum(), gun_sonra(30))
        self.assertIn("uyarısı görünüyor", bulgu[0])

    def test_kaynak_degisikligi_bildirilir(self):
        rapor = {"universities": [{"id": "marmara", "previousCount": 790, "count": 795,
                                   "added": 7, "removed": 2, "sourceChanged": True}]}
        bulgu = sci.evaluate(rapor, kurum(), gun_sonra(1))
        self.assertEqual(bulgu, ["`marmara` kaynağı değişti: 790 → 795 kayıt (+7 / -2)."])

    def test_rapor_yoksa_denetim_basarisizligi_bildirilir(self):
        bulgu = sci.evaluate(None, kurum(), gun_sonra(1))
        self.assertIn("Denetim raporu üretilemedi", bulgu[0])

    def test_okunamayan_tarih_bildirilir(self):
        bulgu = sci.evaluate(DEGISMEDI, kurum("bilinmiyor"), gun_sonra(1))
        self.assertIn("okunamadı", bulgu[0])

    def test_esik_sitedeki_uyariyla_ayni(self):
        # Site uyarısı ile bildirim eşiği ayrışırsa hatırlatma ya geç ya boşuna gelir.
        js = (ROOT / "site" / "veri.js").read_text(encoding="utf-8")
        esik = re.search(r"now - time > (\d+) \* 86400000", js)
        self.assertIsNotNone(esik, "veri.js içindeki eskime eşiği bulunamadı")
        self.assertEqual(int(esik.group(1)), sci.STALE_DAYS)


class IssueEsitleme(unittest.TestCase):
    def _calistir(self, bulgular, acik):
        cagrilar = []

        def sahte_gh(*args):
            cagrilar.append(args[:2])
            if args[:2] == ("issue", "list"):
                return json.dumps([{"number": 12}] if acik else [])
            return "https://github.com/o/r/issues/13\n" if args[:2] == ("issue", "create") else ""

        with patch.object(sci, "gh", side_effect=sahte_gh):
            sonuc = sci.sync_issue(bulgular, gun_sonra(1), "")
        return sonuc, [c for c in cagrilar if c[0] == "issue" and c[1] != "list"]

    def test_bulgu_varsa_ve_issue_yoksa_acar(self):
        sonuc, cagri = self._calistir(["x"], acik=False)
        self.assertEqual(cagri, [("issue", "create")])
        self.assertIn("açıldı", sonuc)

    def test_bulgu_varsa_acik_issueyu_gunceller_ve_bildirim_icin_yorum_yazar(self):
        _, cagri = self._calistir(["x"], acik=True)
        self.assertEqual(cagri, [("issue", "edit"), ("issue", "comment")])

    def test_her_sey_yolundaysa_acik_issueyu_kapatir(self):
        _, cagri = self._calistir([], acik=True)
        self.assertEqual(cagri, [("issue", "close")])

    def test_her_sey_yolunda_ve_issue_yoksa_dokunmaz(self):
        sonuc, cagri = self._calistir([], acik=False)
        self.assertEqual((sonuc, cagri), ("işlem yok", []))


class WorkflowSiniri(unittest.TestCase):
    def test_yalniz_issue_yazabilir_ve_yalniz_mainde_bildirir(self):
        metin = (ROOT / ".github" / "workflows" / "source-check.yml").read_text(encoding="utf-8")
        self.assertIn("issues: write", metin)
        self.assertNotIn("contents: write", metin)
        self.assertIn("scripts/source_check_issue.py --apply", metin)
        self.assertIn("github.ref == 'refs/heads/main'", metin)


if __name__ == "__main__":
    unittest.main()
