#!/usr/bin/env python3
"""Conservative browser offline-page X11 gate. Manual screenshot review remains required."""
import json,re,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit("Usage: verify_offline_v30.py results")
root=Path(sys.argv[1]);report={"schema":"Puppy50_v35_preseed_offline_browser_KVM","tiers":{},"all_apps_verified":False,"50mb_verified":False}
for ram in (256,384):
 f=root/f"ram_{ram}MiB"/"serial.log"
 s=f.read_text(errors="replace").replace("\r","") if f.exists() else ""
 scans=re.findall(r"PUPPY50_V28_WINDOW_SCAN_BEGIN scan=\d+(.*?)PUPPY50_V28_WINDOW_SCAN_END",s,re.S)
 reports=len(scans)
 title_present=any("PUPPY50 OFFLINE PAGE PROOF" in scan for scan in scans)
 original_gui=all(re.search("PUPPY50_TEST "+x+"=PASS",s) for x in ("Xorg","jwm","ROX-Filer","x11_socket"))
 result={"ram_allocated_mib":ram,"x11_gui_probe_pass":bool(original_gui),
         "real_scan_count":reports,"local_html_file_created": "PUPPY50_V30_OFFLINE_PAGE_CREATED" in s,
         "x11_offline_page_title_observed":title_present,
         "actual_rendered_pixels_verified":False,
         "all_apps_verified":False,"50mb_verified":False}
 report["tiers"][str(ram)]=result
(root/"v30_probe_result.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
if not all(v["x11_gui_probe_pass"] and v["local_html_file_created"] and v["real_scan_count"]>=2 for v in report["tiers"].values()):
 raise SystemExit("One or more guest startup probes incomplete; not an app success")
