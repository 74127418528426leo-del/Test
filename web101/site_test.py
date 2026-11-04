#!/usr/bin/env python3
"""Puppy50 v101 real webpage smoke test in previously verified RAM-only Firefox.
Four externally served websites; no canned/mock pages. Raw QEMU PPM frames and
guest serial evidence are mandatory. A screenshot is NOT 4K playback proof.
"""
import argparse,json,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from web85.qemu_debian_live_smoke import qmp,ppm_valid
from web92.browser_keyboard import sequence as old_sequence

SITES={
 "cnn":{"url":"https://www.cnn.com/","ram":3072,"duration":390},
 "youtube4k":{"url":"https://www.youtube.com/watch?v=TlLmve5I67o","ram":4096,"duration":470},
 "john":{"url":"https://3dbibleonline.github.io/john/","ram":3072,"duration":390},
 "bible3d":{"url":"https://74127418528426leo-del.github.io/BIBLE-3D/","ram":4096,"duration":390},
}
PUNCT={
 ':':['shift','semicolon'],'/':['slash'],'.':['dot'],'-':['minus'],
 '?':['shift','slash'],'=':['equal'],'_':['shift','minus'],
 "'":['apostrophe'],'"':['shift','apostrophe'],'(':['shift','9'],
 ')':['shift','0'],'[':['leftbracket'],']':['rightbracket'],
 '{':['shift','leftbracket'],'}':['shift','rightbracket'],
 ',':['comma'],'+':['shift','equal'],';':['semicolon'],
 '&':['shift','7'],' ':['spc'],'*':['shift','8']
}
def char_keys(c):
    if 'a'<=c<='z' or c.isdigit() and c.isascii():
        return [c]
    if 'A'<=c<='Z':
        return ['shift',c.lower()]
    if c in PUNCT:
        return PUNCT[c]
    raise ValueError('Unknown character; do not type uncertain keys: '+repr(c))
def send_key(mon,names,hold=85):
    return qmp(mon,"send-key",{"keys":[{"type":"qcode","data":name} for name in names],
                               "hold-time":hold})
def type_text(mon,s,interval=.12):
    for c in s:
        send_key(mon,char_keys(c),105)
        time.sleep(interval)
def goto(mon,url):
    if url not in [s["url"] for s in SITES.values()]:
        raise ValueError('Only explicitly reviewed public HTTPS targets allowed')
    send_key(mon,['ctrl','l'],125)
    time.sleep(1.4)
    type_text(mon,url)
    send_key(mon,['ret'],110)
def shot(mon,out,mark,result):
    dest=out/f"frame_{mark:03d}.ppm"
    qmp(mon,"screendump",{"filename":str(dest)})
    if not dest.is_file() or not ppm_valid(dest):
        raise RuntimeError("Invalid/absent real guest QEMU image: "+str(mark))
    result['screenshots'].append(dest.name)
def youtube_console(mon,out,result):
    # Probe YouTube's native HTML5 <video> element through Firefox's actual
    # Web Console. This DOES NOT force a 2160p rendition.
    # Video resolution/currentTime can be judged only from actual screenshot.
    send_key(mon,['ctrl','shift','k'],155)
    time.sleep(5)
    for name,expression in [
        ("height","document.querySelector('video').videoHeight"),
        ("time","document.querySelector('video').currentTime"),
        ("frames","document.querySelector('video').getVideoPlaybackQuality().droppedVideoFrames")]:
        try:
            type_text(mon,expression,.105)
            send_key(mon,['ret'],110)
            result['youtube_console_commands'].append({"name":name,"sent":True,
                      "expression":expression,"verified_js_result":False})
            time.sleep(5)
            shot(mon,out,{"height":365,"time":415,"frames":455}[name],result)
        except Exception as exc:
            result['errors'].append("Devtools "+name+": "+repr(exc))
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--site",choices=SITES,required=True)
    ap.add_argument("--iso",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--ram",type=int)
    a=ap.parse_args()
    s=SITES[a.site];ram=a.ram or s["ram"];total=s["duration"]
    if not 2048<=ram<=6144:raise ValueError('RAM out of range')
    iso=a.iso.resolve(strict=True)
    if iso.stat().st_size<900_000_000:raise ValueError('Not the complete Firefox ESR Live ISO')
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    mon=out/'qmp.sock'
    cmd=["qemu-system-x86_64","-machine","pc,accel=kvm","-cpu","host",
         "-m",str(ram),"-smp","2",
         "-drive",f"file={iso},if=ide,media=cdrom,id=livecd,readonly=on",
         "-boot","order=d","-display","none","-vga","std",
         "-qmp",f"unix:{mon},server=on,wait=off",
         "-serial",f"file:{out/'serial.log'}",
         "-nic","user,model=e1000,ipv6=off","-no-reboot"]
    result={"schema":"PUPPY50_V101_REAL_CNN_YOUTUBE_GITHUB_PAGES",
      "site":a.site,"target_url":s["url"],"guest_ram_mib":ram,
      "real_qemu_kvm":True,"screenshots":[],"errors":[],
      "navigation_keystrokes_submitted":False,"guest_CA_verified_public_HTTPS":False,
      "guest_nonroot_firefox_started":False,"live_media_ejected":False,
      "running_after_ejection":False,"website_visually_confirmed":False,
      "youtube_2160p_proven":False,"youtube_actual_video_playback_proven":False,
      "youtube_console_commands":[],"physical_hardware_browsing_proven":False}
    with (out/'qemu.log').open('wb') as log:
        vm=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
        start=time.monotonic()
        schedule=([18,110,150,225,290,305,310,330,365,415,455,470]
                  if a.site=="youtube4k" else [18,110,150,225,290,310,350,390])
        try:
            for mark in schedule:
                while time.monotonic()-start <mark and vm.poll() is None:
                    time.sleep(.4)
                if vm.poll() is not None:
                    result['errors'].append('VM exited before '+str(mark))
                    break
                if mark==18:
                    send_key(mon,['ret'],110)
                    result['boot_enter_sent']=True
                    continue
                if mark==150:
                    try:
                        goto(mon,s['url'])
                        result['navigation_keystrokes_submitted']=True
                    except Exception as exc:
                        result['errors'].append('QMP URL navigation: '+repr(exc))
                if mark==310:
                    try:
                        qmp(mon,'human-monitor-command',{'command-line':'eject -f livecd'})
                        block=str(qmp(mon,'human-monitor-command',{'command-line':'info block livecd'})).lower()
                        result['live_media_ejected']=('not inserted' in block or 'no media' in block)
                    except Exception as exc:
                        result['errors'].append('media eject: '+repr(exc))
                if mark==330 and a.site=="youtube4k":
                    youtube_console(mon,out,result)
                if mark not in (18,150,310,365,415,455):
                    try:shot(mon,out,mark,result)
                    except Exception as exc:result['errors'].append('QEMU frame '+str(mark)+': '+repr(exc))
            result['running_after_ejection']=vm.poll() is None and result['live_media_ejected']
        finally:
            if vm.poll() is None:
                vm.terminate()
                try:vm.wait(timeout=10)
                except subprocess.TimeoutExpired:vm.kill();vm.wait(timeout=5)
    serial=(out/'serial.log').read_text(errors='replace') if (out/'serial.log').exists() else ''
    result['guest_CA_verified_public_HTTPS']=(
      "PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_DIRECT=PASS" in serial or
      "PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_BRIDGE=PASS" in serial)
    result['guest_nonroot_firefox_started']="P50_V91_NONROOT_FIREFOX_PROCESS_SEEN" in serial
    result['has_real_final_frame']=f"frame_{total:03d}.ppm" in result['screenshots']
    (out/'result.json').write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2),flush=True)
    # Preserve negative browsing results; only guest boot/Firefox process/HTTPS
    # are automated gates. All four site/web-video results require real review.
    if not result['guest_CA_verified_public_HTTPS']:raise SystemExit('Guest CA HTTPS baseline failed')
    if not result['guest_nonroot_firefox_started']:raise SystemExit('Nonroot Firefox never started')
    if not result['navigation_keystrokes_submitted']:raise SystemExit('Site URL never submitted')
    if not result['has_real_final_frame']:raise SystemExit('Missing final actual QEMU frame')
    if not result['running_after_ejection']:raise SystemExit('RAM-only media-ejection test failed')
    print('P50_V101_BASELINE_PASS_SITE_VISUAL_AND_YOUTUBE_4K_STILL_REQUIRE_HUMAN_REVIEW')
if __name__=='__main__':main()
