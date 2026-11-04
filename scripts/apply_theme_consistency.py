from pathlib import Path
import re

root = Path.cwd()
base = root / "app/src/main/java/com/amitysa/app"
main = base / "MainActivity.kt"
if not main.exists():
    raise SystemExit("AmitySA MainActivity.kt was not found")

s = main.read_text(encoding="utf-8")

# Force one consistent 3D Mirror Gloss palette across the entire application.
midnight = '''private val Midnight = AmityTheme(
    "mirror", "3D Mirror Gloss", true,
    Color(0xFF070A10), Color(0xCC182331), Color(0xFFF5F8FC), Color(0xFFB7C3D2),
    Color(0xFFDCE8F5), Color(0xFF54C8FF), Color(0xFF07111D)
)'''
s, count = re.subn(r'private val Midnight = AmityTheme\(.*?\n\)', midnight, s, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Could not update the primary AmitySA theme palette")

s, count = re.subn(r'private val themeChoices = listOf\([^\n]*\)', 'private val themeChoices = listOf(Midnight)', s, count=1)
if count != 1:
    raise SystemExit("Could not restrict theme picker to the approved Mirror Gloss theme")

resolver = '''@Composable
private fun resolveTheme(id: String): AmityTheme = Midnight

// Reflective dark glass backdrop shared by every screen.
internal val AmityBackdrop = Brush.verticalGradient(
    listOf(Color(0xFF080B12), Color(0xFF111C2A), Color(0xFF07090F))
)
internal val MirrorEdge = Brush.linearGradient(
    listOf(Color(0xFFEAF4FF), Color(0xFF526B86), Color(0xFFB8D5F0), Color(0xFF26384D))
)'''
s, count = re.subn(r'@Composable\nprivate fun resolveTheme\(id: String\): AmityTheme = when \(id\) \{.*?\n\}', resolver, s, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Could not replace theme resolver with the fixed Mirror Gloss theme")

s = s.replace('mutableStateOf(prefs.getString("theme", "midnight") ?: "midnight")', 'mutableStateOf("mirror")')
s = s.replace('internal val HeaderTop = Color(0xFF0B0E14)', 'internal val HeaderTop = Color(0xFF1C2A3A)')
s = s.replace('internal val HeaderBottom = Color(0xFF05070B)', 'internal val HeaderBottom = Color(0xFF05070B)')
s = s.replace('internal val Gold = Color(0xFFF5B942)', 'internal val Gold = Color(0xFFDCE8F5)')

# Use a dark metallic Material palette for standard controls and dialogs.
scheme = '''    // One metallic palette for standard controls, dialogs, cards and feature pages.
    val scheme = darkColorScheme(
        primary = theme.primary, onPrimary = theme.onAccent,
        secondary = theme.accent, onSecondary = theme.onAccent,
        tertiary = theme.accent, background = theme.canvas,
        onBackground = theme.ink, surface = theme.card,
        onSurface = theme.ink, surfaceVariant = Color(0xFF26384B),
        onSurfaceVariant = theme.inkSoft, outline = Color(0xFF8FA8C2)
    )'''
pattern = r'    val scheme = if \(theme\.dark\)\s*darkColorScheme\([^\n]*\)\s*else\s*lightColorScheme\([^\n]*\)'
if 'onSurfaceVariant = theme.inkSoft' not in s:
    s, count = re.subn(pattern, scheme, s, count=1)
    if count != 1:
        raise SystemExit("Could not locate Material color scheme block")

# Ensure the root content is painted with the selected dark surface.
old = '    MaterialTheme(colorScheme = scheme) {\n        CompositionLocalProvider(LocalAmity provides theme) {'
new = '    MaterialTheme(colorScheme = scheme) {\n        Surface(modifier = Modifier.fillMaxSize(), color = theme.canvas) {\n        CompositionLocalProvider(LocalAmity provides theme) {'
if 'Surface(modifier = Modifier.fillMaxSize(), color = theme.canvas)' not in s:
    if old not in s:
        raise SystemExit("Could not locate root MaterialTheme provider")
    s = s.replace(old, new, 1)
    tail = '            if (showPopup) LaunchPopup { showPopup = false }\n        }\n    }\n}'
    replacement = '            if (showPopup) LaunchPopup { showPopup = false }\n        }\n        }\n    }\n}'
    if tail not in s:
        raise SystemExit("Could not locate root theme provider closing block")
    s = s.replace(tail, replacement, 1)

# Remove the automatic light/dark choice so users always see the approved theme.
auto_row = r'\s*ThemeRow\(\s*label = "Match my phone \(auto\)",.*?\n\s*\)\n'
s = re.sub(auto_row, '\n', s, count=1, flags=re.S)

# Make the app background visibly reflective rather than a flat fill.
main.write_text(s, encoding="utf-8")
for path in base.glob("*.kt"):
    source = path.read_text(encoding="utf-8")
    source = source.replace(".background(t.canvas)", ".background(AmityBackdrop)")
    path.write_text(source, encoding="utf-8")

# Keep feature-page headers on the same cool chrome surface.
header = base / "ChildrenScreens.kt"
if header.exists():
    h = header.read_text(encoding="utf-8")
    if "internal fun ScreenHeader(title: String, onBack: () -> Unit) {" in h:
        # Keep this patch idempotent when the archive already declares theme.
        signature = "internal fun ScreenHeader(title: String, onBack: () -> Unit) {"
        start = h.find(signature)
        end = h.find("\\n}", start)
        if start < 0 or end < 0:
            raise SystemExit("Could not locate ScreenHeader body")
        body = h[start:end]
        body_lines = [line for line in body.splitlines()
                      if "val theme = LocalAmity.current" not in line]
        body = body_lines[0] + "\\n    val theme = LocalAmity.current"
        if len(body_lines) > 1:
            body += "\\n" + "\\n".join(body_lines[1:])
        h = h[:start] + body + h[end:]
        h = h.replace(
            ".background(Brush.verticalGradient(listOf(HeaderTop, HeaderBottom)))",
            ".background(Brush.verticalGradient(listOf(theme.primary, theme.primary.copy(alpha = 0.84f))))",
            1
        )
        h = h.replace('"←", color = Color.White, fontSize = 24.sp,', '"←", color = theme.onAccent, fontSize = 24.sp,', 1)
        h = h.replace('Text(title, color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.Bold)',
                      'Text(title, color = theme.onAccent, fontSize = 22.sp, fontWeight = FontWeight.Bold)', 1)
        header.write_text(h, encoding="utf-8")

print("Applied AmitySA 3D Mirror Gloss theme to the final Android source: reflective dark backdrop, chrome palette, glass-toned surfaces and matching feature headers.")
