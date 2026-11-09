import hashlib
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from ram_patch import patch_hash, memory_retry_function

SOURCE='''actual=$("$B" sha256sum "$COPY") || fail 'copy hash failed'
actual=${actual%% *}
[ "$actual" = "$expected" ] || fail 'copied hash differs from ISO manifest'
printf 'VERIFIED\\n'
'''
class RamPatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.fake=self.root/'busybox'
        self.fake.write_text('''#!/bin/sh
case "$1" in
sha256sum) shift; exec /usr/bin/sha256sum "$@";;
awk) n=$(cat "$STATE" 2>/dev/null || printf 0); n=$((n+1)); printf %s "$n" >"$STATE"; sed -n "${n}p" "$VALUES";;
sleep) :;;
*) exit 2;;
esac
''');self.fake.chmod(0o755)
    def tearDown(self):self.tmp.cleanup()
    def shell(self,text,**env):
        return subprocess.run(['sh','-c',text],capture_output=True,text=True,env={**os.environ,'B':str(self.fake),**env})
    def test_engines_accept_correct_destination_and_reject_corruption(self):
        copy=self.root/'copy';copy.write_bytes(b'actual verified destination bytes')
        digest=hashlib.sha256(copy.read_bytes()).hexdigest()
        for mode in ('profile','openssl','coreutils'):
            with self.subTest(mode=mode):
                script='fail(){ exit 74; }\n'+patch_hash(SOURCE,mode)
                good=self.shell('set -x\n'+script,COPY=str(copy),expected=digest)
                self.assertEqual(good.returncode,0,good.stderr);self.assertEqual(good.stdout,'VERIFIED\n')
                engine={'profile':'sha256sum','openssl':'/usr/bin/openssl dgst -sha256 -r','coreutils':'/usr/bin/sha256sum'}[mode]
                self.assertIn(engine,good.stderr)
                bad=self.shell(script,COPY=str(copy),expected='0'*64)
                self.assertEqual(bad.returncode,74);self.assertNotIn('VERIFIED',bad.stdout)
    def test_retry_waits_for_original_threshold_and_stops_immediately_when_met(self):
        values=self.root/'values';values.write_text('393315\n393316\n999999\n');state=self.root/'state'
        shell=memory_retry_function()+'\nneed_k=100\nemit(){ :; }\np50_wait_memory\nprintf "status=%s memory=%s\\n" "$?" "$mem_k"\n'
        r=self.shell(shell,STATE=str(state),VALUES=str(values));self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(r.stdout,'status=0 memory=393316\n');self.assertEqual(state.read_text(),'2')
    def test_retry_fails_closed_after_bounded_wait_or_invalid_sample(self):
        values=self.root/'values';state=self.root/'state';values.write_text('100\n'*10)
        shell=memory_retry_function()+'\nneed_k=100\nemit(){ :; }\np50_wait_memory\nprintf "status=%s\\n" "$?"\n'
        r=self.shell(shell,STATE=str(state),VALUES=str(values));self.assertEqual(r.stdout,'status=1\n');self.assertEqual(state.read_text(),'10')
        state.unlink();values.write_text('invalid\n')
        r=self.shell(shell,STATE=str(state),VALUES=str(values));self.assertEqual(r.stdout,'status=2\n');self.assertEqual(state.read_text(),'1')
    def test_rejects_missing_or_duplicated_hash_command(self):
        for text in ('other',SOURCE+SOURCE):
            with self.assertRaises(ValueError):patch_hash(text,'openssl')

if __name__=='__main__':unittest.main()
