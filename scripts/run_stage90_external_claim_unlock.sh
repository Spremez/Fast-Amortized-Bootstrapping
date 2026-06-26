#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE90_OUT_DIR:-repro/stage90_external_claim_unlock}"
run_native_bench="${STAGE90_RUN_NATIVE_BENCH:-1}"
python_bin="${PYTHON_BIN:-python3}"

mkdir -p "$out_dir"

citation_log="$out_dir/citation_probe.log"
native_log="$out_dir/native_perf_gate.log"
external_log="$out_dir/external_evidence_intake.log"
builder_log="$out_dir/stage90_builder.log"

STAGE27_CITATION_PROBE_OUT_DIR="$out_dir/citation_probe" \
  bash scripts/run_stage27_citation_access_probe.sh > "$citation_log" 2>&1

STAGE28_PERF_GATE_OUT_DIR="$out_dir/native_perf_gate" \
STAGE28_RUN_BENCH="$run_native_bench" \
  bash scripts/run_stage28_native_perf_counter_gate.sh > "$native_log" 2>&1

native_status="$(
  awk -F, '$1 == "hardware_counter_gate" {print $2}' "$out_dir/native_perf_gate/summary.csv" 2>/dev/null || true
)"
native_status="${native_status:-MISSING}"

if [[ "$native_status" == "PASS" ]]; then
  STAGE28_NATIVE_PERF_SUMMARY="$out_dir/native_perf_gate/summary.csv" \
    "$python_bin" scripts/register_external_evidence.py > "$external_log" 2>&1
else
  "$python_bin" scripts/register_external_evidence.py > "$external_log" 2>&1
fi

"$python_bin" scripts/build_stage90_external_claim_unlock.py > "$builder_log" 2>&1

printf 'Stage90 external claim unlock summary: %s\n' "$out_dir/summary.csv"
