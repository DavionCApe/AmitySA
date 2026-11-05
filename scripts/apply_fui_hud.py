from pathlib import Path

p = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
s = p.read_text(encoding="utf-8")

def add_import(line: str):
    global s
    if line not in s:
        marker = "import "
        pos = s.find(marker)
        if pos < 0:
            raise SystemExit("FUI/HUD upgrade stopped: Kotlin imports not found")
        s = s[:pos] + line + "\n" + s[pos:]

for line in [
    "import androidx.compose.foundation.Canvas",
    "import androidx.compose.ui.draw.alpha",
    "import androidx.compose.ui.layout.ContentScale",
    "import androidx.compose.ui.geometry.Offset",
    "import androidx.compose.ui.graphics.drawscope.Stroke",
    "import androidx.compose.animation.core.LinearEasing"
]:
    add_import(line)

component = r'''@Composable
private fun AmityHudBackdrop() {
    val motion = rememberInfiniteTransition(label = "amityHudMotion")
    val scanProgress by motion.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(5200, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "hudScanProgress"
    )
    Canvas(modifier = Modifier.fillMaxSize().alpha(0.20f)) {
        val cyan = Color(0xFF35DFFF)
        val violet = Color(0xFF8878FF)
        val red = Color(0xFFFF5478)
        val inset = 18.dp.toPx()
        val corner = 30.dp.toPx()
        val stroke = 1.dp.toPx()

        // Restrained holographic grid, kept faint behind the app content.
        for (i in 1..9) {
            val y = size.height * i / 10f
            drawLine(cyan.copy(alpha = 0.16f), Offset(0f, y), Offset(size.width, y), 0.55.dp.toPx())
        }
        for (i in 1..7) {
            val x = size.width * i / 8f
            drawLine(violet.copy(alpha = 0.10f), Offset(x, 0f), Offset(x, size.height), 0.45.dp.toPx())
        }

        // Four HUD corner brackets.
        drawLine(cyan, Offset(inset, inset), Offset(inset + corner, inset), stroke)
        drawLine(cyan, Offset(inset, inset), Offset(inset, inset + corner), stroke)
        drawLine(violet, Offset(size.width - inset, inset), Offset(size.width - inset - corner, inset), stroke)
        drawLine(violet, Offset(size.width - inset, inset), Offset(size.width - inset, inset + corner), stroke)
        drawLine(violet, Offset(inset, size.height - inset), Offset(inset + corner, size.height - inset), stroke)
        drawLine(violet, Offset(inset, size.height - inset), Offset(inset, size.height - inset - corner), stroke)
        drawLine(cyan, Offset(size.width - inset, size.height - inset), Offset(size.width - inset - corner, size.height - inset), stroke)
        drawLine(cyan, Offset(size.width - inset, size.height - inset), Offset(size.width - inset, size.height - inset - corner), stroke)

        // Slow scan beam.
        val scanY = size.height * scanProgress
        drawLine(red.copy(alpha = 0.45f), Offset(inset, scanY), Offset(size.width - inset, scanY), 1.2.dp.toPx())
        drawCircle(cyan.copy(alpha = 0.75f), radius = 2.2.dp.toPx(), center = Offset(size.width - inset - 8.dp.toPx(), inset + 8.dp.toPx()))
    }
}

'''
if "private fun AmityHudBackdrop()" not in s:
    anchor = s.find("@Composable\nprivate fun HomeScreen(")
    if anchor < 0:
        raise SystemExit("FUI/HUD upgrade stopped: HomeScreen insertion point not found")
    s = s[:anchor] + component + s[anchor:]

old = 'Box(modifier = Modifier.fillMaxSize().background(t.canvas)) {'
new = '''Box(
        modifier = Modifier.fillMaxSize().background(
            Brush.verticalGradient(
                listOf(Color(0xFF020817), Color(0xFF071A35), Color(0xFF030713))
            )
        )
    ) {
        // The approved AmitySA family-shield artwork is the shared, low-opacity
        // wallpaper behind the active page windows and HUD overlays.
        Image(
            painter = painterResource(R.drawable.amity_logo),
            contentDescription = null,
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize().alpha(0.24f)
        )
        AmityHudBackdrop()'''
if old in s:
    s = s.replace(old, new, 1)
elif 'AmityHudBackdrop()' not in s:
    raise SystemExit("FUI/HUD upgrade stopped: home screen root container not found")

# Add a small, restrained sci-fi status strip above the dashboard content.
header_call = 'item { Header(account.username, onOpenThemes) { item -> if (item == "Home") showMenu = false else onMenuAction(item) } }'
if header_call in s and 'AMITYSA // FAMILY NETWORK' not in s:
    s = s.replace(
        header_call,
        header_call + '''
            item {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 22.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        "AMITYSA // FAMILY NETWORK",
                        color = Color(0xFF62DFFF),
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.8.sp
                    )
                    Text(
                        "SYSTEM ONLINE",
                        color = Color(0xFF73F0C4),
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.2.sp
                    )
                }
            }''',
        1
    )

p.write_text(s, encoding="utf-8")
print("AmitySA FUI / Sci-Fi HUD backdrop, animated scan beam, corner brackets and system status strip applied.")
