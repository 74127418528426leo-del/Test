"""Unit tests for the fail-closed Hermes evidence report validator."""
import importlib.util
import json
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name("hermes_review_gate.py")
SPEC = importlib.util.spec_from_file_location("hermes_review_gate", MODULE)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def sample_state():
    return {
        "vm_goal_verified": False,
        "history": [
            {"run_id": "older", "matched_prefetch_control": {
                "mean_candidate_seconds": 10.5, "mean_control_seconds": 10.0}},
            {"run_id": "43874157306", "matched_prefetch_control": {
                "mean_candidate_seconds": 9.787, "mean_control_seconds": 9.393}},
            {"run_id": "newer-unmatched-failure", "frames": {}},
        ],
    }


def sample_report():
    return {
        "run_id": "43874157306",
        "candidate_mean_seconds": 9.787,
        "control_mean_seconds": 9.393,
        "goal_verified": False,
        "test_summary": gate.EXPECTED_TEST_SUMMARY,
        "limitation": gate.EXPECTED_LIMITATION,
    }


def sample_transcript(report=None, tool_calls=5):
    return (
        "Query: bounded evidence review\n\n☤ Hermes\n"
        + json.dumps(report or sample_report())
        + "\n────────────────────────\nResume this session with: local-session\n"
        + f"Messages: 7 (1 user, {tool_calls} tool calls)\n"
    )


class HermesReviewGateTests(unittest.TestCase):
    def test_accepts_matching_report_after_five_file_tool_calls(self):
        report, calls = gate.parse_hermes_transcript(sample_transcript())
        result = gate.validate_report(report, sample_state(), calls)
        self.assertTrue(result["agent_report_consistent"])
        self.assertEqual(result["run_id"], "43874157306")
        self.assertFalse(result["goal_verified"])
        self.assertEqual(result["agent_tool_calls"], 5)

    def test_rejects_zero_or_insufficient_file_tool_calls(self):
        for calls in (0, 4):
            with self.subTest(calls=calls), self.assertRaisesRegex(ValueError, "file-tool calls"):
                gate.parse_hermes_transcript(sample_transcript(tool_calls=calls))

    def test_rejects_hallucinated_run_mean_or_goal(self):
        for key, value in (
            ("run_id", "2026-11-16"),
            ("candidate_mean_seconds", 1.5),
            ("control_mean_seconds", 11.0),
            ("goal_verified", True),
        ):
            with self.subTest(key=key):
                report = sample_report()
                report[key] = value
                parsed, calls = gate.parse_hermes_transcript(sample_transcript(report))
                with self.assertRaises(ValueError):
                    gate.validate_report(parsed, sample_state(), calls)

    def test_rejects_unsupported_success_and_limit_claims(self):
        for key, value in (
            ("test_summary", "Critical path simulation completed; 1.5s achieved."),
            ("limitation", "None."),
        ):
            report = sample_report()
            report[key] = value
            with self.assertRaises(ValueError):
                gate.validate_report(report, sample_state(), 5)

    def test_rejects_missing_extra_fields_and_nonfinite_numbers(self):
        report = sample_report()
        report.pop("limitation")
        with self.assertRaisesRegex(ValueError, "fields mismatch"):
            gate.validate_report(report, sample_state(), 5)
        report = sample_report()
        report["extra"] = "untrusted"
        with self.assertRaisesRegex(ValueError, "fields mismatch"):
            gate.validate_report(report, sample_state(), 5)
        report = sample_report()
        report["candidate_mean_seconds"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite number"):
            gate.validate_report(report, sample_state(), 5)

    def test_rejects_invalid_json_and_missing_footer(self):
        bad = "☤ Hermes\nnot JSON\n────────────────\nMessages: 4 (1 user, 5 tool calls)"
        with self.assertRaisesRegex(ValueError, "raw JSON"):
            gate.parse_hermes_transcript(bad)
        with self.assertRaisesRegex(ValueError, "no authentic"):
            gate.parse_hermes_transcript("☤ Hermes\n{}\n")

    def test_rejects_invalid_latest_persistent_state(self):
        state = sample_state()
        state["vm_goal_verified"] = "false"
        with self.assertRaisesRegex(ValueError, "boolean"):
            gate.latest_matched_comparison(state)
        with self.assertRaisesRegex(ValueError, "no completed"):
            gate.latest_matched_comparison({"vm_goal_verified": False, "history": [{"run_id": "x"}]})


if __name__ == "__main__":
    unittest.main()
