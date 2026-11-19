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

# The archive contained a stale placeholder MainActivity in this file.
# Replace it with the encrypted credential store expected by MainActivity.kt.
store = Path("app/src/main/java/com/amitysa/app/RememberLoginStore.kt")
store.write_text("""package com.amitysa.app

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

data class SavedLogin(val email: String, val password: String)

class RememberLoginStore(context: Context) {
    private val prefs = context.getSharedPreferences("amity_saved_login", Context.MODE_PRIVATE)
    private val alias = "amitysa_remember_login_key"

    fun save(email: String, password: String) {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())
        val encrypted = cipher.doFinal(password.toByteArray(Charsets.UTF_8))
        prefs.edit()
            .putString("email", email)
            .putString("iv", Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
            .putString("password", Base64.encodeToString(encrypted, Base64.NO_WRAP))
            .apply()
    }

    fun load(): SavedLogin? {
        val email = prefs.getString("email", null) ?: return null
        val ivText = prefs.getString("iv", null) ?: return null
        val passwordText = prefs.getString("password", null) ?: return null
        return try {
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(
                Cipher.DECRYPT_MODE,
                getOrCreateKey(),
                GCMParameterSpec(128, Base64.decode(ivText, Base64.NO_WRAP))
            )
            val password = cipher.doFinal(Base64.decode(passwordText, Base64.NO_WRAP))
                .toString(Charsets.UTF_8)
            SavedLogin(email, password)
        } catch (_: Exception) {
            clear()
            null
        }
    }

    fun clear() {
        prefs.edit().clear().apply()
    }

    private fun getOrCreateKey(): SecretKey {
        val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (keyStore.getKey(alias, null) as? SecretKey)?.let { return it }
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        generator.init(
            KeyGenParameterSpec.Builder(
                alias,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build()
        )
        return generator.generateKey()
    }
}
""", encoding="utf-8")
print("Installed encrypted Android Keystore-backed RememberLoginStore.")
