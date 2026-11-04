#!/usr/bin/env python3
"""Audit actual serial, screenshots, and guest process metrics; fail closed.
Firefox page render is NEVER inferred merely from Ctrl+L or HTTPS curl.
"""
import argparse,json,re
from pathlib import Path
def audit(folder,mode,ram):
    folder=Path(folder)
    serial=(folder/"serial.log").read_text(errors="replace") if (folder/"serial.log").exists() else ""
    result=json.loads((folder/"result.json").read_text()) if (folder/"result.json").exists() else {}
    samples=[]
    for ln in serial.splitlines():
        if "P50_V99_RAM_SAMPLE " not in ln:continue
        values={}
        for key,v in re.findall(r"([a-zA-Z][a-zA-Z0-9]*)=(-?\d+)",ln):
            try:values[key]=int(v)
            except ValueError:pass
        if "availableKiB" in values:samples.append(values)
    ff= bool(result.get("real_nonroot_firefox_process") and "P50_V91_NONROOT_FIREFOX_PROCESS_SEEN" in serial)
    tls=bool(result.get("real_guest_ca_verified_public_https") and
       ("PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_DIRECT=PASS" in serial or
        "PUPPY50_V85_GUEST_CA_VERIFIED_PUBLIC_HTTPS_BRIDGE=PASS" in serial))
    zram=("P50_V99_ZRAM_ENABLED=1" in serial and "P50_V99_ZRAM_NO_PHYSICAL_DISK=1" in serial)
    return {
       "schema":"PUPPY50_V99_ACTUAL_KVM_FIREFOX_ZRAM_AB",
       "mode":mode,"guest_RAM_MiB":ram,
       "guest_CA_verified_public_https":tls,
       "nonroot_firefox_seen":ff,
       "boot_media_ejected":result.get("boot_cd_ejected") is True,
       "guest_running_after_eject":result.get("guest_running_at_end") is True,
       "browser_navigation_requested":result.get("real_QMP_browser_navigation_requested") is True,
       "actual_external_webpage_visible_verified":False,
       "zram_enabled_guest_verified":zram,
       "zram_samples_count":len(samples),
       "min_mem_available_mib":round(min(v["availableKiB"] for v in samples)/1024,2) if samples else None,
       "max_swap_in_use_mib":round(max((v.get("swapTotalKiB",0)-v.get("swapFreeKiB",0)) for v in samples)/1024,2) if samples else None,
       "max_zram_physical_mib":round(max(v.get("physicalBytes",0) for v in samples)/1048576,2) if samples else None,
       "max_zram_original_mib":round(max(v.get("originalBytes",0) for v in samples)/1048576,2) if samples else None,
       "max_oom_kill_counter":max((v.get("oomKill",0) for v in samples),default=None),
       "real_KVM_screenshots":result.get("screenshots",[]),
       "full_RAM_only_bare_metal_hardware_proven":False,
       "physical_wifi_hardware_verified":False,
       "observed_guest_memory_samples":samples}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--mode",choices=["original","zram"],required=True)
    p.add_argument("--ram",type=int,required=True)
    a=p.parse_args()
    data=audit(a.evidence,a.mode,a.ram)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({k:v for k,v in data.items() if k!="observed_guest_memory_samples"},indent=2))
if __name__=="__main__":main()
