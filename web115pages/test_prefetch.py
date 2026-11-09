import os
import subprocess
import tempfile
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent

class PrefetchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.bin=Path(cls.tmp.name)/'prefetch'
        subprocess.run(['gcc','-O2','-Wall','-Wextra','-Werror','-o',str(cls.bin),str(HERE/'prefetch.c')],check=True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_reads_selected_extents_and_rejects_size_change(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=root/'file';data.write_bytes(os.urandom(8192));plan=root/'plan'
            plan.write_text(f'P50_FILE\t{data}\t8192\t4096\nRANGE\t0\t4096\n')
            r=subprocess.run([str(self.bin),str(plan)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr);self.assertIn('P50_PREFETCH_BYTES 4096',r.stdout)
            data.write_bytes(b'x')
            r=subprocess.run([str(self.bin),str(plan)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
    def test_rejects_overlapping_out_of_bounds_and_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=root/'file';data.write_bytes(os.urandom(8192));link=root/'link';link.symlink_to(data);plan=root/'plan'
            for path,ranges in ((data,'RANGE\t4096\t8192\n'),(data,'RANGE\t0\t4096\nRANGE\t0\t4096\n'),(link,'RANGE\t0\t4096\n')):
                plan.write_text(f'P50_FILE\t{path}\t8192\t4096\n'+ranges)
                self.assertNotEqual(subprocess.run([str(self.bin),str(plan)],capture_output=True).returncode,0)

if __name__=='__main__':unittest.main()
