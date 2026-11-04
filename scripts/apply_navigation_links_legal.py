from pathlib import Path

root = Path.cwd()
main = root / "app/src/main/java/com/amitysa/app/MainActivity.kt"
cloud = root / "app/src/main/java/com/amitysa/app/CloudScreens.kt"
if not main.is_file() or not cloud.is_file():
    raise SystemExit("AmitySA Compose source files were not found")

s = main.read_text(encoding="utf-8").replace("\r\n", "\n")
c = cloud.read_text(encoding="utf-8").replace("\r\n", "\n")

def replace_once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}; source was not written")
    return source.replace(old, new, 1)

# Add a simple route history immediately after the app's screen state.
state_line = next((line for line in s.splitlines() if line.lstrip().startswith("var screen by remember")), None)
if state_line is None:
    raise SystemExit("Navigation history: could not find the app screen state declaration")
history = '''
    val screenHistory = remember { mutableStateListOf<String>() }
    fun navigateTo(target: String) {
        if (screen != target) {
            screenHistory.add(screen)
            screen = target
        }
    }
    fun goBack() {
        if (screenHistory.isNotEmpty()) {
            screen = screenHistory.removeAt(screenHistory.lastIndex)
        } else {
            screenHistory.clear()
            screen = "home"
        }
    }'''
if "val screenHistory = remember" not in s:
    s = s.replace(state_line, state_line + history, 1)

# Replace the existing Android BackHandler body using balanced delimiters.
back_start = s.find("BackHandler(")
if back_start < 0:
    raise SystemExit("Navigation history: Android BackHandler was not found")
paren_open = s.find("(", back_start)
depth = 0
paren_end = -1
for i in range(paren_open, len(s)):
    if s[i] == "(":
        depth += 1
    elif s[i] == ")":
        depth -= 1
        if depth == 0:
            paren_end = i + 1
            break
if paren_end < 0:
    raise SystemExit("Navigation history: could not parse BackHandler parameters")
body_open = s.find("{", paren_end)
depth = 0
body_end = -1
for i in range(body_open, len(s)):
    if s[i] == "{":
        depth += 1
    elif s[i] == "}":
        depth -= 1
        if depth == 0:
            body_end = i + 1
            break
if body_end < 0:
    raise SystemExit("Navigation history: could not parse BackHandler body")
s = s[:back_start] + '''BackHandler(enabled = acc != null && screen != "home") {
        goBack()
    }''' + s[body_end:]

# Route changes inside AmityApp now push the current screen. Return controls pop it.
app_start = s.index("fun AmityApp(")
app_end = s.index("\n// ---------- Connectivity ----------", app_start)
app = s[app_start:app_end]
app = app.replace('onBack = { screen = "home" }', 'onBack = { goBack() }')
for old, new in [
    ('onDone = { screen = "children" }', 'onDone = { goBack() }'),
    ('onClose = { screen = "home" }', 'onClose = { goBack() }'),
    ('onSetup = { screen = "sosSetup" }', 'onSetup = { navigateTo("sosSetup") }'),
    ('SosSetupScreen(acc) { screen = "home" }', 'SosSetupScreen(acc) { goBack() }'),
    ('FamilyMapScreen(acc) { screen = "home" }', 'FamilyMapScreen(acc) { goBack() }'),
    ('ZonesScreen(acc) { screen = "home" }', 'ZonesScreen(acc) { goBack() }'),
    ('FamilyCheckInScreen(acc) { screen = "home" }', 'FamilyCheckInScreen(acc) { goBack() }'),
    ('CloudScreen(acc) { screen = "home" }', 'CloudScreen(acc) { goBack() }'),
]:
    app = app.replace(old, new)

for route in ["home", "children", "edit", "sos", "sosSetup", "zones", "cloud", "security", "map", "checkin", "legal"]:
    app = app.replace(f'screen = "{route}"', f'navigateTo("{route}")')

# Sign-out and account deletion clear history rather than preserving stale routes.
app = app.replace('store.signOut(); account = null; navigateTo("home")',
                  'store.signOut(); account = null; screenHistory.clear(); screen = "home"')
app = app.replace('account = null; navigateTo("home")',
                  'account = null; screenHistory.clear(); screen = "home"')
app = app.replace('account = null; screenHistory.clear(); screen = "home"; locked = false',
                  'account = null; screenHistory.clear(); screen = "home"; locked = false')

# Put the legal page before the home screen branch.
home_branch = app.find("else HomeScreen(")
if home_branch < 0:
    raise SystemExit("Terms & Privacy: could not find the home-screen route")
if 'screen == "legal"' not in app:
    app = app[:home_branch] + 'else if (screen == "legal") TermsPrivacyScreen(onBack = { goBack() })\n            ' + app[home_branch:]

# Add a route from the existing Cloud link action.
cloud_route = 'action.title == "Cloud link" -> navigateTo("cloud")'
if cloud_route not in app:
    raise SystemExit("Terms & Privacy: Cloud link action route not found")
if 'action.title == "Terms & Privacy"' not in app:
    app = app.replace(cloud_route, cloud_route + '\n                        action.title == "Terms & Privacy" -> navigateTo("legal")', 1)
s = s[:app_start] + app + s[app_end:]

# Add a home tile after the existing Cloud link tile.
if 'QuickAction("📄", "Terms & Privacy"' not in s:
    tile_line = next((line for line in s.splitlines() if "QuickAction(" in line and '"Cloud link"' in line), None)
    if tile_line is None:
        raise SystemExit("Terms & Privacy: Cloud link home tile not found")
    s = s.replace(tile_line, tile_line + '\n' + tile_line[:len(tile_line) - len(tile_line.lstrip())] +
                  'QuickAction("📄", "Terms & Privacy", "Privacy, safety & app terms"),', 1)

# Explain privacy, sharing, risks and limitations in a dedicated in-app page.
legal = r'''

@Composable
private fun TermsPrivacyScreen(onBack: () -> Unit) {
    val t = LocalAmity.current
    val sections = listOf(
        "ABOUT AMITYSA" to "AmitySA is a family-safety and parent/educator coordination tool. It supports communication and awareness; it is not an emergency response service, medical service, or replacement for responsible adult supervision.",
        "YOUR INFORMATION AND PRIVACY" to "AmitySA is designed to keep information on your device by default. Account details, child notes and allergies, SOS contacts, safe-zone settings and information you do not choose to share are stored locally on your phone. The developer does not have automatic access to information stored only on your phone.",
        "OPTIONAL CLOUD LINKING" to "Cloud linking is optional and remains off until you choose to connect. If you create or accept a parent/teacher link, your username, role and child or learner details you deliberately share may be sent to the configured server. Shared details can include names, grade, class, school, guardian contact details and enabled feature settings. Notes and allergies are not included in the normal cloud-sharing flow. A linked parent or educator may see the information shared on that link. You can remove a link or delete shared records using the controls in the app.",
        "CHILD PHONE AND LOCATION" to "Pairing a child's phone and enabling location sharing requires an adult to set it up. When enabled, the paired phone may send location updates to the configured server so an authorised linked adult can view them. Location can be inaccurate, delayed or unavailable because of GPS, device settings, battery saving, mobile coverage or network problems. Turn location sharing off or unpair the device when it is no longer needed.",
        "INVITES AND SHARING" to "Invite codes and links are intended only for the parent or educator you choose. Anyone who obtains a valid, unused invite may be able to attempt to join, so share it privately and do not post it publicly. Do not share screenshots, codes or child information with people who are not authorised. Check the recipient and information selected before sharing.",
        "SECURITY AND DATA LOSS" to "The app uses security measures such as encrypted network connections and account/device tokens where supported. No app, phone, server, internet connection or storage system can be guaranteed completely secure or free from failure. Unauthorised access, device loss, malware, weak device passwords, misdirected invites, service outages or accidental deletion may expose, alter or cause loss of information. Keep your phone and accounts protected and maintain any backups you need. Do not use AmitySA as the only copy of critical information.",
        "EMERGENCY AND SAFETY LIMITS" to "Do not rely on AmitySA as the only way to contact emergency services or check on a child. SOS delivery, calls, messages, notifications and location updates depend on your phone, permissions, battery, mobile network and third-party services. In an emergency, contact the appropriate emergency service directly and follow local safety procedures.",
        "YOUR RESPONSIBILITIES" to "You are responsible for using the app lawfully, obtaining any required parent/guardian or school authority, informing people where required, choosing who receives invites, reviewing permissions and keeping your device secure. Parents and educators remain responsible for decisions about children's care, supervision and safety.",
        "SERVICE DISCLAIMER AND LIABILITY" to "AmitySA is provided as a tool on an 'as available' basis. The developer does not promise uninterrupted service, error-free operation, perfect location accuracy, successful delivery of every alert, or absolute protection against cyberattacks or data loss. To the maximum extent permitted by applicable law, the developer is not liable for indirect or consequential loss arising from outages, misuse, inaccurate information, unauthorised access or data loss. Nothing in these terms excludes or limits liability, consumer rights, privacy rights or remedies that cannot legally be excluded or limited under South African law or other applicable law. These terms do not excuse deliberate wrongdoing or any duty that the law requires the developer to meet.",
        "PRIVACY RIGHTS AND CONTACT" to "You may request access to, correction of or deletion of personal information, subject to applicable law. In South Africa, personal information is protected by the Protection of Personal Information Act (POPIA), and complaints may be directed to the Information Regulator. For support or privacy requests, use the current contact details published with the official AmitySA app listing. The developer must keep those contact details and the public privacy policy up to date.",
        "CHANGES TO THESE TERMS" to "These terms and the privacy information may be updated when the app or its services change. The latest version shown here applies from the date it is published in the app. Important changes should be clearly communicated before they take effect where required by law."
    )
    Column(Modifier.fillMaxSize().background(t.canvas)) {
        ScreenHeader("Terms, Privacy & Safety", onBack)
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Card(
                colors = CardDefaults.cardColors(containerColor = t.card),
                shape = RoundedCornerShape(18.dp)
            ) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Your privacy matters", color = t.ink, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    Text("Cloud sharing is optional. You choose whether to link, what to share and who receives an invite.", color = t.inkSoft, fontSize = 13.sp)
                }
            }
            sections.forEach { (heading, body) ->
                Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    Text(heading, color = t.primary, fontSize = 13.sp, fontWeight = FontWeight.ExtraBold)
                    Text(body, color = t.ink, fontSize = 13.sp, lineHeight = 19.sp)
                }
                HorizontalDivider(color = t.inkSoft.copy(alpha = 0.18f))
            }
            Text("Last reviewed: 4 November 2026", color = t.inkSoft, fontSize = 11.sp)
        }
    }
}
'''
if "private fun TermsPrivacyScreen(" not in s:
    s += legal
main.write_text(s, encoding="utf-8")

# Both options create a fresh server-side random code; the server expires pending
# invites after 24 hours and accepts each code once.
needle = '''                    Button(
                        onClick = { launchCloud { withContext(Dispatchers.IO) { client().createLink() }; doSync() } },
                        enabled = !busy, modifier = Modifier.fillMaxWidth().height(48.dp),
                        shape = RoundedCornerShape(14.dp), colors = buttonColors
                    ) { Text("Create an invite", fontWeight = FontWeight.SemiBold) }'''
replacement = '''                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Button(
                            onClick = { launchCloud { withContext(Dispatchers.IO) { client().createLink() }; doSync() } },
                            enabled = !busy, modifier = Modifier.weight(1f).height(48.dp),
                            shape = RoundedCornerShape(14.dp), colors = buttonColors
                        ) { Text("Create link", fontSize = 11.sp, fontWeight = FontWeight.SemiBold, maxLines = 1) }
                        OutlinedButton(
                            onClick = { launchCloud { withContext(Dispatchers.IO) { client().createLink() }; doSync() } },
                            enabled = !busy, modifier = Modifier.weight(1f).height(48.dp),
                            shape = RoundedCornerShape(14.dp)
                        ) { Text("Generate random link", color = t.primary, fontSize = 11.sp, fontWeight = FontWeight.SemiBold, maxLines = 1) }
                    }
                    Text("Each option creates a fresh, one-time invite code that expires after 24 hours. Share it only with the parent or teacher you intend to link with.", color = t.inkSoft, fontSize = 11.sp)'''
c = replace_once(c, needle, replacement, "create/random invite button row")
cloud.write_text(c, encoding="utf-8")
print("Added previous-screen navigation, random parent/teacher invite option, and Terms/Privacy/Safety page.")
