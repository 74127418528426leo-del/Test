#!/usr/bin/env python3
"""Summarize observed Firefox startup state from real guest /proc telemetry.

A wchan such as futex_wait_queue means a thread is sleeping in a wait;
it does NOT on its own establish a deadlock or insufficient memory.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

STATE=re.compile(r'^PUPPY50_V52_STATE pid=(\d+) comm=(.*?) state=(\S+) threads=(\S+) vmsize_kib=(\S+) vmpeak_kib=(\S+) wchan=(\S+)',re.M)
THREAD=re.compile(r'^PUPPY50_V52_THREAD pid=(\d+) tid=(\d+) wchan=(\S+)',re.M)

def analyze(serial):
    rows=[]
    for pid,comm,state,threads,vmsize,vmpeak,wchan in STATE.findall(serial):
        rows.append(dict(pid=int(pid),comm=comm,state=state,
              threads=int(threads) if threads.isdigit() else None,
              vmsize_kib=int(vmsize) if vmsize.isdigit() else None,
              vmpeak_kib=int(vmpeak) if vmpeak.isdigit() else None,
              wchan=wchan))
    browser=[r for r in rows if r['comm'].startswith(('firefox','Web Content','Isolated Web','Privileged Cont','RDD Process','Socket Process','GPU Process'))]
    firefox=[r for r in rows if r['comm'].startswith('firefox')]
    parent_pids=sorted(set(r['pid'] for r in firefox))
    ch=Counter((r['state'],r['wchan']) for r in firefox)
    task_channels=Counter(chan for pid,tid,chan in THREAD.findall(serial) if int(pid) in parent_pids)
    peak_threads=max((r['threads'] for r in firefox if r['threads'] is not None),default=None)
    max_vm=max((r['vmsize_kib'] for r in firefox if r['vmsize_kib'] is not None),default=None)
    max_peak=max((r['vmpeak_kib'] for r in firefox if r['vmpeak_kib'] is not None),default=None)
    return {
      'schema':'PUPPY50_V52_FIREFOX_WAITSTATE',
      'observed_firefox_parent_pids':parent_pids,
      'firefox_state_samples':len(firefox),
      'browser_process_samples':len(browser),
      'peak_firefox_threads':peak_threads,
      'peak_firefox_virtual_memory_mib':round(max_vm/1024,2) if max_vm is not None else None,
      'peak_firefox_vmpeak_mib':round(max_peak/1024,2) if max_peak is not None else None,
      'common_main_wait_channels':[{'state':s,'wchan':w,'samples':n} for (s,w),n in ch.most_common(15)],
      'representative_thread_channels':[{'wchan':w,'samples':n} for w,n in task_channels.most_common(15)],
      'has_sufficient_process_state_data':len(firefox)>=3,
      'browser_rendered_proven':False,
      'root_cause_identified':False,
      'reason':'Parent thread wait channel and VmSize help locate stalls but do not prove root cause without Firefox logs, window mapping, allocation traces and visual screenshots.'
    }

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('serial',type=Path);a.add_argument('--out',type=Path,required=True)
    x=a.parse_args()
    obj=analyze(x.serial.read_text(errors='replace'))
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(obj,indent=2)+'\n')
    print(json.dumps(obj,indent=2))
    return 0 if obj['has_sufficient_process_state_data'] else 2

if __name__=='__main__':raise SystemExit(main())
