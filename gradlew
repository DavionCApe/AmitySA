#!/usr/bin/env sh
# Lightweight Gradle launcher for AmitySA.
# Uses the pinned Gradle distribution when no system Gradle is installed.
set -eu

APP_HOME=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
GRADLE_VERSION="${GRADLE_VERSION:-8.11.1}"

if command -v gradle >/dev/null 2>&1; then
  exec gradle "$@"
fi

if ! command -v curl >/dev/null 2>&1 || ! command -v unzip >/dev/null 2>&1; then
  echo "Gradle is not installed and curl/unzip are required to bootstrap Gradle $GRADLE_VERSION." >&2
  exit 1
fi

GRADLE_USER_HOME="${GRADLE_USER_HOME:-$HOME/.gradle}"
DIST_DIR="$GRADLE_USER_HOME/wrapper/dists/amitysa-gradle-$GRADLE_VERSION"
GRADLE_HOME="$DIST_DIR/gradle-$GRADLE_VERSION"
GRADLE_BIN="$GRADLE_HOME/bin/gradle"

if [ ! -x "$GRADLE_BIN" ]; then
  mkdir -p "$DIST_DIR"
  ZIP_FILE="$DIST_DIR/gradle-$GRADLE_VERSION-bin.zip"
  echo "Downloading Gradle $GRADLE_VERSION..."
  curl --fail --location --silent --show-error \
    "https://services.gradle.org/distributions/gradle-$GRADLE_VERSION-bin.zip" \
    --output "$ZIP_FILE"
  unzip -q -o "$ZIP_FILE" -d "$DIST_DIR"
  rm -f "$ZIP_FILE"
fi

if [ ! -x "$GRADLE_BIN" ]; then
  echo "Gradle bootstrap failed: $GRADLE_BIN was not created." >&2
  exit 1
fi

exec "$GRADLE_BIN" "$@"
