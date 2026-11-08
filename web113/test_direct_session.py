import unittest
from direct_session import patch_main, patch_migration

class DirectSessionTests(unittest.TestCase):
    def test_main_installs_only_in_fast_live_overlay(self):
        source='pre\n\tFstab\n\tNetbase\npost'
        result=patch_main(source)
        self.assertIn('if [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then',result)
        self.assertIn('PAMName=login',result)
        self.assertIn('User=user',result)
        self.assertIn('ExecStartPre=+/usr/local/sbin/puppy50-prepare-session',result)
        self.assertIn('ExecStart=/usr/bin/startx /usr/bin/dbus-run-session /usr/bin/openbox-session',result)
        self.assertIn('TTYPath=/dev/tty1',result)
        self.assertIn('/lib/systemd/system/lightdm.service',result)
        self.assertIn('\n\tFstab\n\tNetbase\n',result)
    def test_rejects_missing_duplicate_and_previously_patched_hook(self):
        for source in ('oops','\n\tFstab\n\tNetbase\n\n\tFstab\n\tNetbase\n','P50_V113_DIRECT_X\n\tFstab\n\tNetbase\n'):
            with self.assertRaises(ValueError):patch_main(source)
    def test_diagnostic_does_not_change_migration_marker_and_checks_nonroot_session(self):
        source='first\n"$B" sleep 8\nemit P50_STAGE_START\nlast\n'
        result=patch_migration(source)
        self.assertIn('P50_V113_DIRECT_UI_OK',result)
        self.assertIn("pgrep -u user -f '[f]irefox'",result)
        self.assertIn('pgrep -u user -x nm-applet',result)
        self.assertIn('PAMName',result)
        self.assertIn('"$B" sleep 8\nemit P50_STAGE_START\n',result)
        with self.assertRaises(ValueError):patch_migration(result)

if __name__=='__main__':unittest.main()
