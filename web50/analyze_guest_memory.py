#!/usr/bin/env python3
"""Report observed real guest memory pressure; do not infer browser visibility.
Inputs are serial logs from read-only guest memory watch and real QEMU result.
"""
import argparse, json, re
from pathlib import Path

BEGIN = re.compile(r'PUPPY50_V50_SAMPLE_BEGIN index=(\d+)\s*(.*?)PUPPY50_V50_SAMPLE_END index=\1', re.S)

def analyze(serial, qemu=None):
    samples = []
    for num, body in BEGIN.findall(serial.replace('\r','')):
        mem = {k:int(v) for k,v in re.findall(r'^PUPPY50_V50_MEM (\w+): (\d+)',body,re.M)}
        counters = {k:int(v) for k,v in re.findall(r'^PUPPY50_V50_VMSTAT (\w+) (\d+)',body,re.M)}
        processes = []
        for pid,comm,rss,pss in re.findall(
            r'^PUPPY50_V50_PROCESS pid=(\d+) comm=(.*?) rss_kib=(\w+) pss_kib=(\w+)',body,re.M):
            processes.append({'pid':int(pid),'comm':comm,
                              'rss_kib':int(rss) if rss.isdigit() else None,
                              'pss_kib':int(pss) if pss.isdigit() else None})
        psi_some = re.search(r'^PUPPY50_V50_PSI some avg10=([\d.]+)',body,re.M)
        psi_full = re.search(r'^PUPPY50_V50_PSI full avg10=([\d.]+)',body,re.M)
        samples.append({'index':int(num),
                        'mem_available_kib':mem.get('MemAvailable'),
                        'shmem_kib':mem.get('Shmem'),
                        'mem_total_kib':mem.get('MemTotal'),
                        'swap_used_kib':max(0,mem['SwapTotal']-mem['SwapFree'])
                             if 'SwapTotal' in mem and 'SwapFree' in mem else None,
                        'oom_kill_counter':counters.get('oom_kill'),
                        'major_page_faults':counters.get('pgmajfault'),
                        'psi_some_avg10':float(psi_some.group(1)) if psi_some else None,
                        'psi_full_avg10':float(psi_full.group(1)) if psi_full else None,
                        'tracked_processes':processes})
    avails=[x['mem_available_kib'] for x in samples if x['mem_available_kib'] is not None]
    psi=[x['psi_full_avg10'] for x in samples if x['psi_full_avg10'] is not None]
    oom=[x['oom_kill_counter'] for x in samples if x['oom_kill_counter'] is not None]
    counted_oom=oom[-1]-oom[0] if len(oom)>1 else None
    firefox_process_counts=[sum(p['comm'].startswith(('firefox','Web Content','Isolated Web','Privileged Cont','RDD Process','GPU Process','Socket Process','Utility Process'))
                                for p in x['tracked_processes']) for x in samples]
    visible=None
    if isinstance(qemu,dict):
        visible=qemu.get('browser_after_ejection_verified')
    return {
        'schema':'PUPPY50_V50_REAL_SERIAL_MEMORY_ANALYSIS',
        'source_is_guest_serial':True,
        'samples_complete':len(samples),
        'guest_ram_mib_allocated':qemu.get('ram_allocated_mib') if isinstance(qemu,dict) else None,
        'guest_ram_copy_complete':qemu.get('ram_copy_complete') if isinstance(qemu,dict) else None,
        'guest_root_switch':qemu.get('ram_root_switch') if isinstance(qemu,dict) else None,
        'guest_cd_ejected':qemu.get('media_ejection_verified') if isinstance(qemu,dict) else None,
        'firefox_launch_requested':'PUPPY50_WEB_V45_FIREFOX_REQUESTED' in serial,
        'firefox_process_observed':any(firefox_process_counts),
        'max_tracked_firefox_processes':max(firefox_process_counts,default=0),
        'oom_kill_counter_delta':counted_oom,
        'oom_observed':counted_oom is not None and counted_oom>0,
        'minimum_mem_available_mib':round(min(avails)/1024,3) if avails else None,
        'maximum_psi_full_avg10':max(psi) if psi else None,
        'browser_visible_after_ejection':visible if visible is True else False,
        'browser_interactive_proven':False,
        'valid_monitoring':len(samples)>=3 and bool(avails),
        'diagnosis': ('OOM_OBSERVED' if counted_oom is not None and counted_oom>0
          else 'NO_KERNEL_OOM_IN_SAMPLED_WINDOW' if len(samples)>=3 and len(oom)>1
          else 'INSUFFICIENT_MEMORY_TELEMETRY'),
        'limits':'No OOM means only no observed OOM, not proof of memory sufficiency. QEMU result legacy browser_visible flag is generally unverified; screenshots require independent visual review. Samples never prove functionality.',
        'samples':samples
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('serial',type=Path)
    p.add_argument('--qemu-result',type=Path)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    r=analyze(args.serial.read_text(errors='replace'),json.loads(args.qemu_result.read_text()) if args.qemu_result else None)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ('samples','limits')},indent=2))
    return 0 if r['valid_monitoring'] else 2

if __name__=='__main__':
    raise SystemExit(main())
