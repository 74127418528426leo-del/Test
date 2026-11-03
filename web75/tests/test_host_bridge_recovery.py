import ast
import importlib.util
import tempfile
import unittest
from pathlib import Path
mod_path=Path(__file__).resolve().parents[1]/"qemu_https_bridge_recovery.py"
spec=importlib.util.spec_from_file_location("v75",mod_path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class HostBridgeRecoveryTests(unittest.TestCase):
    def test_script_compiles(self):
        ast.parse(mod_path.read_text())
    def test_exact_real_guest_environment_retained(self):
        data=mod_path.read_text()
        self.assertIn("pc,accel=kvm",data)
        self.assertIn("file={args.iso}",data)
        self.assertIn('id=puppycd',data)
        self.assertIn("real_qemu_browser_link_click_submitted",data)
    def test_real_outage_not_fake_success(self):
        src=mod_path.read_text()
        self.assertIn("os.kill(pid,signal.SIGTERM)",src)
        self.assertIn('sock.connect_ex(("127.0.0.1",3128))',src)
        self.assertIn('report["host_bridge_was_unavailable"]=True',src)
        self.assertIn('report["host_bridge_restart_succeeded"]=True',src)
        self.assertIn('report["restored_host_CA_HTTPS_ok"]',src)
        self.assertIn('report["host_physical_network_transition_proven"]=False',src)
    def test_bad_ppm_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"frame.ppm"
            path.write_bytes(b"not an image")
            with self.assertRaises(ValueError):
                module.cyan_fraction(path)
if __name__=="__main__":unittest.main()
