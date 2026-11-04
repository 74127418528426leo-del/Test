import importlib.util,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"prune_intel_live.py"
spec=importlib.util.spec_from_file_location("intel",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class T(unittest.TestCase):
 def root(self,r):
  for name in m.PRESERVE+["etc/systemd/system/puppy50-memory-diagnostics.service"]:
   p=r/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text("ORIGINAL "+name)
  for name in m.GPU_FIRMWARE+["usr/lib/firmware/i915","usr/lib/firmware/iwlwifi","usr/lib/firmware/rtw89"]:
   p=r/name;p.mkdir(parents=True,exist_ok=True);(p/"fw.bin").write_bytes(b"video"*100)
  for name in ["boot/vmlinuz-6.12.115","boot/initrd.img-6.12.115","boot/leave-me-alone"]:
   p=r/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b"data")
  return r
 def test_selective_gpu_only_and_boot_dupes(self):
  with tempfile.TemporaryDirectory() as d:
   root=self.root(Path(d))
   before={n:(root/n).read_bytes() for n in m.PRESERVE}
   x=m.patch(root)
   self.assertEqual(before,{n:(root/n).read_bytes() for n in m.PRESERVE})
   self.assertTrue(x["intel_i915_firmware_preserved"])
   self.assertTrue((root/"usr/lib/firmware/iwlwifi/fw.bin").is_file())
   self.assertTrue((root/"usr/lib/firmware/rtw89/fw.bin").is_file())
   self.assertTrue((root/"boot/leave-me-alone").is_file())
   self.assertFalse((root/"boot/vmlinuz-6.12.115").exists())
   self.assertFalse((root/"boot/initrd.img-6.12.115").exists())
   self.assertFalse((root/"usr/lib/firmware/amdgpu").exists())
   self.assertFalse((root/"usr/lib/firmware/nvidia").exists())
   self.assertFalse(x["measured_compressed_iso_savings"])
 def test_not_running_host(self):
  with self.assertRaises(ValueError):m.patch("/")
 def test_symlink_escaping_root_refused(self):
  with tempfile.TemporaryDirectory() as d:
   r=self.root(Path(d))
   (r/"usr/lib/firmware/nvidia/fw.bin").unlink()
   (r/"usr/lib/firmware/nvidia").rmdir()
   (r/"usr/lib/firmware/nvidia").symlink_to("/etc")
   with self.assertRaises(ValueError):m.patch(r)
 def test_zram_experiment_not_combined(self):
  with tempfile.TemporaryDirectory() as d:
   r=self.root(Path(d));(r/"etc/systemd/system/puppy50-zram-live.service").write_text("zram")
   with self.assertRaises(ValueError):m.patch(r)
if __name__=="__main__":unittest.main()
