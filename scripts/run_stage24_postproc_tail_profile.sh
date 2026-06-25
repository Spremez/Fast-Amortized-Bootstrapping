#!/usr/bin/env bash
set -euo pipefail

r_values="${STAGE24_POSTPROC_R_VALUES:-2 4}"
runs="${STAGE24_POSTPROC_RUNS:-1}"
reps="${SAB_PVW_BENCH_REPS:-1}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
active_buffer="${SAB_PVW_ACTIVE_BUFFER_FUSION:-true}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
threshold_pct="${STAGE24_POSTPROC_TAIL_PROMOTE_THRESHOLD_PCT:-2.0}"
out_dir="${STAGE24_POSTPROC_OUT_DIR:-repro/stage24_postproc_tail_${fft_lib}_runs${runs}}"

if [[ "$runs" -lt 1 || "$reps" -lt 1 ]]; then
  printf 'invalid config runs=%s reps=%s\n' "$runs" "$reps" >&2
  exit 1
fi

mkdir -p "$out_dir"

sample_csv="$out_dir/postproc_samples.csv"
summary_csv="$out_dir/summary.csv"
printf 'r,run,call_index,lanes,bootstrap_wo_extract_us,direct_extract_us,packing_ks_us,hw_ks_us,tail_us,full_us,body_pct,direct_pct,packing_pct,hwks_pct,tail_pct,source_log\n' > "$sample_csv"
printf 'r,run,status,pvw_avg_us,scalar_repeated_avg_us,speedup,profile_samples,mean_tail_pct,max_tail_pct,threshold_pct,decision,source_log\n' > "$summary_csv"

extract_field() {
  local line="$1"
  local name="$2"
  printf '%s\n' "$line" | tr ' ' '\n' |
    awk -F= -v name="$name" '$1 == name {print $2; exit}' | sed 's/x$//'
}

for r in $r_values; do
  r_out="$out_dir/r${r}"
  mkdir -p "$r_out"

  make clean
  make FFT_LIB="$fft_lib" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED="$mat_specialized" \
    SAB_PVW_ACTIVE_BUFFER_FUSION="$active_buffer" \
    SAB_PVW_BENCH=true SAB_PVW_POSTPROC_PROFILE=true \
    SAB_PVW_BENCH_R="$r" SAB_PVW_BENCH_REPS="$reps" \
    KEY="$key" PARAM="$param" -j"$jobs"

  for run_idx in $(seq 0 "$((runs - 1))"); do
    log_file="$r_out/run_${run_idx}.log"
    stdbuf -o0 ./main | tee "$log_file"

    correctness_line="$(grep 'SAB_PVW_BENCH correctness target_full' "$log_file" | tail -n 1)"
    summary_line="$(grep 'SAB_PVW_BENCH summary target_full' "$log_file" | tail -n 1)"
    if [[ -z "$correctness_line" || -z "$summary_line" ]]; then
      printf 'missing benchmark lines in %s\n' "$log_file" >&2
      exit 1
    fi

    status="$(printf '%s\n' "$correctness_line" | awk '{print $NF}')"
    if [[ "$status" != "Pass" ]]; then
      printf 'correctness gate failed in %s: %s\n' "$log_file" "$correctness_line" >&2
      exit 1
    fi

    profile_count="$(grep -c 'SAB_PVW_POSTPROC_PROFILE sample' "$log_file" || true)"
    if [[ "$profile_count" -eq 0 ]]; then
      printf 'missing postproc profile lines in %s\n' "$log_file" >&2
      exit 1
    fi

    metrics="$(
      grep 'SAB_PVW_POSTPROC_PROFILE sample' "$log_file" |
        awk -v r="$r" -v run="$run_idx" -v src="$log_file" \
            -v samples="$sample_csv" -v threshold="$threshold_pct" '
          function pct(part, whole) {
            if (whole == 0) return 0.0;
            return 100.0 * part / whole;
          }
          {
            delete f;
            for (i = 1; i <= NF; i++) {
              split($i, kv, "=");
              if (length(kv[1]) && length(kv[2])) f[kv[1]] = kv[2];
            }
            lanes = f["lanes"] + 0;
            boot = f["bootstrap_wo_extract_us"] + 0;
            direct = f["direct_extract_us"] + 0;
            packing = f["packing_ks_us"] + 0;
            hwks = f["hw_ks_us"] + 0;
            full = f["full_us"] + 0;
            tail = direct + packing + hwks;
            body_pct = pct(boot, full);
            direct_pct = pct(direct, full);
            packing_pct = pct(packing, full);
            hwks_pct = pct(hwks, full);
            tail_pct = pct(tail, full);
            printf "%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%s\n",
              r, run, NR - 1, lanes, boot, direct, packing, hwks, tail,
              full, body_pct, direct_pct, packing_pct, hwks_pct, tail_pct,
              src >> samples;
            sum_tail_pct += tail_pct;
            if (NR == 1 || tail_pct > max_tail_pct) max_tail_pct = tail_pct;
          }
          END {
            mean_tail_pct = sum_tail_pct / NR;
            decision = (max_tail_pct < threshold) ? "DEFER_TAIL_SMALL" : "PROFILE_MATERIAL_REVIEW";
            printf "%d %.6f %.6f %s", NR, mean_tail_pct, max_tail_pct, decision;
          }'
    )"

    read -r samples_seen mean_tail_pct max_tail_pct decision <<< "$metrics"

    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$r" "$run_idx" "$status" \
      "$(extract_field "$summary_line" pvw_avg_us)" \
      "$(extract_field "$summary_line" scalar_repeated_avg_us)" \
      "$(extract_field "$summary_line" speedup_vs_scalar_repeated)" \
      "$samples_seen" "$mean_tail_pct" "$max_tail_pct" "$threshold_pct" \
      "$decision" "$log_file" >> "$summary_csv"
  done
done

printf 'Stage 24 post-processing samples: %s\n' "$sample_csv"
printf 'Stage 24 post-processing summary: %s\n' "$summary_csv"
