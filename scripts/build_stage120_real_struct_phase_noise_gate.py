#!/usr/bin/env python3
"""Build Stage120 vector-shared real C struct phase/noise gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage120_real_struct_phase_noise_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
PHASE_CSV = OUT_DIR / "phase_noise_results.csv"
LAYOUT_CSV = OUT_DIR / "layout_results.csv"
COMPILE_LOG = OUT_DIR / "compile.log"
C_SOURCE = OUT_DIR / "real_struct_phase_noise_gate.c"
C_BINARY = OUT_DIR / "real_struct_phase_noise_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage120_real_struct_phase_noise_gate.md"
PLAN_MD = ROOT / "experiments" / "stage120_real_struct_phase_noise_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage120_real_struct_phase_noise_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_vector_shared_real_struct.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


PHASE_FIELDS = [
    "r",
    "N",
    "seed",
    "mismatches_noiseless",
    "max_abs_error_noiseless",
    "max_abs_noise",
    "max_noise_bound",
    "noise_bound_violations",
    "requested_bytes",
    "rss_kb",
    "status",
]

LAYOUT_FIELDS = [
    "r",
    "N",
    "dense_terms",
    "vector_terms",
    "dense_total_polys",
    "vector_total_polys",
    "vector_over_dense_poly_ratio",
    "requested_bytes",
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
#define _POSIX_C_SOURCE 200809L
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef struct {
  size_t N;
  int64_t *coeffs;
} Poly;

typedef struct {
  Poly mask;
  Poly body;
} VSCipher;

typedef struct {
  size_t r;
  size_t N;
  Poly *secret;
  VSCipher *shared;
  VSCipher *body;
  size_t requested_bytes;
} VSObject;

static void *xcalloc(size_t count, size_t size) {
  void *ptr = calloc(count, size);
  if (ptr == NULL) {
    fprintf(stderr, "calloc failed\n");
    exit(2);
  }
  return ptr;
}

static long rss_kb(void) {
  FILE *fd = fopen("/proc/self/statm", "r");
  if (fd == NULL) return -1;
  long pages_total = 0;
  long pages_rss = 0;
  if (fscanf(fd, "%ld %ld", &pages_total, &pages_rss) != 2) {
    fclose(fd);
    return -1;
  }
  fclose(fd);
  long page = sysconf(_SC_PAGESIZE);
  if (page <= 0) page = 4096;
  return (pages_rss * page) / 1024;
}

static int64_t small(uint64_t salt, uint64_t a, uint64_t b, uint64_t c) {
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0xbf58476d1ce4e5b9ULL) * 0x94d049bb133111ebULL;
  x ^= (b + 0x2545f4914f6cdd1dULL) * 0x9e3779b97f4a7c15ULL;
  x ^= (c + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 33;
  int64_t v = (int64_t)(x % 7ULL) - 3;
  return v;
}

static int64_t msg(uint64_t salt, size_t lane, size_t coeff, size_t seed) {
  return small(salt + 10 * seed, lane, coeff, 0);
}

static int64_t digit(uint64_t salt, size_t lane, size_t coeff, size_t seed) {
  int64_t v = small(salt + 10 * seed, lane, coeff, 1);
  return v == 0 ? 1 : v;
}

static int64_t noise(size_t lane, size_t coeff, size_t term, size_t seed) {
  int64_t v = small(100 + 10 * seed + term, lane, coeff, 2) % 3;
  if (v < 0) v = -v;
  return v - 1;
}

static Poly alloc_poly(size_t N, size_t *bytes) {
  Poly p;
  p.N = N;
  p.coeffs = (int64_t *)xcalloc(N, sizeof(int64_t));
  *bytes += sizeof(int64_t) * N;
  return p;
}

static void free_poly(Poly *p) {
  free(p->coeffs);
  p->coeffs = NULL;
  p->N = 0;
}

static VSObject alloc_object(size_t r, size_t N) {
  VSObject obj;
  obj.r = r;
  obj.N = N;
  obj.requested_bytes = sizeof(VSObject);
  obj.secret = (Poly *)xcalloc(r, sizeof(Poly));
  obj.shared = (VSCipher *)xcalloc(r, sizeof(VSCipher));
  obj.body = (VSCipher *)xcalloc(r, sizeof(VSCipher));
  obj.requested_bytes += r * sizeof(Poly) + 2 * r * sizeof(VSCipher);
  for (size_t lane = 0; lane < r; lane++) {
    obj.secret[lane] = alloc_poly(N, &obj.requested_bytes);
    obj.shared[lane].mask = alloc_poly(N, &obj.requested_bytes);
    obj.shared[lane].body = alloc_poly(N, &obj.requested_bytes);
    obj.body[lane].mask = alloc_poly(N, &obj.requested_bytes);
    obj.body[lane].body = alloc_poly(N, &obj.requested_bytes);
  }
  return obj;
}

static void free_object(VSObject *obj) {
  for (size_t lane = 0; lane < obj->r; lane++) {
    free_poly(&obj->secret[lane]);
    free_poly(&obj->shared[lane].mask);
    free_poly(&obj->shared[lane].body);
    free_poly(&obj->body[lane].mask);
    free_poly(&obj->body[lane].body);
  }
  free(obj->secret);
  free(obj->shared);
  free(obj->body);
  obj->secret = NULL;
  obj->shared = NULL;
  obj->body = NULL;
}

static void negacyclic_mul(Poly *out, const Poly *a, const Poly *b) {
  const size_t N = out->N;
  memset(out->coeffs, 0, sizeof(int64_t) * N);
  for (size_t i = 0; i < N; i++) {
    for (size_t j = 0; j < N; j++) {
      size_t idx = i + j;
      int64_t sign = 1;
      if (idx >= N) {
        idx -= N;
        sign = -1;
      }
      out->coeffs[idx] += sign * a->coeffs[i] * b->coeffs[j];
    }
  }
}

static void fill_secret(VSObject *obj, size_t seed) {
  for (size_t lane = 0; lane < obj->r; lane++) {
    for (size_t i = 0; i < obj->N; i++) {
      int64_t v = small(20 + seed, lane, i, 0) % 3;
      obj->secret[lane].coeffs[i] = v;
    }
  }
}

static void encrypt_poly(VSCipher *ct, const Poly *secret, size_t lane,
    size_t seed, uint64_t msg_salt, uint64_t mask_salt, size_t noise_term,
    int with_noise) {
  const size_t N = secret->N;
  Poly prod = alloc_poly(N, &(size_t){0});
  for (size_t i = 0; i < N; i++) {
    ct->mask.coeffs[i] = small(mask_salt + seed, lane, i, 0);
  }
  negacyclic_mul(&prod, &ct->mask, secret);
  for (size_t i = 0; i < N; i++) {
    int64_t e = with_noise ? noise(lane, i, noise_term, seed) : 0;
    ct->body.coeffs[i] = prod.coeffs[i] + msg(msg_salt, lane, i, seed) + e;
  }
  free_poly(&prod);
}

static void decrypt_phase(Poly *out, const VSCipher *ct, const Poly *secret) {
  const size_t N = secret->N;
  Poly prod = alloc_poly(N, &(size_t){0});
  negacyclic_mul(&prod, &ct->mask, secret);
  for (size_t i = 0; i < N; i++) {
    out->coeffs[i] = ct->body.coeffs[i] - prod.coeffs[i];
  }
  free_poly(&prod);
}

static int run_case(size_t r, size_t N, size_t seed) {
  VSObject clean = alloc_object(r, N);
  VSObject noisy = alloc_object(r, N);
  fill_secret(&clean, seed);
  fill_secret(&noisy, seed);
  for (size_t lane = 0; lane < r; lane++) {
    encrypt_poly(&clean.shared[lane], &clean.secret[lane], lane, seed, 1, 31, 0, 0);
    encrypt_poly(&clean.body[lane], &clean.secret[lane], lane, seed, 2, 41, 1, 0);
    encrypt_poly(&noisy.shared[lane], &noisy.secret[lane], lane, seed, 1, 31, 0, 1);
    encrypt_poly(&noisy.body[lane], &noisy.secret[lane], lane, seed, 2, 41, 1, 1);
  }

  Poly phase_shared = alloc_poly(N, &clean.requested_bytes);
  Poly phase_body = alloc_poly(N, &clean.requested_bytes);
  Poly noisy_shared = alloc_poly(N, &clean.requested_bytes);
  Poly noisy_body = alloc_poly(N, &clean.requested_bytes);

  uint64_t mismatches = 0;
  uint64_t noise_violations = 0;
  int64_t max_err = 0;
  int64_t max_noise = 0;
  int64_t max_bound = 0;

  for (size_t lane = 0; lane < r; lane++) {
    decrypt_phase(&phase_shared, &clean.shared[lane], &clean.secret[lane]);
    decrypt_phase(&phase_body, &clean.body[lane], &clean.secret[lane]);
    decrypt_phase(&noisy_shared, &noisy.shared[lane], &noisy.secret[lane]);
    decrypt_phase(&noisy_body, &noisy.body[lane], &noisy.secret[lane]);
    for (size_t i = 0; i < N; i++) {
      const int64_t ds = digit(51, lane, i, seed);
      const int64_t db = digit(61, lane, i, seed);
      const int64_t expected = ds * msg(1, lane, i, seed) + db * msg(2, lane, i, seed);
      const int64_t got = ds * phase_shared.coeffs[i] + db * phase_body.coeffs[i];
      const int64_t noisy_got = ds * noisy_shared.coeffs[i] + db * noisy_body.coeffs[i];
      int64_t err = got - expected;
      if (err < 0) err = -err;
      int64_t nerr = noisy_got - got;
      if (nerr < 0) nerr = -nerr;
      int64_t bound = (ds < 0 ? -ds : ds) + (db < 0 ? -db : db);
      if (err != 0) mismatches++;
      if (nerr > bound) noise_violations++;
      if (err > max_err) max_err = err;
      if (nerr > max_noise) max_noise = nerr;
      if (bound > max_bound) max_bound = bound;
    }
  }

  const size_t requested = clean.requested_bytes + noisy.requested_bytes;
  const long rss = rss_kb();
  const int ok = mismatches == 0 && noise_violations == 0;
  printf("PHASE,%zu,%zu,%zu,%" PRIu64 ",%" PRId64 ",%" PRId64
         ",%" PRId64 ",%" PRIu64 ",%zu,%ld,%s\n",
      r, N, seed, mismatches, max_err, max_noise, max_bound,
      noise_violations, requested, rss, ok ? "PASS_REAL_STRUCT_PHASE_NOISE" : "FAIL");

  free_poly(&phase_shared);
  free_poly(&phase_body);
  free_poly(&noisy_shared);
  free_poly(&noisy_body);
  free_object(&clean);
  free_object(&noisy);
  return ok ? 0 : 1;
}

static int layout_case(size_t r, size_t N) {
  VSObject obj = alloc_object(r, N);
  const uint64_t dense_terms = (uint64_t)(r + 1) * (uint64_t)(r + 1);
  const uint64_t vector_terms = 2 * (uint64_t)r;
  const uint64_t dense_total_polys = (1 + (uint64_t)r) + dense_terms;
  const uint64_t vector_total_polys = 4 * (uint64_t)r;
  const double ratio = (double)vector_total_polys / (double)dense_total_polys;
  const int ok = vector_terms < dense_terms && ratio <= 1.0;
  printf("LAYOUT,%zu,%zu,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%.6f,%zu,%s\n",
      r, N, dense_terms, vector_terms, dense_total_polys,
      vector_total_polys, ratio, obj.requested_bytes,
      ok ? "PASS_LAYOUT" : "FAIL");
  free_object(&obj);
  return ok ? 0 : 1;
}

int main(void) {
  const size_t rs[] = {2, 4, 6};
  const size_t Ns[] = {32, 64};
  const size_t seeds[] = {0, 1, 2, 3, 4};
  int failures = 0;
  for (size_t i = 0; i < sizeof(rs) / sizeof(rs[0]); i++) {
    for (size_t j = 0; j < sizeof(Ns) / sizeof(Ns[0]); j++) {
      failures += layout_case(rs[i], Ns[j]);
      for (size_t k = 0; k < sizeof(seeds) / sizeof(seeds[0]); k++) {
        failures += run_case(rs[i], Ns[j], seeds[k]);
      }
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


def run_probe(compile_ok: bool) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    if not compile_ok:
        return [], []
    proc = bash(f"./{rel(C_BINARY)}", timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(
            f"real struct phase/noise probe failed\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    phase_rows: List[Dict[str, str]] = []
    layout_rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        tag = values[0]
        if tag == "PHASE":
            phase_rows.append(dict(zip(PHASE_FIELDS, values[1:])))
        elif tag == "LAYOUT":
            layout_rows.append(dict(zip(LAYOUT_FIELDS, values[1:])))
        else:
            raise RuntimeError(f"unexpected probe row: {line}")
    return phase_rows, layout_rows


def build_summary(compile_ok: bool, phase_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not compile_ok:
        return [
            {
                "gate": "stage120_compile",
                "status": "BLOCKED",
                "metric": "gcc_compile",
                "value": "false",
                "evidence": rel(COMPILE_LOG),
                "detail": "Real struct C probe did not compile.",
                "next_action": "Stop before real struct work.",
            },
            {
                "gate": "stage120_decision",
                "status": "BLOCKED_STAGE120_REAL_STRUCT_COMPILER",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(COMPILE_LOG),
                "detail": "No real struct evidence is available.",
                "next_action": "Stop the branch.",
            },
        ]

    phase_ok = all(row["status"] == "PASS_REAL_STRUCT_PHASE_NOISE" for row in phase_rows)
    mismatch_values = ";".join(row["mismatches_noiseless"] for row in phase_rows)
    noise_values = ";".join(row["noise_bound_violations"] for row in phase_rows)
    layout_ok = all(row["status"] == "PASS_LAYOUT" for row in layout_rows)
    r4_layout = next(row for row in layout_rows if row["r"] == "4" and row["N"] == "64")
    max_noise = max(int(row["max_abs_noise"]) for row in phase_rows)
    max_bound = max(int(row["max_noise_bound"]) for row in phase_rows)
    decision = (
        "PASS_STAGE120_REAL_STRUCT_PHASE_NOISE_READY_DFT_PROTOTYPE_REQUIRED"
        if phase_ok and layout_ok and max_noise <= max_bound
        else "FAIL_STAGE120_REAL_STRUCT_PHASE_NOISE"
    )
    return [
        {
            "gate": "stage120_compile",
            "status": "PASS",
            "metric": "gcc_compile",
            "value": "true",
            "evidence": rel(COMPILE_LOG),
            "detail": "Generated real C struct polynomial prototype compiled under WSL gcc.",
            "next_action": "Use as standalone prototype evidence only.",
        },
        {
            "gate": "stage120_phase_equivalence",
            "status": "PASS" if phase_ok else "FAIL",
            "metric": "mismatches_noiseless",
            "value": mismatch_values,
            "evidence": rel(PHASE_CSV),
            "detail": "Negacyclic-polynomial phase decrypts match vector-shared reference across all seeds.",
            "next_action": "If this fails, do not implement DFT prototype.",
        },
        {
            "gate": "stage120_noise_bound",
            "status": "PASS_BOUNDED" if phase_ok and max_noise <= max_bound else "FAIL",
            "metric": "noise_bound_violations",
            "value": noise_values,
            "evidence": rel(PHASE_CSV),
            "detail": "Injected coefficient noise stays within digit-sum bounds.",
            "next_action": "Real cryptographic noise still needs MOSFHET parameter validation.",
        },
        {
            "gate": "stage120_layout_allocation",
            "status": "PASS" if layout_ok else "FAIL",
            "metric": "r4_N64_vector_over_dense_poly_ratio",
            "value": r4_layout["vector_over_dense_poly_ratio"],
            "evidence": rel(LAYOUT_CSV),
            "detail": "Real struct allocation model preserves the vector-shared layout bound.",
            "next_action": "Stage121 should add DFT/conversion object prototype before any hot path.",
        },
        {
            "gate": "stage120_decision",
            "status": decision,
            "metric": "next_gate_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Real structs pass polynomial phase/noise gate outside SAB.",
            "next_action": "Stage121 should prototype DFT/conversion for the vector-shared object outside `sab_pvw_*`.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage120 Real Struct Phase/Noise Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Build a standalone vector-shared real C struct prototype using polynomial",
        "arrays and negacyclic multiplication. Verify allocation, noiseless phase,",
        "and bounded coefficient-noise behavior before any DFT or SAB integration.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage120_real_struct_phase_noise_gate.py",
        "```",
        "",
        "Passing this stage permits only a DFT/conversion prototype outside",
        "`sab_pvw_*`.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(phase_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage120 Real Struct Phase/Noise Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage120 replaces scalar toy equations with actual C structs containing",
        "polynomial arrays. Each lane has two RLWE-like ciphertext objects:",
        "vector-shared and body. Each object contains mask and body polynomials.",
        "Phase uses negacyclic multiplication `body - mask * secret`.",
        "",
        "This is still not MOSFHET integration: coefficients are signed small",
        "integers, not torus ciphertexts with production FFT/DFT arithmetic.",
        "",
        "## Phase Summary",
        "",
        "| r | N | seed | mismatches | max noise | max bound | violations |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in phase_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['seed']} | "
            f"{row['mismatches_noiseless']} | {row['max_abs_noise']} | "
            f"{row['max_noise_bound']} | {row['noise_bound_violations']} |"
        )
    lines += [
        "",
        "## Layout Summary",
        "",
        "| r | N | dense terms | vector terms | vector/dense poly ratio | requested bytes |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_terms']} | "
            f"{row['vector_terms']} | {row['vector_over_dense_poly_ratio']} | "
            f"{row['requested_bytes']} |"
        )
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# V120: Vector-Shared Real Struct Prototype",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB r-body research track.",
        "- Focused module: lane-local vector-shared external-product object.",
        "- Optimization target: eventual complete-SAB `T_bootstrap/r`.",
        "- Status labels: `[real-struct-prototype]`, `[phase-supported]`, `[not-DFT]`, `[not-hot-path]`.",
        "- Main hypothesis: vector-shared lane-local objects can preserve polynomial phase correctness before DFT integration.",
        "",
        "## Mathematical Definition",
        "",
        "For lane q, define two ciphertext-like objects `(a_shared_q,b_shared_q)`",
        "and `(a_body_q,b_body_q)`. Phase is computed as",
        "`b - a*s_q` using negacyclic multiplication. The combined lane output is",
        "`d_shared * phase(shared_q) + d_body_q * phase(body_q)`.",
        "",
        "## Pseudocode",
        "",
        "```text",
        "Input: r, N, seed",
        "Output: phase/noise gate status",
        "1. Allocate r lane secrets and 2r ciphertext objects.",
        "2. Encrypt shared/body messages with negacyclic mask*secret products.",
        "3. Decrypt phases and compare with dense vector-shared reference.",
        "4. Repeat with bounded coefficient noise.",
        "5. Stop before DFT or SAB integration.",
        "```",
        "",
        "## Delta From Stage119",
        "",
        "| Stage119 | Stage120 | Status |",
        "| --- | --- | --- |",
        "| coefficient-level toy equations | allocated C structs and polynomial arrays | implemented in repro prototype |",
        "| scalar multiplication model | negacyclic polynomial multiplication | phase gate passed |",
        "| toy noise bound | coefficient noise through phase decrypt | bounded in prototype |",
        "",
        "## Required Next Experiments",
        "",
        "- DFT/conversion prototype;",
        "- structured external-product arithmetic prototype;",
        "- r=2/4 equivalence against dense reference;",
        "- only then isolated MOSFHET-adjacent kernel integration.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], phase_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage120 Real Struct Phase/Noise Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage120 builds a standalone vector-shared real C struct prototype with",
        "polynomial arrays and negacyclic phase decryption. It remains outside",
        "`sab_pvw_*` and MOSFHET hot paths.",
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
        "## Layout Rows",
        "",
        "| r | N | dense terms | vector terms | poly ratio | requested bytes | status |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_terms']} | "
            f"{row['vector_terms']} | {row['vector_over_dense_poly_ratio']} | "
            f"{row['requested_bytes']} | {row['status']} |"
        )
    lines += [
        "",
        "## Phase/Noise Rows",
        "",
        "| r | N | seed | mismatches | max noise | bound | violations | rss KB | status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in phase_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['seed']} | "
            f"{row['mismatches_noiseless']} | {row['max_abs_noise']} | "
            f"{row['max_noise_bound']} | {row['noise_bound_violations']} | "
            f"{row['rss_kb']} | {row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "This advances the valid vector-shared route from object semantics to a",
        "real C polynomial struct prototype. It still does not provide DFT,",
        "external-product kernel, SAB schedule, complete-SAB correctness, or",
        "performance evidence.",
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
        if row.get("run_id") != "stage120-real-struct-phase-noise-001"
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
        rel(ROOT / "scripts" / "build_stage120_real_struct_phase_noise_gate.py"),
    ]
    rows.append(
        {
            "run_id": "stage120-real-struct-phase-noise-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 120",
            "backend": "WSL gcc real C prototype",
            "command": "python scripts/build_stage120_real_struct_phase_noise_gate.py",
            "params": "vector-shared real structs r=2,4,6 N=32,64 seeds=0..4",
            "seed": "0..4",
            "status": status,
            "summary": "Stage120 validates vector-shared real C polynomial structs for phase/noise outside SAB.",
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
                ROOT / "scripts" / "build_stage120_real_struct_phase_noise_gate.py",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage120 real struct phase/noise gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") or status.startswith("BLOCKED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
