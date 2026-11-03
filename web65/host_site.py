#!/usr/bin/env python3
"""Serve a deterministic real webpage on the QEMU host's loopback interface.
QEMU user networking exposes the host loopback server as 10.0.2.2.
No external network, no certificate bypass, no guest-specific QEMU shortcuts.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

COLOR=(203,45,145)
PAGE=b"""<!doctype html><html><head><meta charset="utf-8"><title>Puppy50 V65 Remote Website</title>
<style>html,body{margin:0;min-height:100vh;background:rgb(203,45,145)!important;color:white!important;font:30px Arial,sans-serif;}
h1{font-size:52px;padding:60px 50px 0}</style></head>
<body><h1>REMOTE HOST WEBPAGE CONFIRMED</h1>
<p style="padding:24px 50px">Real HTTP page served from the QEMU host across the virtual Ethernet network.</p>
<script>document.documentElement.setAttribute('data-remote-page-js','executed')</script>
</body></html>"""

def make_handler(log):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path!="/v65":
                self.send_error(404)
                return
            with log.open("a") as out:
                out.write(f"V65_HOST_ACCEPTED_BROWSER_GET path={self.path} client={self.client_address[0]}\n")
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(PAGE)))
            self.send_header("Cache-Control","no-store")
            self.end_headers()
            self.wfile.write(PAGE)
        def log_message(self, fmt, *args):
            pass
    return Handler

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port",type=int,default=8000)
    ap.add_argument("--log",type=Path,required=True)
    a=ap.parse_args()
    a.log.parent.mkdir(parents=True,exist_ok=True)
    # QEMU's built-in alias 10.0.2.2 connects to the host's loopback.
    with ThreadingHTTPServer(("127.0.0.1",a.port),make_handler(a.log)) as server:
        server.serve_forever()
if __name__=="__main__":
    main()
