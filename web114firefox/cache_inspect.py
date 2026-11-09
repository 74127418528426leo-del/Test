#!/usr/bin/env python3
"""List startup-cache index keys without accessing any profile database."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

MAGIC = b'startupcache0002\0'


def inspect_cache(raw):
    if not raw.startswith(MAGIC) or len(raw) < len(MAGIC) + 4:
        raise ValueError('Unexpected startup-cache magic')
    pos = len(MAGIC)
    size, = struct.unpack_from('<I', raw, pos)
    pos += 4
    end = pos + size
    if end > len(raw):
        raise ValueError('Truncated startup-cache index')
    payload_len = len(raw) - end
    next_offset = 0
    keys = []
    while pos < end:
        if end - pos < 14:
            raise ValueError('Truncated startup-cache entry')
        offset, compressed, uncompressed, name_len = struct.unpack_from('<IIIH', raw, pos)
        pos += 14
        if name_len < 1 or pos + name_len > end or offset != next_offset or compressed == 0 or uncompressed == 0 or offset + compressed > payload_len:
            raise ValueError('Invalid startup-cache entry')
        try:
            key = raw[pos:pos + name_len].decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValueError('Invalid startup-cache key') from exc
        if key in keys or '\0' in key:
            raise ValueError('Duplicate or invalid startup-cache key')
        keys.append(key)
        pos += name_len
        next_offset += compressed
    if pos != end or next_offset != payload_len or not keys:
        raise ValueError('Unexpected startup-cache payload')
    return {'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw), 'entries':len(keys), 'keys':keys}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('file',type=Path)
    args=parser.parse_args()
    print(json.dumps(inspect_cache(args.file.read_bytes()),indent=2))


if __name__ == '__main__':
    main()
