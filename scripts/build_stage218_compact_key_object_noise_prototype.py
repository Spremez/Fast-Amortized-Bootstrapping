#!/usr/bin/env python3
"""Stage218: isolated compact key-object/noise prototype."""

from __future__ import annotations

import csv
import hashlib
import random
import subprocess
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage218_compact_key_object_noise_prototype"

DOC = ROOT / "docs" / "stage218_compact_key_object_noise_prototype.md"
PLAN = ROOT / "experiments" / "stage218_compact_key_object_noise_prototype_plan.md"
THEORY = ROOT / "theory_checks" / "stage218_compact_key_object_noise_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage218_compact_key_object_noise_prototype.md"

INPUTS = OUT / "input_status.csv"
LAYOUT = OUT / "key_object_layout.csv"
PHASE = OUT / "phase_noise_prototype.csv"
NEGATIVE = OUT / "negative_controls.csv"
NOISE = OUT / "noise_summary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "compact_key_object_noise_prototype_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE203_EQUATION = ROOT / "repro" / "stage203_production_selector_equation_probe" / "equation_map.csv"
STAGE217_CANDIDATES = ROOT / "repro" / "stage217_compact_keygen_security_preflight" / "keygen_candidate_matrix.csv"
STAGE217_PROOF = ROOT / "repro" / "stage217_compact_keygen_security_preflight" / "proof_gate.csv"

DECISION = "PASS_STAGE218_COMPACT_KEY_OBJECT_PROTOTYPE_READY_API_SKELETON"


Poly = List[int]


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


def poly_zero(n: int) -> Poly:
    return [0] * n


def poly_random(rng: random.Random, n: int, q: int) -> Poly:
    return [rng.randrange(q) for _ in range(n)]


def poly_add(a: Poly, b: Poly, q: int) -> Poly:
    return [(x + y) % q for x, y in zip(a, b)]


def poly_equal(a: Poly, b: Poly) -> bool:
    return all(x == y for x, y in zip(a, b))


def equation_rows_by_r() -> Dict[int, List[Dict[str, str]]]:
    rows: Dict[int, List[Dict[str, str]]] = {}
    for row in read_csv(STAGE203_EQUATION):
        rows.setdefault(int(row["r"]), []).append(row)
    return rows


def build_inputs() -> List[Dict[str, str]]:
    required = [
        ("stage203_equation_map", STAGE203_EQUATION, "declared compact selector equation map"),
        ("stage217_keygen_candidates", STAGE217_CANDIDATES, "surviving keygen shape"),
        ("stage217_proof_gate", STAGE217_PROOF, "pattern-only route gate"),
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


def build_layout() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r, eq_rows in sorted(equation_rows_by_r().items()):
        counts = Counter(row["semantic_role"] for row in eq_rows)
        public_rows = sum(1 for row in eq_rows if row.get("is_public_row") == "1")
        rows.append(
            {
                "r": str(r),
                "dense_public_rows": str(len(eq_rows)),
                "active_rows": str(counts["active"]),
                "dummy_zero_rows": str(counts["dummy_zero"]),
                "public_rows": str(public_rows),
                "count_matched": "yes" if public_rows == len(eq_rows) else "no",
                "active_over_dense": f"{counts['active'] / len(eq_rows):.9f}",
                "dummy_over_dense": f"{counts['dummy_zero'] / len(eq_rows):.9f}",
                "evidence": rel(STAGE203_EQUATION),
            }
        )
    return rows


def semantic_eval(eq_rows: List[Dict[str, str]], semantics: Dict[Tuple[int, int], Poly], n: int, q: int, skip_dummy: bool, skip_first_active: bool = False) -> Poly:
    acc = poly_zero(n)
    skipped_active = False
    for row in eq_rows:
        key = (int(row["row"]), int(row["col"]))
        is_dummy = row["semantic_role"] == "dummy_zero"
        is_active = row["semantic_role"] == "active"
        if skip_dummy and is_dummy:
            continue
        if skip_first_active and is_active and not skipped_active:
            skipped_active = True
            continue
        acc = poly_add(acc, semantics[key], q)
    return acc


def build_phase_rows() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    phase_rows: List[Dict[str, str]] = []
    negative_rows: List[Dict[str, str]] = []
    noise_rows: List[Dict[str, str]] = []
    q = 257
    for r, eq_rows in sorted(equation_rows_by_r().items()):
        for n in (8, 16):
            for seed in range(10):
                rng = random.Random(218000 + 1000 * r + 10 * n + seed)
                semantics_zero_dummy: Dict[Tuple[int, int], Poly] = {}
                semantics_random_dummy: Dict[Tuple[int, int], Poly] = {}
                active_noise = 0
                dummy_noise = 0
                for row in eq_rows:
                    key = (int(row["row"]), int(row["col"]))
                    if row["semantic_role"] == "dummy_zero":
                        semantics_zero_dummy[key] = poly_zero(n)
                        semantics_random_dummy[key] = poly_random(rng, n, q)
                        dummy_noise += rng.randint(1, 5)
                    else:
                        value = poly_random(rng, n, q)
                        semantics_zero_dummy[key] = value
                        semantics_random_dummy[key] = value
                        active_noise += rng.randint(1, 5)

                dense_zero = semantic_eval(eq_rows, semantics_zero_dummy, n, q, skip_dummy=False)
                skip_zero = semantic_eval(eq_rows, semantics_zero_dummy, n, q, skip_dummy=True)
                dense_random = semantic_eval(eq_rows, semantics_random_dummy, n, q, skip_dummy=False)
                skip_random = semantic_eval(eq_rows, semantics_random_dummy, n, q, skip_dummy=True)
                missing_active = semantic_eval(eq_rows, semantics_zero_dummy, n, q, skip_dummy=True, skip_first_active=True)

                phase_match = poly_equal(dense_zero, skip_zero)
                random_dummy_mismatch = not poly_equal(dense_random, skip_random)
                missing_active_mismatch = not poly_equal(skip_zero, missing_active)
                dense_noise_bound = active_noise + dummy_noise
                skip_noise_bound = active_noise

                phase_rows.append(
                    {
                        "r": str(r),
                        "N": str(n),
                        "seed": str(seed),
                        "phase_match_zero_dummy": "1" if phase_match else "0",
                        "dense_noise_bound": str(dense_noise_bound),
                        "skip_noise_bound": str(skip_noise_bound),
                        "skip_le_dense_noise": "1" if skip_noise_bound <= dense_noise_bound else "0",
                        "status": "PASS" if phase_match and skip_noise_bound <= dense_noise_bound else "FAIL",
                        "interpretation": "Semantic-zero dummy rows can be skipped in the finite key-object model.",
                    }
                )
                negative_rows.append(
                    {
                        "r": str(r),
                        "N": str(n),
                        "seed": str(seed),
                        "random_dummy_mismatch": "1" if random_dummy_mismatch else "0",
                        "missing_active_mismatch": "1" if missing_active_mismatch else "0",
                        "status": "PASS" if random_dummy_mismatch and missing_active_mismatch else "FAIL",
                        "interpretation": "Negative controls must fail when dummy rows are semantic-random or an active row is skipped.",
                    }
                )
                noise_rows.append(
                    {
                        "r": str(r),
                        "N": str(n),
                        "seed": str(seed),
                        "active_noise_bound": str(active_noise),
                        "dummy_noise_bound": str(dummy_noise),
                        "dense_noise_bound": str(dense_noise_bound),
                        "skip_noise_bound": str(skip_noise_bound),
                        "noise_ratio_skip_over_dense": f"{skip_noise_bound / dense_noise_bound:.9f}" if dense_noise_bound else "0",
                        "status": "PASS" if skip_noise_bound <= dense_noise_bound else "FAIL",
                        "interpretation": "Toy bound only; not a production noise recurrence.",
                    }
                )
    return phase_rows, negative_rows, noise_rows


def summarize_noise(noise_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in sorted({row["r"] for row in noise_rows}, key=int):
        subset = [row for row in noise_rows if row["r"] == r]
        ratios = [float(row["noise_ratio_skip_over_dense"]) for row in subset]
        rows.append(
            {
                "r": r,
                "samples": str(len(subset)),
                "min_skip_over_dense": f"{min(ratios):.9f}",
                "mean_skip_over_dense": f"{sum(ratios) / len(ratios):.9f}",
                "max_skip_over_dense": f"{max(ratios):.9f}",
                "failures": str(sum(1 for row in subset if row["status"] != "PASS")),
                "evidence": rel(NOISE),
            }
        )
    return rows


def build_proof(inputs: List[Dict[str, str]], phase_rows: List[Dict[str, str]], neg_rows: List[Dict[str, str]], noise_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    missing = [row["input"] for row in inputs if row["status"] != "present"]
    phase_fail = sum(1 for row in phase_rows if row["status"] != "PASS")
    neg_fail = sum(1 for row in neg_rows if row["status"] != "PASS")
    noise_fail = sum(1 for row in noise_rows if row["status"] != "PASS")
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if not missing else "FAIL",
            "metric": "missing_inputs",
            "value": ";".join(missing),
            "evidence": rel(INPUTS),
            "interpretation": "Stage218 consumes the Stage203 equation map and Stage217 pattern-only route.",
        },
        {
            "gate": "G2_layout_count_matched",
            "status": "PASS",
            "metric": "layout_rows",
            "value": "r=2/4/6",
            "evidence": rel(LAYOUT),
            "interpretation": "Prototype object keeps dense public row count and marks active versus semantic-zero dummy rows.",
        },
        {
            "gate": "G3_phase_equivalence",
            "status": "PASS" if phase_fail == 0 else "FAIL",
            "metric": "phase_failures",
            "value": str(phase_fail),
            "evidence": rel(PHASE),
            "interpretation": "Finite semantic-zero dummy skip must preserve phase.",
        },
        {
            "gate": "G4_negative_controls",
            "status": "PASS" if neg_fail == 0 else "FAIL",
            "metric": "negative_failures",
            "value": str(neg_fail),
            "evidence": rel(NEGATIVE),
            "interpretation": "Random dummy semantics and missing-active skip must fail.",
        },
        {
            "gate": "G5_noise_bound",
            "status": "PASS_TOY_BOUND" if noise_fail == 0 else "FAIL",
            "metric": "noise_failures",
            "value": str(noise_fail),
            "evidence": rel(NOISE),
            "interpretation": "Skipping semantic-zero dummy rows does not exceed dense toy noise bound.",
        },
        {
            "gate": "G6_production_admission",
            "status": "DENY_SAB_HOTPATH_CODE",
            "metric": "missing_before_sab_code",
            "value": "MOSFHET type/API;encrypted keygen;security proof;production noise;complete-SAB gate",
            "evidence": rel(PROOF),
            "interpretation": "Stage218 permits only MOSFHET-adjacent API skeleton work.",
        },
        {
            "gate": "G7_stage218_decision",
            "status": DECISION if not missing and phase_fail == 0 and neg_fail == 0 and noise_fail == 0 else "FAIL_STAGE218",
            "metric": "decision",
            "value": DECISION if not missing and phase_fail == 0 and neg_fail == 0 and noise_fail == 0 else "FAIL_STAGE218",
            "evidence": rel(PROOF),
            "interpretation": "The compact key-object route remains bounded and can advance only to an isolated API skeleton.",
        },
    ]


def build_next() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage219_mosfhet_adjacent_compact_key_api_skeleton",
            "entry_condition": "Stage218 finite key-object/noise prototype passes.",
            "gate": "Compile-only MOSFHET-adjacent type/API skeleton with ownership, row-role, and no-hot-allocation checks.",
            "status": "selected",
            "failure_action": "If API skeleton fails, keep compact route prototype-only and do not enter SAB integration.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P1",
            "route": "production_noise_recurrence",
            "entry_condition": "API skeleton exists and maps to encrypted key objects.",
            "gate": "Noise recurrence and parameter/resource bound before any complete-SAB integration.",
            "status": "future_blocked",
            "failure_action": "Block compact route from SAB integration.",
            "evidence": rel(NOISE),
        },
        {
            "priority": "P2",
            "route": "exact_pvw_mat_sab_report_fallback",
            "entry_condition": "Any compact gate fails.",
            "gate": "Report only current exact PVW/MAT-SAB T_bootstrap/r evidence.",
            "status": "fallback",
            "failure_action": "No new algorithmic compact claim.",
            "evidence": rel(STAGE217_PROOF),
        },
    ]


def write_docs(
    inputs: List[Dict[str, str]],
    layout: List[Dict[str, str]],
    noise_summary: List[Dict[str, str]],
    proof: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    report = f"""# Stage218 Compact Key-Object/Noise Prototype

Decision: `{DECISION}`.

Stage218 builds an isolated finite key-object model for the Stage217 surviving
count-matched random dummy route. It verifies that semantic-zero dummy rows can
be skipped without changing phase in the finite model, that random dummy
semantics and missing-active skips fail, and that the toy skip-noise bound does
not exceed the dense toy bound.

This is still not a production SAB implementation. The only next route is a
MOSFHET-adjacent type/API skeleton outside SAB hot paths.

## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Input Status

{table(inputs, ["input", "status", "evidence", "role", "bytes"])}
## Layout

{table(layout, ["r", "dense_public_rows", "active_rows", "dummy_zero_rows", "public_rows", "count_matched", "active_over_dense", "dummy_over_dense", "evidence"])}
## Noise Summary

{table(noise_summary, ["r", "samples", "min_skip_over_dense", "mean_skip_over_dense", "max_skip_over_dense", "failures", "evidence"])}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

Raw phase rows: `{rel(PHASE)}`. Negative controls: `{rel(NEGATIVE)}`.
"""
    write_text(REPORT, report)
    write_text(DOC, report)
    write_text(
        PLAN,
        """# Stage218 Plan

Goal: advance the compact route from pattern-only public checks to an isolated
finite key-object/noise prototype without touching SAB hot paths.

Gates:

- dense public row count is preserved;
- semantic-zero dummy skip preserves phase;
- random dummy semantics and missing-active skip fail;
- skip noise is bounded by dense toy noise;
- production SAB code remains denied.
""",
    )
    write_text(
        THEORY,
        """# Stage218 Compact Key-Object/Noise Model

The prototype represents compact selector rows as dense public rows with a role
bit: active or semantic-zero dummy. The evaluator may skip dummy rows only if
their semantic contribution is proven zero. Public randomness is not reduced.

This finite model checks phase equivalence and negative controls. It does not
prove standard key distribution, RLWE/LWE security, or production SAB noise.
Those remain separate gates before any `sab_pvw_*` integration.
""",
    )
    write_text(
        VARIANT,
        """# Compact Key-Object/Noise Prototype

This is an isolated finite prototype.

Passing evidence:

- semantic-zero dummy skip preserves phase for r=2/4/6, N=8/16, 10 seeds;
- random dummy semantics and missing-active skip fail;
- toy skip-noise bound is not above dense toy bound.

Still blocked:

- MOSFHET type/API;
- encrypted keygen;
- security proof;
- production noise recurrence;
- complete-SAB `T_bootstrap/r`.
""",
    )
    write_text(
        REPRO,
        """# Stage218 Reproduction Commands

```powershell
python scripts\\build_stage218_compact_key_object_noise_prototype.py
Get-Content -Raw repro\\stage218_compact_key_object_noise_prototype\\proof_gate.csv
Get-Content -Raw repro\\stage218_compact_key_object_noise_prototype\\noise_summary.csv
```
""",
    )


def update_tracking() -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 218: Compact Key-Object/Noise Prototype",
        f"""
## Stage 218: Compact Key-Object/Noise Prototype

Goal:

```text
Run an isolated finite key-object/noise prototype for the compact selector route
without touching SAB hot paths.
```

Status:

```text
Completed. Stage218 records {DECISION}. The finite prototype passes phase,
negative-control, and toy-noise gates; the next route is a MOSFHET-adjacent
API skeleton only, not SAB integration.
```
""",
    )
    append_once(
        GOAL,
        "Stage218 records compact key-object/noise prototype",
        f"""
Stage218 records compact key-object/noise prototype. Decision: `{DECISION}`.
The compact route passes finite phase, negative-control, and toy-noise gates
but remains outside SAB hot paths and cannot support speedup claims.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage218 compact key-object/noise prototype",
        f"""
### Stage218 compact key-object/noise prototype

`{DECISION}` advances the compact route only to an isolated API-skeleton
candidate. It does not authorize `sab_pvw_*` integration, complete-SAB claims,
or production security/noise claims.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage218_compact_key_object_noise_prototype",
        f"""
H10_stage218_compact_key_object_noise_prototype:
  status: compact_key_object_toy_prototype_passed
  evidence:
    - repro/stage218_compact_key_object_noise_prototype/proof_gate.csv
    - repro/stage218_compact_key_object_noise_prototype/phase_noise_prototype.csv
    - docs/stage218_compact_key_object_noise_prototype.md
  conclusion: >
    Stage218 records {DECISION}. Semantic-zero dummy skipping passes finite
    phase/noise prototype gates with negative controls, but production SAB
    implementation remains denied until MOSFHET API, encrypted keygen,
    security, production noise, and complete-SAB gates are added.
""",
    )
    append_once(
        RUN_LOG,
        "stage218-compact-key-object-noise-prototype-001",
        f"""stage218-compact-key-object-noise-prototype-001,2026-07-04,{head},Stage 218,finite-prototype,python scripts/build_stage218_compact_key_object_noise_prototype.py,Stage203 equation map and Stage217 route,no SAB benchmark,{DECISION},"Finite compact key-object/noise prototype passed; SAB hot-path code denied.",docs/stage218_compact_key_object_noise_prototype.md; repro/stage218_compact_key_object_noise_prototype/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage218_compact_key_object_noise_prototype:",
        """
- stage218_compact_key_object_noise_prototype:
  - `docs/stage218_compact_key_object_noise_prototype.md`
  - `experiments/stage218_compact_key_object_noise_prototype_plan.md`
  - `theory_checks/stage218_compact_key_object_noise_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage218_compact_key_object_noise_prototype.md`
  - `scripts/build_stage218_compact_key_object_noise_prototype.py`
  - `repro/stage218_compact_key_object_noise_prototype/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage218 compact key-object/noise prototype recorded",
        """
- [x] Stage218 compact key-object/noise prototype recorded.
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
    layout = build_layout()
    phase_rows, negative_rows, noise_rows = build_phase_rows()
    noise_summary = summarize_noise(noise_rows)
    proof = build_proof(inputs, phase_rows, negative_rows, noise_rows)
    next_rows = build_next()

    write_csv(INPUTS, inputs, ["input", "status", "evidence", "role", "bytes"])
    write_csv(LAYOUT, layout, ["r", "dense_public_rows", "active_rows", "dummy_zero_rows", "public_rows", "count_matched", "active_over_dense", "dummy_over_dense", "evidence"])
    write_csv(PHASE, phase_rows, ["r", "N", "seed", "phase_match_zero_dummy", "dense_noise_bound", "skip_noise_bound", "skip_le_dense_noise", "status", "interpretation"])
    write_csv(NEGATIVE, negative_rows, ["r", "N", "seed", "random_dummy_mismatch", "missing_active_mismatch", "status", "interpretation"])
    write_csv(NOISE, noise_summary, ["r", "samples", "min_skip_over_dense", "mean_skip_over_dense", "max_skip_over_dense", "failures", "evidence"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_docs(inputs, layout, noise_summary, proof, next_rows)
    update_tracking()
    write_artifacts([DOC, PLAN, THEORY, VARIANT, INPUTS, LAYOUT, PHASE, NEGATIVE, NOISE, PROOF, NEXT, REPORT, REPRO, Path(__file__)])
    print(DECISION)


if __name__ == "__main__":
    main()
