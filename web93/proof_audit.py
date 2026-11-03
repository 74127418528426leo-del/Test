#!/usr/bin/env python3
"""Summarize real KVM Firefox evidence with no invented visual success."""
import argparse,hashlib,json,re
from pathlib import Path

def audit(folder,ram_mib):
    folder=Path(folder)
    report_file=folder/'result.json'
    report=json.loads(report_file.read_text()) if report_file.is_file() else {}
    frames={}
    for name in ['frame_100.ppm','frame_145.ppm','frame_185.ppm','frame_220.ppm','frame_260.ppm','frame_300.ppm']:
        path=folder/name
        if not path.is_file():continue
        with path.open('rb') as f:
            header=f.read(100)
        m=re.match(rb'^P6\s+(\d+)\s+(\d+)\s+(\d+)\s',header)
        if not m:continue
        width,height,limit=map(int,m.groups())
        if width>8192 or height>8192 or limit!=255 or path.stat().st_size!=m.end()+width*height*3:continue
        frames[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'width':width,'height':height}
    required=['real_QMP_browser_navigation_requested','real_guest_ca_verified_public_https',
              'real_nonroot_firefox_process','boot_cd_ejected','guest_running_at_end']
    checks={x:report.get(x) is True for x in required}
    checks['final_frame_real']= 'frame_300.ppm' in frames
    return {'schema':'PUPPY50_V93_LIVE_BROWSER_RAM_THRESHOLD',
            'ram_allocated_mib':ram_mib,
            'browser_network_and_boot_prerequisites_passed':all(checks.values()),
            'prerequisite_checks':checks,
            'valid_real_qemu_frames':frames,
            'actual_external_webpage_visually_verified':False,
            'physical_wifi_credential_roaming_verified':False,
            'host_machine_total_ram_not_measured':True,
            'status':'EVIDENCE_NEEDS_VISUAL_INSPECTION' if all(checks.values()) else 'INCOMPLETE_OR_FAILED',
            'notes':'External website is not proven solely from typing, HTTPS curl or a nonblank framebuffer.'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--evidence',type=Path,required=True)
    p.add_argument('--ram',type=int,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    result=audit(a.evidence,a.ram)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='valid_real_qemu_frames'},indent=2))
if __name__=='__main__':main()
