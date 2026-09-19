"""Yeni veri eski tarayıcı koduyla birleşmemeli; sürümler dosyanın içeriğini izlemeli."""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("version_assets", ROOT / "scripts/version_assets.py")
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)


class AssetVersions(unittest.TestCase):
    def test_content_changes_change_url_and_check_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            (site / "app.js").write_text("old code")
            (site / "styles.css").write_text("body {}")
            page = site / "index.html"
            page.write_text('<script src="app.js"></script><link href="/styles.css"><a href="https://example.edu/file.css">Kaynak</a>')
            self.assertEqual(assets.update_versions(site), ["index.html"])
            old = page.read_text()
            self.assertIn('https://example.edu/file.css', old)
            self.assertIn('/styles.css?v=', old)
            self.assertEqual(assets.update_versions(site, check=True), [])
            (site / "app.js").write_text("new code")
            self.assertEqual(assets.update_versions(site, check=True), ["index.html"])
            self.assertEqual(page.read_text(), old)
            assets.update_versions(site)
            self.assertNotEqual(page.read_text(), old)
            self.assertEqual(assets.update_versions(site, check=True), [])

    def test_published_asset_versions_match_content(self):
        self.assertEqual(assets.update_versions(check=True), [],
                         "JS/CSS değişti: python3 scripts/version_assets.py çalıştırılmalı.")

    def test_json_requests_revalidate_browser_cache(self):
        script = '''
const fs = require('fs'), vm = require('vm'), assert = require('assert');
let request;
const context = {window:{}, fetch:(url, options) => {
  request = {url, options};
  return Promise.resolve({ok:true, headers:{get:()=>'application/json'}, json:()=>({count:468})});
}};
vm.createContext(context);
vm.runInContext(fs.readFileSync('site/veri.js','utf8'),context);
context.window.atlasJson('data-maku.json').then(data => {
  assert.strictEqual(request.url,'data-maku.json');
  assert.strictEqual(request.options?.cache,'no-cache');
  assert.strictEqual(data.count,468);
}).catch(error => {console.error(error); process.exitCode=1;});
'''
        result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class LiveHeaderPolicies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("check_live_headers", ROOT / "scripts/check_live_headers.py")
        cls.checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.checker)

    def test_observed_four_hour_cache_and_reporting_fail(self):
        headers = {"Cache-Control": "public, max-age=14400, must-revalidate",
                   "NEL": '{"report_to":"cf-nel","success_fraction":0.0,"max_age":604800}',
                   "Report-To": '{"group":"cf-nel","max_age":604800,"endpoints":[{"url":"https://a.nel.cloudflare.com/report"}]}'}
        self.assertEqual(len(self.checker.header_errors(headers)), 3)

    def test_disabled_policies_and_revalidation_pass(self):
        self.assertEqual(self.checker.header_errors({"Cache-Control": "no-cache", "NEL": '{"max_age":0}',
                         "Report-To": '{"group":"cf-nel","max_age":0,"endpoints":[]}'}), [])
        self.assertEqual(self.checker.header_errors({"Cache-Control": "public, max-age=0, must-revalidate"}), [])

    def test_unreadable_or_new_reporting_endpoints_fail(self):
        for key, value in (("NEL", "invalid"), ("NEL", "[]"), ("Reporting-Endpoints", 'default="https://example.org/report"')):
            self.assertTrue(self.checker.header_errors({"Cache-Control": "no-cache", key: value}))
