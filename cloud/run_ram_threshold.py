#!/usr/bin/env python3
"""Puppy50 threshold probe: only 1280/1536/2048 MiB, verify RAM-only boot and CD eject; no all-app claim.
Not a GUI interaction test. All source SFS loop devices must be RAM-backed.
"""
import argparse,hashlib,json,socket,subprocess,time,re
from pathlib import Path

def monitor(path,command):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(1);s.connect(str(path))
        def receive(seconds=8):
            out=b'';stop=time.monotonic()+seconds
            while time.monotonic()<stop:
                try:
                    c=s.recv(4096)
                    if not c:break
                    out+=c
                    if b'(qemu) ' in out:break
                except socket.timeout:continue
            return out.decode(errors='replace')
        if '(qemu)' not in receive():raise RuntimeError('QEMU monitor unavailable')
        s.sendall((command+'\n').encode());return receive()

def main():
    p=argparse.ArgumentParser();p.add_argument('--iso',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--seconds',type=int,default=220)
    p.add_argument('--ram-mib',type=int,required=True,choices=(1280,1536,2048))
    a=p.parse_args();a.iso=a.iso.resolve(strict=True);a.out.mkdir(parents=True,exist_ok=True)
    monitorpath=a.out/'monitor.sock'
    cmd=['qemu-system-x86_64','-machine','pc,accel=kvm','-cpu','host','-m',str(a.ram_mib),
         '-smp','2','-drive',f'file={a.iso},if=ide,media=cdrom,id=puppycd,readonly=on',
         '-boot','order=d','-display','none','-vga','std',
         '-monitor',f'unix:{monitorpath},server=on,wait=off',
         '-serial',f'file:{a.out/"serial.log"}','-nic','none','-no-reboot']
    start=time.monotonic()
    report={'schema':'puppy50_v39_actual_4g_cd_ejection',
            'ram_allocated_mib':a.ram_mib,'original_sfs_resident_in_ram_verified':False,
            'media_ejection_verified':False,'browser_after_ejection_verified':False,
            '50mb_verified':False,'images':[],'errors':[],'host_elapsed_s':None}
    with (a.out/'qemu.log').open('wb') as out:
        q=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT)
        try:
            for seconds in [95,145,a.seconds]:
                while time.monotonic()-start<seconds and q.poll() is None:time.sleep(1)
                if q.poll() is not None:break
                if seconds==145:
                    try:
                        report['block_before_eject']=monitor(monitorpath,'info block puppycd')
                        report['eject_command']=monitor(monitorpath,'eject -f puppycd')
                        report['block_after_eject']=monitor(monitorpath,'info block puppycd')
                        after=report['block_after_eject'].lower()
                        report['media_ejection_verified']=('not inserted' in after or 'no media' in after) and 'error' not in report['eject_command'].lower()
                    except Exception as exc:report['errors'].append('eject: '+repr(exc))
                image=a.out/f'frame_{seconds:03}.ppm'
                try:
                    response=monitor(monitorpath,'screendump '+str(image))
                    if image.exists() and image.stat().st_size>100:report['images'].append(image.name)
                    else:report['errors'].append('screendump: '+response[-200:])
                except Exception as exc:report['errors'].append('screendump: '+repr(exc))
            report['qemu_exit_before_deadline']=q.poll()
        finally:
            if q.poll() is None:
                q.terminate()
                try:q.wait(timeout=8)
                except subprocess.TimeoutExpired:q.kill();q.wait()
    s=(a.out/'serial.log').read_text(errors='replace').replace('\r','')
    report['host_elapsed_s']=round(time.monotonic()-start,2)
    proof=re.search(r'PUPPY50_V39_RAM_PROOF_BEGIN(.*?)PUPPY50_V39_RAM_PROOF_END',s,re.S)
    report['real_guest_proof_emitted']=bool(proof)
    if proof:
        info=proof.group(1)
        got=dict((k,int(v)) for k,v in re.findall(r'PUPPY50_COPIED_SFS name=([^\s]+) bytes=(\d+)',info))
        loops=re.findall(r'^/dev/loop\d+:.*',info,re.M)
        report['copied_sfs_file_bytes']=got
        report['actual_sfs_loop_backings']=loops
        report['non_ram_sfs_loops']=[x for x in loops if '.sfs' in x.lower() and '/mnt/tmpfs/' not in x]
        report['source_medium_not_required_by_sfs_loops']=bool(got) and not report['non_ram_sfs_loops'] and len([x for x in loops if '/mnt/tmpfs/' in x])>=len(got)
        report['copy_policy_verified']='PUPPY50_RAMONLY_COPY_SELECTION=yes' in info
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('block_before_eject','block_after_eject','actual_sfs_loop_backings','copied_sfs_file_bytes')},indent=2))
    if not (report['media_ejection_verified'] and len(report['images'])>=3 and report.get('qemu_exit_before_deadline') is None):
        raise SystemExit('QEMU eject/display check failed. Complete RAM backing checked separately by v40 guest probe.')
if __name__=='__main__':main()
