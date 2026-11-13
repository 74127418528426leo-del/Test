#!/usr/bin/env python3
"""Research-only: initialize QEMU DRM before early Xorg, prevent fallback LightDM.

This is intentionally specific to virtual QEMU std VGA/bochs DRM.
It does NOT prove i915/physical hardware and does NOT relax X auth or Firefox sandbox.
Apply after the v123 patch and before packing a disposable initrd.
"""
from pathlib import Path
import argparse

INSERT='''        # P50_V125_DRM_PREREQ: test only. Without the DRM driver, early Xorg
        # fails AddScreen/ScreenInit and the old LightDM creates an illusion of
        # a successful early boot; explicitly disallow that false positive.
        p50_lightdm="$p50_root/etc/systemd/system/lightdm.service"
        [ ! -e "$p50_lightdm" ] && [ ! -L "$p50_lightdm" ] || panic "v125: existing lightdm override"
        ln -s /dev/null "$p50_lightdm" || panic "v125: cannot prevent late LightDM fallback"
        [ -x "$p50_root/usr/sbin/modprobe" ] || panic "v125: missing root modprobe"
        chroot "$p50_root" /usr/sbin/modprobe -q bochs_drm || panic "v125: bochs_drm is unavailable"
        udevadm trigger --subsystem-match=drm >/dev/null 2>&1 || panic "v125: cannot trigger DRM"
        udevadm settle >/dev/null 2>&1 || panic "v125: cannot settle DRM"
        p50_drm_attempt=0
        while [ "$p50_drm_attempt" -lt 30 ] && [ ! -c "$p50_root/dev/dri/card0" ]; do
            sleep .10
            p50_drm_attempt=$((p50_drm_attempt+1))
        done
        [ -c "$p50_root/dev/dri/card0" ] || panic "v125: no ready virtual DRM card0"
        printf 'P50_V125_EARLY_DRM_READY %s\\n' "$(cat /proc/uptime)" >/dev/ttyS0
'''
BEFORE='''        cat > "$p50_start" <<'P50_V123_START_X' '''
BEFORE=BEFORE.rstrip()
def patch(root:Path)->Path:
    root=root.resolve(strict=True)
    if root==Path('/') or not root.is_dir(): raise ValueError('Refuse host filesystem')
    p=root/'usr/lib/live/boot/9990-main.sh'
    if not p.is_file() or p.is_symlink():raise ValueError('Expected extracted initrd script')
    src=p.read_text()
    if 'P50_V123_BEFORE_PID1' not in src or src.count(BEFORE)!=1 or 'P50_V125_DRM_PREREQ' in src:
        raise ValueError('Unrecognized or already patched source')
    p.write_text(src.replace(BEFORE,INSERT+BEFORE,1))
    return p
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('extracted_root',type=Path)
    print(patch(a.parse_args().extracted_root))
