#!/usr/bin/env python3
"""Schedule a native Firefox new-tab command AFTER the local input validation.
This changes only the compressed rootfs; kernel and initrd remain unchanged.
A successful CLI command is never counted as webpage rendering proof.
"""
from pathlib import Path
import argparse,json

ANCHOR="su -s /bin/sh web -c 'DISPLAY=:0 XAUTHORITY=/home/web/.Xauthority HOME=/home/web firefox-esr file:///usr/share/puppy50web/index.html' >/var/log/firefox.log 2>&1"
SCRIPT="""# v69 test: preserve the original local page and click/key proof. Afterwards
# ask THE SAME unprivileged existing Firefox instance to open a public URL.
# This avoids fragile QEMU HMP emulation of a multi-character address-bar URL.
(
  sleep 205
  echo 'PUPPY50_V69_NATIVE_FIREFOX_NAV_REQUESTED=https://example.com/' >/dev/ttyS0 2>/dev/null || true
  su -s /bin/sh web -c 'DISPLAY=:0 XAUTHORITY=/home/web/.Xauthority HOME=/home/web firefox-esr --new-tab https://example.com/' >>/var/log/firefox-native-nav.log 2>&1
  code=$?
  echo "PUPPY50_V69_NATIVE_FIREFOX_NAV_EXIT=$code" >/dev/ttyS0 2>/dev/null || true
  tail -15 /var/log/firefox-native-nav.log >/dev/ttyS0 2>/dev/null || true
) &
"""
def patch(root):
    root=Path(root)
    launch=root/"usr/local/bin/puppy50-web-launch"
    if not launch.is_file():raise ValueError("Firefox start script missing")
    src=launch.read_text()
    if src.count(ANCHOR)!=1:
        raise ValueError("Exact Firefox startup anchor missing or duplicated")
    if "PUPPY50_V69_NATIVE_FIREFOX_NAV_REQUESTED" in src:
        raise ValueError("v69 automatic navigation already present")
    launch.write_text(src.replace(ANCHOR,SCRIPT+ANCHOR))
    launch.chmod(0o755)
    return {"native_firefox_navigation_scheduled":True,
      "remote_page_rendering_proven":False,
      "before_local_mouse_key_proof":False,
      "boot_kernel_initrd_unchanged":True,
      "guest_HTTPS_validation_preserved":True}
if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("root",type=Path)
    print(json.dumps(patch(ap.parse_args().root),indent=2))
