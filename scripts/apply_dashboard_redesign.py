#!/usr/bin/env python3
"""Apply the AmitySA JARVIS glassmorphic theme to web layout files.

Scans HTML files under the workspace, parses their structure, and links a
shared CSS theme. Existing HTML is backed up before modification. The script
is safe to run repeatedly and supports --dry-run.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

LOGGER = logging.getLogger("amitysa.dashboard")
CSS_NAME = "jarvis-glass-dashboard.css"
MARKER = "<!-- AMITYSA_JARVIS_THEME -->"
BACKUP_DIR = ".amitysa-dashboard-backups"

EXCLUDED_DIRS = {
    ".git", ".gradle", ".idea", ".venv", "venv", "__pycache__",
    "node_modules", "build", "dist", "out", "target", "vendor",
    "generated", BACKUP_DIR,
}

CSS = r"""/* AmitySA JARVIS V1 - glassmorphic web dashboard */
:root {
  color-scheme: dark;
  --jarvis-canvas: #0D1117;
  --jarvis-cyan: #00D2FF;
  --jarvis-blue: #0066FF;
  --jarvis-glass: rgba(22, 32, 45, 0.78);
  --jarvis-glass-strong: rgba(13, 17, 23, 0.92);
  --jarvis-border: rgba(0, 210, 255, 0.42);
  --jarvis-glow: rgba(0, 210, 255, 0.20);
  --jarvis-text: #E6F7FF;
  --jarvis-muted: #8CA6B5;
  --jarvis-radius: 16px;
}
html { min-height: 100%; background: var(--jarvis-canvas); }
body {
  min-height: 100vh; margin: 0; color: var(--jarvis-text);
  background:
    radial-gradient(ellipse at 50% 0%, rgba(0,102,255,.13), transparent 52%),
    var(--jarvis-canvas);
  font-family: Inter, "Segoe UI", Roboto, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
header, .topbar, .navbar, .sidebar, nav, aside {
  border-color: var(--jarvis-border);
}
header, .topbar, .navbar {
  background: var(--jarvis-glass-strong);
  border-bottom: 1px solid var(--jarvis-border);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}
.dashboard, .dashboard-container, .app-container, main {
  box-sizing: border-box; width: 100%; min-width: 0;
}
.dashboard, .dashboard-container { padding: 20px; }
.jarvis-glass, .glass-panel, .dashboard-panel, .dashboard-card,
.data-panel, .widget, .card,
[class*="dashboard-card"], [class*="dashboard-panel"],
[class*="glass-panel"], [class*="data-card"], [class*="widget-card"] {
  color: var(--jarvis-text);
  background: var(--jarvis-glass);
  border: 1px solid var(--jarvis-border);
  border-radius: var(--jarvis-radius);
  box-shadow: 0 0 18px rgba(0,210,255,.08), inset 0 0 18px rgba(0,210,255,.035);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  transition: border-color 220ms ease, box-shadow 220ms ease, transform 220ms ease;
}
.jarvis-glass:hover, .glass-panel:hover, .dashboard-panel:hover,
.dashboard-card:hover, .data-panel:hover, .widget:hover, .card:hover {
  border-color: var(--jarvis-cyan);
  box-shadow: 0 0 20px var(--jarvis-glow), inset 0 0 14px rgba(0,210,255,.06);
}
.jarvis-border, .neon-border { border: 1px solid var(--jarvis-cyan); box-shadow: 0 0 12px var(--jarvis-glow); }
.jarvis-divider { height: 1px; border: 0; background: linear-gradient(90deg, transparent, var(--jarvis-cyan), transparent); }
h1, h2, h3, h4, h5, h6 { color: var(--jarvis-text); letter-spacing: .035em; }
.jarvis-highlight, .neon-text, .accent-text { color: var(--jarvis-cyan); text-shadow: 0 0 12px var(--jarvis-glow); }
small, .muted, .subtitle { color: var(--jarvis-muted); }
button, .button, .btn, .jarvis-button {
  color: var(--jarvis-text); background: rgba(0,102,255,.13);
  border: 1px solid var(--jarvis-border); border-radius: 10px;
  padding: 10px 16px; cursor: pointer; transition: .22s ease;
}
button:hover, .button:hover, .btn:hover, .jarvis-button:hover {
  background: rgba(0,210,255,.15); border-color: var(--jarvis-cyan);
  box-shadow: 0 0 14px var(--jarvis-glow);
}
input, select, textarea {
  color: var(--jarvis-text); background: rgba(13,17,23,.82);
  border: 1px solid var(--jarvis-border); border-radius: 10px;
  padding: 10px 12px; outline: none;
}
input:focus, select:focus, textarea:focus {
  border-color: var(--jarvis-cyan); box-shadow: 0 0 12px var(--jarvis-glow);
}
table { width: 100%; border-collapse: collapse; color: var(--jarvis-text); }
th, td { padding: 12px; border-bottom: 1px solid var(--jarvis-border); text-align: left; }
th { color: var(--jarvis-cyan); background: rgba(0,210,255,.055); }
a { color: var(--jarvis-cyan); text-decoration: none; }
a:hover { text-shadow: 0 0 10px var(--jarvis-glow); }
.jarvis-status { display: inline-flex; align-items: center; gap: 8px; color: var(--jarvis-cyan); }
.jarvis-status::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--jarvis-cyan); box-shadow: 0 0 10px var(--jarvis-cyan); }
@media (max-width: 768px) {
  .dashboard, .dashboard-container { padding: 12px; }
  .dashboard-grid { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; }
}
"""


class LayoutParser(HTMLParser):
    """Collect structural tags and dashboard-like class/id names."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: set[str] = set()
        self.classes: set[str] = set()
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        self.tags.add(tag.lower())
        values = dict(attrs)
        self.classes.update(values.get("class", "").lower().split())
        element_id = values.get("id")
        if element_id:
            self.ids.add(element_id.lower())

    handle_startendtag = handle_starttag

    @property
    def dashboard_score(self) -> int:
        hints = {"dashboard", "panel", "card", "widget", "sidebar",
                 "navbar", "navigation", "main-content", "data-panel"}
        return len((self.classes | self.ids) & hints)


def discover_html(workspace: Path):
    for root, directories, files in os.walk(workspace):
        directories[:] = [d for d in directories if d not in EXCLUDED_DIRS]
        for filename in files:
            path = Path(root) / filename
            if path.suffix.lower() in {".html", ".htm"}:
                yield path


def backup_file(path: Path, workspace: Path) -> Path:
    relative = path.relative_to(workspace)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = workspace / BACKUP_DIR / stamp / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    return destination


def atomic_write(path: Path, content: str) -> None:
    temporary = path.with_name(path.name + ".jarvis-tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def stylesheet_link(html_path: Path, css_path: Path) -> str:
    relative = os.path.relpath(css_path, html_path.parent).replace(os.sep, "/")
    return f'{MARKER}\n<link rel="stylesheet" href="{relative}">\n'


def inject_link(content: str, link: str) -> tuple[str, bool]:
    if MARKER in content or re.search(
        r'<link\b[^>]*href=["\'][^"\']*' + re.escape(CSS_NAME) + r'["\']',
        content, flags=re.IGNORECASE
    ):
        return content, False

    head_close = re.search(r"</head\s*>", content, flags=re.IGNORECASE)
    if head_close:
        return content[:head_close.start()] + link + content[head_close.start():], True

    head_open = re.search(r"<head\b[^>]*>", content, flags=re.IGNORECASE)
    if head_open:
        pos = head_open.end()
        return content[:pos] + "\n" + link + content[pos:], True

    html_open = re.search(r"<html\b[^>]*>", content, flags=re.IGNORECASE)
    if html_open:
        pos = html_open.end()
        return content[:pos] + "\n<head>\n" + link + "</head>\n" + content[pos:], True

    return "<head>\n" + link + "</head>\n" + content, True


def process_layout(path: Path, workspace: Path, css_path: Path, dry_run: bool) -> str:
    try:
        original = path.read_text(encoding="utf-8")
        parser = LayoutParser()
        parser.feed(original)
        parser.close()
        updated, changed = inject_link(original, stylesheet_link(path, css_path))
        LOGGER.info("%s | dashboard hints=%d | %s",
                    path.relative_to(workspace), parser.dashboard_score,
                    "inject" if changed else "already configured")
        if not changed:
            return "unchanged"
        if dry_run:
            return "planned"
        backup_file(path, workspace)
        atomic_write(path, updated)
        return "updated"
    except (OSError, UnicodeError, ValueError) as exc:
        LOGGER.error("Failed %s: %s", path, exc)
        return "failed"


def main() -> int:
    cli = argparse.ArgumentParser(description="Apply AmitySA JARVIS glassmorphic styling to HTML layouts.")
    cli.add_argument("--workspace", default=".", help="Project root (default: current directory).")
    cli.add_argument("--dry-run", action="store_true", help="Preview without modifying files.")
    cli.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    args = cli.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    workspace = Path(args.workspace).expanduser().resolve()
    if not workspace.is_dir():
        LOGGER.error("Workspace directory does not exist: %s", workspace)
        return 2

    layouts = sorted(discover_html(workspace))
    LOGGER.info("Workspace: %s", workspace)
    LOGGER.info("Found %d HTML layout file(s).", len(layouts))
    if args.dry_run:
        LOGGER.info("DRY RUN: no files will be changed.")

    css_path = workspace / CSS_NAME
    if not args.dry_run and (not css_path.exists() or css_path.read_text(encoding="utf-8") != CSS):
        if css_path.exists():
            backup_file(css_path, workspace)
        atomic_write(css_path, CSS)
        LOGGER.info("Wrote shared stylesheet: %s", css_path.relative_to(workspace))
    elif args.dry_run:
        LOGGER.info("Would ensure shared stylesheet: %s", CSS_NAME)

    counts = {"updated": 0, "planned": 0, "unchanged": 0, "failed": 0}
    for layout in layouts:
        counts[process_layout(layout, workspace, css_path, args.dry_run)] += 1

    LOGGER.info("Summary: %s", counts)
    if counts["failed"]:
        return 1
    LOGGER.info("Dashboard theme processing complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
