from pathlib import Path
import re

root = Path.cwd()
html_source = root / "web/jarvis-multi-ai.html"
if not html_source.is_file():
    raise SystemExit("web/jarvis-multi-ai.html is missing")
main = root / "app/src/main/java/com/amitysa/app/MainActivity.kt"
if not main.is_file():
    raise SystemExit("AmitySA MainActivity.kt was not found")

assets = root / "app/src/main/assets"
assets.mkdir(parents=True, exist_ok=True)
asset = assets / "jarvis-multi-ai.html"
asset.write_text(html_source.read_text(encoding="utf-8"), encoding="utf-8")

source = main.read_text(encoding="utf-8")
imports = [
    "import android.app.Activity",
    "import android.webkit.JavascriptInterface",
    "import android.webkit.WebView",
    "import android.webkit.WebViewClient",
    "import androidx.activity.compose.rememberLauncherForActivityResult",
    "import androidx.compose.ui.platform.LocalContext",
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
    val context = LocalContext.current
    val webViewState = remember { mutableStateOf<WebView?>(null) }
    val ioExecutor = remember { java.util.concurrent.Executors.newSingleThreadExecutor() }

    fun sendResult(payload: org.json.JSONObject) {
        val encoded = org.json.JSONObject.quote(payload.toString())
        webViewState.value?.post {
            webViewState.value?.evaluateJavascript(
                "window.jarvisFileResult && window.jarvisFileResult(JSON.parse($encoded));",
                null
            )
        }
    }

    fun deliverUri(uri: android.net.Uri?, kind: String) {
        if (uri == null) {
            sendResult(org.json.JSONObject()
                .put("success", false).put("cancelled", true)
                .put("message", "JARVIS: Selection was cancelled."))
            return
        }
        val resolver = context.contentResolver
        try {
            resolver.takePersistableUriPermission(
                uri, android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION
            )
        } catch (_: SecurityException) {
            // Some providers grant temporary access only.
        }
        if (kind == "folder") {
            sendResult(org.json.JSONObject()
                .put("success", true).put("type", "folder")
                .put("uri", uri.toString())
                .put("message", "JARVIS: Folder access is ready."))
            return
        }
        ioExecutor.execute {
            try {
                val name = resolver.query(
                    uri, arrayOf(android.provider.OpenableColumns.DISPLAY_NAME),
                    null, null, null
                )?.use { cursor ->
                    if (cursor.moveToFirst()) cursor.getString(0) else null
                } ?: "Selected file"
                val mime = resolver.getType(uri) ?: "application/octet-stream"
                val bytes = resolver.openInputStream(uri)?.use { input ->
                    val output = java.io.ByteArrayOutputStream()
                    val buffer = ByteArray(8192)
                    var total = 0
                    while (true) {
                        val count = input.read(buffer)
                        if (count < 0) break
                        total += count
                        if (total > 10 * 1024 * 1024) {
                            throw IllegalStateException("File exceeds the 10 MB inline transfer limit.")
                        }
                        output.write(buffer, 0, count)
                    }
                    output.toByteArray()
                } ?: throw IllegalStateException("The selected file is no longer available.")
                sendResult(org.json.JSONObject()
                    .put("success", true).put("type", kind)
                    .put("uri", uri.toString()).put("name", name)
                    .put("mimeType", mime).put("size", bytes.size)
                    .put("bytesBase64", android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP))
                    .put("message", "JARVIS: $name is ready for processing."))
            } catch (error: Exception) {
                sendResult(org.json.JSONObject()
                    .put("success", false).put("error", "FILE_READ_FAILED")
                    .put("message", "JARVIS: Could not read the selected file. " + (error.localizedMessage ?: "Unknown error")))
            }
        }
    }

    val filePicker = rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.OpenDocument()
    ) { uri -> deliverUri(uri, "file") }
    val audioPicker = rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.OpenDocument()
    ) { uri -> deliverUri(uri, "audio") }
    val folderPicker = rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.OpenDocumentTree()
    ) { uri -> deliverUri(uri, "folder") }

    AndroidView(
        modifier = Modifier.fillMaxSize(),
        factory = { viewContext ->
            WebView(viewContext).apply {
                webViewState.value = this
                setBackgroundColor(android.graphics.Color.TRANSPARENT)
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                settings.loadsImagesAutomatically = true
                settings.allowFileAccess = true
                settings.allowContentAccess = true
                settings.allowFileAccessFromFileURLs = false
                settings.allowUniversalAccessFromFileURLs = false
                settings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
                webViewClient = WebViewClient()
                addJavascriptInterface(object {
                    @JavascriptInterface fun onFeatureSelected(name: String) {
                        (viewContext as? Activity)?.runOnUiThread { onMenuAction(name) }
                    }
                    @JavascriptInterface fun onEmergencyRequested() {
                        (viewContext as? Activity)?.runOnUiThread { onSos() }
                    }
                    @JavascriptInterface fun pickFile() { (viewContext as? Activity)?.runOnUiThread { filePicker.launch(arrayOf("*/*")) } }
                    @JavascriptInterface fun pickAudio() { (viewContext as? Activity)?.runOnUiThread { audioPicker.launch(arrayOf("audio/*")) } }
                    @JavascriptInterface fun pickFolder() { (viewContext as? Activity)?.runOnUiThread { folderPicker.launch(null) } }
                    @JavascriptInterface fun openAudio(uriString: String) {
                        (viewContext as? Activity)?.runOnUiThread {
                            try {
                                val intent = android.content.Intent(android.content.Intent.ACTION_VIEW).apply {
                                    setDataAndType(android.net.Uri.parse(uriString), "audio/*")
                                    addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
                                }
                                viewContext.startActivity(android.content.Intent.createChooser(intent, "Open audio with"))
                            } catch (error: Exception) {
                                sendResult(org.json.JSONObject().put("success", false).put("message", "Unable to open audio: " + (error.localizedMessage ?: "No audio player available")))
                            }
                        }
                    }
                }, "AmityNative")
                loadUrl("file:///android_asset/jarvis-multi-ai.html")
            }
        },
        update = { view ->
            webViewState.value = view
            if (view.url == null) view.loadUrl("file:///android_asset/jarvis-multi-ai.html")
        }
    )
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

# Emit the exact generated Kotlin around the known compiler diagnostics.
generated_lines = source.splitlines()
print("---- Generated MainActivity.kt lines 1645-1680 ----")
for line_number in range(1645, min(1680, len(generated_lines)) + 1):
    print(f"{line_number}: {generated_lines[line_number - 1]}")

manifest = root / "app/src/main/AndroidManifest.xml"
if not manifest.is_file():
    raise SystemExit("AndroidManifest.xml was not found")

# Add only permissions used by the current network and audio features.
# MANAGE_EXTERNAL_STORAGE is intentionally not granted by default: broad
# storage access needs a separate user-approved Settings flow and a qualifying
# core use case. Use the Storage Access Framework for user-selected documents.
required_permissions = [
    "android.permission.INTERNET",
    "android.permission.ACCESS_NETWORK_STATE",
    "android.permission.ACCESS_WIFI_STATE",
    "android.permission.RECORD_AUDIO",
    "android.permission.MODIFY_AUDIO_SETTINGS",
]
manifest_text = manifest.read_text(encoding="utf-8")
for permission_name in required_permissions:
    if permission_name not in manifest_text:
        permission_xml = f'    <uses-permission android:name="{permission_name}" />\n'
        manifest_text = manifest_text.replace("<application", permission_xml + "    <application", 1)

if "android.hardware.microphone" not in manifest_text:
    feature_xml = '    <uses-feature android:name="android.hardware.microphone" android:required="false" />\n'
    manifest_text = manifest_text.replace("<application", feature_xml + "    <application", 1)

# Do not re-enable legacy external storage on modern Android targets.
manifest_text = manifest_text.replace(' android:requestLegacyExternalStorage="true"', "")
manifest.write_text(manifest_text, encoding="utf-8")

if "item { JarvisWebEmbed(onMenuAction, onSos) }" not in main.read_text(encoding="utf-8"):
    raise SystemExit("JARVIS Multi-AI HUD was not added to the dashboard")
if not asset.is_file():
    raise SystemExit("JARVIS OS V24.7 HUD asset was not packaged")
print("Embedded the interactive Earth HUD with native SAF file/audio/folder pickers and native result callbacks.")
