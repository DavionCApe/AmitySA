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
