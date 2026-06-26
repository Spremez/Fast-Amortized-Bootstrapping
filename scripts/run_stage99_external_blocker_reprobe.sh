#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT_DIR="${STAGE99_OUT_DIR:-repro/stage99_external_blocker_reprobe}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
RUN_NATIVE_BENCH="${STAGE99_RUN_NATIVE_BENCH:-0}"

mkdir -p "$OUT_DIR"

write_local_fulltext_search() {
  local csv="$OUT_DIR/local_fulltext_search.csv"
  printf 'source,path,status,sha256,detail\n' > "$csv"

  csv_row() {
    local source="$1"
    local path="$2"
    local status="$3"
    local sha="$4"
    local detail="$5"
    detail="${detail//$'\n'/ }"
    detail="${detail//,/;}"
    printf '%s,%s,%s,%s,%s\n' "$source" "$path" "$status" "$sha" "$detail" >> "$csv"
  }

  if [[ -n "${FAB686_FULLTEXT_PATH:-}" ]]; then
    if [[ -f "$FAB686_FULLTEXT_PATH" ]]; then
      local sha
      sha="$(sha256sum "$FAB686_FULLTEXT_PATH" | awk '{print $1}')"
      csv_row "FAB686_FULLTEXT_PATH" "$FAB686_FULLTEXT_PATH" "FOUND_ENV_FULLTEXT" "$sha" \
        "User-provided full-text artifact exists; run Stage38 for review."
    else
      csv_row "FAB686_FULLTEXT_PATH" "$FAB686_FULLTEXT_PATH" "MISSING_ENV_FULLTEXT" "" \
        "FAB686_FULLTEXT_PATH is set but the file does not exist."
    fi
  else
    csv_row "FAB686_FULLTEXT_PATH" "" "NOT_SET" "" "No user-provided full-text path."
  fi

  local roots=(
    "$ROOT"
    "$ROOT/external"
    "$ROOT/papers"
    "$ROOT/docs"
    "$ROOT/repro"
    "/mnt/c/Users/spremez/Downloads"
    "/mnt/c/Users/spremez/Documents"
  )
  if [[ -n "${STAGE99_LOCAL_FULLTEXT_ROOTS:-}" ]]; then
    mapfile -t roots <<< "$STAGE99_LOCAL_FULLTEXT_ROOTS"
  fi

  local patterns=(
    '*2025*686*.pdf'
    '*Fast*Amortized*Bootstrapping*.pdf'
    '*Small*Keys*Polynomial*Noise*.pdf'
  )

  local found_any=0
  local root
  for root in "${roots[@]}"; do
    if [[ ! -d "$root" ]]; then
      csv_row "local_root" "$root" "ROOT_MISSING" "" "Search root does not exist."
      continue
    fi
    local before_found="$found_any"
    local pattern
    for pattern in "${patterns[@]}"; do
      while IFS= read -r -d '' candidate; do
        found_any=1
        local sha
        sha="$(sha256sum "$candidate" | awk '{print $1}')"
        csv_row "local_find" "$candidate" "FOUND_CANDIDATE" "$sha" \
          "Candidate path matched $pattern; run Stage38 before treating it as reviewed 2025/686 full text."
      done < <(find "$root" -maxdepth 4 -type f -iname "$pattern" -print0 2>/dev/null || true)
    done
    if [[ "$before_found" == "$found_any" ]]; then
      csv_row "local_root" "$root" "NO_MATCH" "" "No configured candidate pattern matched under this root."
    fi
  done
}

{
  echo "Stage99 external blocker reprobe"
  date -u
  git rev-parse --short HEAD

  STAGE28_PERF_GATE_OUT_DIR="$OUT_DIR/native_perf_probe" \
  STAGE28_RUN_BENCH="$RUN_NATIVE_BENCH" \
    bash scripts/run_stage28_native_perf_counter_gate.sh \
    > "$OUT_DIR/native_perf_probe.log" 2>&1 || true

  STAGE27_CITATION_PROBE_OUT_DIR="$OUT_DIR/citation_probe" \
    bash scripts/run_stage27_citation_access_probe.sh \
    > "$OUT_DIR/citation_probe.log" 2>&1 || true

  write_local_fulltext_search

  "$PYTHON_BIN" scripts/build_stage99_external_blocker_reprobe.py --out-dir "$OUT_DIR"
} 2>&1 | tee "$OUT_DIR/stage99_run.log"
