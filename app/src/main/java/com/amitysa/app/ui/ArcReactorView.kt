package com.amitysa.app.ui.components

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp

@Composable
fun ArcReactorView(
    modifier: Modifier = Modifier,
    baseColor: Color = Color(0xFF00D2FF)
) {
    val infiniteTransition = rememberInfiniteTransition(label = "ArcReactorPulse")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.85f,
        targetValue = 1.05f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 1500, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "PulseScale"
    )

    Canvas(modifier = modifier.size(120.dp)) {
        val maxRadius = size.minDimension / 2
        drawCircle(
            color = baseColor.copy(alpha = 0.3f),
            radius = maxRadius * 0.9f,
            style = Stroke(width = 2.dp.toPx())
        )
        drawCircle(
            color = baseColor.copy(alpha = 0.15f * pulseScale),
            radius = maxRadius * 0.7f * pulseScale
        )
        drawCircle(
            color = baseColor,
            radius = maxRadius * 0.2f
        )
    }
}
