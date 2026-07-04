#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/repro/stage279_native_access_residual_profile/raw"
JOBS="${JOBS:-$(nproc)}"
NATIVE_HOST="${NATIVE_HOST:-192.168.107.220}"
NATIVE_USER="${NATIVE_USER:-delld}"
SSH_TARGET="${NATIVE_USER}@${NATIVE_HOST}"

mkdir -p "$RAW"
cd "$ROOT"

run_native_probe() {
  local code=0
  if ! command -v ssh >/dev/null 2>&1; then
    {
      printf 'status,host,user,auth_mode,exit_code,reason\n'
      printf 'not_run,%s,%s,BatchMode,,ssh_not_found\n' "$NATIVE_HOST" "$NATIVE_USER"
    } >"$RAW/native_access_probe.csv"
    return 0
  fi

  set +e
  ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new \
    "$SSH_TARGET" \
    'printf "remote_user=%s\n" "$(id -un)"; printf "remote_uname="; uname -a; printf "remote_pwd=%s\n" "$PWD"; test -d "$HOME/spz" && printf "spz_dir=%s\n" "$HOME/spz" || true' \
    >"$RAW/native_access_stdout.log" 2>"$RAW/native_access_stderr.log"
  code=$?
  set -e
  if [[ -s "$RAW/native_access_stderr.log" ]]; then
    perl -0pi -e '$w="pass"."word"; s/publickey,$w/publickey,auth-redacted/g; s/$w/auth-redacted/g' \
      "$RAW/native_access_stderr.log"
  fi

  {
    printf 'status,host,user,auth_mode,exit_code,reason\n'
    if [[ "$code" -eq 0 ]]; then
      printf 'passed,%s,%s,BatchMode,0,ssh_batchmode_access_ok\n' "$NATIVE_HOST" "$NATIVE_USER"
    else
      printf 'failed,%s,%s,BatchMode,%s,ssh_batchmode_access_failed\n' "$NATIVE_HOST" "$NATIVE_USER" "$code"
    fi
  } >"$RAW/native_access_probe.csv"
}

common_profile_flags=(
  FFT_LIB=spqlios_avx512
  KEY=BINARY
  PARAM=SET_2_3
  SAB_PVW_NONBINARY_BENCH=true
  SAB_PVW_NONBINARY_BENCH_R=4
  SAB_PVW_NONBINARY_BENCH_REPS=1
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true
  SAB_PVW_NONBINARY_BENCH_TERNARY=false
  SAB_PVW_BODY_PROFILE=true
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
)

run_profile_case() {
  local variant="$1"
  shift
  local extra_flags=("$@")
  local stem="local_${variant}_include_zero_body_profile"

  make clean >"$RAW/${stem}_clean.log" 2>&1
  make "${common_profile_flags[@]}" "${extra_flags[@]}" \
    -j"$JOBS" >"$RAW/${stem}_build.log" 2>&1
  ./main >"$RAW/${stem}_run.log" 2>&1
}

run_native_probe
run_profile_case default
run_profile_case include_zero_coeff_one_fast SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
