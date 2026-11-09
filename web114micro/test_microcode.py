import struct
import unittest
from microcode import select_intel_records, replace_newc_file


def record(sig, rev=1, payload=2000):
    data=bytes((i*13+7)%256 for i in range(payload))
    assert payload%4==0
    total=48+payload
    words=[1,rev,0x01012024,sig,0,1,0xff,payload,total,0,0,0]
    checksum=(-sum(words)-sum(struct.unpack('<'+str(payload//4)+'I',data)))&0xffffffff
    words[4]=checksum
    return struct.pack('<12I',*words)+data

def cpio(entries):
    out=bytearray()
    for name,data in entries+[('TRAILER!!!',b'')]:
        n=name.encode()+b'\0';vals=[1,0o100644,0,0,1,0,len(data),0,0,0,0,len(n),0]
        out.extend(b'070701'+b''.join(f'{x:08x}'.encode() for x in vals))
        out.extend(n);out.extend(b'\0'*((-len(out))%4));out.extend(data);out.extend(b'\0'*((-len(out))%4))
    out.extend(b'\0'*((-len(out))%512));return bytes(out)

def extended_record(primary,alternate):
    base=bytearray(record(primary));words=list(struct.unpack_from('<12I',base))
    words[8]=3072;words[4]=0
    data=base[48:];words[4]=(-sum(words)-sum(struct.unpack('<500I',data)))&0xffffffff
    alt_flags=words[6];alt_sum=(words[3]+words[6]+words[4]-alternate-alt_flags)&0xffffffff
    entries=struct.pack('<3I',alternate,alt_flags,alt_sum)
    ext=[1,0,0,0,0];ext[1]=(-sum(ext)-sum(struct.unpack('<3I',entries)))&0xffffffff
    return struct.pack('<12I',*words)+data+struct.pack('<5I',*ext)+entries+b'\0'*(1024-32)

class MicrocodeTests(unittest.TestCase):
    def test_retains_every_patch_for_both_intel_i3_540_steppings(self):
        a,b,c,d=record(0x20652,1),record(0x20655,2),record(0x306a9,3),record(0x20652,4)
        selected,report=select_intel_records(a+c+b+d,{0x20652,0x20655})
        self.assertEqual(selected,a+b+d)
        self.assertEqual(report['records_kept'],3)
        self.assertEqual(report['signatures_kept'],['0x00020652','0x00020655'])
    def test_rejects_corrupt_or_truncated_microcode_and_absent_stepping(self):
        a=record(0x20652);b=record(0x20655)
        for data,wanted in [(a+b[:-1],{0x20652}),(a[:-1]+b'\0'+b,{0x20652}), (a,{0x20652,0x20655})]:
            with self.assertRaises(ValueError):select_intel_records(data,wanted)
    def test_keeps_a_patch_when_i3_signature_is_in_valid_extended_table(self):
        a=extended_record(0x306a9,0x20652);b=record(0x20655)
        selected,_=select_intel_records(a+b,{0x20652,0x20655});self.assertEqual(selected,a+b)
        damaged=bytearray(a+b);damaged[2050]^=1
        with self.assertRaises(ValueError):select_intel_records(bytes(damaged),{0x20652,0x20655})
    def test_accepts_checksummed_nonzero_header_metadata_used_by_newer_intel_updates(self):
        a=bytearray(record(0x306a9));words=list(struct.unpack_from('<12I',a))
        words[10]=0x100015b;words[4]=0
        words[4]=(-sum(words)-sum(struct.unpack('<500I',a[48:])))&0xffffffff
        a[:48]=struct.pack('<12I',*words)
        b,c=record(0x20652),record(0x20655)
        selected,_=select_intel_records(bytes(a)+b+c,{0x20652,0x20655})
        self.assertEqual(selected,b+c)
    def test_replaces_exact_cpio_entry_without_changing_other_entries(self):
        old=cpio([('a',b'small'),('kernel/x86/microcode/GenuineIntel.bin',record(0x20652)+record(0x20655)),('z',b'end')])
        reduced=record(0x20655)
        new=replace_newc_file(old,'kernel/x86/microcode/GenuineIntel.bin',reduced)
        self.assertEqual(new,cpio([('a',b'small'),('kernel/x86/microcode/GenuineIntel.bin',reduced),('z',b'end')]))
        self.assertEqual(len(new)%512,0)
    def test_rejects_ambiguous_missing_and_malformed_cpio(self):
        target='kernel/x86/microcode/GenuineIntel.bin';data=record(0x20652)
        for archive in (cpio([('a',data)]),cpio([(target,data),(target,data)]),b'invalid'):
            with self.assertRaises(ValueError):replace_newc_file(archive,target,data)

if __name__=='__main__':unittest.main()
