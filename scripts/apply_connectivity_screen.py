from pathlib import Path

root = Path.cwd()
main = root / "app/src/main/java/com/amitysa/app/MainActivity.kt"
screen = root / "app/src/main/java/com/amitysa/app/ConnectivityScreen.kt"
if not main.is_file():
    raise SystemExit("MainActivity.kt missing after source extraction")
s = main.read_text(encoding="utf-8").replace("\r\n", "\n")

ui = r'''package com.amitysa.app

import android.annotation.SuppressLint
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.content.Intent
import android.bluetooth.BluetoothProfile
import android.bluetooth.BluetoothSocket
import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@SuppressLint("MissingPermission")
@Composable
fun ConnectivityScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val nearby = remember { mutableStateListOf<NearbyBluetooth.Device>() }
    var classicScan by remember { mutableStateOf<NearbyBluetooth.ClassicScan?>(null) }
    var bleScan by remember { mutableStateOf<NearbyBluetooth.BleScan?>(null) }
    var socket by remember { mutableStateOf<BluetoothSocket?>(null) }
    var gatt by remember { mutableStateOf<BluetoothGatt?>(null) }
    var status by remember { mutableStateOf("Bluetooth is not connected") }
    var scanning by remember { mutableStateOf(false) }
    var wifiOn by remember { mutableStateOf(DeviceConnectivity.isWifiEnabled(context)) }
    var internetOn by remember { mutableStateOf(DeviceConnectivity.hasInternet(context)) }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { results ->
        status = if (results.values.all { it }) "Permissions granted. Choose a connection option."
        else "Bluetooth permissions are needed to scan and connect."
    }
    val enableLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) {
        status = if (NearbyBluetooth.isReady(context)) "Bluetooth is ready."
        else "Bluetooth was not enabled."
    }

    fun ensurePermissions(action: () -> Unit) {
        val missing = NearbyBluetooth.missingPermissions(context)
        if (missing.isEmpty()) {
            if (NearbyBluetooth.isReady(context)) action()
            else enableLauncher.launch(NearbyBluetooth.enableRequest())
        } else {
            permissionLauncher.launch(missing.toTypedArray())
        }
    }

    fun stopScanning() {
        classicScan?.close()
        classicScan = null
        bleScan?.close()
        bleScan = null
        scanning = false
    }

    DisposableEffect(Unit) {
        onDispose {
            classicScan?.close()
            bleScan?.close()
            NearbyBluetooth.close(socket)
            gatt?.close()
        }
    }

    Column(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Bluetooth & Wi-Fi", style = MaterialTheme.typography.headlineSmall)
            TextButton(onClick = onBack) { Text("Back") }
        }
        Text("Connect family phones nearby, or discover compatible Bluetooth accessories.",
            style = MaterialTheme.typography.bodyMedium)
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Wi-Fi & internet", style = MaterialTheme.typography.titleMedium)
                Text("Wi-Fi: " + if (wifiOn) "On" else "Off")
                Text("Internet: " + if (internetOn) "Connected" else "Not connected")
                OutlinedButton(onClick = {
                    wifiOn = DeviceConnectivity.isWifiEnabled(context)
                    internetOn = DeviceConnectivity.hasInternet(context)
                }) { Text("Refresh connection status") }
                Text("AmitySA does not switch Wi-Fi on or off for you.", fontSize = 12.sp)
            }
        }
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Parent ↔ child phones", style = MaterialTheme.typography.titleMedium)
                Text("Both phones need AmitySA, Bluetooth enabled and user-approved Android pairing. Keep the phones nearby.",
                    style = MaterialTheme.typography.bodySmall)
                Text(status, color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.bodySmall)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = {
                        ensurePermissions {
                            try {
                                enableLauncher.launch(NearbyBluetooth.discoverableRequest())
                                status = "Approve visibility in Android. Then scan from the other phone."
                            } catch (e: Exception) { status = e.message ?: "Could not enable visibility." }
                        }
                    }, modifier = Modifier.weight(1f)) { Text("Make discoverable", fontSize = 11.sp) }
                    OutlinedButton(onClick = {
                        ensurePermissions {
                            stopScanning()
                            nearby.clear()
                            val scan = NearbyBluetooth.ClassicScan(context, { d ->
                                if (nearby.none { it.address == d.address }) nearby.add(d)
                            }, { scanning = false })
                            classicScan = scan
                            scanning = scan.start()
                            status = if (scanning) "Searching for nearby Bluetooth phones and devices…"
                            else "Could not start scan. Check permissions and Bluetooth."
                        }
                    }, modifier = Modifier.weight(1f)) { Text("Find phones", fontSize = 11.sp) }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = {
                        ensurePermissions {
                            scope.launch {
                                status = "Waiting for the other AmitySA phone…"
                                try {
                                    val connected = withContext(Dispatchers.IO) { NearbyBluetooth.waitForPhone(context) }
                                    socket = connected
                                    status = "Phone connection established."
                                } catch (e: Exception) { status = e.message ?: "Phone connection failed." }
                            }
                        }
                    }, modifier = Modifier.weight(1f)) { Text("Wait for phone", fontSize = 11.sp) }
                    OutlinedButton(onClick = {
                        stopScanning()
                        NearbyBluetooth.close(socket)
                        socket = null
                        status = "Disconnected."
                    }, modifier = Modifier.weight(1f)) { Text("Disconnect", fontSize = 11.sp) }
                }
                if (socket != null) Text("Connected over Bluetooth. This nearby link is not remote tracking.",
                    color = MaterialTheme.colorScheme.primary, fontSize = 12.sp)
            }
        }
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Bluetooth accessories", style = MaterialTheme.typography.titleMedium)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = {
                        ensurePermissions {
                            stopScanning()
                            nearby.clear()
                            val scan = NearbyBluetooth.ClassicScan(context, { d ->
                                if (nearby.none { it.address == d.address }) nearby.add(d)
                            }, { scanning = false })
                            classicScan = scan
                            scanning = scan.start()
                        }
                    }, modifier = Modifier.weight(1f)) { Text("Classic scan", fontSize = 11.sp) }
                    OutlinedButton(onClick = {
                        ensurePermissions {
                            stopScanning()
                            nearby.clear()
                            val scan = NearbyBluetooth.BleScan(context, { d, _ ->
                                if (nearby.none { it.address == d.address }) nearby.add(d)
                            }, { status = "BLE scan error: $it" })
                            bleScan = scan
                            scanning = scan.start()
                            if (!scanning) status = "BLE scan could not start."
                        }
                    }, modifier = Modifier.weight(1f)) { Text("BLE scan", fontSize = 11.sp) }
                }
                if (scanning) TextButton(onClick = { stopScanning() }) { Text("Stop scanning") }
                Text("Found devices: " + nearby.size, style = MaterialTheme.typography.bodySmall)
                LazyColumn(Modifier.heightIn(max = 230.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    items(nearby, key = { it.address }) { device ->
                        Card(shape = RoundedCornerShape(12.dp)) {
                            Column(Modifier.fillMaxWidth().padding(10.dp)) {
                                Text(device.name ?: "Unnamed device", style = MaterialTheme.typography.titleSmall)
                                Text((if (device.ble) "Bluetooth LE" else "Classic Bluetooth") + " • " + device.address,
                                    style = MaterialTheme.typography.bodySmall)
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    TextButton(onClick = {
                                        ensurePermissions {
                                            val ok = NearbyBluetooth.requestPairing(context, device.bluetooth)
                                            status = if (ok) "Pairing requested. Approve the Android system prompt."
                                            else "Pairing could not be started."
                                        }
                                    }) { Text("Pair") }
                                    TextButton(onClick = {
                                        ensurePermissions {
                                            if (device.ble) {
                                                try {
                                                    gatt?.close()
                                                    gatt = NearbyBluetooth.connectBle(context, device.bluetooth,
                                                        object : BluetoothGattCallback() {
                                                            override fun onConnectionStateChange(g: BluetoothGatt, code: Int, newState: Int) {
                                                                status = if (newState == BluetoothProfile.STATE_CONNECTED) {
                                                                    g.discoverServices()
                                                                    "BLE accessory connected. Checking supported services…"
                                                                } else "BLE accessory disconnected."
                                                            }
                                                            override fun onServicesDiscovered(g: BluetoothGatt, code: Int) {
                                                                status = if (code == BluetoothGatt.GATT_SUCCESS)
                                                                    "BLE connected. Accessory services discovered; supported functions depend on its manufacturer."
                                                                else "Could not read accessory services."
                                                            }
                                                        })
                                                    status = "Connecting to BLE accessory…"
                                                } catch (e: Exception) { status = e.message ?: "BLE connection failed." }
                                            } else {
                                                scope.launch {
                                                    try {
                                                        val connected = withContext(Dispatchers.IO) {
                                                            NearbyBluetooth.connectPhone(context, device.bluetooth)
                                                        }
                                                        socket = connected
                                                        status = "Phone/accessory Bluetooth socket connected."
                                                    } catch (e: Exception) {
                                                        status = e.message ?: "Connection failed. Pair first if required."
                                                    }
                                                }
                                            }
                                        }
                                    }) { Text("Connect") }
                                }
                            }
                        }
                    }
                }
                Text("Accessory features vary. AmitySA can discover BLE devices, but only devices with a supported service can exchange useful data.",
                    style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}
@Composable
fun AmitySettingsScreen(onBack: () -> Unit, onConnectivity: () -> Unit, onLegal: () -> Unit) {
    val context = LocalContext.current
    fun openSystemSettings(intent: Intent) {
        try { intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); context.startActivity(intent) }
        catch (_: Exception) {
            try { context.startActivity(Intent(android.provider.Settings.ACTION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
            catch (_: Exception) { }
        }
    }
    Column(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Settings", style = MaterialTheme.typography.headlineSmall)
            TextButton(onClick = onBack) { Text("Back") }
        }
        Text("Manage AmitySA, device permissions and connection preferences.", style = MaterialTheme.typography.bodyMedium)
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Connections", style = MaterialTheme.typography.titleMedium)
                Text("Bluetooth, Wi-Fi, parent/child phone pairing and accessories.")
                Button(onClick = onConnectivity, modifier = Modifier.fillMaxWidth()) { Text("Bluetooth & Wi-Fi") }
            }
        }
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Notifications", style = MaterialTheme.typography.titleMedium)
                Text("Manage AmitySA notification permission and notification channels in Android.")
                OutlinedButton(onClick = { openSystemSettings(Intent(android.provider.Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(android.provider.Settings.EXTRA_APP_PACKAGE, context.packageName)) }, modifier = Modifier.fillMaxWidth()) { Text("Notification settings") }
            }
        }
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Permissions & privacy", style = MaterialTheme.typography.titleMedium)
                Text("Review camera, location, nearby devices and other permissions granted to AmitySA.")
                OutlinedButton(onClick = { openSystemSettings(Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS, android.net.Uri.parse("package:" + context.packageName))) }, modifier = Modifier.fillMaxWidth()) { Text("App permissions") }
                OutlinedButton(onClick = onLegal, modifier = Modifier.fillMaxWidth()) { Text("Terms, privacy & safety") }
            }
        }
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Battery & background activity", style = MaterialTheme.typography.titleMedium)
                Text("Review battery restrictions if you expect background alerts or location updates. Android may still limit background work.")
                OutlinedButton(onClick = { openSystemSettings(Intent(android.provider.Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)) }, modifier = Modifier.fillMaxWidth()) { Text("Battery optimisation settings") }
            }
        }
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Accessibility", style = MaterialTheme.typography.titleMedium)
                Text("Open Android accessibility settings for system-wide text size, magnification and assistance features.")
                OutlinedButton(onClick = { openSystemSettings(Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS)) }, modifier = Modifier.fillMaxWidth()) { Text("Accessibility settings") }
            }
        }
        Text("Android controls sensitive permissions. AmitySA will request access when a feature needs it; you can change or revoke access at any time in Android settings.", style = MaterialTheme.typography.bodySmall)
    }
}

'''
screen.write_text(ui, encoding="utf-8")

# Add one home shortcut, one route and one screen branch. Fail closed if source shape changed.
# Keep device connectivity out of the home shortcuts. Add one Settings entry instead.
if 'QuickAction("⚙️", "Settings"' not in s:
    tile = next((line for line in s.splitlines() if "QuickAction(" in line and '"Cloud link"' in line), None)
    if tile is None:
        raise SystemExit("Could not locate Cloud link home shortcut")
    indent = tile[:len(tile)-len(tile.lstrip())]
    s = s.replace(tile, tile + "\n" + indent + 'QuickAction("⚙️", "Settings", "App preferences & device controls"),', 1)

app_start = s.index("fun AmityApp(")
app_end = s.index("\n// ---------- Connectivity ----------", app_start)
app = s[app_start:app_end]
cloud_action = 'action.title == "Cloud link" -> navigateTo("cloud")'
if cloud_action not in app:
    raise SystemExit("Could not locate Cloud link action handler")
if 'action.title == "Settings"' not in app:
    app = app.replace(cloud_action, cloud_action + '\n                        action.title == "Settings" -> navigateTo("settings")', 1)

home_branch = app.find("else HomeScreen(")
if home_branch < 0:
    raise SystemExit("Could not locate HomeScreen route")
if 'screen == "connectivity"' not in app:
    app = app[:home_branch] + 'else if (screen == "settings") AmitySettingsScreen(onBack = { goBack() }, onConnectivity = { navigateTo("connectivity") }, onLegal = { navigateTo("legal") })\n            else if (screen == "connectivity") ConnectivityScreen(onBack = { goBack() })\n            ' + app[home_branch:]
s = s[:app_start] + app + s[app_end:]
main.write_text(s, encoding="utf-8")
print("Added AmitySA Bluetooth & Wi-Fi screen with permission requests, Wi-Fi status, parent/child discoverability, scanning, pairing, phone connection, Classic/BLE accessory discovery and BLE GATT connection.")
