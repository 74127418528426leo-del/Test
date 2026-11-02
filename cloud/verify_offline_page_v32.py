#!/usr/bin/env python3
"""Fail-closed Firefox offline-page proof from real guest X11 and zram serial logs."""
from pathlib import Path
import json,re,sys
if len(sys.argv)!=2:raise SystemExit("Usage: verify_offline_page_v32.py results")
root=Path(sys.argv[1]); sfile=root/"ram_512MiB"/"serial.log"
s=sfile.read_text(errors="replace") if sfile.exists() else ""
w=re.findall(r"PUPPY50_V28_WINDOW_SCAN_BEGIN scan=(\d+)(.*?)PUPPY50_V28_WINDOW_SCAN_END",s,re.S)
render_scans=[n for n,body in w if "PUPPY50 V32 OFFLINE PAGE OK" in body]
z=re.findall(r"PUPPY50_V32_ZRAM_STAT scan=\d+\s*\n([0-9 ]+)",s)
last_zram=list(map(int,z[-1].split())) if z else []
m=re.findall(r"PUPPY50_V28_MEMORY scan=(\d+)(.*?)(?=PUPPY50_V28_WINDOW_SCAN_BEGIN|PUPPY50_V26_BROWSER_PROCS|\Z)",s,re.S)
last_memory=m[-1][1] if m else ""
swap_total=re.search(r"SwapTotal:\s+(\d+)",last_memory)
swap_free=re.search(r"SwapFree:\s+(\d+)",last_memory)
out={"schema":"puppy50_v32_offline_firefox_real_guest","ram_allocated_mib":512,
    "desktop_process_evidence":all(f"PUPPY50_TEST {x}=PASS" in s for x in ("Xorg","jwm","ROX-Filer","x11_socket")),
    "offline_file_created":"PUPPY50_V32_OFFLINE_PAGE_CREATED" in s,
    "window_scans":len(w),"specific_page_title_seen_in_x11":bool(render_scans),
    "page_title_scan_ids":render_scans,"actual_gui_screenshot_review_still_needed":True,
    "zram_physical_bytes":last_zram[2] if len(last_zram)>2 else None,
    "zram_uncompressed_bytes":last_zram[0] if len(last_zram)>0 else None,
    "swap_used_kib":int(swap_total[1])-int(swap_free[1]) if swap_total and swap_free else None,
    "interactive_click_tested":False,"full_application_suite_tested":False,"strict_50mb_verified":False}
(root/"v32_page_proof.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
if not(out["desktop_process_evidence"] and out["offline_file_created"] and out["specific_page_title_seen_in_x11"]):
    raise SystemExit("Actual guest offline-page title was NOT observed: no success claim")
