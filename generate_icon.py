#!/usr/bin/env python3
"""
Generate a macOS .icns icon file for Battery Monitor app.
Uses Pillow to draw a battery icon, then converts via iconutil.
"""

import subprocess
import os
import shutil
from PIL import Image, ImageDraw


def rounded_rectangle(draw, xy, radius, fill):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = [int(v) for v in xy]
    r = min(int(radius), (x1 - x0) // 2, (y1 - y0) // 2)
    if r < 1 or x1 <= x0 or y1 <= y0:
        draw.rectangle([x0, y0, x1, y1], fill=fill)
        return
    # Four corners
    draw.ellipse([x0, y0, x0 + 2 * r, y0 + 2 * r], fill=fill)
    draw.ellipse([x1 - 2 * r, y0, x1, y0 + 2 * r], fill=fill)
    draw.ellipse([x0, y1 - 2 * r, x0 + 2 * r, y1], fill=fill)
    draw.ellipse([x1 - 2 * r, y1 - 2 * r, x1, y1], fill=fill)
    # Two rectangles to fill gaps
    draw.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    draw.rectangle([x0, y0 + r, x1, y1 - r], fill=fill)


def create_battery_icon_png(output_path, size):
    """Create a battery icon PNG at the given size using Pillow."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    s = size / 512.0

    # Background rounded rectangle (green)
    pad = int(40 * s)
    corner = int(80 * s)
    rounded_rectangle(draw, (pad, pad, size - pad, size - pad), corner, '#30D158')

    # Battery body outline
    bx0, by0 = int(145 * s), int(155 * s)
    bx1, by1 = int(367 * s), int(395 * s)
    border_w = max(int(8 * s), 2)

    # Battery terminal (top nub)
    nub_w = int(40 * s)
    nub_h = int(22 * s)
    nub_r = max(int(6 * s), 2)
    ncx = (bx0 + bx1) // 2
    rounded_rectangle(draw,
                      (ncx - nub_w, by0 - nub_h, ncx + nub_w, by0 + nub_r),
                      nub_r, 'white')

    # Battery body (white outline with rounded corners)
    body_r = max(int(16 * s), 3)
    rounded_rectangle(draw, (bx0, by0, bx1, by1), body_r, 'white')

    # Inner cutout (green, to make it look like an outline)
    inner_pad = border_w
    inner_r = max(int(10 * s), 2)
    rounded_rectangle(draw,
                      (bx0 + inner_pad, by0 + inner_pad, bx1 - inner_pad, by1 - inner_pad),
                      inner_r, '#30D158')

    # Battery fill (white, from bottom, ~75%)
    fill_pad = border_w + max(int(4 * s), 1)
    fill_pct = 0.75
    fill_total_h = (by1 - fill_pad) - (by0 + fill_pad)
    fill_h = int(fill_total_h * fill_pct)
    fill_y0 = by1 - fill_pad - fill_h
    fill_y1 = by1 - fill_pad
    fill_r = max(int(6 * s), 1)
    rounded_rectangle(draw, (bx0 + fill_pad, fill_y0, bx1 - fill_pad, fill_y1), fill_r, 'white')

    # Lightning bolt
    cx = (bx0 + bx1) / 2
    bolt = [
        (cx + 8 * s, by0 + 55 * s),
        (cx - 22 * s, by0 + 135 * s),
        (cx - 2 * s, by0 + 128 * s),
        (cx - 12 * s, by0 + 195 * s),
        (cx + 22 * s, by0 + 110 * s),
        (cx + 2 * s, by0 + 118 * s),
    ]
    bolt = [(int(x), int(y)) for x, y in bolt]
    draw.polygon(bolt, fill='#30D158', outline='#28A745')

    img.save(output_path, 'PNG')


def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    iconset_dir = os.path.join(project_dir, 'icon.iconset')
    icns_path = os.path.join(project_dir, 'icon.icns')

    # Create iconset directory
    os.makedirs(iconset_dir, exist_ok=True)

    # Required icon sizes for macOS .icns
    icon_specs = [
        ('icon_16x16.png', 16),
        ('icon_16x16@2x.png', 32),
        ('icon_32x32.png', 32),
        ('icon_32x32@2x.png', 64),
        ('icon_128x128.png', 128),
        ('icon_128x128@2x.png', 256),
        ('icon_256x256.png', 256),
        ('icon_256x256@2x.png', 512),
        ('icon_512x512.png', 512),
        ('icon_512x512@2x.png', 1024),
    ]

    print("🎨 Generating icon images...")
    for filename, size in icon_specs:
        output_path = os.path.join(iconset_dir, filename)
        print(f"  Creating {filename} ({size}x{size})...")
        create_battery_icon_png(output_path, size)

    print("🔧 Converting to .icns...")
    subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', icns_path], check=True)

    # Cleanup iconset
    shutil.rmtree(iconset_dir)

    print(f"✅ Icon created: {icns_path}")


if __name__ == '__main__':
    main()
