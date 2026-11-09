import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent

class ResidentProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.bin=Path(cls.temp.name)/'p50-resident'
        subprocess.run(['gcc','-O2','-Wall','-Wextra','-Werror','-o',str(cls.bin),str(HERE/'resident.c')],check=True)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_records_bounded_page_aligned_resident_intervals(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'payload';p.write_bytes(os.urandom(524288))
            r=subprocess.run([str(self.bin),str(p)],text=True,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
            lines=r.stdout.splitlines();head=lines[0].split('\t')
            self.assertEqual(head[:2],['P50_FILE',str(p)])
            size,page=int(head[2]),int(head[3]);self.assertEqual(size,524288)
            self.assertGreater(page,0)
            intervals=[]
            for row in lines[1:]:
                m=re.fullmatch(r'RANGE\t(\d+)\t(\d+)',row);self.assertIsNotNone(m,row)
                start,length=map(int,m.groups());self.assertEqual(start%page,0)
                self.assertGreater(length,0);self.assertLessEqual(start+length,((size+page-1)//page)*page)
                intervals.append((start,length))
            self.assertTrue(intervals)
            self.assertTrue(all(a[0]+a[1]<=b[0] for a,b in zip(intervals,intervals[1:])))
    def test_missing_and_empty_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'empty';p.touch()
            self.assertNotEqual(subprocess.run([str(self.bin),str(p)],capture_output=True).returncode,0)
            self.assertNotEqual(subprocess.run([str(self.bin),str(p)+'-missing'],capture_output=True).returncode,0)

if __name__=='__main__':unittest.main()
