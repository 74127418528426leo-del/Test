#!/usr/bin/env python3
"""Patch ONLY the extracted v64 RAM-root software, not the kernel or bootloader.

The ISO's tested e1000+evdev initrd remains byte-for-byte unchanged; swap
the network probe for a CA-verified direct/proxy fallback diagnostic.
"""
import argparse
from pathlib import Path
def patch(root):
    root=Path(root)
    launcher=root/"usr/local/bin/puppy50-web-launch"
    dest=root/"usr/local/bin/puppy50-network-probe"
    cert=root/"etc/ssl/certs/ca-certificates.crt"
    firefox=root/"usr/lib/firefox-esr"
    src=Path(__file__).with_name("online_probe.sh")
    if not (launcher.is_file() and dest.is_file() and firefox.is_dir() and cert.is_file()):
        raise ValueError("Existing complete v64 Firefox/CA/network baseline absent")
    if "puppy50-network-probe" not in launcher.read_text():
        raise ValueError("Online probe is not invoked before Firefox")
    script=src.read_bytes()
    dest.write_bytes(script)
    dest.chmod(0o755)
    page=root/"usr/share/puppy50web/index.html"
    if not page.is_file():raise ValueError("Offline DOM test page missing")
    # Keep the original local-page interaction markers intact.
    contents=page.read_text()
    if "KEYBOARD CONFIRMED" not in contents:
        raise ValueError("Original keyboard proof absent")
    return {"software_overlay_bytes":len(script),
            "kernel_and_initrd_changed":False,
            "CA_bundle_preserved":True,
            "Firefox_input_proof_preserved":True,
            "TLS_certificate_verification_disabled":False}
if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root",type=Path)
    args=ap.parse_args()
    print("PUPPY50_V67_SOFTWARE_OVERLAY",patch(args.root))
