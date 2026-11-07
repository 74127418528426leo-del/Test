import unittest
from stage_boot_patch import patch_helpers, patch_main

class BootPatchTests(unittest.TestCase):
    def test_only_root_squashfs_uses_staged_mapper_and_fallback_is_kept(self):
        old='get_backing_device ()\n{\n\techo $(setup_loop "${1}" \'0\' "${2}")\n}\n'
        result=patch_helpers(old)
        self.assertIn('p50_backing_device ()',result)
        self.assertIn('/run/live/medium/live/filesystem.squashfs)',result)
        self.assertIn('setup_loop "${1}" \'0\' "${2}"',result)
        self.assertIn('p50-staged-root',result)
        self.assertIn('${TORAM:-}',result)
        self.assertNotIn('echo $(setup_loop "${1}" \'0\' "${2}")',result)
    def test_requires_one_original_hook(self):
        with self.assertRaises(ValueError): patch_helpers('no matching function')
        line='echo $(setup_loop "${1}" \'0\' "${2}")'
        with self.assertRaises(ValueError): patch_helpers(line+'\n'+line)
    def test_adds_graphical_service_only_for_demand_boot(self):
        result=patch_main('abc\n\tFstab\n\tNetbase\n')
        self.assertIn('${TORAM:-}',result)
        self.assertIn('graphical.target.wants/p50-staged-migration.service',result)
        self.assertIn('/run/p50-stage/tools',result)
        self.assertIn('\n\tFstab\n\tNetbase\n',result)
    def test_rejects_missing_or_duplicate_service_location(self):
        with self.assertRaises(ValueError): patch_main('Fstab\n')
        with self.assertRaises(ValueError): patch_main('\n\tFstab\n\tNetbase\n\tFstab\n\tNetbase\n')

if __name__=='__main__': unittest.main()
