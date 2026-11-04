from pathlib import Path
import re

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not main.is_file():
    raise SystemExit("AmitySA MainActivity.kt was not found")
source = main.read_text(encoding="utf-8").replace("\r\n", "\n")

# Preserve the project's real screen initializer instead of assuming "home".
if 'val screenHistory = remember { mutableStateListOf<String>() }' not in source:
    pattern = re.compile(r'(?m)^(?P<indent>[ \t]*)var screen\s+by\s+remember(?:Saveable)?\b[^\n]*$')
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise SystemExit(
            "Expected one single-line var screen by remember declaration; found "
            + str(len(matches))
        )
    m = matches[0]
    indent = m.group("indent")
    helpers = (
        m.group(0) + "\n"
        + indent + "val screenHistory = remember { mutableStateListOf<String>() }\n"
        + indent + "fun navigateTo(destination: String) {\n"
        + indent + "    if (screen != destination) {\n"
        + indent + "        screenHistory.add(screen)\n"
        + indent + "        screen = destination\n"
        + indent + "    }\n"
        + indent + "}\n"
        + indent + "fun navigateBack() {\n"
        + indent + "    if (screenHistory.isNotEmpty()) {\n"
        + indent + "        screen = screenHistory.removeAt(screenHistory.lastIndex)\n"
        + indent + "    } else {\n"
        + indent + '        screen = "home"\n'
        + indent + "    }\n"
        + indent + "}"
    )
    source = source[:m.start()] + helpers + source[m.end():]

# Replace the known Android back-handler pattern when present.
back_pattern = re.compile(
    r'(?s)BackHandler\(enabled\s*=\s*acc\s*!=\s*null\s*&&\s*screen\s*!=\s*"home"\)\s*\{\s*'
    r'screen\s*=\s*if\s*\(screen\s*==\s*"edit"\)\s*"children"\s*else\s*"home"\s*\}'
)
source, _ = back_pattern.subn(
    'BackHandler(enabled = acc != null && screen != "home") { navigateBack() }',
    source,
    count=1
)

app_start = source.find("fun AmityApp(")
app_end = source.find("// ---------- Connectivity ----------", app_start)
if app_start < 0 or app_end < 0:
    raise SystemExit("Could not locate AmityApp boundaries")
app = source[app_start:app_end]

for route in ["home", "children", "edit", "sos", "sosSetup", "zones", "cloud", "security", "map", "checkin"]:
    app = re.sub(
        r'(?<![A-Za-z0-9_])screen\s*=\s*"' + re.escape(route) + r'"',
        'navigateTo("' + route + '")',
        app
    )

# Keep direct assignments inside the history helper itself.
app = app.replace(
    'screenHistory.add(screen)\n            navigateTo("destination")',
    'screenHistory.add(screen)\n            screen = destination'
)
app = app.replace(
    'else {\n            navigateTo("home")\n        }',
    'else {\n            screen = "home"\n        }'
)

# Page-level back callbacks should pop history, not force the home screen.
app = app.replace('onBack = { navigateTo("home") }', 'onBack = { navigateBack() }')
app = app.replace('onClose = { navigateTo("home") }', 'onClose = { navigateBack() }')
app = app.replace('SosSetupScreen(acc) { navigateTo("home") }', 'SosSetupScreen(acc) { navigateBack() }')
app = app.replace('ZonesScreen(acc) { navigateTo("home") }', 'ZonesScreen(acc) { navigateBack() }')
app = app.replace('CloudScreen(acc) { navigateTo("home") }', 'CloudScreen(acc) { navigateBack() }')
app = app.replace('onDone = { navigateTo("children") }', 'onDone = { navigateBack() }')

# Clear history on sign-out/account deletion.
app = app.replace(
    'store.signOut(); account = null; navigateTo("home")',
    'store.signOut(); account = null; screenHistory.clear(); screen = "home"'
)
app = app.replace(
    'account = null; navigateTo("home"); locked = false',
    'account = null; screenHistory.clear(); screen = "home"; locked = false'
)

if 'fun navigateBack()' not in app or 'val screenHistory = remember { mutableStateListOf<String>() }' not in app:
    raise SystemExit("Navigation history helpers were not installed")
source = source[:app_start] + app + source[app_end:]
main.write_text(source, encoding="utf-8")
print("Applied AmitySA navigation history using the existing screen state; preserved its initializer and installed previous-page back navigation.")
