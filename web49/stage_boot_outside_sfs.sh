#!/bin/sh
# v49: Move redundant boot-tree out of the RAM-resident SquashFS build tree.
# The ISO bootloader already carries a SEPARATE kernel and initrd.
# This script is intended ONLY for a disposable staged Alpine build tree.
set -eu
[ "$#" -eq 2 ] || { echo "usage: stage_boot_outside_sfs.sh STAGED_ROOT EXTERNAL_BOOT_ASSETS" >&2; exit 2; }
ROOT=$(realpath "$1")
OUT=$(realpath -m "$2")
case "$ROOT" in
  /|/boot|/usr|/etc) echo "refuse sensitive root directory" >&2; exit 3 ;;
esac
[ -d "$ROOT/etc/apk" ] || { echo "not an Alpine staged root" >&2; exit 4; }
[ -f "$ROOT/boot/vmlinuz-lts" ] || { echo "missing staged matching kernel" >&2; exit 5; }
[ -d "$ROOT/lib/modules" ] || [ -d "$ROOT/usr/lib/modules" ] || { echo "missing kernel module tree" >&2; exit 6; }
[ ! -e "$OUT" ] || { echo "backup already exists, refusing overwrite" >&2; exit 7; }
mkdir -p "$(dirname "$OUT")"
# Backup/move, not delete: the kernel is required separately for ISO assembly.
mv "$ROOT/boot" "$OUT"
mkdir -p "$ROOT/boot"
test -s "$OUT/vmlinuz-lts"
test -z "$(ls -A "$ROOT/boot")"
echo "PUPPY50_V49_BOOT_TREE_STAGED_OUTSIDE_SFS=PASS"
echo "PUPPY50_V49_BOOT_TREE_APPARENT_BYTES=$(du -sb "$OUT" | cut -f1)"
