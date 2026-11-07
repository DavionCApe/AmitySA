from pathlib import Path
from PIL import Image, ImageOps
import re

# This is the full-resolution AmitySA artwork already stored in the repository.
# It is a JPEG despite the historical .png filename.
SOURCE = Path("amitysa_home_logo.png")
SRC_ROOT = Path("app/src")
if not SOURCE.is_file():
    raise SystemExit(f"Requested AmitySA artwork is missing: {SOURCE}")
if not SRC_ROOT.is_dir():
    raise SystemExit(f"Android source folder missing: {SRC_ROOT}")

density_sizes = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
resource_roots = [p for p in SRC_ROOT.glob("*/res") if p.is_dir()]
if not resource_roots:
    resource_roots = [SRC_ROOT / "main" / "res"]
    resource_roots[0].mkdir(parents=True, exist_ok=True)

with Image.open(SOURCE) as opened:
    artwork = ImageOps.exif_transpose(opened).convert("RGB")

    # Preserve the complete supplied landscape artwork. Fit it inside a square
    # dark canvas rather than center-cropping away the AmitySA wordmark.
    for res in resource_roots:
        for density, size in density_sizes.items():
            folder = res / f"mipmap-{density}"
            folder.mkdir(parents=True, exist_ok=True)

            # Remove every previous launcher variant before writing the new one.
            for old in folder.glob("ic_launcher*"):
                if old.is_file():
                    old.unlink()

            canvas = Image.new("RGB", (size, size), (2, 8, 19))
            fitted = ImageOps.contain(artwork, (size, size), method=Image.Resampling.LANCZOS)
            x = (size - fitted.width) // 2
            y = (size - fitted.height) // 2
            canvas.paste(fitted, (x, y))
            canvas.save(folder / "ic_launcher.png", "PNG", optimize=True)
            canvas.save(folder / "ic_launcher_round.png", "PNG", optimize=True)

        # Remove adaptive launcher XMLs that can keep referencing an old
        # foreground/background asset and override the regenerated icons.
        for folder in res.glob("mipmap-anydpi-v*"):
            for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
                candidate = folder / name
                if candidate.exists():
                    candidate.unlink()

        # Remove the obsolete flat launcher image if it was copied from the
        # archived Android project.
        for folder in res.rglob("*"):
            if folder.is_file() and folder.stem.lower() in {
                "amitysa_launcher", "ic_launcher_old", "ic_launcher_legacy"
            }:
                folder.unlink()

    # The old tiny flat artwork is not a valid fallback anywhere in the build.
    legacy = Path("branding/amitysa_launcher.jpg")
    if legacy.exists():
        legacy.unlink()

# Point every app manifest at the newly generated PNG launcher resources.
for manifest in SRC_ROOT.glob("*/AndroidManifest.xml"):
    source = manifest.read_text(encoding="utf-8")
    source = re.sub(
        r'android:icon="@(?:mipmap|drawable)/[^"]+"',
        'android:icon="@mipmap/ic_launcher"',
        source,
    )
    source = re.sub(
        r'android:roundIcon="@(?:mipmap|drawable)/[^"]+"',
        'android:roundIcon="@mipmap/ic_launcher_round"',
        source,
    )
    if 'android:icon="@mipmap/ic_launcher"' not in source:
        source = source.replace(
            "<application",
            '<application android:icon="@mipmap/ic_launcher" android:roundIcon="@mipmap/ic_launcher_round"',
            1,
        )
    manifest.write_text(source, encoding="utf-8")

# Fail the build if an obsolete flat launcher file survived resource generation.
for res in resource_roots:
    for old in res.rglob("*"):
        if old.is_file() and old.stem.lower() in {
            "amitysa_launcher", "ic_launcher_old", "ic_launcher_legacy"
        }:
            raise SystemExit(f"Obsolete launcher artwork remains: {old}")

print(
    f"Applied the full AmitySA artwork from {SOURCE} to "
    f"{len(resource_roots)} Android resource set(s); removed obsolete flat launcher artwork."
)
