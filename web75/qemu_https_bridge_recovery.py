#!/usr/bin/env python3
"""Real KVM smoke test for an interactive user-controlled Puppy50 home page.
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
import os
import signal
import sys
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
    a.add_argument("--bridge-pid-file",type=Path,required=True)
    a.add_argument("--bridge-script",type=Path,required=True)
    args=a.parse_args()
    args.iso=args.iso.resolve(strict=True);args.out.mkdir(parents=True,exist_ok=True)
    monitor=args.out/"hmp.sock"
    cmd=["qemu-system-x86_64","-machine","pc,accel=kvm","-cpu","host",
         "-m",str(args.ram),"-smp","2",
         "-drive",f"file={args.iso},if=ide,media=cdrom,id=puppycd,readonly=on",
         "-boot","order=d","-display","none","-vga","std",
         "-monitor",f"unix:{monitor},server=on,wait=off",
         "-serial",f"file:{args.out/'serial.log'}",
         "-netdev","user,id=puppynet,ipv6=off",
         "-device","e1000,netdev=puppynet,id=puppynic","-no-reboot"]
    report={"schema":"PUPPY50_V75_HOST_HTTPS_BRIDGE_RECOVERY",
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
                if mark in (165,185):
                    # Host network recovery experiment: interrupt the
                    # independently provisioned, loopback-only HTTPS bridge,
                    # then restore it with no change to QEMU/guest NIC.
                    try:
                        if mark==165:
                            pid=int(args.bridge_pid_file.read_text().strip())
                            command=Path(f"/proc/{pid}/cmdline").read_bytes()
                            if b"host_https_bridge.py" not in command:
                                raise RuntimeError("PID is not the expected host bridge; refusing to kill")
                            os.kill(pid,signal.SIGTERM)
                            for _ in range(35):
                                try:os.kill(pid,0)
                                except ProcessLookupError:break
                                time.sleep(.1)
                            # A zombie may remain until the launching shell
                            # reaps it; the actual socket must close.
                            disconnected=False
                            for _ in range(35):
                                with socket.socket() as sock:
                                    sock.settimeout(.3)
                                    if sock.connect_ex(("127.0.0.1",3128))!=0:
                                        disconnected=True;break
                                time.sleep(.2)
                            if not disconnected:raise RuntimeError("Host bridge socket did not close")
                            report["host_bridge_was_unavailable"]=True
                        else:
                            outfile=(args.out/"restarted-host-bridge.log").open("wb")
                            spawned=subprocess.Popen([sys.executable,"-u",str(args.bridge_script.resolve()),"--port","3128"],stdout=outfile,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
                            report["restarted_bridge_pid"]=spawned.pid
                            for _ in range(50):
                                if spawned.poll() is not None:break
                                with socket.socket() as sock:
                                    sock.settimeout(.3)
                                    if sock.connect_ex(("127.0.0.1",3128))==0:break
                                time.sleep(.2)
                            else:raise RuntimeError("Restarted host bridge did not begin listening")
                            if spawned.poll() is not None:
                                raise RuntimeError("Restarted host bridge exited")
                            report["host_bridge_restart_succeeded"]=True
                            # Host-side CA verification proves the restored
                            # upstream can connect before Firefox's guest
                            # navigation; it is NOT itself Firefox proof.
                            verified=subprocess.run(
                                ["curl","--fail","--silent","--show-error","--head",
                                 "--proxy","http://127.0.0.1:3128","--noproxy","",
                                 "--proto","=https","--connect-timeout","8",
                                 "--max-time","18","https://www.wikipedia.org/"],
                                capture_output=True,text=True,timeout=25)
                            report["restored_host_CA_HTTPS_ok"]=verified.returncode==0
                            if verified.returncode!=0:
                                report["errors"].append("post-restart host HTTPS failed: "+verified.stderr[-500:])
                    except Exception as exc:
                        report["errors"].append("host proxy interruption/restart: "+repr(exc))
                if mark==205:
                    try:
                        # The default QEMU pointer is in the centre of the
                        # 1920x1080 Firefox window. On v70 it hovers over the
                        # centre Wikipedia tile. Actual pixels determine if
                        # navigating the LINK changed the browser viewport.
                        names=["info mice","mouse_button 1","mouse_button 0"]
                        report["mouse_action_trace"]=[]
                        for name in names:
                            reply=hmp(monitor,name)
                            report["mouse_action_trace"].append({"command":name,"reply":reply[-200:]})
                            if any(t in reply.lower() for t in ("unknown command","invalid parameter","error:")):
                                raise RuntimeError("QEMU refused "+name)
                            time.sleep(0.4)
                        report["real_qemu_browser_link_click_submitted"]=True
                        time.sleep(12)
                    except Exception as exc:
                        report["real_qemu_browser_link_click_submitted"]=False
                        report["errors"].append("mouse link navigation: "+repr(exc))
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
            try:
                if 'spawned' in locals() and spawned.poll() is None:
                    spawned.terminate()
                    try:spawned.wait(timeout=5)
                    except subprocess.TimeoutExpired:spawned.kill();spawned.wait()
            except Exception as ex:
                report["errors"].append("host bridge cleanup: "+repr(ex))
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
    report["Wikipedia_link_pixel_transition"]={
        "before_homepage_cyan":before,
        "after_click_cyan":after,
        "homepage_color_disappeared":bool(before is not None and after is not None and before>0.025 and after<0.010)}
    report["Wikipedia_public_page_visually_confirmed"]=False
    report["guest_network_link_off_on_commands_submitted"]=False
    report["host_https_bridge_outage_and_recovery_verified"]=(
        report.get("host_bridge_was_unavailable") is True and
        report.get("host_bridge_restart_succeeded") is True and
        report.get("restored_host_CA_HTTPS_ok") is True
    )
    report["host_physical_network_transition_proven"]=False
    report["guest_adapter_was_left_unchanged"]=True
    report["guest_released_and_reacquired_DHCP_proven"]=False
    report["post_link_recovery_wikipedia_content_manually_reviewed"]=False

    report["public_external_website_retested_in_this_build"]=False
    report["other_sites_verified"]=False
    report["physical_wifi_supported"]=False
    (args.out/"result.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    checks=("ram_root_copy","ram_root_switch","ejected",
            "xorg_started","firefox_launch_requested","guest_DHCP","guest_DNS",
            "guest_public_CA_verified_HTTPS","guest_status_page_written",
            "timed_demo_not_requested","actual_user_homepage_visibly_rendered",
            "guest_did_not_exit_early","real_qemu_browser_link_click_submitted",
            "host_https_bridge_outage_and_recovery_verified")
    missing=[c for c in checks if report.get(c) is not True]
    if missing:raise SystemExit("PUPPY50_V75_FAIL_CLOSED: "+repr(missing))
if __name__=="__main__":
    main()
