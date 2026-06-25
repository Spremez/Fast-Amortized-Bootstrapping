#!/usr/bin/env bash
set -euo pipefail

r_values="${STAGE17_ATTRIB_R_VALUES:-4}"
reps="${STAGE17_ATTRIB_REPS:-1}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE17_ATTRIB_OUT_DIR:-repro/stage17_perf_attribution}"

mkdir -p "$out_dir"

summary_csv="$out_dir/summary.csv"
printf 'r,status,perf_status,pvw_avg_us,scalar_repeated_avg_us,speedup,run_log,time_log,perf_log,instruction_log\n' > "$summary_csv"

extract_field() {
  local line="$1"
  local name="$2"
  printf '%s\n' "$line" | sed -n "s/.*${name}=\\([^ ]*\\).*/\\1/p" | sed 's/x$//'
}

for r in $r_values; do
  r_out="$out_dir/r${r}"
  mkdir -p "$r_out"

  make clean
  make FFT_LIB="$fft_lib" MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    SAB_PVW_BENCH=true SAB_PVW_BENCH_R="$r" SAB_PVW_BENCH_REPS="$reps" \
    KEY="$key" PARAM="$param" -j"$jobs"

  instruction_log="$r_out/mattrgsw_instruction_snippet.txt"
  {
    printf 'objdump FMA-family snippets for build/mattrgsw.o\n'
    objdump -d build/mattrgsw.o | grep -E 'vfmadd|vfnmadd|vfmsub' | head -n 40 || true
  } > "$instruction_log"

  run_log="$r_out/run.log"
  time_log="$r_out/time.log"
  perf_log="$r_out/perf.log"
  perf_err="$r_out/perf.err"
  perf_status="unavailable"

  if command -v perf >/dev/null 2>&1; then
    set +e
    perf stat -e cycles,instructions,cache-references,cache-misses,branches,branch-misses \
      -o "$perf_log" -- stdbuf -o0 ./main > "$run_log" 2> "$perf_err"
    perf_rc="$?"
    set -e
    if [[ "$perf_rc" -eq 0 ]]; then
      perf_status="pass"
      printf 'perf stat succeeded\n' > "$time_log"
    else
      perf_status="failed_fallback_time"
      /usr/bin/time -v stdbuf -o0 ./main > "$run_log" 2> "$time_log"
    fi
  else
    perf_status="missing_fallback_time"
    printf 'perf not found\n' > "$perf_log"
    /usr/bin/time -v stdbuf -o0 ./main > "$run_log" 2> "$time_log"
  fi

  correctness_line="$(grep 'SAB_PVW_BENCH correctness target_full' "$run_log" | tail -n 1)"
  summary_line="$(grep 'SAB_PVW_BENCH summary target_full' "$run_log" | tail -n 1)"
  if [[ -z "$correctness_line" || -z "$summary_line" ]]; then
    printf 'missing benchmark lines in %s\n' "$run_log" >&2
    exit 1
  fi

  status="$(printf '%s\n' "$correctness_line" | awk '{print $NF}')"
  if [[ "$status" != "Pass" ]]; then
    printf 'correctness gate failed in %s: %s\n' "$run_log" "$correctness_line" >&2
    exit 1
  fi

  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$r" "$status" "$perf_status" \
    "$(extract_field "$summary_line" pvw_avg_us)" \
    "$(extract_field "$summary_line" scalar_repeated_avg_us)" \
    "$(extract_field "$summary_line" speedup_vs_scalar_repeated)" \
    "$run_log" "$time_log" "$perf_log" "$instruction_log" >> "$summary_csv"
done

printf 'Stage 17 attribution summary: %s\n' "$summary_csv"
