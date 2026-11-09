import hashlib
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from clean_patch import patch_source

BASE='''#!/bin/sh
actual=$("$B" sha256sum "$COPY") || fail 'copy hash failed'
actual=${actual%% *}
[ "$actual" = "$expected" ] || fail 'copied hash differs from ISO manifest'
printf 'VERIFIED\\n'
'''

class CleanPatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.copy=self.root/'root.squashfs';self.copy.write_bytes(b'complete destination bytes')
        self.busybox=self.root/'busybox'
        self.busybox.write_text('#!/bin/sh\n[ "$1" = sha256sum ] || exit 2\nshift\nexec /usr/bin/sha256sum "$@"\n');self.busybox.chmod(0o755)
    def tearDown(self):self.tmp.cleanup()
    def run_shell(self,script,digest=None):
        if digest is None:digest=hashlib.sha256(self.copy.read_bytes()).hexdigest()
        return subprocess.run(['sh','-c',"fail(){ echo \"FAILED: $*\"; exit 74; }\n"+script],env={**os.environ,'B':str(self.busybox),'COPY':str(self.copy),'expected':digest},capture_output=True,text=True)
    def test_succeeds_on_fast_hash_and_rejects_wrong_hash(self):
        s=patch_source(BASE);self.assertEqual(self.run_shell(s).returncode,0)
        r=self.run_shell(s,'0'*64);self.assertEqual(r.returncode,74);self.assertIn('copied hash differs',r.stdout)
    def test_missing_fast_hash_falls_back_to_original_busybox(self):
        s=patch_source(BASE).replace('/usr/bin/sha256sum',str(self.root/'missing'))
        r=self.run_shell(s);self.assertEqual(r.returncode,0,r.stderr);self.assertIn('VERIFIED',r.stdout)
    def test_both_unavailable_keep_the_copy_unverified(self):
        self.busybox.write_text('#!/bin/sh\nexit 1\n');self.busybox.chmod(0o755)
        s=patch_source(BASE).replace('/usr/bin/sha256sum',str(self.root/'missing'))
        r=self.run_shell(s);self.assertEqual(r.returncode,74);self.assertIn('copy hash failed',r.stdout);self.assertNotIn('VERIFIED',r.stdout)
    def test_only_expected_line_is_replaced(self):
        s=patch_source(BASE)
        self.assertEqual(s.replace('''if actual=$(/usr/bin/sha256sum "$COPY"); then
    :
else
    actual=$("$B" sha256sum "$COPY") || fail 'copy hash failed'
fi''','''actual=$("$B" sha256sum "$COPY") || fail 'copy hash failed' '''.rstrip()),BASE)
        for bad in ('missing',BASE+BASE,s):
            with self.assertRaises(ValueError):patch_source(bad)

if __name__=='__main__':unittest.main()
