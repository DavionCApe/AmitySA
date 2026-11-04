from pathlib import Path

root = Path.cwd()
main = root / "app/src/main/java/com/amitysa/app/MainActivity.kt"
if not main.exists():
    raise SystemExit(f"MainActivity.kt not found: {main}")
s = main.read_text(encoding="utf-8")

replacements = {
    "import androidx.compose.animation.AnimatedContent\n": "import androidx.compose.animation.AnimatedContent\nimport androidx.compose.animation.AnimatedVisibility\n",
    "import androidx.compose.animation.scaleIn\n": "import androidx.compose.animation.scaleIn\nimport androidx.compose.animation.scaleOut\n",
    "import androidx.compose.foundation.lazy.items\n": "import androidx.compose.foundation.lazy.items\nimport androidx.compose.foundation.lazy.rememberLazyListState\n",
    "import androidx.compose.runtime.*\n": "import androidx.compose.runtime.*\nimport androidx.compose.runtime.derivedStateOf\n",
}
for old, new in replacements.items():
    if old in s and new not in s:
        s = s.replace(old, new, 1)

needle = """private val Forest = AmityTheme(
    "forest", "Forest (dark green)", true,
    Color(0xFF0E1712), Color(0xFF16241C), Color(0xFFEAF3EC), Color(0xFF93AA9B),
    Color(0xFF4CC38A), Color(0xFFE8C468), Color(0xFF14210F)
)
private val themeChoices = listOf(Midnight, Ocean, Sunrise, Forest)
"""
replacement = """private val Forest = AmityTheme(
    "forest", "Forest (dark green)", true,
    Color(0xFF0E1712), Color(0xFF16241C), Color(0xFFEAF3EC), Color(0xFF93AA9B),
    Color(0xFF4CC38A), Color(0xFFE8C468), Color(0xFF14210F)
)
private val Lavender = AmityTheme(
    "lavender", "Lavender (soft purple)", false,
    Color(0xFFF5F2FB), Color(0xFFFFFFFF), Color(0xFF28213A), Color(0xFF766C8C),
    Color(0xFF7053B8), Color(0xFFE7B95D), Color(0xFFFFFFFF)
)
private val Rose = AmityTheme(
    "rose", "Rose (soft warm)", false,
    Color(0xFFFFF2F3), Color(0xFFFFFFFF), Color(0xFF3B2028), Color(0xFF896B73),
    Color(0xFFB84E70), Color(0xFFF2B45D), Color(0xFFFFFFFF)
)
private val themeChoices = listOf(Midnight, Ocean, Sunrise, Forest, Lavender, Rose)
"""
if needle in s:
    s = s.replace(needle, replacement, 1)
elif 'private val Lavender = AmityTheme(' not in s:
    raise SystemExit("Could not locate theme palette insertion point")

s = s.replace('''    "forest" -> Forest
    else -> if (isSystemInDarkTheme()) Midnight else Ocean
''', '''    "forest" -> Forest
    "lavender" -> Lavender
    "rose" -> Rose
    else -> if (isSystemInDarkTheme()) Midnight else Ocean
''', 1)

start = s.index("@Composable\nprivate fun HomeScreen(")
end = s.index("\n@Composable\nprivate fun Header(", start)
new_home = """@Composable
private fun HomeScreen(
    account: Account,
    onSignOut: () -> Unit,
    online: Boolean,
    onOpenThemes: () -> Unit,
    onSos: () -> Unit,
    onAction: (QuickAction) -> Unit,
    onMenuAction: (String) -> Unit
) {
    val t = LocalAmity.current
    val ctx = LocalContext.current
    val feed = remember(account.email) {
        val fmt = SimpleDateFormat("d MMM, HH:mm", Locale.getDefault())
        ZoneStore(ctx).events(account.email).take(3).map { Activity("📍", it.text, fmt.format(Date(it.time))) }
            .ifEmpty { recentActivity }
    }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()
    val showBackToTop by remember {
        derivedStateOf { listState.firstVisibleItemIndex > 2 || listState.firstVisibleItemScrollOffset > 520 }
    }

    Box(modifier = Modifier.fillMaxSize().background(t.canvas)) {
        LazyColumn(
            state = listState,
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(bottom = 112.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item { Header(account.username, onOpenThemes, onMenuAction) }
            if (!online) item { OfflineBanner() }
            item { StatusCard(online) }
            item { SosCard(onSos) }
            item { SectionTitle("Quick actions") }
            items(quickActions.chunked(2)) { pair ->
                Row(
                    modifier = Modifier.padding(horizontal = 20.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    pair.forEach { action ->
                        ActionCard(action, enabled = !(action.needsInternet && !online), modifier = Modifier.weight(1f)) {
                            onAction(action)
                        }
                    }
                }
            }
            item { SectionTitle(if (online) "Recent activity" else "Saved activity") }
            items(feed) { ActivityRow(it) }
            item { AccountSection(account, onSignOut) }
        }

        AnimatedVisibility(
            visible = showBackToTop,
            modifier = Modifier.align(Alignment.BottomEnd).navigationBarsPadding().padding(end = 20.dp, bottom = 20.dp),
            enter = fadeIn(tween(180)) + scaleIn(initialScale = 0.82f, animationSpec = tween(220)),
            exit = fadeOut(tween(140)) + scaleOut(targetScale = 0.82f, animationSpec = tween(160))
        ) {
            FloatingActionButton(
                onClick = { scope.launch { listState.animateScrollToItem(0) } },
                containerColor = t.primary,
                contentColor = Color.White,
                shape = RoundedCornerShape(18.dp)
            ) {
                Text("↑", fontSize = 26.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}
"""
s = s[:start] + new_home + s[end:]
main.write_text(s, encoding="utf-8")
print("Applied six-theme palette and animated scroll-to-top home layout.")
