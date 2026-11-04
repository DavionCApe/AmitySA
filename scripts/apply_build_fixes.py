from pathlib import Path
import re

root = Path.cwd()
child_store = root / "app/src/main/java/com/amitysa/app/ChildStore.kt"
main_activity = root / "app/src/main/java/com/amitysa/app/MainActivity.kt"

if not child_store.exists() or not main_activity.exists():
    raise SystemExit(f"Android Kotlin sources not found under {root}")

source = child_store.read_text(encoding="utf-8")
if "fun school(owner: String)" not in source:
    marker = '    private val prefs = context.getSharedPreferences("amity_children", Context.MODE_PRIVATE)\n'
    if marker not in source:
        raise SystemExit("ChildStore preferences declaration not found")
    addition = '''
    /** School name for this educator account, stored locally on this device. */
    fun school(owner: String): String = prefs.getString("school_$owner", "") ?: ""

    fun setSchool(owner: String, school: String) {
        prefs.edit().putString("school_$owner", school.trim()).apply()
    }
'''
    source = source.replace(marker, marker + addition, 1)
    child_store.write_text(source, encoding="utf-8")

source = main_activity.read_text(encoding="utf-8")
# Compose BOM 2024.06 does not expose InfiniteTransition.animateFloat in this project setup.
source = re.sub(
    r'    val pulse by rememberInfiniteTransition\(label = "pulse"\)\.animateFloat\(.*?\n    \)\n',
    '    val pulse = 1f\n',
    source,
    count=1,
    flags=re.S
)
source = source.replace("import androidx.compose.animation.core.animateFloat\n", "")
if 'val pulse = 1f' not in source:
    raise SystemExit("Could not replace splash pulse animation")
main_activity.write_text(source, encoding="utf-8")
print("Applied and verified ChildStore school methods and compatible splash scaling.")

# Keep Google Maps' MapType enum strongly typed.
family_map = root / "app/src/main/java/com/amitysa/app/FamilyMapScreen.kt"
map_source = family_map.read_text(encoding="utf-8")
map_source, map_count = re.subn(
    r'var mapType by remember \\{\\s*mutableIntStateOf\\(MapType\\.NORMAL\\)\\s*\\}',
    'var mapType by remember { mutableStateOf(MapType.NORMAL) }',
    map_source,
    count=1
)
if map_count != 1:
    raise SystemExit("Could not convert FamilyMapScreen mapType state to MapType state")
family_map.write_text(map_source, encoding="utf-8")

# Wire the dropdown action handler through HomeScreen into Header.
source = main_activity.read_text(encoding="utf-8")
source, signature_count = re.subn(
    r'(private fun HomeScreen\(\s*account: Account,\s*onSignOut: \(\) -> Unit,\s*online: Boolean,\s*onOpenThemes: \(\) -> Unit,\s*onSos: \(\) -> Unit,\s*onAction: \(QuickAction\) -> Unit)(\s*\))',
    r'\1,\n    onMenuAction: (String) -> Unit\2',
    source,
    count=1
)
if signature_count != 1:
    raise SystemExit("Could not add onMenuAction to HomeScreen signature")
source, header_count = re.subn(
    r'item \{ Header\(account\.username, onOpenThemes\) \}',
    'item { Header(account.username, onOpenThemes, onMenuAction) }',
    source,
    count=1
)
if header_count != 1:
    raise SystemExit("Could not pass onMenuAction from HomeScreen to Header")
main_activity.write_text(source, encoding="utf-8")

# Use the explicit osmdroid Polygon setter to avoid resolving the outer list.
offline_map = root / "app/src/main/java/com/amitysa/app/OfflineFamilyMapView.kt"
offline_source = offline_map.read_text(encoding="utf-8")
offline_source, polygon_count = re.subn(
    r'(?m)^\s*points = circlePoints\(point\.lat, point\.lng, point\.radiusM\.toDouble\(\)\)$',
    '                        setPoints(circlePoints(point.lat, point.lng, point.radiusM.toDouble()))',
    offline_source,
    count=1
)
if polygon_count != 1:
    raise SystemExit("Could not update offline map safe-zone polygon points")
offline_map.write_text(offline_source, encoding="utf-8")

print("Applied MapType, menu callback, and offline polygon compile repairs.")
