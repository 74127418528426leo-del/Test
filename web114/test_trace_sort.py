import os
import tempfile
import unittest
from pathlib import Path
from trace_sort import build_sort

class TraceSortTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        for name in ('usr/lib/firefox-esr/libxul.so','usr/lib/firefox-esr/omni.ja','etc/ld.so.cache'):
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode())
        (self.root/'usr/lib/firefox-esr/link.so').symlink_to('libxul.so')
        os.link(self.root/'usr/lib/firefox-esr/omni.ja',self.root/'usr/lib/firefox-esr/hardlink.ja')
        (self.root/'usr/lib/firefox-esr/escape').symlink_to('/etc/passwd')
    def tearDown(self):self.tmp.cleanup()
    def trace(self,lines,footer='P50_ACCESS_END\t7\t0\t0'):
        return '\n'.join(['P50_ACCESS_TRACE_V1','P50_ACCESS_MARK_OK',*lines,footer])+'\n'
    def test_preserves_first_open_order_and_ignores_duplicate_and_transient_paths(self):
        t=self.trace(['EV\t1\t8\t/usr/lib/firefox-esr/link.so','EV\t2\t8\t/usr/lib/firefox-esr/libxul.so','EV\t3\t8\t/tmp/profile','EV\t4\t8\t/usr/lib/firefox-esr/omni.ja','EV\t5\t8\t/usr/lib/firefox-esr/hardlink.ja','EV\t6\t8\t/etc/ld.so.cache','EV\t7\t8\t/usr/lib/firefox-esr/escape'])
        entries,report=build_sort(t,self.root)
        self.assertEqual(entries,[('usr/lib/firefox-esr/libxul.so',32767),('usr/lib/firefox-esr/omni.ja',32766),('etc/ld.so.cache',32765)])
        self.assertEqual(report['kept'],3)
        self.assertTrue(all('passwd' not in name and 'profile' not in name for name,_ in entries))
    def test_rejects_incomplete_overflowed_or_capped_collection(self):
        line='EV\t1\t8\t/usr/lib/firefox-esr/libxul.so'
        for trace in ('P50_ACCESS_TRACE_V1\nP50_ACCESS_MARK_OK\n'+line+'\n',self.trace([line],footer='P50_ACCESS_END\t1\t1\t0'),self.trace([line],footer='P50_ACCESS_END\t1\t0\t1')):
            with self.subTest(trace=trace):
                with self.assertRaises(ValueError):build_sort(trace,self.root)
    def test_rejects_malformed_events_and_mismatched_count(self):
        for trace in (self.trace(['EV\tbogus\t8\t/etc/ld.so.cache'],footer='P50_ACCESS_END\t1\t0\t0'),self.trace(['EV\t1\t8\t/etc/ld.so.cache'],footer='P50_ACCESS_END\t2\t0\t0')):
            with self.subTest(trace=trace):
                with self.assertRaises(ValueError):build_sort(trace,self.root)
    def test_rejects_non_monotonic_trace_and_skips_unsafe_resolved_names(self):
        spaced=self.root/'usr/lib/firefox-esr/name with space';spaced.write_text('x')
        (self.root/'usr/lib/firefox-esr/alias').symlink_to('name with space')
        bad=self.trace(['EV\t5\t8\t/etc/ld.so.cache','EV\t4\t8\t/usr/lib/firefox-esr/libxul.so'],footer='P50_ACCESS_END\t2\t0\t0')
        with self.assertRaises(ValueError):build_sort(bad,self.root)
        good=self.trace(['EV\t1\t8\t/usr/lib/firefox-esr/alias','EV\t2\t8\t/etc/ld.so.cache'],footer='P50_ACCESS_END\t2\t0\t0')
        entries,_=build_sort(good,self.root)
        self.assertEqual(entries,[('etc/ld.so.cache',32767)])
    def test_rejects_dotdot_escape_and_unrepresentable_paths(self):
        t=self.trace(['EV\t1\t8\t/usr/lib/firefox-esr/../../../../etc/passwd','EV\t2\t8\t/usr/lib/firefox-esr/escape','EV\t3\t8\t/etc/ld.so.cache'],footer='P50_ACCESS_END\t3\t0\t0')
        entries,_=build_sort(t,self.root)
        self.assertEqual(entries,[('etc/ld.so.cache',32767)])

if __name__=='__main__':unittest.main()
