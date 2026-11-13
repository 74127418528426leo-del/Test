#!/usr/bin/env python3
"""V118 research-only: move live user preparation ahead of systemd startup.

This patches ONLY a separately extracted initrd and refuses unknown layouts.
It must not run against the physical system or published v117 release.
"""
import argparse
from pathlib import Path

MARKER = "\n\tFstab\n\tNetbase\n"
HOOK = r'''
    # P50_V118_EARLY_USER: research-only initramfs preparation.
    # Requires stage root and verifies every input before bypassing preflight.
    if [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
        p50_passwd="${rootmnt}/etc/passwd"
        p50_skel="${rootmnt}/etc/skel/.config/openbox/autostart"
        p50_drop="${rootmnt}/etc/systemd/system/lightdm.service.d/10-puppy50-live-preflight.conf"
        [ -f "$p50_passwd" ] && [ -f "$p50_skel" ] && [ -f "$p50_drop" ] || panic "p50-v118: required files absent"
        [ ! -L "$p50_passwd" ] && [ ! -L "$p50_drop" ] || panic "p50-v118: unsafe account path"
        grep -Fqx 'ExecStartPre=/usr/local/sbin/puppy50-prepare-session' "$p50_drop" || panic "p50-v118: unexpected preflight"
        if ! grep -q '^user:' "$p50_passwd"; then
            chroot "${rootmnt}" /usr/sbin/useradd -m -s /bin/bash -c "Puppy50 Live" user || panic "p50-v118: user creation failed"
        fi
        p50_uid="$(awk -F: '$1=="user" {print $3}' "$p50_passwd")"
        p50_gid="$(awk -F: '$1=="user" {print $4}' "$p50_passwd")"
        case "${p50_uid}:${p50_gid}" in *[!0-9:]*|:*|*:|'') panic "p50-v118: invalid account ID";; esac
        mkdir -p "${rootmnt}/home/user/.config/openbox" || panic "p50-v118: home setup failed"
        cp "$p50_skel" "${rootmnt}/home/user/.config/openbox/autostart" || panic "p50-v118: autostart copy failed"
        chown -R "${p50_uid}:${p50_gid}" "${rootmnt}/home/user" || panic "p50-v118: owner update failed"
        chmod 0755 "${rootmnt}/home/user/.config/openbox/autostart" || panic "p50-v118: autostart mode failed"
        cat > "${rootmnt}/etc/lightdm/lightdm.conf" <<'P50_V118_LIGHTDM'
[Seat:*]
autologin-user=user
autologin-user-timeout=0
user-session=openbox
autologin-session=openbox
greeter-hide-users=false
allow-guest=false
P50_V118_LIGHTDM
        cat > "$p50_drop" <<'P50_V118_DONE'
# User was created in verified live overlay by initramfs.
[Service]
ExecStartPre=
P50_V118_DONE
        printf 'P50_V118_EARLY_USER_READY %s\n' "$(cat /proc/uptime)" > /dev/ttyS0
    fi
'''.replace("\n    ", "\n\t")


def patch(root: Path) -> Path:
    root = root.resolve(strict=True)
    if root == Path("/") or not root.is_dir():
        raise ValueError("Only extracted initramfs directories are allowed")
    path = root / "usr/lib/live/boot/9990-main.sh"
    if not path.is_file() or path.is_symlink():
        raise ValueError("Expected a regular live-boot script")
    src = path.read_text()
    if src.count(MARKER) != 1 or "P50_V118_EARLY_USER" in src:
        raise ValueError("Unexpected or previously patched initrd layout")
    path.write_text(src.replace(MARKER, HOOK + MARKER, 1))
    return path


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("extracted_root", type=Path)
    args = p.parse_args()
    print(patch(args.extracted_root))
