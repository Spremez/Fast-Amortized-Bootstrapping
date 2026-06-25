#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE27_CITATION_PROBE_OUT_DIR:-repro/stage27_citation_access_probe}"
agent="${STAGE27_CITATION_PROBE_AGENT:-Mozilla/5.0 stage27-citation-gate}"
timeout_s="${STAGE27_CITATION_PROBE_TIMEOUT:-45}"

mkdir -p "$out_dir"
semantic_tmp="$out_dir/.semantic_scholar_fab686.tmp.json"
dblp_tmp="$out_dir/.dblp_fab686_title.tmp.json"
trap 'rm -f "$semantic_tmp" "$dblp_tmp"' EXIT

csv="$out_dir/access_probe.csv"
printf 'id,url,http_code,content_type,size_download,effective_url,status,notes\n' > "$csv"

probe_url() {
  local id="$1"
  local url="$2"
  local notes="$3"
  local meta
  set +e
  meta=$(curl -L --max-time "$timeout_s" -A "$agent" -o /dev/null \
    -w '%{http_code}\t%{content_type}\t%{size_download}\t%{url_effective}' \
    "$url" 2>/dev/null)
  local rc=$?
  set -e
  local http_code content_type size_download effective_url status
  IFS=$'\t' read -r http_code content_type size_download effective_url <<< "$meta"
  if [[ "$rc" -ne 0 ]]; then
    status="CURL_ERROR_${rc}"
  elif [[ "$http_code" == "200" && "$content_type" == application/pdf* ]]; then
    status="PDF_ACCESSIBLE"
  elif [[ "$http_code" == "200" || "$http_code" == "202" ]]; then
    status="METADATA_OR_HTML_ONLY"
  elif [[ "$http_code" == "403" ]]; then
    status="BLOCKED_403"
  else
    status="HTTP_${http_code}"
  fi
  python3 - "$csv" "$id" "$url" "$http_code" "$content_type" "$size_download" "$effective_url" "$status" "$notes" <<'PY'
import csv
import sys

path, *row = sys.argv[1:]
with open(path, "a", newline="", encoding="utf-8") as f:
    csv.writer(f, lineterminator="\n").writerow(row)
PY
}

probe_url "FAB686_EPRINT_HTML" \
  "https://eprint.iacr.org/2025/686" \
  "base FAB ePrint landing page"
probe_url "FAB686_EPRINT_PDF" \
  "https://eprint.iacr.org/2025/686.pdf" \
  "base FAB ePrint PDF candidate"
probe_url "FAB686_ACM_DOI" \
  "https://dl.acm.org/doi/10.1145/3719027.3765181" \
  "ACM DOI landing page"
probe_url "FAB686_ACM_PDF" \
  "https://dl.acm.org/doi/pdf/10.1145/3719027.3765181" \
  "ACM PDF candidate"
probe_url "FAB686_SEMANTIC_PAGE" \
  "https://www.semanticscholar.org/paper/ac77b3b95d4d7c2bea17775158435e000f18857e" \
  "Semantic Scholar paper page"
probe_url "FAB686_RESEARCHGATE" \
  "https://www.researchgate.net/publication/397881480_Fast_Amortized_Bootstrapping_with_Small_Keys_and_Polynomial_Noise_Overhead" \
  "ResearchGate publication page"

curl -L --max-time "$timeout_s" -A "$agent" \
  "https://api.semanticscholar.org/graph/v1/paper/DOI:10.1145/3719027.3765181?fields=title,authors,year,venue,externalIds,openAccessPdf,url,abstract" \
  > "$semantic_tmp" 2>/dev/null || true

curl -L --max-time "$timeout_s" -A "$agent" \
  "https://dblp.org/search/publ/api?q=Fast%20Amortized%20Bootstrapping%20with%20Small%20Keys%20and%20Polynomial%20Noise%20Overhead&format=json" \
  > "$dblp_tmp" 2>/dev/null || true

STAGE27_CITATION_PROBE_OUT_DIR="$out_dir" \
STAGE27_SEMANTIC_TMP="$semantic_tmp" \
STAGE27_DBLP_TMP="$dblp_tmp" \
  python3 - <<'PY'
import csv
import json
import os
from pathlib import Path

out_dir = Path(os.environ["STAGE27_CITATION_PROBE_OUT_DIR"])
summary = out_dir / "summary.csv"
access_rows = list(csv.DictReader((out_dir / "access_probe.csv").open(newline="", encoding="utf-8")))

semantic_path = Path(os.environ["STAGE27_SEMANTIC_TMP"])
semantic_status = "UNREAD"
semantic_pdf = ""
semantic_title = ""
if semantic_path.exists() and semantic_path.stat().st_size:
    try:
        data = json.loads(semantic_path.read_text(encoding="utf-8"))
        semantic_title = data.get("title", "")
        semantic_pdf = (data.get("openAccessPdf") or {}).get("url") or ""
        semantic_status = "METADATA_AVAILABLE_NO_OPEN_ACCESS_PDF" if not semantic_pdf else "OPEN_ACCESS_PDF_REPORTED"
    except Exception as exc:
        semantic_status = f"JSON_PARSE_ERROR:{exc}"

dblp_path = Path(os.environ["STAGE27_DBLP_TMP"])
dblp_status = "UNREAD"
dblp_hits = ""
if dblp_path.exists() and dblp_path.stat().st_size:
    try:
        data = json.loads(dblp_path.read_text(encoding="utf-8"))
        hits = data.get("result", {}).get("hits", {}).get("@total", "")
        dblp_hits = str(hits)
        dblp_status = "TITLE_METADATA_AVAILABLE" if hits and hits != "0" else "NO_HITS"
    except Exception as exc:
        dblp_status = f"JSON_PARSE_ERROR:{exc}"

pdf_accessible = any(row["status"] == "PDF_ACCESSIBLE" for row in access_rows)
full_text_gate = "PASS_FULL_TEXT_AVAILABLE" if pdf_accessible else "BLOCKED_FULL_TEXT_NOT_AVAILABLE"

with summary.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(["gate", "status", "detail"])
    writer.writerow(["direct_pdf_access", "PASS" if pdf_accessible else "BLOCKED", full_text_gate])
    writer.writerow(["semantic_scholar_metadata", semantic_status, semantic_title])
    writer.writerow(["semantic_scholar_open_access_pdf_url", "FOUND" if semantic_pdf else "MISSING", semantic_pdf])
    writer.writerow(["dblp_title_metadata", dblp_status, f"hits={dblp_hits}"])
    writer.writerow(["citation_decision", "BLOCK_THEOREM_LEVEL_CITATIONS" if not pdf_accessible else "ALLOW_FULL_TEXT_CITATION_AUDIT", "Do not cite 2025/686 theorem/algorithm/remark numbers without full text."])

print(f"Stage 27 citation access probe: {out_dir / 'access_probe.csv'}")
print(f"Stage 27 citation access summary: {summary}")
PY
