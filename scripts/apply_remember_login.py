from pathlib import Path
p = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
s = p.read_text(encoding="utf-8")

def once(old, new, name):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{name}: expected one match, found {n}; source unchanged.")
    s = s.replace(old, new, 1)

once(
    '    val store = remember { AccountStore(context) }\n    var account by remember { mutableStateOf(store.currentAccount()) }',
    '    val store = remember { AccountStore(context) }\n    val rememberLoginStore = remember { RememberLoginStore(context) }\n    var rememberLoginPrompt by remember { mutableStateOf<Pair<Account, String>?>(null) }\n    var account by remember { mutableStateOf(store.currentAccount()) }',
    "remember-login state")
once(
    'onAuthenticated = { account = it; showAuth = false },',
    """onAuthenticated = { authenticated, passwordToSave ->
                    account = authenticated
                    showAuth = false
                    if (passwordToSave != null) rememberLoginPrompt = authenticated to passwordToSave
                },""",
    "authentication callback")
once(
    """            if (showThemes) {
                ThemeDialog(""",
    """            rememberLoginPrompt?.let { pending ->
                AlertDialog(
                    onDismissRequest = { rememberLoginPrompt = null },
                    title = { Text("Save login details on this device?") },
                    text = { Text("Save your login details securely on this device so they can be filled in next time you sign in. Your password is encrypted using Android Keystore and is not stored as plain text.") },
                    confirmButton = {
                        TextButton(onClick = {
                            rememberLoginStore.save(pending.first.email, pending.second)
                            rememberLoginPrompt = null
                            Toast.makeText(context, "Login details saved securely on this device.", Toast.LENGTH_SHORT).show()
                        }) { Text("Save details") }
                    },
                    dismissButton = { TextButton(onClick = { rememberLoginPrompt = null }) { Text("Not now") } }
                )
            }
            if (showThemes) {
                ThemeDialog(""",
    "save-login prompt")
once(
    'private fun AuthScreen(store: AccountStore, online: Boolean, onChildSetup: () -> Unit, onAuthenticated: (Account) -> Unit, onPreview: () -> Unit, startRegistering: Boolean) {',
    'private fun AuthScreen(store: AccountStore, online: Boolean, onChildSetup: () -> Unit, onAuthenticated: (Account, String?) -> Unit, onPreview: () -> Unit, startRegistering: Boolean) {',
    "AuthScreen callback")
once(
    '    val t = LocalAmity.current\n    var registering by remember { mutableStateOf(startRegistering) }',
    '    val t = LocalAmity.current\n    val context = LocalContext.current\n    val rememberLoginStore = remember { RememberLoginStore(context) }\n    var savedLogin by remember { mutableStateOf(rememberLoginStore.load()) }\n    var registering by remember { mutableStateOf(startRegistering) }',
    "AuthScreen storage")
once(
    '    var email by remember { mutableStateOf("") }\n    var phone by remember { mutableStateOf("") }\n    var password by remember { mutableStateOf("") }',
    '    var email by remember { mutableStateOf(savedLogin?.email ?: "") }\n    var phone by remember { mutableStateOf("") }\n    var password by remember { mutableStateOf(savedLogin?.password ?: "") }',
    "prefill saved details")
once(
    '            is AuthResult.Success -> onAuthenticated(result.account)',
    '            is AuthResult.Success -> onAuthenticated(result.account, password)',
    "successful sign-in")
once(
    """            if (registering) {
                AuthField(confirm, { confirm = it; error = null }, "Confirm password", password = true, showPassword = showPassword)
            }

            error?.let""",
    """            if (registering) {
                AuthField(confirm, { confirm = it; error = null }, "Confirm password", password = true, showPassword = showPassword)
            }
            if (!registering && savedLogin != null) {
                TextButton(onClick = {
                    rememberLoginStore.clear()
                    savedLogin = null
                    email = ""
                    password = ""
                    Toast.makeText(context, "Saved login details removed from this device.", Toast.LENGTH_SHORT).show()
                }, modifier = Modifier.fillMaxWidth()) {
                    Text("Remove saved login details", color = t.primary)
                }
            }

            error?.let""",
    "remove saved details control")
p.write_text(s, encoding="utf-8")
print("Remember-login feature integrated.")
