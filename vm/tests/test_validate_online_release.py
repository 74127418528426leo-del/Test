import importlib.util,json,tempfile,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"validate_online_release.py"
spec=importlib.util.spec_from_file_location("release_gate",p)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class PublicReleaseGateTests(unittest.TestCase):
    def setup_files(self,folder):
        d=Path(folder)
        iso=d/"online.iso"
        with iso.open("wb") as f:
            f.truncate(1*1048576)
            f.seek(16*2048+1);f.write(b"CD001")
        frame=d/"frame_310.ppm";frame.write_bytes(b"P6 1920 1080 255\n"+b"X"*15)
        guest=d/"guest.json"
        guest.write_text(json.dumps({k:True for k in
         ("real_RAM_root_and_CD_ejection","guest_DHCP","guest_DNS",
          "guest_strict_CA_HTTPS","offline_Firefox_input",
          "external_URL_keypress_submitted","host_bridge_guest_TLS")}))
        review=d/"review.json"
        review.write_text(json.dumps({
            "reviewed_screenshot":True,
            "public_website_actually_visible_in_firefox":True,
            "firefox_HTTPS_URL_confirmed":True,
            "iso_sha256":mod.digest(iso),
            "screenshot_sha256":mod.digest(frame)}))
        return iso,guest,review,frame
    def test_valid_reviewed_proof(self):
        with tempfile.TemporaryDirectory() as d:
            iso,guest,review,frame=self.setup_files(d)
            self.assertTrue(mod.validate(iso,guest,review,frame)["actual_1gib_Firefox_public_website_visible"])
    def test_no_guest_ca_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            iso,guest,review,frame=self.setup_files(d)
            x=json.loads(guest.read_text());x["guest_strict_CA_HTTPS"]=False;guest.write_text(json.dumps(x))
            with self.assertRaises(ValueError):mod.validate(iso,guest,review,frame)
    def test_unreviewed_image_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            iso,guest,review,frame=self.setup_files(d)
            x=json.loads(review.read_text());x["reviewed_screenshot"]=False;review.write_text(json.dumps(x))
            with self.assertRaises(ValueError):mod.validate(iso,guest,review,frame)
    def test_wrong_image_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            iso,guest,review,frame=self.setup_files(d)
            frame.write_bytes(b"tampered")
            with self.assertRaises(ValueError):mod.validate(iso,guest,review,frame)
if __name__=="__main__":unittest.main()
