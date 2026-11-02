#!/usr/bin/env python3
"""Puppy50 v22: fail-closed safe default no-copy patch for BookwormPup64 initrd.

No files are overwritten in place. Explicit pfix=copy remains available.
"""
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit("Usage: python3 patch_puppy_init_v22.py SOURCE_INIT NEW_INIT")
source,dest=map(Path,sys.argv[1:])
if not source.is_file() or dest.exists() or source.resolve()==dest.resolve():
    raise SystemExit("Refusing source missing, existing destination, or in-place modification")
original=source.read_bytes()
old=b'''if [ "$PCOPY" = "yes" -o "$PRAMONLY" = "yes" ] ; then
 COPY2RAM="yes"
elif [ "$PNOCOPY" = "yes" ] ; then
 COPY2RAM="no"
fi'''
new=b'''# Puppy50: default to disk-backed SquashFS. Explicit copy still works.
if [ "$PCOPY" = "yes" -a "$PNOCOPY" != "yes" ] ; then
 COPY2RAM="yes"
else
 COPY2RAM="no"
fi'''
if original.count(old)!=1:
    raise SystemExit(f"Refusing patch: expected exactly 1 original conditional, got {original.count(old)}")
patched=original.replace(old,new)
dest.write_bytes(patched)
dest.chmod(source.stat().st_mode & 0o777)
assert patched.count(new)==1
print("SOURCE_SHA256="+hashlib.sha256(original).hexdigest())
print("PATCHED_SHA256="+hashlib.sha256(patched).hexdigest())
print("DEFAULT_NOCOPY=yes")
print("EXPLICIT_PCOPY_RETAINED=yes")
