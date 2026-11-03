import importlib.util,unittest
from pathlib import Path
path=Path(__file__).resolve().parents[1]/'browser_keyboard.py'
sp=importlib.util.spec_from_file_location('kb',path)
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class TestBrowserKeys(unittest.TestCase):
 def test_addressbar_and_enter(self):
  seq=m.sequence()
  self.assertEqual(len(seq),len(m.URL)+2)
  self.assertEqual([x['data'] for x in seq[0]['keys']],['ctrl','l'])
  self.assertEqual(seq[-1]['keys'][0]['data'],'ret')
 def test_colon_is_shift_semicolon(self):
  self.assertEqual([x['data'] for x in m.keys_for_text(':')[0]['keys']],['shift','semicolon'])
 def test_https_only(self):
  with self.assertRaises(ValueError):m.sequence('http://example.com')
 def test_reject_non_ascii_and_markup(self):
  with self.assertRaises(ValueError):m.sequence('https://example.com/<script>')
if __name__=='__main__':unittest.main()
