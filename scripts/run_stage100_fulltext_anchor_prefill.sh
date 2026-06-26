#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUT_DIR="repro/stage100_fulltext_anchor_prefill"
mkdir -p "$OUT_DIR"

{
  echo "stage=Stage 100"
  echo "script=scripts/run_stage100_fulltext_anchor_prefill.sh"
  echo "pwd=$(pwd)"
  echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  command -v pdftotext || true
  python3 --version || python --version
} > "$OUT_DIR/stage100_run.log" 2>&1

if command -v pdftotext >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
  python3 scripts/build_stage100_fulltext_anchor_prefill.py 2>&1 | tee "$OUT_DIR/stage100_build.log"
elif command -v pdftotext >/dev/null 2>&1 && command -v python >/dev/null 2>&1; then
  python scripts/build_stage100_fulltext_anchor_prefill.py 2>&1 | tee "$OUT_DIR/stage100_build.log"
elif command -v powershell.exe >/dev/null 2>&1 && command -v wslpath >/dev/null 2>&1; then
  WIN_ROOT="$(wslpath -w "$ROOT")"
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
    "Set-Location -LiteralPath '$WIN_ROOT'; python scripts\\build_stage100_fulltext_anchor_prefill.py" \
    2>&1 | tee "$OUT_DIR/stage100_build.log"
else
  echo "Stage100 requires pdftotext plus python, or a WSL powershell.exe fallback." | tee "$OUT_DIR/stage100_build.log"
  exit 1
fi
