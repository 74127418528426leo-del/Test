#!/usr/bin/env python3
"""Prepare a disposable initramfs module tree for compression experiments."""
import argparse
import hashlib
import json
import lzma
import os
import stat
import tempfile
from pathlib import Path


def unpack_modules(root):
    given=Path(root)
    if given.is_symlink():raise ValueError('Root must not be a symlink')
    root=given.resolve(strict=True)
    if root==Path('/') or not root.is_dir():raise ValueError('Expected isolated extracted directory')
    sources=sorted(root.rglob('*.ko.xz'))
    if not sources:raise ValueError('No compressed modules found')
    for p in sources:
        if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root) or p.stat().st_nlink!=1:
            raise ValueError('Unsafe or linked source: '+str(p))
        target=p.with_suffix('')
        if target.exists() or target.is_symlink():raise ValueError('Output already exists: '+str(target))
    staged=[];entries=[]
    try:
        for p in sources:
            try:data=lzma.decompress(p.read_bytes())
            except (lzma.LZMAError,EOFError,OSError) as exc:raise ValueError('Invalid XZ module: '+str(p)) from exc
            if not data.startswith(b'\x7fELF'):raise ValueError('Uncompressed module is not ELF: '+str(p))
            fd,tmpname=tempfile.mkstemp(prefix='.p50-module-',dir=p.parent)
            tmp=Path(tmpname);staged.append((p,tmp))
            with os.fdopen(fd,'wb') as f:f.write(data)
            st=p.stat();os.chown(tmp,st.st_uid,st.st_gid);os.chmod(tmp,stat.S_IMODE(st.st_mode));os.utime(tmp,ns=(st.st_atime_ns,st.st_mtime_ns))
            entries.append({'source':str(p.relative_to(root)),'target':str(p.with_suffix('').relative_to(root)),'compressed_bytes':st.st_size,'raw_bytes':len(data),'raw_sha256':hashlib.sha256(data).hexdigest()})
        for p,tmp in staged:os.replace(tmp,p.with_suffix(''));p.unlink()
    finally:
        for _,tmp in staged:tmp.unlink(missing_ok=True)
    return {'files':len(entries),'compressed_bytes':sum(e['compressed_bytes'] for e in entries),'raw_bytes':sum(e['raw_bytes'] for e in entries),'modules':entries}


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
    report=unpack_modules(a.root);a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='modules'},indent=2))

if __name__=='__main__':main()
