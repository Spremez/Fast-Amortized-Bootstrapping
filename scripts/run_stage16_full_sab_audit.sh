#!/usr/bin/env bash
set -euo pipefail

runs="${STAGE16_FULL_SAB_RUNS:-3}"
reps="${STAGE16_FULL_SAB_REPS:-1}"
r_values="${STAGE16_FULL_SAB_R_VALUES:-2 4}"
out_dir="${STAGE16_FULL_SAB_OUT_DIR:-repro/stage16_avx512_full_sab_audit_runs${runs}_reps${reps}}"

if [[ "$runs" -lt 1 || "$reps" -lt 1 ]]; then
  printf 'invalid config runs=%s reps=%s\n' "$runs" "$reps" >&2
  exit 1
fi

mkdir -p "$out_dir"

summary_csv="$out_dir/summary.csv"
printf 'r,runs,reps,status,pvw_mean_us,scalar_repeated_mean_us,speedup_mean,speedup_min,speedup_max,source_summary\n' > "$summary_csv"

for r in $r_values; do
  r_out="$out_dir/r${r}"
  STAGE11_BENCH_OUT_DIR="$r_out" \
  SAB_PVW_BENCH_R="$r" \
  SAB_PVW_BENCH_REPS="$reps" \
  STAGE11_BENCH_RUNS="$runs" \
    bash scripts/run_stage11_avx512_smallr_bench.sh

  r_summary="$r_out/summary.csv"
  if [[ ! -s "$r_summary" ]]; then
    printf 'missing r=%s summary: %s\n' "$r" "$r_summary" >&2
    exit 1
  fi

  awk -F, -v r="$r" -v runs="$runs" -v reps="$reps" -v source="$r_summary" '
    NR == 1 { next }
    {
      if ($2 != "Pass") {
        status = "FAIL"
      }
      count += 1
      pvw += $3
      scalar += $6
      speed += $9
      if (count == 1 || $9 < speed_min) speed_min = $9
      if (count == 1 || $9 > speed_max) speed_max = $9
      if ($9 <= 1.0) nonpositive += 1
    }
    END {
      if (count != runs) {
        printf("unexpected run count for r=%s: got %d expected %d\n", r, count, runs) > "/dev/stderr"
        exit 1
      }
      if (status == "") status = "PASS"
      if (nonpositive > 0) status = "PERF_FAIL"
      printf("%s,%d,%d,%s,%.3f,%.3f,%.6f,%.6f,%.6f,%s\n",
        r, runs, reps, status, pvw / count, scalar / count,
        speed / count, speed_min, speed_max, source)
    }
  ' "$r_summary" >> "$summary_csv"
done

if grep -q ',FAIL,' "$summary_csv" || grep -q ',PERF_FAIL,' "$summary_csv"; then
  printf 'Stage 16 full SAB audit failed: %s\n' "$summary_csv" >&2
  exit 1
fi

printf 'Stage 16 full SAB audit summary: %s\n' "$summary_csv"
