#!/usr/bin/env python3
"""Minimal optional host-side HTTPS CONNECT bridge for Puppy50 QEMU.

The guest uses QEMU's 10.0.2.2 loopback alias and this host-only port.
TLS bytes pass unchanged end-to-end; the proxy does not add CAs, intercept
TLS, handle credentials, or relax client certificate validation.
No destinations on loopback/private/link-local/reserved networks.
This is experimental, not a general enterprise proxy or production firewall.
"""
import argparse
import ipaddress
import selectors
import socket
import socketserver
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlsplit

def resolve_public(host,port):
    if not host or not (1<=port<=65535):
        raise ValueError("invalid proxy destination")
    if port not in (443,8443):
        raise ValueError("only HTTPS ports 443 and 8443 allowed")
    answers=socket.getaddrinfo(host,port,type=socket.SOCK_STREAM)
    approved=[]
    for family,socktype,proto,canonname,sockaddr in answers:
        addr=ipaddress.ip_address(sockaddr[0])
        if addr.is_global:
            approved.append((family,socktype,proto,sockaddr))
    if not approved:
        raise ValueError("destination has no public IP")
    return approved

def connect_public(host,port):
    last=None
    for family,stype,proto,address in resolve_public(host,port):
        s=socket.socket(family,stype,proto)
        s.settimeout(10)
        try:
            s.connect(address)
            return s
        except OSError as ex:
            last=ex
            s.close()
    raise OSError(f"public HTTPS connection failed: {last.__class__.__name__ if last else 'unknown'}")

def tunnel(left,right):
    left.settimeout(15)
    right.settimeout(15)
    with selectors.DefaultSelector() as selector:
        selector.register(left,selectors.EVENT_READ,right)
        selector.register(right,selectors.EVENT_READ,left)
        idle_count=0
        while idle_count<45:
            ready=selector.select(timeout=1)
            if not ready:
                idle_count+=1
                continue
            idle_count=0
            for key,_ in ready:
                data=key.fileobj.recv(65536)
                if not data:
                    return
                key.data.sendall(data)

class HostHTTPSProxy(BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def do_CONNECT(self):
        try:
            loc=urlsplit("//"+self.path)
            host=loc.hostname
            port=loc.port or 443
            if loc.username or loc.password or loc.path or loc.query:
                raise ValueError("malformed CONNECT authority")
            upstream=connect_public(host,port)
        except (OSError,ValueError,TypeError) as exc:
            self.send_error(403 if isinstance(exc,ValueError) else 502,"HTTPS target inaccessible")
            return
        try:
            self.connection.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            tunnel(self.connection,upstream)
        except (OSError,TimeoutError):
            return
        finally:
            upstream.close()
        self.close_connection=True

    def do_GET(self):
        self.send_error(405,"HTTPS CONNECT only")
    def do_POST(self):
        self.send_error(405,"HTTPS CONNECT only")
    def log_message(self,format,*args):
        pass

class ThreadServer(socketserver.ThreadingMixIn,socketserver.TCPServer):
    allow_reuse_address=True
    daemon_threads=True

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",type=int,default=3128)
    args=parser.parse_args()
    # Only loopback binding is allowed: QEMU maps guest 10.0.2.2 to host
    # localhost. A LAN-visible unauthenticated proxy would be unsafe.
    with ThreadServer(("127.0.0.1",args.port),HostHTTPSProxy) as server:
        print(f"PUPPY50_HOST_CONNECT_BRIDGE_LISTEN_PORT={args.port}",flush=True)
        server.serve_forever()
if __name__=="__main__":
    main()
