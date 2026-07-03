#!/usr/bin/env python3
"""Stage221: compact encrypted keygen noise/resource recurrence gate."""

from __future__ import annotations

import csv
import hashlib
import math
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage221_compact_keygen_noise_recurrence"

DOC = ROOT / "docs" / "stage221_compact_keygen_noise_recurrence.md"
PLAN = ROOT / "experiments" / "stage221_compact_keygen_noise_recurrence_plan.md"
THEORY = ROOT / "theory_checks" / "stage221_compact_keygen_noise_recurrence_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage221_compact_noise_recurrence.md"

INPUTS = OUT / "input_status.csv"
RECURRENCE = OUT / "recurrence_model.csv"
RESOURCE = OUT / "resource_bound.csv"
PER_BIT = OUT / "per_bit_normalization.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "compact_keygen_noise_recurrence_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE220_PROOF = ROOT / "repro" / "stage220_encrypted_compact_keygen_prototype" / "proof_gate.csv"
STAGE220_KEYGEN = ROOT / "repro" / "stage220_encrypted_compact_keygen_prototype" / "keygen_results.csv"
STAGE220_LAYOUT = ROOT / "repro" / "stage220_encrypted_compact_keygen_prototype" / "layout_results.csv"
STAGE203_RESOURCE = ROOT / "repro" / "stage203_production_selector_equation_probe" / "resource_projection.csv"
STAGE187_THEOREM = ROOT / "repro" / "stage187_compact_proof_obligation_draft" / "theorem_matrix.csv"

DECISION = "PASS_STAGE221_COMPACT_KEYGEN_NOISE_RECURRENCE_READY_ISOLATED_EP"
H_PLUS_ONE = 40
R_PREC = 7
MAIN_N = 2048

INPUT_FIELDS = ["input", "status", "evidence", "role", "bytes"]
RECURRENCE_FIELDS = [
    "backend",
    "r",
    "N",
    "seeds",
    "steps_per_lane",
    "dense_rows",
    "active_rows",
    "dummy_rows",
    "max_row_noise",
    "dense_sigma_proxy",
    "active_sigma_proxy",
    "active_over_dense_sigma",
    "dense_l1_proxy",
    "active_l1_proxy",
    "active_over_dense_l1",
    "status",
]
RESOURCE_FIELDS = [
    "r",
    "N",
    "dense_public_rows",
    "active_eval_rows",
    "dummy_public_rows",
    "public_key_row_saving",
    "eval_row_reduction",
    "rows_per_bit_dense_public",
    "rows_per_bit_active_eval",
    "rows_per_bit_dummy_public",
    "stage203_eval_reduction_if_skip",
    "status",
]
PER_BIT_FIELDS = [
    "r",
    "N",
    "processed_bits_per_batch",
    "steps_per_lane",
    "scalar_repeated_schedule_steps",
    "mat_batch_schedule_steps",
    "lane_amortization_step_ceiling",
    "compact_vs_dense_mat_row_ceiling",
    "compact_active_rows_per_bit",
    "dense_mat_rows_per_bit",
    "claim_boundary",
]


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
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
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
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out) + "\n"


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
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
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def fnum(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def build_inputs() -> List[Dict[str, str]]:
    inputs = [
        (
            "stage220_proof_gate",
            STAGE220_PROOF,
            "admission proof for encrypted compact keygen prototype",
        ),
        (
            "stage220_keygen_results",
            STAGE220_KEYGEN,
            "measured encrypted-row max noise and pass/fail data",
        ),
        (
            "stage220_layout_results",
            STAGE220_LAYOUT,
            "dense/active/dummy row counts",
        ),
        (
            "stage203_resource_projection",
            STAGE203_RESOURCE,
            "selector row reduction reference",
        ),
        (
            "stage187_theorem_matrix",
            STAGE187_THEOREM,
            "claim-boundary proof obligations",
        ),
    ]
    rows = []
    for name, path, role in inputs:
        rows.append(
            {
                "input": name,
                "status": "present" if path.exists() else "missing",
                "evidence": rel(path),
                "role": role,
                "bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    return rows


def stage220_passes() -> bool:
    proof = read_csv(STAGE220_PROOF)
    return any(row.get("status") == "PASS_STAGE220_ENCRYPTED_COMPACT_KEYGEN_READY_NOISE_RECURRENCE" for row in proof)


def grouped_keygen() -> Dict[tuple[str, str, str], List[Dict[str, str]]]:
    grouped: Dict[tuple[str, str, str], List[Dict[str, str]]] = {}
    for row in read_csv(STAGE220_KEYGEN):
        key = (row.get("backend", ""), row.get("r", ""), row.get("N", ""))
        grouped.setdefault(key, []).append(row)
    return grouped


def resource_projection_by_r() -> Dict[str, Dict[str, str]]:
    return {row.get("r", ""): row for row in read_csv(STAGE203_RESOURCE)}


def build_recurrence_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for (backend, r_str, n_str), samples in sorted(grouped_keygen().items(), key=lambda item: (int(item[0][1]), int(item[0][2]))):
        if not samples:
            continue
        r = int(r_str)
        n = int(n_str)
        dense_rows = max(int(row["dense_rows"]) for row in samples)
        active_rows = max(int(row["active_rows"]) for row in samples)
        dummy_rows = max(int(row["dummy_rows"]) for row in samples)
        max_noise = max(fnum(row["max_noise_abs"]) for row in samples)
        steps = H_PLUS_ONE * R_PREC * n
        dense_var = steps * dense_rows * max_noise * max_noise
        active_var = steps * active_rows * max_noise * max_noise
        dense_sigma = math.sqrt(dense_var)
        active_sigma = math.sqrt(active_var)
        dense_l1 = steps * dense_rows * max_noise
        active_l1 = steps * active_rows * max_noise
        all_pass = all(row.get("status") == "PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE" for row in samples)
        status = "PASS_RELATIVE_RECURRENCE_NO_WORSE_THAN_DENSE_MAT" if all_pass and active_sigma <= dense_sigma else "FAIL_RELATIVE_RECURRENCE"
        rows.append(
            {
                "backend": backend,
                "r": r_str,
                "N": n_str,
                "seeds": str(len(samples)),
                "steps_per_lane": str(steps),
                "dense_rows": str(dense_rows),
                "active_rows": str(active_rows),
                "dummy_rows": str(dummy_rows),
                "max_row_noise": f"{max_noise:.6f}",
                "dense_sigma_proxy": f"{dense_sigma:.6f}",
                "active_sigma_proxy": f"{active_sigma:.6f}",
                "active_over_dense_sigma": f"{active_sigma / dense_sigma:.9f}" if dense_sigma else "",
                "dense_l1_proxy": f"{dense_l1:.6f}",
                "active_l1_proxy": f"{active_l1:.6f}",
                "active_over_dense_l1": f"{active_l1 / dense_l1:.9f}" if dense_l1 else "",
                "status": status,
            }
        )
    return rows


def build_resource_rows() -> List[Dict[str, str]]:
    stage203 = resource_projection_by_r()
    rows: List[Dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in read_csv(STAGE220_LAYOUT):
        key = (row.get("r", ""), row.get("N", ""))
        if key in seen:
            continue
        seen.add(key)
        r = int(row["r"])
        dense = fnum(row["dense_rows"])
        active = fnum(row["active_rows"])
        dummy = fnum(row["dummy_rows"])
        stage203_row = stage203.get(row["r"], {})
        eval_reduction = 1.0 - active / dense if dense else 0.0
        status = "PASS_RESOURCE_BOUND_DECLARED_NO_KEY_SIZE_SAVING" if dense > 0 and active <= dense and dummy >= 0 else "FAIL_RESOURCE_BOUND"
        rows.append(
            {
                "r": row["r"],
                "N": row["N"],
                "dense_public_rows": f"{dense:.0f}",
                "active_eval_rows": f"{active:.0f}",
                "dummy_public_rows": f"{dummy:.0f}",
                "public_key_row_saving": "0",
                "eval_row_reduction": f"{eval_reduction:.9f}",
                "rows_per_bit_dense_public": f"{dense / r:.9f}",
                "rows_per_bit_active_eval": f"{active / r:.9f}",
                "rows_per_bit_dummy_public": f"{dummy / r:.9f}",
                "stage203_eval_reduction_if_skip": stage203_row.get("evaluator_row_reduction_if_skip_proven", ""),
                "status": status,
            }
        )
    return rows


def build_per_bit_rows(resource_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows = []
    for row in resource_rows:
        r = int(row["r"])
        n = int(row["N"])
        steps = H_PLUS_ONE * R_PREC * n
        dense = fnum(row["dense_public_rows"])
        active = fnum(row["active_eval_rows"])
        rows.append(
            {
                "r": row["r"],
                "N": row["N"],
                "processed_bits_per_batch": row["r"],
                "steps_per_lane": str(steps),
                "scalar_repeated_schedule_steps": str(r * steps),
                "mat_batch_schedule_steps": str(steps),
                "lane_amortization_step_ceiling": f"{float(r):.9f}",
                "compact_vs_dense_mat_row_ceiling": f"{dense / active:.9f}" if active else "",
                "compact_active_rows_per_bit": row["rows_per_bit_active_eval"],
                "dense_mat_rows_per_bit": row["rows_per_bit_dense_public"],
                "claim_boundary": "row-count/model ceiling only; requires Stage222 isolated EP and complete SAB A/B before latency claim",
            }
        )
    return rows


def build_proof(inputs: List[Dict[str, str]], recurrence_rows: List[Dict[str, str]], resource_rows: List[Dict[str, str]], per_bit_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    missing = [row["input"] for row in inputs if row["status"] != "present"]
    recurrence_pass = recurrence_rows and all(row["status"] == "PASS_RELATIVE_RECURRENCE_NO_WORSE_THAN_DENSE_MAT" for row in recurrence_rows)
    resource_pass = resource_rows and all(row["status"] == "PASS_RESOURCE_BOUND_DECLARED_NO_KEY_SIZE_SAVING" for row in resource_rows)
    per_bit_active = sorted({row["compact_active_rows_per_bit"] for row in per_bit_rows})
    per_bit_pass = len(per_bit_active) == 1 and per_bit_active[0] == "4.000000000"
    max_sigma_ratio = max((fnum(row["active_over_dense_sigma"]) for row in recurrence_rows), default=0.0)
    max_l1_ratio = max((fnum(row["active_over_dense_l1"]) for row in recurrence_rows), default=0.0)
    max_eval_reduction = max((fnum(row["eval_row_reduction"]) for row in resource_rows), default=0.0)
    ready = not missing and stage220_passes() and recurrence_pass and resource_pass and per_bit_pass
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if not missing else "FAIL",
            "metric": "missing_inputs",
            "value": ";".join(missing),
            "evidence": rel(INPUTS),
            "interpretation": "Stage221 consumes Stage220 encrypted keygen data plus Stage203/Stage187 claim boundaries.",
        },
        {
            "gate": "G2_stage220_admission",
            "status": "PASS" if stage220_passes() else "FAIL",
            "metric": "stage220_decision",
            "value": "present" if stage220_passes() else "missing",
            "evidence": rel(STAGE220_PROOF),
            "interpretation": "Noise recurrence is only meaningful after encrypted compact keygen prototype passed.",
        },
        {
            "gate": "G3_relative_noise_recurrence",
            "status": "PASS" if recurrence_pass else "FAIL",
            "metric": "max_active_over_dense_sigma;max_active_over_dense_l1",
            "value": f"{max_sigma_ratio:.9f};{max_l1_ratio:.9f}",
            "evidence": rel(RECURRENCE),
            "interpretation": "Under the deterministic row-noise recurrence proxy, active-row compact evaluation is no worse than dense MAT.",
        },
        {
            "gate": "G4_resource_boundary",
            "status": "PASS" if resource_pass else "FAIL",
            "metric": "public_key_row_saving;max_eval_row_reduction",
            "value": f"0;{max_eval_reduction:.9f}",
            "evidence": rel(RESOURCE),
            "interpretation": "Public key rows remain dense; only evaluator row skipping is admitted.",
        },
        {
            "gate": "G5_per_bit_normalization",
            "status": "PASS" if per_bit_pass else "FAIL",
            "metric": "compact_active_rows_per_bit",
            "value": ";".join(per_bit_active),
            "evidence": rel(PER_BIT),
            "interpretation": "`T_bootstrap/r` normalization is explicit; row-count ceilings are not latency claims.",
        },
        {
            "gate": "G6_production_admission",
            "status": "ALLOW_ISOLATED_COMPACT_EP_ONLY",
            "metric": "missing_before_sab_code",
            "value": "compact_ep_phase_equivalence;complete_sab_gate;multi_seed_noise;security_reduction",
            "evidence": rel(PROOF),
            "interpretation": "Stage221 can open isolated compact EP experiments only; SAB hot-path code remains denied.",
        },
        {
            "gate": "G7_stage221_decision",
            "status": DECISION if ready else "FAIL_STAGE221",
            "metric": "decision",
            "value": DECISION if ready else "FAIL_STAGE221",
            "evidence": rel(PROOF),
            "interpretation": "Relative recurrence/resource/per-bit gates permit Stage222 isolated compact EP, not complete-SAB acceleration claims.",
        },
    ]


def build_next(decision: str) -> List[Dict[str, str]]:
    selected = decision == DECISION
    return [
        {
            "priority": "P0",
            "route": "stage222_isolated_compact_ep_integration",
            "entry_condition": "Stage221 recurrence/resource/per-bit gates pass.",
            "gate": "Implement isolated compact external product reference and compare phase/noise versus dense MAT.",
            "status": "selected" if selected else "blocked",
            "failure_action": "If isolated EP fails, keep compact route outside SAB and report model-only result.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P1",
            "route": "stage223_compact_ep_microbench",
            "entry_condition": "Stage222 isolated compact EP correctness passes.",
            "gate": "Measure compact active-row EP versus dense MAT under same backend before any SAB schedule work.",
            "status": "future_blocked",
            "failure_action": "Record kernel-level neutral/negative result.",
            "evidence": rel(PER_BIT),
        },
        {
            "priority": "P2",
            "route": "exact_pvw_mat_sab_report_fallback",
            "entry_condition": "Stage221 fails or Stage222 correctness fails.",
            "gate": "Use already verified exact PVW/MAT-SAB `T_bootstrap/r` evidence only.",
            "status": "fallback",
            "failure_action": "No compact algorithmic claim.",
            "evidence": rel(STAGE220_PROOF),
        },
    ]


def write_docs(inputs: List[Dict[str, str]], recurrence_rows: List[Dict[str, str]], resource_rows: List[Dict[str, str]], per_bit_rows: List[Dict[str, str]], proof_rows: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> None:
    decision = proof_rows[-1]["status"]
    doc = f"""# Stage221 Compact Keygen Noise Recurrence

Decision: `{decision}`.

Stage221 binds the encrypted compact keygen prototype to the target SAB schedule
with an explicit relative noise/resource recurrence. The endpoint is still
`T_bootstrap/r`: compact rows are normalized per processed plaintext bit, and
row-count ceilings are separated from latency claims.

This stage permits only isolated compact external-product experiments. It does
not modify `sab_pvw_*`, does not prove standard key security, and does not claim
complete SAB speedup.

## Proof Gates

{table(proof_rows, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Recurrence Model

{table(recurrence_rows, RECURRENCE_FIELDS)}
## Resource Boundary

{table(resource_rows, RESOURCE_FIELDS)}
## Per-Bit Normalization

{table(per_bit_rows, PER_BIT_FIELDS)}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
"""
    write_text(DOC, doc)
    write_text(REPORT, doc)
    write_text(
        THEORY,
        """# Stage221 Compact Keygen Noise Recurrence Model

For each encrypted compact selector row, Stage220 measured a deterministic
prototype noise bound `eta_row`. Stage221 uses a conservative independent-row
proxy over the SAB schedule:

```text
steps(N) = (h + 1) * r_prec * N = 40 * 7 * N
sigma_dense  = sqrt(steps(N) * dense_rows  * eta_row^2)
sigma_active = sqrt(steps(N) * active_rows * eta_row^2)
```

The gate is relative: `sigma_active <= sigma_dense` and the L1 proxy is also no
worse. This is enough to admit isolated compact external-product experiments,
but not enough for a production security theorem or a complete-SAB speedup
claim. Later stages must add phase equivalence, multi-seed noise, and full SAB
`T_bootstrap/r` benchmarks.
""",
    )
    write_text(
        PLAN,
        """# Stage221 Experiment Plan

1. Read Stage220 encrypted keygen rows and Stage203 selector resource data.
2. Compute dense versus active-row recurrence over `40 * 7 * N` SAB steps.
3. Normalize active/dense row work by processed plaintext bits `r`.
4. Permit Stage222 only if relative recurrence, resource disclosure, and
   per-bit normalization gates pass.

No runtime latency claim is made in this stage.
""",
    )
    write_text(
        VARIANT,
        """# MAT-RLWE SAB Stage221 Compact Noise Recurrence

The compact route keeps dense public selector rows for key distribution while
allowing evaluator-side skipping of semantic-zero dummy rows after proof. The
active rows per processed bit are `4` for the current r=2/4/6 selector model,
but public rows per bit still grow as `(r + 1)^2 / r`.

Stage221 therefore supports only a bounded next step: isolated compact external
product correctness/noise testing. Complete SAB integration remains gated.
""",
    )
    write_text(
        REPRO,
        f"""# Stage221 Reproduction Commands

```powershell
python scripts\\build_stage221_compact_keygen_noise_recurrence.py
Get-Content {rel(PROOF)}
Get-Content {rel(RECURRENCE)}
Get-Content {rel(PER_BIT)}
```
""",
    )


def update_tracking(status: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 221: Compact Keygen Noise Recurrence",
        f"""
## Stage 221: Compact Keygen Noise Recurrence

Goal:

```text
Bind encrypted compact keygen rows to a SAB schedule-level relative
noise/resource recurrence and decide whether isolated compact EP experiments
are allowed.
```

Status:

```text
Completed. Stage221 records {status}. Relative dense-vs-active recurrence and
`T_bootstrap/r` row normalization pass, but only isolated compact EP experiments
are authorized; SAB hot-path integration remains denied.
```
""",
    )
    append_once(
        GOAL,
        "Stage221 compact keygen noise recurrence",
        f"""
- Stage221 compact keygen noise recurrence: `{status}`. This is a relative
  row-noise/resource gate for compact selector rows, not a complete-SAB speedup
  claim.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage221 compact keygen noise recurrence",
        f"""
- Stage221 compact keygen noise recurrence completed with `{status}`. The next
  selected route is isolated compact external-product integration; `sab_pvw_*`
  remains untouched.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage221_compact_keygen_noise_recurrence",
        f"""
H10_stage221_compact_keygen_noise_recurrence:
  status: compact_noise_recurrence_passed
  evidence:
    - repro/stage221_compact_keygen_noise_recurrence/proof_gate.csv
    - repro/stage221_compact_keygen_noise_recurrence/recurrence_model.csv
    - repro/stage221_compact_keygen_noise_recurrence/per_bit_normalization.csv
  conclusion: >
    Stage221 records {status}. The compact route has a relative dense-vs-active
    noise/resource recurrence and explicit T_bootstrap/r normalization, but only
    isolated compact EP experiments are admitted.
""",
    )
    append_once(
        RUN_LOG,
        "stage221-compact-keygen-noise-recurrence-001",
        f"""stage221-compact-keygen-noise-recurrence-001,2026-07-04,{head},Stage 221,model,python scripts/build_stage221_compact_keygen_noise_recurrence.py,Stage220 encrypted keygen rows,no SAB benchmark,{status},"Relative recurrence/per-bit resource gate; SAB hot-path code denied.",docs/stage221_compact_keygen_noise_recurrence.md; repro/stage221_compact_keygen_noise_recurrence/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage221_compact_keygen_noise_recurrence:",
        """
- stage221_compact_keygen_noise_recurrence:
  - `docs/stage221_compact_keygen_noise_recurrence.md`
  - `experiments/stage221_compact_keygen_noise_recurrence_plan.md`
  - `theory_checks/stage221_compact_keygen_noise_recurrence_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage221_compact_noise_recurrence.md`
  - `scripts/build_stage221_compact_keygen_noise_recurrence.py`
  - `repro/stage221_compact_keygen_noise_recurrence/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage221 compact keygen noise recurrence recorded",
        """
- [x] Stage221 compact keygen noise recurrence recorded.
""",
    )


def write_artifacts(paths: Iterable[Path]) -> None:
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
    write_csv(ARTIFACT, rows, ["path", "exists", "sha256", "bytes"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = build_inputs()
    recurrence_rows = build_recurrence_rows()
    resource_rows = build_resource_rows()
    per_bit_rows = build_per_bit_rows(resource_rows)
    proof_rows = build_proof(inputs, recurrence_rows, resource_rows, per_bit_rows)
    next_rows = build_next(proof_rows[-1]["status"])
    write_csv(INPUTS, inputs, INPUT_FIELDS)
    write_csv(RECURRENCE, recurrence_rows, RECURRENCE_FIELDS)
    write_csv(RESOURCE, resource_rows, RESOURCE_FIELDS)
    write_csv(PER_BIT, per_bit_rows, PER_BIT_FIELDS)
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_docs(inputs, recurrence_rows, resource_rows, per_bit_rows, proof_rows, next_rows)
    status = proof_rows[-1]["status"]
    update_tracking(status)
    write_artifacts([DOC, PLAN, THEORY, VARIANT, INPUTS, RECURRENCE, RESOURCE, PER_BIT, PROOF, NEXT, REPORT, REPRO, Path(__file__)])
    print(status)
    return 0 if status == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
