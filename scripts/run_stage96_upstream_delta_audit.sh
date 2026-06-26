#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT_DIR="${STAGE96_OUT_DIR:-repro/stage96_upstream_delta_audit}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
mkdir -p "$OUT_DIR"

{
  echo "Stage96 upstream delta audit"
  date -u
  git rev-parse --short HEAD
  git remote -v
  git fetch origin
  "$PYTHON_BIN" scripts/build_stage96_upstream_delta_audit.py --out-dir "$OUT_DIR"
} 2>&1 | tee "$OUT_DIR/stage96_run.log"
