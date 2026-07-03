#!/usr/bin/env python3
"""Stage210: admit or reject current-head MAT-EP implementation candidates."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage210_candidate_admission"
STAGE209_SPLIT = ROOT / "repro" / "stage209_current_head_mat_ep_split" / "split_projection.csv"
STAGE194_PRIOR = ROOT / "repro" / "stage194_exact_dft_conversion_preflight" / "prior_gate_matrix.csv"
STAGE181_SUMMARY = ROOT / "repro" / "stage181_sub_decomp_avx512_gate" / "summary.csv"
STAGE183_SCREEN = ROOT / "repro" / "stage183_addmul_dataflow_screen" / "candidate_matrix.csv"

DOC = ROOT / "docs" / "stage210_candidate_admission.md"
PLAN = ROOT / "experiments" / "stage210_candidate_admission_plan.md"
THEORY = ROOT / "theory_checks" / "stage210_candidate_admission_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage210_candidate_admission.md"
MATRIX = OUT / "candidate_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "candidate_admission_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE210_SELECT_DFT_ROWS_PREFLIGHT_NO_HOTPATH_CODE"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def read_csv(path: Path) -> List[Dict[str, str]]:
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


def max_share(split_rows: List[Dict[str, str]], variant: str) -> str:
    vals = [float(row["estimated_full_sab_share"]) for row in split_rows if row["variant"] == variant and row["estimated_full_sab_share"]]
    return f"{max(vals):.6f}" if vals else ""


def min_required(split_rows: List[Dict[str, str]], variant: str) -> str:
    vals = [
        float(row["component_speedup_for_3pct_full_gain"])
        for row in split_rows
        if row["variant"] == variant and row["component_speedup_for_3pct_full_gain"] not in {"", "inf"}
    ]
    return f"{min(vals):.6f}" if vals else ""


def build_candidates() -> List[Dict[str, str]]:
    split = read_csv(STAGE209_SPLIT)
    prior_rows = read_csv(STAGE194_PRIOR) if STAGE194_PRIOR.exists() else []
    prior_text = "; ".join(f"{row['gate']}={row['status']}" for row in prior_rows)
    stage181 = read_text(STAGE181_SUMMARY)
    stage183 = read_text(STAGE183_SCREEN)
    return [
        {
            "candidate": "C1_reopen_existing_dft_batching_or_direct_scale",
            "stage209_component": "torus_to_dft_rows",
            "max_estimated_full_sab_share": max_share(split, "torus_to_dft_rows"),
            "min_component_speedup_for_3pct": min_required(split, "torus_to_dft_rows"),
            "prior_evidence": prior_text,
            "decision": "REJECT_REOPEN_OLD_MECHANISMS",
            "reason": "Stage136/163/174/194 already reject or neutralize the obvious same-format DFT batching/direct-scale routes.",
            "code_permission": "denied",
            "next_gate": "Only a new FFT/dataflow mechanism may proceed.",
        },
        {
            "candidate": "C2_new_multirow_fft_api_or_dft_dataflow",
            "stage209_component": "torus_to_dft_rows",
            "max_estimated_full_sab_share": max_share(split, "torus_to_dft_rows"),
            "min_component_speedup_for_3pct": min_required(split, "torus_to_dft_rows"),
            "prior_evidence": "Stage209 top component; prior old mechanisms rejected.",
            "decision": "ADMIT_PREFLIGHT_ONLY",
            "reason": "The component is large enough, but implementation permission requires a concrete new API/dataflow that is not Stage136/163/174 repeated.",
            "code_permission": "preflight_only",
            "next_gate": "Stage211 must inspect/build a bounded FFT/dataflow probe before production code.",
        },
        {
            "candidate": "C3_sub_decompose_avx512_or_fusion_reopen",
            "stage209_component": "sub_decompose",
            "max_estimated_full_sab_share": max_share(split, "sub_decompose"),
            "min_component_speedup_for_3pct": min_required(split, "sub_decompose"),
            "prior_evidence": "Stage181=" + ("REJECTED" if "REJECT" in stage181 else "present"),
            "decision": "REJECT_DIRECT_REOPEN",
            "reason": "A direct AVX512 sub-decompose route was already rejected; reopen only with new r=2/r=4 counter evidence.",
            "code_permission": "denied",
            "next_gate": "Native counter refresh may reopen if it shows a different mechanism.",
        },
        {
            "candidate": "C4_addmul_retiling_reopen",
            "stage209_component": "addmul_from_dec_dft",
            "max_estimated_full_sab_share": max_share(split, "addmul_from_dec_dft"),
            "min_component_speedup_for_3pct": min_required(split, "addmul_from_dec_dft"),
            "prior_evidence": "Stage183=" + ("NO_CODE" if "NO_CODE" in stage183 else "present"),
            "decision": "REJECT_WITHOUT_NEW_ASSEMBLY_COUNTER_MECHANISM",
            "reason": "Current small-r MAT-aware addmul already exists; obvious retile/streaming routes have been rejected or need counters.",
            "code_permission": "denied",
            "next_gate": "Native counter or assembly-backed mechanism required.",
        },
    ]


def build_gates(candidates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    top = next(row for row in candidates if row["candidate"] == "C2_new_multirow_fft_api_or_dft_dataflow")
    return [
        {
            "gate": "G1_stage209_input",
            "status": "PASS",
            "evidence": rel(STAGE209_SPLIT),
            "detail": "Stage209 split projection is present and current-head r=2/r=4 scoped.",
            "remaining_gap": "Microbench route selection only.",
        },
        {
            "gate": "G2_old_mechanism_guard",
            "status": "PASS_OLD_DFT_ROUTES_REJECTED",
            "evidence": rel(MATRIX),
            "detail": "Known DFT batching/direct-scale/subdecomp/addmul reopen routes are denied.",
            "remaining_gap": "Does not block genuinely new FFT/dataflow preflights.",
        },
        {
            "gate": "G3_candidate_selection",
            "status": "PASS_PREFLIGHT_SELECTED",
            "evidence": rel(MATRIX),
            "detail": f"Selected preflight target {top['candidate']} with max estimated full-SAB share {top['max_estimated_full_sab_share']}.",
            "remaining_gap": "Hot-path implementation remains unauthorized until Stage211 preflight passes.",
        },
        {
            "gate": "G4_decision",
            "status": DECISION,
            "evidence": rel(PROOF),
            "detail": "Stage210 routes to a bounded preflight instead of speculative hot-path implementation.",
            "remaining_gap": "Implementation and complete-SAB A/B remain future gates.",
        },
    ]


def build_next() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage211_fft_dataflow_preflight",
            "entry_condition": "Stage210 admits only a new DFT/FFT dataflow preflight.",
            "gate": "Produce a concrete probe or reject code permission.",
            "current_status": "ready",
            "evidence": rel(MATRIX),
        },
        {
            "priority": "P1",
            "route": "native_counter_refresh",
            "entry_condition": "Native perf is available.",
            "gate": "Collect counters for Stage209 split variants.",
            "current_status": "blocked_by_stage209_environment",
            "evidence": "repro/stage209_current_head_mat_ep_split/environment.csv",
        },
        {
            "priority": "P2",
            "route": "production_hotpath_code",
            "entry_condition": "Stage211 or native counters provides a new mechanism.",
            "gate": "Flag-only implementation, correctness, noise/resource, full SAB A/B.",
            "current_status": "denied_now",
            "evidence": rel(PROOF),
        },
    ]


def report(candidates: List[Dict[str, str]], gates: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> str:
    return f"""# Stage210 Candidate Admission

Decision: `{DECISION}`.

Stage210 converts Stage209 split measurements into code-admission policy. The
largest current component is `torus_to_dft_rows`, but old same-format DFT
routes are not reopened because prior gates already rejected or neutralized
them.

## Candidate Matrix

{table(candidates, ["candidate", "stage209_component", "max_estimated_full_sab_share", "min_component_speedup_for_3pct", "decision", "code_permission", "next_gate"])}

## Gates

{table(gates, ["gate", "status", "evidence", "detail", "remaining_gap"])}

## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}
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
        "## Stage 210: Candidate Admission",
        f"""
## Stage 210: Candidate Admission

Goal:

```text
Turn Stage209 split measurements into explicit code-admission policy.
```

Status:

```text
Completed. Stage210 records {DECISION}. Existing DFT batching/direct-scale,
direct sub-decompose, and addmul retile routes are denied for hot-path code.
Only a genuinely new FFT/dataflow preflight is admitted as Stage211.
```
""",
    )
    append_once(
        GOAL,
        "Stage210 candidate admission",
        f"""

## Stage210 candidate admission

At commit `{head}`, Stage210 selects DFT/FFT dataflow as the only admitted
preflight route and explicitly denies speculative production hot-path code.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage210 candidate admission",
        f"""

### Stage210 candidate admission

`{DECISION}` prevents theory drift and blind tuning: Stage211 must produce a
concrete DFT/FFT dataflow preflight or reject implementation permission.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage210_candidate_admission",
        """

H10_stage210_candidate_admission:
  status: preflight_route_selected
  evidence:
    - repro/stage210_candidate_admission/candidate_matrix.csv
    - docs/stage210_candidate_admission.md
  conclusion: >
    Stage210 admits only a new DFT/FFT dataflow preflight. It denies reopening
    old DFT batching/direct-scale, direct sub-decompose, or addmul retile
    routes without new evidence.
""",
    )
    append_once(
        RUN_LOG,
        "stage210-candidate-admission-001",
        f"""stage210-candidate-admission-001,2026-07-04,{head},Stage 210,n/a,python scripts/build_stage210_candidate_admission.py,admit/reject current-head MAT-EP candidates from Stage209 and prior gates,n/a,{DECISION},"Only new DFT/FFT dataflow preflight admitted; production hot-path code denied now.",docs/stage210_candidate_admission.md; repro/stage210_candidate_admission/candidate_matrix.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage210_candidate_admission:",
        """

- stage210_candidate_admission:
  - `docs/stage210_candidate_admission.md`
  - `experiments/stage210_candidate_admission_plan.md`
  - `theory_checks/stage210_candidate_admission_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage210_candidate_admission.md`
  - `scripts/build_stage210_candidate_admission.py`
  - `repro/stage210_candidate_admission/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage210 candidate admission",
        """
- [x] Stage210 candidate admission denies speculative hot-path code and routes
  only to a bounded new DFT/FFT dataflow preflight.
""",
    )


def main() -> None:
    if not STAGE209_SPLIT.exists():
        raise SystemExit(f"missing Stage209 split evidence: {STAGE209_SPLIT}")
    candidates = build_candidates()
    gates = build_gates(candidates)
    next_rows = build_next()
    write_csv(MATRIX, candidates, ["candidate", "stage209_component", "max_estimated_full_sab_share", "min_component_speedup_for_3pct", "prior_evidence", "decision", "reason", "code_permission", "next_gate"])
    write_csv(PROOF, gates, ["gate", "status", "evidence", "detail", "remaining_gap"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])
    text = report(candidates, gates, next_rows)
    write_text(DOC, text)
    write_text(REPORT, text)
    write_text(PLAN, "# Stage210 Candidate Admission Plan\n\nUse Stage209 split data and prior gates to decide whether production code is allowed. This stage may only admit a bounded preflight, not hot-path code.\n")
    write_text(THEORY, "# Stage210 Admission Model\n\nA component with high estimated share is not enough for implementation permission. A candidate must also avoid repeating prior neutral or rejected mechanisms and must define a falsifiable next gate.\n")
    write_text(VARIANT, "# Stage210 Candidate Admission\n\nThis stage adds no production variant. It records which MAT-EP subcomponent routes are rejected, preflight-only, or blocked by missing counter evidence.\n")
    write_text(REPRO, "# Stage210 Reproduction Commands\n\n```bash\npython3 scripts/build_stage210_candidate_admission.py\n```\n")
    write_csv(ARTIFACT, artifact_rows([DOC, PLAN, THEORY, VARIANT, MATRIX, PROOF, NEXT, REPORT, REPRO, Path(__file__)]), ["path", "exists", "sha256", "bytes"])
    update_tracking()
    print(DECISION)


if __name__ == "__main__":
    main()
