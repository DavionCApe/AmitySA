package com.amitysa.app

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
    private val alias = "amity_saved_login_aes_v1"

    @Synchronized fun save(email: String, password: String) {
        try {
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())
            val encrypted = cipher.doFinal(password.toByteArray(Charsets.UTF_8))
            prefs.edit().putString("email", email.trim().lowercase())
                .putString("nonce", Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
                .putString("password", Base64.encodeToString(encrypted, Base64.NO_WRAP)).apply()
        } catch (_: Exception) { clear() }
    }

    @Synchronized fun load(): SavedLogin? {
        val email = prefs.getString("email", null) ?: return null
        val nonce = prefs.getString("nonce", null) ?: return null
        val encrypted = prefs.getString("password", null) ?: return null
        return try {
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(),
                GCMParameterSpec(128, Base64.decode(nonce, Base64.NO_WRAP)))
            SavedLogin(email, cipher.doFinal(Base64.decode(encrypted, Base64.NO_WRAP)).toString(Charsets.UTF_8))
        } catch (_: Exception) { clear(); null }
    }

    @Synchronized fun clear() { prefs.edit().clear().apply() }

    private fun getOrCreateKey(): SecretKey {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (ks.getKey(alias, null) as? SecretKey)?.let { return it }
        val gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        gen.init(KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setRandomizedEncryptionRequired(true).build())
        return gen.generateKey()
    }
}
