#!/usr/bin/env python3
"""Conservative analysis of guest-side mount evidence and external QEMU ejection.

This parser never treats process startup, Linux boot or successful CI execution
as proof of interactive browsing. Use --require-ram-proof to fail on incomplete
mount or backing evidence, rather than invent success from legacy v39 markers.
"""
import argparse
import json
import re
from pathlib import Path

def evaluate(log, qemu=None):
    data = dict(re.findall(r"^(RAM_IMAGE_PATH|RAM_IMAGE_BYTES|PUPPY50_RAM_PROBE_VERSION)=(.*)$", log, re.M))
    complete = "PUPPY50_RAM_PROBE_BEGIN" in log and "PUPPY50_RAM_PROBE_END" in log
    mounts = set(re.findall(r"^MOUNT source=(\S+) target=(\S+) fstype=(\S+)", log, re.M))
    loops = re.findall(r"^LOOP_BACKING device=(\S+) path=(\S+)", log, re.M)
    info = dict((name,int(n)) for name,n in re.findall(r"^MEMINFO key=(\w+): kib=(\d+)", log,re.M))
    swaps = re.findall(r"^SWAP_DEVICE path=(\S+) type=(\S+) size_kib=(\d+) used_kib=(\d+)",log,re.M)
    ramfs = any(target=="/.web-ram" and typ=="tmpfs" for _,target,typ in mounts)
    squash = any(target=="/.web-lower" and typ=="squashfs" for _,target,typ in mounts)
    overlay = any(target=="/" and typ=="overlay" for _,target,typ in mounts)
    iso_still_mounted = any(typ=="iso9660" for _,_,typ in mounts)
    # Only accept an explicit link to the SAME path whose parent was shown
    # tmpfs-backed. Some kernels show the pre-move path /ram; in that case
    # refuse full proof until the guest records file-system identity.
    loop_in_current_ram = any(path=="/.web-ram/webroot.sfs" for _,path in loops)
    copied = bool(re.search(r"^PUPPY50_WEB_V45_RAM_COPY_COMPLETE bytes=\d+", log, re.M))
    switched = "PUPPY50_WEB_V45_SWITCH_ROOT_RAM_ONLY" in log
    media_unmounted = "PUPPY50_WEB_V45_BOOT_MEDIA_UNMOUNTED" in log
    image_recorded = data.get("RAM_IMAGE_PATH")=="/.web-ram/webroot.sfs" and data.get("RAM_IMAGE_BYTES","").isdigit()
    disk_swap = [s[0] for s in swaps if not s[0].startswith("/dev/zram")]
    disk_swap_unknown = info.get("SwapTotal",0)>0 and not swaps
    mounts_verified = all([complete,ramfs,squash,overlay,loop_in_current_ram,image_recorded])
    guest_ram_only_verification = all([mounts_verified,copied,switched,media_unmounted,not iso_still_mounted,not disk_swap,not disk_swap_unknown])
    qemu_verified = isinstance(qemu,dict) and qemu.get("media_ejection_verified") is True
    return {
      "schema": "PUPPY50_RAM_PROOF_REVIEW_V1",
      "guest_probe_complete": complete,
      "ram_tmpfs_mount_seen": ramfs,
      "squashfs_lower_mount_seen": squash,
      "root_overlay_mount_seen": overlay,
      "loop_sfs_backed_by_current_ram_path": loop_in_current_ram,
      "ram_sfs_file_size_seen": image_recorded,
      "root_switch_and_copy_markers": copied and switched and media_unmounted,
      "iso9660_mount_still_present": iso_still_mounted,
      "disk_swap_devices": disk_swap,
      "swap_enabled_but_unattributed": disk_swap_unknown,
      "guest_ram_only_verification": guest_ram_only_verification,
      "external_qemu_cd_ejection_verified": qemu_verified,
      "strict_ram_only_proof_complete": guest_ram_only_verification and qemu_verified,
      "firefox_requested": "PUPPY50_WEB_V45_FIREFOX_REQUESTED" in log,
      "interactive_web_browser_proven": False,
      "https_and_usb_proven": False,
      "ram_mib_kernel_reported": round(info["MemTotal"]/1024,2) if "MemTotal" in info else None,
      "note": "Only claims mount-source proof and external CD ejection when all required evidence is present. Website usability and security require separate tests."
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("serial_log",type=Path)
    p.add_argument("--qemu-result",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--require-ram-proof",action="store_true")
    a=p.parse_args()
    qemu=json.loads(a.qemu_result.read_text()) if a.qemu_result else None
    result=evaluate(a.serial_log.read_text(errors="replace"),qemu)
    value=json.dumps(result,indent=2)+"\n"
    if a.out: a.out.write_text(value)
    print(value,end="")
    return 2 if a.require_ram_proof and not result["strict_ram_only_proof_complete"] else 0

if __name__=="__main__":
    raise SystemExit(main())
