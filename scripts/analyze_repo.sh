#!/usr/bin/env bash
# analyze_repo.sh — Clone a GitHub repo, build CodeKG, run analysis, save to analysis/
#
# Usage:
#   ./scripts/analyze_repo.sh owner/repo
#   ./scripts/analyze_repo.sh https://github.com/owner/repo
#   ./scripts/analyze_repo.sh owner/repo --include-dir src --include-dir lib
#
# Extra flags after the repo argument are forwarded to codekg-build-sqlite.
# If no --include-dir is given, the script auto-detects the Python package dir
# (looks for a subdir matching the repo name, then src/, then falls back to all).
#
# Output: analysis/<repo_name>_analysis_<YYYYMMDD>.md

set -euo pipefail

# ── helpers ──────────────────────────────────────────────────────────────────

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}▶ $*${NC}"; }
success() { echo -e "${GREEN}✓ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠ $*${NC}"; }
die()     { echo -e "${RED}✗ $*${NC}" >&2; exit 1; }

# ── args ─────────────────────────────────────────────────────────────────────

[[ $# -lt 1 ]] && die "Usage: $0 owner/repo [--include-dir DIR ...]"

INPUT="$1"
shift
EXTRA_BUILD_ARGS=("$@")   # remaining args forwarded to codekg-build-sqlite

# Normalise: strip trailing .git, extract owner/repo from URL or bare slug
INPUT="${INPUT%.git}"
if [[ "$INPUT" =~ ^https?://github\.com/([^/]+/[^/]+) ]]; then
    SLUG="${BASH_REMATCH[1]}"
elif [[ "$INPUT" =~ ^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)$ ]]; then
    SLUG="$INPUT"
else
    die "Cannot parse '$INPUT' as a GitHub repo. Provide 'owner/repo' or a GitHub URL."
fi

OWNER="${SLUG%/*}"
REPO_NAME="${SLUG#*/}"
CLONE_URL="https://github.com/${SLUG}.git"

REPOS_DIR="$HOME/repos"
CLONE_DIR="$REPOS_DIR/$REPO_NAME"

# analysis/ is relative to the code_kg repo root (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODE_KG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ANALYSIS_DIR="$CODE_KG_ROOT/analysis"

DATE_STAMP="$(date +%Y%m%d)"
OUT_FILE="$ANALYSIS_DIR/${REPO_NAME}_analysis_${DATE_STAMP}.md"

# ── preflight ────────────────────────────────────────────────────────────────

info "Target repo : $SLUG"
info "Clone path  : $CLONE_DIR"
info "Output file : $OUT_FILE"
echo

command -v git   >/dev/null || die "git not found"
command -v codekg-build-sqlite >/dev/null || \
command -v codekg >/dev/null || \
    die "codekg not found — run this script from within the code-kg virtual environment"

mkdir -p "$REPOS_DIR" "$ANALYSIS_DIR"

# ── clone (or refresh) ───────────────────────────────────────────────────────

if [[ -d "$CLONE_DIR/.git" ]]; then
    warn "Repo already exists at $CLONE_DIR — pulling latest..."
    git -C "$CLONE_DIR" pull --ff-only
else
    info "Cloning $CLONE_URL → $CLONE_DIR"
    git clone --depth 1 "$CLONE_URL" "$CLONE_DIR"
fi
success "Repo ready"
echo

# ── resolve --include-dir (auto-detect if none supplied) ─────────────────────

has_include_dir=false
for arg in "${EXTRA_BUILD_ARGS[@]+"${EXTRA_BUILD_ARGS[@]}"}"; do
    [[ "$arg" == "--include-dir" ]] && has_include_dir=true && break
done

if ! $has_include_dir; then
    # Heuristic: repo_name/ > src/ (only if it contains .py files) > lib/ > (nothing = index all)
    if [[ -d "$CLONE_DIR/$REPO_NAME" ]] && \
       find "$CLONE_DIR/$REPO_NAME" -maxdepth 3 -name "*.py" -quit -print 2>/dev/null | grep -q .; then
        warn "Auto-detected package dir: $REPO_NAME/"
        EXTRA_BUILD_ARGS+=(--include-dir "$REPO_NAME")
    elif [[ -d "$CLONE_DIR/src" ]] && \
         find "$CLONE_DIR/src" -maxdepth 3 -name "*.py" -quit -print 2>/dev/null | grep -q .; then
        warn "Auto-detected package dir: src/"
        EXTRA_BUILD_ARGS+=(--include-dir src)
    elif [[ -d "$CLONE_DIR/lib" ]] && \
         find "$CLONE_DIR/lib" -maxdepth 3 -name "*.py" -quit -print 2>/dev/null | grep -q .; then
        warn "Auto-detected package dir: lib/"
        EXTRA_BUILD_ARGS+=(--include-dir lib)
    else
        warn "No package subdir found — indexing entire repo"
    fi
fi
echo

# ── build CodeKG ─────────────────────────────────────────────────────────────

info "Building CodeKG SQLite index..."
codekg-build-sqlite --repo "$CLONE_DIR" --wipe "${EXTRA_BUILD_ARGS[@]+"${EXTRA_BUILD_ARGS[@]}"}" 2>&1 | sed 's/^/  /'

info "Building CodeKG LanceDB (semantic) index..."
codekg-build-lancedb --repo "$CLONE_DIR" 2>&1 | sed 's/^/  /'

success "Knowledge graph built"
echo

# ── analyse ──────────────────────────────────────────────────────────────────

info "Running analysis → $OUT_FILE"
codekg-analyze "$CLONE_DIR" --output "$OUT_FILE" 2>&1 | sed 's/^/  /'

if [[ -f "$OUT_FILE" ]]; then
    SIZE="$(wc -l < "$OUT_FILE" | tr -d ' ')"
    success "Analysis saved: $OUT_FILE  (${SIZE} lines)"
else
    die "Analysis finished but output file not found: $OUT_FILE"
fi

echo
echo -e "${GREEN}All done! Open the report:${NC}"
echo "  $OUT_FILE"
