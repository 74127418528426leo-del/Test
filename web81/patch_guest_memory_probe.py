#!/usr/bin/env python3
"""Insert ONE read-only memory telemetry process into a disposable v78 root.

No kernel/initrd/CA/Firefox binary changes. Do not modify a user's host root.
"""
import argparse
import hashlib
import json
from pathlib import Path

ANCHOR='Xorg :0 vt1 -nolisten tcp -auth "$XAUTH" > /var/log/Xorg0.log 2>&1 &'
LINE='/usr/local/libexec/puppy50-memory-probe >/dev/ttyS0 2>/dev/null &'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def patch(root):
    root=Path(root).resolve(strict=True)
    if root.name!="rootfs" or root.parent.name!="output":
        raise ValueError("Refusing to patch any non-disposable root")
    launcher=root/"usr/local/bin/puppy50-web-launch"
    ca=root/"etc/ssl/certs/ca-certificates.crt"
    ff=root/"usr/lib/firefox-esr"
    if not launcher.is_file() or not ca.is_file() or not ff.is_dir():
        raise ValueError("Real v78 browser files missing")
    old=launcher.read_text()
    if old.count(ANCHOR)!=1 or LINE in old:
        raise ValueError("Xorg launcher anchor missing, repeated or already patched")
    before_ca=digest(ca)
    probe=root/"usr/local/libexec/puppy50-memory-probe"
    probe.parent.mkdir(parents=True,exist_ok=True)
    probe.write_bytes(Path(__file__).with_name("guest_memory_probe.sh").read_bytes())
    probe.chmod(0o755)
    launcher.write_text(old.replace(ANCHOR,LINE+"\n"+ANCHOR))
    launcher.chmod(0o755)
    if digest(ca)!=before_ca:raise AssertionError("CA bundle unexpectedly changed")
    return {
      "schema":"PUPPY50_V81_GUEST_MEMORY_ONLY_INSTRUMENTATION",
      "source_v78_package_database_unchanged":True,
      "source_v78_firefox_binaries_unchanged":True,
      "source_v78_CA_bundle_unchanged":True,
      "source_v78_network_probe_unchanged":True,
      "kernel_and_initrd_unchanged":True,
      "read_only_10second_memory_pressure_serial_probe":True,
      "Firefox_sandbox_and_site_isolation_preserved":True,
      "guest_RAM_page_behavior_modified_by_probe_possible":True,
      "usable_public_release":False
    }

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root",type=Path)
    r=patch(ap.parse_args().root)
    print(json.dumps(r,indent=2))
