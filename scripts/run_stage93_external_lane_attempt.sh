#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE93_OUT_DIR:-repro/stage93_external_lane_attempt}"
python_bin="${PYTHON_BIN:-python3}"
search_roots="${STAGE93_FULLTEXT_SEARCH_ROOTS:-. /mnt/d/projects}"
max_depth="${STAGE93_SEARCH_MAX_DEPTH:-6}"

mkdir -p "$out_dir"

native_log="$out_dir/native_perf_gate.log"
search_csv="$out_dir/local_fulltext_search.csv"

STAGE28_PERF_GATE_OUT_DIR="$out_dir/native_perf_gate" \
  STAGE28_RUN_BENCH=1 \
  bash scripts/run_stage28_native_perf_counter_gate.sh > "$native_log" 2>&1 || true

printf 'root,path,size_bytes,match_reason\n' > "$search_csv"
for root in $search_roots; do
  if [[ ! -d "$root" ]]; then
    continue
  fi
  while IFS= read -r -d '' path; do
    size="$(wc -c < "$path" | tr -d ' ')"
    base="$(basename "$path")"
    lower="$(printf '%s' "$base" | tr '[:upper:]' '[:lower:]')"
    reason="filename_match"
    case "$lower" in
      *2025*686*|*fast*amortized*bootstrapp*|*small*keys*polynomial*noise*)
        reason="probable_fab686_filename"
        ;;
    esac
    printf '%s,%s,%s,%s\n' "$root" "$path" "$size" "$reason" >> "$search_csv"
  done < <(
    find "$root" -maxdepth "$max_depth" -type f \( \
      -iname '*2025*686*.pdf' -o \
      -iname '*2025*686*.txt' -o \
      -iname '*fast*amortized*bootstrapp*.pdf' -o \
      -iname '*fast*amortized*bootstrapp*.txt' -o \
      -iname '*small*keys*polynomial*noise*.pdf' -o \
      -iname '*small*keys*polynomial*noise*.txt' -o \
      -iname '*amortized*bootstrapp*.pdf' \
    \) -print0 2>/dev/null
  )
done

"$python_bin" scripts/build_stage93_external_lane_attempt.py --out-dir "$out_dir"

printf 'Stage93 external lane attempt summary: %s\n' "$out_dir/summary.csv"
