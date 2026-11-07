import os
from pathlib import Path
import tempfile
import unittest
from bundle_runtime import copy_runtime_library, parse_ldd

class RuntimeBundleTests(unittest.TestCase):
    def test_dynamic_loader_retains_executable_permissions(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'source-loader';source.write_bytes(b'loader');source.chmod(0o755)
            target=Path(t)/'lib'/'ld-linux-x86-64.so.2';target.parent.mkdir()
            copy_runtime_library(source,target)
            self.assertTrue(os.access(target,os.X_OK));self.assertEqual(target.read_bytes(),b'loader')
    def test_nonexecutable_library_stays_nonexecutable(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'source-lib';source.write_bytes(b'lib');source.chmod(0o644)
            target=Path(t)/'libcopy';copy_runtime_library(source,target)
            self.assertFalse(target.stat().st_mode & 0o111)
    def test_parse_detects_loader_and_dependencies(self):
        parsed=parse_ldd('linux-vdso.so.1 (0x0001)\nlibdevmapper.so.1 => /lib/libdm.so (0x0002)\n/lib64/ld-linux-x86-64.so.2 (0x0003)\n')
        self.assertEqual(parsed,[('libdevmapper.so.1','/lib/libdm.so'),('ld-linux-x86-64.so.2','/lib64/ld-linux-x86-64.so.2')])
    def test_missing_dependency_is_a_hard_error(self):
        with self.assertRaises(ValueError):parse_ldd('libmissing.so => not found\n')

if __name__=='__main__':unittest.main()
