from pathlib import Path

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not main.is_file():
    raise SystemExit(f"AmitySA MainActivity.kt was not found: {main}")

source = main.read_text(encoding="utf-8").replace("\r\n", "\n")

# Use stable declaration markers rather than an indentation-sensitive regex.
auth_start = source.find("private fun AuthScreen(")
mode_start = source.find("private fun ModePill(", auth_start + 1)
if auth_start < 0 or mode_start < 0:
    raise SystemExit("Could not locate AuthScreen and ModePill boundaries")

auth = source[auth_start:mode_start]
label = 'Text("Skip signup for now · Preview app"'
global_count = source.count(label)
auth_count = auth.count(label)

# Some source archives no longer contain the optional preview shortcut at all.
# In that case there is nothing to scope; do not fail the entire Android build.
if global_count == 0:
    print("No signup preview shortcut exists in this source archive; scope step safely skipped.")
    raise SystemExit(0)
if global_count != 1 or auth_count != 1:
    raise SystemExit(
        "Preview CTA scope validation failed: "
        f"found {global_count} total label(s), {auth_count} inside AuthScreen. "
        "No source changes were written."
    )

# Rewire only the FAB immediately containing the signup preview label.
label_pos = auth.index(label)
fab_pos = auth.rfind("ExtendedFloatingActionButton(", 0, label_pos)
if fab_pos < 0:
    raise SystemExit("Preview label is not inside an ExtendedFloatingActionButton")
fab_end = auth.find(") {", fab_pos)
if fab_end < 0:
    raise SystemExit("Could not determine the preview FAB parameter block")
fab = auth[fab_pos:fab_end]
if "onClick = onPreview," not in fab:
    if "onClick = onBack," not in fab:
        raise SystemExit("Preview FAB has no recognized preview/back callback")
    fab = fab.replace("onClick = onBack,", "onClick = onPreview,", 1)
    auth = auth[:fab_pos] + fab + auth[fab_end:]

# Rename AuthScreen's callback parameter if this source still calls it onBack.
sig_end = auth.find(") {", 0)
if sig_end < 0:
    raise SystemExit("Could not parse AuthScreen's parameter list")
signature = auth[:sig_end]
if "onPreview:" not in signature:
    if "onBack: () -> Unit" not in signature:
        raise SystemExit("AuthScreen has no supported preview callback parameter")
    signature = signature.replace("onBack: () -> Unit", "onPreview: () -> Unit", 1)
    auth = signature + auth[sig_end:]

# Update only the AuthScreen invocation before its declaration.
call_start = source.find("AuthScreen(", 0, auth_start)
if call_start < 0:
    raise SystemExit("Could not locate the AuthScreen invocation")
call_end = source.find("\n            )", call_start)
if call_end < 0:
    raise SystemExit("Could not determine the AuthScreen invocation boundary")
call = source[call_start:call_end]
if "onPreview =" not in call:
    if "onBack =" not in call:
        raise SystemExit("AuthScreen invocation has no onPreview/onBack argument")
    call = call.replace("onBack =", "onPreview =", 1)
    source = source[:call_start] + call + source[call_end:]

# Reinsert the updated AuthScreen block at its original location.
source = source[:auth_start] + auth + source[mode_start:]

if source.count(label) != 1:
    raise SystemExit("Final preview CTA uniqueness check failed")
main.write_text(source, encoding="utf-8")
print("AuthScreen preview shortcut verified and scoped successfully.")
