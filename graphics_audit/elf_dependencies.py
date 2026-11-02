#!/usr/bin/env python3
"""Identify graphics/LLVM dynamic links without executing any staged binary.

A DT_NEEDED edge is positive evidence that the library is required for loading
that ELF. Absence of an edge DOES NOT prove safety of removal (dlopen, plugins).
Does not build a lighter Mesa, and does not prove graphics or WebGL operation.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

NEEDED = re.compile(r"\(NEEDED\)\s+Shared library:\s+\[([^\]]+)\]")

def extract_needed(readelf_stdout):
    return NEEDED.findall(readelf_stdout)

def analyze_file(path, root):
    if not path.exists() or not path.is_file():
        return None
    p = subprocess.run(["readelf","-dW",str(path)],capture_output=True,text=True,timeout=30)
    names=extract_needed(p.stdout) if p.returncode==0 else []
    return {
      "path":str(path.relative_to(root)),
      "bytes":path.stat().st_size,
      "elf_readable":p.returncode==0,
      "needed_libraries":names,
      "needs_LLVM_directly":any(name.startswith("libLLVM") for name in names),
      "needs_libgallium_directly":any("gallium" in name for name in names)
    }

def audit(root):
    root=Path(root).resolve(strict=True)
    targets=[]
    for pattern in ("usr/lib/libgallium*.so*","usr/lib/libLLVM*.so*",
                    "usr/lib/libEGL*.so*","usr/lib/libGL*.so*",
                    "usr/lib/libvulkan*.so*","usr/lib/firefox-esr/libxul.so",
                    "usr/lib/libwebkitgtk*.so*"):
        for path in root.glob(pattern):
            if path.is_file() and not path.is_symlink() and path not in targets:
                targets.append(path)
    selected=[obj for obj in (analyze_file(p,root) for p in sorted(targets)) if obj]
    gallium=[x for x in selected if "libgallium" in Path(x["path"]).name]
    llvm=[x for x in selected if "libLLVM" in Path(x["path"]).name]
    return {
      "schema":"PUPPY50_GRAPHICS_ABI_AUDIT_V1",
      "library_data":selected,
      "gallium_directly_needs_LLVM":any(x["needs_LLVM_directly"] for x in gallium),
      "gallium_present":bool(gallium),
      "llvm_present":bool(llvm),
      "llvm_total_regular_file_bytes":sum(x["bytes"] for x in llvm),
      "total_examined_files":len(selected),
      "llvm_removal_safe":False,
      "gpu_webgl_verified":False,
      "interpretation":"DT_NEEDED is positive load-time dependency. Lack of direct link is not proof of safe removal. Never delete installed LLVM without verifying all ELF and dlopen/plugin users and complete graphics tests."
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=audit(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="library_data"},indent=2))
    for row in result["library_data"]:
        if row["needed_libraries"]:
            print(row["path"],"NEEDED:",",".join(row["needed_libraries"]))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
