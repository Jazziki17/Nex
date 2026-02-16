"""Generate Nex app icon — dark circle with "N" glyph."""

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).parent.parent / "desktop" / "resources"
SIZE = 1024


def generate_icon():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark circle background with subtle gradient feel
    cx, cy, r = SIZE // 2, SIZE // 2, SIZE // 2 - 20

    # Outer glow ring
    for i in range(8, 0, -1):
        alpha = int(15 * i)
        draw.ellipse(
            [cx - r - i * 3, cy - r - i * 3, cx + r + i * 3, cy + r + i * 3],
            fill=(100, 200, 255, alpha),
        )

    # Main dark circle
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(15, 15, 25, 255))

    # Inner subtle ring
    ring_width = 3
    draw.ellipse(
        [cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10],
        outline=(80, 180, 255, 120),
        width=ring_width,
    )

    # "N" glyph — try system font, fall back to default
    font_size = int(SIZE * 0.48)
    font = None
    for font_name in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        try:
            font = ImageFont.truetype(font_name, font_size)
            break
        except (OSError, IOError):
            continue

    if font is None:
        font = ImageFont.load_default()

    # Draw "N" centered
    text = "N"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = cx - tw // 2 - bbox[0]
    ty = cy - th // 2 - bbox[1]

    # Subtle text glow
    for offset in range(4, 0, -1):
        alpha = int(40 * offset)
        draw.text(
            (tx, ty), text, font=font, fill=(100, 200, 255, alpha),
            stroke_width=offset * 2, stroke_fill=(100, 200, 255, alpha),
        )

    # Main text
    draw.text((tx, ty), text, font=font, fill=(220, 240, 255, 255))

    # Save PNG
    png_path = OUTPUT_DIR / "icon.png"
    img.save(str(png_path), "PNG")
    print(f"Saved {png_path}")

    # Generate .icns using macOS iconutil
    generate_icns(png_path)


def generate_icns(png_path: Path):
    """Convert PNG to .icns via iconutil."""
    iconset_dir = tempfile.mkdtemp(suffix=".iconset")
    iconset = Path(iconset_dir)

    sizes = [16, 32, 64, 128, 256, 512]
    img = Image.open(str(png_path))

    for s in sizes:
        # Standard
        resized = img.resize((s, s), Image.LANCZOS)
        resized.save(str(iconset / f"icon_{s}x{s}.png"))
        # @2x (Retina)
        s2 = s * 2
        if s2 <= 1024:
            resized2 = img.resize((s2, s2), Image.LANCZOS)
            resized2.save(str(iconset / f"icon_{s}x{s}@2x.png"))

    icns_path = OUTPUT_DIR / "icon.icns"
    result = subprocess.run(
        ["iconutil", "-c", "icns", iconset_dir, "-o", str(icns_path)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"Saved {icns_path}")
    else:
        print(f"iconutil failed: {result.stderr}")

    # Cleanup
    import shutil
    shutil.rmtree(iconset_dir, ignore_errors=True)


if __name__ == "__main__":
    generate_icon()
