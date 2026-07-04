#!/usr/bin/env python3
"""Build Stage312 full-SAB A/B artifacts for narrow32 digit conversion."""

from __future__ import annotations

import csv
import hashlib
import math
import re
import subprocess
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage312_digit_narrow32_fullsab_ab"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage312_digit_narrow32_fullsab_ab.md"
THEORY = ROOT / "theory_checks" / "stage312_digit_narrow32_fullsab_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage312_digit_narrow32_fullsab.md"
PLAN = ROOT / "experiments" / "stage312_digit_narrow32_fullsab_ab_plan.md"
RUNNER = ROOT / "scripts" / "run_stage312_digit_narrow32_fullsab_ab.sh"
BUILDER = ROOT / "scripts" / "build_stage312_digit_narrow32_fullsab_ab.py"

PERF_SAMPLES = OUT / "perf_samples.csv"
PERF_SUMMARY = OUT / "perf_summary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage312_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION_PASS = "PASS_STAGE312_DIGIT_NARROW32_FULLSAB_POSITIVE_NOISE_REQUIRED"
DECISION_NEUTRAL = "NEUTRAL_STAGE312_DIGIT_NARROW32_FULLSAB_NO_PROMOTION"
DECISION_FAIL = "FAIL_STAGE312_DIGIT_NARROW32_FULLSAB_CORRECTNESS"

CORRECT_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH correctness target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) h=(?P<h>\d+) r_prec=(?P<r_prec>\d+): (?P<status>\w+)"
)
SAMPLE_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH sample target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) rep=(?P<rep>\d+) pvw_us=(?P<pvw_us>\d+) "
    r"pvw_lane_us=(?P<pvw_lane_us>[0-9.]+) scalar_repeated_us=(?P<scalar_us>\d+) "
    r"scalar_lane_us=(?P<scalar_lane_us>[0-9.]+) speedup=(?P<speedup>[0-9.]+)x"
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


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


def ci95(vals: List[float]) -> tuple[float, float]:
    if not vals:
        return 0.0, 0.0
    if len(vals) == 1:
        return vals[0], vals[0]
    tcrit = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262}.get(len(vals), 1.960)
    half = tcrit * pstdev(vals) / math.sqrt(len(vals))
    return mean(vals) - half, mean(vals) + half


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def parse_variant(variant: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for outer_idx, path in enumerate(sorted((RAW / variant).glob("run_*.log"))):
        text = read_text(path)
        correct = CORRECT_RE.search(text)
        correctness = correct.group("status") if correct else "MISSING"
        for sample in SAMPLE_RE.finditer(text):
            rows.append({
                "variant": variant,
                "outer_run": outer_idx,
                "inner_rep": sample.group("rep"),
                "correctness": correctness,
                "mode": sample.group("mode"),
                "r": sample.group("r"),
                "h": correct.group("h") if correct else "",
                "r_prec": correct.group("r_prec") if correct else "",
                "pvw_us": sample.group("pvw_us"),
                "pvw_lane_us": sample.group("pvw_lane_us"),
                "scalar_repeated_us": sample.group("scalar_us"),
                "scalar_lane_us": sample.group("scalar_lane_us"),
                "speedup_vs_repeated_scalar": sample.group("speedup"),
                "source_log": rel(path),
            })
    return rows


def summarize(variant: str, samples: List[Dict[str, object]]) -> Dict[str, object]:
    vals = [fnum(row.get("pvw_lane_us")) for row in samples if row.get("variant") == variant]
    scalars = [fnum(row.get("scalar_lane_us")) for row in samples if row.get("variant") == variant]
    statuses = {str(row.get("correctness", "")) for row in samples if row.get("variant") == variant}
    low, high = ci95(vals)
    return {
        "variant": variant,
        "samples": len(vals),
        "correctness": "Pass" if vals and statuses == {"Pass"} else ",".join(sorted(statuses)) or "MISSING",
        "t_bootstrap_over_r_mean_us": f"{mean(vals):.3f}" if vals else "",
        "t_bootstrap_over_r_stddev_us": f"{pstdev(vals):.3f}" if len(vals) > 1 else "0.000",
        "t_bootstrap_over_r_ci95_low_us": f"{low:.3f}" if vals else "",
        "t_bootstrap_over_r_ci95_high_us": f"{high:.3f}" if vals else "",
        "t_bootstrap_over_r_min_us": f"{min(vals):.3f}" if vals else "",
        "t_bootstrap_over_r_max_us": f"{max(vals):.3f}" if vals else "",
        "scalar_t_bootstrap_over_r_mean_us": f"{mean(scalars):.3f}" if scalars else "",
        "speedup_vs_repeated_scalar_mean": f"{mean(scalars) / mean(vals):.6f}" if vals and scalars else "",
    }


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage312-digit-narrow32-fullsab-ab-001"
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
        "stage": "Stage 312",
        "backend": "spqlios_avx512-local",
        "command": "STAGE312_RUNS=5 STAGE312_REPS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage312_digit_narrow32_fullsab_ab.sh",
        "config": "direct baseline vs narrow32 complete-SAB T_bootstrap/r A/B",
        "params": "BINARY SET_2_3_2048; r=4; include-zero",
        "seed": "n/a",
        "status": decision,
        "summary": "Stage312 tests whether Stage311 narrow32 microbench gain survives complete SAB.",
        "artifacts": f"{rel(DOC)}; {rel(PERF_SUMMARY)}; {rel(PROOF)}",
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
    samples = parse_variant("direct_baseline") + parse_variant("narrow32_digit")
    write_csv(PERF_SAMPLES, samples, [
        "variant", "outer_run", "inner_rep", "correctness", "mode", "r",
        "h", "r_prec", "pvw_us", "pvw_lane_us", "scalar_repeated_us",
        "scalar_lane_us", "speedup_vs_repeated_scalar", "source_log",
    ])

    baseline = summarize("direct_baseline", samples)
    candidate = summarize("narrow32_digit", samples)
    bmean = fnum(baseline.get("t_bootstrap_over_r_mean_us"))
    cmean = fnum(candidate.get("t_bootstrap_over_r_mean_us"))
    candidate_speedup = bmean / cmean if bmean and cmean else 0.0
    conservative = fnum(baseline.get("t_bootstrap_over_r_min_us")) / fnum(candidate.get("t_bootstrap_over_r_max_us")) if fnum(candidate.get("t_bootstrap_over_r_max_us")) else 0.0
    ci_separated = fnum(candidate.get("t_bootstrap_over_r_ci95_high_us")) < fnum(baseline.get("t_bootstrap_over_r_ci95_low_us"))
    comparison = {
        "variant": "comparison",
        "samples": min(int(baseline.get("samples", 0)), int(candidate.get("samples", 0))),
        "correctness": "Pass" if baseline.get("correctness") == "Pass" and candidate.get("correctness") == "Pass" else "FAIL",
        "narrow32_vs_direct_baseline_mean": f"{candidate_speedup:.6f}",
        "narrow32_ci_separated_from_baseline": str(ci_separated).lower(),
        "conservative_baseline_min_over_narrow32_max": f"{conservative:.6f}",
    }
    summary_rows = [baseline, candidate, comparison]
    write_csv(PERF_SUMMARY, summary_rows, [
        "variant", "samples", "correctness", "t_bootstrap_over_r_mean_us",
        "t_bootstrap_over_r_stddev_us", "t_bootstrap_over_r_ci95_low_us",
        "t_bootstrap_over_r_ci95_high_us", "t_bootstrap_over_r_min_us",
        "t_bootstrap_over_r_max_us", "scalar_t_bootstrap_over_r_mean_us",
        "speedup_vs_repeated_scalar_mean", "narrow32_vs_direct_baseline_mean",
        "narrow32_ci_separated_from_baseline",
        "conservative_baseline_min_over_narrow32_max",
    ])

    correctness_pass = comparison["correctness"] == "Pass"
    enough_samples = int(comparison["samples"]) >= 5
    effect_pass = candidate_speedup >= 1.01
    decision = DECISION_FAIL
    if correctness_pass and enough_samples and effect_pass:
        decision = DECISION_PASS
    elif correctness_pass:
        decision = DECISION_NEUTRAL

    proof = [
        {"gate": "G1_correctness", "status": "PASS" if correctness_pass else "FAIL", "metric": "full SAB correctness", "value": comparison["correctness"], "interpretation": "Both variants must pass target_full correctness."},
        {"gate": "G2_sample_count", "status": "PASS" if enough_samples else "FAIL", "metric": "samples", "value": str(comparison["samples"]), "interpretation": "Stage312 preflight requires at least five samples per variant."},
        {"gate": "G3_fullsab_effect", "status": "PASS" if effect_pass else "NO_PROMOTION", "metric": "narrow32/direct mean T/r", "value": f"{candidate_speedup:.6f}", "interpretation": "Microbench gain must survive complete SAB T_bootstrap/r."},
        {"gate": "G4_ci_context", "status": "RECORDED", "metric": "CI separated", "value": str(ci_separated).lower(), "interpretation": "CI separation is context for a preflight; high-stat is a later gate."},
        {"gate": "G5_claim_boundary", "status": "PASS_PREFLIGHT_ONLY", "metric": "scope", "value": "5-run complete-SAB A/B", "interpretation": "Positive Stage312 opens noise/high-stat gates; it is not final paper evidence."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls Stage313 route."},
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])

    next_stage = "stage313_digit_narrow32_noise_resource" if decision == DECISION_PASS else "stage313_no_promotion_backend_or_other_digit"
    next_task = "Run correctness/noise/resource for narrow32 and then high-stat if positive." if decision == DECISION_PASS else "Do not promote narrow32; keep current direct baseline."
    write_csv(NEXT, [{
        "priority": "P0",
        "stage": next_stage,
        "input": decision,
        "task": next_task,
        "gate": "noise/resource/high-stat before any final SAB acceleration claim",
    }], ["priority", "stage", "input", "task", "gate"])

    report = (
        "# Stage312 Digit Narrow32 Full-SAB A/B\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage312 tests whether the Stage311 narrow32 digit microbench gain survives complete SAB under the primary metric `T_bootstrap/r`.\n\n"
        "## Performance Summary\n\n" + table(summary_rows, [
            "variant", "samples", "correctness", "t_bootstrap_over_r_mean_us",
            "t_bootstrap_over_r_ci95_low_us", "t_bootstrap_over_r_ci95_high_us",
            "speedup_vs_repeated_scalar_mean", "narrow32_vs_direct_baseline_mean",
        ]) +
        "\n\n## Proof Gate\n\n" + table(proof, ["gate", "status", "metric", "value", "interpretation"]) + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage312 Digit Narrow32 Full-SAB Model

Stage311 only proved an isolated direct sub-DTF microbench effect. Stage312
checks the complete SAB endpoint `T_bootstrap/r`, comparing the current
direct-DFT baseline against the same path plus
`MAT_TRGSW_DIRECT_DFT_DIGIT_NARROW32=true`.

The algorithmic semantics remain unchanged: the candidate only changes how
signed gadget digits are converted to double when the digit range fits int32.
Promotion requires complete SAB correctness and a positive full-SAB preflight.
Noise/resource and high-stat campaigns remain separate gates.
""")
    write_text(VARIANT, f"""# Stage312 Narrow32 Full-SAB Candidate

Decision: `{decision}`.

This stage does not make narrow32 default. It tests the default-off flag under
complete SAB `T_bootstrap/r`. A positive decision only admits noise/resource
and high-stat follow-up gates.
""")
    write_text(PLAN, """# Stage312 Experiment Plan

1. Build direct baseline and narrow32 variants with the same backend and SAB flags.
2. Run five complete SAB target benchmark samples per variant.
3. Use `T_bootstrap/r` as the primary endpoint.
4. Require correctness and mean speedup >= 1.01 before opening noise/resource.
5. Do not claim final acceleration until noise/resource/high-stat pass.
""")
    write_text(COMMANDS, """# Stage312 Reproduction Commands

```bash
STAGE312_RUNS=5 STAGE312_REPS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 \\
  bash scripts/run_stage312_digit_narrow32_fullsab_ab.sh
python3 scripts/build_stage312_digit_narrow32_fullsab_ab.py
```
""")

    append_once(ROADMAP, "## Stage 312: Digit Narrow32 Full-SAB A/B", "\n## Stage 312: Digit Narrow32 Full-SAB A/B\n\nGoal: test whether Stage311 narrow32 digit conversion improves complete SAB `T_bootstrap/r` against the current direct-DFT baseline.\n\n" f"Status: `{decision}`.\n")
    append_once(GOAL, "<!-- stage312-digit-narrow32-fullsab-ab -->", "\n<!-- stage312-digit-narrow32-fullsab-ab -->\n### Stage312 digit narrow32 full-SAB A/B\n\n" f"`{decision}` tests narrow32 at the complete SAB `T_bootstrap/r` endpoint; noise/resource/high-stat remain separate gates.\n")
    append_once(HYPOTHESES, "H312_digit_narrow32_fullsab_ab:", "\nH312_digit_narrow32_fullsab_ab:\n" f"  status: {decision}\n  primary_metric: complete_sab_T_bootstrap_over_r\n  evidence:\n    - repro/stage312_digit_narrow32_fullsab_ab/perf_samples.csv\n    - repro/stage312_digit_narrow32_fullsab_ab/perf_summary.csv\n    - repro/stage312_digit_narrow32_fullsab_ab/proof_gate.csv\n  conclusion: >\n    Stage312 tests whether the Stage311 narrow32 digit microbench effect\n    survives complete SAB. A positive result is still a preflight until\n    noise/resource and high-stat gates pass.\n")
    append_once(MANIFEST, "- stage312_digit_narrow32_fullsab_ab:", "\n- stage312_digit_narrow32_fullsab_ab:\n  - `docs/stage312_digit_narrow32_fullsab_ab.md`\n  - `theory_checks/stage312_digit_narrow32_fullsab_model.md`\n  - `algorithm_variants/mat_rlwe_sab_stage312_digit_narrow32_fullsab.md`\n  - `experiments/stage312_digit_narrow32_fullsab_ab_plan.md`\n  - `scripts/run_stage312_digit_narrow32_fullsab_ab.sh`\n  - `scripts/build_stage312_digit_narrow32_fullsab_ab.py`\n  - `repro/stage312_digit_narrow32_fullsab_ab/`\n")
    append_once(CHECKLIST, "<!-- stage312-digit-narrow32-fullsab-ab-checklist -->", "\n<!-- stage312-digit-narrow32-fullsab-ab-checklist -->\n" f"- [x] Stage312 records `{decision}` for complete SAB narrow32 A/B.\n")
    append_run_log(decision)

    artifacts = [
        DOC, THEORY, VARIANT, PLAN, RUNNER, BUILDER, PERF_SAMPLES,
        PERF_SUMMARY, PROOF, NEXT, COMMANDS, REPORT, RAW / "variant_plan.csv",
    ]
    artifacts.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(artifacts)
    print(decision)


if __name__ == "__main__":
    main()
