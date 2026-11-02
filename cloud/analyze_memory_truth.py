#!/usr/bin/env python3
"""Audit real 4 GiB RAM-only Puppy after boot media ejection.

Compare with identical probes. Never mistake a process for rendered webpage or
MemTotal-MemAvailable for total exact physical allocation.
"""
import argparse,json,re,statistics
from pathlib import Path
FIELDS=("MemTotal","MemFree","MemAvailable","Cached","Buffers","Shmem","AnonPages","SReclaimable","SUnreclaim","Slab","KernelStack","PageTables","SwapTotal","SwapFree")
def parse(serial_path,runner_path):
    s=Path(serial_path).read_text(errors='replace').replace('\r','')
    runner=json.loads(Path(runner_path).read_text())
    matches=re.findall(r'PUPPY50_V40_BEGIN sample=(\d+)(.*?)PUPPY50_V40_END sample=\1',s,re.S)
    samples=[]
    for name,block in matches:
        mem={key:int(v)/1024 for key,v in re.findall(r'^('+('|'.join(FIELDS))+r'):\s*(\d+)\s+kB',block,re.M)}
        got=dict((key,round(mem[key],3)) for key in FIELDS if key in mem)
        got['sample']=int(name)
        if "MemTotal" in mem and "MemAvailable" in mem:
            got['memtotal_minus_available_MiB']=round(mem['MemTotal']-mem['MemAvailable'],3)
        zx=re.search(r'PUPPY50_TRUTH_ZRAM_PHYSICAL\s*\n([0-9 ]+)\s*\n',block)
        if zx:
            nums=zx.group(1).split()
            if len(nums)>2:got['zram_allocator_physical_MiB']=round(int(nums[2])/1048576,3)
        psi=re.search(r'full avg10=([0-9.]+)',block)
        if psi:got['psi_full_avg10_percent']=float(psi.group(1))
        samples.append(got)
    started='PUPPY50_TRUTH_BROWSER_LAUNCHER=' in s
    windowlog=re.search(r'PUPPY50_TRUTH_BROWSER_AUDIT_BEGIN(.*?)PUPPY50_TRUTH_BROWSER_AUDIT_END',s,re.S)
    names=(windowlog.group(1) if windowlog else '')
    return {
      'screenshots':runner.get('images',[]),
      'ejected_media':runner.get('media_ejection_verified',False),
      'qemu_sustained':runner.get('qemu_exit_before_deadline') is None,
      'browser_launcher_after_boot':re.findall(r'PUPPY50_TRUTH_BROWSER_LAUNCHER=(\S+)',s),
      'browser_process_at_late_audit':bool(re.search(r'firefox(?:-bin|-esr)?',names,re.I)),
      'page_title_in_window_tree':bool(re.search('PUPPY50 RAM AFTER EJECT',names,re.I)),
      'actual_page_pixels_verified':False,
      'samples':samples,
      'late_memory_observation':samples[-1] if samples else {},
      'evidence_complete':len(samples)>=7 and bool(windowlog),
    }
def main():
    p=argparse.ArgumentParser();p.add_argument('v40_serial');p.add_argument('v40_result');p.add_argument('v43_serial');p.add_argument('v43_result');p.add_argument('--out',required=True)
    a=p.parse_args();control=parse(a.v40_serial,a.v40_result);opt=parse(a.v43_serial,a.v43_result)
    report={'test':'puppy50_memory_truth_after_eject','same_guest_ram_mib':4096,'baseline_v40':control,'optimized_v43':opt,
      'automatic_browser_render_verified':False,'complete_application_compatibility_verified':False,
      '384mib_all_ram_possible_with_original_current_bytes':False,
      'no_untested_speed_claims':True,
      'one_run_each_not_repeated_benchmark':True}
    if control['samples'] and opt['samples']:
        a0=control['late_memory_observation'].get('memtotal_minus_available_MiB')
        b0=opt['late_memory_observation'].get('memtotal_minus_available_MiB')
        if a0 is not None and b0 is not None:
            report['late_memtotal_minus_available_difference_mib']=round(a0-b0,3)
    ok=all(x['ejected_media'] and x['qemu_sustained'] and x['evidence_complete'] for x in (control,opt))
    report['full_guest_eject_and_telemetry_pass']=ok
    Path(a.out).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('baseline_v40','optimized_v43')},indent=2))
    if not ok:raise SystemExit("FAIL: boot/ejection/telemetry missing, no claim")
if __name__=='__main__':main()
