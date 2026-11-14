import tempfile
import unittest
from pathlib import Path
import port_staged


class StagedPortTests(unittest.TestCase):
    def test_rejects_old_or_mismatched_live_boot(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'old-main').write_text('old');(p/'new-main').write_text('different')
            with self.assertRaises(ValueError):
                port_staged.port_main((p/'old-main').read_text(),(p/'new-main').read_text())

    def test_preserves_updated_homepage_and_standard_live_boot(self):
        new='prefix\n\tFstab\n\tNetbase\nend\n'
        add=('\n\t# Experimental staged boot: these tools and the service live in RAM.\n'
             '\t\tp50_home="${rootmnt}/usr/share/puppy50web/index.html"\n'
             '\t\t[ -f "${p50_home}" ] || panic "p50: browser home missing"\n'
             '\t\tgrep oldhomepage\n\tfi\n\n\t# P50_V114_OPTIONAL_FONTCACHE\n'
             '\t# P50_V123_BEFORE_PID1: isolated QEMU-only research, unsafe for physical release.\n'
             '\tif [ -z "${TORAM:-}" ] && [ -b /dev/mapper/p50-staged-root ]; then\n\tfi\n')
        old=new.replace('\n\tFstab',add+'\n\tFstab')
        out=port_staged.port_main(old,new)
        self.assertIn('p50: browser home missing',out)
        self.assertNotIn('grep oldhomepage',out)
        self.assertIn('P50_FAST_GPU_GUARD',out)
        self.assertIn('\n\tFstab\n\tNetbase\n',out)


if __name__ == '__main__': unittest.main()
