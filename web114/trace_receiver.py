#!/usr/bin/env python3
"""Accept one bounded trace from the local QEMU guest during an isolated test."""
import argparse
import os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

def make_server(target,host='127.0.0.1',port=8767,max_bytes=10000000):
    target=Path(target)
    if max_bytes<1:raise ValueError('max_bytes must be positive')
    class Handler(BaseHTTPRequestHandler):
        def finish_response(self,code):
            self.send_response(code);self.send_header('Content-Length','0');self.end_headers()
        def do_POST(self):
            if self.path!='/trace':self.finish_response(404);return
            raw=self.headers.get('Content-Length','')
            if not raw.isdigit() or int(raw)<1:self.finish_response(400);return
            size=int(raw)
            if size>max_bytes:self.finish_response(413);return
            data=self.rfile.read(size)
            if len(data)!=size:self.finish_response(400);return
            try:
                fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            except FileExistsError:self.finish_response(409);return
            with os.fdopen(fd,'wb') as f:f.write(data)
            self.finish_response(201)
        def log_message(self,fmt,*args):print('trace-receiver',fmt%args,flush=True)
    return ThreadingHTTPServer((host,port),Handler)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--port',type=int,default=8767);a=p.parse_args()
    make_server(a.output,port=a.port).serve_forever()

if __name__=='__main__':main()
