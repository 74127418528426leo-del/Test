"""Tests use sparse synthetic image sizes; no real guest proof is claimed."""
import importlib.util
import pathlib
import tempfile
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("budget", ROOT / "ram_budget_gate.py")
budget = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(budget)

class BudgetTests(unittest.TestCase):
    def test_actual_v46_image_fails_384_mib_planning_budget(self):
        r = budget.assess(387715072)
        self.assertEqual(r["classification"], "FAIL_ASSUMED_RUNTIME_BUDGET")
        self.assertAlmostEqual(r["spare_after_image_mib_upper_bound"], 14.246, places=3)
        self.assertAlmostEqual(r["required_image_shrink_mib_assumed"], 241.754, places=3)
        self.assertFalse(r["real_browser_proven_at_guest_ram"])

    def test_hard_impossible_if_sfs_alone_exceeds_all_ram(self):
        r=budget.assess(400*budget.MIB)
        self.assertEqual(r["classification"],"FAIL_HARD_SFS_ALONE_GE_GUEST_RAM")

    def test_small_image_is_only_an_estimated_pass(self):
        r=budget.assess(96*budget.MIB)
        self.assertEqual(r["classification"], "PASS_ESTIMATE_ONLY_NOT_REAL_VM_PROOF")

    def test_cli_reports_failure_and_measured_size(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/"synthetic.sfs"
            with p.open("wb") as f: f.truncate(387715072)
            r=subprocess.run([sys.executable,str(ROOT/"ram_budget_gate.py"),str(p)],
                             text=True,capture_output=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn('"image_bytes_measured": 387715072',r.stdout)

if __name__ == "__main__": unittest.main()
