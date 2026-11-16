#!/usr/bin/env python3
"""Koi leaps out of the ink scroll -- make.fun ai-excited-01 entry.

Renders one 1024x1024 image to <output>/entry.png. The koi photograph
(entry.png, shipped in this repository) is mounted as the painting on an
unrolling Japanese ink scroll: dark indigo wash, rice-paper panel, wooden
rollers, gold speed lines, ink splashes and a red seal stamp, with a short
line of text addressed to the judge.

Only the standard library + Pillow are used. No network. The render is
fully deterministic: a fixed random seed, fixed fonts, fixed JPEG quality
steps, no timestamps -- two runs produce byte-identical output.

After writing, the program verifies its own output fail-fast (exists,
<= 1 MiB, <= 1024x1024, valid JPEG/PNG magic bytes, fully decodable,
not blank, not a byte copy of the source photo) and exits nonzero with a
clear message on any failure.
"""

import argparse
import hashlib
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

# --- limits from RULES.txt -------------------------------------------------
MAX_BYTES = 1_048_576          # 1 MiB
MAX_SIDE = 1024                # pixels
OUT_NAME = "entry.png"

# --- artwork constants ------------------------------------------------------
SIZE = 1024                    # canvas is square, 1024 x 1024
SEED = 20261117                # fixed seed: the render must be deterministic
INK_TOP = (13, 21, 38)         # deep indigo, top of the wash
INK_BOTTOM = (27, 47, 74)      # deep indigo, bottom of the wash
PAPER = (245, 239, 224)        # warm rice paper
PAPER_EDGE = (214, 196, 158)   # aged paper edge
VERMILION = (196, 30, 28)      # seal red / border red
GOLD = (212, 175, 55)          # gold leaf
WOOD = (122, 82, 42)           # scroll roller wood
WOOD_DARK = (84, 54, 26)
TITLE = "ONE LEAP"
SUBTITLE = "OUT OF THE INK."


def fail(message):
    """Print a clear failure and exit nonzero (fail-fast)."""
    print("ERROR: " + message, file=sys.stderr)
    sys.exit(1)


def output_dir():
    """Where entry.png goes: --output, $MAKEFUN_OUTPUT_DIR, /output, else out/."""
    env = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env:
        return env
    if os.path.isdir("/output"):
        return "/output"
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "out")


def load_font(size, bold=True):
    """Best available font at the requested size; never crashes the render."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def vertical_gradient(size, top, bottom):
    """A smooth top-to-bottom wash, drawn one row at a time."""
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)
    for y in range(size):
        t = y / max(size - 1, 1)
        colour = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (size, y)], fill=colour)
    return img


def add_paper_grain(img, rng, dots=2600):
    """Faint light/dark speckle so the wash reads as paper, not plastic."""
    draw = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    for _ in range(dots):
        x = rng.randrange(w)
        y = rng.randrange(h)
        shade = rng.choice([(255, 255, 255, 14), (0, 0, 0, 18)])
        draw.point((x, y), fill=shade)
    return img


def build_scroll_panel(koi, rng):
    """Rice-paper panel holding the koi photo, tilted as if mid-unroll.

    Returns an RGBA layer the caller pastes onto the canvas.
    """
    panel_side = 800
    panel = Image.new("RGBA", (panel_side, panel_side), PAPER + (255,))
    draw = ImageDraw.Draw(panel)
    # Aged edge: a darker inset frame, then the vermilion hairline.
    draw.rectangle([0, 0, panel_side - 1, panel_side - 1],
                   outline=PAPER_EDGE, width=10)
    draw.rectangle([14, 14, panel_side - 15, panel_side - 15],
                   outline=VERMILION, width=4)
    # The koi photo, centre-cropped square and inset inside the frame.
    photo = koi.copy()
    side = min(photo.size)
    photo = photo.crop(((photo.width - side) // 2, (photo.height - side) // 2,
                        (photo.width + side) // 2, (photo.height + side) // 2))
    photo = photo.resize((panel_side - 72, panel_side - 72), Image.LANCZOS)
    panel.paste(photo, (36, 36))
    # Ink splashes escaping the photo's corners, as if the fish just burst out.
    splash = ImageDraw.Draw(panel, "RGBA")
    for _ in range(26):
        cx = rng.randrange(30, panel_side - 30)
        cy = rng.randrange(30, panel_side - 30)
        # Keep splashes near the edges so the koi stays clean.
        if 90 < cx < panel_side - 90 and 90 < cy < panel_side - 90:
            continue
        r = rng.randrange(2, 11)
        splash.ellipse([cx - r, cy - r, cx + r, cy + r],
                       fill=(20, 20, 26, rng.randrange(120, 220)))
    # Red seal stamp, bottom right of the panel.
    seal = 74
    sx, sy = panel_side - seal - 34, panel_side - seal - 34
    draw.rectangle([sx, sy, sx + seal, sy + seal], fill=VERMILION)
    draw.rectangle([sx + 6, sy + 6, sx + seal - 6, sy + seal - 6],
                   outline=(255, 255, 255), width=2)
    font = load_font(30, bold=True)
    draw.text((sx + seal // 2, sy + seal // 2), "KOI",
              font=font, fill=(255, 255, 255), anchor="mm")
    return panel.rotate(-2.0, resample=Image.BICUBIC, expand=False)


def draw_roller(draw, x0, y, x1, height):
    """One wooden scroll roller with end caps."""
    draw.rounded_rectangle([x0, y, x1, y + height], radius=height // 2,
                           fill=WOOD)
    draw.rounded_rectangle([x0, y + height // 4, x1, y + height // 2],
                           radius=height // 8, fill=WOOD_DARK)
    for cx in (x0 + 14, x1 - 14):
        draw.ellipse([cx - 12, y - 4, cx + 12, y + height + 4],
                     fill=WOOD_DARK, outline=GOLD, width=2)


def draw_speed_lines(draw, rng):
    """Gold motion lines fanning out from behind the panel, top-left."""
    cx, cy = 512, 430
    for _ in range(26):
        angle = rng.uniform(-2.6, -0.5)  # fan across the upper-left sky
        length = rng.uniform(120, 330)
        spread = rng.uniform(0.6, 1.0)
        x2 = cx + length * spread * math.cos(angle)
        y2 = cy + length * spread * math.sin(angle)
        draw.line([(cx, cy), (x2, y2)], fill=GOLD + (rng.randrange(60, 150),),
                  width=rng.choice([2, 3, 4]))


def draw_ink_strokes(draw, rng):
    """A few bold black brush strokes sweeping in from the right edge."""
    for _ in range(5):
        y0 = rng.randrange(120, 900)
        x0 = rng.randrange(820, 1000)
        x1 = x0 + rng.randrange(20, 90)
        y1 = y0 + rng.randrange(-70, 70)
        draw.line([(x0, y0), (x1, y1)], fill=(8, 8, 12, 200),
                  width=rng.choice([10, 14, 18, 24]))
        # A spray of droplets trailing each stroke.
        for _ in range(8):
            dx = rng.randrange(-30, 60)
            dy = rng.randrange(-30, 30)
            r = rng.randrange(1, 5)
            draw.ellipse([x1 + dx - r, y1 + dy - r, x1 + dx + r, y1 + dy + r],
                         fill=(8, 8, 12, 160))


def centered_text(draw, y, text, font, fill):
    """Draw text horizontally centred at the given y."""
    draw.text((SIZE // 2, y), text, font=font, fill=fill, anchor="ma")


def render(koi_path):
    """Compose the full 1024x1024 scene and return it as an RGB image."""
    rng = random.Random(SEED)
    try:
        koi = Image.open(koi_path).convert("RGB")
    except (OSError, IOError) as exc:
        fail("cannot open source koi image %r: %s" % (koi_path, exc))

    canvas = vertical_gradient(SIZE, INK_TOP, INK_BOTTOM)
    canvas = add_paper_grain(canvas, rng)
    draw = ImageDraw.Draw(canvas, "RGBA")

    draw_speed_lines(draw, rng)

    # A thin gold halo behind the panel: the burst the fish leaps out of.
    draw.ellipse([92, 130, 932, 970], outline=GOLD + (200,), width=5)
    draw.ellipse([104, 142, 920, 958], outline=GOLD + (110,), width=2)

    # The scroll panel, tilted -2 degrees, centred slightly low so the
    # title has room above it.
    panel = build_scroll_panel(koi, rng)
    canvas.paste(panel, (112, 150), panel)

    # Wooden rollers above and below the panel: the scroll itself.
    draw_roller(draw, 150, 108, 874, 30)
    draw_roller(draw, 150, 922, 874, 30)

    draw_ink_strokes(draw, rng)

    # Title above, subtitle below -- the line addressed to the judge.
    title_font = load_font(92, bold=True)
    centered_text(draw, 6, TITLE, title_font, GOLD + (255,))
    sub_font = load_font(44, bold=True)
    centered_text(draw, 956, SUBTITLE, sub_font, (245, 239, 224, 255))

    return canvas.convert("RGB")


def save_within_limit(img, path):
    """Save as JPEG (named entry.png, as the rules allow) under the 1 MiB cap.

    Steps the quality down deterministically until the file fits.
    """
    for quality in (92, 88, 84, 80, 75, 70, 65, 60):
        img.save(path, format="JPEG", quality=quality, optimize=True,
                 progressive=False)
        size = os.path.getsize(path)
        if size <= MAX_BYTES:
            return size, quality
    fail("output still %d bytes at quality 60, over the %d-byte cap"
         % (os.path.getsize(path), MAX_BYTES))


def verify(path, source_path):
    """Fail-fast checks on the written file. Returns (bytes, sha256)."""
    if not os.path.isfile(path):
        fail("output file missing: %s" % path)
    size = os.path.getsize(path)
    if size == 0:
        fail("output file is empty: %s" % path)
    if size > MAX_BYTES:
        fail("output is %d bytes, over the %d-byte cap" % (size, MAX_BYTES))
    with open(path, "rb") as fh:
        head = fh.read(8)
    is_jpeg = head[:2] == b"\xff\xd8"
    is_png = head[:8] == b"\x89PNG\r\n\x1a\n"
    if not (is_jpeg or is_png):
        fail("output has unknown magic bytes %r (not PNG or JPEG)" % head)
    try:
        with Image.open(path) as img:
            img.load()  # decode every tile: a truncated file fails here
            width, height = img.size
            mode = img.mode
            # Not-blank check: a real scene has real pixel variance.
            small = img.convert("L").resize((64, 64))
            pixels = list(small.tobytes())  # one byte per pixel, L mode
            mean = sum(pixels) / len(pixels)
            variance = sum((p - mean) ** 2 for p in pixels) / len(pixels)
    except Exception as exc:  # corrupt / truncated image data
        fail("output is not a decodable image: %s" % exc)
    if width > MAX_SIDE or height > MAX_SIDE:
        fail("output is %dx%d, over the %dx%d cap" % (width, height, MAX_SIDE, MAX_SIDE))
    if variance < 25:
        fail("output looks blank (pixel variance %.1f)" % variance)
    with open(path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    if source_path and os.path.isfile(source_path):
        with open(source_path, "rb") as fh:
            source_digest = hashlib.sha256(fh.read()).hexdigest()
        if digest == source_digest:
            fail("output is byte-identical to the source photo; "
                 "the render must transform it")
    print("VERIFY OK: %s (%s, %dx%d, %s, %d bytes, sha256 %s)"
          % (path, "JPEG" if is_jpeg else "PNG", width, height, mode,
             size, digest[:16]))
    return size, digest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=None,
                        help="output directory (default: $MAKEFUN_OUTPUT_DIR, "
                             "/output, or ./out)")
    parser.add_argument("--verify-only", default=None, metavar="PATH",
                        help="only verify an existing file, do not render")
    args = parser.parse_args(argv)

    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")

    if args.verify_only:
        verify(args.verify_only, source)
        return 0

    out_dir = args.output or output_dir()
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        fail("cannot create output directory %r: %s" % (out_dir, exc))
    out_path = os.path.join(out_dir, OUT_NAME)

    image = render(source)
    size, quality = save_within_limit(image, out_path)
    print("RENDER OK: %s (%dx%d, JPEG quality %d, %d bytes)"
          % (out_path, SIZE, SIZE, quality, size))
    verify(out_path, source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
