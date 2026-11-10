import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from font_cache_clean import HOOK,MARKER,patch_main

class OptionalCacheTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.src=self.root/'source';self.src.mkdir();(self.src/'aaa-le64.cache-9').write_bytes(b'cache-a');(self.src/'bbb-le64.cache-9').write_bytes(b'cache-b')
  self.dest=self.root/'guest/var/cache/fontconfig';self.dest.mkdir(parents=True);(self.dest/'CACHEDIR.TAG').write_bytes(b'original')
 def tearDown(self):self.tmp.cleanup()
 def run_hook(self,toram='',extra=''):
  hook=HOOK.replace('p50_fc_source=/usr/lib/p50-fontcache','p50_fc_source="$TEST_SOURCE"')
  pre='''set -e
function [ { if test "$#" -eq 3 && test "$1" = "-b" && test "$2" = "/dev/mapper/p50-staged-root"; then return 0; fi; builtin [ "$@"; }
'''
  return subprocess.run(['bash','-c',pre+extra+hook],env={**os.environ,'TORAM':toram,'rootmnt':str(self.root/'guest'),'TEST_SOURCE':str(self.src)},text=True,capture_output=True)
 def assert_no_staging(self):self.assertFalse(list(self.dest.glob('.p50-fontcache-*')))
 def test_valid_cache_installs_exact_files(self):
  r=self.run_hook();self.assertEqual(r.returncode,0,r.stderr)
  self.assertEqual((self.dest/'aaa-le64.cache-9').read_bytes(),b'cache-a');self.assertEqual((self.dest/'bbb-le64.cache-9').read_bytes(),b'cache-b');self.assertEqual((self.dest/'CACHEDIR.TAG').read_bytes(),b'original');self.assert_no_staging()
 def test_full_ram_fallback_and_missing_source_are_nonfatal(self):
  self.assertEqual(self.run_hook('1').returncode,0);self.assertFalse((self.dest/'aaa-le64.cache-9').exists())
  for p in self.src.iterdir():p.unlink()
  self.src.rmdir();self.assertEqual(self.run_hook().returncode,0);self.assert_no_staging()
 def test_source_or_destination_symlink_is_not_followed(self):
  (self.src/'aaa-le64.cache-9').unlink();(self.src/'aaa-le64.cache-9').symlink_to(self.root/'outside')
  self.assertEqual(self.run_hook().returncode,0);self.assertFalse((self.dest/'bbb-le64.cache-9').exists())
  (self.src/'aaa-le64.cache-9').unlink();(self.src/'aaa-le64.cache-9').write_bytes(b'cache-a')
  (self.dest/'CACHEDIR.TAG').unlink();self.dest.rmdir();self.dest.symlink_to(self.src,target_is_directory=True)
  self.assertEqual(self.run_hook().returncode,0);self.assertFalse((self.src/'CACHEDIR.TAG').exists())
 def test_symlinked_cache_parent_is_not_followed(self):
  parent=self.root/'guest/var/cache';external=self.root/'external';shutil.move(str(parent),external);parent.symlink_to(external,target_is_directory=True)
  self.assertEqual(self.run_hook().returncode,0)
  self.assertFalse((external/'fontconfig/aaa-le64.cache-9').exists())
  self.assertFalse((external/'fontconfig/bbb-le64.cache-9').exists())
 def test_existing_cache_and_symlink_are_never_overwritten(self):
  (self.dest/'aaa-le64.cache-9').write_bytes(b'existing');(self.dest/'bbb-le64.cache-9').symlink_to(self.root/'outside')
  self.assertEqual(self.run_hook().returncode,0);self.assertEqual((self.dest/'aaa-le64.cache-9').read_bytes(),b'existing');self.assertTrue((self.dest/'bbb-le64.cache-9').is_symlink());self.assertFalse((self.root/'outside').exists());self.assert_no_staging()
 def test_failed_copy_discards_staged_files_and_continues_boot(self):
  extra='cp(){ /bin/cp "$@"; return 1; }\n'
  self.assertEqual(self.run_hook(extra=extra).returncode,0);self.assertFalse((self.dest/'aaa-le64.cache-9').exists());self.assertFalse((self.dest/'bbb-le64.cache-9').exists());self.assert_no_staging()
 def test_failed_move_leaves_only_complete_individual_files(self):
  extra='mv(){ case "$*" in *bbb-le64.cache-9*) return 1;; *) /bin/mv "$@";; esac; }\n'
  self.assertEqual(self.run_hook(extra=extra).returncode,0);self.assertEqual((self.dest/'aaa-le64.cache-9').read_bytes(),b'cache-a');self.assertFalse((self.dest/'bbb-le64.cache-9').exists());self.assert_no_staging()
 def test_single_guarded_insertion_and_valid_shell(self):
  result=patch_main('#!/bin/sh'+MARKER)
  self.assertEqual(subprocess.run(['sh','-n'],input=result,text=True).returncode,0)
  for bad in ('nothing',MARKER+MARKER,result):
   with self.assertRaises(ValueError):patch_main(bad)
if __name__=='__main__':unittest.main()
