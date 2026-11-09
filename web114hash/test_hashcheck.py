import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from hashcheck import patch_source, inject_fault

SOURCE='''#!/bin/sh
actual=$(/usr/bin/sha256sum "$COPY") || fail 'copy hash failed'
actual=${actual%% *}
[ "$actual" = "$expected" ] || fail 'copied hash differs from ISO manifest'
printf 'VERIFIED\\n'
'''

class HashCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)
        self.copy=self.path/'copy'; self.copy.write_bytes(b'Puppy50 RAM copy validation')
        self.backup=self.path/'busybox'
        self.backup.write_text('#!/bin/sh\n[ "$1" = sha256sum ] || exit 55\nshift\nexec /usr/bin/sha256sum "$@"\n')
        self.backup.chmod(0o755)
    def tearDown(self): self.tmp.cleanup()
    def run_shell(self,code,expected):
        import hashlib
        if expected=='correct':expected=hashlib.sha256(self.copy.read_bytes()).hexdigest()
        return subprocess.run(['sh','-c','fail(){ echo "FAILED: $*"; exit 74; }\nemit(){ :; }\n'+code],
            env={**os.environ,'B':str(self.backup),'COPY':str(self.copy),'expected':expected},
            capture_output=True,text=True)
    def test_primary_success_and_corrupt_hash_rejected(self):
        s=patch_source(SOURCE)
        self.assertEqual(self.run_shell(s,'correct').returncode,0)
        x=self.run_shell(s,'0'*64)
        self.assertEqual(x.returncode,74);self.assertIn('copied hash differs',x.stdout);self.assertNotIn('VERIFIED',x.stdout)
    def test_unavailable_primary_uses_busybox(self):
        s=patch_source(SOURCE).replace('/usr/bin/sha256sum',str(self.path/'missing-primary'))
        x=self.run_shell(s,'correct');self.assertEqual(x.returncode,0,x.stderr);self.assertIn('VERIFIED',x.stdout)
    def test_both_engines_unavailable_fails_closed(self):
        self.backup.write_text('#!/bin/sh\nexit 71\n');self.backup.chmod(0o755)
        s=patch_source(SOURCE).replace('/usr/bin/sha256sum',str(self.path/'missing-primary'))
        x=self.run_shell(s,'correct');self.assertEqual(x.returncode,74);self.assertIn('copy hash failed',x.stdout);self.assertNotIn('VERIFIED',x.stdout)
    def test_rejects_wrong_or_repeated_input(self):
        for source in ('bad',SOURCE+SOURCE,patch_source(SOURCE)):
            with self.assertRaises(ValueError):patch_source(source)
    def test_faults_reject_wrong_or_repeated_input(self):
        for mode in ('bad_checksum','missing_primary','all_hash_unavailable'):
            with self.assertRaises(ValueError):inject_fault('unrelated',mode)

if __name__=='__main__':unittest.main()
