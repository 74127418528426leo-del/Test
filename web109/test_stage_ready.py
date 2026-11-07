import unittest
from boot_bench_staged import migration_status

class ReadyMarkerTests(unittest.TestCase):
    def test_waits_until_the_explicit_ready_marker(self):
        self.assertEqual(migration_status('P50_STAGE_START\nP50_STAGE_COPY_VERIFIED\n'), 'pending')
        self.assertEqual(migration_status('P50_STAGE_START\nP50_STAGE_READY\n'), 'ready')
    def test_any_failure_wins_over_a_ready_marker(self):
        self.assertEqual(migration_status('P50_STAGE_FAILED: hash\nP50_STAGE_NOT_READY\n'), 'failed')
        self.assertEqual(migration_status('P50_STAGE_FAILED: hash\nP50_STAGE_READY\n'), 'failed')
    def test_partial_or_misleading_markers_are_not_ready(self):
        self.assertEqual(migration_status('P50_STAGE_NOT_READY\n'), 'failed')
        self.assertEqual(migration_status('P50_STAGE_READY_PARTIAL\n'), 'pending')

if __name__=='__main__':unittest.main()
