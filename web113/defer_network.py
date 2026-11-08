#!/usr/bin/env python3
"""Test-only network driver deferral; preserve and verify every late-root copy."""
import argparse
import hashlib
import json
from pathlib import Path

DRIVERS='usr/lib/modules/6.12.115+deb13.1-amd64/kernel/drivers/net'
FIRMWARE_BASE='usr/lib/firmware'
FIRMWARE_GROUPS=('netronome','liquidio','bnx2x','cxgb4','qed')


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def defer(early,main,late,mode,min_drivers=100,min_firmware=20):
    if mode not in ('drivers','drivers-firmware'):raise ValueError('Unknown experiment')
    early,main,late=(Path(p).resolve(strict=True) for p in (early,main,late))
    roots=(early,main,late)
    if any(p==Path('/') or not p.is_dir() for p in roots):raise ValueError('Expected isolated extracted directories')
    if any(a==b or a in b.parents or b in a.parents for i,a in enumerate(roots) for b in roots[i+1:]):
        raise ValueError('Extracted roots must be disjoint')
    drivers_dir=early/DRIVERS
    if not drivers_dir.is_dir() or drivers_dir.is_symlink():raise ValueError('Expected early network driver directory')
    drivers=sorted(drivers_dir.rglob('*.ko.xz'))
    if len(drivers)<min_drivers:raise ValueError('Unexpectedly few early network drivers')
    firmware=[];groups=[]
    if mode=='drivers-firmware':
        for name in FIRMWARE_GROUPS:
            folder=main/FIRMWARE_BASE/name
            if not folder.exists():continue
            if folder.is_symlink() or not folder.is_dir():raise ValueError('Unexpected firmware directory')
            groups.append(name)
            firmware.extend(p for p in folder.rglob('*') if p.is_file() or p.is_symlink())
        firmware.sort()
        if len(firmware)<min_firmware or (min_firmware>=20 and set(groups)!=set(FIRMWARE_GROUPS)):
            raise ValueError('Expected firmware groups/files are missing')
    removals=[]
    for base,paths,kind in ((early,drivers,'driver'),(main,firmware,'firmware')):
        for p in paths:
            if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(base):
                raise ValueError('Unexpected early file '+str(p))
            rel=p.relative_to(base);target=late/rel
            if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(late):
                raise ValueError('Missing or unsafe late copy '+str(rel))
            src_hash=digest(p)
            if src_hash!=digest(target):raise ValueError('Late copy differs '+str(rel))
            removals.append((p,{'kind':kind,'path':str(rel),'bytes':p.stat().st_size,'sha256':src_hash}))
    # The entire candidate set is validated before any deletion occurs.
    for p,_ in removals:p.unlink()
    entries=[item for _,item in removals]
    return {'mode':mode,'drivers':len(drivers),'firmware_files':len(firmware),'firmware_groups':groups,
            'removed_bytes':sum(item['bytes'] for item in entries),'verified_against_late_root':True,'files':entries}


def main():
    p=argparse.ArgumentParser();p.add_argument('early',type=Path);p.add_argument('main',type=Path);p.add_argument('late',type=Path)
    p.add_argument('mode',choices=('drivers','drivers-firmware'));p.add_argument('report',type=Path);a=p.parse_args()
    report=defer(a.early,a.main,a.late,a.mode)
    a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))

if __name__=='__main__':main()
