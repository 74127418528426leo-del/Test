#!/usr/bin/env python3
"""Give staged boot a clear, full-RAM-first fallback on BIOS and UEFI."""
from pathlib import Path
import argparse

BIOS_DEFAULT='''label live-amd64
\tmenu label ^Live system (amd64)
\tmenu default
\tlinux /live/vmlinuz
\tinitrd /live/initrd.img
\tappend boot=live components toram quiet locales=en_US.UTF-8
'''
BIOS_FAIL='''label live-amd64-failsafe
\tmenu label Live system (amd64 fail-safe mode)
\tlinux /live/vmlinuz
\tinitrd /live/initrd.img
\tappend boot=live components memtest noapic noapm nodma nomce nosmp nosplash vga=788
'''
GRUB_DEFAULT='''menuentry "Live system (amd64)" --hotkey=l {
\tlinux\t/live/vmlinuz-6.12.115+deb13.1-amd64 boot=live components toram quiet locales=en_US.UTF-8 findiso=${iso_path}
\tinitrd\t/live/initrd.img-6.12.115+deb13.1-amd64
}'''
GRUB_FAIL='''menuentry "Live system (amd64 fail-safe mode)" {
\tlinux\t/live/vmlinuz-6.12.115+deb13.1-amd64 boot=live components memtest noapic noapm nodma nomce nosmp nosplash vga=788
\tinitrd\t/live/initrd.img-6.12.115+deb13.1-amd64
}'''

def require_once(text,*needles):
    if any(text.count(n)!=1 for n in needles):raise ValueError('Unexpected or ambiguous original boot menu')

def patch_bios(text):
    require_once(text,BIOS_DEFAULT,BIOS_FAIL)
    fast=BIOS_DEFAULT.replace('^Live system (amd64)','^Fast start (wait for RAM READY)').replace('components toram quiet','components quiet')
    fallback=BIOS_DEFAULT.replace('label live-amd64\n','label live-amd64-fullram\n').replace('^Live system (amd64)','Full RAM first (fallback)').replace('\tmenu default\n','')
    recovery=BIOS_FAIL.replace('Live system (amd64 fail-safe mode)','Recovery (full RAM, safe mode)').replace('components memtest','components toram memtest')
    return text.replace(BIOS_DEFAULT,fast,1).replace(BIOS_FAIL,fallback+'\n'+recovery,1)

def patch_grub(text):
    require_once(text,GRUB_DEFAULT,GRUB_FAIL)
    fast=GRUB_DEFAULT.replace('Live system (amd64)','Fast start (wait for RAM READY)').replace('components toram quiet','components quiet')
    fallback=GRUB_DEFAULT.replace('Live system (amd64)','Full RAM first (fallback)').replace(' --hotkey=l','')
    recovery=GRUB_FAIL.replace('Live system (amd64 fail-safe mode)','Recovery (full RAM, safe mode)').replace('components memtest','components toram memtest')
    return text.replace(GRUB_DEFAULT,fast,1).replace(GRUB_FAIL,fallback+'\n'+recovery,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('bios',type=Path);p.add_argument('grub',type=Path);a=p.parse_args()
    if any(x.is_symlink() or not x.is_file() for x in (a.bios,a.grub)):raise ValueError('menus must be regular files')
    b=patch_bios(a.bios.read_text());g=patch_grub(a.grub.read_text())
    a.bios.write_text(b);a.grub.write_text(g)

if __name__=='__main__':main()
