#!/usr/bin/env bash
set -euo pipefail

python_bin="${PYTHON_BIN:-python3}"

"$python_bin" scripts/build_stage91_final_package.py

printf 'Stage91 final package summary: %s\n' "repro/stage91_final_package/summary.csv"
