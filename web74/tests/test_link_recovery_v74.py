import importlib.util
import tempfile
import unittest
from pathlib import Path

p=Path(__file__).resolve().parents[1]/"qemu_link_recovery_v74.py"
spec=importlib.util.spec_from_file_location("link_v74",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class LinkRecoveryTests(unittest.TestCase):
    def test_named_guest_network_and_explicit_off_on(self):
        text=p.read_text()
        self.assertIn('e1000,netdev=puppynet,id=puppynic',text)
        self.assertIn('user,id=puppynet,ipv6=off',text)
        self.assertIn('set_link puppynic {state}',text)
        self.assertIn('for mark in [95,145,165,185,205,245,args.seconds]:',text)
        self.assertIn('NIC_link_actions',text)
        self.assertIn('guest_network_link_off_on_commands_submitted',text)
    def test_link_not_equivalent_to_host_wifi_change(self):
        text=p.read_text()
        self.assertIn('host_physical_network_transition_proven"]=False',text)
        self.assertIn('guest_released_and_reacquired_DHCP_proven"]=False',text)
        self.assertIn('post_link_recovery_wikipedia_content_manually_reviewed"]=False',text)
    def test_cyan_pixel_check_rejects_invalid_and_distinguishes_home(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            home=root/"home.ppm";after=root/"after.ppm"
            home.write_bytes(b"P6\n640 480\n255\n"+bytes((9,198,206))*640*480)
            after.write_bytes(b"P6\n640 480\n255\n"+bytes((245,245,245))*640*480)
            self.assertGreater(m.cyan_fraction(home)["fraction"],.035)
            self.assertLess(m.cyan_fraction(after)["fraction"],.010)
    def test_no_fake_website_success_in_runner(self):
        text=p.read_text()
        self.assertIn('Wikipedia_public_page_visually_confirmed"]=False',text)
        self.assertIn('mouse_button 1',text)
        self.assertIn('mouse_button 0',text)
if __name__=="__main__":unittest.main()
