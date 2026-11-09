import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from standard_session import patch_main, patch_migration

SOURCE='#!/bin/sh\n\tFstab\n\tNetbase\n'
LOGIND='[Unit]\nWants=user.slice modprobe@drm.service\nAfter=nss-user-lookup.target user.slice modprobe@drm.service\n[Service]\nExecStart=/usr/lib/systemd/systemd-logind\n'

class StandardSessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        unit=self.root/'usr/lib/systemd/system/systemd-logind.service';unit.parent.mkdir(parents=True);unit.write_text(LOGIND)
        display=self.root/'etc/systemd/system/display-manager.service';display.parent.mkdir(parents=True);display.symlink_to('/lib/systemd/system/lightdm.service')
        (self.root/'etc/X11/Xsession.d').mkdir(parents=True)
    def tearDown(self):self.tmp.cleanup()
    def run_hook(self,toram=''):
        source=patch_main(SOURCE)
        sh=subprocess.run(['sh','-n'],input=source,text=True,capture_output=True)
        self.assertEqual(sh.returncode,0,sh.stderr)
        pre='''Fstab(){ :; }; Netbase(){ :; }; panic(){ echo "$*" >&2; exit 42; }
function [ { if test "$#" -eq 3 && test "$1" = "-b" && test "$2" = "/dev/mapper/p50-staged-root"; then return 0; fi; builtin [ "$@"; }
'''
        return subprocess.run(['bash','-c',pre+source],env={**os.environ,'rootmnt':str(self.root),'TORAM':toram},capture_output=True,text=True)
    def test_early_session_keeps_drm_and_executes_debian_xsession(self):
        result=self.run_hook();self.assertEqual(result.returncode,0,result.stderr)
        sys=self.root/'etc/systemd/system'
        self.assertEqual((sys/'systemd-logind.service').read_text(),LOGIND)
        display=(sys/'display-manager.service').read_text()
        self.assertIn('User=user',display);self.assertIn('PAMName=login',display)
        self.assertIn('/usr/bin/dbus-run-session /etc/X11/Xsession /usr/bin/openbox-session',display)
        self.assertIn('P50_V114_XSESSION_HOOK_RAN',(self.root/'etc/X11/Xsession.d/89puppy50-probe').read_text())
    def test_original_fallback_session_is_untouched(self):
        result=self.run_hook('1');self.assertEqual(result.returncode,0,result.stderr)
        sys=self.root/'etc/systemd/system'
        self.assertFalse((sys/'systemd-logind.service').exists())
        self.assertEqual(os.readlink(sys/'display-manager.service'),'/lib/systemd/system/lightdm.service')
    def test_unexpected_or_duplicate_hook_fails(self):
        for source in ('bad',patch_main(SOURCE)):
            with self.assertRaises(ValueError):patch_main(source)
    def test_delayed_report_checks_xsession_marker_and_keeps_migration_hook(self):
        marker='"$B" sleep 8\nemit P50_STAGE_START\n'
        result=patch_migration('#!/bin/sh\n'+marker)
        self.assertIn('P50_V114_XSESSION_HOOK_OK',result)
        self.assertIn(marker,result)
        self.assertEqual(subprocess.run(['sh','-n'],input=result,text=True).returncode,0)

if __name__=='__main__':unittest.main()
