#!/usr/bin/env python3
"""Receive one bounded, isolated-VM-generated Firefox startup-cache seed."""
import argparse
import os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

def make_server(target,host='127.0.0.1',port=8767,max_bytes=32000000):
    target=Path(target)
    if max_bytes<1:raise ValueError('max_bytes must be positive')
    class Handler(BaseHTTPRequestHandler):
        def reply(self,status):self.send_response(status);self.send_header('Content-Length','0');self.end_headers()
        def do_POST(self):
            if self.path!='/cache':self.reply(404);return
            length=self.headers.get('Content-Length','')
            if not length.isdigit() or int(length)<1:self.reply(400);return
            n=int(length)
            if n>max_bytes:self.reply(413);return
            body=self.rfile.read(n)
            if len(body)!=n:self.reply(400);return
            try:fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            except FileExistsError:self.reply(409);return
            with os.fdopen(fd,'wb') as f:f.write(body)
            self.reply(201)
        def log_message(self,fmt,*args):print('cache-receiver',fmt%args,flush=True)
    return ThreadingHTTPServer((host,port),Handler)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--port',type=int,default=8767);a=p.parse_args();make_server(a.output,port=a.port).serve_forever()
if __name__=='__main__':main()
