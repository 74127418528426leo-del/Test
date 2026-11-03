#!/usr/bin/env python3
"""Offline integrity audit of real Puppy50 ISO root against Alpine apk database.

This is a package-coherency diagnostic, NOT a full security/CVE assessment.
Checks actual ownership of ELF shared libraries and file digests where apk
stores a Q1 SHA-1 record; flags the known unmanaged graphics overlay.
"""
import argparse
import base64
import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path

def safe_path(root, relative):
    # All APK db paths are relative. Prevent directory traversal and prevent
    # reading host files even with malicious package records.
    p=Path(relative)
    if p.is_absolute() or ".." in p.parts or not p.parts:
        raise ValueError("Unsafe APK path in installed database")
    return root/p

def parse_apk_installed(text):
    result={}
    packages=[]
    for raw in text.split("\n\n"):
        if not raw.strip():continue
        name=""
        version=""
        folder=""
        last=None
        for row in raw.splitlines():
            if not re.match(r"^[A-Za-z]:",row):continue
            key=row[0];value=row[2:]
            if key=="P":name=value
            elif key=="V":version=value
            elif key=="F":folder=value
            elif key=="R":
                rel=str(Path(folder)/value)
                result[rel]={"package":name,"version":version,"expected_digest":None}
                last=rel
            elif key=="Z" and last:
                result[last]["expected_digest"]=value
        if name:packages.append({"name":name,"version":version})
    return result,packages

def expected_sha1(field):
    if not field or not field.startswith("Q1"):return None
    try:
        raw=base64.b64decode(field[2:]+("="*((-len(field[2:]))%4)),validate=True)
        return raw if len(raw)==20 else None
    except (ValueError,base64.binascii.Error):
        return None

def is_shared_library(path):
    return bool(re.search(r"\.so(?:\.\d+(?:\.\d+)*)?$",path.name))

def audit(root):
    root=Path(root).resolve()
    db=root/"lib/apk/db/installed"
    if not db.is_file():
        raise ValueError("No Alpine /lib/apk/db/installed; do not invent package integrity")
    entries,packages=parse_apk_installed(db.read_text(errors="replace"))
    by_package={p["name"]:p["version"] for p in packages}
    libs=[]
    for folder in ("lib","lib64","usr/lib","usr/lib64","usr/local/lib"):
        d=root/folder
        if d.is_dir():
            for file in d.rglob("*"):
                if file.is_file() and is_shared_library(file):
                    libs.append(file)
    unowned=[]
    mismatched=[]
    checksum_checked=0
    checksum_unavailable=0
    for f in libs:
        rel=f.relative_to(root).as_posix()
        rec=entries.get(rel)
        if not rec:
            unowned.append(rel)
            continue
        if f.is_symlink():
            continue
        expected=expected_sha1(rec["expected_digest"])
        if expected is None:
            checksum_unavailable+=1
            continue
        checksum_checked+=1
        h=hashlib.sha1()
        with f.open("rb") as stream:
            for data in iter(lambda:stream.read(1<<20),b""):h.update(data)
        if h.digest()!=expected:
            mismatched.append({"path":rel,"package":rec["package"],"version":rec["version"]})
    # A single trusted baseline file is not proof of maintained updates.
    cert=root/"etc/ssl/certs/ca-certificates.crt"
    browser=by_package.get("firefox-esr") or by_package.get("firefox")
    target_owners={}
    for p in ("usr/lib/libEGL.so.1","usr/lib/libGL.so.1","usr/lib/dri/swrast_dri.so",
              "usr/lib/libgbm.so.1","usr/local/bin/puppy50-web-launch"):
        o=entries.get(p)
        target_owners[p]=o["package"] if o else None
    return {
      "schema":"PUPPY50_APK_PACKAGE_COHERENCE_AUDIT_V1",
      "purpose":"Detect package database drift/unmanaged library overlays; not a full vulnerability audit",
      "apk_database_present":True,
      "apk_package_records":len(packages),
      "firefox_package_version_in_database":browser,
      "mesa_package_versions_in_database":{k:v for k,v in by_package.items() if "mesa" in k.lower()},
      "shared_library_files":len(libs),
      "shared_library_files_without_apk_owner":len(unowned),
      "unowned_lib_examples":unowned[:60],
      "owned_shared_libraries_sha1_checked":checksum_checked,
      "owned_shared_libraries_sha1_mismatched":len(mismatched),
      "owned_library_digest_mismatches":mismatched[:60],
      "owned_libraries_without_decodable_digest":checksum_unavailable,
      "selected_file_owners":target_owners,
      "ca_bundle_exists":cert.is_file(),
      "ca_bundle_bytes":cert.stat().st_size if cert.is_file() else 0,
      "security_updates_certified":False,
      "browser_sandbox_certified":False,
      "known_trusted_release_signature_present":False,
      "full_CVE_scan_performed":False,
      "ready_for_sensitive_accounts":False,
      "software_root_checked_path":str(root),
      "warning":"APK ownership and legacy SHA1 installed-file records are a limited coherency check, not evidence of security maintenance."
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root",type=Path)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    report=audit(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    # Avoid exposing local filesystem paths as user-facing claims.
    summary={k:v for k,v in report.items() if k!="software_root_checked_path"}
    print(json.dumps(summary,indent=2))
if __name__=="__main__":
    main()
