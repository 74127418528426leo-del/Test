#!/usr/bin/env python3
"""Serve one temporary test video with Range support and a nonce page."""

import argparse
import html
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


class FixtureHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_HEAD(self):
        self.serve(False)

    def do_GET(self):
        self.serve(True)

    def respond(self, status, content_type, length, extra=()):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(length))
        self.send_header('Cache-Control', 'no-store')
        for key, value in extra:
            self.send_header(key, value)
        self.end_headers()

    def serve(self, body):
        request = urlsplit(self.path)
        if request.path == '/after.html':
            supplied = parse_qs(request.query).get('nonce', [])
            if supplied != [self.server.nonce]:
                self.respond(403, 'text/plain', 0)
                return
            message = f'<!doctype html><title>RAM test</title><h1>AFTER EJECT {html.escape(self.server.nonce)}</h1>\n'.encode()
            self.respond(200, 'text/html; charset=utf-8', len(message))
            if body:
                self.wfile.write(message)
            return
        if request.path != '/fixture.mp4' or not self.server.fixture.is_file():
            self.respond(404, 'text/plain', 0)
            return
        length = self.server.fixture.stat().st_size
        start, end, status = 0, length - 1, 200
        range_header = self.headers.get('Range')
        if range_header:
            match = re.fullmatch(r'bytes=(\d*)-(\d*)', range_header.strip())
            if not match or not length or (not match.group(1) and not match.group(2)):
                self.respond(416, 'text/plain', 0, [('Content-Range', f'bytes */{length}')])
                return
            if not match.group(1):
                suffix = int(match.group(2))
                start = max(0, length - suffix)
            else:
                start = int(match.group(1))
                end = min(length - 1, int(match.group(2))) if match.group(2) else length - 1
            if start >= length or start > end:
                self.respond(416, 'text/plain', 0, [('Content-Range', f'bytes */{length}')])
                return
            status = 206
        headers = [('Accept-Ranges', 'bytes')]
        if status == 206:
            headers.append(('Content-Range', f'bytes {start}-{end}/{length}'))
        self.respond(status, 'video/mp4', max(0, end - start + 1), headers)
        if body:
            try:
                with self.server.fixture.open('rb') as stream:
                    stream.seek(start)
                    remaining = end - start + 1
                    while remaining:
                        data = stream.read(min(1024 * 1024, remaining))
                        if not data:
                            break
                        self.wfile.write(data)
                        remaining -= len(data)
            except (BrokenPipeError, ConnectionResetError):
                pass


def make_server(host, port, fixture, nonce):
    if not re.fullmatch(r'[A-Z0-9-]{5,50}', nonce):
        raise ValueError('A unique uppercase nonce is required')
    server = ThreadingHTTPServer((host, port), FixtureHandler)
    server.fixture = Path(fixture)
    server.nonce = nonce
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--nonce', required=True)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    make_server('127.0.0.1', args.port, args.fixture, args.nonce).serve_forever()
