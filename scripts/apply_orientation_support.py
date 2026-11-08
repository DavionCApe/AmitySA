#!/usr/bin/env python3
"""Allow AmitySA activities to rotate between portrait and landscape.

Run after the Android project archive has been extracted into the workspace.
The default Android orientation policy (unspecified) respects the device's
Auto-rotate setting and lets Compose layouts receive landscape constraints.
"""
from pathlib import Path
import re
import sys

ROOT = Path("app/src/main")
if not ROOT.is_dir():
    raise SystemExit("Android source directory not found: app/src/main")

manifests = list(ROOT.rglob("AndroidManifest.xml"))
if not manifests:
    raise SystemExit("No AndroidManifest.xml found under app/src/main")

changed = 0
for path in manifests:
    text = path.read_text(encoding="utf-8")
    original = text

    def allow_rotation(match):
        tag = match.group(0)
        # Remove any fixed portrait/landscape lock and explicitly use Android's
        # normal user-controlled orientation behavior.
        if re.search(r'android:screenOrientation\s*=', tag):
            tag = re.sub(
                r'\s+android:screenOrientation\s*=\s*["\'][^"\']*["\']',
                '',
                tag,
            )
        if tag.rstrip().endswith("/>"):
            return tag[:-2] + ' android:screenOrientation="unspecified" />'
        return tag[:-1] + ' android:screenOrientation="unspecified">'

    text = re.sub(r'<activity(?:-alias)?\b[^>]*>', allow_rotation, text, flags=re.DOTALL)
    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1
        print(f"Updated rotation policy: {path}")

if changed == 0:
    print("No fixed activity orientation was found; Android's default already permits rotation.")
else:
    print(f"Landscape rotation enabled in {changed} manifest(s).")

# Fail if a fixed portrait lock remains on an activity declaration.
for path in manifests:
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r'<activity(?:-alias)?\b[^>]*>', text, flags=re.DOTALL):
        tag = match.group(0)
        if re.search(r'android:screenOrientation\s*=\s*["\'](?:portrait|sensorPortrait|userPortrait)["\']', tag):
            raise SystemExit(f"Portrait lock remains in {path}: {tag}")
print("Verified: no activity is locked to portrait.")
