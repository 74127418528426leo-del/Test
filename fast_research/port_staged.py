#!/usr/bin/env python3
"""Port the known staged live-boot patch only onto byte-matching live-boot scripts."""
from pathlib import Path
import sys
from hardware_guard import guard_text

START='\n\t# Experimental staged boot: these tools and the service live in RAM.\n'
END='\n\tFstab\n\tNetbase\n'
HOME='\t\tp50_home="${rootmnt}/usr/share/puppy50web/index.html"\n'
HOME_END='\n\tfi\n\n\t# P50_V114_OPTIONAL_FONTCACHE'


def port_main(old,new):
    if old.count(START)!=1 or old.count(END)!=1:
        raise ValueError('Unexpected staged main script')
    i=old.index(START);j=old.index(END,i)
    if old[:i]+old[j:]!=new:
        raise ValueError('Updated live-boot main differs from staged base')
    staged=old[i:j]
    if staged.count(HOME)!=1 or staged.count(HOME_END)!=1:
        raise ValueError('Unexpected homepage mutation block')
    a=staged.index(HOME);b=staged.index(HOME_END,a)
    staged=staged[:a]+HOME+'\t\t[ -f "${p50_home}" ] || panic "p50: browser home missing"'+staged[b:]
    return guard_text(new[:i]+staged+new[i:])


def port_misc(old,new):
    first='\np50_backing_device ()\n';after='\nget_backing_device ()\n'
    if old.count(first)!=1 or old.count(after)!=1:
        raise ValueError('Unexpected staged backing-device script')
    a=old.index(first);b=old.index(after,a)
    stripped=old[:a]+old[b:]
    staged_call='p50_backing_device "${1}" "${2}"'
    standard_call='echo $(setup_loop "${1}" \'0\' "${2}")'
    if stripped.count(staged_call)!=1 or stripped.replace(staged_call,standard_call,1)!=new:
        raise ValueError('Updated live-boot helper differs from staged base')
    return old


def main(old_root,new_root):
    old_root=Path(old_root).resolve(strict=True);new_root=Path(new_root).resolve(strict=True)
    if old_root==Path('/') or new_root==Path('/') or old_root==new_root:
        raise ValueError('Only separate extracted initrd trees are permitted')
    rel=Path('usr/lib/live/boot')
    oldmain=old_root/rel/'9990-main.sh';newmain=new_root/rel/'9990-main.sh'
    oldmisc=old_root/rel/'9990-misc-helpers.sh';newmisc=new_root/rel/'9990-misc-helpers.sh'
    for p in (oldmain,newmain,oldmisc,newmisc):
        if p.is_symlink() or not p.is_file():raise ValueError('Unexpected boot script: '+str(p))
    m=port_main(oldmain.read_text(),newmain.read_text())
    h=port_misc(oldmisc.read_text(),newmisc.read_text())
    newmain.write_text(m);newmisc.write_text(h)


if __name__=='__main__':main(*sys.argv[1:3])
