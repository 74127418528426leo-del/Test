"""Qualification must fail closed on ambiguous timing and ISO identity."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import json
import shlex
import subprocess


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

    def test_unrounded_upper_bound_controls_strict_five_second_gate(self):
        r = report()
        r["first_visible_Firefox_frame_seconds"]["uefi1"] = 5.00
        r["home_frame_observation_upper_seconds"]["uefi1"] = 4.999
        self.assertTrue(controller.verify(r)[0])

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

    def test_legacy_goal_flag_cannot_stop_future_experiments(self):
        state={"vm_goal_verified":True,"vm_goal_candidate":"legacy", "history":[]}
        candidate, _ = controller.choose(state)
        self.assertIsNotNone(candidate)
        self.assertTrue(hasattr(controller, "clear_stale_goal"))
        controller.clear_stale_goal(state)
        self.assertFalse(state["vm_goal_verified"])
        self.assertEqual(state["history"], [])
        cid = controller.PREFETCH_CANDIDATES[0]["id"]
        digest = "a" * 64
        state.update({"vm_goal_verified":True,"vm_goal_candidate":cid,"vm_goal_iso_sha256":digest,
                      "history":[{"candidate_id":cid,"vm_passed":True,
                                  "iso_sha256":digest,"benchmark_timing_schema":2,
                                  "run_id":run} for run in ("1", "2")]})
        candidate, _ = controller.choose(state)
        self.assertIsNone(candidate)

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
                    "guest_ram_mib":3072, "virtual_cpu_model":"i3-540-conservative",
                    "virtual_media":"ahci-cd", "network_mode":"online",
                    "virtual_read_cap_bytes_per_second":None,
                    "qemu_running_at_end":True, "input_sent_after_eject":True,
                    "staged_ram_ready_seconds":14.0,
                    "post_eject_browser_http200_confirmed":True,
                    "media_ejected":True,
                    "home_frame_observation":{"first_matching_probe_end_seconds":home},
                    "serial_marker_first_seen_seconds":{"P50_V127_FIREFOX_DIRECT_EXEC":receipt}}))
                (p / "serial.log").write_text("P50_V127_FIREFOX_DIRECT_EXEC 103.0 0.0\nP50_STAGE_COPY_VERIFIED\nP50_STAGE_READY\n")
            got = analysis.analyze(root, ["bios1"])
            pair = got["pairs"][0]
            self.assertEqual(pair["candidate"]["host_exec_receipt_to_home_observation_seconds"], 5.0)
            self.assertEqual(pair["control_minus_candidate_seconds"], 1.0)
            self.assertFalse(got["five_second_goal_verified"])
            path = root / "bios1/result.json"
            delayed = json.loads(path.read_text())
            delayed["serial_marker_first_seen_seconds"]["P50_V127_FIREFOX_DIRECT_EXEC"] = 8.2
            path.write_text(json.dumps(delayed))
            try:
                later = analysis.analyze(root, ["bios1"])["pairs"][0]["candidate"]
            except ValueError as exc:
                self.fail(f"delayed host serial receipt should remain diagnostic: {exc}")
            self.assertIsNone(later["host_exec_receipt_to_home_observation_seconds"])
            delayed["serial_marker_first_seen_seconds"] = {}
            path.write_text(json.dumps(delayed))
            missing = analysis.analyze(root, ["bios1"])["pairs"][0]["candidate"]
            self.assertIsNone(missing["host_exec_receipt_to_home_observation_seconds"])
            mismatch = root / "matched_bios1/result.json"
            control = json.loads(mismatch.read_text())
            control["guest_ram_mib"] = 512
            mismatch.write_text(json.dumps(control))
            with self.assertRaises(ValueError):
                analysis.analyze(root, ["bios1"])
            control["guest_ram_mib"] = 3072
            mismatch.write_text(json.dumps(control))
            (root / "matched_bios1/serial.log").write_text("P50_STAGE_READY\n")
            with self.assertRaises(ValueError):
                analysis.analyze(root, ["bios1"])

    def test_cookie_experiment_keeps_fresh_secret_and_authenticated_launch(self):
        path = ROOT / "research_lab/patch_parallel_cookie.py"
        self.assertTrue(path.is_file())
        spec = importlib.util.spec_from_file_location("parallel_cookie", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = '''# P50_V125_DRM_PREREQ
printf 'P50_V125_DRM_GATE_START %s\\n' "$(cat /proc/uptime)" >/dev/ttyS0
p50_cookie="$(mcookie)"
xauth -f /home/user/.Xauthority add :0 . "$p50_cookie"
/usr/lib/xorg/Xorg :0 -auth /home/user/.Xauthority -nolisten tcp
chroot "$p50_root" /usr/local/sbin/p50-v123-start-x >/dev/ttyS0 2>&1 &
'''
        modified = module.patch_text(original)
        self.assertIn('chroot "$p50_root" /bin/sh -c', modified)
        self.assertIn('/usr/bin/mcookie > "$p50_cookie_guest/pending"', modified)
        self.assertIn('xauth -f /home/user/.Xauthority add :0 . "$p50_cookie"', modified)
        self.assertIn('P50_EARLY_COOKIE_DIR=', modified)
        self.assertIn('rmdir "$P50_EARLY_COOKIE_DIR"', modified)
        self.assertNotIn('p50_cookie="$(mcookie)"', modified)
        self.assertIn('/usr/lib/xorg/Xorg :0 -auth /home/user/.Xauthority -nolisten tcp', modified)
        with self.assertRaises(ValueError):
            module.patch_text(modified)

    def test_cookie_overlap_waits_and_fails_closed_when_generator_fails(self):
        path = ROOT / "research_lab/patch_parallel_cookie.py"
        self.assertTrue(path.is_file())
        spec = importlib.util.spec_from_file_location("parallel_cookie", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "run").mkdir()
            for generator, expected in (("printf '%s\\n' 0123456789abcdef0123456789abcdef", 0),
                                        ("return 1", 23)):
                fake = Path(temp) / "fake-mcookie"
                fake.write_text("#!/bin/sh\n" + ("exit 1" if generator == "return 1" else generator) + "\n")
                fake.chmod(0o700)
                simulated_start = (module.START.replace(">/dev/ttyS0", ">/dev/null")
                                   .replace('p50_cookie_guest="/run/p50-cookie.$$"',
                                            'p50_cookie_guest="$p50_root/run/p50-cookie.$$"')
                                   .replace('p50_cookie_dir="$p50_root$p50_cookie_guest"',
                                            'p50_cookie_dir="$p50_cookie_guest"')
                                   .replace('/usr/bin/mcookie', str(fake)))
                script = ("set -eu\np50_root=" + shlex.quote(temp) + "\n"
                          "panic() { exit 98; }\nchroot() { shift; \"$@\"; }\n" +
                          simulated_start +
                          "P50_EARLY_COOKIE_DIR=$p50_cookie_dir\n" + module.WAIT.replace(">/dev/ttyS0", ">/dev/null") +
                          "\n[ ! -e \"$p50_cookie_dir\" ]\nwait\n")
                proc = subprocess.run(["sh", "-c", script], capture_output=True, text=True)
                self.assertEqual(proc.returncode, expected, proc.stderr)


if __name__ == "__main__":
    unittest.main()
