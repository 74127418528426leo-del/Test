"""Detect the local browser homepage across common framebuffer formats.

Detection is provisional: retain screenshots for visual inspection.
"""
from PIL import Image


def home_visible(image):
    image = image.convert('RGB').resize((160, 100), Image.Resampling.NEAREST)
    colors = ((18, 54, 88), (7, 19, 34), (23, 52, 80))
    counts = [0, 0, 0]
    for pixel in image.getdata():
        for i, target in enumerate(colors):
            if all(abs(pixel[channel] - target[channel]) <= 5 for channel in range(3)):
                counts[i] += 1
    return counts[0] >= 300 and counts[1] >= 1500 and counts[2] >= 300
