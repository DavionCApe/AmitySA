from pathlib import Path

root = Path(__file__).resolve().parents[1]
child_store = root / "app/src/main/java/com/amitysa/app/ChildStore.kt"
main_activity = root / "app/src/main/java/com/amitysa/app/MainActivity.kt"

source = child_store.read_text(encoding="utf-8")
needle = '    fun newId(): String = UUID.randomUUID().toString()\n'
addition = '''    /** School name shared by educator screens on this phone. */
    fun school(owner: String): String = prefs.getString("school_$owner", "") ?: ""

    fun setSchool(owner: String, school: String) {
        prefs.edit().putString("school_$owner", school.trim()).apply()
    }

'''
if "fun school(owner: String)" not in source:
    if needle not in source:
        raise SystemExit("Could not find ChildStore insertion point")
    child_store.write_text(source.replace(needle, addition + needle), encoding="utf-8")

source = main_activity.read_text(encoding="utf-8")
needle = "import androidx.compose.animation.core.infiniteRepeatable\n"
addition = "import androidx.compose.animation.core.animateFloat\n"
if addition not in source:
    if needle not in source:
        raise SystemExit("Could not find MainActivity import insertion point")
    main_activity.write_text(source.replace(needle, needle + addition), encoding="utf-8")

print("Applied AmitySA Kotlin compile fixes.")
