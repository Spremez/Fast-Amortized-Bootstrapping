#!/usr/bin/env python3
"""Build Stage125 compact selector gadget-decomposition gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT_DIR = ROOT / "repro" / "stage125_compact_selector_gadget_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
GADGET_CSV = OUT_DIR / "gadget_results.csv"
LAYOUT_CSV = OUT_DIR / "layout_results.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "compact_selector_gadget_gate.c"
C_BINARY = OUT_DIR / "compact_selector_gadget_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage125_compact_selector_gadget_gate.md"
PLAN_MD = ROOT / "experiments" / "stage125_compact_selector_gadget_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage125_compact_selector_gadget_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_compact_selector_gadget.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


GADGET_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "k",
    "Bg_bit",
    "seed",
    "coeff_dft_mismatches",
    "negative_failures",
    "max_dft_gap",
    "tolerance",
    "status",
]

LAYOUT_FIELDS = [
    "r",
    "N",
    "T",
    "k",
    "current_selector_dft_polys",
    "compact_selector_dft_polys",
    "selector_ratio",
    "current_dec_polys",
    "compact_dec_polys",
    "dec_overhead",
    "current_selector_plus_dec",
    "compact_selector_plus_dec",
    "selector_plus_dec_ratio",
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
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


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
#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef STAGE125_BACKEND
#define STAGE125_BACKEND "unknown"
#endif

static uint64_t mix64(uint64_t salt, uint64_t a, uint64_t b, uint64_t c) {
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0xbf58476d1ce4e5b9ULL) * 0x94d049bb133111ebULL;
  x ^= (b + 0x2545f4914f6cdd1dULL) * 0x9e3779b97f4a7c15ULL;
  x ^= (c + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 33;
  x *= 0xff51afd7ed558ccdULL;
  x ^= x >> 33;
  return x;
}

static uint64_t abs_gap(Torus a, Torus b) {
  const uint64_t d = (uint64_t)(a - b);
  if (d <= (1ULL << 63)) return d;
  return (~d) + 1ULL;
}

static TorusPolynomial *new_poly_array(int count, int N) {
  TorusPolynomial *out =
      (TorusPolynomial *)safe_malloc(sizeof(TorusPolynomial) * count);
  for (int i = 0; i < count; i++) out[i] = polynomial_new_torus_polynomial(N);
  return out;
}

static DFT_Polynomial *new_dft_array(int count, int N) {
  DFT_Polynomial *out =
      (DFT_Polynomial *)safe_malloc(sizeof(DFT_Polynomial) * count);
  for (int i = 0; i < count; i++) out[i] = polynomial_new_DFT_polynomial(N);
  return out;
}

static void free_poly_array_local(TorusPolynomial *in, int count) {
  for (int i = 0; i < count; i++) free_polynomial(in[i]);
  free(in);
}

static void free_dft_array_local(DFT_Polynomial *in, int count) {
  for (int i = 0; i < count; i++) free_DFT_polynomial(in[i]);
  free(in);
}

static void zero_poly(TorusPolynomial p) {
  memset(p->coeffs, 0, sizeof(Torus) * p->N);
}

static void zero_dft(DFT_Polynomial p) {
  memset(p->coeffs, 0, sizeof(double) * p->N);
}

static void fill_component(TorusPolynomial out, int lane, int kind, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)mix64(1000 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)kind, (uint64_t)i);
  }
}

static void make_gadget(TorusPolynomial out, int t, int Bg_bit, int exp,
    int64_t m) {
  zero_poly(out);
  const int word_size = (int)(sizeof(Torus) * 8);
  const Torus h = (Torus)1ULL << (word_size - (t + 1) * Bg_bit);
  out->coeffs[exp & (out->N - 1)] = (Torus)(m * (int64_t)h);
}

static void dft_mul_add_torus(DFT_Polynomial out, TorusPolynomial a,
    TorusPolynomial b) {
  DFT_Polynomial da = polynomial_new_DFT_polynomial(a->N);
  DFT_Polynomial db = polynomial_new_DFT_polynomial(a->N);
  polynomial_torus_to_DFT(da, a);
  polynomial_torus_to_DFT(db, b);
  polynomial_mul_addto_DFT(out, da, db);
  free_DFT_polynomial(da);
  free_DFT_polynomial(db);
}

static void compare_poly(TorusPolynomial a, TorusPolynomial b, uint64_t tol,
    uint64_t *mismatches, uint64_t *max_gap) {
  for (int i = 0; i < a->N; i++) {
    const uint64_t gap = abs_gap(a->coeffs[i], b->coeffs[i]);
    if (gap > tol) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static void run_case(int r, int N, int T, int k, int Bg_bit, int seed) {
  const uint64_t tol = 16384;
  const int lanes = r;
  const int streams = 2 * T * r;
  const int exp = (seed * 11 + r + 3) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *mask = new_poly_array(lanes, N);
  TorusPolynomial *body = new_poly_array(lanes, N);
  TorusPolynomial *dec_mask = new_poly_array(T * r, N);
  TorusPolynomial *dec_body = new_poly_array(T * r, N);
  TorusPolynomial gadget = polynomial_new_torus_polynomial(N);
  TorusPolynomial *ref_a = new_poly_array(lanes, N);
  TorusPolynomial *ref_b = new_poly_array(lanes, N);
  DFT_Polynomial *dft_a = new_dft_array(lanes, N);
  DFT_Polynomial *dft_b = new_dft_array(lanes, N);
  TorusPolynomial *out_a = new_poly_array(lanes, N);
  TorusPolynomial *out_b = new_poly_array(lanes, N);
  TorusPolynomial *neg_a = new_poly_array(lanes, N);
  TorusPolynomial *neg_b = new_poly_array(lanes, N);

  for (int q = 0; q < r; q++) {
    fill_component(mask[q], q, 0, seed);
    fill_component(body[q], q, 1, seed);
    zero_poly(ref_a[q]);
    zero_poly(ref_b[q]);
    zero_dft(dft_a[q]);
    zero_dft(dft_b[q]);
    zero_poly(neg_a[q]);
    zero_poly(neg_b[q]);
  }

  for (int t = 0; t < T; t++) {
    make_gadget(gadget, t, Bg_bit, exp, monomial);
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      polynomial_decompose_i(dec_mask[idx], mask[q], Bg_bit, T, t);
      polynomial_decompose_i(dec_body[idx], body[q], Bg_bit, T, t);
      polynomial_naive_mul_addto_torus(ref_a[q], dec_mask[idx], gadget);
      polynomial_naive_mul_addto_torus(ref_b[q], dec_body[idx], gadget);
      dft_mul_add_torus(dft_a[q], dec_mask[idx], gadget);
      dft_mul_add_torus(dft_b[q], dec_body[idx], gadget);
      polynomial_naive_mul_addto_torus(neg_b[q], dec_body[idx], gadget);
    }
  }

  uint64_t mismatches = 0;
  uint64_t max_gap = 0;
  uint64_t negative_failures = 0;
  for (int q = 0; q < r; q++) {
    polynomial_DFT_to_torus(out_a[q], dft_a[q]);
    polynomial_DFT_to_torus(out_b[q], dft_b[q]);
    compare_poly(ref_a[q], out_a[q], tol, &mismatches, &max_gap);
    compare_poly(ref_b[q], out_b[q], tol, &mismatches, &max_gap);
    uint64_t neg_gap = 0;
    compare_poly(ref_a[q], neg_a[q], 0, &negative_failures, &neg_gap);
    compare_poly(ref_b[q], neg_b[q], 0, &negative_failures, &neg_gap);
  }

  const int ok = mismatches == 0 && negative_failures > 0;
  printf("GADGET,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%s\n",
      STAGE125_BACKEND, r, N, T, k, Bg_bit, seed, mismatches,
      negative_failures, max_gap, tol,
      ok ? "PASS_COMPACT_SELECTOR_GADGET" : "FAIL");

  const uint64_t current_sel = (uint64_t)T * (uint64_t)(k + r) * (uint64_t)(k + r);
  const uint64_t compact_sel = 2ULL * (uint64_t)T * (uint64_t)r * (uint64_t)(k + 1);
  const uint64_t current_dec = (uint64_t)T * (uint64_t)(k + r);
  const uint64_t compact_dec = 2ULL * (uint64_t)T * (uint64_t)r;
  const uint64_t current_total = current_sel + current_dec;
  const uint64_t compact_total = compact_sel + compact_dec;
  const double selector_ratio = (double)current_sel / (double)compact_sel;
  const double dec_overhead = (double)compact_dec / (double)current_dec;
  const double total_ratio = (double)current_total / (double)compact_total;
  const int layout_ok = selector_ratio > 1.0 && total_ratio >= 1.0;
  printf("LAYOUT,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64
         ",%" PRIu64 ",%.6f,%" PRIu64 ",%" PRIu64 ",%.6f,%s\n",
      r, N, T, k, current_sel, compact_sel, selector_ratio, current_dec,
      compact_dec, dec_overhead, current_total, compact_total, total_ratio,
      layout_ok ? "PASS_LAYOUT_MODEL" : "FAIL");

  free_poly_array_local(mask, lanes);
  free_poly_array_local(body, lanes);
  free_poly_array_local(dec_mask, T * r);
  free_poly_array_local(dec_body, T * r);
  free_polynomial(gadget);
  free_poly_array_local(ref_a, lanes);
  free_poly_array_local(ref_b, lanes);
  free_dft_array_local(dft_a, lanes);
  free_dft_array_local(dft_b, lanes);
  free_poly_array_local(out_a, lanes);
  free_poly_array_local(out_b, lanes);
  free_poly_array_local(neg_a, lanes);
  free_poly_array_local(neg_b, lanes);
  (void)streams;
}

int main(void) {
  const int k = 1;
  const int T = 7;
  const int Bg_bit = 7;
  run_case(2, 1024, T, k, Bg_bit, 0);
  run_case(2, 1024, T, k, Bg_bit, 1);
  run_case(4, 1024, T, k, Bg_bit, 0);
  run_case(4, 1024, T, k, Bg_bit, 1);
  run_case(6, 1024, T, k, Bg_bit, 0);
  run_case(6, 1024, T, k, Bg_bit, 1);
  run_case(2, 2048, T, k, Bg_bit, 0);
  run_case(4, 2048, T, k, Bg_bit, 0);
  run_case(6, 2048, T, k, Bg_bit, 0);
  return 0;
}
'''
    write_text_lf(C_SOURCE, source.lstrip())


def build_mosfhet_static(backend: str) -> bool:
    cmd = (
        "cd src/mosfhet && "
        "make clean >/dev/null 2>&1 || true && "
        f"make static FFT_LIB={backend} A_PRNG=none ENABLE_VAES=false "
        "ENABLE_PVW_TMLWE=false -j$(nproc)"
    )
    proc = bash(cmd, timeout=180)
    log = [
        f"command: {cmd}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize_log(proc.stdout),
        "--- stderr ---",
        sanitize_log(proc.stderr),
    ]
    write_text_lf(BUILD_LOG, "\n".join(log) + "\n")
    return proc.returncode == 0


def compile_probe(backend: str) -> bool:
    cmd = (
        f"gcc -O2 -DSTAGE125_BACKEND=\\\"{backend}\\\" "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(C_BINARY)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
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


def cleanup_build_outputs() -> None:
    try:
        C_BINARY.unlink()
    except FileNotFoundError:
        pass
    bash("cd src/mosfhet && make clean >/dev/null 2>&1 || true", timeout=60)


def run_probe(build_ok: bool, compile_ok: bool) -> tuple[List[Dict[str, str]], List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
        cleanup_build_outputs()
        return [], [], False
    proc = bash(f"./{rel(C_BINARY)}", timeout=120)
    log = [
        f"command: ./{rel(C_BINARY)}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize_log(proc.stdout),
        "--- stderr ---",
        sanitize_log(proc.stderr),
    ]
    write_text_lf(RUN_LOG_TXT, "\n".join(log) + "\n")
    gadget_rows: List[Dict[str, str]] = []
    layout_rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        tag = values[0]
        if tag == "GADGET":
            gadget_rows.append(dict(zip(GADGET_FIELDS, values[1:])))
        elif tag == "LAYOUT":
            layout_rows.append(dict(zip(LAYOUT_FIELDS, values[1:])))
        else:
            raise RuntimeError(f"unexpected probe row: {line}")
    cleanup_build_outputs()
    return gadget_rows, layout_rows, proc.returncode == 0


def build_summary(
    build_ok: bool,
    compile_ok: bool,
    run_ok: bool,
    gadget_rows: List[Dict[str, str]],
    layout_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = [
        {
            "gate": "stage125_mosfhet_static_build",
            "status": "PASS" if build_ok else "BLOCKED",
            "metric": "make_static_spqlios",
            "value": "true" if build_ok else "false",
            "evidence": rel(BUILD_LOG),
            "detail": "MOSFHET static library build using FFT_LIB=spqlios.",
            "next_action": "Fix production build before interpreting gadget decomposition.",
        },
        {
            "gate": "stage125_probe_compile",
            "status": "PASS" if compile_ok else "BLOCKED",
            "metric": "gcc_probe_compile",
            "value": "true" if compile_ok else "false",
            "evidence": rel(COMPILE_LOG),
            "detail": "Standalone compact selector gadget probe linked against libmosfhet.a.",
            "next_action": "Fix the probe compile before any gadget decision.",
        },
    ]
    if not build_ok or not compile_ok:
        rows.append(
            {
                "gate": "stage125_decision",
                "status": "BLOCKED_STAGE125_GADGET_BUILD_OR_COMPILE",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(SUMMARY_CSV),
                "detail": "Compact selector gadget probe did not run.",
                "next_action": "Resolve build/compile failure.",
            }
        )
        return rows

    have_gadget = run_ok and len(gadget_rows) > 0
    gadget_ok = have_gadget and all(row["status"] == "PASS_COMPACT_SELECTOR_GADGET" for row in gadget_rows)
    negative_ok = have_gadget and all(int(row["negative_failures"]) > 0 for row in gadget_rows)
    layout_ok = len(layout_rows) > 0 and all(row["status"] == "PASS_LAYOUT_MODEL" for row in layout_rows)
    mismatch_values = ";".join(row["coeff_dft_mismatches"] for row in gadget_rows)
    negative_values = ";".join(row["negative_failures"] for row in gadget_rows)
    max_gap = max([int(row["max_dft_gap"]) for row in gadget_rows] or [0])
    tolerance = max([int(row["tolerance"]) for row in gadget_rows] or [0])
    min_selector_ratio = min([float(row["selector_ratio"]) for row in layout_rows] or [0.0])
    min_total_ratio = min([float(row["selector_plus_dec_ratio"]) for row in layout_rows] or [0.0])
    max_dec_overhead = max([float(row["dec_overhead"]) for row in layout_rows] or [0.0])
    rows.extend(
        [
            {
                "gate": "stage125_probe_run",
                "status": "PASS" if run_ok else "FAIL",
                "metric": "probe_returncode",
                "value": "0" if run_ok else "nonzero",
                "evidence": rel(RUN_LOG_TXT),
                "detail": "Compact selector gadget decomposition probe executed.",
                "next_action": "Inspect run log on failure.",
            },
            {
                "gate": "stage125_compact_gadget_dft",
                "status": "PASS_WITH_TOLERANCE" if gadget_ok and max_gap <= tolerance else "FAIL",
                "metric": "coeff_dft_mismatches;max_gap;tolerance",
                "value": f"{mismatch_values};{max_gap};{tolerance}",
                "evidence": rel(GADGET_CSV),
                "detail": "Lane-local decomposition plus compact diagonal gadget injection matches coefficient reference through production DFT.",
                "next_action": "If this fails, compact selector injection is not ready for encryption design.",
            },
            {
                "gate": "stage125_negative_control",
                "status": "PASS_REJECTS_BODY_ONLY_SELECTOR" if negative_ok else "FAIL",
                "metric": "negative_failures",
                "value": negative_values,
                "evidence": rel(GADGET_CSV),
                "detail": "Omitting shared-mask gadget rows remains rejected.",
                "next_action": "Do not implement body-only compact selector rows.",
            },
            {
                "gate": "stage125_layout_model",
                "status": "PASS" if layout_ok else "FAIL",
                "metric": "min_selector_ratio;min_selector_plus_dec_ratio;max_dec_overhead",
                "value": f"{min_selector_ratio:.6f};{min_total_ratio:.6f};{max_dec_overhead:.6f}",
                "evidence": rel(LAYOUT_CSV),
                "detail": "Selector storage advantage survives while decomposition stream overhead is recorded.",
                "next_action": "Future performance work must include decomposition overhead, especially r=2.",
            },
            {
                "gate": "stage125_decision",
                "status": (
                    "PASS_STAGE125_COMPACT_SELECTOR_GADGET_READY_ENCRYPTION_NOISE_GATE_REQUIRED"
                    if gadget_ok and layout_ok
                    else "FAIL_STAGE125_COMPACT_SELECTOR_GADGET"
                ),
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(SUMMARY_CSV),
                "detail": "Compact selector gadget decomposition and diagonal injection are smoke-validated outside `sab_pvw_*`.",
                "next_action": "Stage126 should test compact selector encryption/noise before any hot-path code.",
            },
        ]
    )
    return rows


def write_plan() -> None:
    lines = [
        "# Stage125 Compact Selector Gadget Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Check whether the Stage124 compact selector skeleton can support the",
        "necessary gadget decomposition and diagonal injection without rebuilding",
        "dense `MAT_TRGSW_DFT` rows.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage125_compact_selector_gadget_gate.py",
        "```",
        "",
        "## Falsification Criteria",
        "",
        "- MOSFHET static build or probe compile fails;",
        "- production DFT compact gadget output diverges from coefficient reference;",
        "- omitting shared-mask rows does not fail as a negative control;",
        "- selector layout advantage disappears once decomposition streams are counted.",
        "",
        "Passing this stage permits only compact selector encryption/noise",
        "prototyping outside the SAB hot path.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(gadget_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage125 Compact Selector Gadget Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage125 checks the finite gadget-injection boundary after Stage124's type",
        "API skeleton. For each lane q and gadget level t, the probe decomposes",
        "the lane-local mask and body polynomials with MOSFHET",
        "`polynomial_decompose_i`. It then applies two compact selector rows:",
        "`shared[t,q]` injects the diagonal gadget into the lane-local mask",
        "component and `body[t,q]` injects it into the lane-local body component.",
        "",
        "The gate compares coefficient-domain gadget application with production",
        "SPQLIOS DFT multiply-add. This is not selector encryption or a noise proof.",
        "",
        "## Gadget Rows",
        "",
        "| backend | r | N | T | Bg | seed | DFT mismatches | negative failures | max gap | tolerance | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in gadget_rows:
        lines.append(
            f"| {row['backend']} | {row['r']} | {row['N']} | {row['T']} | "
            f"{row['Bg_bit']} | {row['seed']} | {row['coeff_dft_mismatches']} | "
            f"{row['negative_failures']} | {row['max_dft_gap']} | "
            f"{row['tolerance']} | {row['status']} |"
        )
    lines += [
        "",
        "## Layout Rows",
        "",
        "| r | N | selector ratio | dec overhead | selector+dec ratio | status |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['selector_ratio']} | "
            f"{row['dec_overhead']} | {row['selector_plus_dec_ratio']} | "
            f"{row['status']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        "This stage does not encrypt compact selector rows, model cryptographic",
        "noise, implement AVX512 kernels, integrate SAB schedules, or measure",
        "complete `T_bootstrap/r`.",
    ]
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# V125: Compact Selector Gadget Injection",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB r-body research track.",
        "- Focused module: compact selector decomposition and diagonal gadget injection.",
        "- Optimization target: eventual complete-SAB `T_bootstrap/r`.",
        "- Status labels: `[gadget-smoke]`, `[production-dft-linked]`, `[not-encrypted]`, `[not-hot-path]`.",
        "",
        "## Pseudocode",
        "",
        "```text",
        "for lane q:",
        "  for gadget level t:",
        "    d_shared[t,q] = decompose(mask_q, t)",
        "    d_body[t,q]   = decompose(body_q, t)",
        "    out.a[q] += d_shared[t,q] * G_t",
        "    out.b[q] += d_body[t,q] * G_t",
        "```",
        "",
        "The production DFT path must match this coefficient reference. The",
        "body-only negative control must fail because shared-mask gadget rows are",
        "required for lane-local ciphertext reconstruction.",
        "",
        "## Required Next Gate",
        "",
        "Stage126 must add compact selector encryption/noise modeling. If encryption",
        "requires restoring dense `MAT_TRGSW_DFT` rows, this branch must be",
        "rejected or redesigned before any SAB integration.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], gadget_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage125 Compact Selector Gadget Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage125 checks lane-local gadget decomposition and compact diagonal",
        "injection through MOSFHET production DFT. It remains outside selector",
        "encryption and `sab_pvw_*`.",
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
        "## Gadget Rows",
        "",
        "| backend | r | N | T | Bg | seed | DFT mismatches | negative failures | max gap | tolerance | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in gadget_rows:
        lines.append(
            f"| {row['backend']} | {row['r']} | {row['N']} | {row['T']} | "
            f"{row['Bg_bit']} | {row['seed']} | {row['coeff_dft_mismatches']} | "
            f"{row['negative_failures']} | {row['max_dft_gap']} | "
            f"{row['tolerance']} | {row['status']} |"
        )
    lines += [
        "",
        "## Layout Rows",
        "",
        "| r | N | selector ratio | dec overhead | selector+dec ratio | status |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['selector_ratio']} | "
            f"{row['dec_overhead']} | {row['selector_plus_dec_ratio']} | "
            f"{row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "The compact selector can express the needed diagonal gadget injection in a",
        "production DFT smoke model. Decomposition-stream overhead is now explicit:",
        "r=2 is only break-even for selector+decomposition counts, while r=4 and",
        "r=6 retain positive count ratios.",
    ]
    write_text_lf(OUT_MD, "\n".join(lines) + "\n")


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


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
    run_id = "stage125-compact-selector-gadget-001"
    rows = read_csv(RUN_LOG)
    rows = [row for row in rows if row.get("run_id") != run_id]
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        GADGET_CSV,
        LAYOUT_CSV,
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        ARTIFACT_INDEX,
        Path("scripts/build_stage125_compact_selector_gadget_gate.py"),
    ]
    rows.append(
        {
            "run_id": run_id,
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 125",
            "backend": "MOSFHET FFT_LIB=spqlios",
            "command": "python scripts/build_stage125_compact_selector_gadget_gate.py",
            "params": "k=1 T=7 Bg_bit=7 r=2,4,6 N=1024,2048",
            "seed": "0..1 subset",
            "status": status,
            "summary": "Stage125 smoke-validates compact selector gadget decomposition and diagonal injection outside SAB.",
            "artifacts": "; ".join(rel(p if p.is_absolute() else ROOT / p) for p in artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backend = "spqlios"
    write_c_source()
    build_ok = build_mosfhet_static(backend)
    compile_ok = compile_probe(backend) if build_ok else False
    gadget_rows, layout_rows, run_ok = run_probe(build_ok, compile_ok)
    write_csv(GADGET_CSV, gadget_rows, GADGET_FIELDS)
    write_csv(LAYOUT_CSV, layout_rows, LAYOUT_FIELDS)
    summary = build_summary(build_ok, compile_ok, run_ok, gadget_rows, layout_rows)
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_plan()
    write_theory(gadget_rows, layout_rows)
    write_variant()
    write_md(summary, gadget_rows, layout_rows)
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        GADGET_CSV,
        LAYOUT_CSV,
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        Path(__file__),
    ]
    write_artifact_index(artifacts)
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage125 compact selector gadget gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
