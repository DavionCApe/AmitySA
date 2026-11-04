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
map_count = map_source.count("var mapType by remember { mutableIntStateOf(MapType.NORMAL) }")
if map_count != 1:
    raise SystemExit("Could not locate the original FamilyMapScreen mapType state")
map_source = map_source.replace(
    "var mapType by remember { mutableIntStateOf(MapType.NORMAL) }",
    "var mapType by remember { mutableStateOf(MapType.NORMAL) }",
    1
)
family_map.write_text(map_source, encoding="utf-8")

# Wire the dropdown action handler through HomeScreen into Header.
source = main_activity.read_text(encoding="utf-8")
home_start = source.find("private fun HomeScreen(")
header_start = source.find("private fun Header(", home_start)
if home_start < 0 or header_start < 0:
    raise SystemExit("Could not locate HomeScreen and Header declarations")
home_block = source[home_start:header_start]
if "onMenuAction: (String) -> Unit" not in home_block:
    home_block, signature_count = re.subn(
        r"(?m)^(\\s*)onAction: \\(QuickAction\\) -> Unit\\s*$",
        r"\\1onAction: (QuickAction) -> Unit,\\n\\1onMenuAction: (String) -> Unit",
        home_block,
        count=1
    )
    if signature_count != 1:
        raise SystemExit("Could not add onMenuAction to HomeScreen signature")
header_call = "Header(account.username, onOpenThemes)"
if header_call not in home_block:
    raise SystemExit("Could not locate Header call in HomeScreen")
home_block = home_block.replace(header_call, "Header(account.username, onOpenThemes, onMenuAction)", 1)
source = source[:home_start] + home_block + source[header_start:]
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
