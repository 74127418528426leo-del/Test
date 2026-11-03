import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest

SUPERVISOR=Path(__file__).resolve().parents[1]/"bridge_supervisor.py"
BRIDGE=Path(__file__).resolve().parents[2]/"web66"/"host_https_bridge.py"

def unused_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1",0))
        return s.getsockname()[1]

def wait_status(path,generation=1,deadline=8):
    end=time.monotonic()+deadline
    while time.monotonic()<end:
        try:
            data=json.loads(path.read_text())
            if data.get("generation",0)>=generation and data.get("ready"):return data
        except (OSError,ValueError):pass
        time.sleep(.12)
    raise AssertionError("No bridge status for generation "+str(generation))

def port_open(port):
    with socket.socket() as s:
        s.settimeout(.3)
        return s.connect_ex(("127.0.0.1",port))==0

class HostBridgeRecoveryTests(unittest.TestCase):
    def test_unowned_port_refused(self):
        port=unused_port()
        with socket.socket() as s:
            s.bind(("127.0.0.1",port))
            s.listen(1)
            with tempfile.TemporaryDirectory() as d:
                cmd=[sys.executable,str(SUPERVISOR),
                     "--bridge-script",str(BRIDGE),
                     "--status",str(Path(d)/"status.json"),
                     "--log",str(Path(d)/"bridge.log"),
                     "--port",str(port)]
                r=subprocess.run(cmd,capture_output=True,text=True,timeout=5)
                self.assertNotEqual(r.returncode,0)
                self.assertIn("already occupied",r.stderr)

    def test_self_heals_but_does_not_serve_http_or_private_targets(self):
        port=unused_port()
        with tempfile.TemporaryDirectory() as d:
            status=Path(d)/"status.json"
            log=Path(d)/"bridge.log"
            command=[sys.executable,"-u",str(SUPERVISOR),
                     "--bridge-script",str(BRIDGE),"--status",str(status),
                     "--log",str(log),"--port",str(port),"--max-restarts","4"]
            parent=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            last=None
            try:
                first=wait_status(status)
                self.assertTrue(port_open(port))
                self.assertEqual(first["supervisor_pid"],parent.pid)
                with socket.create_connection(("127.0.0.1",port),timeout=2) as client:
                    client.sendall(b"CONNECT 127.0.0.1:443 HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
                    self.assertIn(b"403",client.recv(1500))
                # This simulates an unexpected bridge crash; the supervisor
                # must restart it without altering the VM or host network.
                os.kill(first["bridge_pid"],signal.SIGKILL)
                last=wait_status(status,generation=2,deadline=10)
                self.assertNotEqual(first["bridge_pid"],last["bridge_pid"])
                self.assertTrue(port_open(port))
                self.assertIsNone(parent.poll())
            finally:
                if parent.poll() is None:parent.terminate()
                try:out,_=parent.communicate(timeout=6)
                except subprocess.TimeoutExpired:
                    parent.kill();out,_=parent.communicate(timeout=3)
            self.assertIn("PUPPY50_V80_BRIDGE_CLEANUP=PASS",out)
            self.assertFalse(status.exists())
            for _ in range(20):
                if not port_open(port):break
                time.sleep(.1)
            self.assertFalse(port_open(port),"Bridge must close when VM launcher/supervisor exits")

if __name__=="__main__":unittest.main()
