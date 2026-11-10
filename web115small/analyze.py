#!/usr/bin/env python3
"""Validate page snapshots and pick the last one observed before the home frame."""
import argparse,json
from pathlib import Path

REQUIRED={'/usr/lib/firefox-esr/libxul.so','/usr/lib/firefox-esr/omni.ja','/usr/lib/firefox-esr/browser/omni.ja'}

def analyze_text(text,result):
    rows=text.splitlines()
    if len(rows)<2 or rows[0]!='P50_HOT_TRACE_V1' or rows[-1]!='P50_HOT_TRACE_END':raise ValueError('Incomplete trace')
    snapshots={};current=None;path=None;last_end=0
    for row in rows[1:-1]:
        f=row.split('\t')
        try:
            if f[0]=='SNAP' and len(f)==3:
                if current is not None:raise ValueError('Nested snapshot')
                current=int(f[1])
                if current in snapshots:raise ValueError('Duplicate snapshot')
                snapshots[current]={'uptime':float(f[2]),'lines':[],'files':{}};path=None
            elif f[0]=='ENDSNAP' and len(f)==2:
                if current is None or int(f[1])!=current or set(snapshots[current]['files'])!=REQUIRED:raise ValueError('Bad snapshot end')
                current=None;path=None
            elif current is not None and f[0]=='P50_FILE' and len(f)==4:
                path=f[1];size,page=int(f[2]),int(f[3])
                if path not in REQUIRED or path in snapshots[current]['files'] or size<=0 or page<=0 or page&(page-1):raise ValueError('Unexpected file')
                snapshots[current]['lines'].append(row)
                snapshots[current]['files'][path]={'size':size,'pagesize':page,'cached':0};last_end=0
            elif current is not None and path is not None and f[0]=='RANGE' and len(f)==3:
                start,length=int(f[1]),int(f[2]);info=snapshots[current]['files'][path];page=info['pagesize'];limit=((info['size']+page-1)//page)*page
                if start<last_end or start%page or length<=0 or length%page or start+length>limit:raise ValueError('Invalid range')
                info['cached']+=length;last_end=start+length;snapshots[current]['lines'].append(row)
            else:raise ValueError('Unexpected row')
        except (ValueError,KeyError,IndexError) as e:raise ValueError('Invalid snapshot row: '+row) from e
    if current is not None or sorted(snapshots)!=list(range(14)):raise ValueError('Missing snapshots')
    home=result.get('first_home_seen_seconds');seen=result.get('serial_marker_first_seen_seconds',{})
    if not isinstance(home,(int,float)):raise ValueError('No home frame')
    avail=[i for i in snapshots if 'P50_HOT_SNAPSHOT_%02d'%i in seen and seen['P50_HOT_SNAPSHOT_%02d'%i]<=home]
    if not avail:raise ValueError('No snapshot observed before home')
    chosen=max(avail);snap=snapshots[chosen]
    if not snap['files']['/usr/lib/firefox-esr/libxul.so']['cached']:raise ValueError('No resident Firefox pages in chosen snapshot')
    if not all(result.get(k) for k in ('early_js_response_seconds','staged_ram_ready_seconds','early_media_attached_before_navigation','early_media_attached_after_js_response','media_ejected','input_sent_after_eject','qemu_running_at_end')) or result.get('errors'):raise ValueError('Browser or RAM test failed')
    out={'measurement':'Guest page-cache residency, not physical I/O. Host clock from QEMU launch; 2 vCPU, 3 GiB, BIOS, USB capped at 30 MiB/s.',
         'physical_acer_tested':False,'first_home_seen_seconds':home,'selected_snapshot':chosen,'host_marker_seconds':seen['P50_HOT_SNAPSHOT_%02d'%chosen],
         'snapshot_guest_uptime':snap['uptime'],'files':snap['files'],'markers':seen}
    return out,snap['lines']

def main():
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('result',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    summary,lines=analyze_text(a.trace.read_text(),json.loads(a.result.read_text()))
    (a.out/'selected-pages.tsv').write_text('\n'.join(lines)+'\n')
    (a.out/'page-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
