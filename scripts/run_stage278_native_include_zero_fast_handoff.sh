#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/repro/stage278_native_larger_stats_include_zero_fast/raw"
NATIVE_HOST="${NATIVE_HOST:-}"
NATIVE_WORKDIR="${NATIVE_WORKDIR:-}"
NATIVE_USER="${NATIVE_USER:-}"
SSH_TARGET="${NATIVE_HOST}"

mkdir -p "$RAW"

if [[ -n "$NATIVE_USER" && -n "$NATIVE_HOST" ]]; then
  SSH_TARGET="${NATIVE_USER}@${NATIVE_HOST}"
fi

if [[ -z "$SSH_TARGET" || -z "$NATIVE_WORKDIR" ]]; then
  {
    printf 'status,reason\n'
    printf 'not_run,missing_NATIVE_HOST_or_NATIVE_WORKDIR\n'
  } >"$RAW/native_handoff_status.csv"
  exit 0
fi

ssh -o BatchMode=yes -o ConnectTimeout=8 "$SSH_TARGET" \
  "cd '$NATIVE_WORKDIR' && bash scripts/run_stage278_include_zero_fast_local_larger_stats.sh" \
  >"$RAW/native_handoff_stdout.log" 2>"$RAW/native_handoff_stderr.log" || {
    code="$?"
    {
      printf 'status,reason,exit_code\n'
      printf 'failed,ssh_or_remote_runner_failed,%s\n' "$code"
    } >"$RAW/native_handoff_status.csv"
    exit 0
  }

{
  printf 'status,reason,exit_code\n'
  printf 'passed,remote_runner_completed,0\n'
} >"$RAW/native_handoff_status.csv"
