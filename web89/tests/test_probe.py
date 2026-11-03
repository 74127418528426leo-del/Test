import importlib.util,os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name):
    s=importlib.util.spec_from_file_location(name,ROOT/(name+'.py'))
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m
class MemoryTests(unittest.TestCase):
    def test_root_patch_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); p=base/'usr/local/bin/puppy50-web-launch'
            p.parent.mkdir(parents=True)
            p.write_text("echo 'PUPPY50_WEB_V45_XORG_START'\necho 'PUPPY50_WEB_V45_FIREFOX_REQUESTED'\n")
            obj=module('instrument_root').patch(base,ROOT/'guest_ram_probe.sh')
            self.assertFalse(obj['security_settings_changed'])
            self.assertIn('PUPPY50_V89_MEMORY_SAMPLER_STARTED',p.read_text())
            with self.assertRaises(ValueError):module('instrument_root').patch(base,ROOT/'guest_ram_probe.sh')
    def test_missing_anchor_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);p=base/'usr/local/bin/puppy50-web-launch';p.parent.mkdir(parents=True)
            p.write_text('other code')
            with self.assertRaises(ValueError):module('instrument_root').patch(base,ROOT/'guest_ram_probe.sh')
    def test_parse_missing_pss(self):
        r=module('analyze_serial').parse_serial('P50MEM phase=t_15 firefox_count=3 firefox_pss_kib=0 firefox_pss_missing=3\n',384)
        self.assertIsNone(r['peak_observed_firefox_pss_mib'])
    def test_memory_numbers_not_guest_allocation(self):
        lines='P50MEM phase=pre_xorg MemAvailable=300000 compressed_root_bytes=156520448 oom_kills=0 firefox_count=0\nP50MEM phase=t_15 MemAvailable=200000 compressed_root_bytes=156520448 oom_kills=1 firefox_count=4 firefox_pss_kib=110592 firefox_pss_missing=0'
        r=module('analyze_serial').parse_serial(lines,384)
        self.assertEqual(r['samples_observed'],2)
        self.assertEqual(r['peak_observed_firefox_pss_mib'],108)
        self.assertAlmostEqual(r['compressed_root_mib'],149.27,places=2)
        self.assertTrue(r['oom_kills_increased'])
    def test_real_shell_against_fake_proc(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/'meminfo').write_text('MemTotal: 393216 kB\nMemAvailable: 150000 kB\n')
            (p/'vmstat').write_text('oom_kill 0\n')
            for pid,ppid,name,pss in [(100,1,'firefox-esr',45000),(101,100,'Web Content',34000),(400,1,'Xorg',12000)]:
                d=p/str(pid);d.mkdir()
                (d/'comm').write_text(name+'\n')
                (d/'status').write_text(f'PPid: {ppid}\n')
                (d/'smaps_rollup').write_text(f'Pss: {pss} kB\nPrivate_Clean: 400 kB\nPrivate_Dirty: 600 kB\nSwap: 0 kB\n')
            s=subprocess.run(['sh',str(ROOT/'guest_ram_probe.sh'),'test'],env={**os.environ,'PUPPY50_PROC_ROOT':str(p)},capture_output=True,text=True,check=True)
            self.assertIn('firefox_count=2',s.stdout)
            self.assertIn('firefox_pss_kib=79000',s.stdout)
if __name__=='__main__':unittest.main()
