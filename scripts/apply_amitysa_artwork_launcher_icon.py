from pathlib import Path
import re
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

SOURCE = Path("app/src/main/res/drawable-nodpi/amity_logo.jpg")
if not SOURCE.is_file():
    raise SystemExit(f"Approved AmitySA home artwork not found: {SOURCE}")

# Use the exact same source image as the loading/home screen. Keep the complete
# landscape artwork visible; a softly blurred extension fills the square icon.
with Image.open(SOURCE) as opened:
    artwork = opened.convert("RGB")
    canvas_size = 1024
    background = ImageOps.fit(artwork, (canvas_size, canvas_size), method=Image.Resampling.LANCZOS)
    background = background.filter(ImageFilter.GaussianBlur(radius=30))
    background = ImageEnhance.Brightness(background).enhance(0.34)

    foreground = ImageOps.contain(artwork, (canvas_size - 32, canvas_size - 32), method=Image.Resampling.LANCZOS)
    x = (canvas_size - foreground.width) // 2
    y = (canvas_size - foreground.height) // 2
    background.paste(foreground, (x, y))
    master = background

density_sizes = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
resource_roots = [p for p in Path("app/src").glob("*/res") if p.is_dir()]
if not resource_roots:
    raise SystemExit("No Android resource directories found")

for res in resource_roots:
    for density, size in density_sizes.items():
        folder = res / f"mipmap-{density}"
        folder.mkdir(parents=True, exist_ok=True)
        icon = master.resize((size, size), Image.Resampling.LANCZOS)
        icon.save(folder / "ic_launcher.png", format="PNG", optimize=True)
        icon.save(folder / "ic_launcher_round.png", format="PNG", optimize=True)
        # Remove stale raster variants that could conflict with the new PNG.
        for stale in ("ic_launcher.jpg", "ic_launcher.webp", "ic_launcher_round.jpg", "ic_launcher_round.webp"):
            candidate = folder / stale
            if candidate.exists():
                candidate.unlink()

    # Remove old adaptive launcher XML definitions so Android cannot continue
    # displaying an outdated foreground asset.
    for folder in res.glob("mipmap-anydpi*"):
        for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
            candidate = folder / name
            if candidate.exists():
                candidate.unlink()

for manifest in Path("app/src").glob("*/AndroidManifest.xml"):
    text = manifest.read_text(encoding="utf-8")
    app_match = re.search(r"<application\\b[^>]*>", text, flags=re.DOTALL)
    if not app_match:
        continue
    tag = app_match.group(0)
    tag = re.sub(r'\\s+android:icon="[^"]*"', "", tag)
    tag = re.sub(r'\\s+android:roundIcon="[^"]*"', "", tag)
    tag = tag[:-1] + ' android:icon="@mipmap/ic_launcher" android:roundIcon="@mipmap/ic_launcher_round">'
    text = text[:app_match.start()] + tag + text[app_match.end():]
    manifest.write_text(text, encoding="utf-8")

print("Launcher icon and round icon now use the exact approved AmitySA home/loading artwork.")
print(f"Generated density assets in {len(resource_roots)} resource set(s).")
