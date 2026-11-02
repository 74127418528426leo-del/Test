#!/usr/bin/env python3
"""Conservative check of repeated guest X11 and memory telemetry.
A browser window is not claimed from a named 10x10 helper or a process.
"""
import json,re,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit("Usage: verify_threshold_v29.py real-results-directory")
base=Path(sys.argv[1]);data={"schema":"Puppy50-v29-browser-threshold","all_apps_verified":False,
 "50mb_verified":False,"tiers":{}}
for ram in [384,448]:
 p=base/f"ram_{ram}MiB"/"serial.log"
 txt=p.read_text(errors="replace").replace("\r","") if p.exists() else ""
 gui=re.search(r"PUPPY50_V25_BEGIN(.*?)PUPPY50_V25_END",txt,re.S)
 matches=list(re.finditer(r"PUPPY50_V28_WINDOW_SCAN_BEGIN scan=(\d+)(.*?)PUPPY50_V28_WINDOW_SCAN_END scan=\1",txt,re.S))
 d={"guest_gui_probe_complete":bool(gui),"x11_processes_present":False,"complete_x11_scans":len(matches),
    "firefox_process_detected":bool(re.search(r"\{firefox-bin\}|\{Web Content\}",txt)),
    "firefox_named_x11_object_detected":any(re.search(r'"Firefox"|firefox-esr',m.group(2),re.I) for m in matches),
    "large_visible_browser_window_verified":False, "all_apps_verified":False, "50mb_verified":False}
 if gui:d["x11_processes_present"]=all(re.search(r"PUPPY50_TEST "+re.escape(k)+r"=PASS",gui.group(1)) for k in ["Xorg","jwm","ROX-Filer","x11_socket"])
 data["tiers"][str(ram)]=d
print(json.dumps(data,indent=2))
(base/"v29_summary.json").write_text(json.dumps(data,indent=2)+"\n")
if not all(x["x11_processes_present"] and x["complete_x11_scans"]>=2 for x in data["tiers"].values()):
    raise SystemExit("At least one real guest failed the basic process/X11 telemetry gate")
