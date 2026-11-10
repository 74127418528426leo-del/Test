#!/usr/bin/env python3
"""Validate diagnostic seed, pre-session validity and non-root Firefox opens."""
import argparse,json,re
from pathlib import Path

def require(condition,message):
 if not condition:raise ValueError(message)

def verify(serial,manifest,dirs,result):
 s=serial.replace('\r',''); lines=s.splitlines();wanted={}
 for line in manifest.splitlines():
  m=re.fullmatch(r'([0-9a-f]{64})  ([a-zA-Z0-9_.-]+-le64\.cache-9)',line)
  require(m is not None,'invalid cache manifest');name=m.group(2);require(name not in wanted,'duplicate cache');wanted[name]=m.group(1)
 require(bool(wanted),'empty manifest')
 marks=('P50_FONT_BEFORE_INIT_BEGIN','P50_FONT_VALIDITY_BEGIN','P50_FONT_VALIDITY_RC 0','P50_FONT_VALIDITY_END','P50_FONT_BEFORE_INIT_END','P50_FONT_TRACE_READY','P50_FONT_FIREFOX_CACHE_OPEN','P50_FONT_TRACE_END')
 positions=[s.find(m) for m in marks];require(all(x>=0 for x in positions) and positions==sorted(positions),'missing or out-of-order proof markers')
 for label in ('BEFORE','AFTER'):
  actual={}
  for line in lines:
   if not line.startswith('P50_FONT_'+label+' '):continue
   parts=line.split();require(len(parts)==4,'malformed hash pair');_,name,source,dest=parts
   require(name not in actual and source==dest,'changed cache bytes');actual[name]=source
  require(actual==wanted,'seed mismatch or missing cache')
 valid=s[positions[1]:positions[3]]
 expected=[x for x in dirs.splitlines() if x]
 require(bool(expected),'no expected font directories')
 for directory in expected:require(directory+': skipping, existing cache is valid' in valid,'font cache not valid for '+directory)
 require('caching, new cache contents' not in valid,'fontconfig regenerated a cache')
 events=[]
 for line in lines:
  if not line.startswith('P50_FONT_ACCESS\t'):continue
  parts=line.split('\t');require(len(parts)==6,'malformed cache access')
  _,stamp,pid,uid,comm,path=parts
  require(stamp.isdigit() and pid.isdigit() and uid.isdigit() and path.startswith('/var/cache/fontconfig/'),'invalid access')
  events.append({'uid':int(uid),'comm':comm,'name':path.rsplit('/',1)[-1]})
 firefox=[e for e in events if e['uid']==1000 and e['comm']=='firefox-esr' and e['name'] in wanted]
 require(bool(firefox),'no nonroot Firefox open of verified cache')
 footer=[line for line in lines if line.startswith('P50_FONT_TRACE_END ')]
 require(len(footer)==1 and re.fullmatch(r'P50_FONT_TRACE_END \d+ 0 0',footer[0]) is not None,'incomplete/overflowed trace')
 require(int(footer[0].split()[1])==len(events),'trace count mismatch')
 seen=result.get('serial_marker_first_seen_seconds',{}).get('P50_FONT_FIREFOX_CACHE_OPEN');home=result.get('first_home_seen_seconds')
 require(isinstance(seen,(int,float)) and isinstance(home,(int,float)) and seen<=home,'Firefox cache open not observed before first home')
 return {'expected_cache_files':len(wanted),'expected_directories':len(expected),'cache_open_events':len(events),'firefox_cache_opens':len(firefox),'firefox_open_seen_seconds':seen,'first_home_seconds':home,'interpretation':'Diagnostic only; fanotify shows opens, not cache parsing or causal speedup.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('serial',type=Path);p.add_argument('manifest',type=Path);p.add_argument('dirs',type=Path);p.add_argument('result',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
 report=verify(a.serial.read_text(),a.manifest.read_text(),a.dirs.read_text(),json.loads(a.result.read_text()));a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
