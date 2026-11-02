#!/usr/bin/env python3
"""Puppy50 v35: KVM real-guest browser with deferred plocate refresh at 256 and 384MiB.
A framebuffer screenshot is not automatically proof of working GUI.
"""
import argparse, json, subprocess, time, socket, hashlib, re
from pathlib import Path
MEMORY=[256,384]
def hmp(path, cmd):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(1)
        s.connect(str(path))
        def rec(limit=9):
            out=b'';stop=time.monotonic()+limit
            while time.monotonic()<stop:
                try:
                    p=s.recv(8192)
                    if not p:break
                    out+=p
                    if b'(qemu) ' in out: break
                except socket.timeout: continue
            return out.decode(errors='replace')
        greeting=rec()
        if '(qemu)' not in greeting: raise RuntimeError('monitor greeting missing')
        s.sendall((cmd+'\n').encode())
        return rec()
def trial(iso,out,ram,secs):
    d=out/f'ram_{ram}MiB';d.mkdir(parents=True,exist_ok=True)
    monitor=d/'qemu.sock'
    cmd=['qemu-system-x86_64','-machine','pc,accel=kvm','-cpu','host','-m',str(ram),
         '-smp','1','-cdrom',str(iso),'-boot','order=d',
         '-display','none','-vga','std','-monitor',
         f'unix:{monitor},server=on,wait=off',
         '-serial',f'file:{d/"serial.log"}','-nic','none','-no-reboot']
    (d/'command.json').write_text(json.dumps(cmd[1:],indent=2))
    info={'ram_allocated_MiB':ram,'actual_cd_boot':True,'qemu_launched':False,
          'qemu_exit_before_deadline':None,
          'desktop_verified':False,'all_apps_verified':False,
          'ram_used_MiB':None,'50mb_verified':False,'screens':[],'capture_errors':[]}
    start=time.monotonic()
    with (d/'qemu.log').open('wb') as log:
        proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
        info['qemu_launched']=True
        try:
            for mark in sorted(set([min(60,secs//3),min(130,secs*2//3),secs])):
                while proc.poll() is None and time.monotonic()-start<mark:
                    time.sleep(.8)
                if proc.poll() is not None:break
                screenshot=d/f'frame_{mark:03}.ppm'
                try:
                    response=hmp(monitor,f'screendump {screenshot}')
                    if screenshot.exists() and screenshot.stat().st_size>64:
                        info['screens'].append(screenshot.name)
                    else: info['capture_errors'].append(response[-400:])
                except Exception as exc: info['capture_errors'].append(repr(exc))
            info['qemu_exit_before_deadline']=proc.poll()
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=7)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
    serial=(d/'serial.log').read_text(errors='replace') if (d/'serial.log').exists() else ''
    qlog=(d/'qemu.log').read_text(errors='replace')
    info['serial_bytes']=len(serial)
    info['kernel_started']='Linux version ' in serial
    info['memory_failure_in_kernel']=bool(re.search(r'(Out of memory|Kernel panic.*[Mm]emory|memory allocation failure|oom-killer)',serial))
    info['qemu_internal_assertion']='qemu_mutex_lock_iothread_impl' in qlog
    info['host_elapsed_s']=round(time.monotonic()-start,1)
    info['kernel_tail']=serial.splitlines()[-12:]
    info['qemu_tail']=qlog.splitlines()[-8:]
    (d/'result.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps({'ram':ram,'screens':len(info['screens']),'kernel_started':info['kernel_started'],'kernel_oom':info['memory_failure_in_kernel'],'qemu_assertion':info['qemu_internal_assertion']}),flush=True)
    return info
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--iso',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--seconds',type=int,default=215)
    ap.add_argument('--rams',type=int,nargs='+',default=MEMORY)
    a=ap.parse_args()
    if not 70<=a.seconds<=600:ap.error('duration outside safe range')
    a.iso=a.iso.resolve(strict=True);a.out.mkdir(parents=True,exist_ok=True)
    results=[trial(a.iso,a.out,m,a.seconds) for m in a.rams]
    summary={'schema':'Puppy50-v24-actual-cd-boot-low-ram','source_iso_sha256':hashlib.sha256(a.iso.read_bytes()).hexdigest(),
             'screens_require_visual_confirmation':True,'guest_ram_usage_not_measured':True,
             'cases':results}
    (a.out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':main()
