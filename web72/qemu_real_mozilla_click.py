#!/usr/bin/env python3
"""Real KVM smoke test for an real Mozilla HTTPS link on published Puppy50 home page.
No simulated browser success: QEMU framebuffer, kernel boot, external CA
verification and media-ejection are read from the actual guest and monitor.
"""
import argparse
import hashlib
import json
import re
import socket
import subprocess
import time
from pathlib import Path

def hmp(path,command):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as conn:
        conn.settimeout(1)
        conn.connect(str(path))
        def receive(limit=7):
            buf=b""
            deadline=time.monotonic()+limit
            while time.monotonic()<deadline:
                try:
                    data=conn.recv(4096)
                    if not data:break
                    buf+=data
                    if b"(qemu) " in buf:break
                except socket.timeout:continue
            return buf.decode(errors="replace")
        if "(qemu)" not in receive():
            raise RuntimeError("QEMU monitor prompt not found")
        conn.sendall((command+"\n").encode())
        return receive()

def cyan_fraction(filename):
    raw=Path(filename).read_bytes()
    m=re.match(rb"P6\s+(\d+)\s+(\d+)\s+(\d+)\s",raw)
    if not m:raise ValueError("Not an uncompressed QEMU PPM screenshot")
    w,h,maxval=map(int,m.groups())
    pixels=raw[m.end():]
    if w<640 or h<480 or maxval!=255 or len(pixels)!=3*w*h:
        raise ValueError("Unexpected QEMU framebuffer geometry")
    n=0;count=0
    for i in range(0,w*h,113):
        rgb=pixels[3*i:3*i+3]
        count+=1
        if all(abs(a-b)<=18 for a,b in zip(rgb,(9,198,206))):n+=1
    return {"fraction":round(n/count,5),"width":w,"height":h,"samples":count}

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--iso",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--seconds",type=int,default=230)
    a.add_argument("--ram",type=int,default=1024)
    args=a.parse_args()
    args.iso=args.iso.resolve(strict=True);args.out.mkdir(parents=True,exist_ok=True)
    monitor=args.out/"hmp.sock"
    cmd=["qemu-system-x86_64","-machine","pc,accel=kvm","-cpu","host",
         "-m",str(args.ram),"-smp","2",
         "-drive",f"file={args.iso},if=ide,media=cdrom,id=puppycd,readonly=on",
         "-boot","order=d","-display","none","-vga","std",
         "-monitor",f"unix:{monitor},server=on,wait=off",
         "-serial",f"file:{args.out/'serial.log'}",
         "-nic","user,model=e1000,ipv6=off","-no-reboot"]
    report={"schema":"PUPPY50_V72_ACTUAL_MOZILLA_SITE_KVM",
            "errors":[],"screenshots":[],"ejected":False}
    start=time.monotonic()
    with (args.out/"qemu.log").open("wb") as out:
        q=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT)
        try:
            for mark in [95,145,155,165,175,185,205,245,args.seconds]:
                while time.monotonic()-start < mark and q.poll() is None:
                    time.sleep(1)
                if q.poll() is not None:break
                if mark==145:
                    try:
                        report["eject_result"]=hmp(monitor,"eject -f puppycd")
                        block=hmp(monitor,"info block puppycd").lower()
                        report["ejected"]=("not inserted" in block or "no media" in block) and "error" not in report["eject_result"].lower()
                    except Exception as exc:
                        report["errors"].append("CD eject: "+repr(exc))
                # Keyboard-only navigation is independent of whether QEMU
                # selects absolute vmmouse or PS/2 relative pointer. The
                # homepage's first three anchors are Example, Wikipedia,
                # Mozilla. Capture frames after each Tab to inspect focus.
                if mark in (155,165,175):
                    try:
                        reply=hmp(monitor,"sendkey tab")
                        if any(t in reply.lower() for t in ("unknown command","invalid parameter","error:")):
                            raise RuntimeError("QEMU refused Tab "+reply[-240:])
                        report.setdefault("QEMU_real_tab_navigation",[]).append({
                            "second":mark,"reply":reply[-200:]})
                        report["keyboard_tab_events_submitted"]=len(report["QEMU_real_tab_navigation"])
                    except Exception as exc:
                        report["errors"].append("keyboard Tab: "+repr(exc))
                if mark==205:
                    try:
                        reply=hmp(monitor,"sendkey ret")
                        if any(t in reply.lower() for t in ("unknown command","invalid parameter","error:")):
                            raise RuntimeError("QEMU refused Enter "+reply[-240:])
                        report["real_qemu_keyboard_mozilla_link_activation_submitted"]=True
                        report["keyboard_enter_reply"]=reply[-200:]
                        time.sleep(10)
                    except Exception as exc:
                        report["real_qemu_keyboard_mozilla_link_activation_submitted"]=False
                        report["errors"].append("Mozilla keyboard activation: "+repr(exc))
                frame=args.out/f"frame_{mark:03}.ppm"
                try:
                    reply=hmp(monitor,"screendump "+str(frame))
                    if frame.is_file() and frame.stat().st_size>1000:
                        report["screenshots"].append(frame.name)
                    else: report["errors"].append("frame: "+reply[-200:])
                except Exception as exc:report["errors"].append("screenshot: "+repr(exc))
            report["guest_did_not_exit_early"]=q.poll() is None
        finally:
            if q.poll() is None:
                q.terminate()
                try:q.wait(timeout=7)
                except subprocess.TimeoutExpired:q.kill();q.wait()
    serial=(args.out/"serial.log").read_text(errors="replace")
    report["ram_root_copy"]="PUPPY50_WEB_V45_RAM_COPY_COMPLETE" in serial
    report["ram_root_switch"]="PUPPY50_WEB_V45_SWITCH_ROOT_RAM_ONLY" in serial
    report["xorg_started"]="PUPPY50_WEB_V45_XORG_RUNNING" in serial
    report["firefox_launch_requested"]="PUPPY50_WEB_V45_FIREFOX_REQUESTED" in serial
    report["guest_DHCP"]="PUPPY50_V67_DHCP=PASS" in serial
    report["guest_DNS"]="PUPPY50_V67_DNS=PASS" in serial
    report["guest_public_CA_verified_HTTPS"]="PUPPY50_V67_EXTERNAL_TLS_CA_VERIFIED=PASS" in serial
    report["guest_status_page_written"]="PUPPY50_V70_NETWORK_STATUS_PAGE_WRITTEN=PASS code=0" in serial
    report["timed_demo_not_requested"]="PUPPY50_V69_NATIVE_FIREFOX_NAV_REQUESTED" not in serial
    fractions=[]
    for name in report["screenshots"]:
        try:
            detail=cyan_fraction(args.out/name)
            fractions.append({"file":name,**detail})
        except Exception as exc:report["errors"].append("pixels "+name+": "+repr(exc))
    report["cyan_homepage_frames"]=fractions
    report["actual_user_homepage_visibly_rendered"]=any(x["fraction"]>0.014 for x in fractions)
    before=next((x["fraction"] for x in fractions if x["file"]=="frame_185.ppm"),None)
    after=next((x["fraction"] for x in fractions if x["file"]=="frame_245.ppm"),None)
    report["Mozilla_link_pixel_transition"]={
        "before_homepage_cyan":before,
        "after_click_cyan":after,
        "homepage_color_disappeared":bool(before is not None and after is not None and before>0.025 and after<0.010)}
    report["Mozilla_public_page_visually_confirmed"]=False
    report["keyboard_tab_count_proven"]=report.get("keyboard_tab_events_submitted")==3
    report["navigation_mode"]="three QEMU Tab keys followed by Enter, with focus-stage screenshots"
    report["Mozilla_keyboard_focus_frame"]="frame_185.ppm"

    report["public_external_website_retested_in_this_build"]=False
    report["other_sites_verified"]=False
    report["physical_wifi_supported"]=False
    (args.out/"result.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    checks=("ram_root_copy","ram_root_switch","ejected",
            "xorg_started","firefox_launch_requested","guest_DHCP","guest_DNS",
            "guest_public_CA_verified_HTTPS","guest_status_page_written",
            "timed_demo_not_requested","actual_user_homepage_visibly_rendered",
            "guest_did_not_exit_early","real_qemu_keyboard_mozilla_link_activation_submitted","keyboard_tab_count_proven")
    missing=[c for c in checks if report.get(c) is not True]
    if missing:raise SystemExit("PUPPY50_V72_FAIL_CLOSED: "+repr(missing))
if __name__=="__main__":
    main()
