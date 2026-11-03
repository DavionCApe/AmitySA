from pathlib import Path
import re

root = Path.cwd()
main = root / "app/src/main/java/com/amitysa/app/MainActivity.kt"
header = root / "app/src/main/java/com/amitysa/app/ChildrenScreens.kt"
if not main.exists() or not header.exists():
    raise SystemExit("AmitySA Compose source files were not found")

s = main.read_text(encoding="utf-8")
full_scheme = '''    // Use one selected palette across standard controls, cards, dialogs and advanced pages.
    val scheme = if (theme.dark) darkColorScheme(
        primary = theme.primary, onPrimary = theme.onAccent,
        secondary = theme.accent, onSecondary = theme.onAccent,
        tertiary = theme.accent, background = theme.canvas,
        onBackground = theme.ink, surface = theme.card,
        onSurface = theme.ink, surfaceVariant = theme.canvas,
        onSurfaceVariant = theme.inkSoft, outline = theme.inkSoft
    ) else lightColorScheme(
        primary = theme.primary, onPrimary = theme.onAccent,
        secondary = theme.accent, onSecondary = theme.onAccent,
        tertiary = theme.accent, background = theme.canvas,
        onBackground = theme.ink, surface = theme.card,
        onSurface = theme.ink, surfaceVariant = theme.canvas,
        onSurfaceVariant = theme.inkSoft, outline = theme.inkSoft
    )'''
pattern = r'    val scheme = if \\(theme\\.dark\\)\\s*darkColorScheme\\([^\\n]*\\)\\s*else\\s*lightColorScheme\\([^\\n]*\\)'
if "onSurfaceVariant = theme.inkSoft" not in s:
    s, count = re.subn(pattern, full_scheme, s, count=1)
    if count != 1:
        raise SystemExit("Could not locate the app-wide Material theme palette block")

old = '    MaterialTheme(colorScheme = scheme) {\\n        CompositionLocalProvider(LocalAmity provides theme) {'
new = '    MaterialTheme(colorScheme = scheme) {\\n        Surface(modifier = Modifier.fillMaxSize(), color = theme.canvas) {\\n        CompositionLocalProvider(LocalAmity provides theme) {'
if 'Surface(modifier = Modifier.fillMaxSize(), color = theme.canvas)' not in s:
    if old not in s:
        raise SystemExit("Could not locate the root theme provider")
    s = s.replace(old, new, 1)
    tail = '            if (showPopup) LaunchPopup { showPopup = false }\\n        }\\n    }\\n}'
    replacement = '            if (showPopup) LaunchPopup { showPopup = false }\\n        }\\n        }\\n    }\\n}'
    if tail not in s:
        raise SystemExit("Could not locate the end of the root theme provider")
    s = s.replace(tail, replacement, 1)
main.write_text(s, encoding="utf-8")

h = header.read_text(encoding="utf-8")
if 'internal fun ScreenHeader(title: String, onBack: () -> Unit) {\\n    val theme = LocalAmity.current' not in h:
    h = h.replace('internal fun ScreenHeader(title: String, onBack: () -> Unit) {',
                  'internal fun ScreenHeader(title: String, onBack: () -> Unit) {\\n    val theme = LocalAmity.current', 1)
h = h.replace('.background(Brush.verticalGradient(listOf(HeaderTop, HeaderBottom)))',
              '.background(Brush.verticalGradient(listOf(theme.primary, theme.primary.copy(alpha = 0.84f))))', 1)
h = h.replace('"←", color = Color.White, fontSize = 24.sp,', '"←", color = theme.onAccent, fontSize = 24.sp,', 1)
h = h.replace('Text(title, color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.Bold)',
              'Text(title, color = theme.onAccent, fontSize = 22.sp, fontWeight = FontWeight.Bold)', 1)
header.write_text(h, encoding="utf-8")
print("Applied shared light/dark colors to app surfaces, dialogs, controls and feature headers.")
