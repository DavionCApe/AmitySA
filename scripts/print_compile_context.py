from pathlib import Path

root = Path("app/src/main/java/com/amitysa/app")
for path in sorted(root.rglob("*.kt")):
    lines = path.read_text(encoding="utf-8").splitlines()
    matches = [i for i, line in enumerate(lines) if any(term in line for term in ("fun Header(", "fun HomeScreen(", "fun DashboardScreen(", "circlePoints"))]
    if matches:
        print(f"\\n===== {path} =====")
        for i in matches:
            print(f"--- around {i+1} ---")
            for n in range(max(0, i-5), min(len(lines), i+26)):
                print(f"{n+1}: {lines[n]}")

for filename, spans in {
    "FamilyMapScreen.kt": [(50, 57)],
    "MainActivity.kt": [(375, 430), (770, 785), (1545, 1570)],
    "OfflineFamilyMapView.kt": [(65, 76)],
}.items():
    path = root / filename
    lines = path.read_text(encoding="utf-8").splitlines()
    print(f"\\n===== {path} =====")
    for start, end in spans:
        for n in range(start-1, min(end, len(lines))):
            print(f"{n+1}: {lines[n]}")
