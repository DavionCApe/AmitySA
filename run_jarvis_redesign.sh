#!/usr/bin/env bash
# AmitySA JARVIS redesign task runner.
# Run from any directory; project paths are resolved from this script's location.
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

BRANCH="${AMITYSA_BRANCH:-design/neon-glass-ui}"
COMMIT_MESSAGE="${AMITYSA_COMMIT_MESSAGE:-Apply JARVIS FUI/HUD redesign}"
NO_GIT=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: ./run_jarvis_redesign.sh [--dry-run] [--no-git]

Runs compile-context discovery, available JARVIS/dashboard/HUD/palette scripts,
then a supported Kotlin formatter. By default it stages project changes,
creates a commit when needed, and pushes the configured branch to origin.

Options:
  --dry-run  Print commands and checks without running scripts or Git writes.
  --no-git   Run redesign and formatting steps, but do not stage/commit/push.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --no-git) NO_GIT=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; usage >&2; exit 2 ;;
  esac
done

log() { printf '\n[JARVIS] %s\n' "$*"; }
warn() { printf '\n[WARN] %s\n' "$*" >&2; }
die() { printf '\n[ERROR] %s\n' "$*" >&2; exit 1; }

run() {
  if (( DRY_RUN )); then
    printf '[DRY-RUN]'; printf ' %q' "$@"; printf '\n'
  else
    "$@"
  fi
}

command -v python3 >/dev/null 2>&1 || die "python3 is required."
[[ -x ./gradlew ]] || die "Gradle wrapper ./gradlew is missing or not executable."
[[ -d .git ]] || die "Run this task runner from an AmitySA Git checkout."

PYTHON_BIN="$(command -v python3)"

run_python_script() {
  local script="$1"
  if [[ -f "$script" ]]; then
    log "Running $script"
    run "$PYTHON_BIN" "$script"
  else
    warn "Optional script not found; skipping: $script"
  fi
}

log "Project root: $ROOT_DIR"
log "Target branch: $BRANCH"

# Context report first, before source transformations.
run_python_script "scripts/print_compile_context.py"

# Primary Compose/JARVIS interface pass, then dashboard pass.
run_python_script "scripts/apply_jarvis_primary_interface.py"
run_python_script "scripts/apply_dashboard_redesign.py"

# Native HUD and Android resource palette alignment macros.
run_python_script "scripts/apply_fui_hud.py"
run_python_script "scripts/apply_theme_consistency.py"

# Prefer Spotless; fall back to ktlintFormat when spotlessApply is unavailable.
log "Formatting Kotlin sources"
if (( DRY_RUN )); then
  printf '[DRY-RUN] ./gradlew spotlessApply (fallback: ./gradlew ktlintFormat)\n'
else
  set +e
  SPOTLESS_OUTPUT="$(./gradlew spotlessApply --no-daemon 2>&1)"
  SPOTLESS_STATUS=$?
  set -e
  printf '%s\n' "$SPOTLESS_OUTPUT"
  if (( SPOTLESS_STATUS != 0 )); then
    if grep -Fq "Task 'spotlessApply' not found" <<<"$SPOTLESS_OUTPUT"; then
      warn "spotlessApply is not configured; trying ktlintFormat."
      ./gradlew ktlintFormat --no-daemon || die "Both formatting options failed; inspect Gradle output."
    else
      die "spotlessApply failed for another reason; refusing to hide the formatter error."
    fi
  fi
fi

if (( NO_GIT )); then
  log "Completed without Git staging, commit, or push (--no-git)."
  exit 0
fi

if (( DRY_RUN )); then
  log "Dry run complete. Git stage/commit/push would target branch $BRANCH."
  exit 0
fi

command -v git >/dev/null 2>&1 || die "git is required for the deployment sequence."
CURRENT_BRANCH="$(git branch --show-current)"
[[ "$CURRENT_BRANCH" == "$BRANCH" ]] || die "Refusing to commit on '$CURRENT_BRANCH'; checkout '$BRANCH' first."

# Stage project source/configuration and scripts, excluding generated backups
# and build outputs. Review git status before running if the checkout has edits.
git add -A -- app scripts .github run_jarvis_redesign.sh || die "Git staging failed."
git reset -q -- .amitysa-theme-backups app/build 2>/dev/null || true

if git diff --cached --quiet; then
  log "No staged changes; nothing to commit."
else
  log "Creating commit"
  git -c core.hooksPath=/dev/null commit -m "$COMMIT_MESSAGE"
fi

log "Pushing $BRANCH to origin"
git push origin "$BRANCH"
log "Redesign sequence and Git push completed."
