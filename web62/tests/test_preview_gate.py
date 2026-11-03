"""Synthetic fixtures for ISO preview qualification. Do not claim real VM proof."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

p=Path(__file__).resolve().parents[1]/"preview_gate.py"
spec=importlib.util.spec_from_file_location("gate",p)
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class PreviewGateTests(unittest.TestCase):
    def fixture(self,d):
        d=Path(d)
        iso=d/"preview.iso"
        with iso.open("wb") as f:
            f.truncate(51*1048576)
            f.seek(16*2048+1)
            f.write(b"CD001")
        results={
          "384":{"ram_copy":True,"root_switch":True,"cd_ejected":True,"script_ready":False},
          "1024":{"ram_copy":True,"root_switch":True,"cd_ejected":True,
                  "script_ready":True,"mouse_event_visually_confirmed":True,
                  "keyboard_event_visually_confirmed":True}
        }
        j=d/"results.json";j.write_text(json.dumps(results))
        evidence=d/"evidence"
        for ram in ("384","1024"):
            p=evidence/f"ram_{ram}MiB"
            p.mkdir(parents=True)
            (p/"serial.log").write_text("\n".join(gate.EARLY_SIGNALS))
        return iso,j,evidence

    def test_valid_preview_requires_boot_and_input(self):
        with tempfile.TemporaryDirectory() as d:
            iso,j,e=self.fixture(d)
            out=gate.check(iso,j,e,commit="test-sha")
            self.assertEqual(out["source_commit"],"test-sha")
            self.assertTrue(out["1024mib_offline_script_mouse_keyboard"])
            self.assertFalse(out["384mib_functional_browser"])
            self.assertEqual(len(out["sha256"]),64)

    def test_384mib_boot_failure_blocks_download(self):
        with tempfile.TemporaryDirectory() as d:
            iso,j,e=self.fixture(d)
            obj=json.loads(j.read_text());obj["384"]["cd_ejected"]=False
            j.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError,"384MiB"):
                gate.check(iso,j,e)

    def test_no_1024_mouse_proof_blocks_download(self):
        with tempfile.TemporaryDirectory() as d:
            iso,j,e=self.fixture(d)
            obj=json.loads(j.read_text());obj["1024"]["mouse_event_visually_confirmed"]=False
            j.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError,"1024MiB"):
                gate.check(iso,j,e)

    def test_missing_real_kernel_input_markers_blocks_download(self):
        with tempfile.TemporaryDirectory() as d:
            iso,j,e=self.fixture(d)
            (e/"ram_1024MiB"/"serial.log").write_text("no input drivers")
            with self.assertRaisesRegex(ValueError,"1024MiB"):
                gate.check(iso,j,e)

    def test_wrong_iso_signature_blocks_download(self):
        with tempfile.TemporaryDirectory() as d:
            iso,j,e=self.fixture(d)
            with iso.open("r+b") as f:
                f.seek(16*2048+1);f.write(b"WRONG")
            with self.assertRaisesRegex(ValueError,"ISO9660"):
                gate.check(iso,j,e)
if __name__=="__main__":unittest.main()
