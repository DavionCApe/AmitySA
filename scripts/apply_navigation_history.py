from pathlib import Path
import re

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not main.is_file():
    raise SystemExit("AmitySA MainActivity.kt was not found")
source = main.read_text(encoding="utf-8").replace("\r\n", "\n")

if 'val screenHistory = remember { mutableStateListOf<String>() }' not in source:
    pattern = re.compile(r'(?m)^(?P<indent>[ \t]*)var screen\s+by\s+remember(?:Saveable)?\b[^\n]*$')
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise SystemExit("Expected one single-line screen state declaration; found " + str(len(matches)))
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

app_start = source.find("fun AmityApp(")
app_end = source.find("// ---------- Connectivity ----------", app_start)
if app_start < 0 or app_end < 0:
    raise SystemExit("Could not locate AmityApp boundaries")
app = source[app_start:app_end]

# Replace any simple existing BackHandler, regardless of its previous condition.
back_handler = 'BackHandler(enabled = acc != null && screen != "home") { navigateBack() }'
generic_back = re.compile(r'BackHandler\s*\([^)]*\)\s*\{[^{}]*\}', re.S)
if generic_back.search(app):
    app = generic_back.sub(back_handler, app, count=1)
else:
    marker = "    val lifecycleOwner = LocalLifecycleOwner.current"
    if marker not in app:
        raise SystemExit("Could not find safe insertion point for Android BackHandler")
    app = app.replace(marker, "    " + back_handler + "\n" + marker, 1)

for route in ["home", "children", "edit", "sos", "sosSetup", "zones", "cloud", "security", "map", "checkin"]:
    app = re.sub(
        r'(?<![A-Za-z0-9_])screen\s*=\s*"' + re.escape(route) + r'"',
        'navigateTo("' + route + '")',
        app
    )

app = app.replace(
    'screenHistory.add(screen)\n            navigateTo("destination")',
    'screenHistory.add(screen)\n            screen = destination'
)
app = app.replace(
    'else {\n            navigateTo("home")\n        }',
    'else {\n            screen = "home"\n        }'
)

app = app.replace('onBack = { navigateTo("home") }', 'onBack = { navigateBack() }')
app = app.replace('onClose = { navigateTo("home") }', 'onClose = { navigateBack() }')
app = app.replace('SosSetupScreen(acc) { navigateTo("home") }', 'SosSetupScreen(acc) { navigateBack() }')
app = app.replace('ZonesScreen(acc) { navigateTo("home") }', 'ZonesScreen(acc) { navigateBack() }')
app = app.replace('CloudScreen(acc) { navigateTo("home") }', 'CloudScreen(acc) { navigateBack() }')
app = app.replace('onDone = { navigateTo("children") }', 'onDone = { navigateBack() }')

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
if back_handler not in app:
    raise SystemExit("Android BackHandler is not connected to navigation history")

source = source[:app_start] + app + source[app_end:]
if "import androidx.activity.compose.BackHandler" not in source:
    package_match = re.search(r'(?m)^package [^\n]+\n', source)
    if not package_match:
        raise SystemExit("Could not locate Kotlin package declaration")
    source = source[:package_match.end()] + "\nimport androidx.activity.compose.BackHandler\n" + source[package_match.end():]

# Fix stale ActivityRow references after all preceding UI generators have run.
# Locate the composable containing item.time, then patch only that function. The
# same item.icon expression is valid elsewhere (for example QuickAction rows).
icon_old = "Text(item.icon, fontSize = 22.sp)"
time_old = "Text(item.time, color = t.inkSoft, fontSize = 12.sp)"
time_index = source.find(time_old)
if time_index < 0:
    raise SystemExit("ActivityRow time reference was not found after final UI generation")

# Use the nearest preceding composable boundary and the next one as the scope.
scope_start = source.rfind("\n@Composable", 0, time_index)
if scope_start < 0:
    scope_start = source.rfind("\nprivate fun ", 0, time_index)
if scope_start < 0:
    scope_start = source.rfind("\nfun ", 0, time_index)
scope_end = source.find("\n@Composable", time_index + len(time_old))
if scope_end < 0:
    scope_end = len(source)
if scope_start < 0 or scope_end <= time_index:
    raise SystemExit("Could not isolate ActivityRow composable for compile repair")

activity_scope = source[scope_start:scope_end]
icon_count = activity_scope.count(icon_old)
time_count = activity_scope.count(time_old)
if icon_count == 1 and time_count == 1:
    activity_scope = activity_scope.replace(icon_old, 'Text("•", fontSize = 22.sp)', 1)
    activity_scope = activity_scope.replace(time_old, 'Text("Activity recorded", color = t.inkSoft, fontSize = 12.sp)', 1)
    # Activity.title may not be a non-null String in the imported model;
    # stringify it so Compose resolves the String Text overload.
    activity_scope = activity_scope.replace("Text(item.title,", "Text(item.title.toString(),", 1)
    # The generated source currently leaves two orphan closing braces after
    # ActivityRow. Keep the function's own closing brace and discard only the
    # two extra top-level braces before the next composable.
    scope_lines = activity_scope.rstrip("\\n").split("\\n")
    if len(scope_lines) >= 3 and all(line.strip() == "}" for line in scope_lines[-3:]):
        scope_lines = scope_lines[:-2]
        activity_scope = "\\n".join(scope_lines) + "\\n"
    else:
        raise SystemExit("ActivityRow did not end with the expected redundant brace pattern")
    source = source[:scope_start] + activity_scope + source[scope_end:]
else:
    raise SystemExit(
        f"Unexpected ActivityRow scoped field counts: icon={icon_count}, time={time_count}"
    )

main.write_text(source, encoding="utf-8")
print("Applied previous-page navigation and connected Android system Back to the history stack.")
