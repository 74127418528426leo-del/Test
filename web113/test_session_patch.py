import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import session_patch as p

class SessionPatchTests(unittest.TestCase):
    def test_parallel_mode_preserves_lightdm_and_pam(self):
        source='\n\tFstab\n\tNetbase\n';out=p.patch_main(source,'parallel')
        self.assertIn('lightdm.service.d',out)
        self.assertIn('After=',out)
        self.assertIn('live-config.service',out)
        self.assertNotIn('DefaultDependencies=no',out)
        self.assertNotIn('dbus.socket.d',out)
        self.assertNotIn('runuser',out)
        self.assertIn('[ -z "${TORAM:-}" ]',out)

    def test_early_bus_mode_creates_explicit_ordering_not_root_browser(self):
        out=p.patch_main('\n\tFstab\n\tNetbase\n','earlybus')
        self.assertIn('DefaultDependencies=no',out)
        self.assertIn('dbus.socket.d',out)
        self.assertIn('dbus.service.d',out)
        self.assertIn('systemd-tmpfiles-setup.service',out)
        self.assertNotIn('firefox-esr --no-sandbox',out)

    def test_shell_injection_is_reversible_and_fallback_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'etc/systemd/system/lightdm.service.d').mkdir(parents=True)
            text=p.patch_main('\n\tFstab\n\tNetbase\n','earlybus')
            text=text.replace('[ -b /dev/mapper/p50-staged-root ]','[ -d "$rootmnt" ]')
            setup='panic(){ echo "$*" >&2; exit 55; }; Fstab(){ :; }; Netbase(){ :; }\n'
            env={**os.environ,'rootmnt':temp,'TORAM':'1'}
            r=subprocess.run(['sh','-c',setup+text],env=env,text=True,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertFalse((root/'etc/systemd/system/dbus.socket.d').exists())
            env['TORAM']=''
            r=subprocess.run(['sh','-c',setup+text],env=env,text=True,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
            for service in ('lightdm.service.d','dbus.socket.d','dbus.service.d'):
                self.assertTrue((root/'etc/systemd/system'/service/'80-v113-experiment.conf').is_file())
            r=subprocess.run(['sh','-c',setup+text],env=env,text=True,capture_output=True)
            self.assertNotEqual(r.returncode,0)

    def test_refuses_ambiguous_or_previously_patched_hooks(self):
        m='\n\tFstab\n\tNetbase\n'
        for source in ('absent',m+m,'P50_V113_SESSION_EXPERIMENT'+m):
            with self.assertRaises(ValueError):p.patch_main(source,'parallel')

if __name__=='__main__':unittest.main()
