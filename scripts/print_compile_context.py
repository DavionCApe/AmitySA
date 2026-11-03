from pathlib import Path

ranges = {
    "app/src/main/java/com/amitysa/app/FamilyMapScreen.kt": [(40, 62), (180, 230)],
    "app/src/main/java/com/amitysa/app/MainActivity.kt": [(390, 420), (765, 790)],
    "app/src/main/java/com/amitysa/app/OfflineFamilyMapView.kt": [(55, 85)],
}
for filename, spans in ranges.items():
    path = Path(filename)
    print(f"\\n===== {filename} =====")
    if not path.exists():
        print("MISSING")
        continue
    lines = path.read_text(encoding="utf-8").splitlines()
    for start, end in spans:
        print(f"--- lines {start}-{end} ---")
        for number in range(start, min(end, len(lines)) + 1):
            print(f"{number}: {lines[number - 1]}")
