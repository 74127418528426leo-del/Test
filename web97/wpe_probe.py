#!/usr/bin/env python3
"""WPE 2.54 modern-JS PSS via same UID. Compare only as headless research data."""
import json,os,signal,subprocess,time,argparse
from pathlib import Path
def memory():
    p=subprocess.run(["runuser","-u","p50","--","env","PYTHONPATH=web95",
                      "python3","web95/owner_probe.py"],
                     text=True,capture_output=True,timeout=12)
    if p.returncode:raise RuntimeError(p.stderr[:250])
    return json.loads(p.stdout)
def run(out,url,seconds):
    out.mkdir(parents=True,exist_ok=True)
    cmd=["runuser","-u","p50","--","env","WPE_PLATFORM=headless",
         "HOME=/home/p50","XDG_RUNTIME_DIR=/tmp/p50-runtime",
         "LIBGL_ALWAYS_SOFTWARE=1","/usr/local/bin/p50-wpeprobe",url]
    samples=[]
    with (out/"engine.log").open("wb") as log:
        p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        start=time.monotonic()
        try:
            for n in [5,12,20,seconds]:
                while time.monotonic()-start<n:time.sleep(.3)
                try:samples.append({"time_seconds":n,**memory()})
                except Exception as exc:samples.append({"time_seconds":n,"error":repr(exc)})
        finally:
            if p.poll() is None:
                try:os.killpg(p.pid,signal.SIGTERM)
                except ProcessLookupError:pass
            try:p.wait(timeout=6)
            except subprocess.TimeoutExpired:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                p.wait(timeout=5)
    logs=(out/"engine.log").read_text(errors="replace")
    goods=[r for r in samples if r.get("process_count",0)>0 and r.get("pss_missing",1)==0]
    result={
      "schema":"PUPPY50_V97_WPE_2_54_HEADLESS_MODERN_JS_MEASURE",
      "platform":"WPE_PLATFORM=headless; no graphical output; Debian forky",
      "url":url,"process_exit_code":p.returncode,"samples":samples,
      "peak_observed_pss_mib":round(max(r["pss_kib"] for r in goods)/1024,2) if goods else None,
      "peak_observed_uss_mib":round(max(r["uss_kib"] for r in goods)/1024,2) if goods else None,
      "modern_js_and_dom_ran":"P50_WPE_MODERN_JS_EVAL_RESULT=MODERN_JS_2,4,6_DOM_ES2015_EXECUTED" in logs,
      "load_finished":"P50_WPE_WEBVIEW_LOAD_FINISHED" in logs,
      "real_webpage_visually_confirmed":False,
      "not_actual_384_mib_guest_or_gui":True,
      "tls_checks_disabled":False,
      "sandbox_disabled":False}
    (out/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="samples"},indent=2))
    if not result["modern_js_and_dom_ran"]:raise SystemExit("WPE_JS_RUNTIME_NOT_PROVEN")
    if result["peak_observed_pss_mib"] is None:raise SystemExit("MISSING_REAL_PSS")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--url",default="http://127.0.0.1:8765/03-modern.html")
    ap.add_argument("--seconds",type=int,default=25)
    a=ap.parse_args()
    assert 20<=a.seconds<=30
    run(a.out,a.url,a.seconds)
if __name__=="__main__":main()
