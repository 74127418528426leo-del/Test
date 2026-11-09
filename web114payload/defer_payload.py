#!/usr/bin/env python3
"""Defer selected fast-initramfs files only after verifying their late-root copies."""
import argparse
import hashlib
import json
from pathlib import Path

GROUPS=('netronome','liquidio','bnx2x','cxgb4','qed')
FIRMWARE='usr/lib/firmware'
HWDB='usr/lib/udev/hwdb.bin'

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def defer(main,late,mode,min_firmware=20,require_all_groups=True):
    if mode not in ('netfw','hwdb','combined'):raise ValueError('Unknown experiment')
    main,late=(Path(p).resolve(strict=True) for p in (main,late))
    if any(p==Path('/') or not p.is_dir() for p in (main,late)) or main==late or main in late.parents or late in main.parents:
        raise ValueError('Expected disjoint extracted roots')
    selected=[];groups=[]
    if mode in ('netfw','combined'):
        for name in GROUPS:
            folder=main/FIRMWARE/name
            if not folder.exists():continue
            if folder.is_symlink() or not folder.is_dir() or not folder.resolve().is_relative_to(main):raise ValueError('Unsafe firmware group')
            groups.append(name)
            for p in sorted(folder.rglob('*')):
                if p.is_file() and not p.is_symlink():selected.append((p,'firmware'))
        if len(selected)<min_firmware or (require_all_groups and set(groups)!=set(GROUPS)):
            raise ValueError('Expected firmware files or groups are missing')
    if mode in ('hwdb','combined'):
        p=main/HWDB
        if p.is_symlink() or not p.is_file():raise ValueError('Expected regular early hardware database')
        selected.append((p,'hwdb'))
    removed=[]
    for p,kind in selected:
        if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(main):raise ValueError('Unsafe early file '+str(p))
        rel=p.relative_to(main);target=late/rel
        if not target.is_file() or not target.resolve().is_relative_to(late):raise ValueError('Missing or unsafe late copy '+str(rel))
        h=digest(p)
        if h!=digest(target):raise ValueError('Late copy differs '+str(rel))
        removed.append((p,{'kind':kind,'path':str(rel),'bytes':p.stat().st_size,'sha256':h}))
    # Validate the entire selection before making any deletion.
    for path,_ in removed:path.unlink()
    entries=[x for _,x in removed]
    return {'mode':mode,'firmware_files':sum(x['kind']=='firmware' for x in entries),'hwdb_files':sum(x['kind']=='hwdb' for x in entries),'firmware_groups':groups,'removed_bytes':sum(x['bytes'] for x in entries),'verified_against_late_root':True,'files':entries}

def main():
    p=argparse.ArgumentParser();p.add_argument('main',type=Path);p.add_argument('late',type=Path);p.add_argument('mode',choices=('netfw','hwdb','combined'));p.add_argument('report',type=Path);a=p.parse_args()
    result=defer(a.main,a.late,a.mode);a.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))

if __name__=='__main__':main()
