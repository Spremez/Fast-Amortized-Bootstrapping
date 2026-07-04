"""Stage245: bridge Stage226 native counter attribution to current head.

This stage does not run a new benchmark.  It checks whether executable
MAT/PVW-SAB sources changed after Stage226.  If the hot-path tree is unchanged,
Stage226 native counters remain valid as attribution-only evidence for the
current paper package; they are not promoted to theoretical optimality or new
performance statistics.
"""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage245_current_head_counter_bridge"

STAGE226_COMMIT = "f2b753f"
STAGE226_PROOF = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "proof_gate.csv"
STAGE226_ATTR = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "attribution_summary.csv"
STAGE226_COUNTERS = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "counter_summary.csv"
STAGE226_REMOTE = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "remote_environment.csv"

DOC = ROOT / "docs" / "stage245_current_head_counter_bridge.md"
PLAN = ROOT / "experiments" / "stage245_current_head_counter_bridge_plan.md"
THEORY = ROOT / "theory_checks" / "stage245_counter_reuse_boundary.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage245_counter_bridge.md"

INPUTS = OUT / "input_status.csv"
CODE_DELTA = OUT / "code_delta.csv"
EVIDENCE = OUT / "evidence_bridge.csv"
CLAIMS = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage245_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

HOT_PATHS = ["main.c", "Makefile", "include", "src"]
DECISION_PASS = "PASS_STAGE245_COUNTER_REUSE_BRIDGED_NO_HOTPATH_DELTA"
DECISION_FAIL = "FAIL_STAGE245_HOTPATH_DELTA_REQUIRES_NATIVE_COUNTER_REFRESH"


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


def read_csv(path: Path) -> list[dict[str, str]]:
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
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip("\n"))
        if not text.endswith("\n"):
            f.write("\n")


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
    rows = []
    for path, role in [
        (STAGE226_PROOF, "Stage226 native counter proof gates"),
        (STAGE226_ATTR, "Stage226 attribution summary"),
        (STAGE226_COUNTERS, "Stage226 native counter summary"),
        (STAGE226_REMOTE, "Stage226 native host/environment record"),
    ]:
        rows.append({
            "input": rel(path),
            "status": "present" if path.exists() else "missing",
            "role": role,
            "bytes": path.stat().st_size if path.exists() else 0,
        })
    return rows


def code_delta_rows(head: str) -> list[dict[str, object]]:
    diff = run_git(["diff", "--name-status", f"{STAGE226_COMMIT}..{head}", "--", *HOT_PATHS])
    rows: list[dict[str, object]] = []
    if diff:
        for line in diff.splitlines():
            parts = line.split("\t")
            status = parts[0]
            path = parts[-1] if parts else ""
            rows.append({
                "base": STAGE226_COMMIT,
                "head": head,
                "path": path,
                "status": status,
                "hot_path_effect": "requires_new_native_counter_refresh",
                "interpretation": "Executable or kernel source changed after Stage226.",
            })
    else:
        rows.append({
            "base": STAGE226_COMMIT,
            "head": head,
            "path": ";".join(HOT_PATHS),
            "status": "NO_DIFF",
            "hot_path_effect": "stage226_counter_attribution_reusable",
            "interpretation": "No tracked MAT/PVW-SAB executable hot-path delta after Stage226.",
        })
    return rows


def evidence_rows(head: str, hotpath_clear: bool) -> list[dict[str, object]]:
    attr = {row["metric"]: row for row in read_csv(STAGE226_ATTR)} if STAGE226_ATTR.exists() else {}
    proof = read_csv(STAGE226_PROOF) if STAGE226_PROOF.exists() else []
    stage226_decision = next((row["status"] for row in proof if row.get("gate") == "G7_stage226_decision"), "missing")
    wanted = [
        "stage224_backend_vs_wrapper_mean_speedup",
        "stage226_perf_run_backend_vs_wrapper_lane_speedup",
        "stage226_cycles_wrapper_over_backend",
        "stage226_loads_wrapper_over_backend",
        "stage226_stores_wrapper_over_backend",
        "attribution_label",
    ]
    rows = [{
        "metric": "current_head",
        "value": head,
        "source": "git rev-parse HEAD",
        "reuse_status": "reusable" if hotpath_clear else "not_reusable",
        "claim_effect": "current head bridge only; no new benchmark",
    }, {
        "metric": "stage226_decision",
        "value": stage226_decision,
        "source": rel(STAGE226_PROOF),
        "reuse_status": "reusable" if hotpath_clear and stage226_decision.startswith("PASS_") else "not_reusable",
        "claim_effect": "native counter attribution gate",
    }]
    for metric in wanted:
        row = attr.get(metric, {})
        if metric == "stage224_backend_vs_wrapper_mean_speedup":
            reuse_status = "reusable_prior_timing_not_stage245_claim" if hotpath_clear else "requires_refresh"
        else:
            reuse_status = "reusable_attribution_only" if hotpath_clear else "requires_refresh"
        rows.append({
            "metric": metric,
            "value": row.get("value", ""),
            "source": row.get("evidence", rel(STAGE226_ATTR)),
            "reuse_status": reuse_status,
            "claim_effect": row.get("interpretation", "Stage226 attribution bridge."),
        })
    return rows


def claim_rows(hotpath_clear: bool) -> list[dict[str, object]]:
    return [
        {
            "claim": "complete_sab_timing",
            "status": "unchanged_prior_evidence",
            "allowed_wording": "Use Stage224/Stage233-236 repeated complete-SAB timing as timing evidence.",
            "forbidden_wording": "Treat Stage245 as a new speedup measurement.",
            "evidence": "repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv; repro/stage236_set_2_3_4096_r4_highstat_slice/performance_stats.csv",
        },
        {
            "claim": "native_counter_attribution",
            "status": "reusable_attribution_only" if hotpath_clear else "refresh_required",
            "allowed_wording": "Stage226 counters explain the same unchanged exact backend-vs-wrapper hot path.",
            "forbidden_wording": "Claim theoretical optimality or universal AVX512 optimality from these counters.",
            "evidence": rel(STAGE226_ATTR),
        },
        {
            "claim": "theoretical_optimality",
            "status": "blocked",
            "allowed_wording": "Keep optimality as an open theory/model/assembly gate.",
            "forbidden_wording": "State that MAT-aware AVX512 reached the theoretical optimum.",
            "evidence": "theory_checks/stage245_counter_reuse_boundary.md",
        },
        {
            "claim": "new_algorithm_scope",
            "status": "unchanged",
            "allowed_wording": "Selected binary exact dense PVW/MAT-SAB claim only.",
            "forbidden_wording": "Extend to compact route, non-binary branches, or all parameters.",
            "evidence": "repro/stage240_scoped_latex_draft/claim_audit.csv",
        },
    ]


def gate_rows(inputs: list[dict[str, object]], deltas: list[dict[str, object]], evidence: list[dict[str, object]]) -> list[dict[str, object]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    hotpath_clear = all(row["status"] == "NO_DIFF" for row in deltas)
    stage226_ok = any(row["metric"] == "stage226_decision" and str(row["value"]).startswith("PASS_") for row in evidence)
    decision = DECISION_PASS if inputs_ok and hotpath_clear and stage226_ok else DECISION_FAIL
    return [
        {
            "gate": "G1_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "stage226 inputs",
            "value": "all present" if inputs_ok else "missing input",
            "evidence": rel(INPUTS),
            "interpretation": "Counter bridge starts only from recorded Stage226 native evidence.",
        },
        {
            "gate": "G2_hotpath_delta",
            "status": "PASS_NO_HOTPATH_DELTA" if hotpath_clear else "FAIL_HOTPATH_DELTA",
            "metric": "git diff main.c Makefile include src",
            "value": "no diff" if hotpath_clear else "diff present",
            "evidence": rel(CODE_DELTA),
            "interpretation": "No source delta permits reuse of Stage226 attribution; source delta requires a fresh native run.",
        },
        {
            "gate": "G3_stage226_counter_gate",
            "status": "PASS" if stage226_ok else "FAIL",
            "metric": "Stage226 decision",
            "value": next((row["value"] for row in evidence if row["metric"] == "stage226_decision"), "missing"),
            "evidence": rel(STAGE226_PROOF),
            "interpretation": "Stage226 itself must have passed before reuse.",
        },
        {
            "gate": "G4_claim_boundary",
            "status": "PASS_ATTRIBUTION_ONLY",
            "metric": "no new optimality/performance claim",
            "value": "enforced",
            "evidence": rel(CLAIMS),
            "interpretation": "Stage245 is a bridge, not a new benchmark or theorem.",
        },
        {
            "gate": "G5_stage245_decision",
            "status": decision,
            "metric": "decision",
            "value": decision,
            "evidence": rel(GATES),
            "interpretation": "Proceed to broader algorithm/proof gates only after respecting this boundary.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage246_nonbinary_or_compact_algorithm_gate",
            "entry_condition": "A broader-than-selected-binary algorithmic claim is proposed.",
            "gate": "closed equations, invariant proof obligations, correctness/noise/resource matrix, full-SAB A/B",
            "status": "blocked_until_new_design",
            "failure_action": "Do not extend selected binary exact dense claim.",
            "evidence": "repro/stage240_scoped_latex_draft/claim_audit.csv",
        },
        {
            "priority": "P1",
            "route": "stage247_batchboot_monitor_rerun",
            "entry_condition": "Before final submission or after USENIX/DBLP/Crossref metadata changes.",
            "gate": "official source route only; no generated BibTeX",
            "status": "future_monitor",
            "failure_action": "Leave BatchBoot TODO.",
            "evidence": "repro/stage244_batchboot_bibtex_monitor/remaining_todo.csv",
        },
        {
            "priority": "P2",
            "route": "fresh_native_counter_rerun",
            "entry_condition": "Any future change touches main.c, Makefile, include/, src/, benchmark command semantics, or backend flags.",
            "gate": "native perf counters on the changed binary",
            "status": "conditional",
            "failure_action": "Mark Stage226 counters historical only.",
            "evidence": "repro/stage245_current_head_counter_bridge/code_delta.csv",
        },
    ]


def artifact_rows(paths: list[Path]) -> list[dict[str, object]]:
    rows = []
    for path in paths:
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256(path) if path.exists() and path.is_file() else "",
            "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        })
    return rows


def write_docs(head: str, inputs, deltas, evidence, claims, gates, nextq) -> None:
    decision = gates[-1]["status"]
    write_text(DOC, f"""# Stage245 Current-Head Counter Bridge

Decision: `{decision}`.

Stage245 verifies whether Stage226 native counter attribution can still be used
for the current head. It does not run a new benchmark. Its sole executable-code
test is `git diff --name-status {STAGE226_COMMIT}..{head} -- main.c Makefile include src`.

## Code Delta

{table(deltas, ["base", "head", "path", "status", "hot_path_effect", "interpretation"])}

## Evidence Bridge

{table(evidence, ["metric", "value", "source", "reuse_status", "claim_effect"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])}

## Proof Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

## Inputs

{table(inputs, ["input", "status", "role", "bytes"])}
""")
    write_text(REPORT, f"""# Stage245 Report

Decision: `{decision}`.

Stage245 records that the executable MAT/PVW-SAB hot path has no tracked source
delta after Stage226. Therefore Stage226 native counters can remain cited as
mechanism attribution for the unchanged exact route. The primary speedup metric
remains complete-SAB `T_bootstrap/r` from repeated timing stages, and theoretical
optimality remains blocked.
""")
    write_text(PLAN, f"""# Stage245 Current-Head Counter Bridge Plan

## Objective

Bridge Stage226 native counter evidence to current head only if executable
MAT/PVW-SAB code is unchanged.

## Command

```text
python scripts/build_stage245_current_head_counter_bridge.py
```

## Gates

- Inputs from Stage226 exist.
- `git diff --name-status {STAGE226_COMMIT}..HEAD -- main.c Makefile include src` is empty.
- Stage226 decision is pass.
- Claim boundary states attribution-only reuse.
""")
    write_text(THEORY, """# Stage245 Counter Reuse Boundary

Stage245 is a provenance and claim-boundary check, not a performance or
optimality proof.

If `main.c`, `Makefile`, `include/`, and `src/` are unchanged after Stage226,
then the Stage226 native counter run still describes the same compiled hot-path
sources under the same explicit route. This supports mechanism attribution for
the selected exact dense backend-vs-wrapper comparison.

It does not prove:

- theoretical optimality of MAT-aware AVX512;
- universal superiority of one layout;
- a new complete-SAB speedup;
- non-binary, compact-route, or all-parameter correctness.

Any future executable-code or benchmark-command change must trigger a fresh
native counter run before Stage226 counters are cited for the new binary.
""")
    write_text(VARIANT, """# MAT-RLWE SAB Stage245 Counter Bridge

Stage245 keeps the PVW/MAT-SAB algorithm unchanged. It only records whether
native counter attribution from Stage226 remains connected to the current head.

Algorithmic state:

- selected binary exact dense PVW/MAT-SAB remains the measured path;
- scalar SAB remains the baseline;
- complete-SAB `T_bootstrap/r` remains the throughput metric;
- Stage226 counters are mechanism attribution only;
- compact and non-binary routes remain future proof/implementation gates.
""")
    write_text(REPRO_CMDS, f"""# Stage245 Reproduction Commands

```text
python scripts/build_stage245_current_head_counter_bridge.py
git diff --name-status {STAGE226_COMMIT}..HEAD -- main.c Makefile include src
python -m py_compile scripts/build_stage245_current_head_counter_bridge.py
```

Decision: `{decision}`.
""")


def update_project_files(head: str, decision: str) -> None:
    append_once(ROADMAP, "## Stage 245: Current-Head Counter Bridge", f"""
## Stage 245: Current-Head Counter Bridge

Goal:

```text
Audit whether Stage226 native counter attribution remains valid for the current
head by checking executable MAT/PVW-SAB hot-path deltas.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. The Stage226 native
counter evidence is bridged as attribution-only because no tracked hot-path
source delta exists after Stage226. It is not a new timing or optimality claim.
```
""")
    append_once(GOAL, "Stage245 current-head counter bridge", f"""
- Stage245 current-head counter bridge records `{decision}`: Stage226 native
  counters remain usable as attribution-only evidence for the unchanged exact
  dense MAT/PVW-SAB route, but do not prove theoretical optimality or a new
  speedup.
""")
    append_once(CURRENT_GOAL, "### Stage245 current-head counter bridge", f"""
### Stage245 current-head counter bridge

`{decision}` records a current-head provenance bridge for Stage226 native
counter attribution. The active goal remains open because broader algorithmic
routes, theoretical optimality, non-binary support, and final citation closure
remain incomplete.
""")
    append_once(HYPOTHESES, "H10_stage245_current_head_counter_bridge:", f"""
H10_stage245_current_head_counter_bridge:
  status: current_head_counter_bridge_attribution_only
  evidence:
    - repro/stage245_current_head_counter_bridge/code_delta.csv
    - repro/stage245_current_head_counter_bridge/evidence_bridge.csv
    - repro/stage245_current_head_counter_bridge/proof_gate.csv
    - docs/stage245_current_head_counter_bridge.md
  conclusion: >
    Stage245 records {decision}. It checks the current head against Stage226
    and finds no tracked executable MAT/PVW-SAB hot-path delta. Stage226 native
    counters can be cited as attribution-only evidence for the unchanged exact
    route, not as a new speedup, novelty, or theoretical-optimality proof.
""")
    append_once(RUN_LOG, "stage245-current-head-counter-bridge-001", f"""stage245-current-head-counter-bridge-001,{date.today().isoformat()},{head},Stage 245,provenance_audit,"python scripts/build_stage245_current_head_counter_bridge.py","Stage226 counters + git hot-path diff",n/a,{decision},"Stage226 counters bridged as attribution-only; no executable hot-path delta.",docs/stage245_current_head_counter_bridge.md; repro/stage245_current_head_counter_bridge/proof_gate.csv
""")
    append_once(MANIFEST, "- stage245_current_head_counter_bridge:", """
- stage245_current_head_counter_bridge:
  - `docs/stage245_current_head_counter_bridge.md`
  - `experiments/stage245_current_head_counter_bridge_plan.md`
  - `theory_checks/stage245_counter_reuse_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage245_counter_bridge.md`
  - `scripts/build_stage245_current_head_counter_bridge.py`
  - `repro/stage245_current_head_counter_bridge/`
""")
    append_once(CHECKLIST, "Stage245 current-head counter bridge records attribution-only reuse", f"""
- [x] Stage245 current-head counter bridge records attribution-only reuse `{decision}`.
""")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    head = run_git(["rev-parse", "--short", "HEAD"])
    inputs = input_rows()
    deltas = code_delta_rows(head)
    hotpath_clear = all(row["status"] == "NO_DIFF" for row in deltas)
    evidence = evidence_rows(head, hotpath_clear)
    claims = claim_rows(hotpath_clear)
    gates = gate_rows(inputs, deltas, evidence)
    nextq = next_rows()

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(CODE_DELTA, deltas, ["base", "head", "path", "status", "hot_path_effect", "interpretation"])
    write_csv(EVIDENCE, evidence, ["metric", "value", "source", "reuse_status", "claim_effect"])
    write_csv(CLAIMS, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])

    write_docs(head, inputs, deltas, evidence, claims, gates, nextq)
    artifacts = [DOC, PLAN, THEORY, VARIANT, INPUTS, CODE_DELTA, EVIDENCE, CLAIMS, GATES, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "exists", "sha256", "bytes"])
    update_project_files(head, gates[-1]["status"])
    print(f"Stage245 report: {rel(DOC)}")
    print(f"Stage245 decision: {gates[-1]['status']}")


if __name__ == "__main__":
    main()
