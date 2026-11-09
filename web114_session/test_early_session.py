import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from early_session import patch_main,patch_migration

SOURCE='#!/bin/sh\n\tFstab\n\tNetbase\n'
LOGIND='[Unit]\nWants=user.slice modprobe@drm.service\nAfter=nss-user-lookup.target user.slice modprobe@drm.service\n[Service]\nExecStart=/usr/lib/systemd/systemd-logind\n'
class EarlySessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        base=self.root/'usr/lib/systemd/system/systemd-logind.service';base.parent.mkdir(parents=True);base.write_text(LOGIND)
        link=self.root/'etc/systemd/system/display-manager.service';link.parent.mkdir(parents=True);link.symlink_to('/lib/systemd/system/lightdm.service')
    def tearDown(self):self.tmp.cleanup()
    def run_script(self,toram=''):
        source=patch_main(SOURCE)
        pre='''Fstab(){ :; }; Netbase(){ :; }; panic(){ echo "$*" >&2; exit 42; }
function [ { if test "$#" -eq 3 && test "$1" = "-b" && test "$2" = "/dev/mapper/p50-staged-root"; then return 0; fi; builtin [ "$@"; }
'''
        return subprocess.run(['bash','-c',pre+source],env={**os.environ,'rootmnt':str(self.root),'TORAM':toram},capture_output=True,text=True)
    def test_fast_boot_prepares_nonroot_session_and_early_bus(self):
        r=self.run_script();self.assertEqual(r.returncode,0,r.stderr)
        sys=self.root/'etc/systemd/system';dm=(sys/'display-manager.service').read_text()
        self.assertIn('User=user',dm);self.assertIn('PAMName=login',dm)
        self.assertIn('DefaultDependencies=no',dm);self.assertNotIn('After=live-config.service',dm)
        prep=(sys/'p50-user-preparation.service').read_text();self.assertIn('Before=sysinit.target',prep)
        self.assertNotIn('After=live-config.service',prep)
        for unit in ('dbus.socket','dbus.service','systemd-logind.service'):
            override=(sys/(unit+'.d')/'80-v114-early.conf').read_text()
            self.assertIn('DefaultDependencies=no',override);self.assertIn('Before=sysinit.target',override)
        logind=(sys/'systemd-logind.service').read_text();self.assertIn('Wants=user.slice modprobe@drm.service',logind);self.assertNotIn('After=nss-user-lookup.target user.slice modprobe@drm.service',logind)
        self.assertEqual(os.readlink(sys/'lightdm.service'),'/dev/null')
    def test_fallback_does_not_install_early_units(self):
        r=self.run_script(toram='1');self.assertEqual(r.returncode,0,r.stderr)
        self.assertFalse((self.root/'etc/systemd/system/p50-user-preparation.service').exists())
        self.assertEqual(os.readlink(self.root/'etc/systemd/system/display-manager.service'),'/lib/systemd/system/lightdm.service')
    def test_rejects_unexpected_logind_unit_without_overwriting(self):
        path=self.root/'usr/lib/systemd/system/systemd-logind.service';path.write_text('[Unit]\nunexpected\n')
        r=self.run_script();self.assertEqual(r.returncode,42)
        self.assertFalse((self.root/'etc/systemd/system/systemd-logind.service').exists())
    def test_rejects_missing_and_duplicate_hooks(self):
        with self.assertRaises(ValueError):patch_main('bad')
        with self.assertRaises(ValueError):patch_main(patch_main(SOURCE))
        with self.assertRaises(ValueError):patch_migration('bad')

if __name__=='__main__':unittest.main()
