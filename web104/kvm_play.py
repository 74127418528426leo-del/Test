#!/usr/bin/env python3
"""Actually stream official 3840x2160 Pexels MP4 through Firefox in a RAM-only
QEMU guest. Only the small player HTML is served from QEMU host via local HTTP;
video bytes load over HTTPS from Pexels CDN, with normal guest CA checks.
"""
import argparse,json,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from web85.qemu_debian_live_smoke import qmp,ppm_valid
from web102.pexels_kvm import send_key,type_text,marker_until
URL="http://10.0.2.2:8766/pexels.html"
VIDEO="https://videos.pexels.com/video-files/27251986/12102943_3840_2160_30fps.mp4"

def snap(mon,out,seconds,d):
    dest=out/f"frame_{seconds:03d}.ppm"
    qmp(mon,"screendump",{"filename":str(dest)})
    if not dest.is_file() or not ppm_valid(dest):
        raise RuntimeError("Real screenshot unavailable at "+str(seconds))
    d["frames"].append(dest.name)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--iso",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    iso=a.iso.resolve(strict=True)
    if iso.stat().st_size<900_000_000:raise ValueError("Incomplete verified Firefox ISO")
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    mon=out/"qmp.sock"
    cmd=["qemu-system-x86_64","-machine","pc,accel=kvm","-cpu","host",
      "-m","4096","-smp","2",
      "-drive",f"file={iso},if=ide,media=cdrom,id=livecd,readonly=on",
      "-boot","order=d","-display","none","-vga","std",
      "-qmp",f"unix:{mon},server=on,wait=off",
      "-serial",f"file:{out/'serial.log'}",
      "-nic","user,model=e1000,ipv6=off","-no-reboot"]
    d={"schema":"PUPPY50_V104_REAL_PEXELS_4K_GUEST_HTML5",
      "local_test_page":URL,"actual_remote_video_source":VIDEO,"ram_mib":4096,
      "source_metadata_width":3840,"source_metadata_height":2160,
      "guest_page_visually_verified":False,"guest_4k_decoding_verified":False,
      "guest_playback_verified":False,"measured_guest_fps":None,
      "guest_nonroot_firefox":False,"guest_HTTPS_CA_verified":False,
      "guest_live_media_ejected":False,"guest_still_running_at_end":False,
      "frames":[],"errors":[]}
    with (out/"qemu.log").open("wb") as log:
        vm=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
        start=time.monotonic()
        try:
            marker_until(start,18,vm);send_key(mon,['ret'],120)
            marker_until(start,105,vm);snap(mon,out,105,d)
            marker_until(start,139,vm)
            send_key(mon,['ctrl','l'],125)
            time.sleep(1)
            type_text(mon,URL,.11)
            send_key(mon,['ret'],120)
            d["local_page_URL_submitted"]=True
            for mark in [185,225,265,295]:
                marker_until(start,mark,vm);snap(mon,out,mark,d)
            marker_until(start,300,vm)
            try:
                qmp(mon,"human-monitor-command",{"command-line":"eject -f livecd"})
                res=str(qmp(mon,"human-monitor-command",{"command-line":"info block livecd"})).lower()
                d["guest_live_media_ejected"]=("not inserted" in res or "no media" in res)
            except Exception as exc:d["errors"].append("media eject "+repr(exc))
            for mark in [330,360,390,415]:
                marker_until(start,mark,vm);snap(mon,out,mark,d)
            d["guest_still_running_at_end"]=vm.poll() is None
        except Exception as exc:d["errors"].append("QEMU sequence "+repr(exc))
        finally:
            if vm.poll() is None:
                vm.terminate()
                try:vm.wait(timeout=10)
                except subprocess.TimeoutExpired:vm.kill();vm.wait(timeout=5)
    serial=(out/"serial.log").read_text(errors="replace") if (out/"serial.log").is_file() else ""
    d["guest_nonroot_firefox"]="P50_V91_NONROOT_FIREFOX_PROCESS_SEEN" in serial
    d["guest_HTTPS_CA_verified"]=(
      "PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_DIRECT=PASS" in serial or
      "PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_BRIDGE=PASS" in serial)
    (out/"result.json").write_text(json.dumps(d,indent=2)+"\n")
    print(json.dumps(d,indent=2))
    if not d["guest_nonroot_firefox"] or not d["guest_HTTPS_CA_verified"]:
        raise SystemExit("Guest Firefox or CA HTTPS baseline not verified")
    if "frame_415.ppm" not in d["frames"]:raise SystemExit("Missing actual final QEMU frame")
    print("GUEST_BROWSER_AND_ALL_FRAMES_CAPTURED; actual 4K must be reviewed from pixels")
if __name__=="__main__":main()
