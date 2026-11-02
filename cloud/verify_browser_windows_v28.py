#!/usr/bin/env python3
"""Require actual guest-reported X11 Firefox windows; processes alone are not enough."""
import json,re,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit("Usage: verify_browser_windows_v28.py RESULTS_DIR")
root=Path(sys.argv[1]);result={"schema":"Puppy50_v28_X11_browser_window_proof","browser_interaction_verified":False,"50mb_verified":False,"cases":{}}
for ram in (512,256):
    f=root/f"ram_{ram}MiB"/"serial.log"
    s=f.read_text(errors="replace").replace("\r","") if f.exists() else ""
    gui=re.search(r"PUPPY50_V25_BEGIN(.*?)PUPPY50_V25_END",s,re.S)
    scans=re.findall(r"PUPPY50_V28_WINDOW_SCAN_BEGIN scan=(\d+)(.*?)PUPPY50_V28_WINDOW_SCAN_END",s,re.S)
    valid_window=[n for n,body in scans if re.search(r'0x[0-9a-f]+.*?(?:Firefox|Mozilla Firefox|firefox-esr)',body,re.I)]
    d={"ram_allocated_mib":ram,"gui_processes_present":False,"window_scan_count":len(scans),
       "browser_window_scans":valid_window,"firefox_window_proven":bool(valid_window),
       "browser_process_seen":bool(re.search(r'\{firefox-bin\}|\{firefox_esr\}',s)),
       "full_browser_interactive_verified":False,"50mb_verified":False}
    if gui:
        d["gui_processes_present"]=all(re.search(r"PUPPY50_TEST\s+"+ re.escape(x)+r"=PASS",gui.group(1))
          for x in ("Xorg","jwm","ROX-Filer","x11_socket"))
    result["cases"][str(ram)]=d
(root/"window_verification.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2),flush=True)
# A completed diagnostic run does not imply UI is functional; fail if no GUI/scan evidence.
if not all(x["gui_processes_present"] and x["window_scan_count"]>0 for x in result["cases"].values()):
    raise SystemExit("Missing actual graphical/scan evidence")
