#!/usr/bin/env python3
"""Inspect actual QEMU P6 framebuffer without OCR, proxy or invented success.

The offline page switches its entire body to #2bcc71 on a real 't' keypress.
Compare the captured pre-key and post-key frame; exact green threshold is a
conservative proxy for an input handler actually executing on screen.
"""
import argparse
import json
import re
from pathlib import Path

TARGET=(43,204,113)

def inspect(path, stride=313):
    raw=Path(path).read_bytes()
    match=re.match(rb"P6\s+(\d+)\s+(\d+)\s+(\d+)\s",raw)
    if not match:
        raise ValueError("Not a P6 PPM framebuffer")
    w,h,maxv=map(int,match.groups())
    if maxv!=255 or w<=0 or h<=0:
        raise ValueError("Unexpected RGB format")
    pixels=raw[match.end():]
    if len(pixels)!=w*h*3:
        raise ValueError(f"Wrong framebuffer byte count {len(pixels)} != {w*h*3}")
    hits=samples=0
    for index in range(0,w*h,stride):
        p=3*index
        rgb=pixels[p:p+3]
        if all(abs(a-b)<35 for a,b in zip(rgb,TARGET)):
            hits+=1
        samples+=1
    return {"image":str(path),"width":w,"height":h,"samples":samples,
            "matching_green_fraction":round(hits/samples,5)}

def compare(before,after):
    b,a=inspect(before),inspect(after)
    if b['width']!=a['width'] or b['height']!=a['height']:
        raise ValueError("Framebuffer resolution changed")
    return {"schema":"PUPPY50_V55_REAL_KEYBOARD_FRAMEBUFFER_PROOF",
            "before":b,"after":a,
            "green_change_fraction":round(a["matching_green_fraction"]-b["matching_green_fraction"],5),
            "keyboard_event_visibly_changed_page":(b["matching_green_fraction"]<0.04 and
                 a["matching_green_fraction"]>0.30 and
                 a["matching_green_fraction"]-b["matching_green_fraction"]>0.25),
            "web_security_https_network_webgl_proven":False,
            "limits":"Proves only that the displayed local offline page changed in response to the virtual T keypress. No network, HTTPS, real hardware, click input, or modern websites proved."}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("before",type=Path);ap.add_argument("after",type=Path)
    ap.add_argument("--report",type=Path,required=True)
    a=ap.parse_args()
    result=compare(a.before,a.after)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
