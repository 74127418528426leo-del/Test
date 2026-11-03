#!/usr/bin/env python3
"""Fail-closed public ONLINE QEMU prerelease gate.

We require a real guest CA-validated external HTTPS test AND independent
manual inspection of a Firefox screenshot of the public website.
A QEMU keypress, a browser PID or a successful curl alone is not enough.
"""
import argparse,hashlib,json
from pathlib import Path

def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def validate(iso, guest_report, review, screenshot):
    iso=Path(iso);review=Path(review);screenshot=Path(screenshot)
    proof=json.loads(Path(guest_report).read_text())
    human=json.loads(review.read_text())
    needed=("real_RAM_root_and_CD_ejection","guest_DHCP","guest_DNS",
            "guest_strict_CA_HTTPS","offline_Firefox_input",
            "external_URL_keypress_submitted")
    if not all(proof.get(k) is True for k in needed):
        raise ValueError("Actual guest TLS/input requirements not met")
    if not (proof.get("host_bridge_guest_TLS") or proof.get("direct_guest_TLS")):
        raise ValueError("No confirmed end-to-end HTTPS transport")
    if not all(human.get(k) is True for k in
       ("reviewed_screenshot","public_website_actually_visible_in_firefox",
        "firefox_HTTPS_URL_confirmed")):
        raise ValueError("Independent visual public-site proof missing")
    if human.get("screenshot_sha256")!=digest(screenshot):
        raise ValueError("Manually inspected screenshot checksum mismatch")
    if human.get("iso_sha256")!=digest(iso):
        raise ValueError("Manually inspected ISO checksum mismatch")
    with iso.open("rb") as f:
        f.seek(16*2048+1)
        if f.read(5)!=b"CD001":raise ValueError("Not bootable ISO9660")
    return {"schema":"PUPPY50_V68_PUBLIC_ONLINE_QEMU_RELEASE_PROOF",
            "iso_filename":iso.name,"iso_sha256":digest(iso),
            "iso_bytes":iso.stat().st_size,
            "actual_1gib_Firefox_public_website_visible":True,
            "guest_public_HTTPS_strict_CA_verified":True,
            "RAM_root_and_boot_media_ejection":True,
            "guest_mouse_keyboard_offline_page_proven":True,
            "384mib_browser_working":False,
            "any_physical_network_or_wifi_certified":False,
            "browser_security_update_policy_certified":False,
            "physical_2010_Intel_hardware_supported":False,
            "manual_screenshot_sha256":digest(screenshot),
            "version":"experimental QEMU-only prerelease"}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--iso",required=True,type=Path)
    p.add_argument("--results",required=True,type=Path)
    p.add_argument("--review",required=True,type=Path)
    p.add_argument("--screenshot",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    r=validate(a.iso,a.results,a.review,a.screenshot)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2)+"\n")
    print(json.dumps(r,indent=2))
if __name__=="__main__":main()
