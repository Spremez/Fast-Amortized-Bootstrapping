#!/usr/bin/env python3
"""Build Stage315 backend-IFFT admission artifacts.

This stage is deliberately a route gate, not a new performance claim.  It
converts the Stage314 closeout into a concrete next implementation target and
records why local digit, wrapper materialization, and duplicate schedule
variants should not be pursued before a real backend-IFFT preflight.
"""

from __future__ import annotations

import csv
import hashlib
import math
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage315_backend_ifft_admission"
DOC = ROOT / "docs" / "stage315_backend_ifft_admission.md"
THEORY = ROOT / "theory_checks" / "stage315_backend_ifft_budget.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage315_backend_ifft_candidate.md"
PLAN = ROOT / "experiments" / "stage315_backend_ifft_validation_plan.md"
BUILDER = ROOT / "scripts" / "build_stage315_backend_ifft_admission.py"

SUMMARY = OUT / "admission_summary.csv"
THRESHOLDS = OUT / "component_thresholds.csv"
CANDIDATES = OUT / "candidate_cards.csv"
ANCHORS = OUT / "code_anchor_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage315_report.md"
ARTIFACT = OUT / "artifact_index.csv"

STAGE314 = ROOT / "repro" / "stage314_local_digit_closeout" / "stage314_summary.csv"
STAGE310 = ROOT / "repro" / "stage310_ifft_rows_scaling_bench" / "bench_summary.csv"
STAGE303 = ROOT / "repro" / "stage303_param_matrix_highstat" / "perf_summary.csv"
STAGE313 = ROOT / "repro" / "stage313_narrow32_profile_attribution" / "profile_summary.csv"
STAGE88 = ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "full_sab_repeated.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE315_BACKEND_IFFT_ADMISSION_SELECT_STAGE316_ABI_PREFLIGHT"
DECISION_FAIL = "FAIL_STAGE315_BACKEND_IFFT_ADMISSION_EVIDENCE_MISSING"
FULL_SAB_GATE = 1.02


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip())
        if not text.endswith("\n"):
            f.write("\n")


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def first(rows: List[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def stage_decision(path: Path) -> str:
    rows = read_csv(path)
    return rows[0].get("decision", "MISSING") if rows else "MISSING"


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append(
            "| "
            + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields)
            + " |"
        )
    return "\n".join(out)


def component_reduction_required(share: float, target_speedup: float) -> float:
    if share <= 0.0 or target_speedup <= 1.0:
        return 0.0
    return (1.0 - 1.0 / target_speedup) / share


def projected_speedup(share: float, reduction: float) -> float:
    if share <= 0.0:
        return 1.0
    remaining = 1.0 - share * reduction
    if remaining <= 0.0:
        return math.inf
    return 1.0 / remaining


def append_run_log(decision: str) -> None:
    run_id = "stage315-backend-ifft-admission-001"
    if run_id in read_text(RUN_LOG):
        return
    fields: List[str] = []
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
    if not fields:
        fields = [
            "run_id",
            "date",
            "git_ref",
            "stage",
            "backend",
            "command",
            "config",
            "seed",
            "status",
            "summary",
            "artifacts",
        ]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": git_head(),
        "commit_or_state": git_head(),
        "stage": "Stage 315",
        "backend": "analysis",
        "command": "python3 scripts/build_stage315_backend_ifft_admission.py",
        "config": "Stage314 route gate plus Stage310/303/313 evidence",
        "params": "BINARY SET_2_3_2048 r=4 include-zero primary endpoint T_bootstrap/r",
        "seed": "n/a",
        "status": decision,
        "summary": (
            "Stage315 selects a backend-IFFT ABI preflight and blocks duplicate "
            "local digit/wrapper/schedule variants without a >=1.02 full-SAB budget."
        ),
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(PROOF)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        data = path.read_bytes()
        rows.append(
            {
                "path": rel(path),
                "bytes": str(len(data)),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    stage314_decision = stage_decision(STAGE314)
    stage310_decision = stage_decision(STAGE310)
    stage313_summary = read_csv(STAGE313)
    direct = first(stage313_summary, "variant", "direct_profile")
    stage303_rows = read_csv(STAGE303)
    stage303_direct = first(stage303_rows, "variant", "perf_direct_dft")
    stage303_compare = first(stage303_rows, "variant", "comparison")
    stage88_backend = first(read_csv(STAGE88), "variant", "backend")
    stage88_wrapper = first(read_csv(STAGE88), "variant", "wrapper")

    body_full = fnum(direct.get("body_full_us_sum"))
    digit = fnum(direct.get("digit_us"))
    ifft = fnum(direct.get("ifft_us"))
    dense = fnum(direct.get("split_dense_us"))
    mat_ep = fnum(direct.get("body_mat_ep_us_sum"))

    shares = {
        "digit_to_double": digit / body_full if body_full else 0.0,
        "spqlios_ifft": ifft / body_full if body_full else 0.0,
        "dense_mat_addmul": dense / body_full if body_full else 0.0,
        "mat_ep_lifecycle": mat_ep / body_full if body_full else 0.0,
    }

    thresholds = []
    for component, share in shares.items():
        needed = component_reduction_required(share, FULL_SAB_GATE)
        thresholds.append(
            {
                "component": component,
                "share_of_body_profile": f"{share:.6f}",
                "component_reduction_required_for_1p02_body": f"{needed:.6f}",
                "projected_speedup_if_10pct_reduction": f"{projected_speedup(share, 0.10):.6f}",
                "projected_speedup_if_25pct_reduction": f"{projected_speedup(share, 0.25):.6f}",
                "stage315_interpretation": (
                    "admit only with concrete implementation budget"
                    if component != "mat_ep_lifecycle"
                    else "large enough only if candidate affects lifecycle, not one small subcomponent"
                ),
            }
        )
    write_csv(
        THRESHOLDS,
        thresholds,
        [
            "component",
            "share_of_body_profile",
            "component_reduction_required_for_1p02_body",
            "projected_speedup_if_10pct_reduction",
            "projected_speedup_if_25pct_reduction",
            "stage315_interpretation",
        ],
    )

    backend_ifft_needed = component_reduction_required(shares["spqlios_ifft"], FULL_SAB_GATE)
    evidence_ok = (
        stage314_decision.startswith("PASS_STAGE314")
        and stage310_decision.startswith("PASS_STAGE310")
        and bool(direct)
    )
    decision = DECISION if evidence_ok else DECISION_FAIL

    summary_rows = [
        {
            "decision": decision,
            "primary_metric": "complete_sab_T_bootstrap_over_r",
            "stage314_route": stage314_decision,
            "stage310_ifft_route": stage310_decision,
            "stage303_direct_dft_vs_control": stage303_compare.get(
                "direct_dft_vs_selected_control_mean", ""
            ),
            "stage303_direct_dft_speedup_vs_repeated_scalar": stage303_compare.get(
                "speedup_vs_repeated_scalar_mean", ""
            )
            or stage303_direct.get(
                "speedup_vs_repeated_scalar_mean", ""
            ),
            "stage313_ifft_share_of_body": f"{shares['spqlios_ifft']:.6f}",
            "stage313_mat_ep_share_of_body": f"{shares['mat_ep_lifecycle']:.6f}",
            "ifft_reduction_required_for_1p02_body": f"{backend_ifft_needed:.6f}",
            "selected_next_stage": "stage316_spqlios_ifft_batch_abi_preflight",
        }
    ]
    write_csv(
        SUMMARY,
        summary_rows,
        [
            "decision",
            "primary_metric",
            "stage314_route",
            "stage310_ifft_route",
            "stage303_direct_dft_vs_control",
            "stage303_direct_dft_speedup_vs_repeated_scalar",
            "stage313_ifft_share_of_body",
            "stage313_mat_ep_share_of_body",
            "ifft_reduction_required_for_1p02_body",
            "selected_next_stage",
        ],
    )

    candidates = [
        {
            "candidate_id": "H315-C1-spqlios-batch-ifft-abi",
            "status": "SELECT_FOR_STAGE316_ABI_PREFLIGHT",
            "mechanism": (
                "Replace the current rows independent `ifft(proc->tables_reverse, row)` "
                "inside direct sub-DTF materialization with an isolated backend batch "
                "ABI/prototype that computes the same rows."
            ),
            "budget": (
                f"Stage313 IFFT share={shares['spqlios_ifft']:.6f}; requires "
                f">={backend_ifft_needed:.6f} component reduction for a 1.02 body budget."
            ),
            "why_not_theory_loop": (
                "Stage316 must produce code-level ABI, isolated correctness, and "
                "microbench evidence before SAB integration."
            ),
        },
        {
            "candidate_id": "H315-C2-local-digit-microvariant",
            "status": "CLOSED_BY_STAGE314",
            "mechanism": "Further AVX digit conversion tweaks without broader lifecycle change.",
            "budget": "Stage314 projected observed narrow32-only body gain is 1.007439.",
            "why_not_theory_loop": "No new implementation unless a pre-implementation full-SAB budget is >=1.02.",
        },
        {
            "candidate_id": "H315-C3-wrapper-from-dft-add",
            "status": "ALREADY_IN_CURRENT_BASELINE",
            "mechanism": "Use `SAB_PVW_BACKEND_FROM_DFT_ADD` / backend add during materialization.",
            "budget": (
                "Stage312/313 common flags already include SAB_PVW_BACKEND_FROM_DFT_ADD=true; "
                f"old Stage88 r=6 backend mean={stage88_backend.get('mean_speedup_vs_scalar', '')} "
                f"vs wrapper mean={stage88_wrapper.get('mean_speedup_vs_scalar', '')}."
            ),
            "why_not_theory_loop": "Do not re-open as a new candidate; it is part of current r=4 direct baseline.",
        },
        {
            "candidate_id": "H315-C4-lazy-dft-schedule-state",
            "status": "DEFER_NO_COUNT_REDUCTION_PROOF",
            "mechanism": "Keep CMUX outputs in DFT form across butterfly windows.",
            "budget": "No admitted budget because next SAB operations consume torus-domain state.",
            "why_not_theory_loop": "Requires a new state invariant and materialization-count proof before code.",
        },
        {
            "candidate_id": "H315-C5-dense-mat-avx-rewrite",
            "status": "DEFER",
            "mechanism": "Rewrite dense MAT addmul layout/register tiling.",
            "budget": (
                f"Stage313 dense share={shares['dense_mat_addmul']:.6f}; "
                "reopen only with assembly/counter hypothesis and full-SAB budget."
            ),
            "why_not_theory_loop": "Previous dense/FMA directions were near-neutral; not the next bottleneck route.",
        },
    ]
    write_csv(
        CANDIDATES,
        candidates,
        ["candidate_id", "status", "mechanism", "budget", "why_not_theory_loop"],
    )

    anchors = [
        {
            "anchor": "direct_sub_dft_ifft_loop",
            "file": "src/mosfhet/src/mattrgsw.c",
            "lines": "1110-1163",
            "fact": "direct sub-DTF materialization converts each gadget row to double and calls `ifft` per row.",
            "stage315_use": "Stage316 target implementation boundary.",
        },
        {
            "anchor": "r4_rowbatch_digit_existing",
            "file": "src/mosfhet/src/mattrgsw.c",
            "lines": "1039-1107",
            "fact": "r=4 row-batched digit conversion already exists, but still loops `ifft` per row.",
            "stage315_use": "Shows remaining non-digit backend work.",
        },
        {
            "anchor": "pvw_cmux_materialization",
            "file": "src/sab_pvw.c",
            "lines": "615-655",
            "fact": "CMUX materializes MAT EP output and may use backend from_DFT_add.",
            "stage315_use": "This path is already in the current direct baseline, not the new target.",
        },
        {
            "anchor": "pvm_from_dft_add_backend_flag",
            "file": "src/mosfhet/src/pvwtmlwe.c",
            "lines": "763-781",
            "fact": "`SAB_PVW_BACKEND_FROM_DFT_ADD` calls `polynomial_DFT_to_torus_add`.",
            "stage315_use": "Records why wrapper materialization is not selected again.",
        },
        {
            "anchor": "spqlios_reverse_transform_api",
            "file": "src/mosfhet/src/polynomial.c",
            "lines": "373-379,435-465",
            "fact": "current torus-to-DFT array wrapper still iterates per row; no real batch IFFT API is exposed.",
            "stage315_use": "Stage316 must operate at backend ABI/prototype level.",
        },
    ]
    write_csv(ANCHORS, anchors, ["anchor", "file", "lines", "fact", "stage315_use"])

    proof = [
        {
            "gate": "G1_stage314_route",
            "status": "PASS" if stage314_decision.startswith("PASS_STAGE314") else "FAIL",
            "metric": "Stage314 decision",
            "value": stage314_decision,
            "interpretation": "Local digit variants must be closed before choosing Stage315.",
        },
        {
            "gate": "G2_stage310_backend_requirement",
            "status": "PASS" if stage310_decision.startswith("PASS_STAGE310") else "FAIL",
            "metric": "Stage310 decision",
            "value": stage310_decision,
            "interpretation": "C-wrapper IFFT is insufficient; backend ABI preflight is required.",
        },
        {
            "gate": "G3_budget_materiality",
            "status": "PASS" if backend_ifft_needed <= 0.12 else "REVIEW",
            "metric": "required IFFT component reduction for 1.02 body",
            "value": f"{backend_ifft_needed:.6f}",
            "interpretation": "Stage316 must show at least this isolated IFFT reduction before SAB integration.",
        },
        {
            "gate": "G4_duplicate_route_blocked",
            "status": "PASS",
            "metric": "backend from_DFT_add",
            "value": "already in Stage312/313 common flags",
            "interpretation": "Do not claim an old materialization flag as new work.",
        },
        {
            "gate": "G5_primary_metric",
            "status": "PASS",
            "metric": "metric",
            "value": "T_bootstrap/r",
            "interpretation": "All future comparisons must be amortized per processed body/lane.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Controls Stage316.",
        },
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])

    write_csv(
        NEXT,
        [
            {
                "priority": "P0",
                "stage": "stage316_spqlios_ifft_batch_abi_preflight",
                "input": decision,
                "task": (
                    "Prototype or statically reject a backend batch-IFFT ABI for the "
                    "rows=k+r=5 direct sub-DTF path, outside full SAB first."
                ),
                "gate": (
                    f"isolated correctness plus >= {backend_ifft_needed:.6f} IFFT component "
                    "reduction, then complete SAB T_bootstrap/r A/B"
                ),
            }
        ],
        ["priority", "stage", "input", "task", "gate"],
    )

    report = (
        "# Stage315 Backend IFFT Admission\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage315 converts the Stage314 closeout into one executable next route. "
        "The primary endpoint remains complete SAB `T_bootstrap/r`, i.e. "
        "bootstrapping time divided by the number of independent PVW body lanes "
        "processed by one MAT/PVW bootstrapping call.\n\n"
        "## Admission Summary\n\n"
        + table(
            summary_rows,
            [
                "decision",
                "primary_metric",
                "stage310_ifft_route",
                "stage313_ifft_share_of_body",
                "ifft_reduction_required_for_1p02_body",
                "selected_next_stage",
            ],
        )
        + "\n\n## Component Thresholds\n\n"
        + table(
            thresholds,
            [
                "component",
                "share_of_body_profile",
                "component_reduction_required_for_1p02_body",
                "projected_speedup_if_10pct_reduction",
                "projected_speedup_if_25pct_reduction",
            ],
        )
        + "\n\n## Candidate Selection\n\n"
        + table(candidates, ["candidate_id", "status", "mechanism", "budget"])
        + "\n\n## Code Anchors\n\n"
        + table(anchors, ["anchor", "file", "lines", "fact", "stage315_use"])
        + "\n\n## Proof Gate\n\n"
        + table(proof, ["gate", "status", "metric", "value", "interpretation"])
        + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)

    write_text(
        THEORY,
        f"""# Stage315 Backend IFFT Budget

The project comparison dimension is `T_bootstrap/r`, not raw one-call latency
alone.  For r independent LUT/SAB lanes, the scalar baseline is repeated scalar
SAB and the PVW/MAT endpoint is one r-body SAB call divided by r.

The current r=4 direct path already includes backend FromDFT-add materialization
and direct sub-DTF.  Stage313 attributes the direct profile as:

- MAT EP lifecycle share of body: {shares['mat_ep_lifecycle']:.6f}
- digit-to-double share of body: {shares['digit_to_double']:.6f}
- SPQLIOS IFFT share of body: {shares['spqlios_ifft']:.6f}
- dense MAT addmul share of body: {shares['dense_mat_addmul']:.6f}

For a component with body share `s`, reducing only that component by `x` gives
`speedup = 1 / (1 - s*x)`.  To clear the Stage314 admission gate of 1.02x body
budget, the SPQLIOS IFFT component must shrink by at least
{backend_ifft_needed:.6f}.  A 10% IFFT reduction projects to
{projected_speedup(shares['spqlios_ifft'], 0.10):.6f}, while a 25% reduction
projects to {projected_speedup(shares['spqlios_ifft'], 0.25):.6f}.

Therefore Stage316 is admitted only as a backend ABI/prototype preflight:
produce isolated correctness and IFFT microbench evidence before touching the
full SAB path.  If the backend cannot plausibly clear the IFFT reduction gate,
stop and return to higher-level schedule candidates with an explicit
materialization-count proof.
""",
    )

    write_text(
        VARIANT,
        f"""# Stage315 Candidate: SPQLIOS Batch IFFT ABI

Status: `{decision}`.

## Candidate

`H315-C1-spqlios-batch-ifft-abi` targets the rows=k+r=5 direct sub-DTF path in
`mat_trgsw_sub_decompose_DFT_direct`.  The candidate is not another digit
conversion tweak and not another wrapper around `pvmtmlwe_from_DFT_add`; those
routes are either closed or already part of the current direct baseline.

## Algorithmic Delta

The algebra is unchanged.  The implementation should replace:

```text
for row in rows:
    digit[row] = gadget_decompose(lhs[row], rhs[row])
    ifft(tables_reverse, digit[row])
```

with an isolated backend routine that returns the same transformed rows:

```text
batch_digit_ifft_rows5(tables_reverse, rows)
```

or proves that no such backend API can meet the budget on this backend.

## Admission Gate For Implementation

- isolated correctness against the current per-row `ifft`;
- at least {backend_ifft_needed:.6f} reduction in the IFFT component, or an
  equivalent full-SAB budget above 1.02 before SAB integration;
- full SAB `T_bootstrap/r` A/B only after the isolated gate passes;
- scalar SAB default path unchanged.
""",
    )

    write_text(
        PLAN,
        f"""# Stage315 Validation Plan For Stage316

1. Audit SPQLIOS reverse-transform ABI and assembly entry points.
2. Decide whether a rows=5 batch ABI can be prototyped without changing
   ciphertext semantics or key format.
3. If feasible, implement an isolated Stage316 benchmark outside SAB first.
4. Required Stage316 gate: correctness against current per-row `ifft`, plus
   >= {backend_ifft_needed:.6f} isolated IFFT component reduction.
5. Only then run full SAB `T_bootstrap/r` A/B.
6. If the backend gate fails, record the negative result and move to a
   schedule-level candidate only with a concrete materialization-count proof.
""",
    )

    write_text(
        COMMANDS,
        """# Stage315 Reproduction Commands

```bash
python3 scripts/build_stage315_backend_ifft_admission.py
```
""",
    )

    append_once(
        ROADMAP,
        "## Stage 315: Backend IFFT Admission",
        "\n## Stage 315: Backend IFFT Admission\n\n"
        "Goal: select the next non-duplicate route after local digit closeout.\n\n"
        f"Status: `{decision}`.\n",
    )
    append_once(
        GOAL,
        "<!-- stage315-backend-ifft-admission -->",
        "\n<!-- stage315-backend-ifft-admission -->\n"
        "### Stage315 backend IFFT admission\n\n"
        f"`{decision}` selects Stage316 SPQLIOS batch-IFFT ABI preflight and "
        "keeps the primary metric as complete SAB `T_bootstrap/r`.\n",
    )
    append_once(
        HYPOTHESES,
        "H315_backend_ifft_admission:",
        "\nH315_backend_ifft_admission:\n"
        f"  status: {decision}\n"
        "  primary_metric: complete_sab_T_bootstrap_over_r\n"
        "  evidence:\n"
        "    - repro/stage315_backend_ifft_admission/admission_summary.csv\n"
        "    - repro/stage315_backend_ifft_admission/component_thresholds.csv\n"
        "    - repro/stage315_backend_ifft_admission/candidate_cards.csv\n"
        "    - repro/stage315_backend_ifft_admission/proof_gate.csv\n"
        "  conclusion: >\n"
        "    Stage315 selects a backend-IFFT ABI preflight as the next executable\n"
        "    route and blocks duplicate local digit/materialization wrapper work\n"
        "    without a projected full-SAB budget above 1.02.\n",
    )
    append_once(
        MANIFEST,
        "- stage315_backend_ifft_admission:",
        "\n- stage315_backend_ifft_admission:\n"
        "  - `docs/stage315_backend_ifft_admission.md`\n"
        "  - `theory_checks/stage315_backend_ifft_budget.md`\n"
        "  - `algorithm_variants/mat_rlwe_sab_stage315_backend_ifft_candidate.md`\n"
        "  - `experiments/stage315_backend_ifft_validation_plan.md`\n"
        "  - `scripts/build_stage315_backend_ifft_admission.py`\n"
        "  - `repro/stage315_backend_ifft_admission/`\n",
    )
    append_once(
        CHECKLIST,
        "<!-- stage315-backend-ifft-admission-checklist -->",
        "\n<!-- stage315-backend-ifft-admission-checklist -->\n"
        f"- [x] Stage315 records `{decision}` and Stage316 admission gate.\n",
    )
    append_run_log(decision)

    artifacts = [
        DOC,
        THEORY,
        VARIANT,
        PLAN,
        BUILDER,
        SUMMARY,
        THRESHOLDS,
        CANDIDATES,
        ANCHORS,
        PROOF,
        NEXT,
        COMMANDS,
        REPORT,
    ]
    artifact_index(artifacts)
    print(decision)


if __name__ == "__main__":
    main()
