from pathlib import Path
import re

root = Path.cwd()
html_source = root / "web/jarvis-earth-hud.html"
if not html_source.is_file():
    raise SystemExit("web/jarvis-earth-hud.html is missing")
main = root / "app/src/main/java/com/amitysa/app/MainActivity.kt"
if not main.is_file():
    raise SystemExit("AmitySA MainActivity.kt was not found")

assets = root / "app/src/main/assets"
assets.mkdir(parents=True, exist_ok=True)
asset = assets / "jarvis-earth-hud.html"
asset.write_text(html_source.read_text(encoding="utf-8"), encoding="utf-8")

source = main.read_text(encoding="utf-8")
imports = [
    "import android.app.Activity",
    "import android.webkit.JavascriptInterface",
    "import android.webkit.WebView",
    "import android.webkit.WebViewClient",
    "import androidx.compose.ui.viewinterop.AndroidView",
]
for item in imports:
    if item not in source:
        package = re.search(r"(?m)^package [^\n]+\n", source)
        if not package:
            raise SystemExit("Could not locate Kotlin package declaration")
        source = source[:package.end()] + "\n" + item + source[package.end():]

# Route HUD feature taps into the existing dashboard callbacks.
old_item = "item { JarvisWebEmbed() }"
new_item = "item { JarvisWebEmbed(onMenuAction, onSos) }"
if new_item not in source:
    if old_item in source:
        source = source.replace(old_item, new_item, 1)
    else:
        marker = "            item { JarvisRadar(online, children, zones) }"
        if marker not in source:
            raise SystemExit("Could not locate JarvisRadar insertion point")
        source = source.replace(marker, marker + "\n            " + new_item, 1)

# Replace an earlier version of this composable if present.
start = source.find("@Composable\nprivate fun JarvisWebEmbed(")
if start >= 0:
    end = source.find("\n@Composable\nprivate fun JarvisStatus(", start)
    if end < 0:
        raise SystemExit("Could not locate JarvisStatus after JarvisWebEmbed")
    source = source[:start] + source[end:]

marker = "@Composable\nprivate fun JarvisStatus("
if marker not in source:
    raise SystemExit("Could not locate JarvisStatus composable insertion point")

component = r'''@Composable
private fun JarvisWebEmbed(
    onMenuAction: (String) -> Unit,
    onSos: () -> Unit
) {
    val t = LocalAmity.current
    Card(
        Modifier.padding(horizontal = 16.dp).fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xF0061422)),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xAA00E5FF))
    ) {
        AndroidView(
            modifier = Modifier.fillMaxWidth().height(690.dp)
                .clip(RoundedCornerShape(14.dp)),
            factory = { context ->
                WebView(context).apply {
                    settings.javaScriptEnabled = true
                    settings.domStorageEnabled = true
                    settings.loadsImagesAutomatically = true
                    settings.allowFileAccess = true
                    settings.allowContentAccess = false
                    settings.allowFileAccessFromFileURLs = false
                    settings.allowUniversalAccessFromFileURLs = false
                    webViewClient = WebViewClient()
                    addJavascriptInterface(object {
                        @JavascriptInterface
                        fun onFeatureSelected(name: String) {
                            (context as? Activity)?.runOnUiThread {
                                onMenuAction(name)
                            }
                        }

                        @JavascriptInterface
                        fun onEmergencyRequested() {
                            (context as? Activity)?.runOnUiThread {
                                onSos()
                            }
                        }
                    }, "AmityNative")
                    loadUrl("file:///android_asset/jarvis-earth-hud.html")
                }
            },
            update = { view ->
                if (view.url == null) {
                    view.loadUrl("file:///android_asset/jarvis-earth-hud.html")
                }
            }
        )
    }
}

'''
source = source.replace(marker, component + marker, 1)

# Persistent native emergency dock anchored to the dashboard viewport.
dock_marker = '        AnimatedVisibility(showTop, Modifier.align(Alignment.BottomEnd)'
dock = r'''        Row(
            Modifier.align(Alignment.BottomCenter)
                .fillMaxWidth()
                .navigationBarsPadding()
                .padding(horizontal = 16.dp, vertical = 10.dp)
                .clip(RoundedCornerShape(14.dp))
                .background(Color(0xF02A190B))
                .clickable { onSos() }
                .padding(horizontal = 14.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("SOS", color = Color(0xFF171006), fontSize = 11.sp,
                fontWeight = FontWeight.Black,
                modifier = Modifier.clip(RoundedCornerShape(8.dp))
                    .background(Color(0xFFFF9100)).padding(horizontal = 10.dp, vertical = 8.dp))
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text("EMERGENCY SERVICES", color = Color(0xFFFFD09A),
                    fontSize = 10.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp)
                Text("Tap for the AmitySA emergency response action",
                    color = Color(0xFFB99A78), fontSize = 8.sp)
            }
            Text("OPEN  ›", color = Color(0xFFFF9100), fontSize = 9.sp,
                fontWeight = FontWeight.Bold)
        }
'''
if dock_marker not in source:
    raise SystemExit("Could not locate dashboard floating control insertion point")
if 'Text("EMERGENCY SERVICES"' not in source:
    source = source.replace(dock_marker, dock + "\n" + dock_marker, 1)
main.write_text(source, encoding="utf-8")

manifest = root / "app/src/main/AndroidManifest.xml"
if manifest.is_file():
    text = manifest.read_text(encoding="utf-8")
    permission = '<uses-permission android:name="android.permission.INTERNET" />'
    if "android.permission.INTERNET" not in text:
        text = text.replace("<application", permission + "\n    <application", 1)
        manifest.write_text(text, encoding="utf-8")

if "item { JarvisWebEmbed(onMenuAction, onSos) }" not in main.read_text(encoding="utf-8"):
    raise SystemExit("JARVIS Earth HUD was not added to the dashboard")
if not asset.is_file():
    raise SystemExit("JARVIS Earth HUD asset was not packaged")
print("Embedded the interactive Earth HUD in native Compose and connected feature/emergency taps to existing dashboard callbacks.")
