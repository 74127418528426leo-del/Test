"""Offline regression checks for Hermes WhatsApp status and partial QEMU evidence."""
import importlib.util
import json
import tempfile
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,str(path))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

status=load("p50_status",ROOT/"hermes_skills/puppy50-progress/scripts/status.py")
partial=load("p50_partial",ROOT/"collect_vm_evidence.py")
prefetch=load("p50_prefetch",ROOT/"patch_libxul_prefetch.py")

class StatusTests(unittest.TestCase):
    def test_successful_ci_is_not_five_second_os(self):
        state={"vm_goal_verified":False,"history":[
            {"candidate_id":"nice-10_zstd3","vm_passed":False,
             "reason":"not all four Firefox frames strictly below five seconds",
             "frames":{"bios1":10.31,"uefi1":21.03,"bios2":8.65,"uefi2":12.89}}
        ]}
        queue={"candidates":[{"nice":-10,"zstd":3}]}
        runs={"workflow_runs":[
            {"name":"Puppy50 autonomous guarded VM experimentation",
             "status":"completed","conclusion":"success","html_url":"https://github.com/example/run"}
        ]}
        got=status.snapshot(state,queue,runs)
        self.assertFalse(got["vm_goal_verified"])
        self.assertEqual(got["best_complete_4boot_candidate"]["worst_seconds"],21.03)
        self.assertEqual(got["best_complete_4boot_candidate"]["mean_seconds"],13.22)
        self.assertFalse(got["best_complete_4boot_candidate"]["strict_vm_goal_passed"])
        self.assertIn("NOT VERIFIED",status.format_text(got,"progress"))
        self.assertIn("21.03s",status.format_text(got,"fastest"))
        self.assertEqual(got["vm_experiments_recorded"],1)

    def test_only_partial_frame_evidence_is_not_complete(self):
        got=status.snapshot(
           {"vm_goal_verified":False,"history":[
             {"candidate_id":"nice-9_zstd2","vm_passed":False,
              "frames":{"bios1":9.75},"reason":"UEFI failed HTTP200"}]},
           {"candidates":[]},{"workflow_runs":[]})
        self.assertIsNone(got["best_complete_4boot_candidate"])
        self.assertIn("No complete four-boot",status.format_text(got,"fastest"))
        self.assertIn("9.75s",status.format_text(got,"latest"))

    def test_real_matched_control_exposed_without_claiming_five_seconds(self):
        matched={
          "reference_prefetch_mib":256,"candidate_prefetch_mib":0,
          "mean_control_seconds":12.0,"mean_candidate_seconds":9.4,
          "mean_control_minus_candidate_seconds":2.6
        }
        state={"vm_goal_verified":False,"history":[{
          "candidate_id":"nice-10_zstd3_prefetch0",
          "vm_passed":False,"frames":{"bios1":8.8,"uefi1":10.8,
                                   "bios2":7.5,"uefi2":10.6},
          "matched_prefetch_control":matched}]}
        data=status.snapshot(state,{"candidates":[]},{"workflow_runs":[]})
        t=status.format_text(data,"comparison")
        self.assertIn("256 MiB",t)
        self.assertIn("0 MiB",t)
        self.assertIn("2.6s",t)
        self.assertIn("NOT certified",t)
        self.assertFalse(data["vm_goal_verified"])

    def test_live_http_requests_must_use_fixed_github_host(self):
        for path in ("http://evil.invalid","//evil.invalid","/x/../y"):
            with self.assertRaises(ValueError):
                status.fetch_json(path)

    def test_help_is_read_only(self):
        t=status.format_text({},"help").lower()
        self.assertIn("read-only",t)
        self.assertIn("no builds",t)

class CollectTests(unittest.TestCase):
    def test_real_partial_results_never_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for label,frame,http_ok in (
               ("bios1",9.2,True),("uefi1",10.0,False)):
                p=root/label/"result.json"
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text(json.dumps({
                   "first_home_seen_seconds":frame,
                   "staged_ram_ready_seconds":15.0,
                   "post_eject_browser_http200_confirmed":http_ok,
                   "errors":[] if http_ok else ["missing real browser HTTP200"]}))
            out=partial.collect(root)
            self.assertEqual(out["observed_frames"]["bios1"],9.2)
            self.assertEqual(out["observed_frames"]["uefi1"],10.0)
            self.assertFalse(out["functional_gates_passed"])
            self.assertFalse(out["verified_under_five_seconds"])
            self.assertFalse(out["full_four_boot_result_available"])
            self.assertEqual(len(out["vm_failures"]),3)

    def test_four_fast_frames_still_not_verified_without_full_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            for label in partial.LABELS:
                p=Path(tmp)/label/"result.json"
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text(json.dumps({"first_home_seen_seconds":4.1,
                                         "post_eject_browser_http200_confirmed":False}))
            out=partial.collect(tmp)
            self.assertTrue(out["full_four_boot_result_available"])
            self.assertFalse(out["verified_under_five_seconds"])
            self.assertEqual(out["four_frame_mean_seconds"],4.1)
            self.assertEqual(len(out["vm_failures"]),4)

class PrefetchTests(unittest.TestCase):
    def sample_boot(self,path):
        target=Path(path)/"usr/lib/live/boot/9990-main.sh"
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text("""#!/bin/sh
# P50_V131_LIBXUL_READAHEAD
# P50_V127_FIREFOX_DIRECT_EXEC
# P50_V149_WEBRENDER_USERJS_READY
printf 'P50_V133_PREFETCH_256MB_STARTED %s\\n' "$(cat /proc/uptime)" >/dev/ttyS0
            nice -n 10 dd if="$p50_lib" of=/dev/null bs=1048576 count=256 2>/dev/null
""")
        return target

    def test_all_allowed_depths_preserve_bounded_change(self):
        for size in prefetch.ALLOWED:
            with tempfile.TemporaryDirectory() as tmp:
                target=self.sample_boot(tmp)
                original=target.read_text()
                prefetch.patch(tmp,size)
                modified=target.read_text()
                self.assertIn(f"P50_V133_PREFETCH_{size}MB_STARTED",modified)
                self.assertIn("P50_V127_FIREFOX_DIRECT_EXEC",modified)
                self.assertIn("P50_V149_WEBRENDER_USERJS_READY",modified)
                self.assertNotEqual(original,modified)
                self.assertRaises(ValueError,prefetch.patch,tmp,size)
                if size==0:self.assertNotIn("dd if=",modified)
                else:self.assertIn(f"count={size}",modified)

    def test_reject_host_and_bad_depths(self):
        self.assertRaises(ValueError,prefetch.patch,"/",32)
        with tempfile.TemporaryDirectory() as tmp:
            self.sample_boot(tmp)
            self.assertRaises(ValueError,prefetch.patch,tmp,999)

if __name__=="__main__":
    unittest.main()
