#!/usr/bin/env python3
"""Exact bytewise duplicate audit for ORIGINAL Puppy SFS regular files.
This is an opportunity UPPER BOUND before compression and SFS implementation.
No symlinks are rewritten and no file is removed.
"""
import argparse,collections,hashlib,json,os
from pathlib import Path

def one_layer(layer,root,destination):
    root=Path(root).resolve(strict=True)
    dst=Path(destination)
    total=0;count=0;entries=[]
    for dirpath, _, files in os.walk(root,followlinks=False):
        for name in files:
            p=Path(dirpath)/name
            if not p.is_file() or p.is_symlink():continue
            size=p.stat().st_size
            if not size:continue
            h=hashlib.sha256()
            with p.open("rb") as f:
                for b in iter(lambda:f.read(2*1024*1024),b''):h.update(b)
            rel=str(p.relative_to(root))
            entries.append({'layer':layer,'path':rel,'bytes':size,'sha256':h.hexdigest()})
            count+=1;total+=size
    with dst.open('w') as f:
        for r in entries:f.write(json.dumps(r,separators=(",",":"))+"\n")
    print(json.dumps({'layer':layer,'files':count,'regular_file_bytes':total,'record_path':str(dst)}))

def combined(paths,dest):
    group=collections.defaultdict(list)
    layers=collections.defaultdict(int)
    for f in paths:
        for line in Path(f).open():
            r=json.loads(line);group[(r["sha256"],r["bytes"])].append(r)
            layers[r["layer"]]+=r["bytes"]
    rows=[];dup_upper=0
    for (hash_value,size),items in group.items():
        if len(set(r["layer"] for r in items))<2:continue
        # Upper-bound actual bytes from duplicate files crossing layers.
        # Existing in-layer hardlinks and duplicates may be separately deduped.
        duplicates=len(items)-1
        extra=size*duplicates
        dup_upper+=extra
        rows.append({'bytes_per_file':size,'copies':len(items),'uncompressed_extra_bytes_upper_bound':extra,
                     'paths':[(r["layer"],r["path"]) for r in items[:8]],'sha256':hash_value})
    result={'schema':'Puppy50_v42_original_byte_identical_regular_file_cross_layer_opportunity',
        'layers':dict(layers),
        'across_layer_duplicate_groups':len(rows),
        'uncompressed_extra_bytes_upper_bound':dup_upper,
        'uncompressed_extra_mib_upper_bound':round(dup_upper/1048576,3),
        'important_caveats':[
          'Uncompressed duplicate file bytes do NOT equal achievable compressed SFS savings.',
          'Shared libraries and firmware might be different versions despite similar filenames.',
          'No files, symlinks, applications or overlay precedence have been changed.',
          'A hypothetical cross-layer content store requires proving every path, metadata, mount order and update behavior.'],
        'top_duplicate_groups':sorted(rows,key=lambda r:r['uncompressed_extra_bytes_upper_bound'],reverse=True)[:50]}
    Path(dest).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!='top_duplicate_groups'},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();sp=p.add_subparsers(dest="cmd",required=True)
    a=sp.add_parser("layer");a.add_argument("layer");a.add_argument("root");a.add_argument("output")
    b=sp.add_parser("aggregate");b.add_argument("output");b.add_argument("reports",nargs="+")
    opts=p.parse_args()
    if opts.cmd=="layer":one_layer(opts.layer,opts.root,opts.output)
    else:combined(opts.reports,opts.output)
