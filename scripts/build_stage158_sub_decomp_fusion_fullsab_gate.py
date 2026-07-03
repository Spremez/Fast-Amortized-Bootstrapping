#!/usr/bin/env python3
"""Stage158: guarded sub-decompose fusion full-SAB gate."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage158_sub_decomp_fusion_fullsab_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
VARIANT_CSV = OUT_DIR / "variant_results.csv"
COMPARISON_CSV = OUT_DIR / "comparison.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

DOC_STAGE = ROOT / "docs" / "stage158_sub_decomp_fusion_fullsab_gate.md"
DOC_PLAN = ROOT / "experiments" / "stage158_sub_decomp_fusion_fullsab_gate_plan.md"
DOC_THEORY = ROOT / "theory_checks" / "stage158_sub_decomp_fusion_fullsab_model.md"
DOC_VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_sub_decomp_fusion_fullsab.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_DOC = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
    "SAB_PVW_BENCH=true SAB_PVW_BENCH_R=6 SAB_PVW_BENCH_REPS=1"
)

VARIANTS = [
    {
        "name": "control_h14_r6_backend",
        "flags": BASE_FLAGS,
    },
    {
        "name": "sub_decomp_fusion_h14_r6_backend",
        "flags": BASE_FLAGS + " SAB_PVW_SUB_DECOMP_FUSION=true",
    },
]

CORRECT_RE = re.compile(r"SAB_PVW_BENCH correctness target_full r=(?P<r>\d+) h=(?P<h>\d+) r_prec=(?P<r_prec>\d+): (?P<status>\w+)")
SUMMARY_RE = re.compile(
    r"SAB_PVW_BENCH summary target_full r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw_avg_us>[0-9.]+) .*?"
    r"pvw_lane_avg_us=(?P<pvw_lane_avg_us>[0-9.]+) "
    r"scalar_repeated_avg_us=(?P<scalar_repeated_avg_us>[0-9.]+) .*?"
    r"scalar_lane_avg_us=(?P<scalar_lane_avg_us>[0-9.]+) "
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x"
)


def write_csv(path: Path, rows: List[Dict[str, object]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize(text: str) -> str:
    return "".join(ch if ch in "\n\r\t" or 32 <= ord(ch) < 127 else "?" for ch in text)


def wsl_repo() -> str:
    drive = ROOT.drive.rstrip(":").lower()
    rest = ROOT.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


def run_wsl(command: str, log: Path, timeout: int = 1800) -> int:
    bash_cmd = f"cd {wsl_repo()} && {command}"
    proc = subprocess.run(["wsl", "bash", "-lc", bash_cmd], cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=timeout)
    output = proc.stdout.decode("utf-8", errors="ignore")
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("command: " + command + "\n" + sanitize(output), encoding="ascii", errors="ignore")
    return proc.returncode


def parse_run(log: Path) -> Dict[str, str]:
    text = log.read_text(encoding="ascii", errors="ignore")
    correct = CORRECT_RE.search(text)
    summary = SUMMARY_RE.search(text)
    row: Dict[str, str] = {
        "correctness": correct.group("status") if correct else "MISSING",
    }
    if summary:
        row.update(summary.groupdict())
    return row


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, object]] = []
    artifacts: List[Path] = []

    for variant in VARIANTS:
        vdir = OUT_DIR / variant["name"]
        clean_log = vdir / "clean.log"
        build_log = vdir / "build.log"
        run_log = vdir / "run.log"
        clean_rc = run_wsl("make clean", clean_log, timeout=300)
        build_rc = run_wsl(f"make {variant['flags']} -j$(nproc)", build_log, timeout=900) if clean_rc == 0 else 1
        run_rc = run_wsl("./main", run_log, timeout=1200) if build_rc == 0 else 1
        parsed = parse_run(run_log) if run_log.exists() else {"correctness": "MISSING"}
        row: Dict[str, object] = {
            "variant": variant["name"],
            "status": "PASS" if clean_rc == 0 and build_rc == 0 and run_rc == 0 and parsed.get("correctness") == "Pass" else "FAIL",
            "clean_rc": clean_rc,
            "build_rc": build_rc,
            "run_rc": run_rc,
            "flags": variant["flags"],
        }
        row.update(parsed)
        rows.append(row)
        artifacts.extend([clean_log, build_log, run_log])

    write_csv(VARIANT_CSV, rows, [
        "variant", "status", "clean_rc", "build_rc", "run_rc", "flags",
        "correctness", "r", "reps", "pvw_avg_us", "pvw_lane_avg_us",
        "scalar_repeated_avg_us", "scalar_lane_avg_us", "speedup",
    ])

    control = next((r for r in rows if r["variant"] == "control_h14_r6_backend"), {})
    fusion = next((r for r in rows if r["variant"] == "sub_decomp_fusion_h14_r6_backend"), {})
    comparison_rows: List[Dict[str, object]] = []
    if control.get("status") == "PASS" and fusion.get("status") == "PASS":
        c_lane = float(control.get("pvw_lane_avg_us", 0) or 0)
        f_lane = float(fusion.get("pvw_lane_avg_us", 0) or 0)
        c_total = float(control.get("pvw_avg_us", 0) or 0)
        f_total = float(fusion.get("pvw_avg_us", 0) or 0)
        speedup = c_lane / f_lane if f_lane else 0.0
        comparison_rows = [
            {
                "metric": "T_bootstrap_per_lane_us",
                "control": f"{c_lane:.3f}",
                "fusion": f"{f_lane:.3f}",
                "fusion_over_control": f"{speedup:.6f}",
                "status": "PASS" if speedup >= 1.02 else ("NEUTRAL" if speedup >= 0.99 else "REJECT"),
            },
            {
                "metric": "full_sab_pvw_us",
                "control": f"{c_total:.3f}",
                "fusion": f"{f_total:.3f}",
                "fusion_over_control": f"{(c_total / f_total if f_total else 0.0):.6f}",
                "status": "INFO",
            },
        ]
        if speedup >= 1.02:
            decision = "SMOKE_STAGE158_SUB_DECOMP_FUSION_FULLSAB_POSITIVE_REPEATED_REQUIRED"
        elif speedup >= 0.99:
            decision = "NEUTRAL_STAGE158_SUB_DECOMP_FUSION_FULLSAB_LOW_SIGNAL"
        else:
            decision = "REJECT_STAGE158_SUB_DECOMP_FUSION_FULLSAB_SLOWER"
    else:
        decision = "FAIL_STAGE158_SUB_DECOMP_FUSION_BUILD_OR_CORRECTNESS"
        comparison_rows = [
            {
                "metric": "full_sab_gate",
                "control": control.get("status", "MISSING"),
                "fusion": fusion.get("status", "MISSING"),
                "fusion_over_control": "",
                "status": "FAIL",
            }
        ]

    write_csv(COMPARISON_CSV, comparison_rows, ["metric", "control", "fusion", "fusion_over_control", "status"])

    summary_rows = [
        {
            "gate": "stage158_build_correctness",
            "status": "PASS" if all(r.get("status") == "PASS" for r in rows) else "FAIL",
            "metric": "control;fusion",
            "value": ";".join(str(r.get("correctness", "")) for r in rows),
            "evidence": rel(VARIANT_CSV),
            "detail": "Both variants must build and pass full-SAB correctness.",
            "next_action": "Do not interpret timing if this fails.",
        },
        {
            "gate": "stage158_fullsab_smoke",
            "status": comparison_rows[0]["status"],
            "metric": comparison_rows[0]["metric"],
            "value": comparison_rows[0]["fusion_over_control"],
            "evidence": rel(COMPARISON_CSV),
            "detail": "Same backend, same r=6, same H14 current-head path.",
            "next_action": "Repeat and add noise/resource only if positive.",
        },
        {
            "gate": "stage158_decision",
            "status": decision,
            "metric": "candidate_route",
            "value": "sub_decomp_fusion_fullsab",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Decide whether the Stage157 positive microbench survives full SAB.",
            "next_action": "Promote only after repeated full-SAB/noise/resource gates.",
        },
    ]
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(rows, comparison_rows, summary_rows, decision)
    update_global_docs(decision)

    artifacts.extend([SUMMARY_CSV, VARIANT_CSV, COMPARISON_CSV, DOC_STAGE, DOC_PLAN, DOC_THEORY, DOC_VARIANT])
    artifact_rows = [
        {"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in artifacts if path.exists()
    ]
    write_csv(ARTIFACT_CSV, artifact_rows, ["path", "sha256", "bytes"])

    print(f"Stage158 sub-decomp fusion full-SAB gate: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")


def write_docs(
    rows: List[Dict[str, object]],
    comparison_rows: List[Dict[str, object]],
    summary_rows: List[Dict[str, object]],
    decision: str,
) -> None:
    DOC_STAGE.write_text(f"""# Stage158 Sub-Decompose Fusion Full-SAB Gate

Decision: `{decision}`

Stage158 integrates the Stage157 candidate behind
`SAB_PVW_SUB_DECOMP_FUSION=true` and compares complete SAB r=6 throughput
against the same H14 backend control under WSL `spqlios_avx512`.

## Variants

{md_table(rows, ["variant", "status", "correctness", "r", "reps", "pvw_lane_avg_us", "speedup"])}

## Comparison

{md_table(comparison_rows, ["metric", "control", "fusion", "fusion_over_control", "status"])}

## Gates

{md_table(summary_rows, ["gate", "status", "metric", "value", "next_action"])}

Interpretation: this is a one-run full-SAB smoke. A positive result only opens
repeated performance plus noise/resource gates; a neutral or negative result
keeps the implementation as an explicit ablation.
""", encoding="utf-8", newline="\n")

    DOC_PLAN.write_text("""# Stage158 Experiment Plan

Goal: test whether Stage157 sub-decompose fusion improves complete SAB
`T_bootstrap/r`.

Platform: WSL/Linux with `FFT_LIB=spqlios_avx512`.

Control: H14 r=6 backend current-head path.

Candidate: same flags plus `SAB_PVW_SUB_DECOMP_FUSION=true`.

Correctness gate: both variants must print `SAB_PVW_BENCH correctness ... Pass`.

Performance gate: candidate/control on `T_bootstrap/r`; positive smoke requires
later repeated/noise/resource gates before any promotion.
""", encoding="utf-8", newline="\n")

    DOC_THEORY.write_text("""# Stage158 Full-SAB Model

Stage157 measured only the local sub+decompose loop. Stage158 evaluates the
same mechanism inside complete SAB:

```text
control: pvmtmlwe_sub(tmp, in2, in1); mat_trgsw_mul_pvmtmlwe_DFT(tmp)
fusion:  mat_trgsw_mul_pvmtmlwe_sub_DFT(in1, in2)
```

The sparse schedule count is unchanged. The only intended savings are reduced
temporary sub memory traffic and direct dense decomposition of the difference.
Therefore any observed full-SAB speedup must be smaller than the isolated
microbench speedup and must be confirmed by repeated runs.
""", encoding="utf-8", newline="\n")

    DOC_VARIANT.write_text("""# MAT-RLWE SAB Sub-Decomp Fusion Full-SAB Variant

Flag:

```text
SAB_PVW_SUB_DECOMP_FUSION=true
```

Default status:

```text
off
```

The scalar SAB path and default PVW path remain unchanged. This variant only
changes the explicit `sab_pvw_*` CMUX hot path.
""", encoding="utf-8", newline="\n")


def update_global_docs(decision: str) -> None:
    append_once(
        ROADMAP,
        "## Stage 158: Sub-Decompose Fusion Full-SAB Gate",
        f"""## Stage 158: Sub-Decompose Fusion Full-SAB Gate

Goal:

```text
Integrate Stage157 sub-decompose fusion behind an explicit flag and test
complete SAB T_bootstrap/r against the same H14 r=6 backend control.
```

Status:

```text
Completed. Stage158 records {decision}. Defaults remain unchanged.
```
""",
    )
    append_once(
        GOAL_DOC,
        "Stage158 tests sub-decompose fusion in full SAB",
        f"""Stage158 tests sub-decompose fusion in complete SAB after Stage157. Decision:
`{decision}`. It keeps `SAB_PVW_SUB_DECOMP_FUSION` explicit/default false and
does not upgrade claims unless repeated/noise/resource gates pass.
""",
    )
    append_once(
        CURRENT_GOAL,
        "62. Treat Stage158 as the sub-decompose fusion full-SAB gate",
        f"""62. Treat Stage158 as the sub-decompose fusion full-SAB gate:
    `{decision}`. It is the first complete-SAB check for the Stage157
    implementation candidate; promotion still requires repeated gates.
""",
    )
    append_once(
        HYPOTHESES,
        "H82_sub_decomp_fusion_fullsab",
        f"""  - id: H82_sub_decomp_fusion_fullsab
    statement: >
      The Stage157 sub-decompose fusion candidate should improve complete
      r=6 PVW/MAT-SAB T_bootstrap/r under the same H14 backend path.
    mechanism: >
      It removes the intermediate PVW_TMLWE sub write/read and directly
      decomposes in2-in1 before the unchanged MAT addmul/materialization.
    status: stage158_sub_decomp_fusion_fullsab_gate
    evidence: docs/stage158_sub_decomp_fusion_fullsab_gate.md; experiments/stage158_sub_decomp_fusion_fullsab_gate_plan.md; theory_checks/stage158_sub_decomp_fusion_fullsab_model.md; algorithm_variants/mat_rlwe_sab_sub_decomp_fusion_fullsab.md; repro/stage158_sub_decomp_fusion_fullsab_gate/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - full SAB correctness fails
      - candidate does not improve T_bootstrap_per_lane over same-backend control
""",
    )
    append_once(
        RUN_LOG,
        "stage158-sub-decomp-fusion-fullsab-gate-001",
        f"2026-07-03,stage158-sub-decomp-fusion-fullsab-gate-001,full-sab-bench,spqlios_avx512,SET_2_3_2048,BINARY,{decision},docs/stage158_sub_decomp_fusion_fullsab_gate.md;repro/stage158_sub_decomp_fusion_fullsab_gate/summary.csv\n",
    )
    append_once(
        MANIFEST,
        "stage158_sub_decomp_fusion_fullsab_gate",
        "- `repro/stage158_sub_decomp_fusion_fullsab_gate/`: Stage158 sub-decompose fusion full-SAB gate outputs.\n",
    )
    append_once(
        CHECKLIST,
        "Stage158 sub-decompose fusion full-SAB gate",
        "- [x] Stage158 sub-decompose fusion full-SAB WSL gate generated and recorded.\n",
    )


def md_table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(out)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


if __name__ == "__main__":
    build()
