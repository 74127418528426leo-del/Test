import unittest
from analyze import analyze_text

FILES=('/usr/lib/firefox-esr/libxul.so','/usr/lib/firefox-esr/omni.ja','/usr/lib/firefox-esr/browser/omni.ja')
def trace():
    lines=['P50_HOT_TRACE_V1']
    for i in range(14):
        lines.append(f'SNAP\t{i}\t{4+i}')
        for name in FILES:lines.extend([f'P50_FILE\t{name}\t8192\t4096','RANGE\t0\t4096'])
        lines.append(f'ENDSNAP\t{i}')
    return '\n'.join(lines+['P50_HOT_TRACE_END'])+'\n'
def result():
    return {'first_home_seen_seconds':15.0,'early_js_response_seconds':18.0,'staged_ram_ready_seconds':35.0,
            'serial_marker_first_seen_seconds':{'P50_HOT_SNAPSHOT_00':10.0,'P50_HOT_SNAPSHOT_01':12.0},
            'early_media_attached_before_navigation':True,'early_media_attached_after_js_response':True,
            'media_ejected':True,'input_sent_after_eject':True,'qemu_running_at_end':True,'errors':[]}

class AnalyzeTests(unittest.TestCase):
    def test_selects_last_host_observed_snapshot_before_home(self):
        summary,lines=analyze_text(trace(),result())
        self.assertEqual(summary['selected_snapshot'],1)
        self.assertEqual(summary['files'][FILES[0]]['cached'],4096)
        self.assertEqual(sum(x.startswith('P50_FILE') for x in lines),3)
    def test_rejects_incomplete_trace_out_of_bounds_and_no_host_marker(self):
        t=trace()
        for bad in (t.replace('P50_HOT_TRACE_END','no'),t.replace('RANGE\t0\t4096','RANGE\t8192\t4096',1)):
            with self.assertRaises(ValueError):analyze_text(bad,result())
        r=result();r['serial_marker_first_seen_seconds']={}
        with self.assertRaises(ValueError):analyze_text(t,r)

if __name__=='__main__':unittest.main()
