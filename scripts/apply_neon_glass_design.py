from pathlib import Path

p = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
s = p.read_text(encoding="utf-8")

def replace_once(old: str, new: str, label: str):
    global s
    if old not in s:
        raise SystemExit(f"Neon glass upgrade stopped: could not find {label}")
    s = s.replace(old, new, 1)

# Premium midnight palette: deep navy, electric cyan and violet glass.
replace_once(
'''private val Midnight = AmityTheme(
    "midnight", "Midnight (logo colours)", true,
    Color(0xFF0F131A), Color(0xFF182029), Color(0xFFF2F4F7), Color(0xFF9AA5B4),
    Color(0xFF2DD4CF), Color(0xFFF5B942), Color(0xFF1A1405)
)''',
'''private val Midnight = AmityTheme(
    "midnight", "AmitySA Neon Glass", true,
    Color(0xFF050B1B), Color(0xFF102344), Color(0xFFF5FAFF), Color(0xFFA9BEDA),
    Color(0xFF18CFFF), Color(0xFF9A72FF), Color(0xFF031326)
)''',
"Midnight palette"
)
replace_once('''internal val HeaderTop = Color(0xFF0B0E14)
internal val HeaderBottom = Color(0xFF05070B)
internal val Gold = Color(0xFFF5B942)
internal val Danger = Color(0xFFD93025)''',
'''internal val HeaderTop = Color(0xFF08265D)
internal val HeaderBottom = Color(0xFF030817)
internal val Gold = Color(0xFF38E7FF)
internal val Danger = Color(0xFFFF315E)''',
"header palette"
)

# Give the header a layered blue glow while preserving the existing logo and theme action.
replace_once(
'''            .background(Brush.verticalGradient(listOf(HeaderTop, HeaderBottom)))''',
'''            .background(
                Brush.linearGradient(
                    listOf(Color(0xFF0A3B88), Color(0xFF071A43), HeaderBottom)
                )
            )''',
"header glass gradient"
)

# Persist the palette and header treatment; all existing screens and safety flows remain intact.
p.write_text(s, encoding="utf-8")
print("AmitySA neon glass palette and header treatment applied.")
