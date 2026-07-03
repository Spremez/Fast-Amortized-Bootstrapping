#!/usr/bin/env python3
"""Stage211: preflight current-head FFT/DFT dataflow before hot-path code."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage211_fft_dataflow_preflight"

STAGE209_SPLIT = ROOT / "repro" / "stage209_current_head_mat_ep_split" / "split_projection.csv"
STAGE209_ENV = ROOT / "repro" / "stage209_current_head_mat_ep_split" / "environment.csv"
STAGE210_CANDIDATES = ROOT / "repro" / "stage210_candidate_admission" / "candidate_matrix.csv"
STAGE194_PRIOR = ROOT / "repro" / "stage194_exact_dft_conversion_preflight" / "prior_gate_matrix.csv"
STAGE194_MECHANISMS = ROOT / "repro" / "stage194_exact_dft_conversion_preflight" / "mechanism_candidates.csv"
STAGE163_SUMMARY = ROOT / "repro" / "stage163_from_dft_batching_microbench" / "summary.csv"
STAGE136_RATIO = ROOT / "repro" / "stage136_batched_decomp_dft_gate" / "ratio_summary.csv"

MATTRGSW_C = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"
POLYNOMIAL_C = ROOT / "src" / "mosfhet" / "src" / "polynomial.c"
SPQLIOS_H = ROOT / "src" / "mosfhet" / "src" / "fft" / "spqlios" / "spqlios-fft.h"
SPQLIOS_C = ROOT / "src" / "mosfhet" / "src" / "fft" / "spqlios" / "fft_processor_spqlios.c"

DOC = ROOT / "docs" / "stage211_fft_dataflow_preflight.md"
PLAN = ROOT / "experiments" / "stage211_fft_dataflow_preflight_plan.md"
THEORY = ROOT / "theory_checks" / "stage211_fft_dataflow_preflight_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage211_fft_dataflow_preflight.md"

API_SURFACE = OUT / "api_surface.csv"
PRIOR_GATE = OUT / "prior_gate_matrix.csv"
MECHANISM = OUT / "mechanism_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "fft_dataflow_preflight_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE211_DFT_DATAFLOW_PREFLIGHT_DENY_HOTPATH_CODE"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.strip() + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._"
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def csv_value(rows: List[Dict[str, str]], key: str, value: str, field: str) -> str:
    for row in rows:
        if row.get(key) == value:
            return row.get(field, "")
    return ""


def max_float(rows: List[Dict[str, str]], field: str, where_key: str = "", where_value: str = "") -> str:
    vals: List[float] = []
    for row in rows:
        if where_key and row.get(where_key) != where_value:
            continue
        try:
            vals.append(float(row[field]))
        except (KeyError, ValueError):
            pass
    return f"{max(vals):.6f}" if vals else ""


def min_float(rows: List[Dict[str, str]], field: str, where_key: str = "", where_value: str = "") -> str:
    vals: List[float] = []
    for row in rows:
        if where_key and row.get(where_key) != where_value:
            continue
        try:
            vals.append(float(row[field]))
        except (KeyError, ValueError):
            pass
    return f"{min(vals):.6f}" if vals else ""


def contains_regex(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.MULTILINE | re.DOTALL) is not None


def source_surface() -> List[Dict[str, str]]:
    poly = read_text(POLYNOMIAL_C)
    mat = read_text(MATTRGSW_C)
    spq_h = read_text(SPQLIOS_H)
    spq_c = read_text(SPQLIOS_C)
    all_spq = spq_h + "\n" + spq_c

    row_loop_count = len(re.findall(r"polynomial_torus_to_DFT\s*\(\s*scratch->dec_dft\s*\[\s*i\s*\]", mat))
    compact_runtime_count = len(re.findall(r"polynomial_torus_to_DFT\s*\(\s*scratch->dec_(?:shared|body)_dft", mat))
    key_set_count = len(re.findall(r"polynomial_torus_to_DFT\s*\(\s*out->(?:shared|body)_[ab]\s*\[idx\]", mat))
    batch_api_count = len(
        re.findall(
            r"(execute_reverse_torus64_(?:batch|rows|multi)|polynomial_torus_to_DFT_(?:batch|rows|multi))",
            poly + "\n" + mat + "\n" + all_spq,
        )
    )

    return [
        {
            "fact": "polynomial_torus_to_DFT_signature",
            "status": "single_poly_api" if contains_regex(poly, r"void\s+polynomial_torus_to_DFT\s*\(\s*DFT_Polynomial\s+\w+\s*,\s*TorusPolynomial\s+\w+\s*\)") else "missing",
            "evidence": f"{rel(POLYNOMIAL_C)}:373",
            "detail": "The MOSFHET wrapper accepts one output DFT polynomial and one input torus polynomial.",
            "implication": "MAT rows are converted by repeated scalar-row calls under the current API.",
        },
        {
            "fact": "spqlios_reverse_torus64_signature",
            "status": "single_row_backend_api" if "void execute_reverse_torus64(double* res, const uint64_t* a" in spq_h else "missing",
            "evidence": f"{rel(SPQLIOS_H)}:43",
            "detail": "The public backend primitive exposes one output double buffer and one input torus buffer.",
            "implication": "No existing source-level multirow reverse DFT primitive is available to call.",
        },
        {
            "fact": "spqlios_processor_scratch",
            "status": "one_reverse_scratch_buffer" if "double *real_inout_rev;" in spq_h else "unknown",
            "evidence": f"{rel(SPQLIOS_H)}:31",
            "detail": "The processor owns one reverse scratch buffer in the current structure.",
            "implication": "A true multirow primitive needs backend API and scratch-layout changes, not only SAB call-site edits.",
        },
        {
            "fact": "current_exact_mat_ep_row_loops",
            "status": "row_loop_present",
            "evidence": f"{rel(MATTRGSW_C)}:741; {rel(MATTRGSW_C)}:837",
            "detail": f"Found {row_loop_count} exact MAT-EP runtime row-loop call sites over scratch->dec_dft[i].",
            "implication": "The measured Stage209 torus_to_dft_rows component is this repeated conversion boundary.",
        },
        {
            "fact": "compact_path_runtime_dft_calls",
            "status": "single_poly_calls_present" if compact_runtime_count else "not_found",
            "evidence": f"{rel(MATTRGSW_C)}:963; {rel(MATTRGSW_C)}:968",
            "detail": f"Found {compact_runtime_count} compact-path runtime scratch conversion call sites.",
            "implication": "The compact path also relies on single-poly DFT calls.",
        },
        {
            "fact": "compact_key_setup_dft_calls",
            "status": "single_poly_calls_present" if key_set_count else "not_found",
            "evidence": f"{rel(MATTRGSW_C)}:919-922",
            "detail": f"Found {key_set_count} compact key-row conversion call sites.",
            "implication": "Key setup DFT materialization does not create a runtime multirow primitive.",
        },
        {
            "fact": "multirow_dft_api_search",
            "status": "not_present" if batch_api_count == 0 else "present",
            "evidence": f"{rel(POLYNOMIAL_C)}; {rel(SPQLIOS_H)}; {rel(SPQLIOS_C)}",
            "detail": f"Regex search found {batch_api_count} reverse-torus batch/rows/multi API names.",
            "implication": "Stage211 cannot honestly route to production code through an existing multirow DFT API.",
        },
    ]


def prior_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in read_csv(STAGE194_PRIOR):
        rows.append(
            {
                "source": row.get("gate", ""),
                "route": row.get("route", ""),
                "status": row.get("status", ""),
                "quantitative_result": row.get("quantitative_result", ""),
                "evidence": row.get("evidence", ""),
                "stage211_consequence": row.get("consequence", ""),
            }
        )
    for row in read_csv(STAGE194_MECHANISMS):
        rows.append(
            {
                "source": row.get("candidate", ""),
                "route": row.get("mechanism_type", ""),
                "status": row.get("status", ""),
                "quantitative_result": row.get("quantitative_or_static_result", ""),
                "evidence": row.get("best_evidence", ""),
                "stage211_consequence": row.get("next_action", ""),
            }
        )
    return rows


def mechanism_rows() -> List[Dict[str, str]]:
    split = read_csv(STAGE209_SPLIT)
    max_share = max_float(split, "estimated_full_sab_share", "variant", "torus_to_dft_rows")
    min_req = min_float(split, "component_speedup_for_3pct_full_gain", "variant", "torus_to_dft_rows")
    perf_path = csv_value(read_csv(STAGE209_ENV), "key", "perf_path", "value")
    counter_status = csv_value(read_csv(STAGE209_ENV), "key", "counter_status", "value")
    return [
        {
            "mechanism": "M1_current_row_loop",
            "mechanism_class": "baseline",
            "evidence": f"{rel(MATTRGSW_C)}:741; {rel(MATTRGSW_C)}:837; {rel(STAGE209_SPLIT)}",
            "estimated_full_sab_share": max_share,
            "min_component_speedup_for_3pct": min_req,
            "decision": "BASELINE_ONLY",
            "reason": "It explains the measured cost but provides no new dataflow or fewer operations.",
            "next_gate": "Use as reference for any future DFT primitive.",
        },
        {
            "mechanism": "M2_reopen_same_format_batching",
            "mechanism_class": "old_backend_loop_order",
            "evidence": f"{rel(STAGE163_SUMMARY)}; {rel(STAGE136_RATIO)}; {rel(STAGE194_PRIOR)}",
            "estimated_full_sab_share": max_share,
            "min_component_speedup_for_3pct": min_req,
            "decision": "DENY_REOPEN",
            "reason": "Stage136 batched decomp-to-DFT was negative and Stage163 backend batching was neutral.",
            "next_gate": "Only reopen with a different API or new counter-backed mechanism.",
        },
        {
            "mechanism": "M3_direct_decompose_to_dft_or_lazy_state",
            "mechanism_class": "representation_change",
            "evidence": f"{rel(STAGE194_PRIOR)}; {rel(POLYNOMIAL_C)}:373; {rel(MATTRGSW_C)}:793",
            "estimated_full_sab_share": max_share,
            "min_component_speedup_for_3pct": min_req,
            "decision": "PROOF_BLOCKED",
            "reason": "Decomposition uses coefficient-domain subtract, offset, shift, and mask before DFT; bypassing the torus polynomial needs exact closure and noise proof.",
            "next_gate": "Separate proof route only; no production hot path from Stage211.",
        },
        {
            "mechanism": "M4_new_multirow_fft_backend_api",
            "mechanism_class": "new_backend_primitive",
            "evidence": f"{rel(SPQLIOS_H)}:31; {rel(SPQLIOS_H)}:43; {rel(SPQLIOS_C)}:81",
            "estimated_full_sab_share": max_share,
            "min_component_speedup_for_3pct": min_req,
            "decision": "ADMIT_BACKEND_API_DESIGN_ONLY",
            "reason": "A true multirow reverse DFT could target the largest current component, but the source tree has no callable primitive yet.",
            "next_gate": "Stage212 should specify and microbench a standalone backend prototype before SAB integration.",
        },
        {
            "mechanism": "M5_native_counter_route",
            "mechanism_class": "measurement_infrastructure",
            "evidence": rel(STAGE209_ENV),
            "estimated_full_sab_share": max_share,
            "min_component_speedup_for_3pct": min_req,
            "decision": "BLOCKED_LOCALLY" if not perf_path else "AVAILABLE",
            "reason": f"Stage209 counter status is {counter_status or 'unknown'}; local perf_path is empty.",
            "next_gate": "Run on native Linux or a configured remote host before reopening assembly-level claims.",
        },
    ]


def proof_rows(api: List[Dict[str, str]], mechanisms: List[Dict[str, str]]) -> List[Dict[str, str]]:
    stage210 = read_csv(STAGE210_CANDIDATES)
    c2 = [row for row in stage210 if row.get("candidate") == "C2_new_multirow_fft_api_or_dft_dataflow"]
    api_single = all(
        row["status"] in {"single_poly_api", "single_row_backend_api", "one_reverse_scratch_buffer", "row_loop_present", "single_poly_calls_present", "not_present"}
        for row in api
    )
    old_denied = any(row["mechanism"] == "M2_reopen_same_format_batching" and row["decision"] == "DENY_REOPEN" for row in mechanisms)
    new_backend_only = any(row["mechanism"] == "M4_new_multirow_fft_backend_api" and row["decision"] == "ADMIT_BACKEND_API_DESIGN_ONLY" for row in mechanisms)
    return [
        {
            "gate": "G1_stage210_input",
            "status": "PASS" if c2 else "FAIL",
            "evidence": rel(STAGE210_CANDIDATES),
            "detail": "Stage210 admits only C2 as preflight-only DFT/FFT dataflow work.",
            "remaining_gap": "Stage211 must decide whether a concrete mechanism exists now.",
        },
        {
            "gate": "G2_api_surface",
            "status": "PASS_SINGLE_ROW_DFT_API_ONLY" if api_single else "FAIL_API_AUDIT",
            "evidence": rel(API_SURFACE),
            "detail": "The current wrapper/backend exposes single-poly reverse DFT and row-loop call sites.",
            "remaining_gap": "No existing multirow DFT primitive can be integrated directly.",
        },
        {
            "gate": "G3_prior_route_guard",
            "status": "PASS_OLD_DFT_ROUTES_REJECTED" if old_denied else "FAIL_PRIOR_GUARD",
            "evidence": rel(PRIOR_GATE),
            "detail": "Same-format batching, direct-scale, batched decomp-to-DFT, and naive lazy-state routes are closed or proof-blocked.",
            "remaining_gap": "Only genuinely new mechanisms may proceed.",
        },
        {
            "gate": "G4_mechanism_admission",
            "status": "PASS_BACKEND_API_DESIGN_ONLY" if new_backend_only else "FAIL_NO_ROUTE",
            "evidence": rel(MECHANISM),
            "detail": "The only admitted route is a future standalone multirow FFT/backend API design, not current SAB hot-path code.",
            "remaining_gap": "Needs a prototype API and microbench before integration.",
        },
        {
            "gate": "G5_stage211_decision",
            "status": DECISION,
            "evidence": rel(PROOF),
            "detail": "Stage211 prevents theory drift by denying local production hot-path edits when no current source-level primitive exists.",
            "remaining_gap": "Proceed to Stage212 backend API sketch/probe or native counter refresh.",
        },
    ]


def next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage212_multirow_fft_backend_api_probe",
            "entry_condition": "Stage211 admits backend/API design only.",
            "gate": "Define exact API, scratch layout, correctness oracle, and microbench for row groups before SAB integration.",
            "status": "ready",
            "evidence": rel(MECHANISM),
        },
        {
            "priority": "P1",
            "route": "native_perf_counter_refresh",
            "entry_condition": "Native Linux perf or configured remote host is available.",
            "gate": "Collect load/store/FMA/cache/cycle counters for Stage209 split variants.",
            "status": "blocked_locally",
            "evidence": rel(STAGE209_ENV),
        },
        {
            "priority": "P2",
            "route": "sab_hotpath_integration",
            "entry_condition": "Stage212 or native counters promote a concrete mechanism.",
            "gate": "Flag-only implementation, staged equivalence, full SAB A/B, noise/resource, and claim audit.",
            "status": "denied_now",
            "evidence": rel(PROOF),
        },
    ]


def report(api: List[Dict[str, str]], priors: List[Dict[str, str]], mechanisms: List[Dict[str, str]], gates: List[Dict[str, str]], queue: List[Dict[str, str]]) -> str:
    split = read_csv(STAGE209_SPLIT)
    max_share = max_float(split, "estimated_full_sab_share", "variant", "torus_to_dft_rows")
    min_req = min_float(split, "component_speedup_for_3pct_full_gain", "variant", "torus_to_dft_rows")
    return f"""# Stage211 FFT/DFT Dataflow Preflight

Decision: `{DECISION}`.

Stage211 checks whether the current codebase has a new DFT/FFT dataflow
mechanism that is concrete enough for production SAB hot-path implementation.
It does not add a new kernel. The audit finds that the current MOSFHET wrapper
and SPQLIOS backend expose single-polynomial reverse DFT calls, while prior
same-format batching and direct-scale routes are already neutral, rejected, or
proof-blocked.

The current-head Stage209 budget still matters: `torus_to_dft_rows` reaches a
maximum estimated complete-SAB share of `{max_share}`, and a 3% complete-SAB
gain would require at least `{min_req}x` component speedup in the best current
projection. Stage211 therefore keeps DFT/dataflow as a valid research target
but denies local hot-path edits until a new primitive or proof exists.

## API Surface

{table(api, ["fact", "status", "evidence", "detail", "implication"])}

## Prior Gates

{table(priors, ["source", "route", "status", "quantitative_result", "evidence", "stage211_consequence"])}

## Mechanism Matrix

{table(mechanisms, ["mechanism", "mechanism_class", "estimated_full_sab_share", "min_component_speedup_for_3pct", "decision", "reason", "next_gate"])}

## Proof Gates

{table(gates, ["gate", "status", "evidence", "detail", "remaining_gap"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "evidence"])}
"""


def plan_text() -> str:
    return f"""# Stage211 FFT/DFT Dataflow Preflight Plan

Decision target: `{DECISION}`.

Research loop:

1. Hypothesis: the Stage209 `torus_to_dft_rows` cost can only justify code if
   a mechanism differs from old same-format batching/direct-scale attempts.
2. Theory model: exact MAT-EP currently performs coefficient-domain
   decomposition, row-wise torus-to-DFT conversion, then DFT-domain addmul.
   A conversion shortcut must either supply a new exact backend primitive or
   prove representation closure and noise behavior.
3. Implementation boundary: Stage211 writes no production SAB hot-path code.
   It records whether implementation is admitted, blocked, or denied.
4. Gate: old routes remain denied; a new multirow FFT/backend API is admitted
   only as a Stage212 standalone probe.
5. Exit: if no concrete primitive exists, move to Stage212 API/probe or native
   counter refresh instead of repeating theory.
"""


def theory_text() -> str:
    return """# Stage211 FFT/DFT Dataflow Model

The exact MAT external product boundary is:

```text
PVW_TMLWE pair -> coefficient-domain sub/decompose -> rows of torus
polynomials -> row-wise reverse DFT -> DFT-domain selector addmul -> output
PVW_TMLWE_DFT
```

Under the current source API, `polynomial_torus_to_DFT` calls
`execute_reverse_torus64` once per polynomial. The SPQLIOS processor exposes
one reverse scratch buffer, so reducing row conversion overhead is not a local
SAB call-site edit. It is either:

- a backend/API problem: define a multirow reverse DFT primitive with safe
  scratch layout and prove bit-identical output against the single-row API; or
- a representation-change problem: bypass coefficient-domain torus rows, which
  requires exact closure for subtract/offset/shift/mask decomposition and a
  noise proof.

Prior stages already rejected or neutralized old same-format batching,
direct-scale, and naive lazy-state routes. Therefore Stage211 denies hot-path
implementation and routes only to a standalone backend/API probe.
"""


def variant_text() -> str:
    return """# MAT-RLWE SAB Stage211 FFT/DFT Dataflow Variant

Stage211 defines no new production variant. It is a code-admission checkpoint
for the current MAT-RLWE/r-body SAB implementation.

Allowed next variant:

```text
stage212_multirow_fft_backend_api_probe
```

This future probe may introduce a standalone reverse-DFT API and compare it
against the current single-row path. It must pass bit/equivalence tests and a
microbench before any `sab_pvw_*` integration.

Denied now:

- reopening same-format DFT batching;
- reopening batched decompose-to-DFT;
- direct lazy DFT accumulator integration;
- production SAB hot-path edits without a new primitive.
"""


def artifact_rows(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
                "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
            }
        )
    return rows


def update_tracking() -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 211: FFT/DFT Dataflow Preflight",
        f"""
## Stage 211: FFT/DFT Dataflow Preflight

Goal:

```text
Audit whether the admitted DFT/FFT dataflow route has a current source-level
mechanism concrete enough for production SAB hot-path implementation.
```

Status:

```text
Completed. Stage211 records {DECISION}. The current code exposes single-row
torus-to-DFT APIs and row-loop MAT-EP conversions; old same-format DFT routes
remain denied by prior gates. The only admitted continuation is a standalone
multirow FFT/backend API probe or native counter refresh, not production SAB
hot-path edits at this stage.
```
""",
    )
    append_once(
        GOAL,
        "Stage211 FFT/DFT dataflow preflight",
        f"""

## Stage211 FFT/DFT dataflow preflight

At commit `{head}`, Stage211 keeps the MAT-RLWE SAB metric and current
complete-SAB evidence intact while denying local hot-path DFT edits without a
new backend primitive or proof. The next executable route is Stage212
multirow FFT/backend API probing.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage211 FFT/DFT dataflow preflight",
        f"""

### Stage211 FFT/DFT dataflow preflight

`{DECISION}` prevents the optimization loop from drifting into repeated DFT
theory. The current code has no existing multirow DFT primitive; proceed to a
bounded Stage212 backend/API probe or native counter refresh.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage211_fft_dataflow_preflight",
        """

H10_stage211_fft_dataflow_preflight:
  status: hotpath_code_denied_backend_api_probe_selected
  evidence:
    - repro/stage211_fft_dataflow_preflight/api_surface.csv
    - repro/stage211_fft_dataflow_preflight/mechanism_matrix.csv
    - docs/stage211_fft_dataflow_preflight.md
  conclusion: >
    Current-head source exposes only single-polynomial torus-to-DFT conversion
    APIs for MAT-EP row conversion. Old same-format DFT routes remain denied;
    the next admitted work is a standalone multirow FFT/backend API probe or
    native counter refresh, not production SAB hot-path implementation.
""",
    )
    append_once(
        RUN_LOG,
        "stage211-fft-dataflow-preflight-001",
        f"""stage211-fft-dataflow-preflight-001,2026-07-04,{head},Stage 211,n/a,python scripts/build_stage211_fft_dataflow_preflight.py,audit DFT/FFT dataflow API and code admission,n/a,{DECISION},"Single-row DFT API only; old DFT routes denied; route to Stage212 backend/API probe.",docs/stage211_fft_dataflow_preflight.md; repro/stage211_fft_dataflow_preflight/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage211_fft_dataflow_preflight:",
        """

- stage211_fft_dataflow_preflight:
  - `docs/stage211_fft_dataflow_preflight.md`
  - `experiments/stage211_fft_dataflow_preflight_plan.md`
  - `theory_checks/stage211_fft_dataflow_preflight_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage211_fft_dataflow_preflight.md`
  - `scripts/build_stage211_fft_dataflow_preflight.py`
  - `repro/stage211_fft_dataflow_preflight/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage211 FFT/DFT dataflow preflight",
        """
- [x] Stage211 FFT/DFT dataflow preflight records the current single-row DFT
  API boundary, denies old DFT route reopenings, and routes only to a bounded
  Stage212 backend/API probe or native counter refresh.
""",
    )


def main() -> None:
    required = [
        STAGE209_SPLIT,
        STAGE209_ENV,
        STAGE210_CANDIDATES,
        STAGE194_PRIOR,
        MATTRGSW_C,
        POLYNOMIAL_C,
        SPQLIOS_H,
        SPQLIOS_C,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("missing required Stage211 inputs: " + ", ".join(missing))

    api = source_surface()
    priors = prior_rows()
    mechanisms = mechanism_rows()
    gates = proof_rows(api, mechanisms)
    queue = next_rows()
    text = report(api, priors, mechanisms, gates, queue)

    write_csv(API_SURFACE, api, ["fact", "status", "evidence", "detail", "implication"])
    write_csv(PRIOR_GATE, priors, ["source", "route", "status", "quantitative_result", "evidence", "stage211_consequence"])
    write_csv(MECHANISM, mechanisms, ["mechanism", "mechanism_class", "evidence", "estimated_full_sab_share", "min_component_speedup_for_3pct", "decision", "reason", "next_gate"])
    write_csv(PROOF, gates, ["gate", "status", "evidence", "detail", "remaining_gap"])
    write_csv(NEXT, queue, ["priority", "route", "entry_condition", "gate", "status", "evidence"])
    write_text(DOC, text)
    write_text(REPORT, text)
    write_text(PLAN, plan_text())
    write_text(THEORY, theory_text())
    write_text(VARIANT, variant_text())
    write_text(
        REPRO,
        "# Stage211 Reproduction Commands\n\n```bash\npython3 scripts/build_stage211_fft_dataflow_preflight.py\n```\n",
    )
    write_csv(
        ARTIFACT,
        artifact_rows([DOC, PLAN, THEORY, VARIANT, API_SURFACE, PRIOR_GATE, MECHANISM, PROOF, NEXT, REPORT, REPRO, Path(__file__)]),
        ["path", "exists", "sha256", "bytes"],
    )
    update_tracking()
    print(DECISION)


if __name__ == "__main__":
    main()
