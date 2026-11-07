#!/usr/bin/env python3
"""Test-only local CONNECT bridge that records attempted destinations.

The inherited bridge forwards TLS bytes without intercepting or replacing
certificates. This harness only logs the CONNECT authority for these tests.
"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web66.host_https_bridge import HostHTTPSProxy, ThreadServer


class TracingProxy(HostHTTPSProxy):
    def do_CONNECT(self):
        with self.server.connect_log.open('a', encoding='utf-8') as log:
            log.write(self.path + '\n')
        return super().do_CONNECT()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', type=int, default=3128)
    p.add_argument('--connect-log', type=Path, required=True)
    args = p.parse_args()
    with ThreadServer(('127.0.0.1', args.port), TracingProxy) as server:
        server.connect_log = args.connect_log.resolve()
        print('PUPPY50_TRACED_TEST_BRIDGE_LISTENING', flush=True)
        server.serve_forever()
