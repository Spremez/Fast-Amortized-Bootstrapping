#!/usr/bin/env bash
set -euo pipefail

start_seed="${1:-6862025}"
seed_count="${2:-50}"

if [[ "$seed_count" -le 0 ]]; then
  printf 'seed_count must be positive, got %s\n' "$seed_count" >&2
  exit 1
fi

seeds=()
for ((i = 0; i < seed_count; i++)); do
  seeds+=("$((start_seed + i))")
done

exec bash scripts/run_stage6_seed_sweep.sh "${seeds[@]}"
