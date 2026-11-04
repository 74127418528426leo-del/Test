#!/usr/bin/env python3
"""Puppy50 v102 Intel-graphics-only Live ISO experiment.

Conservative scoped prune only:
- NVIDIA discrete GPU firmware and AMDGPU GPU firmware (NOT network firmware)
- Redundant copies of kernel/initramfs under /boot INSIDE read-only SFS.
The actual bootable ISO kernel and initrd OUTSIDE SFS remain byte-identical.

This variant loses support for hardware requiring those GPU firmwares. It
does NOT promise all hardware or any Wi-Fi access. Never patch a host root.
"""
import argparse,hashlib,json,shutil
from pathlib import Path

PRESERVE=[
 "usr/bin/firefox-esr",
 "usr/local/sbin/puppy50-network-probe",
 "etc/ssl/certs/ca-certificates.crt",
 "usr/local/sbin/puppy50-memory-diagnostics",
 "etc/skel/.config/openbox/autostart",
]
GPU_FIRMWARE=["usr/lib/firmware/nvidia","usr/lib/firmware/amdgpu"]

def hash_bytes(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def secure_path(root,rel,allow_internal_symlink=False):
    p=root/rel
    if not p.exists() and not p.is_symlink():raise ValueError("Missing target "+rel)
    if p.is_symlink() and not allow_internal_symlink:raise ValueError("Refusing symlink target "+rel)
    resolved=p.resolve(strict=True)
    if not resolved.is_relative_to(root):raise ValueError("Target escapes extracted root")
    return resolved
def patch(path):
    root=Path(path).resolve(strict=True)
    if root==Path("/") or not root.is_dir():raise ValueError("Never modify host root")
    for f in PRESERVE: secure_path(root,f,allow_internal_symlink=True)
    if not (root/"etc/systemd/system/puppy50-memory-diagnostics.service").is_file():
        raise ValueError("Not the tested v100 diagnostics-only Firefox baseline")
    if (root/"etc/systemd/system/puppy50-zram-live.service").exists():
        raise ValueError("Do not mix the failed zram experiment into v102")
    before={name:hash_bytes(root/name) for name in PRESERVE}
    removed=[]
    for rel in GPU_FIRMWARE:
        p=secure_path(root,rel)
        if not p.is_dir():raise ValueError("Expected GPU firmware directory: "+rel)
        files=list(p.rglob("*"))
        if not files:raise ValueError("Unexpectedly empty firmware directory: "+rel)
        n=sum(x.stat().st_size for x in files if x.is_file() and not x.is_symlink())
        shutil.rmtree(p)
        removed.append({"path":rel,"uncompressed_bytes":n,"type":"GPU firmware directory"})
    boot=secure_path(root,"boot")
    for p in sorted(boot.glob("*")):
        name=p.name
        if not (name.startswith("initrd.img-") or name.startswith("vmlinuz-")):
            continue
        if p.is_symlink() or not p.is_file():raise ValueError("Unexpected boot image type "+str(p))
        size=p.stat().st_size
        p.unlink()
        removed.append({"path":"boot/"+name,"uncompressed_bytes":size,"type":"duplicate internal Live boot payload"})
    if not any(x["type"]=="duplicate internal Live boot payload" for x in removed):
        raise ValueError("Did not find duplicate internal kernel/initramfs")
    after={name:hash_bytes(root/name) for name in PRESERVE}
    if after!=before:raise ValueError("Browser, network, TLS or boot diagnostics changed")
    return {
      "schema":"PUPPY50_V102_INTEL_ONLY_GPU_FIRMWARE_EXP",
      "removed_files":removed,
      "removed_uncompressed_bytes":sum(a["uncompressed_bytes"] for a in removed),
      "immutable_browser_network_ca_and_live_startup_sha256":after,
      "all_wireless_firmware_intentionally_preserved":True,
      "intel_i915_firmware_preserved":(root/"usr/lib/firmware/i915").is_dir(),
      "physical_wifi_tested":False,
      "amd_nvidia_gpu_firmware_removed":True,
      "boot_kernel_and_initrd_in_ISO_must_be_verified_separately":True,
      "measured_compressed_iso_savings":False,
      "real_2gib_firefox_browsing_proven":False,
      "security_sandbox_not_modified":True}
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("extracted_live_root",type=Path)
    print(json.dumps(patch(a.parse_args().extracted_live_root),indent=2))
