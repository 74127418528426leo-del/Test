import subprocess,unittest
from prefetch_patch import patch_main
M='\n\tFstab\n\tNetbase\n'

class PrefetchPatchTests(unittest.TestCase):
    def test_only_fast_path_starts_nonblocking_prefetch(self):
        s=patch_main('#!/bin/sh'+M)
        self.assertIn('[ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]',s)
        self.assertIn('Type=simple',s)
        self.assertEqual(subprocess.run(['sh','-n'],input=s,text=True,capture_output=True).returncode,0)
    def test_rejects_missing_duplicate_or_previously_patched_hook(self):
        for s in ('x',M+M,patch_main(M)):
            with self.assertRaises(ValueError):patch_main(s)

if __name__=='__main__':unittest.main()
