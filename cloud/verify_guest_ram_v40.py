#!/usr/bin/env python3
"""Fail-closed Puppy50 v40: guest records verify actual RAM-backed SFS layers after CD eject."""
import argparse,json,re
from pathlib import Path

def verify(serial, qemu_report, manifest):
    out={"schema":"puppy50-v40-guest-loop-backing","all_original_sfs_in_ram":False,
         "no_disk_swap":False,"loop_backings_in_ram":False,
         "media_ejected":bool(qemu_report.get('media_ejection_verified')),
         "post_eject_gui_observed":False,"strict_ram_only_pass":False,
         "guest_samples":[],"50mb_ram_achieved":False}
    serial=serial.replace('\r','')
    blocks=re.findall(r'PUPPY50_V40_BEGIN sample=(\d+)(.*?)PUPPY50_V40_END sample=\1',serial,re.S)
    for n,body in blocks:
        fs={k:int(v) for k,v in re.findall(r'^PUPPY50_V40_SFS file=([^\s]+) size=(\d+)$',body,re.M)}
        lb=re.search(r'PUPPY50_V40_LOOP_BACKING(.*?)PUPPY50_V40_SWAP',body,re.S)
        loops=re.findall(r'^/dev/loop\d+:.*',lb.group(1),re.M) if lb else []
        swap=re.search(r'PUPPY50_V40_SWAP(.*?)PUPPY50_V40_MEMINFO',body,re.S)
        lines=swap.group(1).splitlines() if swap else []
        swapdev=[x.split()[0] for x in lines if x.strip() and not x.startswith('Filename') and len(x.split())>=3]
        gui=re.findall(r'^PUPPY50_V40_GUI_PROCESS ([^\s]+) PASS$',body,re.M)
        out["guest_samples"].append({"sample":int(n),"copies":fs,"loops":loops,"swaps":swapdev,"gui":gui})
    if not out['guest_samples']:return out
    late=out["guest_samples"][-1]
    out['all_original_sfs_in_ram']=set(manifest.items()).issubset(set(late['copies'].items()))
    sfsloop=[x for x in late['loops'] if '.sfs' in x.lower()]
    out['loop_backings_in_ram']=len(sfsloop)>=len(manifest) and all('/mnt/tmpfs/' in x or '/initrd/mnt/tmpfs/' in x for x in sfsloop)
    out['no_disk_swap']=all(s.startswith('/dev/zram') or s.startswith('/dev/ram') for s in late['swaps'])
    out['post_eject_gui_observed']=len(out['guest_samples'])>=8 and all(x in late["gui"] for x in ('Xorg','jwm','ROX-Filer'))
    out['strict_ram_only_pass']=all(out[k] for k in ('all_original_sfs_in_ram','no_disk_swap','loop_backings_in_ram','media_ejected','post_eject_gui_observed'))
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument('serial',type=Path);p.add_argument('qemu_report',type=Path);p.add_argument('manifest',type=Path)
    p.add_argument('--out',type=Path,default=Path('v40_report.json'))
    a=p.parse_args()
    result=verify(a.serial.read_text(errors="replace") if a.serial.is_file() else "",
                  json.loads(a.qemu_report.read_text()),json.loads(a.manifest.read_text()))
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!='guest_samples'},indent=2))
    if not result["strict_ram_only_pass"]:raise SystemExit("Guest RAM-only proof incomplete; refusing to release ISO")

if __name__=='__main__':main()
