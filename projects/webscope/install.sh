#!/usr/bin/env bash
# webscope installer — downloads the single-file tool onto your PATH.
# No sudo, no dependencies (webscope is Python 3.9+ stdlib only).
#
#   curl -fsSL <raw-url>/install.sh | bash
#
# Override the source ref or install dir if you like:
#   WEBSCOPE_REF=main WEBSCOPE_BIN="$HOME/bin" bash install.sh
set -euo pipefail

REPO="rydermetcalfx4-commits/agent"
REF="${WEBSCOPE_REF:-main}"
BIN_DIR="${WEBSCOPE_BIN:-$HOME/.local/bin}"
SRC="https://raw.githubusercontent.com/${REPO}/${REF}/projects/webscope/webscope.py"
DEST="${BIN_DIR}/webscope"

command -v python3 >/dev/null 2>&1 || { echo "error: python3 is required" >&2; exit 1; }

mkdir -p "$BIN_DIR"
echo "Downloading webscope ($REF) -> $DEST"
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$SRC" -o "$DEST"
elif command -v wget >/dev/null 2>&1; then
  wget -qO "$DEST" "$SRC"
else
  echo "error: need curl or wget" >&2; exit 1
fi
chmod +x "$DEST"

echo "Installed: $DEST"
if ! command -v webscope >/dev/null 2>&1; then
  echo
  echo "Add this to your shell profile so 'webscope' is on PATH:"
  echo "  export PATH=\"$BIN_DIR:\$PATH\""
fi
echo
echo "Run it:  webscope app.example.com"
