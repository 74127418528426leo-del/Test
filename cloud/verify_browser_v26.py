#!/usr/bin/env python3
"""Puppy50 v26: fail-closed check for original GUI plus browser-launch evidence."""
import json, re, sys
from pathlib import Path
if len(sys.argv)!=2: raise SystemExit("Usage: python3 verify_browser_v26.py results-directory")
root=Path(sys.argv[1]); summary={"schema":"Puppy50_v26_disposable_VM_app_smoke","50_mb_verified":False,
    "interactive_browser_verified":False,"cases":{}}
for ram in (384,256):
    serialpath=root/f"ram_{ram}MiB"/"serial.log"
    s=serialpath.read_text(errors="replace") if serialpath.exists() else ""
    gui=re.search(r"PUPPY50_V25_BEGIN(.*?)PUPPY50_V25_END",s,re.S)
    app=re.search(r"PUPPY50_V26_BEGIN(.*?)PUPPY50_V26_END",s,re.S)
    d={"gui_report_complete":bool(gui),"browser_report_complete":bool(app),
       "gui_processes_verified":False,"browser_requested":False,
       "browser_process_seen":False,"browser_interactive_verified":False,
       "50_mb_verified":False}
    if gui:
        d["gui_processes_verified"]=all(re.search(r"PUPPY50_TEST\s+"+ re.escape(x) +r"=PASS",gui.group(1))
          for x in ("Xorg","jwm","ROX-Filer","x11_socket"))
    if app:
        body=app.group(1)
        req=re.search(r"PUPPY50_V26_BROWSER_REQUEST\s+(\S+)",body)
        d["browser_requested"]=bool(req and req.group(1) not in ("NONE","NO_GUI"))
        ps=re.search(r"PUPPY50_V26_BROWSER_PROCS(.*?)PUPPY50_V26_MEM_AFTER_BROWSER",body,re.S)
        d["browser_process_seen"]=bool(ps and re.search(r"firefox|chromium|seamonkey",ps.group(1),re.I))
    summary["cases"][f"{ram}MiB"]=d
    print(json.dumps({f"{ram}MiB":d},indent=2),flush=True)
summary["all_gui_screens_verified"]=all(x["gui_processes_verified"] for x in summary["cases"].values())
summary["all_browser_launch_requests"]=all(x["browser_requested"] for x in summary["cases"].values())
summary["browser_process_evidence_in_each_vm"]=all(x["browser_process_seen"] for x in summary["cases"].values())
root.joinpath("v26_experiment.json").write_text(json.dumps(summary,indent=2)+"\n")
if not summary["all_gui_screens_verified"] or not summary["all_browser_launch_requests"] or not summary["browser_process_evidence_in_each_vm"]:
    raise SystemExit("One or more functional evidence gates failed. Raw logs were saved.")
