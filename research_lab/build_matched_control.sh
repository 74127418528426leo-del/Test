#!/usr/bin/env bash
# Verified same-host structural experiment control builder.
# The preserved source hook was copied AFTER niceness patch, BEFORE any
# prefetch modification. This recreates otherwise-identical ISO prefetch=256.
set -euo pipefail

: "${P50_PREFETCH_MIB:?P50_PREFETCH_MIB required}"
: "${P50_ZSTD_LEVEL:?P50_ZSTD_LEVEL required}"
test "$P50_PREFETCH_MIB" != "256" || { echo "No separate control needed"; exit 0; }

test -f out/matched-control-hook.sh
test -f out/v151.iso
test -f out/v149.iso
test -f out/v149.manifest
test -f out/early-prefix
test -f out/original-full.initrd
test -f out/original.squashfs
test -f input/base.iso
if ! test -f out/original-live/vmlinuz || ! test -f out/original-live/vmlinuz-6.12.115+deb13.1-amd64; then
  mkdir -p out/original-live
  xorriso -osirrox on -indev input/base.iso \
    -extract /live/vmlinuz out/original-live/vmlinuz \
    -extract /live/vmlinuz-6.12.115+deb13.1-amd64 out/original-live/vmlinuz-6.12.115+deb13.1-amd64 \
    >out/reports/original-kernel-extract.log 2>&1
fi
test -f out/original-live/vmlinuz
test -f out/original-live/vmlinuz-6.12.115+deb13.1-amd64
mkdir -p out/candidate-kernel-check
xorriso -osirrox on -indev out/v151.iso \
  -extract /live/vmlinuz out/candidate-kernel-check/vmlinuz \
  -extract /live/vmlinuz-6.12.115+deb13.1-amd64 out/candidate-kernel-check/vmlinuz-6.12.115+deb13.1-amd64 \
  >out/reports/candidate-kernel-check.log 2>&1
cmp out/original-live/vmlinuz out/candidate-kernel-check/vmlinuz
cmp out/original-live/vmlinuz-6.12.115+deb13.1-amd64 out/candidate-kernel-check/vmlinuz-6.12.115+deb13.1-amd64
sudo cp out/matched-control-hook.sh out/main/usr/lib/live/boot/9990-main.sh
sudo sh -n out/main/usr/lib/live/boot/9990-main.sh
grep -Fq 'P50_V133_PREFETCH_256MB_STARTED' out/matched-control-hook.sh
grep -Fq 'count=256' out/matched-control-hook.sh
grep -Fq 'P50_V149_WEBRENDER_USERJS_READY' out/matched-control-hook.sh

(cd out/main && sudo find . -print0 | LC_ALL=C sort -z |
  sudo cpio -o --null -H newc --quiet) >out/matched-control.cpio
zstd -q -"${P50_ZSTD_LEVEL}" -T2 -o out/matched-control.cpio.zst out/matched-control.cpio
cat out/early-prefix out/matched-control.cpio.zst >out/matched-control.initrd
cmp -n 36154880 out/original.initrd out/matched-control.initrd

xorriso -indev out/v149.iso -outdev out/matched-control-stage.iso \
  -map out/matched-control.initrd /live/initrd.img \
  -map out/matched-control.initrd /live/initrd.img-6.12.115+deb13.1-amd64 \
  -boot_image any replay -commit -end >out/reports/matched-control-stage.log 2>&1

python3 - <<'PY'
import hashlib,re
from pathlib import Path
orig=Path("out/v149.manifest").read_text().splitlines()
assert len(orig)==293
d=hashlib.sha256(Path("out/matched-control.initrd").read_bytes()).hexdigest()
allowed={"./live/initrd.img","./live/initrd.img-6.12.115+deb13.1-amd64"}
out=[];seen=set()
for line in orig:
    m=re.fullmatch(r"([0-9a-fA-F]{64})( [ *])(.*)",line)
    assert m,line
    name=m.group(3)
    if name in allowed:seen.add(name)
    out.append((d if name in allowed else m.group(1))+m.group(2)+name)
assert seen==allowed
Path("out/matched-control.manifest").write_text("\n".join(out)+"\n")
PY

xorriso -indev out/matched-control-stage.iso -outdev out/matched-control.iso \
  -map out/matched-control.manifest /sha256sum.txt \
  -boot_image any replay -commit -end >out/reports/matched-control-final.log 2>&1

mkdir -p out/matched-control-check
xorriso -osirrox on -indev out/matched-control.iso \
  -extract /live/initrd.img out/matched-control-check/initrd \
  -extract /live/initrd-full.img out/matched-control-check/recovery \
  -extract /live/filesystem.squashfs out/matched-control-check/root \
  -extract /sha256sum.txt out/matched-control-check/manifest \
  >out/reports/matched-control-recheck.log 2>&1
cmp out/matched-control.initrd out/matched-control-check/initrd
cmp out/original-full.initrd out/matched-control-check/recovery
cmp out/original.squashfs out/matched-control-check/root
cmp out/matched-control.manifest out/matched-control-check/manifest
sha256sum out/matched-control.iso out/v151.iso \
  >out/reports/matched-control-and-candidate-sha256.txt
echo "P50_MATCHED_SAME_HOST_256MB_CONTROL_REBUILT_AND_AUDITED"
