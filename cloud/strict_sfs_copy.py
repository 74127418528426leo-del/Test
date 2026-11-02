#!/usr/bin/env python3
"""Patch ONLY one known Puppy SFS copy-to-RAM fallback path.

No program layers removed. If the real init script differs, refuse to build.
This is a correctness change: never silently boot from disk in a RAM-only build.
"""
import hashlib,re,sys
from pathlib import Path
if len(sys.argv)!=3:raise SystemExit("usage: python3 strict_sfs_copy.py ORIGINAL_INIT NEW_INIT")
a,b=map(Path,sys.argv[1:])
if not a.is_file() or b.exists() or a.resolve()==b.resolve():
    raise SystemExit("Source missing, in-place mutation or output already exists")
source=a.read_bytes()
rx=re.compile(
 rb'(?m)^[ \t]*if[ \t]+\[[ \t]*\$TFREEK[ \t]+-le[ \t]+\$TNEEDK[ \t]*\][ \t]*;[ \t]*then'
 rb'[ \t]*\r?\n'
 rb'(?:[ \t]*\r?\n)*'
 rb'[ \t]*COPY2RAM="no"[ \t]*#[^\r\n]*stop copying when running out of ram[^\r\n]*\r?\n'
 rb'(?:[ \t]*\r?\n)*'
 rb'[ \t]*return[ \t]+0[ \t]*\r?\n'
 rb'(?:[ \t]*\r?\n)*'
 rb'[ \t]*fi\b'
)
matches=list(rx.finditer(source))
if len(matches)!=1:
    raise SystemExit(f"Refusing unknown RAM-copy fallback pattern, found {len(matches)}")
new=b'''if [ "$TFREEK" -le "$TNEEDK" ];then
 echo "PUPPY50_STRICT_RAM_FAILURE: insufficient tmpfs for $ONE_BASENAME; no source-disk fallback" > /dev/console
 fatal_error "Puppy50 RAM-only: cannot copy all original SFS files into RAM."
 exit 1
fi'''
patched,n=rx.subn(lambda _:new,source)
if n!=1:raise SystemExit("Refusing non-unique replacement")
if b'COPY2RAM="no" # stop copying when running out of ram' in patched:
    raise SystemExit("Old source storage fallback still present")
if b'PUPPY50_STRICT_RAM_FAILURE:' not in patched:raise SystemExit("Strict error marker missing")
b.write_bytes(patched)
b.chmod(a.stat().st_mode & 0o777)
print("PUPPY50_STRICT_RAM_COPY=ENFORCED")
print("ORIGINAL_SHA256",hashlib.sha256(source).hexdigest())
print("PATCHED_SHA256",hashlib.sha256(patched).hexdigest())
