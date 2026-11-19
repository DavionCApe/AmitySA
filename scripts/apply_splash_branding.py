from pathlib import Path
import re
import xml.etree.ElementTree as ET
from PIL import Image, ImageOps

source = Path("branding/amitysa_launcher.jpg")
res = Path("app/src/main/res")
manifest = Path("app/src/main/AndroidManifest.xml")
if not source.is_file() or not res.is_dir() or not manifest.is_file():
    raise SystemExit("Splash branding stopped: artwork, Android resources, or manifest is missing.")

ANDROID = "http://schemas.android.com/apk/res/android"
ET.register_namespace("android", ANDROID)
with Image.open(source) as opened:
    artwork = opened.convert("RGBA")
    # Preserve the complete shield artwork; never crop it to fill the splash icon.
    splash = Image.new("RGBA", (512, 512), (2, 8, 19, 0))
    fitted = ImageOps.contain(artwork, (460, 460), Image.Resampling.LANCZOS)
    splash.alpha_composite(fitted, ((512 - fitted.width) // 2, (512 - fitted.height) // 2))

target = res / "drawable-nodpi" / "amitysa_splash_logo.png"
target.parent.mkdir(parents=True, exist_ok=True)
splash.save(target, "PNG", optimize=True)

# Replace existing raster logo/brand artwork too, so a legacy in-app splash
# composable cannot keep displaying the old mark from a drawable resource.
updated = []
logo_pattern = re.compile(r"(logo|brand|amity)", re.I)
for folder in res.glob("drawable*"):
    if not folder.is_dir():
        continue
    for candidate in folder.iterdir():
        if not candidate.is_file() or not logo_pattern.search(candidate.stem):
            continue
        if candidate.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        try:
            with Image.open(source) as opened:
                image = opened.convert("RGBA")
                if candidate.suffix.lower() in {".jpg", ".jpeg"}:
                    image = image.convert("RGB")
                image.save(candidate)
            updated.append(str(candidate))
        except Exception as error:
            raise SystemExit(f"Could not replace legacy logo resource {candidate}: {error}")

# Point Android 12+ splash themes at the newly generated artwork.
root = ET.parse(manifest).getroot()
refs = set()
for node in root.iter():
    value = node.attrib.get(f"{{{ANDROID}}}theme")
    if value and value.startswith("@style/"):
        refs.add(value.split("/", 1)[1])

styles_updated = []
for values_dir in res.glob("values*"):
    if not values_dir.is_dir():
        continue
    for xml in values_dir.glob("*.xml"):
        try:
            tree = ET.parse(xml)
        except ET.ParseError:
            continue
        changed = False
        for style in tree.getroot().findall("style"):
            if style.attrib.get("name") not in refs:
                continue
            for name, value in (
                ("android:windowSplashScreenAnimatedIcon", "@drawable/amitysa_splash_logo"),
                ("android:windowSplashScreenBackground", "#020813"),
            ):
                item = next((x for x in style.findall("item") if x.attrib.get("name") == name), None)
                if item is None:
                    item = ET.SubElement(style, "item", {"name": name})
                item.text = value
                changed = True
            if changed:
                styles_updated.append(style.attrib.get("name"))
        if changed:
            tree.write(xml, encoding="utf-8", xml_declaration=True)

print("Created Android splash artwork: " + str(target))
print("Updated existing drawable logos: " + (", ".join(updated) if updated else "none found"))
print("Updated Android splash theme(s): " + (", ".join(sorted(set(styles_updated))) if styles_updated else "no matching theme style found; drawable is packaged for legacy splash usage"))
