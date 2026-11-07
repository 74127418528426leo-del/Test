#!/usr/bin/env python3
"""Bundle an inspected utility's dynamic runtime, including executable loader mode."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess

def parse_ldd(text):
    if 'not found' in text:
        raise ValueError('a dynamic dependency could not be resolved')
    result=[];names=set()
    for line in text.splitlines():
        m=re.search(r'^\s*(\S+)\s+=>\s+(/\S+)',line)
        if m:name,path=m.group(1),m.group(2)
        else:
            m=re.search(r'^\s*(/\S*ld-linux\S+)',line)
            if not m:continue
            path=m.group(1);name=Path(path).name
        if Path(name).name!=name or name in names:
            raise ValueError(f'duplicate or unsafe runtime name: {name}')
        names.add(name);result.append((name,path))
    return result

def copy_runtime_library(source,target):
    source,target=Path(source),Path(target)
    if not source.is_file() or target.is_symlink() or target.exists():
        raise ValueError('source must exist and target must be new')
    shutil.copy2(source,target,follow_symlinks=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('binary',type=Path);p.add_argument('destination',type=Path);a=p.parse_args()
    if not a.destination.is_dir() or a.destination.is_symlink():raise ValueError('destination must be a directory')
    libs=parse_ldd(subprocess.check_output(['ldd',str(a.binary)],text=True))
    names={name for name,_ in libs}
    if 'ld-linux-x86-64.so.2' not in names or not any(name.startswith('libdevmapper') for name in names):
        raise ValueError('required loader or device-mapper library missing')
    for name,path in libs:copy_runtime_library(path,a.destination/name)
    if not os.access(a.destination/'ld-linux-x86-64.so.2',os.X_OK):raise ValueError('bundled loader is not executable')
    print('Bundled isolated runtime libraries:',', '.join(name for name,_ in libs))

if __name__=='__main__':main()
