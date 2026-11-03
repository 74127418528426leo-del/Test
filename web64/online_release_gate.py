#!/usr/bin/env python3
"""Acceptance gate for external-network guest, without inventing website proof.

* Requires real 1024MiB QEMU RAM-root, verified user input, DHCP and
  CA-verified HTTPS from inside the guest using curl.
* Requires a screenshot after attempting to navigate Firefox to example.com,
  but this alone is NOT certified browser page rendering. Inspect it manually.
* The 384MiB guest need only prove a true RAM-root boot, never browser use.
"""
import argparse,hashlib,json
from pathlib import Path
MIB=1048576
EARLY=("PUPPY50_V58_INPUT_EARLY_LOADED=evdev",
       "PUPPY50_V58_INPUT_EARLY_LOADED=psmouse",
       "PUPPY50_V64_NETWORK_EARLY_E1000_LOADER_PRESENT=PASS")
def validate(iso,evidence):
    iso=Path(iso);evidence=Path(evidence)
    if not iso.is_file() or iso.stat().st_size < 50*MIB:
        raise ValueError("Online bootable ISO missing or implausibly small")
    with iso.open("rb") as f:
        f.seek(16*2048+1)
        if f.read(5)!=b"CD001":raise ValueError("Not an ISO9660 image")
    guests={}
    for ram in (384,1024):
        p=evidence/f"ram_{ram}MiB"
        res=json.loads((p/"result.json").read_text())
        serial=(p/"serial.log").read_text(errors="replace")
        for key in ("ram_copy_complete","ram_root_switch","media_ejection_verified"):
            if res.get(key) is not True:raise ValueError(f"Missing {ram}MiB RAM-root/media gate: {key}")
        for mark in EARLY[:2]:
            if mark not in serial:raise ValueError(f"Missing kernel input marker at {ram}MiB: {mark}")
        guests[str(ram)]={"ram_root_and_media_eject":True,
                          "offline_interaction":bool(res.get("script_ready_visually_proven") and res.get("mouse_click_visually_proven") and res.get("keyboard_visually_proven")),
                          "guest_certificate_verified_https":bool(res.get("guest_ca_verified_external_https"))}
        if ram==1024:
            required=("script_ready_visually_proven","mouse_click_visually_proven","keyboard_visually_proven",
                      "qemu_e1000_early_loaded","guest_dhcp_lease","guest_default_route","guest_dns_config",
                      "guest_ca_verified_external_https","guest_online_ready","firefox_address_bar_keys_submitted")
            missing=[key for key in required if res.get(key) is not True]
            if missing:raise ValueError("Online 1024MiB acceptance failed: "+repr(missing))
            if not (p/"frame_245.ppm").is_file():raise ValueError("No actual after-navigation browser screenshot")
    h=hashlib.sha256()
    with iso.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return {"schema":"PUPPY50_V64_ONLINE_QEMU_EXPERIMENT",
            "iso_filename":iso.name,"iso_bytes":iso.stat().st_size,"iso_sha256":h.hexdigest(),
            "guests":guests,
            "1024mib_guest_real_DHCP_DNS_CA_verified_external_HTTPS":True,
            "1024mib_offline_Firefox_JS_mouse_keyboard":True,
            "1024mib_Firefox_HTTPS_URL_navigation_command_sent":True,
            "browser_actual_remote_page_content_verified_automatically":False,
            "384mib_full_browser_works":False,"physical_wifi_any_network_supported":False,
            "physical_computer_GPU_firmware_validated":False,
            "sandbox_https_security_certified":False,
            "website_screenshot_requires_manual_review":True,
            "qemu_network":"outbound-only unprivileged user-mode NAT (e1000)"
           }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--iso",type=Path,required=True)
    p.add_argument("--evidence",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=validate(a.iso,a.evidence)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
