from pathlib import Path

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not main.exists():
    raise SystemExit("AmitySA MainActivity.kt was not found")
s = main.read_text(encoding="utf-8")
start = s.find("@Composable\nprivate fun HomeScreen(")
end = s.find("\n@Composable\nprivate fun WelcomeScreen(", start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate generated HomeScreen boundaries")

home = r'''@Composable
private fun HomeScreen(
    account: Account, onSignOut: () -> Unit, online: Boolean,
    onOpenThemes: () -> Unit, onSos: () -> Unit,
    onAction: (QuickAction) -> Unit, onMenuAction: (String) -> Unit
) {
    var showMenu by remember { mutableStateOf(false) }
    var showEmergency by remember { mutableStateOf(false) }
    if (showMenu) JarvisDashboard(account, online, onOpenThemes, onSos, onAction,
        { item -> if (item == "Home") showMenu = false else onMenuAction(item) }, onSignOut)
    else if (showEmergency) EmergencyServicesScreen(
        onPrevious = { showEmergency = false },
        onNext = { showEmergency = false; showMenu = true }
    ) else WelcomeScreen(account.username) { showEmergency = true }
}

@Composable
private fun JarvisDashboard(
    account: Account, online: Boolean, onOpenThemes: () -> Unit, onSos: () -> Unit,
    onAction: (QuickAction) -> Unit, onMenuAction: (String) -> Unit, onSignOut: () -> Unit
) {
    val ctx = LocalContext.current
    val t = LocalAmity.current
    val children = remember(account.email) { ChildStore(ctx).list(account.email).size }
    val zones = remember(account.email) { ZoneStore(ctx).zones(account.email).size }
    val state = rememberLazyListState()
    val scope = rememberCoroutineScope()
    val showTop = state.firstVisibleItemIndex > 1 || state.firstVisibleItemScrollOffset > 420
    Box(Modifier.fillMaxSize().background(AmityBackdrop)) {
        LazyColumn(state = state, modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(bottom = 100.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)) {
            item { Header(account.username, onOpenThemes, onMenuAction) }
            item {
                Column(Modifier.padding(horizontal = 20.dp)) {
                    Text("AMITYSA  /  FAMILY COMMAND", color = t.primary, fontSize = 10.sp,
                        fontWeight = FontWeight.ExtraBold, letterSpacing = 2.sp)
                    Text("Good to see you, \${account.username}", color = t.ink,
                        fontSize = 23.sp, fontWeight = FontWeight.Bold)
                    Text("Your Family’s Safety, Connected.", color = t.inkSoft, fontSize = 12.sp)
                }
            }
            item { JarvisStatus(online) }
            item { JarvisRadar(online, children, zones) }
            item {
                Row(Modifier.padding(horizontal = 20.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    JarvisMetric("FAMILY", children.toString(), "PROFILES", Modifier.weight(1f))
                    JarvisMetric("SAFE ZONES", zones.toString(), "SAVED", Modifier.weight(1f))
                    JarvisMetric("NETWORK", if (online) "ONLINE" else "OFFLINE",
                        "CONNECTION", Modifier.weight(1f), !online)
                }
            }
            item { JarvisSos(onSos) }
            item {
                Text("COMMAND MODULES", Modifier.padding(horizontal = 20.dp),
                    color = t.primary, fontSize = 11.sp, fontWeight = FontWeight.ExtraBold,
                    letterSpacing = 1.8.sp)
            }
            items(quickActions.chunked(2)) { pair ->
                Row(Modifier.padding(horizontal = 20.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    pair.forEach { action ->
                        JarvisAction(action, !(action.needsInternet && !online),
                            Modifier.weight(1f)) { onAction(action) }
                    }
                    if (pair.size == 1) Spacer(Modifier.weight(1f))
                }
            }
            item {
                Card(Modifier.padding(horizontal = 20.dp).fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xD9091B2A)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0x6646CFEA))) {
                    Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("ACCOUNT IDENTIFICATION", color = t.primary, fontSize = 9.sp,
                            fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp)
                        Text("\${account.username}  ·  \${if (account.role == Role.EDUCATOR) "EDUCATOR" else "PARENT"}",
                            color = t.ink, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                        Text(account.email, color = t.inkSoft, fontSize = 11.sp)
                        OutlinedButton(onClick = onSignOut, modifier = Modifier.fillMaxWidth()) {
                            Text("SIGN OUT")
                        }
                    }
                }
            }
            item { Text("AMITYSA  •  COMMAND CENTRE",
                Modifier.fillMaxWidth().padding(vertical = 8.dp), textAlign = TextAlign.Center,
                color = t.inkSoft, fontSize = 9.sp, letterSpacing = 1.2.sp) }
        }
        AnimatedVisibility(showTop, Modifier.align(Alignment.BottomEnd)
            .navigationBarsPadding().padding(18.dp),
            enter = fadeIn(tween(160)) + scaleIn(initialScale = 0.8f),
            exit = fadeOut(tween(120)) + scaleOut(targetScale = 0.8f)) {
            FloatingActionButton(onClick = { scope.launch { state.animateScrollToItem(0) } },
                containerColor = t.primary, contentColor = Color(0xFF03131D),
                shape = RoundedCornerShape(13.dp)) { Text("↑", fontSize = 24.sp) }
        }
    }
}

@Composable
private fun JarvisStatus(online: Boolean) {
    val t = LocalAmity.current
    Row(Modifier.padding(horizontal = 20.dp).fillMaxWidth()
        .clip(RoundedCornerShape(12.dp)).background(Color(0xD9091B2A))
        .padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(8.dp).clip(CircleShape)
            .background(if (online) Color(0xFF45E6B0) else Color(0xFFFFA24A)))
        Spacer(Modifier.width(9.dp))
        Text(if (online) "SYSTEM LINK ACTIVE" else "OFFLINE MODE · LOCAL DATA",
            color = t.ink, fontSize = 10.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.weight(1f))
        Text(if (online) "CONNECTED" else "STANDBY",
            color = if (online) Color(0xFF45E6B0) else Color(0xFFFFA24A),
            fontSize = 9.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun JarvisRadar(online: Boolean, children: Int, zones: Int) {
    val t = LocalAmity.current
    val motion = rememberInfiniteTransition(label = "dashboardRadar")
    val angle by motion.animateFloat(0f, 360f,
        infiniteRepeatable(tween(9500, easing = androidx.compose.animation.core.LinearEasing)),
        label = "radarSweep")
    val pulse by motion.animateFloat(0.35f, 0.95f,
        infiniteRepeatable(tween(1300), repeatMode = androidx.compose.animation.core.RepeatMode.Reverse),
        label = "radarPulse")
    Card(Modifier.padding(horizontal = 20.dp).fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xE6081A29)),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0x8846CFEA))) {
        Box(Modifier.fillMaxWidth().height(218.dp).padding(12.dp)) {
            Canvas(Modifier.fillMaxSize()) {
                val cx = size.width / 2f
                val cy = size.height * 0.53f
                val r = size.height * 0.42f
                val cyan = Color(0xAA36D8F2)
                listOf(1f, 0.7f, 0.4f).forEach { f ->
                    drawCircle(cyan.copy(alpha = 0.62f * f), r * f,
                        androidx.compose.ui.geometry.Offset(cx, cy),
                        style = androidx.compose.ui.graphics.drawscope.Stroke(1.dp.toPx()))
                }
                drawLine(cyan.copy(alpha = 0.35f),
                    androidx.compose.ui.geometry.Offset(cx-r, cy),
                    androidx.compose.ui.geometry.Offset(cx+r, cy), 1.dp.toPx())
                drawLine(cyan.copy(alpha = 0.35f),
                    androidx.compose.ui.geometry.Offset(cx, cy-r),
                    androidx.compose.ui.geometry.Offset(cx, cy+r), 1.dp.toPx())
                val a = Math.toRadians(angle.toDouble())
                val ex = cx + kotlin.math.cos(a).toFloat() * r
                val ey = cy + kotlin.math.sin(a).toFloat() * r
                drawLine(Color(0xDD9AF5FF).copy(alpha = pulse),
                    androidx.compose.ui.geometry.Offset(cx, cy),
                    androidx.compose.ui.geometry.Offset(ex, ey), 2.dp.toPx())
                drawCircle(Color(0xFFFFA24A).copy(alpha = pulse), 4.dp.toPx(),
                    androidx.compose.ui.geometry.Offset(ex, ey))
                drawCircle(Color(0xFF9AF5FF), 3.dp.toPx(),
                    androidx.compose.ui.geometry.Offset(cx, cy))
                for (i in 0..23) {
                    val tick = Math.toRadians(i * 15.0)
                    drawLine(cyan,
                        androidx.compose.ui.geometry.Offset(cx + kotlin.math.cos(tick).toFloat()*r*0.91f,
                            cy + kotlin.math.sin(tick).toFloat()*r*0.91f),
                        androidx.compose.ui.geometry.Offset(cx + kotlin.math.cos(tick).toFloat()*r,
                            cy + kotlin.math.sin(tick).toFloat()*r), 1.dp.toPx())
                }
            }
            Column(Modifier.align(Alignment.TopStart)) {
                Text("FAMILY OVERVIEW", color = t.primary, fontSize = 9.sp,
                    fontWeight = FontWeight.ExtraBold, letterSpacing = 1.3.sp)
                Text("SCANNER // \${if (online) "LINK READY" else "LOCAL STANDBY"}",
                    color = t.inkSoft, fontSize = 8.sp)
            }
            Column(Modifier.align(Alignment.BottomStart)) {
                Text("PROFILES  $children", color = t.ink, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                Text("SAFE ZONES  $zones", color = t.inkSoft, fontSize = 8.sp)
            }
            Text("AMITY // HUD", Modifier.align(Alignment.TopEnd), color = Color(0xFFFFA24A),
                fontSize = 8.sp, fontWeight = FontWeight.Bold)
            Text(if (online) "NETWORK NOMINAL" else "NETWORK DISCONNECTED",
                Modifier.align(Alignment.BottomEnd),
                color = if (online) Color(0xFF45E6B0) else Color(0xFFFFA24A),
                fontSize = 8.sp, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
private fun JarvisMetric(label: String, value: String, detail: String,
    modifier: Modifier = Modifier, alert: Boolean = false) {
    Column(modifier.clip(RoundedCornerShape(12.dp)).background(Color(0xD9091B2A))
        .padding(horizontal = 8.dp, vertical = 10.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
        Text(label, color = Color(0xFF8BB8C8), fontSize = 7.sp, fontWeight = FontWeight.Bold, maxLines = 1)
        Text(value, color = if (alert) Color(0xFFFFA24A) else Color(0xFF9AF5FF),
            fontSize = 16.sp, fontWeight = FontWeight.ExtraBold, maxLines = 1)
        Text(detail, color = Color(0xFF7595A5), fontSize = 7.sp, fontWeight = FontWeight.Bold)
        Row(horizontalArrangement = Arrangement.spacedBy(2.dp)) {
            repeat(5) { i ->
                Box(Modifier.weight(1f).height(3.dp).clip(RoundedCornerShape(2.dp))
                    .background(if (alert) Color(0xFFFFA24A).copy(alpha = if (i < 2) 0.9f else 0.18f)
                        else Color(0xFF36D8F2).copy(alpha = if (i < 4) 0.8f else 0.2f)))
            }
        }
    }
}

@Composable
private fun JarvisSos(onSos: () -> Unit) {
    Row(Modifier.padding(horizontal = 20.dp).fillMaxWidth()
        .clip(RoundedCornerShape(15.dp)).background(Color(0xFF32151B))
        .clickable(onClick = onSos).padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(42.dp).clip(CircleShape).background(Color(0x55FF5A63)),
            contentAlignment = Alignment.Center) {
            Text("SOS", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.ExtraBold)
        }
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text("EMERGENCY RESPONSE", color = Color.White, fontSize = 11.sp,
                fontWeight = FontWeight.ExtraBold)
            Text("Open your configured emergency alert", color = Color(0xFFFFC3C6), fontSize = 9.sp)
        }
        Text("OPEN  ›", color = Color(0xFFFF9A3C), fontSize = 9.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun JarvisAction(item: QuickAction, enabled: Boolean,
    modifier: Modifier = Modifier, onClick: () -> Unit) {
    val t = LocalAmity.current
    Card(modifier.alpha(if (enabled) 1f else 0.42f).clickable(onClick = onClick),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xD9091B2A)),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0x5546CFEA))) {
        Row(Modifier.padding(horizontal = 10.dp, vertical = 13.dp),
            verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(34.dp).clip(RoundedCornerShape(9.dp))
                .background(Color(0x2236D8F2)), contentAlignment = Alignment.Center) {
                Text(item.icon, fontSize = 18.sp)
            }
            Spacer(Modifier.width(8.dp))
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                Text(item.title.uppercase(), color = t.ink, fontSize = 9.sp,
                    fontWeight = FontWeight.ExtraBold, maxLines = 1)
                Text(item.subtitle, color = t.inkSoft, fontSize = 8.sp, lineHeight = 11.sp, maxLines = 2)
            }
            Text("›", color = Color(0xFFFFA24A), fontSize = 18.sp, fontWeight = FontWeight.Bold)
        }
    }
}
'''
s = s[:start] + home + s[end:]
main.write_text(s, encoding="utf-8")
print("Applied JARVIS command dashboard: animated radar, real profile and safe-zone counts, live network state, SOS response panel, telemetry meters and holographic action modules.")
