#!/usr/bin/env python3
"""Fail-closed, one-condition Puppy Linux init precedence fix. DO NOT overwrite originals."""
import hashlib, pathlib, sys
if len(sys.argv)!=3:
    raise SystemExit("Usage: patch_init_priority_v18.py ORIGINAL_INIT PATCHED_INIT")
src=pathlib.Path(sys.argv[1]);dest=pathlib.Path(sys.argv[2])
if not src.is_file() or dest.exists() or src.resolve()==dest.resolve():
    raise SystemExit("Missing source, existing destination, or in-place overwrite refused")
raw=src.read_bytes()
old=b'''if [ "$PCOPY" = "yes" -o "$PRAMONLY" = "yes" ] ; then
 COPY2RAM="yes"
elif [ "$PNOCOPY" = "yes" ] ; then
 COPY2RAM="no"
fi'''
new=b'''if [ "$PNOCOPY" = "yes" ] ; then
 COPY2RAM="no"
elif [ "$PCOPY" = "yes" -o "$PRAMONLY" = "yes" ] ; then
 COPY2RAM="yes"
fi'''
n=raw.count(old)
if n!=1: raise SystemExit(f"Refusing patch: expected exactly one matching original conditional, got {n}")
patched=raw.replace(old,new)
dest.write_bytes(patched);dest.chmod(src.stat().st_mode&0o777)
print("Source init SHA256",hashlib.sha256(raw).hexdigest())
print("Patched init SHA256",hashlib.sha256(patched).hexdigest())
print("Original length",len(raw),"patched length",len(patched))
