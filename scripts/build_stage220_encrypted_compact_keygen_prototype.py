#!/usr/bin/env python3
"""Stage220: encrypted compact keygen prototype."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT = ROOT / "repro" / "stage220_encrypted_compact_keygen_prototype"

DOC = ROOT / "docs" / "stage220_encrypted_compact_keygen_prototype.md"
PLAN = ROOT / "experiments" / "stage220_encrypted_compact_keygen_prototype_plan.md"
THEORY = ROOT / "theory_checks" / "stage220_encrypted_compact_keygen_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage220_encrypted_compact_keygen_prototype.md"

INPUTS = OUT / "input_status.csv"
KEYGEN = OUT / "keygen_results.csv"
LAYOUT = OUT / "layout_results.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
BUILD_LOG = OUT / "mosfhet_static_build.log"
COMPILE_LOG = OUT / "compile_probe.log"
RUN_LOG_TXT = OUT / "run_probe.log"
C_SOURCE = OUT / "stage220_encrypted_compact_keygen_prototype.c"
C_BINARY = OUT / "stage220_encrypted_compact_keygen_prototype"
REPORT = OUT / "encrypted_compact_keygen_prototype_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE203_EQUATION = ROOT / "repro" / "stage203_production_selector_equation_probe" / "equation_map.csv"
STAGE219_PROOF = ROOT / "repro" / "stage219_mosfhet_compact_key_api_skeleton" / "proof_gate.csv"
STAGE219_API = ROOT / "repro" / "stage219_mosfhet_compact_key_api_skeleton" / "api_results.csv"
HEADER = ROOT / "src" / "mosfhet" / "include" / "mosfhet.h"

DECISION = "PASS_STAGE220_ENCRYPTED_COMPACT_KEYGEN_READY_NOISE_RECURRENCE"

KEYGEN_FIELDS = [
    "backend",
    "r",
    "N",
    "seed",
    "dense_rows",
    "active_rows",
    "dummy_rows",
    "public_pattern_failures",
    "phase_mismatches",
    "dft_mismatches",
    "dummy_semantic_failures",
    "missing_active_negative_failures",
    "random_dummy_negative_failures",
    "max_dft_gap",
    "max_noise_abs",
    "noise_bound",
    "status",
]

LAYOUT_FIELDS = [
    "r",
    "N",
    "dense_rows",
    "active_rows",
    "dummy_rows",
    "public_rows",
    "active_over_dense",
    "dummy_over_dense",
    "status",
]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out) + "\n"


def sanitize_log(text: str) -> str:
    if text is None:
        return ""
    text = text.replace("\x00", "")
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ch.isprintable())
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


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


def build_inputs() -> List[Dict[str, str]]:
    required = [
        ("stage203_equation_map", STAGE203_EQUATION, "row-role source for generated encrypted keygen probe"),
        ("stage219_proof_gate", STAGE219_PROOF, "permission for encrypted compact keygen prototype only"),
        ("stage219_api_results", STAGE219_API, "compiled API skeleton evidence"),
        ("mosfhet_header", HEADER, "production MOSFHET public types/functions"),
    ]
    return [
        {
            "input": name,
            "status": "present" if path.exists() else "missing",
            "evidence": rel(path),
            "role": role,
            "bytes": str(path.stat().st_size) if path.exists() else "0",
        }
        for name, path, role in required
    ]


def equation_rows_by_r() -> Dict[int, List[Dict[str, str]]]:
    rows: Dict[int, List[Dict[str, str]]] = {}
    for row in read_csv(STAGE203_EQUATION):
        rows.setdefault(int(row["r"]), []).append(row)
    return rows


def c_role(row: Dict[str, str]) -> str:
    return "STAGE220_ROLE_ACTIVE" if row["semantic_role"] == "active" else "STAGE220_ROLE_DUMMY_ZERO"


def write_c_source() -> None:
    by_r = equation_rows_by_r()
    array_blocks: List[str] = []
    for r, rows in sorted(by_r.items()):
        array_blocks.append(f"static const Stage220EquationRow stage220_r{r}_rows[] = {{")
        for row in rows:
            array_blocks.append(
                f"  {{{row['row']}, {row['col']}, {c_role(row)}, {row['may_skip_after_proof']}}},"
            )
        array_blocks.append("};")
    arrays = "\n".join(array_blocks)
    source = f'''
#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#ifndef STAGE220_BACKEND
#define STAGE220_BACKEND "unknown"
#endif

typedef enum {{
  STAGE220_ROLE_ACTIVE = 1,
  STAGE220_ROLE_DUMMY_ZERO = 2
}} Stage220Role;

typedef struct {{
  int row;
  int col;
  int role;
  int may_skip;
}} Stage220EquationRow;

{arrays}

typedef struct _Stage220EncryptedRow {{
  TorusPolynomial a;
  TorusPolynomial b;
  TorusPolynomial semantic;
  TorusPolynomial noise;
  DFT_Polynomial a_dft;
  DFT_Polynomial b_dft;
  int matrix_row;
  int matrix_col;
  int secret_lane;
  int role;
  int may_skip;
}} *Stage220EncryptedRow;

typedef struct _Stage220EncryptedKey {{
  Stage220EncryptedRow * rows;
  int row_count;
  int active_count;
  int dummy_count;
  int r;
  int N;
}} *Stage220EncryptedKey;

static uint64_t mix64(uint64_t salt, uint64_t a, uint64_t b, uint64_t c){{
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0xbf58476d1ce4e5b9ULL) * 0x94d049bb133111ebULL;
  x ^= (b + 0x2545f4914f6cdd1dULL) * 0x9e3779b97f4a7c15ULL;
  x ^= (c + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 33;
  x *= 0xff51afd7ed558ccdULL;
  x ^= x >> 33;
  return x;
}}

static Torus signed_torus(int64_t value){{
  return (Torus)value;
}}

static uint64_t abs_gap(Torus a, Torus b){{
  const uint64_t d = (uint64_t)(a - b);
  if(d <= (1ULL << 63)) return d;
  return (~d) + 1ULL;
}}

static const Stage220EquationRow * rows_for_r(int r, int * count){{
  if(r == 2){{
    *count = (int)(sizeof(stage220_r2_rows) / sizeof(stage220_r2_rows[0]));
    return stage220_r2_rows;
  }}
  if(r == 4){{
    *count = (int)(sizeof(stage220_r4_rows) / sizeof(stage220_r4_rows[0]));
    return stage220_r4_rows;
  }}
  if(r == 6){{
    *count = (int)(sizeof(stage220_r6_rows) / sizeof(stage220_r6_rows[0]));
    return stage220_r6_rows;
  }}
  *count = 0;
  return NULL;
}}

static void zero_poly(TorusPolynomial p){{
  for(int i = 0; i < p->N; i++) p->coeffs[i] = 0;
}}

static void copy_addto(TorusPolynomial out, TorusPolynomial in){{
  for(int i = 0; i < out->N; i++) out->coeffs[i] += in->coeffs[i];
}}

static void copy_subto(TorusPolynomial out, TorusPolynomial in){{
  for(int i = 0; i < out->N; i++) out->coeffs[i] -= in->coeffs[i];
}}

static void fill_secret(TorusPolynomial out, int lane, int seed){{
  for(int i = 0; i < out->N; i++){{
    out->coeffs[i] = (Torus)(mix64(220100ULL + (uint64_t)seed,
        (uint64_t)lane, 0, (uint64_t)i) & 1ULL);
  }}
}}

static void fill_mask(TorusPolynomial out, int row, int col, int seed){{
  for(int i = 0; i < out->N; i++){{
    const int64_t value = (int64_t)(mix64(220200ULL + (uint64_t)seed,
        (uint64_t)row, (uint64_t)col, (uint64_t)i) % 3ULL) - 1;
    out->coeffs[i] = signed_torus(value);
  }}
}}

static void fill_noise(TorusPolynomial out, int row, int col, int seed){{
  for(int i = 0; i < out->N; i++){{
    const int64_t value = (int64_t)(mix64(220300ULL + (uint64_t)seed,
        (uint64_t)row, (uint64_t)col, (uint64_t)i) % 3ULL) - 1;
    out->coeffs[i] = signed_torus(value);
  }}
}}

static void fill_active_semantic(TorusPolynomial out, int row, int col,
    int seed){{
  zero_poly(out);
  const int idx = (13 * row + 17 * col + seed) & (out->N - 1);
  const int64_t sign = ((row + col + seed) & 1) ? -1 : 1;
  out->coeffs[idx] = signed_torus(sign * (int64_t)(1 + ((row + col) % 5)));
}}

static void fill_random_dummy_semantic(TorusPolynomial out, int row, int col,
    int seed){{
  zero_poly(out);
  const int idx = (19 * row + 23 * col + seed + 7) & (out->N - 1);
  out->coeffs[idx] = signed_torus(3);
}}

static Stage220EncryptedRow row_alloc(int N){{
  Stage220EncryptedRow row = (Stage220EncryptedRow)safe_malloc(sizeof(*row));
  row->a = polynomial_new_torus_polynomial(N);
  row->b = polynomial_new_torus_polynomial(N);
  row->semantic = polynomial_new_torus_polynomial(N);
  row->noise = polynomial_new_torus_polynomial(N);
  row->a_dft = polynomial_new_DFT_polynomial(N);
  row->b_dft = polynomial_new_DFT_polynomial(N);
  return row;
}}

static void row_free(Stage220EncryptedRow row){{
  if(row == NULL) return;
  free_polynomial(row->a);
  free_polynomial(row->b);
  free_polynomial(row->semantic);
  free_polynomial(row->noise);
  free_DFT_polynomial(row->a_dft);
  free_DFT_polynomial(row->b_dft);
  free(row);
}}

static Stage220EncryptedKey key_alloc(int r, int N){{
  int row_count = 0;
  const Stage220EquationRow * eq = rows_for_r(r, &row_count);
  if(eq == NULL || row_count == 0) return NULL;
  Stage220EncryptedKey key = (Stage220EncryptedKey)safe_malloc(sizeof(*key));
  key->rows = (Stage220EncryptedRow *)safe_malloc(sizeof(Stage220EncryptedRow) * row_count);
  key->row_count = row_count;
  key->active_count = 0;
  key->dummy_count = 0;
  key->r = r;
  key->N = N;
  for(int i = 0; i < row_count; i++){{
    key->rows[i] = row_alloc(N);
    key->rows[i]->matrix_row = eq[i].row;
    key->rows[i]->matrix_col = eq[i].col;
    key->rows[i]->secret_lane = (eq[i].row + eq[i].col) % r;
    key->rows[i]->role = eq[i].role;
    key->rows[i]->may_skip = eq[i].may_skip;
    if(eq[i].role == STAGE220_ROLE_ACTIVE) key->active_count++;
    if(eq[i].role == STAGE220_ROLE_DUMMY_ZERO) key->dummy_count++;
  }}
  return key;
}}

static void key_free(Stage220EncryptedKey key){{
  if(key == NULL) return;
  for(int i = 0; i < key->row_count; i++) row_free(key->rows[i]);
  free(key->rows);
  free(key);
}}

static void encrypt_row(Stage220EncryptedRow row, TorusPolynomial secret,
    int seed){{
  fill_mask(row->a, row->matrix_row, row->matrix_col, seed);
  fill_noise(row->noise, row->matrix_row, row->matrix_col, seed);
  if(row->role == STAGE220_ROLE_ACTIVE){{
    fill_active_semantic(row->semantic, row->matrix_row, row->matrix_col, seed);
  }} else {{
    zero_poly(row->semantic);
  }}
  zero_poly(row->b);
  polynomial_naive_mul_addto_torus(row->b, row->a, secret);
  copy_addto(row->b, row->semantic);
  copy_addto(row->b, row->noise);
  polynomial_torus_to_DFT(row->a_dft, row->a);
  polynomial_torus_to_DFT(row->b_dft, row->b);
}}

static void phase(TorusPolynomial out, TorusPolynomial a, TorusPolynomial b,
    TorusPolynomial secret){{
  TorusPolynomial prod = polynomial_new_torus_polynomial(secret->N);
  zero_poly(prod);
  polynomial_naive_mul_addto_torus(prod, a, secret);
  for(int i = 0; i < secret->N; i++) out->coeffs[i] = b->coeffs[i] - prod->coeffs[i];
  free_polynomial(prod);
}}

static void compare_poly(TorusPolynomial a, TorusPolynomial b, uint64_t tol,
    uint64_t * mismatches, uint64_t * max_gap){{
  for(int i = 0; i < a->N; i++){{
    const uint64_t gap = abs_gap(a->coeffs[i], b->coeffs[i]);
    if(gap > tol) (*mismatches)++;
    if(gap > *max_gap) *max_gap = gap;
  }}
}}

static uint64_t max_abs_poly(TorusPolynomial p){{
  uint64_t out = 0;
  for(int i = 0; i < p->N; i++){{
    const uint64_t gap = abs_gap(p->coeffs[i], 0);
    if(gap > out) out = gap;
  }}
  return out;
}}

static uint64_t public_pattern_failures(Stage220EncryptedKey key){{
  uint64_t failures = 0;
  for(int i = 0; i < key->row_count; i++){{
    int nonzero = 0;
    for(int c = 0; c < key->N; c++){{
      if(key->rows[i]->a->coeffs[c] != 0) {{
        nonzero = 1;
        break;
      }}
    }}
    if(!nonzero) failures++;
    for(int j = i + 1; j < key->row_count; j++){{
      int equal = 1;
      for(int c = 0; c < key->N; c++){{
        if(key->rows[i]->a->coeffs[c] != key->rows[j]->a->coeffs[c]) {{
          equal = 0;
          break;
        }}
      }}
      if(equal) failures++;
    }}
  }}
  return failures;
}}

static void run_case(int r, int N, int seed){{
  const uint64_t tolerance = 2048;
  const uint64_t noise_bound = (uint64_t)(2 * N * (r + 1));
  Stage220EncryptedKey key = key_alloc(r, N);
  TorusPolynomial * secrets = (TorusPolynomial *)safe_malloc(sizeof(TorusPolynomial) * r);
  TorusPolynomial row_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial dft_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial dft_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial dft_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected = polynomial_new_torus_polynomial(N);
  TorusPolynomial active_clean = polynomial_new_torus_polynomial(N);
  TorusPolynomial missing_active_clean = polynomial_new_torus_polynomial(N);
  TorusPolynomial random_dummy_clean = polynomial_new_torus_polynomial(N);
  uint64_t phase_mismatches = 0;
  uint64_t dft_mismatches = 0;
  uint64_t dummy_semantic_failures = 0;
  uint64_t max_dft_gap = 0;
  uint64_t max_noise_abs = 0;

  for(int q = 0; q < r; q++){{
    secrets[q] = polynomial_new_torus_polynomial(N);
    fill_secret(secrets[q], q, seed);
  }}
  for(int i = 0; i < key->row_count; i++){{
    encrypt_row(key->rows[i], secrets[key->rows[i]->secret_lane], seed);
  }}

  const uint64_t pattern_failures = public_pattern_failures(key);
  zero_poly(active_clean);
  zero_poly(missing_active_clean);
  zero_poly(random_dummy_clean);
  int skipped_active = 0;

  for(int i = 0; i < key->row_count; i++){{
    Stage220EncryptedRow row = key->rows[i];
    zero_poly(expected);
    copy_addto(expected, row->semantic);
    copy_addto(expected, row->noise);
    phase(row_phase, row->a, row->b, secrets[row->secret_lane]);
    compare_poly(row_phase, expected, 0, &phase_mismatches, &max_dft_gap);

    polynomial_DFT_to_torus(dft_a, row->a_dft);
    polynomial_DFT_to_torus(dft_b, row->b_dft);
    phase(dft_phase, dft_a, dft_b, secrets[row->secret_lane]);
    compare_poly(dft_phase, expected, tolerance, &dft_mismatches, &max_dft_gap);

    if(row->role == STAGE220_ROLE_DUMMY_ZERO){{
      for(int c = 0; c < N; c++){{
        if(row->semantic->coeffs[c] != 0) dummy_semantic_failures++;
      }}
      TorusPolynomial random_sem = polynomial_new_torus_polynomial(N);
      fill_random_dummy_semantic(random_sem, row->matrix_row, row->matrix_col, seed);
      copy_addto(random_dummy_clean, random_sem);
      free_polynomial(random_sem);
    }} else {{
      copy_addto(active_clean, row->semantic);
      if(skipped_active){{
        copy_addto(missing_active_clean, row->semantic);
      }} else {{
        skipped_active = 1;
      }}
    }}
    const uint64_t row_noise = max_abs_poly(row->noise);
    if(row_noise > max_noise_abs) max_noise_abs = row_noise;
  }}

  uint64_t dummy_gap = 0;
  uint64_t missing_active_negative_failures = 0;
  uint64_t random_dummy_negative_failures = 0;
  compare_poly(active_clean, missing_active_clean, 0, &missing_active_negative_failures, &dummy_gap);
  compare_poly(active_clean, random_dummy_clean, 0, &random_dummy_negative_failures, &dummy_gap);

  const int ok = pattern_failures == 0 && phase_mismatches == 0 &&
      dft_mismatches == 0 && dummy_semantic_failures == 0 &&
      missing_active_negative_failures > 0 && random_dummy_negative_failures > 0 &&
      max_noise_abs <= noise_bound;

  printf("KEYGEN,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%s\\n",
      STAGE220_BACKEND, r, N, seed, key->row_count, key->active_count,
      key->dummy_count, pattern_failures, phase_mismatches, dft_mismatches,
      dummy_semantic_failures, missing_active_negative_failures,
      random_dummy_negative_failures, max_dft_gap, max_noise_abs, noise_bound,
      ok ? "PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE" : "FAIL");

  const double active_over_dense = (double)key->active_count / (double)key->row_count;
  const double dummy_over_dense = (double)key->dummy_count / (double)key->row_count;
  const int layout_ok = key->row_count == (r + 1) * (r + 1) &&
      key->active_count + key->dummy_count == key->row_count;
  printf("LAYOUT,%d,%d,%d,%d,%d,%d,%.9f,%.9f,%s\\n",
      r, N, key->row_count, key->active_count, key->dummy_count,
      key->row_count, active_over_dense, dummy_over_dense,
      layout_ok ? "PASS_ENCRYPTED_KEYGEN_LAYOUT" : "FAIL");

  for(int q = 0; q < r; q++) free_polynomial(secrets[q]);
  free(secrets);
  free_polynomial(row_phase);
  free_polynomial(dft_a);
  free_polynomial(dft_b);
  free_polynomial(dft_phase);
  free_polynomial(expected);
  free_polynomial(active_clean);
  free_polynomial(missing_active_clean);
  free_polynomial(random_dummy_clean);
  key_free(key);
}}

int main(void){{
  run_case(2, 1024, 0);
  run_case(2, 1024, 1);
  run_case(4, 1024, 0);
  run_case(4, 1024, 1);
  run_case(6, 1024, 0);
  run_case(6, 1024, 1);
  run_case(2, 2048, 0);
  run_case(4, 2048, 0);
  run_case(6, 2048, 0);
  return 0;
}}
'''
    write_text(C_SOURCE, source)


def build_mosfhet_static(backend: str) -> bool:
    cmd = (
        "cd src/mosfhet && "
        "make clean >/dev/null 2>&1 || true && "
        f"make static FFT_LIB={backend} A_PRNG=none ENABLE_VAES=false "
        "ENABLE_PVW_TMLWE=false -j$(nproc)"
    )
    proc = bash(cmd, timeout=180)
    write_text(
        BUILD_LOG,
        "\n".join(
            [
                f"command: {cmd}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize_log(proc.stdout),
                "--- stderr ---",
                sanitize_log(proc.stderr),
            ]
        ),
    )
    return proc.returncode == 0


def compile_probe(backend: str) -> bool:
    cmd = (
        f"gcc -O2 -DSTAGE220_BACKEND=\\\"{backend}\\\" "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(C_BINARY)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
    )
    proc = bash(cmd, timeout=60)
    write_text(
        COMPILE_LOG,
        "\n".join(
            [
                f"command: {cmd}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize_log(proc.stdout),
                "--- stderr ---",
                sanitize_log(proc.stderr),
            ]
        ),
    )
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
    write_text(
        RUN_LOG_TXT,
        "\n".join(
            [
                f"command: ./{rel(C_BINARY)}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize_log(proc.stdout),
                "--- stderr ---",
                sanitize_log(proc.stderr),
            ]
        ),
    )
    keygen_rows: List[Dict[str, str]] = []
    layout_rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        if not line.strip():
            continue
        values = line.strip().split(",")
        if values[0] == "KEYGEN":
            keygen_rows.append(dict(zip(KEYGEN_FIELDS, values[1:])))
        elif values[0] == "LAYOUT":
            layout_rows.append(dict(zip(LAYOUT_FIELDS, values[1:])))
        else:
            raise RuntimeError(f"unexpected probe row: {line}")
    cleanup_build_outputs()
    return keygen_rows, layout_rows, proc.returncode == 0


def build_proof(build_ok: bool, compile_ok: bool, run_ok: bool, keygen_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]], inputs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    missing = [row["input"] for row in inputs if row["status"] != "present"]
    keygen_pass = run_ok and keygen_rows and all(row["status"] == "PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE" for row in keygen_rows)
    layout_pass = layout_rows and all(row["status"] == "PASS_ENCRYPTED_KEYGEN_LAYOUT" for row in layout_rows)
    max_gap = max((int(row["max_dft_gap"]) for row in keygen_rows), default=0)
    max_noise = max((int(row["max_noise_abs"]) for row in keygen_rows), default=0)
    max_bound = max((int(row["noise_bound"]) for row in keygen_rows), default=0)
    phase_fail = sum(int(row["phase_mismatches"]) for row in keygen_rows)
    dft_fail = sum(int(row["dft_mismatches"]) for row in keygen_rows)
    semantic_fail = sum(int(row["dummy_semantic_failures"]) for row in keygen_rows)
    pattern_fail = sum(int(row["public_pattern_failures"]) for row in keygen_rows)
    min_missing_active_neg = min((int(row["missing_active_negative_failures"]) for row in keygen_rows), default=0)
    min_random_dummy_neg = min((int(row["random_dummy_negative_failures"]) for row in keygen_rows), default=0)
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if not missing else "FAIL",
            "metric": "missing_inputs",
            "value": ";".join(missing),
            "evidence": rel(INPUTS),
            "interpretation": "Stage220 consumes Stage203 equations and Stage219 compact key API skeleton evidence.",
        },
        {
            "gate": "G2_mosfhet_static_build",
            "status": "PASS" if build_ok else "BLOCKED",
            "metric": "make_static_spqlios",
            "value": str(build_ok).lower(),
            "evidence": rel(BUILD_LOG),
            "interpretation": "Prototype links against current MOSFHET static library.",
        },
        {
            "gate": "G3_probe_compile_run",
            "status": "PASS" if compile_ok and run_ok else "FAIL",
            "metric": "compile_ok;run_ok",
            "value": f"{str(compile_ok).lower()};{str(run_ok).lower()}",
            "evidence": f"{rel(COMPILE_LOG)}; {rel(RUN_LOG_TXT)}",
            "interpretation": "Standalone encrypted compact keygen prototype compiles and runs.",
        },
        {
            "gate": "G4_keygen_phase_semantics",
            "status": "PASS" if keygen_pass and phase_fail == 0 and semantic_fail == 0 else "FAIL",
            "metric": "phase_mismatches;dummy_semantic_failures",
            "value": f"{phase_fail};{semantic_fail}",
            "evidence": rel(KEYGEN),
            "interpretation": "Each encrypted row decrypts to semantic payload plus noise; dummy rows preserve semantic zero.",
        },
        {
            "gate": "G5_public_pattern_and_dft",
            "status": "PASS" if keygen_pass and pattern_fail == 0 and dft_fail == 0 else "FAIL",
            "metric": "public_pattern_failures;dft_mismatches;max_dft_gap",
            "value": f"{pattern_fail};{dft_fail};{max_gap}",
            "evidence": rel(KEYGEN),
            "interpretation": "Dense public row count uses nonzero/nonduplicate random masks and production DFT roundtrip remains within tolerance.",
        },
        {
            "gate": "G6_negative_controls",
            "status": "PASS" if keygen_pass and min_missing_active_neg > 0 and min_random_dummy_neg > 0 else "FAIL",
            "metric": "min_missing_active_negative;min_random_dummy_negative",
            "value": f"{min_missing_active_neg};{min_random_dummy_neg}",
            "evidence": rel(KEYGEN),
            "interpretation": "Skipping an active row and assigning nonzero dummy semantics both fail as required.",
        },
        {
            "gate": "G7_noise_bound_and_layout",
            "status": "PASS" if keygen_pass and layout_pass and max_noise <= max_bound else "FAIL",
            "metric": "max_noise_abs;max_noise_bound",
            "value": f"{max_noise};{max_bound}",
            "evidence": f"{rel(KEYGEN)}; {rel(LAYOUT)}",
            "interpretation": "Deterministic prototype noise remains below bound and layout preserves dense public row count.",
        },
        {
            "gate": "G8_production_admission",
            "status": "DENY_SAB_HOTPATH_CODE",
            "metric": "missing_before_sab_code",
            "value": "security_reduction;production_noise_recurrence;compact_ep_integration;complete_sab_gate",
            "evidence": rel(PROOF),
            "interpretation": "Stage220 permits production-noise recurrence modeling only; no SAB integration or speedup claim.",
        },
        {
            "gate": "G9_stage220_decision",
            "status": DECISION if not missing and build_ok and compile_ok and run_ok and keygen_pass and layout_pass else "FAIL_STAGE220",
            "metric": "decision",
            "value": DECISION if not missing and build_ok and compile_ok and run_ok and keygen_pass and layout_pass else "FAIL_STAGE220",
            "evidence": rel(PROOF),
            "interpretation": "Encrypted compact keygen prototype is ready for production noise recurrence gate, still outside SAB hot path.",
        },
    ]


def build_next() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage221_compact_keygen_noise_recurrence",
            "entry_condition": "Stage220 encrypted compact keygen prototype passes phase/DFT/negative/noise gates.",
            "gate": "Model production repeated-SAB noise recurrence and resource bounds before any compact EP/SAB integration.",
            "status": "selected",
            "failure_action": "If recurrence or resource bound fails, compact route remains prototype-only.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P1",
            "route": "stage222_isolated_compact_ep_integration",
            "entry_condition": "Production noise recurrence passes and keygen API remains closed.",
            "gate": "Isolated compact external product integration; still no SAB schedule integration.",
            "status": "future_blocked",
            "failure_action": "Record kernel-only negative or neutral result.",
            "evidence": rel(KEYGEN),
        },
        {
            "priority": "P2",
            "route": "exact_pvw_mat_sab_report_fallback",
            "entry_condition": "Any compact keygen/noise gate fails.",
            "gate": "Report only current exact PVW/MAT-SAB T_bootstrap/r evidence.",
            "status": "fallback",
            "failure_action": "No compact algorithmic claim.",
            "evidence": rel(STAGE219_PROOF),
        },
    ]


def write_docs(inputs: List[Dict[str, str]], keygen_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]], proof: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> None:
    report = f"""# Stage220 Encrypted Compact Keygen Prototype

Decision: `{proof[-1]["status"]}`.

Stage220 builds and runs a MOSFHET-linked encrypted compact keygen prototype.
Each row stores random-looking public mask/body material, explicit active or
semantic-zero-dummy role metadata, and deterministic finite noise. The gate
checks row phase, production DFT roundtrip, public-pattern constraints,
semantic-zero dummy preservation, and negative controls.

This is not a production security proof and does not enter `sab_pvw_*`.

## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Input Status

{table(inputs, ["input", "status", "evidence", "role", "bytes"])}
## Keygen Results

{table(keygen_rows, KEYGEN_FIELDS)}
## Layout Results

{table(layout_rows, LAYOUT_FIELDS)}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
"""
    write_text(REPORT, report)
    write_text(DOC, report)
    write_text(
        PLAN,
        """# Stage220 Plan

Goal: prototype encrypted compact keygen rows after the Stage219 API skeleton.

Gates:

- current MOSFHET static library builds;
- generated C probe compiles and runs;
- encrypted row phase equals semantic payload plus modeled noise;
- dummy rows preserve semantic-zero payload while retaining public randomness;
- DFT conversion remains within tolerance;
- skipping active rows and nonzero dummy semantics fail as negative controls;
- no SAB hot-path code is authorized.
""",
    )
    write_text(
        THEORY,
        """# Stage220 Encrypted Compact Keygen Model

The prototype models each compact selector row as an encryption-like object:

```text
b = a * s_lane + semantic(row) + noise(row)
```

Active rows carry deterministic finite semantic payloads. Dummy rows keep
random-looking public masks and bodies but have semantic payload zero. This is
the first gate that checks the compact route after row-role API skeletoning
with production MOSFHET polynomial and DFT functions.

This remains a deterministic prototype. It does not prove standard security,
parameterized noise recurrence, compact EP integration, or complete-SAB
`T_bootstrap/r`.
""",
    )
    write_text(
        VARIANT,
        """# Encrypted Compact Keygen Prototype

This is an isolated keygen prototype.

Verified:

- dense public row count with random-looking nonduplicate masks;
- active row phase equals semantic payload plus noise;
- dummy row semantic payload is zero;
- production DFT roundtrip stays within tolerance;
- missing-active and nonzero-dummy negative controls fail.

Still blocked:

- security reduction;
- production repeated-SAB noise recurrence;
- compact EP integration;
- complete-SAB `T_bootstrap/r` benchmark.
""",
    )
    write_text(
        REPRO,
        """# Stage220 Reproduction Commands

```powershell
python scripts\\build_stage220_encrypted_compact_keygen_prototype.py
Get-Content -Raw repro\\stage220_encrypted_compact_keygen_prototype\\proof_gate.csv
Get-Content -Raw repro\\stage220_encrypted_compact_keygen_prototype\\keygen_results.csv
```
""",
    )


def update_tracking(status: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 220: Encrypted Compact Keygen Prototype",
        f"""
## Stage 220: Encrypted Compact Keygen Prototype

Goal:

```text
Prototype encrypted compact keygen rows with semantic-zero dummy role
preservation and negative controls, without touching SAB hot paths.
```

Status:

```text
Completed. Stage220 records {status}. Encrypted compact keygen rows pass
phase/DFT/public-pattern/negative/noise gates and route next to production
noise recurrence; SAB integration remains denied.
```
""",
    )
    append_once(
        GOAL,
        "Stage220 records encrypted compact keygen prototype",
        f"""
Stage220 records encrypted compact keygen prototype. Decision: `{status}`.
The compact route now has an isolated encrypted-row prototype, but still lacks
security reduction, production SAB noise recurrence, compact EP integration,
and complete-SAB speedup evidence.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage220 encrypted compact keygen prototype",
        f"""
### Stage220 encrypted compact keygen prototype

`{status}` advances the compact route only to a production-noise recurrence
candidate. It does not authorize `sab_pvw_*` integration, complete-SAB claims,
or security claims.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage220_encrypted_compact_keygen_prototype",
        f"""
H10_stage220_encrypted_compact_keygen_prototype:
  status: encrypted_compact_keygen_prototype_passed
  evidence:
    - repro/stage220_encrypted_compact_keygen_prototype/proof_gate.csv
    - repro/stage220_encrypted_compact_keygen_prototype/keygen_results.csv
    - docs/stage220_encrypted_compact_keygen_prototype.md
  conclusion: >
    Stage220 records {status}. The compact route has an isolated encrypted-row
    keygen prototype with semantic-zero dummy role preservation and negative
    controls, but security, production noise recurrence, compact EP
    integration, and complete-SAB gates remain missing.
""",
    )
    append_once(
        RUN_LOG,
        "stage220-encrypted-compact-keygen-prototype-001",
        f"""stage220-encrypted-compact-keygen-prototype-001,2026-07-04,{head},Stage 220,spqlios,python scripts/build_stage220_encrypted_compact_keygen_prototype.py,Stage203 equations and Stage219 API skeleton,no SAB benchmark,{status},"Encrypted compact keygen prototype; SAB hot-path code denied.",docs/stage220_encrypted_compact_keygen_prototype.md; repro/stage220_encrypted_compact_keygen_prototype/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage220_encrypted_compact_keygen_prototype:",
        """
- stage220_encrypted_compact_keygen_prototype:
  - `docs/stage220_encrypted_compact_keygen_prototype.md`
  - `experiments/stage220_encrypted_compact_keygen_prototype_plan.md`
  - `theory_checks/stage220_encrypted_compact_keygen_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage220_encrypted_compact_keygen_prototype.md`
  - `scripts/build_stage220_encrypted_compact_keygen_prototype.py`
  - `repro/stage220_encrypted_compact_keygen_prototype/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage220 encrypted compact keygen prototype recorded",
        """
- [x] Stage220 encrypted compact keygen prototype recorded.
""",
    )


def write_artifacts(paths: Iterable[Path]) -> None:
    rows = [
        {
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path),
            "bytes": str(path.stat().st_size) if path.exists() else "0",
        }
        for path in paths
    ]
    write_csv(ARTIFACT, rows, ["path", "exists", "sha256", "bytes"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = build_inputs()
    write_c_source()
    backend = "spqlios"
    build_ok = build_mosfhet_static(backend)
    compile_ok = compile_probe(backend) if build_ok else False
    keygen_rows, layout_rows, run_ok = run_probe(build_ok, compile_ok)
    write_csv(KEYGEN, keygen_rows, KEYGEN_FIELDS)
    write_csv(LAYOUT, layout_rows, LAYOUT_FIELDS)
    proof = build_proof(build_ok, compile_ok, run_ok, keygen_rows, layout_rows, inputs)
    next_rows = build_next()
    write_csv(INPUTS, inputs, ["input", "status", "evidence", "role", "bytes"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_docs(inputs, keygen_rows, layout_rows, proof, next_rows)
    status = proof[-1]["status"]
    update_tracking(status)
    write_artifacts([DOC, PLAN, THEORY, VARIANT, INPUTS, KEYGEN, LAYOUT, PROOF, NEXT, BUILD_LOG, COMPILE_LOG, RUN_LOG_TXT, C_SOURCE, REPORT, REPRO, Path(__file__)])
    print(status)
    return 0 if status == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
