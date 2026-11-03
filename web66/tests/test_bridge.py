import importlib.util
import socket
import tempfile
import threading
import unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"host_https_bridge.py"
spec=importlib.util.spec_from_file_location("bridge",p)
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)

class BridgeSafetyTests(unittest.TestCase):
    def test_reject_loopback_destination(self):
        with self.assertRaises(ValueError):
            bridge.resolve_public("127.0.0.1",443)
    def test_reject_non_tls_port(self):
        with self.assertRaises(ValueError):
            bridge.resolve_public("example.com",22)
    def test_server_refuses_private_connect(self):
        with bridge.ThreadServer(("127.0.0.1",0),bridge.HostHTTPSProxy) as s:
            thread=threading.Thread(target=s.serve_forever,daemon=True)
            thread.start()
            with socket.create_connection(s.server_address,timeout=3) as c:
                c.sendall(b"CONNECT 127.0.0.1:443 HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
                data=c.recv(2048)
            s.shutdown()
            self.assertIn(b"403",data)
    def test_server_refuses_http_get(self):
        with bridge.ThreadServer(("127.0.0.1",0),bridge.HostHTTPSProxy) as s:
            t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
            with socket.create_connection(s.server_address,timeout=3) as c:
                c.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
                data=c.recv(2048)
            s.shutdown()
            self.assertIn(b"405",data)

if __name__=="__main__":
    unittest.main()
