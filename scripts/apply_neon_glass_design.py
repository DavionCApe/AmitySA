from pathlib import Path

p = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
s = p.read_text(encoding="utf-8")

def replace_once(old: str, new: str, label: str):
    global s
    if old not in s:
        raise SystemExit(f"Neon glass upgrade stopped: could not find {label}")
    s = s.replace(old, new, 1)

# Electric navy theme with cyan and violet highlights.
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
)''', "Midnight palette")
replace_once(
'''internal val HeaderTop = Color(0xFF0B0E14)
internal val HeaderBottom = Color(0xFF05070B)
internal val Gold = Color(0xFFF5B942)
internal val Danger = Color(0xFFD93025)''',
'''internal val HeaderTop = Color(0xFF08265D)
internal val HeaderBottom = Color(0xFF030817)
internal val Gold = Color(0xFF38E7FF)
internal val Danger = Color(0xFFFF315E)''', "header palette")

# Add a subtle neon outline to the existing material cards without changing their actions.
replace_once(
'''        colors = CardDefaults.cardColors(containerColor = t.card),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {''',
'''        colors = CardDefaults.cardColors(containerColor = t.card.copy(alpha = 0.94f)),
        border = androidx.compose.foundation.BorderStroke(1.dp, t.primary.copy(alpha = 0.34f)),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
    ) {''', "status glass card")
replace_once(
'''        colors = CardDefaults.cardColors(containerColor = t.card),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {''',
'''        colors = CardDefaults.cardColors(containerColor = t.card.copy(alpha = 0.94f)),
        border = androidx.compose.foundation.BorderStroke(1.dp, t.accent.copy(alpha = 0.38f)),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
    ) {''', "action glass card")

# Make the brand header feel brighter and more dimensional.
replace_once(
'''            .background(Brush.verticalGradient(listOf(HeaderTop, HeaderBottom)))''',
'''            .background(Brush.linearGradient(listOf(Color(0xFF0A3B88), Color(0xFF071A43), HeaderBottom)))''',
"header gradient")
# Header subtitle is intentionally left to the existing generated header layout.
# Keep the SOS action prominent, but use the approved blue-to-violet neon treatment.
replace_once(
'''            .background(Brush.horizontalGradient(listOf(Danger, Color(0xFFB3261E))))''',
'''            .background(Brush.horizontalGradient(listOf(Color(0xFF087BDB), Color(0xFF5B42C8), Color(0xFF9A3ED0))))''',
"SOS neon gradient")

p.write_text(s, encoding="utf-8")
print("AmitySA neon glass theme, header, SOS and outlined dashboard cards applied.")
