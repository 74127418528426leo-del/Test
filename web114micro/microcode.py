#!/usr/bin/env python3
"""Build a strictly validated, CPU-specific test microcode archive.

The result is test-only: other Intel processors require the unchanged fallback.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

TARGET='kernel/x86/microcode/GenuineIntel.bin'
SIGNATURES={0x00020652,0x00020655}

def wordsum(data):
    if len(data)%4:raise ValueError('Unaligned microcode checksum region')
    return sum(x[0] for x in struct.iter_unpack('<I',data))&0xffffffff

def select_intel_records(blob,wanted):
    if not blob or not wanted:raise ValueError('Empty microcode or requested signatures')
    pos=0;kept=[];matched=set();total=0
    while pos<len(blob):
        if len(blob)-pos<48:raise ValueError('Truncated microcode header')
        h=struct.unpack_from('<12I',blob,pos)
        version,rev,date,sig,checksum,loader,flags,dsize,tsize,*reserved=h
        if version!=1 or loader!=1 or any(reserved):raise ValueError('Unknown Intel record header')
        if dsize==0 and tsize==0:dsize,tsize=2000,2048
        if dsize%4 or tsize%1024 or tsize<48+dsize or pos+tsize>len(blob):raise ValueError('Invalid Intel record size')
        raw=blob[pos:pos+tsize];main=raw[:48+dsize]
        if wordsum(main)!=0:raise ValueError('Bad Intel microcode checksum')
        signatures={sig}
        if len(raw)>len(main):
            extra=raw[len(main):]
            if len(extra)<20 or wordsum(extra)!=0:raise ValueError('Invalid extended signature checksum')
            count,_,r1,r2,r3=struct.unpack_from('<5I',extra)
            if any((r1,r2,r3)) or 20+12*count>len(extra):raise ValueError('Invalid extended signature count')
            if any(extra[20+12*count:]):raise ValueError('Nonzero extended table padding')
            for i in range(count):
                esig,eflags,esum=struct.unpack_from('<3I',extra,20+i*12)
                if (esig+eflags+esum-sig-flags-checksum)&0xffffffff:raise ValueError('Bad extended signature entry')
                signatures.add(esig)
        hits=signatures&wanted
        if hits:kept.append(raw);matched.update(hits)
        pos+=tsize;total+=1
    if matched!=wanted:raise ValueError('Microcode missing requested signatures: '+str(sorted(wanted-matched)))
    result=b''.join(kept)
    return result,{'original_bytes':len(blob),'selected_bytes':len(result),'records_total':total,'records_kept':len(kept),'signatures_kept':[f'0x{x:08x}' for x in sorted(matched)],'original_sha256':hashlib.sha256(blob).hexdigest(),'selected_sha256':hashlib.sha256(result).hexdigest()}

def replace_newc_file(archive,target,replacement):
    if not target or target.startswith('/') or '..' in target.split('/'):raise ValueError('Invalid archive target')
    out=bytearray();pos=0;matches=0;finished=False;target_offset=None
    while pos<len(archive):
        start=pos
        if len(archive)-pos<110 or archive[pos:pos+6]!=b'070701':raise ValueError('Invalid newc header')
        header=archive[pos:pos+110];pos+=110
        try:fields=[int(header[6+i*8:14+i*8],16) for i in range(13)]
        except ValueError as e:raise ValueError('Invalid newc field') from e
        size,namesize=fields[6],fields[11]
        if namesize<1 or pos+namesize>len(archive):raise ValueError('Invalid newc name')
        name_bytes=archive[pos:pos+namesize]
        if name_bytes[-1:]!=b'\0' or b'\0' in name_bytes[:-1]:raise ValueError('Invalid newc name terminator')
        name=name_bytes[:-1].decode('utf-8');pos+=namesize;pos=(pos+3)&~3
        if pos+size>len(archive):raise ValueError('Truncated newc payload')
        old_payload=archive[pos:pos+size];end=(pos+size+3)&~3
        if end>len(archive):raise ValueError('Truncated newc alignment')
        if name==target:
            matches+=1;target_offset=pos
            header=header[:54]+f'{len(replacement):08x}'.encode()+header[62:]
            out.extend(header);out.extend(archive[start+110:pos]);out.extend(replacement);out.extend(b'\0'*((-len(out))%4))
        else:out.extend(archive[start:end])
        pos=end
        if name=='TRAILER!!!':finished=True;break
    if not finished or matches!=1 or any(archive[pos:]):raise ValueError('Missing trailer, nonzero padding, or ambiguous target')
    if target_offset is None:raise ValueError('Target missing')
    out.extend(b'\0'*((-len(out))%512))
    return bytes(out)

def main():
    p=argparse.ArgumentParser();p.add_argument('intel_archive',type=Path);p.add_argument('intel_blob',type=Path);p.add_argument('output',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
    if any(f.resolve()==a.output.resolve() for f in (a.intel_archive,a.intel_blob)):raise ValueError('Output would overwrite input')
    blob=a.intel_blob.read_bytes();selected,report=select_intel_records(blob,SIGNATURES)
    new=replace_newc_file(a.intel_archive.read_bytes(),TARGET,selected)
    a.output.write_bytes(new);a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
