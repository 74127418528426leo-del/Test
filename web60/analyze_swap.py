#!/usr/bin/env python3
"""Interpret physical RAM zram device telemetry from actual guest serial logs.

zram's virtual SwapTotal is NOT physical RAM. Do not use it to calculate
extra physical capacity or claim browser rendering.
"""
import argparse
import json
import re
from pathlib import Path

STAT=re.compile(r"PUPPY50_V60_ZRAM_MM_STAT\s+(\d+)\s+(\d+)\s+(\d+)")
SWAP=re.compile(r"^SwapTotal:\s+(\d+) kB",re.M)

def analyze(serial):
    active="PUPPY50_V60_ZRAM_ACTIVE=PASS" in serial
    samples=[tuple(map(int,m)) for m in STAT.findall(serial)]
    loaded=any("PUPPY50_V46_DIRECT_INSMOD module=zram status=0" in x for x in serial.splitlines())
    swap_total=[int(x) for x in SWAP.findall(serial)]
    max_orig=max((o for o,c,m in samples),default=0)
    max_compr=max((c for o,c,m in samples),default=0)
    max_phys=max((m for o,c,m in samples),default=0)
    return {
        "schema":"PUPPY50_V60_ZRAM_MEMORY_ACCOUNTING",
        "early_zram_insmod_observed":loaded,
        "zram_swap_activated_in_guest":active,
        "zram_mm_stat_samples":len(samples),
        "largest_logical_swapped_mib":round(max_orig/1048576,3),
        "largest_sampled_compressed_data_mib":round(max_compr/1048576,3),
        "largest_sampled_physical_allocator_mib":round(max_phys/1048576,3),
        "largest_reported_swap_total_mib":round(max(swap_total,default=0)/1024,3),
        "zram_used_for_actual_pages":bool(max_orig>0 and max_phys>0),
        "sufficient_evidence_of_zram_swap_setup":bool(active and len(samples)>=2),
        "live_webpage_rendering_proven":False,
        "384mib_browser_functionality_proven":False,
        "scope":"Metrics sampled from the real Linux guest, not inferred from nominal zram disksize; physical RAM remains capped by QEMU."
    }

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("serial",type=Path)
    a.add_argument("--report",type=Path,required=True)
    args=a.parse_args()
    result=analyze(args.serial.read_text(errors='replace'))
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
