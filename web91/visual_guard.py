#!/usr/bin/env python3
"""Reject the specific centered LightDM login dialog seen in real v88 frame."""
import argparse,json,re
from pathlib import Path
def analyze(path):
    raw=Path(path).read_bytes()
    m=re.match(rb'^P6\s+(\d+)\s+(\d+)\s+(\d+)\s',raw[:100])
    if not m:raise ValueError('Not QEMU P6 frame')
    w,h,maxv=map(int,m.groups());off=m.end()
    if not (640<=w<=8192 and 480<=h<=8192 and maxv==255 and len(raw)==off+3*w*h):
        raise ValueError('Incomplete or unsupported framebuffer')
    black=total=bright=center=0
    for y in range(int(.18*h),int(.96*h),7):
        for x in range(0,int(.32*w),7):
            k=off+3*(y*w+x);r,g,b=raw[k:k+3]
            total+=1
            if max(r,g,b)<48:black+=1
    for y in range(int(.39*h),int(.61*h),4):
        for x in range(int(.395*w),int(.605*w),4):
            k=off+3*(y*w+x);r,g,b=raw[k:k+3]
            center+=1
            if min(r,g,b)>230:bright+=1
    ob=round(black/total,4);cw=round(bright/center,4)
    return {'outside_black_fraction':ob,'center_bright_fraction':cw,
       'previous_LightDM_login_signature':ob>.93 and cw>.65,
       'Firefox_page_positively_verified':False,
       'note':'Not matching greeter does not positively prove Firefox. Inspect actual screenshots.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('frame',type=Path);a=p.parse_args()
    print(json.dumps(analyze(a.frame),indent=2))
