#!/usr/bin/env python3
"""Stage164: representation-changing closure route gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage164_representation_closure_route"

SUMMARY_CSV = OUT_DIR / "summary.csv"
EVIDENCE_CSV = OUT_DIR / "evidence_inputs.csv"
CANDIDATE_CSV = OUT_DIR / "candidate_matrix.csv"
DIMENSION_CSV = OUT_DIR / "dimension_model.csv"
NEXT_QUEUE_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage164_representation_closure_route.md"
PLAN_MD = ROOT / "experiments" / "stage164_representation_closure_route_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage164_representation_closure_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_representation_closure_route.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

INPUTS = {
    "stage139": ROOT / "repro" / "stage139_compact_closure_audit" / "summary.csv",
    "stage156": ROOT / "repro" / "stage156_lazy_dft_closure_gate" / "summary.csv",
    "stage160": ROOT / "repro" / "stage160_post_fusion_frontier" / "summary.csv",
    "stage162": ROOT / "repro" / "stage162_materialization_count_feasibility" / "summary.csv",
    "stage163": ROOT / "repro" / "stage163_from_dft_batching_microbench" / "summary.csv",
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def decision_from(path: Path) -> str:
    for row in read_csv(path):
        if row.get("gate", "").endswith("decision"):
            return row.get("status", "")
    return "MISSING"


def build_evidence() -> List[Dict[str, str]]:
    rows = []
    for name, path in INPUTS.items():
        rows.append({
            "source": name,
            "path": rel(path),
            "present": "yes" if path.exists() else "no",
            "decision": decision_from(path) if path.exists() else "MISSING",
        })
    return rows


def build_dimension_model() -> List[Dict[str, str]]:
    rows = []
    for r in (2, 4, 6, 8):
        dense_terms = (1 + r) * (1 + r)
        pvw_state_polys = 1 + r
        diagonal_compact_masks = r
        rows.append({
            "r": str(r),
            "pvw_state_polys": str(pvw_state_polys),
            "generic_dense_selector_terms_per_level": str(dense_terms),
            "diagonal_compact_masks": str(diagonal_compact_masks),
            "generic_exact_term_lower_bound": str(dense_terms),
            "interpretation": "A generic encrypted MAT selector is a full linear map from 1+r decomposed input rows to 1+r output polynomials.",
        })
    return rows


def build_candidates() -> List[Dict[str, str]]:
    return [
        {
            "candidate": "same_format_materialization_count_reduction",
            "status": "CLOSED",
            "blocking_evidence": decision_from(INPUTS["stage162"]),
            "mechanism_tested": "Reduce from_DFT calls without changing torus-input accumulator/API.",
            "research_action": "Do not reopen unless the accumulator representation changes.",
        },
        {
            "candidate": "from_dft_backend_batching",
            "status": "NEUTRAL_NOT_PROMOTED",
            "blocking_evidence": decision_from(INPUTS["stage163"]),
            "mechanism_tested": "Use component-major batching to lower per-call materialization wall time.",
            "research_action": "Keep existing fused-add backend; do not integrate batching.",
        },
        {
            "candidate": "naive_lazy_dft_accumulator",
            "status": "REJECTED",
            "blocking_evidence": decision_from(INPUTS["stage156"]),
            "mechanism_tested": "Keep only DFT accumulator outputs across CMUX steps.",
            "research_action": "Rejected because the next MAT EP needs nonlinear coefficient-domain decomposition.",
        },
        {
            "candidate": "diagonal_compact_direct_sab_state",
            "status": "REJECTED",
            "blocking_evidence": decision_from(INPUTS["stage139"]),
            "mechanism_tested": "Insert compact diagonal/lane-local output directly as a PVW_TMLWE SAB accumulator.",
            "research_action": "Rejected because lane-specific masks violate the shared-mask PVW invariant.",
        },
        {
            "candidate": "closed_full_mat_kernel_and_decompose_dft",
            "status": "VALID_CURRENT_EXECUTABLE_ROUTE",
            "blocking_evidence": "Stage160 dominant component remains mat_ep_plus_subdecomp; Stage140 lower bound keeps closed full-MAT as valid state.",
            "mechanism_tested": "Preserve PVW_TMLWE state and optimize decompose/DFT/addmul constant factors.",
            "research_action": "Run a closed full-MAT streaming/decompose-DFT microbench before production changes.",
        },
        {
            "candidate": "structured_shared_output_compact_keygen",
            "status": "OPEN_THEORY_KEYGEN_REQUIRED",
            "blocking_evidence": "Generic dense selector exactness needs (1+r)^2 terms per level; fewer terms require a new structured key distribution/proof.",
            "mechanism_tested": "Design compact selector rows that output one shared mask plus r bodies.",
            "research_action": "Only proceed after an algebra/keygen/noise proof gate; no production SAB integration yet.",
        },
    ]


def build_next_queue() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "165",
            "name": "closed full-MAT decompose/DFT streaming microbench",
            "entry_condition": "Stage164 selects valid current-state executable route.",
            "gate": "Compare current all-row dec_dft plus MAT-aware AVX addmul against row-streamed dec_dft/addmul without losing exact DFT output.",
            "failure_rule": "If streaming loses to current tiled AVX, close this route and keep current full-MAT kernel.",
        },
        {
            "priority": "P1",
            "stage": "166",
            "name": "shared-output compact algebra/keygen proof gate",
            "entry_condition": "Only if pursuing count/key-size reduction beyond full-MAT constant factors.",
            "gate": "Prove a compact selector can produce one shared mask and r bodies with acceptable noise/security.",
            "failure_rule": "If generic dense exactness or noise proof fails, do not integrate compact SAB.",
        },
        {
            "priority": "P2",
            "stage": "167",
            "name": "native current r=6 counter refresh",
            "entry_condition": "Native Linux perf host available.",
            "gate": "Measure current post-fusion r=6 retired loads/stores/FMA/cycles for MAT EP and from_DFT attribution.",
            "failure_rule": "If only WSL proxy is available, keep optimality claims blocked.",
        },
    ]


def decide(evidence: List[Dict[str, str]]) -> str:
    if any(row["present"] != "yes" for row in evidence):
        return "BLOCKED_STAGE164_MISSING_PRIOR_EVIDENCE"
    return "PASS_STAGE164_REPRESENTATION_ROUTE_TO_CLOSED_FULL_MAT_STREAMING_GATE"


def build_summary(decision: str, evidence: List[Dict[str, str]]) -> List[Dict[str, str]]:
    missing = [row["source"] for row in evidence if row["present"] != "yes"]
    return [
        {
            "gate": "stage164_evidence_inputs",
            "status": "PASS" if not missing else "BLOCKED",
            "metric": "missing_sources",
            "value": ";".join(missing) if missing else "none",
            "evidence": rel(EVIDENCE_CSV),
            "detail": "Stage164 consumes the compact closure, lazy DFT, post-fusion profile, materialization count, and backend batching gates.",
            "next_action": "Repair missing evidence before routing representation work.",
        },
        {
            "gate": "stage164_dimension_model",
            "status": "PASS",
            "metric": "generic_exact_selector_lower_bound",
            "value": "(1+r)^2 per gadget level",
            "evidence": rel(DIMENSION_CSV),
            "detail": "A generic exact MAT selector is a full linear map; compact term reduction needs a structured keygen proof.",
            "next_action": "Do not claim compact exactness from isolated lane-local kernels.",
        },
        {
            "gate": "stage164_candidate_matrix",
            "status": "PASS",
            "metric": "selected_candidate",
            "value": "closed_full_mat_kernel_and_decompose_dft",
            "evidence": rel(CANDIDATE_CSV),
            "detail": "Closed routes and open high-risk routes are separated from the next executable route.",
            "next_action": "Run Stage165 closed full-MAT streaming/decompose-DFT microbench.",
        },
        {
            "gate": "stage164_decision",
            "status": decision,
            "metric": "next_executable_stage",
            "value": "Stage165",
            "evidence": rel(NEXT_QUEUE_CSV),
            "detail": "Stage164 prevents another theory loop by selecting a concrete microbench before production changes.",
            "next_action": "Implement Stage165 as an isolated exact-output kernel gate.",
        },
    ]


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() and path.is_file() else "",
            "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def write_docs(
    decision: str,
    summary: List[Dict[str, str]],
    evidence: List[Dict[str, str]],
    candidates: List[Dict[str, str]],
    dimensions: List[Dict[str, str]],
    next_queue: List[Dict[str, str]],
) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    evidence_fields = ["source", "path", "present", "decision"]
    candidate_fields = ["candidate", "status", "blocking_evidence", "mechanism_tested", "research_action"]
    dimension_fields = [
        "r", "pvw_state_polys", "generic_dense_selector_terms_per_level",
        "diagonal_compact_masks", "generic_exact_term_lower_bound", "interpretation",
    ]
    next_fields = ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"]

    write_text_lf(OUT_MD, f"""# Stage164 Representation Closure Route

Decision: `{decision}`.

Stage164 closes the immediate post-Stage163 routing question. The current code
does not have a ready representation-changing path that both reduces
materialization count and preserves the PVW shared-mask accumulator invariant.
The next executable route is a closed full-MAT decompose/DFT streaming
microbench, not SAB production integration.

## Gate Summary

{table(summary, summary_fields)}

## Evidence Inputs

{table(evidence, evidence_fields)}

## Candidate Matrix

{table(candidates, candidate_fields)}

## Dimension Model

{table(dimensions, dimension_fields)}

## Next Queue

{table(next_queue, next_fields)}
""")

    write_text_lf(PLAN_MD, """# Stage164 Validation Plan

Goal: prevent the MAT-RLWE SAB optimization loop from reopening already closed
representation ideas, and select one concrete next executable gate.

Inputs:

- Stage139 compact closure audit;
- Stage156 lazy-DFT closure gate;
- Stage160 post-fusion profile;
- Stage162 materialization-count feasibility;
- Stage163 from_DFT backend batching microbench.

Acceptance:

- all prior evidence must be present;
- closed, neutral, rejected, open-proof, and executable candidates must be
  separated;
- the next stage must be a concrete gate with failure criteria.
""")

    write_text_lf(THEORY_MD, """# Stage164 Representation Closure Model

For a PVW/MAT accumulator with one shared mask and `r` bodies, a generic dense
MAT selector maps `1+r` decomposed input rows to `1+r` output polynomials. This
is a full linear map with `(1+r)^2` independent selector terms per gadget level.

Any compact route using fewer independent terms must either:

1. prove that the key distribution intentionally constrains the selector while
   preserving security and noise bounds; or
2. accept that it is not exact for the generic dense selector.

Stage139 already shows that diagonal compact output is not a direct PVW_TMLWE
state because masks become lane-specific. Stage156 rejects DFT-only persistence
because decomposition is nonlinear. Stage162 closes same-format materialization
count reduction, and Stage163 rejects component-major backend batching as a
production candidate.

Therefore the non-speculative next step is to optimize the valid closed
full-MAT path at the decompose/DFT/addmul boundary, with exact DFT output as
the correctness gate.
""")

    write_text_lf(VARIANT_MD, f"""# MAT-RLWE SAB Representation Closure Route

Stage164 is a route-selection artifact, not a new production algorithm.

Selected next executable route:

```text
closed_full_mat_kernel_and_decompose_dft -> Stage165 microbench
```

Rejected or non-promoted routes:

- same-format materialization count reduction;
- component-major from_DFT backend batching;
- naive lazy DFT accumulator;
- direct diagonal compact SAB state.

Open but not implementation-ready:

- structured shared-output compact keygen. This needs algebra, security, and
  noise proof gates before code integration.

Decision: `{decision}`.
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 164: Representation Closure Route", f"""
## Stage 164: Representation Closure Route

Goal:

```text
Combine the compact-closure, lazy-DFT, materialization-count, and backend
batching evidence to select the next non-speculative representation route.
```

Status:

```text
Completed. Stage164 records {decision}. It routes next to a closed full-MAT
decompose/DFT streaming microbench and keeps structured compact keygen work
behind algebra/security/noise proof gates.
```
""")

    append_once(GOAL_MD, "Stage164 records representation closure routing", f"""
Stage164 records representation closure routing after Stage163. Decision:
`{decision}`. It prevents a theory loop by closing already rejected routes and
selecting Stage165 closed full-MAT decompose/DFT streaming as the next
executable gate.
""")

    append_once(CURRENT_GOAL_MD, "68. Treat Stage164 as the representation closure route", f"""
68. Treat Stage164 as the representation closure route:
    `{decision}`. It does not claim a new SAB algorithm; it selects Stage165 as
    the next exact-output microbench and keeps structured compact keygen behind
    proof gates.
""")

    append_once(HYPOTHESIS_YAML, "id: H88_representation_closure_route", f"""
  - id: H88_representation_closure_route
    statement: >
      After same-format count reduction and backend batching are closed or
      neutral, the next executable PVW/MAT-SAB optimization should preserve the
      closed full-MAT state and test decompose/DFT/addmul constant factors
      before any compact-state SAB integration.
    mechanism: >
      Generic exact compact selector reduction conflicts with the full
      `(1+r)^2` dense selector map unless a new structured keygen/security/noise
      proof is supplied; current compact diagonal outputs are not PVW_TMLWE
      closed.
    status: stage164_representation_closure_route
    evidence: docs/stage164_representation_closure_route.md; experiments/stage164_representation_closure_route_plan.md; theory_checks/stage164_representation_closure_model.md; repro/stage164_representation_closure_route/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - prior closure evidence is missing
      - a rejected compact or lazy-DFT route is reopened without a new invariant proof
      - Stage165 is skipped and production SAB code is changed without exact-output microbench evidence
""")

    append_once(RUN_LOG, "stage164-representation-closure-route-001", f"""
stage164-representation-closure-route-001,2026-07-03,{git_head()},Stage 164,analysis,python scripts/build_stage164_representation_closure_route.py,Stage139/156/160/162/163 evidence,none,{decision},Representation-changing closure route gate.,repro/stage164_representation_closure_route
""")

    append_once(MANIFEST, "stage164_representation_closure_route", f"""
- stage164_representation_closure_route: `{decision}`
  - `docs/stage164_representation_closure_route.md`
  - `experiments/stage164_representation_closure_route_plan.md`
  - `theory_checks/stage164_representation_closure_model.md`
  - `algorithm_variants/mat_rlwe_sab_representation_closure_route.md`
  - `repro/stage164_representation_closure_route/`
""")

    append_once(CHECKLIST, "Stage164 representation closure route pack recorded", """
- [x] Stage164 representation closure route pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    evidence = build_evidence()
    dimensions = build_dimension_model()
    candidates = build_candidates()
    next_queue = build_next_queue()
    decision = decide(evidence)
    summary = build_summary(decision, evidence)

    write_csv(EVIDENCE_CSV, evidence, ["source", "path", "present", "decision"])
    write_csv(DIMENSION_CSV, dimensions, [
        "r", "pvw_state_polys", "generic_dense_selector_terms_per_level",
        "diagonal_compact_masks", "generic_exact_term_lower_bound", "interpretation",
    ])
    write_csv(CANDIDATE_CSV, candidates, [
        "candidate", "status", "blocking_evidence", "mechanism_tested", "research_action",
    ])
    write_csv(NEXT_QUEUE_CSV, next_queue, [
        "priority", "stage", "name", "entry_condition", "gate", "failure_rule",
    ])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(decision, summary, evidence, candidates, dimensions, next_queue)
    update_global_docs(decision)
    artifact_index([
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, EVIDENCE_CSV,
        CANDIDATE_CSV, DIMENSION_CSV, NEXT_QUEUE_CSV, Path(__file__),
    ])

    print(decision)
    for row in next_queue:
        print(f"{row['priority']} Stage{row['stage']}: {row['name']}")


if __name__ == "__main__":
    main()
