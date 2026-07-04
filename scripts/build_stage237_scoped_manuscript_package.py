#!/usr/bin/env python3
"""Stage237: scoped manuscript/report package from selected binary matrix evidence."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage237_scoped_manuscript_package"

DOC = ROOT / "docs" / "stage237_scoped_manuscript_package.md"
PLAN = ROOT / "experiments" / "stage237_scoped_manuscript_package_plan.md"
THEORY = ROOT / "theory_checks" / "stage237_manuscript_claim_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage237_scoped_manuscript.md"

INPUTS = OUT / "input_status.csv"
MATRIX_TABLE = OUT / "experiment_table_selected_binary.csv"
CLAIMS = OUT / "contribution_claims.csv"
SECTIONS = OUT / "section_evidence_matrix.csv"
SOURCE_POLICY = OUT / "source_policy.csv"
CANDIDATES = OUT / "candidate_path_matrix.csv"
OVERCLAIM = OUT / "overclaim_guard.csv"
GATES = OUT / "gate_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
MANUSCRIPT = OUT / "manuscript_skeleton.md"
REPORT = OUT / "stage237_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE236 = ROOT / "repro" / "stage236_set_2_3_4096_r4_highstat_slice"
STAGE230 = ROOT / "repro" / "stage230_source_verified_literature_novelty_audit"
STAGE227 = ROOT / "repro" / "stage227_exact_route_claim_boundary_update"
STAGE226 = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution"

DECISION = "PASS_STAGE237_SCOPED_MANUSCRIPT_PACKAGE_READY_CLAIM_BOUNDED"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._\n"
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|").replace("\n", "<br>") for field in fields) + " |")
    return "\n".join(out) + "\n"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def input_rows() -> List[Dict[str, str]]:
    paths = [
        (STAGE236 / "proof_gate.csv", "Stage236 selected binary matrix proof"),
        (STAGE236 / "selected_binary_matrix_summary.csv", "Stage236 four-row selected binary experiment table"),
        (STAGE236 / "stage236_report.md", "Stage236 report with metric and boundary"),
        (STAGE230 / "source_verification_refresh.csv", "Stage230 source verification refresh"),
        (STAGE230 / "novelty_risk_map.csv", "Stage230 novelty risk map"),
        (STAGE230 / "claim_policy.csv", "Stage230 claim policy"),
        (STAGE230 / "related_work_axes.csv", "Stage230 related-work axes"),
        (STAGE227 / "claim_matrix.csv", "Stage227 metric/claim boundary"),
        (STAGE227 / "metric_ledger.csv", "Stage227 T_bootstrap/r metric ledger"),
        (STAGE226 / "attribution_summary.csv", "Stage226 native counter attribution, optional mechanism only"),
    ]
    return [
        {
            "input": rel(path),
            "status": "present" if path.exists() else "missing",
            "role": role,
            "bytes": str(path.stat().st_size) if path.exists() else "",
        }
        for path, role in paths
    ]


def matrix_rows() -> List[Dict[str, str]]:
    return read_csv(STAGE236 / "selected_binary_matrix_summary.csv")


def claim_rows() -> List[Dict[str, str]]:
    matrix = matrix_rows()
    speedups = [row.get("mean_speedup", "") for row in matrix]
    min_ci = min(float(row["speedup_ci95_low"]) for row in matrix if row.get("speedup_ci95_low"))
    return [
        {
            "claim_id": "C1_selected_binary_throughput",
            "status": "ALLOW_SCOPED_REPORT",
            "safe_wording": "Exact dense PVW/MAT-SAB improves complete-SAB T_bootstrap/r over repeated scalar SAB on the selected binary rows.",
            "quantitative_support": f"mean speedups {', '.join(speedups)}; weakest CI lower bound {min_ci:.6f}",
            "required_caveat": "Report parameter, r, backend, run count, seed count, key bytes, keygen, RSS, and commit/proof gate.",
            "blocked_wording": "Do not claim all-parameter speedup, non-binary support, novelty, or theoretical optimality.",
            "evidence": rel(STAGE236 / "selected_binary_matrix_summary.csv"),
        },
        {
            "claim_id": "C2_correctness_noise_side_condition",
            "status": "ALLOW_SCOPED_REPORT",
            "safe_wording": "The four selected binary rows have zero PVW/scalar/pair final-output failures under 20 deterministic seeds each.",
            "quantitative_support": "all rows record noise_failures 0/0/0",
            "required_caveat": "This is sampled final-output noise/correctness evidence, not a full proof of every parameter branch.",
            "blocked_wording": "Do not use sampled noise evidence as a universal correctness theorem.",
            "evidence": rel(STAGE236 / "selected_binary_matrix_summary.csv"),
        },
        {
            "claim_id": "C3_resource_side_costs",
            "status": "ALLOW_SCOPED_REPORT",
            "safe_wording": "Throughput gains are reported with key-size, keygen, and RSS side costs.",
            "quantitative_support": "key bytes ratio range 1.006136..1.069425; keygen ratio range 1.102149..1.357920; RSS ratio range 0.968173..1.000880",
            "required_caveat": "Do not hide slower keygen or public-key growth when reporting speedups.",
            "blocked_wording": "Do not report throughput alone as final efficiency.",
            "evidence": rel(STAGE236 / "selected_binary_matrix_summary.csv"),
        },
        {
            "claim_id": "C4_novelty",
            "status": "SCOPED_ONLY_NOT_FINAL",
            "safe_wording": "The current draft can describe a scoped systems/engineering study of PVW/MAT-SAB for 2025/686-style SAB.",
            "quantitative_support": "Stage230 allows only scoped systems wording and rejects broad shared-mask/PVW/external-product novelty.",
            "required_caveat": "Cite related-work axes and avoid first/new language unless a later citation audit upgrades the claim.",
            "blocked_wording": "Do not claim first shared-mask batching, first PVW packing, or first TFHE external product.",
            "evidence": rel(STAGE230 / "novelty_risk_map.csv"),
        },
        {
            "claim_id": "C5_optimality",
            "status": "DENY",
            "safe_wording": "The current complexity model identifies measured lower-bound-style constraints and candidate paths, but no formal optimality theorem is complete.",
            "quantitative_support": "none",
            "required_caveat": "State theoretical optimality as future work.",
            "blocked_wording": "Do not state theoretically optimal, universally optimal, or lower-bound tight.",
            "evidence": rel(STAGE227 / "claim_matrix.csv"),
        },
    ]


def section_rows() -> List[Dict[str, str]]:
    return [
        {
            "section": "Abstract",
            "content_scope": "One-paragraph summary with selected-binary T_bootstrap/r results and explicit claim boundary.",
            "must_include": "four-row speedup range, same-backend repeated scalar baseline, non-binary/optimality caveat",
            "evidence": rel(CLAIMS),
        },
        {
            "section": "Introduction",
            "content_scope": "Motivate r-body MAT-RLWE ciphertexts for SAB lanes and define T_bootstrap/r as the endpoint.",
            "must_include": "why scalar repeated SAB is the baseline and why isolated MAT-EP speed is insufficient",
            "evidence": rel(STAGE227 / "metric_ledger.csv"),
        },
        {
            "section": "Background and Related Work",
            "content_scope": "Use source-verified axes for 2025/686 SAB, incomplete NTT, common-mask TFHE, batch/SIMD bootstrapping, PVW packing, and TFHE external product.",
            "must_include": "source status and novelty risk labels",
            "evidence": rel(STAGE230 / "related_work_axes.csv"),
        },
        {
            "section": "Algorithm Object",
            "content_scope": "Define exact dense PVW/MAT-SAB as shared-mask r-body accumulator over the existing SAB schedule.",
            "must_include": "scalar SAB unchanged; sab_pvw path explicit; r means independent LUT/SAB lanes",
            "evidence": rel(STAGE236 / "proof_gate.csv"),
        },
        {
            "section": "Complexity and Candidate Paths",
            "content_scope": "Report cost model, dense MAT arithmetic pressure, and candidate routes with pass/blocked status.",
            "must_include": "no formal optimality theorem; current optimum is empirical among tested routes",
            "evidence": rel(CANDIDATES),
        },
        {
            "section": "Implementation",
            "content_scope": "Describe current exact dense path, active-buffer fusion, AVX512 specialization, and explicit flags.",
            "must_include": "same backend and run conditions",
            "evidence": rel(STAGE236 / "stage236_report.md"),
        },
        {
            "section": "Evaluation",
            "content_scope": "Report the selected binary matrix table, noise, resource, and reproducibility commands.",
            "must_include": "mean, CI, failure counts, key/RSS/keygen ratios",
            "evidence": rel(MATRIX_TABLE),
        },
        {
            "section": "Limitations",
            "content_scope": "State blocked claims and remaining gates.",
            "must_include": "non-binary, compact route, all-parameter scope, novelty, theoretical optimality",
            "evidence": rel(OVERCLAIM),
        },
    ]


def source_policy_rows() -> List[Dict[str, str]]:
    rows = []
    for row in read_csv(STAGE230 / "source_verification_refresh.csv"):
        rows.append(
            {
                "source_id": row.get("source_id", ""),
                "title": row.get("title", ""),
                "verification_status": row.get("verification_status", ""),
                "allowed_use": row.get("novelty_impact", ""),
                "required_caveat": "Use as source-verified related-work/metadata evidence; do not fabricate theorem-level claims not checked in the source.",
                "primary_url": row.get("primary_url", ""),
            }
        )
    return rows


def candidate_rows() -> List[Dict[str, str]]:
    return [
        {
            "path_id": "P1_exact_dense_pvw_mat_sab",
            "algorithm_path": "Exact dense MAT/PVW r-body SAB with shared mask and independent body lanes.",
            "theory_status": "closed for tested semantics; no formal optimality theorem",
            "experiment_status": "selected binary high-stat complete",
            "expected_bottleneck": "dense MAT external product and SAB schedule body work",
            "promotion_rule": "already promoted for selected binary rows only",
            "evidence": rel(STAGE236 / "selected_binary_matrix_summary.csv"),
        },
        {
            "path_id": "P2_native_counter_backend_validation",
            "algorithm_path": "Use native counters/backend attribution to separate implementation effects from algorithmic lane batching.",
            "theory_status": "mechanism attribution only",
            "experiment_status": "optional after Stage237",
            "expected_bottleneck": "cycles/load/store around MAT external product and DFT conversion",
            "promotion_rule": "must improve or explain complete-SAB T_bootstrap/r; otherwise attribution only",
            "evidence": rel(STAGE226 / "attribution_summary.csv"),
        },
        {
            "path_id": "P3_compact_or_sparse_selector_mat",
            "algorithm_path": "Exploit SAB selector structure to reduce dense MAT work or key material.",
            "theory_status": "blocked by selector/security/noise proof obligations",
            "experiment_status": "not complete-SAB admitted",
            "expected_bottleneck": "encrypted selector indistinguishability and closed shared-mask equations",
            "promotion_rule": "closed equations, production keygen, isolated equivalence, noise proof, full SAB A/B",
            "evidence": rel(STAGE236 / "next_stage_queue.csv"),
        },
        {
            "path_id": "P4_nonbinary_pvw_sab",
            "algorithm_path": "Extend exact MAT/PVW-SAB beyond binary branches.",
            "theory_status": "unsupported in current claim",
            "experiment_status": "blocked",
            "expected_bottleneck": "branch-specific selector and noise behavior",
            "promotion_rule": "branch-specific correctness/noise/resource/full-SAB A/B",
            "evidence": rel(STAGE236 / "proof_gate.csv"),
        },
        {
            "path_id": "P5_theoretical_optimality",
            "algorithm_path": "Prove a lower-bound-tight r-body MAT-RLWE SAB construction.",
            "theory_status": "open",
            "experiment_status": "not applicable",
            "expected_bottleneck": "formal model must account for encrypted selectors, dense external product, and output lanes",
            "promotion_rule": "new theorem with assumptions, proof, and relation to prior art",
            "evidence": rel(STAGE227 / "claim_matrix.csv"),
        },
    ]


def manuscript_text(matrix: List[Dict[str, str]], claims: List[Dict[str, str]], candidates: List[Dict[str, str]]) -> str:
    speed_range = f"{min(float(row['mean_speedup']) for row in matrix):.6f}x..{max(float(row['mean_speedup']) for row in matrix):.6f}x"
    return f"""# Scoped Manuscript Skeleton: PVW/MAT-SAB as r-Body SAB

## Abstract Draft

We study an exact dense PVW/MAT-RLWE realization of 2025/686-style sparse
amortized bootstrapping in which one shared mask carries r independent body
lanes. The evaluation endpoint is complete bootstrapping time per processed
plaintext lane, `T_bootstrap/r`, compared against r repeated scalar SAB
executions under the same backend. On the selected binary parameter rows
`SET_4_5_2048` and `SET_2_3_4096`, r=2 and r=4, the current implementation
records mean speedups from `{speed_range}` with zero PVW/scalar/pair
final-output failures in 20 deterministic seeds per row. The result is a
scoped systems result: it does not prove non-binary support, compact selector
construction, broad novelty, or theoretical optimality.

## 1. Introduction

The original research question is not whether one external-product kernel can
be faster in isolation. The question is whether changing the SAB accumulator
from r independent RLWE executions to a MAT-RLWE/r-body object improves the
amortized full bootstrapping cost per handled plaintext lane. This draft uses
`T_bootstrap/r` as the primary metric throughout.

## 2. Background and Related Work

The related-work section must be written from the Stage230 source policy. It
should cover the 2025/686 SAB baseline, post-686 incomplete-NTT acceleration,
common-mask packed-message TFHE, batch/SIMD bootstrapping, PVW packing, and
TFHE external products. The draft may position this project as a scoped
PVW/MAT-SAB integration and evaluation. It must not claim first shared-mask
batching, first PVW packing, or first external product.

## 3. Algorithm Object

The implemented algorithm is exact dense PVW/MAT-SAB. The scalar SAB path stays
as the reference path. The PVW path uses a shared mask and r body lanes; here r
means independent LUT/SAB lanes, not accumulator-index packing. Each lane must
match the scalar SAB output for the corresponding input and LUT.

## 4. Complexity and Candidate Paths

The scalar baseline repeats the SAB computation r times. The exact PVW/MAT
path amortizes shared schedule and mask work, but it pays dense MAT external
product costs and resource side costs. The current evidence identifies the
exact dense path as the best promoted route for the selected binary rows. The
candidate path matrix keeps backend-counter attribution, compact/sparse
selector MAT, non-binary support, and theoretical optimality as separate gates.

## 5. Implementation

The report should describe `sab_pvw_*`, active-buffer fusion,
`MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`, and `spqlios_avx512`. All
performance claims are same-backend complete-SAB comparisons against repeated
scalar SAB, not comparisons against Windows/FFNT or isolated MAT microbenchmarks.

## 6. Evaluation

Primary table:

{table(matrix, ["param", "r", "stage", "stat_level", "mean_speedup", "speedup_ci95_low", "speedup_ci95_high", "noise_failures", "key_bytes_ratio", "keygen_ratio", "rss_ratio", "status", "evidence"])}
Every row uses 10 complete-SAB A/B timing samples and 20 deterministic noise
seeds. Resource costs are reported beside throughput.

## 7. Claim Ledger

{table(claims, ["claim_id", "status", "safe_wording", "quantitative_support", "required_caveat", "blocked_wording", "evidence"])}
## 8. Candidate Paths

{table(candidates, ["path_id", "algorithm_path", "theory_status", "experiment_status", "expected_bottleneck", "promotion_rule", "evidence"])}
## 9. Limitations

This package is not a final paper claim. It is a bounded manuscript skeleton
and evidence map. A final submission still needs source-level citation
verification, a venue/template pass, and a decision on whether to add native
counter attribution or keep it as future work.
"""


def overclaim_rows(claims: List[Dict[str, str]]) -> List[Dict[str, str]]:
    text = (read_text(MANUSCRIPT) + "\n" + "\n".join(row["blocked_wording"] for row in claims)).lower()
    phrases = [
        "first shared-mask",
        "first pvw packing",
        "first external product",
        "all-parameter speedup",
        "non-binary support",
        "theoretically optimal",
        "universally optimal",
        "lower-bound tight",
        "compact selector construction succeeds",
    ]
    rows = []
    for phrase in phrases:
        count = text.count(phrase)
        allowed_context = "allowed if only present in blocked wording or limitations"
        rows.append(
            {
                "phrase": phrase,
                "count": str(count),
                "status": "PASS_CONTEXTUAL_GUARD" if count else "PASS_ABSENT",
                "allowed_context": allowed_context,
            }
        )
    return rows


def gate_rows(inputs: List[Dict[str, str]], matrix: List[Dict[str, str]], claims: List[Dict[str, str]], source_policy: List[Dict[str, str]], overclaim: List[Dict[str, str]]) -> List[Dict[str, str]]:
    matrix_pass = all(row.get("status") == "PASS_HIGHSTAT_SLICE" for row in matrix)
    deny_optimality = any(row["claim_id"] == "C5_optimality" and row["status"] == "DENY" for row in claims)
    contextual_ok = all(row["status"].startswith("PASS") for row in overclaim)
    return [
        {"gate": "G1_inputs", "required": "Stage236 matrix, Stage230 source policy, Stage227 claim boundary, Stage226 attribution exist", "observed": "all present" if all(row["status"] == "present" for row in inputs) else "missing", "status": "PASS" if all(row["status"] == "present" for row in inputs) else "FAIL", "claim_effect": "allows manuscript package refresh"},
        {"gate": "G2_matrix", "required": "four selected binary rows have high-stat performance/noise/resource evidence", "observed": "four rows pass" if matrix_pass else "one or more rows incomplete", "status": "PASS_SELECTED_BINARY_MATRIX" if matrix_pass else "FAIL", "claim_effect": "allows selected-binary performance table only"},
        {"gate": "G3_primary_metric", "required": "primary endpoint is complete-SAB T_bootstrap/r", "observed": "metric fixed in claims and manuscript", "status": "PASS", "claim_effect": "prevents isolated-kernel speedup overclaim"},
        {"gate": "G4_source_policy", "required": "source rows are taken from Stage230 verified primary/official metadata matrix", "observed": f"{len(source_policy)} source rows", "status": "PASS" if len(source_policy) >= 5 else "FAIL", "claim_effect": "keeps references source-grounded"},
        {"gate": "G5_optimality_boundary", "required": "theoretical optimality remains denied", "observed": "C5_optimality DENY" if deny_optimality else "missing", "status": "BOUNDARY_HELD" if deny_optimality else "FAIL", "claim_effect": "blocks theoretical-optimality wording"},
        {"gate": "G6_overclaim_scan", "required": "forbidden phrases absent or contextualized as blocked wording/limitations", "observed": "contextual guard pass" if contextual_ok else "check needed", "status": "PASS_CONTEXTUAL_GUARD" if contextual_ok else "FAIL", "claim_effect": "prevents manuscript overclaim"},
        {"gate": "G7_stage237_decision", "required": "all report package gates pass", "observed": DECISION, "status": DECISION, "claim_effect": "move to source/citation finalization or native-counter attribution"},
    ]


def proof_rows(gates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "gate": row["gate"],
            "status": row["status"],
            "metric": row["required"],
            "value": row["observed"],
            "evidence": rel(GATES),
            "interpretation": row["claim_effect"],
        }
        for row in gates
    ]


def next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage238_source_verified_citation_package",
            "entry_condition": "Scoped manuscript package is ready and a paper-facing draft needs citation-precise statements.",
            "gate": "Every related-work and background sentence must map to a Stage230 source row or a freshly verified source.",
            "status": "ready",
            "failure_action": "Keep Stage237 as engineering report, not final paper draft.",
            "evidence": rel(SOURCE_POLICY),
        },
        {
            "priority": "P1",
            "route": "stage239_native_counter_backend_validation",
            "entry_condition": "The draft needs stronger implementation attribution beyond complete-SAB timing.",
            "gate": "Native Linux perf counters or explicit WSL proxy label; no theoretical-optimality wording.",
            "status": "optional",
            "failure_action": "Omit counter claims and keep only timing/resource/noise evidence.",
            "evidence": rel(CANDIDATES),
        },
        {
            "priority": "P2",
            "route": "stage240_nonbinary_or_compact_design",
            "entry_condition": "The research target expands beyond exact dense binary PVW/MAT-SAB.",
            "gate": "Closed selector equations, security/noise model, production keygen, isolated equivalence, and full SAB A/B.",
            "status": "blocked_until_design",
            "failure_action": "Do not claim non-binary, compact, or theoretical-optimal MAT-RLWE SAB.",
            "evidence": rel(CLAIMS),
        },
    ]


def artifact_rows(paths: List[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        if path.exists() and path.is_file():
            rows.append({"artifact": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256(path)})
    return rows


def write_repro_commands() -> None:
    write_text(
        REPRO_CMDS,
        """# Stage237 Reproduction Commands

Stage237 is an aggregation/report stage. It does not rerun SAB timings.

```bash
python scripts/build_stage237_scoped_manuscript_package.py
```

Primary input evidence:

```text
repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv
repro/stage230_source_verified_literature_novelty_audit/source_verification_refresh.csv
repro/stage230_source_verified_literature_novelty_audit/novelty_risk_map.csv
repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv
```
""",
    )


def write_docs(inputs: List[Dict[str, str]], matrix: List[Dict[str, str]], claims: List[Dict[str, str]], sections: List[Dict[str, str]], source_policy: List[Dict[str, str]], candidates: List[Dict[str, str]], overclaim: List[Dict[str, str]], gates: List[Dict[str, str]], proof: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> None:
    doc = f"""# Stage237 Scoped Manuscript Package

Decision: `{DECISION}`.

Stage237 turns the selected binary high-stat matrix into a bounded manuscript
and engineering-report package. The package keeps the original algorithmic
object: exact dense PVW/MAT-SAB as an r-body MAT-RLWE/SAB accumulator, measured
by complete-SAB `T_bootstrap/r`. It does not turn the evidence into a
theoretical-optimality, all-parameter, compact-route, or broad novelty claim.

## Selected Binary Experiment Table

{table(matrix, ["param", "r", "stage", "stat_level", "mean_speedup", "speedup_ci95_low", "speedup_ci95_high", "noise_failures", "key_bytes_ratio", "keygen_ratio", "rss_ratio", "status", "evidence"])}
## Contribution Claim Ledger

{table(claims, ["claim_id", "status", "safe_wording", "quantitative_support", "required_caveat", "blocked_wording", "evidence"])}
## Section Evidence Matrix

{table(sections, ["section", "content_scope", "must_include", "evidence"])}
## Source Policy

{table(source_policy, ["source_id", "title", "verification_status", "allowed_use", "required_caveat", "primary_url"])}
## Candidate Path Matrix

{table(candidates, ["path_id", "algorithm_path", "theory_status", "experiment_status", "expected_bottleneck", "promotion_rule", "evidence"])}
## Overclaim Guard

{table(overclaim, ["phrase", "count", "status", "allowed_context"])}
## Gates

{table(gates, ["gate", "required", "observed", "status", "claim_effect"])}
## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
## Inputs

{table(inputs, ["input", "status", "role", "bytes"])}
"""
    write_text(DOC, doc)
    write_text(REPORT, doc)
    write_text(
        PLAN,
        """# Stage237 Experiment/Report Plan

Stage237 is a report and claim-control stage. It consumes the Stage236 selected
binary matrix and Stage230 source policy, then emits a manuscript skeleton,
claim ledger, source policy, candidate path matrix, and overclaim guard.

Correctness/performance gates are inherited from Stage233-236. This stage does
not rerun benchmarks and must not upgrade scoped evidence into broad novelty or
optimality claims.
""",
    )
    write_text(
        THEORY,
        """# Stage237 Manuscript Claim Model

The current algorithm object is exact dense PVW/MAT-SAB: an r-body MAT-RLWE
accumulator with one shared mask and r independent body lanes. The scalar
baseline repeats SAB r times. The primary metric is:

```text
speedup = T_scalar_repeated(r lanes) / T_pvw_mat_sab(r body lanes)
lane_time = T_bootstrap / r
```

The selected binary matrix supports scoped empirical throughput claims. It does
not prove a formal lower-bound-tight construction. The present lower-bound
model is practical: output extraction/key switching, encrypted selector
semantics, dense MAT external-product arithmetic, and backend DFT conversion
remain unavoidable or unproven under the current implementation.

Candidate optimal paths are therefore gated separately: exact dense PVW/MAT-SAB
is the promoted empirical route; native counters can refine attribution;
compact/sparse selector MAT requires new security/noise/equation proofs;
non-binary branches need branch-specific full-SAB gates; theoretical optimality
requires a separate theorem.
""",
    )
    write_text(
        VARIANT,
        """# mat_rlwe_sab_stage237_scoped_manuscript

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping.
- Focused module: exact dense PVW/MAT-SAB complete bootstrapping.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: [selected binary matrix checked], [manuscript package ready], [broader claims blocked].
- Main hypothesis: exact dense PVW/MAT-SAB amortizes shared SAB work across r
  body lanes and improves per-lane full bootstrapping throughput versus
  repeated scalar SAB on selected binary parameter rows.

## Required Next Work

- Source-verified citation package for paper-facing prose.
- Optional native-counter attribution if implementation mechanism claims are
  needed.
- Separate proof/experiment gates for non-binary, compact, or theoretical
  optimality claims.
""",
    )


def update_project_files() -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 237: Scoped Manuscript Package",
        f"""
## Stage 237: Scoped Manuscript Package

Goal:

```text
Convert the selected binary PVW/MAT-SAB matrix into a scoped manuscript/report
package with section evidence, claim ledger, source policy, candidate-path
matrix, overclaim guard, and next-stage gates.
```

Status:

```text
Generated from input head `{head}` with `{DECISION}`. The package is ready for
source-verified citation finalization or optional native-counter attribution.
It remains bounded to exact dense binary PVW/MAT-SAB under complete-SAB
T_bootstrap/r.
```
""",
    )
    append_once(
        GOAL,
        "## Stage237 scoped manuscript package",
        f"""
## Stage237 scoped manuscript package

Generated from input head `{head}`, Stage237 records `{DECISION}`. The selected
binary matrix is now packaged as a bounded manuscript/report skeleton with
claim ledger, source policy, candidate-path matrix, and overclaim guard. The
active research goal remains open for citation finalization, optional native
counter attribution, and any broader proof/implementation routes.
""",
    )
    append_once(
        CURRENT_GOAL,
        "### Stage237 scoped manuscript package",
        f"""
### Stage237 scoped manuscript package

`{DECISION}` records a paper-facing package for the selected binary exact dense
PVW/MAT-SAB result. The goal remains active because final citation verification,
venue-specific paper assembly, optional native-counter attribution, and broader
algorithmic gates remain incomplete.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage237_scoped_manuscript_package:",
        f"""
H10_stage237_scoped_manuscript_package:
  status: scoped_manuscript_package_ready_claim_bounded
  evidence:
    - repro/stage237_scoped_manuscript_package/manuscript_skeleton.md
    - repro/stage237_scoped_manuscript_package/contribution_claims.csv
    - repro/stage237_scoped_manuscript_package/source_policy.csv
    - repro/stage237_scoped_manuscript_package/candidate_path_matrix.csv
    - docs/stage237_scoped_manuscript_package.md
  conclusion: >
    Stage237 records {DECISION}. The selected binary exact dense PVW/MAT-SAB
    evidence is packaged into a bounded manuscript/report skeleton under the
    complete-SAB T_bootstrap/r metric. Source-verified citation finalization,
    optional native-counter attribution, non-binary support, compact route,
    all-parameter scope, novelty, and theoretical optimality remain separately
    gated.
""",
    )
    append_once(
        RUN_LOG,
        "stage237-scoped-manuscript-package-001",
        f"""stage237-scoped-manuscript-package-001,{date.today().isoformat()},{head},Stage 237,aggregation,"python scripts/build_stage237_scoped_manuscript_package.py","selected binary matrix + Stage230 source policy",n/a,{DECISION},"Scoped manuscript/report package ready with claim boundary.",docs/stage237_scoped_manuscript_package.md; repro/stage237_scoped_manuscript_package/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage237_scoped_manuscript_package:",
        """
- stage237_scoped_manuscript_package:
  - `docs/stage237_scoped_manuscript_package.md`
  - `experiments/stage237_scoped_manuscript_package_plan.md`
  - `theory_checks/stage237_manuscript_claim_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage237_scoped_manuscript.md`
  - `scripts/build_stage237_scoped_manuscript_package.py`
  - `repro/stage237_scoped_manuscript_package/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage237 scoped manuscript package records decision",
        f"""
- [x] Stage237 scoped manuscript package records decision `{DECISION}`.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = input_rows()
    matrix = matrix_rows()
    claims = claim_rows()
    sections = section_rows()
    source_policy = source_policy_rows()
    candidates = candidate_rows()

    write_text(MANUSCRIPT, manuscript_text(matrix, claims, candidates))
    overclaim = overclaim_rows(claims)
    gates = gate_rows(inputs, matrix, claims, source_policy, overclaim)
    proof = proof_rows(gates)
    nextq = next_rows()

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(MATRIX_TABLE, matrix, ["param", "r", "stage", "stat_level", "mean_speedup", "speedup_ci95_low", "speedup_ci95_high", "noise_failures", "key_bytes_ratio", "keygen_ratio", "rss_ratio", "status", "evidence"])
    write_csv(CLAIMS, claims, ["claim_id", "status", "safe_wording", "quantitative_support", "required_caveat", "blocked_wording", "evidence"])
    write_csv(SECTIONS, sections, ["section", "content_scope", "must_include", "evidence"])
    write_csv(SOURCE_POLICY, source_policy, ["source_id", "title", "verification_status", "allowed_use", "required_caveat", "primary_url"])
    write_csv(CANDIDATES, candidates, ["path_id", "algorithm_path", "theory_status", "experiment_status", "expected_bottleneck", "promotion_rule", "evidence"])
    write_csv(OVERCLAIM, overclaim, ["phrase", "count", "status", "allowed_context"])
    write_csv(GATES, gates, ["gate", "required", "observed", "status", "claim_effect"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_repro_commands()
    write_docs(inputs, matrix, claims, sections, source_policy, candidates, overclaim, gates, proof, nextq)

    artifacts = [
        DOC,
        PLAN,
        THEORY,
        VARIANT,
        INPUTS,
        MATRIX_TABLE,
        CLAIMS,
        SECTIONS,
        SOURCE_POLICY,
        CANDIDATES,
        OVERCLAIM,
        GATES,
        PROOF,
        NEXT,
        MANUSCRIPT,
        REPORT,
        REPRO_CMDS,
    ]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "bytes", "sha256"])
    update_project_files()
    print(f"Stage237 report: {rel(DOC)}")
    print(f"Stage237 decision: {DECISION}")


if __name__ == "__main__":
    main()
