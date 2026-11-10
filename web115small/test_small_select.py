import unittest

from small_select import select_earliest

PATHS=('/usr/lib/firefox-esr/libxul.so','/usr/lib/firefox-esr/omni.ja','/usr/lib/firefox-esr/browser/omni.ja')

def fixture(first=4,range_len=8192):
    lines=['P50_HOT_TRACE_V1']
    for i in range(14):
        lines.append(f'SNAP\t{i}\t{i+4}.0')
        for index,path in enumerate(PATHS):
            lines.append(f'P50_FILE\t{path}\t33554432\t4096')
            if index==0 and i>=first:lines.append(f'RANGE\t0\t{range_len}')
        lines.append(f'ENDSNAP\t{i}')
    lines.append('P50_HOT_TRACE_END')
    result={'first_home_seen_seconds':20,'serial_marker_first_seen_seconds':{'P50_HOT_SNAPSHOT_%02d'%i:i+4 for i in range(14)},'early_js_response_seconds':21,'staged_ram_ready_seconds':30,'early_media_attached_before_navigation':True,'early_media_attached_after_js_response':True,'media_ejected':True,'input_sent_after_eject':True,'qemu_running_at_end':True,'errors':[]}
    return '\n'.join(lines)+'\n',result

class SmallSelectTests(unittest.TestCase):
    def test_picks_first_useful_snapshot_and_only_its_bounded_ranges(self):
        trace,result=fixture();plan,summary=select_earliest(trace,result)
        self.assertEqual(summary['selected_snapshot'],4)
        self.assertEqual(summary['total_bytes'],8192)
        self.assertEqual(plan.count('P50_FILE\t'),3)
        self.assertEqual(plan.count('RANGE\t0\t8192'),1)
        self.assertNotIn('SNAP\t',plan)
    def test_rejects_unbounded_plan_and_trace_without_firefox_pages(self):
        trace,result=fixture(range_len=17*1024*1024)
        with self.assertRaises(ValueError):select_earliest(trace,result)
        trace,result=fixture(first=14)
        with self.assertRaises(ValueError):select_earliest(trace,result)
    def test_rejects_incomplete_invalid_or_post_home_snapshot(self):
        trace,result=fixture()
        for bad in (trace.replace('P50_HOT_TRACE_END',''),trace.replace('RANGE\t0\t8192','RANGE\t1\t8192')):
            with self.assertRaises(ValueError):select_earliest(bad,result)
        result['first_home_seen_seconds']=7
        with self.assertRaises(ValueError):select_earliest(trace,result)

if __name__=='__main__':unittest.main()
