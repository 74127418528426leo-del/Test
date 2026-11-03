#!/usr/bin/env python3
"""Real KVM smoke test for the separate maintained Debian Live browser pilot.

Only actual QEMU serial output and framebuffer images count as guest proof.
A successful host curl or installed package alone does not prove guest browsing.
"""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import time

def hmp(path,cmd):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(1)
        s.connect(str(path))
        def recv_prompt(timeout=8):
            out=b""
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                try:
                    part=s.recv(4096)
                    if not part:break
                    out+=part
                    if b"(qemu) " in out:break
                except socket.timeout:continue
            return out.decode(errors="replace")
        if "(qemu)" not in recv_prompt():
            raise RuntimeError("No QEMU HMP prompt")
        s.sendall((cmd+"\n").encode())
        return recv_prompt()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--iso",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--ram",type=int,default=4096)
    p.add_argument("--seconds",type=int,default=395)
    a=p.parse_args()
    a.iso=a.iso.resolve(strict=True)
    if a.iso.stat().st_size<150*1024*1024:raise SystemExit("Unexpectedly small live ISO")
    a.out.mkdir(parents=True,exist_ok=True)
    monitor=a.out/"hmp.sock"
    command=["qemu-system-x86_64","-machine","pc,accel=kvm","-cpu","host",
      "-m",str(a.ram),"-smp","2",
      "-drive",f"file={a.iso},if=ide,media=cdrom,id=livecd,readonly=on",
      "-boot","order=d","-display","none","-vga","std",
      "-monitor",f"unix:{monitor},server=on,wait=off",
      "-serial",f"file:{a.out/'serial.log'}",
      "-nic","user,model=e1000,ipv6=off","-no-reboot"]
    output={"schema":"PUPPY50_V85_ACTUAL_DEBIAN_LIVE_QEMU_GUEST",
      "guest_memory_mib":a.ram,"screenshots":[],"errors":[],
      "guest_public_HTTPS_proven":False,
      "guest_WiFi_hardware_tested":False,
      "guest_network_menu_visually_confirmed":False,
      "browser_public_webpage_visually_verified":False,
      "toram_media_ejection_survived":False,
      "production_ready":False}
    with (a.out/"qemu.log").open("wb") as log:
        vm=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        start=time.monotonic()
        try:
            for mark in [100,165,240,300,a.seconds]:
                while time.monotonic()-start<mark and vm.poll() is None:time.sleep(1)
                if vm.poll() is not None:break
                if mark==300:
                    try:
                        output["eject_reply"]=hmp(monitor,"eject -f livecd")[-400:]
                        block=hmp(monitor,"info block livecd").lower()
                        output["media_removed"]=("not inserted" in block or "no media" in block)
                    except Exception as exc:
                        output["errors"].append("Eject: "+repr(exc))
                frame=a.out/f"frame_{mark:03d}.ppm"
                try:
                    hmp(monitor,"screendump "+str(frame))
                    if frame.is_file() and frame.stat().st_size>1000000:
                        output["screenshots"].append(str(frame.name))
                    else:output["errors"].append("No frame at "+str(mark))
                except Exception as exc:
                    output["errors"].append("Screenshot "+str(mark)+": "+repr(exc))
            output["guest_still_running_at_end"]=vm.poll() is None
        finally:
            if vm.poll() is None:
                vm.terminate()
                try:vm.wait(timeout=10)
                except subprocess.TimeoutExpired:vm.kill();vm.wait(timeout=5)
    serial=(a.out/"serial.log").read_text(errors="replace") if (a.out/"serial.log").is_file() else ""
    output["guest_public_HTTPS_proven"]=(
        "PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_DIRECT=PASS" in serial or
        "PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_BRIDGE=PASS" in serial)
    output["guest_network_mode"]=next((line.split("=",1)[1] for line in serial.splitlines()
         if line.startswith("PUPPY50_V85_NETWORK_MODE=")),None)
    output["toram_media_ejection_survived"]=bool(output.get("media_removed") and
         output.get("guest_still_running_at_end") and
         f"frame_{a.seconds:03d}.ppm" in output["screenshots"])
    output["original_CD_ejection_proves_all_live_root_was_in_RAM"]=False
    output["Firefox_ESR_version_checked_by_image_package_inventory_not_serial"]=True
    (a.out/"result.json").write_text(json.dumps(output,indent=2)+"\n")
    print(json.dumps(output,indent=2))
    if not output["screenshots"]:
        raise SystemExit("PUPPY50_V85_NO_REAL_GUI_FRAME")
    if not output["guest_public_HTTPS_proven"]:
        raise SystemExit("PUPPY50_V85_NO_GUEST_STRICT_CA_EXTERNAL_HTTPS")
    if not output["toram_media_ejection_survived"]:
        raise SystemExit("PUPPY50_V85_TORAM_NOT_PROVEN_AFTER_MEDIA_EJECTION")
if __name__=="__main__":main()
