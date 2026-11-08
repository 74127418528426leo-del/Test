import unittest
from guard_profile import instrument

class GuardProfileTests(unittest.TestCase):
    def test_records_available_needed_and_unchanged_reserve_before_the_check(self):
        original='step\n[ "$mem_k" -ge $((need_k + 393216)) ] || fail \'insufficient available memory and reserve\'\nafter\n'
        result=instrument(original)
        self.assertIn('P50_V113_GUARD_AVAILABLE_KIB=$mem_k NEED_KIB=$need_k RESERVE_KIB=393216',result)
        self.assertIn('[ "$mem_k" -ge $((need_k + 393216)) ]',result)
        self.assertLess(result.index('P50_V113_GUARD_AVAILABLE_KIB'),result.index('[ "$mem_k" -ge'))
    def test_rejects_missing_repeated_or_already_instrumented_guard(self):
        guard='[ "$mem_k" -ge $((need_k + 393216)) ] || fail \'insufficient available memory and reserve\'\n'
        for bad in ('bad',guard+guard,'P50_V113_GUARD_AVAILABLE_KIB\n'+guard):
            with self.assertRaises(ValueError):instrument(bad)

if __name__=='__main__':unittest.main()
