from pathlib import Path

p = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not p.is_file():
    raise SystemExit("AmitySA MainActivity.kt was not found")
s = p.read_text(encoding="utf-8").replace("\r\n", "\n")

imports = [
    "import androidx.compose.animation.core.LinearEasing",
    "import androidx.compose.ui.graphics.drawscope.rotate",
]
for item in imports:
    if item not in s:
        anchor = "import androidx.compose.animation.core."
        pos = s.find(anchor)
        if pos < 0:
            raise SystemExit("Could not locate Compose imports")
        s = s[:pos] + item + "\n" + s[pos:]

if "private fun JarvisOrbitalCommandRing()" not in s:
    marker = "@Composable\nprivate fun SessionPageControls("
    if marker not in s:
        raise SystemExit("Could not locate active-page navigation controls")
    orbital = r"""@Composable
private fun JarvisOrbitalCommandRing() {
    val motion = rememberInfiniteTransition(label = "jarvisCommandOrbit")
    val rotation by motion.animateFloat(
        0f, 360f,
        infiniteRepeatable(tween(11000, easing = LinearEasing)),
        label = "commandOrbitRotation"
    )
    val pulse by motion.animateFloat(
        0.35f, 0.9f,
        infiniteRepeatable(tween(1250), repeatMode = RepeatMode.Reverse),
        label = "commandOrbitPulse"
    )
    Box(Modifier.fillMaxWidth().height(104.dp), contentAlignment = Alignment.Center) {
        Canvas(Modifier.fillMaxSize()) {
            val cx = size.width / 2f
            val cy = size.height / 2f
            val r = size.height * 0.36f
            val cyan = Color(0xFF65DDF5)
            drawCircle(cyan.copy(alpha = 0.22f), r * 1.42f, androidx.compose.ui.geometry.Offset(cx, cy), style = androidx.compose.ui.graphics.drawscope.Stroke(1.dp.toPx()))
            drawCircle(cyan.copy(alpha = 0.55f), r, androidx.compose.ui.geometry.Offset(cx, cy), style = androidx.compose.ui.graphics.drawscope.Stroke(1.dp.toPx()))
            rotate(rotation, androidx.compose.ui.geometry.Offset(cx, cy)) {
                drawOval(Color(0xFF9AF5FF).copy(alpha = 0.62f), topLeft = androidx.compose.ui.geometry.Offset(cx-r*1.55f, cy-r*0.38f), size = androidx.compose.ui.geometry.Size(r*3.1f, r*0.76f), style = androidx.compose.ui.graphics.drawscope.Stroke(1.dp.toPx()))
                drawCircle(Color(0xFFFFA36B).copy(alpha = pulse), 3.dp.toPx(), androidx.compose.ui.geometry.Offset(cx+r*1.55f, cy))
            }
            for (i in 0 until 12) {
                val a = Math.toRadians(i * 30.0 + rotation * 0.22)
                drawLine(cyan.copy(alpha = 0.48f),
                    androidx.compose.ui.geometry.Offset(cx+kotlin.math.cos(a).toFloat()*r*1.12f, cy+kotlin.math.sin(a).toFloat()*r*1.12f),
                    androidx.compose.ui.geometry.Offset(cx+kotlin.math.cos(a).toFloat()*r*1.30f, cy+kotlin.math.sin(a).toFloat()*r*1.30f), 1.dp.toPx())
            }
            // Animated holographic Earth core: sphere, latitude/longitude bands and rotating meridians.
            drawCircle(Color(0xFF062B49).copy(alpha = 0.96f), 15.dp.toPx(), androidx.compose.ui.geometry.Offset(cx, cy))
            drawCircle(Color(0xFF63E8FF).copy(alpha = 0.92f), 15.dp.toPx(), androidx.compose.ui.geometry.Offset(cx, cy), style = androidx.compose.ui.graphics.drawscope.Stroke(1.2.dp.toPx()))
            rotate(rotation * 1.35f, androidx.compose.ui.geometry.Offset(cx, cy)) {
                drawOval(Color(0xFF75EFFF).copy(alpha = 0.78f), topLeft = androidx.compose.ui.geometry.Offset(cx - 6.dp.toPx(), cy - 14.dp.toPx()), size = androidx.compose.ui.geometry.Size(12.dp.toPx(), 28.dp.toPx()), style = androidx.compose.ui.graphics.drawscope.Stroke(0.9.dp.toPx()))
                drawOval(Color(0xFF75EFFF).copy(alpha = 0.52f), topLeft = androidx.compose.ui.geometry.Offset(cx - 14.dp.toPx(), cy - 5.dp.toPx()), size = androidx.compose.ui.geometry.Size(28.dp.toPx(), 10.dp.toPx()), style = androidx.compose.ui.graphics.drawscope.Stroke(0.8.dp.toPx()))
                drawArc(Color(0xFF9AF5FF).copy(alpha = 0.72f), 205f, 130f, false, topLeft = androidx.compose.ui.geometry.Offset(cx - 11.dp.toPx(), cy - 11.dp.toPx()), size = androidx.compose.ui.geometry.Size(22.dp.toPx(), 22.dp.toPx()), style = androidx.compose.ui.graphics.drawscope.Stroke(1.dp.toPx()))
            }
            drawCircle(Color(0xFF9AF5FF).copy(alpha = pulse), 2.dp.toPx(), androidx.compose.ui.geometry.Offset(cx, cy))
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text("J.A.R.V.I.S", color = Color(0xFFE7FAFF), fontSize = 10.sp, fontWeight = FontWeight.Black, letterSpacing = 1.8.sp)
            Text("HOLOGRAPHIC COMMAND LINK", color = Color(0xFF65DDF5), fontSize = 7.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
        }
    }
}

"""
    s = s.replace(marker, orbital + marker, 1)

dropdown = '            DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }, modifier = Modifier.heightIn(max = 520.dp).background(t.card)) {\n'
if "                JarvisOrbitalCommandRing()\\n" not in s:
    if dropdown not in s:
        raise SystemExit("Could not locate active-page dropdown")
    s = s.replace(dropdown, dropdown + "                JarvisOrbitalCommandRing()\n", 1)

p.write_text(s, encoding="utf-8")
print("Installed the animated JARVIS orbital command ring in the active-page navigation menu.")
