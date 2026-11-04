from pathlib import Path
import re

root = Path.cwd()
manifest = root / "app/src/main/AndroidManifest.xml"
if not manifest.is_file():
    raise SystemExit("AndroidManifest.xml was not found")
xml = manifest.read_text(encoding="utf-8")
for entry in [
    '    <uses-permission android:name="android.permission.BLUETOOTH_ADVERTISE" />',
    '    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" android:maxSdkVersion="30" />',
]:
    name = re.search(r'android:name="([^"]+)"', entry).group(1)
    if not re.search(r'<uses-permission[^>]*android:name="' + re.escape(name) + r'"', xml):
        pos = xml.find(">", xml.find("<manifest"))
        xml = xml[:pos + 1] + "\n" + entry + xml[pos + 1:]
manifest.write_text(xml, encoding="utf-8")

target = root / "app/src/main/java/com/amitysa/app/NearbyBluetooth.kt"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(r'''package com.amitysa.app

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.*
import android.content.*
import android.content.pm.PackageManager
import android.os.Build
import java.io.Closeable
import java.util.UUID

/**
 * AmitySA nearby connectivity:
 * - Parent/child phones use a dedicated secure RFCOMM service after Android pairing.
 * - Classic and BLE accessories are discovered independently.
 * Blocking socket operations must run on Dispatchers.IO.
 * This does not silently enable Bluetooth or promise arbitrary accessory compatibility.
 */
object NearbyBluetooth {
    val PHONE_SERVICE: UUID = UUID.fromString("b83d9c2e-6b3a-4d8f-9a31-4f0d8e7a2c61")

    data class Device(val bluetooth: BluetoothDevice, val name: String?, val address: String, val ble: Boolean)

    private fun adapter(c: Context) =
        (c.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager)?.adapter

    fun requiredPermissions(): Array<String> = when {
        Build.VERSION.SDK_INT >= 31 -> arrayOf(
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.BLUETOOTH_ADVERTISE
        )
        Build.VERSION.SDK_INT >= 23 -> arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)
        else -> emptyArray()
    }

    fun missingPermissions(c: Context): List<String> = requiredPermissions().filter {
        c.checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED
    }

    fun isReady(c: Context): Boolean {
        if (missingPermissions(c).isNotEmpty()) return false
        return try { adapter(c)?.isEnabled == true } catch (_: SecurityException) { false }
    }

    fun enableRequest(): Intent = Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE)
    fun discoverableRequest(seconds: Int = 120): Intent =
        Intent(BluetoothAdapter.ACTION_REQUEST_DISCOVERABLE).putExtra(
            BluetoothAdapter.EXTRA_DISCOVERABLE_DURATION, seconds.coerceIn(60, 300)
        )

    @SuppressLint("MissingPermission")
    fun pairedDevices(c: Context): List<Device> {
        if (missingPermissions(c).isNotEmpty()) return emptyList()
        return try {
            adapter(c)?.bondedDevices.orEmpty().map { Device(it, it.name, it.address, false) }
        } catch (_: SecurityException) { emptyList() }
    }

    @SuppressLint("MissingPermission")
    fun requestPairing(c: Context, device: BluetoothDevice): Boolean {
        if (missingPermissions(c).isNotEmpty()) return false
        return try { device.bondState == BluetoothDevice.BOND_BONDED || device.createBond() }
        catch (_: SecurityException) { false }
    }

    class ClassicScan(
        private val context: Context,
        private val onFound: (Device) -> Unit,
        private val onFinished: () -> Unit
    ) : Closeable {
        private var registered = false
        private val receiver = object : BroadcastReceiver() {
            @SuppressLint("MissingPermission")
            override fun onReceive(c: Context?, i: Intent?) {
                when (i?.action) {
                    BluetoothDevice.ACTION_FOUND -> {
                        val d = if (Build.VERSION.SDK_INT >= 33)
                            i.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE, BluetoothDevice::class.java)
                        else {
                            @Suppress("DEPRECATION")
                            i.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
                        }
                        if (d != null) try { onFound(Device(d, d.name, d.address, false)) }
                        catch (_: SecurityException) { }
                    }
                    BluetoothAdapter.ACTION_DISCOVERY_FINISHED -> onFinished()
                }
            }
        }

        @SuppressLint("MissingPermission")
        fun start(): Boolean {
            if (missingPermissions(context).isNotEmpty()) return false
            val a = adapter(context) ?: return false
            return try {
                val filter = IntentFilter().apply {
                    addAction(BluetoothDevice.ACTION_FOUND)
                    addAction(BluetoothAdapter.ACTION_DISCOVERY_FINISHED)
                }
                if (Build.VERSION.SDK_INT >= 33)
                    context.registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED)
                else {
                    @Suppress("DEPRECATION")
                    context.registerReceiver(receiver, filter)
                }
                registered = true
                if (a.isDiscovering) a.cancelDiscovery()
                a.startDiscovery()
            } catch (_: SecurityException) { close(); false }
        }

        @SuppressLint("MissingPermission")
        override fun close() {
            try { adapter(context)?.cancelDiscovery() } catch (_: SecurityException) { }
            if (registered) {
                try { context.unregisterReceiver(receiver) } catch (_: IllegalArgumentException) { }
                registered = false
            }
        }
    }

    class BleScan(
        private val context: Context,
        private val onFound: (Device, Int) -> Unit,
        private val onError: (Int) -> Unit = {}
    ) : Closeable {
        private var scanner: BluetoothLeScanner? = null
        private val callback = object : ScanCallback() {
            @SuppressLint("MissingPermission")
            override fun onScanResult(type: Int, result: ScanResult) {
                val d = result.device
                try {
                    onFound(Device(d, d.name ?: result.scanRecord?.deviceName, d.address, true), result.rssi)
                } catch (_: SecurityException) { }
            }
            override fun onScanFailed(code: Int) = onError(code)
        }

        @SuppressLint("MissingPermission")
        fun start(): Boolean {
            if (missingPermissions(context).isNotEmpty()) return false
            return try {
                scanner = adapter(context)?.bluetoothLeScanner ?: return false
                scanner?.startScan(callback)
                true
            } catch (_: SecurityException) { false }
        }

        @SuppressLint("MissingPermission")
        override fun close() {
            try { scanner?.stopScan(callback) } catch (_: SecurityException) { }
            scanner = null
        }
    }

    /** Call from Dispatchers.IO; both users must approve pairing in Android first. */
    @SuppressLint("MissingPermission")
    fun connectPhone(c: Context, device: BluetoothDevice): BluetoothSocket {
        check(missingPermissions(c).isEmpty()) { "Bluetooth permissions are required" }
        check(device.bondState == BluetoothDevice.BOND_BONDED) {
            "Pair the phones in Android Bluetooth settings first"
        }
        adapter(c)?.cancelDiscovery()
        return device.createRfcommSocketToServiceRecord(PHONE_SERVICE).also { it.connect() }
    }

    /** Call from Dispatchers.IO on the phone waiting for its parent/child peer. */
    @SuppressLint("MissingPermission")
    fun waitForPhone(c: Context): BluetoothSocket {
        check(missingPermissions(c).isEmpty()) { "Bluetooth permissions are required" }
        val server = (adapter(c) ?: error("Bluetooth is unavailable"))
            .listenUsingRfcommWithServiceRecord("AmitySA", PHONE_SERVICE)
        return server.use { it.accept() }
    }

    /** BLE accessory service support is manufacturer-specific; inspect GATT services after connect. */
    @SuppressLint("MissingPermission")
    fun connectBle(c: Context, device: BluetoothDevice, callback: BluetoothGattCallback): BluetoothGatt {
        check(missingPermissions(c).isEmpty()) { "Bluetooth permissions are required" }
        return device.connectGatt(c, false, callback, BluetoothDevice.TRANSPORT_LE)
    }

    fun close(socket: BluetoothSocket?) { try { socket?.close() } catch (_: Exception) { } }
}
''', encoding="utf-8")
print("Added AmitySA phone-to-phone Bluetooth transport plus Classic/BLE accessory discovery and connection primitives.")
