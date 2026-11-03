#!/usr/bin/env python3
"""Read-only RAM probe inserted into v70 guest startup, without changing Firefox."""
from pathlib import Path
import argparse,json
ANCHOR_XORG="echo 'PUPPY50_WEB_V45_XORG_START'"
ANCHOR_FF="echo 'PUPPY50_WEB_V45_FIREFOX_REQUESTED'"
def patch(root,probe_source):
    root=Path(root);probe_source=Path(probe_source)
    session=root/'usr/local/bin/puppy50-web-launch'
    probe=root/'usr/local/bin/puppy50-serial-ram-probe'
    if not session.is_file() or not probe_source.is_file():raise ValueError("source files missing")
    source=session.read_text()
    for anchor in (ANCHOR_XORG,ANCHOR_FF):
        if source.count(anchor)!=1:raise ValueError("missing exact tested marker: "+anchor)
    if 'PUPPY50_V89_MEMORY_SAMPLER_STARTED' in source:raise ValueError("already patched")
    start="""if [ -x /usr/local/bin/puppy50-serial-ram-probe ];then
 /usr/local/bin/puppy50-serial-ram-probe pre_xorg >/dev/ttyS0 2>/dev/null || true
fi
"""
    loop="""if [ -x /usr/local/bin/puppy50-serial-ram-probe ];then
 /usr/local/bin/puppy50-serial-ram-probe pre_firefox >/dev/ttyS0 2>/dev/null || true
 (
  n=0
  while [ "$n" -lt 24 ];do
   sleep 15
   /usr/local/bin/puppy50-serial-ram-probe "t_$((n*15+15))" >/dev/ttyS0 2>/dev/null || true
   n=$((n+1))
  done
 ) &
 echo PUPPY50_V89_MEMORY_SAMPLER_STARTED >/dev/ttyS0 2>/dev/null || true
fi
"""
    source=source.replace(ANCHOR_XORG,start+ANCHOR_XORG,1).replace(ANCHOR_FF,loop+ANCHOR_FF,1)
    session.write_text(source);session.chmod(0o755)
    probe.write_bytes(probe_source.read_bytes());probe.chmod(0o755)
    return {'schema':'PUPPY50_V89_READ_ONLY_MEMORY_INSTRUMENTATION',
            'firefox_command_unchanged':True,'security_settings_changed':False,
            'sample_interval_seconds':15,'pre_xorg':True,'pre_firefox':True}
if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    ap.add_argument('--probe',type=Path,default=Path(__file__).with_name('guest_ram_probe.sh'))
    a=ap.parse_args()
    print(json.dumps(patch(a.root,a.probe),indent=2))
