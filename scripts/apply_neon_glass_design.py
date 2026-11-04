from pathlib import Path

p = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
s = p.read_text(encoding="utf-8")

def replace_once(old: str, new: str, label: str):
    global s
    if old not in s:
        raise SystemExit(f"Neon glass upgrade stopped: could not find {label}")
    s = s.replace(old, new, 1)

# Premium midnight palette: deep navy, electric cyan and violet glass.
replace_once(
'''private val Midnight = AmityTheme(
    "midnight", "Midnight (logo colours)", true,
    Color(0xFF0F131A), Color(0xFF182029), Color(0xFFF2F4F7), Color(0xFF9AA5B4),
    Color(0xFF2DD4CF), Color(0xFFF5B942), Color(0xFF1A1405)
)''',
'''private val Midnight = AmityTheme(
    "midnight", "AmitySA Neon Glass", true,
    Color(0xFF050B1B), Color(0xFF102344), Color(0xFFF5FAFF), Color(0xFFA9BEDA),
    Color(0xFF18CFFF), Color(0xFF9A72FF), Color(0xFF031326)
)''',
"Midnight palette"
)
replace_once('''internal val HeaderTop = Color(0xFF0B0E14)
internal val HeaderBottom = Color(0xFF05070B)
internal val Gold = Color(0xFFF5B942)
internal val Danger = Color(0xFFD93025)''',
'''internal val HeaderTop = Color(0xFF08265D)
internal val HeaderBottom = Color(0xFF030817)
internal val Gold = Color(0xFF38E7FF)
internal val Danger = Color(0xFFFF315E)''',
"header palette"
)

# Give the header a layered blue glow while preserving the existing logo and theme action.
replace_once(
'''            .background(Brush.verticalGradient(listOf(HeaderTop, HeaderBottom)))''',
'''            .background(
                Brush.linearGradient(
                    listOf(Color(0xFF0A3B88), Color(0xFF071A43), HeaderBottom)
                )
            )''',
"header glass gradient"
)

# Replace the status card with a translucent, cyan-edged glass panel.
start = s.index("@Composable\nprivate fun StatusCard(")
end = s.index("\n@Composable\nprivate fun SosCard(", start)
s = s[:start] + '''@Composable
private fun StatusCard(online: Boolean) {
    val t = LocalAmity.current
    Card(
        modifier = Modifier.padding(horizontal = 20.dp).fillMaxWidth(),
        shape = RoundedCornerShape(22.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, t.primary.copy(alpha = 0.55f)),
        colors = CardDefaults.cardColors(containerColor = Color(0xCC102B52)),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
    ) {
        Row(
            modifier = Modifier
                .background(Brush.horizontalGradient(listOf(Color(0x5530CFFF), Color.Transparent)))
                .padding(18.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                Modifier.size(13.dp).clip(CircleShape)
                    .background(if (online) Color(0xFF45F0B0) else Gold)
            )
            Spacer(Modifier.width(12.dp))
            Column {
                Text(
                    if (online) "Family connection ready" else "Working offline",
                    color = Color.White, fontWeight = FontWeight.Bold, fontSize = 16.sp
                )
                Text(
                    if (online) "Your AmitySA safety tools are available" else "Saved information stays on this phone",
                    color = Color(0xFFB8D1EE), fontSize = 12.sp
                )
            }
        }
    }
}
''' + s[end:]

# SOS panel keeps the existing real SOS navigation and becomes a luminous glass control.
start = s.index("@Composable\nprivate fun SosCard(")
end = s.index("\n@Composable\nprivate fun SectionTitle(", start)
s = s[:start] + '''@Composable
private fun SosCard(onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .padding(horizontal = 20.dp)
            .fillMaxWidth()
            .clip(RoundedCornerShape(25.dp))
            .background(
                Brush.linearGradient(
                    listOf(Color(0xFFFF4774), Color(0xFFB51249), Color(0xFF501A55))
                )
            )
            .clickable(onClick = onClick)
            .padding(22.dp)
    ) {
        Column {
            Text("SOS  •  EMERGENCY", color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.ExtraBold)
            Spacer(Modifier.height(4.dp))
            Text("Get help when it matters.", color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.ExtraBold)
            Text("Open your configured emergency assistance.", color = Color.White.copy(alpha = 0.88f), fontSize = 13.sp)
        }
    }
}
''' + s[end:]

# Glass action cards with bright edges and a restrained glow.
start = s.index("@Composable\nprivate fun ActionCard(")
end = s.index("\n@Composable\nprivate fun ActivityRow(", start)
s = s[:start] + '''@Composable
private fun ActionCard(item: QuickAction, enabled: Boolean, modifier: Modifier = Modifier, onClick: () -> Unit) {
    val t = LocalAmity.current
    Card(
        modifier = modifier.alpha(if (enabled) 1f else 0.45f).clickable(onClick = onClick),
        shape = RoundedCornerShape(22.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, t.primary.copy(alpha = 0.34f)),
        colors = CardDefaults.cardColors(containerColor = Color(0xCC102344)),
        elevation = CardDefaults.cardElevation(defaultElevation = 6.dp)
    ) {
        Column(
            modifier = Modifier
                .background(Brush.linearGradient(listOf(Color(0x3326CFFF), Color.Transparent)))
                .padding(16.dp)
        ) {
            Box(
                modifier = Modifier.size(46.dp).clip(RoundedCornerShape(15.dp))
                    .background(Brush.linearGradient(listOf(t.primary.copy(alpha = 0.32f), Color(0x559A72FF)))),
                contentAlignment = Alignment.Center
            ) { Text(item.icon, fontSize = 23.sp) }
            Spacer(Modifier.height(12.dp))
            Text(item.title, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 15.sp)
            Text(item.subtitle, color = Color(0xFFA9BEDA), fontSize = 11.sp)
        }
    }
}

@Composable
private fun NeonFamilyOverview() {
    val t = LocalAmity.current
    Column(
        modifier = Modifier.padding(horizontal = 20.dp).fillMaxWidth()
            .clip(RoundedCornerShape(24.dp))
            .background(Brush.linearGradient(listOf(Color(0xDD123568), Color(0xDD101B3B))))
            .then(Modifier),
    ) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("FAMILY SAFETY OVERVIEW", color = t.primary, fontSize = 11.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.3.sp)
            Text("Your family, connected.", color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text(
                "Pair a child's device to view supported safety information here. Screen-time and app-control features are not yet active in this build.",
                color = Color(0xFFB8CDE8), fontSize = 12.sp, lineHeight = 17.sp
            )
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OverviewPill("👨‍👩‍👧", "Family")
                OverviewPill("🤖", "NannyAI preview")
            }
        }
    }
}

@Composable
private fun OverviewPill(icon: String, label: String) {
    Row(
        modifier = Modifier.clip(RoundedCornerShape(14.dp))
            .background(Color(0x332BCBFF))
            .padding(horizontal = 11.dp, vertical = 9.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Text(icon, fontSize = 15.sp)
        Text(label, color = Color.White, fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
    }
}
''' + s[end:]

p.write_text(s, encoding="utf-8")
print("AmitySA neon glass design applied.")
