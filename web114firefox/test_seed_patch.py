import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import seed_patch


class SeedPatchTests(unittest.TestCase):
    def test_boot_hook_is_guarded_and_preserves_sequence(self):
        source = 'before' + seed_patch.MAIN_MARKER + 'after'
        output = seed_patch.patch_main(source)
        self.assertIn(seed_patch.MAIN_MARKER, output)
        self.assertIn('[ -z "${TORAM:-}" ]', output)
        self.assertIn('P50_V114_UI_CACHE', output)
        self.assertIn('firefox-esr file:///usr/share/puppy50web/index.html', output)
        self.assertNotIn('MOZ_DISABLE_CONTENT_SANDBOX', output)
        self.assertEqual(subprocess.run(['sh', '-n'], input=output, text=True).returncode, 0)
        with self.assertRaises(ValueError):
            seed_patch.patch_main('missing')
        with self.assertRaises(ValueError):
            seed_patch.patch_main(output)

    def test_wrapper_supplies_independent_writable_cache_and_forwards_arguments(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            seed = root / 'seed'
            seed.write_bytes(b'version-matched test cache')
            binary = root / 'firefox-esr'
            binary.write_text('#!/bin/sh\nprintf "%s\\n" "${MOZ_STARTUP_CACHE:-}" "$1" > "$TEST_RESULT"\n')
            binary.chmod(0o755)
            wrapper = root / 'wrapper'
            wrapper.write_text(seed_patch.WRAPPER.replace('/run/p50-stage/tools/p50-v114-ui-cache', str(seed)))
            wrapper.chmod(0o755)
            env = dict(os.environ, PATH=str(root) + ':/usr/bin:/bin', TMPDIR=str(root), TEST_RESULT=str(root / 'result'))
            subprocess.run([str(wrapper), 'file:///browser-home'], env=env, check=True)
            lines = (root / 'result').read_text().splitlines()
            self.assertEqual(lines[1], 'file:///browser-home')
            cache = Path(lines[0])
            self.assertNotEqual(cache, seed)
            self.assertEqual(cache.read_bytes(), seed.read_bytes())
            self.assertTrue(os.access(cache, os.W_OK))
            seed.unlink()
            subprocess.run([str(wrapper), 'about:blank'], env=env, check=True)
            self.assertEqual((root / 'result').read_text().splitlines(), ['', 'about:blank'])


if __name__ == '__main__':
    unittest.main()
