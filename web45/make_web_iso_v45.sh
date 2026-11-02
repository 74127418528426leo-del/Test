#!/bin/bash
# Puppy50 Web v45: build a *real* RAM-copy browser ISO using matching Alpine kernel.
# Not a production build. Fail on missing kernel, layers or initrd module closure.
set -euo pipefail
[ "$#" -eq 4 ] || { echo "usage: make_web_iso_v45.sh ALPINE_ROOT ORIGINAL_PUPPY_ISO OUT_ISO REPORT_DIR" >&2;exit 2; }
ROOT=$(realpath "$1")
SOURCE=$(realpath "$2")
OUT=$3
REPORT=$4
mkdir -p "$REPORT"
test -f "$SOURCE"
test -s "$ROOT/boot/vmlinuz-lts"
test -s "$ROOT/usr/share/puppy50web/index.html"
test -s "$ROOT/usr/local/bin/puppy50-web-launch"
SCRATCH=$(mktemp -d)
trap 'rm -rf "$SCRATCH"' EXIT
mkdir -p "$SCRATCH/initrd/bin" "$SCRATCH/initrd/dev" "$SCRATCH/initrd/proc" "$SCRATCH/initrd/sys"
cp /bin/busybox "$SCRATCH/initrd/busybox"
cp /bin/busybox "$SCRATCH/initrd/bin/busybox"
cp web45/init_ram_only.sh "$SCRATCH/initrd/init"
chmod +x "$SCRATCH/initrd/init"
python3 web45/minimal_initrd_modules.py "$ROOT" "$SCRATCH/initrd" "$REPORT/initrd_module_closure.json"
VERSION=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["kernel_release"])' "$REPORT/initrd_module_closure.json")
depmod -b "$SCRATCH/initrd" "$VERSION"
python3 web45/direct_insmod_loader.py "$SCRATCH/initrd/lib/modules/$VERSION" "$SCRATCH/initrd/load_early_modules.sh"
test -x "$SCRATCH/initrd/load_early_modules.sh"
# A previous real KVM boot showed every module lookup failing in BusyBox.
# Require an explicit uncompressed .ko entry for each essential early driver.
for module in sr_mod scsi_mod cdrom ata_piix isofs squashfs loop overlay; do
  if ! grep -Eq "/${module}\\.ko:" "$SCRATCH/initrd/lib/modules/$VERSION/modules.dep"; then
    echo "PUPPY50_WEB_V46_FAIL_INITRD_MODDEP module=$module" >&2
    exit 4
  fi
done
echo 'PUPPY50_WEB_V46_VALIDATED_INITRD_MODULE_DEPENDENCIES'
(
  cd "$SCRATCH/initrd"
  find . -print0 | cpio --null -o -H newc 2>/dev/null | gzip -n -6
) > "$SCRATCH/initrd.gz"
test -s "$SCRATCH/initrd.gz"
echo "PUPPY50_WEB_V45_INITRD_BYTES=$(stat -c %s "$SCRATCH/initrd.gz")" | tee "$REPORT/boot_image_sizes.txt"
# The target image does not retain a single original Puppy program or SFS
# except bootloader assets; the Alpine browser root is the single RAM-copied SFS.
xorriso -indev "$SOURCE" -outdev "$OUT" \
  -rm /adrv_dpupbw64_10.0.12.sfs \
      /bdrv_dpupbw64_10.0.12.sfs \
      /fdrv_dpupbw64_10.0.12.sfs \
      /kbuild-6.1.148.sfs \
      /zdrv_dpupbw64_10.0.12.sfs -- \
  -map "$ROOT/boot/vmlinuz-lts" /vmlinuz \
  -map "$SCRATCH/initrd.gz" /initrd.gz \
  -map "$ROOT/../puppy50-web-v45-root.sfs" /puppy_dpupbw64_10.0.12.sfs \
  -boot_image any replay -commit -end \
  > "$REPORT/xorriso.log" 2>&1
test -s "$OUT"
mkdir -p "$SCRATCH/verify"
7z e -y -o"$SCRATCH/verify" "$OUT" vmlinuz initrd.gz puppy_dpupbw64_10.0.12.sfs >/dev/null
cmp "$ROOT/boot/vmlinuz-lts" "$SCRATCH/verify/vmlinuz"
cmp "$SCRATCH/initrd.gz" "$SCRATCH/verify/initrd.gz"
cmp "$ROOT/../puppy50-web-v45-root.sfs" "$SCRATCH/verify/puppy_dpupbw64_10.0.12.sfs"
sha256sum "$OUT" > "$REPORT/experimental_iso.sha256"
stat -c 'PUPPY50_WEB_V45_ISO_BYTES=%s' "$OUT" | tee -a "$REPORT/boot_image_sizes.txt"
echo 'PUPPY50_WEB_V45_BOOTABLE_IMAGE_ASSEMBLED_BYTES_VERIFIED'
