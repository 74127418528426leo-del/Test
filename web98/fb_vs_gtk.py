#!/usr/bin/env python3
"""Puppy50 v98: same Debian, same Xvfb, NetSurf GTK vs framebuffer frontend.
Both use JavaScript ON. Browser session PSS measured from its own UID.
This DOES NOT measure the OS kernel/X server or prove 384MiB RAM-only boot.
"""
import argparse,json,os,signal,subprocess,time
from pathlib import Path
URLS={"basic_js":"http://127.0.0.1:8765/01-execution.html",
      "wikipedia":"https://www.wikipedia.org/"}
def cmd(frontend,url):
    if frontend=="fb":
        return ["netsurf-fb","--enable_javascript=1","-f","x","-w","760","-h","560","-b","32",url]
    if frontend=="gtk":
        return ["netsurf-gtk",url]
    raise ValueError(frontend)
def same_user_pss():
    p=subprocess.run(["runuser","-u","p50","--","env","PYTHONPATH=web95",
       "python3","web95/owner_probe.py"],capture_output=True,text=True,timeout=15)
    if p.returncode:raise RuntimeError("Missing same-UID PSS: "+p.stderr[:240])
    return json.loads(p.stdout)
def one(frontend,site,out,duration):
    url=URLS[site]
    profile=out/frontend;profile.mkdir(parents=True,exist_ok=True)
    env=["DISPLAY=:97","HOME=/home/p50","XDG_CONFIG_HOME=/home/p50/.config",
         "XDG_RUNTIME_DIR=/tmp/p50-runtime"]
    argv=["runuser","-u","p50","--","env",*env,
          "dbus-run-session","--",*cmd(frontend,url)]
    samples=[];error=None
    with (profile/(site+".log")).open("wb") as log:
        p=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        start=time.monotonic()
        try:
            for n in [4,10,duration]:
                while time.monotonic()-start<n:time.sleep(.2)
                try:samples.append({"seconds":n,**same_user_pss()})
                except Exception as exc:samples.append({"seconds":n,"error":repr(exc)})
            shot=profile/(site+".png")
            subprocess.run(["scrot","-z",str(shot)],env={**os.environ,"DISPLAY":":97"},timeout=12)
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
    good=[x for x in samples if x.get("process_count",0)>0 and x.get("pss_missing",1)==0]
    screenshot=profile/(site+".png")
    return {"frontend":frontend,"site":site,"url":url,"js_requested":True,
      "peak_pss_mib":round(max(x["pss_kib"] for x in good)/1024,2) if good else None,
      "peak_uss_mib":round(max(x["uss_kib"] for x in good)/1024,2) if good else None,
      "samples":samples,"valid_screenshot":screenshot.exists() and screenshot.stat().st_size>1000,
      "js_execute_verified_in_image":False,"https_site_verified_in_image":False,
      "runner_error":error,"not_384_mib_full_OS_test":True}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--seconds",type=int,default=17)
    a=p.parse_args()
    assert 12<=a.seconds<=30
    a.out.mkdir(parents=True,exist_ok=True)
    prefs=Path("/home/p50/.config/netsurf/Choices")
    prefs.parent.mkdir(parents=True,exist_ok=True)
    prefs.write_text("enable_javascript:1\n")
    subprocess.run(["chown","-R","p50:p50","/home/p50/.config"],check=True)
    results=[]
    for frontend in ["gtk","fb"]:
        for page in URLS:
            row=one(frontend,page,a.out,a.seconds)
            results.append(row)
            (a.out/"results.json").write_text(json.dumps({
              "schema":"PUPPY50_V98_NETSURF_FF_X_VS_GTK_SAME_DISPLAY",
              "measurement":"same-user browser-session PSS, Xvfb 800x600, JavaScript ON",
              "results":results,"real_visual_review_required":True
            },indent=2)+"\n")
            print(json.dumps({k:v for k,v in row.items() if k!="samples"}),flush=True)
if __name__=="__main__":main()
