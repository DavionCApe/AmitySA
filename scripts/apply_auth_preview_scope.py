from pathlib import Path

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not main.exists():
    raise SystemExit("AmitySA MainActivity.kt was not found")

s = main.read_text(encoding="utf-8")

# Keep the preview shortcut attached only to the signup/sign-in screen.
s = s.replace(
    "onBack = { showAuth = false },",
    "onPreview = { showAuth = false },",
    1,
)
s = s.replace(
    "onAuthenticated: (Account) -> Unit, onBack: () -> Unit, startRegistering: Boolean)",
    "onAuthenticated: (Account) -> Unit, onPreview: () -> Unit, startRegistering: Boolean)",
    1,
)
s = s.replace("onClick = onBack,\n          modifier = Modifier\n              .align(Alignment.BottomCenter)",
              "onClick = onPreview,\n          modifier = Modifier\n              .align(Alignment.BottomCenter)",
              1)

# Add explicit scope comments and fail safely if the expected UI structure changes.
marker = "      ExtendedFloatingActionButton(\n          onClick = onPreview,"
if marker not in s:
    raise SystemExit("Could not locate the signup preview button inside AuthScreen")

auth_start = s.find("private fun AuthScreen(")
auth_end = s.find("@Composable\nprivate fun ModePill", auth_start)
if auth_start < 0 or auth_end < 0:
    raise SystemExit("Could not determine the AuthScreen source boundaries")
auth_block = s[auth_start:auth_end]
label = 'Text("Skip signup for now · Preview app"'
if auth_block.count(label) != 1 or s.count(label) != 1:
    raise SystemExit("Preview shortcut must appear exactly once, inside AuthScreen")

if "// This preview-only action belongs exclusively to the signup/sign-in screen." not in auth_block:
    s = s[:auth_start] + auth_block.replace(
        "      ExtendedFloatingActionButton(\n          onClick = onPreview,",
        "      // This preview-only action belongs exclusively to the signup/sign-in screen.\n"
        "      // It is not rendered on the welcome preview, home screen, or feature pages.\n"
        "      ExtendedFloatingActionButton(\n          onClick = onPreview,",
        1,
    ) + s[auth_end:]

main.write_text(s, encoding="utf-8")
print("Preview shortcut is scoped to signup/sign-in only.")
