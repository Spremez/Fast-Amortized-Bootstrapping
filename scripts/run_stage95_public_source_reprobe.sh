#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE95_OUT_DIR:-repro/stage95_public_source_reprobe}"
python_bin="${PYTHON:-python3}"

if ! command -v "$python_bin" >/dev/null 2>&1; then
  python_bin="python"
fi

"$python_bin" scripts/build_stage72_external_source_refresh.py
"$python_bin" scripts/build_stage95_public_source_reprobe.py --out-dir "$out_dir"
printf 'Stage95 public source reprobe summary: %s\n' "$out_dir/summary.csv"
