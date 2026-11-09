#!/usr/bin/env python3
"""Summarize four verified alternating interactive VM trials."""
import json,statistics,sys
from pathlib import Path

def evaluate(root):
    root=Path(root);names=('base1','cand1','cand2','base2');data={n:json.loads((root/n/'result.json').read_text()) for n in names}
    keys=('first_home_seen_seconds','early_js_response_seconds','staged_ram_ready_seconds')
    for n,r in data.items():
        if not all(isinstance(r.get(k),(int,float)) and r[k]>0 for k in keys):raise ValueError('Missing timings '+n)
        if not all(r.get(k) for k in ('early_media_attached_before_navigation','early_media_attached_after_js_response','media_ejected','input_sent_after_eject','qemu_running_at_end')) or r.get('errors'):raise ValueError('Browser or RAM failure '+n)
    summary={'measurement':'One host, A-B-B-A order; clock from QEMU launch, 2 vCPU, 3 GiB, BIOS, 30 MiB/s virtual USB, 0.2 s polling plus image capture.','physical_acer_tested':False,
             'results':{n:{k:data[n][k] for k in keys} for n in names}}
    for label,pair in [('baseline',('base1','base2')),('candidate',('cand1','cand2'))]:
        for k in keys:summary[label+'_mean_'+k]=statistics.mean(data[n][k] for n in pair)
    summary['home_gain_seconds']=summary['baseline_mean_first_home_seen_seconds']-summary['candidate_mean_first_home_seen_seconds']
    summary['js_gain_seconds']=summary['baseline_mean_early_js_response_seconds']-summary['candidate_mean_early_js_response_seconds']
    return summary

if __name__=='__main__':
    root=Path(sys.argv[1]);data=evaluate(root);(root/'reports/comparison.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2))
