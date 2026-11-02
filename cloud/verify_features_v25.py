#!/usr/bin/env python3
"""Fail closed: prove real guest markers and selected process checks, not full app UX."""
import json, re, sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit("Usage: verify_features_v25.py cloud-results")
base=Path(sys.argv[1])
report={"schema":"puppy50_v25_guest_feature_evidence","full_functionality_verified":False,"50mb_verified":False,"cases":{}}
for folder in sorted(base.glob("ram_*MiB")):
    f=folder/"serial.log"
    serial=f.read_text(errors="replace") if f.is_file() else ""
    match=re.search(r"PUPPY50_V25_BEGIN(.*?)PUPPY50_V25_END",serial,re.S)
    d={"guest_markers":bool(match),"ram_allocation_mib":int(folder.name.split("_")[1].replace("MiB","")),
       "test_pass":False,"memory_not_available_kib":None,"checks":{}}
    if match:
        payload=match.group(1)
        for key,val in re.findall(r"^PUPPY50_TEST\s+([\w-]+)=(PASS|FAIL|MISSING|NOT_VERIFIED|[01])$",payload,re.M):
            d["checks"][key]=val
        total=re.search(r"^MemTotal:\s+(\d+)",payload,re.M)
        avail=re.search(r"^MemAvailable:\s+(\d+)",payload,re.M)
        if total and avail:
            d["memory_not_available_kib"]=int(total.group(1))-int(avail.group(1))
        d["test_pass"]=all(d["checks"].get(k)=="PASS" for k in ("Xorg","jwm","ROX-Filer","x11_socket")) and d["memory_not_available_kib"] is not None
    report["cases"][folder.name]=d
    print(json.dumps({folder.name:d},indent=2))
(base/"feature_gate_summary.json").write_text(json.dumps(report,indent=2)+"\n")
if not report["cases"] or not all(x["test_pass"] for x in report["cases"].values()):
    print("At least one guest did not pass feature gate. Evidence saved.",file=sys.stderr)
    raise SystemExit(2)
