#!/usr/bin/env python3
"""Parse real QEMU guest memory rows. Missing is null, never a fake zero."""
import argparse,json
from pathlib import Path
KEYS=('MemTotal','MemAvailable','MemFree','Cached','Shmem','AnonPages','Slab','SReclaimable','PageTables','KernelStack','SwapFree','SwapTotal','firefox_count','firefox_pss_kib','firefox_uss_kib','firefox_swap_kib','firefox_pss_missing','all_process_pss_kib','all_process_pss_missing','compressed_root_bytes','psi_some_avg10','oom_kills')
def parse_serial(data,ram):
    rows=[]
    for line in data.splitlines():
        idx=line.find('P50MEM phase=')
        if idx<0:continue
        attrs={}
        for token in line[idx:].split()[1:]:
            if '=' in token:
                k,v=token.split('=',1);attrs[k]=v
        row={'phase':attrs.get('phase','unknown')}
        for key in KEYS:
            try:row[key]=float(attrs[key]) if key=='psi_some_avg10' else int(attrs[key])
            except (KeyError,ValueError,TypeError):row[key]=None
        rows.append(row)
    good=[r for r in rows if r['firefox_count'] and r['firefox_pss_missing']==0 and r['firefox_pss_kib'] is not None]
    avail=[r['MemAvailable'] for r in rows if r['MemAvailable'] is not None]
    roots=[r['compressed_root_bytes'] for r in rows if r['compressed_root_bytes'] is not None]
    oom=[r['oom_kills'] for r in rows if r['oom_kills'] is not None]
    return dict(schema='PUPPY50_V89_GUEST_MEMORY_ATTRIBUTION',
      guest_ram_allocated_mib=ram,samples_observed=len(rows),
      firefox_complete_pss_samples=len(good),
      peak_observed_firefox_pss_mib=round(max(r['firefox_pss_kib'] for r in good)/1024,2) if good else None,
      lowest_memavailable_mib=round(min(avail)/1024,2) if avail else None,
      compressed_root_mib=round(max(roots)/1048576,2) if roots else None,
      oom_kills_increased=(max(oom)>min(oom)) if len(oom)>1 else None,
      samples=rows,
      note='Per-process PSS excludes kernel and unmapped cache. Screenshot needs independent human inspection.')
if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--serial',type=Path,required=True)
    a.add_argument('--ram',type=int,required=True)
    a.add_argument('--out',type=Path,required=True)
    args=a.parse_args()
    report=parse_serial(args.serial.read_text(errors='replace'),args.ram)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))
