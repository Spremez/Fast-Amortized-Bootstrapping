#!/usr/bin/env python3
"""Stage346: audit the path from scoped MAT-SAB evidence to a new algorithm."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from io import StringIO
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage346_algorithm_redesign_audit"

DOC = ROOT / "docs" / "stage346_algorithm_redesign_audit.md"
THEORY = ROOT / "theory_checks" / "stage346_mat_sab_algorithm_gap_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage346_redesign_candidates.md"
PLAN = ROOT / "experiments" / "stage347_mechanism_proof_gate_plan.md"
BUILDER = ROOT / "scripts" / "build_stage346_algorithm_redesign_audit.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

STAGE345_SUMMARY = ROOT / "repro" / "stage345_binary_matrix_synthesis" / "summary.csv"
STAGE345_MATRIX = ROOT / "repro" / "stage345_binary_matrix_synthesis" / "binary_matrix.csv"
STAGE345_CLAIMS = ROOT / "repro" / "stage345_binary_matrix_synthesis" / "claim_boundary.csv"

SUMMARY = OUT / "summary.csv"
CURRENT = OUT / "current_state_layers.csv"
GAPS = OUT / "algorithm_gap_matrix.csv"
ROUTES = OUT / "redesign_route_queue.csv"
RESOURCES = OUT / "resource_claim_gap.csv"
PAPER = OUT / "paper_claim_ledger.csv"
STOP_RULES = OUT / "stop_rules.csv"
PROOF = OUT / "proof_gate.csv"
REPORT = OUT / "stage346_report.md"
COMMANDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION = "PASS_STAGE346_REDESIGN_AUDIT_READY_STAGE347_MECHANISM_GATE"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


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


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines)


def current_state_layers(matrix: list[dict[str, str]], summary: dict[str, str]) -> list[dict[str, object]]:
    speed_range = f"{summary.get('speedup_min', '')}..{summary.get('speedup_max', '')}"
    return [
        {
            "layer": "L0_scalar_sab_baseline",
            "status": "preserved_reference",
            "evidence": "scalar SAB remains the repeated baseline in Stage345 matrix",
            "meaning_for_goal": "Baseline is not replaced; every MAT claim is measured as T_bootstrap/r versus repeated scalar SAB.",
            "next_action": "keep as immutable comparator",
        },
        {
            "layer": "L1_exact_dense_pvw_mat_sab",
            "status": "scoped_complete_sab_evidence_ready",
            "evidence": f"{len(matrix)} binary rows, speedup {speed_range}, metric {summary.get('primary_metric', '')}",
            "meaning_for_goal": "This is a working MAT-RLWE/r-body SAB implementation with complete-SAB amortized evidence.",
            "next_action": "use as the current exact-dense reference and paper systems baseline",
        },
        {
            "layer": "L2_exact_dense_local_microvariants",
            "status": "mostly_closed_or_neutral",
            "evidence": "active-buffer/direct-DFT promoted; r4-unrolled, selector-transpose, digit, and batch-IFFT routes are neutral/failed in prior stages",
            "meaning_for_goal": "More loop-only dense MAT rewrites need a measured new budget before source changes.",
            "next_action": "do not reopen without new profiler counter evidence",
        },
        {
            "layer": "L3_nonbinary_mat_sab_extension",
            "status": "separate_branch_not_in_stage345_claim",
            "evidence": "non-binary sparse/full-path smoke and small noise gates exist, but Stage345 binary matrix does not cover target performance",
            "meaning_for_goal": "Useful for breadth, not the next route to a stronger binary algorithm claim.",
            "next_action": "only continue if non-binary paper scope is explicitly required",
        },
        {
            "layer": "L4_structured_compact_selector_route",
            "status": "proof_blocked_but_algorithmically_relevant",
            "evidence": "finite/prototype stages support compact ideas, while production closure/security/keygen remain blocked",
            "meaning_for_goal": "This is the only current route likely to become a genuinely new SAB algorithm rather than an implementation refinement.",
            "next_action": "Stage347 mechanism proof gate",
        },
        {
            "layer": "L5_paper_literature_claims",
            "status": "scoped_systems_result_ready_novelty_open",
            "evidence": "Stage333/334/335 keep broad novelty and theoretical optimality blocked",
            "meaning_for_goal": "Paper wording must separate measured systems contribution from new-algorithm claims until Stage347+ passes.",
            "next_action": "refresh tables now; delay novelty wording until source-verified mechanism claim exists",
        },
    ]


def algorithm_gap_matrix() -> list[dict[str, object]]:
    return [
        {
            "gap": "G_exact_dense_vs_new_algorithm",
            "current_status": "exact_dense_path_works",
            "why_it_matters": "The current path changes the ciphertext to shared-mask r-body MAT form and speeds complete SAB per lane, but it still uses dense MAT selector/external-product structure.",
            "required_closure": "Define whether the paper claim is scoped exact-dense integration or a new structured selector/state algorithm.",
            "stage347_gate": "A mechanism candidate must state its accumulator state, selector key form, and closure invariant.",
        },
        {
            "gap": "G_dense_matrix_cost",
            "current_status": "not_theoretical_optimality",
            "why_it_matters": "For k=1 and r bodies, the dense MAT object has m=1+r rows/bodies. Shared-mask amortization helps, but dense off-lane work prevents ideal r-fold scaling.",
            "required_closure": "Either prove current dense rows are unavoidable under the current key format, or replace them with a closed structured selector family.",
            "stage347_gate": "Finite checker or lower-bound proof obligation must be machine-checkable.",
        },
        {
            "gap": "G_sab_schedule_closure",
            "current_status": "partial",
            "why_it_matters": "A structured MAT state must survive CMUX/NCMUX, RGSW monomial, sparse_mul, sub_a, and extract without re-densifying.",
            "required_closure": "For every scalar lane q, phase(body[q]) must equal the corresponding scalar SAB lane after every schedule step.",
            "stage347_gate": "Checker covers CMUX/NCMUX plus at least one sparse_mul/sub_a lifecycle; Stage348 extends to full schedule if Stage347 passes.",
        },
        {
            "gap": "G_keygen_security_noise",
            "current_status": "blocked_for_compact_route",
            "why_it_matters": "Selector compression is not valid unless encrypted key material is indistinguishable enough for the intended security model and noise remains bounded.",
            "required_closure": "Key object, encryption distribution, noise recurrence, and resource accounting for the new selector/state form.",
            "stage347_gate": "No hot-path implementation until the proof plan names these obligations.",
        },
        {
            "gap": "G_resource_claim",
            "current_status": "partial",
            "why_it_matters": "Stage345 records RSS, but paper-level resource claims need key size, keygen time, scratch, peak memory, and per-lane throughput together.",
            "required_closure": "A resource table for every promoted row and variant.",
            "stage347_gate": "Resource obligations are attached to each admitted mechanism.",
        },
        {
            "gap": "G_literature_novelty",
            "current_status": "open",
            "why_it_matters": "Shared-mask/multi-body ideas overlap prior work; the novel part, if any, must be SAB-specific state/key/schedule design with verified sources.",
            "required_closure": "Full-text source audit and claim-to-source ledger.",
            "stage347_gate": "No novelty wording is admitted by algorithm experiments alone.",
        },
    ]


def redesign_routes() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "Stage347_closed_structured_state_or_lower_bound_gate",
            "hypothesis": "A closed compact/lane-state MAT-SAB representation can reduce dense off-lane selector work while preserving per-lane scalar SAB phase.",
            "theory_task": "Write state tuple, selector rows, update equations, and negative controls; if impossible, formalize a current-format lower-bound instead.",
            "implementation_task": "Generate a finite checker/proof harness only; no SAB hot-path code.",
            "promotion_gate": "Pass closure equations for r=2 and r=4 over CMUX/NCMUX plus sparse_mul/sub_a lifecycle, or produce a clear lower-bound artifact.",
            "failure_action": "Keep exact-dense Stage345 result as the algorithmic endpoint and stop new mechanism work.",
        },
        {
            "priority": "P1",
            "route": "Stage348_closed_state_finite_full_schedule_checker",
            "hypothesis": "The Stage347 state is closed over the complete binary SAB sparse schedule.",
            "theory_task": "Extend the checker to h/r_prec/N symbolic counts and step-by-step lane invariant checks.",
            "implementation_task": "Finite-ring checker with deterministic seeds and mismatch reports.",
            "promotion_gate": "Zero phase mismatches and negative controls fail as expected.",
            "failure_action": "Revise equations once; if still failing, close the route.",
        },
        {
            "priority": "P2",
            "route": "Stage349_key_security_noise_resource_preflight",
            "hypothesis": "The closed state can be generated with encrypted selector/key material without unacceptable noise or resource growth.",
            "theory_task": "Define key distributions, security reduction boundary, noise recurrence, and public-key size model.",
            "implementation_task": "MOSFHET-adjacent isolated keygen/noise prototype.",
            "promotion_gate": "Noise and resource gates pass for r=2/4; security assumptions are explicitly scoped.",
            "failure_action": "Block production integration and report as theoretical/prototype-only.",
        },
        {
            "priority": "P3",
            "route": "Stage350_isolated_kernel_microbench",
            "hypothesis": "The closed state reduces work at kernel level under the same backend.",
            "theory_task": "Count external products, DFT conversions, memory traffic, and expected T_kernel/r.",
            "implementation_task": "Default-off isolated kernel and microbench, no full SAB integration.",
            "promotion_gate": "Correctness plus same-backend microbench improvement with attribution.",
            "failure_action": "Do not integrate into SAB; keep as negative ablation.",
        },
        {
            "priority": "P4",
            "route": "Stage351_full_sab_flagged_integration",
            "hypothesis": "The new state remains faster after full SAB schedule, extract, and post-processing overheads.",
            "theory_task": "Update complete-SAB cost model and stage attribution.",
            "implementation_task": "New explicit sab_pvw_structured_* path; scalar and exact-dense paths unchanged.",
            "promotion_gate": "Full SAB T_bootstrap/r A/B passes for r=2/4 with deterministic equivalence.",
            "failure_action": "Keep exact-dense path as default scoped result.",
        },
        {
            "priority": "P5",
            "route": "Stage352_highstat_noise_resource_parameter_matrix",
            "hypothesis": "The new path is statistically reliable and parameter-stable.",
            "theory_task": "State generality limits across N, h, r_prec, branch, and backend.",
            "implementation_task": ">=10 timing runs, multi-seed noise, resource/keygen tables across selected parameter matrix.",
            "promotion_gate": "No correctness regressions; resource cost is reported next to speedup.",
            "failure_action": "Scope the claim to passing rows only.",
        },
        {
            "priority": "P6",
            "route": "Stage353_source_verified_paper_package",
            "hypothesis": "The algorithmic claim is distinguishable from prior work and supported by verified citations.",
            "theory_task": "Related-work and claim ledger with full-text support.",
            "implementation_task": "Paper tables, algorithms, ablations, limitations, and reproducibility package.",
            "promotion_gate": "No claim lacks a source/evidence row.",
            "failure_action": "Publish/report only the scoped systems result.",
        },
    ]


def resource_claim_gap(matrix: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in matrix:
        rows.append({
            "case": row.get("case", ""),
            "rss_kb_recorded": row.get("time_maxrss_kb", ""),
            "key_size_recorded_for_this_row": "not_in_stage345_matrix",
            "keygen_time_recorded_for_this_row": "not_in_stage345_matrix",
            "scratch_peak_recorded_for_this_row": "not_in_stage345_matrix",
            "paper_resource_claim_status": "blocked_except_rss",
            "required_next": "Stage347+ promoted variants must bind speedup to key size, keygen, RSS, and scratch.",
        })
    return rows


def paper_claim_ledger(summary: dict[str, str]) -> list[dict[str, object]]:
    return [
        {
            "claim": "complete_binary_mat_sab_amortized_speedup",
            "status": "allowed_scoped",
            "safe_wording": f"On tested binary include-zero parameter rows under spqlios_avx512, PVW/MAT-SAB improves complete SAB T_bootstrap/r versus repeated scalar SAB; observed speedup range {summary.get('speedup_min', '')}..{summary.get('speedup_max', '')}.",
            "blocked_wording": "Do not claim universal SAB acceleration, non-binary coverage, backend-general speedup, or theoretical optimality.",
            "evidence": rel(STAGE345_MATRIX),
        },
        {
            "claim": "new_bootstrapping_algorithm",
            "status": "not_yet",
            "safe_wording": "The current implementation is an exact dense r-body MAT-RLWE SAB path with measured acceleration.",
            "blocked_wording": "Do not call it a new asymptotically better SAB algorithm unless Stage347+ proves and implements a closed structured state or lower-bound-qualified design.",
            "evidence": rel(GAPS),
        },
        {
            "claim": "theoretical_optimality",
            "status": "blocked",
            "safe_wording": "Exact-dense local optimization frontier is largely closed under current evidence.",
            "blocked_wording": "Do not state theoretical optimum for MAT-SAB without a defined model and lower-bound proof.",
            "evidence": rel(THEORY),
        },
        {
            "claim": "paper_novelty",
            "status": "blocked",
            "safe_wording": "A scoped systems contribution may be written with current evidence.",
            "blocked_wording": "Do not claim novelty of shared-mask/multi-body batching without verified related-work support and a SAB-specific delta.",
            "evidence": "Stage333/334/335 plus future Stage353",
        },
    ]


def stop_rules() -> list[dict[str, object]]:
    return [
        {
            "rule": "no_theory_loop",
            "condition": "A proposed new state cannot be converted into equations and a finite checker in Stage347.",
            "action": "Stop the mechanism route and keep the Stage345 scoped exact-dense result.",
        },
        {
            "rule": "no_hotpath_before_closure",
            "condition": "CMUX/NCMUX plus sparse_mul/sub_a closure is unproven.",
            "action": "Do not edit sab_pvw hot paths.",
        },
        {
            "rule": "one_revision_limit",
            "condition": "A finite checker fails.",
            "action": "Allow one equation revision; a second failure closes the candidate.",
        },
        {
            "rule": "same_backend_endpoint",
            "condition": "A candidate only wins a kernel microbench or different backend.",
            "action": "Do not claim SAB acceleration; require full SAB T_bootstrap/r under the same backend.",
        },
        {
            "rule": "source_verified_paper_claims",
            "condition": "A manuscript sentence asserts novelty, optimality, or related-work contrast.",
            "action": "Require source/full-text evidence in the claim ledger.",
        },
    ]


def proof_gate(summary: dict[str, str], matrix: list[dict[str, str]], routes: list[dict[str, object]]) -> list[dict[str, object]]:
    stage345_pass = summary.get("decision") == "PASS_STAGE345_BINARY_MATRIX_SYNTHESIS_SCOPED_READY"
    metric_ok = summary.get("primary_metric") == "complete_sab_T_bootstrap_over_r_vs_repeated_scalar"
    row_ok = len(matrix) == 6 and all(row.get("samples") == "10" and row.get("correctness") == "Pass" for row in matrix)
    return [
        {
            "gate": "G1_stage345_input",
            "status": "PASS" if stage345_pass else "FAIL",
            "value": summary.get("decision", ""),
            "interpretation": "Stage346 only audits after the current binary matrix is ready.",
        },
        {
            "gate": "G2_metric_alignment",
            "status": "PASS" if metric_ok else "FAIL",
            "value": summary.get("primary_metric", ""),
            "interpretation": "The active endpoint remains complete SAB T_bootstrap/r, matching the MAT-r-body intent.",
        },
        {
            "gate": "G3_evidence_quality",
            "status": "PASS" if row_ok else "FAIL",
            "value": f"rows={len(matrix)}",
            "interpretation": "The scoped current result is strong enough to serve as the exact-dense reference.",
        },
        {
            "gate": "G4_new_algorithm_boundary",
            "status": "PASS",
            "value": "current exact-dense result is not relabeled as theoretical optimality",
            "interpretation": "The new-algorithm goal remains active and distinct from the current measured systems result.",
        },
        {
            "gate": "G5_stage347_route",
            "status": "PASS" if routes and routes[0].get("route", "").startswith("Stage347") else "FAIL",
            "value": routes[0].get("route", "") if routes else "",
            "interpretation": "Next execution is a falsifiable mechanism/lower-bound gate, not another unconstrained rewrite.",
        },
        {
            "gate": "G6_decision",
            "status": DECISION if stage345_pass and metric_ok and row_ok else "FAIL_STAGE346_REDESIGN_AUDIT",
            "value": DECISION if stage345_pass and metric_ok and row_ok else "FAIL",
            "interpretation": "Controls whether Stage347 is admitted.",
        },
    ]


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


def artifact_index(paths: list[Path]) -> None:
    rows = [{"artifact": rel(path), "exists": path.exists(), "bytes": file_size(path), "sha256": sha256_file(path)} for path in paths]
    write_csv(ARTIFACT, rows, ["artifact", "exists", "bytes", "sha256"])


def append_run_log() -> None:
    marker = "stage346-algorithm-redesign-audit-001"
    row = [
        marker,
        date.today().isoformat(),
        git_head(),
        "Stage 346",
        "algorithm-redesign-audit",
        "python scripts/build_stage346_algorithm_redesign_audit.py",
        "Stage345 binary matrix; exact dense frontier; compact route blockers",
        "n/a",
        DECISION,
        "Separates current exact-dense MAT-SAB evidence from the still-open new-algorithm route and admits Stage347 mechanism proof gate.",
        f"{rel(DOC)}; {rel(THEORY)}; {rel(PLAN)}; {rel(SUMMARY)}; {rel(GAPS)}; {rel(ROUTES)}",
    ]
    line_buffer = StringIO()
    csv.writer(line_buffer, lineterminator="").writerow(row)
    replacement = line_buffer.getvalue()
    current = read_text(RUN_LOG)
    if marker in current:
        lines = [replacement if line.startswith(f"{marker},") else line for line in current.splitlines()]
        write_text(RUN_LOG, "\n".join(lines))
        return
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        csv.writer(handle, lineterminator="\n").writerow(row)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    matrix = read_csv(STAGE345_MATRIX)
    summary = first_row(STAGE345_SUMMARY)
    claims = read_csv(STAGE345_CLAIMS)
    speeds = [fnum(row.get("speedup_mean")) for row in matrix]
    layers = current_state_layers(matrix, summary)
    gaps = algorithm_gap_matrix()
    routes = redesign_routes()
    resources = resource_claim_gap(matrix)
    paper = paper_claim_ledger(summary)
    stops = stop_rules()
    proof = proof_gate(summary, matrix, routes)
    summary_rows = [{
        "decision": DECISION,
        "input_head": git_head(),
        "stage345_decision": summary.get("decision", ""),
        "primary_metric": summary.get("primary_metric", ""),
        "binary_rows": len(matrix),
        "speedup_min": f"{min(speeds):.6f}" if speeds else "",
        "speedup_max": f"{max(speeds):.6f}" if speeds else "",
        "speedup_mean": f"{mean(speeds):.6f}" if speeds else "",
        "new_algorithm_status": "open_stage347_required",
        "next_route": routes[0]["route"],
    }]

    write_csv(SUMMARY, summary_rows, ["decision", "input_head", "stage345_decision", "primary_metric", "binary_rows", "speedup_min", "speedup_max", "speedup_mean", "new_algorithm_status", "next_route"])
    write_csv(CURRENT, layers, ["layer", "status", "evidence", "meaning_for_goal", "next_action"])
    write_csv(GAPS, gaps, ["gap", "current_status", "why_it_matters", "required_closure", "stage347_gate"])
    write_csv(ROUTES, routes, ["priority", "route", "hypothesis", "theory_task", "implementation_task", "promotion_gate", "failure_action"])
    write_csv(RESOURCES, resources, ["case", "rss_kb_recorded", "key_size_recorded_for_this_row", "keygen_time_recorded_for_this_row", "scratch_peak_recorded_for_this_row", "paper_resource_claim_status", "required_next"])
    write_csv(PAPER, paper, ["claim", "status", "safe_wording", "blocked_wording", "evidence"])
    write_csv(STOP_RULES, stops, ["rule", "condition", "action"])
    write_csv(PROOF, proof, ["gate", "status", "value", "interpretation"])

    write_text(COMMANDS, """# Stage346 Reproduction Commands

```powershell
python scripts\\build_stage346_algorithm_redesign_audit.py
```
""")

    write_text(DOC, f"""# Stage346 Algorithm Redesign Audit

Decision: `{DECISION}`.

Stage346 re-scopes the active objective after Stage345. The current project
does have a complete exact-dense PVW/MAT-SAB path with binary high-stat
`T_bootstrap/r` evidence, but that is not yet a proof of theoretical
optimality and not yet a new compact/structured SAB algorithm.

## Current Position

{md_table(summary_rows, ["decision", "stage345_decision", "primary_metric", "binary_rows", "speedup_min", "speedup_max", "speedup_mean", "new_algorithm_status"])}

The supported comparison dimension is amortized complete bootstrapping time per
processed lane/bit:

```text
speedup = (repeated scalar SAB T_bootstrap / r)
          / (PVW/MAT-SAB T_bootstrap / r)
```

Across the six Stage345 binary rows, the measured speedup range is
`{summary_rows[0]["speedup_min"]}` to `{summary_rows[0]["speedup_max"]}`, with
mean `{summary_rows[0]["speedup_mean"]}`. This is strong scoped systems
evidence. It does not by itself establish a new asymptotic algorithm.

## Project Layers

{md_table(layers, ["layer", "status", "meaning_for_goal", "next_action"])}

## Algorithm Gaps

{md_table(gaps, ["gap", "current_status", "required_closure", "stage347_gate"])}

## Revised Route To Completion

{md_table(routes, ["priority", "route", "promotion_gate", "failure_action"])}

## Paper Claim Ledger

{md_table(paper, ["claim", "status", "safe_wording", "blocked_wording"])}

## Stop Rules

{md_table(stops, ["rule", "condition", "action"])}
""")

    write_text(THEORY, """# Stage346 MAT-SAB Algorithm Gap Model

## Baseline Object

Repeated scalar SAB evaluates r independent scalar bootstraps and compares to
PVW/MAT-SAB by the amortized endpoint:

```text
T_scalar_per_lane = T_repeated_scalar / r
T_mat_per_lane    = T_pvw_mat_sab / r
```

The current PVW/MAT-SAB object is an r-body RLWE-like accumulator:

```text
C = (a, b_0, ..., b_{r-1})
```

All lanes share the mask component `a`; each body `b_q` carries one output
lane. SAB correctness requires a stepwise invariant:

```text
phase(C.body[q]) == phase(scalar_SAB_lane[q])
```

for each lane q after CMUX/NCMUX, RGSW monomial updates, sparse multiplication,
sub_a, extraction, and key switching.

## Exact Dense Path

The implemented path uses MAT external products for the r-body object. For
`k=1`, the dense MAT dimension is `m = 1 + r`. Shared-mask decomposition and
body batching reduce repeated work, but dense selector rows still introduce
off-lane terms. Therefore the measured 1.6x-1.75x complete-SAB per-lane
speedup is meaningful but far from ideal r-fold scaling, especially for r=4.

The exact dense path is a valid scoped systems result. It is not a proof that
MAT-SAB is optimal, because the model has not ruled out structured selector or
closed lane-state representations with fewer off-lane terms.

## New Algorithm Requirement

A stronger algorithm needs one of two outcomes:

1. Closed structured-state route:
   - define a state representation that stays closed under the full SAB
     schedule;
   - define selector/key material that updates each lane without re-densifying
     into the full `(1+r) x (1+r)` matrix;
   - prove or check the lane phase invariant after each SAB step;
   - then implement behind a new explicit path.

2. Current-format lower-bound route:
   - define the allowed key/state model;
   - prove that dense off-lane work is unavoidable inside that model;
   - downgrade the contribution to exact-dense optimality under that restricted
     model, not global MAT-SAB optimality.

Stage347 must choose one of these outcomes. It may not produce only informal
theory text; it must create a finite checker or a lower-bound proof artifact
with explicit assumptions.
""")

    write_text(VARIANT, """# Stage346 Redesign Candidates

## Current Reference: Exact Dense PVW/MAT-SAB

Status: keep as scoped reference.

This path is already implemented and measured at the complete SAB
`T_bootstrap/r` endpoint. It should not be rewritten unless a new profile
budget is recorded.

## Candidate A: Closed Structured Lane-State MAT-SAB

Goal: replace dense off-lane MAT selector work with a state that stores a
shared component plus lane-local or lane-pair deltas, while preserving the
scalar SAB phase invariant for every lane.

Stage347 requirements:

- state tuple and selector rows are explicitly defined;
- CMUX/NCMUX, RGSW monomial, sparse_mul, sub_a, and extract obligations are
  listed;
- finite checker covers r=2 and r=4;
- negative controls fail when off-lane or dummy terms are removed incorrectly.

## Candidate B: Current-Format Dense Lower Bound

Goal: prove that with the existing `MAT_TRGSW_DFT` key/state format, loop-only
off-lane skipping is impossible and dense rows are locally necessary.

This is not a speedup candidate. It is a paper-boundary candidate: it can
justify why the current exact dense implementation is the best result under the
existing format, while leaving new-format algorithms open.

## Candidate C: Non-Binary Extension

Status: defer unless paper scope expands.

Non-binary MAT-SAB already has staged smoke/noise work, but it is not the main
route to a stronger binary MAT-SAB algorithmic claim.
""")

    write_text(PLAN, """# Stage347 Mechanism Proof Gate Plan

Goal: convert the open MAT-SAB new-algorithm question into one falsifiable
mechanism gate.

## Required Entry

Stage347 must start from Stage346. It cannot edit SAB hot-path code.

## Route A: Closed Structured State

Tasks:

- define the candidate accumulator state and selector key shape;
- write the per-step lane invariant;
- implement a finite checker for r=2 and r=4;
- include negative controls for invalid off-lane skipping and invalid
  shared-output collapse;
- map every passing equation to the later MOSFHET integration obligation.

Promotion gate:

- zero phase mismatches in the finite checker;
- negative controls fail;
- resource/key/noise obligations are named for Stage349.

## Route B: Current-Format Lower Bound

Tasks:

- define the restricted current-format model;
- prove or check why dense off-lane terms are required;
- state exactly what the lower bound does not cover.

Promotion gate:

- assumptions are explicit;
- result is suitable for a claim-boundary section, not a new speedup claim.

## Exit Policy

If neither route can produce a checker/proof artifact, the mechanism route is
closed and the project proceeds with the scoped exact-dense systems paper.
""")

    write_text(REPORT, f"""# Stage346 Report

Decision: `{DECISION}`.

## Summary

{md_table(summary_rows, ["decision", "binary_rows", "speedup_min", "speedup_max", "speedup_mean", "next_route"])}

## Current Layers

{md_table(layers, ["layer", "status", "next_action"])}

## Gaps

{md_table(gaps, ["gap", "current_status", "stage347_gate"])}

## Routes

{md_table(routes, ["priority", "route", "promotion_gate"])}

## Proof Gate

{md_table(proof, ["gate", "status", "value"])}
""")

    append_once(GOAL, "<!-- stage346-algorithm-redesign-audit -->", f"""
<!-- stage346-algorithm-redesign-audit -->
- Stage346: `{DECISION}`. The scoped exact-dense PVW/MAT-SAB result remains supported by Stage345, but the new-algorithm goal is now explicitly routed to Stage347 closed structured-state or current-format lower-bound proof. No SAB hot-path rewrite is admitted before that gate.
""")
    append_once(ROADMAP, "<!-- stage346-algorithm-redesign-audit -->", f"""
<!-- stage346-algorithm-redesign-audit -->
## Stage346: Algorithm Redesign Audit

- Decision: `{DECISION}`.
- Result: separates current exact-dense MAT-SAB evidence from the still-open new-algorithm route.
- Next: Stage347 mechanism proof gate.

## Stage347: Closed State Or Lower-Bound Mechanism Gate

- Goal: prove a closed structured MAT-SAB state or prove a current-format dense lower bound.
- Code permission: finite checker/proof artifact only; no SAB hot-path integration.
- Gate: r=2/r=4 lane invariant passes over CMUX/NCMUX plus sparse_mul/sub_a lifecycle, or lower-bound assumptions are explicit.

## Stage348: Full Schedule Finite Checker

- Goal: if Stage347 admits a structured state, check the complete binary SAB schedule.
- Gate: zero lane phase mismatches and failing negative controls.

## Stage349: Keygen/Security/Noise/Resource Preflight

- Goal: define encrypted selector material, noise recurrence, and resource model for the new state.
- Gate: isolated keygen/noise/resource pass before production integration.

## Stage350: Isolated Structured Kernel Microbench

- Goal: test the new state at kernel level under the same backend.
- Gate: correctness plus same-backend kernel improvement; no SAB claim yet.

## Stage351: Full SAB Flagged Integration

- Goal: add a new explicit `sab_pvw_structured_*` path only if Stage347-350 pass.
- Gate: full SAB `T_bootstrap/r` A/B and deterministic equivalence for r=2/r=4.

## Stage352: High-Stat Noise/Resource/Parameter Matrix

- Goal: convert a promoted structured path into statistically reliable evidence.
- Gate: timing, noise, key size, keygen, RSS, scratch, and parameter matrix pass.

## Stage353: Source-Verified Paper Package

- Goal: write paper claims only from verified source and experiment ledgers.
- Gate: no novelty, optimality, or related-work claim without source support.
""")
    append_once(HYPOTHESES, "H346_algorithm_redesign_audit:", f"""
H346_algorithm_redesign_audit:
  status: {DECISION}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage346_algorithm_redesign_audit/summary.csv
    - repro/stage346_algorithm_redesign_audit/current_state_layers.csv
    - repro/stage346_algorithm_redesign_audit/algorithm_gap_matrix.csv
    - repro/stage346_algorithm_redesign_audit/redesign_route_queue.csv
  conclusion: >
    Stage346 separates the supported exact-dense PVW/MAT-SAB systems result
    from the still-open new-algorithm objective. The next valid execution is
    Stage347 closed structured-state or current-format lower-bound proof, not
    another speculative SAB hot-path rewrite.
""")
    append_once(MANIFEST, "<!-- stage346-algorithm-redesign-audit-manifest -->", """
<!-- stage346-algorithm-redesign-audit-manifest -->
- stage346_algorithm_redesign_audit:
  - `docs/stage346_algorithm_redesign_audit.md`
  - `theory_checks/stage346_mat_sab_algorithm_gap_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage346_redesign_candidates.md`
  - `experiments/stage347_mechanism_proof_gate_plan.md`
  - `scripts/build_stage346_algorithm_redesign_audit.py`
  - `repro/stage346_algorithm_redesign_audit/`
""")
    append_once(CHECKLIST, "<!-- stage346-algorithm-redesign-audit-checklist -->", f"""
<!-- stage346-algorithm-redesign-audit-checklist -->
- [x] Stage346 records `{DECISION}` and routes the new-algorithm objective to a falsifiable Stage347 mechanism gate.
""")
    append_run_log()
    artifact_index([DOC, THEORY, VARIANT, PLAN, BUILDER, SUMMARY, CURRENT, GAPS, ROUTES, RESOURCES, PAPER, STOP_RULES, PROOF, REPORT, COMMANDS])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
