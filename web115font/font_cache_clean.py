#!/usr/bin/env python3
"""Seed optional fontconfig caches atomically per file without risking boot."""
import argparse
from pathlib import Path

MARKER='\n\tFstab\n\tNetbase\n'
HOOK=r'''
\t# P50_V114_OPTIONAL_FONTCACHE: complete cache files or normal font discovery.
\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then
\t\tp50_fc_source=/usr/lib/p50-fontcache
\t\tp50_fc_dest="${rootmnt}/var/cache/fontconfig"
\t\tif [ -d "${p50_fc_source}" ] && [ ! -L "${p50_fc_source}" ] && [ -d "${rootmnt}/var" ] && [ ! -L "${rootmnt}/var" ] && [ -d "${rootmnt}/var/cache" ] && [ ! -L "${rootmnt}/var/cache" ] && [ -d "${p50_fc_dest}" ] && [ ! -L "${p50_fc_dest}" ]; then
\t\t\tp50_fc_valid=1
\t\t\tp50_fc_count=0
\t\t\tfor p50_fc_item in "${p50_fc_source}"/*.cache-9; do
\t\t\t\tif [ ! -f "${p50_fc_item}" ] || [ -L "${p50_fc_item}" ]; then p50_fc_valid=0; break; fi
\t\t\t\tp50_fc_count=$((p50_fc_count + 1))
\t\t\tdone
\t\t\tp50_fc_stage="${p50_fc_dest}/.p50-fontcache-$$"
\t\t\tif [ "${p50_fc_valid}" = 1 ] && [ "${p50_fc_count}" -gt 0 ] && [ ! -e "${p50_fc_stage}" ] && [ ! -L "${p50_fc_stage}" ] && (umask 077; mkdir "${p50_fc_stage}"); then
\t\t\t\tfor p50_fc_item in "${p50_fc_source}"/*.cache-9; do
\t\t\t\t\tp50_fc_name="${p50_fc_item##*/}"
\t\t\t\t\tif ! cp -p "${p50_fc_item}" "${p50_fc_stage}/${p50_fc_name}"; then p50_fc_valid=0; break; fi
\t\t\t\tdone
\t\t\t\tif [ "${p50_fc_valid}" = 1 ]; then
\t\t\t\t\tfor p50_fc_item in "${p50_fc_stage}"/*.cache-9; do
\t\t\t\t\t\tp50_fc_name="${p50_fc_item##*/}"
\t\t\t\t\t\tif [ -f "${p50_fc_item}" ] && [ ! -L "${p50_fc_item}" ] && [ ! -e "${p50_fc_dest}/${p50_fc_name}" ] && [ ! -L "${p50_fc_dest}/${p50_fc_name}" ]; then
\t\t\t\t\t\t\tmv "${p50_fc_item}" "${p50_fc_dest}/${p50_fc_name}" || :
\t\t\t\t\t\tfi
\t\t\t\t\tdone
\t\t\t\tfi
\t\t\t\trm -rf "${p50_fc_stage}" || :
\t\t\tfi
\t\t\tunset p50_fc_valid p50_fc_count p50_fc_stage p50_fc_item p50_fc_name
\t\t\tunset p50_fc_source p50_fc_dest
\t\tfi
\tfi
'''.replace('\\t','\t')

def patch_main(text):
 if text.count(MARKER)!=1 or 'P50_V114_OPTIONAL_FONTCACHE' in text:raise ValueError('Unexpected boot main')
 return text.replace(MARKER,HOOK+MARKER,1)

def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root.resolve(strict=True)
 if root==Path('/'):raise ValueError('Refusing to modify running system')
 path=root/'usr/lib/live/boot/9990-main.sh'
 if path.is_symlink() or not path.is_file():raise ValueError('Expected isolated regular boot script')
 path.write_text(patch_main(path.read_text()))
if __name__=='__main__':main()
