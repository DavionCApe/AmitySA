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
    val activity = LocalContext.current as? Activity
    androidx.compose.runtime.DisposableEffect(activity) {
        val decor = activity?.window?.decorView
        val previousFlags = decor?.systemUiVisibility ?: 0
        decor?.systemUiVisibility =
            android.view.View.SYSTEM_UI_FLAG_LAYOUT_STABLE or
            android.view.View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN or
            android.view.View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION or
            android.view.View.SYSTEM_UI_FLAG_FULLSCREEN or
            android.view.View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or
            android.view.View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        onDispose {
            if (decor != null) decor.systemUiVisibility = previousFlags
        }
    }
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
home_start = source.find("@Composable\nprivate fun HomeScreen(")
home_end = source.find("\n@Composable\nprivate fun ", home_start + 1)
home = source[home_start:home_end]
if "JarvisWebEmbed(" not in home:
    raise SystemExit("Primary dashboard is not connected to the supplied JARVIS HUD")
if "SYSTEM_UI_FLAG_IMMERSIVE_STICKY" not in home:
    raise SystemExit("JARVIS dashboard is not configured for immersive fullscreen")
if "WelcomeScreen(" in home or "JarvisDashboard(" in home:
    raise SystemExit("Legacy dashboard route remains inside the primary HomeScreen")
html = asset.read_text(encoding="utf-8")
for marker in ("JARVIS", "WORLD STATISTICS", "AUDIO WAVEFREQ"):
    if marker not in html:
        raise SystemExit("JARVIS HUD asset is missing expected content: " + marker)
print("Verified primary authenticated HomeScreen uses the JARVIS HUD in immersive fullscreen mode.")
