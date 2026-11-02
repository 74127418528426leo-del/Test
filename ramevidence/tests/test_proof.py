"""Conservative proof parser tests with fully synthetic logs (not VM success)."""
import importlib.util
import pathlib
import unittest

PATH=pathlib.Path(__file__).resolve().parents[1] / "check_proof.py"
spec=importlib.util.spec_from_file_location("check_proof",PATH)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE="""PUPPY50_WEB_V45_RAM_COPY_COMPLETE bytes=100000
PUPPY50_WEB_V45_BOOT_MEDIA_UNMOUNTED
PUPPY50_WEB_V45_SWITCH_ROOT_RAM_ONLY
PUPPY50_WEB_V45_FIREFOX_REQUESTED
PUPPY50_RAM_PROBE_BEGIN
PUPPY50_RAM_PROBE_VERSION=1
MOUNT source=overlay target=/ fstype=overlay
MOUNT source=tmpfs target=/.web-ram fstype=tmpfs
MOUNT source=/dev/loop0 target=/.web-lower fstype=squashfs
MOUNT source=tmpfs target=/.web-rw fstype=tmpfs
RAM_IMAGE_PATH=/.web-ram/webroot.sfs
RAM_IMAGE_BYTES=100000
LOOP_BACKING device=loop0 path=/.web-ram/webroot.sfs
MEMINFO key=MemTotal: kib=376000
MEMINFO key=SwapTotal: kib=0
PUPPY50_RAM_PROBE_END
"""

class ProofTests(unittest.TestCase):
    def test_complete_synthetic_proof_accepts_mount_and_external_ejection(self):
        v=module.evaluate(BASE,{"media_ejection_verified":True})
        self.assertTrue(v["strict_ram_only_proof_complete"])
        self.assertFalse(v["interactive_web_browser_proven"])
        self.assertEqual(v["ram_mib_kernel_reported"],367.19)

    def test_missing_external_qemu_proof_is_fail_closed(self):
        self.assertFalse(module.evaluate(BASE)["strict_ram_only_proof_complete"])

    def test_legacy_markers_alone_are_never_proof(self):
        self.assertFalse(module.evaluate("PUPPY50_WEB_V45_RAM_COPY_COMPLETE bytes=100000")["guest_ram_only_verification"])

    def test_loop_source_on_unverified_old_path_is_not_proof(self):
        unsafe=BASE.replace("/.web-ram/webroot.sfs\nMEMINFO","/ram/webroot.sfs\nMEMINFO")
        self.assertFalse(module.evaluate(unsafe,{"media_ejection_verified":True})["strict_ram_only_proof_complete"])

    def test_disk_swap_disqualifies_ram_only(self):
        unsafe=BASE.replace("MEMINFO key=SwapTotal: kib=0","MEMINFO key=SwapTotal: kib=50000\nSWAP_DEVICE path=/dev/sda1 type=partition size_kib=50000 used_kib=0")
        self.assertFalse(module.evaluate(unsafe,{"media_ejection_verified":True})["strict_ram_only_proof_complete"])

    def test_unreported_swap_disqualifies_ram_only(self):
        unsafe=BASE.replace("SwapTotal: kib=0","SwapTotal: kib=50000")
        self.assertTrue(module.evaluate(unsafe)["swap_enabled_but_unattributed"])
        self.assertFalse(module.evaluate(unsafe,{"media_ejection_verified":True})["strict_ram_only_proof_complete"])

    def test_still_mounted_cd_is_failure(self):
        unsafe=BASE.replace("PUPPY50_RAM_PROBE_END","MOUNT source=/dev/sr0 target=/media fstype=iso9660\nPUPPY50_RAM_PROBE_END")
        self.assertFalse(module.evaluate(unsafe,{"media_ejection_verified":True})["strict_ram_only_proof_complete"])

if __name__=="__main__":
    unittest.main()
