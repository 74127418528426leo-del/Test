import lzma
import os
import tempfile
import unittest
from pathlib import Path
from module_unpack import unpack_modules

class ModuleUnpackTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def make(self,name,data):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(lzma.compress(data));return p
    def test_replaces_compressed_modules_with_exact_uncompressed_bytes(self):
        first=self.make('usr/lib/modules/kern/a.ko.xz',b'\x7fELFalpha')
        second=self.make('usr/lib/modules/kern/sub/b.ko.xz',b'\x7fELFbeta')
        os.chmod(first,0o640);other=self.root/'usr/lib/modules/kern/modules.dep';other.write_text('unchanged')
        report=unpack_modules(self.root)
        self.assertFalse(first.exists());self.assertFalse(second.exists())
        self.assertEqual(first.with_suffix('').read_bytes(),b'\x7fELFalpha')
        self.assertEqual(second.with_suffix('').read_bytes(),b'\x7fELFbeta')
        self.assertEqual(first.with_suffix('').stat().st_mode & 0o777,0o640)
        self.assertEqual(other.read_text(),'unchanged');self.assertEqual(report['files'],2)
    def test_corrupt_module_aborts_before_any_original_is_changed(self):
        first=self.make('a.ko.xz',b'\x7fELFvalid');bad=self.root/'z.ko.xz';bad.write_bytes(b'bad-xz')
        before=first.read_bytes()
        with self.assertRaises(ValueError):unpack_modules(self.root)
        self.assertEqual(first.read_bytes(),before);self.assertEqual(bad.read_bytes(),b'bad-xz')
        self.assertFalse(first.with_suffix('').exists())
    def test_refuses_existing_output_and_non_elf_module(self):
        src=self.make('x.ko.xz',b'\x7fELFdata');target=src.with_suffix('');target.write_bytes(b'original')
        with self.assertRaises(ValueError):unpack_modules(self.root)
        self.assertEqual(target.read_bytes(),b'original');target.unlink()
        src.write_bytes(lzma.compress(b'not-elf'))
        with self.assertRaises(ValueError):unpack_modules(self.root)
        self.assertTrue(src.exists())
    def test_rejects_symlinked_module_and_root(self):
        src=self.make('a.ko.xz',b'\x7fELFdata');(self.root/'b.ko.xz').symlink_to(src)
        with self.assertRaises(ValueError):unpack_modules(self.root)
        with self.assertRaises(ValueError):unpack_modules(Path('/'))

if __name__=='__main__':unittest.main()
