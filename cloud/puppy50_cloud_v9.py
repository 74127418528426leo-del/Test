#!/usr/bin/env python3
"""Actual x86-64 QEMU-TCG boot evidence. Does NOT invent RAM-consumption figures."""
import argparse, hashlib, json, shutil, socket, subprocess, tempfile, time
from pathlib import Path
from datetime import datetime, timezone

SHA = 'ae65f6e6d70a96f48bdbb291c2426f8a2fd77a73692e149e81a5eecb6fe7509f'
CASES = [('copy_1024', 'ram,copy', 1024), ('nocopy_512', 'ram,nocopy', 512),
         ('nocopy_128', 'ram,nocopy', 128), ('nocopy_64', 'ram,nocopy', 64)]

def checksum(path):
    d = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(4*1024*1024), b''):
            d.update(block)
    return d.hexdigest()

def monitor(sockfile, command):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(8)
        s.connect(str(sockfile))
        s.recv(4096)
        s.sendall((command+'\n').encode())
        out = b''
        for _ in range(6):
            try: out += s.recv(4096)
            except socket.timeout: break
            if out.endswith(b'(qemu) '): break
        return out.decode(errors='replace')

def run_case(iso, kernel, initrd, name, pfix, ram, out, seconds):
    out.mkdir(parents=True, exist_ok=True)
    monitor_path = out/'qemu.sock'
    serial_path = out/'serial.log'
    result = {'case':name,'ram_allocated_mib':ram,'pfix':pfix,'qemu_launched':False,
              'guest_ram_used_mb':None,'guest_meminfo_collected':False,
              'desktop_confirmed':False,'50mb_verified':False,'screenshots':[],
              'kernel_banner_seen':False,'status':'NOT_RUN'}
    cmd = ['qemu-system-x86_64','-machine','pc,accel=tcg','-m',str(ram),'-smp','2',
           '-kernel',str(kernel),'-initrd',str(initrd),
           '-append',f'pmedia=cd pfix={pfix} console=ttyS0 console=tty0 loglevel=6',
           '-drive',f'file={iso},media=cdrom,readonly=on','-boot','order=d',
           '-vga','std','-display','none',
           '-monitor',f'unix:{monitor_path},server=on,wait=off',
           '-serial',f'file:{serial_path}','-nic','none','-no-reboot']
    (out/'qemu_arguments.json').write_text(json.dumps(cmd[1:], indent=2))
    started = time.monotonic()
    try:
        with open(out/'qemu.log','wb') as log:
            p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            try:
                result['qemu_launched'] = True
                for mark in [60,120,180,240,360,600]:
                    if mark>seconds: continue
                    while time.monotonic()-started<mark and p.poll() is None:
                        time.sleep(1)
                    if p.poll() is not None: break
                    ppm = out/f'screen_{mark:03}.ppm'
                    try:
                        monitor(monitor_path, f'screendump {ppm}')
                        if ppm.exists() and ppm.stat().st_size>64:
                            result['screenshots'].append(ppm.name)
                    except (OSError, ValueError) as e:
                        result.setdefault('capture_errors',[]).append(str(e))
                result['qemu_exit_before_stop'] = p.poll()
            finally:
                if p.poll() is None:
                    p.terminate()
                    try: p.wait(timeout=8)
                    except subprocess.TimeoutExpired: p.kill(); p.wait()
        serial = serial_path.read_text(errors='replace') if serial_path.exists() else ''
        result['kernel_banner_seen'] = 'Linux version ' in serial
        result['status'] = ('KERNEL_BOOT_EVIDENCE' if result['kernel_banner_seen']
                            else 'SCREEN_ONLY' if result['screenshots'] else 'NO_BOOT_EVIDENCE')
    except Exception as e:
        result['status'] = 'ERROR'; result['error'] = repr(e)
    result['duration_s'] = int(time.monotonic()-started)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--iso',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('cloud-results'))
    p.add_argument('--seconds',type=int,default=240)
    a=p.parse_args()
    if not 60<=a.seconds<=600: p.error('seconds must be 60..600')
    a.iso=a.iso.resolve(strict=True)
    if checksum(a.iso)!=SHA: p.error('Official ISO SHA256 mismatch')
    with a.iso.open('rb') as f:
        f.seek(32769)
        if f.read(5)!=b'CD001': p.error('ISO9660 signature mismatch')
    if not shutil.which('qemu-system-x86_64') or not shutil.which('7z'):
        p.error('Require qemu-system-x86_64 and 7z')
    a.out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['7z','e','-y','-o'+tmp,str(a.iso),'vmlinuz','initrd.gz'],
                       check=True, stdout=subprocess.DEVNULL, timeout=180)
        kernel=Path(tmp)/'vmlinuz';initrd=Path(tmp)/'initrd.gz'
        if not kernel.is_file() or not initrd.is_file(): p.error('Missing kernel/initrd')
        results=[]
        for name,pfix,ram in CASES:
            results.append(run_case(a.iso,kernel,initrd,name,pfix,ram,a.out/name,a.seconds))
    summary={'schema':'puppy50_v9_actual_qemu','iso_sha256_verified':True,
             '50mb_verified':False,'guest_idle_ram_used_mb':None,
             'limitation':'VM RAM allocation and screenshots are not guest idle RAM measurements',
             'cases':results,'completed_utc':datetime.now(timezone.utc).isoformat()}
    (a.out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('SUMMARY:',json.dumps({'cases':len(results),'kernel_boot_markers':sum(r['kernel_banner_seen'] for r in results)}))

if __name__=='__main__': main()
