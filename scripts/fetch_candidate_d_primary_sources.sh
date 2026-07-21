#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY="${ROOT}/literature/candidate_d_source_registry.json"
OUT_DIR="${ROOT}/references/candidate_d_fulltext"
HASHES="${OUT_DIR}/source_hashes.csv"
HASHES_PART="${HASHES}.part"

if [[ -L "${ROOT}/references" || -L "${OUT_DIR}" ]]; then
  printf 'BLOCK: full-text output directory may not be a symlink\n' >&2
  exit 1
fi
mkdir -p "${OUT_DIR}"
cd "${ROOT}"

if [[ -n "${PYTHON:-}" ]]; then
  python_bin="${PYTHON}"
elif command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
elif command -v python >/dev/null 2>&1; then
  python_bin="python"
else
  printf 'BLOCK: Python 3 is unavailable\n' >&2
  exit 1
fi

for tool in curl sha256sum pdftotext pdfinfo; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    printf 'BLOCK: required tool is unavailable: %s\n' "${tool}" >&2
    exit 1
  fi
done

"${python_bin}" -m research.mat_sab.candidate_d_literature \
  validate-output-root "${ROOT}" "${OUT_DIR}" >/dev/null

mapfile -t sources < <(
  "${python_bin}" -m research.mat_sab.candidate_d_literature \
    fetch-manifest "${REGISTRY}"
)

printf '%s\n' \
  'source_id,download_url,fetch_status,pdf_sha256,pdf_bytes,pdf_pages,pdftotext_status,text_sha256,text_bytes' \
  > "${HASHES_PART}"

is_pdf() {
  local path="$1"
  [[ -f "${path}" ]] && [[ "$(head -c 4 "${path}" || true)" == "%PDF" ]]
}

matches_expected_hash() {
  local path="$1"
  local expected="$2"
  [[ "${expected}" == "-" ]] || \
    [[ "$(sha256sum "${path}" | awk '{print $1}')" == "${expected}" ]]
}

try_local_import() {
  local source_id="$1"
  local expected="$2"
  local destination="$3"
  local candidate=""
  if [[ -n "${CANDIDATE_D_SOURCE_DIR:-}" ]]; then
    candidate="${CANDIDATE_D_SOURCE_DIR}/${source_id}.pdf"
  fi
  if [[ "${source_id}" == "FAB_2025_686" && -n "${FAB686_FULLTEXT_PATH:-}" ]]; then
    candidate="${FAB686_FULLTEXT_PATH}"
  fi
  if [[ "${source_id}" == "NTRU_AMORT_2026_068" && -n "${NTRU_AMORT_FULLTEXT_PATH:-}" ]]; then
    candidate="${NTRU_AMORT_FULLTEXT_PATH}"
  fi
  if [[ -n "${candidate}" ]] && is_pdf "${candidate}" && \
      matches_expected_hash "${candidate}" "${expected}"; then
    cp "${candidate}" "${destination}"
    return 0
  fi
  return 1
}

failures=0
for entry in "${sources[@]}"; do
  IFS=$'\t' read -r source_id primary fallbacks expected_sha expected_text_sha expected_pages <<< "${entry}"
  pdf="${OUT_DIR}/${source_id}.pdf"
  text="${OUT_DIR}/${source_id}.txt"
  pdf_part="${pdf}.part"
  text_part="${text}.part"
  selected_url="CACHE"
  fetch_status="CACHE_VERIFIED"
  for output_path in "${pdf}" "${text}" "${pdf_part}" "${text_part}"; do
    if [[ -L "${output_path}" ]]; then
      printf 'BLOCK: full-text output entry may not be a symlink: %s\n' \
        "${output_path}" >&2
      exit 1
    fi
  done
  rm -f "${pdf_part}" "${text_part}"

  cache_valid=false
  if is_pdf "${pdf}" && matches_expected_hash "${pdf}" "${expected_sha}"; then
    cache_valid=true
  fi

  if [[ "${cache_valid}" != true ]]; then
    acquired=false
    if try_local_import "${source_id}" "${expected_sha}" "${pdf_part}"; then
      selected_url="LOCAL_IMPORT"
      fetch_status="LOCAL_IMPORT_VERIFIED"
      acquired=true
    else
      urls=("${primary}")
      if [[ "${fallbacks}" != "-" ]]; then
        IFS=';' read -r -a fallback_array <<< "${fallbacks}"
        urls+=("${fallback_array[@]}")
      fi
      if [[ "${CANDIDATE_D_OFFLINE:-0}" != "1" ]]; then
        for url in "${urls[@]}"; do
          rm -f "${pdf_part}"
          if curl --fail --location --retry 1 --connect-timeout 20 --max-time 180 \
              --silent --show-error \
              --user-agent 'CandidateD-D1-Primary-Source-Fetch/2.0' \
              --output "${pdf_part}" "${url}" && \
              is_pdf "${pdf_part}" && \
              matches_expected_hash "${pdf_part}" "${expected_sha}"; then
            selected_url="${url}"
            fetch_status="DOWNLOAD_VERIFIED"
            acquired=true
            break
          fi
        done
      fi
    fi
    if [[ "${acquired}" == true ]]; then
      mv -f "${pdf_part}" "${pdf}"
      cache_valid=true
    fi
  fi

  if [[ "${cache_valid}" != true ]]; then
    rm -f "${pdf_part}" "${text_part}"
    printf '%s\n' \
      "${source_id},${primary},DOWNLOAD_OR_HASH_FAILED,,,,NOT_RUN,," \
      >> "${HASHES_PART}"
    failures=$((failures + 1))
    continue
  fi

  pdf_sha256="$(sha256sum "${pdf}" | awk '{print $1}')"
  pdf_bytes="$(wc -c < "${pdf}" | tr -d '[:space:]')"
  pdf_pages="$(
    pdfinfo "${pdf}" 2>/dev/null \
      | awk -F: '/^Pages:/ {gsub(/[[:space:]]/, "", $2); print $2}'
  )"
  if [[ -z "${pdf_pages}" ]]; then
    printf '%s\n' \
      "${source_id},${selected_url},${fetch_status},${pdf_sha256},${pdf_bytes},,PDFINFO_FAILED,," \
      >> "${HASHES_PART}"
    failures=$((failures + 1))
    continue
  fi
  if [[ "${expected_pages}" != "-" && "${pdf_pages}" != "${expected_pages}" ]]; then
    printf '%s\n' \
      "${source_id},${selected_url},${fetch_status},${pdf_sha256},${pdf_bytes},${pdf_pages},PAGE_COUNT_MISMATCH,," \
      >> "${HASHES_PART}"
    failures=$((failures + 1))
    continue
  fi

  text_valid=false
  if [[ -s "${text}" ]] && matches_expected_hash "${text}" "${expected_text_sha}"; then
    text_valid=true
    pdftotext_status="CACHE_VERIFIED"
  elif pdftotext -layout "${pdf}" "${text_part}" >/dev/null 2>&1 && \
      [[ -s "${text_part}" ]] && \
      matches_expected_hash "${text_part}" "${expected_text_sha}"; then
    mv -f "${text_part}" "${text}"
    text_valid=true
    pdftotext_status="PASS"
  fi

  if [[ "${text_valid}" == true ]]; then
    text_sha256="$(sha256sum "${text}" | awk '{print $1}')"
    text_bytes="$(wc -c < "${text}" | tr -d '[:space:]')"
  else
    rm -f "${text_part}"
    text_sha256=""
    text_bytes=""
    pdftotext_status="EXTRACTION_OR_TEXT_HASH_FAILED"
    failures=$((failures + 1))
  fi

  printf '%s\n' \
    "${source_id},${selected_url},${fetch_status},${pdf_sha256},${pdf_bytes},${pdf_pages},${pdftotext_status},${text_sha256},${text_bytes}" \
    >> "${HASHES_PART}"
done

mv -f "${HASHES_PART}" "${HASHES}"
"${python_bin}" scripts/run_candidate_d_d1_literature.py

if (( failures > 0 )); then
  printf 'BLOCK: %d required source acquisition or extraction failure(s)\n' \
    "${failures}" >&2
  exit 1
fi

printf 'PASS: acquired and extracted %d required primary sources\n' \
  "${#sources[@]}"
