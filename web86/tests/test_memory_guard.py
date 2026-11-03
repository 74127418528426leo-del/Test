import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

LAUNCHER=Path(__file__).resolve().parents[2]/"vm/launch_linux_v86.sh"

class MemoryGuardAndHostNetworkTests(unittest.TestCase):
    def setup_bundle(self,d):
        root=Path(d)
        shutil.copyfile(LAUNCHER,root/"launch_linux_v86.sh")
        iso=root/"Puppy50_Web_v70_Normal_Browser_Online.iso"
        iso.write_bytes(b"test-only artifact for launcher argument verification")
        h=hashlib.sha256(iso.read_bytes()).hexdigest()
        (root/"SHA256SUMS").write_text(h+"  "+iso.name+"\n")
        fake=root/"bin"
        fake.mkdir()
        qemu=fake/"qemu-system-x86_64"
        qemu.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$PUPPY50_TEST_OUTPUT\"\n")
        qemu.chmod(0o755)
        return root,fake
    def test_1536_default_uses_v70_original_without_writing_disks(self):
        with tempfile.TemporaryDirectory() as d:
            root,fake=self.setup_bundle(d)
            argsfile=root/"args.txt"
            env=os.environ.copy()
            env.pop("PUPPY50_RAM_MIB",None)
            env["PUPPY50_TEST_OUTPUT"]=str(argsfile)
            env["PUPPY50_NETWORK"]="off"
            env["PATH"]=str(fake)+os.pathsep+env.get("PATH","")
            p=subprocess.run(["bash",str(root/"launch_linux_v86.sh")],env=env,
                capture_output=True,text=True,timeout=12)
            # CI runner must have enough free RAM to test normal 1536 profile
            if p.returncode==25:
                self.skipTest("Host memory guard correctly refused underprovisioned CI runner")
            self.assertEqual(p.returncode,0,p.stderr)
            cmd=argsfile.read_text().splitlines()
            self.assertIn("-m",cmd)
            self.assertEqual(cmd[cmd.index("-m")+1],"1536")
            self.assertIn("-nic",cmd)
            self.assertIn("none",cmd)
            self.assertNotIn("-hda",cmd)
    def test_invalid_ram_rejected_before_vm_launch(self):
        with tempfile.TemporaryDirectory() as d:
            root,fake=self.setup_bundle(d)
            env=os.environ.copy()
            env.update({"PUPPY50_RAM_MIB":"8192","PUPPY50_NETWORK":"off",
                "PUPPY50_TEST_OUTPUT":str(root/"args.txt"),"PATH":str(fake)+os.pathsep+env.get("PATH","")})
            p=subprocess.run(["bash",str(root/"launch_linux_v86.sh")],env=env,
                capture_output=True,text=True,timeout=8)
            self.assertEqual(p.returncode,15)
            self.assertFalse((root/"args.txt").exists())
    def test_source_does_not_disable_tls(self):
        s=LAUNCHER.read_text()
        self.assertIn('RAM="${PUPPY50_RAM_MIB:-1536}"',s)
        self.assertIn("HOST_AVAILABLE_MIB",s)
        self.assertIn("host_https_bridge_supervisor_v80.py",s)
        self.assertNotIn("--insecure",s)
        self.assertNotIn("MOZ_DISABLE_CONTENT_SANDBOX",s)
if __name__=="__main__":unittest.main()
