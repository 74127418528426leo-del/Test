#!/usr/bin/env python3
"""Emit a dependency-ordered BusyBox insmod boot loader from initrd modules.dep."""
import argparse,pathlib,re
SEEDS=['ata_piix','sr_mod','isofs','loop','squashfs','overlay','virtio_pci','virtio_blk','ahci','sd_mod','usb_storage',
       # Input modules have to be loaded before switch_root: on this image
       # /lib/modules in the final root does not provide modprobe lookup.
       'evdev','psmouse','mousedev','e1000','virtio_net']
def stem(s):
 return re.sub(r'\.ko(?:\.(?:xz|gz|zst))?$','',pathlib.PurePosixPath(s).name).replace('-','_')
def generate(txt,release,exists=None):
 deps={}
 for line in txt.splitlines():
  if ':' not in line:continue
  name,raw=line.split(':',1)
  if name.strip().endswith('.ko'):deps[name.strip()]=raw.strip().split()
 bystem={stem(k):k for k in deps}
 required=['ata_piix','sr_mod','loop','squashfs','overlay','isofs','evdev','psmouse','mousedev','e1000']
 missing=[x for x in required if x not in bystem]
 if missing:raise ValueError('Missing critical module(s): '+repr(missing))
 seen=set();active=set();ordered=[]
 def visit(k):
  if k in seen:return
  if k in active:raise ValueError('Circular module dependency '+k)
  if k not in deps:raise ValueError('Unbundled dependency '+k)
  if exists and not exists(k):raise ValueError('Missing initrd module file '+k)
  active.add(k)
  for dep in deps[k]:visit(dep)
  active.remove(k);seen.add(k);ordered.append(k)
 for seed in SEEDS:
  if seed in bystem:visit(bystem[seed])
 lines=['#!/bin/busybox sh','# Ordered direct kernel module loading, independent of BusyBox modprobe index parser.','echo PUPPY50_V46_DIRECT_INSMOD_BEGIN']
 for rel in ordered:
  lines+=['/busybox insmod "/lib/modules/'+release+'/'+rel+'" 2>&1',
          'echo "PUPPY50_V46_DIRECT_INSMOD module='+stem(rel)+' status=$?"']
 lines.append('echo PUPPY50_V46_DIRECT_INSMOD_END')
 return '\n'.join(lines)+'\n',ordered
def main():
 p=argparse.ArgumentParser()
 p.add_argument('modules',type=pathlib.Path);p.add_argument('out',type=pathlib.Path)
 a=p.parse_args()
 source=a.modules
 sh,order=generate((source/'modules.dep').read_text(),source.name,lambda r:(source/r).is_file())
 a.out.write_text(sh);a.out.chmod(0o755)
 print('PUPPY50_V46_MODULE_DEPENDENCY_CHAIN_VALIDATED',len(order))
if __name__=='__main__':main()
