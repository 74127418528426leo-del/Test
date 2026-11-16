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


def sample_transcript(report=None, tool_calls=1, successful_read=True, json_prefix=False):
    trace = (
        "📖 Read research_lab/agent-context/review-input.json L1-6\n"
        if successful_read else
        "✗ Read review-input.json [File not found]\n"
    )
    payload = json.dumps(report or sample_report())
    if json_prefix:
        payload = "json" + payload
    return (
        "Query: bounded evidence review\n" + trace + "\n☤ Hermes\n"
        + payload
        + "\n────────────────────────\nResume this session with: local-session\n"
        + f"Messages: 3 (1 user, {tool_calls} tool call{'s' if tool_calls != 1 else ''})\n"
    )


class HermesReviewGateTests(unittest.TestCase):
    def test_accepts_matching_report_after_successful_packet_read(self):
        report, calls = gate.parse_hermes_transcript(sample_transcript())
        result = gate.validate_report(report, sample_state(), calls)
        self.assertTrue(result["agent_report_consistent"])
        self.assertEqual(result["run_id"], "43874157306")
        self.assertFalse(result["goal_verified"])
        self.assertEqual(result["agent_tool_calls"], 1)

    def test_accepts_bare_json_label_prefix(self):
        report, calls = gate.parse_hermes_transcript(sample_transcript(json_prefix=True))
        result = gate.validate_report(report, sample_state(), calls)
        self.assertTrue(result["agent_report_consistent"])
        self.assertEqual(result["run_id"], "43874157306")

    def test_accepts_hermes_escaped_object_format_seen_in_ci(self):
        payload = json.dumps(sample_report())
        escaped = '{"' + payload[1:].replace('"', r'\"')
        transcript = sample_transcript().replace(payload, escaped)
        report, calls = gate.parse_hermes_transcript(transcript)
        result = gate.validate_report(report, sample_state(), calls)
        self.assertTrue(result["agent_report_consistent"])
        self.assertEqual(result["run_id"], "43874157306")

    def test_rejects_zero_file_tool_calls(self):
        with self.assertRaisesRegex(ValueError, "file-tool call"):
            gate.parse_hermes_transcript(sample_transcript(tool_calls=0))

    def test_rejects_failed_packet_read_even_if_a_tool_was_called(self):
        with self.assertRaisesRegex(ValueError, "successfully read"):
            gate.parse_hermes_transcript(sample_transcript(tool_calls=1, successful_read=False))

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
                gate.validate_report(report, sample_state(), 1)

    def test_rejects_missing_extra_fields_and_nonfinite_numbers(self):
        report = sample_report()
        report.pop("limitation")
        with self.assertRaisesRegex(ValueError, "fields mismatch"):
            gate.validate_report(report, sample_state(), 1)
        report = sample_report()
        report["extra"] = "untrusted"
        with self.assertRaisesRegex(ValueError, "fields mismatch"):
            gate.validate_report(report, sample_state(), 1)
        report = sample_report()
        report["candidate_mean_seconds"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite number"):
            gate.validate_report(report, sample_state(), 1)

    def test_rejects_invalid_json_and_missing_footer(self):
        bad = (
            "📖 Read review-input.json L1-6\n☤ Hermes\nnot JSON\n"
            "────────────────\nMessages: 4 (1 user, 1 tool call)"
        )
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
