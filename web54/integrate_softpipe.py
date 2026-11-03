#!/usr/bin/env python3
"""Integrate *self-built* Softpipe Mesa into disposable QEMU staged root only.

THIS IS A TEST IMAGE. The package database becomes inconsistent until custom
Mesa is packaged properly. No general-hardware image or security update claim.
Before removing LLVM, check the DT_NEEDED entries of all remaining staged ELF
files. Absence of direct LLVM links is not a proof of absence of dlopen users.
"""
import argparse
import json
import os
import re
import subprocess
import tarfile
from pathlib import Path

MIB = 1048576
NEEDED_LLVM = re.compile(r"\(NEEDED\).*Shared library:\s*\[(libLLVM[^\]]*)\]")

def validate_root(root):
    root = Path(root).resolve(strict=True)
    if root.name != "rootfs" or root.parent.name != "output":
        raise ValueError("requires disposable */output/rootfs only")
    for rel in ("etc/apk/repositories","usr/share/puppy50web/index.html",
                "usr/lib/libgallium-26.1.6.so"):
        if not (root/rel).is_file():
            raise ValueError("missing staged-file marker: "+rel)
    return root

def validate_tar(tar,root):
    items = tar.getmembers()
    for m in items:
        # POSIX tar archives conventionally begin with the root '.' entry.
        # It denotes the staging root itself, not its parent directory.
        if Path(m.name) == Path("."):
            if not m.isdir():
                raise ValueError("unsafe non-directory root entry")
            continue
        if not (m.isdir() or m.isfile() or m.issym() or m.islnk()):
            raise ValueError("unexpected tar member "+m.name)
        dest = root/m.name
        # Resolve existing parents, reject links into host filesystem.
        if not dest.parent.resolve().is_relative_to(root):
            raise ValueError("path exits staged root: "+m.name)
        if m.name.startswith("/") or ".." in Path(m.name).parts:
            raise ValueError("unsafe archive path: "+m.name)
        if m.issym():
            link = (dest.parent/m.linkname).resolve()
            if not link.is_relative_to(root):
                raise ValueError("link escapes staged root: "+m.name)
        if m.islnk():
            link = (root/m.linkname).resolve()
            if not link.is_relative_to(root):
                raise ValueError("hard link escapes staged root: "+m.name)
    return items

def scan_llvm_needed(root):
    hits=[]
    files=0
    for dirpath, dirs, names in os.walk(root,followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(dirpath)/d).is_symlink()]
        for name in names:
            p=Path(dirpath)/name
            if p.is_symlink() or not p.is_file():
                continue
            try:
                with p.open("rb") as fh:
                    if fh.read(4)!=b"\x7fELF":
                        continue
            except OSError:
                continue
            files+=1
            r=subprocess.run(["readelf","-dW",str(p)],
                             capture_output=True,text=True,timeout=25)
            for lib in NEEDED_LLVM.findall(r.stdout):
                hits.append({"relative_path":str(p.relative_to(root)),
                             "needed":lib})
    return files,hits

def integrate(root,archive):
    root=validate_root(root)
    archive=Path(archive).resolve(strict=True)
    old_gallium=root/"usr/lib/libgallium-26.1.6.so"
    old_size=old_gallium.stat().st_size
    with tarfile.open(archive,"r:gz") as t:
        names=validate_tar(t,root)
        t.extractall(root,filter="data")
    new_gallium=root/"usr/lib/libgallium-26.1.6.so"
    if not new_gallium.is_file() or new_gallium.stat().st_size<=0:
        raise ValueError("missing replacement Gallium library")
    count,llvm_hits=scan_llvm_needed(root)
    llvm_files=[p for p in (root/"usr/lib").glob("libLLVM*") if p.is_file() or p.is_symlink()]
    # Stop rather than produce a misleading partial 'small' image.
    if llvm_hits:
        raise ValueError("LLVM still dynamically required by "+str(llvm_hits[:12]))
    if not llvm_files:
        raise ValueError("expected existing LLVM files to audit")
    old_llvm_apparent=sum(p.stat().st_size for p in llvm_files if p.is_file() and not p.is_symlink())
    for p in llvm_files:
        p.unlink()
    return {
      "schema":"PUPPY50_V54_STAGED_SOFTPIPE_REPLACEMENT",
      "qemu_only":True,
      "physical_gpu_crocus_supported":False,
      "archive_members":len(names),
      "old_gallium_bytes":old_size,
      "new_gallium_bytes":new_gallium.stat().st_size,
      "staged_elf_files_checked":count,
      "remaining_direct_llvm_needed":llvm_hits,
      "llvm_regular_bytes_removed":old_llvm_apparent,
      "llvm_paths_removed":[str(p.relative_to(root)) for p in llvm_files],
      "package_database_consistent":False,
      "runtime_browser_or_software_gl_proven":False,
      "security_update_distribution_ready":False,
      "warning":"Only staged QEMU disposable image. A zero DT_NEEDED count does not exclude LLVM dlopen users; real rendering, EGL/GLX tests and packaging are required."
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--mesa-archive",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    result=integrate(a.root,a.mesa_archive)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
