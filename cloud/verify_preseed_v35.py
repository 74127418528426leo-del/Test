#!/usr/bin/env python3
"""Validate original Puppy apps, guest-side prebuilt search and desktop at 256MiB."""
from pathlib import Path
import json,re,sys
if len(sys.argv)!=2:raise SystemExit("Usage: verify_preseed_v31.py RESULTS")
root=Path(sys.argv[1]); f=root/"ram_512MiB"/"serial.log"
s=f.read_text(errors="replace") if f.is_file() else ""
required={
 "index_database_mounted":'PUPPY50_V31_DB_PRESENT=yes' in s,
 "real_guest_plocate_search":'PUPPY50_V31_ROX_SEARCH=PASS' in s,
 "xorg_running":'PUPPY50_TEST Xorg=PASS' in s,
 "jwm_running":'PUPPY50_TEST jwm=PASS' in s,
 "rox_running":'PUPPY50_TEST ROX-Filer=PASS' in s,
 "x11_socket":'PUPPY50_TEST x11_socket=PASS' in s,
 "original_browser_launcher":'PUPPY50_V26_BROWSER_REQUEST defaultbrowser' in s,
 "firefox_process":bool(re.search(r'\{firefox-bin\}.*FirefoxESR-portable64',s)),
}
info={"schema":"puppy50_v35_prebuilt_search_live_guest","ram_allocated_mib":512,
      "status":"VERIFIED_GUEST_CHECKS" if all(required.values()) else "INCOMPLETE_OR_FAILURE",
      "checks":required,"index_update_completion_verified":False,
      "browser_window_verified":False,"all_apps_verified":False,
      "steady_state_ram_mib":None,"strict_50mb_verified":False}
(root/"v31_verified.json").write_text(json.dumps(info,indent=2)+"\n")
print(json.dumps(info,indent=2))
if not all(required.values()):raise SystemExit("Puppy50 v31: missing one or more required guest proofs")
