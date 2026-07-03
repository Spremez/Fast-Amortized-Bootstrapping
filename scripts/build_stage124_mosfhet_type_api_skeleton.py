#!/usr/bin/env python3
"""Build Stage124 MOSFHET-adjacent vector-shared type/API skeleton gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT_DIR = ROOT / "repro" / "stage124_mosfhet_type_api_skeleton"
SUMMARY_CSV = OUT_DIR / "summary.csv"
API_CSV = OUT_DIR / "api_results.csv"
LAYOUT_CSV = OUT_DIR / "layout_results.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "mosfhet_type_api_skeleton.c"
C_BINARY = OUT_DIR / "mosfhet_type_api_skeleton"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage124_mosfhet_type_api_skeleton.md"
PLAN_MD = ROOT / "experiments" / "stage124_mosfhet_type_api_skeleton_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage124_mosfhet_type_api_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_vector_shared_type_api_skeleton.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


API_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "k",
    "component_failures",
    "metadata_failures",
    "selector_coverage_failures",
    "roundtrip_mismatches",
    "max_roundtrip_gap",
    "tolerance",
    "status",
]

LAYOUT_FIELDS = [
    "r",
    "N",
    "T",
    "k",
    "current_acc_polys",
    "vector_acc_polys",
    "acc_overhead",
    "current_selector_dft_polys",
    "vector_selector_dft_polys",
    "selector_ratio",
    "current_total_polys",
    "vector_total_polys",
    "total_ratio",
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

#ifndef STAGE124_BACKEND
#define STAGE124_BACKEND "unknown"
#endif

typedef enum {
  STAGE124_KIND_ACC = 0,
  STAGE124_KIND_SHARED = 1,
  STAGE124_KIND_BODY = 2
} Stage124Kind;

typedef struct _Stage124LaneTMLWE {
  TorusPolynomial *a;
  TorusPolynomial b;
  int k;
  int N;
  int lane;
  int gadget;
  Stage124Kind kind;
} *Stage124LaneTMLWE;

typedef struct _Stage124LaneTMLWE_DFT {
  DFT_Polynomial *a;
  DFT_Polynomial b;
  int k;
  int N;
  int lane;
  int gadget;
  Stage124Kind kind;
} *Stage124LaneTMLWE_DFT;

typedef struct _Stage124Accumulator {
  Stage124LaneTMLWE *lane;
  int k;
  int r;
  int N;
} *Stage124Accumulator;

typedef struct _Stage124Accumulator_DFT {
  Stage124LaneTMLWE_DFT *lane;
  int k;
  int r;
  int N;
} *Stage124Accumulator_DFT;

typedef struct _Stage124Selector_DFT {
  Stage124LaneTMLWE_DFT *shared;
  Stage124LaneTMLWE_DFT *body;
  int T;
  int Q;
  int k;
  int r;
  int N;
} *Stage124Selector_DFT;

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

static Torus small_torus(uint64_t salt, uint64_t lane, uint64_t comp,
    uint64_t idx) {
  return (Torus)(mix64(salt, lane, comp, idx) % 17ULL);
}

static uint64_t abs_gap(Torus a, Torus b) {
  const uint64_t d = (uint64_t)(a - b);
  if (d <= (1ULL << 63)) return d;
  return (~d) + 1ULL;
}

static Stage124LaneTMLWE lane_alloc(int k, int N, int lane, int gadget,
    Stage124Kind kind) {
  Stage124LaneTMLWE out = (Stage124LaneTMLWE)safe_malloc(sizeof(*out));
  out->a = (TorusPolynomial *)safe_malloc(sizeof(TorusPolynomial) * k);
  for (int i = 0; i < k; i++) out->a[i] = polynomial_new_torus_polynomial(N);
  out->b = polynomial_new_torus_polynomial(N);
  out->k = k;
  out->N = N;
  out->lane = lane;
  out->gadget = gadget;
  out->kind = kind;
  return out;
}

static Stage124LaneTMLWE_DFT lane_dft_alloc(int k, int N, int lane, int gadget,
    Stage124Kind kind) {
  Stage124LaneTMLWE_DFT out =
      (Stage124LaneTMLWE_DFT)safe_malloc(sizeof(*out));
  out->a = (DFT_Polynomial *)safe_malloc(sizeof(DFT_Polynomial) * k);
  for (int i = 0; i < k; i++) out->a[i] = polynomial_new_DFT_polynomial(N);
  out->b = polynomial_new_DFT_polynomial(N);
  out->k = k;
  out->N = N;
  out->lane = lane;
  out->gadget = gadget;
  out->kind = kind;
  return out;
}

static void lane_free(Stage124LaneTMLWE in) {
  if (in == NULL) return;
  for (int i = 0; i < in->k; i++) free_polynomial(in->a[i]);
  free(in->a);
  free_polynomial(in->b);
  free(in);
}

static void lane_dft_free(Stage124LaneTMLWE_DFT in) {
  if (in == NULL) return;
  for (int i = 0; i < in->k; i++) free_DFT_polynomial(in->a[i]);
  free(in->a);
  free_DFT_polynomial(in->b);
  free(in);
}

static Stage124Accumulator acc_alloc(int k, int r, int N) {
  Stage124Accumulator out = (Stage124Accumulator)safe_malloc(sizeof(*out));
  out->lane = (Stage124LaneTMLWE *)safe_malloc(sizeof(Stage124LaneTMLWE) * r);
  for (int q = 0; q < r; q++) out->lane[q] = lane_alloc(k, N, q, -1, STAGE124_KIND_ACC);
  out->k = k;
  out->r = r;
  out->N = N;
  return out;
}

static Stage124Accumulator_DFT acc_dft_alloc(int k, int r, int N) {
  Stage124Accumulator_DFT out =
      (Stage124Accumulator_DFT)safe_malloc(sizeof(*out));
  out->lane = (Stage124LaneTMLWE_DFT *)safe_malloc(sizeof(Stage124LaneTMLWE_DFT) * r);
  for (int q = 0; q < r; q++) out->lane[q] = lane_dft_alloc(k, N, q, -1, STAGE124_KIND_ACC);
  out->k = k;
  out->r = r;
  out->N = N;
  return out;
}

static void acc_free(Stage124Accumulator in) {
  if (in == NULL) return;
  for (int q = 0; q < in->r; q++) lane_free(in->lane[q]);
  free(in->lane);
  free(in);
}

static void acc_dft_free(Stage124Accumulator_DFT in) {
  if (in == NULL) return;
  for (int q = 0; q < in->r; q++) lane_dft_free(in->lane[q]);
  free(in->lane);
  free(in);
}

static Stage124Selector_DFT selector_dft_alloc(int T, int Q, int k, int r,
    int N) {
  Stage124Selector_DFT out =
      (Stage124Selector_DFT)safe_malloc(sizeof(*out));
  const int rows = T * r;
  out->shared = (Stage124LaneTMLWE_DFT *)safe_malloc(sizeof(Stage124LaneTMLWE_DFT) * rows);
  out->body = (Stage124LaneTMLWE_DFT *)safe_malloc(sizeof(Stage124LaneTMLWE_DFT) * rows);
  for (int t = 0; t < T; t++) {
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      out->shared[idx] = lane_dft_alloc(k, N, q, t, STAGE124_KIND_SHARED);
      out->body[idx] = lane_dft_alloc(k, N, q, t, STAGE124_KIND_BODY);
    }
  }
  out->T = T;
  out->Q = Q;
  out->k = k;
  out->r = r;
  out->N = N;
  return out;
}

static Stage124LaneTMLWE_DFT selector_shared(Stage124Selector_DFT in, int t,
    int q) {
  return in->shared[t * in->r + q];
}

static Stage124LaneTMLWE_DFT selector_body(Stage124Selector_DFT in, int t,
    int q) {
  return in->body[t * in->r + q];
}

static void selector_dft_free(Stage124Selector_DFT in) {
  if (in == NULL) return;
  const int rows = in->T * in->r;
  for (int i = 0; i < rows; i++) {
    lane_dft_free(in->shared[i]);
    lane_dft_free(in->body[i]);
  }
  free(in->shared);
  free(in->body);
  free(in);
}

static void lane_fill(Stage124LaneTMLWE in, uint64_t salt) {
  for (int j = 0; j < in->k; j++) {
    for (int i = 0; i < in->N; i++) {
      in->a[j]->coeffs[i] = small_torus(salt, (uint64_t)in->lane,
          (uint64_t)(10 + j), (uint64_t)i);
    }
  }
  for (int i = 0; i < in->N; i++) {
    in->b->coeffs[i] = small_torus(salt, (uint64_t)in->lane, 100, (uint64_t)i);
  }
}

static void acc_to_dft(Stage124Accumulator_DFT out, Stage124Accumulator in) {
  for (int q = 0; q < in->r; q++) {
    for (int j = 0; j < in->k; j++) {
      polynomial_torus_to_DFT(out->lane[q]->a[j], in->lane[q]->a[j]);
    }
    polynomial_torus_to_DFT(out->lane[q]->b, in->lane[q]->b);
  }
}

static void acc_from_dft(Stage124Accumulator out, Stage124Accumulator_DFT in) {
  for (int q = 0; q < in->r; q++) {
    for (int j = 0; j < in->k; j++) {
      polynomial_DFT_to_torus(out->lane[q]->a[j], in->lane[q]->a[j]);
    }
    polynomial_DFT_to_torus(out->lane[q]->b, in->lane[q]->b);
  }
}

static void compare_acc(Stage124Accumulator a, Stage124Accumulator b,
    uint64_t tol, uint64_t *mismatches, uint64_t *max_gap) {
  for (int q = 0; q < a->r; q++) {
    for (int j = 0; j < a->k; j++) {
      for (int i = 0; i < a->N; i++) {
        const uint64_t gap = abs_gap(a->lane[q]->a[j]->coeffs[i],
            b->lane[q]->a[j]->coeffs[i]);
        if (gap > tol) (*mismatches)++;
        if (gap > *max_gap) *max_gap = gap;
      }
    }
    for (int i = 0; i < a->N; i++) {
      const uint64_t gap = abs_gap(a->lane[q]->b->coeffs[i],
          b->lane[q]->b->coeffs[i]);
      if (gap > tol) (*mismatches)++;
      if (gap > *max_gap) *max_gap = gap;
    }
  }
}

static int collect_acc_ptrs(Stage124Accumulator acc, void **ptrs, int offset) {
  int n = offset;
  for (int q = 0; q < acc->r; q++) {
    for (int j = 0; j < acc->k; j++) ptrs[n++] = acc->lane[q]->a[j]->coeffs;
    ptrs[n++] = acc->lane[q]->b->coeffs;
  }
  return n;
}

static int collect_selector_ptrs(Stage124Selector_DFT sel, void **ptrs,
    int offset) {
  int n = offset;
  for (int t = 0; t < sel->T; t++) {
    for (int q = 0; q < sel->r; q++) {
      Stage124LaneTMLWE_DFT rows[2] = {
        selector_shared(sel, t, q),
        selector_body(sel, t, q)
      };
      for (int x = 0; x < 2; x++) {
        for (int j = 0; j < rows[x]->k; j++) ptrs[n++] = rows[x]->a[j]->coeffs;
        ptrs[n++] = rows[x]->b->coeffs;
      }
    }
  }
  return n;
}

static uint64_t pointer_failures(void **ptrs, int count) {
  uint64_t failures = 0;
  for (int i = 0; i < count; i++) {
    if (ptrs[i] == NULL) failures++;
    for (int j = i + 1; j < count; j++) {
      if (ptrs[i] == ptrs[j]) failures++;
    }
  }
  return failures;
}

static uint64_t selector_coverage_failures(Stage124Selector_DFT sel) {
  uint64_t failures = 0;
  for (int t = 0; t < sel->T; t++) {
    for (int q = 0; q < sel->r; q++) {
      Stage124LaneTMLWE_DFT s = selector_shared(sel, t, q);
      Stage124LaneTMLWE_DFT b = selector_body(sel, t, q);
      if (s->lane != q || s->gadget != t || s->kind != STAGE124_KIND_SHARED) failures++;
      if (b->lane != q || b->gadget != t || b->kind != STAGE124_KIND_BODY) failures++;
    }
  }
  return failures;
}

static uint64_t metadata_failures(Stage124Accumulator acc,
    Stage124Accumulator_DFT acc_dft, Stage124Selector_DFT sel, int k, int r,
    int N, int T) {
  uint64_t failures = 0;
  if (acc->k != k || acc->r != r || acc->N != N) failures++;
  if (acc_dft->k != k || acc_dft->r != r || acc_dft->N != N) failures++;
  if (sel->k != k || sel->r != r || sel->N != N || sel->T != T) failures++;
  for (int q = 0; q < r; q++) {
    if (acc->lane[q]->lane != q || acc->lane[q]->kind != STAGE124_KIND_ACC) failures++;
    if (acc_dft->lane[q]->lane != q || acc_dft->lane[q]->kind != STAGE124_KIND_ACC) failures++;
  }
  return failures;
}

static void run_case(int r, int N, int T, int k) {
  const int Q = 7;
  const uint64_t tol = 1024;
  const uint64_t current_acc = (uint64_t)(k + r);
  const uint64_t vector_acc = (uint64_t)r * (uint64_t)(k + 1);
  const uint64_t current_sel = (uint64_t)T * (uint64_t)(k + r) * (uint64_t)(k + r);
  const uint64_t vector_sel = 2ULL * (uint64_t)T * (uint64_t)r * (uint64_t)(k + 1);
  const uint64_t current_total = current_acc + current_sel;
  const uint64_t vector_total = vector_acc + vector_sel;

  Stage124Accumulator acc = acc_alloc(k, r, N);
  Stage124Accumulator_DFT acc_dft = acc_dft_alloc(k, r, N);
  Stage124Accumulator roundtrip = acc_alloc(k, r, N);
  Stage124Selector_DFT selector = selector_dft_alloc(T, Q, k, r, N);

  for (int q = 0; q < r; q++) lane_fill(acc->lane[q], 1234 + (uint64_t)N);
  acc_to_dft(acc_dft, acc);
  acc_from_dft(roundtrip, acc_dft);

  uint64_t mismatches = 0;
  uint64_t max_gap = 0;
  compare_acc(acc, roundtrip, tol, &mismatches, &max_gap);

  const int ptr_cap = (int)(2 * vector_acc + vector_sel + 16);
  void **ptrs = (void **)safe_malloc(sizeof(void *) * ptr_cap);
  int ptr_count = 0;
  ptr_count = collect_acc_ptrs(acc, ptrs, ptr_count);
  ptr_count = collect_acc_ptrs(roundtrip, ptrs, ptr_count);
  ptr_count = collect_selector_ptrs(selector, ptrs, ptr_count);
  const uint64_t component_failures = pointer_failures(ptrs, ptr_count);
  free(ptrs);

  const uint64_t meta_failures =
      metadata_failures(acc, acc_dft, selector, k, r, N, T);
  const uint64_t coverage_failures = selector_coverage_failures(selector);
  const int api_ok = component_failures == 0 && meta_failures == 0
      && coverage_failures == 0 && mismatches == 0;

  const double acc_overhead = (double)vector_acc / (double)current_acc;
  const double selector_ratio = (double)current_sel / (double)vector_sel;
  const double total_ratio = (double)current_total / (double)vector_total;
  const int layout_ok = selector_ratio > 1.0 && total_ratio > 1.0;

  printf("API,%s,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%s\n",
      STAGE124_BACKEND, r, N, T, k, component_failures, meta_failures,
      coverage_failures, mismatches, max_gap, tol,
      api_ok ? "PASS_TYPE_API_SKELETON" : "FAIL");

  printf("LAYOUT,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64
         ",%" PRIu64 ",%.6f,%" PRIu64 ",%" PRIu64 ",%.6f,%s\n",
      r, N, T, k, current_acc, vector_acc, acc_overhead, current_sel,
      vector_sel, selector_ratio, current_total, vector_total, total_ratio,
      layout_ok ? "PASS_LAYOUT_MODEL" : "FAIL");

  selector_dft_free(selector);
  acc_free(roundtrip);
  acc_dft_free(acc_dft);
  acc_free(acc);
}

int main(void) {
  const int k = 1;
  const int T = 7;
  run_case(2, 1024, T, k);
  run_case(4, 1024, T, k);
  run_case(6, 1024, T, k);
  run_case(2, 2048, T, k);
  run_case(4, 2048, T, k);
  run_case(6, 2048, T, k);
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
        f"gcc -O2 -DSTAGE124_BACKEND=\\\"{backend}\\\" "
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
    api_rows: List[Dict[str, str]] = []
    layout_rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        tag = values[0]
        if tag == "API":
            api_rows.append(dict(zip(API_FIELDS, values[1:])))
        elif tag == "LAYOUT":
            layout_rows.append(dict(zip(LAYOUT_FIELDS, values[1:])))
        else:
            raise RuntimeError(f"unexpected probe row: {line}")
    cleanup_build_outputs()
    return api_rows, layout_rows, proc.returncode == 0


def build_summary(
    build_ok: bool,
    compile_ok: bool,
    run_ok: bool,
    api_rows: List[Dict[str, str]],
    layout_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = [
        {
            "gate": "stage124_mosfhet_static_build",
            "status": "PASS" if build_ok else "BLOCKED",
            "metric": "make_static_spqlios",
            "value": "true" if build_ok else "false",
            "evidence": rel(BUILD_LOG),
            "detail": "MOSFHET static library build using FFT_LIB=spqlios.",
            "next_action": "Fix production build before interpreting the type/API skeleton.",
        },
        {
            "gate": "stage124_probe_compile",
            "status": "PASS" if compile_ok else "BLOCKED",
            "metric": "gcc_probe_compile",
            "value": "true" if compile_ok else "false",
            "evidence": rel(COMPILE_LOG),
            "detail": "Standalone type/API skeleton probe linked against libmosfhet.a.",
            "next_action": "Fix the skeleton compile before any API decision.",
        },
    ]
    if not build_ok or not compile_ok:
        rows.append(
            {
                "gate": "stage124_decision",
                "status": "BLOCKED_STAGE124_TYPE_API_BUILD_OR_COMPILE",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(SUMMARY_CSV),
                "detail": "Type/API skeleton did not run.",
                "next_action": "Resolve build/compile failure.",
            }
        )
        return rows

    have_api = run_ok and len(api_rows) > 0
    api_ok = have_api and all(row["status"] == "PASS_TYPE_API_SKELETON" for row in api_rows)
    layout_ok = len(layout_rows) > 0 and all(row["status"] == "PASS_LAYOUT_MODEL" for row in layout_rows)
    component_values = ";".join(row["component_failures"] for row in api_rows)
    metadata_values = ";".join(row["metadata_failures"] for row in api_rows)
    coverage_values = ";".join(row["selector_coverage_failures"] for row in api_rows)
    roundtrip_values = ";".join(row["roundtrip_mismatches"] for row in api_rows)
    max_gap = max([int(row["max_roundtrip_gap"]) for row in api_rows] or [0])
    tolerance = max([int(row["tolerance"]) for row in api_rows] or [0])
    min_selector_ratio = min([float(row["selector_ratio"]) for row in layout_rows] or [0.0])
    min_total_ratio = min([float(row["total_ratio"]) for row in layout_rows] or [0.0])
    max_acc_overhead = max([float(row["acc_overhead"]) for row in layout_rows] or [0.0])
    rows.extend(
        [
            {
                "gate": "stage124_probe_run",
                "status": "PASS" if run_ok else "FAIL",
                "metric": "probe_returncode",
                "value": "0" if run_ok else "nonzero",
                "evidence": rel(RUN_LOG_TXT),
                "detail": "Standalone MOSFHET-adjacent type/API skeleton probe executed.",
                "next_action": "Inspect run log on failure.",
            },
            {
                "gate": "stage124_component_ownership",
                "status": "PASS" if api_ok else "FAIL",
                "metric": "component_failures",
                "value": component_values,
                "evidence": rel(API_CSV),
                "detail": "All allocated torus/DFT polynomial coefficient buffers are non-null and non-aliased inside the skeleton scope.",
                "next_action": "Fix ownership before any gadget decomposition work.",
            },
            {
                "gate": "stage124_metadata_and_lane_coverage",
                "status": "PASS" if api_ok else "FAIL",
                "metric": "metadata_failures;selector_coverage_failures",
                "value": f"{metadata_values};{coverage_values}",
                "evidence": rel(API_CSV),
                "detail": "Accumulator, DFT accumulator, and selector rows preserve k/r/N/T metadata and lane-local shared/body indexing.",
                "next_action": "Fix lane coverage before defining selector encryption.",
            },
            {
                "gate": "stage124_acc_dft_roundtrip",
                "status": "PASS_WITH_TOLERANCE" if api_ok and max_gap <= tolerance else "FAIL",
                "metric": "roundtrip_mismatches;max_gap;tolerance",
                "value": f"{roundtrip_values};{max_gap};{tolerance}",
                "evidence": rel(API_CSV),
                "detail": "Vector-shared accumulator torus->DFT->torus lifecycle survives production MOSFHET conversion.",
                "next_action": "If this fails, do not design gadget decomposition on top of this type skeleton.",
            },
            {
                "gate": "stage124_layout_model",
                "status": "PASS" if layout_ok else "FAIL",
                "metric": "min_selector_ratio;min_total_ratio;max_acc_overhead",
                "value": f"{min_selector_ratio:.6f};{min_total_ratio:.6f};{max_acc_overhead:.6f}",
                "evidence": rel(LAYOUT_CSV),
                "detail": "Compact selector DFT storage beats current dense selector and total accumulator+selector polynomial count despite accumulator overhead.",
                "next_action": "Gadget decomposition must preserve this compact selector layout.",
            },
            {
                "gate": "stage124_decision",
                "status": (
                    "PASS_STAGE124_MOSFHET_TYPE_API_SKELETON_READY_GADGET_DECOMPOSITION_GATE_REQUIRED"
                    if api_ok and layout_ok
                    else "FAIL_STAGE124_MOSFHET_TYPE_API_SKELETON"
                ),
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(SUMMARY_CSV),
                "detail": "MOSFHET-adjacent vector-shared type/API skeleton is compile-checked outside `sab_pvw_*`.",
                "next_action": "Stage125 should define and test gadget decomposition/selector injection for the compact selector.",
            },
        ]
    )
    return rows


def write_plan() -> None:
    lines = [
        "# Stage124 MOSFHET Type/API Skeleton Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Convert the Stage123 production FFT smoke result into a compile-checked",
        "MOSFHET-adjacent type/API skeleton for vector-shared lane-local",
        "accumulators and compact selectors. This remains outside `sab_pvw_*`.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage124_mosfhet_type_api_skeleton.py",
        "```",
        "",
        "## Falsification Criteria",
        "",
        "- MOSFHET cannot build with `FFT_LIB=spqlios`;",
        "- the standalone skeleton cannot link against production MOSFHET symbols;",
        "- allocated polynomial buffers are null or aliased;",
        "- lane metadata or selector shared/body coverage is wrong;",
        "- accumulator torus->DFT->torus conversion exceeds tolerance;",
        "- compact selector layout loses the Stage119/122 storage advantage.",
        "",
        "Passing this stage permits only gadget-decomposition/selector-injection",
        "prototyping outside the SAB hot path.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(api_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage124 MOSFHET Type/API Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage124 defines the first MOSFHET-adjacent type/API skeleton for the",
        "vector-shared route selected by Stage119 and exercised arithmetically by",
        "Stage122/123. The skeleton deliberately does not modify MOSFHET headers or",
        "the SAB hot path.",
        "",
        "For k=1, the current PVW accumulator stores `k+r = 1+r` polynomials.",
        "The vector-shared accumulator stores one lane-local mask/body ciphertext",
        "per lane, or `r(k+1) = 2r` polynomials. This is an accumulator overhead.",
        "The selector side is where the structured route must win: current dense",
        "`MAT_TRGSW_DFT` storage is `T(k+r)^2`, while the compact vector-shared",
        "selector skeleton stores `2Tr(k+1)` DFT polynomials.",
        "",
        "## API Rows",
        "",
        "| backend | r | N | T | k | component failures | metadata failures | coverage failures | roundtrip mismatches | max gap | tolerance | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in api_rows:
        lines.append(
            f"| {row['backend']} | {row['r']} | {row['N']} | {row['T']} | "
            f"{row['k']} | {row['component_failures']} | {row['metadata_failures']} | "
            f"{row['selector_coverage_failures']} | {row['roundtrip_mismatches']} | "
            f"{row['max_roundtrip_gap']} | {row['tolerance']} | {row['status']} |"
        )
    lines += [
        "",
        "## Layout Rows",
        "",
        "| r | N | T | current acc | vector acc | acc overhead | current selector | vector selector | selector ratio | current total | vector total | total ratio |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['T']} | "
            f"{row['current_acc_polys']} | {row['vector_acc_polys']} | "
            f"{row['acc_overhead']} | {row['current_selector_dft_polys']} | "
            f"{row['vector_selector_dft_polys']} | {row['selector_ratio']} | "
            f"{row['current_total_polys']} | {row['vector_total_polys']} | "
            f"{row['total_ratio']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        "This stage is a type/API skeleton gate. It does not prove selector",
        "encryption, gadget decomposition, noise growth, AVX512 performance, SAB",
        "schedule compatibility, extraction/key switching, or complete",
        "`T_bootstrap/r` acceleration.",
    ]
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# V124: MOSFHET-Adjacent Vector-Shared Type/API Skeleton",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB r-body research track.",
        "- Focused module: vector-shared accumulator and compact selector type/API boundary.",
        "- Optimization target: eventual complete-SAB `T_bootstrap/r`.",
        "- Status labels: `[type-api-skeleton]`, `[production-fft-linked]`, `[not-gadget]`, `[not-hot-path]`.",
        "- Main hypothesis: the Stage119/122 vector-shared object route can be expressed as MOSFHET-style allocation, DFT lifecycle, and lane-indexed selector accessors without losing the count advantage.",
        "",
        "## Type Shape",
        "",
        "```text",
        "Stage124LaneTMLWE      = lane-local mask a[0..k-1] plus body b",
        "Stage124Accumulator   = r lane-local Stage124LaneTMLWE objects",
        "Stage124Selector_DFT  = shared[t,q] and body[t,q] lane-local DFT objects",
        "```",
        "",
        "For k=1, accumulator polynomials grow from `1+r` to `2r`, while selector",
        "DFT polynomials shrink from `T(1+r)^2` to `4Tr`.",
        "",
        "## Required Next Gate",
        "",
        "Stage125 must define the compact selector gadget decomposition and",
        "diagonal injection semantics. If decomposition requires reconstructing",
        "dense `MAT_TRGSW_DFT` rows, this branch must be rejected or redesigned.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], api_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage124 MOSFHET Type/API Skeleton",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage124 compiles and runs a standalone MOSFHET-adjacent skeleton for",
        "vector-shared lane-local accumulators and compact selector DFT rows. It",
        "does not modify production MOSFHET headers or `sab_pvw_*`.",
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
        "## API Rows",
        "",
        "| backend | r | N | T | k | component failures | metadata failures | coverage failures | roundtrip mismatches | max gap | tolerance | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in api_rows:
        lines.append(
            f"| {row['backend']} | {row['r']} | {row['N']} | {row['T']} | "
            f"{row['k']} | {row['component_failures']} | {row['metadata_failures']} | "
            f"{row['selector_coverage_failures']} | {row['roundtrip_mismatches']} | "
            f"{row['max_roundtrip_gap']} | {row['tolerance']} | {row['status']} |"
        )
    lines += [
        "",
        "## Layout Rows",
        "",
        "| r | N | T | current acc | vector acc | acc overhead | current selector | vector selector | selector ratio | current total | vector total | total ratio | status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['T']} | "
            f"{row['current_acc_polys']} | {row['vector_acc_polys']} | "
            f"{row['acc_overhead']} | {row['current_selector_dft_polys']} | "
            f"{row['vector_selector_dft_polys']} | {row['selector_ratio']} | "
            f"{row['current_total_polys']} | {row['vector_total_polys']} | "
            f"{row['total_ratio']} | {row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "The skeleton preserves MOSFHET allocation and production DFT lifecycle",
        "while keeping lane-local selector coverage explicit. It opens only the",
        "next gadget-decomposition gate; it is not complete-SAB acceleration",
        "evidence.",
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
    run_id = "stage124-mosfhet-type-api-skeleton-001"
    rows = read_csv(RUN_LOG)
    rows = [row for row in rows if row.get("run_id") != run_id]
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        API_CSV,
        LAYOUT_CSV,
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        ARTIFACT_INDEX,
        Path("scripts/build_stage124_mosfhet_type_api_skeleton.py"),
    ]
    rows.append(
        {
            "run_id": run_id,
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 124",
            "backend": "MOSFHET FFT_LIB=spqlios",
            "command": "python scripts/build_stage124_mosfhet_type_api_skeleton.py",
            "params": "k=1 T=7 r=2,4,6 N=1024,2048",
            "seed": "deterministic fill",
            "status": status,
            "summary": "Stage124 compile-checks MOSFHET-adjacent vector-shared type/API skeleton outside SAB.",
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
    api_rows, layout_rows, run_ok = run_probe(build_ok, compile_ok)
    write_csv(API_CSV, api_rows, API_FIELDS)
    write_csv(LAYOUT_CSV, layout_rows, LAYOUT_FIELDS)
    summary = build_summary(build_ok, compile_ok, run_ok, api_rows, layout_rows)
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_plan()
    write_theory(api_rows, layout_rows)
    write_variant()
    write_md(summary, api_rows, layout_rows)
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        API_CSV,
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
    print(f"Stage124 MOSFHET type/API skeleton: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
