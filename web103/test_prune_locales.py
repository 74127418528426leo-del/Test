import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name('prune_locales.py')


class LocalePruneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'root'
        self.locales = self.root / 'usr/share/locale'
        for name in ('en', 'en_GB', 'en@variant', 'es', 'es_MX', 'es@variant', 'fr', 'zh_CN'):
            folder = self.locales / name / 'LC_MESSAGES'
            folder.mkdir(parents=True, exist_ok=True)
            (folder / 'app.mo').write_text(name)
        (self.locales / 'locale.alias').write_text('keep')
        for name in ('usr/lib/firmware/iwlwifi.bin', 'etc/ssl/certs/ca-certificates.crt', 'usr/lib/firefox-esr/libxul.so'):
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('preserve')
        self.outside = Path(self.tmp.name) / 'outside'
        self.outside.mkdir()
        (self.outside / 'keep').write_text('untouched')
        (self.locales / 'de').symlink_to(self.outside, target_is_directory=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_preserves_required_languages_and_nonlocale_files(self):
        p = subprocess.run([sys.executable, str(SCRIPT), str(self.root)], text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        report = json.loads(p.stdout)
        self.assertEqual(set(report['removed']), {'fr', 'zh_CN', 'de'})
        for name in ('en', 'en_GB', 'en@variant', 'es', 'es_MX', 'es@variant', 'locale.alias'):
            self.assertTrue((self.locales / name).exists(), name)
        for name in ('fr', 'zh_CN', 'de'):
            self.assertFalse((self.locales / name).exists(), name)
        self.assertEqual((self.outside / 'keep').read_text(), 'untouched')
        for name in ('usr/lib/firmware/iwlwifi.bin', 'etc/ssl/certs/ca-certificates.crt', 'usr/lib/firefox-esr/libxul.so'):
            self.assertEqual((self.root / name).read_text(), 'preserve')

    def test_rejects_locale_directory_symlink(self):
        import shutil
        shutil.rmtree(self.locales)
        self.locales.symlink_to(self.outside, target_is_directory=True)
        p = subprocess.run([sys.executable, str(SCRIPT), str(self.root)], text=True, capture_output=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual((self.outside / 'keep').read_text(), 'untouched')

    def test_rejects_system_root(self):
        p = subprocess.run([sys.executable, str(SCRIPT), '/'], text=True, capture_output=True)
        self.assertNotEqual(p.returncode, 0)


if __name__ == '__main__':
    unittest.main()
