#!/usr/bin/env python3
"""Measure three independent visible local browser states in real QEMU P6 frames.
No OCR, no process-ID based success, and no claim of real-website networking.
"""
import argparse,json,re
from pathlib import Path

PALETTE={
 'script_ready':(255,192,68),
 'mouse_click':(212,140,39),
 'keyboard':(43,204,113)
}

def profile(path, stride=211):
    raw=Path(path).read_bytes()
    m=re.match(rb"P6\s+(\d+)\s+(\d+)\s+(\d+)\s",raw)
    if not m:raise ValueError("Expected a P6 PPM")
    w,h,maxv=map(int,m.groups())
    pixels=raw[m.end():]
    if maxv!=255 or w<100 or h<100 or len(pixels)!=w*h*3:
        raise ValueError("Invalid framebuffer dimensions or pixels")
    counts={name:0 for name in PALETTE}
    n=0
    for i in range(0,w*h,stride):
        p=pixels[3*i:3*i+3]
        for name,rgb in PALETTE.items():
            if all(abs(x-y)<=20 for x,y in zip(p,rgb)):counts[name]+=1
        n+=1
    return {"width":w,"height":h,"samples":n,
            "fractions":{k:round(v/n,5) for k,v in counts.items()}}

def compare_stages(before,clicked,keyed):
    a,b,c=profile(before),profile(clicked),profile(keyed)
    if (a['width'],a['height'])!=(b['width'],b['height']) or (a['width'],a['height'])!=(c['width'],c['height']):
        raise ValueError("Framebuffer resolution differs between stages")
    initial_ready=a["fractions"]["script_ready"]>0.012
    mouse=(a["fractions"]["mouse_click"]<0.05 and b["fractions"]["mouse_click"]>0.22)
    keyboard=(b["fractions"]["keyboard"]<0.05 and c["fractions"]["keyboard"]>0.22)
    return {"schema":"PUPPY50_V56_INDEPENDENT_DOM_EVENT_PROOF",
            "before":a,"after_click":b,"after_key":c,
            "script_ready":initial_ready,
            "click_confirmed":mouse,
            "key_confirmed":keyboard,
            "full_input_proof":bool(initial_ready and mouse and keyboard),
            "network_https_real_hardware_proven":False,
            "scope":"Visible local offline script and DOM mouse/key handlers only; guest QEMU HMP submission must be independently checked."}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('before',type=Path);p.add_argument('clicked',type=Path)
    p.add_argument('keyed',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    result=compare_stages(a.before,a.clicked,a.keyed)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
