import unittest
from delay_patch import patch

class DelayPatchTests(unittest.TestCase):
    def test_changes_only_delay(self):
        original='before\n"$B" sleep 8\nemit P50_STAGE_START\nafter\n'
        for seconds in (0,2,4,6):
            self.assertEqual(patch(original,seconds),original.replace('sleep 8','sleep '+str(seconds)))
    def test_rejects_unknown_or_ambiguous_input(self):
        marker='"$B" sleep 8\nemit P50_STAGE_START\n'
        for original,seconds in [('',2),(marker+marker,2),(marker,-1),(marker,7),(marker,8)]:
            with self.assertRaises(ValueError):patch(original,seconds)
if __name__=='__main__':unittest.main()
