import importlib.util
import tempfile
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
def module(name,path):
    sp=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m

patch=module("patch81",BASE/"patch_guest_memory_probe.py")
mem=module("mem81",BASE/"analyze_memory_serial.py")

class ReadOnlyGuestMemoryTests(unittest.TestCase):
    def test_minimal_serial_line_parsed(self):
        line=("PUPPY50_V81_MEM tick=2 uptime_sec=20 total_kib=1024000 "+
              "available_kib=120000 free_kib=10000 swap_total_kib=0 "+
              "swap_free_kib=0 anon_kib=505000 shmem_kib=900 oom_kill=0 "+
              "psi_some_avg10=2.54 psi_full_avg10=0.12 "+
              "browser_processes=6 browser_VmRSS_sum_kib=700000\n")
        records=mem.parse(line)
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]["available_kib"],120000)
        self.assertEqual(records[0]["psi_some_avg10"],2.54)
    def test_missing_values_not_fabricated(self):
        self.assertEqual(mem.parse("PUPPY50_V81_MEM tick=1"),[])
    def test_never_patch_host_or_non_disposable_root(self):
        with self.assertRaises(ValueError):patch.patch(Path("/"))
    def test_disposable_only_preserves_Xorg_and_nonroot_Firefox(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/"output/rootfs"
            launch=root/"usr/local/bin/puppy50-web-launch"
            ca=root/"etc/ssl/certs/ca-certificates.crt"
            ff=root/"usr/lib/firefox-esr"
            for p in (launch,ca):p.parent.mkdir(parents=True,exist_ok=True)
            ff.mkdir(parents=True)
            launch.write_text("#!/bin/sh\n"+patch.ANCHOR+"\nfirefox-esr\n")
            ca.write_bytes(b"test ca")
            res=patch.patch(root)
            self.assertTrue(res["source_v78_CA_bundle_unchanged"])
            self.assertIn(patch.LINE,launch.read_text())
            self.assertIn("firefox-esr",launch.read_text())
            with self.assertRaises(ValueError):patch.patch(root)
    def test_no_sandbox_or_network_setting_changes_in_probe(self):
        src=(BASE/"guest_memory_probe.sh").read_text()
        self.assertIn("/proc/meminfo",src)
        self.assertIn("/proc/pressure/memory",src)
        for forbidden in ("--insecure","MOZ_DISABLE_CONTENT_SANDBOX","sysctl -w","swapoff","ip route add","iptables"):
            self.assertNotIn(forbidden,src)

if __name__=="__main__":unittest.main()
