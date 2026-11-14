"""Detect a deliberately solid-color test page across framebuffer sizes."""
from PIL import Image


def page_color_visible(image, color):
    image = image.convert('RGB').resize((160, 100), Image.Resampling.NEAREST)
    matching = 0
    for pixel in image.getdata():
        if all(abs(pixel[channel] - color[channel]) <= 5 for channel in range(3)):
            matching += 1
    return matching >= 1500
