#!/usr/bin/env python3
"""Analyze *guest-side* Linux /proc serial RAM telemetry without OCR or heuristics.

MemAvailable estimates reclaimable guest RAM; browser VmRSS sum overcounts
shared pages; PSI only exists if built into this kernel. No causality claim.
"""
import argparse
import json
import re
import statistics
from pathlib import Path

PATTERN=re.compile(r"PUPPY50_V81_MEM\s+([^\r\n]+)")
PAIR=re.compile(r"([A-Za-z_][A-Za-z_0-9]*)=(-?[0-9]+(?:\.[0-9]+)?)")
FIELDS=("total_kib","available_kib","free_kib","swap_total_kib",
        "swap_free_kib","anon_kib","shmem_kib","oom_kill",
        "psi_some_avg10","psi_full_avg10","browser_processes",
        "browser_VmRSS_sum_kib","uptime_sec","tick")

def parse(text):
    rows=[]
    for raw in PATTERN.findall(text):
        items=dict(PAIR.findall(raw))
        if not all(x in items for x in FIELDS):continue
        rows.append({k:float(items[k]) for k in FIELDS})
    return sorted(rows,key=lambda x:x["tick"])

def report(serial_path,scenario,ram):
    text=Path(serial_path).read_text(errors="replace")
    items=parse(text)
    if len(items)<10:
        raise ValueError("Insufficient actual guest memory samples")
    av=[x["available_kib"] for x in items]
    psi=[x["psi_some_avg10"] for x in items if x["psi_some_avg10"]>=0]
    oom=[x["oom_kill"] for x in items if x["oom_kill"]>=0]
    total=items[0]["total_kib"]
    return {
      "schema":"PUPPY50_V81_READ_ONLY_LINUX_GUEST_MEM_PRESSURE",
      "source_scenario":scenario,
      "qemu_configured_RAM_mib":ram,
      "actual_Linux_MemTotal_kib":total,
      "samples":len(items),
      "sample_interval_seconds":10,
      "minimum_Linux_MemAvailable_kib":min(av),
      "median_Linux_MemAvailable_kib":statistics.median(av),
      "ending_Linux_MemAvailable_kib":av[-1],
      "minimum_available_fraction_of_MemTotal":round(min(av)/total,4) if total else None,
      "swap_total_kib":items[0]["swap_total_kib"],
      "maximum_memory_PSI_some_avg10":max(psi) if psi else None,
      "maximum_memory_PSI_full_avg10":max((x["psi_full_avg10"] for x in items if x["psi_full_avg10"]>=0),default=None),
      "kernel_OOM_kill_counter_increase":max(oom)-min(oom) if oom else None,
      "maximum_browser_process_count":max(x["browser_processes"] for x in items),
      "maximum_sum_of_browser_process_VmRSS_kib_not_PSS":max(x["browser_VmRSS_sum_kib"] for x in items),
      "observed_rows":items,
      "browser_site_rendering_visually_confirmed":False,
      "guest_memory_pressure_is_the_cause_certified":False,
      "warning":"VmRSS sum counts shared pages more than once. Kernel MemAvailable is an estimate. PSI may be unavailable. A sample run cannot establish causation."
    }

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--serial",type=Path,required=True)
    ap.add_argument("--scenario",required=True)
    ap.add_argument("--ram",type=int,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    r=report(a.serial,a.scenario,a.ram)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2)+"\n")
    print(json.dumps({k:v for k,v in r.items() if k!="observed_rows"},indent=2))
