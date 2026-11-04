from pathlib import Path

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not main.exists():
    raise SystemExit("AmitySA MainActivity.kt was not found")

s = main.read_text(encoding="utf-8")

imports = [
    "import androidx.compose.animation.core.LinearEasing",
    "import androidx.compose.animation.core.animateFloat",
    "import androidx.compose.animation.core.infiniteRepeatable",
    "import androidx.compose.animation.core.rememberInfiniteTransition",
    "import androidx.compose.animation.core.tween",
    "import androidx.compose.runtime.getValue",
]
for item in imports:
    if item not in s:
        # Place with imports before the first androidx import group terminator.
        idx = s.find("import androidx.")
        if idx < 0:
            raise SystemExit("Could not find Compose imports")
        s = s[:idx] + item + "\n" + s[idx:]

# Replace the static HUD canvas with an animated, non-interactive JARVIS layer.
start = s.find('        Canvas(modifier = Modifier.fillMaxSize()) {')
if start < 0:
    raise SystemExit("Existing FUI HUD Canvas was not found")
end_token = "        }\n        }\n    }\n}"
end = s.find(end_token, start)
if end < 0:
    raise SystemExit("Could not locate the end of the app-wide HUD overlay")
end += len("        }")
animated = """        val jarvisMotion = rememberInfiniteTransition(label = "jarvisMotion")
        val radarAngle by jarvisMotion.animateFloat(
            initialValue = 0f,
            targetValue = 360f,
            animationSpec = infiniteRepeatable(tween(9000, easing = LinearEasing)),
            label = "radarSweep"
        )
        val orbitAngle by jarvisMotion.animateFloat(
            initialValue = 0f,
            targetValue = 360f,
            animationSpec = infiniteRepeatable(tween(14000, easing = LinearEasing)),
            label = "orbitMotion"
        )
        val pulse by jarvisMotion.animateFloat(
            initialValue = 0.35f,
            targetValue = 0.95f,
            animationSpec = infiniteRepeatable(tween(1500), repeatMode = androidx.compose.animation.core.RepeatMode.Reverse),
            label = "hudPulse"
        )
        Canvas(modifier = Modifier.fillMaxSize()) {
            val cyan = Color(0x9956DFFF)
            val bright = Color(0xCCB9F5FF)
            val orange = Color(0x99FF9A38)
            val cx = size.width * 0.84f
            val cy = size.height * 0.22f
            val radius = (size.minDimension * 0.105f).coerceIn(34f, 88f)

            // Fine screen-edge brackets and technical registration marks.
            val inset = 12f
            val arm = 18f
            val stroke = 1.5f
            val corners = listOf(
                Pair(androidx.compose.ui.geometry.Offset(inset, inset), 1f to 1f),
                Pair(androidx.compose.ui.geometry.Offset(size.width-inset, inset), -1f to 1f),
                Pair(androidx.compose.ui.geometry.Offset(inset, size.height-inset), 1f to -1f),
                Pair(androidx.compose.ui.geometry.Offset(size.width-inset, size.height-inset), -1f to -1f)
            )
            corners.forEach { (p, d) ->
                drawLine(cyan, p, androidx.compose.ui.geometry.Offset(p.x + arm*d.first, p.y), stroke)
                drawLine(cyan, p, androidx.compose.ui.geometry.Offset(p.x, p.y + arm*d.second), stroke)
            }

            // Compact orbital scanner stays in the upper-right safe area.
            drawCircle(cyan, radius, androidx.compose.ui.geometry.Offset(cx, cy), style = androidx.compose.ui.graphics.drawscope.Stroke(1f))
            drawCircle(cyan.copy(alpha = 0.45f), radius * 0.68f, androidx.compose.ui.geometry.Offset(cx, cy), style = androidx.compose.ui.graphics.drawscope.Stroke(1f))
            drawCircle(cyan.copy(alpha = 0.30f), radius * 0.34f, androidx.compose.ui.geometry.Offset(cx, cy), style = androidx.compose.ui.graphics.drawscope.Stroke(1f))
            drawLine(cyan.copy(alpha = 0.35f), androidx.compose.ui.geometry.Offset(cx-radius, cy), androidx.compose.ui.geometry.Offset(cx+radius, cy), 0.8f)
            drawLine(cyan.copy(alpha = 0.35f), androidx.compose.ui.geometry.Offset(cx, cy-radius), androidx.compose.ui.geometry.Offset(cx, cy+radius), 0.8f)
            val radians = Math.toRadians(radarAngle.toDouble())
            val sx = cx + kotlin.math.cos(radians).toFloat() * radius
            val sy = cy + kotlin.math.sin(radians).toFloat() * radius
            drawLine(bright.copy(alpha = pulse), androidx.compose.ui.geometry.Offset(cx, cy), androidx.compose.ui.geometry.Offset(sx, sy), 2f)
            drawCircle(orange.copy(alpha = pulse), 3.2f, androidx.compose.ui.geometry.Offset(sx, sy))
            val orbit = Math.toRadians(orbitAngle.toDouble())
            val ox = cx + kotlin.math.cos(orbit).toFloat() * radius * 0.68f
            val oy = cy + kotlin.math.sin(orbit).toFloat() * radius * 0.68f
            drawCircle(bright.copy(alpha = pulse), 2.6f, androidx.compose.ui.geometry.Offset(ox, oy))

            // Short segmented telemetry rails, with a moving status pulse.
            val railY = 30f
            drawLine(cyan.copy(alpha = 0.55f), androidx.compose.ui.geometry.Offset(size.width*0.35f, railY), androidx.compose.ui.geometry.Offset(size.width*0.70f, railY), 1f)
            for (i in 0..8) {
                val x = size.width * (0.36f + i * 0.042f)
                val h = if (i % 3 == 0) 7f else 3f
                drawLine(cyan, androidx.compose.ui.geometry.Offset(x, railY-h), androidx.compose.ui.geometry.Offset(x, railY+h), 1f)
            }
            drawCircle(orange.copy(alpha = pulse), 2.5f, androidx.compose.ui.geometry.Offset(size.width*0.70f, railY))
            // Small animated signal nodes along the lower edge.
            for (i in 0..4) {
                val x = size.width * (0.12f + i * 0.045f)
                drawCircle(if (i == ((radarAngle / 72f).toInt() % 5)) bright else cyan.copy(alpha = 0.55f), if (i == ((radarAngle / 72f).toInt() % 5)) 3.2f else 1.8f, androidx.compose.ui.geometry.Offset(x, size.height-22f))
            }
        }"""
s = s[:start] + animated + s[end:]
main.write_text(s, encoding="utf-8")
print("Installed app-wide animated JARVIS HUD: rotating radar sweep, orbiting marker, pulsing alert nodes and telemetry rails.")
