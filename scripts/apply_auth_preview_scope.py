from pathlib import Path
import re

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not main.is_file():
    raise SystemExit(f"AmitySA MainActivity.kt was not found: {main}")

source = main.read_text(encoding="utf-8")

# Locate AuthScreen without depending on indentation or line-ending style.
start_match = re.search(r"(?m)^\s*private fun AuthScreen\s*\(", source)
if not start_match:
    raise SystemExit("Could not locate the AuthScreen declaration")

end_match = re.search(
    r"(?m)^\s*@Composable\s*\n\s*private fun ModePill\b",
    source[start_match.end():],
)
if not end_match:
    raise SystemExit("Could not determine where AuthScreen ends")

auth_start = start_match.start()
auth_end = start_match.end() + end_match.start()
auth = source[auth_start:auth_end]

label = 'Text("Skip signup for now · Preview app"'
if auth.count(label) != 1:
    raise SystemExit(
        "Expected exactly one 'Skip signup for now · Preview app' label "
        "inside AuthScreen; no source changes were written"
    )
if source.count(label) != 1:
    raise SystemExit(
        "The preview label also appears outside AuthScreen; refusing to "
        "change the wrong screen"
    )

# Find the FAB that owns the preview label, allowing arbitrary whitespace.
label_pos = auth.index(label)
fab_pos = auth.rfind("ExtendedFloatingActionButton(", 0, label_pos)
if fab_pos < 0:
    raise SystemExit(
        "Found the preview label, but could not find its "
        "ExtendedFloatingActionButton inside AuthScreen"
    )

fab_open = auth.find("(", fab_pos)
click_match = re.search(
    r"\bonClick\s*=\s*[^,\n]+,",
    auth[fab_open + 1:label_pos],
)
if not click_match:
    raise SystemExit(
        "Found the preview FAB, but could not identify its onClick callback"
    )

callback_start = fab_open + 1 + click_match.start()
callback_end = fab_open + 1 + click_match.end()
auth = auth[:callback_start] + "onClick = onPreview," + auth[callback_end:]

# Ensure AuthScreen exposes the preview callback.
sig_start = auth.find("private fun AuthScreen(")
sig_end = auth.find(") {", sig_start)
if sig_start < 0 or sig_end < 0:
    raise SystemExit("Could not parse the AuthScreen parameter list")
signature = auth[sig_start:sig_end]
if "onPreview:" not in signature:
    if "onBack: () -> Unit" in signature:
        signature = signature.replace("onBack: () -> Unit", "onPreview: () -> Unit", 1)
    else:
        raise SystemExit(
            "AuthScreen has no onPreview callback and no supported onBack "
            "parameter to migrate"
        )
    auth = auth[:sig_start] + signature + auth[sig_end:]

# Update only the AuthScreen call site, not unrelated onBack handlers.
call_match = re.search(
    r"(?s)(else\s+if\s*\(acc\s*==\s*null\)\s*AuthScreen\s*\()(.*?)(\n\s*\))",
    source,
)
if not call_match:
    raise SystemExit("Could not locate the unauthenticated AuthScreen call site")
call_args = call_match.group(2)
if "onPreview =" not in call_args:
    if "onBack =" in call_args:
        call_args = call_args.replace("onBack =", "onPreview =", 1)
    else:
        raise SystemExit("AuthScreen call site has no onPreview/onBack argument")
source = (
    source[:call_match.start()]
    + call_match.group(1) + call_args + call_match.group(3)
    + source[call_match.end():]
)

# Recalculate the AuthScreen block after the call-site edit.
start_match = re.search(r"(?m)^\s*private fun AuthScreen\s*\(", source)
end_match = re.search(
    r"(?m)^\s*@Composable\s*\n\s*private fun ModePill\b",
    source[start_match.end():],
)
auth_start = start_match.start()
auth_end = start_match.end() + end_match.start()
auth = source[auth_start:auth_end]

if "// Preview shortcut is intentionally scoped to AuthScreen only." not in auth:
    label_pos = auth.index(label)
    fab_pos = auth.rfind("ExtendedFloatingActionButton(", 0, label_pos)
    auth = (
        auth[:fab_pos]
        + "// Preview shortcut is intentionally scoped to AuthScreen only.\n      "
        + auth[fab_pos:]
    )
    source = source[:auth_start] + auth + source[auth_end:]

main.write_text(source, encoding="utf-8")
print("AuthScreen preview shortcut verified and scoped successfully.")
