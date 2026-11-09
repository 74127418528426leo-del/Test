import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from ram_patch import memory_retry_function
from ram_faults import inject_retry_fault, inject_bad_checksum

class RamFaultInjectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.busybox=self.root/'busybox'
        self.busybox.write_text('#!/bin/sh\ncase "$1" in awk) printf "9999999\\n";; sleep) :;; *) exit 2;; esac\n');self.busybox.chmod(0o755)
    def tearDown(self):self.tmp.cleanup()
    def run_test(self,body):return subprocess.run(['sh','-c',body],capture_output=True,text=True,env={**os.environ,'B':str(self.busybox)})
    def test_recovery_only_after_two_guard_failures(self):
        f=inject_retry_fault(memory_retry_function(),'recover')
        r=self.run_test(f+'\nneed_k=100\nemit(){ :; }\np50_wait_memory; printf "%s %s\\n" "$?" "$p50_attempt"\n')
        self.assertEqual(r.stdout,'0 3\n')
    def test_exhaustion_never_passes_even_with_high_actual_memory(self):
        f=inject_retry_fault(memory_retry_function(),'exhaust')
        r=self.run_test(f+'\nneed_k=100\nemit(){ :; }\np50_wait_memory; printf "%s %s\\n" "$?" "$p50_attempt"\n')
        self.assertEqual(r.stdout,'1 10\n')
    def test_bad_checksum_injection_preserves_validation_and_forces_mismatch(self):
        source='''expected=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
[ "${#expected}" -eq 64 ] || fail 'source checksum missing or ambiguous'
[ "$expected" = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ] || exit 17
'''
        r=self.run_test("fail(){ exit 43; }\n"+inject_bad_checksum(source))
        self.assertEqual(r.returncode,17)
    def test_rejects_wrong_or_duplicated_targets(self):
        with self.assertRaises(ValueError):inject_retry_fault('unexpected','recover')
        with self.assertRaises(ValueError):inject_retry_fault(memory_retry_function(),'unknown')
        with self.assertRaises(ValueError):inject_bad_checksum('unexpected')

if __name__=='__main__':unittest.main()
