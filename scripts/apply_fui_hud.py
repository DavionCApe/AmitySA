from pathlib import Path

main = Path("app/src/main/java/com/amitysa/app/MainActivity.kt")
if not main.exists():
    raise SystemExit("AmitySA MainActivity.kt was not found")

s = main.read_text(encoding="utf-8")

# Add the drawing import without duplicating it.
if "import androidx.compose.foundation.Canvas" not in s:
    anchor = "import androidx.compose.foundation.background"
    if anchor in s:
        s = s.replace(anchor, "import androidx.compose.foundation.Canvas\n" + anchor, 1)
    else:
        first = s.find("import ")
        if first < 0:
            raise SystemExit("Could not find Kotlin imports for the HUD overlay")
        s = s[:first] + "import androidx.compose.foundation.Canvas\n" + s[first:]

# The theme-consistency stage wraps the entire app in this root Surface.
# Draw a subtle non-interactive HUD overlay after the page content so every
# screen receives the same sci-fi frame without changing touch behavior.
marker = """            if (showPopup) LaunchPopup { showPopup = false }
        }
        }
    }
}"""
overlay = """            if (showPopup) LaunchPopup { showPopup = false }
        }
        Canvas(modifier = Modifier.fillMaxSize()) {
            val hud = Color(0x9954C8FF)
            val bright = Color(0xCCB8E8FF)
            val corner = 24f
            val inset = 13f
            val arm = 17f
            val stroke = 2.2f

            // Four precision corner brackets.
            drawLine(hud, androidx.compose.ui.geometry.Offset(inset, inset), androidx.compose.ui.geometry.Offset(inset + arm, inset), stroke)
            drawLine(hud, androidx.compose.ui.geometry.Offset(inset, inset), androidx.compose.ui.geometry.Offset(inset, inset + arm), stroke)
            drawLine(hud, androidx.compose.ui.geometry.Offset(size.width - inset, inset), androidx.compose.ui.geometry.Offset(size.width - inset - arm, inset), stroke)
            drawLine(hud, androidx.compose.ui.geometry.Offset(size.width - inset, inset), androidx.compose.ui.geometry.Offset(size.width - inset, inset + arm), stroke)
            drawLine(hud, androidx.compose.ui.geometry.Offset(inset, size.height - inset), androidx.compose.ui.geometry.Offset(inset + arm, size.height - inset), stroke)
            drawLine(hud, androidx.compose.ui.geometry.Offset(inset, size.height - inset), androidx.compose.ui.geometry.Offset(inset, size.height - inset - arm), stroke)
            drawLine(hud, androidx.compose.ui.geometry.Offset(size.width - inset, size.height - inset), androidx.compose.ui.geometry.Offset(size.width - inset - arm, size.height - inset), stroke)
            drawLine(hud, androidx.compose.ui.geometry.Offset(size.width - inset, size.height - inset), androidx.compose.ui.geometry.Offset(size.width - inset, size.height - inset - arm), stroke)

            // Fine telemetry ticks along the top and bottom edges.
            for (index in 0..10) {
                val x = size.width * (index + 1) / 12f
                val tick = if (index % 5 == 0) 10f else 4f
                drawLine(hud, androidx.compose.ui.geometry.Offset(x, 8f), androidx.compose.ui.geometry.Offset(x, 8f + tick), 1.2f)
                drawLine(hud, androidx.compose.ui.geometry.Offset(x, size.height - 8f), androidx.compose.ui.geometry.Offset(x, size.height - 8f - tick), 1.2f)
            }
            // Small centre alignment marker.
            val cx = size.width / 2f
            drawLine(bright, androidx.compose.ui.geometry.Offset(cx - 13f, 15f), androidx.compose.ui.geometry.Offset(cx + 13f, 15f), 1.4f)
            drawLine(bright, androidx.compose.ui.geometry.Offset(cx, 9f), androidx.compose.ui.geometry.Offset(cx, 21f), 1.4f)
        }
        }
    }
}"""
if "val bright = Color(0xCCB8E8FF)" not in s:
    if marker not in s:
        raise SystemExit("Could not locate the final app-wide theme wrapper for the HUD overlay")
    s = s.replace(marker, overlay, 1)

main.write_text(s, encoding="utf-8")

# Give the existing shared reflective backdrop a restrained blue energy tint.
for path in Path("app/src/main/java/com/amitysa/app").glob("*.kt"):
    source = path.read_text(encoding="utf-8")
    source = source.replace(
        "listOf(Color(0xFF080B12), Color(0xFF111C2A), Color(0xFF07090F))",
        "listOf(Color(0xFF050A13), Color(0xFF102338), Color(0xFF070B14))"
    )
    path.write_text(source, encoding="utf-8")

print("Applied AmitySA FUI + Sci-Fi HUD styling app-wide: precision corner brackets, telemetry ticks, cyan alignment reticle and deep-space reflective backdrop.")
