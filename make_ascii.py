"""Turn a portrait photo into ASCII art for the profile card.

Usage:  python make_ascii.py photo.jpg [cols rows left,top,right,bottom]
Writes ascii_dark.txt / ascii_light.txt (the characters) and shade_dark.txt /
shade_light.txt (one digit 0-9 per character: how strongly build.py draws it).
Shading each character is what makes the face recognisable, like a halftone print.

Dark mode draws light text on a dark card, so bright parts of the photo get dense
characters (a "positive" image). Light mode is the opposite: dark parts get dense
characters. Using one file for both makes one of the two look like a negative.
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
CHAR_ASPECT = 2.08   # glyph height / advance width of a monospace font


def _norm(a, mask, lo_p=1, hi_p=99):
    lo, hi = np.percentile(a[mask], [lo_p, hi_p])
    return np.clip((a - lo) / max(hi - lo, 1e-6), 0, 1)


def convert(path, cols=76, rows=46, crop=None):
    img = Image.open(path).convert("RGB")
    if crop:
        img = img.crop(crop)
    gray = img.convert("L")

    # background = the bright, flat studio wall
    blur = np.asarray(gray.filter(ImageFilter.GaussianBlur(3))).astype(float)
    bg_full = blur > 200

    # one value per character cell, then a light sharpen so glasses, eyes and beard stay crisp
    # (average only the subject's pixels, so the white wall doesn't brighten the hair outline)
    g = np.asarray(gray).astype(float)
    m = (~bg_full).astype(float)
    shrink = lambda a: np.asarray(Image.fromarray(a.astype("float32"), "F").resize((cols, rows), Image.BOX)).astype(float)
    cov = shrink(m)
    avg = np.where(cov > 0, shrink(g * m) / np.maximum(cov, 1e-6), 255)
    small = Image.fromarray(np.clip(avg, 0, 255).astype("uint8"))
    small = small.filter(ImageFilter.UnsharpMask(radius=1.2, percent=70, threshold=0))
    L = np.asarray(small).astype(float)
    subj = cov > 0.4

    bright = _norm(L, subj)
    arts = {}
    for mode, dens in (("dark", bright ** 1.1), ("light", (1 - bright) ** 1.2)):
        floor = 0.3 if mode == "dark" else 0.12   # dark hair must stay visible on the dark card
        chars = floor + (1 - floor) * dens
        lines, shades = [], []
        for r in range(rows):
            line = "".join(
                RAMP[min(int(chars[r, c] * (len(RAMP) - 1)), len(RAMP) - 1)] if subj[r, c] else " "
                for c in range(cols))
            shade = "".join(str(min(int(round(dens[r, c] * 9)), 9)) if subj[r, c] else "0"
                            for c in range(cols))
            lines.append(line.rstrip())
            shades.append(shade[:len(line.rstrip())])
        arts[mode] = ("\n".join(lines), "\n".join(shades))
    return arts


if __name__ == "__main__":
    path = sys.argv[1]
    cols = int(sys.argv[2]) if len(sys.argv) > 2 else 76
    rows = int(sys.argv[3]) if len(sys.argv) > 3 else 46
    crop = tuple(map(int, sys.argv[4].split(","))) if len(sys.argv) > 4 else None
    for mode, (art, shade) in convert(path, cols, rows, crop).items():
        with open(f"ascii_{mode}.txt", "w", encoding="utf-8") as f:
            f.write(art + "\n")
        with open(f"shade_{mode}.txt", "w", encoding="utf-8") as f:
            f.write(shade + "\n")
        print(f"wrote ascii_{mode}.txt and shade_{mode}.txt")
