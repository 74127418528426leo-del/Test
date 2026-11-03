#!/usr/bin/env python3
"""Puppy50 Web: size-focused, reversible kernel-module/firmware reduction.

Not proof of compatibility. Only remove selected kernel modules and firmware
payloads not in the explicit common-browser-hardware allowlist. NEVER prune
Firefox's runtime, GTK, SSL, Xorg, fonts, user files or Wi-Fi tools.
"""
import hashlib,json,re,sys
from pathlib import Path

DRIVER_SEEDS={
    # Ram-only loop mounts and bootable optical/USB storage
    'loop','squashfs','overlay','isofs','sr_mod','cdrom','sd_mod','usb_storage','uas',
    'ahci','libahci','ata_piix','libata','ext4','vfat','fat','nls_cp437','nls_iso8859_1',
    'nvme','virtio_blk','virtio_pci','virtio_net',
    # Intel i3-540 GMA/i915 and other basic graphics/console
    'i915','drm','drm_kms_helper','drm_display_helper','ttm','fbdev','simpledrm','bochs','virtio_gpu',
    # Keyboard/mouse, USB, HID and common hubs
    'usbhid','hid','hid_generic','i8042','atkbd','psmouse','evdev','mousedev','serio_raw','xhci_hcd','xhci_pci',
    'ehci_hcd','ehci_pci','uhci_hcd','usbcore','usb_common',
    # Audio, sound devices, basic cameras
    'snd_hda_intel','snd_hda_codec_realtek','snd_hda_codec_hdmi','snd_hda_codec_generic',
    'snd_pcm','snd_usb_audio','snd_seq','uvcvideo','videodev',
    # Common wired and wireless network interfaces
    'e1000e','e1000','igb','r8169','tg3','atl1c','igc',
    'iwlwifi','iwlmvm','iwldvm','ath9k','ath9k_htc','ath10k_pci',
    'rt2800usb','rtl8xxxu','rtl8192cu','rtw88_8822bu','cfg80211','mac80211',
    # Bluetooth, as an optional input device
    'btusb','bluetooth'
}
FIRMWARE_KEEP_PREFIXES=('i915/','iwlwifi-','intel/','rtl_nic/','rtlwifi/','ath9k_htc/','ath10k/','rtw88/','mediatek/','rtl_bt/')
KEEP_LOCALE=('en','es')

def canonical(s):
    return re.sub(r'\.ko(?:\.(?:gz|xz|zst))?$','',Path(s).name)

def run(root):
    root=Path(root).resolve(strict=True)
    trees=[]
    for prefix in ['lib/modules','usr/lib/modules']:
        for p in (root/prefix).glob('*'):
            if (p/'modules.dep').is_file() and p.resolve() not in [x.resolve() for x in trees]: trees.append(p)
    if len(trees)!=1:raise ValueError('Expected one Alpine kernel module tree, got '+repr([str(t) for t in trees]))
    tree=trees[0];lines=(tree/'modules.dep').read_text().splitlines()
    dep={}
    for line in lines:
        if ':' in line:
            k,val=line.split(':',1);dep[k]=val.strip().split()
    byname={canonical(k):k for k in dep}
    selected=set()
    def add(k):
        if k in selected:return
        if k not in dep:raise ValueError('Missing dependency '+k)
        selected.add(k)
        for d in dep[k]:add(d)
    seeded=[]
    for name in sorted(DRIVER_SEEDS):
        if name in byname:
            add(byname[name]);seeded.append(name)
    if 'i915' not in seeded:
        raise ValueError('Expected i915 as a kernel module. Hardware profile not safe to build.')
    removed=[];retained=[]
    for rel in dep:
        f=tree/rel
        if rel in selected:retained.append((str(f.relative_to(root)),f.stat().st_size))
        else:
            removed.append((str(f.relative_to(root)),f.stat().st_size))
            f.unlink()
    firm_dirs=[root/'lib/firmware',root/'usr/lib/firmware']
    firm_dirs=[p for p in firm_dirs if p.is_dir() and p.resolve()==p] or [p for p in firm_dirs if p.is_dir()]
    seen=set();firm_rm=[];firm_keep=[]
    for fd in firm_dirs:
        for f in fd.rglob('*'):
            if not f.is_file():continue
            try:rf=f.resolve(strict=True)
            except FileNotFoundError:continue
            if rf in seen:continue
            seen.add(rf)
            rel=str(f.relative_to(fd))
            if rel.startswith(FIRMWARE_KEEP_PREFIXES):
                firm_keep.append((str(f.relative_to(root)),f.stat().st_size))
            else:
                firm_rm.append((str(f.relative_to(root)),f.stat().st_size))
                f.unlink()
    for basedir in ['usr/share/man','usr/share/doc','usr/share/info']:
        directory=root/basedir
        if directory.is_dir():
            for f in directory.rglob('*'):
                if f.is_file() or f.is_symlink():f.unlink()
    for folder in ['usr/share/locale']:
        p=root/folder
        if p.is_dir():
            for lang in p.iterdir():
                if lang.is_dir() and not lang.name.startswith(KEEP_LOCALE):
                    for f in lang.rglob('*'):
                        if f.is_file() or f.is_symlink():f.unlink()
    return {
      'schema':'PUPPY50_WEB_V45_HARDWARE_FOCUSED_PRUNING',
      'kernel_version':tree.name,'all_module_files':len(dep),
      'selected_driver_seeds_present':seeded,
      'retained_module_files':len(retained),'removed_module_files':len(removed),
      'module_removed_file_bytes':sum(sz for _,sz in removed),
      'firmware_removed_file_bytes':sum(sz for _,sz in firm_rm),
      'firmware_retained_file_bytes':sum(sz for _,sz in firm_keep),
      'firmware_removed_file_count':len(firm_rm),
      'NO_USER_APPLICATION_BINARY_REMOVED':True,
      'all_hardware_compatibility_proven':False,
      'source_WiFi_chipset_not_known':True,
      'warning':'Only support for included hardware classes is intended. No claim of full driver coverage or 384MiB browser functionality.',
      'removed_module_paths_first100':[x for x,_ in removed[:100]],
    }
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: prune_hardware.py ROOT OUT_JSON')
    result=run(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if not k.startswith('removed_module_paths_')},indent=2))
