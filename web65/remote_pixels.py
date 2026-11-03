#!/usr/bin/env python3
"""Confirm an actual network-served webpage appears in the QEMU framebuffer.

Requires a uniquely colored web page AFTER a real Firefox address-bar
navigation, and absence of that color BEFORE the navigation. A host-side
GET log plus this evidence proves browser reached a webpage via QEMU NAT.
This does NOT prove public Internet or HTTPS.
"""
import re
from pathlib import Path

COLOR=(203,45,145)
def color_fraction(path, stride=173):
    raw=Path(path).read_bytes()
    m=re.match(rb"P6\s+(\d+)\s+(\d+)\s+(\d+)\s",raw)
    if not m:raise ValueError("expected P6 QEMU screenshot")
    w,h,maxv=map(int,m.groups())
    pix=raw[m.end():]
    if w<200 or h<200 or maxv!=255 or len(pix)!=w*h*3:
        raise ValueError("invalid framebuffer size or color depth")
    matches=0
    count=0
    for j in range(0,w*h,stride):
        rgb=pix[3*j:3*j+3]
        count+=1
        if all(abs(a-b)<=17 for a,b in zip(rgb,COLOR)):matches+=1
    return {"width":w,"height":h,"fraction":round(matches/count,5),"samples":count}

def remote_page_proof(before,after):
    a,b=color_fraction(before),color_fraction(after)
    if (a["width"],a["height"])!=(b["width"],b["height"]):
        raise ValueError("QEMU screenshot resolutions differ")
    return {"schema":"PUPPY50_V65_REAL_HOST_WEBPAGE_FRAMEBUFFER",
            "before":a,"after":b,
            "page_color_transition":bool(a["fraction"]<0.02 and b["fraction"]>0.18),
            "proof_scope":"Firefox displayed a distinct remote host HTTP page over QEMU NAT; not external HTTPS"}
