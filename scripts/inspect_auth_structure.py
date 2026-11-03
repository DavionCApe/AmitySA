from pathlib import Path
p = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not p.exists():
    raise SystemExit("MainActivity.kt not found")
lines = p.read_text(encoding="utf-8").splitlines()
terms = ("AuthScreen(", "onLogin", "onSignIn", "SharedPreferences", "signIn", "login", "Account(")
hits = [i for i, line in enumerate(lines) if any(t.lower() in line.lower() for t in terms)]
shown = set()
for i in hits:
    lo, hi = max(0, i-3), min(len(lines), i+5)
    if any(n in shown for n in range(lo, hi)):
        continue
    print(f"--- MainActivity.kt lines {lo+1}-{hi} ---")
    for n in range(lo, hi):
        print(f"{n+1}: {lines[n]}")
        shown.add(n)
