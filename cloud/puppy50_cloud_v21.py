#!/usr/bin/env python3
"""Puppy50 v21: repeated real Puppy desktop boot + stable-state memory accounting."""
import argparse, hashlib, json, os, re, shutil, socket, subprocess, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_SHA256="ae65f6e6d70a96f48bdbb291c2426f8a2fd77a73692e149e81a5eecb6fe7509f"
# The kernel-only test intentionally lacks initrd and will not start Puppy.
CASES = (
 ("stable_boot_A",4096,"pc",True,480,False),
 ("stable_boot_B",4096,"pc",True,480,False),
)
def digest(path):
    d=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(4*1024*1024),b""): d.update(b)
    return d.hexdigest()
def hmp_capture(socket_path, output):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        sock.connect(str(socket_path))
        def receive(limit=8):
            data=b""; deadline=time.monotonic()+limit
            while time.monotonic()<deadline:
                try:
                    part=sock.recv(8192)
                    if not part: break
                    data+=part
                    if b"(qemu) " in data: break
                except socket.timeout: pass
            return data.decode(errors="replace")
        greeting=receive()
        if "(qemu)" not in greeting: raise RuntimeError("No QEMU HMP prompt")
        sock.sendall(("screendump "+str(output)+"\n").encode())
        response=receive()
        if not output.exists() or output.stat().st_size<100:
            raise RuntimeError("screendump failed: "+response[-500:])
    return output.stat().st_size
def run_one(iso,kernel,initrd,output,spec):
    label,mem,machine,with_initrd,seconds,reclaim=spec
    dest=output/label;dest.mkdir(parents=True,exist_ok=True)
    log=dest/"qemu.log"; serial=dest/"serial.log"; monitor=dest/"monitor.sock"
    cmd=["qemu-system-x86_64","-machine",f"{machine},accel=tcg","-m",str(mem),"-smp","1",
         "-kernel",str(kernel)]
    if with_initrd:cmd+=["-initrd",str(initrd)]
    cmd+=["-append","pmedia=cd pfix=ram,nocopy console=tty0 console=ttyS0 loglevel=7" + (" puppy50_reclaim=1" if reclaim else ""),
          "-drive",f"file={iso},media=cdrom,readonly=on","-vga","std","-display","none",
          "-monitor",f"unix:{monitor},server=on,wait=off",
          "-serial",f"file:{serial}","-nic","none","-no-reboot"]
    (dest/"qemu_args.json").write_text(json.dumps(cmd[1:],indent=2)+"\n")
    info={"case":label,"allocated_mib":mem,"machine":machine,"initrd_loaded":with_initrd,
          "time_budget_s":seconds,"cache_reclaim_trial":reclaim,"guest_idle_ram_mb":None,"desktop_confirmed":False,
          "50_mb_verified":False,"kernel_seen":False,"switch_root_seen":False,
          "zram_seen":False,"captures":[],"errors":[]}
    t0=time.monotonic()
    with open(log,"wb") as output_file:
        p=subprocess.Popen(cmd,stdout=output_file,stderr=subprocess.STDOUT)
        try:
            for checkpoint in sorted(set([min(12,seconds//2),seconds])):
                while p.poll() is None and time.monotonic()-t0<checkpoint:
                    time.sleep(.4)
                if p.poll() is not None: break
                fname=dest/f"screen_{checkpoint:03}.ppm"
                try:
                    size=hmp_capture(monitor,fname)
                    info["captures"].append({"file":fname.name,"bytes":size})
                except Exception as e:
                    info["errors"].append(str(e)[:1000])
            info["exit_early"]=p.poll()
        finally:
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=6)
                except subprocess.TimeoutExpired:p.kill();p.wait()
    s=serial.read_text(errors="replace") if serial.exists() else ""
    q=log.read_text(errors="replace") if log.exists() else ""
    info.update({"elapsed_host_s":round(time.monotonic()-t0,2),
                 "return_code":p.returncode,"serial_bytes":len(s),
                 "kernel_seen":"Linux version " in s,
                 "switch_root_seen":"switch_root" in s,
                 "zram_seen":"Loading zram swap" in s,
                 "qemu_assertion":"qemu_mutex_lock_iothread_impl" in q,
                 "guest_oom_evidence":bool(re.search(r"(?:Out of memory|oom-killer|Kernel panic.*[Mm]emory)",s)),
                 "serial_tail":s.splitlines()[-16:],
                 "qemu_tail":q.splitlines()[-8:]})
    info["stage"]=("QEMU_INTERNAL_FAILURE" if info["qemu_assertion"] else
                    "GUEST_OOM_EVIDENCE" if info["guest_oom_evidence"] else
                    "PUPPY_SWITCH_ROOT" if info["switch_root_seen"] else
                    "KERNEL_STARTED" if info["kernel_seen"] else "NO_KERNEL_EVIDENCE")
    (dest/"result.json").write_text(json.dumps(info,indent=2)+"\n")
    print(json.dumps({"case":label,"stage":info["stage"],"host_s":info["elapsed_host_s"],"screens":len(info["captures"]) }),flush=True)
    return info
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--iso",type=Path,required=True)
    ap.add_argument("--out",type=Path,default=Path("results-v11"))
    ap.add_argument("--cases",nargs="+",choices=[x[0] for x in CASES])
    args=ap.parse_args()
    iso=args.iso.resolve(strict=True)
    if digest(iso)!=EXPECTED_SHA256: ap.error("Official ISO SHA256 mismatch")
    with iso.open("rb") as f:
        f.seek(32769)
        if f.read(5)!=b"CD001":ap.error("ISO9660 signature mismatch")
    if not shutil.which("7z") or not shutil.which("qemu-system-x86_64"):
        ap.error("7z and qemu-system-x86_64 are required")
    args.out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p50v11-") as work:
        subprocess.run(["7z","e","-y","-o"+work,str(iso),"vmlinuz","initrd.gz"],check=True,
                       stdout=subprocess.DEVNULL,timeout=120)
        kernel=Path(work)/"vmlinuz";initrd=Path(work)/"initrd.gz"
        if not kernel.is_file() or not initrd.is_file(): ap.error("Missing kernel/initrd")
        print("Verified original ISO. initrd size bytes:",initrd.stat().st_size,flush=True)
        results=[run_one(iso,kernel,initrd,args.out,spec) for spec in CASES
                 if not args.cases or spec[0] in args.cases]
    summary={"schema":"puppy50_v21_repeated_idle_stability_diagnostic","download_hash_verified":True,
             "actual_guest_idle_used_mb":None,"50mb_achieved":False,"passive_no_cache_reclaim":True,
             "desktop_verified":False,"completed_utc":datetime.now(timezone.utc).isoformat(),
             "cases":results}
    (args.out/"SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n")
if __name__=="__main__":main()
