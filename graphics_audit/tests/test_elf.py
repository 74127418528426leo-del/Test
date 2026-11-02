import importlib.util
from pathlib import Path
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"elf_dependencies.py"
spec=importlib.util.spec_from_file_location("elfdeps",SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class ElfDepTests(unittest.TestCase):
    def test_extract_needed_filters_other_dynamic_tags(self):
        source=""" 0x0000000000000001 (NEEDED) Shared library: [libLLVM.so.22.1]
 0x0000000000000001 (NEEDED) Shared library: [libc.musl-x86_64.so.1]
 0x000000000000000e (SONAME) Library soname: [libgallium.so]
 """
        self.assertEqual(m.extract_needed(source),
          ["libLLVM.so.22.1","libc.musl-x86_64.so.1"])
    def test_empty_is_not_evidence_safe_to_delete(self):
        self.assertEqual(m.extract_needed("No dynamic section in this file."),[])

if __name__=="__main__":unittest.main()
