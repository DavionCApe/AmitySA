from pathlib import Path

p = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
s = p.read_text(encoding="utf-8")

def add_import(line: str):
    global s
    if line not in s:
        s = s.replace("import androidx.compose.animation.core.infiniteRepeatable\n",
                      "import androidx.compose.animation.core.infiniteRepeatable\n" + line + "\n", 1)

add_import("import androidx.compose.animation.core.animateFloat")
add_import("import androidx.compose.ui.draw.shadow")
add_import("import androidx.compose.foundation.border")

old = '''        Image(
            painter = painterResource(R.drawable.amity_logo),
            contentDescription = "AmitySA logo",
            modifier = Modifier.fillMaxWidth(0.7f).widthIn(max = 320.dp)
        )'''
new = '''        FloatingAmityLogo(
            modifier = Modifier.fillMaxWidth(0.7f).widthIn(max = 320.dp)
        )'''
if s.count(old) != 1:
    raise SystemExit(f"Floating logo upgrade stopped: expected one home header logo, found {s.count(old)}")
s = s.replace(old, new, 1)

anchor = "@Composable\nprivate fun Header(username: String, onOpenThemes: () -> Unit) {"
component = '''@Composable
private fun FloatingAmityLogo(modifier: Modifier = Modifier) {
    val motion = rememberInfiniteTransition(label = "amityLogoFloat")
    val floatY by motion.animateFloat(
        initialValue = -5f,
        targetValue = 5f,
        animationSpec = infiniteRepeatable(
            animation = tween(2600, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "logoFloatY"
    )
    val tilt by motion.animateFloat(
        initialValue = -2.2f,
        targetValue = 2.2f,
        animationSpec = infiniteRepeatable(
            animation = tween(3400, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "logoTilt"
    )
    val glow by motion.animateFloat(
        initialValue = 0.20f,
        targetValue = 0.48f,
        animationSpec = infiniteRepeatable(
            animation = tween(1800, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "logoGlow"
    )

    Box(
        modifier = modifier
            .padding(horizontal = 8.dp, vertical = 10.dp),
        contentAlignment = Alignment.Center
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth(0.82f)
                .height(112.dp)
                .graphicsLayer { alpha = glow }
                .background(
                    Brush.radialGradient(
                        listOf(Color(0xFF18CFFF), Color(0xFF765BFF).copy(alpha = 0.48f), Color.Transparent)
                    ),
                    CircleShape
                )
        )
        Image(
            painter = painterResource(R.drawable.amity_logo),
            contentDescription = "AmitySA floating 3D logo",
            modifier = Modifier
                .fillMaxWidth()
                .shadow(18.dp, RoundedCornerShape(28.dp), clip = false)
                .graphicsLayer {
                    translationY = floatY
                    rotationY = tilt
                    rotationX = -tilt * 0.45f
                    scaleX = 1.015f
                    scaleY = 1.015f
                    cameraDistance = 20f * density
                }
        )
    }
}

'''
if anchor not in s:
    raise SystemExit("Floating logo upgrade stopped: Header insertion point not found")
if "private fun FloatingAmityLogo" not in s:
    s = s.replace(anchor, component + anchor, 1)

p.write_text(s, encoding="utf-8")
print("AmitySA home header now uses the existing logo with a gentle 3D float, tilt and pulsing neon halo.")
