#!/usr/bin/env python3
"""Stage204: source-anchor intake for the active PVW/MAT-SAB goal.

This stage records which real public sources can currently support high-level
claims about 2025/686 and which claims still require the full paper text or
line-level source inspection. It deliberately avoids importing large external
HTML/PDF snapshots into the repository.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage204_source_anchor_intake"

SUMMARY_CSV = OUT_DIR / "summary.csv"
SOURCE_CSV = OUT_DIR / "source_access_log.csv"
CLAIM_CSV = OUT_DIR / "source_claim_map.csv"
BOUNDARY_CSV = OUT_DIR / "claim_boundaries.csv"
PROOF_GATE_CSV = OUT_DIR / "proof_gate.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"
REPORT_MD = OUT_DIR / "source_anchor_intake_report.md"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage204_source_anchor_intake.md"
PLAN_MD = ROOT / "experiments" / "stage204_source_anchor_intake_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage204_source_anchor_claim_boundary.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_source_anchor_policy.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE203_SUMMARY = ROOT / "repro" / "stage203_production_selector_equation_probe" / "summary.csv"
STAGE203_PROOF = ROOT / "repro" / "stage203_production_selector_equation_probe" / "proof_gate.csv"

DECISION = "PASS_STAGE204_SOURCE_ANCHOR_INTAKE_METADATA_ONLY"
ACCESS_DATE = date.today().isoformat()


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


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    write_text_lf(path, current.rstrip() + "\n" + text.rstrip() + "\n")


def source_rows() -> List[Dict[str, str]]:
    return [
        {
            "source_id": "S1_eprint_landing",
            "url": "https://eprint.iacr.org/2025/686",
            "kind": "IACR ePrint landing",
            "access_status": "canonical_url_recorded_pdf_automated_fetch_blocked",
            "observed_support": "Confirms the canonical public paper identifier and landing URL when accessed through browser/search metadata.",
            "not_supported": "No local full-text algorithm equations or theorem anchors were extracted.",
            "repo_snapshot": "not_committed_external_snapshot",
            "access_date": ACCESS_DATE,
        },
        {
            "source_id": "S2_github_readme",
            "url": "https://github.com/antoniocgj/Fast-Amortized-Bootstrapping",
            "kind": "author implementation README",
            "access_status": "accessible",
            "observed_support": "Build modes, AVX-512/VAES warning, r7i.metal-24xl paper-result platform, parameter families, and noise-measurement warning.",
            "not_supported": "Does not replace paper theorem proofs or full source-line audit.",
            "repo_snapshot": "not_committed_external_snapshot",
            "access_date": ACCESS_DATE,
        },
        {
            "source_id": "S3_askcrypto_topic",
            "url": "https://askcryp.to/t/resource-topic-2025-686-fast-amortized-bootstrapping-with-small-keys-and-polynomial-noise-overhead/23992",
            "kind": "AskCryptography resource topic",
            "access_status": "accessible_metadata",
            "observed_support": "Title, paper identifier, authors, and abstract-level topic framing.",
            "not_supported": "Does not provide line-level algorithm equations for this repository.",
            "repo_snapshot": "not_committed_external_snapshot",
            "access_date": ACCESS_DATE,
        },
        {
            "source_id": "S4_author_page",
            "url": "https://antonioguimaraes.org/publication/guimaraes-fast-2025/",
            "kind": "author publication page",
            "access_status": "accessible_metadata",
            "observed_support": "Title, abstract-level method summary, CCS 2025 appearance statement, source-reported complexity and benchmark claims.",
            "not_supported": "Not a substitute for full-text proof details or our PVW/MAT-SAB contribution evidence.",
            "repo_snapshot": "not_committed_external_snapshot",
            "access_date": ACCESS_DATE,
        },
    ]


def claim_rows() -> List[Dict[str, str]]:
    return [
        {
            "claim_id": "C1_identity",
            "claim": "2025/686 is titled Fast amortized bootstrapping with small keys and polynomial noise overhead by Antonio Guimaraes and Hilder V. L. Pereira.",
            "support_level": "metadata_supported",
            "sources": "S2_github_readme; S3_askcrypto_topic; S4_author_page",
            "allowed_use": "Paper identity and citation metadata.",
            "not_allowed_use": "No novelty or technical proof conclusion.",
        },
        {
            "claim_id": "C2_publication_status",
            "claim": "The implementation README and author page report the work as preprint/to appear at CCS 2025.",
            "support_level": "metadata_supported",
            "sources": "S2_github_readme; S4_author_page",
            "allowed_use": "Source-reported venue status with date-sensitive wording.",
            "not_allowed_use": "Do not treat as independently verified proceedings metadata without a conference/proceedings source.",
        },
        {
            "claim_id": "C3_source_reported_algorithm_goal",
            "claim": "The source-reported method targets amortized bootstrapping with smaller keys, polynomial noise overhead, and efficient sparse polynomial multiplication.",
            "support_level": "abstract_supported",
            "sources": "S3_askcrypto_topic; S4_author_page",
            "allowed_use": "High-level motivation and bottleneck framing.",
            "not_allowed_use": "Do not use as equation-level SAB call graph or proof of our MAT route.",
        },
        {
            "claim_id": "C4_source_reported_complexity",
            "claim": "The author page reports O(h) homomorphic operations per message and O(sqrt(h lambda) log lambda) noise overhead for the paper method.",
            "support_level": "source_reported_not_reproved",
            "sources": "S4_author_page",
            "allowed_use": "Record as a source-reported baseline claim requiring full-text confirmation before theorem comparison.",
            "not_allowed_use": "Do not combine with our PVW/MAT projection as a proven theorem.",
        },
        {
            "claim_id": "C5_source_reported_benchmarks",
            "claim": "The author page reports 2 to 8-bit bootstrapping in 1.46 ms to 28.5 ms and improvements over TFHE-rs in the paper's setting.",
            "support_level": "source_reported_not_reproduced",
            "sources": "S4_author_page",
            "allowed_use": "External benchmark context only.",
            "not_allowed_use": "Do not compare against our PVW/MAT-SAB numbers without same-platform reproduction.",
        },
        {
            "claim_id": "C6_implementation_platform",
            "claim": "The README reports AVX-512/VAES as the primary fast build path, gives an AVX2/FMA fallback command, and says paper results use AWS r7i.metal-24xl.",
            "support_level": "implementation_metadata_supported",
            "sources": "S2_github_readme",
            "allowed_use": "Backend fairness and hardware reporting requirements.",
            "not_allowed_use": "Do not attribute our speedups to algorithmic changes without same-backend A/B.",
        },
        {
            "claim_id": "C7_parameter_families",
            "claim": "The README lists binary, ternary, and arbitrary-key parameter commands including SET_2_3_2048.",
            "support_level": "implementation_metadata_supported",
            "sources": "S2_github_readme",
            "allowed_use": "Experiment matrix planning.",
            "not_allowed_use": "Does not prove correctness/noise of our modified path.",
        },
        {
            "claim_id": "C8_noise_warning",
            "claim": "The README warns that measuring noise makes performance measurements unreliable and may affect correctness checks.",
            "support_level": "implementation_metadata_supported",
            "sources": "S2_github_readme",
            "allowed_use": "Separate latency runs from noise-instrumented runs.",
            "not_allowed_use": "Do not mix noise instrumentation timings into formal speed claims.",
        },
    ]


def boundary_rows() -> List[Dict[str, str]]:
    return [
        {
            "boundary_id": "B1_pdf_gap",
            "allowed": "Use metadata/abstract/README facts from accessible sources.",
            "blocked": "Full-text theorem, remark, algorithm, and equation references remain blocked until the PDF/full text is supplied or manually accessible.",
            "next_gate": "Acquire reviewed full text and build a page/section anchor table.",
        },
        {
            "boundary_id": "B2_benchmark_gap",
            "allowed": "Use source-reported external benchmarks as context.",
            "blocked": "No paper benchmark value can be merged with our PVW/MAT-SAB result unless same metric, same backend, and same hardware are controlled.",
            "next_gate": "Run same-platform baseline and PVW/MAT-SAB A/B with T_bootstrap/r as primary endpoint.",
        },
        {
            "boundary_id": "B3_algorithm_gap",
            "allowed": "Use sparse polynomial multiplication as the source-reported bottleneck/method axis.",
            "blocked": "No production selector/keygen change follows from metadata-only sources.",
            "next_gate": "Map SAB setup, sparse_mul, CMUX/NCMUX, RGSW monomial, and extract/KS to source anchors.",
        },
        {
            "boundary_id": "B4_novelty_gap",
            "allowed": "Record candidate novelty questions.",
            "blocked": "No novelty claim is allowed without related-work search and full-text comparison.",
            "next_gate": "Build related-work matrix after full text and post-686 works are anchored.",
        },
    ]


def proof_gate_rows() -> List[Dict[str, str]]:
    return [
        {
            "gate": "G1_real_sources",
            "status": "PASS_METADATA",
            "evidence": rel(SOURCE_CSV),
            "detail": "Real public source URLs and accessible metadata are recorded.",
            "remaining_gap": "Full ePrint PDF text was not localized through automated fetch.",
        },
        {
            "gate": "G2_claim_boundaries",
            "status": "PASS_RECORDED",
            "evidence": rel(BOUNDARY_CSV),
            "detail": "Allowed and blocked uses are separated.",
            "remaining_gap": "No theorem/equation-level source anchors.",
        },
        {
            "gate": "G3_experiment_policy",
            "status": "PASS_RECORDED",
            "evidence": rel(CLAIM_CSV),
            "detail": "README hardware/backend/noise warnings are converted into benchmark policy.",
            "remaining_gap": "Same-platform experiment rerun still required.",
        },
        {
            "gate": "G4_production_keygen",
            "status": "BLOCKED",
            "evidence": rel(STAGE203_PROOF),
            "detail": "Stage204 supplies source metadata only, not selector equations or keygen proof.",
            "remaining_gap": "Production keygen/security/noise proof and full SAB A/B.",
        },
    ]


def next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "full_text_anchor_table",
            "entry_condition": "A reviewed local PDF/full text of 2025/686 is available.",
            "gate": "Map algorithm, theorem, remark, and experiment claims to page/section anchors.",
            "current_status": "waiting_full_text",
            "evidence": rel(PROOF_GATE_CSV),
        },
        {
            "priority": "P1",
            "route": "same_platform_benchmark_refresh",
            "entry_condition": "Linux/WSL or native performance platform with spqlios_avx512/AVX path is available.",
            "gate": "Separate scalar SAB, repeated scalar, PVW/MAT-SAB, and noise-instrumented runs under T_bootstrap/r.",
            "current_status": "ready_when_compute_available",
            "evidence": rel(CLAIM_CSV),
        },
        {
            "priority": "P2",
            "route": "production_keygen_design",
            "entry_condition": "Full-text equations and code schedule are aligned.",
            "gate": "Show selector distribution, semantic zero, noise recurrence, key size, and complete-SAB throughput.",
            "current_status": "blocked_on_full_text_and_design",
            "evidence": rel(STAGE203_PROOF),
        },
    ]


def summary_rows() -> List[Dict[str, str]]:
    inputs_present = STAGE203_SUMMARY.exists() and STAGE203_PROOF.exists()
    return [
        {
            "gate": "stage204_inputs",
            "status": "PASS" if inputs_present else "FAIL",
            "metric": "required_stage203_inputs_present",
            "value": "1" if inputs_present else "0",
            "evidence": f"{rel(STAGE203_SUMMARY)}; {rel(STAGE203_PROOF)}",
            "detail": "Stage204 follows Stage203 proof-only selector equation probe.",
            "next_action": "Repair missing Stage203 records before using Stage204.",
        },
        {
            "gate": "stage204_sources",
            "status": "PASS_METADATA",
            "metric": "real_source_rows",
            "value": str(len(source_rows())),
            "evidence": rel(SOURCE_CSV),
            "detail": "Accessible real public sources are recorded without committing external full snapshots.",
            "next_action": "Acquire full PDF for theorem/equation anchors.",
        },
        {
            "gate": "stage204_claim_map",
            "status": "PASS_RECORDED",
            "metric": "claim_rows",
            "value": str(len(claim_rows())),
            "evidence": rel(CLAIM_CSV),
            "detail": "Source-supported metadata, platform, parameter, and warning claims are separated from unproved technical claims.",
            "next_action": "Use same-backend experiments for any speed claim.",
        },
        {
            "gate": "stage204_boundaries",
            "status": "PASS_RECORDED",
            "metric": "blocked_boundaries",
            "value": str(len(boundary_rows())),
            "evidence": rel(BOUNDARY_CSV),
            "detail": "Full-text, benchmark, algorithm, and novelty gaps remain explicit.",
            "next_action": "Proceed to full-text anchors or same-platform benchmarks, not more speculative theory.",
        },
        {
            "gate": "stage204_decision",
            "status": DECISION,
            "metric": "goal_status",
            "value": "active",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Real source intake is sufficient for metadata and experiment-policy grounding only.",
            "next_action": "Continue with concrete full-text or benchmark gates.",
        },
    ]


def artifact_rows(paths: List[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256(path) if path.exists() else "",
                "bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    return rows


def build_report(summary: List[Dict[str, str]], sources: List[Dict[str, str]], claims: List[Dict[str, str]], boundaries: List[Dict[str, str]], gates: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> str:
    return f"""# Stage204 Source Anchor Intake

Decision: `{DECISION}`.

Stage204 converts the source-anchor blocker into a bounded evidence record. It
uses real public source URLs for metadata, implementation-environment policy,
and experiment planning. It does not claim coverage of theorem-level content.

## Summary

{table(summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}

## Source Access Log

{table(sources, ["source_id", "kind", "access_status", "url", "observed_support", "not_supported"])}

## Source Claim Map

{table(claims, ["claim_id", "support_level", "sources", "claim", "allowed_use", "not_allowed_use"])}

## Claim Boundaries

{table(boundaries, ["boundary_id", "allowed", "blocked", "next_gate"])}

## Proof Gates

{table(gates, ["gate", "status", "evidence", "detail", "remaining_gap"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}
"""


def update_tracking() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 204: Source Anchor Intake",
        """
## Stage 204: Source Anchor Intake

Goal:

```text
Ground the active 2025/686 work in real public sources without overstating
metadata-only evidence as theorem or implementation proof.
```

Status:

```text
Completed. Stage204 records PASS_STAGE204_SOURCE_ANCHOR_INTAKE_METADATA_ONLY.
Real source metadata and implementation-environment policy are recorded, while
full-text theorem/equation anchors and production keygen gates remain open.
```
""",
    )
    append_once(
        GOAL_MD,
        "Stage204 records source anchor intake.",
        """
Stage204 records source anchor intake. Decision: `PASS_STAGE204_SOURCE_ANCHOR_INTAKE_METADATA_ONLY`.
It grounds paper identity, source-reported complexity context, README backend
policy, and parameter/noise-measurement constraints in real public sources,
while keeping theorem/equation, novelty, and production keygen claims blocked.
""",
    )
    append_once(
        CURRENT_GOAL_MD,
        "108. Treat Stage204 as source anchor intake:",
        """
108. Treat Stage204 as source anchor intake:
    `PASS_STAGE204_SOURCE_ANCHOR_INTAKE_METADATA_ONLY`. Real public source
    metadata and implementation-environment constraints are recorded, but
    full-text theorem/equation anchors and production keygen evidence remain
    missing.
""",
    )
    append_once(
        HYPOTHESIS_YAML,
        "  - id: H128_source_anchor_intake",
        """
  - id: H128_source_anchor_intake
    statement: >
      Source-level grounding must distinguish real metadata, source-reported
      claims, same-platform benchmark requirements, and full-text theorem gaps.
    mechanism: >
      Stage204 records accessible public sources for 2025/686, maps each
      supported claim to allowed and blocked uses, and turns README platform and
      noise warnings into experiment policy.
    status: stage204_source_anchor_intake
    evidence: docs/stage204_source_anchor_intake.md; experiments/stage204_source_anchor_intake_plan.md; theory_checks/stage204_source_anchor_claim_boundary.md; repro/stage204_source_anchor_intake/summary.csv
    current_decision: >
      PASS_STAGE204_SOURCE_ANCHOR_INTAKE_METADATA_ONLY
    failure_criteria:
      - metadata-only evidence is used as theorem or equation support
      - source-reported external benchmarks are merged with our results without same-platform controls
      - production keygen or novelty claims proceed without full-text anchors
""",
    )
    append_once(
        RUN_LOG,
        "stage204_source_anchor_intake",
        f"{ACCESS_DATE},{git_commit()},stage204_source_anchor_intake,python scripts/build_stage204_source_anchor_intake.py,metadata_only_sources,none,repro/stage204_source_anchor_intake/summary.csv,{DECISION}\n",
    )
    append_once(
        MANIFEST,
        "### Stage204 Source Anchor Intake",
        """
### Stage204 Source Anchor Intake

- `docs/stage204_source_anchor_intake.md`
- `experiments/stage204_source_anchor_intake_plan.md`
- `theory_checks/stage204_source_anchor_claim_boundary.md`
- `algorithm_variants/mat_rlwe_sab_source_anchor_policy.md`
- `repro/stage204_source_anchor_intake/`
""",
    )
    append_once(
        CHECKLIST,
        "- [x] Stage204 source anchor intake records real-source metadata only and blocks theorem/equation overclaim.",
        "- [x] Stage204 source anchor intake records real-source metadata only and blocks theorem/equation overclaim.\n",
    )


def main() -> None:
    sources = source_rows()
    claims = claim_rows()
    boundaries = boundary_rows()
    gates = proof_gate_rows()
    nextq = next_rows()
    summary = summary_rows()

    write_csv(SOURCE_CSV, sources, ["source_id", "url", "kind", "access_status", "observed_support", "not_supported", "repo_snapshot", "access_date"])
    write_csv(CLAIM_CSV, claims, ["claim_id", "claim", "support_level", "sources", "allowed_use", "not_allowed_use"])
    write_csv(BOUNDARY_CSV, boundaries, ["boundary_id", "allowed", "blocked", "next_gate"])
    write_csv(PROOF_GATE_CSV, gates, ["gate", "status", "evidence", "detail", "remaining_gap"])
    write_csv(NEXT_CSV, nextq, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    report = build_report(summary, sources, claims, boundaries, gates, nextq)
    write_text_lf(REPORT_MD, report)
    write_text_lf(OUT_MD, report)
    write_text_lf(
        PLAN_MD,
        f"""# Stage204 Source Anchor Intake Plan

Primary endpoint: decide which 2025/686 claims can be grounded in currently
accessible real public sources.

Correctness gate: no metadata-only source may be used as theorem, equation,
security, novelty, or complete-SAB performance evidence.

Performance gate: README hardware/backend warnings become same-platform
benchmark requirements; no new speedup claim is made in this stage.

Decision: `{DECISION}`.
""",
    )
    write_text_lf(
        THEORY_MD,
        """# Stage204 Claim-Boundary Model

Accessible source metadata can identify the paper, authors, source-reported
method context, and implementation environment. It cannot establish the exact
SAB equations, selector distributions, security proof, noise recurrence, or
PVW/MAT-SAB novelty.

Therefore the active goal must move next through either a full-text anchor
table or same-platform benchmark refresh, not through additional unsupported
theory elaboration.
""",
    )
    write_text_lf(
        VARIANT_MD,
        """# MAT-RLWE SAB Source Anchor Policy

Any future PVW/MAT-SAB claim must cite the source tier that supports it:

- metadata source: title, authors, venue-status wording, parameter list;
- implementation README: build/backend/hardware/noise-measurement policy;
- full text: theorem, algorithm, equation, security, and experiment anchors;
- local experiment: correctness, noise, resource, and `T_bootstrap/r` speed.

Claims crossing tiers are rejected until the stronger evidence exists.
""",
    )
    write_text_lf(
        COMMANDS_MD,
        """# Stage204 Reproduction Commands

```powershell
python -m py_compile scripts\\build_stage204_source_anchor_intake.py
python scripts\\build_stage204_source_anchor_intake.py
Get-Content -Raw repro\\stage204_source_anchor_intake\\summary.csv
Get-Content -Raw repro\\stage204_source_anchor_intake\\proof_gate.csv
```

External source checks used during intake:

```powershell
Invoke-WebRequest https://raw.githubusercontent.com/antoniocgj/Fast-Amortized-Bootstrapping/main/README.md
Invoke-WebRequest https://askcryp.to/t/resource-topic-2025-686-fast-amortized-bootstrapping-with-small-keys-and-polynomial-noise-overhead/23992
Invoke-WebRequest https://antonioguimaraes.org/publication/guimaraes-fast-2025/
```
""",
    )

    artifact_paths = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        REPORT_MD,
        COMMANDS_MD,
        SUMMARY_CSV,
        SOURCE_CSV,
        CLAIM_CSV,
        BOUNDARY_CSV,
        PROOF_GATE_CSV,
        NEXT_CSV,
        Path(__file__),
    ]
    write_csv(ARTIFACT_CSV, artifact_rows(artifact_paths), ["path", "exists", "sha256", "bytes"])
    update_tracking()
    print(DECISION)


if __name__ == "__main__":
    main()
