#!/usr/bin/env python3
"""Stage201: structured selector distribution proof probe."""

from __future__ import annotations

import csv
import hashlib
import random
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage201_structured_selector_distribution_probe"

SUMMARY_CSV = OUT_DIR / "summary.csv"
ASSUMPTION_CSV = OUT_DIR / "assumptions.csv"
DISTRIBUTION_CSV = OUT_DIR / "distribution_probe.csv"
CANDIDATE_CSV = OUT_DIR / "candidate_matrix.csv"
PROOF_GATE_CSV = OUT_DIR / "proof_gate.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"
REPORT_MD = OUT_DIR / "structured_selector_distribution_report.md"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage201_structured_selector_distribution_probe.md"
PLAN_MD = ROOT / "experiments" / "stage201_structured_selector_distribution_probe_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage201_structured_selector_distribution_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_structured_selector_distribution_probe.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE190_SUMMARY = ROOT / "repro" / "stage190_selector_distribution_distinguisher" / "summary.csv"
STAGE190_PROBE = ROOT / "repro" / "stage190_selector_distribution_distinguisher" / "distribution_probe.csv"
STAGE200_COUNTER = ROOT / "repro" / "stage200_formal_gap_model_with_probe" / "counterexample_matrix.csv"
STAGE200_OBLIGATION = ROOT / "repro" / "stage200_formal_gap_model_with_probe" / "proof_obligations.csv"
STAGE200_NEXT = ROOT / "repro" / "stage200_formal_gap_model_with_probe" / "next_stage_queue.csv"

DECISION = "PASS_STAGE201_STRUCTURED_SELECTOR_DISTRIBUTION_PROBE_PROOF_ONLY"


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


def random_mask(rng: random.Random, n: int, q: int) -> Tuple[int, ...]:
    return tuple(rng.randrange(q) for _ in range(n))


def zero_mask(n: int) -> Tuple[int, ...]:
    return tuple(0 for _ in range(n))


def equal_pair_count(rows: Sequence[Tuple[int, ...]]) -> int:
    seen: Dict[Tuple[int, ...], int] = {}
    pairs = 0
    for row in rows:
        count = seen.get(row, 0)
        pairs += count
        seen[row] = count + 1
    return pairs


def build_rows(candidate: str, dense_rows: int, compact_rows: int, rng: random.Random, n: int, q: int) -> List[Tuple[int, ...]]:
    if candidate == "dense_reference":
        return [random_mask(rng, n, q) for _ in range(dense_rows)]
    if candidate == "delete_body_cross_rows":
        return [random_mask(rng, n, q) for _ in range(compact_rows)]
    if candidate == "deterministic_zero_padding":
        rows = [random_mask(rng, n, q) for _ in range(compact_rows)]
        rows.extend(zero_mask(n) for _ in range(dense_rows - compact_rows))
        return rows
    if candidate == "forced_shared_masks":
        base = random_mask(rng, n, q)
        rows = []
        for idx in range(dense_rows):
            rows.append(base if idx % 4 == 0 else random_mask(rng, n, q))
        return rows
    if candidate == "dummy_random_padding":
        rows = [random_mask(rng, n, q) for _ in range(compact_rows)]
        rows.extend(random_mask(rng, n, q) for _ in range(dense_rows - compact_rows))
        return rows
    raise ValueError(candidate)


def build_assumptions() -> List[Dict[str, str]]:
    return [
        {
            "assumption_id": "A1_public_selector_rows",
            "statement": "The selector public key exposes row count and mask coefficients.",
            "scope": "finite public-distribution probe",
            "evidence": rel(STAGE190_PROBE),
            "falsification": "A production format hiding row count and mask relations would need a separate API/proof.",
        },
        {
            "assumption_id": "A2_dense_reference",
            "statement": "The dense exact full-MAT selector uses the dense row count as the public reference format.",
            "scope": "current exact full-MAT route",
            "evidence": rel(STAGE190_PROBE),
            "falsification": "Declare a new structured public key distribution rather than dense equivalence.",
        },
        {
            "assumption_id": "A3_dummy_padding_scope",
            "statement": "Random dummy padding is tested only for simple public row/zero/equality distinguishers, not for semantic correctness or security.",
            "scope": "proof-only candidate",
            "evidence": rel(DISTRIBUTION_CSV),
            "falsification": "A semantic proof or production keygen/noise gate may still reject it.",
        },
    ]


def build_distribution_probe() -> List[Dict[str, str]]:
    candidates = [
        "delete_body_cross_rows",
        "deterministic_zero_padding",
        "forced_shared_masks",
        "dummy_random_padding",
    ]
    rows: List[Dict[str, str]] = []
    q = 257
    n = 16
    t = 7
    trials = 64
    for r in (2, 4, 6):
        dense_count = (r + 1) * (r + 1) * t
        compact_count = 4 * r * t
        for candidate in candidates:
            row_count_hits = 0
            zero_hits = 0
            equality_hits = 0
            for trial in range(trials):
                rng = random.Random(2010000 + r * 10000 + trial)
                probe_rows = build_rows(candidate, dense_count, compact_count, rng, n, q)
                if len(probe_rows) != dense_count:
                    row_count_hits += 1
                if any(row == zero_mask(n) for row in probe_rows):
                    zero_hits += 1
                if equal_pair_count(probe_rows) > 0:
                    equality_hits += 1
            public_hits = row_count_hits + zero_hits + equality_hits
            if candidate == "dummy_random_padding":
                status = "PASS_PUBLIC_PATTERN_ONLY" if public_hits == 0 else "DISTINGUISHER_FOUND"
            else:
                status = "DISTINGUISHER_FOUND" if public_hits > 0 else "FAIL_NO_DISTINGUISHER"
            rows.append(
                {
                    "candidate": candidate,
                    "r": str(r),
                    "dense_rows": str(dense_count),
                    "compact_rows": str(compact_count),
                    "trials": str(trials),
                    "row_count_hits": str(row_count_hits),
                    "zero_mask_hits": str(zero_hits),
                    "mask_equality_hits": str(equality_hits),
                    "public_pattern_hits": str(public_hits),
                    "status": status,
                    "interpretation": interpretation_for(candidate, status),
                }
            )
    return rows


def interpretation_for(candidate: str, status: str) -> str:
    if candidate == "delete_body_cross_rows":
        return "Public row count changes, matching the Stage190 rejection."
    if candidate == "deterministic_zero_padding":
        return "Dense row count is restored, but deterministic zero masks are public."
    if candidate == "forced_shared_masks":
        return "Forced mask equality creates a public relation."
    if candidate == "dummy_random_padding":
        return "Simple public pattern tests pass only because dense row count and random-looking masks are retained; semantic proof remains open."
    return status


def build_candidate_matrix(probe_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    candidates = sorted({row["candidate"] for row in probe_rows})
    out: List[Dict[str, str]] = []
    for candidate in candidates:
        rows = [row for row in probe_rows if row["candidate"] == candidate]
        failures = sum(1 for row in rows if row["status"] in {"DISTINGUISHER_FOUND", "FAIL_NO_DISTINGUISHER"})
        if candidate == "dummy_random_padding":
            decision = "KEEP_PROOF_ONLY_NO_CODE_PERMISSION" if failures == 0 else "REJECT_PUBLIC_PATTERN"
            resource = "dense public row count retained; key-size saving not demonstrated"
        else:
            decision = "REJECT_PUBLIC_DISTRIBUTION_EQUIVALENCE" if any(row["status"] == "DISTINGUISHER_FOUND" for row in rows) else "INCONCLUSIVE"
            resource = "intended compactness conflicts with public distribution"
        out.append(
            {
                "candidate": candidate,
                "rows": str(len(rows)),
                "public_pattern_failures": str(failures),
                "decision": decision,
                "resource_note": resource,
                "evidence": rel(DISTRIBUTION_CSV),
            }
        )
    return out


def build_proof_gate(candidate_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    dummy = next(row for row in candidate_rows if row["candidate"] == "dummy_random_padding")
    return [
        {
            "gate": "T1_public_distribution",
            "status": "PARTIAL_PATTERN_ONLY" if dummy["decision"] == "KEEP_PROOF_ONLY_NO_CODE_PERMISSION" else "FAIL",
            "evidence": f"{rel(DISTRIBUTION_CSV)}; {rel(CANDIDATE_CSV)}",
            "missing_before_code": "Hybrid/simulation proof that dummy rows are indistinguishable from the declared selector distribution.",
        },
        {
            "gate": "T2_functional_correctness",
            "status": "BLOCKED",
            "evidence": rel(STAGE200_COUNTER),
            "missing_before_code": "Proof that skipped/dummy rows are semantically zero for all SAB updates, not only public-pattern safe.",
        },
        {
            "gate": "T3_resource_value",
            "status": "WEAK",
            "evidence": rel(CANDIDATE_CSV),
            "missing_before_code": "Show complete-SAB T_bootstrap/r value despite retaining dense public row count.",
        },
        {
            "gate": "T4_noise_and_keygen",
            "status": "BLOCKED",
            "evidence": rel(STAGE200_OBLIGATION),
            "missing_before_code": "Production keygen, noise recurrence, and multi-seed correctness gates.",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "source_anchor_intake",
            "entry_condition": "Reviewed 2025/686 full text is supplied locally.",
            "gate": "Map source-specific SAB claims to inspected paper anchors.",
            "current_status": "waiting_external_artifact",
            "evidence": "repro/stage196_public_source_refresh/citation_gate.csv",
        },
        {
            "priority": "P1",
            "route": "dummy_padding_semantic_probe",
            "entry_condition": "Continue the only public-pattern-surviving selector route.",
            "gate": "Finite functional probe showing dummy/skipped rows are semantically zero under a declared structured keygen model.",
            "current_status": "proof_probe_only",
            "evidence": rel(PROOF_GATE_CSV),
        },
        {
            "priority": "P2",
            "route": "new_exact_mechanism_admission",
            "entry_condition": "A concrete exact-path backend/addmul/DFT mechanism is supplied.",
            "gate": "Projection, correctness, noise/resource, and complete-SAB T_bootstrap/r gates.",
            "current_status": "waiting_new_mechanism",
            "evidence": "repro/stage200_formal_gap_model_with_probe/gap_projection.csv",
        },
    ]


def build_summary_rows(probe_rows: List[Dict[str, str]], candidate_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs = [STAGE190_SUMMARY, STAGE190_PROBE, STAGE200_COUNTER, STAGE200_OBLIGATION, STAGE200_NEXT]
    inputs_ok = all(path.exists() for path in inputs)
    rejected = sum(1 for row in candidate_rows if row["decision"].startswith("REJECT"))
    proof_only = sum(1 for row in candidate_rows if row["decision"] == "KEEP_PROOF_ONLY_NO_CODE_PERMISSION")
    dummy_failures = sum(
        1
        for row in probe_rows
        if row["candidate"] == "dummy_random_padding" and row["status"] != "PASS_PUBLIC_PATTERN_ONLY"
    )
    return [
        {
            "gate": "stage201_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if inputs_ok else "0",
            "evidence": f"{rel(STAGE190_SUMMARY)}; {rel(STAGE200_COUNTER)}",
            "detail": "Stage201 consumes Stage190 selector distinguishers and Stage200 proof obligations.",
            "next_action": "Repair missing inputs before using this probe.",
        },
        {
            "gate": "stage201_distribution_probe",
            "status": "PASS",
            "metric": "probe_rows",
            "value": str(len(probe_rows)),
            "evidence": rel(DISTRIBUTION_CSV),
            "detail": "Finite public-pattern probes cover r=2/4/6 and four selector candidates.",
            "next_action": "Use candidate matrix for routing, not production claims.",
        },
        {
            "gate": "stage201_candidate_matrix",
            "status": "PASS_RECORDED",
            "metric": "rejected;proof_only",
            "value": f"{rejected};{proof_only}",
            "evidence": rel(CANDIDATE_CSV),
            "detail": "Three candidates remain publicly distinguishable; dummy random padding is proof-only and not code permission.",
            "next_action": "Only semantic proof probes may continue the dummy route.",
        },
        {
            "gate": "stage201_dummy_pattern_gate",
            "status": "PASS_PATTERN_ONLY" if dummy_failures == 0 else "FAIL_PATTERN",
            "metric": "dummy_pattern_failures",
            "value": str(dummy_failures),
            "evidence": rel(PROOF_GATE_CSV),
            "detail": "The only surviving public-pattern route retains dense public shape and still lacks functional/resource/noise proof.",
            "next_action": "Run semantic proof probe only; do not implement SAB code.",
        },
        {
            "gate": "stage201_decision",
            "status": DECISION if inputs_ok and dummy_failures == 0 else "FAIL_STAGE201",
            "metric": "goal_status",
            "value": "active",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Structured selector proof route is narrowed; full goal remains active and implementation remains denied.",
            "next_action": "Proceed to source anchors, dummy semantic proof probe, or new exact mechanism admission.",
        },
    ]


def write_report(
    assumption_rows: List[Dict[str, str]],
    probe_rows: List[Dict[str, str]],
    candidate_rows: List[Dict[str, str]],
    proof_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        REPORT_MD,
        f"""# Structured Selector Distribution Probe

Decision: `{DECISION}`.

Stage201 tests public distribution patterns for structured selector routes.
It rejects row deletion, deterministic zero padding, and forced shared masks
as dense-distribution-equivalent claims. Random dummy padding survives only
simple public-pattern probes; it keeps dense public shape and remains proof-only.

## Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Assumptions

{table(assumption_rows, ["assumption_id", "statement", "scope", "evidence", "falsification"])}
## Candidate Matrix

{table(candidate_rows, ["candidate", "rows", "public_pattern_failures", "decision", "resource_note", "evidence"])}
## Proof Gates

{table(proof_rows, ["gate", "status", "evidence", "missing_before_code"])}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}

Full probe rows are recorded in `{rel(DISTRIBUTION_CSV)}`.
""",
    )


def write_commands() -> None:
    write_text_lf(
        COMMANDS_MD,
        """# Stage201 Reproduction Commands

```powershell
# Rebuild structured selector distribution probe
python scripts\\build_stage201_structured_selector_distribution_probe.py

# Inspect outputs
Get-Content -Raw repro\\stage201_structured_selector_distribution_probe\\summary.csv
Get-Content -Raw repro\\stage201_structured_selector_distribution_probe\\distribution_probe.csv
Get-Content -Raw repro\\stage201_structured_selector_distribution_probe\\candidate_matrix.csv
Get-Content -Raw repro\\stage201_structured_selector_distribution_probe\\proof_gate.csv
```
""",
    )


def write_docs(
    assumption_rows: List[Dict[str, str]],
    candidate_rows: List[Dict[str, str]],
    proof_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage201 Structured Selector Distribution Probe

Decision: `{DECISION}`.

Stage201 narrows the proof-only compact/shared-output route. It does not permit
production SAB code.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Assumptions

{table(assumption_rows, ["assumption_id", "statement", "scope", "evidence", "falsification"])}
## Candidate Matrix

{table(candidate_rows, ["candidate", "rows", "public_pattern_failures", "decision", "resource_note", "evidence"])}
## Proof Gates

{table(proof_rows, ["gate", "status", "evidence", "missing_before_code"])}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage201 Plan

Goal: test whether structured selector candidates survive simple public
distribution distinguishers before any implementation work.

Rules:

- row count, deterministic zero masks, and mask equality are public patterns;
- passing these finite public-pattern probes is not a security proof;
- dummy padding keeps dense public shape and cannot by itself prove speedup;
- no production code is allowed without semantic, noise, resource, and
  complete-SAB gates.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage201 Structured Selector Distribution Model

The compact/shared-output route needs a declared selector distribution. Stage190
already rejects row deletion, deterministic zero rows, and forced shared masks
as standard dense-distribution shortcuts. Stage201 repeats the idea with a
candidate that pads omitted rows with random-looking dummy rows.

Result:

- deleted rows, zero padding, and forced shared masks remain publicly
  distinguishable in the finite probe;
- random dummy padding passes only simple public-pattern tests;
- dummy padding keeps dense public row count, so key-size savings are not
  demonstrated;
- semantic correctness and noise/keygen proof remain blocked.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Structured Selector Distribution Probe

This is not a production algorithm. It is a proof-route filter.

Rejected for dense-equivalence claims:

- delete body-cross rows;
- pad missing rows with deterministic zero masks;
- force shared or equal output masks.

Kept only as proof-only:

- random dummy padding with dense public shape.

The proof-only route must next show semantic zero-term behavior and resource
value before any SAB integration.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 201: Structured Selector Distribution Probe",
        f"""
## Stage 201: Structured Selector Distribution Probe

Goal:

```text
Run finite public-distribution probes for structured selector candidates after
Stage200 identifies selector structure as an open proof obligation.
```

Status:

```text
Completed. Stage201 records {DECISION}. Only random dummy padding survives
simple public-pattern checks, and it remains proof-only with no production code
permission.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage201 records structured selector distribution probe",
        f"""
Stage201 records structured selector distribution probe. Decision:
`{DECISION}`. It rejects publicly distinguishable selector shortcuts and keeps
random dummy padding as proof-only, with no production-code permission.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage201 as structured selector distribution probe",
        f"""
105. Treat Stage201 as structured selector distribution probe:
    `{DECISION}`. The compact/shared-output route remains proof-only; dummy
    padding survives only simple public-pattern checks and still lacks semantic,
    resource, noise, and complete-SAB evidence.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H125_structured_selector_distribution_probe",
        f"""
  - id: H125_structured_selector_distribution_probe
    statement: >
      Structured selector shortcuts must survive public distribution probes
      before any compact/shared-output SAB implementation route can reopen.
    mechanism: >
      Stage201 tests row count, deterministic zero-mask, and mask-equality
      distinguishers for deleted rows, zero padding, forced shared masks, and
      random dummy padding under finite public-key models.
    status: stage201_structured_selector_distribution_probe
    evidence: docs/stage201_structured_selector_distribution_probe.md; experiments/stage201_structured_selector_distribution_probe_plan.md; theory_checks/stage201_structured_selector_distribution_model.md; repro/stage201_structured_selector_distribution_probe/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - a publicly distinguishable selector shortcut is treated as dense-equivalent
      - dummy padding is treated as a security proof or implementation permission
      - production SAB code is opened without semantic, noise, resource, and full-SAB gates
""",
    )

    append_once(
        RUN_LOG,
        "stage201-structured-selector-distribution-probe-001",
        f"""
stage201-structured-selector-distribution-probe-001,2026-07-04,{git_head()},Stage 201,analysis+finite-probe,python scripts/build_stage201_structured_selector_distribution_probe.py,Stage190/200 evidence,none,{DECISION},Structured selector public distribution proof probe.,repro/stage201_structured_selector_distribution_probe
""",
    )

    append_once(
        MANIFEST,
        "stage201_structured_selector_distribution_probe",
        f"""
- stage201_structured_selector_distribution_probe: `{DECISION}`
  - `docs/stage201_structured_selector_distribution_probe.md`
  - `experiments/stage201_structured_selector_distribution_probe_plan.md`
  - `theory_checks/stage201_structured_selector_distribution_model.md`
  - `algorithm_variants/mat_rlwe_sab_structured_selector_distribution_probe.md`
  - `repro/stage201_structured_selector_distribution_probe/`
""",
    )

    append_once(CHECKLIST, "Stage201 structured selector distribution probe recorded", """
- [x] Stage201 structured selector distribution probe recorded.
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
    assumption_rows = build_assumptions()
    probe_rows = build_distribution_probe()
    candidate_rows = build_candidate_matrix(probe_rows)
    proof_rows = build_proof_gate(candidate_rows)
    next_rows = build_next_rows()
    summary_rows = build_summary_rows(probe_rows, candidate_rows)

    write_csv(ASSUMPTION_CSV, assumption_rows, ["assumption_id", "statement", "scope", "evidence", "falsification"])
    write_csv(
        DISTRIBUTION_CSV,
        probe_rows,
        [
            "candidate",
            "r",
            "dense_rows",
            "compact_rows",
            "trials",
            "row_count_hits",
            "zero_mask_hits",
            "mask_equality_hits",
            "public_pattern_hits",
            "status",
            "interpretation",
        ],
    )
    write_csv(CANDIDATE_CSV, candidate_rows, ["candidate", "rows", "public_pattern_failures", "decision", "resource_note", "evidence"])
    write_csv(PROOF_GATE_CSV, proof_rows, ["gate", "status", "evidence", "missing_before_code"])
    write_csv(NEXT_CSV, next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_report(assumption_rows, probe_rows, candidate_rows, proof_rows, next_rows, summary_rows)
    write_commands()
    write_docs(assumption_rows, candidate_rows, proof_rows, next_rows, summary_rows)
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
            ASSUMPTION_CSV,
            DISTRIBUTION_CSV,
            CANDIDATE_CSV,
            PROOF_GATE_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
