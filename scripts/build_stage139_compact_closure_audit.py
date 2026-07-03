#!/usr/bin/env python3
"""Build Stage139 compact-output PVW_TMLWE closure audit."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import os
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "scripts" / "build_stage137_decomp_dft_attribution_gate.py"
MOSFHET_DIR = ROOT / "src" / "mosfhet"
STAGE138_C = ROOT / "repro" / "stage138_shared_mask_compact_gate" / "shared_mask_compact_gate.c"
OUT_DIR = ROOT / "repro" / "stage139_compact_closure_audit"
SUMMARY_CSV = OUT_DIR / "summary.csv"
CLOSURE_CSV = OUT_DIR / "closure.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "compact_closure_audit.c"
C_BINARY = OUT_DIR / "compact_closure_audit"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage139_compact_closure_audit.md"
PLAN_MD = ROOT / "experiments" / "stage139_compact_closure_audit_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage139_compact_closure_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_compact_closure_boundary.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"


CLOSURE_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "Bg_bit",
    "seed",
    "mask_mismatches",
    "max_mask_gap",
    "status",
]


def load_helper():
    spec = importlib.util.spec_from_file_location("stage137_helpers", HELPER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Stage137 helper module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load_helper()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def bash(command: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-lc", command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def sanitize_log(text: str) -> str:
    return H.sanitize_log(text)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    return "\n".join(H.table(rows, fields))


def append_once(path: Path, heading: str, block: str) -> None:
    H.append_once(path, heading, block)


def min_field(rows: List[Dict[str, str]], field: str, r_filter: set[str] | None = None) -> str:
    return H.min_field(rows, field, r_filter)


def write_c_source() -> None:
    include_path = Path(os.path.relpath(STAGE138_C, C_SOURCE.parent)).as_posix()
    source = f'''
#define main stage138_original_main
#include "{include_path}"
#undef main

#ifndef STAGE139_BACKEND
#define STAGE139_BACKEND "unknown"
#endif

static void stage139_compare_mask_lanes(MAT_TRGSW_COMPACT_OUTPUT_DFT out,
    uint64_t *mismatches, double *max_gap) {{
  for (int lane = 1; lane < out->r; lane++) {{
    compare_dft(out->a[0], out->a[lane], mismatches, max_gap);
  }}
}}

static void stage139_closure_case(int r, int N, int T, int Bg_bit, int seed) {{
  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(1, r, N);
  MAT_TRGSW_COMPACT_DFT selector =
      mat_trgsw_compact_alloc_new_DFT_sample(T, Bg_bit, 1, r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT out =
      mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_MUL_SCRATCH scratch =
      mat_trgsw_compact_alloc_mul_scratch(N);

  fill_case(in, selector, r, N, T, Bg_bit, seed);
  mat_trgsw_compact_mul_pvmtmlwe_DFT(out, in, selector, scratch);

  uint64_t mismatches = 0;
  double max_gap = 0.0;
  stage139_compare_mask_lanes(out, &mismatches, &max_gap);
  const char *status = "EXPECTED_NONCLOSED_COMPACT_OUTPUT";
  if (r <= 1) status = mismatches == 0 ? "TRIVIAL_R1_CLOSED" : "FAIL_R1";
  else if (mismatches == 0) status = "UNEXPECTED_SHARED_MASK_CLOSED";

  printf("CLOSURE139,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%.9f,%s\\n",
      STAGE139_BACKEND, r, N, T, Bg_bit, seed, mismatches, max_gap, status);

  free_mat_trgsw_compact_mul_scratch(scratch);
  free_mat_trgsw_compact_output_DFT(out);
  free_mat_trgsw_compact_DFT(selector);
  free_pvmtmlwe(in);
}}

int main(void) {{
  const int T = 7;
  const int Bg_bit = 7;
  const int seed = 0;
  stage139_closure_case(2, 512, T, Bg_bit, seed);
  stage139_closure_case(4, 512, T, Bg_bit, seed);
  stage139_closure_case(6, 512, T, Bg_bit, seed);
  stage139_closure_case(2, 1024, T, Bg_bit, seed);
  stage139_closure_case(4, 1024, T, Bg_bit, seed);
  stage139_closure_case(6, 1024, T, Bg_bit, seed);
  fprintf(stderr, "stage139_sink=%f\\n", g_stage138_sink);
  return 0;
}}
'''
    write_text_lf(C_SOURCE, source.lstrip())


def build_mosfhet_static(backend: str) -> bool:
    cmd = (
        "cd src/mosfhet && make clean >/dev/null 2>&1 || true && "
        f"make static FFT_LIB={backend} A_PRNG=none ENABLE_VAES=false "
        "ENABLE_PVW_TMLWE=true -j$(nproc)"
    )
    proc = bash(cmd, timeout=180)
    write_text_lf(BUILD_LOG, "\n".join([
        f"command: {cmd}", f"returncode: {proc.returncode}", "--- stdout ---",
        sanitize_log(proc.stdout), "--- stderr ---", sanitize_log(proc.stderr)
    ]) + "\n")
    return proc.returncode == 0


def compile_probe(backend: str) -> bool:
    cmd = (
        f"gcc -O2 -DSTAGE138_BACKEND=\\\"{backend}\\\" "
        f"-DSTAGE139_BACKEND=\\\"{backend}\\\" "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(C_BINARY)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
    )
    proc = bash(cmd, timeout=60)
    write_text_lf(COMPILE_LOG, "\n".join([
        f"command: {cmd}", f"returncode: {proc.returncode}", "--- stdout ---",
        sanitize_log(proc.stdout), "--- stderr ---", sanitize_log(proc.stderr)
    ]) + "\n")
    return proc.returncode == 0


def cleanup_build_outputs() -> None:
    try:
        C_BINARY.unlink()
    except FileNotFoundError:
        pass
    bash("cd src/mosfhet && make clean >/dev/null 2>&1 || true", timeout=60)


def parse_stdout(stdout: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for line in stdout.splitlines():
        parts = line.strip().split(",")
        if parts and parts[0] == "CLOSURE139" and len(parts) == len(CLOSURE_FIELDS) + 1:
            rows.append(dict(zip(CLOSURE_FIELDS, parts[1:])))
    return rows


def run_probe(build_ok: bool, compile_ok: bool) -> Tuple[List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
        cleanup_build_outputs()
        return [], False
    proc = bash(f"./{rel(C_BINARY)}", timeout=180)
    write_text_lf(RUN_LOG_TXT, "\n".join([
        f"command: ./{rel(C_BINARY)}", f"returncode: {proc.returncode}",
        "--- stdout ---", sanitize_log(proc.stdout), "--- stderr ---", sanitize_log(proc.stderr)
    ]) + "\n")
    rows = parse_stdout(proc.stdout)
    cleanup_build_outputs()
    return rows, proc.returncode == 0


def build_summary(build_ok: bool, compile_ok: bool, run_ok: bool,
    closure_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    expected_nonclosed = (
        len(closure_rows) == 6
        and all(row["status"] == "EXPECTED_NONCLOSED_COMPACT_OUTPUT" and int(row["mask_mismatches"]) > 0 for row in closure_rows)
    )
    if not (build_ok and compile_ok and run_ok and len(closure_rows) == 6):
        decision = "FAIL_STAGE139_COMPACT_CLOSURE_AUDIT"
    elif expected_nonclosed:
        decision = "PASS_STAGE139_COMPACT_DIAGONAL_NOT_PVW_CLOSED_REDIRECT_FULL_MAT_ROUTE"
    else:
        decision = "INVESTIGATE_STAGE139_UNEXPECTED_COMPACT_CLOSURE"
    return [
        {"gate": "stage139_mosfhet_static_build", "status": "PASS" if build_ok else "FAIL", "metric": "make_static_spqlios_pvw", "value": str(build_ok).lower(), "evidence": rel(BUILD_LOG), "detail": "MOSFHET static build with PVW/MAT objects.", "next_action": "Fix build first."},
        {"gate": "stage139_probe_compile", "status": "PASS" if compile_ok else "FAIL", "metric": "gcc_probe_compile", "value": str(compile_ok).lower(), "evidence": rel(COMPILE_LOG), "detail": "Standalone compact closure audit compiled.", "next_action": ""},
        {"gate": "stage139_probe_run", "status": "PASS" if run_ok else "FAIL", "metric": "probe_returncode", "value": "0" if run_ok else "nonzero-or-skipped", "evidence": rel(RUN_LOG_TXT), "detail": "Compact closure audit executed.", "next_action": ""},
        {"gate": "stage139_closure_rows", "status": "PASS" if len(closure_rows) == 6 else "FAIL", "metric": "closure_rows", "value": str(len(closure_rows)), "evidence": rel(CLOSURE_CSV), "detail": "Closure rows recorded for r=2,4,6 and N=512,1024.", "next_action": ""},
        {"gate": "stage139_expected_nonclosure", "status": "PASS" if expected_nonclosed else "FAIL", "metric": "min_mask_mismatches", "value": min_field(closure_rows, "mask_mismatches") if closure_rows else "", "evidence": rel(CLOSURE_CSV), "detail": "Compact diagonal output has lane-specific masks and is not directly PVW_TMLWE closed.", "next_action": "Do not wire this output directly into SAB state."},
        {"gate": "stage139_decision", "status": decision, "metric": "route_policy", "value": "", "evidence": f"{rel(SUMMARY_CSV)}; {rel(CLOSURE_CSV)}", "detail": "Stage139 decides whether Stage138 compact output can be direct SAB state.", "next_action": "Use full MAT PVW_TMLWE output or design shared-output compact, not diagonal compact, for Stage140."},
    ]


def write_docs(summary: List[Dict[str, str]], closure_rows: List[Dict[str, str]]) -> None:
    status = summary[-1]["status"]
    summary_table = table(summary, ["gate", "status", "metric", "value", "detail"])
    closure_table = table(closure_rows, CLOSURE_FIELDS)
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage139 Compact Closure Audit Plan", "", "Date: 2026-07-03", "",
        "## Objective", "",
        "Check whether the Stage138 diagonal compact output is closed under the PVW_TMLWE state invariant: one shared mask and r body lanes.", "",
        "## Falsification Criteria", "",
        "- the audit is skipped after Stage138 promotion;",
        "- a lane-wise compact output is wired into SAB without proving shared-mask closure;",
        "- the result is interpreted as a performance failure instead of a representation-boundary decision.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage139 Compact Closure Model", "", "Date: 2026-07-03", "",
        "A PVW/MAT-RLWE ciphertext state used by SAB has one shared mask polynomial `a` and r body polynomials.",
        "Stage138's compact diagonal output stores one output mask per lane. This can accelerate repeated independent lane-pair work, but it is not automatically a PVW_TMLWE state.",
        "If output masks differ across lanes, converting them to one shared mask while preserving phase would require secret-key-dependent correction, so direct SAB integration is invalid.",
        "",
        "## Closure Rows", "", closure_table,
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# V139: Compact Closure Boundary", "", "## Summary", "",
        "Stage139 rejects direct use of diagonal compact output as the r-body SAB accumulator when the output masks are lane-specific.",
        "The valid next routes are full MAT PVW_TMLWE optimization or a new shared-output compact representation that accumulates a single mask.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage139 Compact Closure Audit", "", "Date: 2026-07-03", "",
        "## Decision", "", f"`{status}`", "",
        "Stage139 prevents a route error: Stage138's compact diagonal kernel improves amortized independent-lane EP, but its output is not directly a PVW_TMLWE accumulator if lane masks differ.",
        "",
        "## Gates", "", summary_table, "",
        "## Closure Rows", "", closure_table,
    ]) + "\n")


def update_longform_docs(status: str, closure_rows: List[Dict[str, str]]) -> None:
    min_mismatch = min_field(closure_rows, "mask_mismatches")
    stage_block = f"""
## Stage 139: Compact Closure Audit

Goal:

```text
Determine whether Stage138 diagonal compact output is directly usable as a
PVW_TMLWE SAB state with one shared mask and r bodies.
```

Status:

```text
Completed. Stage139 records {status}. Minimum mask mismatch count is
{min_mismatch}; direct diagonal compact SAB integration is blocked. Stage140
must use full MAT PVW_TMLWE output or design a shared-output compact kernel.
```
"""
    append_once(ROADMAP_MD, "## Stage 139: Compact Closure Audit", stage_block)
    goal_block = f"""
Stage139 corrects the Stage138 promotion boundary. The compact diagonal kernel
is useful for repeated independent lane-pair EP, but it is not directly closed
as a PVW_TMLWE r-body ciphertext because lane output masks differ. The next
algorithmic route is shared-output compact/full-MAT optimization, not direct
diagonal compact insertion into SAB.
"""
    append_once(GOAL_MD, "Stage139 corrects the Stage138 promotion boundary", goal_block)
    current_block = f"""
43. Treat Stage139 as the compact closure audit:
    `{status}`. Minimum mask mismatch count is {min_mismatch}. Direct diagonal
    compact output is not a valid PVW_TMLWE SAB accumulator; Stage140 must
    target full MAT/shared-output compact closure.
"""
    append_once(CURRENT_GOAL_MD, "43. Treat Stage139 as the compact", current_block)


def upsert_hypothesis(status: str, closure_rows: List[Dict[str, str]]) -> None:
    min_mismatch = min_field(closure_rows, "mask_mismatches")
    block = f"""  - id: H63_compact_diagonal_pvw_closure
    statement: >
      The Stage138 diagonal compact external product is not directly closed as
      a PVW_TMLWE SAB accumulator unless all output lane masks are equal.
    mechanism: >
      PVW_TMLWE has one shared mask and r bodies. Diagonal compact EP emits a
      lane-local mask for each lane, and a secret-key-dependent correction would
      be needed to fold those masks into one shared mask.
    status: stage139_compact_closure_audit
    evidence: docs/stage139_compact_closure_audit.md; experiments/stage139_compact_closure_audit_plan.md; theory_checks/stage139_compact_closure_model.md; algorithm_variants/mat_rlwe_sab_compact_closure_boundary.md; scripts/build_stage139_compact_closure_audit.py; repro/stage139_compact_closure_audit/summary.csv; repro/stage139_compact_closure_audit/closure.csv; repro/stage139_compact_closure_audit/artifact_index.csv
    current_decision: >
      Stage139 records {status}. The minimum mask mismatch count is
      {min_mismatch}. Direct diagonal compact SAB integration is blocked.
    failure_criteria:
      - direct compact output is inserted into SAB without shared-mask closure
      - Stage138 kernel speedup is claimed as r-body SAB speedup
      - shared-output/full-MAT route is skipped
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8")
    marker = "  - id: H63_compact_diagonal_pvw_closure"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(HYPOTHESIS_YAML, text + block)


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
            continue
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() else "",
            "size_bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def upsert_run_log(status: str) -> None:
    fields = ["run_id", "date", "commit_or_state", "stage", "backend", "command", "params", "seed", "status", "summary", "artifacts"]
    run_id = "stage139-compact-closure-audit-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, CLOSURE_CSV, BUILD_LOG, COMPILE_LOG, RUN_LOG_TXT, C_SOURCE, ARTIFACT_INDEX, Path(__file__).resolve()]
    rows.append({
        "run_id": run_id,
        "date": "2026-07-03",
        "commit_or_state": f"working-tree-after-{git_head()}",
        "stage": "Stage 139",
        "backend": "MOSFHET FFT_LIB=spqlios ENABLE_PVW_TMLWE=true",
        "command": "python scripts/build_stage139_compact_closure_audit.py",
        "params": "r=2,4,6 N=512,1024 T=7 Bg_bit=7 closure=shared-mask",
        "seed": "0 subset",
        "status": status,
        "summary": "Stage139 audits whether diagonal compact output is closed as PVW_TMLWE.",
        "artifacts": "; ".join(rel(p) for p in artifacts),
    })
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 139 Compact Closure Audit

- `docs/stage139_compact_closure_audit.md`
- `experiments/stage139_compact_closure_audit_plan.md`
- `theory_checks/stage139_compact_closure_model.md`
- `algorithm_variants/mat_rlwe_sab_compact_closure_boundary.md`
- `scripts/build_stage139_compact_closure_audit.py`
- `repro/stage139_compact_closure_audit/summary.csv`
- `repro/stage139_compact_closure_audit/closure.csv`
- `repro/stage139_compact_closure_audit/mosfhet_static_build.log`
- `repro/stage139_compact_closure_audit/compile_probe.log`
- `repro/stage139_compact_closure_audit/run_probe.log`
- `repro/stage139_compact_closure_audit/compact_closure_audit.c`
- `repro/stage139_compact_closure_audit/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 139 Compact Closure Audit", block)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backend = "spqlios"
    write_c_source()
    build_ok = build_mosfhet_static(backend)
    compile_ok = compile_probe(backend) if build_ok else False
    closure_rows, run_ok = run_probe(build_ok, compile_ok)
    write_csv(CLOSURE_CSV, closure_rows, CLOSURE_FIELDS)
    summary = build_summary(build_ok, compile_ok, run_ok, closure_rows)
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    status = summary[-1]["status"]
    write_docs(summary, closure_rows)
    update_longform_docs(status, closure_rows)
    upsert_hypothesis(status, closure_rows)
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, CLOSURE_CSV, BUILD_LOG, COMPILE_LOG, RUN_LOG_TXT, C_SOURCE, ARTIFACT_INDEX, Path(__file__).resolve()]
    write_artifact_index(artifacts)
    upsert_run_log(status)
    upsert_global_manifest()
    print(f"Stage139 compact closure audit: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if not status.startswith("FAIL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
