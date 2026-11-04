from pathlib import Path
from PIL import Image
import re

SOURCE = Path("branding/amitysa_launcher.jpg")
SRC_ROOT = Path("app/src")
if not SOURCE.exists():
    raise SystemExit(f"Launcher artwork missing: {SOURCE}")
if not SRC_ROOT.exists():
    raise SystemExit(f"Android source folder missing: {SRC_ROOT}")

density_sizes = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
resource_roots = [p for p in SRC_ROOT.glob("*/res") if p.is_dir()]
if not resource_roots:
    resource_roots = [SRC_ROOT / "main" / "res"]
    resource_roots[0].mkdir(parents=True, exist_ok=True)

with Image.open(SOURCE) as original:
    original = original.convert("RGB")
    for res in resource_roots:
        for density, size in density_sizes.items():
            folder = res / f"mipmap-{density}"
            folder.mkdir(parents=True, exist_ok=True)
            icon = original.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
            icon.save(folder / "ic_launcher.jpg", "JPEG", quality=94, optimize=True)
            icon.save(folder / "ic_launcher_round.jpg", "JPEG", quality=94, optimize=True)
        # Remove adaptive XML so it cannot keep showing an old foreground image.
        for folder in res.glob("mipmap-anydpi-v*"):
            for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
                candidate = folder / name
                if candidate.exists():
                    candidate.unlink()

for manifest in SRC_ROOT.glob("*/AndroidManifest.xml"):
    text = manifest.read_text(encoding="utf-8")
    text = re.sub(r'android:icon="@(?:mipmap|drawable)/[^"]+"', 'android:icon="@mipmap/ic_launcher"', text)
    text = re.sub(r'android:roundIcon="@(?:mipmap|drawable)/[^"]+"', 'android:roundIcon="@mipmap/ic_launcher_round"', text)
    manifest.write_text(text, encoding="utf-8")

print(f"Updated launcher artwork in {len(resource_roots)} Android resource set(s).")
