import unittest
from PIL import Image, ImageDraw
from menu_selection import highlighted


class BootMenuDetectionTests(unittest.TestCase):
    def test_distinguishes_default_and_recovery_highlights(self):
        first = Image.new('RGB', (640, 480), 'black')
        ImageDraw.Draw(first).rectangle((100, 248, 575, 262), fill=(113, 147, 181))
        second = Image.new('RGB', (640, 480), 'black')
        ImageDraw.Draw(second).rectangle((100, 264, 575, 278), fill=(113, 147, 181))
        self.assertEqual(highlighted(first), 'default')
        self.assertEqual(highlighted(second), 'recovery')

    def test_black_screen_is_not_a_selected_menu(self):
        self.assertIsNone(highlighted(Image.new('RGB', (640, 480), 'black')))


if __name__ == '__main__':
    unittest.main()
