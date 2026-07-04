#!/usr/bin/env python3
"""Build Stage273 sub_a from_DFT_add alias microtest artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage273_sub_a_from_DFT_add_alias_microtest"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage273_sub_a_from_DFT_add_alias_microtest.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

FROM_DFT_RE = re.compile(
    r"SAB_PVW_SUBA_ALIAS_TEST from_DFT_add variant=(?P<variant>\S+) "
    r"case=(?P<case>\S+) k=(?P<k>\d+) r=(?P<r>\d+) N=(?P<N>\d+) "
    r"mismatches=(?P<mismatches>\d+) gate=(?P<gate>Pass|Fail)"
)
SUB_A_RE = re.compile(
    r"SAB_PVW_SUBA_ALIAS_TEST sub_a_equivalence variant=(?P<variant>\S+) "
    r"mode=(?P<mode>\S+) r=(?P<r>\d+) in_N=(?P<in_N>\d+) "
    r"mismatches=(?P<mismatches>\d+) gate=(?P<gate>Pass|Fail)"
)
STEP_RE = re.compile(
    r"SAB_PVW_SUBA_ALIAS_TEST sub_a_step variant=(?P<variant>\S+) "
    r"mode=(?P<mode>\S+) step=(?P<step>\S+)"
)
OVERALL_RE = re.compile(
    r"SAB_PVW_SUBA_ALIAS_TEST overall variant=(?P<variant>\S+) gate=(?P<gate>Pass|Fail)"
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="\n", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text.lstrip())
        if not text.endswith("\n"):
            handle.write("\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def table(rows: list[dict[str, str]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |"]
    out.append("| " + " | ".join("---" for _ in fields) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def read_exit_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def parse_logs() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    alias_rows: list[dict[str, str]] = []
    sub_a_rows: list[dict[str, str]] = []
    step_rows: list[dict[str, str]] = []
    overall_rows: list[dict[str, str]] = []
    exit_rows: list[dict[str, str]] = []

    for exit_path in sorted(RAW.glob("*_exit_code.csv")):
        exit_rows.extend(read_exit_rows(exit_path))

    for path in sorted(RAW.glob("*_run.log")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            match = FROM_DFT_RE.search(line)
            if match:
                row = match.groupdict()
                row["source_log"] = rel(path)
                alias_rows.append(row)
                continue
            match = SUB_A_RE.search(line)
            if match:
                row = match.groupdict()
                row["source_log"] = rel(path)
                sub_a_rows.append(row)
                continue
            match = STEP_RE.search(line)
            if match:
                row = match.groupdict()
                row["source_log"] = rel(path)
                step_rows.append(row)
                continue
            match = OVERALL_RE.search(line)
            if match:
                row = match.groupdict()
                row["source_log"] = rel(path)
                overall_rows.append(row)

    alias_rows.sort(key=lambda row: (row["variant"], row["case"]))
    sub_a_rows.sort(key=lambda row: (row["variant"], row["mode"]))
    step_rows.sort(key=lambda row: (row["variant"], row["mode"], row["step"]))
    overall_rows.sort(key=lambda row: row["variant"])
    exit_rows.sort(key=lambda row: (row["variant"], row["phase"]))
    return alias_rows, sub_a_rows, step_rows, overall_rows, exit_rows


def gate_status(alias_rows: list[dict[str, str]], sub_a_rows: list[dict[str, str]],
                overall_rows: list[dict[str, str]], exit_rows: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
    by_alias = {(row["variant"], row["case"]): row for row in alias_rows}
    by_sub_a = {(row["variant"], row["mode"]): row for row in sub_a_rows}
    by_overall = {row["variant"]: row for row in overall_rows}
    by_exit = {(row["variant"], row["phase"]): row for row in exit_rows}

    default_distinct = by_alias.get(("default", "out_distinct"), {})
    default_alias = by_alias.get(("default", "out_equals_addend"), {})
    backend_distinct = by_alias.get(("backend_from_dft_add", "out_distinct"), {})
    backend_alias = by_alias.get(("backend_from_dft_add", "out_equals_addend"), {})
    backend_include = by_sub_a.get(("backend_from_dft_add", "include_zero"), {})
    backend_ternary = by_sub_a.get(("backend_from_dft_add", "ternary"), {})
    backend_run = by_exit.get(("backend_from_dft_add", "run"), {})
    default_run = by_exit.get(("default", "run"), {})

    checks = [
        {
            "gate": "G1_default_distinct",
            "status": "PASS" if default_distinct.get("gate") == "Pass" and default_distinct.get("mismatches") == "0" else "FAIL",
            "metric": "default out!=addend",
            "value": default_distinct.get("mismatches", "missing"),
            "interpretation": "Portable fallback remains correct when output and addend are distinct.",
        },
        {
            "gate": "G2_default_alias_negative_control",
            "status": "PASS_NEGATIVE_CONTROL" if default_alias.get("gate") == "Fail" and int(default_alias.get("mismatches", "0") or "0") > 0 else "FAIL",
            "metric": "default out==addend",
            "value": default_alias.get("mismatches", "missing"),
            "interpretation": "Portable fallback is not alias-safe, so in-place sub_a fusion must not use it.",
        },
        {
            "gate": "G3_backend_alias_helper",
            "status": "PASS" if backend_distinct.get("gate") == "Pass" and backend_alias.get("gate") == "Pass" and backend_alias.get("mismatches") == "0" else "FAIL",
            "metric": "backend out==addend",
            "value": backend_alias.get("mismatches", "missing"),
            "interpretation": "Backend direct add helper is alias-safe in this deterministic PVW_TMLWE microtest.",
        },
        {
            "gate": "G4_backend_include_zero_sub_a",
            "status": "PASS" if backend_include.get("gate") == "Pass" and backend_include.get("mismatches") == "0" else "FAIL",
            "metric": "include-zero sub_a exact equivalence",
            "value": backend_include.get("mismatches", "missing"),
            "interpretation": "Alias materialization preserves include-zero sub_a state for r=4 fixture.",
        },
        {
            "gate": "G5_backend_ternary_sub_a",
            "status": "PASS" if backend_ternary.get("gate") == "Pass" and backend_ternary.get("mismatches") == "0" else "FAIL",
            "metric": "ternary sub_a exact equivalence",
            "value": backend_ternary.get("mismatches", "missing"),
            "interpretation": "Alias materialization preserves ternary sub_a state for r=4 fixture.",
        },
        {
            "gate": "G6_exit_codes",
            "status": "PASS" if default_run.get("exit_code") == "0" and backend_run.get("exit_code") == "0" else "FAIL",
            "metric": "run exit",
            "value": f"default={default_run.get('exit_code', 'missing')}; backend={backend_run.get('exit_code', 'missing')}",
            "interpretation": "Both microtest binaries completed.",
        },
        {
            "gate": "G7_claim_boundary",
            "status": "PASS_MICROTEST_ONLY",
            "metric": "claim scope",
            "value": "no full SAB speed claim",
            "interpretation": "Stage273 only gates a candidate implementation path.",
        },
    ]

    if all(row["status"].startswith("PASS") for row in checks):
        decision = "PASS_STAGE273_SUB_A_ALIAS_MICROTEST_ENABLES_FLAGGED_SMOKE"
    elif checks[2]["status"] == "FAIL":
        decision = "FAIL_STAGE273_SUB_A_ALIAS_MICROTEST_ALIAS"
    elif checks[3]["status"] == "FAIL" or checks[4]["status"] == "FAIL":
        decision = "FAIL_STAGE273_SUB_A_ALIAS_MICROTEST_SUBA_EQUIV"
    else:
        decision = "FAIL_STAGE273_SUB_A_ALIAS_MICROTEST_INFRA"

    checks.append(
        {
            "gate": "G8_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Proceed only to an explicit-flag Stage274 smoke when this decision is PASS.",
        }
    )
    return decision, checks


def claim_rows() -> list[dict[str, str]]:
    return [
        {
            "claim": "backend_from_dft_add_alias_safety",
            "status": "microtest_supported",
            "allowed_wording": "The backend direct-add helper passed deterministic out==addend PVW_TMLWE alias testing.",
            "forbidden_wording": "All from_DFT_add implementations are alias-safe.",
            "evidence": "alias_summary.csv",
        },
        {
            "claim": "sub_a_alias_equivalence",
            "status": "microtest_supported",
            "allowed_wording": "A local alias-materialized sub_a candidate exactly matched reference include-zero and ternary sub_a on the Stage273 r=4 fixture.",
            "forbidden_wording": "The full SAB path is faster or fully correct after this stage.",
            "evidence": "sub_a_equivalence.csv",
        },
        {
            "claim": "default_fallback_alias",
            "status": "negative_control",
            "allowed_wording": "The portable fallback failed out==addend alias testing and must not be used in-place.",
            "forbidden_wording": "The default fallback can be used for sub_a in-place fusion.",
            "evidence": "alias_summary.csv",
        },
        {
            "claim": "full_bootstrap_speedup",
            "status": "not_tested",
            "allowed_wording": "Stage274 must test full SAB T_bootstrap/r under an explicit flag.",
            "forbidden_wording": "Stage273 proves a SAB acceleration.",
            "evidence": "proof_gate.csv",
        },
    ]


def next_rows(decision: str) -> list[dict[str, str]]:
    if decision.startswith("PASS_"):
        return [
            {
                "priority": "P0",
                "route": "stage274_sub_a_fused_materialization_smoke",
                "entry_condition": "Stage273 backend alias and sub_a equivalence gates passed.",
                "gate": "Add an explicit `SAB_PVW_SUBA_FUSED_FROM_DFT_ADD` flag; run correctness plus r=4 include-zero/ternary full SAB T_bootstrap/r smoke.",
                "status": "selected",
                "failure_action": "If full SAB is neutral or negative, close S272-A as microtest-only and do not default-enable.",
            },
            {
                "priority": "P1",
                "route": "stage275_sub_a_fused_repeated_noise_resource",
                "entry_condition": "Only if Stage274 smoke is positive.",
                "gate": "Repeated timing, noise/resource, and claim-boundary check.",
                "status": "conditional",
                "failure_action": "Demote to neutral if repeated or noise/resource gates fail.",
            },
        ]
    return [
        {
            "priority": "P0",
            "route": "close_s272a_or_redesign_non_alias_temp_path",
            "entry_condition": "Stage273 failed.",
            "gate": "Record failure and choose a non-alias or lower-risk candidate.",
            "status": "selected",
            "failure_action": "Do not implement in-place sub_a fused materialization.",
        }
    ]


def artifacts(paths: list[Path]) -> list[dict[str, str]]:
    return [{"path": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256(path)} for path in paths if path.exists() and path.is_file()]


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(CURRENT_GOAL, "### Stage273 sub_a from_DFT_add alias microtest", f"""
### Stage273 sub_a from_DFT_add alias microtest

`{decision}` records an isolated alias/equivalence gate for the non-binary
`sub_a` fused materialization candidate. It validates only the backend
direct-add route under deterministic r=4 fixtures and keeps the default fallback
as a negative control.
""")
    append_once(HYPOTHESES, "H10_stage273_sub_a_from_DFT_add_alias_microtest:", f"""
H10_stage273_sub_a_from_DFT_add_alias_microtest:
  status: {decision}
  evidence:
    - repro/stage273_sub_a_from_DFT_add_alias_microtest/alias_summary.csv
    - repro/stage273_sub_a_from_DFT_add_alias_microtest/sub_a_equivalence.csv
    - repro/stage273_sub_a_from_DFT_add_alias_microtest/proof_gate.csv
    - docs/stage273_sub_a_from_DFT_add_alias_microtest.md
  conclusion: >
    Stage273 records {decision}. It permits only a flagged Stage274 smoke for
    backend-based sub_a fused materialization; it does not prove full SAB
    speedup and does not make the portable fallback alias-safe.
""")
    append_once(RUN_LOG, "stage273-sub-a-from-dft-add-alias-microtest-001", f"""stage273-sub-a-from-dft-add-alias-microtest-001,2026-07-04,{head},Stage 273,spqlios_avx512-microtest,bash scripts/run_stage273_sub_a_from_DFT_add_alias_microtest.sh; python scripts/build_stage273_sub_a_from_DFT_add_alias_microtest.py,"default negative control plus backend alias/sub_a exact equivalence",n/a,{decision},"Microtest only; selected Stage274 explicit-flag full SAB T_bootstrap/r smoke if PASS.",docs/stage273_sub_a_from_DFT_add_alias_microtest.md; repro/stage273_sub_a_from_DFT_add_alias_microtest/proof_gate.csv
""")
    append_once(MANIFEST, "- stage273_sub_a_from_DFT_add_alias_microtest:", """
- stage273_sub_a_from_DFT_add_alias_microtest:
  - `docs/stage273_sub_a_from_DFT_add_alias_microtest.md`
  - `scripts/run_stage273_sub_a_from_DFT_add_alias_microtest.sh`
  - `scripts/build_stage273_sub_a_from_DFT_add_alias_microtest.py`
  - `repro/stage273_sub_a_from_DFT_add_alias_microtest/`
""")
    append_once(CHECKLIST, "stage273-sub-a-from-dft-add-alias-microtest-checklist", f"""
<!-- stage273-sub-a-from-dft-add-alias-microtest-checklist -->
- [x] Stage273 records `{decision}` with raw logs, parsed gates, and claim boundaries.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    alias_rows, sub_a_rows, step_rows, overall_rows, exit_rows = parse_logs()
    decision, proof = gate_status(alias_rows, sub_a_rows, overall_rows, exit_rows)
    claims = claim_rows()
    queue = next_rows(decision)

    write_csv(REPRO / "alias_summary.csv", alias_rows, ["variant", "case", "k", "r", "N", "mismatches", "gate", "source_log"])
    write_csv(REPRO / "sub_a_equivalence.csv", sub_a_rows, ["variant", "mode", "r", "in_N", "mismatches", "gate", "source_log"])
    write_csv(REPRO / "sub_a_steps.csv", step_rows, ["variant", "mode", "step", "source_log"])
    write_csv(REPRO / "overall.csv", overall_rows, ["variant", "gate", "source_log"])
    write_csv(REPRO / "run_exit.csv", exit_rows, ["variant", "phase", "exit_code"])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    report = f"""# Stage273 Sub_a From_DFT_Add Alias Microtest

Decision: `{decision}`.

Stage273 is an isolated microtest for the Stage272 non-binary `sub_a`
materialization candidate. It does not change the default SAB/PVW hot path and
does not claim full bootstrapping speedup.

## Alias Helper Results

{table(alias_rows, ["variant", "case", "k", "r", "N", "mismatches", "gate"])}

## Sub_a Equivalence

{table(sub_a_rows, ["variant", "mode", "r", "in_N", "mismatches", "gate"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

## Fixture Note

The `sub_a` equivalence fixture uses a Stage273-only sparse secret fixture that
fills the input key coefficients without computing input-key DFT tables. This
keeps the microtest focused on `sub_a` selector materialization and avoids
mixing unsupported tiny input-ring DFT behavior into the alias-safety gate. The
PVW/MAT ciphertext ring used by the tested helper is `N=1024`, `r=4`.

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage273_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage273 Reproduction Commands

```bash
bash scripts/run_stage273_sub_a_from_DFT_add_alias_microtest.sh
python3 scripts/build_stage273_sub_a_from_DFT_add_alias_microtest.py
```

This stage is a microtest. It is not a full SAB benchmark and must not be used
as a `T_bootstrap/r` speed claim.
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage273_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "alias_summary.csv",
        REPRO / "sub_a_equivalence.csv",
        REPRO / "sub_a_steps.csv",
        REPRO / "overall.csv",
        REPRO / "run_exit.csv",
        REPRO / "proof_gate.csv",
        REPRO / "claim_boundary.csv",
        REPRO / "next_stage_queue.csv",
        Path(__file__),
        ROOT / "scripts" / "run_stage273_sub_a_from_DFT_add_alias_microtest.sh",
    ]
    for raw in sorted(RAW.glob("*")):
        paths.append(raw)
    write_csv(REPRO / "artifact_index.csv", artifacts(paths), ["path", "bytes", "sha256"])
    print(decision)
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
