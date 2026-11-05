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
                    Text("Good to see you, ${account.username}", color = t.ink,
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
                        Text("${account.username}  ·  ${if (account.role == Role.EDUCATOR) "EDUCATOR" else "PARENT"}",
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
private fun JarvisRadar(online: Boolean, children: Int, zones: Int, processing: Boolean = false) {
    val motion = rememberInfiniteTransition(label = "amityAiCore")
    val outerAngle by motion.animateFloat(0f, 360f,
        infiniteRepeatable(tween(if (processing) 3000 else 18000, easing = androidx.compose.animation.core.LinearEasing)), label = "outerOrbit")
    val innerAngle by motion.animateFloat(360f, 0f,
        infiniteRepeatable(tween(if (processing) 1500 else 11000, easing = androidx.compose.animation.core.LinearEasing)), label = "innerOrbit")
    val pulse by motion.animateFloat(if (processing) 0.72f else 0.45f, 1f,
        infiniteRepeatable(tween(if (processing) 600 else 3000), repeatMode = androidx.compose.animation.core.RepeatMode.Reverse), label = "corePulse")
    val outerDuration = if (processing) 3000 else 18000
    val innerDuration = if (processing) 1500 else 11000
    val blue = Color(0xFF0077FF)
    val coreCyan = if (processing) blue else Color(0xFF00F0FF)
    Card(Modifier.padding(horizontal = 16.dp).fillMaxWidth(), shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xF0061422)),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xAA38DDF5))) {
        Column(Modifier.fillMaxWidth().padding(14.dp), horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("AMITY // INTELLIGENCE CORE", color = Color(0xFF9AF5FF), fontSize = 9.sp,
                        fontWeight = FontWeight.ExtraBold, letterSpacing = 1.7.sp)
                    Text("AUTONOMOUS FAMILY SAFETY SYSTEM", color = Color(0xFF668FA4), fontSize = 7.sp, letterSpacing = 1.1.sp)
                }
                Text("●  ${if (processing) "PROCESSING" else if (online) "ONLINE" else "LOCAL"}", color = if (processing) blue else if (online) Color(0xFF45E6B0) else Color(0xFFFFA24A),
                    fontSize = 8.sp, fontWeight = FontWeight.ExtraBold)
            }
            Box(Modifier.fillMaxWidth().height(258.dp), contentAlignment = Alignment.Center) {
                Canvas(Modifier.fillMaxSize()) {
                    val cx = size.width / 2f
                    val cy = size.height / 2f
                    val r = size.minDimension * 0.405f
                    val center = androidx.compose.ui.geometry.Offset(cx, cy)
                    val cyan = Color(0xFF39DDF5)
                    val ice = Color(0xFFB8F8FF)
                    val amber = Color(0xFFFFA24A)
                    drawCircle(brush = androidx.compose.ui.graphics.Brush.radialGradient(
                        colors = listOf(Color(0x6639DDF5).copy(alpha = pulse), Color(0x2239DDF5), Color.Transparent),
                        center = center, radius = r * 1.45f), radius = r * 1.45f, center = center)
                    drawCircle(Color(0x8839DDF5), r, center, style = androidx.compose.ui.graphics.drawscope.Stroke(1.1.dp.toPx()))
                    drawCircle(Color(0x6639DDF5), r * 0.83f, center,
                        style = androidx.compose.ui.graphics.drawscope.Stroke(1.dp.toPx(),
                            pathEffect = androidx.compose.ui.graphics.PathEffect.dashPathEffect(floatArrayOf(5.dp.toPx(), 5.dp.toPx()))))
                    drawCircle(Color(0xAA9AF5FF), r * 0.60f, center, style = androidx.compose.ui.graphics.drawscope.Stroke(1.3.dp.toPx()))
                    // Segmented orbit arcs: deliberate gaps between each scan segment.
                    repeat(6) { segment ->
                        drawArc(coreCyan.copy(alpha = pulse), outerAngle + segment * 60f, 34f, false,
                            androidx.compose.ui.geometry.Offset(cx-r, cy-r), androidx.compose.ui.geometry.Size(r*2, r*2),
                            style = androidx.compose.ui.graphics.drawscope.Stroke(3.dp.toPx(), cap = androidx.compose.ui.graphics.StrokeCap.Round))
                    }
                    repeat(4) { segment ->
                        drawArc(amber.copy(alpha = 0.9f), innerAngle + segment * 90f, 24f, false,
                            androidx.compose.ui.geometry.Offset(cx-r*0.83f, cy-r*0.83f), androidx.compose.ui.geometry.Size(r*1.66f, r*1.66f),
                            style = androidx.compose.ui.graphics.drawscope.Stroke(2.dp.toPx(), cap = androidx.compose.ui.graphics.StrokeCap.Round))
                    }
                    for (i in 0 until 48) {
                        val a = Math.toRadians(i * 7.5)
                        val major = i % 4 == 0
                        val inner = if (major) r * 0.88f else r * 0.93f
                        drawLine(if (major) ice.copy(alpha = 0.8f) else cyan.copy(alpha = 0.38f),
                            androidx.compose.ui.geometry.Offset(cx + kotlin.math.cos(a).toFloat()*inner, cy + kotlin.math.sin(a).toFloat()*inner),
                            androidx.compose.ui.geometry.Offset(cx + kotlin.math.cos(a).toFloat()*r*0.99f, cy + kotlin.math.sin(a).toFloat()*r*0.99f),
                            if (major) 1.4.dp.toPx() else 0.7.dp.toPx())
                    }
                    val a1 = Math.toRadians(outerAngle.toDouble())
                    val a2 = Math.toRadians(innerAngle.toDouble())
                    drawCircle(amber.copy(alpha = pulse), 5.dp.toPx(),
                        androidx.compose.ui.geometry.Offset(cx + kotlin.math.cos(a1).toFloat()*r, cy + kotlin.math.sin(a1).toFloat()*r))
                    drawCircle(ice, 3.5.dp.toPx(),
                        androidx.compose.ui.geometry.Offset(cx + kotlin.math.cos(a2).toFloat()*r*0.83f, cy + kotlin.math.sin(a2).toFloat()*r*0.83f))
                    drawCircle(Color(0x4439DDF5), r*0.48f, center)
                    drawCircle(brush = androidx.compose.ui.graphics.Brush.radialGradient(
                        colors = if (processing) listOf(Color(0xFFE5F1FF), Color(0xFF0077FF), Color(0xFF064C9D), Color(0xFF041B31)) else listOf(Color(0xFFDAFFFF), Color(0xFF55E8FF), Color(0xFF087DA7), Color(0xFF041B31)),
                        center = center, radius = r*0.47f), radius = r*0.43f, center = center)
                    drawCircle(ice.copy(alpha = pulse), r*0.31f, center, style = androidx.compose.ui.graphics.drawscope.Stroke(1.dp.toPx()))
                    drawCircle(Color(0xFF061A2A), r*0.25f, center)
                    drawCircle(coreCyan.copy(alpha = pulse), 4.dp.toPx(), center)
                    drawLine(Color(0x889AF5FF), androidx.compose.ui.geometry.Offset(cx-r*0.53f, cy),
                        androidx.compose.ui.geometry.Offset(cx+r*0.53f, cy), 0.8.dp.toPx())
                    drawLine(Color(0x889AF5FF), androidx.compose.ui.geometry.Offset(cx, cy-r*0.53f),
                        androidx.compose.ui.geometry.Offset(cx, cy+r*0.53f), 0.8.dp.toPx())
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("A", color = Color(0xFFE4FFFF), fontSize = 32.sp, fontWeight = FontWeight.Black)
                    Text("CORE", color = Color(0xFF9AF5FF), fontSize = 8.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 2.sp)
                }
                Column(Modifier.align(Alignment.CenterStart)) {
                    Text("LINK", color = Color(0xFF6D9CB0), fontSize = 7.sp)
                    Text(if (online) "READY" else "LOCAL", color = Color(0xFF9AF5FF), fontSize = 8.sp, fontWeight = FontWeight.Bold)
                }
                Column(Modifier.align(Alignment.CenterEnd), horizontalAlignment = Alignment.End) {
                    Text("SECURITY SETUP", color = Color(0xFF6D9CB0), fontSize = 7.sp)
                    Text(if (children > 0 && zones > 0) "CONFIGURED" else "SETUP NEEDED",
                        color = if (children > 0 && zones > 0) Color(0xFF9AF5FF) else Color(0xFFFFA24A),
                        fontSize = 8.sp, fontWeight = FontWeight.Bold)
                }
                Text("360° SCAN", Modifier.align(Alignment.BottomCenter).padding(bottom = 3.dp),
                    color = Color(0xFF6D9CB0), fontSize = 7.sp, letterSpacing = 1.4.sp)
            }
            Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(10.dp)).background(Color(0xAA0A2638))
                .padding(horizontal = 10.dp, vertical = 9.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                Column {
                    Text("FAMILY UNITS", color = Color(0xFF6D9CB0), fontSize = 7.sp)
                    Text(children.toString().padStart(2, '0'), color = Color(0xFF9AF5FF), fontSize = 14.sp, fontWeight = FontWeight.ExtraBold)
                }
                Column {
                    Text("SAFE ZONES", color = Color(0xFF6D9CB0), fontSize = 7.sp)
                    Text(zones.toString().padStart(2, '0'), color = Color(0xFF9AF5FF), fontSize = 14.sp, fontWeight = FontWeight.ExtraBold)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("CORE STATUS", color = Color(0xFF6D9CB0), fontSize = 7.sp)
                    Text(if (processing) "PROCESSING" else if (online && children > 0 && zones > 0) "READY" else "STANDBY",
                        color = if (processing) blue else if (online && children > 0 && zones > 0) Color(0xFF45E6B0) else Color(0xFFFFA24A),
                        fontSize = 10.sp, fontWeight = FontWeight.ExtraBold)
                }
            }
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
