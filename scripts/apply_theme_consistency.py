#!/usr/bin/env python3
"""Apply the AmitySA JARVIS palette consistently across Android resource roots.

The script is intentionally conservative: it updates named Android color resources
and theme color attributes, and writes a canonical palette resource into every
Android values* resource directory. It does not recolor arbitrary drawable artwork,
photos, icons, or application content.

Default palette:
  background: #0D1117
  accent:     #00D2FF
  secondary:  #0066FF
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET


BACKGROUND = "#0D1117"
ACCENT = "#00D2FF"
SECONDARY = "#0066FF"
PALETTE_FILE = "amitysa_jarvis_palette.xml"

EXCLUDED_DIRS = {
    ".git", ".gradle", ".idea", ".kotlin", ".venv", "venv",
    "__pycache__", "node_modules", "build", "dist", "out",
    "target", "generated", "vendor", ".amitysa-theme-backups",
}

# Semantic resource names are normalized before matching.
BACKGROUND_NAMES = {
    "background", "backgroundcolor", "windowbackground", "canvas",
    "appbackground", "screenbackground", "scaffoldbackground",
    "surfacebackground", "primarybackground", "darkbackground",
}
ACCENT_NAMES = {
    "primary", "primarycolor", "accent", "accentcolor", "highlight",
    "highlightcolor", "brand", "brandcolor", "neon", "neoncyan",
    "cyan", "cyanaccent", "colorprimary", "coloraccent",
}
SECONDARY_NAMES = {
    "secondary", "secondarycolor", "tertiary", "tertiarycolor",
    "blue", "electricblue", "hudblue",
}
SURFACE_NAMES = {
    "surface", "surfacecolor", "card", "cardcolor", "panel",
    "panelcolor", "surfacevariant", "dialogbackground",
}
ON_BACKGROUND_NAMES = {
    "onbackground", "oncanvas", "textprimary", "primarytext",
    "foreground", "foregroundcolor", "textcolor",
}
ON_SURFACE_NAMES = {"onsurface", "cardtext", "paneltext"}
ON_ACCENT_NAMES = {"onprimary", "onaccent", "accenttext", "buttontext"}
OUTLINE_NAMES = {"outline", "border", "bordercolor", "divider", "stroke"}


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def color_for_name(name: str) -> str | None:
    key = normalized(name)
    if key in BACKGROUND_NAMES or any(x in key for x in ("windowbackground", "screenbackground", "appbackground")):
        return BACKGROUND
    if key in ACCENT_NAMES or key.startswith("colorprimary") or key.endswith("accent"):
        return ACCENT
    if key in SECONDARY_NAMES or key.endswith("electricblue"):
        return SECONDARY
    if key in SURFACE_NAMES or "cardbackground" in key or "panelbackground" in key:
        return "#16202D"
    if key in ON_BACKGROUND_NAMES or key in ON_SURFACE_NAMES:
        return "#EAF7FF"
    if key in ON_ACCENT_NAMES:
        return "#001018"
    if key in OUTLINE_NAMES or "border" in key:
        return "#00D2FF"
    return None


def is_excluded(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in EXCLUDED_DIRS for part in parts)


def discover_resource_roots(root: Path) -> list[Path]:
    found: set[Path] = set()
    for current, dirs, _files in os.walk(root):
        current_path = Path(current)
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        if current_path.name == "res":
            found.add(current_path)
    return sorted(found)


def values_dirs(resource_roots: Iterable[Path]) -> list[Path]:
    result: set[Path] = set()
    for res in resource_roots:
        for child in res.iterdir():
            if child.is_dir() and child.name == "values" or child.is_dir() and child.name.startswith("values-"):
                result.add(child)
    return sorted(result)


def canonical_palette_xml() -> str:
    return """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <!-- Canonical AmitySA JARVIS V1 palette. Keep these values in sync with Compose. -->
    <color name="amitysa_jarvis_background">#0D1117</color>
    <color name="amitysa_jarvis_accent">#00D2FF</color>
    <color name="amitysa_jarvis_secondary">#0066FF</color>
    <color name="amitysa_jarvis_surface">#16202D</color>
    <color name="amitysa_jarvis_text">#EAF7FF</color>
    <color name="amitysa_jarvis_on_accent">#001018</color>
    <color name="amitysa_jarvis_outline">#00D2FF</color>
</resources>
"""


@dataclass
class Change:
    path: Path
    description: str
    content: str


def update_xml_file(path: Path) -> tuple[str, int]:
    original = path.read_text(encoding="utf-8")
    updated = original
    changes = 0

    # Replace literal values of named <color> resources.
    color_tag = re.compile(
        r'(<color\b[^>]*\bname\s*=\s*["\']([^"\']+)["\'][^>]*>)(.*?)(</color\s*>)',
        re.IGNORECASE | re.DOTALL,
    )

    def replace_color(match: re.Match[str]) -> str:
        nonlocal changes
        target = color_for_name(match.group(2))
        if target is None:
            return match.group(0)
        old_value = match.group(3).strip()
        if old_value.lower() == target.lower():
            return match.group(0)
        changes += 1
        return f"{match.group(1)}{target}{match.group(4)}"

    updated = color_tag.sub(replace_color, updated)

    # Normalize standard Material/AppCompat theme color items to canonical resources.
    item_map = {
        "colorprimary": "@color/amitysa_jarvis_accent",
        "colorprimarydark": "@color/amitysa_jarvis_background",
        "coloraccent": "@color/amitysa_jarvis_accent",
        "colorsecondary": "@color/amitysa_jarvis_secondary",
        "android:coloraccent": "@color/amitysa_jarvis_accent",
        "android:windowbackground": "@color/amitysa_jarvis_background",
        "windowbackground": "@color/amitysa_jarvis_background",
    }
    item_tag = re.compile(
        r'(<item\b[^>]*\bname\s*=\s*["\']([^"\']+)["\'][^>]*>)(.*?)(</item\s*>)',
        re.IGNORECASE | re.DOTALL,
    )

    def replace_item(match: re.Match[str]) -> str:
        nonlocal changes
        target = item_map.get(match.group(2).strip().lower())
        if target is None:
            return match.group(0)
        if match.group(3).strip() == target:
            return match.group(0)
        changes += 1
        return f"{match.group(1)}{target}{match.group(4)}"

    updated = item_tag.sub(replace_item, updated)
    return updated, changes


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def backup(path: Path, root: Path, backup_root: Path) -> None:
    relative = path.relative_to(root)
    destination = backup_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd(),
                        help="Android project/workspace root (default: current directory)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report intended changes without writing files")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root = args.workspace.resolve()
    if not root.is_dir():
        print(f"ERROR: workspace directory does not exist: {root}", file=sys.stderr)
        return 2

    resource_roots = discover_resource_roots(root)
    if not resource_roots:
        print(f"ERROR: no Android resource roots named 'res' found under {root}", file=sys.stderr)
        return 2

    vals = values_dirs(resource_roots)
    if not vals:
        print("ERROR: resource roots were found, but no values/values-* directories exist.", file=sys.stderr)
        return 2

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = root / ".amitysa-theme-backups" / stamp
    changed_files = 0
    changed_values = 0
    created_palettes = 0

    print(f"Workspace: {root}")
    print(f"Resource roots: {len(resource_roots)}")
    print(f"Values directories: {len(vals)}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'WRITE'}")

    for values_dir in vals:
        palette_path = values_dir / PALETTE_FILE
        if palette_path.exists():
            existing = palette_path.read_text(encoding="utf-8")
            if existing != canonical_palette_xml():
                if args.verbose:
                    print(f"UPDATE palette: {palette_path.relative_to(root)}")
                if not args.dry_run:
                    backup(palette_path, root, backup_root)
                    atomic_write(palette_path, canonical_palette_xml())
                changed_files += 1
            elif args.verbose:
                print(f"OK palette: {palette_path.relative_to(root)}")
        else:
            if args.verbose:
                print(f"CREATE palette: {palette_path.relative_to(root)}")
            if not args.dry_run:
                atomic_write(palette_path, canonical_palette_xml())
            created_palettes += 1
            changed_files += 1

        for xml_path in sorted(values_dir.glob("*.xml")):
            if xml_path.name == PALETTE_FILE:
                continue
            try:
                updated, count = update_xml_file(xml_path)
            except (OSError, UnicodeError) as exc:
                print(f"WARNING: could not read {xml_path.relative_to(root)}: {exc}", file=sys.stderr)
                continue
            if count and updated != xml_path.read_text(encoding="utf-8"):
                if args.verbose:
                    print(f"UPDATE {xml_path.relative_to(root)} ({count} named values)")
                if not args.dry_run:
                    backup(xml_path, root, backup_root)
                    atomic_write(xml_path, updated)
                changed_files += 1
                changed_values += count

    print(f"Files to change/changed: {changed_files}")
    print(f"Named color/theme values normalized: {changed_values}")
    print(f"Canonical palette files created: {created_palettes}")
    if not args.dry_run and changed_files:
        print(f"Backups: {backup_root}")
    print("Palette targets: background #0D1117; accent #00D2FF; secondary #0066FF.")
    print("Note: arbitrary drawable artwork and hard-coded Kotlin/Compose colors are not rewritten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
