import importlib.util
import os
import select
import signal
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"vm/host_https_bridge_supervisor_v80.py"
BRIDGE=ROOT/"web66/host_https_bridge.py"
spec=importlib.util.spec_from_file_location("supervisor",P)
sup=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sup)

def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1",0))
        return s.getsockname()[1]

def read_until(proc,needle,timeout=8):
    end=time.monotonic()+timeout
    text=""
    while time.monotonic()<end:
        if proc.poll() is not None:
            raise AssertionError("supervisor exited early: "+text)
        ready,_,_=select.select([proc.stdout],[],[],.25)
        if ready:
            line=proc.stdout.readline()
            text+=line
            if needle in line:return line
    raise AssertionError("Timed out waiting for "+needle+" logs="+text)

class SupervisorTests(unittest.TestCase):
    def test_local_port_must_be_unoccupied(self):
        port=free_port()
        with socket.socket() as s:
            s.bind(("127.0.0.1",port))
            s.listen(1)
            self.assertFalse(sup.port_available(port))
    def test_crashed_child_restarts_and_parent_cleans_up(self):
        port=free_port()
        proc=subprocess.Popen(
            [sys.executable,"-u",str(P),"--bridge",str(BRIDGE),"--port",str(port)],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        try:
            line=read_until(proc,"PUPPY50_BRIDGE_CHILD_PID=")
            first=int(line.split("=")[1].strip())
            read_until(proc,"PUPPY50_BRIDGE_HOST_LOCAL_LISTENER_READY")
            self.assertTrue(sup.listener_present(port))
            os.kill(first,signal.SIGTERM)
            line=read_until(proc,"PUPPY50_BRIDGE_CHILD_PID=",timeout=10)
            second=int(line.split("=")[1].strip())
            self.assertNotEqual(first,second)
            read_until(proc,"PUPPY50_BRIDGE_HOST_LOCAL_LISTENER_READY",timeout=10)
            self.assertTrue(sup.listener_present(port))
        finally:
            proc.terminate()
            try:proc.communicate(timeout=7)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate(timeout=4)
        self.assertTrue(sup.port_available(port))
    def test_no_unknown_proxy_port_adoption(self):
        port=free_port()
        with socket.socket() as s:
            s.bind(("127.0.0.1",port))
            s.listen()
            rc=subprocess.run(
                [sys.executable,str(P),"--bridge",str(BRIDGE),"--port",str(port)],
                capture_output=True,text=True,timeout=5)
        self.assertNotEqual(rc.returncode,0)
        self.assertIn("PUPPY50_BRIDGE_SUPERVISOR_REFUSED",rc.stdout)
    def test_launcher_preserves_signature_and_no_guest_disk(self):
        source=(ROOT/"vm/launch_linux_v80.sh").read_text()
        self.assertIn("sha256sum -c SHA256SUMS",source)
        self.assertIn("host_https_bridge_supervisor_v80.py",source)
        self.assertIn("media=cdrom,readonly=on",source)
        self.assertIn('NIC=(-nic user,model=e1000,ipv6=off)',source)
        self.assertNotIn("--insecure",source)
if __name__=="__main__":unittest.main()
