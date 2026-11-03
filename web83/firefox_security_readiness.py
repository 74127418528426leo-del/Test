#!/usr/bin/env python3
"""Evidence-based browser freshness gate for Puppy50 experimental ISOs.

The input is a REAL APK inventory report from an extracted ISO. Compare its
installed Firefox ESR against a dated official Mozilla security-update
baseline; never equate an intact package database with an updated browser.
This is one necessary release condition, not a CVE scanner or security proof.
"""
import argparse
import json
import re
from pathlib import Path

REQUIRED_MAJOR_MINOR_PATCH=(153,6,0)
AS_OF="2026-10-27"
SOURCE="https://www.mozilla.org/en-US/security/advisories/mfsa2026-120/"
RELEASE_URL="https://www.firefox.com/en-US/firefox/153.6.0/releasenotes/"

def parsed_version(version):
    if not isinstance(version,str):
        raise ValueError("Missing Firefox package version")
    m=re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:-r\d+)?",version)
    if not m:raise ValueError("Unexpected Firefox ESR package version: "+version)
    return tuple(int(n) for n in m.groups())

def audit(records):
    data=json.loads(Path(records).read_text())
    if data.get("schema")!="PUPPY50_APK_PACKAGE_COHERENCE_AUDIT_V1":
        raise ValueError("Expected genuine APK-coherency report from extracted ISO")
    if data.get("apk_database_present") is not True:
        raise ValueError("Installed APK database missing")
    version=data.get("firefox_package_version_in_database")
    found=parsed_version(version)
    meets=found>=REQUIRED_MAJOR_MINOR_PATCH
    source_integrity_ok=(
        data.get("owned_shared_libraries_sha1_mismatched")==0 and
        data.get("shared_library_files_without_apk_owner")==0 and
        data.get("package_manager_inventory_missing") is False
    )
    return {
      "schema":"PUPPY50_V83_FIREFOX_RELEASE_SECURITY_READINESS",
      "actual_extracted_package_version":version,
      "minimum_published_ESR_baseline":"153.6.0",
      "baseline_date":AS_OF,
      "official_security_advisory":SOURCE,
      "official_release_notes":RELEASE_URL,
      "browser_version_meets_published_security_baseline":meets,
      "apk_library_ownership_and_digest_coherent":source_integrity_ok,
      "browser_and_graphics_updates_reproducibly_built":False,
      "browser_sandbox_independently_audited":False,
      "HTTPS_one_site_verified_does_not_prove_browsing_safe":True,
      "public_production_security_release_eligible":False,
      "online_prototype_carry_sensitive_logins":False,
      "reasons":(
          ["Installed Firefox ESR predates published October 27, 2026 security fixes"] if not meets else []
        )+[
          "Independent browser sandbox, update-signature and full CVE verification still missing",
          "In-memory OS requires reproducible signed updated boot images after shutdown"
        ]
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apk-audit",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--fail-outdated",action="store_true",help="Release gate: nonzero when browser predates dated official baseline")
    a=p.parse_args()
    r=audit(a.apk_audit)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2)+"\n")
    print(json.dumps(r,indent=2))
    if a.fail_outdated and not r["browser_version_meets_published_security_baseline"]:
        raise SystemExit("BLOCKED: outdated browser package")
if __name__=="__main__":main()
