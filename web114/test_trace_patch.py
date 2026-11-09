import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from trace_patch import DIAGNOSTIC, patch_main, patch_migration

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
    def test_diagnostic_migration_keeps_original_marker_and_is_valid_shell(self):
        source='#!/bin/sh\n"$B" sleep 8\nemit P50_STAGE_START\n'
        patched=patch_migration(source)
        self.assertIn('P50_V114_DIAG_BEGIN',patched)
        self.assertIn('P50_V114_DIAG_END',patched)
        self.assertIn('"$B" sleep 8\nemit P50_STAGE_START\n',patched)
        result=subprocess.run(['sh','-n'],input=patched,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_diagnostic_migration_rejects_missing_duplicate_or_prepatched_marker(self):
        marker='"$B" sleep 8\nemit P50_STAGE_START\n'
        for source in ('nothing',marker+marker,patch_migration(marker)):
            with self.assertRaises(ValueError):patch_migration(source)
    def test_diagnostics_finish_even_when_a_file_or_service_is_missing(self):
        target=self.root/'diagnostics.txt'
        script='set -e\nls(){ return 2; }\nsystemctl(){ return 3; }\njournalctl(){ return 4; }\nB=/bin/true\n'
        script+=DIAGNOSTIC.replace('>/dev/ttyS0','>"$TEST_DIAG"')+'\nwait\n'
        result=subprocess.run(['sh','-c',script],env={**os.environ,'TEST_DIAG':str(target)},capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('P50_V114_DIAG_END',target.read_text())

if __name__=='__main__':unittest.main()
