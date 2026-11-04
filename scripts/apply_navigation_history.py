from pathlib import Path
import re

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not main.is_file():
    raise SystemExit("AmitySA MainActivity.kt was not found")

source = main.read_text(encoding="utf-8").replace("\r\n", "\n")

# Install a real in-app navigation history. Every screen transition pushes the
# previous route, so Back returns to the actual previous page, not always Home.
state = '    var screen by remember { mutableStateOf("home") }'
replacement = '''    var screen by remember { mutableStateOf("home") }
    val screenHistory = remember { mutableStateListOf<String>() }
    fun navigateTo(destination: String) {
        if (screen != destination) {
            screenHistory.add(screen)
            screen = destination
        }
    }
    fun navigateBack() {
        if (screenHistory.isNotEmpty()) {
            screen = screenHistory.removeAt(screenHistory.lastIndex)
        } else {
            screen = "home"
        }
    }'''
if 'val screenHistory = remember { mutableStateListOf<String>() }' not in source:
    if source.count(state) != 1:
        raise SystemExit("Could not find the unique AmitySA screen state declaration")
    source = source.replace(state, replacement, 1)

# Route the system back gesture/button through modal and page history in order.
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

# Only modify AmityApp's body, not unrelated composables or the helper itself.
app_start = source.find('fun AmityApp(')
app_end = source.find('// ---------- Connectivity ----------', app_start)
if app_start < 0 or app_end < 0:
    raise SystemExit("Could not locate AmityApp boundaries")
app = source[app_start:app_end]

# Replace route assignments with stack-aware navigation. Keep the assignments
# inside navigateTo/navigateBack themselves untouched.
for route in ["home", "children", "edit", "sos", "sosSetup", "zones", "cloud", "security"]:
    app = re.sub(r'(?<![A-Za-z0-9_])screen = "' + re.escape(route) + r'"',
                 'navigateTo("' + route + '")', app)

# The stack-aware helper owns these two direct assignments.
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

# Back arrows and completion actions should pop to the previous page.
app = app.replace('onBack = { navigateTo("home") }', 'onBack = { navigateBack() }')
app = app.replace('onClose = { navigateTo("home") }', 'onClose = { navigateBack() }')
app = app.replace('onSetup = { navigateTo("sosSetup") }', 'onSetup = { navigateTo("sosSetup") }')
app = app.replace('SosSetupScreen(acc) { navigateTo("home") }', 'SosSetupScreen(acc) { navigateBack() }')
app = app.replace('ZonesScreen(acc) { navigateTo("home") }', 'ZonesScreen(acc) { navigateBack() }')
app = app.replace('CloudScreen(acc) { navigateTo("home") }', 'CloudScreen(acc) { navigateBack() }')
app = app.replace('onDone = { navigateTo("children") }', 'onDone = { navigateBack() }')

# A successful sign-out/deletion clears history so another account cannot
# navigate into pages belonging to the previous signed-in session.
app = app.replace('store.signOut(); account = null; navigateTo("home")',
                  'store.signOut(); account = null; screenHistory.clear(); screen = "home"')
app = app.replace('account = null; navigateTo("home"); locked = false',
                  'account = null; screenHistory.clear(); screen = "home"; locked = false')

# Guard against any route-changing callbacks bypassing the history.
for route in ["home", "children", "edit", "sos", "sosSetup", "zones", "cloud", "security"]:
    if re.search(r'(?<![A-Za-z0-9_])screen = "' + re.escape(route) + r'"', app):
        raise SystemExit("A direct screen assignment remains for route: " + route)

source = source[:app_start] + app + source[app_end:]
main.write_text(source, encoding="utf-8")
print("Applied AmitySA back-stack navigation: Android back, screen back arrows and completion actions return to the previous in-app page; Home is used only when history is empty.")
