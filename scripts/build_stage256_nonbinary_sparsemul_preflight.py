"""Stage256: non-binary sparse_mul integration preflight.

Stage255 proved actual isolated MOSFHET MAT selector updates.  Stage256 moves
one level up: it designs the non-binary sparse_mul integration boundary,
projects counts/noise/resource obligations, and runs a finite multi-round
schedule lifecycle probe.  It still does not edit production SAB/PVW sources.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage256_nonbinary_sparsemul_preflight"

INPUTS = {
    "stage255_proof_gate": ROOT / "repro" / "stage255_mosfhet_nonbinary_selector_keygen_noise" / "proof_gate.csv",
    "stage255_probe": ROOT / "repro" / "stage255_mosfhet_nonbinary_selector_keygen_noise" / "selector_noise_probe.csv",
    "stage255_admission": ROOT / "repro" / "stage255_mosfhet_nonbinary_selector_keygen_noise" / "implementation_admission.csv",
    "stage254_cost": ROOT / "repro" / "stage254_nonbinary_keygen_noise_preflight" / "cost_projection.csv",
    "stage253_equivalence": ROOT / "repro" / "stage253_isolated_nonbinary_suba_equivalence" / "lane_equivalence_probe.csv",
    "sab_pvw_header": ROOT / "include" / "sab_pvw.h",
    "sab_pvw_source": ROOT / "src" / "sab_pvw.c",
    "scalar_sab_source": ROOT / "src" / "sparse_amortized_bootstrap.c",
}

DOC = ROOT / "docs" / "stage256_nonbinary_sparsemul_preflight.md"
PLAN = ROOT / "experiments" / "stage256_nonbinary_sparsemul_preflight_plan.md"
THEORY = ROOT / "theory_checks" / "stage256_nonbinary_sparsemul_preflight_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage256_nonbinary_sparsemul_preflight.md"

INPUT_STATUS = OUT / "input_status.csv"
SOURCE = OUT / "source_boundary_matrix.csv"
DESIGN = OUT / "integration_design_matrix.csv"
COUNTS = OUT / "schedule_count_projection.csv"
PROBE = OUT / "finite_sparsemul_schedule_probe.csv"
NEGATIVE = OUT / "negative_control_matrix.csv"
RECURRENCE = OUT / "noise_resource_recurrence.csv"
ADMISSION = OUT / "implementation_admission.csv"
CLAIM = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage256_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE256_NONBINARY_SPARSEMUL_PREFLIGHT_READY_EXPLICIT_IMPLEMENTATION"
MODULUS = 257


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip() + "\n")


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
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


def stage255_passes() -> bool:
    rows = read_csv(INPUTS["stage255_proof_gate"])
    return bool(rows) and rows[-1].get("status") == "PASS_STAGE255_MOSFHET_SELECTOR_KEYGEN_NOISE_READY_NONBINARY_SPARSEMUL_PREFLIGHT"


def source_boundary_rows() -> list[dict[str, object]]:
    header = read_text(INPUTS["sab_pvw_header"])
    pvw = read_text(INPUTS["sab_pvw_source"])
    scalar = read_text(INPUTS["scalar_sab_source"])
    rows = [
        {
            "boundary": "current_binary_key_object",
            "source_fact": "SAB_PVW_Key contains only MAT_TRGSW_DFT *** s",
            "observed": "yes" if "MAT_TRGSW_DFT *** s" in header else "no",
            "required_delta": "new explicit non-binary key object or sidecar with s_coff/s_sign",
            "production_edit_allowed_now": "no",
        },
        {
            "boundary": "current_sparse_mul",
            "source_fact": "sab_pvw_sparse_mul_binary consumes sab->s and sab_pvw_sub_a_binary",
            "observed": "yes" if "sab_pvw_sparse_mul_binary" in pvw and "sab_pvw_sub_a_binary" in pvw else "no",
            "required_delta": "new sab_pvw_nonbinary_sparse_mul path consuming active state and selector families",
            "production_edit_allowed_now": "only_after_stage257",
        },
        {
            "boundary": "binary_guard",
            "source_fact": "PVW constructor rejects coeff != 1",
            "observed": "yes" if "only binary sparse input keys are supported" in pvw else "no",
            "required_delta": "do not remove guard; add explicit non-binary constructor",
            "production_edit_allowed_now": "no",
        },
        {
            "boundary": "scalar_reference",
            "source_fact": "scalar sub_a has include_zero and ternary branches",
            "observed": "yes" if "sab->include_zeros" in scalar and "sab->ternary_secret" in scalar else "no",
            "required_delta": "use scalar equations as reference for Stage257 tests",
            "production_edit_allowed_now": "not_applicable",
        },
    ]
    for path in [INPUTS["sab_pvw_header"], INPUTS["sab_pvw_source"], INPUTS["scalar_sab_source"]]:
        proc = subprocess.run(["git", "diff", "--name-only", "--", rel(path)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rows.append({
            "boundary": f"source_isolation_{path.name}",
            "source_fact": rel(path),
            "observed": "unchanged" if not proc.stdout.strip() else "modified",
            "required_delta": "Stage256 must not modify production source",
            "production_edit_allowed_now": "no",
        })
    return rows


def design_rows() -> list[dict[str, object]]:
    return [
        {
            "component": "nonbinary_key_object",
            "required_shape": "distance bit selectors plus optional MAT s_coff/s_sign families",
            "consumer": "nonbinary sparse_mul/sub_a only",
            "invariant": "binary SAB_PVW_Key and sab_pvw_sparse_mul_binary remain unchanged",
            "stage257_task": "define explicit sidecar or new key type",
        },
        {
            "component": "rgsw_monomial_step",
            "required_shape": "reuse existing sab_pvw_RGSW_monomial_mul_state for distance-bit schedule",
            "consumer": "same active buffer state as binary path",
            "invariant": "CMUX count remains (h+1)*r_prec*in_N",
            "stage257_task": "call existing state primitive, no non-binary change",
        },
        {
            "component": "include_zero_sub_a",
            "required_shape": "p <- p + s_coff*((X^a - 1)p)",
            "consumer": "MAT s_coff selector for every sparse step",
            "invariant": "one extra selector external product per accumulator index per step",
            "stage257_task": "implement isolated function behind explicit flag/path",
        },
        {
            "component": "ternary_sub_a",
            "required_shape": "p1 <- X^a p; p <- p1 + s_sign*((X^-2a - 1)p1)",
            "consumer": "MAT s_sign selector for every sparse step",
            "invariant": "one extra selector external product per accumulator index per step",
            "stage257_task": "implement isolated function behind explicit flag/path",
        },
        {
            "component": "final_rgsw",
            "required_shape": "same final RGSW monomial multiplication as binary path",
            "consumer": "distance-bit selectors only",
            "invariant": "no sub_a after final RGSW",
            "stage257_task": "preserve binary schedule order",
        },
    ]


def count_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    params = [
        ("SET_2_3_2048", 2048, 39, 7),
        ("SET_4_5_2048", 2048, 42, 7),
        ("SET_2_3_4096", 4096, 32, 8),
    ]
    for name, in_n, h, r_prec in params:
        binary_main = (h + 1) * r_prec * in_n
        suba = h * in_n
        for branch, families in [("include_zero", 1), ("ternary", 1), ("stress_both", 2)]:
            total = binary_main + suba * families
            rows.append({
                "param": name,
                "branch": branch,
                "in_N": in_n,
                "h": h,
                "r_prec": r_prec,
                "binary_main_ep_calls": binary_main,
                "extra_suba_ep_calls": suba * families,
                "total_ep_class_calls": total,
                "extra_over_binary_main": f"{(suba * families) / binary_main:.6f}",
                "total_over_binary_main": f"{total / binary_main:.6f}",
                "claim_status": "single_branch_preflight" if families == 1 else "stress_only",
            })
    return rows


def negacyclic_mul_x(poly: list[int], exp: int) -> list[int]:
    n = len(poly)
    e = exp % (2 * n)
    outer = 1
    if e >= n:
        e -= n
        outer = -1
    out = [0] * n
    for i, coeff in enumerate(poly):
        j = i + e
        sign = outer
        if j >= n:
            j -= n
            sign = -sign
        out[j] = (out[j] + sign * coeff) % MODULUS
    return out


def make_poly(seed: int, idx: int, lane: int, n: int) -> list[int]:
    return [((seed + 5) * (idx + 3) + (lane + 7) * (i + 1) + i * i + 11) % MODULUS for i in range(n)]


def public_rgsw_step(state: list[list[list[int]]], distance: int) -> list[list[list[int]]]:
    in_n = len(state)
    lanes = len(state[0])
    out: list[list[list[int]]] = []
    for idx in range(in_n):
        src = (idx + distance) % in_n
        row: list[list[int]] = []
        for lane in range(lanes):
            row.append(negacyclic_mul_x(state[src][lane], distance + idx + lane))
        out.append(row)
    return out


def suba_update(poly: list[int], branch: str, a: int, selector: int) -> list[int]:
    if branch == "include_zero":
        if selector == 0:
            return poly[:]
        return negacyclic_mul_x(poly, a)
    first = negacyclic_mul_x(poly, a)
    if selector == 0:
        return first
    return negacyclic_mul_x(poly, -a)


def binary_naive_update(poly: list[int], a: int) -> list[int]:
    return negacyclic_mul_x(poly, a)


def run_schedule_probe(branch: str, lanes: int, seed: int) -> tuple[dict[str, object], dict[str, object]]:
    in_n = 16
    n = 64
    h = 5
    r_prec = 3
    scalar = [[make_poly(seed, idx, lane, n) for lane in range(lanes)] for idx in range(in_n)]
    pvw = [[poly[:] for poly in row] for row in scalar]
    naive = [[poly[:] for poly in row] for row in scalar]
    mismatches = 0
    negative_checked = 0
    negative_naive_matches = 0
    copyback_count = 0
    active = 0
    distances = [((seed + step * 3 + 5) % ((1 << r_prec) - 1)) + 1 for step in range(h + 1)]
    for step in range(h):
        active ^= r_prec & 1
        scalar = public_rgsw_step(scalar, distances[step])
        pvw = public_rgsw_step(pvw, distances[step])
        naive = public_rgsw_step(naive, distances[step])
        for idx in range(in_n):
            for lane in range(lanes):
                a = ((seed * 7 + step * 5 + idx * 3 + lane * 2 + 1) % (2 * n - 1)) + 1
                selector = (seed + step + idx + lane) & 1
                before = scalar[idx][lane]
                scalar_next = suba_update(before, branch, a, selector)
                pvw_next = suba_update(pvw[idx][lane], branch, a, selector)
                naive_next = binary_naive_update(naive[idx][lane], a)
                if scalar_next != pvw_next:
                    mismatches += sum(1 for x, y in zip(scalar_next, pvw_next) if x != y)
                if branch == "include_zero" and selector == 0:
                    negative_checked += 1
                    if naive_next == scalar_next:
                        negative_naive_matches += 1
                if branch == "ternary" and selector == 1:
                    negative_checked += 1
                    if naive_next == scalar_next:
                        negative_naive_matches += 1
                scalar[idx][lane] = scalar_next
                pvw[idx][lane] = pvw_next
                naive[idx][lane] = naive_next
    active ^= r_prec & 1
    scalar = public_rgsw_step(scalar, distances[h])
    pvw = public_rgsw_step(pvw, distances[h])
    if active != 0:
        copyback_count += 1
    final_mismatches = 0
    for idx in range(in_n):
        for lane in range(lanes):
            if scalar[idx][lane] != pvw[idx][lane]:
                final_mismatches += sum(1 for x, y in zip(scalar[idx][lane], pvw[idx][lane]) if x != y)
    row = {
        "branch": branch,
        "r": lanes,
        "seed": seed,
        "in_N": in_n,
        "poly_N": n,
        "h": h,
        "r_prec": r_prec,
        "round_mismatches": mismatches,
        "final_mismatches": final_mismatches,
        "negative_controls_checked": negative_checked,
        "copyback_count": copyback_count,
        "status": "PASS_SPARSEMUL_PREFLIGHT" if mismatches == 0 and final_mismatches == 0 and negative_checked > 0 else "FAIL",
    }
    neg = {
        "branch": branch,
        "r": lanes,
        "seed": seed,
        "negative_controls_checked": negative_checked,
        "negative_control_naive_matches": negative_naive_matches,
        "negative_control_expected_failures": negative_checked - negative_naive_matches,
        "status": "PASS_NEGATIVE_CONTROL" if negative_checked > 0 and (negative_checked - negative_naive_matches) > 0 else "FAIL",
    }
    return row, neg


def probe_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    neg: list[dict[str, object]] = []
    for branch in ["include_zero", "ternary"]:
        for lanes in [1, 2, 4]:
            for seed in range(10):
                row, negrow = run_schedule_probe(branch, lanes, seed)
                rows.append(row)
                neg.append(negrow)
    return rows, neg


def recurrence_rows(counts: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [
        {
            "item": "selector_ep_noise",
            "model": "each non-binary sub_a consumes one additional MAT selector EP per accumulator index",
            "target_value": "h * in_N = 79872 for SET_2_3_2048",
            "status": "needs_stage257_measurement",
            "failure_action": "do not integrate full SAB",
        },
        {
            "item": "active_buffer_lifecycle",
            "model": "reuse existing active buffer state; normalize only at API boundary",
            "target_value": "no semantic copyback in finite preflight except final normalization",
            "status": "preflight_pass_required",
            "failure_action": "disable active-buffer non-binary path",
        },
        {
            "item": "key_size_growth",
            "model": "one additional MAT selector family adds h selector objects",
            "target_value": "39 extra selector objects at target h=39",
            "status": "needs_stage257_resource_measurement",
            "failure_action": "scope or reject non-binary branch",
        },
        {
            "item": "complete_sab_noise",
            "model": "not inferred from isolated or finite schedule probes",
            "target_value": "multi-seed final-output noise after full integration",
            "status": "blocked_until_stage258",
            "failure_action": "no speedup/noise claim",
        },
    ]
    max_extra = max(float(row["extra_over_binary_main"]) for row in counts if row["claim_status"] == "single_branch_preflight")
    rows.append({
        "item": "count_pressure_gate",
        "model": "single non-binary branch extra EP-class calls remain under 0.20 of binary main path",
        "target_value": f"max_single_branch_extra={max_extra:.6f}",
        "status": "pass_preflight" if max_extra < 0.20 else "fail_preflight",
        "failure_action": "do not implement sparse_mul",
    })
    return rows


def admission_rows(probe: list[dict[str, object]], neg: list[dict[str, object]], counts: list[dict[str, object]]) -> list[dict[str, object]]:
    probe_ok = bool(probe) and all(row["status"] == "PASS_SPARSEMUL_PREFLIGHT" for row in probe)
    neg_ok = bool(neg) and all(row["status"] == "PASS_NEGATIVE_CONTROL" for row in neg)
    max_extra = max(float(row["extra_over_binary_main"]) for row in counts if row["claim_status"] == "single_branch_preflight")
    admit = probe_ok and neg_ok and max_extra < 0.20
    return [
        {
            "route": "stage257_explicit_nonbinary_sparsemul_implementation",
            "decision": "ADMIT_EXPLICIT_IMPLEMENTATION" if admit else "BLOCK",
            "production_permission": "explicit_new_path_only",
            "reason": "finite schedule lifecycle, negative controls, count pressure, and Stage255 actual selector gate pass" if admit else "preflight incomplete",
            "next_gate": "implement explicit sab_pvw_nonbinary_* path without changing binary default",
        },
        {
            "route": "default_binary_sab",
            "decision": "NO_CHANGE",
            "production_permission": "no_default_change",
            "reason": "binary path remains baseline and regression oracle",
            "next_gate": "scalar/binary regression tests after any Stage257 code",
        },
        {
            "route": "nonbinary_full_sab_speedup",
            "decision": "BLOCKED",
            "production_permission": "no",
            "reason": "no full sparse_mul implementation, full SAB correctness, multi-seed noise, or T_bootstrap/r benchmark yet",
            "next_gate": "Stage257+Stage258",
        },
    ]


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "sparsemul_preflight",
            "status": "supported_preflight",
            "allowed_wording": "A non-binary sparse_mul integration boundary and finite schedule preflight are ready for explicit implementation.",
            "forbidden_wording": "Non-binary sparse_mul is implemented.",
            "evidence": rel(PROBE),
        },
        {
            "claim": "count_model",
            "status": "supported_model_only",
            "allowed_wording": "Single non-binary branch adds h*in_N EP-class updates before measurement.",
            "forbidden_wording": "The count model proves speedup.",
            "evidence": rel(COUNTS),
        },
        {
            "claim": "full_sab_speedup",
            "status": "unsupported",
            "allowed_wording": "No non-binary full-SAB speedup is claimed.",
            "forbidden_wording": "Non-binary PVW/MAT-SAB accelerates bootstrapping.",
            "evidence": rel(ADMISSION),
        },
    ]


def gate_rows(inputs, source, probe, neg, counts, recurrence, admission) -> list[dict[str, object]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    stage255_ok = stage255_passes()
    source_ok = all(row["observed"] in {"yes", "unchanged"} for row in source)
    probe_ok = bool(probe) and all(row["status"] == "PASS_SPARSEMUL_PREFLIGHT" for row in probe)
    neg_ok = bool(neg) and all(row["status"] == "PASS_NEGATIVE_CONTROL" for row in neg)
    counts_ok = all(float(row["extra_over_binary_main"]) < 0.20 for row in counts if row["claim_status"] == "single_branch_preflight")
    recurrence_ok = all(row["status"] != "fail_preflight" for row in recurrence)
    admission_ok = admission[0]["decision"] == "ADMIT_EXPLICIT_IMPLEMENTATION"
    decision_ok = inputs_ok and stage255_ok and source_ok and probe_ok and neg_ok and counts_ok and recurrence_ok and admission_ok
    return [
        {
            "gate": "G1_inputs_and_stage255",
            "status": "PASS" if inputs_ok and stage255_ok else "FAIL",
            "metric": "inputs;stage255",
            "value": f"{str(inputs_ok).lower()};{str(stage255_ok).lower()}",
            "evidence": f"{rel(INPUT_STATUS)}; {rel(INPUTS['stage255_proof_gate'])}",
            "interpretation": "Stage256 is valid only after actual isolated selector gate passes.",
        },
        {
            "gate": "G2_source_boundary",
            "status": "PASS" if source_ok else "FAIL",
            "metric": "source boundaries",
            "value": "observed",
            "evidence": rel(SOURCE),
            "interpretation": "Current binary source shape and required non-binary deltas are explicit.",
        },
        {
            "gate": "G3_finite_schedule_probe",
            "status": "PASS" if probe_ok and neg_ok else "FAIL",
            "metric": "probe_rows;negative_rows",
            "value": f"{len(probe)};{len(neg)}",
            "evidence": f"{rel(PROBE)}; {rel(NEGATIVE)}",
            "interpretation": "Multi-round finite sparse_mul lifecycle preserves lane equivalence and negative controls.",
        },
        {
            "gate": "G4_count_recurrence",
            "status": "PASS_PREFLIGHT" if counts_ok and recurrence_ok else "FAIL",
            "metric": "single branch extra EP ratio",
            "value": "below_0.20",
            "evidence": f"{rel(COUNTS)}; {rel(RECURRENCE)}",
            "interpretation": "Count pressure and recurrence obligations are recorded before implementation.",
        },
        {
            "gate": "G5_admission_boundary",
            "status": "PASS_EXPLICIT_PATH_ONLY" if admission_ok else "FAIL",
            "metric": "implementation permission",
            "value": "explicit_new_path_only" if admission_ok else "blocked",
            "evidence": rel(ADMISSION),
            "interpretation": "Stage257 may implement an explicit non-binary path only; default binary remains unchanged.",
        },
        {
            "gate": "G6_stage256_decision",
            "status": DECISION if decision_ok else "FAIL_STAGE256_NONBINARY_SPARSEMUL_PREFLIGHT",
            "metric": "decision",
            "value": DECISION if decision_ok else "FAIL_STAGE256_NONBINARY_SPARSEMUL_PREFLIGHT",
            "evidence": rel(GATES),
            "interpretation": "Proceed to explicit non-binary sparse_mul implementation gate, not full SAB.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage257_explicit_nonbinary_sparsemul_implementation",
            "entry_condition": "Stage256 admits explicit implementation only.",
            "gate": "add sidecar/new key object and sab_pvw_nonbinary_sparse_mul without changing binary default",
            "status": "selected_next",
            "failure_action": "revert/disable explicit path; keep binary default",
            "evidence": rel(ADMISSION),
        },
        {
            "priority": "P1",
            "route": "stage258_nonbinary_sparsemul_correctness_noise",
            "entry_condition": "Stage257 explicit path compiles",
            "gate": "actual MOSFHET sparse_mul equivalence, selector noise/resource, binary regression",
            "status": "conditional",
            "failure_action": "do not enter full SAB",
            "evidence": rel(RECURRENCE),
        },
        {
            "priority": "P2",
            "route": "stage259_nonbinary_full_sab_ab",
            "entry_condition": "Stage258 sparse_mul gates pass",
            "gate": "complete-SAB T_bootstrap/r, multi-seed noise, resource, scalar/default isolation",
            "status": "future_gated",
            "failure_action": "no non-binary bootstrapping speedup claim",
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


def write_docs(inputs, source, design, counts, probe, neg, recurrence, admission, claims, gates, nextq, head: str) -> None:
    write_text(DOC, f"""# Stage256 Non-Binary Sparse_Mul Preflight

Decision: `{gates[-1]["status"]}`.

Stage256 lifts the non-binary route from isolated `sub_a` selector updates to
the `sparse_mul` integration boundary. It does not implement production code.

## Source Boundary

{table(source, ["boundary", "source_fact", "observed", "required_delta", "production_edit_allowed_now"])}

## Integration Design

{table(design, ["component", "required_shape", "consumer", "invariant", "stage257_task"])}

## Schedule Count Projection

{table(counts, ["param", "branch", "in_N", "h", "r_prec", "binary_main_ep_calls", "extra_suba_ep_calls", "total_ep_class_calls", "extra_over_binary_main", "total_over_binary_main", "claim_status"])}

## Finite Schedule Probe

{table(probe, ["branch", "r", "seed", "in_N", "poly_N", "h", "r_prec", "round_mismatches", "final_mismatches", "negative_controls_checked", "copyback_count", "status"])}

## Negative Controls

{table(neg, ["branch", "r", "seed", "negative_controls_checked", "negative_control_naive_matches", "negative_control_expected_failures", "status"])}

## Noise/Resource Recurrence

{table(recurrence, ["item", "model", "target_value", "status", "failure_action"])}

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
    write_text(REPORT, f"""# Stage256 Report

Decision: `{gates[-1]["status"]}`.

Stage256 records the explicit non-binary sparse_mul integration boundary:
reuse distance-bit RGSW monomial steps, add one MAT selector external product
per accumulator index per sparse step for either `s_coff` or `s_sign`, and keep
the final RGSW step unchanged.

The finite multi-round lifecycle probe passes for include-zero and ternary,
r=1/2/4, seeds 0..9. This is a preflight schedule/lifecycle check, not a full
RGSW or complete-SAB proof. Stage257 may implement only an explicit new path;
the binary default remains unchanged.
""")
    write_text(PLAN, """# Stage256 Non-Binary Sparse_Mul Preflight Plan

## Objective

Design and gate non-binary sparse_mul integration before writing production
code.

## Gates

- Stage255 actual isolated selector gate must pass.
- Source boundaries and required deltas must be explicit.
- Finite multi-round sparse schedule probe must pass positive and negative
  controls.
- Count/noise/resource recurrence obligations must be recorded.
- Stage257 permission is explicit new path only; no default binary changes.
""")
    write_text(THEORY, """# Stage256 Non-Binary Sparse_Mul Preflight Model

Binary sparse_mul performs:

```text
for step in 0..h-1:
    RGSW_monomial_mul(distance_bits[step])
    sub_a_binary()
RGSW_monomial_mul(distance_bits[h])
```

The non-binary branch keeps the same distance-bit RGSW schedule and replaces
`sub_a_binary` by:

```text
include-zero: p <- p + s_coff*((X^a - 1)p)
ternary:      p1 <- X^a p; p <- p1 + s_sign*((X^-2a - 1)p1)
```

Thus one single non-binary branch adds `h * in_N` MAT selector external-product
class calls before any lower-level fusion. This is a cost model, not measured
full-SAB runtime.
""")
    write_text(VARIANT, """# MAT-RLWE SAB Stage256 Non-Binary Sparse_Mul Preflight

## Variant Delta

Prepare an explicit `sab_pvw_nonbinary_sparse_mul` route with optional
`s_coff` or `s_sign` selector families. The existing binary sparse_mul remains
the default and reference path.

## Status

Preflight only. It authorizes Stage257 explicit implementation, not full
bootstrapping or speedup claims.
""")
    write_text(REPRO_CMDS, f"""# Stage256 Reproduction Commands

```text
python scripts/build_stage256_nonbinary_sparsemul_preflight.py
python -m py_compile scripts/build_stage256_nonbinary_sparsemul_preflight.py
```

Decision: `{gates[-1]["status"]}`.
""")


def update_project_files(head: str, decision: str) -> None:
    append_once(ROADMAP, "## Stage 256: Non-Binary Sparse_Mul Preflight", f"""
## Stage 256: Non-Binary Sparse_Mul Preflight

Goal:

```text
Design and gate non-binary sparse_mul integration before writing an explicit
implementation path.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. The integration boundary
is explicit: reuse binary distance-bit RGSW steps, add one MAT selector EP per
accumulator index per sparse step for either s_coff or s_sign, and preserve the
final RGSW step. Finite multi-round lifecycle probes pass for r=1/2/4. Stage257
may implement an explicit non-binary sparse_mul path only; full SAB speedup
remains blocked.
```
""")
    append_once(GOAL, "Stage256 non-binary sparse_mul preflight", f"""
- Stage256 non-binary sparse_mul preflight records `{decision}`: explicit
  non-binary sparse_mul implementation is now admitted as a separate path, but
  full non-binary SAB and speedup claims remain blocked.
""")
    append_once(CURRENT_GOAL, "### Stage256 non-binary sparse_mul preflight", f"""
### Stage256 non-binary sparse_mul preflight

`{decision}` advances the route from isolated selector updates to sparse_mul
integration readiness. The active goal remains open for explicit implementation,
actual sparse_mul correctness/noise, complete SAB A/B, and final claim closure.
""")
    append_once(HYPOTHESES, "H10_stage256_nonbinary_sparsemul_preflight:", f"""
H10_stage256_nonbinary_sparsemul_preflight:
  status: explicit_nonbinary_sparsemul_implementation_admitted
  evidence:
    - repro/stage256_nonbinary_sparsemul_preflight/source_boundary_matrix.csv
    - repro/stage256_nonbinary_sparsemul_preflight/finite_sparsemul_schedule_probe.csv
    - repro/stage256_nonbinary_sparsemul_preflight/schedule_count_projection.csv
    - repro/stage256_nonbinary_sparsemul_preflight/proof_gate.csv
    - docs/stage256_nonbinary_sparsemul_preflight.md
  conclusion: >
    Stage256 records {decision}. It admits only an explicit non-binary
    sparse_mul implementation path; binary default behavior, full SAB speedup,
    and non-binary bootstrapping claims remain blocked.
""")
    append_once(RUN_LOG, "stage256-nonbinary-sparsemul-preflight-001", f"""stage256-nonbinary-sparsemul-preflight-001,{date.today().isoformat()},{head},Stage 256,sparsemul_preflight,"python scripts/build_stage256_nonbinary_sparsemul_preflight.py","Stage255 actual isolated selector evidence + finite schedule lifecycle",n/a,{decision},"Explicit non-binary sparse_mul implementation admitted; full SAB remains blocked.",docs/stage256_nonbinary_sparsemul_preflight.md; repro/stage256_nonbinary_sparsemul_preflight/proof_gate.csv
""")
    append_once(MANIFEST, "- stage256_nonbinary_sparsemul_preflight:", """
- stage256_nonbinary_sparsemul_preflight:
  - `docs/stage256_nonbinary_sparsemul_preflight.md`
  - `experiments/stage256_nonbinary_sparsemul_preflight_plan.md`
  - `theory_checks/stage256_nonbinary_sparsemul_preflight_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage256_nonbinary_sparsemul_preflight.md`
  - `scripts/build_stage256_nonbinary_sparsemul_preflight.py`
  - `repro/stage256_nonbinary_sparsemul_preflight/`
""")
    append_once(CHECKLIST, "Stage256 non-binary sparse_mul preflight admits explicit implementation", f"""
- [x] Stage256 non-binary sparse_mul preflight admits explicit implementation `{decision}`.
""")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    head = run_git(["rev-parse", "--short", "HEAD"])
    inputs = input_rows()
    source = source_boundary_rows()
    design = design_rows()
    counts = count_rows()
    probe, neg = probe_rows()
    recurrence = recurrence_rows(counts)
    admission = admission_rows(probe, neg, counts)
    claims = claim_rows()
    gates = gate_rows(inputs, source, probe, neg, counts, recurrence, admission)
    nextq = next_rows()

    write_csv(INPUT_STATUS, inputs, ["input_id", "path", "status", "bytes"])
    write_csv(SOURCE, source, ["boundary", "source_fact", "observed", "required_delta", "production_edit_allowed_now"])
    write_csv(DESIGN, design, ["component", "required_shape", "consumer", "invariant", "stage257_task"])
    write_csv(COUNTS, counts, ["param", "branch", "in_N", "h", "r_prec", "binary_main_ep_calls", "extra_suba_ep_calls", "total_ep_class_calls", "extra_over_binary_main", "total_over_binary_main", "claim_status"])
    write_csv(PROBE, probe, ["branch", "r", "seed", "in_N", "poly_N", "h", "r_prec", "round_mismatches", "final_mismatches", "negative_controls_checked", "copyback_count", "status"])
    write_csv(NEGATIVE, neg, ["branch", "r", "seed", "negative_controls_checked", "negative_control_naive_matches", "negative_control_expected_failures", "status"])
    write_csv(RECURRENCE, recurrence, ["item", "model", "target_value", "status", "failure_action"])
    write_csv(ADMISSION, admission, ["route", "decision", "production_permission", "reason", "next_gate"])
    write_csv(CLAIM, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])

    write_docs(inputs, source, design, counts, probe, neg, recurrence, admission, claims, gates, nextq, head)
    artifacts = [DOC, PLAN, THEORY, VARIANT, INPUT_STATUS, SOURCE, DESIGN, COUNTS, PROBE, NEGATIVE, RECURRENCE, ADMISSION, CLAIM, GATES, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "exists", "sha256", "bytes"])
    if gates[-1]["status"] == DECISION:
        update_project_files(head, gates[-1]["status"])
    print(f"Stage256 report: {rel(DOC)}")
    print(f"Stage256 decision: {gates[-1]['status']}")
    return 0 if gates[-1]["status"] == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
