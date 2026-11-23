import json
import unittest

from hermes_qwen_review import expected_review, review_passed


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            "candidate": "nice-10_zstd3",
            "worst_seconds": 1.0,
            "next_step": "replicate",
        }
        self.result = {
            "completed": True,
            "api_calls": 2,
            "final_response": json.dumps(self.expected),
        }

    def test_completed_review_matches_evidence(self):
        self.assertTrue(review_passed(self.result, ["best"], "best", self.expected))

    def test_matching_text_requires_the_correct_tool_read(self):
        for reads in ([], ["latest"]):
            with self.subTest(reads=reads):
                self.assertFalse(review_passed(self.result, reads, "best", self.expected))

    def test_incomplete_or_unsupported_results_do_not_pass(self):
        for update in (
            {"completed": False},
            {"api_calls": 1},
            {"final_response": "The test passed"},
            {"final_response": json.dumps(dict(self.expected, worst_seconds=2.0))},
            {"final_response": json.dumps(dict(self.expected, worst_seconds=True))},
        ):
            with self.subTest(update=update):
                result = dict(self.result, **update)
                self.assertFalse(review_passed(result, ["best"], "best", self.expected))

    def test_report_recommends_optimization_at_the_strict_threshold(self):
        batch = {
            "candidate": "nice-10_zstd3",
            "frames_recorded": 4,
            "worst_seconds": 5.0,
            "vm_gate_passed": False,
            "independently_verified": False,
        }
        self.assertEqual(expected_review(batch)["next_step"], "optimize")
        batch["worst_seconds"] = 4.9
        self.assertEqual(expected_review(batch)["next_step"], "diagnose")
