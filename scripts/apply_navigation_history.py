from pathlib import Path
import re

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not main.is_file():
    raise SystemExit("AmitySA MainActivity.kt was not found")
source = main.read_text(encoding="utf-8").replace("\r\n", "\n")

state_pattern = re.compile(
    r'(?m)^(?P<indent>[ \t]*)var screen by remember(?:Saveable)?\s*'
    r'\{\s*mutableStateOf\("home"\)\s*\}\s*$'
)
replacement = '''{indent}var screen by remember {{ mutableStateOf("home") }}
{indent}val screenHistory = remember {{ mutableStateListOf<String>() }}
{indent}fun navigateTo(destination: String) {{
{indent}    if (screen != destination) {{
{indent}        screenHistory.add(screen)
{indent}        screen = destination
{indent}    }}
{indent}}}
{indent}fun navigateBack() {{
{indent}    if (screenHistory.isNotEmpty()) {{
{indent}        screen = screenHistory.removeAt(screenHistory.lastIndex)
{indent}    }} else {{
{indent}        screen = "home"
{indent}    }}
{indent}}}'''
if 'val screenHistory = remember { mutableStateListOf<String>() }' not in source:
    matches = list(state_pattern.finditer(source))
    if len(matches) != 1:
        raise SystemExit(
            "Expected exactly one screen state declaration using remember/rememberSaveable "
            "and mutableStateOf(\"home\"); found " + str(len(matches))
        )
    match = matches[0]
    source = source[:match.start()] + replacement.format(indent=match.group("indent")) + source[match.end():]

old_back = '''    BackHandler(enabled = acc != null && screen != "home") {
        screen = if (screen == "edit") "children" else "home"
    }'''
new_back = '''    BackHandler(enabled = showThemes || showPopup || pairing || deviceSos || (acc != null && screen != "home")) {
        when {
            showThemes -> showThemes = false
            showPopup -> showPopup = false
            pairing -> pairing = false
            deviceSos -> deviceSos = false
            acc != null && screen != "home" -> navigateBack()
        }
    }'''
if old_back in source:
    source = source.replace(old_back, new_back, 1)
elif 'navigateBack()' not in source[source.find('BackHandler'):source.find('val theme = resolveTheme')]:
    raise SystemExit("Could not find the existing BackHandler block")

app_start = source.find("fun AmityApp(")
app_end = source.find("// ---------- Connectivity ----------", app_start)
if app_start < 0 or app_end < 0:
    raise SystemExit("Could not locate AmityApp boundaries")
app = source[app_start:app_end]

for route in ["home", "children", "edit", "sos", "sosSetup", "zones", "cloud", "security"]:
    app = re.sub(
        r'(?<![A-Za-z0-9_])screen = "' + re.escape(route) + r'"',
        'navigateTo("' + route + '")',
        app
    )

# Restore the assignments that belong inside the navigation helpers.
app = app.replace('''    fun navigateTo(destination: String) {
        if (screen != destination) {
            screenHistory.add(screen)
            navigateTo("destination")
        }
    }''', '''    fun navigateTo(destination: String) {
        if (screen != destination) {
            screenHistory.add(screen)
            screen = destination
        }
    }''')
app = app.replace('''    fun navigateBack() {
        if (screenHistory.isNotEmpty()) {
            screen = screenHistory.removeAt(screenHistory.lastIndex)
        } else {
            navigateTo("home")
        }
    }''', '''    fun navigateBack() {
        if (screenHistory.isNotEmpty()) {
            screen = screenHistory.removeAt(screenHistory.lastIndex)
        } else {
            screen = "home"
        }
    }''')

# Back arrows and page-completion actions return to the actual previous page.
app = app.replace('onBack = { navigateTo("home") }', 'onBack = { navigateBack() }')
app = app.replace('onClose = { navigateTo("home") }', 'onClose = { navigateBack() }')
app = app.replace('SosSetupScreen(acc) { navigateTo("home") }', 'SosSetupScreen(acc) { navigateBack() }')
app = app.replace('ZonesScreen(acc) { navigateTo("home") }', 'ZonesScreen(acc) { navigateBack() }')
app = app.replace('CloudScreen(acc) { navigateTo("home") }', 'CloudScreen(acc) { navigateBack() }')
app = app.replace('onDone = { navigateTo("children") }', 'onDone = { navigateBack() }')

# Signing out/deleting the account must clear the old account's route history.
app = app.replace(
    'store.signOut(); account = null; navigateTo("home")',
    'store.signOut(); account = null; screenHistory.clear(); screen = "home"'
)
app = app.replace(
    'account = null; navigateTo("home"); locked = false',
    'account = null; screenHistory.clear(); screen = "home"; locked = false'
)

# Validate that ordinary route changes now go through the stack.
helper_end = app.find("    val lifecycleOwner = LocalLifecycleOwner.current")
app_callbacks = app[helper_end:] if helper_end >= 0 else app
for route in ["children", "edit", "sos", "sosSetup", "zones", "cloud", "security"]:
    if re.search(r'(?<![A-Za-z0-9_])screen = "' + re.escape(route) + r'"', app_callbacks):
        raise SystemExit("Direct screen assignment remains for route: " + route)
for match in re.finditer(r'(?<![A-Za-z0-9_])screen = "home"', app_callbacks):
    line = app_callbacks[app_callbacks.rfind("\n", 0, match.start()) + 1:app_callbacks.find("\n", match.start())]
    if "screenHistory.clear()" not in line:
        raise SystemExit("Unexpected direct Home assignment outside session reset")

source = source[:app_start] + app + source[app_end:]
main.write_text(source, encoding="utf-8")
print("Applied AmitySA previous-page navigation: Android back, page back arrows and completion actions pop the in-app history; Home is used only when no prior page exists.")
