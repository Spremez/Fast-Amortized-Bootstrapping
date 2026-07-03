#!/usr/bin/env python3
"""Stage197: metadata-safe citation support bank for PVW/MAT-SAB writing."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage197_metadata_safe_citation_bank"

SUMMARY_CSV = OUT_DIR / "summary.csv"
SUPPORT_CSV = OUT_DIR / "sentence_support_bank.csv"
PARAGRAPH_CSV = OUT_DIR / "paragraph_support_map.csv"
GUARD_CSV = OUT_DIR / "claim_guard.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"
REPORT_MD = OUT_DIR / "metadata_safe_support_report.md"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage197_metadata_safe_citation_bank.md"
PLAN_MD = ROOT / "experiments" / "stage197_metadata_safe_citation_bank_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage197_citation_support_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_metadata_safe_writing_boundary.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE178_PERBIT = ROOT / "repro" / "stage178_fullmat_perbit_frontier" / "per_bit_throughput.csv"
STAGE177_LIT = ROOT / "repro" / "stage177_verified_literature_novelty_gate" / "literature_matrix.csv"
STAGE188_SKEL = ROOT / "repro" / "stage188_scoped_manuscript_skeleton" / "manuscript_skeleton.md"
STAGE188_SUMMARY = ROOT / "repro" / "stage188_scoped_manuscript_skeleton" / "summary.csv"
STAGE192_SUMMARY = ROOT / "repro" / "stage192_compact_admission_route_selection" / "summary.csv"
STAGE193_SUMMARY = ROOT / "repro" / "stage193_exact_addmul_dataflow_preflight" / "summary.csv"
STAGE194_SUMMARY = ROOT / "repro" / "stage194_exact_dft_conversion_preflight" / "summary.csv"
STAGE195_LEDGER = ROOT / "repro" / "stage195_scoped_paper_repro_refresh" / "final_claim_ledger.csv"
STAGE195_REPORT = ROOT / "repro" / "stage195_scoped_paper_repro_refresh" / "scoped_report.md"
STAGE196_SOURCE = ROOT / "repro" / "stage196_public_source_refresh" / "source_probe.csv"
STAGE196_CITATION = ROOT / "repro" / "stage196_public_source_refresh" / "citation_gate.csv"
STAGE196_CLAIM = ROOT / "repro" / "stage196_public_source_refresh" / "claim_policy.csv"

DECISION = "PASS_STAGE197_METADATA_SAFE_CITATION_BANK_READY_GOAL_ACTIVE"

FORBIDDEN_PHRASES = [
    "theoretically optimal",
    "optimal avx512",
    "implemented compact",
    "compact sab speedup",
    "prove novelty",
    "mathematically optimal",
]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv_dicts(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out) + "\n"


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text_lf(path, current + text.lstrip("\n"))


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def metric(metric_name: str) -> str:
    for row in read_csv_dicts(STAGE178_PERBIT):
        if row.get("metric") == metric_name:
            return row.get("value", "")
    return ""


def source_title(source_id: str) -> str:
    for row in read_csv_dicts(STAGE196_SOURCE):
        if row.get("id") == source_id:
            return row.get("title_or_marker", "")
    return ""


def citation_status(gate: str) -> str:
    for row in read_csv_dicts(STAGE196_CITATION):
        if row.get("gate") == gate:
            return row.get("status", "")
    return ""


def build_support_rows() -> List[Dict[str, str]]:
    return [
        {
            "sentence_id": "S1_object_metric",
            "section": "abstract/method",
            "status": "ALLOW",
            "sentence": "We evaluate a PVW/MAT r-body form of the SAB implementation using complete bootstrapping time per processed lane, T_bootstrap/r, as the primary metric.",
            "evidence_type": "local_repro",
            "evidence": f"{rel(STAGE178_PERBIT)}; {rel(STAGE195_LEDGER)}",
            "required_qualification": "Use only for the implemented exact full-MAT path under recorded conditions.",
            "blocked_escalation": "Do not claim final optimality or all-parameter generality.",
        },
        {
            "sentence_id": "S2_primary_result",
            "section": "abstract/results",
            "status": "ALLOW_SCOPED",
            "sentence": f"The current exact full-MAT path records mean {metric('speedup_vs_scalar_repeated_mean')}x speedup, minimum {metric('speedup_vs_scalar_repeated_min')}x, and CI-low {metric('speedup_vs_scalar_repeated_ci95_low')}x on T_bootstrap/r against repeated scalar SAB.",
            "evidence_type": "local_repro",
            "evidence": rel(STAGE178_PERBIT),
            "required_qualification": "Report backend, parameters, seeds, and commit with the result.",
            "blocked_escalation": "Do not replace complete-SAB timing with kernel-only timing.",
        },
        {
            "sentence_id": "S3_target_metadata",
            "section": "background",
            "status": "ALLOW_METADATA_ONLY",
            "sentence": f"Public metadata identifies ePrint 2025/686 as '{source_title('GP2025_686_HTML')}', the target baseline/source line for this implementation study.",
            "evidence_type": "public_metadata",
            "evidence": rel(STAGE196_SOURCE),
            "required_qualification": "Bibliographic/source-existence use only.",
            "blocked_escalation": "Do not cite specific theorem, equation, proof, or experiment details until reviewed full text is supplied.",
        },
        {
            "sentence_id": "S4_code_route",
            "section": "reproducibility",
            "status": "ALLOW_METADATA_ONLY",
            "sentence": "The public code-route probe for the 2025/686 implementation repository is reachable in the Stage196 source refresh.",
            "evidence_type": "public_metadata",
            "evidence": rel(STAGE196_SOURCE),
            "required_qualification": "Use only for code-route visibility and provenance context.",
            "blocked_escalation": "Do not treat repository visibility as proof of paper claims.",
        },
        {
            "sentence_id": "S5_related_work_boundary",
            "section": "related_work",
            "status": "ALLOW_CONSERVATIVE",
            "sentence": "Public metadata for 2025/696 and 2025/2112 creates adjacent related-work obligations, so novelty wording must remain conservative until full-text comparison is complete.",
            "evidence_type": "public_metadata_plus_local_lit_matrix",
            "evidence": f"{rel(STAGE177_LIT)}; {rel(STAGE196_SOURCE)}",
            "required_qualification": "State this as a review obligation, not as a dominance or exact-overlap result.",
            "blocked_escalation": "Do not claim broad novelty or superiority from metadata-only evidence.",
        },
        {
            "sentence_id": "S6_compact_boundary",
            "section": "limitations/future_work",
            "status": "ALLOW_BLOCKED_ROUTE",
            "sentence": "Compact/shared-output MAT-SAB remains a proof-only route with recorded T1/T2/T4 blockers and no complete-SAB implementation claim.",
            "evidence_type": "local_repro",
            "evidence": f"{rel(STAGE192_SUMMARY)}; {rel(STAGE195_LEDGER)}",
            "required_qualification": "Present as blocked future work or negative frontier.",
            "blocked_escalation": "Do not describe compact/shared-output MAT-SAB as an implemented bootstrapping path.",
        },
        {
            "sentence_id": "S7_exact_frontier",
            "section": "limitations/future_work",
            "status": "ALLOW_BLOCKED_ROUTE",
            "sentence": "Current exact addmul and DFT/conversion routes have no promoted local code candidate after Stage193 and Stage194 preflights.",
            "evidence_type": "local_repro",
            "evidence": f"{rel(STAGE193_SUMMARY)}; {rel(STAGE194_SUMMARY)}",
            "required_qualification": "Use to explain why no blind hot-path tuning is opened.",
            "blocked_escalation": "Do not claim a new addmul or DFT/conversion speedup without new measured gates.",
        },
        {
            "sentence_id": "S8_manuscript_status",
            "section": "paper_status",
            "status": "ALLOW_PROCESS",
            "sentence": "The current manuscript artifact is a scoped skeleton and support package, not a final paper.",
            "evidence_type": "local_repro",
            "evidence": f"{rel(STAGE188_SUMMARY)}; {rel(STAGE195_LEDGER)}; {rel(STAGE196_CITATION)}",
            "required_qualification": "Keep final citation verification as an explicit prerequisite.",
            "blocked_escalation": "Do not present the skeleton as submission-ready without reviewed citations.",
        },
    ]


def build_paragraph_rows() -> List[Dict[str, str]]:
    return [
        {
            "paragraph_id": "P1_abstract_scope",
            "target_section": "abstract",
            "allowed_sentence_ids": "S1_object_metric; S2_primary_result; S8_manuscript_status",
            "must_include_qualification": "recorded conditions; complete-SAB T_bootstrap/r; scoped status",
            "must_avoid": "all-parameter generality; final optimality; compact implementation",
            "evidence": f"{rel(SUPPORT_CSV)}; {rel(STAGE195_LEDGER)}",
        },
        {
            "paragraph_id": "P2_background_baseline",
            "target_section": "background",
            "allowed_sentence_ids": "S3_target_metadata; S4_code_route",
            "must_include_qualification": "metadata-only use until full text is reviewed",
            "must_avoid": "specific theorem/equation/proof citation from metadata",
            "evidence": f"{rel(SUPPORT_CSV)}; {rel(STAGE196_CITATION)}",
        },
        {
            "paragraph_id": "P3_results",
            "target_section": "results",
            "allowed_sentence_ids": "S1_object_metric; S2_primary_result",
            "must_include_qualification": "backend/parameters/seeds/commit and scalar repeated baseline",
            "must_avoid": "kernel-only timing as bootstrapping speedup",
            "evidence": f"{rel(SUPPORT_CSV)}; {rel(STAGE178_PERBIT)}",
        },
        {
            "paragraph_id": "P4_related_work",
            "target_section": "related_work",
            "allowed_sentence_ids": "S5_related_work_boundary",
            "must_include_qualification": "metadata shows obligation, not final comparison",
            "must_avoid": "novelty or superiority claim before full-text comparison",
            "evidence": f"{rel(SUPPORT_CSV)}; {rel(STAGE177_LIT)}; {rel(STAGE196_SOURCE)}",
        },
        {
            "paragraph_id": "P5_limitations",
            "target_section": "limitations",
            "allowed_sentence_ids": "S6_compact_boundary; S7_exact_frontier; S8_manuscript_status",
            "must_include_qualification": "blocked or no-promoted-code status",
            "must_avoid": "treating blocked routes as final failures of all possible algorithms",
            "evidence": f"{rel(SUPPORT_CSV)}; {rel(STAGE192_SUMMARY)}; {rel(STAGE193_SUMMARY)}; {rel(STAGE194_SUMMARY)}",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "next_stage": "fulltext_anchor_intake",
            "entry_condition": "A reviewed 2025/686 full text is supplied locally.",
            "gate": "Extract exact theorem, algorithm, parameter, and experiment anchors for every baseline claim.",
            "failure_rule": "If text is unavailable, keep Stage197 support bank metadata-safe only.",
            "evidence": rel(STAGE196_CITATION),
        },
        {
            "priority": "P1",
            "next_stage": "metadata_safe_manuscript_refresh",
            "entry_condition": "Use only Stage197 allowed sentences and existing local performance/noise/resource evidence.",
            "gate": "Generate a revised scoped manuscript draft and scan it against the support bank.",
            "failure_rule": "Any unsupported theorem/novelty/implementation sentence must be removed or downgraded.",
            "evidence": rel(SUPPORT_CSV),
        },
        {
            "priority": "P2",
            "next_stage": "new_mechanism_admission",
            "entry_condition": "A new exact backend mechanism, compact proof evidence, or native/full-text external artifact appears.",
            "gate": "Run hypothesis, correctness, noise/resource, complete-SAB T_bootstrap/r, and claim gates.",
            "failure_rule": "No code branch opens from writing artifacts alone.",
            "evidence": rel(NEXT_CSV),
        },
    ]


def build_guard_rows(files: List[Path]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in files:
        text = read_text(path).lower()
        for phrase in FORBIDDEN_PHRASES:
            rows.append(
                {
                    "file": rel(path),
                    "phrase": phrase,
                    "hits": "1" if phrase in text else "0",
                    "status": "FAIL" if phrase in text else "PASS",
                }
            )
    return rows


def build_summary_rows(guard_rows: List[Dict[str, str]], support_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs = [
        STAGE178_PERBIT,
        STAGE177_LIT,
        STAGE188_SUMMARY,
        STAGE192_SUMMARY,
        STAGE193_SUMMARY,
        STAGE194_SUMMARY,
        STAGE195_LEDGER,
        STAGE196_SOURCE,
        STAGE196_CITATION,
    ]
    inputs_ok = all(path.exists() for path in inputs)
    guard_hits = sum(1 for row in guard_rows if row.get("hits") != "0")
    allowed = sum(1 for row in support_rows if row.get("status", "").startswith("ALLOW"))
    citation_blocked = citation_status("target_686_fulltext_review") == "BLOCKED"
    return [
        {
            "gate": "stage197_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if inputs_ok else "0",
            "evidence": f"{rel(STAGE178_PERBIT)}; {rel(STAGE195_LEDGER)}; {rel(STAGE196_CITATION)}",
            "detail": "Stage197 consumes local performance/claim evidence and public-source citation gates.",
            "next_action": "Repair missing inputs before manuscript use.",
        },
        {
            "gate": "stage197_support_bank",
            "status": "PASS",
            "metric": "allowed_sentence_rows",
            "value": str(allowed),
            "evidence": rel(SUPPORT_CSV),
            "detail": "Every reusable sentence is assigned a status, evidence type, qualification, and blocked escalation.",
            "next_action": "Use only ALLOW rows in scoped writing.",
        },
        {
            "gate": "stage197_claim_guard",
            "status": "PASS" if guard_hits == 0 else "FAIL",
            "metric": "forbidden_hits",
            "value": str(guard_hits),
            "evidence": rel(GUARD_CSV),
            "detail": "Generated support artifacts avoid selected overclaim phrases.",
            "next_action": "Fix generated artifacts if nonzero.",
        },
        {
            "gate": "stage197_fulltext_boundary",
            "status": "BLOCKED" if citation_blocked else "REVIEW_REQUIRED",
            "metric": "target_686_fulltext_gate",
            "value": citation_status("target_686_fulltext_review"),
            "evidence": rel(STAGE196_CITATION),
            "detail": "The support bank remains metadata-safe until reviewed 2025/686 full text is supplied.",
            "next_action": "Ingest full text or keep theorem-level baseline claims out.",
        },
        {
            "gate": "stage197_decision",
            "status": DECISION if guard_hits == 0 and inputs_ok else "FAIL_STAGE197",
            "metric": "goal_status",
            "value": "active",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Writing support is now machine-checkable; the broader MAT-RLWE SAB research objective remains active.",
            "next_action": "Proceed to metadata-safe manuscript refresh or full-text anchor intake.",
        },
    ]


def build_guard_summary_rows(guard_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    files = sorted({row["file"] for row in guard_rows})
    return [
        {
            "scanned_files": str(len(files)),
            "checked_patterns": str(len(FORBIDDEN_PHRASES)),
            "failed_rows": str(sum(1 for row in guard_rows if row.get("status") != "PASS")),
            "evidence": rel(GUARD_CSV),
        }
    ]


def write_report(
    support_rows: List[Dict[str, str]],
    paragraph_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        REPORT_MD,
        f"""# Metadata-Safe Citation Support Bank

Decision: `{DECISION}`.

This support bank converts the current PVW/MAT-SAB evidence into sentence-level
writing rules. It intentionally separates local complete-SAB evidence from
public metadata. Metadata can support source existence and related-work
obligations only; local repro artifacts support the scoped performance result.

## Sentence Support

{table(support_rows, ["sentence_id", "section", "status", "sentence", "evidence_type", "evidence", "required_qualification", "blocked_escalation"])}
## Paragraph Map

{table(paragraph_rows, ["paragraph_id", "target_section", "allowed_sentence_ids", "must_include_qualification", "must_avoid", "evidence"])}
## Next Queue

{table(next_rows, ["priority", "next_stage", "entry_condition", "gate", "failure_rule", "evidence"])}
""",
    )


def write_commands() -> None:
    write_text_lf(
        COMMANDS_MD,
        """# Stage197 Reproduction Commands

```powershell
# Rebuild the support bank
python scripts\\build_stage197_metadata_safe_citation_bank.py

# Inspect sentence-level writing support
Get-Content -Raw repro\\stage197_metadata_safe_citation_bank\\sentence_support_bank.csv

# Inspect paragraph mapping
Get-Content -Raw repro\\stage197_metadata_safe_citation_bank\\paragraph_support_map.csv

# Inspect guard status
Get-Content -Raw repro\\stage197_metadata_safe_citation_bank\\claim_guard.csv

# Inspect upstream source boundary used by this stage
Get-Content -Raw repro\\stage196_public_source_refresh\\citation_gate.csv
```
""",
    )


def write_docs(
    support_rows: List[Dict[str, str]],
    paragraph_rows: List[Dict[str, str]],
    guard_summary_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage197 Metadata-Safe Citation Bank

Decision: `{DECISION}`.

Stage197 turns the Stage195/196 claim boundary into a reusable support bank for
scoped writing. It is not a new algorithm, benchmark, or citation review.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Sentence Support

{table(support_rows, ["sentence_id", "section", "status", "sentence", "evidence_type", "evidence", "required_qualification", "blocked_escalation"])}
## Paragraph Map

{table(paragraph_rows, ["paragraph_id", "target_section", "allowed_sentence_ids", "must_include_qualification", "must_avoid", "evidence"])}
## Claim Guard Summary

{table(guard_summary_rows, ["scanned_files", "checked_patterns", "failed_rows", "evidence"])}
## Next Queue

{table(next_rows, ["priority", "next_stage", "entry_condition", "gate", "failure_rule", "evidence"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage197 Plan

Goal: prevent paper-writing drift after Stage196 by binding every reusable
sentence to evidence and an explicit qualification.

Rules:

- complete-SAB speedup sentences must use local `T_bootstrap/r` artifacts;
- 2025/686 baseline statements are metadata-only until reviewed full text is
  supplied;
- related-work metadata creates comparison obligations, not novelty proof;
- writing artifacts do not open implementation branches.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage197 Citation Support Model

The support model has four levels:

- `ALLOW`: local repro evidence supports the sentence under stated scope.
- `ALLOW_SCOPED`: local repro supports a quantitative statement only with
  backend, parameter, seed, and baseline qualifications.
- `ALLOW_METADATA_ONLY`: public metadata supports bibliographic/source
  existence, not paper-specific theorem or experiment claims.
- `ALLOW_BLOCKED_ROUTE`: local evidence supports a blocked-route statement,
  not an implemented algorithm claim.

The support bank is a guard against overclaiming; it is not evidence for
algorithmic completion.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Metadata-Safe Writing Boundary

This is a writing-control artifact for MAT-RLWE/r-body SAB. It does not define
a new ciphertext format or external-product kernel.

Allowed:

- scoped exact full-MAT `T_bootstrap/r` result;
- metadata-only baseline/source existence;
- explicit limitations and blocked frontiers.

Blocked:

- theorem-level 2025/686 citations without reviewed full text;
- broad novelty or all-parameter claims;
- compact/shared-output implementation claims.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 197: Metadata-Safe Citation Bank",
        f"""
## Stage 197: Metadata-Safe Citation Bank

Goal:

```text
Convert Stage195/196 claim boundaries into sentence-level writing support so
future manuscript work cannot silently upgrade metadata or local kernel evidence.
```

Status:

```text
Completed. Stage197 records {DECISION}. Scoped writing now has a sentence
support bank, paragraph map, guard scan, and next-stage queue; the broader
research goal remains active.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage197 records metadata-safe citation bank",
        f"""
Stage197 records metadata-safe citation bank. Decision: `{DECISION}`. It binds
scoped performance, baseline metadata, related-work obligations, and blocked
frontiers to explicit evidence and qualifications.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage197 as metadata-safe citation bank",
        f"""
101. Treat Stage197 as metadata-safe citation bank:
    `{DECISION}`. Sentence-level writing support is now available, but
    theorem-level citation review, stronger novelty, compact implementation,
    and final optimality remain blocked.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H121_metadata_safe_citation_bank",
        f"""
  - id: H121_metadata_safe_citation_bank
    statement: >
      The current scoped PVW/MAT-SAB result can be written safely only if every
      reusable sentence is bound to local repro evidence or public metadata and
      carries the correct qualification.
    mechanism: >
      Stage197 maps allowed sentences to evidence, paragraphs, blocked
      escalations, and guard scans, preventing metadata-only and kernel-only
      evidence from being used as stronger paper claims.
    status: stage197_metadata_safe_citation_bank
    evidence: docs/stage197_metadata_safe_citation_bank.md; experiments/stage197_metadata_safe_citation_bank_plan.md; theory_checks/stage197_citation_support_model.md; repro/stage197_metadata_safe_citation_bank/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - a reusable sentence lacks evidence or qualification
      - public metadata is used for theorem or experiment details
      - writing artifacts open a code branch without experimental gates
""",
    )

    append_once(
        RUN_LOG,
        "stage197-metadata-safe-citation-bank-001",
        f"""
stage197-metadata-safe-citation-bank-001,2026-07-04,{git_head()},Stage 197,analysis,python scripts/build_stage197_metadata_safe_citation_bank.py,Stage178/188/195/196 evidence,none,{DECISION},Metadata-safe citation support bank and guard scan.,repro/stage197_metadata_safe_citation_bank
""",
    )

    append_once(
        MANIFEST,
        "stage197_metadata_safe_citation_bank",
        f"""
- stage197_metadata_safe_citation_bank: `{DECISION}`
  - `docs/stage197_metadata_safe_citation_bank.md`
  - `experiments/stage197_metadata_safe_citation_bank_plan.md`
  - `theory_checks/stage197_citation_support_model.md`
  - `algorithm_variants/mat_rlwe_sab_metadata_safe_writing_boundary.md`
  - `repro/stage197_metadata_safe_citation_bank/`
""",
    )

    append_once(CHECKLIST, "Stage197 metadata-safe citation bank recorded", """
- [x] Stage197 metadata-safe citation bank recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path),
                "bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    support_rows = build_support_rows()
    paragraph_rows = build_paragraph_rows()
    next_rows = build_next_rows()
    write_report(support_rows, paragraph_rows, next_rows)
    write_commands()
    write_csv(
        SUPPORT_CSV,
        support_rows,
        [
            "sentence_id",
            "section",
            "status",
            "sentence",
            "evidence_type",
            "evidence",
            "required_qualification",
            "blocked_escalation",
        ],
    )
    write_csv(
        PARAGRAPH_CSV,
        paragraph_rows,
        ["paragraph_id", "target_section", "allowed_sentence_ids", "must_include_qualification", "must_avoid", "evidence"],
    )
    write_csv(NEXT_CSV, next_rows, ["priority", "next_stage", "entry_condition", "gate", "failure_rule", "evidence"])
    guard_files = [REPORT_MD, SUPPORT_CSV, PARAGRAPH_CSV, NEXT_CSV, COMMANDS_MD]
    guard_rows = build_guard_rows(guard_files)
    guard_summary_rows = build_guard_summary_rows(guard_rows)
    summary_rows = build_summary_rows(guard_rows, support_rows)

    write_csv(GUARD_CSV, guard_rows, ["file", "phrase", "hits", "status"])
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_docs(support_rows, paragraph_rows, guard_summary_rows, next_rows, summary_rows)

    final_guard_files = [
        REPORT_MD,
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUPPORT_CSV,
        PARAGRAPH_CSV,
        NEXT_CSV,
        COMMANDS_MD,
    ]
    guard_rows = build_guard_rows(final_guard_files)
    guard_summary_rows = build_guard_summary_rows(guard_rows)
    summary_rows = build_summary_rows(guard_rows, support_rows)
    write_csv(GUARD_CSV, guard_rows, ["file", "phrase", "hits", "status"])
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_docs(support_rows, paragraph_rows, guard_summary_rows, next_rows, summary_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            REPORT_MD,
            COMMANDS_MD,
            SUMMARY_CSV,
            SUPPORT_CSV,
            PARAGRAPH_CSV,
            GUARD_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
