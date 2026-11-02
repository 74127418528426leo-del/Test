"""Offline regression checks: staging-root only; never invoke host OpenRC."""
import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "wire_openrc_services.sh"

class OpenRCWiringTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "etc/init.d").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def install(self, *names):
        for name in names:
            (self.root / "etc/init.d" / name).write_text("#!/bin/sh\n")

    def runwire(self):
        return subprocess.run(["sh", str(SCRIPT), str(self.root)], capture_output=True, text=True)

    def test_correct_levels_and_relative_links(self):
        self.install("udev", "udev-trigger", "udev-settle", "udev-postmount", "dbus", "dhcpcd")
        r = self.runwire()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for name, level in [("udev", "sysinit"), ("udev-trigger", "sysinit"),
                            ("udev-settle", "sysinit"), ("udev-postmount", "default"),
                            ("dbus", "default"), ("dhcpcd", "default")]:
            link = self.root / "etc/runlevels" / level / name
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.readlink(), pathlib.Path("../../init.d") / name)
            self.assertTrue(link.exists(), f"broken link: {link}")
        self.assertEqual(self.runwire().returncode, 0)

    def test_missing_optional_services_are_skipped(self):
        self.install("dbus")
        r = self.runwire()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.root / "etc/runlevels/default/dbus").exists())
        self.assertFalse((self.root / "etc/runlevels/sysinit/udev").is_symlink())

    def test_refuses_to_overwrite_non_symlink(self):
        self.install("dhcpcd")
        p = self.root / "etc/runlevels/default/dhcpcd"
        p.parent.mkdir(parents=True)
        p.write_text("preserve")
        r = self.runwire()
        self.assertEqual(r.returncode, 3)
        self.assertEqual(p.read_text(), "preserve")

if __name__ == "__main__":
    unittest.main()
