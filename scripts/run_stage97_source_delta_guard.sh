#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT_DIR="${STAGE97_OUT_DIR:-repro/stage97_source_delta_guard}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
mkdir -p "$OUT_DIR"

{
  echo "Stage97 source delta guard"
  date -u
  git rev-parse --short HEAD
  "$PYTHON_BIN" scripts/build_stage97_source_delta_guard.py --out-dir "$OUT_DIR"
} 2>&1 | tee "$OUT_DIR/stage97_run.log"
