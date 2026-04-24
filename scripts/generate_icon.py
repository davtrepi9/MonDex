"""
Genera l'icona dell'app: Pokeball cyber su sfondo dark.
Crea PNG nelle dimensioni Android (mdpi 48 -> xxxhdpi 192).
"""
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    print("Installa Pillow: pip install Pillow")
    sys.exit(1)


SIZES = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}

OUT_BASE = r"C:\Users\david\Desktop\Api\pokedex_offline\android\app\src\main\res"


def make_icon(size: int) -> Image.Image:
    """Crea Pokeball cyber su sfondo dark."""
    # Base RGBA
    img = Image.new("RGBA", (size, size), (10, 14, 26, 255))  # bgDark cyber
    d = ImageDraw.Draw(img)

    cx = cy = size / 2
    r = size * 0.40  # raggio pokeball

    # Glow esterno (multilayer per simulare bagliore)
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(8, 0, -2):
        alpha = max(8, 80 - i * 8)
        gd.ellipse(
            [cx - r - i, cy - r - i, cx + r + i, cy + r + i],
            outline=(0, 229, 255, alpha),
            width=2,
        )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=size / 32))
    img.paste(glow, (0, 0), glow)

    # Metà superiore: cyan
    d.pieslice(
        [cx - r, cy - r, cx + r, cy + r],
        start=180,
        end=360,
        fill=(0, 229, 255, 255),
        outline=(255, 255, 255, 220),
        width=max(2, size // 64),
    )
    # Metà inferiore: magenta
    d.pieslice(
        [cx - r, cy - r, cx + r, cy + r],
        start=0,
        end=180,
        fill=(255, 31, 143, 255),
        outline=(255, 255, 255, 220),
        width=max(2, size // 64),
    )

    # Linea centrale nera + gradiente
    bar_h = max(3, size // 28)
    d.rectangle([cx - r - 2, cy - bar_h / 2, cx + r + 2, cy + bar_h / 2],
                fill=(10, 14, 26, 255))

    # Bottone centrale: anello bianco + cerchio interno con glow
    btn_r = r * 0.32
    # Outer ring (white)
    d.ellipse([cx - btn_r, cy - btn_r, cx + btn_r, cy + btn_r],
              fill=(255, 255, 255, 255),
              outline=(10, 14, 26, 255),
              width=max(2, size // 48))
    # Inner glow circle
    inner = btn_r * 0.55
    d.ellipse([cx - inner, cy - inner, cx + inner, cy + inner],
              fill=(0, 229, 255, 255))

    # Highlight piccolo bianco in alto-sx (vetro)
    hl_r = r * 0.18
    hx, hy = cx - r * 0.45, cy - r * 0.55
    d.ellipse([hx - hl_r, hy - hl_r * 0.7, hx + hl_r, hy + hl_r * 0.7],
              fill=(255, 255, 255, 80))

    return img


def main():
    if not os.path.exists(OUT_BASE):
        print(f"Cartella res non trovata: {OUT_BASE}")
        return 1

    for density, size in SIZES.items():
        out_dir = os.path.join(OUT_BASE, f"mipmap-{density}")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "ic_launcher.png")
        img = make_icon(size)
        img.save(out_path, "PNG", optimize=True)
        # Round version (alcuni launcher la cercano)
        round_path = os.path.join(out_dir, "ic_launcher_round.png")
        img.save(round_path, "PNG", optimize=True)
        print(f"  {density:8s} {size:3d}px -> {out_path}")

    print("\nIcone generate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
