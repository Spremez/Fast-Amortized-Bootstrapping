"""Stage254: non-binary selector keygen/noise preflight.

This stage converts Stage253 isolated equivalence into a keygen/noise/resource
admission ledger.  It does not implement production keygen.  It records which
MAT selector encryptions are required, their schedule counts, and the proof
obligations before non-binary PVW/MAT-SAB can enter complete bootstrapping.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage254_nonbinary_keygen_noise_preflight"

INPUTS = {
    "stage253_proof_gate": ROOT / "repro" / "stage253_isolated_nonbinary_suba_equivalence" / "proof_gate.csv",
    "stage253_equivalence": ROOT / "repro" / "stage253_isolated_nonbinary_suba_equivalence" / "lane_equivalence_probe.csv",
    "stage252_layout": ROOT / "repro" / "stage252_nonbinary_mat_selector_key_skeleton" / "key_layout_projection.csv",
    "stage252_probe": ROOT / "repro" / "stage252_nonbinary_mat_selector_key_skeleton" / "toy_key_object_probe.csv",
    "stage251_equations": ROOT / "repro" / "stage251_nonbinary_selector_semantics" / "semantic_equation_matrix.csv",
    "sab_pvw_source": ROOT / "src" / "sab_pvw.c",
    "mosfhet_mattrgsw_source": ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c",
    "mosfhet_header": ROOT / "src" / "mosfhet" / "include" / "mosfhet.h",
}

DOC = ROOT / "docs" / "stage254_nonbinary_keygen_noise_preflight.md"
PLAN = ROOT / "experiments" / "stage254_nonbinary_keygen_noise_preflight_plan.md"
THEORY = ROOT / "theory_checks" / "stage254_nonbinary_keygen_noise_preflight_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage254_nonbinary_keygen_noise_preflight.md"

INPUT_STATUS = OUT / "input_status.csv"
KEYGEN = OUT / "selector_keygen_design.csv"
COST = OUT / "cost_projection.csv"
NOISE = OUT / "noise_obligation_matrix.csv"
RESOURCE = OUT / "resource_obligation_matrix.csv"
SOURCE = OUT / "source_capability_matrix.csv"
ADMISSION = OUT / "implementation_admission.csv"
CLAIM = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage254_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE254_NONBINARY_KEYGEN_NOISE_PREFLIGHT_READY_MOSFHET_ISOLATED_PROTOTYPE"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return proc.stdout.strip()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip() + "\n")


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip("\n").rstrip() + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def table(rows: list[dict[str, object]], fields: list[str]) -> str:
    if not rows:
        return "_No rows._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def input_rows() -> list[dict[str, object]]:
    return [
        {
            "input_id": key,
            "path": rel(path),
            "status": "present" if path.exists() else "missing",
            "bytes": path.stat().st_size if path.exists() else 0,
        }
        for key, path in INPUTS.items()
    ]


def stage253_passes() -> bool:
    rows = read_csv(INPUTS["stage253_proof_gate"])
    return bool(rows) and rows[-1].get("status") == "PASS_STAGE253_ISOLATED_NONBINARY_SUBA_EQUIVALENCE_READY_KEYGEN_NOISE_PREFLIGHT"


def source_capability_rows() -> list[dict[str, object]]:
    sab_pvw = read_text(INPUTS["sab_pvw_source"])
    mattrgsw = read_text(INPUTS["mosfhet_mattrgsw_source"])
    header = read_text(INPUTS["mosfhet_header"])
    return [
        {
            "capability": "mat_monomial_encrypt_zero_one",
            "source": "src/mosfhet/src/mattrgsw.c; src/mosfhet/include/mosfhet.h",
            "observed": "yes" if "mat_trgsw_monomial_sample" in mattrgsw and "mat_trgsw_monomial_sample" in header else "no",
            "status": "PRESENT" if "mat_trgsw_monomial_sample" in mattrgsw and "mat_trgsw_monomial_sample" in header else "MISSING",
            "interpretation": "The primitive needed for 0/1 MAT selector encryption exists.",
        },
        {
            "capability": "mat_to_dft_conversion",
            "source": "src/mosfhet/src/mattrgsw.c; src/mosfhet/include/mosfhet.h",
            "observed": "yes" if "mat_trgsw_to_DFT" in mattrgsw and "mat_trgsw_to_DFT" in header else "no",
            "status": "PRESENT" if "mat_trgsw_to_DFT" in mattrgsw and "mat_trgsw_to_DFT" in header else "MISSING",
            "interpretation": "The primitive needed to store selector rows in DFT form exists.",
        },
        {
            "capability": "current_binary_encrypt_bits_pattern",
            "source": "src/sab_pvw.c",
            "observed": "yes" if "sab_pvw_encrypt_bits" in sab_pvw and "mat_trgsw_monomial_sample" in sab_pvw else "no",
            "status": "PRESENT" if "sab_pvw_encrypt_bits" in sab_pvw and "mat_trgsw_monomial_sample" in sab_pvw else "MISSING",
            "interpretation": "Current binary keygen already loops over MAT monomial bit encryption.",
        },
        {
            "capability": "production_nonbinary_keygen",
            "source": "src/sab_pvw.c",
            "observed": "no" if "only binary sparse input keys are supported" in sab_pvw else "unknown",
            "status": "MISSING_BLOCKED",
            "interpretation": "Production non-binary keygen remains absent by design.",
        },
    ]


def keygen_rows() -> list[dict[str, object]]:
    return [
        {
            "selector_family": "distance_bits",
            "plaintext": "bit_j(r_diff)",
            "monomial_exponent": 0,
            "count_per_key": "(h + 1) * r_prec",
            "existing_pattern": "sab_pvw_encrypt_bits",
            "needed_for_stage255": "reuse current binary pattern as reference",
        },
        {
            "selector_family": "s_coff",
            "plaintext": "c in {0,1}",
            "monomial_exponent": 0,
            "count_per_key": "h when include_zero",
            "existing_pattern": "same MAT monomial encryption primitive, new family",
            "needed_for_stage255": "allocate/encrypt DFT selector family and verify include-zero sub_a",
        },
        {
            "selector_family": "s_sign",
            "plaintext": "s in {0,1}",
            "monomial_exponent": 0,
            "count_per_key": "h when ternary",
            "existing_pattern": "same MAT monomial encryption primitive, new family",
            "needed_for_stage255": "allocate/encrypt DFT selector family and verify ternary sub_a",
        },
    ]


def cost_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    params = [
        ("SET_2_3_2048", 2048, 39, 7),
        ("SET_4_5_2048", 2048, 42, 7),
        ("SET_2_3_4096", 4096, 32, 8),
    ]
    for name, in_n, h, r_prec in params:
        main_ep = (h + 1) * r_prec * in_n
        suba_ep = h * in_n
        base_selectors = (h + 1) * r_prec
        for branch, families in [("include_zero", 1), ("ternary", 1), ("include_zero_plus_ternary_stress", 2)]:
            extra_ep = suba_ep * families
            extra_selectors = h * families
            rows.append({
                "param": name,
                "branch": branch,
                "in_N": in_n,
                "h": h,
                "r_prec": r_prec,
                "binary_main_ep_calls": main_ep,
                "extra_suba_ep_calls": extra_ep,
                "extra_ep_over_binary_main": f"{extra_ep / main_ep:.6f}",
                "binary_selector_objects": base_selectors,
                "extra_selector_objects": extra_selectors,
                "selector_count_ratio": f"{(base_selectors + extra_selectors) / base_selectors:.6f}",
                "admission": "single_family_admitted_to_isolated_prototype" if families == 1 else "stress_only_not_claimed",
            })
    return rows


def noise_rows() -> list[dict[str, object]]:
    return [
        {
            "obligation": "selector_encryption_noise",
            "status": "pending_stage255",
            "required_evidence": "encrypt MAT s_coff/s_sign selectors and record initial noise distribution",
            "failure_action": "do not integrate non-binary sparse_mul",
        },
        {
            "obligation": "suba_external_product_noise",
            "status": "pending_stage255",
            "required_evidence": "isolated sub_a with encrypted selector DFT and scalar/PVW noise comparison",
            "failure_action": "keep Stage253 finite-only",
        },
        {
            "obligation": "full_sparse_schedule_noise",
            "status": "blocked_until_isolated_passes",
            "required_evidence": "multi-step sparse_mul noise recurrence and multi-seed final-output noise",
            "failure_action": "no complete-SAB claim",
        },
        {
            "obligation": "parameter_resource_tradeoff",
            "status": "pending",
            "required_evidence": "key size, keygen time, scratch/RSS for non-binary selector families",
            "failure_action": "scope or reject non-binary branch",
        },
    ]


def resource_rows(cost: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in cost:
        rows.append({
            "param": row["param"],
            "branch": row["branch"],
            "selector_count_ratio": row["selector_count_ratio"],
            "extra_ep_over_binary_main": row["extra_ep_over_binary_main"],
            "status": "preflight_only",
            "interpretation": "Counts show cost pressure; actual bytes/time/noise require Stage255+ measurement.",
        })
    return rows


def admission_rows(cost: list[dict[str, object]], source: list[dict[str, object]]) -> list[dict[str, object]]:
    source_ok = all(row["status"] in {"PRESENT", "MISSING_BLOCKED"} for row in source)
    max_single_extra = max(float(row["extra_ep_over_binary_main"]) for row in cost if row["branch"] in {"include_zero", "ternary"})
    return [
        {
            "route": "stage255_mosfhet_isolated_selector_keygen",
            "decision": "ADMIT_ISOLATED_PROTOTYPE" if source_ok and max_single_extra < 0.20 else "BLOCK",
            "production_permission": "no",
            "reason": f"single-family extra EP ratio max={max_single_extra:.6f}; source primitives present={str(source_ok).lower()}",
            "next_gate": "actual MAT selector encryption, isolated sub_a equivalence, noise/resource",
        },
        {
            "route": "nonbinary_full_sab",
            "decision": "BLOCKED",
            "production_permission": "no",
            "reason": "no encrypted selector keygen, noise recurrence, sparse_mul integration, or full SAB A/B yet",
            "next_gate": "Stage255 and later",
        },
        {
            "route": "include_zero_plus_ternary_stress",
            "decision": "STRESS_ONLY_NOT_CLAIMED",
            "production_permission": "no",
            "reason": "scalar code prioritizes include_zero branch before ternary; both-family row is only layout pressure",
            "next_gate": "separate branch semantics if ever claimed",
        },
    ]


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "keygen_preflight",
            "status": "supported_preflight",
            "allowed_wording": "MAT primitives needed for 0/1 selector encryption exist and counts are projected.",
            "forbidden_wording": "Non-binary MAT selector keygen is implemented.",
            "evidence": rel(KEYGEN),
        },
        {
            "claim": "nonbinary_cost",
            "status": "count_model_only",
            "allowed_wording": "Single-family non-binary sub_a adds h*in_N MAT external-product-class updates in the model.",
            "forbidden_wording": "This model proves non-binary speedup or slowdown.",
            "evidence": rel(COST),
        },
        {
            "claim": "noise_security",
            "status": "unsupported_pending",
            "allowed_wording": "Noise/security remains a required Stage255+ gate.",
            "forbidden_wording": "Non-binary PVW noise is acceptable.",
            "evidence": rel(NOISE),
        },
    ]


def gate_rows(inputs, source, cost, admission) -> list[dict[str, object]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    stage253_ok = stage253_passes()
    source_ok = all(row["status"] in {"PRESENT", "MISSING_BLOCKED"} for row in source)
    single_cost_ok = all(float(row["extra_ep_over_binary_main"]) < 0.20 for row in cost if row["branch"] in {"include_zero", "ternary"})
    admission_ok = admission[0]["decision"] == "ADMIT_ISOLATED_PROTOTYPE" and all(row["production_permission"] == "no" for row in admission)
    decision_ok = inputs_ok and stage253_ok and source_ok and single_cost_ok and admission_ok
    return [
        {
            "gate": "G1_inputs_and_stage253",
            "status": "PASS" if inputs_ok and stage253_ok else "FAIL",
            "metric": "inputs;stage253",
            "value": f"{str(inputs_ok).lower()};{str(stage253_ok).lower()}",
            "evidence": f"{rel(INPUT_STATUS)}; {rel(INPUTS['stage253_proof_gate'])}",
            "interpretation": "Stage254 is valid only after isolated non-binary equivalence passes.",
        },
        {
            "gate": "G2_source_capability",
            "status": "PASS" if source_ok else "FAIL",
            "metric": "source primitives",
            "value": "present_or_blocked_as_expected",
            "evidence": rel(SOURCE),
            "interpretation": "MAT monomial encryption/DFT primitives exist; production non-binary keygen remains absent.",
        },
        {
            "gate": "G3_cost_pressure",
            "status": "PASS_PREFLIGHT" if single_cost_ok else "FAIL",
            "metric": "single-family extra EP ratio",
            "value": "below_0.20",
            "evidence": rel(COST),
            "interpretation": "Single-family non-binary branches are not ruled out by first-order count pressure.",
        },
        {
            "gate": "G4_noise_obligations",
            "status": "PASS_OBLIGATIONS_RECORDED",
            "metric": "noise obligations",
            "value": "pending",
            "evidence": rel(NOISE),
            "interpretation": "Noise is not proven; obligations are explicit before any production claim.",
        },
        {
            "gate": "G5_admission_boundary",
            "status": "PASS_NO_PRODUCTION",
            "metric": "production permission",
            "value": "no",
            "evidence": rel(ADMISSION),
            "interpretation": "Only MOSFHET-adjacent isolated prototype is admitted.",
        },
        {
            "gate": "G6_stage254_decision",
            "status": DECISION if decision_ok else "FAIL_STAGE254_NONBINARY_KEYGEN_NOISE_PREFLIGHT",
            "metric": "decision",
            "value": DECISION if decision_ok else "FAIL_STAGE254_NONBINARY_KEYGEN_NOISE_PREFLIGHT",
            "evidence": rel(GATES),
            "interpretation": "Proceed to actual isolated selector keygen/noise prototype, not full SAB.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage255_mosfhet_isolated_selector_keygen_noise",
            "entry_condition": "Stage254 preflight admits isolated prototype only.",
            "gate": "actual MAT s_coff/s_sign encryption, isolated sub_a equivalence, noise/resource",
            "status": "selected_next",
            "failure_action": "keep non-binary PVW unsupported",
            "evidence": rel(ADMISSION),
        },
        {
            "priority": "P1",
            "route": "stage256_nonbinary_sparse_mul_integration",
            "entry_condition": "Stage255 passes actual selector keygen/noise/resource",
            "gate": "integrate selector families into sparse_mul outside default path",
            "status": "conditional",
            "failure_action": "no production integration",
            "evidence": rel(NOISE),
        },
        {
            "priority": "P2",
            "route": "stage257_nonbinary_full_sab_ab",
            "entry_condition": "Stage256 integration passes correctness and noise",
            "gate": "complete-SAB T_bootstrap/r, multi-seed noise/resource, scalar default isolation",
            "status": "future_gated",
            "failure_action": "no non-binary speedup claim",
            "evidence": rel(CLAIM),
        },
    ]


def artifact_rows(paths: list[Path]) -> list[dict[str, object]]:
    return [
        {
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256(path) if path.exists() and path.is_file() else "",
            "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        }
        for path in paths
    ]


def write_docs(inputs, source, keygen, cost, noise, resource, admission, claims, gates, nextq, head: str) -> None:
    write_text(DOC, f"""# Stage254 Non-Binary Keygen/Noise Preflight

Decision: `{gates[-1]["status"]}`.

Stage254 records the keygen/noise/resource obligations that must be satisfied
before non-binary PVW/MAT-SAB can move beyond the finite Stage253 model.

## Source Capability

{table(source, ["capability", "source", "observed", "status", "interpretation"])}

## Selector Keygen Design

{table(keygen, ["selector_family", "plaintext", "monomial_exponent", "count_per_key", "existing_pattern", "needed_for_stage255"])}

## Cost Projection

{table(cost, ["param", "branch", "in_N", "h", "r_prec", "binary_main_ep_calls", "extra_suba_ep_calls", "extra_ep_over_binary_main", "binary_selector_objects", "extra_selector_objects", "selector_count_ratio", "admission"])}

## Noise Obligations

{table(noise, ["obligation", "status", "required_evidence", "failure_action"])}

## Resource Obligations

{table(resource, ["param", "branch", "selector_count_ratio", "extra_ep_over_binary_main", "status", "interpretation"])}

## Admission

{table(admission, ["route", "decision", "production_permission", "reason", "next_gate"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])}

## Proof Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

Generated from head `{head}`.
""")
    write_text(REPORT, f"""# Stage254 Report

Decision: `{gates[-1]["status"]}`.

The existing MAT monomial encryption and DFT conversion primitives are present,
so an isolated prototype for `s_coff` and `s_sign` selector keygen is admitted.
Production non-binary keygen remains absent and deliberately blocked.

For target `SET_2_3_2048`, a single non-binary selector family adds
`39*2048 = 79872` sub_a external-product-class updates, which is 0.139286 of
the binary main CMUX external-product-class count `40*7*2048 = 573440`.
This is count pressure, not measured runtime or noise.
""")
    write_text(PLAN, """# Stage254 Non-Binary Keygen/Noise Preflight Plan

## Objective

Decide whether Stage253 isolated equivalence can proceed to an actual
MOSFHET-adjacent selector keygen/noise prototype.

## Gates

- Stage253 must pass.
- MAT monomial encryption and DFT conversion primitives must exist.
- Single-family count pressure must not rule out isolated prototyping.
- Noise/resource obligations must be explicit.
- Production full SAB remains blocked.
""")
    write_text(THEORY, """# Stage254 Non-Binary Keygen/Noise Preflight Model

The non-binary selector families use the same 0/1 MAT monomial selector shape
as binary distance bits, but are consumed in `sub_a` rather than CMUX
butterfly layers.

For one non-binary family, the extra external-product-class count is:

```text
h * in_N
```

The binary main CMUX external-product-class count is:

```text
(h + 1) * r_prec * in_N
```

The target ratio is therefore `h / ((h + 1) r_prec) = 39/(40*7)`.
Noise is not derived by this count model and must be measured or bounded in
the next stage.
""")
    write_text(VARIANT, """# MAT-RLWE SAB Stage254 Non-Binary Keygen/Noise Preflight

## Status

Admits only a MOSFHET-adjacent isolated prototype for MAT `s_coff` and
`s_sign` selector keygen/noise. It does not admit production `sab_pvw_*`
integration or complete-SAB benchmarking.
""")
    write_text(REPRO_CMDS, f"""# Stage254 Reproduction Commands

```text
python scripts/build_stage254_nonbinary_keygen_noise_preflight.py
python -m py_compile scripts/build_stage254_nonbinary_keygen_noise_preflight.py
```

Decision: `{gates[-1]["status"]}`.
""")


def update_project_files(head: str, decision: str) -> None:
    append_once(ROADMAP, "## Stage 254: Non-Binary Keygen/Noise Preflight", f"""
## Stage 254: Non-Binary Keygen/Noise Preflight

Goal:

```text
Record selector keygen, noise, resource, and count obligations before actual
non-binary PVW/MAT selector implementation.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. Existing MAT monomial
encryption and DFT conversion primitives can support an isolated `s_coff`/
`s_sign` prototype. Single-family count pressure is recorded and does not
block isolated prototyping, but production full SAB remains blocked until
actual keygen, noise/resource, and integration gates pass.
```
""")
    append_once(GOAL, "Stage254 non-binary keygen/noise preflight", f"""
- Stage254 non-binary keygen/noise preflight records `{decision}`: isolated
  MAT `s_coff/s_sign` keygen/noise prototyping is admitted, but production
  non-binary SAB and speedup claims remain blocked.
""")
    append_once(CURRENT_GOAL, "### Stage254 non-binary keygen/noise preflight", f"""
### Stage254 non-binary keygen/noise preflight

`{decision}` moves the route to actual MOSFHET-adjacent selector keygen/noise
prototype readiness. The active goal remains open for measured noise/resource,
production integration, full SAB A/B, and final claim closure.
""")
    append_once(HYPOTHESES, "H10_stage254_nonbinary_keygen_noise_preflight:", f"""
H10_stage254_nonbinary_keygen_noise_preflight:
  status: isolated_selector_keygen_noise_prototype_admitted
  evidence:
    - repro/stage254_nonbinary_keygen_noise_preflight/source_capability_matrix.csv
    - repro/stage254_nonbinary_keygen_noise_preflight/cost_projection.csv
    - repro/stage254_nonbinary_keygen_noise_preflight/noise_obligation_matrix.csv
    - repro/stage254_nonbinary_keygen_noise_preflight/proof_gate.csv
    - docs/stage254_nonbinary_keygen_noise_preflight.md
  conclusion: >
    Stage254 records {decision}. It admits only MOSFHET-adjacent isolated
    selector keygen/noise prototyping for s_coff/s_sign. Production
    non-binary SAB integration, complete-SAB speedup, and noise/security
    claims remain blocked.
""")
    append_once(RUN_LOG, "stage254-nonbinary-keygen-noise-preflight-001", f"""stage254-nonbinary-keygen-noise-preflight-001,{date.today().isoformat()},{head},Stage 254,keygen_noise_preflight,"python scripts/build_stage254_nonbinary_keygen_noise_preflight.py","Stage253 equivalence + source capability/count model",n/a,{decision},"Isolated selector keygen/noise prototype admitted; production still blocked.",docs/stage254_nonbinary_keygen_noise_preflight.md; repro/stage254_nonbinary_keygen_noise_preflight/proof_gate.csv
""")
    append_once(MANIFEST, "- stage254_nonbinary_keygen_noise_preflight:", """
- stage254_nonbinary_keygen_noise_preflight:
  - `docs/stage254_nonbinary_keygen_noise_preflight.md`
  - `experiments/stage254_nonbinary_keygen_noise_preflight_plan.md`
  - `theory_checks/stage254_nonbinary_keygen_noise_preflight_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage254_nonbinary_keygen_noise_preflight.md`
  - `scripts/build_stage254_nonbinary_keygen_noise_preflight.py`
  - `repro/stage254_nonbinary_keygen_noise_preflight/`
""")
    append_once(CHECKLIST, "Stage254 non-binary keygen/noise preflight admits isolated prototype", f"""
- [x] Stage254 non-binary keygen/noise preflight admits isolated prototype `{decision}`.
""")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    head = run_git(["rev-parse", "--short", "HEAD"])
    inputs = input_rows()
    source = source_capability_rows()
    keygen = keygen_rows()
    cost = cost_rows()
    noise = noise_rows()
    resource = resource_rows(cost)
    admission = admission_rows(cost, source)
    claims = claim_rows()
    gates = gate_rows(inputs, source, cost, admission)
    nextq = next_rows()

    write_csv(INPUT_STATUS, inputs, ["input_id", "path", "status", "bytes"])
    write_csv(SOURCE, source, ["capability", "source", "observed", "status", "interpretation"])
    write_csv(KEYGEN, keygen, ["selector_family", "plaintext", "monomial_exponent", "count_per_key", "existing_pattern", "needed_for_stage255"])
    write_csv(COST, cost, ["param", "branch", "in_N", "h", "r_prec", "binary_main_ep_calls", "extra_suba_ep_calls", "extra_ep_over_binary_main", "binary_selector_objects", "extra_selector_objects", "selector_count_ratio", "admission"])
    write_csv(NOISE, noise, ["obligation", "status", "required_evidence", "failure_action"])
    write_csv(RESOURCE, resource, ["param", "branch", "selector_count_ratio", "extra_ep_over_binary_main", "status", "interpretation"])
    write_csv(ADMISSION, admission, ["route", "decision", "production_permission", "reason", "next_gate"])
    write_csv(CLAIM, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])

    write_docs(inputs, source, keygen, cost, noise, resource, admission, claims, gates, nextq, head)
    artifacts = [DOC, PLAN, THEORY, VARIANT, INPUT_STATUS, SOURCE, KEYGEN, COST, NOISE, RESOURCE, ADMISSION, CLAIM, GATES, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "exists", "sha256", "bytes"])
    if gates[-1]["status"] == DECISION:
        update_project_files(head, gates[-1]["status"])
    print(f"Stage254 report: {rel(DOC)}")
    print(f"Stage254 decision: {gates[-1]['status']}")
    return 0 if gates[-1]["status"] == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
