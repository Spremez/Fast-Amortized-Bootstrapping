#!/usr/bin/env python3
"""Stage217: compact selector keygen/security preflight."""

from __future__ import annotations

import csv
import hashlib
import random
import subprocess
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage217_compact_keygen_security_preflight"

DOC = ROOT / "docs" / "stage217_compact_keygen_security_preflight.md"
PLAN = ROOT / "experiments" / "stage217_compact_keygen_security_preflight_plan.md"
THEORY = ROOT / "theory_checks" / "stage217_compact_keygen_security_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage217_compact_keygen_security_preflight.md"

INPUTS = OUT / "input_status.csv"
PUBLIC_PROBE = OUT / "public_distribution_probe.csv"
CANDIDATES = OUT / "keygen_candidate_matrix.csv"
EQUATION = OUT / "equation_resource_summary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "compact_keygen_security_preflight_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE201_SUMMARY = ROOT / "repro" / "stage201_structured_selector_distribution_probe" / "summary.csv"
STAGE202_SUMMARY = ROOT / "repro" / "stage202_dummy_padding_semantic_probe" / "summary.csv"
STAGE203_EQUATION = ROOT / "repro" / "stage203_production_selector_equation_probe" / "equation_map.csv"
STAGE203_RESOURCE = ROOT / "repro" / "stage203_production_selector_equation_probe" / "resource_projection.csv"
STAGE203_PROOF = ROOT / "repro" / "stage203_production_selector_equation_probe" / "proof_gate.csv"
STAGE216_PROOF = ROOT / "repro" / "stage216_post_counter_frontier" / "proof_gate.csv"

DECISION = "PASS_STAGE217_PATTERN_ONLY_KEYGEN_PREFLIGHT_NO_SAB_CODE"


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
    with path.open(newline="", encoding="utf-8") as handle:
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
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def f(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def build_inputs() -> List[Dict[str, str]]:
    required = [
        ("stage201_public_pattern", STAGE201_SUMMARY, "prior public-pattern gate"),
        ("stage202_dummy_semantics", STAGE202_SUMMARY, "semantic-zero dummy toy gate"),
        ("stage203_equation_map", STAGE203_EQUATION, "declared production-shaped equation map"),
        ("stage203_resource_projection", STAGE203_RESOURCE, "modeled evaluator-row/noise value"),
        ("stage203_proof_gate", STAGE203_PROOF, "remaining security/keygen blockers"),
        ("stage216_frontier", STAGE216_PROOF, "post-counter route selection"),
    ]
    return [
        {
            "input": name,
            "status": "present" if path.exists() else "missing",
            "evidence": rel(path),
            "role": role,
            "bytes": str(path.stat().st_size) if path.exists() else "0",
        }
        for name, path, role in required
    ]


def equation_counts() -> Dict[int, Dict[str, int]]:
    counts: Dict[int, Counter[str]] = {}
    for row in read_csv(STAGE203_EQUATION):
        r = int(row["r"])
        counts.setdefault(r, Counter())
        counts[r]["dense_rows"] += 1
        if row.get("semantic_role") == "active":
            counts[r]["active_rows"] += 1
        if row.get("semantic_role") == "dummy_zero":
            counts[r]["dummy_rows"] += 1
        if row.get("may_skip_after_proof") == "1":
            counts[r]["skippable_rows"] += 1
    return {r: dict(counter) for r, counter in counts.items()}


def mask_rows(r: int, candidate: str, seed: int) -> List[int]:
    counts = equation_counts()[r]
    dense = counts["dense_rows"]
    active = counts["active_rows"]
    dummy = counts["dummy_rows"]
    candidate_index = {
        "dense_reference": 0,
        "row_deletion": 1,
        "deterministic_zero_dummy": 2,
        "forced_equal_dummy": 3,
        "count_matched_random_dummy": 4,
    }[candidate]
    rng = random.Random(217000 + 1000 * r + 10 * seed + candidate_index)
    if candidate == "dense_reference":
        return [rng.getrandbits(63) | 1 for _ in range(dense)]
    if candidate == "row_deletion":
        return [rng.getrandbits(63) | 1 for _ in range(active)]
    if candidate == "deterministic_zero_dummy":
        return [rng.getrandbits(63) | 1 for _ in range(active)] + [0 for _ in range(dummy)]
    if candidate == "forced_equal_dummy":
        active_masks = [rng.getrandbits(63) | 1 for _ in range(active)]
        shared = active_masks[0]
        return active_masks + [shared for _ in range(dummy)]
    if candidate == "count_matched_random_dummy":
        return [rng.getrandbits(63) | 1 for _ in range(dense)]
    raise ValueError(candidate)


def build_public_probe() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    candidates = [
        "dense_reference",
        "row_deletion",
        "deterministic_zero_dummy",
        "forced_equal_dummy",
        "count_matched_random_dummy",
    ]
    for r in (2, 4, 6):
        dense_count = equation_counts()[r]["dense_rows"]
        for candidate in candidates:
            for seed in range(10):
                masks = mask_rows(r, candidate, seed)
                duplicate_count = len(masks) - len(set(masks))
                zero_count = sum(1 for value in masks if value == 0)
                row_count_mismatch = int(len(masks) != dense_count)
                zero_row_distinguisher = int(zero_count > 0)
                equality_distinguisher = int(duplicate_count > 0)
                public_pattern_fail = row_count_mismatch or zero_row_distinguisher or equality_distinguisher
                expected = "reference" if candidate == "dense_reference" else (
                    "survive_simple_public_pattern" if candidate == "count_matched_random_dummy" else "reject"
                )
                status = "PASS_REFERENCE" if candidate == "dense_reference" else (
                    "PASS_PATTERN_ONLY" if expected == "survive_simple_public_pattern" and not public_pattern_fail else (
                        "PASS_REJECTED_DISTINGUISHABLE" if expected == "reject" and public_pattern_fail else "FAIL_UNEXPECTED"
                    )
                )
                rows.append(
                    {
                        "r": str(r),
                        "candidate": candidate,
                        "seed": str(seed),
                        "public_rows": str(len(masks)),
                        "expected_dense_rows": str(dense_count),
                        "zero_rows": str(zero_count),
                        "duplicate_rows": str(duplicate_count),
                        "row_count_mismatch": str(row_count_mismatch),
                        "zero_row_distinguisher": str(zero_row_distinguisher),
                        "equality_distinguisher": str(equality_distinguisher),
                        "status": status,
                        "interpretation": "Simple public-pattern probe only; not a security proof.",
                    }
                )
    return rows


def candidate_summary(probe_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for candidate in [
        "row_deletion",
        "deterministic_zero_dummy",
        "forced_equal_dummy",
        "count_matched_random_dummy",
    ]:
        subset = [row for row in probe_rows if row["candidate"] == candidate]
        failures = sum(1 for row in subset if row["status"] == "FAIL_UNEXPECTED")
        rejections = sum(1 for row in subset if row["status"] == "PASS_REJECTED_DISTINGUISHABLE")
        pattern_pass = sum(1 for row in subset if row["status"] == "PASS_PATTERN_ONLY")
        if candidate == "count_matched_random_dummy":
            status = "PATTERN_ONLY_SURVIVES" if failures == 0 and pattern_pass == len(subset) else "FAIL_PATTERN_GATE"
            permission = "stage218_isolated_object_probe_only" if status == "PATTERN_ONLY_SURVIVES" else "deny"
            reason = "Matches dense public row count with random dummy masks in finite simple-pattern probes; still lacks security/noise proof."
        else:
            status = "REJECT_PUBLICLY_DISTINGUISHABLE" if failures == 0 and rejections == len(subset) else "FAIL_NEGATIVE_CONTROL"
            permission = "deny"
            reason = "Negative control must remain publicly distinguishable."
        rows.append(
            {
                "candidate": candidate,
                "status": status,
                "probe_rows": str(len(subset)),
                "unexpected_failures": str(failures),
                "code_permission": permission,
                "reason": reason,
                "evidence": rel(PUBLIC_PROBE),
            }
        )
    return rows


def build_equation_summary() -> List[Dict[str, str]]:
    resource = {int(row["r"]): row for row in read_csv(STAGE203_RESOURCE)}
    rows: List[Dict[str, str]] = []
    for r, counts in sorted(equation_counts().items()):
        dense = counts["dense_rows"]
        active = counts["active_rows"]
        dummy = counts["dummy_rows"]
        skip = counts["skippable_rows"]
        res = resource.get(r, {})
        rows.append(
            {
                "r": str(r),
                "dense_rows_per_T": str(dense),
                "active_rows_per_T": str(active),
                "dummy_rows_per_T": str(dummy),
                "skippable_rows_if_proven": str(skip),
                "active_over_dense": f"{active / dense:.9f}",
                "evaluator_row_reduction_if_skip_proven": res.get("evaluator_row_reduction_if_skip_proven", f"{skip / dense:.9f}"),
                "dense_eval_noise_over_skip_mean": res.get("dense_eval_noise_over_skip_mean", ""),
                "admission": "model_value_positive_but_public_key_size_not_reduced",
                "evidence": f"{rel(STAGE203_EQUATION)}; {rel(STAGE203_RESOURCE)}",
            }
        )
    return rows


def build_proof(
    inputs: List[Dict[str, str]],
    probes: List[Dict[str, str]],
    candidates: List[Dict[str, str]],
    equations: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    missing = [row["input"] for row in inputs if row["status"] != "present"]
    unexpected = sum(1 for row in probes if row["status"] == "FAIL_UNEXPECTED")
    surviving = [row for row in candidates if row["candidate"] == "count_matched_random_dummy"][0]
    min_reduction = min((f(row["evaluator_row_reduction_if_skip_proven"]) for row in equations), default=0.0)
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if not missing else "FAIL",
            "metric": "missing_inputs",
            "value": ";".join(missing),
            "evidence": rel(INPUTS),
            "interpretation": "Stage217 consumes Stage201/202/203 proof-only compact evidence and Stage216 route selection.",
        },
        {
            "gate": "G2_public_pattern_negative_controls",
            "status": "PASS" if unexpected == 0 else "FAIL",
            "metric": "unexpected_probe_failures",
            "value": str(unexpected),
            "evidence": rel(PUBLIC_PROBE),
            "interpretation": "Row deletion, deterministic zero rows, and forced equal dummy masks must remain distinguishable.",
        },
        {
            "gate": "G3_surviving_keygen_shape",
            "status": surviving["status"],
            "metric": "surviving_candidate",
            "value": surviving["candidate"],
            "evidence": rel(CANDIDATES),
            "interpretation": "Only count-matched random dummy padding survives simple public-pattern probes, and only as pattern-only evidence.",
        },
        {
            "gate": "G4_equation_resource_signal",
            "status": "PASS_MODEL_VALUE_RECORDED",
            "metric": "min_evaluator_row_reduction_if_skip_proven",
            "value": f"{min_reduction:.9f}",
            "evidence": rel(EQUATION),
            "interpretation": "Modeled evaluator work reduction is positive, but public key row count remains dense and security is not proven.",
        },
        {
            "gate": "G5_production_sab_admission",
            "status": "DENY_SAB_HOTPATH_CODE",
            "metric": "missing_before_sab_code",
            "value": "standard_keygen_distribution;noise_recurrence;resource_bound;complete_sab_gate",
            "evidence": rel(PROOF),
            "interpretation": "Stage217 may route to isolated key-object/noise prototype only; no SAB integration or speedup claim.",
        },
        {
            "gate": "G6_stage217_decision",
            "status": DECISION if not missing and unexpected == 0 else "FAIL_STAGE217",
            "metric": "decision",
            "value": DECISION if not missing and unexpected == 0 else "FAIL_STAGE217",
            "evidence": rel(PROOF),
            "interpretation": "Compact route remains alive but proof-bounded; next work must be isolated key-object/noise prototype.",
        },
    ]


def build_next() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage218_compact_key_object_noise_prototype",
            "entry_condition": "Stage217 count-matched random dummy padding survives simple public-pattern probes.",
            "gate": "Standalone compact key object/noise prototype with negative controls; no SAB hot-path integration.",
            "status": "selected",
            "failure_action": "If prototype closure/noise fails, compact route is blocked and reporting falls back to exact PVW/MAT-SAB only.",
            "evidence": f"{rel(CANDIDATES)}; {rel(PROOF)}",
        },
        {
            "priority": "P1",
            "route": "full_text_source_anchor_review",
            "entry_condition": "Reviewed 2025/686 full text is supplied locally.",
            "gate": "Anchor every theorem/equation claim to inspected paper text.",
            "status": "waiting_artifact",
            "failure_action": "Keep source claims metadata-safe.",
            "evidence": rel(STAGE203_PROOF),
        },
        {
            "priority": "P2",
            "route": "external_backend_mechanism",
            "entry_condition": "A real backend primitive is supplied.",
            "gate": "Exact conversion equivalence and complete-SAB T_bootstrap/r.",
            "status": "waiting_external_mechanism",
            "failure_action": "Record neutral/failed backend ablation.",
            "evidence": rel(STAGE216_PROOF),
        },
    ]


def write_docs(
    inputs: List[Dict[str, str]],
    probes: List[Dict[str, str]],
    candidates: List[Dict[str, str]],
    equations: List[Dict[str, str]],
    proof: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    report = f"""# Stage217 Compact Keygen/Security Preflight

Decision: `{DECISION}`.

Stage217 tests the compact selector route selected by Stage216. It does not
implement SAB code. The finite public-pattern probe rejects row deletion,
deterministic zero dummy rows, and forced equal dummy masks. Count-matched
random dummy padding survives only this simple public-pattern screen.

The result is deliberately limited: production SAB integration remains denied
until standard keygen distribution, noise recurrence, resource bounds, and
complete-SAB `T_bootstrap/r` gates exist.

## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Input Status

{table(inputs, ["input", "status", "evidence", "role", "bytes"])}
## Keygen Candidate Matrix

{table(candidates, ["candidate", "status", "probe_rows", "unexpected_failures", "code_permission", "reason", "evidence"])}
## Equation/Resource Summary

{table(equations, ["r", "dense_rows_per_T", "active_rows_per_T", "dummy_rows_per_T", "skippable_rows_if_proven", "active_over_dense", "evaluator_row_reduction_if_skip_proven", "dense_eval_noise_over_skip_mean", "admission", "evidence"])}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

Raw public-pattern rows: `{rel(PUBLIC_PROBE)}`.
"""
    write_text(REPORT, report)
    write_text(DOC, report)
    write_text(
        PLAN,
        """# Stage217 Plan

Goal: turn the compact selector route into executable keygen/security admission
checks without entering SAB hot-path code.

Gates:

- required Stage201/202/203/216 inputs exist;
- public-pattern negative controls are rejected;
- count-matched random dummy padding is only pattern-only evidence;
- equation/resource value is recorded but not upgraded to implementation
  permission;
- next work is isolated key-object/noise prototype or fail closed.
""",
    )
    write_text(
        THEORY,
        """# Stage217 Compact Keygen/Security Model

The compact selector idea can only be production-safe if public key material is
distributed like an allowed dense key while dummy rows are semantically zero for
evaluation. Public row deletion, deterministic zero rows, or forced shared
masks are distinguishable and are rejected by finite public-pattern probes.

Count-matched random dummy padding avoids these simple public-pattern
distinguishers in this finite model, but this is not a security proof. The next
valid step is an isolated object/noise prototype that keeps negative controls
and still avoids SAB hot-path integration.
""",
    )
    write_text(
        VARIANT,
        """# Compact Selector Keygen/Security Preflight

This is not a SAB implementation variant.

Rejected keygen shapes:

- row deletion;
- deterministic zero dummy rows;
- forced equal/shared dummy masks.

Surviving only as pattern evidence:

- count-matched random dummy padding.

Blocked before SAB code:

- standard keygen distribution proof;
- production noise recurrence;
- resource bound;
- complete-SAB `T_bootstrap/r` benchmark.
""",
    )
    write_text(
        REPRO,
        """# Stage217 Reproduction Commands

```powershell
python scripts\\build_stage217_compact_keygen_security_preflight.py
Get-Content -Raw repro\\stage217_compact_keygen_security_preflight\\proof_gate.csv
Get-Content -Raw repro\\stage217_compact_keygen_security_preflight\\keygen_candidate_matrix.csv
```
""",
    )


def update_tracking() -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 217: Compact Keygen/Security Preflight",
        f"""
## Stage 217: Compact Keygen/Security Preflight

Goal:

```text
Run executable public-pattern, equation/resource, and admission gates for the
compact selector keygen route selected by Stage216.
```

Status:

```text
Completed. Stage217 records {DECISION}. Count-matched random dummy padding
survives only a simple public-pattern screen; SAB hot-path code remains denied.
The next selected route is an isolated compact key-object/noise prototype.
```
""",
    )
    append_once(
        GOAL,
        "Stage217 records compact keygen/security preflight",
        f"""
Stage217 records compact keygen/security preflight. Decision: `{DECISION}`.
Bad compact keygen shapes are rejected by finite public-pattern probes; the
surviving count-matched random dummy shape is pattern-only and cannot be used
for SAB speedup claims.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage217 compact keygen/security preflight",
        f"""
### Stage217 compact keygen/security preflight

`{DECISION}` keeps the compact route executable but bounded. Count-matched
random dummy padding survives simple public-pattern probes, while row deletion,
deterministic zero dummy rows, and forced equal masks are rejected. No SAB
hot-path code or speedup claim is authorized.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage217_compact_keygen_security_preflight",
        f"""
H10_stage217_compact_keygen_security_preflight:
  status: compact_keygen_pattern_only_recorded
  evidence:
    - repro/stage217_compact_keygen_security_preflight/keygen_candidate_matrix.csv
    - repro/stage217_compact_keygen_security_preflight/proof_gate.csv
    - docs/stage217_compact_keygen_security_preflight.md
  conclusion: >
    Stage217 records {DECISION}. Count-matched random dummy padding survives a
    finite simple public-pattern screen, but production keygen/security/noise
    and complete-SAB gates remain missing. SAB hot-path implementation remains
    denied.
""",
    )
    append_once(
        RUN_LOG,
        "stage217-compact-keygen-security-preflight-001",
        f"""stage217-compact-keygen-security-preflight-001,2026-07-04,{head},Stage 217,finite-probe,python scripts/build_stage217_compact_keygen_security_preflight.py,Stage201-203 and Stage216 compact route,no SAB benchmark,{DECISION},"Pattern-only compact keygen preflight; SAB hot-path code denied.",docs/stage217_compact_keygen_security_preflight.md; repro/stage217_compact_keygen_security_preflight/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage217_compact_keygen_security_preflight:",
        """
- stage217_compact_keygen_security_preflight:
  - `docs/stage217_compact_keygen_security_preflight.md`
  - `experiments/stage217_compact_keygen_security_preflight_plan.md`
  - `theory_checks/stage217_compact_keygen_security_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage217_compact_keygen_security_preflight.md`
  - `scripts/build_stage217_compact_keygen_security_preflight.py`
  - `repro/stage217_compact_keygen_security_preflight/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage217 compact keygen/security preflight recorded",
        """
- [x] Stage217 compact keygen/security preflight recorded.
""",
    )


def write_artifacts(paths: Iterable[Path]) -> None:
    rows = [
        {
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path),
            "bytes": str(path.stat().st_size) if path.exists() else "0",
        }
        for path in paths
    ]
    write_csv(ARTIFACT, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    inputs = build_inputs()
    probes = build_public_probe()
    candidates = candidate_summary(probes)
    equations = build_equation_summary()
    proof = build_proof(inputs, probes, candidates, equations)
    next_rows = build_next()

    write_csv(INPUTS, inputs, ["input", "status", "evidence", "role", "bytes"])
    write_csv(
        PUBLIC_PROBE,
        probes,
        [
            "r",
            "candidate",
            "seed",
            "public_rows",
            "expected_dense_rows",
            "zero_rows",
            "duplicate_rows",
            "row_count_mismatch",
            "zero_row_distinguisher",
            "equality_distinguisher",
            "status",
            "interpretation",
        ],
    )
    write_csv(CANDIDATES, candidates, ["candidate", "status", "probe_rows", "unexpected_failures", "code_permission", "reason", "evidence"])
    write_csv(
        EQUATION,
        equations,
        [
            "r",
            "dense_rows_per_T",
            "active_rows_per_T",
            "dummy_rows_per_T",
            "skippable_rows_if_proven",
            "active_over_dense",
            "evaluator_row_reduction_if_skip_proven",
            "dense_eval_noise_over_skip_mean",
            "admission",
            "evidence",
        ],
    )
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_docs(inputs, probes, candidates, equations, proof, next_rows)
    update_tracking()
    write_artifacts([DOC, PLAN, THEORY, VARIANT, INPUTS, PUBLIC_PROBE, CANDIDATES, EQUATION, PROOF, NEXT, REPORT, REPRO, Path(__file__)])
    print(DECISION)


if __name__ == "__main__":
    main()
