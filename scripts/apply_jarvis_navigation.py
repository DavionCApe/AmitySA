from pathlib import Path
import re

root = Path("app/src/main/java/com/amitysa/app")
files = list(root.glob("*.kt"))
if not files:
    raise SystemExit("AmitySA Kotlin source files were not found")

changed = []
for path in files:
    s = path.read_text(encoding="utf-8")
    original = s

    # Style Material 3 bottom navigation as a dark holographic command dock.
    s = re.sub(
        r'NavigationBar\(\s*(?!containerColor\s*=)',
        'NavigationBar(\n        containerColor = Color(0xE6091723),\n        contentColor = Color(0xFF72E8FF),\n        tonalElevation = 0.dp,\n',
        s
    )

    # Give every navigation item the same cyan/orange JARVIS selection language.
    item_colors = '''NavigationBarItemDefaults.colors(
            selectedIconColor = Color(0xFF8CF2FF),
            selectedTextColor = Color(0xFFBDF8FF),
            indicatorColor = Color(0x5538BFE8),
            unselectedIconColor = Color(0xFF7896A8),
            unselectedTextColor = Color(0xFF7896A8)
        )'''
    s = re.sub(
        r'NavigationBarItem\(\s*(?!.*?colors\s*=)',
        'NavigationBarItem(\n        colors = ' + item_colors + ',\n',
        s,
        flags=re.S
    )

    # Convert standard navigation drawer items into dark glass / cyan active states.
    s = re.sub(
        r'NavigationDrawerItem\(\s*(?!.*?colors\s*=)',
        'NavigationDrawerItem(\n        colors = NavigationDrawerItemDefaults.colors(\n'
        '            selectedContainerColor = Color(0x5538BFE8),\n'
        '            unselectedContainerColor = Color.Transparent,\n'
        '            selectedIconColor = Color(0xFF8CF2FF),\n'
        '            unselectedIconColor = Color(0xFF7896A8),\n'
        '            selectedTextColor = Color(0xFFBDF8FF),\n'
        '            unselectedTextColor = Color(0xFFB0C6D4)\n'
        '        ),\n',
        s,
        flags=re.S
    )

    # Preserve menu labels/options while improving the shared header treatment.
    s = s.replace(
        'RoundedCornerShape(16.dp),\n            colors = CardDefaults.cardColors(containerColor = t.card)',
        'RoundedCornerShape(16.dp),\n            border = androidx.compose.foundation.BorderStroke(1.dp, Color(0x6656DFFF)),\n            colors = CardDefaults.cardColors(containerColor = Color(0xD9091B2A))'
    )
    if s != original:
        path.write_text(s, encoding="utf-8")
        changed.append(str(path))

if not changed:
    # Navigation may use a custom row instead of Material NavigationBar.
    # Fail clearly rather than silently reporting a visual change.
    raise SystemExit("No supported Material 3 navigation components were found to style")

print("Applied JARVIS command-dock styling while preserving existing navigation destinations and labels in: " + ", ".join(changed))
