#!/usr/bin/env python3
"""Temporary local, non-cached browser interaction fixture for QEMU tests."""

import argparse
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = b'''<!doctype html>
<html><head><meta charset="utf-8"><title>Early interaction test</title>
<style>html,body{width:100%;height:100%;margin:0}body{background:rgb(137, 31, 89);color:white;font:24px sans-serif}button{margin:40px;padding:24px;font:24px sans-serif}</style></head>
<body><button id="test" autofocus>Press Enter to test JavaScript</button>
<script>document.getElementById('test').addEventListener('click',function(){
document.body.style.backgroundColor='rgb(17, 169, 83)';
this.textContent='EARLY_JS_RESPONSE';
});</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_GET(self):
        data = PAGE if self.path == '/e' else b'not found\n'
        self.send_response(200 if self.path == '/e' else 404)
        self.send_header('Content-Type', 'text/html; charset=utf-8' if self.path == '/e' else 'text/plain')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        print(f'{time.monotonic():.6f} {self.address_string()} {format % args}', flush=True)


def make_server(host, port):
    return ThreadingHTTPServer((host, port), Handler)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=8766)
    args = p.parse_args()
    make_server('127.0.0.1', args.port).serve_forever()
