#!/usr/bin/env python3
"""Puppy50 v96: real NetSurf Duktape ON/OFF under identical Linux/Xvfb conditions.
Root of test container is NOT the measurement process. PSS comes from same-UID
/proc/smaps_rollup via web95/owner_probe.py. Screenshots need actual review.
"""
import argparse,json,os,signal,subprocess,time
from pathlib import Path
PAGES=["01-execution.html","02-dom.html","03-modern.html","04-fetch.html","wikipedia"]
URLS={p:"http://127.0.0.1:8765/"+p for p in PAGES if p!="wikipedia"}
URLS["wikipedia"]="https://www.wikipedia.org/"
def settings(js):
    path=Path("/home/p50/.config/netsurf/Choices")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(f"enable_javascript:{1 if js else 0}\nscript_timeout:5\n")
    subprocess.run(["chown","-R","p50:p50","/home/p50/.config"],check=True)
    saved=path.read_text()
    assert ("enable_javascript:1" if js else "enable_javascript:0") in saved
    return saved
def sample():
    command=["runuser","-u","p50","--","env","PYTHONPATH=web95",
             "python3","web95/owner_probe.py"]
    p=subprocess.run(command,text=True,capture_output=True,timeout=12)
    if p.returncode:raise RuntimeError("same-user memory probe: "+p.stderr[:220])
    return json.loads(p.stdout)
def run_page(page,dir_,js,duration):
    url=URLS[page]
    env={"DISPLAY":":97","HOME":"/home/p50","XDG_RUNTIME_DIR":"/tmp/p50-runtime","XDG_CONFIG_HOME":"/home/p50/.config"}
    cmd=["runuser","-u","p50","--","env",*[f"{k}={v}" for k,v in env.items()],
         "dbus-run-session","--","netsurf-gtk",url]
    samples=[];image=False;error=None
    dir_.mkdir(parents=True,exist_ok=True)
    with (dir_/(page+".log")).open("wb") as log:
        p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        start=time.monotonic()
        try:
            for sec in [3,8,duration]:
                while time.monotonic()-start<sec:time.sleep(.25)
                try:samples.append({"time_seconds":sec,**sample()})
                except Exception as exc:samples.append({"time_seconds":sec,"probe_error":repr(exc)})
            screenshot=dir_/(page+".png")
            sc=subprocess.run(["scrot","-z",str(screenshot)],env={**os.environ,"DISPLAY":":97"},timeout=15)
            image=sc.returncode==0 and screenshot.is_file() and screenshot.stat().st_size>1000
        except Exception as exc:error=repr(exc)
        finally:
            if p.poll() is None:
                try:os.killpg(p.pid,signal.SIGTERM)
                except ProcessLookupError:pass
            try:p.wait(timeout=4)
            except subprocess.TimeoutExpired:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                p.wait(timeout=5)
            subprocess.run(["pkill","-KILL","-u","p50"],check=False,
                            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            time.sleep(.5)
    good=[v for v in samples if v.get("process_count",0)>0 and v.get("pss_missing",1)==0]
    return {"page":page,"url":url,"js_enabled_config":js,"memory_samples":samples,
        "peak_pss_mib":round(max(v["pss_kib"] for v in good)/1024,2) if good else None,
        "peak_uss_mib":round(max(v["uss_kib"] for v in good)/1024,2) if good else None,
        "screenshot_saved":image,"javascript_functionality_confirmed":False,
        "page_visually_confirmed":False,
        "browser_process_exited":p.returncode,"test_error":error}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--js",choices=["on","off"],required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--seconds",type=int,default=17)
    a=ap.parse_args()
    if not 9<=a.seconds<=40:raise SystemExit("Duration out of bounds")
    a.out.mkdir(parents=True,exist_ok=True)
    choices=settings(a.js=="on")
    print("BROWSER_OPTIONS="+choices.strip(),flush=True)
    rows=[]
    for page in PAGES:
        report=run_page(page,a.out,a.js=="on",a.seconds)
        rows.append(report)
        (a.out/"result.json").write_text(json.dumps({
            "schema":"PUPPY50_V96_NETSURF_JS_CONTROLLED_MEASUREMENTS",
            "javascript_config_value":a.js,
            "test_context":"Debian 13 Xvfb, local fixture HTTP for four pages, public HTTPS Wikipedia",
            "actual_javascript_success_not_assumed":True,
            "not_RAM_only_OS":True,
            "rows":rows
        },indent=2)+"\n")
        print(json.dumps({k:v for k,v in report.items() if k!="memory_samples"}),flush=True)
if __name__=="__main__":main()
