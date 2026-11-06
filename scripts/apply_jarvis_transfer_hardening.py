from pathlib import Path
import shutil

root = Path.cwd()
main = root / "app/src/main/java/com/amitysa/app/MainActivity.kt"
html = root / "app/src/main/assets/jarvis-earth-hud.html"
vendor = root / "web/vendor/three.min.js"
if not main.is_file() or not html.is_file():
    raise SystemExit("JARVIS generated Kotlin or HTML asset is missing")
if not vendor.is_file() or vendor.stat().st_size < 10000:
    raise SystemExit("Locally vendored Three.js bundle is missing or incomplete")
assets = root / "app/src/main/assets"
shutil.copy2(vendor, assets / "three.min.js")
page = html.read_text(encoding="utf-8").replace(
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.min.js"></script>',
    '<script src="three.min.js"></script>'
)
if "cdnjs.cloudflare.com/ajax/libs/three.js" in page:
    raise SystemExit("External Three.js dependency remains in the HUD")
html.write_text(page, encoding="utf-8")

source = main.read_text(encoding="utf-8")
start = source.find("@Composable\nprivate fun JarvisWebEmbed(")
end = source.find("\n@Composable\nprivate fun JarvisStatus(", start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate generated JarvisWebEmbed composable")

component = r'''@Composable
private fun JarvisWebEmbed(
    onMenuAction: (String) -> Unit,
    onSos: () -> Unit
) {
    val context = LocalContext.current
    val webViewState = remember { mutableStateOf<WebView?>(null) }
    val ioExecutor = remember {
        java.util.concurrent.ThreadPoolExecutor(
            2, 4, 30L, java.util.concurrent.TimeUnit.SECONDS,
            java.util.concurrent.ArrayBlockingQueue(8),
            java.util.concurrent.ThreadPoolExecutor.AbortPolicy()
        )
    }
    val timeoutExecutor = remember {
        java.util.concurrent.Executors.newSingleThreadScheduledExecutor()
    }

    fun sendResult(payload: org.json.JSONObject) {
        val transferId = java.util.UUID.randomUUID().toString()
        val base64 = payload.optString("bytesBase64", "")
        payload.remove("bytesBase64")
        val encoded = org.json.JSONObject.quote(payload.toString())
        val chunks = if (base64.isEmpty()) emptyList() else base64.chunked(24 * 1024)
        webViewState.value?.post {
            val view = webViewState.value ?: return@post
            view.evaluateJavascript(
                "window.jarvisFileResult && window.jarvisFileResult(JSON.parse($encoded));",
                null
            )
            chunks.forEachIndexed { index, chunk ->
                val safeChunk = org.json.JSONObject.quote(chunk)
                view.evaluateJavascript(
                    "window.jarvisFileResultChunk && window.jarvisFileResultChunk('$transferId'," +
                        index + "," + chunks.size + "," + safeChunk + ");",
                    null
                )
            }
        }
    }

    fun deliverUri(uri: android.net.Uri?, kind: String) {
        if (uri == null) {
            sendResult(org.json.JSONObject().put("success", false)
                .put("cancelled", true).put("message", "JARVIS: Selection was cancelled."))
            return
        }
        val resolver = context.contentResolver
        try {
            resolver.takePersistableUriPermission(uri, android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
        } catch (_: SecurityException) {
            // Some providers grant temporary access only.
        }
        if (kind == "folder") {
            sendResult(org.json.JSONObject().put("success", true).put("type", "folder")
                .put("uri", uri.toString()).put("message", "JARVIS: Folder access is ready."))
            return
        }
        if (kind == "audio") {
            // Do not query or stream the provider on the UI thread. The original
            // SAF URI is enough to expose the external-player action for any size.
            val name = uri.lastPathSegment ?: "Selected audio"
            sendResult(org.json.JSONObject().put("success", true).put("type", "audio")
                .put("uri", uri.toString()).put("name", name).put("mimeType", "audio/*")
                .put("size", -1).put("message", "JARVIS: Audio is ready to open in your audio player."))
            return
        }

        val completed = java.util.concurrent.atomic.AtomicBoolean(false)
        try {
            val task = ioExecutor.submit {
                try {
                    val name = resolver.query(uri, arrayOf(android.provider.OpenableColumns.DISPLAY_NAME),
                        null, null, null)?.use { cursor -> if (cursor.moveToFirst()) cursor.getString(0) else null }
                        ?: "Selected file"
                    val mime = resolver.getType(uri) ?: "application/octet-stream"
                    val bytes = resolver.openInputStream(uri)?.use { input ->
                        val output = java.io.ByteArrayOutputStream()
                        val buffer = ByteArray(8192)
                        var total = 0
                        while (true) {
                            if (Thread.currentThread().isInterrupted) throw InterruptedException("Read cancelled.")
                            val count = input.read(buffer)
                            if (count < 0) break
                            total += count
                            if (total > 10 * 1024 * 1024) throw IllegalStateException("File exceeds the 10 MB inline transfer limit.")
                            output.write(buffer, 0, count)
                        }
                        output.toByteArray()
                    } ?: throw IllegalStateException("The selected file is no longer available.")
                    if (completed.compareAndSet(false, true)) {
                        sendResult(org.json.JSONObject().put("success", true).put("type", "file")
                            .put("uri", uri.toString()).put("name", name).put("mimeType", mime)
                            .put("size", bytes.size)
                            .put("bytesBase64", android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP))
                            .put("message", "JARVIS: $name transferred to the HUD in bounded chunks."))
                    }
                } catch (error: Exception) {
                    if (completed.compareAndSet(false, true)) {
                        sendResult(org.json.JSONObject().put("success", false).put("error", "FILE_READ_FAILED")
                            .put("message", "JARVIS: Could not read the selected file. " +
                                (error.localizedMessage ?: "Unknown error")))
                    }
                }
            }
            timeoutExecutor.schedule({
                if (completed.compareAndSet(false, true)) {
                    task.cancel(true)
                    sendResult(org.json.JSONObject().put("success", false).put("error", "FILE_READ_TIMEOUT")
                        .put("message", "JARVIS: File provider timed out. Try again or choose another provider."))
                }
            }, 45, java.util.concurrent.TimeUnit.SECONDS)
        } catch (_: java.util.concurrent.RejectedExecutionException) {
            sendResult(org.json.JSONObject().put("success", false).put("error", "FILE_QUEUE_FULL")
                .put("message", "JARVIS: File reader is busy. Wait and try again."))
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

    Card(
        Modifier.padding(horizontal = 16.dp).fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xF0061422)),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xAA00E5FF))
    ) {
        AndroidView(
            modifier = Modifier.fillMaxWidth().height(690.dp).clip(RoundedCornerShape(14.dp)),
            factory = { viewContext ->
                WebView(viewContext).apply {
                    webViewState.value = this
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
                            (viewContext as? Activity)?.runOnUiThread { onMenuAction(name) }
                        }
                        @JavascriptInterface
                        fun onEmergencyRequested() {
                            (viewContext as? Activity)?.runOnUiThread { onSos() }
                        }
                        @JavascriptInterface
                        fun pickFile() {
                            (viewContext as? Activity)?.runOnUiThread { filePicker.launch(arrayOf("*/*")) }
                        }
                        @JavascriptInterface
                        fun pickAudio() {
                            (viewContext as? Activity)?.runOnUiThread { audioPicker.launch(arrayOf("audio/*")) }
                        }
                        @JavascriptInterface
                        fun pickFolder() {
                            (viewContext as? Activity)?.runOnUiThread { folderPicker.launch(null) }
                        }
                        @JavascriptInterface
                        fun openAudio(uriString: String) {
                            (viewContext as? Activity)?.runOnUiThread {
                                try {
                                    val intent = android.content.Intent(android.content.Intent.ACTION_VIEW).apply {
                                        setDataAndType(android.net.Uri.parse(uriString), "audio/*")
                                        addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
                                    }
                                    viewContext.startActivity(android.content.Intent.createChooser(intent, "Open audio with"))
                                } catch (error: Exception) {
                                    sendResult(org.json.JSONObject().put("success", false)
                                        .put("error", "AUDIO_OPEN_FAILED")
                                        .put("message", "JARVIS: Unable to open audio. " +
                                            (error.localizedMessage ?: "No compatible player installed.")))
                                }
                            }
                        }
                    }, "AmityNative")
                    loadUrl("file:///android_asset/jarvis-earth-hud.html")
                }
            },
            update = { view ->
                webViewState.value = view
                if (view.url == null) view.loadUrl("file:///android_asset/jarvis-earth-hud.html")
            }
        )
    }
}

'''
source = source[:start] + component + source[end:]
main.write_text(source, encoding="utf-8")

page = html.read_text(encoding="utf-8")
needle = "window.jarvisFileResult=function(r){"
if needle not in page:
    raise SystemExit("Could not find JARVIS file result callback")
chunk_handler = """window.jarvisFileResultChunk=(id,index,total,chunk)=>{const key='jarvis-transfer-'+id;let transfer=window[key];if(!transfer){transfer=window[key]={parts:new Array(total),received:0,total};}if(!transfer.parts[index]){transfer.parts[index]=chunk;transfer.received++;}if(transfer.received===transfer.total){const result=window.jarvisLastFileResult;if(result){result.bytesBase64=transfer.parts.join('');window.jarvisFileBytesReady?.(result);}delete window[key];}};window.jarvisLastFileResult=null;"""
page = page.replace(needle, chunk_handler + needle)
page = page.replace("window.jarvisFileResult=function(r){if(!r){",
                    "window.jarvisFileResult=function(r){window.jarvisLastFileResult=r;if(!r){")
page = page.replace(");\\nwindow.jarvisFileResultChunk", ");window.jarvisFileResultChunk")
html.write_text(page, encoding="utf-8")

if "window.jarvisFileResultChunk" not in page or 'src="three.min.js"' not in page:
    raise SystemExit("HUD chunk receiver or local Three.js reference is missing")
print("Hardened file transfer, provider timeouts, direct audio URI playback, and local Three.js packaging.")
