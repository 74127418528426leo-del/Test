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

def qmp(path, command, arguments=None):
    """QMP JSON control, not HMP interactive readline with ANSI escapes."""
    import uuid
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as conn:
        conn.settimeout(8)
        conn.connect(str(path))
        reader=conn.makefile("rb")
        def receive():
            line=reader.readline(1_000_001)
            if not line or len(line)>1_000_000:raise RuntimeError("QMP missing response")
            return json.loads(line.decode("utf-8"))
        greeting=receive()
        if "QMP" not in greeting:raise RuntimeError("QMP handshake failed")
        for name,args in [("qmp_capabilities",None),(command,arguments)]:
            identifier=uuid.uuid4().hex
            obj={"execute":name,"id":identifier}
            if args is not None:obj["arguments"]=args
            conn.sendall((json.dumps(obj)+"\n").encode())
            for attempt in range(60):
                message=receive()
                if "event" in message:continue
                if message.get("id")!=identifier:raise RuntimeError("QMP mismatched response")
                if "error" in message:raise RuntimeError("QMP "+name+": "+str(message["error"]))
                if "return" not in message:raise RuntimeError("QMP missing return")
                result=message["return"]
                break
            else:raise RuntimeError("QMP response event flood")
        return result

def hmp(path,cmd):
    return str(qmp(path,"human-monitor-command",{"command-line":cmd}))

def ppm_valid(path):
    """640x480 PPM is 921615 bytes: never reject solely for being under 1 MB."""
    import re
    p=Path(path)
    raw=p.read_bytes()
    m=re.match(rb"^P6\s+(\d+)\s+(\d+)\s+(\d+)\s",raw[:100])
    if not m:return False
    width,height,maxval=map(int,m.groups())
    return (320<=width<=16384 and 200<=height<=16384 and maxval==255
            and len(raw)==m.end()+3*width*height)

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
    monitor=a.out/"qmp.sock"
    command=["qemu-system-x86_64","-machine","pc,accel=kvm","-cpu","host",
      "-m",str(a.ram),"-smp","2",
      "-drive",f"file={a.iso},if=ide,media=cdrom,id=livecd,readonly=on",
      "-boot","order=d","-display","none","-vga","std",
      "-qmp",f"unix:{monitor},server=on,wait=off",
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
            for mark in [18,100,165,240,300,a.seconds]:
                while time.monotonic()-start<mark and vm.poll() is None:time.sleep(1)
                if vm.poll() is not None:break
                if mark==18:
                    try:
                        qmp(monitor,"send-key",{"keys":[{"type":"qcode","data":"ret"}],"hold-time":90})
                        output["boot_menu_enter_sent"]=True
                    except Exception as exc:
                        output["boot_menu_enter_sent"]=False
                        output["errors"].append("QMP Enter to start Debian Live: "+repr(exc))
                    continue
                if mark==300:
                    try:
                        output["eject_reply"]=hmp(monitor,"eject -f livecd")[-400:]
                        block=hmp(monitor,"info block livecd").lower()
                        output["media_removed"]=("not inserted" in block or "no media" in block)
                    except Exception as exc:
                        output["errors"].append("Eject: "+repr(exc))
                frame=a.out/f"frame_{mark:03d}.ppm"
                try:
                    qmp(monitor,"screendump",{"filename":str(frame)})
                    if frame.is_file() and ppm_valid(frame):
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
    if not output.get("boot_menu_enter_sent"):
        raise SystemExit("PUPPY50_V88_DEBIAN_LIVE_BOOT_ENTER_WAS_NOT_SENT")
    if not output["screenshots"]:
        raise SystemExit("PUPPY50_V85_NO_REAL_GUI_FRAME")
    if not output["guest_public_HTTPS_proven"]:
        raise SystemExit("PUPPY50_V85_NO_GUEST_STRICT_CA_EXTERNAL_HTTPS")
    if not output["toram_media_ejection_survived"]:
        raise SystemExit("PUPPY50_V85_TORAM_NOT_PROVEN_AFTER_MEDIA_EJECTION")
if __name__=="__main__":main()
