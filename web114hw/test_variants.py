import unittest

from variants import variant


SOURCE = """cmd = ['qemu-system-x86_64', '-m', str(args.ram), '-smp', '2', '-drive', cd]
cmd += ['-device', 'qemu-xhci,id=xhci', '-device', 'usb-storage,drive=livecd,id=bootusb,bootindex=1']
time.sleep(.05 if args.select_fullram_fallback and not result['fullram_fallback_selected'] else .8)
"""


class VariantTests(unittest.TestCase):
    def test_four_cpu_variant_preserves_usb_and_enables_two_threads_per_core(self):
        text = variant(SOURCE, 'cpu')
        self.assertIn("'-smp', '4,sockets=1,cores=2,threads=2'", text)
        self.assertIn('qemu-xhci,id=xhci', text)
        self.assertIn('else .2)', text)

    def test_ehci_variant_preserves_cpu_and_attaches_boot_disk_to_ehci(self):
        text = variant(SOURCE, 'ehci')
        self.assertIn("'-smp', '2'", text)
        self.assertIn('usb-ehci,id=ehci', text)
        self.assertIn('id=bootusb,bootindex=1,bus=ehci.0', text)

    def test_control_is_unchanged_except_polling(self):
        text = variant(SOURCE, 'control')
        self.assertIn("'-smp', '2'", text)
        self.assertIn('qemu-xhci,id=xhci', text)
        self.assertIn('else .2)', text)

    def test_malformed_source_and_unknown_mode_fail_closed(self):
        for mode in ('cpu', 'ehci', 'control'):
            with self.assertRaises(ValueError):
                variant('bad source', mode)
        with self.assertRaises(ValueError):
            variant(SOURCE, 'unknown')


if __name__ == '__main__':
    unittest.main()
