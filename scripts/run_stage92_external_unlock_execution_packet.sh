#!/usr/bin/env bash
set -euo pipefail

python_bin="${PYTHON_BIN:-python3}"

"$python_bin" scripts/build_stage92_external_unlock_execution_packet.py

printf 'Stage92 external unlock execution packet summary: %s\n' "repro/stage92_external_unlock_execution/summary.csv"
