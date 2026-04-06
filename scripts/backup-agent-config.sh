#!/usr/bin/env bash
# backup-agent-config.sh — Back up agent-specific directories and config files
#
# Creates a timestamped snapshot of all AI agent settings so inadvertent
# changes can be recovered easily.
#
# Usage:
#   ./scripts/backup-agent-config.sh [BACKUP_ROOT]
#
#   BACKUP_ROOT  Directory to store backups (default: ~/agent-config-backups)
#
# What is backed up:
#   ~/.claude/  — Claude Code global config (selected subdirs, skips cache/telemetry)
#   .claude/    — Per-repo Claude Code config (relative to this repo)
#   .vscode/    — Per-repo VS Code / GitHub Copilot config
#   .mcp.json   — Per-repo MCP server config
#   ~/Library/Application Support/Claude/claude_desktop_config.json
#   ~/Library/Application Support/Code/User/globalStorage/
#       saoudrizwan.claude-dev/settings/cline_mcp_settings.json

set -euo pipefail

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="${1:-"$HOME/agent-config-backups"}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DEST="$BACKUP_ROOT/$TIMESTAMP"

CLAUDE_GLOBAL="$HOME/.claude"
CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
CLINE_SETTINGS="$HOME/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"

# ── Helpers ────────────────────────────────────────────────────────────────────
log()  { echo "  [backup] $*"; }
warn() { echo "  [skip]   $* — not found"; }

backup_dir() {
    local src="$1" dest_subdir="$2"
    if [[ -d "$src" ]]; then
        mkdir -p "$DEST/$dest_subdir"
        cp -R "$src/." "$DEST/$dest_subdir/"
        log "$src  →  $DEST/$dest_subdir/"
    else
        warn "$src"
    fi
}

backup_file() {
    local src="$1" dest_subdir="$2"
    if [[ -f "$src" ]]; then
        mkdir -p "$DEST/$dest_subdir"
        cp "$src" "$DEST/$dest_subdir/"
        log "$src  →  $DEST/$dest_subdir/"
    else
        warn "$src"
    fi
}

# ── Create destination ─────────────────────────────────────────────────────────
mkdir -p "$DEST"
echo ""
echo "  CodeKG agent config backup"
echo "  Timestamp : $TIMESTAMP"
echo "  Location  : $DEST"
echo "  ────────────────────────────────────────"

# ── 1.  ~/.claude — global Claude Code config (exclude ephemeral/runtime dirs) ──
#    Excluded (runtime / cache / history — too large, not config):
#      cache, debug, file-history, history.jsonl, shell-snapshots, session-env,
#      telemetry, todos, plugins, statsig, worktrees, __store.db,
#      projects (conversation history — hundreds of MB),
#      copilot/mcp-servers (downloaded MCP server binaries — ~500 MB)
CLAUDE_DEST="$DEST/claude-global"
mkdir -p "$CLAUDE_DEST"

# Top-level config files and lightweight config dirs
for item in \
    CLAUDE.md \
    config.json \
    settings.json \
    settings.local.json \
    agents \
    commands \
    memory \
    plans \
    skills \
    tasks
do
    src="$CLAUDE_GLOBAL/$item"
    if [[ -e "$src" ]]; then
        cp -R "$src" "$CLAUDE_DEST/"
        log "~/.claude/$item"
    else
        warn "~/.claude/$item"
    fi
done

# copilot dir — back up everything except the heavy mcp-servers download cache
if [[ -d "$CLAUDE_GLOBAL/copilot" ]]; then
    COPILOT_DEST="$CLAUDE_DEST/copilot"
    mkdir -p "$COPILOT_DEST"
    find "$CLAUDE_GLOBAL/copilot" -mindepth 1 -maxdepth 1 \
        ! -name "mcp-servers" \
        -exec cp -R {} "$COPILOT_DEST/" \;
    log "~/.claude/copilot (excluding mcp-servers/)"
else
    warn "~/.claude/copilot"
fi

# ── 2.  Per-repo .claude/ ──────────────────────────────────────────────────────
backup_dir "$REPO_ROOT/.claude"  "repo/dot-claude"

# ── 3.  Per-repo .vscode/ ─────────────────────────────────────────────────────
backup_dir "$REPO_ROOT/.vscode"  "repo/dot-vscode"

# ── 4.  Per-repo .mcp.json ────────────────────────────────────────────────────
backup_file "$REPO_ROOT/.mcp.json"  "repo"

# ── 5.  Claude Desktop config ─────────────────────────────────────────────────
backup_file "$CLAUDE_DESKTOP_CONFIG"  "claude-desktop"

# ── 6.  Cline MCP settings ────────────────────────────────────────────────────
backup_file "$CLINE_SETTINGS"  "cline"

# ── Summary ───────────────────────────────────────────────────────────────────
echo "  ────────────────────────────────────────"
TOTAL_SIZE=$(du -sh "$DEST" 2>/dev/null | cut -f1)
echo "  Done. Total size: $TOTAL_SIZE"
echo ""

# ── Housekeeping: keep last N backups ─────────────────────────────────────────
KEEP=${CODEKG_BACKUP_KEEP:-20}
BACKUP_COUNT=$(find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
if (( BACKUP_COUNT > KEEP )); then
    TO_DELETE=$(( BACKUP_COUNT - KEEP ))
    echo "  Pruning $TO_DELETE old backup(s) (keeping last $KEEP)..."
    find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d | sort | head -"$TO_DELETE" | while read -r old; do
        rm -rf "$old"
        echo "  [pruned] $old"
    done
    echo ""
fi
