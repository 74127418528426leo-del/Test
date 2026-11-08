import unittest

import autostart_patch


class AutostartPatchTests(unittest.TestCase):
    def test_browser_and_usb_status_start_before_delayed_controls(self):
        s = autostart_patch.FAST_AUTOSTART
        self.assertLess(s.index('/run/p50-stage/tools/p50-status'), s.index('sleep 3'))
        self.assertLess(s.index('firefox-esr file:///usr/share/puppy50web/index.html'), s.index('sleep 3'))
        for name in ('tint2 ', 'nm-applet ', 'polkit-mate-authentication-agent-1'):
            self.assertGreater(s.index(name), s.index('sleep 3'))

    def test_existing_status_hook_is_preserved_and_patch_is_unique(self):
        source = 'before\n' + autostart_patch.STATUS_LINE + '\nafter\n'
        result = autostart_patch.patch_main(source)
        self.assertIn(autostart_patch.STATUS_LINE, result)
        self.assertIn('P50_V110_FAST_AUTOSTART', result)
        with self.assertRaises(ValueError):
            autostart_patch.patch_main(result)
        with self.assertRaises(ValueError):
            autostart_patch.patch_main('missing')

    def test_migration_reports_that_browser_and_network_controls_are_running(self):
        source = '"$B" sleep 8\nemit P50_STAGE_START\n'
        result = autostart_patch.patch_migration(source)
        self.assertIn('P50_V110_UI_OK', result)
        self.assertIn('P50_V110_UI_MISSING', result)
        self.assertIn(source, result)


if __name__ == '__main__':
    unittest.main()
