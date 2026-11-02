#!/usr/bin/env python3
"""Puppy50 v36: fail-closed serial evidence for one 384 MiB browser-cache A/B trial.

Metrics describe a running Linux guest, not total physical RAM occupied.
One boot per condition cannot prove general performance improvement.
"""
import argparse, json, re, statistics
from pathlib import Path

def _block(s,begin,end):
    i=s.find(begin)
    if i<0:return ""
    j=s.find(end,i+len(begin))
    if j<0:return ""
    return s[i+len(begin):j]

def _mem(block,key):
    m=re.search(r"^"+re.escape(key)+r":\s*(\d+)\s+kB",block,re.M)
    return int(m.group(1)) if m else None

def analyze(s):
    s=s.replace("\r","")
    scans=[]
    for m in re.finditer(r"PUPPY50_V28_WINDOW_SCAN_BEGIN scan=(\d+)",s):
        n=int(m.group(1))
        nextm=re.search(r"PUPPY50_V28_WINDOW_SCAN_BEGIN scan=\d+|PUPPY50_V26_END",s[m.end():])
        part=s[m.end():m.end()+nextm.start()] if nextm else s[m.end():]
        end=f"PUPPY50_V28_WINDOW_SCAN_END scan={n}"
        if end not in part:continue
        win=part.split(end,1)[0]
        info=part.split(end,1)[1]
        m2=re.search(r"PUPPY50_V29_ZRAM scan="+str(n)+r"\s*\n\s*(\d+)\s+(\d+)\s+(\d+)",info)
        psi=re.search(r"PUPPY50_V29_MEM_PRESSURE scan="+str(n)+r"\s*\nsome avg10=([0-9.]+).*?\nfull avg10=([0-9.]+)",info,re.S)
        # Distinguish Firefox helper windows from large top-level browser windows.
        x11=[]
        for line in win.splitlines():
            if re.search(r"firefox|mozilla",line,re.I) and re.search(r"\b\d+x\d+[+-]\d+[+-]\d+",line):
                size=re.search(r"(\d+)x(\d+)[+-]\d+[+-]\d+",line)
                if size:x11.append({"width":int(size.group(1)),"height":int(size.group(2)),"line":line.strip()[:240]})
        scans.append({
            "scan":n,
            "swap_used_mib":round((_mem(info,"SwapTotal")-_mem(info,"SwapFree"))/1024,3) if _mem(info,"SwapTotal") is not None and _mem(info,"SwapFree") is not None else None,
            "nonavailable_mib":round((_mem(info,"MemTotal")-_mem(info,"MemAvailable"))/1024,3) if _mem(info,"MemTotal") is not None and _mem(info,"MemAvailable") is not None else None,
            "zram_physical_mib":round(int(m2.group(3))/1048576,3) if m2 else None,
            "psi_some_avg10":float(psi.group(1)) if psi else None,
            "psi_full_avg10":float(psi.group(2)) if psi else None,
            "firefox_x11_windows":x11,
            "large_named_firefox_window":any(x["width"]>=450 and x["height"]>=280 for x in x11),
        })
    gui=_block(s,"PUPPY50_V25_BEGIN","PUPPY50_V25_END")
    gui_pass=all(re.search(r"PUPPY50_TEST\s+"+re.escape(k)+r"=PASS",gui) for k in ("Xorg","jwm","ROX-Filer","x11_socket"))
    complete=len(scans)>=4 and gui_pass and all(x["swap_used_mib"] is not None and x["zram_physical_mib"] is not None and x["psi_full_avg10"] is not None for x in scans[-3:])
    return {"real_guest_gui_proven":bool(gui_pass),"complete_memory_telemetry":bool(complete),"scans":scans,
            "large_firefox_x11_window_observed":any(x["large_named_firefox_window"] for x in scans),
            "actual_html_pixels_verified":False,
            "long_term_responsiveness_verified":False}

def compare(a,b):
    d={"schema":"PUPPY50_V36_384MIB_BROWSER_CACHE_A_B",
       "guest_RAM_immutable_mib":384,
       "control":a,"cache_capped_8mib":b,
       "one_boot_per_condition_preliminary_only":True,
       "all_applications_functionally_verified":False,
       "strict_50MB_memory_achieved":False}
    if a["complete_memory_telemetry"] and b["complete_memory_telemetry"]:
        x=a["scans"][-3:];y=b["scans"][-3:]
        metrics=("swap_used_mib","zram_physical_mib","psi_some_avg10","psi_full_avg10","nonavailable_mib")
        d["last_3_sample_medians"]={key:{"control":round(statistics.median(q[key] for q in x),3),
                   "capped":round(statistics.median(q[key] for q in y),3)} for key in metrics}
        d["observed_swap_reduction_mib"]=round(d["last_3_sample_medians"]["swap_used_mib"]["control"]-d["last_3_sample_medians"]["swap_used_mib"]["capped"],3)
        d["proven_general_improvement"]=False
    else:
        d["comparison_refused_reason"]="At least one guest lacks complete X11 and memory pressure telemetry."
    return d

def main():
    p=argparse.ArgumentParser()
    p.add_argument("control",type=Path)
    p.add_argument("capped",type=Path)
    p.add_argument("--output",type=Path,default=Path("v36_comparison.json"))
    args=p.parse_args()
    result=compare(analyze(args.control.read_text(errors="replace") if args.control.is_file() else ""),
                   analyze(args.capped.read_text(errors="replace") if args.capped.is_file() else ""))
    args.output.parent.mkdir(exist_ok=True,parents=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("control","cache_capped_8mib")},indent=2))
    return 0 if result["control"]["complete_memory_telemetry"] and result["cache_capped_8mib"]["complete_memory_telemetry"] else 3
if __name__=="__main__":raise SystemExit(main())
