#!/usr/bin/env python3
"""Byte + metadata fidelity audit of losslessly repacked SquashFS trees.

Run as root after unsquashfs to preserve uid/gid information. Fail closed.
No files in either tree are modified.
"""
import hashlib,json,os,stat,sys
from pathlib import Path

def inventory(root):
    root=Path(root).resolve(strict=True)
    out={}
    sizes=[]
    for parent, dirs, files in os.walk(root,topdown=True,followlinks=False):
        for name in ['.'] if parent==str(root) else []:
            pass
        for name in sorted(dirs+files):
            p=Path(parent)/name
            rel=str(p.relative_to(root))
            st=p.lstat()
            mode=st.st_mode
            kind='f' if stat.S_ISREG(mode) else 'd' if stat.S_ISDIR(mode) else 'l' if stat.S_ISLNK(mode) else 'other'
            record={'kind':kind,'mode':stat.S_IMODE(mode),'uid':st.st_uid,'gid':st.st_gid,'mtime_ns':st.st_mtime_ns}
            if kind=='f':
                h=hashlib.sha256()
                with p.open('rb') as f:
                    for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
                record.update(size=st.st_size,sha256=h.hexdigest())
                sizes.append((st.st_size,rel))
            elif kind=='l':record['link_target']=os.readlink(p)
            elif kind=='other':
                record['rdev']=st.st_rdev
            try:
                record['xattrs']={n:hashlib.sha256(os.getxattr(p,n,follow_symlinks=False)).hexdigest() for n in sorted(os.listxattr(p,follow_symlinks=False))}
            except (PermissionError,NotImplementedError,OSError):
                record['xattrs']='UNVERIFIED'
            out[rel]=record
    return out,sorted(sizes,reverse=True)

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('Usage: compare_sfs_v41.py ORIGINAL_TREE REPACKED_TREE OUTPUT_JSON')
    orig,top=inventory(sys.argv[1]);copy,copytop=inventory(sys.argv[2])
    mismatches=[key for key in sorted(orig.keys()|copy.keys()) if orig.get(key)!=copy.get(key)]
    result={
        'schema':'puppy50_v41_squashfs_content_fidelity',
        'original_entries':len(orig),'repacked_entries':len(copy),
        'sha256_file_contents_and_metadata_identical':not mismatches,
        'mismatches_first_20':mismatches[:20],
        'top_15_original_files':[{'bytes':int(s),'path':p} for s,p in top[:15]],
        'uncompressed_regular_file_bytes':sum(s for s,_ in top)
    }
    Path(sys.argv[3]).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if mismatches:raise SystemExit('REPACK_FAIL: original file bytes or metadata changed')
