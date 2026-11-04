#!/usr/bin/env python3
"""Real KVM: use virtual keyboard in user-controlled Firefox, retain raw frames.
A QMP command is NOT itself proof a public webpage rendered.
"""
import argparse,json,sys,time,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from web85.qemu_debian_live_smoke import qmp,ppm_valid
from web92.browser_keyboard import sequence,URL
def screenshot(monitor,path,out):
    qmp(monitor,'screendump',{'filename':str(path)})
    if not path.is_file() or not ppm_valid(path):
        raise RuntimeError('Missing valid actual QEMU screenshot '+str(path))
    out['screenshots'].append(path.name)
def homepage_visible(path):
    """Coarse dark-body check used ONLY to decide if a retry is needed."""
    import re
    p=Path(path)
    if not p.is_file():return False
    raw=p.read_bytes()
    m=re.match(rb'^P6\s+(\d+)\s+(\d+)\s+(\d+)\s',raw[:100])
    if not m:return False
    w,h,mx=map(int,m.groups())
    if mx!=255 or len(raw)!=m.end()+3*w*h:return False
    x=int(w*.80);y=int(h*.50)
    idx=m.end()+3*(y*w+x)
    return max(raw[idx:idx+3])<100

def send_url_slow(monitor):
    events=sequence()
    for i,event in enumerate(events):
        # QMP accepts send-key faster than Firefox processes it under RAM pressure.
        # Do not equate QMP acceptance with browser input handling.
        event=dict(event)
        event['hold-time']=145
        qmp(monitor,'send-key',event)
        time.sleep(1.0 if i==0 else .36)
    time.sleep(.5)

def run():
    ap=argparse.ArgumentParser()
    ap.add_argument('--iso',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--ram',type=int,default=4096)
    ap.add_argument('--seconds',type=int,default=300)
    a=ap.parse_args()
    iso=a.iso.resolve(strict=True)
    if iso.stat().st_size<150*1024*1024:raise ValueError('Not complete Debian Live ISO')
    if not 300<=a.seconds<=450:raise ValueError('Require screenshot window after navigation')
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    mon=out/'qmp.sock'
    cmd=['qemu-system-x86_64','-machine','pc,accel=kvm','-cpu','host',
         '-m',str(a.ram),'-smp','2',
         '-drive',f'file={iso},if=ide,media=cdrom,id=livecd,readonly=on',
         '-boot','order=d','-display','none','-vga','std',
         '-qmp',f'unix:{mon},server=on,wait=off',
         '-serial',f'file:{out/"serial.log"}',
         '-nic','user,model=e1000,ipv6=off','-no-reboot']
    report={'schema':'PUPPY50_V94_SLOW_KEYBOARD_REAL_BROWSER_ATTEMPT',
       'url_requested':URL,'guest_memory_mib':a.ram,
       'real_QMP_browser_navigation_requested':False,
       'real_guest_ca_verified_public_https':False,
       'real_nonroot_firefox_process':False,
       'external_webpage_manually_verified':False,
       'screenshots':[],'errors':[],'boot_cd_ejected':False}
    with (out/'qemu.log').open('wb') as logfile:
        vm=subprocess.Popen(cmd,stdout=logfile,stderr=subprocess.STDOUT)
        start=time.monotonic()
        try:
            for mark in [18,100,145,185,220,235,260,a.seconds]:
                while time.monotonic()-start<mark and vm.poll() is None:time.sleep(.5)
                if vm.poll() is not None:
                    report['errors'].append('QEMU guest exited before '+str(mark))
                    break
                if mark==18:
                    qmp(mon,'send-key',{'keys':[{'type':'qcode','data':'ret'}],'hold-time':100})
                    report['boot_menu_enter_sent']=True
                    continue
                try:
                    screenshot(mon,out/f'frame_{mark:03d}.ppm',report)
                except Exception as exc:report['errors'].append('screen '+str(mark)+': '+repr(exc))
                if mark==145:
                    try:
                        send_url_slow(mon)
                        report['real_QMP_browser_navigation_requested']=True
                        report['slow_keyboard_first_attempt']=True
                        report['navigation_after_seconds']=mark
                    except Exception as exc:
                        report['errors'].append('keyboard navigation: '+repr(exc))
                if mark==235:
                    try:
                        report['home_page_still_visible_at_220']=homepage_visible(out/'frame_220.ppm')
                        if report['home_page_still_visible_at_220']:
                            send_url_slow(mon)
                            report['slow_keyboard_retry_submitted']=True
                        else:
                            report['slow_keyboard_retry_submitted']=False
                    except Exception as exc:
                        report['errors'].append('slow keyboard retry: '+repr(exc))
                if mark==260:
                    try:
                        qmp(mon,'human-monitor-command',{'command-line':'eject -f livecd'})
                        status=str(qmp(mon,'human-monitor-command',{'command-line':'info block livecd'})).lower()
                        report['boot_cd_ejected']='not inserted' in status or 'no media' in status
                    except Exception as exc:report['errors'].append('CD eject: '+repr(exc))
            report['guest_running_at_end']=vm.poll() is None
        finally:
            if vm.poll() is None:
                vm.terminate()
                try:vm.wait(timeout=10)
                except subprocess.TimeoutExpired:vm.kill();vm.wait(timeout=5)
    serial=(out/'serial.log').read_text(errors='replace') if (out/'serial.log').exists() else ''
    report['real_guest_ca_verified_public_https']=('PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_DIRECT=PASS' in serial or
                     'PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_BRIDGE=PASS' in serial)
    report['real_nonroot_firefox_process']='P50_V91_NONROOT_FIREFOX_PROCESS_SEEN' in serial
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if not report['real_QMP_browser_navigation_requested']:raise SystemExit('Virtual Firefox address bar not exercised')
    if not report['real_nonroot_firefox_process']:raise SystemExit('No actual guest non-root Firefox process')
    if not report['real_guest_ca_verified_public_https']:raise SystemExit('Guest strict public HTTPS not proved')
    if f'frame_{a.seconds:03d}.ppm' not in report['screenshots']:raise SystemExit('No actual final framebuffer')
    if not report['boot_cd_ejected']:raise SystemExit('No verified live media eject')
    print('V92_EXTERNAL_URL_TYPED_IN_REAL_QEMU_FIREFOX; ACTUAL_PAGE_STILL_REQUIRES_SCREENSHOT_REVIEW')
if __name__=='__main__':run()
