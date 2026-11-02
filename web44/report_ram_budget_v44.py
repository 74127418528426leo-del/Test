#!/usr/bin/env python3
"""Actual immutable OS bytes vs 384 MiB. Does NOT certify browser runtime."""
import argparse,json,os
from pathlib import Path

def summarize(base):
    base=Path(base)
    root=base/'rootfs'
    sfs=base/'puppy50-web-v44-root.sfs'
    if not sfs.is_file() or not (base/'reports/installed-packages.txt').exists():
        raise ValueError('No completed source image/package closure')
    installed=[x for x in (base/'reports/installed-packages.txt').read_text().splitlines() if x.strip()]
    installed_root_bytes=sum(f.stat().st_size for f in root.rglob('*') if f.is_file() and not f.is_symlink())
    sz=sfs.stat().st_size
    cap=384*1048576
    return {'schema':'PUPPY50_WEB_V44_REAL_XZ_ROOT_SIZE',
        'kernel_image_and_driver_modules_included_in_root':True,
        'installed_package_count':len(installed),
        'root_regular_file_payload_bytes':installed_root_bytes,
        'compressed_root_bytes':sz,
        'compressed_root_mib':round(sz/1048576,3),
        'total_ram_target_mib':384,
        'compressed_files_alone_fit_in_384mib':sz<cap,
        'theoretical_remaining_mib_after_only_copy':round((cap-sz)/1048576,3),
        'kernel_graphics_browser_xorg_and_network_runtime_memory_measured_mib':None,
        'actual_full_ram_boot_and_webpage_render_proven':False,
        'browser_after_boot_media_ejection_verified':False,
        'hardware_mouse_keyboard_webgl_wifi_audio_verified':False,
        'physical_ram_384mib_verified':False,
        'risk':'Copying an entire compressed SFS into RAM requires compressed bytes PLUS all Linux/kernel/browser runtime allocations; this file size alone is not a boot memory measurement.'}
def main():
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    d=summarize(a.source);a.out.write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps(d,indent=2))
if __name__=='__main__':main()
