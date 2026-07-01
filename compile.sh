#!/bin/bash
set -e

MAIN="${1:-main.tex}"

echo "Compilo con LuaLaTeX: $MAIN"

if command -v latexmk >/dev/null 2>&1; then
  latexmk -lualatex -interaction=nonstopmode -halt-on-error "$MAIN"
else
  lualatex -interaction=nonstopmode -halt-on-error "$MAIN"
fi
