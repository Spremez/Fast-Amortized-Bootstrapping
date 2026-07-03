#!/usr/bin/env python3
"""Stage160: post-fusion profile/frontier gate."""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage160_post_fusion_frontier"

SUMMARY_CSV = OUT_DIR / "summary.csv"
PROFILE_CSV = OUT_DIR / "profile_sample.csv"
SCHEDULE_CSV = OUT_DIR / "schedule_guard.csv"
COMPONENT_CSV = OUT_DIR / "component_shares.csv"
NEXT_QUEUE_CSV = OUT_DIR / "next_stage_queue.csv"
CANDIDATE_CSV = OUT_DIR / "candidate_status.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage160_post_fusion_frontier.md"
PLAN_MD = ROOT / "experiments" / "stage160_post_fusion_frontier_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage160_post_fusion_frontier_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_post_fusion_frontier.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

R_VALUE = int(os.environ.get("STAGE160_R", "6"))
BENCH_REPS = int(os.environ.get("STAGE160_BENCH_REPS", "1"))
MAKE_JOBS = os.environ.get("STAGE160_JOBS", "$(nproc)")

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
    "SAB_PVW_SUB_DECOMP_FUSION=true "
    f"SAB_PVW_BENCH=true SAB_PVW_BENCH_R={R_VALUE} "
    f"SAB_PVW_BENCH_REPS={BENCH_REPS} SAB_PVW_BODY_PROFILE=true"
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    clean = "".join(ch if ch in "\n\t" or 32 <= ord(ch) < 127 else "?" for ch in text)
    return "\n".join(line.rstrip() for line in clean.splitlines()).rstrip() + "\n"


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def wsl_repo() -> str:
    drive = ROOT.drive.rstrip(":").lower()
    rest = ROOT.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


def run_wsl(command: str, log: Path, timeout: int = 1800) -> int:
    bash_cmd = f"cd {wsl_repo()} && {command}"
    print(f"[stage160] {command}", flush=True)
    proc = subprocess.run(
        ["wsl", "bash", "-lc", bash_cmd],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    output = proc.stdout.decode("utf-8", errors="ignore")
    write_text_lf(log, sanitize("\n".join([
        f"command: {command}",
        f"returncode: {proc.returncode}",
        "--- output ---",
        output,
    ])))
    return proc.returncode


def extract_fields(line: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for token in line.split():
        if "=" in token:
            key, value = token.split("=", 1)
            fields[key] = value.rstrip("x")
    return fields


def fnum(fields: Dict[str, str], name: str) -> float:
    try:
        return float(fields.get(name, "0") or "0")
    except ValueError:
        return 0.0


def find_line(log: Path, marker: str) -> str:
    found = ""
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        if marker in line:
            found = line
    return found


def build_and_run() -> tuple[int, int]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_rc = run_wsl(
        f"make clean >/dev/null 2>&1 || true && make {BASE_FLAGS} -j{MAKE_JOBS}",
        OUT_DIR / "build.log",
        timeout=1200,
    )
    run_rc = 1
    if build_rc == 0:
        run_rc = run_wsl("stdbuf -o0 ./main", OUT_DIR / "run.log", timeout=1800)
    run_wsl("make clean >/dev/null 2>&1 || true", OUT_DIR / "cleanup.log", timeout=300)
    return build_rc, run_rc


def schedule_rows(profile: Dict[str, str]) -> List[Dict[str, str]]:
    in_n = int(profile.get("in_N", "0") or "0")
    h = int(profile.get("h", "0") or "0")
    r_prec = int(profile.get("r_prec", "0") or "0")
    sparse_mul_calls = int(profile.get("sparse_mul_calls", "0") or "0")
    expected_rgsw = sparse_mul_calls * (h + 1)
    expected_cmux = expected_rgsw * r_prec * in_n
    expected_ncmux = expected_rgsw * ((1 << r_prec) - 1)
    expected_sub_a = sparse_mul_calls * h
    expected_copyback = ((h + 1) * (r_prec % 2)) % 2
    checks = [
        ("rgsw_monomial_calls", profile.get("rgsw_monomial_calls", ""), str(expected_rgsw), "sparse_mul_calls*(h+1)"),
        ("cmux_calls", profile.get("cmux_calls", ""), str(expected_cmux), "(h+1)*r_prec*in_N"),
        ("mat_ep_calls", profile.get("mat_ep_calls", ""), str(expected_cmux), "one MAT EP per CMUX/NCMUX update"),
        ("from_dft_calls", profile.get("cmux_from_dft_calls", ""), str(expected_cmux), "one materialization per update"),
        ("ncmux_calls", profile.get("ncmux_calls", ""), str(expected_ncmux), "(h+1)*(2^r_prec-1)"),
        ("sub_a_calls", profile.get("sub_a_calls", ""), str(expected_sub_a), "one sparse subtraction per nonzero sparse term"),
        ("copyback_calls", profile.get("copyback_calls", ""), str(expected_copyback), "active-buffer final normalization only"),
    ]
    rows = []
    for metric, observed, expected, detail in checks:
        rows.append({
            "metric": metric,
            "observed": observed,
            "expected": expected,
            "status": "PASS" if observed == expected else "FAIL",
            "detail": detail,
        })
    return rows


def component_rows(profile: Dict[str, str]) -> List[Dict[str, str]]:
    full_us = max(fnum(profile, "full_us"), 1.0)
    components = [
        ("mat_ep_plus_subdecomp", fnum(profile, "mat_ep_us"), "Dominant fused MAT EP/decompose block; now includes direct diff decomposition under the fusion flag."),
        ("from_dft_materialization", fnum(profile, "cmux_from_dft_us"), "Still one materialization per update; reducing count requires representation/schedule change."),
        ("explicit_sub", fnum(profile, "cmux_sub_us"), "Should be near zero after sub-decompose fusion; this route is now closed."),
        ("ncmux_auto", fnum(profile, "ncmux_auto_us"), "Small automorphism tail."),
        ("sub_a", fnum(profile, "sub_a_us"), "Sparse subtraction tail."),
        ("copyback", fnum(profile, "copyback_us"), "Active-buffer copyback tail."),
    ]
    used = sum(value for _, value, _ in components)
    components.append((
        "unattributed_or_timer_overlap",
        max(full_us - used, 0.0),
        "Residual body/post-processing/timer overlap; target only with finer evidence.",
    ))
    rows: List[Dict[str, str]] = []
    for name, value, interpretation in components:
        share = value / full_us
        ceiling_elim = 1.0 / max(1.0 - share, 1e-9)
        ceiling_2x = 1.0 / max(1.0 - share / 2.0, 1e-9)
        rows.append({
            "component": name,
            "us": f"{value:.3f}",
            "share_of_full": f"{share:.6f}",
            "ceiling_if_eliminated": f"{ceiling_elim:.6f}",
            "ceiling_if_2x_local": f"{ceiling_2x:.6f}",
            "interpretation": interpretation,
        })
    rows.sort(key=lambda row: float(row["share_of_full"]), reverse=True)
    return rows


def next_queue(component: List[Dict[str, str]]) -> List[Dict[str, str]]:
    top = component[0]["component"] if component else "unknown"
    return [
        {
            "priority": "P0",
            "stage": "161",
            "name": "post-fusion native counter or proxy attribution",
            "goal": "Determine whether the fused MAT EP block is FMA-bound, load/store-bound, or spill/cache-bound on the real performance platform.",
            "entry_condition": f"Stage160 top component is {top}.",
            "gate": "Native perf counters if available; otherwise objdump/proxy evidence marked non-final.",
        },
        {
            "priority": "P0",
            "stage": "162",
            "name": "materialization-count reduction feasibility",
            "goal": "Test a representation-changing path that can reduce the 573440 from_DFT materializations or dense same-format update count.",
            "entry_condition": "from_DFT materialization remains a dominant component after sub-decompose fusion.",
            "gate": "Reject before full SAB unless a closure proof and isolated correctness gate exist.",
        },
        {
            "priority": "P1",
            "stage": "163",
            "name": "policy/default boundary for sub-decomp fusion",
            "goal": "Decide whether the explicit Stage159 promotion candidate should become part of the named best research path.",
            "entry_condition": "Stage159 pass plus Stage160 schedule/profile sanity.",
            "gate": "No scalar/default change without an explicit policy commit.",
        },
    ]


def candidate_status(stage159_decision: str) -> List[Dict[str, str]]:
    return [
        {
            "candidate": "H83 sub-decompose fusion",
            "latest_decision": stage159_decision,
            "action": "KEEP_EXPLICIT_PROMOTION_CANDIDATE",
            "reason": "Repeated complete-SAB T_bootstrap/r, noise, and resource gates passed.",
        },
        {
            "candidate": "explicit sub PVW_TMLWE write/read route",
            "latest_decision": "CLOSED_BY_STAGE159",
            "action": "DO_NOT_REOPEN_WITHOUT_NEW_MECHANISM",
            "reason": "The remaining explicit sub time is expected to be near zero under SAB_PVW_SUB_DECOMP_FUSION.",
        },
        {
            "candidate": "same-format blind layout tuning",
            "latest_decision": "STILL_PROFILE_BOUNDED",
            "action": "REQUIRE_COUNTER_OR_COUNT_CHANGE",
            "reason": "Stage154 rejected body-major and Stage155 closed blind layout work without a new measured mechanism.",
        },
    ]


def stage159_decision() -> str:
    path = ROOT / "repro" / "stage159_sub_decomp_fusion_repeated_gate" / "summary.csv"
    if not path.exists():
        return "MISSING_STAGE159_SUMMARY"
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("gate") == "stage159_decision":
                return row.get("status", "")
    return "MISSING_STAGE159_DECISION"


def build_summary(build_rc: int, run_rc: int, schedule: List[Dict[str, str]], component: List[Dict[str, str]], decision159: str) -> List[Dict[str, str]]:
    schedule_ok = all(row["status"] == "PASS" for row in schedule)
    top_component = component[0]["component"] if component else "MISSING"
    top_share = component[0]["share_of_full"] if component else "0"
    if build_rc == 0 and run_rc == 0 and schedule_ok and decision159.startswith("PASS_STAGE159"):
        decision = "PASS_STAGE160_POST_FUSION_FRONTIER_RECORDED"
        next_action = "Proceed to Stage161/162: counter attribution or materialization-count feasibility."
    else:
        decision = "FAIL_STAGE160_POST_FUSION_FRONTIER"
        next_action = "Repair profile/schedule gate before choosing the next optimization target."
    return [
        {
            "gate": "stage160_build_run",
            "status": "PASS" if build_rc == 0 and run_rc == 0 else "FAIL",
            "metric": "build_rc;run_rc",
            "value": f"{build_rc};{run_rc}",
            "evidence": f"{rel(OUT_DIR / 'build.log')}; {rel(OUT_DIR / 'run.log')}",
            "detail": "Build and run the explicit Stage159 fusion path with body profile enabled.",
            "next_action": "",
        },
        {
            "gate": "stage160_schedule_guard",
            "status": "PASS" if schedule_ok else "FAIL",
            "metric": "schedule_counts",
            "value": "PASS" if schedule_ok else "FAIL",
            "evidence": rel(SCHEDULE_CSV),
            "detail": "Confirm fusion did not change the sparse SAB schedule counts.",
            "next_action": "Stop if any count differs.",
        },
        {
            "gate": "stage160_component_frontier",
            "status": "PASS",
            "metric": "top_component;share",
            "value": f"{top_component};{top_share}",
            "evidence": rel(COMPONENT_CSV),
            "detail": "Post-fusion component shares determine the next optimization target.",
            "next_action": "Prioritize count-changing or counter-supported work over blind layout variants.",
        },
        {
            "gate": "stage160_decision",
            "status": decision,
            "metric": "next_frontier",
            "value": top_component,
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage160 is a route-selection gate after Stage159 promotion evidence.",
            "next_action": next_action,
        },
    ]


def write_docs(summary: List[Dict[str, str]], schedule: List[Dict[str, str]], component: List[Dict[str, str]], queue: List[Dict[str, str]], candidates: List[Dict[str, str]]) -> None:
    decision = summary[-1]["status"]
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage160 Post-Fusion Frontier Plan",
        "",
        "Date: 2026-07-03",
        "",
        "Goal: after Stage159 promotes sub-decompose fusion as an explicit candidate, refresh the profile frontier on the fused r=6 H14 path.",
        "",
        "Primary question: which remaining component can still move complete-SAB `T_bootstrap/r`?",
        "",
        "Boundary: no production code changes; profile timing is attribution evidence, not a final latency claim.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage160 Post-Fusion Frontier Model",
        "",
        "Date: 2026-07-03",
        "",
        "Sub-decompose fusion removes the explicit PVW_TMLWE difference materialization, but it does not change the SAB sparse schedule. Therefore the expected counts remain:",
        "",
        "```text",
        "RGSW monomial calls = (h+1)",
        "MAT EP/from_DFT calls = (h+1) * r_prec * N = 40 * 7 * 2048 = 573440",
        "NCMUX calls = (h+1) * (2^r_prec - 1) = 5080",
        "sub_a calls = h = 39",
        "```",
        "",
        "If these counts hold, further multi-percent gains require either a better dominant kernel or a representation/schedule change that reduces materialization or dense update count.",
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# MAT-RLWE SAB Post-Fusion Frontier",
        "",
        "Date: 2026-07-03",
        "",
        "Profiled explicit path:",
        "",
        "```text",
        "MAT_TRGSW_AVX512_RGT4_FUSED=true",
        "SAB_PVW_ACTIVE_BUFFER_FUSION=true",
        "SAB_PVW_BACKEND_FROM_DFT_ADD=true",
        "SAB_PVW_SUB_DECOMP_FUSION=true",
        "SAB_PVW_BODY_PROFILE=true",
        "```",
        "",
        "This is a route-selection artifact for the next research loop, not a default-path change.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage160 Post-Fusion Frontier",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "## Summary Gates",
        "",
        table(summary, ["gate", "status", "metric", "value", "detail", "next_action"]),
        "",
        "## Schedule Guard",
        "",
        table(schedule, ["metric", "observed", "expected", "status", "detail"]),
        "",
        "## Component Frontier",
        "",
        table(component, ["component", "us", "share_of_full", "ceiling_if_2x_local", "interpretation"]),
        "",
        "## Candidate Status",
        "",
        table(candidates, ["candidate", "latest_decision", "action", "reason"]),
        "",
        "## Next Queue",
        "",
        table(queue, ["priority", "stage", "name", "goal", "gate"]),
    ]) + "\n")


def update_global(summary: List[Dict[str, str]]) -> None:
    decision = summary[-1]["status"]
    top = summary[-2]["value"]
    append_once(ROADMAP_MD, "## Stage 160: Post-Fusion Frontier", f"""
## Stage 160: Post-Fusion Frontier

Goal:

```text
Refresh the profile frontier after Stage159 sub-decompose fusion and choose the
next non-theoretical optimization target from actual component shares.
```

Status:

```text
Completed. Stage160 records {decision}; next frontier is {top}.
```
""")
    append_once(GOAL_MD, "Stage160 refreshes the post-fusion component frontier", f"""
Stage160 refreshes the post-fusion component frontier after the Stage159
promotion-candidate result. Decision: `{decision}`. It keeps profile timing as
attribution evidence and routes the next work toward counter-supported kernel
limits or materialization-count reduction.
""")
    append_once(CURRENT_GOAL_MD, "64. Treat Stage160 as the post-fusion frontier gate", f"""
64. Treat Stage160 as the post-fusion frontier gate:
    `{decision}`. It prevents a theory loop by selecting the next target from
    measured post-fusion component shares rather than speculative layout work.
""")
    append_once(HYPOTHESIS_YAML, "H84_post_fusion_frontier", f"""
  - id: H84_post_fusion_frontier
    statement: >
      After sub-decompose fusion, the next useful PVW/MAT-SAB optimization
      should target the measured dominant post-fusion components, not another
      blind same-format layout variant.
    mechanism: >
      Stage160 profiles the explicit r=6 fusion path, verifies schedule counts,
      and ranks component shares for the next falsifiable gate.
    status: stage160_post_fusion_frontier
    evidence: docs/stage160_post_fusion_frontier.md; experiments/stage160_post_fusion_frontier_plan.md; theory_checks/stage160_post_fusion_frontier_model.md; repro/stage160_post_fusion_frontier/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - body-profile build or correctness fails
      - sparse schedule counts no longer match the SAB model
      - next-stage queue is not tied to measured component shares
""")
    append_once(RUN_LOG, "stage160-post-fusion-frontier-001", f"stage160-post-fusion-frontier-001,2026-07-03,{git_head()},Stage 160,spqlios_avx512,python scripts/build_stage160_post_fusion_frontier.py,r={R_VALUE}; bench_reps={BENCH_REPS}; body_profile; sub_decomp_fusion,default-rng,{decision},Post-fusion profile/frontier route-selection gate.,{rel(OUT_DIR)}\n")
    append_once(MANIFEST, "stage160_post_fusion_frontier", f"""
- stage160_post_fusion_frontier: `{decision}`
  - `docs/stage160_post_fusion_frontier.md`
  - `experiments/stage160_post_fusion_frontier_plan.md`
  - `theory_checks/stage160_post_fusion_frontier_model.md`
  - `repro/stage160_post_fusion_frontier/`
""")
    append_once(CHECKLIST, "Stage160 post-fusion frontier pack", """
- [x] Stage160 post-fusion profile/frontier pack recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() else "",
            "size_bytes": str(path.stat().st_size) if path.exists() else "",
        })
    write_csv(ARTIFACT_CSV, rows, ["artifact", "exists", "sha256", "size_bytes"])


def main() -> int:
    build_rc, run_rc = build_and_run()
    run_log = OUT_DIR / "run.log"
    correctness_line = find_line(run_log, "SAB_PVW_BENCH correctness target_full") if run_log.exists() else ""
    bench_line = find_line(run_log, "SAB_PVW_BENCH summary target_full") if run_log.exists() else ""
    profile_line = find_line(run_log, "SAB_PVW_BODY_PROFILE sample") if run_log.exists() else ""
    profile = extract_fields(profile_line)
    bench = extract_fields(bench_line)
    if correctness_line and correctness_line.rsplit(" ", 1)[-1] != "Pass":
        run_rc = 1

    profile_row = dict(profile)
    profile_row.update({
        "correctness": correctness_line.rsplit(" ", 1)[-1] if correctness_line else "MISSING",
        "pvw_avg_us": bench.get("pvw_avg_us", ""),
        "pvw_lane_avg_us": bench.get("pvw_lane_avg_us", ""),
        "scalar_repeated_avg_us": bench.get("scalar_repeated_avg_us", ""),
        "speedup_vs_scalar_repeated": bench.get("speedup_vs_scalar_repeated", ""),
        "source_log": rel(run_log),
    })
    profile_fields = [
        "correctness", "lanes", "in_N", "out_N", "h", "r_prec", "full_us",
        "pvw_avg_us", "pvw_lane_avg_us", "scalar_repeated_avg_us",
        "speedup_vs_scalar_repeated", "setup_tv_xb_calls", "setup_tv_xb_us",
        "blind_rotate_calls", "blind_rotate_us", "sparse_mul_calls",
        "sparse_mul_us", "rgsw_monomial_calls", "rgsw_monomial_us",
        "cmux_calls", "cmux_us", "ncmux_calls", "ncmux_us",
        "cmux_sub_calls", "cmux_sub_us", "cmux_from_dft_calls",
        "cmux_from_dft_us", "cmux_add_calls", "cmux_add_us",
        "ncmux_auto_calls", "ncmux_auto_us", "mat_ep_calls", "mat_ep_us",
        "sub_a_calls", "sub_a_us", "copyback_calls", "copyback_us",
        "source_log",
    ]
    write_csv(PROFILE_CSV, [profile_row], profile_fields)

    schedule = schedule_rows(profile)
    component = component_rows(profile)
    queue = next_queue(component)
    decision159 = stage159_decision()
    candidates = candidate_status(decision159)
    summary = build_summary(build_rc, run_rc, schedule, component, decision159)

    write_csv(SCHEDULE_CSV, schedule, ["metric", "observed", "expected", "status", "detail"])
    write_csv(COMPONENT_CSV, component, ["component", "us", "share_of_full", "ceiling_if_eliminated", "ceiling_if_2x_local", "interpretation"])
    write_csv(NEXT_QUEUE_CSV, queue, ["priority", "stage", "name", "goal", "entry_condition", "gate"])
    write_csv(CANDIDATE_CSV, candidates, ["candidate", "latest_decision", "action", "reason"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(summary, schedule, component, queue, candidates)
    update_global(summary)
    write_artifacts([
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, PROFILE_CSV,
        SCHEDULE_CSV, COMPONENT_CSV, NEXT_QUEUE_CSV, CANDIDATE_CSV,
        OUT_DIR / "build.log", OUT_DIR / "run.log", OUT_DIR / "cleanup.log",
        Path(__file__).resolve(),
    ])

    decision = summary[-1]["status"]
    print(f"Stage160 post-fusion frontier: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
