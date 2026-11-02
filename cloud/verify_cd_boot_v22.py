#!/usr/bin/env python3
"""Real QEMU CD boot (El Torito/bootloader) evidence for Puppy50 v22.
Only visual captures and QEMU survival are automatically verified.
Desktop presence and functionality MUST be reviewed separately.
"""
import argparse,json,subprocess,time,socket
from pathlib import Path
def monitor(path,cmd):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(1.0);s.connect(str(path))
        def recv(seconds=8):
            b=b'';until=time.monotonic()+seconds
            while time.monotonic()<until:
                try:
                    x=s.recv(8192)
                    if not x: break
                    b+=x
                    if b'(qemu) ' in b: break
                except socket.timeout: continue
            return b.decode(errors='replace')
        if '(qemu)' not in recv():raise RuntimeError('Missing monitor prompt')
        s.sendall((cmd+'\n').encode())
        return recv()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--iso',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--duration',type=int,default=420)
    a=ap.parse_args()
    a.iso=a.iso.resolve(strict=True);a.out.mkdir(parents=True,exist_ok=True)
    m=a.out/'qemu.sock'; log=a.out/'qemu.log';serial=a.out/'serial.log'
    result={'test':'normal_cd_boot_no_direct_kernel','iso':a.iso.name,'qemu_started':False,
            'bootloader_verified_by_qemu':False,'desktop_verified':False,
            'full_apps_verified':False,'50_mb_achieved':False,
            'screens':[],'errors':[]}
    cmd=['qemu-system-x86_64','-machine','pc,accel=tcg','-m','1024','-smp','1',
         '-cdrom',str(a.iso),'-boot','order=d','-display','none','-vga','std',
         '-monitor',f'unix:{m},server=on,wait=off','-serial',f'file:{serial}',
         '-nic','none','-no-reboot']
    t=time.monotonic()
    with open(log,'wb') as logfile:
        p=subprocess.Popen(cmd,stdout=logfile,stderr=subprocess.STDOUT)
        try:
            result['qemu_started']=True
            for seconds in [90,240,a.duration]:
                if seconds>a.duration:continue
                while time.monotonic()-t<seconds and p.poll() is None:
                    time.sleep(1)
                if p.poll() is not None: break
                out=a.out/f'boot_{seconds:03}.ppm'
                try:
                    response=monitor(m,f'screendump {out}')
                    if out.is_file() and out.stat().st_size>100:
                        result['screens'].append(out.name)
                    else: result['errors'].append(response[-900:])
                except Exception as e:result['errors'].append(repr(e))
            result['premature_exit']=p.poll()
        finally:
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=7)
                except subprocess.TimeoutExpired:p.kill();p.wait()
    result['host_elapsed_s']=int(time.monotonic()-t)
    result['qemu_exit_code']=p.returncode
    result['bootloader_verified_by_qemu']=bool(result['screens']) and result['premature_exit'] is None
    (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not result['screens'] or result['premature_exit'] is not None:raise SystemExit(4)
if __name__=='__main__':main()
