#!/usr/bin/env python3
"""Puppy50 v102 - actual Pexels 3840x2160 source video in real Firefox/ QEMU.

Separate claims:
  source metadata 3840x2160 is a Pexels claim;
  native Firefox video.videoWidth/videoHeight are visible only through REAL
  guest Web Console QEMU screenshots and require independent review;
  live frame advancement is distinct from simply opening a page.
No proxies bypass a challenge, DRM, sandbox, TLS validation or login.
"""
import argparse,json,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from web85.qemu_debian_live_smoke import qmp,ppm_valid
from web101.site_test import send_key,type_text,goto as original_goto

URL="https://www.pexels.com/video/riverside-27251986/"
EXPR={
 "readyState":"document.querySelector('video').readyState",
 "videoWidth":"document.querySelector('video').videoWidth",
 "videoHeight":"document.querySelector('video').videoHeight",
 "play":"document.querySelector('video').play()",
 "currentTime":"document.querySelector('video').currentTime",
 "totalFrames":"document.querySelector('video').getVideoPlaybackQuality().totalVideoFrames",
 "droppedFrames":"document.querySelector('video').getVideoPlaybackQuality().droppedVideoFrames",
}
def navigation(mon):
    send_key(mon,['ctrl','l'],125)
    time.sleep(1.0)
    type_text(mon,URL,.095)
    send_key(mon,['ret'],110)
def screenshot(mon,out,mark,d):
    p=out/f"frame_{mark:03d}.ppm"
    qmp(mon,"screendump",{"filename":str(p)})
    if not p.is_file() or not ppm_valid(p):
        raise RuntimeError("Real QEMU framebuffer missing at "+str(mark))
    d['frames'].append(p.name)
def console_eval(mon,expression):
    # Firefox Web Console; no shell / Firefox remote debugging enabled.
    # This types into a real non-root Firefox GUI and preserves raw screenshot.
    type_text(mon,expression,.080)
    send_key(mon,['ret'],110)
def marker_until(start,seconds,proc):
    while time.monotonic()-start < seconds and proc.poll() is None:
        time.sleep(.35)
    if proc.poll() is not None:raise RuntimeError("QEMU unexpectedly exited before "+str(seconds))
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--iso",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--ram",type=int,default=4096)
    a=ap.parse_args()
    if a.ram!=4096:raise ValueError("Use fixed 4096 MiB for comparable 4K validation")
    iso=a.iso.resolve(strict=True)
    if iso.stat().st_size <900_000_000:raise ValueError("Full Debian Live Firefox ISO not supplied")
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    mon=out/"qmp.sock"
    cmd=["qemu-system-x86_64","-machine","pc,accel=kvm","-cpu","host",
         "-m",str(a.ram),"-smp","2",
         "-drive",f"file={iso},if=ide,media=cdrom,id=livecd,readonly=on",
         "-boot","order=d","-display","none","-vga","std",
         "-qmp",f"unix:{mon},server=on,wait=off",
         "-serial",f"file:{out/'serial.log'}",
         "-nic","user,model=e1000,ipv6=off","-no-reboot"]
    data={"schema":"PUPPY50_V102_PEXELS_REAL_VIDEO_4K_KVM",
          "url":URL,"source_published_width":3840,"source_published_height":2160,
          "source_published_fps":29.97,"guest_ram_mib":a.ram,
          "actual_guest_4k_playback_verified":False,
          "actual_guest_video_playback_verified":False,
          "actual_guest_page_visible_verified":False,
          "guest_resolution_reported_by_video_element":None,
          "guest_fps_measured":None,
          "guest_HTTPS_CA_pass":False,"nonroot_firefox_process":False,
          "boot_media_ejected":False,"guest_remained_running":False,
          "frames":[],"browser_devtools_commands":[],"errors":[]}
    with (out/"qemu.log").open("wb") as log:
        p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
        start=time.monotonic()
        try:
            marker_until(start,18,p)
            send_key(mon,['ret'],110)
            marker_until(start,110,p)
            screenshot(mon,out,110,data)
            marker_until(start,148,p)
            navigation(mon)
            data["actual_website_url_submitted_via_real_keyboard"]=True
            for mark in [230,285]:
                marker_until(start,mark,p);screenshot(mon,out,mark,data)
            marker_until(start,300,p)
            try:
                qmp(mon,"human-monitor-command",{"command-line":"eject -f livecd"})
                blk=str(qmp(mon,"human-monitor-command",{"command-line":"info block livecd"})).lower()
                data["boot_media_ejected"]=("not inserted" in blk or "no media" in blk)
            except Exception as exc:
                data["errors"].append("boot media eject: "+repr(exc))
            marker_until(start,318,p)
            screenshot(mon,out,318,data)
            marker_until(start,330,p)
            send_key(mon,['ctrl','shift','k'],155)  # Real Firefox Web Console
            time.sleep(5)
            screenshot(mon,out,335,data)
            # Evaluate native video details; do not treat submitting as proving output.
            for mark,key in [(350,'readyState'),(375,'videoWidth'),(400,'videoHeight'),
                             (421,'play'),(450,'currentTime'),(475,'totalFrames'),
                             (500,'droppedFrames')]:
                marker_until(start,mark-10,p)
                try:
                    console_eval(mon,EXPR[key])
                    data["browser_devtools_commands"].append(
                        {"kind":key,"expression":EXPR[key],"typed":True,
                         "actual_result_manually_verified":False})
                except Exception as exc:
                    data["errors"].append("Devtools command "+key+": "+repr(exc))
                marker_until(start,mark,p)
                screenshot(mon,out,mark,data)
            data["guest_remained_running"]=p.poll() is None
        except Exception as exc:
            data["errors"].append("guest automation: "+repr(exc))
        finally:
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=10)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
    serial=(out/"serial.log").read_text(errors="replace") if (out/"serial.log").exists() else ""
    data["guest_HTTPS_CA_pass"]=(
        "PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_DIRECT=PASS" in serial or
        "PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_BRIDGE=PASS" in serial)
    data["nonroot_firefox_process"]="P50_V91_NONROOT_FIREFOX_PROCESS_SEEN" in serial
    (out/"result.json").write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps(data,indent=2),flush=True)
    # True guest boot and diagnostic frames are the automated acceptance gate.
    # Site loading, decoded 2160p, and sustained FPS need actual on-screen evidence.
    if not data["guest_HTTPS_CA_pass"] or not data["nonroot_firefox_process"]:
        raise SystemExit("Guest Firefox or verified HTTPS baseline failed")
    if "frame_318.ppm" not in data["frames"]:
        raise SystemExit("Missing unmodified pre-console actual Pexels website screenshot")
    if "frame_500.ppm" not in data["frames"]:
        raise SystemExit("Missing full diagnostic window/last QEMU frame")
    print("V102_GUEST_EVIDENCE_CAPTURED_4K_PLAYBACK_NOT_AUTOMATICALLY_CLAIMED")
if __name__=="__main__":main()
