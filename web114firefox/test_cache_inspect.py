import struct
import unittest
from cache_inspect import inspect_cache


def build(records):
    header = b''
    payload = b''
    for key, content in records:
        key = key.encode()
        header += struct.pack('<IIIH', len(payload), len(content), 2*len(content), len(key)) + key
        payload += content
    return b'startupcache0002\0' + struct.pack('<I', len(header)) + header + payload


class InspectTests(unittest.TestCase):
    def test_reads_only_header_keys_and_validates_offsets(self):
        raw=build([('jsloader/resource://gre/modules/app',b'abc'),('chrome/content/browser',b'defg')])
        result=inspect_cache(raw)
        self.assertEqual(result['entries'], 2)
        self.assertEqual(result['keys'][0], 'jsloader/resource://gre/modules/app')

    def test_rejects_corruption_and_unknown_format(self):
        good=build([('test',b'abc')])
        for value in (b'bad', good[:-1], good[:17]+b'\xff\xff\xff\xff'+good[21:]):
            with self.assertRaises(ValueError): inspect_cache(value)
