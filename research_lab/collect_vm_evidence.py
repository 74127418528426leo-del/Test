#!/usr/bin/env python3
"""Extract partial actual VM evidence, including failures, without weakening release gates.

Input: downloaded GitHub Actions artifact from guarded Puppy50 compare job.
Output is *diagnostic only*; it is NEVER a passing ISO proof.
"""
import argparse, json, math
from pathlib import Path

LABELS=("bios1","uefi1","bios2","uefi2")

def collect(root):
    root=Path(root)
    data={"schema":1,"source":"actual QEMU result.json artifacts, not release qualification",
          "observed_frames":{},"vm_failures":{},"ram_ready_seconds":{},
          "post_eject_http200_by_boot":{},"full_four_boot_result_available":False}
    for label in LABELS:
        files=list(root.rglob(label+"/result.json")) if root.exists() else []
        if len(files)>1:
            raise ValueError("ambiguous multiple result files for "+label)
        if not files:
            data["vm_failures"][label]="no QEMU result.json collected"
            continue
        try:
            obj=json.loads(files[0].read_text())
        except (OSError,ValueError) as e:
            data["vm_failures"][label]="invalid result.json"
            continue
        if not isinstance(obj,dict):
            data["vm_failures"][label]="non-object VM result"
            continue
        val=obj.get("first_home_seen_seconds")
        if type(val) in (int,float) and math.isfinite(val) and 0<val<600:
            data["observed_frames"][label]=round(float(val),3)
        else:
            data["vm_failures"][label]="real Firefox frame missing"
        ram=obj.get("staged_ram_ready_seconds")
        if type(ram) in (int,float) and math.isfinite(ram) and 0<ram<600:
            data["ram_ready_seconds"][label]=round(float(ram),3)
        ok=obj.get("post_eject_browser_http200_confirmed") is True
        data["post_eject_http200_by_boot"][label]=ok
        errors=obj.get("errors")
        if isinstance(errors,list) and errors:
            data["vm_failures"][label]="; ".join(str(x)[:180] for x in errors[:3])[:450]
        elif not ok:
            data["vm_failures"][label]="post-eject browser HTTP200 not confirmed"
    data["full_four_boot_result_available"]=len(data["observed_frames"])==4
    vals=list(data["observed_frames"].values())
    if vals:
        data["best_observed_frame_seconds"]=min(vals)
        data["worst_observed_frame_seconds"]=max(vals)
        data["four_frame_mean_seconds"]=round(sum(vals)/4,3) if len(vals)==4 else None
    data["functional_gates_passed"]=False
    data["verified_under_five_seconds"]=False
    return data

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    r=collect(a.source)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in r.items() if k not in ("ram_ready_seconds",)},indent=2))
if __name__=="__main__":
    main()
