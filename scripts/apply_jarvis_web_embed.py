from pathlib import Path
import re

root = Path.cwd()
html_source = root / "web/jarvis-multi-ai.html"
if not html_source.is_file():
    raise SystemExit("web/jarvis-multi-ai.html is missing; cannot embed the JARVIS web interface")

main = root / "app/src/main/java/com/amitysa/app/MainActivity.kt"
if not main.is_file():
    raise SystemExit("AmitySA MainActivity.kt was not found")

# Package the standalone prototype as a local Android asset so the embedded
# WebView loads the app-owned file rather than a remote website.
assets = root / "app/src/main/assets"
assets.mkdir(parents=True, exist_ok=True)
(assets / "jarvis-multi-ai.html").write_text(html_source.read_text(encoding="utf-8"), encoding="utf-8")

source = main.read_text(encoding="utf-8")
imports = [
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

# Add the full responsive HUD to the existing scrollable JARVIS dashboard.
marker = '            item { JarvisRadar(online, children, zones) }'
embed_item = marker + '\n            item { JarvisWebEmbed() }'
if "item { JarvisWebEmbed() }" not in source:
    if marker not in source:
        raise SystemExit("Could not locate JarvisRadar dashboard insertion point")
    source = source.replace(marker, embed_item, 1)

composable_marker = "@Composable\nprivate fun JarvisStatus("
if "private fun JarvisWebEmbed()" not in source:
    if composable_marker not in source:
        raise SystemExit("Could not locate JarvisStatus composable insertion point")
    component = r'''@Composable
private fun JarvisWebEmbed() {
    val t = LocalAmity.current
    Card(
        Modifier.padding(horizontal = 16.dp).fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xF0061422)),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xAA38DDF5))
    ) {
        Column(Modifier.fillMaxWidth().padding(10.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Column(Modifier.fillMaxWidth().padding(horizontal = 4.dp)) {
                Text("MULTI-AI WEB INTERFACE", color = Color(0xFF9AF5FF),
                    fontSize = 10.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.5.sp)
                Text("Embedded JARVIS HUD // Local application asset",
                    color = t.inkSoft, fontSize = 9.sp)
            }
            AndroidView(
                modifier = Modifier.fillMaxWidth().height(650.dp)
                    .clip(RoundedCornerShape(12.dp)),
                factory = { context ->
                    WebView(context).apply {
                        settings.javaScriptEnabled = true
                        settings.domStorageEnabled = true
                        settings.loadsImagesAutomatically = true
                        settings.allowFileAccess = true
                        settings.allowContentAccess = true
                        webViewClient = WebViewClient()
                        loadUrl("file:///android_asset/jarvis-multi-ai.html")
                    }
                },
                update = { view ->
                    if (view.url == null) view.loadUrl("file:///android_asset/jarvis-multi-ai.html")
                }
            )
        }
    }
}

'''
    source = source.replace(composable_marker, component + composable_marker, 1)

main.write_text(source, encoding="utf-8")

# Ensure network permission exists for the Three.js CDN and Google Fonts.
manifest = root / "app/src/main/AndroidManifest.xml"
if manifest.is_file():
    manifest_text = manifest.read_text(encoding="utf-8")
    permission = '<uses-permission android:name="android.permission.INTERNET" />'
    if "android.permission.INTERNET" not in manifest_text:
        manifest_text = manifest_text.replace("<application", permission + "\n    <application", 1)
        manifest.write_text(manifest_text, encoding="utf-8")

# Idempotence and packaging checks.
if "item { JarvisWebEmbed() }" not in main.read_text(encoding="utf-8"):
    raise SystemExit("JARVIS WebView dashboard item was not installed")
if not (assets / "jarvis-multi-ai.html").is_file():
    raise SystemExit("JARVIS HTML asset was not copied")

print("Embedded the JARVIS Multi-AI HTML HUD in the native AmitySA dashboard using an Android WebView and packaged local HTML asset.")
