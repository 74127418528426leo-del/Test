#!/usr/bin/env python3
"""Split opt-in directories into a second image while preserving an intact fallback."""
import argparse,json,os,shutil,stat,subprocess
from pathlib import Path,PurePosixPath

DEFAULT=('usr/lib/firmware/netronome','usr/lib/firmware/liquidio','usr/lib/firmware/cxgb4','usr/lib/firmware/bnx2x','usr/lib/firmware/qed','usr/share/doc','usr/share/man')

def split_root(root,extra,selected=DEFAULT):
 root=Path(root).resolve(strict=True);extra=Path(extra).resolve(strict=False)
 if root==Path('/') or not root.is_dir() or extra.exists() or extra.is_symlink() or root==extra or root in extra.parents or extra in root.parents:raise ValueError('Expected separate isolated roots and a new destination')
 names=[]
 for text in selected:
  rel=PurePosixPath(text)
  if rel.is_absolute() or not rel.parts or any(x in ('.','..') for x in text.split('/')):raise ValueError('Unsafe selection')
  path=root.joinpath(*rel.parts)
  for parent in (path,*path.parents):
   if parent==root:break
   if parent.is_symlink():raise ValueError('Symlink in selected directory path')
  if not path.is_dir() or not path.resolve(strict=True).is_relative_to(root):raise ValueError('Missing or unsafe selected directory')
  if any(rel==n or rel in n.parents or n in rel.parents for n in names):raise ValueError('Overlapping selections')
  names.append(rel)
 if not names:raise ValueError('No directories selected')
 seen={};files=0;raw=0
 for current,dirs,filenames in os.walk(root,followlinks=False):
  for item in filenames:
   path=Path(current)/item;st=path.lstat();rel=path.relative_to(root)
   inside=any(rel==n or n in rel.parents for n in names)
   if inside and stat.S_ISREG(st.st_mode):files+=1;raw+=st.st_size
   if stat.S_ISREG(st.st_mode) and st.st_nlink>1:
    key=(st.st_dev,st.st_ino);prev=seen.get(key)
    if prev is not None and prev!=inside:raise ValueError('Hardlink crosses the layer boundary')
    seen[key]=inside
 parent_times={root.joinpath(*n.parts).parent:root.joinpath(*n.parts).parent.stat() for n in names}
 extra.mkdir(mode=0o700,parents=False)
 args=['rsync','-aHAX','--numeric-ids','--relative','--',*(n.as_posix() for n in names),str(extra)+'/']
 subprocess.run(args,cwd=root,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 check=['rsync','-aHAXnci','--numeric-ids','--relative','--',*(n.as_posix() for n in names),str(extra)+'/']
 result=subprocess.run(check,cwd=root,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if result.stdout:raise RuntimeError('Copied extra layer differs: '+result.stdout[:1000])
 st_root=root.stat();os.chown(extra,st_root.st_uid,st_root.st_gid);shutil.copystat(root,extra,follow_symlinks=False)
 for name in names:shutil.rmtree(root.joinpath(*name.parts))
 for path,st in parent_times.items():os.utime(path,ns=(st.st_atime_ns,st.st_mtime_ns),follow_symlinks=False)
 return {'moved_subtrees':[n.as_posix() for n in names],'regular_files':files,'uncompressed_bytes':raw,'copied_and_checked_before_removal':True}

def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('extra',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
 r=split_root(a.root,a.extra);a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
