from pathlib import Path

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not main.is_file():
    raise SystemExit("AmitySA MainActivity.kt was not found")
s = main.read_text(encoding="utf-8")
start = s.find("@Composable\nprivate fun JarvisDashboard()
if start < 0:
    raise SystemExit("Could not locate JarvisDashboard composable")
# Find the next top-level composable after JarvisDashboard; replace the entire
# dashboard implementation so the old native dashboard is no longer rendered.
end = s.find("\n@Composable\nprivate fun JarvisStatus(, start)
if end < 0:
    raise SystemExit("Could not locate the end of JarvisDashboard")
replacement = '''@Composable
private fun JarvisDashboard(
    account: Account, online: Boolean, onOpenThemes: () -> Unit, onSos: () -> Unit,
    onAction: (QuickAction) -> Unit, onMenuAction: (String) -> Unit, onSignOut: () -> Unit
) {
    Box(Modifier.fillMaxSize().background(Color(0xFF040911))) {
        JarvisWebEmbed(onMenuAction, onSos)
    }
}
'''
s = s[:start] + replacement + s[end:]
main.write_text(s, encoding="utf-8")
asset = Path("app/src/main/assets/jarvis-multi-ai.html")
if not asset.is_file():
    raise SystemExit("Multi-AI HUD asset was not packaged")
if "JarvisWebEmbed(onMenuAction, onSos)" not in s:
    raise SystemExit("Primary dashboard is not connected to the Multi-AI HUD")
print("Replaced the native dashboard with the full-screen JARVIS Multi-AI interface.")
