#!/usr/bin/env bash
# Build a test candidate from the checksum-pinned v115 root and current signed
# Debian packages. Run only inside a disposable CI VM, not the user's computer.
set -euo pipefail
BASE=${1:?expected v115 ISO path}
WORK=${2:?expected disposable work directory}
PREVIEW=${3:?expected path to public_preview scripts}
BASE=$(realpath "$BASE")
PREVIEW=$(realpath "$PREVIEW")
mkdir -p "$WORK"
WORK=$(realpath "$WORK")
ROOT="$WORK/root"
printf '%s  %s\n' 'd697081adf836b7c8b75fe352964764e082b0214a262c8d9895eb9388c3e825a' "$BASE" | sha256sum -c -
mkdir -p "$WORK/original" "$WORK/config" "$WORK/reports"
xorriso -osirrox on -indev "$BASE" \
  -extract /live/filesystem.squashfs "$WORK/original/filesystem.squashfs" \
  -extract /isolinux/isolinux.cfg "$WORK/original/isolinux.cfg" \
  -extract /isolinux/menu.cfg "$WORK/original/menu.cfg" \
  -extract /boot/grub/config.cfg "$WORK/original/config.cfg" \
  -extract /sha256sum.txt "$WORK/original/sha256sum.txt" >"$WORK/reports/extract.log" 2>&1
! grep -q '^menu shiftkey' "$WORK/original/menu.cfg"
sudo unsquashfs -no-progress -d "$ROOT" "$WORK/original/filesystem.squashfs" >"$WORK/reports/unsquash.log"
sudo python3 "$PREVIEW/update_home.py" "$ROOT/usr/share/puppy50web/index.html"
sudo cp -a "$ROOT/etc/resolv.conf" "$WORK/resolv.saved"
sudo rm -f "$ROOT/etc/resolv.conf"
sudo cp -L /etc/resolv.conf "$ROOT/etc/resolv.conf"
if sudo test -e "$ROOT/usr/sbin/policy-rc.d"; then
  sudo cp -a "$ROOT/usr/sbin/policy-rc.d" "$WORK/policy.saved"
fi
printf '#!/bin/sh\nexit 101\n' | sudo tee "$ROOT/usr/sbin/policy-rc.d" >/dev/null
sudo chmod 0755 "$ROOT/usr/sbin/policy-rc.d"
mounted_dev=0; mounted_proc=0; mounted_sys=0
cleanup() {
  if (( mounted_sys )); then sudo umount -l "$ROOT/sys" || true; fi
  if (( mounted_proc )); then sudo umount -l "$ROOT/proc" || true; fi
  if (( mounted_dev )); then sudo umount -l "$ROOT/dev" || true; fi
}
trap cleanup EXIT
sudo mount --bind /dev "$ROOT/dev"; mounted_dev=1
sudo mount -t proc proc "$ROOT/proc"; mounted_proc=1
sudo mount --bind /sys "$ROOT/sys"; mounted_sys=1
CHROOT=(sudo chroot "$ROOT" /usr/bin/env -i PATH=/usr/sbin:/usr/bin:/sbin:/bin HOME=/root LANG=C.UTF-8 DEBIAN_FRONTEND=noninteractive)
"${CHROOT[@]}" apt-get update >"$WORK/reports/apt-update.log" 2>&1
"${CHROOT[@]}" apt-get -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold --with-new-pkgs upgrade >"$WORK/reports/apt-upgrade.log" 2>&1
"${CHROOT[@]}" apt-get -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold install firefox-esr linux-image-amd64 python3-xdg fonts-noto-cjk >"$WORK/reports/apt-install.log" 2>&1
"${CHROOT[@]}" dpkg --audit >"$WORK/reports/dpkg-audit.txt"
test ! -s "$WORK/reports/dpkg-audit.txt"
"${CHROOT[@]}" apt-get check >"$WORK/reports/apt-check.log" 2>&1
firefox_ver=$("${CHROOT[@]}" dpkg-query -W -f='${Version}' firefox-esr)
kernel_ver=$("${CHROOT[@]}" dpkg-query -W -f='${Version}' linux-image-amd64)
dpkg --compare-versions "$firefox_ver" ge '153.7.0esr-1~deb13u1'
dpkg --compare-versions "$kernel_ver" ge '6.12.117-0'
printf 'firefox-esr=%s\nlinux-image-amd64=%s\n' "$firefox_ver" "$kernel_ver" >"$WORK/reports/security-versions.txt"
kernel_file=$(find "$ROOT/boot" -maxdepth 1 -type f -name 'vmlinuz-*' -printf '%f\n' | sort -V | tail -n1)
test -n "$kernel_file"
kver=${kernel_file#vmlinuz-}
"${CHROOT[@]}" update-initramfs -u -k "$kver" >"$WORK/reports/update-initramfs.log" 2>&1
test -s "$ROOT/boot/initrd.img-$kver"
"${CHROOT[@]}" lsinitramfs "/boot/initrd.img-$kver" >"$WORK/reports/initramfs-contents.txt"
grep -q 'scripts/live' "$WORK/reports/initramfs-contents.txt"
"${CHROOT[@]}" dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n' >"$WORK/filesystem.packages"
sudo cp "$ROOT/var/lib/dpkg/status" "$WORK/reports/dpkg-status"
sudo cp "$ROOT/boot/$kernel_file" "$WORK/vmlinuz"
sudo cp "$ROOT/boot/initrd.img-$kver" "$WORK/initrd.img"
printf '%s\n' "$kver" >"$WORK/reports/kernel-release.txt"
"${CHROOT[@]}" apt-get clean
cleanup
mounted_dev=0; mounted_proc=0; mounted_sys=0
trap - EXIT
sudo rm -f "$ROOT/etc/resolv.conf"
sudo cp -a "$WORK/resolv.saved" "$ROOT/etc/resolv.conf"
sudo rm -f "$ROOT/usr/sbin/policy-rc.d"
if test -e "$WORK/policy.saved"; then sudo cp -a "$WORK/policy.saved" "$ROOT/usr/sbin/policy-rc.d"; fi
sudo rm -rf "$ROOT/var/lib/apt/lists/"*
sudo mksquashfs "$ROOT" "$WORK/filesystem.squashfs" -noappend -comp zstd -b 262144 -processors 2 -no-progress >"$WORK/reports/mksquashfs.log"
sudo chown "$(id -u):$(id -g)" "$WORK/filesystem.squashfs" "$WORK/vmlinuz" "$WORK/initrd.img" "$WORK/reports/dpkg-status"
python3 "$PREVIEW/boot_configs.py" "$WORK/original/isolinux.cfg" "$WORK/original/config.cfg" "$WORK/config"
python3 - "$WORK" <<'PY'
import hashlib,re,sys
from pathlib import Path
w=Path(sys.argv[1])
replace={
 './live/filesystem.squashfs':w/'filesystem.squashfs',
 './live/filesystem.packages':w/'filesystem.packages',
 './live/vmlinuz':w/'vmlinuz',
 './live/initrd.img':w/'initrd.img',
 './isolinux/isolinux.cfg':w/'config/isolinux.cfg',
 './isolinux/live.cfg':w/'config/live.cfg',
 './boot/grub/config.cfg':w/'config/config.cfg',
 './boot/grub/grub.cfg':w/'config/grub.cfg',
}
result=[];seen=set()
for line in (w/'original/sha256sum.txt').read_text().splitlines():
    m=re.fullmatch(r'([0-9a-fA-F]{64})( [ *])(.*)',line)
    if not m: raise ValueError('Unexpected manifest entry: '+line)
    path=m.group(3)
    if path in seen: raise ValueError('Duplicate entry: '+path)
    seen.add(path)
    if path in replace:
        with replace[path].open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    else: digest=m.group(1)
    result.append(digest+m.group(2)+path)
if not set(replace).issubset(seen): raise ValueError('Missing: '+str(set(replace)-seen))
(w/'sha256sum.txt').write_text('\n'.join(result)+'\n')
print('manifest entries',len(result),'changed',len(replace))
PY
xorriso -indev "$BASE" -outdev "$WORK/candidate.iso" \
  -map "$WORK/filesystem.squashfs" /live/filesystem.squashfs \
  -map "$WORK/filesystem.packages" /live/filesystem.packages \
  -map "$WORK/vmlinuz" /live/vmlinuz \
  -map "$WORK/initrd.img" /live/initrd.img \
  -map "$WORK/config/isolinux.cfg" /isolinux/isolinux.cfg \
  -map "$WORK/config/live.cfg" /isolinux/live.cfg \
  -map "$WORK/config/config.cfg" /boot/grub/config.cfg \
  -map "$WORK/config/grub.cfg" /boot/grub/grub.cfg \
  -map "$WORK/sha256sum.txt" /sha256sum.txt \
  -boot_image any replay -commit -end >"$WORK/reports/xorriso.log" 2>&1
mkdir -p "$WORK/verify"
xorriso -osirrox on -indev "$WORK/candidate.iso" -extract / "$WORK/verify" >"$WORK/reports/verify-extract.log" 2>&1
(cd "$WORK/verify" && sha256sum -c --quiet sha256sum.txt) >"$WORK/reports/manifest-check.txt" 2>&1
sha256sum "$WORK/candidate.iso" >"$WORK/reports/candidate-sha256.txt"
echo 'CANDIDATE_BUILT_AND_INTERNAL_MANIFEST_VERIFIED'
