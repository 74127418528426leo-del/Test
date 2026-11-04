#!/usr/bin/env python3
"""V100: add ONLY read-only memory diagnostics to exact v91 Firefox Live root.
No swap of any kind created. No change to Firefox, HTTPS or network policy.
"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from web99.patch_live_zram import TELEMETRY,DIAG_UNIT
def patch(root):
    root=Path(root).resolve(strict=True)
    if root==Path("/") or not root.is_dir():raise ValueError("Never modify host root")
    baseline=[
      "usr/bin/firefox-esr",
      "usr/sbin/lightdm",
      "usr/local/sbin/puppy50-prepare-session",
      "usr/local/sbin/puppy50-network-probe",
      "etc/ssl/certs/ca-certificates.crt"]
    missing=[name for name in baseline if not (root/name).is_file()]
    if missing:raise ValueError("Base not recognized: "+repr(missing))
    if "P50_V91_LIGHTDM_AUTOLOGIN_PREPARED" not in (root/"usr/local/sbin/puppy50-prepare-session").read_text():
        raise ValueError("Not the previously proven Firefox Live baseline")
    def write(path,content,mode=0o644):
        dest=root/path
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(content)
        dest.chmod(mode)
    # The guest only reads /proc and /sys; never writes to RAM/swap configuration.
    write("usr/local/sbin/puppy50-memory-diagnostics",TELEMETRY,0o755)
    write("etc/systemd/system/puppy50-memory-diagnostics.service",DIAG_UNIT)
    assert not (root/"etc/systemd/system/puppy50-zram-live.service").exists()
    return {
      "schema":"PUPPY50_V100_FIREFOX_LIVE_DIAGNOSTICS_ONLY",
      "writes_to_physical_disks":False,
      "adds_zram_or_swap":False,
      "modifies_browser_network_or_TLS":False,
      "intended_unchanged_2GiB_firefox_behavior":True,
      "guest_evidence_required":True}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("root",type=Path)
    args=p.parse_args()
    print(json.dumps(patch(args.root),indent=2))
