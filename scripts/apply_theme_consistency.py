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
    "jarvis", "JARVIS Command Centre", true,
    Color(0xFF050B14), Color(0xE6102232), Color(0xFFE4FAFF), Color(0xFF8CB8C8),
    Color(0xFF00CFFF), Color(0xFFFF9A3C), Color(0xFF04131D)
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
    listOf(Color(0xFF030812), Color(0xFF0B2032), Color(0xFF050B14))
)
internal val MirrorEdge = Brush.linearGradient(
    listOf(Color(0xFF00D9FF), Color(0xFF245A78), Color(0xFF8AF0FF), Color(0xFF102A3A))
)'''
s, count = re.subn(r'@Composable\nprivate fun resolveTheme\(id: String\): AmityTheme = when \(id\) \{.*?\n\}', resolver, s, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Could not replace theme resolver with the fixed Mirror Gloss theme")

s = s.replace('mutableStateOf(prefs.getString("theme", "midnight") ?: "midnight")', 'mutableStateOf("jarvis")')
s = s.replace('internal val HeaderTop = Color(0xFF0B0E14)', 'internal val HeaderTop = Color(0xFF092033)')
s = s.replace('internal val HeaderBottom = Color(0xFF05070B)', 'internal val HeaderBottom = Color(0xFF05070B)')
s = s.replace('internal val Gold = Color(0xFFF5B942)', 'internal val Gold = Color(0xFFFF9A3C)')

# Use a dark metallic Material palette for standard controls and dialogs.
scheme = '''    // One metallic palette for standard controls, dialogs, cards and feature pages.
    val scheme = darkColorScheme(
        primary = theme.primary, onPrimary = theme.onAccent,
        secondary = theme.accent, onSecondary = theme.onAccent,
        tertiary = theme.accent, background = theme.canvas,
        onBackground = theme.ink, surface = theme.card,
        onSurface = theme.ink, surfaceVariant = Color(0xFF12364A),
        onSurfaceVariant = theme.inkSoft, outline = Color(0xFF00CFFF)
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
        # ScreenHeader already receives LocalAmity from the source archive.
        # Do not inject another local theme declaration here.
        h = h.replace(
            ".background(Brush.verticalGradient(listOf(HeaderTop, HeaderBottom)))",
            ".background(Brush.verticalGradient(listOf(theme.primary, theme.primary.copy(alpha = 0.84f))))",
            1
        )
        h = h.replace('"←", color = Color.White, fontSize = 24.sp,', '"←", color = theme.onAccent, fontSize = 24.sp,', 1)
        h = h.replace('Text(title, color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.Bold)',
                      'Text(title, color = theme.onAccent, fontSize = 22.sp, fontWeight = FontWeight.Bold)', 1)
        header.write_text(h, encoding="utf-8")

print("Applied AmitySA JARVIS Command Centre theme app-wide: deep-space surfaces, cyan holographic controls, amber alert accents and matching feature headers.")
