#!/usr/bin/env bash
set -euo pipefail

params="${STAGE26_PERF_NOISE_PARAMS:-SET_4_5_2048 SET_2_3_4096}"
r_values="${STAGE26_PERF_NOISE_R_VALUES:-2}"
perf_runs="${STAGE26_PERF_RUNS:-1}"
bench_reps="${SAB_PVW_BENCH_REPS:-1}"
noise_seed_count="${STAGE26_NOISE_SEED_COUNT:-1}"
noise_start_seed="${STAGE26_NOISE_START_SEED:-6863025}"
noise_trials="${SAB_PVW_NOISE_TRIALS:-1}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
active_buffer="${SAB_PVW_ACTIVE_BUFFER_FUSION:-true}"
jobs="${JOBS:-$(nproc)}"
python_bin="${PYTHON:-python3}"
out_dir="${STAGE26_PERF_NOISE_OUT_DIR:-repro/stage26_parameter_perf_noise_${fft_lib}_runs${perf_runs}_seeds${noise_seed_count}}"

if [[ "$perf_runs" -lt 1 || "$bench_reps" -lt 1 ||
      "$noise_seed_count" -lt 1 || "$noise_trials" -lt 1 ]]; then
  printf 'invalid config perf_runs=%s bench_reps=%s noise_seed_count=%s noise_trials=%s\n' \
    "$perf_runs" "$bench_reps" "$noise_seed_count" "$noise_trials" >&2
  exit 1
fi

mkdir -p "$out_dir"

for param in $params; do
  for r in $r_values; do
    perf_dir="$out_dir/perf_${param}_r${r}_runs${perf_runs}"
    KEY=BINARY \
    PARAM="$param" \
    FFT_LIB="$fft_lib" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED="$mat_specialized" \
    SAB_PVW_ACTIVE_BUFFER_FUSION="$active_buffer" \
    STAGE20_ACTIVE_BENCH_RUNS="$perf_runs" \
    SAB_PVW_BENCH_R="$r" \
    SAB_PVW_BENCH_REPS="$bench_reps" \
    STAGE20_ACTIVE_BENCH_OUT_DIR="$perf_dir" \
    JOBS="$jobs" \
      bash scripts/run_stage20_active_buffer_bench.sh

    noise_dir="$out_dir/noise_${param}_r${r}_seeds${noise_seed_count}"
    KEY=BINARY \
    PARAM="$param" \
    FFT_LIB="$fft_lib" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED="$mat_specialized" \
    SAB_PVW_ACTIVE_BUFFER_FUSION="$active_buffer" \
    STAGE25_FINAL_NOISE_R_VALUES="$r" \
    STAGE25_FINAL_NOISE_SEED_COUNT="$noise_seed_count" \
    STAGE25_FINAL_NOISE_START_SEED="$noise_start_seed" \
    SAB_PVW_NOISE_TRIALS="$noise_trials" \
    STAGE25_FINAL_NOISE_OUT_DIR="$noise_dir" \
    JOBS="$jobs" \
      bash scripts/run_stage25_final_noise_sweep.sh
  done
done

STAGE26_PERF_NOISE_OUT_DIR="$out_dir" "$python_bin" - <<'PY'
import csv
import glob
import os
import statistics

out_dir = os.environ["STAGE26_PERF_NOISE_OUT_DIR"]

perf_summary = os.path.join(out_dir, "performance_summary.csv")
with open(perf_summary, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "param", "r", "runs", "status", "pvw_mean_us",
        "scalar_repeated_mean_us", "mean_speedup", "min_speedup",
        "max_speedup", "source_csv", "decision",
    ])
    for path in sorted(glob.glob(os.path.join(out_dir, "perf_*_r*_runs*", "summary.csv"))):
        base = os.path.basename(os.path.dirname(path))
        param_and_r = base[len("perf_"):].rsplit("_runs", 1)[0]
        param, r = param_and_r.rsplit("_r", 1)
        rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
        statuses = sorted({row["status"] for row in rows})
        speeds = [float(row["speedup_vs_scalar_repeated"]) for row in rows]
        pvw = [float(row["pvw_avg_us"]) for row in rows]
        scalar = [float(row["scalar_repeated_avg_us"]) for row in rows]
        status = "PASS" if statuses == ["Pass"] else "+".join(statuses)
        decision = "PASS_SMOKE" if status == "PASS" else "FAIL"
        writer.writerow([
            param, r, len(rows), status,
            f"{statistics.mean(pvw):.3f}",
            f"{statistics.mean(scalar):.3f}",
            f"{statistics.mean(speeds):.3f}",
            f"{min(speeds):.3f}",
            f"{max(speeds):.3f}",
            path.replace("\\", "/"),
            decision,
        ])

noise_summary = os.path.join(out_dir, "noise_summary.csv")
with open(noise_summary, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "param", "r", "seeds", "points", "pvw_failures",
        "scalar_failures", "pair_failures", "min_pvw_minus_scalar_log2",
        "max_pvw_minus_scalar_log2", "avg_pvw_minus_scalar_log2",
        "status", "source_csv",
    ])
    for path in sorted(glob.glob(os.path.join(out_dir, "noise_*_r*_seeds*", "aggregate.csv"))):
        base = os.path.basename(os.path.dirname(path))
        param_and_r = base[len("noise_"):].rsplit("_seeds", 1)[0]
        param, r = param_and_r.rsplit("_r", 1)
        rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
        if len(rows) != 1:
            raise SystemExit(f"expected one aggregate row in {path}, got {len(rows)}")
        row = rows[0]
        writer.writerow([
            param, r, row["seeds"], row["points"],
            row["pvw_failures"], row["scalar_failures"],
            row["pair_failures"], row["min_pvw_minus_scalar_log2"],
            row["max_pvw_minus_scalar_log2"],
            row["avg_pvw_minus_scalar_log2"], row["status"],
            path.replace("\\", "/"),
        ])

print(f"Stage 26 parameter performance summary: {perf_summary}")
print(f"Stage 26 parameter noise summary: {noise_summary}")
PY
