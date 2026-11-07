from pathlib import Path

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
asset = Path("app/src/main/assets/jarvis-multi-ai.html")
if not main.is_file() or not asset.is_file():
    raise SystemExit("JARVIS runtime source or packaged HTML asset is missing")

source = main.read_text(encoding="utf-8")
start = source.find("@Composable\nprivate fun HomeScreen(")
end = source.find("\n@Composable\nprivate fun ", start + 1)
if start < 0 or end < 0:
    raise SystemExit("Final generated HomeScreen could not be located")
home = source[start:end]
checks = {
    "JARVIS WebView host": "JarvisWebEmbed(" in home,
    "immersive fullscreen flags": "SYSTEM_UI_FLAG_IMMERSIVE_STICKY" in home,
    "legacy welcome removed from authenticated home": "WelcomeScreen(" not in home,
    "legacy native dashboard removed from authenticated home": "JarvisDashboard(" not in home,
    "fullscreen WebView container": "Modifier.fillMaxSize()" in home,
}
html = asset.read_text(encoding="utf-8")
checks["JARVIS HTML packaged"] = "WORLD STATISTICS" in html and "AUDIO WAVEFREQ" in html
for name, passed in checks.items():
    print(("PASS" if passed else "FAIL") + ": " + name)
if not all(checks.values()):
    raise SystemExit("JARVIS runtime verification failed; refusing to build a misleading APK")
print("Final generated Android source is wired to the JARVIS HUD in fullscreen mode.")
