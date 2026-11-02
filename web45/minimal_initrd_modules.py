#!/usr/bin/env python3
"""Minimal Alpine matching-kernel initrd module dependency closure.
Only modules needed to locate optical media and mount loop/SquashFS/OverlayFS.
No external media or disk swap needed after SFS is copied to RAM.
"""
import json,re,shutil,sys,gzip
from pathlib import Path

def prepare(root,dst):
    root=Path(root);dst=Path(dst)
    modroots=list(root.glob('lib/modules/*'))+list(root.glob('usr/lib/modules/*'))
    modroots=list({p.resolve():p for p in modroots if (p/'modules.dep').is_file()}.values())
    if len(modroots)!=1:
        raise ValueError('Expected exactly one installed Alpine kernel module tree: '+str(modroots))
    source=modroots[0];version=source.name
    # The hardware-focused root already retains a dependency-closed set of
    # just 103 modules. Copy them all rather than relying on host depmod's
    # sometimes incompatible re-generated compressed-module metadata.
    def stem(s):
        name=Path(s).name
        return re.sub(r'\.ko(?:\.(?:zst|xz|gz))?$','',name)
    actual={str(p.relative_to(source)):p for p in source.rglob('*')
            if p.is_file() and re.search(r'\.ko(?:\.(?:zst|xz|gz))?$',p.name)}
    available={stem(k) for k in actual}
    builtins=(source/'modules.builtin').read_text(errors='replace') if (source/'modules.builtin').is_file() else ''
    missing=[k for k in ('loop','squashfs','overlay','isofs','sr_mod')
             if k not in available and k not in builtins]
    if missing:raise ValueError('Critical filesystem/optical kernel modules missing: '+repr(missing))
    copied=set(actual)
    target=dst/'lib/modules'/version
    target.mkdir(parents=True,exist_ok=True)
    for key in copied:
        f=actual[key]
        to=target/key
        # Alpine ships .ko.gz modules. Ubuntu BusyBox in the early initrd
        # does not find compressed module names in modules.dep in our
        # actual KVM log. Convert to .ko, then regenerate dependency indexes.
        if to.name.endswith('.ko.gz'):
            to=to.with_suffix('')
            to.parent.mkdir(parents=True,exist_ok=True)
            with gzip.open(f,'rb') as inp, to.open('wb') as out:
                shutil.copyfileobj(inp,out)
        else:
            to.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(f,to)
    for data in source.glob('modules.*'):
        if data.is_file():shutil.copy2(data,target/data.name)
    return {'kernel_release':version,'modules_copied':len(copied),
            'module_payload_bytes':sum(actual[key].stat().st_size for key in copied),
            'selected_module_names':sorted(stem(x) for x in copied),
            'early_initrd_modules_decompressed_for_busybox':True}

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('Usage: minimal_initrd_modules.py ROOT OUTPUT_DIR REPORT_JSON')
    report=prepare(*sys.argv[1:3])
    Path(sys.argv[3]).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
