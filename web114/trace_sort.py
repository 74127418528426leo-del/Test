#!/usr/bin/env python3
"""Turn a complete guest open trace into a safe, source-relative SquashFS order."""
import argparse
import json
from pathlib import Path, PurePosixPath

PREFIXES=('usr/','etc/','bin/','sbin/','lib/','lib64/')

def build_sort(trace_text, root):
    root=Path(root).resolve(strict=True)
    if not root.is_dir() or root==Path('/'):raise ValueError('Expected an isolated extracted root')
    lines=trace_text.splitlines()
    if len(lines)<3 or lines[0]!='P50_ACCESS_TRACE_V1' or lines[1]!='P50_ACCESS_MARK_OK':
        raise ValueError('Missing complete trace header')
    footer=lines[-1].split('\t')
    if len(footer)!=4 or footer[0]!='P50_ACCESS_END' or not all(x.isdigit() for x in footer[1:]):
        raise ValueError('Missing complete trace footer')
    count,overflow,capped=map(int,footer[1:])
    if overflow or capped or count!=len(lines)-3:raise ValueError('Trace incomplete or event count mismatch')
    entries=[];seen=set();skipped=0;previous=-1
    for line in lines[2:-1]:
        fields=line.split('\t',3)
        if len(fields)!=4 or fields[0]!='EV' or not fields[1].isdigit() or not fields[2].isdigit():
            raise ValueError('Malformed event')
        timestamp=int(fields[1])
        if timestamp<previous:raise ValueError('Non-monotonic trace')
        previous,path=timestamp,fields[3]
        parts=path.split('/')
        if not path.startswith('/') or any(p in ('.','..') for p in parts) or any(c.isspace() or c=='\\' for c in path):
            skipped+=1;continue
        relative=path.lstrip('/')
        if not relative.startswith(PREFIXES):skipped+=1;continue
        candidate=root.joinpath(*PurePosixPath(relative).parts)
        try:
            resolved=candidate.resolve(strict=True);canonical=resolved.relative_to(root)
            canonical_name=canonical.as_posix()
            if not canonical_name.startswith(PREFIXES) or any(c.isspace() or c=='\\' for c in canonical_name):skipped+=1;continue
            if not resolved.is_file():skipped+=1;continue
            st=resolved.stat();identity=(st.st_dev,st.st_ino)
        except (OSError,ValueError,RuntimeError):
            skipped+=1;continue
        if identity in seen:skipped+=1;continue
        if len(entries)>=32767:raise ValueError('Too many unique paths for priority range')
        seen.add(identity);entries.append((canonical.as_posix(),32767-len(entries)))
    return entries,{'events':count,'kept':len(entries),'skipped':skipped,'overflow':overflow,'capped':capped}

def main():
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('root',type=Path);p.add_argument('sort_file',type=Path);p.add_argument('report',type=Path);p.add_argument('--require-firefox',action='store_true');a=p.parse_args()
    entries,report=build_sort(a.trace.read_text(),a.root)
    names={name for name,_ in entries}
    if a.require_firefox and not {'usr/lib/firefox-esr/libxul.so','usr/lib/firefox-esr/omni.ja'}.issubset(names):
        raise ValueError('Trace did not capture required Firefox binary data')
    if not entries:raise ValueError('No eligible paths captured')
    a.sort_file.write_text(''.join(f'{name} {priority}\n' for name,priority in entries))
    a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
