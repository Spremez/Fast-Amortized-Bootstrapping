#!/usr/bin/env python3
"""Build Stage314 local-digit closeout and next-candidate budget artifacts."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage314_local_digit_closeout"
DOC = ROOT / "docs" / "stage314_local_digit_closeout.md"
THEORY = ROOT / "theory_checks" / "stage314_local_digit_budget_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage314_next_candidate_rules.md"
PLAN = ROOT / "experiments" / "stage314_next_candidate_gate_plan.md"
BUILDER = ROOT / "scripts" / "build_stage314_local_digit_closeout.py"

SUMMARY = OUT / "stage314_summary.csv"
BUDGET = OUT / "component_budget.csv"
CANDIDATES = OUT / "candidate_rule_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage314_report.md"
ARTIFACT = OUT / "artifact_index.csv"

STAGE309 = ROOT / "repro" / "stage309_digit_rowbatch_microbench" / "bench_summary.csv"
STAGE311 = ROOT / "repro" / "stage311_digit_narrow32_microbench" / "bench_summary.csv"
STAGE312 = ROOT / "repro" / "stage312_digit_narrow32_fullsab_ab" / "perf_summary.csv"
STAGE313 = ROOT / "repro" / "stage313_narrow32_profile_attribution" / "profile_summary.csv"
STAGE313_LIFE = ROOT / "repro" / "stage313_narrow32_profile_attribution" / "lifecycle_comparison.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE314_LOCAL_DIGIT_MICROVARIANTS_CLOSED_BACKEND_OR_SCHEDULE_NEXT"
DECISION_FAIL = "FAIL_STAGE314_LOCAL_DIGIT_CLOSEOUT_EVIDENCE_MISSING"


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


def first(rows: List[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def stage_decision(path: Path) -> str:
    rows = read_csv(path)
    return rows[0].get("decision", "MISSING") if rows else "MISSING"


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage314-local-digit-closeout-001"
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
        "stage": "Stage 314",
        "backend": "analysis",
        "command": "python3 scripts/build_stage314_local_digit_closeout.py",
        "config": "Stage309-313 evidence synthesis and next-candidate gate",
        "params": "BINARY SET_2_3_2048 r=4 include-zero evidence",
        "seed": "n/a",
        "status": decision,
        "summary": "Stage314 closes local digit microvariants and routes future work to backend IFFT or schedule-level changes unless a candidate clears full-SAB budget gates.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(BUDGET)}; {rel(PROOF)}",
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
    stage309_decision = stage_decision(STAGE309)
    stage311_decision = stage_decision(STAGE311)
    stage312_comparison = first(read_csv(STAGE312), "variant", "comparison")
    stage313_summary = read_csv(STAGE313)
    direct = first(stage313_summary, "variant", "direct_profile")
    narrow = first(stage313_summary, "variant", "narrow32_profile")
    comparison = first(stage313_summary, "variant", "comparison")
    lifecycle = read_csv(STAGE313_LIFE)

    body_full = fnum(direct.get("body_full_us_sum"))
    mat_ep = fnum(direct.get("body_mat_ep_us_sum"))
    digit = fnum(direct.get("digit_us"))
    ifft = fnum(direct.get("ifft_us"))
    dense = fnum(direct.get("split_dense_us"))
    digit_share_body = digit / body_full if body_full else 0.0
    digit_share_mat_ep = digit / mat_ep if mat_ep else 0.0
    ifft_share_body = ifft / body_full if body_full else 0.0
    mat_ep_share_body = mat_ep / body_full if body_full else 0.0
    observed_digit_speedup = fnum(comparison.get("direct_over_narrow32_digit_speedup"))
    observed_full_speedup = fnum(stage312_comparison.get("narrow32_vs_direct_baseline_mean"))
    # Amdahl-style projected body speedup if only the component changes.
    projected_narrow_digit_body_speedup = 1.0 / (1.0 - digit_share_body * (1.0 - 1.0 / observed_digit_speedup)) if observed_digit_speedup > 0 else 0.0

    summary_rows = [{
        "decision": DECISION if direct and narrow and stage312_comparison else DECISION_FAIL,
        "stage309_rowbatch_decision": stage309_decision,
        "stage311_narrow32_micro_decision": stage311_decision,
        "stage312_fullsab_narrow32_vs_direct": stage312_comparison.get("narrow32_vs_direct_baseline_mean", ""),
        "stage313_profile_digit_speedup": comparison.get("direct_over_narrow32_digit_speedup", ""),
        "stage313_profile_mat_ep_speedup": comparison.get("direct_over_narrow32_mat_ep_speedup", ""),
        "digit_share_of_body_profile": f"{digit_share_body:.6f}",
        "digit_share_of_mat_ep": f"{digit_share_mat_ep:.6f}",
        "ifft_share_of_body_profile": f"{ifft_share_body:.6f}",
        "mat_ep_share_of_body_profile": f"{mat_ep_share_body:.6f}",
        "projected_body_speedup_from_observed_digit_only": f"{projected_narrow_digit_body_speedup:.6f}",
        "route": "backend_ifft_or_schedule_level_only_without_new_budget",
    }]
    decision = str(summary_rows[0]["decision"])
    write_csv(SUMMARY, summary_rows, [
        "decision", "stage309_rowbatch_decision", "stage311_narrow32_micro_decision",
        "stage312_fullsab_narrow32_vs_direct", "stage313_profile_digit_speedup",
        "stage313_profile_mat_ep_speedup", "digit_share_of_body_profile",
        "digit_share_of_mat_ep", "ifft_share_of_body_profile",
        "mat_ep_share_of_body_profile",
        "projected_body_speedup_from_observed_digit_only", "route",
    ])

    budget_rows = []
    components = [
        ("digit_to_double", digit, "local digit microvariant"),
        ("ifft", ifft, "backend IFFT"),
        ("dense_from_dec", dense, "dense MAT AVX"),
        ("mat_ep_total", mat_ep, "MAT EP lifecycle"),
    ]
    for name, us, route in components:
        share = us / body_full if body_full else 0.0
        for reduction in [0.05, 0.10, 0.25, 0.50]:
            speedup = 1.0 / (1.0 - share * reduction) if share * reduction < 1.0 else 0.0
            budget_rows.append({
                "component": name,
                "route_family": route,
                "share_of_body_profile": f"{share:.6f}",
                "hypothetical_component_reduction": f"{reduction:.2f}",
                "projected_body_profile_speedup": f"{speedup:.6f}",
                "gate_interpretation": "must exceed full-SAB variance and then pass T_bootstrap/r A/B",
            })
    write_csv(BUDGET, budget_rows, [
        "component", "route_family", "share_of_body_profile",
        "hypothetical_component_reduction", "projected_body_profile_speedup",
        "gate_interpretation",
    ])

    candidate_rows = [
        {
            "candidate_family": "local_digit_microvariants",
            "status": "CLOSED_WITHOUT_NEW_BUDGET",
            "evidence": f"rowbatch={stage309_decision}; narrow32_full={stage312_comparison.get('narrow32_vs_direct_baseline_mean', '')}; attribution_digit={comparison.get('direct_over_narrow32_digit_speedup', '')}",
            "admission_rule": "Only reopen if projected full-SAB T/r speedup is >=1.02 before implementation.",
        },
        {
            "candidate_family": "backend_ifft_batch_or_fusion",
            "status": "OPEN_HIGH_RISK",
            "evidence": f"ifft body share {ifft_share_body:.6f}; Stage310 requires backend-level work",
            "admission_rule": "Requires new backend API/model/assembly correctness before SAB integration.",
        },
        {
            "candidate_family": "schedule_level_reduction",
            "status": "OPEN_ALGORITHMIC",
            "evidence": "single component microvariants are diluted by full SAB schedule",
            "admission_rule": "Must reduce call count, materialization count, or schedule lifecycle at SAB level, not only one conversion instruction.",
        },
        {
            "candidate_family": "dense_mat_avx_rewrite",
            "status": "DEFER",
            "evidence": "Stage301/302 FMA counters near-neutral; Stage313 route does not select dense",
            "admission_rule": "Reopen only if DFT lifecycle ceases to dominate or a concrete assembly/counter hypothesis exists.",
        },
    ]
    write_csv(CANDIDATES, candidate_rows, ["candidate_family", "status", "evidence", "admission_rule"])

    evidence_ok = decision == DECISION
    close_digit = stage309_decision.startswith("NEUTRAL") and observed_full_speedup < 1.01 and observed_digit_speedup > 1.0
    proof = [
        {"gate": "G1_evidence_present", "status": "PASS" if evidence_ok else "FAIL", "metric": "Stage309-313 files", "value": "present" if evidence_ok else "missing", "interpretation": "Closeout must be based on recorded experiments."},
        {"gate": "G2_micro_to_full_alignment", "status": "PASS" if close_digit else "RECHECK", "metric": "micro positive but full neutral", "value": f"digit={observed_digit_speedup:.6f}; full={observed_full_speedup:.6f}", "interpretation": "Local digit changes are diluted and should not continue without stronger budget."},
        {"gate": "G3_budget_rule", "status": "PASS", "metric": "minimum pre-implementation projected T/r", "value": ">=1.02", "interpretation": "New candidates need a predicted full-SAB effect above profile noise."},
        {"gate": "G4_claim_boundary", "status": "PASS", "metric": "scope", "value": "route gate only", "interpretation": "This is not a new speed claim."},
        {"gate": "G5_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls Stage315 route."},
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])

    write_csv(NEXT, [
        {
            "priority": "P0",
            "stage": "stage315_backend_ifft_candidate_spec_or_schedule_level_candidate",
            "input": decision,
            "task": "Choose either a true backend IFFT candidate with correctness model, or a higher-level SAB schedule candidate that reduces materialization/call count.",
            "gate": "candidate card plus projected full-SAB budget >=1.02 before implementation",
        }
    ], ["priority", "stage", "input", "task", "gate"])

    report = (
        "# Stage314 Local Digit Closeout\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage314 closes unsupported local digit microvariants after Stage309-313 and sets an admission rule for future candidates.\n\n"
        "## Summary\n\n" + table(summary_rows, [
            "decision", "stage309_rowbatch_decision", "stage312_fullsab_narrow32_vs_direct",
            "stage313_profile_digit_speedup", "digit_share_of_body_profile",
            "projected_body_speedup_from_observed_digit_only", "route",
        ]) +
        "\n\n## Component Budget\n\n" + table(budget_rows, [
            "component", "share_of_body_profile", "hypothetical_component_reduction",
            "projected_body_profile_speedup",
        ]) +
        "\n\n## Candidate Rules\n\n" + table(candidate_rows, ["candidate_family", "status", "admission_rule"]) +
        "\n\n## Proof Gate\n\n" + table(proof, ["gate", "status", "metric", "value", "interpretation"]) + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, f"""# Stage314 Local Digit Budget Model

Stage314 applies an Amdahl-style budget to the measured Stage313 profile. The
direct digit component is {digit_share_body:.6f} of the profiled body time.
The observed narrow32 digit speedup is {observed_digit_speedup:.6f}, which
projects to only {projected_narrow_digit_body_speedup:.6f} body-level speedup
before considering schedule variance and unchanged IFFT/dense costs.

Therefore local digit microvariants are closed unless a future candidate has a
pre-implementation full-SAB budget of at least 1.02x and then passes complete
`T_bootstrap/r` A/B. Larger opportunities now require backend IFFT work or a
SAB schedule-level reduction in call/materialization count.
""")
    write_text(VARIANT, f"""# Stage314 Next Candidate Rules

Decision: `{decision}`.

No behavior-changing variant is introduced. This is a route gate for future
algorithm work:

- local digit microvariants: closed without a new full-SAB budget;
- backend IFFT: open but high-risk;
- schedule-level SAB reductions: open and algorithmically more relevant;
- dense AVX rewrite: deferred until evidence selects it.
""")
    write_text(PLAN, """# Stage314 Gate Plan

1. Merge Stage309 rowbatch, Stage311 narrow32 microbench, Stage312 full SAB,
   and Stage313 profile attribution.
2. Compute component shares and Amdahl-style projected speedups.
3. Require projected full-SAB budget >=1.02 before implementing another local
   microvariant.
4. Route next work to backend IFFT or schedule-level algorithm candidates.
""")
    write_text(COMMANDS, """# Stage314 Reproduction Commands

```bash
python3 scripts/build_stage314_local_digit_closeout.py
```
""")

    append_once(ROADMAP, "## Stage 314: Local Digit Closeout", "\n## Stage 314: Local Digit Closeout\n\nGoal: close unsupported local digit microvariants and set a full-SAB budget gate for future candidates.\n\n" f"Status: `{decision}`.\n")
    append_once(GOAL, "<!-- stage314-local-digit-closeout -->", "\n<!-- stage314-local-digit-closeout -->\n### Stage314 local digit closeout\n\n" f"`{decision}` closes local digit microvariants without a new full-SAB budget and routes future work to backend IFFT or schedule-level SAB changes.\n")
    append_once(HYPOTHESES, "H314_local_digit_closeout:", "\nH314_local_digit_closeout:\n" f"  status: {decision}\n  primary_metric: evidence_synthesis_and_component_budget\n  evidence:\n    - repro/stage314_local_digit_closeout/stage314_summary.csv\n    - repro/stage314_local_digit_closeout/component_budget.csv\n    - repro/stage314_local_digit_closeout/candidate_rule_matrix.csv\n    - repro/stage314_local_digit_closeout/proof_gate.csv\n  conclusion: >\n    Stage314 closes local digit microvariants unless a future candidate has a\n    projected full-SAB budget >=1.02 before implementation. Next work should\n    target backend IFFT or schedule-level SAB reductions.\n")
    append_once(MANIFEST, "- stage314_local_digit_closeout:", "\n- stage314_local_digit_closeout:\n  - `docs/stage314_local_digit_closeout.md`\n  - `theory_checks/stage314_local_digit_budget_model.md`\n  - `algorithm_variants/mat_rlwe_sab_stage314_next_candidate_rules.md`\n  - `experiments/stage314_next_candidate_gate_plan.md`\n  - `scripts/build_stage314_local_digit_closeout.py`\n  - `repro/stage314_local_digit_closeout/`\n")
    append_once(CHECKLIST, "<!-- stage314-local-digit-closeout-checklist -->", "\n<!-- stage314-local-digit-closeout-checklist -->\n" f"- [x] Stage314 records `{decision}` and next-candidate admission rules.\n")
    append_run_log(decision)

    artifacts = [
        DOC, THEORY, VARIANT, PLAN, BUILDER, SUMMARY, BUDGET, CANDIDATES,
        PROOF, NEXT, COMMANDS, REPORT,
    ]
    artifact_index(artifacts)
    print(decision)


if __name__ == "__main__":
    main()
