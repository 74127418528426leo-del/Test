import subprocess
import unittest
from cache_probe import instrument

class CacheProbeTests(unittest.TestCase):
    def test_retains_existing_migration_sequence_and_accepts_only_one_hook(self):
        src='before\n"$B" sleep 8\nemit P50_STAGE_START\nafter\n'
        result=instrument(src)
        self.assertTrue(result.startswith('before\n'))
        self.assertIn('"$B" sleep 8\nemit P50_STAGE_START\nafter\n',result)
        p=subprocess.run(['sh','-n'],input=result,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        with self.assertRaises(ValueError):instrument(result)
    def test_rejects_missing_or_ambiguous_migration_hooks(self):
        hook='"$B" sleep 8\nemit P50_STAGE_START\n'
        for text in ('bad',hook+hook):
            with self.assertRaises(ValueError):instrument(text)

if __name__=='__main__':unittest.main()
