import unittest
import site_probe

class SiteProbeTests(unittest.TestCase):
    def test_injects_after_public_https_frame(self):
        marker = "                    result['screenshots'].append('external_https.png')\n"
        result = site_probe.patch(marker)
        self.assertIn('P50_V112_OPTIONAL_SITE_PROBE', result)
        self.assertIn("os.environ['P50_TEST_URL']", result)
        self.assertLess(result.index(marker), result.index('P50_V112_OPTIONAL_SITE_PROBE'))

    def test_rejects_missing_or_duplicate_markers(self):
        marker = "                    result['screenshots'].append('external_https.png')\n"
        for original in ('missing', marker + marker):
            with self.assertRaises(ValueError):
                site_probe.patch(original)

if __name__ == '__main__': unittest.main()
