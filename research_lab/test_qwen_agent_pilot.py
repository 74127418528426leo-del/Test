"""Offline safety tests for the bounded Qwen-Agent pilot."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qwen_agent_pilot as pilot


def sample_state():
    return {
        "vm_goal_verified": False,
        "history": [{
            "run_id": "43874157306",
            "matched_prefetch_control": {
                "mean_candidate_seconds": 9.787,
                "mean_control_seconds": 9.393,
            },
        }],
    }


def sample_report():
    return {
        "run_id": "43874157306",
        "candidate_mean_seconds": 9.787,
        "control_mean_seconds": 9.393,
        "goal_verified": False,
        "test_summary": pilot.EXPECTED_TEST_SUMMARY,
        "limitation": pilot.EXPECTED_LIMITATION,
    }


class QwenAgentPilotTests(unittest.TestCase):
    def test_read_tool_opens_only_the_fixed_packet_and_records_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = '{"run_id":"safe"}\n'
            (root / "review-input.json").write_text(payload)
            audit = []
            self.assertEqual(
                pilot.safe_read_review_packet(root, {"path": "review-input.json"}, audit),
                payload,
            )
            self.assertEqual(audit, [{
                "call": 1,
                "tool": pilot.TOOL_NAME,
                "path": "review-input.json",
                "status": "read",
                "bytes": len(payload.encode()),
                "sha256": hashlib.sha256(payload.encode()).hexdigest(),
            }])

    def test_tool_rejects_traversal_absolute_paths_and_extra_parameters(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "review-input.json").write_text("{}")
            for params in (
                {"path": "../review-input.json"},
                {"path": str(root / "review-input.json")},
                {"path": "review-input.json", "other": "x"},
            ):
                with self.subTest(params=params), self.assertRaises(ValueError):
                    pilot.safe_read_review_packet(root, params, [])

    def test_tool_rejects_symlink_and_more_than_one_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "outside.json"
            target.write_text("{}")
            (root / "review-input.json").symlink_to(target)
            with self.assertRaises(ValueError):
                pilot.safe_read_review_packet(root, {"path": "review-input.json"}, [])
            (root / "review-input.json").unlink()
            (root / "review-input.json").write_text("{}")
            audit = []
            pilot.safe_read_review_packet(root, {"path": "review-input.json"}, audit)
            with self.assertRaises(ValueError):
                pilot.safe_read_review_packet(root, {"path": "review-input.json"}, audit)
            self.assertEqual(len(audit), 2)
            self.assertEqual(audit[1]["status"], "denied")

    def test_tool_rejects_oversized_packet(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "review-input.json").write_bytes(
                b"x" * (pilot.MAX_PACKET_BYTES + 1)
            )
            with self.assertRaisesRegex(ValueError, "byte limit"):
                pilot.safe_read_review_packet(
                    root, {"path": "review-input.json"}, []
                )

    def test_run_rejects_packet_symlink_before_loading_agent_framework(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            other = root / "elsewhere"
            other.mkdir()
            (other / "review-input.json").write_text("{}")
            packet = root / "review-input.json"
            packet.symlink_to(other / "review-input.json")
            with self.assertRaisesRegex(ValueError, "not a symlink"):
                pilot.resolve_packet_root(packet)
            packet.unlink()
            packet.write_text("{}")
            self.assertEqual(pilot.resolve_packet_root(packet), root.resolve())

    def test_report_parser_accepts_only_one_raw_json_object(self):
        report = sample_report()
        encoded = json.dumps(report)
        self.assertEqual(pilot.parse_model_report("json" + encoded), report)
        self.assertEqual(pilot.parse_model_report("<think>done</think>\n" + encoded), report)
        with self.assertRaises(ValueError):
            pilot.parse_model_report(encoded + " extra claims")
        with self.assertRaises(ValueError):
            pilot.parse_model_report("```json\n" + encoded + "\n```")

    def test_gate_requires_one_successful_real_tool_execution_and_matches_state(self):
        audit = [{"tool": pilot.TOOL_NAME, "status": "read", "path": "review-input.json"}]
        verified = pilot.validate_agent_run(sample_report(), audit, sample_state())
        self.assertTrue(verified["agent_report_consistent"])
        self.assertIn("Qwen-Agent", verified["scope"])
        with self.assertRaisesRegex(ValueError, "exactly one"):
            pilot.validate_agent_run(sample_report(), [], sample_state())
        with self.assertRaisesRegex(ValueError, "exactly one"):
            pilot.validate_agent_run(sample_report(), audit * 2, sample_state())
        with self.assertRaisesRegex(ValueError, "successfully"):
            pilot.validate_agent_run(sample_report(), [{**audit[0], "status": "denied"}], sample_state())

    def test_message_summary_records_roles_calls_and_bounds_output(self):
        summary = pilot.summarize_agent_messages([
            {"role": "assistant", "tool_calls": [{
                "function": {"name": pilot.TOOL_NAME, "arguments": "{}"}
            }]},
            {"role": "function", "name": pilot.TOOL_NAME, "content": "private tool output"},
            {"role": "assistant", "content": "x" * 600},
        ])
        self.assertEqual(summary["message_roles"], ["assistant", "function", "assistant"])
        self.assertEqual(summary["model_tool_call_names"], [pilot.TOOL_NAME])
        self.assertEqual(len(summary["assistant_final_preview"]), 512)
        self.assertTrue(summary["assistant_preview_truncated"])

    def test_agent_endpoint_must_be_local_loopback(self):
        pilot._require_loopback_endpoint("http://127.0.0.1:8088/v1")
        for url in (
            "https://127.0.0.1:8088/v1",
            "http://example.org:8088/v1",
            "http://127.0.0.1:8088/v1?key=secret",
            "http://user@127.0.0.1:8088/v1",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                pilot._require_loopback_endpoint(url)


if __name__ == "__main__":
    unittest.main()
