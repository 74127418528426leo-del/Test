#!/usr/bin/env python3
"""Minimal Alpine matching-kernel initrd module dependency closure.
Only modules needed to locate optical media and mount loop/SquashFS/OverlayFS.
No external media or disk swap needed after SFS is copied to RAM.
"""
import json,re,shutil,sys
from pathlib import Path

def prepare(root,dst):
    root=Path(root);dst=Path(dst)
    modroots=list(root.glob('lib/modules/*'))+list(root.glob('usr/lib/modules/*'))
    modroots=list({p.resolve():p for p in modroots if (p/'modules.dep').is_file()}.values())
    if len(modroots)!=1:
        raise ValueError('Expected exactly one installed Alpine kernel module tree: '+str(modroots))
    source=modroots[0];version=source.name
    records={}
    for line in (source/'modules.dep').read_text().splitlines():
        if ':' not in line:continue
        key,rest=line.split(':',1);records[key]=rest.strip().split()
    def stem(s):
        name=s.split('/')[-1]
        return re.sub(r'\.ko(?:\.(?:zst|xz|gz))?$','',name)
    wanted={'loop','squashfs','overlay','isofs','sr_mod','cdrom','scsi_mod',
           'ata_piix','libata','sd_mod','virtio_blk','virtio_pci',
           'usb_storage','uas','xhci_hcd','ehci_hcd','uhci_hcd'}
    found={stem(k):k for k in records}
    todo=[found[n] for n in wanted if n in found]
    if not all(k in found or k in (source/'modules.builtin').read_text(errors='replace') for k in ('loop','squashfs','overlay')):
        raise ValueError('Unable to locate essential loop/squashfs/overlay drivers')
    copied=set()
    def add(key):
        if key in copied:return
        if key not in records:raise ValueError('Missing module dependency '+key)
        copied.add(key)
        for dep in records[key]:add(dep)
    for module in todo:add(module)
    target=dst/'lib/modules'/version
    target.mkdir(parents=True,exist_ok=True)
    for key in copied:
        f=source/key
        to=target/key
        to.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(f,to)
    for data in source.glob('modules.*'):
        if data.is_file():shutil.copy2(data,target/data.name)
    return {'kernel_release':version,'modules_copied':len(copied),
            'module_payload_bytes':sum((source/key).stat().st_size for key in copied),
            'selected_module_names':sorted(stem(x) for x in copied)}

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('Usage: minimal_initrd_modules.py ROOT OUTPUT_DIR REPORT_JSON')
    report=prepare(*sys.argv[1:3])
    Path(sys.argv[3]).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
