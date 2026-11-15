#!/usr/bin/env python3
"""Analyze actual Puppy50 host and guest startup clocks WITHOUT subtracting unlike clocks.

Input: GitHub Actions QEMU evidence artifact with {bios1,uefi1,bios2,uefi2}/
result.json and serial.log. No invented timings and no access to physical Acer.
"""
import argparse
import json
import math
import re
from pathlib import Path
from statistics import mean

LABELS=("bios1","uefi1","bios2","uefi2")
MARKERS={
    "early_user":"P50_V118_EARLY_USER_READY",
    "drm_gate":"P50_V125_DRM_GATE_START",
    "drm_ready":"P50_V125_EARLY_DRM_READY",
    "xorg_start":"P50_V123_XORG_START",
    "firefox_exec":"P50_V127_FIREFOX_DIRECT_EXEC",
}
PATTERN=lambda tag:re.compile(r"^"+re.escape(tag)+r"\s+(\d+(?:\.\d+)?)\b",re.M)

def parse_boot(root,label):
    p=Path(root)/label
    result=json.loads((p/"result.json").read_text())
    text=(p/"serial.log").read_text(errors="replace")
    times={}
    for name,tag in MARKERS.items():
        hits=PATTERN(tag).findall(text)
        if len(hits)==1:
            value=float(hits[0])
            if math.isfinite(value) and 0<value<300:times[name]=value
    deltas={}
    for key,begin,end in (
        ("drm_initialization","drm_gate","drm_ready"),
        ("drm_to_xorg","drm_ready","xorg_start"),
        ("xorg_to_firefox_exec","xorg_start","firefox_exec")):
        if begin in times and end in times and times[end]>=times[begin]:
            deltas[key]=round(times[end]-times[begin],3)
    host={}
    for src,name in (
        ("first_home_seen_seconds","first_visible_firefox_frame"),
        ("staged_ram_ready_seconds","verified_ram_ready")):
        v=result.get(src)
        if type(v) in (int,float) and math.isfinite(v) and 0<v<600:
            host[name]=round(float(v),3)
    return {
        "label":label,"firmware":result.get("virtual_firmware"),
        "guest_uptime_markers_seconds":times,"guest_intra_clock_deltas_seconds":deltas,
        "host_monotonic_from_qemu_launch_seconds":host,
        "post_eject_browser_http200_confirmed":
           result.get("post_eject_browser_http200_confirmed") is True,
        "errors":result.get("errors",[])[:3] if isinstance(result.get("errors"),list) else []
    }

def analyze(root):
    all_boots=[parse_boot(root,label) for label in LABELS]
    metrics={}
    for delta in ("drm_initialization","drm_to_xorg","xorg_to_firefox_exec"):
        vals=[b["guest_intra_clock_deltas_seconds"][delta] for b in all_boots
              if delta in b["guest_intra_clock_deltas_seconds"]]
        metrics[delta]={"n":len(vals),"mean":round(mean(vals),3) if vals else None,
                        "min":min(vals) if vals else None,
                        "max":max(vals) if vals else None}
    bios=[b["host_monotonic_from_qemu_launch_seconds"].get("first_visible_firefox_frame")
          for b in all_boots if b["label"].startswith("bios")]
    uefi=[b["host_monotonic_from_qemu_launch_seconds"].get("first_visible_firefox_frame")
          for b in all_boots if b["label"].startswith("uefi")]
    f=lambda vals:round(mean(vals),3) if all(x is not None for x in vals) else None
    return {"scope":"Four actual independent QEMU boots from one GitHub run",
            "boot_count":len(all_boots),
            "guest_stage_delta_seconds":metrics,
            "host_mean_first_frame_seconds":{"bios":f(bios),"uefi":f(uefi)},
            "host_uefi_minus_bios_mean_seconds":
              round(f(uefi)-f(bios),3) if f(uefi) is not None and f(bios) is not None else None,
            "cross_clock_subtraction_is_invalid":True,
            "matched_host_randomized_ab_required_for_causal_claims":True,
            "interpretation":"Guest uptime stage-to-stage deltas are comparable within each "
              "boot, but first-frame host durations include QEMU start/firmware. "
              "Do not subtract guest firefox_exec from host first-frame to claim "
              "Firefox render duration. The DRM-to-Xorg gap alone is not proof "
              "of an explicit sleep or bottleneck cause.",
            "verified_five_second_result":False,
            "boots":all_boots}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=analyze(a.source)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="boots"},indent=2))
if __name__=="__main__":main()
