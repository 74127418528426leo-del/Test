#!/usr/bin/env python3
"""Select the optional layer for all full-RAM menu entries only."""
import argparse,re
from pathlib import Path

def patch_one(text,expected):
 if 'module=full' in text:raise ValueError('Menu already selects a module list')
 result=[];count=0
 for line in text.splitlines(keepends=True):
  if re.match(r'^\s*(?:append|linux)\s+',line) and re.search(r'(?<!\S)boot=live(?!\S)',line) and re.search(r'(?<!\S)toram(?!\S)',line):
   line,n=re.subn(r'(?<!\S)toram(?!\S)','toram module=full',line,count=1);assert n==1;count+=1
  result.append(line)
 if count!=expected:raise ValueError(f'Unexpected full-RAM menu count: {count}')
 return ''.join(result)
def patch_menus(bios,uefi):return patch_one(bios,2),patch_one(uefi,3)
def main():
 p=argparse.ArgumentParser();p.add_argument('bios',type=Path);p.add_argument('uefi',type=Path);a=p.parse_args()
 if any(f.is_symlink() or not f.is_file() for f in (a.bios,a.uefi)):raise ValueError('Expected regular extracted menu files')
 b,u=patch_menus(a.bios.read_text(),a.uefi.read_text());a.bios.write_text(b);a.uefi.write_text(u)
if __name__=='__main__':main()
