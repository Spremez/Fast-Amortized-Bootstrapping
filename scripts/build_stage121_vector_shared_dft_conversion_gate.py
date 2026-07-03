#!/usr/bin/env python3
"""Build Stage121 vector-shared exact DFT/NTT conversion gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage121_vector_shared_dft_conversion_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
CONVERSION_CSV = OUT_DIR / "conversion_results.csv"
LAYOUT_CSV = OUT_DIR / "layout_results.csv"
COMPILE_LOG = OUT_DIR / "compile.log"
C_SOURCE = OUT_DIR / "vector_shared_dft_conversion_gate.c"
C_BINARY = OUT_DIR / "vector_shared_dft_conversion_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage121_vector_shared_dft_conversion_gate.md"
PLAN_MD = ROOT / "experiments" / "stage121_vector_shared_dft_conversion_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage121_vector_shared_dft_conversion_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_vector_shared_dft_conversion.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


CONVERSION_FIELDS = [
    "r",
    "N",
    "seed",
    "modulus",
    "root_status",
    "roundtrip_mismatches",
    "phase_mismatches",
    "noisy_phase_mismatches",
    "noise_bound_violations",
    "max_abs_phase_error",
    "max_abs_noisy_phase_error",
    "max_abs_noise",
    "max_noise_bound",
    "requested_bytes",
    "rss_kb",
    "status",
]

LAYOUT_FIELDS = [
    "r",
    "N",
    "dense_dft_polys",
    "vector_dft_polys",
    "vector_over_dense_dft_poly_ratio",
    "conversion_input_polys",
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
#define _POSIX_C_SOURCE 200809L
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

enum { MOD = 12289 };

typedef struct {
  size_t N;
  int64_t *coeffs;
} Poly;

typedef struct {
  size_t N;
  int64_t *evals;
} DftPoly;

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

static int64_t mod_norm(int64_t x) {
  int64_t v = x % MOD;
  if (v < 0) v += MOD;
  return v;
}

static int64_t mod_signed(int64_t x) {
  int64_t v = mod_norm(x);
  if (v > MOD / 2) v -= MOD;
  return v;
}

static int64_t mod_pow(int64_t a, int64_t e) {
  int64_t out = 1;
  int64_t base = mod_norm(a);
  while (e > 0) {
    if (e & 1) out = (out * base) % MOD;
    base = (base * base) % MOD;
    e >>= 1;
  }
  return out;
}

static int64_t mod_inv(int64_t x) {
  return mod_pow(x, MOD - 2);
}

static int64_t primitive_root_mod(void) {
  const int64_t factors[] = {2, 3};
  for (int64_t g = 2; g < MOD; g++) {
    int ok = 1;
    for (size_t i = 0; i < sizeof(factors) / sizeof(factors[0]); i++) {
      if (mod_pow(g, (MOD - 1) / factors[i]) == 1) {
        ok = 0;
        break;
      }
    }
    if (ok) return g;
  }
  return 0;
}

static int64_t negacyclic_root(size_t N, int *ok) {
  const int64_t g = primitive_root_mod();
  if (g == 0 || ((MOD - 1) % (int64_t)(2 * N)) != 0) {
    *ok = 0;
    return 0;
  }
  const int64_t psi = mod_pow(g, (MOD - 1) / (int64_t)(2 * N));
  *ok = (mod_pow(psi, (int64_t)N) == MOD - 1)
      && (mod_pow(psi, (int64_t)(2 * N)) == 1);
  return psi;
}

static int64_t small(uint64_t salt, uint64_t a, uint64_t b, uint64_t c) {
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0xbf58476d1ce4e5b9ULL) * 0x94d049bb133111ebULL;
  x ^= (b + 0x2545f4914f6cdd1dULL) * 0x9e3779b97f4a7c15ULL;
  x ^= (c + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 33;
  return (int64_t)(x % 7ULL) - 3;
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

static DftPoly alloc_dft(size_t N, size_t *bytes) {
  DftPoly p;
  p.N = N;
  p.evals = (int64_t *)xcalloc(N, sizeof(int64_t));
  *bytes += sizeof(int64_t) * N;
  return p;
}

static void free_poly(Poly *p) {
  free(p->coeffs);
  p->coeffs = NULL;
  p->N = 0;
}

static void free_dft(DftPoly *p) {
  free(p->evals);
  p->evals = NULL;
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

static void forward_dft(DftPoly *out, const Poly *in, int64_t psi) {
  const size_t N = in->N;
  for (size_t j = 0; j < N; j++) {
    const int64_t root = mod_pow(psi, (int64_t)(2 * j + 1));
    int64_t power = 1;
    int64_t acc = 0;
    for (size_t i = 0; i < N; i++) {
      acc = mod_norm(acc + mod_norm(in->coeffs[i]) * power);
      power = (power * root) % MOD;
    }
    out->evals[j] = acc;
  }
}

static void inverse_dft(Poly *out, const DftPoly *in, int64_t psi) {
  const size_t N = out->N;
  const int64_t n_inv = mod_inv((int64_t)N);
  for (size_t i = 0; i < N; i++) {
    int64_t acc = 0;
    for (size_t j = 0; j < N; j++) {
      const int64_t root = mod_pow(psi, (int64_t)(2 * j + 1));
      const int64_t inv_root = mod_inv(root);
      const int64_t factor = mod_pow(inv_root, (int64_t)i);
      acc = mod_norm(acc + in->evals[j] * factor);
    }
    out->coeffs[i] = mod_signed(acc * n_inv);
  }
}

static void dft_phase(DftPoly *out, const DftPoly *body, const DftPoly *mask,
    const DftPoly *secret) {
  for (size_t i = 0; i < out->N; i++) {
    out->evals[i] = mod_norm(body->evals[i] - mask->evals[i] * secret->evals[i]);
  }
}

static void fill_secret(VSObject *obj, size_t seed) {
  for (size_t lane = 0; lane < obj->r; lane++) {
    for (size_t i = 0; i < obj->N; i++) {
      obj->secret[lane].coeffs[i] = small(20 + seed, lane, i, 0) % 3;
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
    const int64_t e = with_noise ? noise(lane, i, noise_term, seed) : 0;
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

static uint64_t roundtrip_check(const Poly *p, int64_t psi, size_t *bytes) {
  DftPoly d = alloc_dft(p->N, bytes);
  Poly back = alloc_poly(p->N, bytes);
  uint64_t mismatches = 0;
  forward_dft(&d, p, psi);
  inverse_dft(&back, &d, psi);
  for (size_t i = 0; i < p->N; i++) {
    if (back.coeffs[i] != p->coeffs[i]) mismatches++;
  }
  free_dft(&d);
  free_poly(&back);
  return mismatches;
}

static uint64_t dft_decrypt_phase(Poly *out, const VSCipher *ct,
    const Poly *secret, int64_t psi, size_t *bytes) {
  DftPoly mask_d = alloc_dft(secret->N, bytes);
  DftPoly body_d = alloc_dft(secret->N, bytes);
  DftPoly secret_d = alloc_dft(secret->N, bytes);
  DftPoly phase_d = alloc_dft(secret->N, bytes);
  forward_dft(&mask_d, &ct->mask, psi);
  forward_dft(&body_d, &ct->body, psi);
  forward_dft(&secret_d, secret, psi);
  dft_phase(&phase_d, &body_d, &mask_d, &secret_d);
  inverse_dft(out, &phase_d, psi);
  free_dft(&mask_d);
  free_dft(&body_d);
  free_dft(&secret_d);
  free_dft(&phase_d);
  return 0;
}

static int run_case(size_t r, size_t N, size_t seed) {
  int root_ok = 0;
  const int64_t psi = negacyclic_root(N, &root_ok);
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

  size_t transient_bytes = 0;
  Poly phase_shared = alloc_poly(N, &transient_bytes);
  Poly phase_body = alloc_poly(N, &transient_bytes);
  Poly noisy_shared = alloc_poly(N, &transient_bytes);
  Poly noisy_body = alloc_poly(N, &transient_bytes);
  Poly dft_phase_shared = alloc_poly(N, &transient_bytes);
  Poly dft_phase_body = alloc_poly(N, &transient_bytes);
  Poly dft_noisy_shared = alloc_poly(N, &transient_bytes);
  Poly dft_noisy_body = alloc_poly(N, &transient_bytes);

  uint64_t roundtrip_mismatches = 0;
  uint64_t phase_mismatches = 0;
  uint64_t noisy_phase_mismatches = 0;
  uint64_t noise_violations = 0;
  int64_t max_phase_error = 0;
  int64_t max_noisy_phase_error = 0;
  int64_t max_noise = 0;
  int64_t max_bound = 0;

  if (root_ok) {
    for (size_t lane = 0; lane < r; lane++) {
      roundtrip_mismatches += roundtrip_check(&clean.secret[lane], psi, &transient_bytes);
      roundtrip_mismatches += roundtrip_check(&clean.shared[lane].mask, psi, &transient_bytes);
      roundtrip_mismatches += roundtrip_check(&clean.shared[lane].body, psi, &transient_bytes);
      roundtrip_mismatches += roundtrip_check(&clean.body[lane].mask, psi, &transient_bytes);
      roundtrip_mismatches += roundtrip_check(&clean.body[lane].body, psi, &transient_bytes);

      decrypt_phase(&phase_shared, &clean.shared[lane], &clean.secret[lane]);
      decrypt_phase(&phase_body, &clean.body[lane], &clean.secret[lane]);
      decrypt_phase(&noisy_shared, &noisy.shared[lane], &noisy.secret[lane]);
      decrypt_phase(&noisy_body, &noisy.body[lane], &noisy.secret[lane]);

      dft_decrypt_phase(&dft_phase_shared, &clean.shared[lane], &clean.secret[lane], psi, &transient_bytes);
      dft_decrypt_phase(&dft_phase_body, &clean.body[lane], &clean.secret[lane], psi, &transient_bytes);
      dft_decrypt_phase(&dft_noisy_shared, &noisy.shared[lane], &noisy.secret[lane], psi, &transient_bytes);
      dft_decrypt_phase(&dft_noisy_body, &noisy.body[lane], &noisy.secret[lane], psi, &transient_bytes);

      for (size_t i = 0; i < N; i++) {
        int64_t err_s = dft_phase_shared.coeffs[i] - phase_shared.coeffs[i];
        int64_t err_b = dft_phase_body.coeffs[i] - phase_body.coeffs[i];
        int64_t nerr_s = dft_noisy_shared.coeffs[i] - noisy_shared.coeffs[i];
        int64_t nerr_b = dft_noisy_body.coeffs[i] - noisy_body.coeffs[i];
        if (err_s < 0) err_s = -err_s;
        if (err_b < 0) err_b = -err_b;
        if (nerr_s < 0) nerr_s = -nerr_s;
        if (nerr_b < 0) nerr_b = -nerr_b;
        if (err_s != 0 || err_b != 0) phase_mismatches++;
        if (nerr_s != 0 || nerr_b != 0) noisy_phase_mismatches++;
        if (err_s > max_phase_error) max_phase_error = err_s;
        if (err_b > max_phase_error) max_phase_error = err_b;
        if (nerr_s > max_noisy_phase_error) max_noisy_phase_error = nerr_s;
        if (nerr_b > max_noisy_phase_error) max_noisy_phase_error = nerr_b;

        const int64_t ds = digit(51, lane, i, seed);
        const int64_t db = digit(61, lane, i, seed);
        const int64_t clean_combined = ds * phase_shared.coeffs[i] + db * phase_body.coeffs[i];
        const int64_t noisy_combined = ds * noisy_shared.coeffs[i] + db * noisy_body.coeffs[i];
        int64_t combined_noise = noisy_combined - clean_combined;
        if (combined_noise < 0) combined_noise = -combined_noise;
        int64_t bound = (ds < 0 ? -ds : ds) + (db < 0 ? -db : db);
        if (combined_noise > bound) noise_violations++;
        if (combined_noise > max_noise) max_noise = combined_noise;
        if (bound > max_bound) max_bound = bound;
      }
    }
  }

  const size_t requested = clean.requested_bytes + noisy.requested_bytes + transient_bytes;
  const long rss = rss_kb();
  const int ok = root_ok && roundtrip_mismatches == 0 && phase_mismatches == 0
      && noisy_phase_mismatches == 0 && noise_violations == 0;
  printf("CONVERT,%zu,%zu,%zu,%d,%s,%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRId64 ",%" PRId64 ",%" PRId64 ",%" PRId64
         ",%zu,%ld,%s\n",
      r, N, seed, MOD, root_ok ? "PASS_ROOT" : "FAIL_ROOT",
      roundtrip_mismatches, phase_mismatches, noisy_phase_mismatches,
      noise_violations, max_phase_error, max_noisy_phase_error, max_noise,
      max_bound, requested, rss, ok ? "PASS_DFT_CONVERSION" : "FAIL");

  free_poly(&phase_shared);
  free_poly(&phase_body);
  free_poly(&noisy_shared);
  free_poly(&noisy_body);
  free_poly(&dft_phase_shared);
  free_poly(&dft_phase_body);
  free_poly(&dft_noisy_shared);
  free_poly(&dft_noisy_body);
  free_object(&clean);
  free_object(&noisy);
  return ok ? 0 : 1;
}

static int layout_case(size_t r, size_t N) {
  VSObject obj = alloc_object(r, N);
  const uint64_t dense_dft_polys = (1 + (uint64_t)r) + (uint64_t)(r + 1) * (uint64_t)(r + 1);
  const uint64_t vector_dft_polys = 4 * (uint64_t)r;
  const uint64_t conversion_input_polys = 5 * (uint64_t)r;
  const double ratio = (double)vector_dft_polys / (double)dense_dft_polys;
  const int ok = vector_dft_polys <= dense_dft_polys && conversion_input_polys > vector_dft_polys;
  printf("LAYOUT,%zu,%zu,%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64
         ",%zu,%s\n",
      r, N, dense_dft_polys, vector_dft_polys, ratio,
      conversion_input_polys, obj.requested_bytes, ok ? "PASS_LAYOUT" : "FAIL");
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
            f"vector-shared DFT conversion probe failed\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    conversion_rows: List[Dict[str, str]] = []
    layout_rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        tag = values[0]
        if tag == "CONVERT":
            conversion_rows.append(dict(zip(CONVERSION_FIELDS, values[1:])))
        elif tag == "LAYOUT":
            layout_rows.append(dict(zip(LAYOUT_FIELDS, values[1:])))
        else:
            raise RuntimeError(f"unexpected probe row: {line}")
    return conversion_rows, layout_rows


def build_summary(
    compile_ok: bool,
    conversion_rows: List[Dict[str, str]],
    layout_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    if not compile_ok:
        return [
            {
                "gate": "stage121_compile",
                "status": "BLOCKED",
                "metric": "gcc_compile",
                "value": "false",
                "evidence": rel(COMPILE_LOG),
                "detail": "Generated exact DFT/NTT conversion probe did not compile.",
                "next_action": "Stop before conversion work.",
            },
            {
                "gate": "stage121_decision",
                "status": "BLOCKED_STAGE121_DFT_CONVERSION_COMPILER",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(COMPILE_LOG),
                "detail": "No conversion evidence is available.",
                "next_action": "Fix the standalone conversion prototype.",
            },
        ]

    convert_ok = all(row["status"] == "PASS_DFT_CONVERSION" for row in conversion_rows)
    layout_ok = all(row["status"] == "PASS_LAYOUT" for row in layout_rows)
    root_values = ";".join(row["root_status"] for row in conversion_rows)
    roundtrip_values = ";".join(row["roundtrip_mismatches"] for row in conversion_rows)
    phase_values = ";".join(row["phase_mismatches"] for row in conversion_rows)
    noisy_phase_values = ";".join(row["noisy_phase_mismatches"] for row in conversion_rows)
    noise_values = ";".join(row["noise_bound_violations"] for row in conversion_rows)
    max_noise = max(int(row["max_abs_noise"]) for row in conversion_rows)
    max_bound = max(int(row["max_noise_bound"]) for row in conversion_rows)
    r4_layout = next(row for row in layout_rows if row["r"] == "4" and row["N"] == "64")
    decision = (
        "PASS_STAGE121_VECTOR_SHARED_DFT_CONVERSION_READY_STRUCTURED_EP_PROTOTYPE_REQUIRED"
        if convert_ok and layout_ok and max_noise <= max_bound
        else "FAIL_STAGE121_VECTOR_SHARED_DFT_CONVERSION"
    )
    return [
        {
            "gate": "stage121_compile",
            "status": "PASS",
            "metric": "gcc_compile",
            "value": "true",
            "evidence": rel(COMPILE_LOG),
            "detail": "Generated exact negacyclic NTT/DFT C probe compiled under WSL gcc.",
            "next_action": "Use as standalone conversion evidence only.",
        },
        {
            "gate": "stage121_root_availability",
            "status": "PASS" if all(v == "PASS_ROOT" for v in root_values.split(";")) else "FAIL",
            "metric": "root_status",
            "value": root_values,
            "evidence": rel(CONVERSION_CSV),
            "detail": "Modulus 12289 supplies exact 2N-th roots for N=32 and N=64.",
            "next_action": "If this fails, select a new exact-transform modulus.",
        },
        {
            "gate": "stage121_roundtrip",
            "status": "PASS" if convert_ok else "FAIL",
            "metric": "roundtrip_mismatches",
            "value": roundtrip_values,
            "evidence": rel(CONVERSION_CSV),
            "detail": "Vector-shared mask/body/secret polynomials round-trip through exact DFT.",
            "next_action": "Do not proceed to external-product prototype on mismatch.",
        },
        {
            "gate": "stage121_phase_equivalence",
            "status": "PASS" if convert_ok else "FAIL",
            "metric": "phase_mismatches;noisy_phase_mismatches",
            "value": f"{phase_values}|{noisy_phase_values}",
            "evidence": rel(CONVERSION_CSV),
            "detail": "DFT-domain phase `B - A*S` matches coefficient-domain phase after inverse DFT.",
            "next_action": "If this fails, the vector-shared object cannot enter frequency-domain EP work.",
        },
        {
            "gate": "stage121_noise_bound",
            "status": "PASS_BOUNDED" if convert_ok and max_noise <= max_bound else "FAIL",
            "metric": "noise_bound_violations",
            "value": noise_values,
            "evidence": rel(CONVERSION_CSV),
            "detail": "Injected coefficient noise remains within the digit-sum bound after conversion.",
            "next_action": "Production torus/FFT noise remains a later MOSFHET gate.",
        },
        {
            "gate": "stage121_layout_allocation",
            "status": "PASS" if layout_ok else "FAIL",
            "metric": "r4_N64_vector_over_dense_dft_poly_ratio",
            "value": r4_layout["vector_over_dense_dft_poly_ratio"],
            "evidence": rel(LAYOUT_CSV),
            "detail": "DFT prototype preserves the vector-shared polynomial-count bound.",
            "next_action": "Next stage may prototype structured EP arithmetic outside `sab_pvw_*`.",
        },
        {
            "gate": "stage121_decision",
            "status": decision,
            "metric": "next_gate_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Exact conversion gate passes outside SAB.",
            "next_action": "Stage122 should prototype structured vector-shared external-product arithmetic outside `sab_pvw_*`.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage121 Vector-Shared DFT/Conversion Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Move the Stage120 vector-shared real struct prototype through a frequency",
        "domain conversion gate before any MOSFHET or SAB hot-path integration.",
        "The gate uses an exact modular negacyclic NTT/DFT over modulus 12289",
        "so conversion errors are semantic errors, not floating-point noise.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage121_vector_shared_dft_conversion_gate.py",
        "```",
        "",
        "## Falsification Criteria",
        "",
        "- no valid 2N-th root for N=32 or N=64;",
        "- any mask/body/secret round-trip mismatch;",
        "- any DFT-domain phase mismatch versus coefficient-domain phase;",
        "- any noisy phase mismatch or digit-sum noise-bound violation;",
        "- vector-shared DFT polynomial count exceeds dense reference count.",
        "",
        "Passing this stage permits only a structured external-product arithmetic",
        "prototype outside `sab_pvw_*`.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(
    conversion_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]
) -> None:
    lines = [
        "# Stage121 Vector-Shared DFT/Conversion Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage121 checks whether the vector-shared lane-local object from Stage120",
        "can cross a frequency-domain conversion boundary without changing its",
        "phase semantics. The prototype uses exact modular evaluation at the",
        "roots of `X^N + 1` modulo 12289. It is a semantic conversion gate,",
        "not a production SPQLIOS/AVX512 performance gate.",
        "",
        "For each lane q, coefficient-domain phase is",
        "",
        "```text",
        "phase_q = b_q - a_q * s_q mod (X^N + 1).",
        "```",
        "",
        "The conversion gate computes",
        "",
        "```text",
        "DFT(phase_q) = DFT(b_q) - DFT(a_q) * DFT(s_q),",
        "phase_q' = InvDFT(DFT(phase_q)).",
        "```",
        "",
        "The gate passes only when `phase_q' == phase_q` for clean and noisy",
        "shared/body objects across all tested r, N, and seeds.",
        "",
        "## Conversion Rows",
        "",
        "| r | N | seed | root | roundtrip | phase | noisy phase | noise violations | max noise | bound |",
        "|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in conversion_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['seed']} | {row['root_status']} | "
            f"{row['roundtrip_mismatches']} | {row['phase_mismatches']} | "
            f"{row['noisy_phase_mismatches']} | {row['noise_bound_violations']} | "
            f"{row['max_abs_noise']} | {row['max_noise_bound']} |"
        )
    lines += [
        "",
        "## Layout Rows",
        "",
        "| r | N | dense DFT polys | vector DFT polys | ratio | conversion input polys | requested bytes |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_dft_polys']} | "
            f"{row['vector_dft_polys']} | {row['vector_over_dense_dft_poly_ratio']} | "
            f"{row['conversion_input_polys']} | {row['requested_bytes']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        "This gate does not prove production FFT roundoff, torus scaling, gadget",
        "decomposition, AVX512 optimality, SAB schedule compatibility, or",
        "complete `T_bootstrap/r` acceleration. It only permits the next",
        "structured external-product arithmetic prototype.",
    ]
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# V121: Vector-Shared Exact DFT Conversion Prototype",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB r-body research track.",
        "- Focused module: vector-shared MAT-RLWE conversion boundary.",
        "- Optimization target: eventual complete-SAB `T_bootstrap/r`.",
        "- Status labels: `[conversion-prototype]`, `[phase-supported]`, `[not-production-fft]`, `[not-hot-path]`.",
        "- Main hypothesis: vector-shared lane-local objects can preserve phase after exact frequency-domain conversion.",
        "",
        "## Mathematical Definition",
        "",
        "For each lane q and ciphertext-like object `(a_q,b_q)`, define",
        "`A_q = DFT(a_q)`, `B_q = DFT(b_q)`, and `S_q = DFT(s_q)` over",
        "`Z_12289[X]/(X^N+1)`. The DFT-domain phase is",
        "`P_q = B_q - A_q*S_q`. The gate requires",
        "`InvDFT(P_q) = b_q - a_q*s_q` for clean and noisy objects.",
        "",
        "## Pseudocode",
        "",
        "```text",
        "Input: r, N, seed",
        "Output: exact conversion gate status",
        "1. Allocate the Stage120 vector-shared real struct object.",
        "2. Encrypt clean and bounded-noise shared/body objects.",
        "3. Find an exact 2N-th root modulo 12289.",
        "4. Round-trip every mask/body/secret polynomial through DFT and inverse DFT.",
        "5. Compute phase in coefficient domain and DFT domain.",
        "6. Compare clean/noisy phases and digit-sum noise bounds.",
        "7. Stop before structured external-product or SAB integration.",
        "```",
        "",
        "## Delta From Stage120",
        "",
        "| Stage120 | Stage121 | Status |",
        "| --- | --- | --- |",
        "| coefficient-domain phase only | exact DFT-domain phase and inverse conversion | implemented in repro prototype |",
        "| no transform round-trip | mask/body/secret DFT round-trip | gate required |",
        "| real struct layout bound | DFT polynomial-count layout bound | recorded |",
        "",
        "## Required Next Experiments",
        "",
        "- structured vector-shared external-product arithmetic prototype;",
        "- r=2/4/6 dense-reference equivalence for selector application;",
        "- production torus/FFT conversion smoke;",
        "- isolated MOSFHET-adjacent kernel only after the above pass.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(
    summary: List[Dict[str, str]],
    conversion_rows: List[Dict[str, str]],
    layout_rows: List[Dict[str, str]],
) -> None:
    lines = [
        "# Stage121 Vector-Shared DFT/Conversion Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage121 advances the vector-shared real struct route through an exact",
        "negacyclic NTT/DFT conversion gate. It remains outside `sab_pvw_*` and",
        "outside production MOSFHET FFT/AVX512 code.",
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
        "| r | N | dense DFT polys | vector DFT polys | ratio | conversion input polys | status |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_dft_polys']} | "
            f"{row['vector_dft_polys']} | {row['vector_over_dense_dft_poly_ratio']} | "
            f"{row['conversion_input_polys']} | {row['status']} |"
        )
    lines += [
        "",
        "## Conversion Rows",
        "",
        "| r | N | seed | root | roundtrip | phase | noisy phase | noise violations | rss KB | status |",
        "|---:|---:|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in conversion_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['seed']} | {row['root_status']} | "
            f"{row['roundtrip_mismatches']} | {row['phase_mismatches']} | "
            f"{row['noisy_phase_mismatches']} | {row['noise_bound_violations']} | "
            f"{row['rss_kb']} | {row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "This removes one necessary semantic blocker: the vector-shared object can",
        "be represented across an exact frequency-domain conversion boundary.",
        "It still does not prove production FFT behavior, structured selector",
        "application, SAB schedule integration, or complete-SAB speedup.",
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
        if row.get("run_id") != "stage121-vector-shared-dft-conversion-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(THEORY_MD),
        rel(VARIANT_MD),
        rel(SUMMARY_CSV),
        rel(CONVERSION_CSV),
        rel(LAYOUT_CSV),
        rel(COMPILE_LOG),
        rel(C_SOURCE),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "build_stage121_vector_shared_dft_conversion_gate.py"),
    ]
    rows.append(
        {
            "run_id": "stage121-vector-shared-dft-conversion-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 121",
            "backend": "WSL gcc exact modular NTT/DFT prototype",
            "command": "python scripts/build_stage121_vector_shared_dft_conversion_gate.py",
            "params": "vector-shared exact DFT r=2,4,6 N=32,64 seeds=0..4 modulus=12289",
            "seed": "0..4",
            "status": status,
            "summary": "Stage121 validates exact DFT conversion and DFT-domain phase for vector-shared objects outside SAB.",
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
    conversion_rows, layout_rows = run_probe(compile_ok)
    summary = build_summary(compile_ok, conversion_rows, layout_rows)
    write_csv(CONVERSION_CSV, conversion_rows, CONVERSION_FIELDS)
    write_csv(LAYOUT_CSV, layout_rows, LAYOUT_FIELDS)
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_theory(conversion_rows, layout_rows)
    write_md(summary, conversion_rows, layout_rows)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                THEORY_MD,
                VARIANT_MD,
                SUMMARY_CSV,
                CONVERSION_CSV,
                LAYOUT_CSV,
                COMPILE_LOG,
                C_SOURCE,
                ROOT / "scripts" / "build_stage121_vector_shared_dft_conversion_gate.py",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage121 vector-shared DFT/conversion gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") or status.startswith("BLOCKED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
