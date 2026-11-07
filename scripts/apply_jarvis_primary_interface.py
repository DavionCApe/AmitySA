from pathlib import Path

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not main.is_file():
    raise SystemExit("AmitySA MainActivity.kt was not found")

source = main.read_text(encoding="utf-8")
start = source.find("@Composable\nprivate fun HomeScreen(")
if start < 0:
    raise SystemExit("Could not locate the generated HomeScreen composable")

end = source.find("\n@Composable\nprivate fun ", start + 1)
if end < 0:
    raise SystemExit("Could not locate the end of HomeScreen")

replacement = """@Composable
private fun HomeScreen(
    account: Account,
    onSignOut: () -> Unit,
    online: Boolean,
    onOpenThemes: () -> Unit,
    onSos: () -> Unit,
    onAction: (QuickAction) -> Unit,
    onMenuAction: (String) -> Unit
) {
    Box(Modifier.fillMaxSize().background(Color(0xFF020813))) {
        JarvisWebEmbed(
            onMenuAction = { action ->
                if (action == "Sign out") onSignOut() else onMenuAction(action)
            },
            onSos = onSos
        )
    }
}
"""
source = source[:start] + replacement + source[end:]
main.write_text(source, encoding="utf-8")

asset = Path("app/src/main/assets/jarvis-multi-ai.html")
if not asset.is_file():
    raise SystemExit("JARVIS OS V24.7 HTML asset was not packaged")
if "JarvisWebEmbed(" not in source:
    raise SystemExit("Primary dashboard is not connected to the supplied JARVIS HUD")
if "private fun HomeScreen(" not in source:
    raise SystemExit("HomeScreen replacement did not complete")
print("Replaced the authenticated home dashboard with the supplied full-screen JARVIS OS V24.7 interface.")
