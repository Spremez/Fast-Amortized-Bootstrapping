#!/usr/bin/env python3
"""Build Stage119 shared-term semantics and object prototype gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage119_shared_term_object_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
PHASE_CSV = OUT_DIR / "phase_results.csv"
LAYOUT_CSV = OUT_DIR / "object_layout.csv"
COMPILE_LOG = OUT_DIR / "compile.log"
C_SOURCE = OUT_DIR / "shared_term_object_gate.c"
C_BINARY = OUT_DIR / "shared_term_object_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage119_shared_term_object_gate.md"
PLAN_MD = ROOT / "experiments" / "stage119_shared_term_object_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage119_shared_term_semantics.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_vector_shared_lane_local_object.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


PHASE_FIELDS = [
    "r",
    "N",
    "variant",
    "mismatches_noiseless",
    "negative_control_failures",
    "max_abs_error_noiseless",
    "max_abs_noise",
    "noise_bound",
    "noise_bound_violations",
    "status",
]

LAYOUT_FIELDS = [
    "r",
    "N",
    "dense_terms",
    "scalar_shared_terms",
    "vector_shared_terms",
    "dense_selector_polys",
    "stage118_selector_polys",
    "vector_selector_polys",
    "dense_total_polys",
    "stage118_total_polys",
    "vector_total_polys",
    "vector_over_dense_byte_ratio",
    "vector_product_ratio",
    "status",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sanitize_log(text: str) -> str:
    if text is None:
        return ""
    text = text.replace("\x00", "")
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ch.isprintable())
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
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


def write_c_source() -> None:
    source = r'''
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static int64_t small(uint64_t salt, uint64_t a, uint64_t b, uint64_t c) {
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0xbf58476d1ce4e5b9ULL) * 0x94d049bb133111ebULL;
  x ^= (b + 0x2545f4914f6cdd1dULL) * 0x9e3779b97f4a7c15ULL;
  x ^= (c + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 33;
  int64_t v = (int64_t)(x % 19ULL) - 9;
  return v == 0 ? 1 : v;
}

static int64_t abs64(int64_t x) {
  return x < 0 ? -x : x;
}

static int64_t digit_shared(size_t coeff) {
  return small(1, coeff, 0, 0);
}

static int64_t digit_body(size_t lane, size_t coeff) {
  return small(2, lane, coeff, 0);
}

static int64_t secret(size_t lane, size_t coeff) {
  return small(3, lane, coeff, 0);
}

static int64_t msg_shared(size_t lane, size_t coeff) {
  return small(4, lane, coeff, 0);
}

static int64_t msg_body(size_t lane, size_t coeff) {
  return small(5, lane, coeff, 0);
}

static int64_t mask_shared(size_t lane, size_t coeff) {
  return small(6, lane, coeff, 0);
}

static int64_t mask_body(size_t lane, size_t coeff) {
  return small(7, lane, coeff, 0);
}

static int64_t noise_value(size_t lane, size_t coeff, size_t term) {
  int64_t v = small(8 + term, lane, coeff, 0) % 3;
  if (v < 0) v = -v;
  return v - 1;
}

static int64_t dense_expected(size_t lane, size_t coeff) {
  return digit_shared(coeff) * msg_shared(lane, coeff) +
      digit_body(lane, coeff) * msg_body(lane, coeff);
}

static int64_t vector_shared_phase(size_t lane, size_t coeff, int with_noise) {
  const int64_t s = secret(lane, coeff);
  const int64_t ns = with_noise ? noise_value(lane, coeff, 0) : 0;
  const int64_t nb = with_noise ? noise_value(lane, coeff, 1) : 0;
  const int64_t shared_body = mask_shared(lane, coeff) * s +
      msg_shared(lane, coeff) + ns;
  const int64_t lane_body = mask_body(lane, coeff) * s +
      msg_body(lane, coeff) + nb;
  const int64_t shared_phase = shared_body - mask_shared(lane, coeff) * s;
  const int64_t body_phase = lane_body - mask_body(lane, coeff) * s;
  return digit_shared(coeff) * shared_phase + digit_body(lane, coeff) * body_phase;
}

static int64_t scalar_shared_phase(size_t lane, size_t coeff) {
  const int64_t s = secret(lane, coeff);
  const int64_t shared_body = mask_shared(0, coeff) * s + msg_shared(0, coeff);
  const int64_t lane_body = mask_body(lane, coeff) * s + msg_body(lane, coeff);
  const int64_t shared_phase = shared_body - mask_shared(0, coeff) * s;
  const int64_t body_phase = lane_body - mask_body(lane, coeff) * s;
  return digit_shared(coeff) * shared_phase + digit_body(lane, coeff) * body_phase;
}

static int run_phase_case(size_t r, size_t N, const char *variant) {
  uint64_t mismatches = 0;
  uint64_t negative_control_failures = 0;
  uint64_t noise_violations = 0;
  int64_t max_error = 0;
  int64_t max_noise = 0;
  int64_t noise_bound = 0;

  for (size_t coeff = 0; coeff < N; coeff++) {
    for (size_t lane = 0; lane < r; lane++) {
      const int64_t expected = dense_expected(lane, coeff);
      int64_t got = 0;
      if (variant[0] == 'v') {
        got = vector_shared_phase(lane, coeff, 0);
        const int64_t noisy = vector_shared_phase(lane, coeff, 1);
        const int64_t bound = abs64(digit_shared(coeff)) + abs64(digit_body(lane, coeff));
        const int64_t noise = abs64(noisy - got);
        if (noise > max_noise) max_noise = noise;
        if (bound > noise_bound) noise_bound = bound;
        if (noise > bound) noise_violations++;
      } else {
        got = scalar_shared_phase(lane, coeff);
      }
      const int64_t err = abs64(got - expected);
      if (err != 0) {
        mismatches++;
        if (variant[0] == 's') negative_control_failures++;
      }
      if (err > max_error) max_error = err;
    }
  }

  const int ok = variant[0] == 'v' ?
      (mismatches == 0 && noise_violations == 0) :
      (negative_control_failures > 0);
  printf("%zu,%zu,%s,%" PRIu64 ",%" PRIu64 ",%" PRId64 ",%" PRId64
         ",%" PRId64 ",%" PRIu64 ",%s\n",
      r, N, variant, mismatches, negative_control_failures, max_error,
      max_noise, noise_bound, noise_violations,
      ok ? (variant[0] == 'v' ? "PASS_VECTOR_OBJECT" : "PASS_REJECTED_SCALAR_SHARED") : "FAIL");
  return ok ? 0 : 1;
}

static int run_layout_case(size_t r, size_t N) {
  (void)N;
  const uint64_t dense_terms = (uint64_t)(r + 1) * (uint64_t)(r + 1);
  const uint64_t scalar_terms = 1 + 2 * (uint64_t)r;
  const uint64_t vector_terms = 2 * (uint64_t)r;
  const uint64_t dense_selector_polys = dense_terms;
  const uint64_t stage118_selector_polys = 2 * scalar_terms;
  const uint64_t vector_selector_polys = 2 * vector_terms;
  const uint64_t dense_total = (1 + (uint64_t)r) + dense_selector_polys;
  const uint64_t stage118_total = 2 * (uint64_t)r + stage118_selector_polys;
  const uint64_t vector_total = 2 * (uint64_t)r + vector_selector_polys;
  const double byte_ratio = (double)vector_total / (double)dense_total;
  const double product_ratio = (double)dense_terms / (double)vector_terms;
  const int ok = vector_terms < dense_terms && vector_total <= stage118_total;
  printf("%zu,%zu,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%.6f,%.6f,%s\n",
      r, N, dense_terms, scalar_terms, vector_terms, dense_selector_polys,
      stage118_selector_polys, vector_selector_polys, dense_total,
      stage118_total, vector_total, byte_ratio, product_ratio,
      ok ? "PASS_LAYOUT_REFINED" : "FAIL");
  return ok ? 0 : 1;
}

int main(void) {
  const size_t rs[] = {2, 4, 6};
  const size_t Ns[] = {64, 256};
  int failures = 0;
  for (size_t i = 0; i < sizeof(rs) / sizeof(rs[0]); i++) {
    for (size_t j = 0; j < sizeof(Ns) / sizeof(Ns[0]); j++) {
      failures += run_phase_case(rs[i], Ns[j], "scalar_shared");
      failures += run_phase_case(rs[i], Ns[j], "vector_shared");
      failures += run_layout_case(rs[i], Ns[j]);
    }
  }
  return failures == 0 ? 0 : 1;
}
'''
    write_text_lf(C_SOURCE, source.lstrip())


def compile_probe() -> bool:
    cmd = (
        "gcc -O2 -std=c11 -Wall -Wextra "
        f"-o {rel(C_BINARY)} {rel(C_SOURCE)}"
    )
    proc = bash(cmd, timeout=60)
    log = [
        f"command: {cmd}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize_log(proc.stdout),
        "--- stderr ---",
        sanitize_log(proc.stderr),
    ]
    write_text_lf(COMPILE_LOG, "\n".join(log) + "\n")
    return proc.returncode == 0


def run_probe(compile_ok: bool) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    if not compile_ok:
        return [], []
    proc = bash(f"./{rel(C_BINARY)}", timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(
            f"shared term object probe failed\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    phase_rows: List[Dict[str, str]] = []
    layout_rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        if len(values) == len(PHASE_FIELDS):
            phase_rows.append(dict(zip(PHASE_FIELDS, values)))
        elif len(values) == len(LAYOUT_FIELDS):
            layout_rows.append(dict(zip(LAYOUT_FIELDS, values)))
        else:
            raise RuntimeError(f"unexpected probe row: {line}")
    return phase_rows, layout_rows


def build_summary(compile_ok: bool, phase_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not compile_ok:
        return [
            {
                "gate": "stage119_compile",
                "status": "BLOCKED",
                "metric": "gcc_compile",
                "value": "false",
                "evidence": rel(COMPILE_LOG),
                "detail": "Shared-term object probe did not compile.",
                "next_action": "Stop before object prototype.",
            },
            {
                "gate": "stage119_decision",
                "status": "BLOCKED_STAGE119_OBJECT_PROBE_COMPILER",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(COMPILE_LOG),
                "detail": "No shared-term semantics evidence is available.",
                "next_action": "Stop the branch.",
            },
        ]

    scalar_rows = [row for row in phase_rows if row["variant"] == "scalar_shared"]
    vector_rows = [row for row in phase_rows if row["variant"] == "vector_shared"]
    scalar_rejected = all(int(row["negative_control_failures"]) > 0 for row in scalar_rows)
    vector_exact = all(row["mismatches_noiseless"] == "0" for row in vector_rows)
    noise_ok = all(row["noise_bound_violations"] == "0" for row in vector_rows)
    layout_ok = all(row["status"] == "PASS_LAYOUT_REFINED" for row in layout_rows)
    r4_layout = next(row for row in layout_rows if row["r"] == "4" and row["N"] == "64")
    decision = (
        "PASS_STAGE119_VECTOR_SHARED_OBJECT_READY_REAL_STRUCT_PROTOTYPE_REQUIRED"
        if scalar_rejected and vector_exact and noise_ok and layout_ok
        else "FAIL_STAGE119_SHARED_TERM_OBJECT_GATE"
    )
    return [
        {
            "gate": "stage119_compile",
            "status": "PASS",
            "metric": "gcc_compile",
            "value": "true",
            "evidence": rel(COMPILE_LOG),
            "detail": "Generated shared-term object C probe compiled under WSL gcc.",
            "next_action": "Use only as object-semantics evidence.",
        },
        {
            "gate": "stage119_scalar_shared_negative_control",
            "status": "PASS_REJECTED" if scalar_rejected else "FAIL",
            "metric": "scalar_negative_failures",
            "value": ";".join(row["negative_control_failures"] for row in scalar_rows),
            "evidence": rel(PHASE_CSV),
            "detail": "A scalar shared term cannot represent independent lane shared messages.",
            "next_action": "Do not implement scalar-shared `1+2r` interpretation.",
        },
        {
            "gate": "stage119_vector_shared_phase",
            "status": "PASS" if vector_exact else "FAIL",
            "metric": "vector_mismatches",
            "value": ";".join(row["mismatches_noiseless"] for row in vector_rows),
            "evidence": rel(PHASE_CSV),
            "detail": "Vector-shared lane-local object matches dense reference in noiseless phase.",
            "next_action": "Real structs must use vector-shared shared-row storage.",
        },
        {
            "gate": "stage119_noise_bound",
            "status": "PASS_BOUNDED" if noise_ok else "FAIL",
            "metric": "noise_bound_violations",
            "value": ";".join(row["noise_bound_violations"] for row in vector_rows),
            "evidence": rel(PHASE_CSV),
            "detail": "Toy noise remains within the digit-sum bound.",
            "next_action": "A real noise model is still required before SAB.",
        },
        {
            "gate": "stage119_layout_refinement",
            "status": "PASS" if layout_ok else "FAIL",
            "metric": "r4_vector_over_dense_byte_ratio",
            "value": r4_layout["vector_over_dense_byte_ratio"],
            "evidence": rel(LAYOUT_CSV),
            "detail": "Vector-shared object is no larger than the Stage118 conservative shape and remains below dense bytes for r=4.",
            "next_action": "Stage120 can prototype real structs outside the hot path.",
        },
        {
            "gate": "stage119_decision",
            "status": decision,
            "metric": "next_gate_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Shared-term semantics are refined: scalar-shared is rejected, vector-shared is the only viable object route.",
            "next_action": "Stage120 should build real C structs and allocation/phase tests outside `sab_pvw_*`.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage119 Shared-Term Object Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Check whether the Stage117/118 shared term can represent independent LUT",
        "lanes. The scalar-shared interpretation must fail; vector-shared",
        "lane-local storage must pass phase and bounded toy-noise checks.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage119_shared_term_object_gate.py",
        "```",
        "",
        "Passing this stage permits real struct prototype work only. It does not",
        "permit SAB hot-path integration.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(phase_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage119 Shared-Term Semantics",
        "",
        "Date: 2026-07-03",
        "",
        "Independent LUT lanes require the shared-row message to be lane-indexed.",
        "A scalar shared term can only store one shared message and is therefore a",
        "negative control. The viable object route is vector-shared: each lane has",
        "a lane-local shared-row encryption and a lane-local body-row encryption.",
        "",
        "This refines Stage117/118: the `1+2r` scalar-shared interpretation is not",
        "valid for independent LUT lanes. The object route uses `2r` encrypted",
        "phase terms and `4r` selector polynomials for k=1.",
        "",
        "## Phase Rows",
        "",
        "| r | N | variant | mismatches | negative failures | noise violations | status |",
        "|---:|---:|---|---:|---:|---:|---|",
    ]
    for row in phase_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['variant']} | "
            f"{row['mismatches_noiseless']} | {row['negative_control_failures']} | "
            f"{row['noise_bound_violations']} | {row['status']} |"
        )
    lines += [
        "",
        "## Layout Rows",
        "",
        "| r | N | dense terms | vector terms | vector selector polys | vector/dense bytes | ratio |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_terms']} | "
            f"{row['vector_shared_terms']} | {row['vector_selector_polys']} | "
            f"{row['vector_over_dense_byte_ratio']} | {row['vector_product_ratio']} |"
        )
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# V119: Vector-Shared Lane-Local Object",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB r-body research track.",
        "- Focused module: lane-local body-linear external product representation.",
        "- Optimization target: `T_bootstrap/r` after complete SAB integration.",
        "- Status labels: `[object-semantics-supported]`, `[noise-toy-only]`, `[not-hot-path]`.",
        "- Main hypothesis: vector-shared lane-local storage can support independent LUT lanes while preserving body-linear term reduction.",
        "",
        "## Mathematical Definition",
        "",
        "For each lane q, store a lane-local shared-row encryption and a lane-local",
        "body-row encryption. The scalar-shared interpretation is rejected because",
        "it cannot encode lane-dependent shared-row messages.",
        "",
        "## Pseudocode",
        "",
        "```text",
        "Input: lane q, coefficient i",
        "Output: phase matching dense reference",
        "1. decrypt shared_q[i] with lane q key",
        "2. decrypt body_q[i] with lane q key",
        "3. return d_shared[i] * phase(shared_q[i]) + d_body[q,i] * phase(body_q[i])",
        "```",
        "",
        "## Delta From Stage118",
        "",
        "| Stage118 interpretation | Stage119 refinement | Status |",
        "| --- | --- | --- |",
        "| scalar shared term possible | rejected for independent LUT lanes | negative control passes |",
        "| conservative selector `2(1+2r)` | vector-shared selector `4r` | phase-supported in toy C |",
        "| noise recorded-not-proven | toy digit-sum noise bound checked | real noise still required |",
        "",
        "## Required Experiments",
        "",
        "- real struct allocation and destructor tests;",
        "- real polynomial phase equivalence;",
        "- real encryption/noise simulator;",
        "- DFT conversion prototype;",
        "- only then isolated external-product kernel work.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], phase_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage119 Shared-Term Object Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage119 checks a real-object semantic risk: whether the shared row can",
        "be scalar-shared across independent LUT lanes. It cannot. The scalar",
        "shared interpretation is rejected, and the vector-shared lane-local",
        "object is selected for future real struct work.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        lines.append(
            f"| {row['gate']} | {row['status']} | {row['metric']} | "
            f"{row['value']} | {row['detail']} |"
        )
    lines += [
        "",
        "## Phase Results",
        "",
        "| r | N | variant | mismatches | negative failures | max noise | noise bound | violations | status |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in phase_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['variant']} | "
            f"{row['mismatches_noiseless']} | {row['negative_control_failures']} | "
            f"{row['max_abs_noise']} | {row['noise_bound']} | "
            f"{row['noise_bound_violations']} | {row['status']} |"
        )
    lines += [
        "",
        "## Layout Refinement",
        "",
        "| r | N | dense terms | scalar terms | vector terms | vector/dense bytes | vector product ratio | status |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_terms']} | "
            f"{row['scalar_shared_terms']} | {row['vector_shared_terms']} | "
            f"{row['vector_over_dense_byte_ratio']} | {row['vector_product_ratio']} | "
            f"{row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "This is a correction, not a final acceleration claim. The valid object",
        "route is vector-shared lane-local storage. Stage120 must build real C",
        "structs and real polynomial phase/noise tests outside `sab_pvw_*`.",
    ]
    write_text_lf(OUT_MD, "\n".join(lines) + "\n")


def artifact_index(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    return rows


def upsert_run_log(status: str) -> None:
    fields = [
        "run_id",
        "date",
        "commit_or_state",
        "stage",
        "backend",
        "command",
        "params",
        "seed",
        "status",
        "summary",
        "artifacts",
    ]
    rows = [
        row for row in read_csv(RUN_LOG)
        if row.get("run_id") != "stage119-shared-term-object-gate-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(THEORY_MD),
        rel(VARIANT_MD),
        rel(SUMMARY_CSV),
        rel(PHASE_CSV),
        rel(LAYOUT_CSV),
        rel(COMPILE_LOG),
        rel(C_SOURCE),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "build_stage119_shared_term_object_gate.py"),
    ]
    rows.append(
        {
            "run_id": "stage119-shared-term-object-gate-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 119",
            "backend": "WSL gcc object-semantics C",
            "command": "python scripts/build_stage119_shared_term_object_gate.py",
            "params": "scalar-shared negative control; vector-shared object r=2,4,6 N=64,256",
            "seed": "deterministic",
            "status": status,
            "summary": "Stage119 rejects scalar-shared term semantics and selects vector-shared lane-local object route.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_plan()
    write_variant()
    write_c_source()
    compile_ok = compile_probe()
    phase_rows, layout_rows = run_probe(compile_ok)
    summary = build_summary(compile_ok, phase_rows, layout_rows)
    write_csv(PHASE_CSV, phase_rows, PHASE_FIELDS)
    write_csv(LAYOUT_CSV, layout_rows, LAYOUT_FIELDS)
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_theory(phase_rows, layout_rows)
    write_md(summary, phase_rows, layout_rows)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                THEORY_MD,
                VARIANT_MD,
                SUMMARY_CSV,
                PHASE_CSV,
                LAYOUT_CSV,
                COMPILE_LOG,
                C_SOURCE,
                ROOT / "scripts" / "build_stage119_shared_term_object_gate.py",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage119 shared-term object gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") or status.startswith("BLOCKED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
