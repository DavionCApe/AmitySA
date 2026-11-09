#!/usr/bin/env python3
"""Apply the shared JARVIS HUD and AmitySA artwork behind every Compose screen.

This runs after apply_fui_hud.py, which defines AmityHudBackdrop(). It wraps
the root Activity Surface content, not individual pages, so existing navigation,
page callbacks, dialogs, and feature logic remain untouched.
"""
from __future__ import annotations

import re
from pathlib import Path

MAIN = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
MARKER = "AMITYSA_GLOBAL_JARVIS_BACKDROP"

def matching_brace(source: str, start: int) -> int:
    """Return the matching } while ignoring Kotlin comments and string literals."""
    depth = 0
    i = start
    state = "code"
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if state == "line":
            if ch == "\n":
                state = "code"
        elif state == "block":
            if ch == "/" and nxt == "*":
                # Kotlin block comments may nest.
                depth += 1
                i += 1
            elif ch == "*" and nxt == "/":
                depth -= 1
                i += 1
                if depth == 0:
                    state = "code"
        elif state == "raw":
            if source.startswith('"""', i):
                state = "code"
                i += 2
        elif state == "string":
            if ch == "\\":
                i += 1
            elif ch == '"':
                state = "code"
        elif state == "char":
            if ch == "\\":
                i += 1
            elif ch == "'":
                state = "code"
        else:
            if ch == "/" and nxt == "/":
                state = "line"
                i += 1
            elif ch == "/" and nxt == "*":
                state = "block"
                depth = 1
                i += 1
            elif source.startswith('"""', i):
                state = "raw"
                i += 2
            elif ch == '"':
                state = "string"
            elif ch == "'":
                state = "char"
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise SystemExit("Global JARVIS UI stopped: could not match root Compose braces.")

def matching_paren(source: str, start: int) -> int:
    depth = 0
    i = start
    quote = None
    while i < len(source):
        ch = source[i]
        if quote:
            if ch == "\\":
                i += 1
            elif ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise SystemExit("Global JARVIS UI stopped: could not match Surface parameters.")

if not MAIN.is_file():
    raise SystemExit(f"Global JARVIS UI stopped: missing {MAIN}")
source = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n")

if MARKER in source:
    print("Global JARVIS HUD is already installed; no duplicate wrapper added.")
    raise SystemExit(0)

if "private fun AmityHudBackdrop()" not in source:
    raise SystemExit("Global JARVIS UI stopped: AmityHudBackdrop() was not generated.")

set_match = re.search(r"\bsetContent\s*\{", source)
if not set_match:
    raise SystemExit("Global JARVIS UI stopped: root setContent block was not found.")
set_open = source.find("{", set_match.start())
set_close = matching_brace(source, set_open)
set_body = source[set_open:set_close + 1]
if not re.search(r"\b(?:AmitySaJarvisTheme|MaterialTheme)\b", set_body):
    raise SystemExit("Global JARVIS UI stopped: root Material/Amity theme wrapper is missing.")

surface_match = re.search(r"\bSurface\s*\(", set_body)
if not surface_match:
    raise SystemExit("Global JARVIS UI stopped: root Surface was not found.")
surface_open = set_open + surface_match.end() - 1
surface_close_paren = matching_paren(source, surface_open)
lambda_open = surface_close_paren + 1
while lambda_open < len(source) and source[lambda_open].isspace():
    lambda_open += 1
if lambda_open >= len(source) or source[lambda_open] != "{":
    raise SystemExit("Global JARVIS UI stopped: root Surface content lambda was not found.")
lambda_close = matching_brace(source, lambda_open)

wrapper = """
            // AMITYSA_GLOBAL_JARVIS_BACKDROP: shared foreground-safe HUD for every page.
            Box(modifier = Modifier.fillMaxSize()) {
                Image(
                    painter = painterResource(R.drawable.amity_logo),
                    contentDescription = null,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize().alpha(0.10f)
                )
                AmityHudBackdrop()
"""
source = source[:lambda_open + 1] + wrapper + source[lambda_open + 1:lambda_close] + "\n            }" + source[lambda_close:]
MAIN.write_text(source, encoding="utf-8")
print("Applied shared JARVIS HUD and low-opacity AmitySA artwork behind the root content; all existing pages remain foreground and interactive.")
