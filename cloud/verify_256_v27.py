#!/usr/bin/env python3
"""Fail closed: read real serial output from 256MiB Puppy experiment."""
import json,re,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit("Usage: verify_256_v27.py result_dir")
root=Path(sys.argv[1]);folder=root/"ram_256MiB"
f=folder/"serial.log"
s=f.read_text(errors="replace") if f.exists() else ""
gui=re.search(r"PUPPY50_V25_BEGIN(.*?)PUPPY50_V25_END",s,re.S)
browser=re.search(r"PUPPY50_V26_BEGIN(.*?)PUPPY50_V26_END",s,re.S)
d={"schema":"Puppy50_v27_reversible_indexing_scheduling","ram_allocated_MiB":256,
   "gui_guest_proven":False,"browser_launcher_requested":False,"browser_process_observed":False,
   "indexer_defer_hook_scheduled": "PUPPY50_INDEX_DEFERRED scheduled" in s,
   "indexer_defer_hook_started": "PUPPY50_INDEX_DEFERRED starting" in s,
   "indexer_completed": "PUPPY50_INDEX_DEFERRED exit=" in s,
   "all_applications_interactive_verified":False,"stable_idle_RAM_MiB":None,"50mb_verified":False}
if gui:d["gui_guest_proven"]=all(re.search(r"PUPPY50_TEST\s+"+x+"=PASS",gui.group(1))
   for x in ["Xorg","jwm","ROX-Filer","x11_socket"])
if browser:
    d["browser_launcher_requested"]=bool(re.search(r"PUPPY50_V26_BROWSER_REQUEST\s+(?!NONE|NO_GUI)\S+",browser.group(1)))
    ps=re.search(r"PUPPY50_V26_BROWSER_PROCS(.*?)PUPPY50_V26_MEM_AFTER_BROWSER",browser.group(1),re.S)
    d["browser_process_observed"]=bool(ps and re.search(r"firefox|chromium|seamonkey",ps.group(1),re.I))
(root/"v27_verified.json").write_text(json.dumps(d,indent=2)+"\n")
print(json.dumps(d,indent=2))
if not(d["gui_guest_proven"] and d["indexer_defer_hook_scheduled"]):
    raise SystemExit("Missing required guest functionality or delayed indexer evidence")
