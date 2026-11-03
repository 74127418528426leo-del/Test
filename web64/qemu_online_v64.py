#!/usr/bin/env python3
"""Puppy50 Web v45: real optical-CD boot with configurable physical RAM and screenshot checks.
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
    p.add_argument('--out',type=Path,required=True);p.add_argument('--seconds',type=int,default=220);p.add_argument('--ram',type=int,default=1024)
    a=p.parse_args();a.iso=a.iso.resolve(strict=True);a.out.mkdir(parents=True,exist_ok=True)
    monitorpath=a.out/'monitor.sock'
    cmd=['qemu-system-x86_64','-machine','pc,accel=kvm','-cpu','host','-m',str(a.ram),
         '-smp','2','-drive',f'file={a.iso},if=ide,media=cdrom,id=puppycd,readonly=on',
         '-boot','order=d','-display','none','-vga','std',
         '-monitor',f'unix:{monitorpath},server=on,wait=off',
         '-serial',f'file:{a.out/"serial.log"}','-nic','user,model=e1000,ipv6=off','-no-reboot']
    start=time.monotonic()
    report={'schema':'puppy50_web_v45_actual_browser_only_iso_cd_ejection',
            'ram_allocated_mib':a.ram,'original_sfs_resident_in_ram_verified':False,
            'media_ejection_verified':False,'browser_after_ejection_verified':False,
            '50mb_verified':False,'images':[],'errors':[],'host_elapsed_s':None}
    with (a.out/'qemu.log').open('wb') as out:
        q=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT)
        try:
            for seconds in [95,145,175,195,245,a.seconds]:
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
                if seconds==175:
                    try:
                        cmds=['info mice','mouse_button 1','mouse_button 0']
                        trace=[]
                        for cmdline in cmds:
                            reply=monitor(monitorpath,cmdline)
                            trace.append({'command':cmdline,'reply':reply[-260:]})
                            if any(token in reply.lower() for token in ('unknown command','invalid parameter','error:')):
                                raise RuntimeError(f'QEMU rejected {cmdline}: {reply[-260:]}')
                            time.sleep(0.3)
                        report['mouse_trace']=trace
                        report['mouse_click_submitted']=True
                    except Exception as exc:
                        report['mouse_click_submitted']=False
                        report['errors'].append('mouse-click: '+repr(exc))
                    time.sleep(3)
                if seconds==195:
                    try:
                        reply=monitor(monitorpath,'sendkey t')
                        if any(token in reply.lower() for token in ('unknown command','invalid parameter','error:')):
                            raise RuntimeError('QEMU rejected key: '+reply[-240:])
                        report['keypress_command']=reply[-260:]
                        report['keypress_submitted_to_qemu']=True
                    except Exception as exc:
                        report['keypress_submitted_to_qemu']=False
                        report['errors'].append('keypress: '+repr(exc))
                    time.sleep(4)
                if seconds==245:
                    # Navigate the ACTUAL Firefox address bar to an HTTPS site.
                    # QEMU HMP input proves only keys were submitted. The
                    # after-navigation framebuffer must be manually inspected.
                    try:
                        url='https://example.com/'
                        keynames={'/':'slash',':':'shift-semicolon','.':'dot'}
                        commands=['sendkey ctrl-l']+[
                          'sendkey '+keynames.get(ch,ch) for ch in url
                        ]+['sendkey ret']
                        for line in commands:
                            reply=monitor(monitorpath,line)
                            if any(token in reply.lower() for token in
                                   ('unknown command','invalid parameter','error:')):
                                raise RuntimeError('QEMU rejected '+line+': '+reply[-250:])
                            time.sleep(0.2)
                        report['remote_https_navigation_requested']=url
                        report['firefox_address_bar_keys_submitted']=True
                        time.sleep(16)
                    except Exception as exc:
                        report['firefox_address_bar_keys_submitted']=False
                        report['errors'].append('url-navigation: '+repr(exc))
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
    report['ram_copy_complete']='PUPPY50_WEB_V45_RAM_COPY_COMPLETE' in s
    report['ram_root_switch']='PUPPY50_WEB_V45_SWITCH_ROOT_RAM_ONLY' in s
    report['xorg_started']='PUPPY50_WEB_V45_XORG_RUNNING' in s
    report['qemu_e1000_early_loaded']='PUPPY50_V46_DIRECT_INSMOD module=e1000 status=0' in s
    report['guest_dhcp_lease']='PUPPY50_V64_DHCP_IPV4=PASS' in s
    report['guest_default_route']='PUPPY50_V64_DEFAULT_ROUTE=PASS' in s
    report['guest_dns_config']='PUPPY50_V64_DNS_CONFIG=PRESENT' in s
    report['guest_ca_verified_external_https']='PUPPY50_V64_DNS_TLS_HTTPS_EXTERNAL=PASS' in s
    report['guest_online_ready']='PUPPY50_V64_NETWORK_READY=PASS' in s
    report['external_website_rendered_by_firefox_proven']=False
    report['internet_exposed_through_user_mode_qemu_nat']=True

    report['firefox_launch_requested']='PUPPY50_WEB_V45_FIREFOX_REQUESTED' in s
    if proof:
        info=proof.group(1)
        got=dict((k,int(v)) for k,v in re.findall(r'PUPPY50_COPIED_SFS name=([^\s]+) bytes=(\d+)',info))
        loops=re.findall(r'^/dev/loop\d+:.*',info,re.M)
        report['copied_sfs_file_bytes']=got
        report['actual_sfs_loop_backings']=loops
        report['non_ram_sfs_loops']=[x for x in loops if '.sfs' in x.lower() and '/mnt/tmpfs/' not in x]
        report['source_medium_not_required_by_sfs_loops']=bool(got) and not report['non_ram_sfs_loops'] and len([x for x in loops if '/mnt/tmpfs/' in x])>=len(got)
        report['copy_policy_verified']='PUPPY50_RAMONLY_COPY_SELECTION=yes' in info
    from frame_stages import compare_stages
    before=a.out/'frame_145.ppm'
    after_click=a.out/'frame_175.ppm'
    after_key=a.out/'frame_195.ppm'
    report['input_stage_frames_present']=all(p.exists() for p in (before,after_click,after_key))
    report['script_ready_visually_proven']=False
    report['mouse_click_visually_proven']=False
    report['keyboard_visually_proven']=False
    if report['input_stage_frames_present']:
        try:
            stages=compare_stages(before,after_click,after_key)
            report['input_stage_proof']=stages
            report['script_ready_visually_proven']=stages['script_ready']
            report['mouse_click_visually_proven']=bool(report.get('mouse_click_submitted') and stages['click_confirmed'])
            report['keyboard_visually_proven']=bool(report.get('keypress_submitted_to_qemu') and stages['key_confirmed'])
        except Exception as exc:
            report['errors'].append('stage-proof: '+repr(exc))
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('block_before_eject','block_after_eject','actual_sfs_loop_backings','copied_sfs_file_bytes')},indent=2))
    if not (report['media_ejection_verified'] and len(report['images'])>=3 and report.get('qemu_exit_before_deadline') is None and report['ram_copy_complete'] and report['ram_root_switch']):
        raise SystemExit('RAM-only v45 CD boot and copy proof not complete; inspect actual serial logs and screenshots.')
if __name__=='__main__':main()
