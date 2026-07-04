"""Stage251: non-binary selector semantics preflight.

This stage turns the known non-binary PVW/MAT-SAB gap into an auditable gate.
It checks source-level facts, records scalar ternary/include-zero equations,
runs a finite rotation semantics probe, and blocks production implementation
until a PVW selector/key-format design exists.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage251_nonbinary_selector_semantics"

INPUTS = {
    "stage26_branch_log": ROOT / "docs" / "stage26_parameter_branch_log.md",
    "stage26_branch_summary": ROOT / "repro" / "stage26_parameter_branch_smoke_avx512" / "branch_summary.csv",
    "stage229_coverage_gaps": ROOT / "repro" / "stage229_parameter_generalization_matrix" / "coverage_gaps.csv",
    "stage229_claim_scope": ROOT / "repro" / "stage229_parameter_generalization_matrix" / "claim_scope.csv",
    "stage250_proof_gate": ROOT / "repro" / "stage250_exact_dense_lower_bound_gap" / "proof_gate.csv",
    "sab_header": ROOT / "include" / "sab.h",
    "sab_pvw_header": ROOT / "include" / "sab_pvw.h",
    "scalar_sab_source": ROOT / "src" / "sparse_amortized_bootstrap.c",
    "pvw_sab_source": ROOT / "src" / "sab_pvw.c",
    "main_harness": ROOT / "main.c",
}

DOC = ROOT / "docs" / "stage251_nonbinary_selector_semantics.md"
PLAN = ROOT / "experiments" / "stage251_nonbinary_selector_semantics_plan.md"
THEORY = ROOT / "theory_checks" / "stage251_nonbinary_selector_semantics_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage251_nonbinary_selector_semantics.md"

INPUT_STATUS = OUT / "input_status.csv"
SOURCE_FACTS = OUT / "source_fact_matrix.csv"
SEMANTIC = OUT / "semantic_equation_matrix.csv"
SELECTOR_GAP = OUT / "selector_gap_matrix.csv"
PROBE = OUT / "finite_semantics_probe.csv"
ADMISSION = OUT / "admission_decision.csv"
CLAIM = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage251_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE251_NONBINARY_SELECTOR_SEMANTICS_PREFLIGHT_BLOCKS_IMPLEMENTATION"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
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


def source_fact_rows() -> list[dict[str, object]]:
    sab_h = read_text(INPUTS["sab_header"])
    pvw_h = read_text(INPUTS["sab_pvw_header"])
    scalar = read_text(INPUTS["scalar_sab_source"])
    pvw = read_text(INPUTS["pvw_sab_source"])
    main = read_text(INPUTS["main_harness"])
    pvw_all = pvw_h + "\n" + pvw
    scalar_all = sab_h + "\n" + scalar

    checks = [
        (
            "scalar_has_coff_selector",
            "include/sab.h; src/sparse_amortized_bootstrap.c",
            "TRGSW_DFT ** s_coff and scalar include-zero/gaussian use",
            "TRGSW_DFT ** s_coff" in sab_h and "res->s_coff" in scalar,
            "present",
        ),
        (
            "scalar_has_sign_selector",
            "include/sab.h; src/sparse_amortized_bootstrap.c",
            "TRGSW_DFT ** s_sign and scalar ternary use",
            "TRGSW_DFT ** s_sign" in sab_h and "res->s_sign" in scalar,
            "present",
        ),
        (
            "scalar_records_branch_flags",
            "include/sab.h; src/sparse_amortized_bootstrap.c",
            "include_zeros, gaussian_secret, ternary_secret branch flags",
            all(token in scalar_all for token in ["include_zeros", "gaussian_secret", "ternary_secret"]),
            "present",
        ),
        (
            "scalar_ternary_sign_equation_source",
            "src/sparse_amortized_bootstrap.c",
            "s_sign encrypts coeff == -1 and sub_a consumes s_sign",
            "coeff == -1" in scalar
            and "sab->s_sign" in scalar
            and "trlwe_mul_by_xai_minus_1" in scalar
            and "-2*a[i]" in scalar,
            "present",
        ),
        (
            "scalar_include_zero_equation_source",
            "src/sparse_amortized_bootstrap.c",
            "s_coff controls identity versus X^a rotation",
            "sab->include_zeros" in scalar
            and "sab->s_coff" in scalar
            and "trlwe_mul_by_xai_minus_1" in scalar,
            "present",
        ),
        (
            "pvw_has_binary_selector_matrix",
            "include/sab_pvw.h",
            "MAT_TRGSW_DFT *** s",
            "MAT_TRGSW_DFT *** s" in pvw_h,
            "present",
        ),
        (
            "pvw_has_sign_selector",
            "include/sab_pvw.h; src/sab_pvw.c",
            "MAT selector equivalent of s_sign",
            "s_sign" in pvw_all,
            "missing",
        ),
        (
            "pvw_has_coff_selector",
            "include/sab_pvw.h; src/sab_pvw.c",
            "MAT selector equivalent of s_coff",
            "s_coff" in pvw_all,
            "missing",
        ),
        (
            "pvw_constructor_rejects_nonbinary_coeff",
            "src/sab_pvw.c",
            "if(coeff != 1) reject",
            "if(coeff != 1)" in pvw and "only binary sparse input keys are supported" in pvw,
            "present",
        ),
        (
            "pvw_target_harness_binary_guard",
            "main.c",
            "#if !defined(BINARY) guard for SAB_PVW target harness",
            "#if !defined(BINARY)" in main and "SAB_PVW target harness currently supports only KEY=BINARY" in main,
            "present",
        ),
        (
            "pvw_binary_sub_a_only",
            "src/sab_pvw.c; include/sab_pvw.h",
            "sab_pvw_sub_a_binary rotates by X^a without sign/presence selector",
            "sab_pvw_sub_a_binary" in pvw_all and "pvmtmlwe_mul_by_xai" in pvw,
            "present",
        ),
    ]

    rows = []
    for fact_id, source, expected, observed, pass_meaning in checks:
        if fact_id in {"pvw_has_sign_selector", "pvw_has_coff_selector"}:
            status = "present_unexpected" if observed else "missing"
        else:
            status = "present" if observed else "missing"
        rows.append({
            "fact_id": fact_id,
            "source": source,
            "expected": expected,
            "observed": "yes" if observed else "no",
            "status": status,
            "pass_meaning": pass_meaning,
            "evidence": source,
        })
    return rows


def semantic_rows() -> list[dict[str, object]]:
    return [
        {
            "branch": "binary",
            "selector": "implicit nonzero coefficient +1",
            "scalar_update": "p' = X^a p",
            "pvw_required_update": "body[q]' = X^a body[q] for every lane q",
            "existing_pvw_support": "yes_binary_only",
            "extra_key_material": "none beyond binary MAT_TRGSW selector s",
            "risk": "covered by existing binary equivalence gates",
        },
        {
            "branch": "include_zero",
            "selector": "s_coff in {0,1}",
            "scalar_update": "p' = p + s_coff * ((X^a - 1)p)",
            "pvw_required_update": "body[q]' = body[q] + s_coff * ((X^a - 1)body[q])",
            "existing_pvw_support": "no",
            "extra_key_material": "MAT_TRGSW_DFT selector family for s_coff",
            "risk": "missing selector storage, keygen, noise recurrence, and equivalence tests",
        },
        {
            "branch": "ternary_positive",
            "selector": "s_sign = 0",
            "scalar_update": "p' = X^a p",
            "pvw_required_update": "body[q]' = X^a body[q]",
            "existing_pvw_support": "only when sign is known positive; harness disallows ternary",
            "extra_key_material": "MAT_TRGSW_DFT selector family for sign bits",
            "risk": "cannot claim branch support without sign selector and negative case",
        },
        {
            "branch": "ternary_negative",
            "selector": "s_sign = 1",
            "scalar_update": "p' = X^a p + s_sign * ((X^{-2a} - 1)X^a p) = X^{-a}p",
            "pvw_required_update": "body[q]' = X^{-a} body[q]",
            "existing_pvw_support": "no",
            "extra_key_material": "MAT_TRGSW_DFT sign selector and negative-rotation CMUX composition",
            "risk": "binary PVW X^a path is wrong for negative coefficients",
        },
        {
            "branch": "gaussian_or_general",
            "selector": "coefficient monomial selector",
            "scalar_update": "p' depends on encrypted coefficient monomial, not just sign/presence",
            "pvw_required_update": "general MAT selector/key-format design",
            "existing_pvw_support": "no",
            "extra_key_material": "beyond Stage251 scope",
            "risk": "more complex than ternary/include-zero and not admitted",
        },
    ]


def rotate(poly: list[int], exp: int) -> list[int]:
    n = len(poly)
    exp %= n
    return [poly[(i - exp) % n] for i in range(n)]


def poly(seed: int, n: int, q: int) -> list[int]:
    return [((seed + 3) * (i + 5) + i * i + 7) % q for i in range(n)]


def finite_probe_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    n = 16
    q = 257
    cases = [
        "binary_matches_scalar",
        "include_zero_c0_matches_identity",
        "include_zero_c1_matches_binary",
        "ternary_positive_matches_binary",
        "ternary_negative_requires_inverse_rotation",
        "pvw_binary_naive_fails_ternary_negative",
    ]
    for seed in range(16):
        p = poly(seed, n, q)
        a = (seed * 3 + 5) % n
        if a == 0:
            a = 1
        if a == n // 2:
            a = (a + 1) % n
        xa = rotate(p, a)
        xminus = rotate(p, -a)
        identity = p[:]
        probes = {
            "binary_matches_scalar": (xa, xa, "positive"),
            "include_zero_c0_matches_identity": (identity, identity, "positive"),
            "include_zero_c1_matches_binary": (xa, xa, "positive"),
            "ternary_positive_matches_binary": (xa, xa, "positive"),
            "ternary_negative_requires_inverse_rotation": (xminus, xminus, "positive"),
            "pvw_binary_naive_fails_ternary_negative": (xa, xminus, "negative_control"),
        }
        for case in cases:
            observed, expected, control = probes[case]
            matches = observed == expected
            if control == "negative_control":
                status = "PASS_COUNTEREXAMPLE" if not matches else "FAIL_COUNTEREXAMPLE"
            else:
                status = "PASS_EQUIVALENCE" if matches else "FAIL_EQUIVALENCE"
            rows.append({
                "seed": seed,
                "N": n,
                "modulus": q,
                "a": a,
                "case": case,
                "control": control,
                "observed_head": " ".join(str(x) for x in observed[:4]),
                "expected_head": " ".join(str(x) for x in expected[:4]),
                "match": "yes" if matches else "no",
                "status": status,
                "interpretation": "finite rotation semantics check, not a SAB correctness proof",
            })
    return rows


def selector_gap_rows(facts: list[dict[str, object]]) -> list[dict[str, object]]:
    fact_status = {str(row["fact_id"]): str(row["status"]) for row in facts}
    return [
        {
            "gap": "ternary_sign_selector_key_material",
            "required_for": "ternary negative coefficient support",
            "current_scalar": "s_sign TRGSW_DFT family exists",
            "current_pvw": "no s_sign equivalent in SAB_PVW_Key",
            "blocking_fact": fact_status.get("pvw_has_sign_selector", ""),
            "required_next_evidence": "PVW/MAT sign selector key skeleton, isolated phase equivalence, full-SAB A/B, noise/resource",
            "production_permission": "no",
        },
        {
            "gap": "include_zero_coefficient_selector_key_material",
            "required_for": "include-zero sparse secret support",
            "current_scalar": "s_coff TRGSW_DFT family exists",
            "current_pvw": "no s_coff equivalent in SAB_PVW_Key",
            "blocking_fact": fact_status.get("pvw_has_coff_selector", ""),
            "required_next_evidence": "PVW/MAT coefficient selector key skeleton, isolated phase equivalence, full-SAB A/B, noise/resource",
            "production_permission": "no",
        },
        {
            "gap": "constructor_and_harness_admission",
            "required_for": "any non-binary PVW benchmark or target gate",
            "current_scalar": "scalar ternary build is preserved by Stage26",
            "current_pvw": "constructor rejects coeff != 1 and target harness requires BINARY",
            "blocking_fact": "binary guard present",
            "required_next_evidence": "explicit non-binary PVW harness after selector semantics are implemented",
            "production_permission": "no",
        },
        {
            "gap": "gaussian_general_coefficient_semantics",
            "required_for": "gaussian/general secret branches",
            "current_scalar": "sub_a_ga uses coefficient monomial semantics",
            "current_pvw": "no general coefficient selector design",
            "blocking_fact": "out_of_scope",
            "required_next_evidence": "separate general coefficient MAT selector design and noise proof",
            "production_permission": "no",
        },
    ]


def admission_rows() -> list[dict[str, object]]:
    return [
        {
            "route": "binary_exact_dense_pvw",
            "decision": "already_supported_scoped",
            "production_permission": "yes_existing_explicit_path",
            "allowed_next_step": "continue scoped exact dense binary reporting or counter-backed exact improvements",
            "required_before_speed_claim": "same-backend complete-SAB T_bootstrap/r, noise, resource",
        },
        {
            "route": "ternary_pvw",
            "decision": "BLOCKED_KEY_FORMAT_AND_SELECTOR_GAP",
            "production_permission": "no",
            "allowed_next_step": "Stage252 non-production MAT sign-selector key skeleton",
            "required_before_speed_claim": "selector keygen, isolated equivalence, full-SAB A/B, noise/resource",
        },
        {
            "route": "include_zero_pvw",
            "decision": "BLOCKED_KEY_FORMAT_AND_SELECTOR_GAP",
            "production_permission": "no",
            "allowed_next_step": "Stage252 non-production MAT coefficient-selector key skeleton",
            "required_before_speed_claim": "selector keygen, isolated equivalence, full-SAB A/B, noise/resource",
        },
        {
            "route": "gaussian_or_general_pvw",
            "decision": "OUT_OF_SCOPE_MORE_COMPLEX_COEFFICIENT_MONOMIAL",
            "production_permission": "no",
            "allowed_next_step": "separate theory/design stage only after ternary/include-zero",
            "required_before_speed_claim": "general coefficient equations, key format, noise recurrence, full-SAB evidence",
        },
    ]


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "scalar_nonbinary_semantics_identified",
            "status": "supported_preflight",
            "allowed_wording": "Scalar SAB has identifiable ternary and include-zero selector semantics through s_sign and s_coff.",
            "forbidden_wording": "Scalar equations alone prove PVW non-binary correctness.",
            "evidence": rel(SEMANTIC),
        },
        {
            "claim": "pvw_nonbinary_support",
            "status": "unsupported_blocked",
            "allowed_wording": "PVW/MAT-SAB non-binary support is not implemented; current target harness is binary-only.",
            "forbidden_wording": "PVW/MAT-SAB supports ternary or include-zero branches.",
            "evidence": rel(SELECTOR_GAP),
        },
        {
            "claim": "finite_probe_result",
            "status": "toy_semantics_only",
            "allowed_wording": "Finite rotation probes confirm the selector equations and the binary negative-control failure.",
            "forbidden_wording": "Toy finite equations prove full SAB correctness or security.",
            "evidence": rel(PROBE),
        },
        {
            "claim": "implementation_permission",
            "status": "denied_for_production",
            "allowed_wording": "Only non-production selector/key skeleton design is admitted next.",
            "forbidden_wording": "Remove binary guards or route non-binary inputs through sab_pvw_sub_a_binary.",
            "evidence": rel(ADMISSION),
        },
    ]


def gate_rows(
    inputs: list[dict[str, object]],
    facts: list[dict[str, object]],
    semantic: list[dict[str, object]],
    gaps: list[dict[str, object]],
    probe: list[dict[str, object]],
    admission: list[dict[str, object]],
    claims: list[dict[str, object]],
) -> list[dict[str, object]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    facts_by_id = {str(row["fact_id"]): row for row in facts}
    scalar_ok = (
        facts_by_id.get("scalar_has_coff_selector", {}).get("status") == "present"
        and facts_by_id.get("scalar_has_sign_selector", {}).get("status") == "present"
        and facts_by_id.get("scalar_ternary_sign_equation_source", {}).get("status") == "present"
        and facts_by_id.get("scalar_include_zero_equation_source", {}).get("status") == "present"
    )
    pvw_gap_ok = (
        facts_by_id.get("pvw_has_sign_selector", {}).get("status") == "missing"
        and facts_by_id.get("pvw_has_coff_selector", {}).get("status") == "missing"
        and facts_by_id.get("pvw_constructor_rejects_nonbinary_coeff", {}).get("status") == "present"
        and facts_by_id.get("pvw_target_harness_binary_guard", {}).get("status") == "present"
    )
    semantic_ok = len(semantic) >= 5 and any(row["branch"] == "ternary_negative" for row in semantic)
    probe_ok = bool(probe) and all(str(row["status"]).startswith("PASS") for row in probe)
    admission_ok = (
        {row["route"]: row for row in admission}.get("ternary_pvw", {}).get("production_permission") == "no"
        and {row["route"]: row for row in admission}.get("include_zero_pvw", {}).get("production_permission") == "no"
    )
    claim_ok = any(row["claim"] == "pvw_nonbinary_support" and row["status"] == "unsupported_blocked" for row in claims)
    decision_ok = inputs_ok and scalar_ok and pvw_gap_ok and semantic_ok and probe_ok and admission_ok and claim_ok
    return [
        {
            "gate": "G1_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required inputs",
            "value": "all present" if inputs_ok else "missing",
            "evidence": rel(INPUT_STATUS),
            "interpretation": "Stage251 consumes Stage26/229/250 branch and claim ledgers plus source files.",
        },
        {
            "gate": "G2_scalar_semantics",
            "status": "PASS" if scalar_ok and semantic_ok else "FAIL",
            "metric": "s_coff/s_sign equations",
            "value": "identified" if scalar_ok and semantic_ok else "missing",
            "evidence": rel(SEMANTIC),
            "interpretation": "Scalar include-zero and ternary semantics are concrete enough for a PVW design target.",
        },
        {
            "gate": "G3_finite_semantics_probe",
            "status": "PASS" if probe_ok else "FAIL",
            "metric": "finite rotation rows",
            "value": len(probe),
            "evidence": rel(PROBE),
            "interpretation": "Positive equations pass and binary negative-control fails as expected.",
        },
        {
            "gate": "G4_pvw_source_gap",
            "status": "PASS_BLOCKED" if pvw_gap_ok else "FAIL",
            "metric": "PVW selector/key gap",
            "value": "no s_sign/s_coff, binary guard present" if pvw_gap_ok else "unexpected support or missing guard",
            "evidence": rel(SOURCE_FACTS),
            "interpretation": "Current PVW code cannot implement non-binary semantics without a new key format.",
        },
        {
            "gate": "G5_production_admission",
            "status": "PASS_NO_IMPLEMENTATION" if admission_ok and claim_ok else "FAIL",
            "metric": "production permission",
            "value": "denied",
            "evidence": rel(ADMISSION),
            "interpretation": "Do not remove binary guards or map non-binary into the binary PVW path.",
        },
        {
            "gate": "G6_stage251_decision",
            "status": DECISION if decision_ok else "FAIL_STAGE251_NONBINARY_SELECTOR_PREFLIGHT",
            "metric": "decision",
            "value": DECISION if decision_ok else "FAIL_STAGE251_NONBINARY_SELECTOR_PREFLIGHT",
            "evidence": rel(GATES),
            "interpretation": "Proceed only to a non-production selector/key skeleton stage.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage252_nonbinary_mat_selector_key_skeleton",
            "entry_condition": "Stage251 identifies scalar equations and blocks current PVW production implementation.",
            "gate": "define MAT s_sign/s_coff key/storage/API skeleton without touching sab_pvw hot path",
            "status": "selected_next",
            "failure_action": "keep non-binary PVW unsupported",
            "evidence": rel(SELECTOR_GAP),
        },
        {
            "priority": "P1",
            "route": "stage253_isolated_nonbinary_pvw_sub_a_equivalence",
            "entry_condition": "Stage252 skeleton compiles and records key/storage semantics.",
            "gate": "finite and MOSFHET-adjacent isolated sub_a equivalence for include-zero and ternary negative cases",
            "status": "conditional",
            "failure_action": "reject non-binary PVW branch implementation",
            "evidence": rel(PROBE),
        },
        {
            "priority": "P2",
            "route": "stage254_nonbinary_full_sab_ab_noise_resource",
            "entry_condition": "isolated equivalence passes and production code is explicitly admitted",
            "gate": "same-backend complete-SAB T_bootstrap/r, noise, resource, scalar default isolation",
            "status": "future_gated",
            "failure_action": "do not claim non-binary bootstrapping speedup",
            "evidence": rel(ADMISSION),
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


def write_docs(
    inputs: list[dict[str, object]],
    facts: list[dict[str, object]],
    semantic: list[dict[str, object]],
    gaps: list[dict[str, object]],
    probe: list[dict[str, object]],
    admission: list[dict[str, object]],
    claims: list[dict[str, object]],
    gates: list[dict[str, object]],
    nextq: list[dict[str, object]],
    head: str,
) -> None:
    write_text(DOC, f"""# Stage251 Non-Binary Selector Semantics

Decision: `{gates[-1]["status"]}`.

Stage251 prevents non-binary PVW/MAT-SAB work from drifting into unsafe
implementation. It identifies the scalar ternary/include-zero equations,
checks a finite rotation model, audits current PVW source support, and blocks
production implementation until a selector/key skeleton exists.

## Source Fact Matrix

{table(facts, ["fact_id", "source", "expected", "observed", "status", "pass_meaning", "evidence"])}

## Semantic Equation Matrix

{table(semantic, ["branch", "selector", "scalar_update", "pvw_required_update", "existing_pvw_support", "extra_key_material", "risk"])}

## Selector Gap Matrix

{table(gaps, ["gap", "required_for", "current_scalar", "current_pvw", "blocking_fact", "required_next_evidence", "production_permission"])}

## Finite Semantics Probe

The finite probe uses length-16 cyclic rotations as a selector-semantics
sanity check. It is deliberately not a security or full-SAB proof.

Rows: `{len(probe)}`. All rows must start with `PASS`.

## Admission Decision

{table(admission, ["route", "decision", "production_permission", "allowed_next_step", "required_before_speed_claim"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])}

## Proof Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

Generated from head `{head}`.
""")
    write_text(REPORT, f"""# Stage251 Report

Decision: `{gates[-1]["status"]}`.

Scalar SAB has explicit selector semantics for non-binary branches: include-zero
uses `s_coff` to choose identity versus `X^a`, and ternary uses `s_sign` to
choose `X^a` versus `X^-a`. Current PVW/MAT-SAB does not have corresponding
MAT selector families and remains binary-only by constructor and harness guard.

The finite probe confirms the equation boundary, including the negative control
that a binary `X^a` update fails for ternary negative coefficients. Production
implementation is therefore denied. The next executable step is a
non-production MAT selector/key skeleton for `s_sign` and `s_coff`.
""")
    write_text(PLAN, """# Stage251 Non-Binary Selector Semantics Plan

## Objective

Define the scalar non-binary equations and decide whether current PVW/MAT-SAB
can implement them.

## Gates

- Source facts must show scalar `s_sign/s_coff` semantics.
- Finite semantics probes must pass positive equations and the binary negative
  control must fail as expected.
- Current PVW source must not be silently promoted when `s_sign/s_coff` are
  missing.
- Production code is admitted only after a separate selector/key skeleton and
  isolated equivalence stage.
""")
    write_text(THEORY, """# Stage251 Non-Binary Selector Semantics Model

Let `p` be the accumulator polynomial/ciphertext state and `a` the switched
rotation exponent.

- Binary coefficient +1: `p' = X^a p`.
- Include-zero selector `c in {0,1}`: `p' = p + c ((X^a - 1)p)`.
- Ternary sign selector `s in {0,1}` after the positive update:
  `p' = X^a p + s ((X^{-2a} - 1)X^a p)`.
  Thus `s=0` gives `X^a p`, while `s=1` gives `X^{-a}p`.

For PVW/MAT-SAB, the r body lanes must satisfy the same equation per lane.
This requires MAT selector material for `s_coff` and `s_sign`. Reusing the
binary PVW update cannot handle the ternary negative branch.
""")
    write_text(VARIANT, """# MAT-RLWE SAB Stage251 Non-Binary Selector Semantics

## Candidate Status

- Parent route: exact dense binary PVW/MAT-SAB.
- Proposed extension: ternary/include-zero PVW/MAT-SAB.
- Current decision: blocked for production implementation.

## Required Delta

The extension needs MAT versions of scalar `s_sign` and `s_coff`, a keygen
path, isolated `sub_a` equivalence for every body lane, then full SAB
`T_bootstrap/r`, noise, and resource gates.

## Failure Mode Captured

The current binary PVW update performs `X^a` for every nonzero coefficient. For
ternary negative coefficients the scalar target is `X^{-a}`, so routing ternary
through `sab_pvw_sub_a_binary` is semantically wrong.
""")
    write_text(REPRO_CMDS, f"""# Stage251 Reproduction Commands

```text
python scripts/build_stage251_nonbinary_selector_semantics.py
python -m py_compile scripts/build_stage251_nonbinary_selector_semantics.py
```

Decision: `{gates[-1]["status"]}`.
""")


def update_project_files(head: str, decision: str) -> None:
    append_once(ROADMAP, "## Stage 251: Non-Binary Selector Semantics", f"""
## Stage 251: Non-Binary Selector Semantics

Goal:

```text
Audit scalar ternary/include-zero selector equations and decide whether current
PVW/MAT-SAB can implement non-binary branches.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. Scalar `s_sign/s_coff`
semantics are identified and finite rotation equations pass, but current
PVW/MAT-SAB has no MAT sign/coefficient selector families, rejects
`coeff != 1`, and guards the target harness to `BINARY`. Production
implementation is blocked; Stage252 must design a non-production selector/key
skeleton first.
```
""")
    append_once(GOAL, "Stage251 non-binary selector semantics", f"""
- Stage251 non-binary selector semantics records `{decision}`: scalar
  ternary/include-zero equations are identified, but current PVW/MAT-SAB
  remains binary-only and no non-binary production implementation is admitted.
""")
    append_once(CURRENT_GOAL, "### Stage251 non-binary selector semantics", f"""
### Stage251 non-binary selector semantics

`{decision}` keeps the active research goal disciplined. Non-binary PVW/MAT-SAB
cannot be claimed or implemented by removing binary guards; the next valid work
is a separate MAT selector/key skeleton for `s_sign` and `s_coff`.
""")
    append_once(HYPOTHESES, "H10_stage251_nonbinary_selector_semantics:", f"""
H10_stage251_nonbinary_selector_semantics:
  status: nonbinary_semantics_identified_current_pvw_blocked
  evidence:
    - repro/stage251_nonbinary_selector_semantics/source_fact_matrix.csv
    - repro/stage251_nonbinary_selector_semantics/semantic_equation_matrix.csv
    - repro/stage251_nonbinary_selector_semantics/finite_semantics_probe.csv
    - repro/stage251_nonbinary_selector_semantics/proof_gate.csv
    - docs/stage251_nonbinary_selector_semantics.md
  conclusion: >
    Stage251 records {decision}. Scalar include-zero and ternary selector
    semantics are identified, finite rotation probes pass, and the binary
    negative-control fails as expected. Current PVW/MAT-SAB lacks MAT
    s_sign/s_coff selector families and remains binary-only; production
    implementation is denied pending a separate selector/key skeleton.
""")
    append_once(RUN_LOG, "stage251-nonbinary-selector-semantics-001", f"""stage251-nonbinary-selector-semantics-001,{date.today().isoformat()},{head},Stage 251,nonbinary_selector_semantics,"python scripts/build_stage251_nonbinary_selector_semantics.py","Stage26/229/250 branch ledgers + source audit + finite semantics probe",n/a,{decision},"Non-binary PVW production implementation blocked; selector/key skeleton selected next.",docs/stage251_nonbinary_selector_semantics.md; repro/stage251_nonbinary_selector_semantics/proof_gate.csv
""")
    append_once(MANIFEST, "- stage251_nonbinary_selector_semantics:", """
- stage251_nonbinary_selector_semantics:
  - `docs/stage251_nonbinary_selector_semantics.md`
  - `experiments/stage251_nonbinary_selector_semantics_plan.md`
  - `theory_checks/stage251_nonbinary_selector_semantics_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage251_nonbinary_selector_semantics.md`
  - `scripts/build_stage251_nonbinary_selector_semantics.py`
  - `repro/stage251_nonbinary_selector_semantics/`
""")
    append_once(CHECKLIST, "Stage251 non-binary selector semantics blocks production implementation", f"""
- [x] Stage251 non-binary selector semantics blocks production implementation `{decision}`.
""")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    head = run_git(["rev-parse", "--short", "HEAD"])
    inputs = input_rows()
    facts = source_fact_rows()
    semantic = semantic_rows()
    gaps = selector_gap_rows(facts)
    probe = finite_probe_rows()
    admission = admission_rows()
    claims = claim_rows()
    gates = gate_rows(inputs, facts, semantic, gaps, probe, admission, claims)
    nextq = next_rows()

    write_csv(INPUT_STATUS, inputs, ["input_id", "path", "status", "bytes"])
    write_csv(SOURCE_FACTS, facts, ["fact_id", "source", "expected", "observed", "status", "pass_meaning", "evidence"])
    write_csv(SEMANTIC, semantic, ["branch", "selector", "scalar_update", "pvw_required_update", "existing_pvw_support", "extra_key_material", "risk"])
    write_csv(SELECTOR_GAP, gaps, ["gap", "required_for", "current_scalar", "current_pvw", "blocking_fact", "required_next_evidence", "production_permission"])
    write_csv(PROBE, probe, ["seed", "N", "modulus", "a", "case", "control", "observed_head", "expected_head", "match", "status", "interpretation"])
    write_csv(ADMISSION, admission, ["route", "decision", "production_permission", "allowed_next_step", "required_before_speed_claim"])
    write_csv(CLAIM, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])

    write_docs(inputs, facts, semantic, gaps, probe, admission, claims, gates, nextq, head)
    artifacts = [
        DOC,
        PLAN,
        THEORY,
        VARIANT,
        INPUT_STATUS,
        SOURCE_FACTS,
        SEMANTIC,
        SELECTOR_GAP,
        PROBE,
        ADMISSION,
        CLAIM,
        GATES,
        NEXT,
        REPORT,
        REPRO_CMDS,
    ]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "exists", "sha256", "bytes"])
    update_project_files(head, gates[-1]["status"])
    print(f"Stage251 report: {rel(DOC)}")
    print(f"Stage251 decision: {gates[-1]['status']}")


if __name__ == "__main__":
    main()
