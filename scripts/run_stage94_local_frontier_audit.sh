#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE94_OUT_DIR:-repro/stage94_local_frontier_audit}"
python_bin="${PYTHON:-python3}"

if ! command -v "$python_bin" >/dev/null 2>&1; then
  python_bin="python"
fi

"$python_bin" scripts/build_stage94_local_frontier_audit.py --out-dir "$out_dir"
printf 'Stage94 local frontier audit summary: %s\n' "$out_dir/summary.csv"
