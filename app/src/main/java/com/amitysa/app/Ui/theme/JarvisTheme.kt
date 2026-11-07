package com.amitysa.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val JarvisSpaceDark = Color(0xFF0D1117)       // Deep cyber obsidian core
val JarvisNeonCyan = Color(0xFF00D2FF)        // Holographic signature interface accent
val JarvisLaserBlue = Color(0xFF0066FF)       // Electric edge glowing trim
val JarvisTranslucentSlate = Color(0x991A2332) // Translucent frosted sci-fi glass panel

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
fun AmitySaJarvisTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = JarvisColorScheme,
        content = content
    )
}
