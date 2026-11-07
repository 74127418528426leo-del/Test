import unittest
from boot_bench_demand import media_condition_passed

class MediaConditionTests(unittest.TestCase):
    def test_ram_only_mode_requires_actual_removal_and_input(self):
        self.assertTrue(media_condition_passed(False, True, True))
        self.assertFalse(media_condition_passed(False, False, True))
        self.assertFalse(media_condition_passed(False, True, False))

    def test_experimental_demand_mode_requires_attached_media_and_input(self):
        self.assertTrue(media_condition_passed(True, False, True))
        self.assertFalse(media_condition_passed(True, True, True))
        self.assertFalse(media_condition_passed(True, False, False))

if __name__ == '__main__': unittest.main()
