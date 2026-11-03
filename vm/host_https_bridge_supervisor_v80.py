#!/usr/bin/env python3
"""Bounded, unprivileged supervisor for Puppy50's localhost-only HTTPS bridge.

The Firefox guest uses the already tested TLS-preserving HTTP CONNECT bridge
at QEMU's 10.0.2.2:3128. The supervisor restarts ITS OWN crashed child only.
It never reads passwords, changes Wi-Fi/VPN/firewall settings or disables TLS.

Security: fail closed if an unknown process owns localhost:<port>. A local
untrusted user could race to bind this static port; this does not provide a
hardened isolation guarantee. Do not use sensitive credentials in this VM.
"""
import argparse
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

STOP=False

def request_stop(_signum,_frame):
    global STOP
    STOP=True

def port_available(port):
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        try:
            sock.bind(("127.0.0.1",port))
            return True
        except OSError:
            return False

def listener_present(port):
    try:
        with socket.create_connection(("127.0.0.1",port),timeout=.35):
            return True
    except OSError:
        return False

def child_shutdown(child):
    if child is None:return
    if child.poll() is not None:return
    child.terminate()
    try:child.wait(timeout=4)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait(timeout=4)

def supervise(bridge,port=3128,max_restarts=4,window=60):
    global STOP
    bridge=Path(bridge).resolve(strict=True)
    if not bridge.is_file():raise ValueError("Host bridge source is not a regular file")
    if not 1024<=port<=65535:raise ValueError("Invalid host-only port")
    if max_restarts<0 or max_restarts>20 or window<1:raise ValueError("Invalid bounded restart policy")
    if not port_available(port):
        raise RuntimeError("Host loopback port is already occupied; refusing unknown proxy")
    child=None
    starts=[]
    try:
        while not STOP:
            now=time.monotonic()
            starts=[x for x in starts if now-x<=window]
            if len(starts)>max_restarts:
                print("PUPPY50_BRIDGE_CRASH_LOOP_FAIL_CLOSED",flush=True)
                return 15
            if not port_available(port):
                print("PUPPY50_UNKNOWN_PROCESS_ON_HTTPS_BRIDGE_PORT_FAIL_CLOSED",flush=True)
                return 16
            child=subprocess.Popen(
                [sys.executable,"-u",str(bridge),"--port",str(port)],
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,close_fds=True)
            starts.append(now)
            print("PUPPY50_BRIDGE_CHILD_PID="+str(child.pid),flush=True)
            healthy=False
            for _ in range(50):
                if STOP:break
                if child.poll() is not None:break
                if listener_present(port):
                    healthy=True;break
                time.sleep(.1)
            if STOP:break
            if not healthy:
                print("PUPPY50_BRIDGE_CHILD_LISTEN_FAILED",flush=True)
                child_shutdown(child)
            else:
                print("PUPPY50_BRIDGE_HOST_LOCAL_LISTENER_READY",flush=True)
                # This is only a local listener check, not evidence of public
                # HTTPS reachability or the guest's certificate verification.
                while not STOP and child.poll() is None:
                    time.sleep(.3)
            if STOP:break
            if child.poll() is None:child_shutdown(child)
            print("PUPPY50_BRIDGE_OWN_CHILD_EXITED_RESTART_ATTEMPT",flush=True)
            time.sleep(.5)
        return 0
    finally:
        child_shutdown(child)
        print("PUPPY50_BRIDGE_SUPERVISOR_CLEAN_EXIT",flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bridge",type=Path,default=Path(__file__).with_name("host_https_bridge.py"))
    ap.add_argument("--port",type=int,default=3128)
    ap.add_argument("--max-restarts",type=int,default=4)
    ap.add_argument("--window-seconds",type=int,default=60)
    a=ap.parse_args()
    signal.signal(signal.SIGINT,request_stop)
    signal.signal(signal.SIGTERM,request_stop)
    try:
        rc=supervise(a.bridge,a.port,a.max_restarts,a.window_seconds)
        return rc
    except (ValueError,OSError,RuntimeError) as exc:
        print("PUPPY50_BRIDGE_SUPERVISOR_REFUSED="+exc.__class__.__name__,flush=True)
        return 17
if __name__=="__main__":
    sys.exit(main())
