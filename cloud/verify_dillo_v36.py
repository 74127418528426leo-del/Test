#!/usr/bin/env python3
"""Puppy50 v36: verify actual 256MiB Puppy original shell, prebuilt search, Dillo window."""
from pathlib import Path
import re,json,sys
if len(sys.argv)!=2:raise SystemExit("Usage: verify_dillo_v36.py results")
base=Path(sys.argv[1])
serial=(base/"ram_256MiB"/"serial.log").read_text(errors="replace")
scans=re.findall(r'PUPPY50_V36_SCAN_BEGIN scan=(\d+)(.*?)PUPPY50_V36_SCAN_END',serial,re.S)
page_windows=[n for n,s in scans if 'PUPPY50 V36 DILLO PAGE PASS' in s]
dillo_windows=[n for n,s in scans if re.search(r'"[^"\n]*Dillo[^"\n]*"',s,re.I)]
report={
  'ram_allocated_mib':256,
  'gui_complete':all(f'PUPPY50_TEST {p}=PASS' in serial for p in ('Xorg','jwm','ROX-Filer','x11_socket')),
  'prebuilt_search_worked':'PUPPY50_V31_ROX_SEARCH=PASS' in serial,
  'dillo_present':'PUPPY50_V36_DILLO_PRESENT' in serial,
  'dillo_launch_requested':'PUPPY50_V36_LAUNCH_REQUESTED' in serial,
  'window_scans':len(scans),
  'dillo_window_seen':bool(dillo_windows),
  'page_title_in_window_seen':bool(page_windows),
  'firefox_removed':False, # build preserves adrv; not a functional app test
  'all_apps_verified':False,
  'strict_50mb_verified':False
}
(base/"v36_verified.json").write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if not all(report[k] for k in ('gui_complete','prebuilt_search_worked','dillo_present','dillo_launch_requested','dillo_window_seen','page_title_in_window_seen')):
  raise SystemExit('Dillo page / guest evidence incomplete; do not claim success.')
