import unittest
import panorama_probe

class PanoramaProbeTests(unittest.TestCase):
    def test_injects_keyboard_after_screenshot(self):
        marker="                    result['screenshots'].append('requested_site.png')\n"
        out=panorama_probe.patch(marker)
        self.assertIn('P50_PANORAMA_KEY_PROBE',out)
        self.assertIn("['right']",out)
        self.assertLess(out.index(marker),out.index('P50_PANORAMA_KEY_PROBE'))
    def test_rejects_wrong_or_duplicate_marker(self):
        marker="                    result['screenshots'].append('requested_site.png')\n"
        for src in ('absent',marker+marker):
            with self.assertRaises(ValueError):panorama_probe.patch(src)

if __name__=='__main__':unittest.main()
