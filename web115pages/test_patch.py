import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from patch import patch_main

MARK='\n\tFstab\n\tNetbase\n'

class HotProbePatchTests(unittest.TestCase):
    def test_only_fast_path_installs_profile_unit(self):
        text=patch_main('#!/bin/sh'+MARK)
        self.assertIn('[ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]',text)
        self.assertIn('P50_HOT_PROBE_SERVICE',text)
        self.assertIn('Before=sysinit.target',text)
        self.assertEqual(subprocess.run(['sh','-n'],input=text,text=True,capture_output=True).returncode,0)
    def test_refuses_unexpected_or_repeated_marker(self):
        for src in ('x',MARK+MARK,patch_main(MARK)):
            with self.assertRaises(ValueError):patch_main(src)

if __name__=='__main__':unittest.main()
