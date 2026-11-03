#!/usr/bin/env python3
"""Verify exact v79 browser evidence and preserve honest screenshot verdicts.

This is a hash-bound visual audit, NOT an OCR classifier or a substitute for
the reviewed image. It explicitly refuses to call homepage disappearance a
successful render. Only the reviewed 2GiB page is classified as visible.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ALLOWED={
 "blank_after_navigation":False,
 "partially_rendered_Wikipedia":False,
 "Wikipedia_homepage_rendered":True
}

def sha256(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def verify(reviews,base):
    rev=json.loads(Path(reviews).read_text())
    if rev.get("schema")!="PUPPY50_V81_HUMAN_REVIEWED_V79_SITE_CONTENT":
        raise ValueError("Unexpected review schema")
    if rev.get("underlying_run_id")!=41682409363:
        raise ValueError("Review must be bound to exact original GitHub KVM run")
    cases=rev["cases"]
    if len(cases)!=3 or len({c["key"] for c in cases})!=3:
        raise ValueError("Must audit exactly three unique tested cases")
    results=[]
    for case in cases:
        k=case["key"]
        folder=Path(base)/k
        report_file=folder/"reports/V79_BROWSER_BENCHMARK.json"
        qemu_file=folder/"evidence/guest/result.json"
        bench=json.loads(report_file.read_text())
        qemu=json.loads(qemu_file.read_text())
        if bench["guest_ram_mib"]!=case["guest_ram_mib"] or bench["source_iso"] not in k:
            raise ValueError("Guest image/RAM metadata mismatch for "+k)
        if bench.get("first_page_transition_seconds_after_vm_start")!=case["automated_first_transition_seconds"]:
            raise ValueError("Automated transition changed for "+k)
        required=("guest_booted_RAM_root","CD_ejected","guest_DHCP_and_DNS",
                  "guest_CA_verified_public_HTTPS","real_guest_mouse_click_sent")
        if not all(bench.get(name) is True for name in required):
            raise ValueError("Missing real KVM boot/network/input proof for "+k)
        if not qemu.get("QEMU_virtual_NIC_kept_online",False):
            raise ValueError("This was supposed to be a stable-link comparison")
        actual=case["actual_page_status_at_405s"]
        if actual not in ALLOWED:
            raise ValueError("Unknown page classification")
        if case["actual_full_Wikipedia_page_visually_present"] is not ALLOWED[actual]:
            raise ValueError("Contradictory human screenshot review")
        screenshot={}
        for t,expected in case["screen_frame_sha256"].items():
            if t not in ("245","405"):
                raise ValueError("Unexpected screenshot stage")
            name="frame_"+t+".ppm"
            path=folder/"evidence/guest"/name
            with path.open("rb") as f:
                head=f.read(100)
            if not re.match(rb"P6\s+1920\s+1080\s+255\s",head):
                raise ValueError("Frame is not expected real 1920x1080 QEMU PPM")
            actual_hash=sha256(path)
            if actual_hash!=expected:
                raise ValueError("Changed frame pixels for "+k+"/"+name)
            screenshot[name]=actual_hash
        results.append({
            "source_image":k,
            "guest_ram_mib":case["guest_ram_mib"],
            "guest_CA_verified_HTTPS":True,
            "automated_page_transition_seconds":case["automated_first_transition_seconds"],
            "manually_reviewed_page_state_at_405s":actual,
            "full_Wikipedia_page_seen":ALLOWED[actual],
            "exact_screenshot_hashes_verified":True,
            "original_KVM_run":41682409363
        })
    fully_rendered=[r["source_image"] for r in results if r["full_Wikipedia_page_seen"]]
    if fully_rendered!=["package-complete-v78-2048"]:
        raise ValueError("No evidence for changed positive 1GiB claim")
    return {
      "schema":"PUPPY50_V81_EXACT_KVM_BROWSER_VISUAL_OUTCOME",
      "original_workflow_url":"https://github.com/74127418528426leo-del/Test/actions/runs/41682409363",
      "all_v79_jobs_reported_green":True,
      "green_navigation_gate_means_actual_full_Wikipedia_page_loaded":False,
      "verified_full_homepage_at_2048MiB_for_package_complete":True,
      "verified_full_homepage_at_1024MiB_for_package_complete":False,
      "one_run_not_performance_distribution":True,
      "public_normal_v70_release_unchanged":True,
      "physical_any_network_or_wifi_certified":False,
      "full_browser_security_updates_certified":False,
      "cases":results
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review",type=Path,required=True)
    p.add_argument("--evidence",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=verify(a.review,a.evidence)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2)+"\n")
    print(json.dumps(r,indent=2))
if __name__=="__main__":main()
