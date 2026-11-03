import unittest
from pathlib import Path
from netsurf_js_probe import PAGES,URLS

class TestBrowserJSLab(unittest.TestCase):
    def test_fixtures_are_real_scripting_probes(self):
        folder=Path('web96/fixtures')
        for page in PAGES:
            if page=='wikipedia':continue
            html=(folder/page).read_text()
            self.assertIn('<script>',html)
            self.assertIn('NOT_',html) if page!='01-execution.html' else self.assertIn('JS_BASIC_EXECUTED',html)
    def test_https_public_and_local_fixtures(self):
        self.assertEqual(URLS['wikipedia'],'https://www.wikipedia.org/')
        for name,uri in URLS.items():
            self.assertTrue(uri.startswith('http://127.0.0.1:8765/') or uri.startswith('https://'))
    def test_es2015_uses_real_arrow_function(self):
        self.assertIn('=>',(Path('web96/fixtures/03-modern.html').read_text()))
    def test_fetch_never_bypasses_tls_or_credentials(self):
        s=Path('web96/netsurf_js_probe.py').read_text()
        self.assertNotIn('--ignore-certificate-errors',s)
        self.assertNotIn('--no-sandbox',s)
        self.assertIn('same-UID',s)
if __name__=='__main__':unittest.main()
