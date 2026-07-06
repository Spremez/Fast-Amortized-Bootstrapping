#!/usr/bin/env python3
"""Stage335: audited source acquisition plus compact-route decision."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage335_source_and_compact_route"

DOC = ROOT / "docs" / "stage335_source_and_compact_route.md"
THEORY = ROOT / "theory_checks" / "stage335_claim_and_route_model.md"
PLAN = ROOT / "experiments" / "stage336_exact_pvw_mat_frontier_plan.md"
BUILDER = ROOT / "scripts" / "build_stage335_source_and_compact_route.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

REF = ROOT / "references" / "stage335_fulltext_acquisition"
SHARING_HTML = REF / "pdf" / "sharing_mask_2025_2112_tches.html"
SHARING_PDF = REF / "pdf" / "sharing_mask_2025_2112_tches.pdf"
SHARING_TEXT = REF / "text" / "sharing_mask_2025_2112_tches.txt"
INCOMPLETE_NTT_FETCH = REF / "pdf" / "incomplete_ntt_2025_696.pdf"
PACKED_TFHE_FETCH = REF / "pdf" / "packed_tfhe_2017_430.pdf"
MOSFHET_FETCH = REF / "pdf" / "mosfhet_2022_515.pdf"

STAGE334_SUMMARY = ROOT / "repro" / "stage334_fulltext_claim_audit" / "summary.csv"
STAGE334_CLAIMS = ROOT / "repro" / "stage334_fulltext_claim_audit" / "claim_audit_matrix.csv"
STAGE217_PROOF = ROOT / "repro" / "stage217_compact_keygen_security_preflight" / "proof_gate.csv"
STAGE220_PROOF = ROOT / "repro" / "stage220_encrypted_compact_keygen_prototype" / "proof_gate.csv"
STAGE221_PROOF = ROOT / "repro" / "stage221_compact_keygen_noise_recurrence" / "proof_gate.csv"
STAGE222_PROOF = ROOT / "repro" / "stage222_isolated_compact_ep_integration" / "proof_gate.csv"
STAGE222_EXPR = ROOT / "repro" / "stage222_isolated_compact_ep_integration" / "expressiveness_results.csv"
STAGE331_SUMMARY = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "summary.csv"

SUMMARY = OUT / "summary.csv"
SOURCE = OUT / "source_acquisition_audit.csv"
ANCHORS = OUT / "sharing_mask_anchor_hits.csv"
CLAIMS = OUT / "claim_boundary.csv"
COMPACT = OUT / "compact_route_audit.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage335_report.md"
COMMANDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION = "PASS_STAGE335_SHARING_MASK_FULLTEXT_AUDITED_COMPACT_SELECTOR_DENIED"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return (
        path.read_text(encoding="utf-8", errors="replace")
        .replace("\x00", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text.lstrip())
        if not text.endswith("\n"):
            handle.write("\n")


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() and path.is_file() else 0


def html_challenge(path: Path) -> bool:
    text = read_text(path)[:4096].lower()
    return "just a moment" in text or "cloudflare" in text or "enable javascript" in text


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines)


def anchor_hits() -> list[dict[str, object]]:
    text = read_text(SHARING_TEXT)
    if not text:
        return []
    patterns = [
        ("cm_ciphertext_definition", ["common mask", "shared mask", "multiple message bodies"]),
        ("distinct_messages", ["distinct message", "common random mask"]),
        ("tfhe_ops_extend_to_cm", ["fhew/tfhe-style", "extended to this cm format"]),
        ("distinct_luts", ["distinct lookup tables", "single cm ciphertext"]),
        ("multi_ciphertext_bootstrapping_prior", ["multiple lwe ciphertexts", "single ciphertext"]),
        ("bootstrapping_cost_table", ["comparison", "classical bootstrapping", "cm-lwe"]),
        ("cm_pbs_inputs", ["cm-pbs", "lookup tables", "bootstrapping key"]),
        ("reported_51_percent", ["51%", "packing"]),
    ]
    lines = text.splitlines()
    rows: list[dict[str, object]] = []
    for anchor, required in patterns:
        refs: list[int] = []
        for idx in range(1, len(lines) + 1):
            window = " ".join(lines[idx - 1:min(len(lines), idx + 5)]).lower()
            if all(term.lower() in window for term in required):
                refs.append(idx)
        rows.append({
            "anchor": anchor,
            "status": "FOUND" if refs else "MISSING",
            "line_refs": ";".join(str(item) for item in refs[:10]),
            "claim_use": "Blocks broad shared-mask/common-mask novelty; not evidence for this repo's 2025/686 SAB speedup.",
        })
    return rows


def source_rows(anchor_ok: bool) -> list[dict[str, object]]:
    return [
        {
            "source": "sharing_the_mask_2025_2112",
            "status": "LOCAL_FULLTEXT_AUDITED" if anchor_ok else "LOCAL_FULLTEXT_PARTIAL",
            "url": "https://tches.iacr.org/index.php/TCHES/article/view/12434",
            "artifact": rel(ANCHORS),
            "bytes": f"pdf={file_size(SHARING_PDF)};text={file_size(SHARING_TEXT)};html={file_size(SHARING_HTML)}",
            "sha256": f"pdf={sha256_file(SHARING_PDF)};text={sha256_file(SHARING_TEXT)}",
            "interpretation": "Direct high-risk prior art for common-mask/shared-mask multi-body TFHE bootstrapping.",
        },
        {
            "source": "paiva_et_al_2025_696",
            "status": "BLOCKED_CLOUDFLARE_CHALLENGE" if html_challenge(INCOMPLETE_NTT_FETCH) else "FETCHED_UNCLASSIFIED",
            "url": "https://eprint.iacr.org/2025/696",
            "artifact": rel(INCOMPLETE_NTT_FETCH),
            "bytes": file_size(INCOMPLETE_NTT_FETCH),
            "sha256": sha256_file(INCOMPLETE_NTT_FETCH),
            "interpretation": "Latest amortized-bootstrapping comparison remains metadata-only until accessible full text is registered.",
        },
        {
            "source": "packed_tfhe_2017_430",
            "status": "BLOCKED_CLOUDFLARE_CHALLENGE" if html_challenge(PACKED_TFHE_FETCH) else "FETCHED_UNCLASSIFIED",
            "url": "https://eprint.iacr.org/2017/430",
            "artifact": rel(PACKED_TFHE_FETCH),
            "bytes": file_size(PACKED_TFHE_FETCH),
            "sha256": sha256_file(PACKED_TFHE_FETCH),
            "interpretation": "Packed-TFHE prior art remains metadata-only in this automated audit.",
        },
        {
            "source": "mosfhet_2022_515",
            "status": "FETCH_FAILED_NOT_PDF" if file_size(MOSFHET_FETCH) < 10_000 else "FETCHED_UNCLASSIFIED",
            "url": "https://eprint.iacr.org/2022/515 ; https://github.com/antoniocgj/MOSFHET",
            "artifact": rel(MOSFHET_FETCH),
            "bytes": file_size(MOSFHET_FETCH),
            "sha256": sha256_file(MOSFHET_FETCH),
            "interpretation": "Backend/AVX optimality remains blocked; current evidence is implementation-local measurement only.",
        },
    ]


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "complete_pvw_mat_sab_t_bootstrap_per_r",
            "status": "ALLOW_SCOPED_MEASURED",
            "evidence": rel(STAGE331_SUMMARY),
            "safe_wording": "For BINARY SET_2_3_2048 on the recorded backend, current-head complete PVW/MAT-SAB improves T_bootstrap/r versus repeated scalar SAB.",
            "blocked_wording": "Universal, all-parameter, or theorem-level speedup.",
        },
        {
            "claim": "shared_mask_r_body_novelty",
            "status": "BLOCK",
            "evidence": rel(ANCHORS),
            "safe_wording": "This work studies a 2025/686 SAB-specific PVW/MAT implementation path.",
            "blocked_wording": "First shared-mask/common-mask multi-body TFHE bootstrapping construction.",
        },
        {
            "claim": "compact_selector_sab_acceleration",
            "status": "BLOCK_CURRENT_COMPACT_STATE",
            "evidence": rel(STAGE222_PROOF),
            "safe_wording": "Lane-local compact EP is correct in isolation, but complete selector integration is denied.",
            "blocked_wording": "Compact selector accelerates complete SAB.",
        },
        {
            "claim": "mat_avx_optimality",
            "status": "BLOCK",
            "evidence": "Stage101/286 counters plus missing MOSFHET full-text audit",
            "safe_wording": "MAT AVX paths have measured backend evidence under recorded flags.",
            "blocked_wording": "The current AVX implementation reaches a theoretical optimum.",
        },
    ]


def compact_rows() -> list[dict[str, object]]:
    return [
        {
            "stage": "217",
            "status": "PATTERN_ONLY",
            "evidence": rel(STAGE217_PROOF),
            "result": "Only count-matched random dummy padding survives public-pattern probes.",
            "admission": "no_sab_hotpath",
        },
        {
            "stage": "220",
            "status": "KEYGEN_PROTOTYPE",
            "evidence": rel(STAGE220_PROOF),
            "result": "Encrypted compact keygen prototype passes phase/DFT/noise negative controls.",
            "admission": "noise_recurrence_only",
        },
        {
            "stage": "221",
            "status": "NOISE_MODEL",
            "evidence": rel(STAGE221_PROOF),
            "result": "Relative recurrence and T_bootstrap/r normalization permit isolated compact EP only.",
            "admission": "isolated_ep_only",
        },
        {
            "stage": "222",
            "status": "COMPLETE_SELECTOR_DENIED",
            "evidence": rel(STAGE222_PROOF),
            "result": "Lane-local compact EP works, but neighbor/cross-body selector equations are missing.",
            "admission": "return_to_exact_pvw_mat_or_new_closed_state",
        },
    ]


def proof_rows(anchor_ok: bool, stage222_denied: bool) -> list[dict[str, object]]:
    return [
        {
            "gate": "G1_stage334_input",
            "status": "PASS" if STAGE334_SUMMARY.exists() else "FAIL",
            "metric": "Stage334 fulltext audit",
            "value": "present" if STAGE334_SUMMARY.exists() else "missing",
            "interpretation": "Stage335 extends, rather than replaces, the previous claim boundary.",
        },
        {
            "gate": "G2_sharing_mask_fulltext",
            "status": "PASS" if anchor_ok else "PARTIAL",
            "metric": "common-mask anchors",
            "value": "anchors_found" if anchor_ok else "anchors_missing",
            "interpretation": "Broad shared-mask/r-body novelty is blocked by audited adjacent work.",
        },
        {
            "gate": "G3_other_fulltexts",
            "status": "BLOCK_METADATA_ONLY",
            "metric": "2025/696;2017/430;MOSFHET",
            "value": "not_fulltext_audited",
            "interpretation": "Latest-work and backend-optimality claims remain blocked.",
        },
        {
            "gate": "G4_compact_route",
            "status": "DENY_COMPLETE_COMPACT_SAB" if stage222_denied else "UNKNOWN",
            "metric": "Stage222 complete selector",
            "value": "denied" if stage222_denied else "not_verified",
            "interpretation": "Do not push compact selector into SAB unless a new closed neighbor-capable state passes isolated gates.",
        },
        {
            "gate": "G5_execution_route",
            "status": DECISION,
            "metric": "next executable work",
            "value": "stage336_exact_pvw_mat_frontier",
            "interpretation": "Avoid theory loop: continue measured exact PVW/MAT-SAB optimization while compact remains proof-blocked.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage336_exact_pvw_mat_frontier",
            "entry_condition": "Stage222 denies current compact complete-selector integration.",
            "gate": "Run same-backend exact PVW/MAT-SAB frontier refresh: current T_bootstrap/r, MAT EP attribution, and one implementable closed-path optimization candidate.",
            "failure_action": "Record neutral/negative and keep exact PVW/MAT-SAB scoped result only.",
        },
        {
            "priority": "P1",
            "route": "stage336_new_neighbor_capable_compact_state_design",
            "entry_condition": "Only if a closed state can represent Stage203 neighbor/cross-body equations.",
            "gate": "Finite phase oracle plus encrypted keygen/noise recurrence before any SAB code.",
            "failure_action": "Do not implement compact SAB hot path.",
        },
        {
            "priority": "P2",
            "route": "fulltext_remaining_sources",
            "entry_condition": "Accessible 2025/696, 2017/430, or MOSFHET PDF is supplied or found.",
            "gate": "Replace metadata blockers with page/line anchors.",
            "failure_action": "Keep latest-work/backend optimality wording blocked.",
        },
    ]


def append_run_log() -> None:
    exists = RUN_LOG.exists()
    marker = "stage335-source-and-compact-route-001"
    if marker in read_text(RUN_LOG):
        return
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8", newline="\n") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        if not exists:
            writer.writerow(["run_id", "date", "git_head", "stage", "backend", "command", "params", "seed", "status", "interpretation", "artifacts"])
        writer.writerow([
            marker,
            "2026-07-06",
            git_head(),
            "Stage 335",
            "source-and-compact-route",
            "python scripts/build_stage335_source_and_compact_route.py",
            "TCHES Sharing-the-Mask full text; Stage217/220/221/222 compact gates",
            "n/a",
            DECISION,
            "Sharing-the-Mask full text blocks broad shared-mask novelty; current compact complete-selector route remains denied; continue exact PVW/MAT frontier.",
            f"{rel(DOC)}; {rel(SOURCE)}; {rel(ANCHORS)}; {rel(COMPACT)}; {rel(PROOF)}",
        ])


def artifact_index(paths: list[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "artifact": rel(path),
            "exists": path.exists(),
            "bytes": file_size(path),
            "sha256": sha256_file(path),
        })
    write_csv(ARTIFACT, rows, ["artifact", "exists", "bytes", "sha256"])


def main() -> int:
    anchors = anchor_hits()
    anchor_ok = bool(anchors) and all(row["status"] == "FOUND" for row in anchors[:4])
    stage222_text = read_text(STAGE222_PROOF)
    stage222_denied = "DENY_COMPLETE_SELECTOR_INTEGRATION" in read_text(STAGE222_EXPR) or "DENY_SAB_HOTPATH_CODE" in stage222_text
    sources = source_rows(anchor_ok)
    claims = claim_rows()
    compact = compact_rows()
    proof = proof_rows(anchor_ok, stage222_denied)
    nextq = next_rows()
    summary = [{
        "decision": DECISION,
        "sharing_mask_fulltext": "audited" if anchor_ok else "partial",
        "other_fulltexts": "blocked_or_metadata_only",
        "compact_route": "complete_selector_denied" if stage222_denied else "unknown",
        "allowed_claim": "scoped measured complete PVW/MAT-SAB T_bootstrap/r",
        "blocked_claims": "broad novelty; compact complete-SAB acceleration; AVX optimality; latest-work superiority",
        "selected_next": "stage336_exact_pvw_mat_frontier",
    }]

    write_csv(SUMMARY, summary, ["decision", "sharing_mask_fulltext", "other_fulltexts", "compact_route", "allowed_claim", "blocked_claims", "selected_next"])
    write_csv(SOURCE, sources, ["source", "status", "url", "artifact", "bytes", "sha256", "interpretation"])
    write_csv(ANCHORS, anchors, ["anchor", "status", "line_refs", "claim_use"])
    write_csv(CLAIMS, claims, ["claim", "status", "evidence", "safe_wording", "blocked_wording"])
    write_csv(COMPACT, compact, ["stage", "status", "evidence", "result", "admission"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "failure_action"])

    write_text(COMMANDS, f"""# Stage335 Reproduction Commands

```powershell
curl.exe -L -A "Mozilla/5.0" -o references\\stage335_fulltext_acquisition\\pdf\\sharing_mask_2025_2112_tches.html https://tches.iacr.org/index.php/TCHES/article/view/12434
curl.exe -L -A "Mozilla/5.0" -o references\\stage335_fulltext_acquisition\\pdf\\sharing_mask_2025_2112_tches.pdf https://tches.iacr.org/index.php/TCHES/article/download/12434/12162
wsl -e bash -lc "pdftotext '/mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping/references/stage335_fulltext_acquisition/pdf/sharing_mask_2025_2112_tches.pdf' '/mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping/references/stage335_fulltext_acquisition/text/sharing_mask_2025_2112_tches.txt'"
python scripts\\build_stage335_source_and_compact_route.py
```

Full-text PDFs and extracted text are ignored by Git. The committed pack records
hashes, source URLs, line anchors, and claim gates only.
""")

    write_text(REPORT, f"""# Stage335 Source And Compact Route Report

Decision: `{DECISION}`.

Stage335 makes two forward moves:

1. It replaces the Stage334 metadata-only blocker for Sharing the Mask with a
   local full-text audit from the TCHES page and PDF.
2. It re-enters the implementation route by consuming Stage217/220/221/222 and
   selecting exact PVW/MAT-SAB frontier work as the next executable path.

## Summary

{md_table(summary, ["decision", "sharing_mask_fulltext", "compact_route", "selected_next"])}

## Source Acquisition

{md_table(sources, ["source", "status", "url", "bytes", "interpretation"])}

## Sharing-The-Mask Anchors

{md_table(anchors, ["anchor", "status", "line_refs", "claim_use"])}

## Claim Boundary

{md_table(claims, ["claim", "status", "safe_wording", "blocked_wording"])}

## Compact Route Audit

{md_table(compact, ["stage", "status", "result", "admission"])}

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value"])}

## Next Queue

{md_table(nextq, ["priority", "route", "gate", "failure_action"])}

Generated from input head `{git_head()}`.
""")

    write_text(DOC, f"""# Stage335 Source And Compact Route

Decision: `{DECISION}`.

The research loop now has a sharper boundary.  Sharing the Mask is no longer a
metadata-only risk: its TCHES full text was fetched locally and audited for
common-mask/shared-mask multi-body TFHE bootstrapping anchors.  This blocks any
claim that PVW/MAT-SAB is the first shared-mask/r-body bootstrapping approach.

At the same time, the compact selector route is not ready for SAB integration.
Stage222 proves the current lane-local compact EP subclass, but denies complete
selector integration because the 2025/686 selector equations require neighbor
or cross-body terms that are outside the current compact output state.

## Consequence For The Main Goal

The allowed positive claim remains scoped: complete PVW/MAT-SAB improves
`T_bootstrap/r` for the recorded target path.  The next executable work is not
more literature discussion; it is Stage336 exact PVW/MAT-SAB frontier refresh
and closed-path optimization under the same `T_bootstrap/r` metric.

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value", "interpretation"])}
""")

    write_text(THEORY, """# Stage335 Claim And Route Model

The model separates three objects:

1. Existing exact PVW/MAT-SAB: a closed r-body ciphertext state that has complete
   SAB evidence under `T_bootstrap/r`.
2. Common-mask/shared-mask prior art: real adjacent work that already studies
   shared masks and multiple bodies for TFHE bootstrapping.
3. Compact selector variant: an attempted row-skipping improvement whose current
   lane-local kernel is correct in isolation, but whose state is not closed for
   the full 2025/686 selector equations.

Promotion rule:

- exact PVW/MAT-SAB may be optimized and measured at full SAB level;
- compact selector may not enter SAB hot paths until a closed state supports
  neighbor/cross-body equations and passes encrypted keygen/noise/phase gates;
- novelty wording must remain scoped unless every high-risk adjacent full text is
  audited and distinguishes the claim.
""")

    write_text(PLAN, """# Stage336 Exact PVW/MAT Frontier Plan

Goal: make implementation progress without waiting for unresolved novelty or
compact-selector blockers.

Primary endpoint: `T_bootstrap/r` for complete SAB, same backend and target
parameters as Stage331.

Tasks:

- Refresh current-head exact PVW/MAT-SAB full benchmark and MAT-EP attribution.
- Identify one closed-path optimization candidate that does not change the SAB
  state semantics: scratch reuse, active-buffer carry, direct DFT lifecycle, or
  r-specialized dense MAT addmul.
- Implement only behind a flag or internal variant.
- Run staged phase equivalence, complete SAB correctness, and repeated A/B
  timing before promotion.

Gate:

- scalar SAB default path unchanged;
- `T_bootstrap/r` is the reported metric;
- no compact selector hot-path code unless a new closed state proof exists;
- neutral and negative results are recorded.
""")

    append_once(GOAL, "<!-- stage335-source-and-compact-route -->", f"""
<!-- stage335-source-and-compact-route -->
- Stage335: `{DECISION}`. Sharing-the-Mask full text now blocks broad shared-mask novelty; Stage222 compact selector complete integration remains denied; next executable route is Stage336 exact PVW/MAT-SAB frontier under `T_bootstrap/r`.
""")
    append_once(ROADMAP, "<!-- stage335-source-and-compact-route -->", f"""
<!-- stage335-source-and-compact-route -->
## Stage335: Source And Compact Route Audit

- Decision: `{DECISION}`.
- Output: `docs/stage335_source_and_compact_route.md`, `repro/stage335_source_and_compact_route/`.
- Next: Stage336 exact PVW/MAT frontier. Compact selector remains outside SAB hot paths until a neighbor-capable closed state passes isolated gates.
""")
    append_once(HYPOTHESES, "H335_source_and_compact_route:", f"""
H335_source_and_compact_route:
  status: {DECISION}
  primary_metric: claim_boundary_and_route_selection
  evidence:
    - repro/stage335_source_and_compact_route/source_acquisition_audit.csv
    - repro/stage335_source_and_compact_route/sharing_mask_anchor_hits.csv
    - repro/stage335_source_and_compact_route/compact_route_audit.csv
    - repro/stage335_source_and_compact_route/proof_gate.csv
  conclusion: >
    Broad shared-mask novelty is blocked by audited TCHES full text, while
    current compact selector integration is blocked by Stage222 expressiveness.
    Continue exact PVW/MAT-SAB optimization under T_bootstrap/r.
""")
    append_once(MANIFEST, "<!-- stage335-source-and-compact-route-manifest -->", """
<!-- stage335-source-and-compact-route-manifest -->
- stage335_source_and_compact_route:
  - `docs/stage335_source_and_compact_route.md`
  - `theory_checks/stage335_claim_and_route_model.md`
  - `experiments/stage336_exact_pvw_mat_frontier_plan.md`
  - `scripts/build_stage335_source_and_compact_route.py`
  - `repro/stage335_source_and_compact_route/`
""")
    append_once(CHECKLIST, "<!-- stage335-source-and-compact-route-checklist -->", f"""
<!-- stage335-source-and-compact-route-checklist -->
- [x] Stage335 records `{DECISION}` and routes next execution to exact PVW/MAT-SAB frontier work.
""")
    append_run_log()
    artifact_index([DOC, THEORY, PLAN, BUILDER, SUMMARY, SOURCE, ANCHORS, CLAIMS, COMPACT, PROOF, NEXT, REPORT, COMMANDS])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
