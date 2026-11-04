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

    # The current app uses a custom header menu rather than Material NavigationBar.
    # Style the existing dropdown itself; do not rename, remove or reorder its items.
    if "DropdownMenu(" in s:
        s = re.sub(
            r'DropdownMenu\(\s*(?!containerColor\s*=)',
            'DropdownMenu(\n        containerColor = Color(0xF20A1A28),\n        tonalElevation = 12.dp,\n        shadowElevation = 18.dp,\n',
            s
        )
    if "DropdownMenuItem(" in s:
        s = re.sub(
            r'DropdownMenuItem\(\s*(?!colors\s*=)',
            'DropdownMenuItem(\n        colors = androidx.compose.material3.MenuDefaults.itemColors(\n'
            '            textColor = Color(0xFFD9F7FF),\n'
            '            leadingIconColor = Color(0xFF62DDF5),\n'
            '            trailingIconColor = Color(0xFFFFA24A),\n'
            '            disabledTextColor = Color(0xFF607A89)\n'
            '        ),\n',
            s
        )

    # Give menu-related glass cards a technical cyan edge.
    s = s.replace(
        'CardDefaults.cardColors(containerColor = t.card)',
        'CardDefaults.cardColors(containerColor = Color(0xD9091B2A))'
    )

    if s != original:
        path.write_text(s, encoding="utf-8")
        changed.append(str(path))

if not changed:
    raise SystemExit("Could not find the existing custom menu/dropdown in the Android Kotlin source")

print("Applied JARVIS glass styling to existing AmitySA menu surfaces without changing menu options: " + ", ".join(changed))
