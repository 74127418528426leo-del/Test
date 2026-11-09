import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from trace_patch import patch_main

SOURCE='#!/bin/sh\n\tFstab\n\tNetbase\n'
class TracePatchTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def run_hook(self,toram=''):
        source=patch_main(SOURCE)
        pre='''Fstab(){ :; }; Netbase(){ :; }; panic(){ echo "$*" >&2; exit 42; }
function [ { if test "$#" -eq 3 && test "$1" = "-b" && test "$2" = "/dev/mapper/p50-staged-root"; then return 0; fi; builtin [ "$@"; }
'''
        return subprocess.run(['bash','-c',pre+source],env={**os.environ,'rootmnt':str(self.root),'TORAM':toram},capture_output=True,text=True)
    def test_fast_path_creates_trace_unit_and_enables_it(self):
        r=self.run_hook();self.assertEqual(r.returncode,0,r.stderr)
        unit=self.root/'etc/systemd/system/p50-open-trace.service';link=self.root/'etc/systemd/system/sysinit.target.wants/p50-open-trace.service'
        self.assertTrue(unit.is_file());self.assertTrue(link.is_symlink());self.assertEqual(os.readlink(link),'../p50-open-trace.service')
    def test_full_ram_fallback_is_untouched(self):
        r=self.run_hook(toram='1');self.assertEqual(r.returncode,0,r.stderr)
        self.assertFalse((self.root/'etc').exists())
    def test_refuses_to_overwrite_existing_unit(self):
        unit=self.root/'etc/systemd/system/p50-open-trace.service';unit.parent.mkdir(parents=True);unit.write_text('existing')
        r=self.run_hook();self.assertEqual(r.returncode,42);self.assertEqual(unit.read_text(),'existing')
    def test_rejects_wrong_or_already_patched_input(self):
        with self.assertRaises(ValueError):patch_main('different')
        with self.assertRaises(ValueError):patch_main(patch_main(SOURCE))

if __name__=='__main__':unittest.main()
