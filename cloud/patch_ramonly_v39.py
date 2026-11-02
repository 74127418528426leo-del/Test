#!/usr/bin/env python3
"""Puppy50 v39: make original Puppy SFS RAM-resident with fail-closed boot.

4GiB feasibility build, not intended for 384MiB. Original applications remain.
"""
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3:raise SystemExit("usage: patch_ramonly_v39.py SOURCE_INIT OUTPUT_INIT")
src,dst=map(Path,sys.argv[1:])
if not src.is_file() or dst.exists() or src.resolve()==dst.resolve():
    raise SystemExit("Refusing ambiguous/overwriting initrd")
b=src.read_bytes()
old=b'''if [ "$PCOPY" = "yes" -o "$PRAMONLY" = "yes" ] ; then
 COPY2RAM="yes"
elif [ "$PNOCOPY" = "yes" ] ; then
 COPY2RAM="no"
fi'''
new=b'''# Puppy50 v39: request RAM for all original SFS layers.
COPY2RAM="yes"'''
if b.count(old)!=1:raise SystemExit("Copy selection changed upstream: refusing")
b=b.replace(old,new)
anchor=b'export PFSCK # read by /sbin/load_ext_file'
if b.count(anchor)!=1:raise SystemExit("pfix marker changed upstream: refusing")
b=b.replace(anchor,b'''# Puppy50 v39: ignore prior save files; clean RAM-only session.
PRAMONLY="yes"
PCOPY="yes"
PNOCOPY=""
'''+anchor)
anchor2=b' [ $RAMSIZE -le 1048576 ] && return 0'
if b.count(anchor2)!=1:raise SystemExit("Low RAM guard changed upstream")
b=b.replace(anchor2,b''' if [ "$RAMSIZE" -le 1048576 ]; then
  echo "PUPPY50_RAMONLY_REJECTED_INSUFFICIENT_RAM" > /dev/console
  fatal_error "RAM-only build needs more than 1 GiB for all files."
 fi''')
anchor3=b'''   COPY2RAM="no" # stop copying when running out of ram
   return 0'''
if b.count(anchor3)!=1:raise SystemExit("tmpfs guard changed upstream")
b=b.replace(anchor3,b'''   echo "PUPPY50_RAMONLY_REJECTED_NOT_ENOUGH_TMPFS" > /dev/console
   fatal_error "RAM-only build: cannot copy an original SFS; no disk fallback."''')
anchor4=b'exec switch_root /pup_new /sbin/init'
if b.count(anchor4)!=1:raise SystemExit("switch_root marker missing")
probe=b'''# Puppy50 v39: log actual RAM-resident SFS and loop backing paths.
if [ -w /dev/ttyS0 ]; then
 {
  echo "PUPPY50_V39_RAM_PROOF_BEGIN"
  echo "PUPPY50_RAMONLY_PUPMODE_RAM=$PRAMONLY"
  echo "PUPPY50_RAMONLY_COPY_SELECTION=$COPY2RAM"
  n=0; k=0
  for f in /mnt/tmpfs/*.sfs; do
   [ -s "$f" ] || continue
   n=$((n+1))
   sz=$(stat -c '%s' "$f")
   k=$((k+sz))
   printf 'PUPPY50_COPIED_SFS name=%s bytes=%s\\n' "$(basename "$f")" "$sz"
  done
  printf 'PUPPY50_TOTAL_SFS count=%s bytes=%s\\n' "$n" "$k"
  echo "PUPPY50_SFS_LOOPS"
  losetup -a
  echo "PUPPY50_V39_RAM_PROOF_END"
 } > /dev/ttyS0 2>&1
fi
'''
b=b.replace(anchor4,probe+anchor4)
dst.write_bytes(b);dst.chmod(src.stat().st_mode & 0o777)
print("SOURCE_SHA256",hashlib.sha256(src.read_bytes()).hexdigest())
print("OUTPUT_SHA256",hashlib.sha256(b).hexdigest())
print("RAM_COPY_FORCED=YES")
print("LOW_RAM_AND_TMPFS_FALLBACK=REFUSED")
