#!/usr/bin/env python3
"""Safe cleanup of UNOWNED compatibility aliases in a DISPOSABLE stock-Mesa control.

These five unversioned symlinks were introduced by the manually overlaid Mesa
graphics stack and do not appear in the original v70 APK installed-file index.
Never touch packaged symlinks or any unexpected file type.
"""
import argparse,json
from pathlib import Path
ALIASES=("usr/lib/libgbm.so","usr/lib/libEGL.so","usr/lib/libGLESv1_CM.so",
         "usr/lib/libGL.so","usr/lib/libGLESv2.so")

def clean(root):
    root=Path(root).resolve(strict=True)
    if root.name!="rootfs" or root.parent.name!="output":
        raise ValueError("Must use disposable */output/rootfs; never host operating system")
    db=root/"lib/apk/db/installed"
    if not db.is_file():raise ValueError("Alpine installed package database absent")
    # Installed-file ownership is a per F: directory + R: filename record.
    current_dir=""
    owned=set()
    for line in db.read_text(errors="replace").splitlines():
        if line.startswith("F:"):current_dir=line[2:]
        elif line.startswith("R:"):owned.add((Path(current_dir)/line[2:]).as_posix())
    removed=[]
    for rel in ALIASES:
        if rel in owned:
            continue
        f=root/rel
        if not f.is_symlink():
            if f.exists():raise ValueError("Unexpected non-symlink unowned file: "+rel)
            continue
        # Never walk through nested filesystem symlinks outside the root.
        if not f.parent.resolve().is_relative_to(root):
            raise ValueError("Parent directory escapes disposable root: "+rel)
        target=(f.parent/f.readlink()).resolve()
        if not target.is_relative_to(root/"usr/lib"):
            raise ValueError("Unowned alias points outside root usr/lib: "+rel)
        f.unlink()
        removed.append(rel)
    return {"schema":"PUPPY50_V76_STOCK_MESA_CONTROL_CLEANUP",
            "removed_only_unowned_known_development_aliases":removed,
            "package_database_unchanged":True,
            "original_public_ISO_unchanged":True}
if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root",type=Path)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args();r=clean(args.root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2)+"\n")
    print(json.dumps(r,indent=2))
