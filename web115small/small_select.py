#!/usr/bin/env python3
"""Select the earliest bounded Firefox residency sample from a validated trace."""
import argparse
import json
from pathlib import Path

from analyze import analyze_text

MAX_BYTES=16*1024*1024

def select_earliest(trace,result,max_bytes=MAX_BYTES):
    if not isinstance(max_bytes,int) or max_bytes<=0:raise ValueError('Invalid byte limit')
    validated,_=analyze_text(trace,result)
    snapshots={};current=None
    for row in trace.splitlines()[1:-1]:
        fields=row.split('\t')
        if fields[0]=='SNAP':
            current=int(fields[1]);snapshots[current]={'uptime':float(fields[2]),'lines':[],'total':0,'libxul':0};path=None
        elif fields[0]=='ENDSNAP':current=None
        elif fields[0]=='P50_FILE':
            path=fields[1];snapshots[current]['lines'].append(row)
        elif fields[0]=='RANGE':
            length=int(fields[2]);snapshots[current]['total']+=length
            if path=='/usr/lib/firefox-esr/libxul.so':snapshots[current]['libxul']+=length
            snapshots[current]['lines'].append(row)
    candidates=[i for i,x in snapshots.items() if x['libxul'] and i<=validated['selected_snapshot']]
    if not candidates:raise ValueError('No early eligible libxul snapshot before Firefox home')
    selected=min(candidates);snap=snapshots[selected]
    if snap['total']<=0 or snap['total']>max_bytes:raise ValueError('Early snapshot exceeds the bounded read budget')
    report={'measurement':'Earliest useful page-cache residency sample, not a demand-I/O trace.',
            'selected_snapshot':selected,'last_snapshot_before_home':validated['selected_snapshot'],
            'guest_uptime':snap['uptime'],'total_bytes':snap['total'],'max_bytes':max_bytes,
            'physical_acer_tested':False}
    return '\n'.join(snap['lines'])+'\n',report

def main():
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('result',type=Path);p.add_argument('plan',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
    plan,report=select_earliest(a.trace.read_text(),json.loads(a.result.read_text()))
    a.plan.write_text(plan);a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
