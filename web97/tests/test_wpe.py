import unittest
from pathlib import Path
class TestWPE(unittest.TestCase):
    def test_retain_security(self):
        s=Path('web97/wpe_modern_js_headless.c').read_text()
        t=Path('web97/wpe_probe.py').read_text()
        self.assertIn('webkit_web_view_evaluate_javascript',s)
        self.assertIn('ES2015_EXECUTED',t)
        self.assertIn('headless',t)
        self.assertNotIn('WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS',s+t)
        self.assertNotIn('--no-sandbox',s+t)
    def test_actual_modern_es6_syntax(self):
        s=Path('web97/wpe_modern_js_headless.c').read_text()
        self.assertIn('const n=[1,2,3].map(v=>v*2)',s)
    def test_result_claim_not_graphical(self):
        s=Path('web97/wpe_probe.py').read_text()
        self.assertIn('"real_webpage_visually_confirmed":False',s)
        self.assertIn('"not_actual_384_mib_guest_or_gui":True',s)
if __name__=='__main__':unittest.main()
