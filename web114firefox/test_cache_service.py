import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from cache_service import patch_main, CAPTURE


class CacheServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, toram=''):
        source = patch_main('#!/bin/sh\n\tFstab\n\tNetbase\n')
        pre = '''Fstab(){ :; }; Netbase(){ :; }; panic(){ echo "$*" >&2; exit 42; }
function [ { if test "$#" -eq 3 && test "$1" = "-b" && test "$2" = "/dev/mapper/p50-staged-root"; then return 0; fi; builtin [ "$@"; }
'''
        return subprocess.run(['bash', '-c', pre + source], env={**os.environ, 'rootmnt':str(self.root), 'TORAM':toram}, capture_output=True, text=True)

    def test_installs_separate_unit_and_enables_it_on_fast_boot(self):
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        unit = self.root/'etc/systemd/system/p50-cache-capture.service'
        link = self.root/'etc/systemd/system/graphical.target.wants/p50-cache-capture.service'
        self.assertIn('ExecStart=/bin/sh /run/p50-stage/tools/p50-cache-capture', unit.read_text())
        self.assertEqual(os.readlink(link), '../p50-cache-capture.service')

    def test_full_ram_fallback_is_untouched(self):
        self.assertEqual(self.run_hook('1').returncode, 0)
        self.assertFalse((self.root/'etc').exists())

    def test_capture_is_valid_bounded_shell_and_rejects_bad_hook(self):
        self.assertEqual(subprocess.run(['sh', '-n'], input=CAPTURE, text=True).returncode, 0)
        self.assertIn(' -lt 220 ', CAPTURE)
        for value in ('wrong', '\n\tFstab\n\tNetbase\n'*2):
            with self.assertRaises(ValueError):
                patch_main(value)
