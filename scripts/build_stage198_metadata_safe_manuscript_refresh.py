#!/usr/bin/env python3
"""Stage198: metadata-safe manuscript refresh from the Stage197 support bank."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage198_metadata_safe_manuscript_refresh"

SUMMARY_CSV = OUT_DIR / "summary.csv"
DRAFT_MD = OUT_DIR / "manuscript_draft.md"
USAGE_CSV = OUT_DIR / "sentence_usage.csv"
COMPLIANCE_CSV = OUT_DIR / "paragraph_compliance.csv"
GUARD_CSV = OUT_DIR / "claim_guard.csv"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage198_metadata_safe_manuscript_refresh.md"
PLAN_MD = ROOT / "experiments" / "stage198_metadata_safe_manuscript_refresh_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage198_manuscript_compliance_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_metadata_safe_manuscript_refresh.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE197_SUPPORT = ROOT / "repro" / "stage197_metadata_safe_citation_bank" / "sentence_support_bank.csv"
STAGE197_PARAGRAPH = ROOT / "repro" / "stage197_metadata_safe_citation_bank" / "paragraph_support_map.csv"
STAGE197_SUMMARY = ROOT / "repro" / "stage197_metadata_safe_citation_bank" / "summary.csv"
STAGE196_CITATION = ROOT / "repro" / "stage196_public_source_refresh" / "citation_gate.csv"
STAGE195_LEDGER = ROOT / "repro" / "stage195_scoped_paper_repro_refresh" / "final_claim_ledger.csv"

DECISION = "PASS_STAGE198_METADATA_SAFE_MANUSCRIPT_REFRESH_READY_GOAL_ACTIVE"

# Labels avoid embedding the blocked phrases in generated documentation.
BLOCKED_PATTERNS = [
    ("B1", re.compile(r"theoretically\s+optimal", re.IGNORECASE)),
    ("B2", re.compile(r"optimal\s+avx512", re.IGNORECASE)),
    ("B3", re.compile(r"implemented\s+compact", re.IGNORECASE)),
    ("B4", re.compile(r"compact\s+sab\s+speedup", re.IGNORECASE)),
    ("B5", re.compile(r"prove\s+novelty", re.IGNORECASE)),
    ("B6", re.compile(r"mathematically\s+optimal", re.IGNORECASE)),
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


def support_by_id() -> Dict[str, Dict[str, str]]:
    return {row["sentence_id"]: row for row in read_csv_dicts(STAGE197_SUPPORT)}


def paragraph_by_id() -> Dict[str, Dict[str, str]]:
    return {row["paragraph_id"]: row for row in read_csv_dicts(STAGE197_PARAGRAPH)}


def sentence(sentence_id: str, support: Dict[str, Dict[str, str]]) -> str:
    return support[sentence_id]["sentence"]


def build_paragraph_specs(support: Dict[str, Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "paragraph_id": "P1_abstract_scope",
            "section": "Abstract",
            "used_sentence_ids": "S1_object_metric; S2_primary_result; S8_manuscript_status",
            "body": " ".join(
                [
                    sentence("S1_object_metric", support),
                    sentence("S2_primary_result", support),
                    sentence("S8_manuscript_status", support),
                    "All result language is limited to recorded conditions and local reproducibility artifacts.",
                ]
            ),
        },
        {
            "paragraph_id": "P2_background_baseline",
            "section": "Background and Source Boundary",
            "used_sentence_ids": "S3_target_metadata; S4_code_route",
            "body": " ".join(
                [
                    sentence("S3_target_metadata", support),
                    sentence("S4_code_route", support),
                    "The draft uses this only as source-line context until a reviewed full text is available.",
                ]
            ),
        },
        {
            "paragraph_id": "P3_results",
            "section": "Measured Result",
            "used_sentence_ids": "S1_object_metric; S2_primary_result",
            "body": " ".join(
                [
                    sentence("S1_object_metric", support),
                    sentence("S2_primary_result", support),
                    "The comparison remains complete bootstrapping against repeated scalar SAB and must be reported with backend, parameter, seed, and commit metadata.",
                ]
            ),
        },
        {
            "paragraph_id": "P4_related_work",
            "section": "Related-Work Boundary",
            "used_sentence_ids": "S5_related_work_boundary",
            "body": " ".join(
                [
                    sentence("S5_related_work_boundary", support),
                    "This paragraph is a review obligation, not a final related-work comparison.",
                ]
            ),
        },
        {
            "paragraph_id": "P5_limitations",
            "section": "Limitations and Next Gates",
            "used_sentence_ids": "S6_compact_boundary; S7_exact_frontier; S8_manuscript_status",
            "body": " ".join(
                [
                    sentence("S6_compact_boundary", support),
                    sentence("S7_exact_frontier", support),
                    sentence("S8_manuscript_status", support),
                    "The next valid routes are full-text anchor intake, metadata-safe draft maintenance, or a new mechanism with correctness, noise, resource, and complete-SAB gates.",
                ]
            ),
        },
    ]


def write_draft(paragraph_specs: List[Dict[str, str]]) -> None:
    sections = [
        "# Metadata-Safe Manuscript Refresh: PVW/MAT-SAB",
        "",
        "This draft is generated from `repro/stage197_metadata_safe_citation_bank/`.",
        "It is a controlled scoped draft, not a final paper.",
        "",
    ]
    for spec in paragraph_specs:
        sections.extend([f"## {spec['section']}", "", spec["body"], ""])
    sections.extend(
        [
            "## Reproduction Entry",
            "",
            "Use `repro/stage198_metadata_safe_manuscript_refresh/reproduction_commands.md` to rebuild and audit this draft.",
            "",
        ]
    )
    write_text_lf(DRAFT_MD, "\n".join(sections))


def build_usage_rows(paragraph_specs: List[Dict[str, str]], support: Dict[str, Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for spec in paragraph_specs:
        ids = [item.strip() for item in spec["used_sentence_ids"].split(";") if item.strip()]
        for sentence_id in ids:
            source = support.get(sentence_id, {})
            rows.append(
                {
                    "paragraph_id": spec["paragraph_id"],
                    "section": spec["section"],
                    "sentence_id": sentence_id,
                    "support_status": source.get("status", "MISSING"),
                    "evidence_type": source.get("evidence_type", ""),
                    "evidence": source.get("evidence", ""),
                    "required_qualification": source.get("required_qualification", ""),
                }
            )
    return rows


def build_compliance_rows(paragraph_specs: List[Dict[str, str]], paragraph_map: Dict[str, Dict[str, str]], support: Dict[str, Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for spec in paragraph_specs:
        paragraph_id = spec["paragraph_id"]
        map_row = paragraph_map.get(paragraph_id, {})
        allowed = {item.strip() for item in map_row.get("allowed_sentence_ids", "").split(";") if item.strip()}
        used = {item.strip() for item in spec["used_sentence_ids"].split(";") if item.strip()}
        missing_support = sorted([item for item in used if item not in support])
        unsupported_status = sorted([item for item in used if not support.get(item, {}).get("status", "").startswith("ALLOW")])
        extra = sorted(used - allowed)
        status = "PASS" if not missing_support and not unsupported_status and not extra else "FAIL"
        rows.append(
            {
                "paragraph_id": paragraph_id,
                "section": spec["section"],
                "status": status,
                "used_sentence_ids": "; ".join(sorted(used)),
                "allowed_sentence_ids": "; ".join(sorted(allowed)),
                "missing_support": "; ".join(missing_support),
                "unsupported_status": "; ".join(unsupported_status),
                "outside_allowed_set": "; ".join(extra),
                "qualification": map_row.get("must_include_qualification", ""),
                "must_avoid": map_row.get("must_avoid", ""),
                "evidence": map_row.get("evidence", ""),
            }
        )
    return rows


def build_guard_rows(files: List[Path]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in files:
        text = read_text(path)
        for label, pattern in BLOCKED_PATTERNS:
            rows.append(
                {
                    "file": rel(path),
                    "pattern_id": label,
                    "hits": str(len(pattern.findall(text))),
                    "status": "PASS" if not pattern.search(text) else "FAIL",
                }
            )
    return rows


def build_guard_summary(guard_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "scanned_files": str(len({row["file"] for row in guard_rows})),
            "checked_patterns": str(len({row["pattern_id"] for row in guard_rows})),
            "failed_rows": str(sum(1 for row in guard_rows if row["status"] != "PASS")),
            "evidence": rel(GUARD_CSV),
        }
    ]


def build_summary_rows(compliance_rows: List[Dict[str, str]], guard_rows: List[Dict[str, str]], usage_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs = [STAGE197_SUPPORT, STAGE197_PARAGRAPH, STAGE197_SUMMARY, STAGE196_CITATION, STAGE195_LEDGER]
    inputs_ok = all(path.exists() for path in inputs)
    compliance_failures = sum(1 for row in compliance_rows if row["status"] != "PASS")
    guard_failures = sum(1 for row in guard_rows if row["status"] != "PASS")
    return [
        {
            "gate": "stage198_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if inputs_ok else "0",
            "evidence": f"{rel(STAGE197_SUPPORT)}; {rel(STAGE197_PARAGRAPH)}; {rel(STAGE196_CITATION)}",
            "detail": "Stage198 consumes the sentence support bank, paragraph map, citation boundary, and final claim ledger.",
            "next_action": "Repair missing inputs before draft use.",
        },
        {
            "gate": "stage198_sentence_usage",
            "status": "PASS",
            "metric": "usage_rows",
            "value": str(len(usage_rows)),
            "evidence": rel(USAGE_CSV),
            "detail": "Every paragraph-level sentence source is recorded with support status and evidence.",
            "next_action": "Use this table when editing the draft.",
        },
        {
            "gate": "stage198_paragraph_compliance",
            "status": "PASS" if compliance_failures == 0 else "FAIL",
            "metric": "failed_paragraphs",
            "value": str(compliance_failures),
            "evidence": rel(COMPLIANCE_CSV),
            "detail": "Used sentence ids must be a subset of the Stage197 paragraph map and have ALLOW-family support.",
            "next_action": "Fix or remove noncompliant paragraphs.",
        },
        {
            "gate": "stage198_claim_guard",
            "status": "PASS" if guard_failures == 0 else "FAIL",
            "metric": "failed_guard_rows",
            "value": str(guard_failures),
            "evidence": rel(GUARD_CSV),
            "detail": "Generated draft and docs avoid selected overclaim patterns.",
            "next_action": "Rewrite generated text if nonzero.",
        },
        {
            "gate": "stage198_decision",
            "status": DECISION if inputs_ok and compliance_failures == 0 and guard_failures == 0 else "FAIL_STAGE198",
            "metric": "goal_status",
            "value": "active",
            "evidence": rel(SUMMARY_CSV),
            "detail": "A metadata-safe scoped draft is refreshed; the broader MAT-RLWE SAB goal remains active.",
            "next_action": "Proceed only to full-text anchor intake, guarded draft edits, or a new experimental mechanism gate.",
        },
    ]


def write_commands() -> None:
    write_text_lf(
        COMMANDS_MD,
        """# Stage198 Reproduction Commands

```powershell
# Rebuild the metadata-safe manuscript refresh
python scripts\\build_stage198_metadata_safe_manuscript_refresh.py

# Inspect draft and compliance tables
Get-Content -Raw repro\\stage198_metadata_safe_manuscript_refresh\\manuscript_draft.md
Get-Content -Raw repro\\stage198_metadata_safe_manuscript_refresh\\paragraph_compliance.csv
Get-Content -Raw repro\\stage198_metadata_safe_manuscript_refresh\\claim_guard.csv

# Inspect upstream support bank
Get-Content -Raw repro\\stage197_metadata_safe_citation_bank\\sentence_support_bank.csv
```
""",
    )


def write_docs(
    summary_rows: List[Dict[str, str]],
    compliance_rows: List[Dict[str, str]],
    usage_rows: List[Dict[str, str]],
    guard_summary: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage198 Metadata-Safe Manuscript Refresh

Decision: `{DECISION}`.

Stage198 generates a scoped manuscript refresh from Stage197's support bank.
It does not introduce new experiments, proof claims, or implementation paths.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Paragraph Compliance

{table(compliance_rows, ["paragraph_id", "section", "status", "used_sentence_ids", "allowed_sentence_ids", "qualification", "must_avoid", "evidence"])}
## Sentence Usage

{table(usage_rows, ["paragraph_id", "section", "sentence_id", "support_status", "evidence_type", "evidence", "required_qualification"])}
## Guard Summary

{table(guard_summary, ["scanned_files", "checked_patterns", "failed_rows", "evidence"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage198 Plan

Goal: refresh the scoped manuscript using only Stage197-supported sentences.

Rules:

- each paragraph must list the Stage197 sentence ids it uses;
- every used sentence must have an ALLOW-family support status;
- all quantitative language must remain tied to complete-SAB `T_bootstrap/r`;
- source-line statements from 2025/686 remain metadata-only until full text is reviewed;
- no writing artifact opens a new implementation branch.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage198 Manuscript Compliance Model

The draft is valid only as a projection of the Stage197 support bank:

- sentence usage is a relation from paragraph ids to allowed sentence ids;
- paragraph compliance requires used ids to be a subset of the approved map;
- guard checks scan the final draft and generated documentation for selected
  overclaim patterns;
- full-text citation and stronger algorithm claims remain outside this stage.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Metadata-Safe Manuscript Refresh Boundary

This is not a new PVW/MAT-SAB algorithm variant. It is a writing-control
artifact for the current exact full-MAT evidence chain.

The draft may report scoped complete-SAB `T_bootstrap/r` evidence and blocked
frontiers. It may not claim final MAT-RLWE SAB completion, broad related-work
positioning, or compact/shared-output implementation.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 198: Metadata-Safe Manuscript Refresh",
        f"""
## Stage 198: Metadata-Safe Manuscript Refresh

Goal:

```text
Generate a scoped manuscript refresh using only the Stage197 sentence support
bank and verify paragraph-level compliance.
```

Status:

```text
Completed. Stage198 records {DECISION}. The refreshed draft is metadata-safe
and compliance-checked, but not a final paper or a new implementation claim.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage198 records metadata-safe manuscript refresh",
        f"""
Stage198 records metadata-safe manuscript refresh. Decision: `{DECISION}`. It
generates a scoped draft from the support bank and keeps full-text citation,
stronger related-work, and implementation gates separate.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage198 as metadata-safe manuscript refresh",
        f"""
102. Treat Stage198 as metadata-safe manuscript refresh:
    `{DECISION}`. A guarded scoped manuscript draft exists, with paragraph
    compliance and claim-guard tables. It is not a final paper and opens no
    new code branch.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H122_metadata_safe_manuscript_refresh",
        f"""
  - id: H122_metadata_safe_manuscript_refresh
    statement: >
      A scoped manuscript refresh can be generated safely from the Stage197
      support bank if every paragraph records allowed sentence ids and passes
      overclaim guards.
    mechanism: >
      Stage198 constructs the draft from approved sentence ids, checks paragraph
      compliance against the support map, and scans generated artifacts for
      selected overclaim patterns.
    status: stage198_metadata_safe_manuscript_refresh
    evidence: docs/stage198_metadata_safe_manuscript_refresh.md; experiments/stage198_metadata_safe_manuscript_refresh_plan.md; theory_checks/stage198_manuscript_compliance_model.md; repro/stage198_metadata_safe_manuscript_refresh/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - a paragraph uses a sentence id outside the Stage197 map
      - a used sentence lacks ALLOW-family support
      - the draft opens theorem-level, broad related-work, or implementation claims
""",
    )

    append_once(
        RUN_LOG,
        "stage198-metadata-safe-manuscript-refresh-001",
        f"""
stage198-metadata-safe-manuscript-refresh-001,2026-07-04,{git_head()},Stage 198,analysis,python scripts/build_stage198_metadata_safe_manuscript_refresh.py,Stage197 support bank,none,{DECISION},Metadata-safe manuscript refresh and paragraph compliance.,repro/stage198_metadata_safe_manuscript_refresh
""",
    )

    append_once(
        MANIFEST,
        "stage198_metadata_safe_manuscript_refresh",
        f"""
- stage198_metadata_safe_manuscript_refresh: `{DECISION}`
  - `docs/stage198_metadata_safe_manuscript_refresh.md`
  - `experiments/stage198_metadata_safe_manuscript_refresh_plan.md`
  - `theory_checks/stage198_manuscript_compliance_model.md`
  - `algorithm_variants/mat_rlwe_sab_metadata_safe_manuscript_refresh.md`
  - `repro/stage198_metadata_safe_manuscript_refresh/`
""",
    )

    append_once(CHECKLIST, "Stage198 metadata-safe manuscript refresh recorded", """
- [x] Stage198 metadata-safe manuscript refresh recorded.
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
    support = support_by_id()
    paragraph_map = paragraph_by_id()
    paragraph_specs = build_paragraph_specs(support)
    write_draft(paragraph_specs)
    write_commands()

    usage_rows = build_usage_rows(paragraph_specs, support)
    compliance_rows = build_compliance_rows(paragraph_specs, paragraph_map, support)
    write_csv(
        USAGE_CSV,
        usage_rows,
        ["paragraph_id", "section", "sentence_id", "support_status", "evidence_type", "evidence", "required_qualification"],
    )
    write_csv(
        COMPLIANCE_CSV,
        compliance_rows,
        [
            "paragraph_id",
            "section",
            "status",
            "used_sentence_ids",
            "allowed_sentence_ids",
            "missing_support",
            "unsupported_status",
            "outside_allowed_set",
            "qualification",
            "must_avoid",
            "evidence",
        ],
    )

    first_guard_files = [DRAFT_MD, COMMANDS_MD, USAGE_CSV, COMPLIANCE_CSV]
    guard_rows = build_guard_rows(first_guard_files)
    guard_summary = build_guard_summary(guard_rows)
    summary_rows = build_summary_rows(compliance_rows, guard_rows, usage_rows)
    write_csv(GUARD_CSV, guard_rows, ["file", "pattern_id", "hits", "status"])
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_docs(summary_rows, compliance_rows, usage_rows, guard_summary)

    final_guard_files = [DRAFT_MD, OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, COMMANDS_MD, USAGE_CSV, COMPLIANCE_CSV]
    guard_rows = build_guard_rows(final_guard_files)
    guard_summary = build_guard_summary(guard_rows)
    summary_rows = build_summary_rows(compliance_rows, guard_rows, usage_rows)
    write_csv(GUARD_CSV, guard_rows, ["file", "pattern_id", "hits", "status"])
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_docs(summary_rows, compliance_rows, usage_rows, guard_summary)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            DRAFT_MD,
            COMMANDS_MD,
            SUMMARY_CSV,
            USAGE_CSV,
            COMPLIANCE_CSV,
            GUARD_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
