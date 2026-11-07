import unittest
from boot_bench_staged import migration_status, should_select_fallback

class ReadyMarkerTests(unittest.TestCase):
    def test_waits_until_the_explicit_ready_marker(self):
        self.assertEqual(migration_status('P50_STAGE_START\nP50_STAGE_COPY_VERIFIED\n'), 'pending')
        self.assertEqual(migration_status('P50_STAGE_START\nP50_STAGE_READY\n'), 'ready')
    def test_any_failure_wins_over_a_ready_marker(self):
        self.assertEqual(migration_status('P50_STAGE_FAILED: hash\nP50_STAGE_NOT_READY\n'), 'failed')
        self.assertEqual(migration_status('P50_STAGE_FAILED: hash\nP50_STAGE_READY\n'), 'failed')
    def test_fallback_is_selected_once_only_when_default_menu_is_visible(self):
        self.assertTrue(should_select_fallback(True,'default',False))
        self.assertFalse(should_select_fallback(False,'default',False))
        self.assertFalse(should_select_fallback(True,'recovery',False))
        self.assertFalse(should_select_fallback(True,'default',True))
    def test_partial_or_misleading_markers_are_not_ready(self):
        self.assertEqual(migration_status('P50_STAGE_NOT_READY\n'), 'failed')
        self.assertEqual(migration_status('P50_STAGE_READY_PARTIAL\n'), 'pending')

if __name__=='__main__':unittest.main()
