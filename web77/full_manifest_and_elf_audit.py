#!/usr/bin/env python3
"""Audit APK tracked files that are ABSENT, plus sampled ELF DT_NEEDED closure.

Complements v73: checking the digests of files that still exist is not enough
if pruning removed libraries while package records remain installed.
This is a read-only factual audit, NOT a complete security/loader/CVE proof.
"""
import argparse
import collections
import json
import os
import re
import subprocess
from pathlib import Path

NEEDED=re.compile(r"\(NEEDED\).*Shared library:\s*\[([^\]]+)\]")
LIB_SEARCH=("lib","lib64","usr/lib","usr/lib64","usr/local/lib")
ELF_TARGETS=(
 "usr/lib/libgallium-26.1.6.so",
 "usr/lib/libEGL.so.1.0.0",
 "usr/lib/libGL.so.1.2.0",
 "usr/lib/gbm/dri_gbm.so",
 "usr/lib/dri/libdril_dri.so",
 "usr/bin/firefox-esr"
)

def inventory(root):
    db=next((root/n for n in
        ("lib/apk/db/installed","usr/lib/apk/db/installed","var/lib/apk/db/installed")
        if (root/n).is_file()),None)
    if db is None:raise ValueError("No package database to audit")
    entries={}
    for stanza in db.read_text(errors="replace").split("\n\n"):
        pkg="";folder=""
        for line in stanza.splitlines():
            if line.startswith("P:"):pkg=line[2:]
            elif line.startswith("F:"):folder=line[2:]
            elif line.startswith("R:"):
                rel=(Path(folder)/line[2:]).as_posix()
                if rel.startswith("/") or ".." in Path(rel).parts:
                    raise ValueError("Untrusted manifest path escapes root")
                entries[rel]=pkg
    return entries

def elf_needed(path):
    with path.open("rb") as f:
        if f.read(4)!=b"\x7fELF":return []
    p=subprocess.run(["readelf","-dW",str(path)],capture_output=True,text=True,timeout=20)
    if p.returncode not in (0,1):
        raise RuntimeError("readelf error for "+str(path))
    return NEEDED.findall(p.stdout)

def audit(root):
    root=Path(root).resolve(strict=True)
    manifest=inventory(root)
    missing=collections.defaultdict(list)
    missing_libs=[]
    for path,pkg in manifest.items():
        p=root/path
        if not os.path.lexists(p):
            missing[pkg].append(path)
            if "/lib" in path and (".so" in path or path.endswith(".a")):
                missing_libs.append({"package":pkg,"path":path})
    libnames=set()
    for d in LIB_SEARCH:
        x=root/d
        # Never let an absolute guest symlink resolve to the RUNNER'S host
        # filesystem; this audit must be read-only and rooted in extraction.
        if x.is_symlink() and not x.resolve().is_relative_to(root):
            continue
        if x.is_dir():
            for p in x.rglob("*"):
                if p.is_symlink():
                    libnames.add(p.name)
                elif p.is_file() and p.resolve().is_relative_to(root):
                    libnames.add(p.name)
    dependency_report={}
    for rel in ELF_TARGETS:
        p=root/rel
        if not p.is_file() or not p.resolve().is_relative_to(root):continue
        needed=elf_needed(p)
        dependency_report[rel]={
          "DT_NEEDED":needed,
          "missing_search_path_basename":[name for name in needed if name not in libnames],
          "llvm_needed":[name for name in needed if "LLVM" in name]
        }
    all_missing=[{"package":pkg,"file":rel} for pkg,files in missing.items() for rel in files]
    per_pkg=sorted([{"package":pkg,"missing":len(files),"examples":files[:8]}
                    for pkg,files in missing.items()],key=lambda x:-x["missing"])
    return {
      "schema":"PUPPY50_V77_FULL_INSTALLED_MANIFEST_AND_ELF_SONAME_AUDIT",
      "apk_recorded_regular_or_symlink_paths":len(manifest),
      "apk_recorded_paths_missing_from_actual_root":len(all_missing),
      "tracked_missing_file_examples":all_missing[:55],
      "packages_with_missing_tracked_files":len(missing),
      "highest_missing_file_counts":per_pkg[:45],
      "missing_registered_library_examples":missing_libs[:90],
      "sampled_critical_elf_DT_NEEDED":dependency_report,
      "sampled_missing_DT_NEEDED_total":sum(len(x["missing_search_path_basename"]) for x in dependency_report.values()),
      "present_library_basenames":len(libnames),
      "zero_digest_mismatches_ensures_all_files_exist":False,
      "complete_dynamic_loader_or_security_certification":False,
      "full_dlopen_dependency_coverage":False,
      "secure_updates_certified":False,
      "note":"A file missing from a package manifest can be intentionally pruned, but still indicates incoherent package ownership and might be needed at runtime. SONAME search is an approximation and does not cover dlopen/rpath/architectures."
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root",type=Path)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    report=audit(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2)[:14000])
if __name__=="__main__":main()
