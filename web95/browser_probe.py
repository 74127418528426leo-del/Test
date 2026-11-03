#!/usr/bin/env python3
"""Puppy50 v95 - real process PSS across one unprivileged Debian browser session.
This is a host/container benchmark, not a 384 MiB RAM-only guest measurement.
No browser sandbox, site isolation or TLS checks are disabled.
"""
import argparse,json,os,signal,subprocess,time
from pathlib import Path
BROWSERS={
 "dillo":["dillo"],"netsurf":["netsurf-gtk"],"links2":["links2","-g"],
 "cog":["cog","-P","x11"],"surf":["surf"],"luakit":["luakit"],
 "falkon":["falkon"],"firefox":["firefox-esr","--no-remote","--new-instance"],
 "epiphany":["epiphany"]}
SITES={"blank":"about:blank","example":"https://example.com/","wikipedia":"https://www.wikipedia.org/"}
def process_memory(uid,proc=Path("/proc"),exclude_pid=None):
    sums={"process_count":0,"pss_kib":0,"uss_kib":0,"rss_kib":0,"swap_kib":0,"pss_missing":0}
    for p in proc.iterdir():
        if not p.name.isdigit() or (exclude_pid is not None and p.name==str(exclude_pid)):continue
        try:
            status=(p/"status").read_text(errors="replace")
            if any(line.startswith("State:") and line.split()[1]=="Z" for line in status.splitlines()):continue
            uids=next(line for line in status.splitlines() if line.startswith("Uid:"))
            if int(uids.split()[2])!=uid:continue
            sums["process_count"]+=1
            sums["rss_kib"]+=next((int(line.split()[1]) for line in status.splitlines() if line.startswith("VmRSS:")),0)
            try:
                roll=(p/"smaps_rollup").read_text(errors="replace")
                vals={}
                for line in roll.splitlines():
                    if ":" not in line:continue
                    key,rest=line.split(":",1)
                    a=rest.split()
                    if a and a[0].isdigit():vals[key]=int(a[0])
                if "Pss" not in vals:raise ValueError("no process PSS")
                sums["pss_kib"]+=vals["Pss"]
                sums["uss_kib"]+=vals.get("Private_Clean",0)+vals.get("Private_Dirty",0)
                sums["swap_kib"]+=vals.get("Swap",0)
            except (OSError,ValueError):sums["pss_missing"]+=1
        except (OSError,ValueError,StopIteration):continue
    return sums
def owner_sample():
    """Root inside a GitHub Docker job may lack CAP_SYS_PTRACE across UIDs.
    Ask the SAME non-root account that owns the browser to read /proc smaps_rollup."""
    helper=Path(__file__).with_name("owner_probe.py")
    response=subprocess.run(["runuser","-u","p50","--","python3",str(helper)],
                            capture_output=True,text=True,timeout=15)
    if response.returncode:
        raise RuntimeError("PSS owner sampler failed: "+response.stderr[:350])
    return json.loads(response.stdout)
def run(browser,site,out,uid,seconds,display):
    out.mkdir(parents=True,exist_ok=True)
    command=[*BROWSERS[browser],SITES[site]]
    launch=["runuser","-u","p50","--","env",f"DISPLAY={display}",
        "HOME=/home/p50","XDG_RUNTIME_DIR=/tmp/p50-runtime",
        "dbus-run-session","--",*command]
    samples=[];screenshot=False
    with (out/f"{site}.log").open("wb") as log:
        proc=subprocess.Popen(launch,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        begin=time.monotonic()
        try:
            for target in sorted(set([x for x in (5,12,22,seconds) if x<=seconds])):
                while time.monotonic()-begin<target:time.sleep(.25)
                samples.append({"elapsed_seconds":target,**owner_sample()})
                if target==seconds:
                    shot=out/f"{site}.png"
                    v=subprocess.run(["scrot","-z",str(shot)],
                        env={**os.environ,"DISPLAY":display},
                        stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=12)
                    screenshot=bool(v.returncode==0 and shot.is_file() and shot.stat().st_size>1000)
        finally:
            if proc.poll() is None:
                try:os.killpg(proc.pid,signal.SIGTERM)
                except ProcessLookupError:pass
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                proc.wait(timeout=5)
            subprocess.run(["pkill","-KILL","-u","p50"],check=False,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            time.sleep(1)
    good=[x for x in samples if x["process_count"]>0 and x["pss_missing"]==0]
    return {"browser":browser,"scenario":site,"url":SITES[site],"command":command,
            "samples":samples,
            "peak_session_pss_mib":round(max(x["pss_kib"] for x in good)/1024,2) if good else None,
            "peak_session_uss_mib":round(max(x["uss_kib"] for x in good)/1024,2) if good else None,
            "screenshot_saved":screenshot,"site_visually_verified":False,
            "guest_RAM_only_OS_tested":False,
            "note":"Session PSS includes same-user DBus helpers; CPU and renderer depend on Xvfb."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--browser",choices=BROWSERS,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--uid",type=int,default=1550)
    p.add_argument("--seconds",type=int,default=30)
    p.add_argument("--display",default=":97")
    a=p.parse_args()
    if not 22<=a.seconds<=90:raise SystemExit("Invalid seconds")
    results=[]
    for site in SITES:
        r=run(a.browser,site,a.output,a.uid,a.seconds,a.display)
        results.append(r)
        (a.output/"partial_results.json").write_text(json.dumps(results,indent=2)+"\n")
        print(json.dumps({k:v for k,v in r.items() if k!="samples"}),flush=True)
    final={"schema":"PUPPY50_V95_HOST_LINUX_BROWSER_PSS_BAKEOFF",
           "browser":a.browser,"environment":"Debian 13 container + Xvfb 1280x800",
           "results":results,"real_site_render_verified":False,
           "not_a_full_384MiB_guest_test":True}
    (a.output/"result.json").write_text(json.dumps(final,indent=2)+"\n")
if __name__=="__main__":main()
