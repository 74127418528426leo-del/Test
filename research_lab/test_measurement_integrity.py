"""Qualification must fail closed on ambiguous timing and ISO identity."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import json


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "autolab_controller", ROOT / "experiments/puppy50-autolab/controller.py"
)
controller = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(controller)


def report():
    frames = {name: 4.99 for name in controller.BOOTS}
    return {
        "first_visible_Firefox_frame_seconds": frames,
        "home_frame_observation_upper_seconds": dict(frames),
        "benchmark_timing_schema": 2,
        "checksum_verified_whole_root_in_RAM_all_four": True,
        "virtual_CD_removed_after_RAM_all_four": True,
        "original_Zstd_root_and_full_RAM_recovery_preserved": True,
        "all_four_real_Firefox_under_five_seconds": True,
        "real_browser_HTTP200_receipts_after_CD_removal": 4,
        "sha256": "a" * 64,
    }


class VerificationIntegrityTests(unittest.TestCase):
    def test_legacy_or_rounded_timing_cannot_certify_five_seconds(self):
        r = report()
        del r["benchmark_timing_schema"]
        self.assertFalse(controller.verify(r)[0])
        r = report()
        r["home_frame_observation_upper_seconds"]["uefi1"] = 5.0001
        self.assertFalse(controller.verify(r)[0])
        r["home_frame_observation_upper_seconds"]["uefi1"] = float("nan")
        self.assertFalse(controller.verify(r)[0])

    def test_independent_runs_must_test_same_iso(self):
        self.assertTrue(hasattr(controller, "independently_verified_iso"))
        qualify = controller.independently_verified_iso
        def item(run, digest, candidate="candidate", passed=True):
            return {"run_id": run, "iso_sha256": digest,
                    "candidate_id": candidate, "vm_passed": passed,
                    "benchmark_timing_schema": 2}
        a, b = "a" * 64, "b" * 64
        self.assertIsNone(qualify([item("1", a), item("2", b)], "candidate"))
        self.assertIsNone(qualify([item("1", a), item("1", a)], "candidate"))
        self.assertIsNone(qualify([item("1", a), item("2", a, passed=False)], "candidate"))
        self.assertIsNone(qualify([item("1", a), item("2", a, "other")], "candidate"))
        self.assertIsNone(qualify([item("1", "bad"), item("2", "bad")], "candidate"))
        old = item("2", a)
        del old["benchmark_timing_schema"]
        self.assertIsNone(qualify([item("1", a), old], "candidate"))
        self.assertEqual(qualify([item("1", a), item("2", a)], "candidate"), a)

    def test_frame_probes_keep_host_clock_bracket_and_exact_capture(self):
        path = ROOT / "research_lab/measurement_probe.py"
        self.assertTrue(path.is_file())
        spec = importlib.util.spec_from_file_location("measurement_probe", path)
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        ticks = iter([100.1, 100.3, 101.1, 101.4])
        clock = lambda: next(ticks)
        visible = iter([False, True])
        calls = []
        def capture(monitor, out, name):
            calls.append((monitor, out, name))
            return next(visible)
        result = {}
        self.assertFalse(probe.probe_frame(capture, "monitor", "out", None, 100, result, clock))
        self.assertTrue(probe.probe_frame(capture, "monitor", "out", None, 100, result, clock))
        self.assertEqual(len(calls), 2)  # no second QMP screenshot after detection
        self.assertEqual(len(result["frame_probe_trace"]), 2)
        bounds = result["home_frame_observation"]
        self.assertAlmostEqual(bounds["last_nonmatching_probe_start_seconds"], 0.1, places=5)
        self.assertGreaterEqual(bounds["first_matching_probe_end_seconds"], 1.4)
        self.assertLess(bounds["first_matching_probe_end_seconds"], 1.401)

    def test_marker_receipt_is_host_time_and_is_not_replaced(self):
        path = ROOT / "research_lab/measurement_probe.py"
        self.assertTrue(path.is_file())
        spec = importlib.util.spec_from_file_location("measurement_probe", path)
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        result = {"serial_marker_first_seen_seconds": {}}
        probe.observe_markers("P50_V127_FIREFOX_DIRECT_EXEC 3.2", result,
                              ["P50_V127_FIREFOX_DIRECT_EXEC"], 105, 100)
        probe.observe_markers("P50_V127_FIREFOX_DIRECT_EXEC 3.2", result,
                              ["P50_V127_FIREFOX_DIRECT_EXEC"], 109, 100)
        self.assertEqual(result["serial_marker_first_seen_seconds"]
                         ["P50_V127_FIREFOX_DIRECT_EXEC"], 5)

    def test_guest_tracing_changes_only_expected_launcher_in_disposable_root(self):
        module_path = ROOT / "research_lab/patch_guest_telemetry.py"
        self.assertTrue(module_path.is_file())
        spec = importlib.util.spec_from_file_location("guest_telemetry", module_path)
        guest = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guest)
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "usr/lib/live/boot/9990-main.sh"
            p.parent.mkdir(parents=True)
            p.write_text('# P50_V123_BEFORE_PID1\np50_cookie="$(mcookie)"\n'
                         'xauth -f /home/user/.Xauthority add :0 . "$p50_cookie"\n'
                         'chmod 0600 /home/user/.Xauthority\n')
            guest.patch(Path(temp))
            data = p.read_text()
            self.assertIn('p50_cookie="$(mcookie)"', data)
            self.assertIn('xauth -f /home/user/.Xauthority add :0 . "$p50_cookie"', data)
            for tag in ("P50_TRACE_LAUNCHER_ENTER", "P50_TRACE_COOKIE_READY",
                        "P50_TRACE_XAUTH_BEGIN", "P50_TRACE_XAUTH_READY"):
                self.assertEqual(data.count(tag), 1)
            with self.assertRaises(ValueError):
                guest.patch(Path(temp))
        with self.assertRaises(ValueError):
            guest.patch(Path("/"))

    def test_benchmark_patcher_rejects_unknown_harness(self):
        path = ROOT / "research_lab/patch_benchmark_timing.py"
        self.assertTrue(path.is_file())
        spec = importlib.util.spec_from_file_location("benchmark_patch", path)
        patcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(patcher)
        with self.assertRaises(ValueError):
            patcher.patch_text("# unknown harness\n")

    def test_paired_analysis_uses_host_receipts_not_guest_uptime(self):
        path = ROOT / "research_lab/analyze_paired_boots.py"
        self.assertTrue(path.is_file())
        spec = importlib.util.spec_from_file_location("paired_analysis", path)
        analysis = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(analysis)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for prefix, home, receipt in (("", 8.0, 3.0), ("matched_", 9.0, 3.5)):
                p = root / (prefix + "bios1")
                p.mkdir()
                (p / "result.json").write_text(json.dumps({
                    "virtual_firmware":"bios", "errors":[],
                    "post_eject_browser_http200_confirmed":True,
                    "media_ejected":True,
                    "home_frame_observation":{"first_matching_probe_end_seconds":home},
                    "serial_marker_first_seen_seconds":{"P50_V127_FIREFOX_DIRECT_EXEC":receipt}}))
                (p / "serial.log").write_text("P50_V127_FIREFOX_DIRECT_EXEC 103.0 0.0\n")
            got = analysis.analyze(root, ["bios1"])
            pair = got["pairs"][0]
            self.assertEqual(pair["candidate"]["host_exec_receipt_to_home_observation_seconds"], 5.0)
            self.assertEqual(pair["control_minus_candidate_seconds"], 1.0)
            self.assertFalse(got["five_second_goal_verified"])


if __name__ == "__main__":
    unittest.main()
