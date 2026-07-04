#!/usr/bin/env python3
"""Build Stage313 narrow32 full-SAB profile attribution artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage313_narrow32_profile_attribution"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage313_narrow32_profile_attribution.md"
THEORY = ROOT / "theory_checks" / "stage313_narrow32_profile_attribution_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage313_narrow32_attribution.md"
PLAN = ROOT / "experiments" / "stage313_narrow32_profile_attribution_plan.md"
RUNNER = ROOT / "scripts" / "run_stage313_narrow32_profile_attribution.sh"
BUILDER = ROOT / "scripts" / "build_stage313_narrow32_profile_attribution.py"

SUMMARY = OUT / "profile_summary.csv"
LIFECYCLE = OUT / "lifecycle_comparison.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage313_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE313_NARROW32_PROFILE_ATTRIBUTION_RECORDED"
DECISION_FAIL = "FAIL_STAGE313_NARROW32_PROFILE_ATTRIBUTION"

CORRECT_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH correctness target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) h=(?P<h>\d+) r_prec=(?P<r_prec>\d+): (?P<status>\w+)"
)
BENCH_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH summary target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw_avg_us>[0-9.]+).*?"
    r"scalar_repeated_avg_us=(?P<scalar_repeated_avg_us>[0-9.]+).*?"
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x.*?"
    r"t_bootstrap_over_r_pvw_us=(?P<t_pvw>[0-9.]+) "
    r"t_bootstrap_over_r_scalar_us=(?P<t_scalar>[0-9.]+)"
)
BODY_RE = re.compile(r"SAB_PVW_BODY_PROFILE sample (?P<body>.+)")
SPLIT_RE = re.compile(r"MAT_TRGSW_SPLIT_PROFILE sample (?P<split>.+)")
DIRECT_RE = re.compile(r"MAT_TRGSW_DIRECT_DFT_PROFILE sample (?P<direct>.+)")
KV_RE = re.compile(r"([A-Za-z0-9_]+)=([^ ]+)")


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


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def parse_kv(regex: re.Pattern[str], text: str, group: str) -> Dict[str, str]:
    matches = list(regex.finditer(text))
    if not matches:
        return {}
    return dict(KV_RE.findall(matches[-1].group(group)))


def parse_body_rows(text: str) -> List[Dict[str, str]]:
    return [dict(KV_RE.findall(match.group("body"))) for match in BODY_RE.finditer(text)]


def parse_variant(variant: str) -> Dict[str, object]:
    log = RAW / variant / "run.log"
    text = read_text(log)
    correct = CORRECT_RE.search(text)
    bench = BENCH_RE.search(text)
    split = parse_kv(SPLIT_RE, text, "split")
    direct = parse_kv(DIRECT_RE, text, "direct")
    body_rows = parse_body_rows(text)
    body_mat_ep_us = sum(fnum(row.get("mat_ep_us")) for row in body_rows)
    body_full_us = sum(fnum(row.get("full_us")) for row in body_rows)
    calls = fnum(direct.get("calls"))
    rows_sum = fnum(direct.get("rows_sum"))
    digit_us = fnum(direct.get("digit_us"))
    ifft_us = fnum(direct.get("ifft_us"))
    direct_total = fnum(direct.get("total_us"))
    return {
        "variant": variant,
        "correctness": correct.group("status") if correct else "missing",
        "mode": correct.group("mode") if correct else "",
        "r": correct.group("r") if correct else "",
        "h": correct.group("h") if correct else "",
        "r_prec": correct.group("r_prec") if correct else "",
        "reps": bench.group("reps") if bench else "",
        "t_bootstrap_over_r_us": bench.group("t_pvw") if bench else "",
        "speedup_vs_scalar": bench.group("speedup") if bench else "",
        "body_profile_rows": len(body_rows),
        "body_full_us_sum": f"{body_full_us:.3f}",
        "body_mat_ep_us_sum": f"{body_mat_ep_us:.3f}",
        "split_dft_us": split.get("dft_us", ""),
        "split_dense_us": split.get("dense_us", ""),
        "split_total_us": split.get("total_us", ""),
        "split_sub_calls": split.get("sub_calls", ""),
        "direct_calls": direct.get("calls", ""),
        "direct_rows_sum": direct.get("rows_sum", ""),
        "digit_us": direct.get("digit_us", ""),
        "ifft_us": direct.get("ifft_us", ""),
        "direct_total_us": direct.get("total_us", ""),
        "digit_share_of_direct_total": f"{digit_us / direct_total:.6f}" if direct_total else "",
        "ifft_share_of_direct_total": f"{ifft_us / direct_total:.6f}" if direct_total else "",
        "digit_avg_us_per_call": f"{digit_us / calls:.6f}" if calls else "",
        "ifft_avg_us_per_call": f"{ifft_us / calls:.6f}" if calls else "",
        "digit_avg_us_per_row": f"{digit_us / rows_sum:.6f}" if rows_sum else "",
        "ifft_avg_us_per_row": f"{ifft_us / rows_sum:.6f}" if rows_sum else "",
        "source_log": rel(log),
    }


def ratio(a: object, b: object) -> str:
    av = fnum(a)
    bv = fnum(b)
    return f"{av / bv:.6f}" if bv else ""


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage313-narrow32-profile-attribution-001"
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
        "stage": "Stage 313",
        "backend": "spqlios_avx512-local-profile",
        "command": "FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage313_narrow32_profile_attribution.sh",
        "config": "direct baseline vs narrow32 full-SAB profile attribution",
        "params": "BINARY SET_2_3_2048; r=4; include-zero; profile-only",
        "seed": "n/a",
        "status": decision,
        "summary": "Stage313 explains why narrow32 microbench did not survive complete SAB.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(LIFECYCLE)}; {rel(PROOF)}",
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
    direct = parse_variant("direct_profile")
    narrow = parse_variant("narrow32_profile")
    rows = [direct, narrow]
    comparison = {
        "variant": "comparison",
        "correctness": "Pass" if direct.get("correctness") == "Pass" and narrow.get("correctness") == "Pass" else "Fail",
        "narrow32_over_direct_T_over_r": ratio(narrow.get("t_bootstrap_over_r_us"), direct.get("t_bootstrap_over_r_us")),
        "direct_over_narrow32_T_over_r_speedup": ratio(direct.get("t_bootstrap_over_r_us"), narrow.get("t_bootstrap_over_r_us")),
        "direct_over_narrow32_digit_speedup": ratio(direct.get("digit_us"), narrow.get("digit_us")),
        "direct_over_narrow32_ifft_speedup": ratio(direct.get("ifft_us"), narrow.get("ifft_us")),
        "direct_over_narrow32_mat_ep_speedup": ratio(direct.get("body_mat_ep_us_sum"), narrow.get("body_mat_ep_us_sum")),
        "direct_over_narrow32_full_profile_speedup": ratio(direct.get("body_full_us_sum"), narrow.get("body_full_us_sum")),
    }
    summary_rows = rows + [comparison]
    write_csv(SUMMARY, summary_rows, [
        "variant", "correctness", "mode", "r", "h", "r_prec", "reps",
        "t_bootstrap_over_r_us", "speedup_vs_scalar", "body_profile_rows",
        "body_full_us_sum", "body_mat_ep_us_sum", "split_dft_us",
        "split_dense_us", "split_total_us", "split_sub_calls",
        "direct_calls", "direct_rows_sum", "digit_us", "ifft_us",
        "direct_total_us", "digit_share_of_direct_total",
        "ifft_share_of_direct_total", "digit_avg_us_per_call",
        "ifft_avg_us_per_call", "digit_avg_us_per_row",
        "ifft_avg_us_per_row", "narrow32_over_direct_T_over_r",
        "direct_over_narrow32_T_over_r_speedup",
        "direct_over_narrow32_digit_speedup",
        "direct_over_narrow32_ifft_speedup",
        "direct_over_narrow32_mat_ep_speedup",
        "direct_over_narrow32_full_profile_speedup", "source_log",
    ])
    lifecycle = [
        {"component": "T_over_r", "direct": direct.get("t_bootstrap_over_r_us"), "narrow32": narrow.get("t_bootstrap_over_r_us"), "direct_over_narrow32": comparison["direct_over_narrow32_T_over_r_speedup"], "interpretation": "instrumented profile latency only"},
        {"component": "body_full", "direct": direct.get("body_full_us_sum"), "narrow32": narrow.get("body_full_us_sum"), "direct_over_narrow32": comparison["direct_over_narrow32_full_profile_speedup"], "interpretation": "sum of body profiles"},
        {"component": "mat_ep", "direct": direct.get("body_mat_ep_us_sum"), "narrow32": narrow.get("body_mat_ep_us_sum"), "direct_over_narrow32": comparison["direct_over_narrow32_mat_ep_speedup"], "interpretation": "MAT EP inclusive profile"},
        {"component": "digit_to_double", "direct": direct.get("digit_us"), "narrow32": narrow.get("digit_us"), "direct_over_narrow32": comparison["direct_over_narrow32_digit_speedup"], "interpretation": "direct DFT digit component"},
        {"component": "ifft", "direct": direct.get("ifft_us"), "narrow32": narrow.get("ifft_us"), "direct_over_narrow32": comparison["direct_over_narrow32_ifft_speedup"], "interpretation": "direct DFT reverse FFT component"},
    ]
    write_csv(LIFECYCLE, lifecycle, ["component", "direct", "narrow32", "direct_over_narrow32", "interpretation"])

    correctness = comparison["correctness"] == "Pass"
    rows_match = direct.get("direct_rows_sum") == narrow.get("direct_rows_sum") and fnum(direct.get("direct_rows_sum")) > 0
    digit_positive = fnum(comparison["direct_over_narrow32_digit_speedup"]) > 1.0
    full_neutral = fnum(comparison["direct_over_narrow32_T_over_r_speedup"]) < 1.01
    decision = DECISION if correctness and rows_match else DECISION_FAIL
    proof = [
        {"gate": "G1_correctness", "status": "PASS" if correctness else "FAIL", "metric": "profile target correctness", "value": comparison["correctness"], "interpretation": "Both profiled variants must preserve complete SAB correctness."},
        {"gate": "G2_profile_consistency", "status": "PASS" if rows_match else "FAIL", "metric": "direct rows", "value": f"{direct.get('direct_rows_sum')}/{narrow.get('direct_rows_sum')}", "interpretation": "Both variants must profile the same direct sub-DTF surface."},
        {"gate": "G3_digit_effect", "status": "RECORDED_POSITIVE" if digit_positive else "RECORDED_NEUTRAL_OR_NEGATIVE", "metric": "direct/narrow32 digit speedup", "value": comparison["direct_over_narrow32_digit_speedup"], "interpretation": "Whether the microbench digit effect is visible in full-SAB profile mode."},
        {"gate": "G4_fullsab_context", "status": "NO_PROMOTION_CONFIRMED" if full_neutral else "RECHECK_STAGE312", "metric": "direct/narrow32 T/r speedup", "value": comparison["direct_over_narrow32_T_over_r_speedup"], "interpretation": "Narrow32 remains unpromoted unless full-SAB T/r improves."},
        {"gate": "G5_claim_boundary", "status": "PASS_PROFILE_ONLY", "metric": "scope", "value": "instrumented one-run profile", "interpretation": "Do not use Stage313 latency as final speed evidence."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls Stage314 route."},
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])
    next_stage = "stage314_stop_local_digit_microvariants_backend_ifft_or_new_algorithm"
    write_csv(NEXT, [{
        "priority": "P0",
        "stage": next_stage,
        "input": decision,
        "task": "Stop promoting narrow32/local digit microvariants unless a candidate has a predicted full-SAB effect above profile noise; route effort to backend IFFT or higher-level SAB schedule changes.",
        "gate": "new candidate must have a full-SAB cost model and component budget before implementation",
    }], ["priority", "stage", "input", "task", "gate"])

    report = (
        "# Stage313 Narrow32 Profile Attribution\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage313 profiles direct baseline and narrow32 under the complete SAB target path to explain why the Stage311 microbench gain did not promote in Stage312.\n\n"
        "## Summary\n\n" + table(summary_rows, [
            "variant", "correctness", "t_bootstrap_over_r_us",
            "body_mat_ep_us_sum", "digit_us", "ifft_us",
            "direct_over_narrow32_T_over_r_speedup",
            "direct_over_narrow32_digit_speedup",
            "direct_over_narrow32_mat_ep_speedup",
        ]) +
        "\n\n## Lifecycle Comparison\n\n" + table(lifecycle, ["component", "direct", "narrow32", "direct_over_narrow32", "interpretation"]) +
        "\n\n## Proof Gate\n\n" + table(proof, ["gate", "status", "metric", "value", "interpretation"]) + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage313 Narrow32 Attribution Model

Stage311 showed a positive isolated digit-conversion microbench. Stage312 showed
no complete-SAB `T_bootstrap/r` promotion. Stage313 reconciles those results by
profiling the same complete SAB path with body, MAT split, and direct DFT
lifecycle counters.

The expected failure mechanism is component dilution: even a visible digit
materialization improvement can be smaller than full-pipeline variation or be
offset by unchanged IFFT/dense/schedule costs. Therefore future local digit
microvariants need a full-SAB component budget before implementation.
""")
    write_text(VARIANT, f"""# Stage313 Narrow32 Attribution

Decision: `{decision}`.

No new variant is introduced. This stage attributes the already-tested
`MAT_TRGSW_DIRECT_DFT_DIGIT_NARROW32` candidate and decides whether to stop
local digit microvariants.
""")
    write_text(PLAN, """# Stage313 Experiment Plan

1. Run direct baseline and narrow32 with full SAB target benchmark.
2. Enable body profile, MAT split profile, and direct DFT lifecycle profile.
3. Compare digit, IFFT, MAT EP, and full-profile times.
4. Confirm Stage312 no-promotion or reopen investigation if attribution contradicts it.
""")
    write_text(COMMANDS, """# Stage313 Reproduction Commands

```bash
FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 \\
  bash scripts/run_stage313_narrow32_profile_attribution.sh
python3 scripts/build_stage313_narrow32_profile_attribution.py
```
""")

    append_once(ROADMAP, "## Stage 313: Narrow32 Profile Attribution", "\n## Stage 313: Narrow32 Profile Attribution\n\nGoal: attribute why Stage311 narrow32 microbench did not promote in complete SAB Stage312.\n\n" f"Status: `{decision}`.\n")
    append_once(GOAL, "<!-- stage313-narrow32-profile-attribution -->", "\n<!-- stage313-narrow32-profile-attribution -->\n### Stage313 narrow32 profile attribution\n\n" f"`{decision}` records component-level attribution for the narrow32 no-promotion result and routes future work away from unsupported local digit microvariants.\n")
    append_once(HYPOTHESES, "H313_narrow32_profile_attribution:", "\nH313_narrow32_profile_attribution:\n" f"  status: {decision}\n  primary_metric: profile_attribution_for_stage312_no_promotion\n  evidence:\n    - repro/stage313_narrow32_profile_attribution/profile_summary.csv\n    - repro/stage313_narrow32_profile_attribution/lifecycle_comparison.csv\n    - repro/stage313_narrow32_profile_attribution/proof_gate.csv\n  conclusion: >\n    Stage313 attributes the gap between Stage311 microbench gain and Stage312\n    full-SAB neutral result. It is profile-only and does not promote narrow32.\n")
    append_once(MANIFEST, "- stage313_narrow32_profile_attribution:", "\n- stage313_narrow32_profile_attribution:\n  - `docs/stage313_narrow32_profile_attribution.md`\n  - `theory_checks/stage313_narrow32_profile_attribution_model.md`\n  - `algorithm_variants/mat_rlwe_sab_stage313_narrow32_attribution.md`\n  - `experiments/stage313_narrow32_profile_attribution_plan.md`\n  - `scripts/run_stage313_narrow32_profile_attribution.sh`\n  - `scripts/build_stage313_narrow32_profile_attribution.py`\n  - `repro/stage313_narrow32_profile_attribution/`\n")
    append_once(CHECKLIST, "<!-- stage313-narrow32-profile-attribution-checklist -->", "\n<!-- stage313-narrow32-profile-attribution-checklist -->\n" f"- [x] Stage313 records `{decision}` for narrow32 no-promotion attribution.\n")
    append_run_log(decision)

    artifacts = [
        DOC, THEORY, VARIANT, PLAN, RUNNER, BUILDER, SUMMARY, LIFECYCLE,
        PROOF, NEXT, COMMANDS, REPORT, RAW / "variant_plan.csv",
    ]
    artifacts.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(artifacts)
    print(decision)


if __name__ == "__main__":
    main()
