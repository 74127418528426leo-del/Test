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
            for mark in [95,145,165,185,205,245,args.seconds]:
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
                if mark==165:
                    try:
                        # v71 verified the QEMU pointer over the center
                        # Wikipedia card. Mozilla is its immediate right
                        # neighbor. The QEMU monitor mouse_move command is
                        # relative; capture a PRE-CLICK frame to independently
                        # verify the actual hovered destination.
                        # This QEMU guest exposes TWO pointer devices:
                        # PS/2 Mouse #2 and active absolute vmmouse #4.
                        # Relative HMP mouse_move did not move vmmouse;
                        # explicitly activate PS/2 before sending deltas.
                        before=hmp(monitor,"info mice")
                        chosen=hmp(monitor,"mouse_set 2")
                        after=hmp(monitor,"info mice")
                        if "Mouse #2: QEMU PS/2 Mouse" not in after or "* Mouse #2:" not in after:
                            raise RuntimeError("Could not activate QEMU PS/2 mouse: "+after[-450:])
                        reply=hmp(monitor,"mouse_move 220 0")
                        if any(t in reply.lower() for t in ("unknown command","invalid parameter","error:")):
                            raise RuntimeError("QEMU rejected mouse_move: "+reply[-250:])
                        report["mozilla_pointer_move_requested"]=True
                        report["explicit_ps2_mouse_selected"]=True
                        report["before_mouse_list"]=before[-400:]
                        report["after_mouse_list"]=after[-400:]
                        report["pointer_move_hmp_reply"]=reply[-250:]
                    except Exception as exc:
                        report["mozilla_pointer_move_requested"]=False
                        report["errors"].append("pointer move: "+repr(exc))
                if mark==185:
                    try:
                        trace=[]
                        for name in ["info mice","mouse_button 1","mouse_button 0"]:
                            reply=hmp(monitor,name)
                            trace.append({"command":name,"reply":reply[-200:]})
                            if any(t in reply.lower() for t in ("unknown command","invalid parameter","error:")):
                                raise RuntimeError("QEMU refused "+name)
                            time.sleep(0.35)
                        report["mouse_action_trace"]=trace
                        report["real_qemu_browser_link_click_submitted"]=True
                        time.sleep(10)
                    except Exception as exc:
                        report["real_qemu_browser_link_click_submitted"]=False
                        report["errors"].append("Mozilla link navigation: "+repr(exc))
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
    report["mouse_input_fix"]="explicit active PS/2 mouse_set 2 before mouse_move; previous active device was absolute vmmouse"
    report["Mozilla_preview_pointer_hover_frame"]="frame_165.ppm"

    report["public_external_website_retested_in_this_build"]=False
    report["other_sites_verified"]=False
    report["physical_wifi_supported"]=False
    (args.out/"result.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    checks=("ram_root_copy","ram_root_switch","ejected",
            "xorg_started","firefox_launch_requested","guest_DHCP","guest_DNS",
            "guest_public_CA_verified_HTTPS","guest_status_page_written",
            "timed_demo_not_requested","actual_user_homepage_visibly_rendered",
            "guest_did_not_exit_early","mozilla_pointer_move_requested","explicit_ps2_mouse_selected","real_qemu_browser_link_click_submitted")
    missing=[c for c in checks if report.get(c) is not True]
    if missing:raise SystemExit("PUPPY50_V72_FAIL_CLOSED: "+repr(missing))
if __name__=="__main__":
    main()
