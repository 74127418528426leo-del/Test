#!/usr/bin/env python3
"""Gate a public v70 ISO on the raw v70 guest and an independently reviewed frame."""
import argparse
import hashlib
import json
import re
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def verify(iso,manifest,evidence,review):
    iso=Path(iso)
    r=json.loads(Path(manifest).read_text())
    e=Path(evidence)/"evidence"/"ram_1024MiB"
    raw=json.loads((e/"result.json").read_text())
    serial=(e/"serial.log").read_text(errors="replace")
    human=json.loads(Path(review).read_text())
    shot=e/human["reviewed_frame_name"]
    conditions={
     "original_iso_hash":digest(iso)==r.get("iso_sha256"),
     "iso_size":iso.stat().st_size==r.get("iso_bytes"),
     "actual_ram_root":raw.get("ram_root_copy") is True and raw.get("ram_root_switch") is True,
     "actual_cd_eject":raw.get("ejected") is True,
     "real_firefox_started":raw.get("xorg_started") is True and raw.get("firefox_launch_requested") is True,
     "guest_DHCP_DNS_CA":all(raw.get(k) is True for k in ("guest_DHCP","guest_DNS","guest_public_CA_verified_HTTPS")),
     "guest_network_status_file_written":raw.get("guest_status_page_written") is True,
     "demo_not_scheduled":raw.get("timed_demo_not_requested") is True,
     "actual_homepage_pixels":raw.get("actual_user_homepage_visibly_rendered") is True,
     "home_page_visually_reviewed":human.get("reviewed_screenshot") is True and human.get("normal_homepage_visible") is True,
     "review_frame_hash":digest(shot)==human.get("reviewed_frame_sha256"),
     "review_iso_hash":digest(iso)==human.get("iso_sha256"),
     "review_run":human.get("run_id")==41660921113,
     "no_automatic_external_navigation":'PUPPY50_V69_NATIVE_FIREFOX_NAV_REQUESTED' not in serial,
     "guest_strict_TLS_actual":'PUPPY50_V67_EXTERNAL_TLS_CA_VERIFIED=PASS' in serial,
    }
    if not all(conditions.values()):
        raise ValueError("Cannot certify public v70 preview: "+
                        repr([name for name,passed in conditions.items() if not passed]))
    with iso.open("rb") as f:
        f.seek(16*2048+1)
        if f.read(5)!=b"CD001":raise ValueError("Missing ISO9660 descriptor")
    return {
      "schema":"PUPPY50_V70_PUBLIC_NORMAL_BROWSER_PROOF",
      "source_KVM_run_id":41660921113,
      "iso_name":iso.name,
      "iso_bytes":iso.stat().st_size,
      "iso_sha256":digest(iso),
      "reviewed_homepage_frame_sha256":digest(shot),
      "normal_homepage_visible":True,
      "CA_verified_HTTPS_in_guest":True,
      "real_boot_into_RAM_and_CD_ejected":True,
      "network_status_present":True,
      "demonstration_auto_navigation_removed":True,
      "other_public_sites_visually_verified":False,
      "physical_any_network_or_WiFi_proven":False,
      "384mib_Firefox_browser_usable":False,
      "certified_secure_for_sensitive_browsing":False,
      "release_type":"Experimental QEMU-only preview"
    }
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso",required=True,type=Path)
    ap.add_argument("--manifest",required=True,type=Path)
    ap.add_argument("--evidence",required=True,type=Path)
    ap.add_argument("--review",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    report=verify(a.iso,a.manifest,a.evidence,a.review)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
