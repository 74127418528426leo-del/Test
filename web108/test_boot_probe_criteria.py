import unittest

from boot_bench_fast import missing_required_probe


class HttpsProbeCriteriaTests(unittest.TestCase):
    def test_online_reference_still_requires_guest_ca_probe(self):
        self.assertTrue(missing_required_probe('online', False, False, False))
        self.assertFalse(missing_required_probe('online', False, False, True))

    def test_explicit_no_startup_probe_mode_allows_missing_probe(self):
        self.assertFalse(missing_required_probe('online', False, True, False))

    def test_offline_and_intentionally_blocked_runs_do_not_require_probe(self):
        self.assertFalse(missing_required_probe('offline', False, False, False))
        self.assertFalse(missing_required_probe('online', True, False, False))


if __name__ == '__main__':
    unittest.main()
