#!/usr/bin/env python3
"""Build Stage308 SPQLIOS IFFT feasibility-audit artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage308_spqlios_ifft_feasibility_audit"
DOC = ROOT / "docs" / "stage308_spqlios_ifft_feasibility_audit.md"
THEORY = ROOT / "theory_checks" / "stage308_spqlios_ifft_feasibility_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage308_ifft_digit_routes.md"
PLAN = ROOT / "experiments" / "stage308_spqlios_ifft_feasibility_audit_plan.md"
BUILDER = ROOT / "scripts" / "build_stage308_spqlios_ifft_feasibility_audit.py"

SUMMARY = OUT / "stage308_summary.csv"
SOURCE_AUDIT = OUT / "source_interface_audit.csv"
ROUTE = OUT / "implementation_route_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage308_report.md"
ARTIFACT = OUT / "artifact_index.csv"

STAGE289 = ROOT / "repro" / "stage289_mat_dft_array_microbench" / "bench_summary.csv"
STAGE290 = ROOT / "repro" / "stage290_dft_direct_output_microbench" / "bench_summary.csv"
STAGE307_LIFECYCLE = ROOT / "repro" / "stage307_direct_ifft_lifecycle_split_profile" / "direct_lifecycle_components.csv"
STAGE307_PROOF = ROOT / "repro" / "stage307_direct_ifft_lifecycle_split_profile" / "proof_gate.csv"

SPQLIOS_HEADER = ROOT / "src" / "mosfhet" / "src" / "fft" / "spqlios" / "spqlios-fft.h"
SPQLIOS_IFFT_AVX512 = ROOT / "src" / "mosfhet" / "src" / "fft" / "spqlios" / "spqlios-ifft-avx512.s"
POLYNOMIAL_C = ROOT / "src" / "mosfhet" / "src" / "polynomial.c"
MATTRGSW_C = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION_PASS = "PASS_STAGE308_IFFT_BACKEND_LOWLEVEL_REQUIRED_DIGIT_PATH_NEXT"
DECISION_FAIL = "FAIL_STAGE308_IFFT_FEASIBILITY_AUDIT_INCOMPLETE"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


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


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def first_row(rows: List[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def stage_decision(path: Path) -> str:
    rows = read_csv(path)
    return rows[0].get("decision", "MISSING") if rows else "MISSING"


def stage307_passed() -> bool:
    return any(
        row.get("gate") == "G7_decision"
        and row.get("status") == "PASS_STAGE307_DIRECT_IFFT_LIFECYCLE_PROFILE_RECORDED"
        for row in read_csv(STAGE307_PROOF)
    )


def line_of(path: Path, pattern: str) -> str:
    for idx, line in enumerate(read_text(path).splitlines(), start=1):
        if pattern in line:
            return f"{rel(path)}:{idx}"
    return rel(path)


def function_body(text: str, name: str) -> str:
    start = text.find(name)
    if start < 0:
        return ""
    brace = text.find("{", start)
    if brace < 0:
        return ""
    depth = 0
    for idx in range(brace, len(text)):
        if text[idx] == "{":
            depth += 1
        elif text[idx] == "}":
            depth -= 1
            if depth == 0:
                return text[brace:idx + 1]
    return ""


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage308-spqlios-ifft-feasibility-audit-001"
    if run_id in read_text(RUN_LOG):
        return
    fields: List[str] = []
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
    if not fields:
        fields = ["run_id", "date", "git_ref", "stage", "backend", "command", "config", "seed", "status", "summary", "artifacts"]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": git_head(),
        "commit_or_state": git_head(),
        "stage": "Stage 308",
        "backend": "analysis-plus-source-audit",
        "command": "python3 scripts/build_stage308_spqlios_ifft_feasibility_audit.py",
        "config": "Stage307 lifecycle split plus SPQLIOS source interface audit",
        "params": "BINARY SET_2_3_2048 r=4 include-zero evidence from Stage307",
        "seed": "n/a",
        "status": decision,
        "summary": "Stage308 finds no existing batch IFFT API and routes near-term implementation to digit materialization, while keeping backend IFFT as a separate low-level track.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(SOURCE_AUDIT)}; {rel(PROOF)}",
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
        rows.append({"path": rel(path), "bytes": str(len(data)), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    header = read_text(SPQLIOS_HEADER)
    polynomial = read_text(POLYNOMIAL_C)
    ifft_avx512 = read_text(SPQLIOS_IFFT_AVX512)
    mattrgsw = read_text(MATTRGSW_C)

    batch_pattern = re.compile(r"\b(ifft|fft)_(array|batch|many)\b|\bbatch_.*\bifft\b|\bifft.*\b(rows|array|batch|many)\b", re.IGNORECASE)
    batch_matches = batch_pattern.findall(header + "\n" + polynomial + "\n" + ifft_avx512)
    array_body = function_body(polynomial, "void polynomial_torus_to_DFT_array")
    lifecycle = read_csv(STAGE307_LIFECYCLE)
    digit = first_row(lifecycle, "component", "digit_to_double")
    ifft = first_row(lifecycle, "component", "ifft")
    digit_share = fnum(digit.get("share_of_direct_profile_total"))
    ifft_share = fnum(ifft.get("share_of_direct_profile_total"))
    stage307_ok = stage307_passed()
    wrapper_neutral = stage_decision(STAGE289).startswith("NEUTRAL") and stage_decision(STAGE290).startswith("NEUTRAL")
    no_batch_api = len(batch_matches) == 0
    array_is_loop = "for " in array_body and "ifft(proc->tables_reverse" in array_body
    digit_substantial = digit_share >= 0.40
    decision = DECISION_PASS if stage307_ok and wrapper_neutral and no_batch_api and array_is_loop and digit_substantial else DECISION_FAIL

    summary_rows = [{
        "decision": decision,
        "stage307_passed": "PASS" if stage307_ok else "FAIL",
        "stage307_digit_share": f"{digit_share:.6f}",
        "stage307_ifft_share": f"{ifft_share:.6f}",
        "existing_batch_ifft_api": "NO" if no_batch_api else "YES",
        "array_wrapper_is_per_row_loop": "YES" if array_is_loop else "NO",
        "stage289_decision": stage_decision(STAGE289),
        "stage290_decision": stage_decision(STAGE290),
        "near_term_route": "stage309_digit_to_double_avx512_candidate",
        "backend_route": "stage310_spqlios_batched_ifft_design",
        "claim": "route_selection_not_new_performance_claim",
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "stage307_passed", "stage307_digit_share",
        "stage307_ifft_share", "existing_batch_ifft_api",
        "array_wrapper_is_per_row_loop", "stage289_decision",
        "stage290_decision", "near_term_route", "backend_route", "claim",
    ])

    source_rows = [
        {
            "source": rel(SPQLIOS_HEADER),
            "evidence": "ifft signature",
            "status": "SINGLE_BUFFER_API" if "void ifft(const void *tables, double *data);" in header else "MISSING",
            "location": line_of(SPQLIOS_HEADER, "void ifft(const void *tables, double *data);"),
            "interpretation": "The public SPQLIOS API exposes one input/output buffer per call.",
        },
        {
            "source": "spqlios source set",
            "evidence": "batch ifft API search",
            "status": "ABSENT" if no_batch_api else "PRESENT",
            "location": "regex ifft_(array|batch|many), batch_*ifft, ifft*rows",
            "interpretation": "No ready batch reverse-FFT API is available for a low-risk C-level optimization.",
        },
        {
            "source": rel(POLYNOMIAL_C),
            "evidence": "polynomial_torus_to_DFT_array",
            "status": "PER_ROW_IFFT_LOOP" if array_is_loop else "UNKNOWN",
            "location": line_of(POLYNOMIAL_C, "void polynomial_torus_to_DFT_array"),
            "interpretation": "The existing multi-row wrapper still calls `ifft` once per row, matching Stage289/290 neutral outcomes.",
        },
        {
            "source": rel(SPQLIOS_IFFT_AVX512),
            "evidence": "assembly entry",
            "status": "SINGLE_DATA_POINTER_ENTRY" if "void _ifft" in ifft_avx512 and "double *real" in ifft_avx512 else "UNKNOWN",
            "location": line_of(SPQLIOS_IFFT_AVX512, "void _ifft"),
            "interpretation": "The AVX512 assembly entry takes one real-data pointer; batching would be a backend ABI/assembly project.",
        },
        {
            "source": rel(MATTRGSW_C),
            "evidence": "digit-to-double AVX512 path",
            "status": "LOCAL_C_AVX512_CANDIDATE" if "_mm512_cvtepi64_pd" in mattrgsw else "MISSING",
            "location": line_of(MATTRGSW_C, "_mm512_cvtepi64_pd"),
            "interpretation": "Digit materialization is local to this project and can be specialized without changing SPQLIOS ABI.",
        },
    ]
    write_csv(SOURCE_AUDIT, source_rows, ["source", "evidence", "status", "location", "interpretation"])

    routes = [
        {
            "route": "stage309_digit_to_double_avx512_candidate",
            "priority": "P0",
            "evidence": f"digit share {digit_share:.6f}; local `_mm512_cvtepi64_pd` path",
            "risk": "medium",
            "gate": "profile flag shows lower digit_us; correctness passes; full SAB A/B required before promotion",
        },
        {
            "route": "stage310_spqlios_batched_ifft_design",
            "priority": "P1",
            "evidence": f"ifft share {ifft_share:.6f}; no existing batch API",
            "risk": "high",
            "gate": "new API/model/assembly or C fallback, isolated FFT correctness, then complete-SAB A/B",
        },
        {
            "route": "dense_mat_avx512_rewrite",
            "priority": "defer",
            "evidence": "Stage301/302 counters and Stage305/307 route do not select dense as the current residual target",
            "risk": "medium",
            "gate": "return only after DFT lifecycle stops dominating",
        },
    ]
    write_csv(ROUTE, routes, ["route", "priority", "evidence", "risk", "gate"])

    proof = [
        {"gate": "G1_stage307_input", "status": "PASS" if stage307_ok else "FAIL", "metric": "Stage307 decision", "value": "PASS_STAGE307_DIRECT_IFFT_LIFECYCLE_PROFILE_RECORDED" if stage307_ok else "missing/fail", "interpretation": "Stage308 must be grounded in the direct lifecycle split."},
        {"gate": "G2_no_existing_batch_ifft_api", "status": "PASS" if no_batch_api else "FAIL", "metric": "source search", "value": "absent" if no_batch_api else "present", "interpretation": "No low-risk batch IFFT call can be wired directly."},
        {"gate": "G3_existing_wrappers_filtered", "status": "PASS" if wrapper_neutral else "FAIL", "metric": "Stage289/290", "value": f"{stage_decision(STAGE289)};{stage_decision(STAGE290)}", "interpretation": "Previously tested DFT wrappers should not be repeated."},
        {"gate": "G4_digit_substantial", "status": "PASS" if digit_substantial else "FAIL", "metric": "digit share", "value": f"{digit_share:.6f}", "interpretation": "A local digit materialization candidate is justified even though ifft is slightly larger."},
        {"gate": "G5_claim_boundary", "status": "PASS", "metric": "scope", "value": "route audit", "interpretation": "Stage308 is not a performance or novelty claim."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls Stage309/310 split between local C optimization and backend FFT research."},
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])

    next_rows = [
        {
            "priority": "P0",
            "route": "stage309_digit_to_double_avx512_candidate",
            "entry_condition": decision,
            "gate": "Implement an opt-in r=4 row-batched or constant-hoisted digit materialization candidate; verify phase/correctness and Stage307-style digit_us reduction.",
            "failure_action": "Mark neutral and keep current direct-DFT path.",
        },
        {
            "priority": "P1",
            "route": "stage310_spqlios_batched_ifft_design",
            "entry_condition": "backend effort approved or Stage309 neutral",
            "gate": "Design a real batch IFFT API/model and isolated correctness/performance test before touching SAB.",
            "failure_action": "Keep SPQLIOS single-row ifft and report backend limit.",
        },
    ]
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])

    report = (
        "# Stage308 SPQLIOS IFFT Feasibility Audit\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage308 checks whether the Stage307 `ifft` residual has an existing low-risk SPQLIOS batching route. It does not change code paths or claim new speedup.\n\n"
        "## Summary\n\n" + table(summary_rows, [
            "decision", "stage307_digit_share", "stage307_ifft_share",
            "existing_batch_ifft_api", "array_wrapper_is_per_row_loop",
            "near_term_route", "backend_route",
        ]) +
        "\n\n## Source Interface Audit\n\n" + table(source_rows, ["source", "evidence", "status", "location"]) +
        "\n\n## Route Matrix\n\n" + table(routes, ["route", "priority", "evidence", "risk", "gate"]) +
        "\n\n## Proof Gate\n\n" + table(proof, ["gate", "status", "metric", "value", "interpretation"]) + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, f"""# Stage308 SPQLIOS IFFT Feasibility Model

Stage307 measured the direct sub-DTF materialization split as:

- digit-to-double share: {digit_share:.6f}
- ifft share: {ifft_share:.6f}

Although `ifft` is slightly larger, the current SPQLIOS interface exposes only
`void ifft(const void *tables, double *data)`. The existing multi-row wrapper
still loops over rows and calls the same single-buffer entry, and Stage289/290
already found those wrapper-level ideas neutral. Therefore a true IFFT
optimization is not a small MAT-SAB C-layer change; it requires a backend API
and likely assembly/model work.

The local next step is the digit-to-double path because it is nearly half of
the direct profile and already lives in `mattrgsw.c` under AVX512. Any promoted
candidate still needs staged correctness, Stage307-style component reduction,
and complete SAB `T_bootstrap/r` A/B before it becomes a bootstrapping speed
claim.
""")
    write_text(VARIANT, f"""# Stage308 IFFT/Digit Route Selection

Decision: `{decision}`.

No behavior-changing variant is introduced. The near-term implementation route
is `stage309_digit_to_double_avx512_candidate`; the high-risk backend route is
`stage310_spqlios_batched_ifft_design`.
""")
    write_text(PLAN, """# Stage308 Audit Plan

1. Read Stage307 lifecycle split.
2. Inspect SPQLIOS public header and AVX512 IFFT entry shape.
3. Confirm existing multi-row DFT wrapper is still a per-row IFFT loop.
4. Combine Stage289/290 neutral results with the source audit.
5. Route Stage309 to a low-risk local optimization candidate.
""")
    write_text(COMMANDS, """# Stage308 Reproduction Commands

```bash
python3 scripts/build_stage308_spqlios_ifft_feasibility_audit.py
```
""")

    append_once(ROADMAP, "## Stage 308: SPQLIOS IFFT Feasibility Audit", "\n## Stage 308: SPQLIOS IFFT Feasibility Audit\n\nGoal: decide whether Stage307's IFFT residual has a low-risk existing batching route or must become backend work.\n\n" f"Status: `{decision}`.\n")
    append_once(GOAL, "<!-- stage308-spqlios-ifft-feasibility-audit -->", "\n<!-- stage308-spqlios-ifft-feasibility-audit -->\n### Stage308 SPQLIOS IFFT feasibility audit\n\n" f"`{decision}` routes near-term work to digit-to-double AVX512 and reserves batched IFFT for backend-level research.\n")
    append_once(HYPOTHESES, "H308_spqlios_ifft_feasibility_audit:", "\nH308_spqlios_ifft_feasibility_audit:\n" f"  status: {decision}\n  primary_metric: source_interface_audit_plus_stage307_profile\n  evidence:\n    - repro/stage308_spqlios_ifft_feasibility_audit/stage308_summary.csv\n    - repro/stage308_spqlios_ifft_feasibility_audit/source_interface_audit.csv\n    - repro/stage308_spqlios_ifft_feasibility_audit/implementation_route_matrix.csv\n    - repro/stage308_spqlios_ifft_feasibility_audit/proof_gate.csv\n  conclusion: >\n    Stage308 finds no existing low-risk batch IFFT interface. The next local\n    implementation target is digit-to-double AVX512 materialization; true IFFT\n    batching remains a separate backend research track.\n")
    append_once(MANIFEST, "- stage308_spqlios_ifft_feasibility_audit:", "\n- stage308_spqlios_ifft_feasibility_audit:\n  - `docs/stage308_spqlios_ifft_feasibility_audit.md`\n  - `theory_checks/stage308_spqlios_ifft_feasibility_model.md`\n  - `algorithm_variants/mat_rlwe_sab_stage308_ifft_digit_routes.md`\n  - `experiments/stage308_spqlios_ifft_feasibility_audit_plan.md`\n  - `scripts/build_stage308_spqlios_ifft_feasibility_audit.py`\n  - `repro/stage308_spqlios_ifft_feasibility_audit/`\n")
    append_once(CHECKLIST, "<!-- stage308-spqlios-ifft-feasibility-audit-checklist -->", "\n<!-- stage308-spqlios-ifft-feasibility-audit-checklist -->\n" f"- [x] Stage308 records `{decision}` and routes Stage309/310.\n")
    append_run_log(decision)

    artifacts = [
        DOC, THEORY, VARIANT, PLAN, BUILDER, SUMMARY, SOURCE_AUDIT, ROUTE,
        PROOF, NEXT, COMMANDS, REPORT,
    ]
    artifact_index(artifacts)
    print(decision)


if __name__ == "__main__":
    main()
