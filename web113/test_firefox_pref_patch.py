import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import firefox_pref_patch as p

class FirefoxPreferenceTests(unittest.TestCase):
    def test_policy_changes_only_preallocation_and_is_user_changeable(self):
        for mode,key,value in [('off','dom.ipc.processPrelaunch.enabled',False),('delay','dom.ipc.processPrelaunch.delayMs',8000)]:
            raw=json.loads(p.policy(mode));self.assertIn('policies',raw)
            d=raw['policies']['Preferences']
            self.assertEqual(d,{key:{'Value':value,'Status':'user'}})
            self.assertNotIn('fission.autostart',str(d))
            self.assertNotIn('security.sandbox',str(d))
    def test_installs_only_on_staged_boot_and_respects_debian_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'usr/lib/firefox-esr').mkdir(parents=True)
            (root/'usr/share/firefox-esr/distribution').mkdir(parents=True)
            (root/'usr/lib/firefox-esr/distribution').symlink_to('../../share/firefox-esr/distribution')
            s=p.patch_main('\n\tFstab\n\tNetbase\n','off').replace('[ -b /dev/mapper/p50-staged-root ]','[ -d "$rootmnt" ]')
            wrapper='panic(){ echo "$*" >&2; exit 55; }; Fstab(){ :; }; Netbase(){ :; }\n'
            env={**os.environ,'rootmnt':temp,'TORAM':'1'}
            r=subprocess.run(['sh','-c',wrapper+s],env=env,text=True,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
            dst=root/'usr/share/firefox-esr/distribution/policies.json'
            self.assertFalse(dst.exists())
            env['TORAM']='';r=subprocess.run(['sh','-c',wrapper+s],env=env,text=True,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr);self.assertTrue(dst.exists())
            self.assertEqual(json.loads(dst.read_text()),json.loads(p.policy('off')))
            r=subprocess.run(['sh','-c',wrapper+s],env=env,text=True,capture_output=True)
            self.assertNotEqual(r.returncode,0)
    def test_checks_current_and_legacy_firefox_profile_locations(self):
        report=p.patch_migration(p.MIGRATE,'off')
        self.assertIn('/home/user/.config/mozilla/firefox/*/prefs.js',report)
        self.assertIn('/home/user/.mozilla/firefox/*/prefs.js',report)
        self.assertIn('user_pref("dom.ipc.processPrelaunch.enabled", false);',report)

    def test_invalid_or_duplicate_hooks_are_rejected(self):
        marker='\n\tFstab\n\tNetbase\n'
        for src in ('absent',marker+marker,'P50_V113_PRELAUNCH_PREF'+marker):
            with self.assertRaises(ValueError):p.patch_main(src,'off')

if __name__=='__main__':unittest.main()
