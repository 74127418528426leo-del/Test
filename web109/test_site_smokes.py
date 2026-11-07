import unittest
from boot_bench_sites import site_smokes_allowed

class SiteSmokePreconditions(unittest.TestCase):
    def test_sites_require_online_network_and_verified_ram_transition(self):
        self.assertTrue(site_smokes_allowed(True,'online',True))
        self.assertFalse(site_smokes_allowed(True,'offline',True))
        self.assertFalse(site_smokes_allowed(True,'online',False))
    def test_disabled_site_smokes_do_not_constrain_normal_boot_tests(self):
        self.assertTrue(site_smokes_allowed(False,'offline',False))
        self.assertTrue(site_smokes_allowed(False,'online',False))

if __name__=='__main__':unittest.main()
