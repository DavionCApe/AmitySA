from pathlib import Path
import re

p = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
s = p.read_text(encoding="utf-8")

def add_import(line: str):
    global s
    if line not in s:
        marker = "import androidx.compose.animation.core.infiniteRepeatable\n"
        if marker not in s:
            raise SystemExit("Floating logo upgrade stopped: animation import anchor not found")
        s = s.replace(marker, marker + line + "\n", 1)

add_import("import androidx.compose.animation.core.animateFloat")
add_import("import androidx.compose.ui.draw.shadow")
add_import("import androidx.compose.foundation.border")

# Locate the logo image inside Header rather than relying on a brittle exact
# indentation/string match (other UI generation steps adjust the header).
header_match = re.search(r"@Composable\s+private fun Header\([^)]*\)\s*\{", s)
if not header_match:
    raise SystemExit("Floating logo upgrade stopped: Header composable not found")
header_start = header_match.end()
next_composable = s.find("\n@Composable", header_start)
header_end = next_composable if next_composable >= 0 else len(s)
header = s[header_start:header_end]
image_match = re.search(r"Image\s*\(", header)
if not image_match:
    raise SystemExit("Floating logo upgrade stopped: no image found in Header")
image_start = image_match.start()
open_paren = header.find("(", image_start)
depth = 0
image_end = None
for index in range(open_paren, len(header)):
    if header[index] == "(":
        depth += 1
    elif header[index] == ")":
        depth -= 1
        if depth == 0:
            image_end = index + 1
            break
if image_end is None:
    raise SystemExit("Floating logo upgrade stopped: could not parse Header image call")
image_block = header[image_start:image_end]
if "painterResource(R.drawable.amity_logo)" not in image_block:
    raise SystemExit("Floating logo upgrade stopped: Header image is not the AmitySA logo")
new_image = '''FloatingAmityLogo(
            modifier = Modifier.fillMaxWidth(0.7f).widthIn(max = 320.dp)
        )'''
header = header[:image_start] + new_image + header[image_end:]
s = s[:header_start] + header + s[header_end:]

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
        modifier = modifier.padding(horizontal = 8.dp, vertical = 10.dp),
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
if "private fun FloatingAmityLogo" not in s:
    anchor = re.search(r"@Composable\s+private fun Header\(", s)
    if not anchor:
        raise SystemExit("Floating logo upgrade stopped: Header insertion point not found")
    s = s[:anchor.start()] + component + s[anchor.start():]

p.write_text(s, encoding="utf-8")
print("AmitySA home header now uses the existing logo with a gentle 3D float, tilt and pulsing neon halo.")
