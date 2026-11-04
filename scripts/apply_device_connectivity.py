from pathlib import Path
import re

root = Path.cwd()
manifest = root / "app/src/main/AndroidManifest.xml"
if not manifest.is_file():
    raise SystemExit("AndroidManifest.xml was not found")

xml = manifest.read_text(encoding="utf-8")
permissions = [
    '    <uses-permission android:name="android.permission.INTERNET" />',
    '    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />',
    '    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />',
    '    <uses-permission android:name="android.permission.CHANGE_WIFI_STATE" />',
    '    <uses-permission android:name="android.permission.BLUETOOTH" android:maxSdkVersion="30" />',
    '    <uses-permission android:name="android.permission.BLUETOOTH_ADMIN" android:maxSdkVersion="30" />',
    '    <uses-permission android:name="android.permission.BLUETOOTH_SCAN" />',
    '    <uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />',
]
for entry in permissions:
    name = re.search(r'android:name="([^"]+)"', entry).group(1)
    if not re.search(r'<uses-permission[^>]*android:name="' + re.escape(name) + r'"', xml):
        xml = xml.replace("<manifest", "<manifest", 1)
        pos = xml.find(">", xml.find("<manifest"))
        if pos < 0:
            raise SystemExit("Could not locate manifest opening tag")
        xml = xml[:pos + 1] + "\n" + entry + xml[pos + 1:]
# Declare optional hardware so devices without Bluetooth/Wi-Fi can still install.
features = [
    '    <uses-feature android:name="android.hardware.bluetooth" android:required="false" />',
    '    <uses-feature android:name="android.hardware.wifi" android:required="false" />',
    '    <uses-feature android:name="android.hardware.bluetooth_le" android:required="false" />',
]
for entry in features:
    name = re.search(r'android:name="([^"]+)"', entry).group(1)
    if not re.search(r'<uses-feature[^>]*android:name="' + re.escape(name) + r'"', xml):
        pos = xml.find(">", xml.find("<manifest"))
        xml = xml[:pos + 1] + "\n" + entry + xml[pos + 1:]
manifest.write_text(xml, encoding="utf-8")

package_dir = root / "app/src/main/java/com/amitysa/app"
package_dir.mkdir(parents=True, exist_ok=True)
helper = package_dir / "DeviceConnectivity.kt"
helper.write_text(r'''package com.amitysa.app

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.pm.PackageManager
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager
import android.os.Build
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager

/**
 * Version-aware, permission-aware connectivity checks for AmitySA.
 * This class checks device capability and status only; it never enables radios,
 * scans for nearby devices, pairs devices, or changes Wi-Fi settings.
 */
object DeviceConnectivity {
    fun requiredBluetoothPermissions(): Array<String> =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            arrayOf(Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            emptyArray()
        }

    fun hasBluetoothPermissions(context: Context): Boolean =
        requiredBluetoothPermissions().all {
            context.checkSelfPermission(it) == PackageManager.PERMISSION_GRANTED
        }

    fun requestBluetoothPermissions(activity: Activity, requestCode: Int) {
        val missing = requiredBluetoothPermissions().filter {
            activity.checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isNotEmpty()) {
            activity.requestPermissions(missing.toTypedArray(), requestCode)
        }
    }

    fun isBluetoothSupported(context: Context): Boolean {
        val manager = context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
        return manager?.adapter != null
    }

    fun isBluetoothEnabled(context: Context): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !hasBluetoothPermissions(context)) return false
        val manager = context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
        return try { manager?.adapter?.isEnabled == true } catch (_: SecurityException) { false }
    }

    fun isWifiSupported(context: Context): Boolean =
        context.packageManager.hasSystemFeature(PackageManager.FEATURE_WIFI)

    @Suppress("DEPRECATION")
    fun isWifiEnabled(context: Context): Boolean {
        if (!isWifiSupported(context)) return false
        return try {
            val manager = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as? WifiManager
            manager?.isWifiEnabled == true
        } catch (_: SecurityException) { false }
    }

    fun hasInternet(context: Context): Boolean {
        val manager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
            ?: return false
        val network = manager.activeNetwork ?: return false
        val capabilities = manager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
            capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }

    fun isUsingWifi(context: Context): Boolean {
        val manager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
            ?: return false
        val network = manager.activeNetwork ?: return false
        val capabilities = manager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
    }
}
''', encoding="utf-8")
print("Added version-aware Bluetooth permission checks, Wi-Fi/network status checks, and optional hardware declarations.")
