package com.example.amitysa.ui.theme // Ensure this matches your project package structure

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Defining the signature JARVIS / Iron Man color profile
val JarvisSpaceDark = Color(0密0D1117)       // Deep obsidian background
val JarvisNeonCyan = Color(0xFF00D2FF)        // Principal glowing interface accent
val JarvisLaserBlue = Color(0xFF0066FF)       // Secondary electric blue highlight
val JarvisTranslucentSlate = Color(0x991A2332) // Translucent glass surface panel
val JarvisMutedText = Color(0xFF8B949E)        // Crisp secondary scannable data tone

private val JarvisColorScheme = darkColorScheme(
    primary = JarvisNeonCyan,
    secondary = JarvisLaserBlue,
    background = JarvisSpaceDark,
    surface = JarvisTranslucentSlate,
    onPrimary = Color.Black,
    onBackground = Color.White,
    onSurface = Color.White
)

@Composable
fun JarvisTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = JarvisColorScheme,
        content = content
    )
}
