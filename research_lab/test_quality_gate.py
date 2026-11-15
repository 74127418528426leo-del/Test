"""Fail closed on low-quality OS science; never treat JSON validity as a speedup."""
import unittest
from quality_gate import assess

class ScientificQualityTests(unittest.TestCase):
    def test_real_truncated_4b_output_is_not_credible(self):
        bad={
          "hypothesis":"Lowering nice to -10 during initramfs Zstd-3 decompression reduces CPU contention for early BIOS/UEFI frame rendering, potentially shaving milliseconds off TTFB by 1",
          "architecture_idea":"Preserve original Firefox sandbox and recovery"
        }
        report=assess(bad)
        self.assertFalse(report["admit"])
        self.assertTrue(any("chronology" in x for x in report["errors"]))
        self.assertTrue(any("truncated" in x for x in report["errors"]))

    def test_technically_specific_reversible_hypothesis_can_be_considered(self):
        good={
          "hypothesis":"Reducing libxul prefetch from 256 to 64 MiB may reduce competing I/O before Xorg; compare real time to the first visible Firefox frame against a matched same-host BIOS and UEFI baseline.",
          "architecture_idea":"Preserve sandbox, root and recovery checks. Rollback automatically if post-eject HTTP200 fails."
        }
        report=assess(good)
        self.assertTrue(report["admit"],report["errors"])

    def test_sentence_and_measurement_required(self):
        p={"hypothesis":"Make booting much faster by optimizing kernel settings",
           "architecture_idea":"Keep recovery."}
        self.assertFalse(assess(p)["admit"])

    def test_never_confuse_heuristic_with_proof(self):
        p={"hypothesis":"Changing initramfs Zstd level might change first visible Firefox frame time; compare same-host BIOS control boots and restore recovery if regressions occur.",
           "architecture_idea":"Preserve recovery and sandbox."}
        self.assertTrue(assess(p)["admit"])
        # Acceptance means only that a proposal is ready for independent review.
        self.assertNotIn("vm_goal_verified",assess(p))

if __name__=="__main__":
    unittest.main()
