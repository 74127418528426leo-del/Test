#!/usr/bin/env python3
"""Analyze the actual QEMU framebuffer body instead of trusting URL changes.

The v79 workflow declared success when the custom home-page cyan strip
disappeared. The earlier raw screenshots proved that was a false-positive:
one page was 99.94% white in the central body, while a correctly rendered
Wikipedia home page had meaningful text/images. This classifier is a
strictly supplementary visual signal, not OCR or an HTML/content verifier.

Never report 'Wikipedia loaded' from this checker alone. Use raw frames
for independent human review before publication or claims.
"""
import argparse
import json
import re
from pathlib import Path

RECT=(350,175,1550,860)

def central_pixels(path):
    raw=Path(path).read_bytes()
    m=re.match(rb"P6\s+(\d+)\s+(\d+)\s+255\s",raw)
    if not m:raise ValueError("Expected real uncompressed P6 QEMU screenshot")
    w,h=map(int,m.groups())
    pix=memoryview(raw)[m.end():]
    if w<1600 or h<900 or len(pix)!=3*w*h:
        raise ValueError("Wrong or truncated QEMU framebuffer")
    x1,y1,x2,y2=RECT
    count=white=dark=chromatic=0
    # Coarse but deterministic 2D sampling. Ignore browser chrome, focus on
    # the actual webpage region, where a blank tab is entirely white.
    for y in range(y1,y2,5):
        for x in range(x1,x2,5):
            i=(y*w+x)*3
            r,g,b=pix[i:i+3]
            count+=1
            if min(r,g,b)>=238:white+=1
            if max(r,g,b)<150:dark+=1
            if max(r,g,b)-min(r,g,b)>60:chromatic+=1
    return {"width":w,"height":h,"samples":count,
            "body_white_fraction":round(white/count,5),
            "body_dark_fraction":round(dark/count,5),
            "body_chromatic_fraction":round(chromatic/count,5)}

def read_frames(folder,marks=(145,185,205,245,285,325,365,405)):
    images=[]
    for t in marks:
        path=Path(folder)/f"frame_{t:03d}.ppm"
        if not path.is_file():continue
        images.append({"seconds":t,**central_pixels(path)})
    return images

def assess(folder,source,ram):
    folder=Path(folder)
    meta=folder/"result.json"
    r=json.loads(meta.read_text()) if meta.is_file() else {}
    rows=read_frames(folder)
    post=[x for x in rows if x["seconds"]>=205]
    final=post[-1] if post else None
    # Pure white bodies are NOT webpage proof; the thresholds are for
    # triage only, with mandatory screenshot review.
    blank=bool(final and final["body_white_fraction"]>=.97 and
               final["body_dark_fraction"]<.003)
    nonblank=bool(final and final["body_dark_fraction"]>=.008 and
                  final["body_white_fraction"]<.93)
    return {
      "schema":"PUPPY50_V84_QEMU_WEBPAGE_BODY_PIXEL_TRIAGE",
      "source":source,"ram_mib":ram,
      "real_ram_boot":bool(r.get("ram_root_copy") and r.get("ram_root_switch")),
      "guest_strict_CA_public_HTTPS":bool(r.get("guest_public_CA_verified_HTTPS")),
      "real_virtual_mouse_click_requested":bool(r.get("real_qemu_browser_link_click_submitted")),
      "network_adapter_stayed_online":bool(r.get("QEMU_virtual_NIC_kept_online")),
      "home_page_disappeared_after_click":bool((r.get("Wikipedia_link_pixel_transition") or {}).get("homepage_color_disappeared")),
      "body_blank_at_final_screenshot":blank,
      "body_nonblank_content_candidate":nonblank,
      "Wikipedia_site_visually_confirmed":False,
      "browser_secure_for_sensitive_accounts":False,
      "any_physical_wifi_tested":False,
      "frames":rows,
      "note":"Nonblank means only enough dark/color pixels to rule out an all-white tab. Independent visual inspection is required."
    }

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frames",type=Path,required=True)
    ap.add_argument("--source",required=True)
    ap.add_argument("--ram",type=int,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    res=assess(a.frames,a.source,a.ram)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(res,indent=2)+"\n")
    print(json.dumps({k:v for k,v in res.items() if k!="frames"},indent=2))
