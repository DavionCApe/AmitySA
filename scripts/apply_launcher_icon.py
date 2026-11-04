from pathlib import Path
from PIL import Image

ROOT = Path("app/src/main")
SOURCE = Path("branding/amitysa_launcher.jpg")
if not SOURCE.exists():
    raise SystemExit(f"Launcher artwork missing: {SOURCE}")
if not ROOT.exists():
    raise SystemExit(f"Android source folder missing: {ROOT}")

res = ROOT / "res"
res.mkdir(parents=True, exist_ok=True)
densities = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
with Image.open(SOURCE) as original:
    original = original.convert("RGB")
    for density, size in densities.items():
        folder = res / f"mipmap-{density}"
        folder.mkdir(parents=True, exist_ok=True)
        icon = original.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
        icon.save(folder / "ic_launcher.jpg", "JPEG", quality=94, optimize=True)
        icon.save(folder / "ic_launcher_round.jpg", "JPEG", quality=94, optimize=True)

# Remove adaptive-icon XML so Android resolves the refreshed raster artwork
# instead of continuing to display an older foreground/background composition.
for folder in res.glob("mipmap-anydpi-v*"):
    for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
        candidate = folder / name
        if candidate.exists():
            candidate.unlink()

manifest = ROOT / "AndroidManifest.xml"
if manifest.exists():
    import re
    text = manifest.read_text(encoding="utf-8")
    text = re.sub(r'android:icon="@(?:mipmap|drawable)/[^"]+"', 'android:icon="@mipmap/ic_launcher"', text)
    text = re.sub(r'android:roundIcon="@(?:mipmap|drawable)/[^"]+"', 'android:roundIcon="@mipmap/ic_launcher_round"', text)
    manifest.write_text(text, encoding="utf-8")
print("Updated AmitySA launcher and round launcher icons.")
