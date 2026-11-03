#!/usr/bin/env python3
"""Read-only host connection check for the Puppy50 QEMU virtual network.
No network credentials are read, printed, changed, stored or forwarded.
The host chooses Wi-Fi/Ethernet/hotspot; QEMU merely uses its existing route.
"""
import os
import socket
import ssl
import sys

def main():
    print("Puppy50 host-network preflight: read-only checks (no settings changed).")
    keys=("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy")
    if any(os.environ.get(k) for k in keys):
        print("Notice: a host HTTP proxy setting is present. The experimental")
        print("localhost bridge uses direct public TCP and does not import proxy credentials.")
    try:
        addrs=socket.getaddrinfo("example.com",443,type=socket.SOCK_STREAM)
        print("Host DNS: PASS (%d candidate endpoints)" % len(addrs))
    except OSError as err:
        print("Host DNS: unavailable (%s)" % err.__class__.__name__)
        print("Connect your HOST computer to a working, authorized network.")
        return 1
    try:
        context=ssl.create_default_context()
        with socket.create_connection(("example.com",443),timeout=5) as sock:
            sock.settimeout(5)
            with context.wrap_socket(sock,server_hostname="example.com") as tls:
                print("Host public HTTPS with certificate validation: PASS (%s)" %
                      tls.version())
                return 0
    except (OSError,ssl.SSLError) as err:
        print("Host direct HTTPS: unavailable (%s)" % err.__class__.__name__)
        print("Check host Wi-Fi/Ethernet/VPN/captive portal/firewall settings.")
        return 2

if __name__=="__main__":
    sys.exit(main())
