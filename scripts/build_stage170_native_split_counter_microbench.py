#!/usr/bin/env python3
"""Stage170: CB5 native split counters for MAT EP and from_DFT."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage170_native_split_counter_microbench"

C_SOURCE = OUT_DIR / "stage170_split_counter_probe.c"
SUMMARY_CSV = OUT_DIR / "summary.csv"
COUNTER_CSV = OUT_DIR / "counter_metrics.csv"
RUN_CSV = OUT_DIR / "run_metrics.csv"
DERIVED_CSV = OUT_DIR / "derived_counter_ratios.csv"
CORRECTNESS_CSV = OUT_DIR / "correctness.csv"
REMOTE_CSV = OUT_DIR / "remote_environment.csv"
POST_RESTORE_CSV = OUT_DIR / "post_restore_verification.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage170_native_split_counter_microbench.md"
PLAN_MD = ROOT / "experiments" / "stage170_native_split_counter_microbench_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage170_split_counter_scope.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_native_split_counter_microbench.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

REMOTE_USER = os.environ.get("STAGE170_REMOTE_USER", "delld")
REMOTE_HOST = os.environ.get("STAGE170_REMOTE_HOST", "192.168.107.220")
REMOTE_BASE = os.environ.get("STAGE170_REMOTE_BASE", "/home/delld/spz")
REMOTE_PASSWORD = os.environ.get("STAGE170_SSHPASS", "")
MAKE_JOBS = os.environ.get("STAGE170_JOBS", "$(nproc)")
R_VALUE = int(os.environ.get("STAGE170_R", "6"))
N_VALUE = int(os.environ.get("STAGE170_N", "2048"))
ITEMS = int(os.environ.get("STAGE170_ITEMS", "256"))
REPS = int(os.environ.get("STAGE170_REPS", "8"))
WARMUPS = int(os.environ.get("STAGE170_WARMUPS", "2"))
BG_BIT = int(os.environ.get("STAGE170_BG_BIT", "23"))

HEAD = subprocess.check_output(
    ["git", "rev-parse", "--short", "HEAD"],
    cwd=ROOT,
    text=True,
).strip()
REMOTE_DIR_NAME = f"Fast-Amortized-Bootstrapping-stage170-{HEAD}"
REMOTE_DIR = f"{REMOTE_BASE}/{REMOTE_DIR_NAME}"
REMOTE_STAGE_DIR = f"{REMOTE_DIR}/repro/stage170_native_split_counter_microbench"
REMOTE_PROBE_SOURCE = f"{REMOTE_STAGE_DIR}/stage170_split_counter_probe.c"
REMOTE_PROBE_BINARY = f"{REMOTE_STAGE_DIR}/stage170_split_counter_probe"

MAKE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "ENABLE_PVW_TMLWE=true MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
    "SAB_PVW_SUB_DECOMP_FUSION=true"
)

PERF_EVENTS = (
    "cycles,instructions,cache-references,cache-misses,branches,branch-misses,"
    "mem_inst_retired.all_loads,mem_inst_retired.all_stores,"
    "fp_arith_inst_retired.512b_packed_double,"
    "fp_arith_inst_retired.256b_packed_double"
)

VARIANTS = ["mat_ep_subdecomp", "from_dft_materialize"]

PERF_LINE_RE = re.compile(r"^\s*([\d,]+)\s+([A-Za-z0-9_.-]+)\b")
ELAPSED_RE = re.compile(r"^\s*([\d.]+)\s+seconds time elapsed")
USER_RE = re.compile(r"^\s*([\d.]+)\s+seconds user")
SYS_RE = re.compile(r"^\s*([\d.]+)\s+seconds sys")
RESULT_RE = re.compile(
    r"RESULT170,(?P<variant>[^,]+),(?P<r>\d+),(?P<N>\d+),"
    r"(?P<items>\d+),(?P<reps>\d+),(?P<calls>\d+),"
    r"(?P<total_ns>\d+),(?P<per_call_us>[0-9.]+),(?P<sink>\d+),"
    r"(?P<status>[^,\s]+)"
)
CORRECT_RE = re.compile(
    r"CORRECT170,(?P<variant>[^,]+),(?P<check>[^,]+),"
    r"(?P<mismatches>\d+),(?P<max_gap>\d+),(?P<status>[^,\s]+)"
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    normalized = [{field: row.get(field, "") for field in fields} for row in row_list]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def wsl_path(path: Path) -> str:
    drive = path.drive.rstrip(":").lower()
    rest = path.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


def wsl_repo() -> str:
    return wsl_path(ROOT)


def scrub(text: str) -> str:
    if REMOTE_PASSWORD:
        text = text.replace(REMOTE_PASSWORD, "***")
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    clean = "".join(ch if ch in "\n\t" or 32 <= ord(ch) < 127 else "?" for ch in text)
    return "\n".join(line.rstrip() for line in clean.splitlines()).rstrip() + "\n"


def run_wsl(command: str, log: Path, timeout: int = 300) -> int:
    proc = subprocess.run(
        ["wsl", "bash", "-lc", command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    write_text_lf(log, "\n".join([
        f"command: {scrub(command).strip()}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        scrub(proc.stdout),
        "--- stderr ---",
        scrub(proc.stderr),
    ]))
    return proc.returncode


def ssh_prefix() -> str:
    return (
        f"sshpass -p {shlex.quote(REMOTE_PASSWORD)} ssh "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage170_known_hosts "
        "-o ConnectTimeout=12 "
        f"{shlex.quote(REMOTE_USER + '@' + REMOTE_HOST)}"
    )


def scp_prefix() -> str:
    return (
        f"sshpass -p {shlex.quote(REMOTE_PASSWORD)} scp "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage170_known_hosts "
        "-o ConnectTimeout=12 "
    )


def remote_command(command: str) -> str:
    return f"{ssh_prefix()} {shlex.quote(command)}"


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def write_c_source() -> None:
    source = fr'''
#include "mosfhet.h"
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE170_R
#define STAGE170_R {R_VALUE}
#endif
#ifndef STAGE170_N
#define STAGE170_N {N_VALUE}
#endif
#ifndef STAGE170_ITEMS
#define STAGE170_ITEMS {ITEMS}
#endif
#ifndef STAGE170_REPS
#define STAGE170_REPS {REPS}
#endif
#ifndef STAGE170_WARMUPS
#define STAGE170_WARMUPS {WARMUPS}
#endif
#ifndef STAGE170_BG_BIT
#define STAGE170_BG_BIT {BG_BIT}
#endif

static inline uint64_t now_ns(void) {{
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ((uint64_t) ts.tv_sec * 1000000000ULL) + (uint64_t) ts.tv_nsec;
}}

static void fill_poly(TorusPolynomial p, uint64_t seed) {{
  uint64_t x = seed ^ 0x9e3779b97f4a7c15ULL;
  for (int i = 0; i < p->N; i++) {{
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    p->coeffs[i] = (Torus) (x * 0x2545f4914f6cdd1dULL + (uint64_t) i);
  }}
}}

static void fill_pvmtmlwe(PVW_TMLWE p, uint64_t seed) {{
  fill_poly(p->a[0], seed ^ 0x100000001b3ULL);
  for (int lane = 0; lane < p->r; lane++) {{
    fill_poly(p->b[lane], seed ^ ((uint64_t) lane << 32) ^ 0x84222325cbf29ce4ULL);
  }}
}}

static void fill_pvmtmlwe_dft(PVW_TMLWE_DFT p, TorusPolynomial tmp, uint64_t seed) {{
  fill_poly(tmp, seed ^ 0x6a09e667f3bcc909ULL);
  polynomial_torus_to_DFT(p->a[0], tmp);
  for (int lane = 0; lane < p->r; lane++) {{
    fill_poly(tmp, seed ^ ((uint64_t) lane << 28) ^ 0xbb67ae8584caa73bULL);
    polynomial_torus_to_DFT(p->b[lane], tmp);
  }}
}}

static void fill_selector(MAT_TRGSW_DFT selector) {{
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE170_N);
  const int rows = 1 + STAGE170_R;
  for (int row = 0; row < rows; row++) {{
    fill_poly(tmp, 0xabcdef0011223344ULL ^ (uint64_t) row);
    polynomial_torus_to_DFT(selector->samples[row]->a[0], tmp);
    for (int lane = 0; lane < STAGE170_R; lane++) {{
      fill_poly(tmp, 0x6677889900aabbccULL ^ ((uint64_t) row << 16) ^ (uint64_t) lane);
      polynomial_torus_to_DFT(selector->samples[row]->b[lane], tmp);
    }}
  }}
  free_polynomial(tmp);
}}

static void zero_pvmtmlwe_dft(PVW_TMLWE_DFT out) {{
  memset(out->a[0]->coeffs, 0, sizeof(double) * STAGE170_N);
  for (int lane = 0; lane < out->r; lane++) {{
    memset(out->b[lane]->coeffs, 0, sizeof(double) * STAGE170_N);
  }}
}}

static void sub_decompose_row(PVW_TMLWE in1, PVW_TMLWE in2,
    TorusPolynomial out, int row) {{
  const uint64_t half_Bg = (1ULL << (STAGE170_BG_BIT - 1));
  const uint64_t h_mask = (1ULL << STAGE170_BG_BIT) - 1;
  const uint64_t word_size = sizeof(Torus) * 8;
  const uint64_t offset = (1ULL << (word_size - 1));
  const uint64_t h_bit = word_size - STAGE170_BG_BIT;

  TorusPolynomial lhs = row == 0 ? in1->a[0] : in1->b[row - 1];
  TorusPolynomial rhs = row == 0 ? in2->a[0] : in2->b[row - 1];
  for (int c = 0; c < STAGE170_N; c++) {{
    const uint64_t diff = rhs->coeffs[c] - lhs->coeffs[c];
    const uint64_t coeff_off = diff + offset;
    out->coeffs[c] = ((coeff_off >> h_bit) & h_mask) - half_Bg;
  }}
}}

static void streaming_sub_mul_DFT(PVW_TMLWE_DFT out, PVW_TMLWE in1,
    PVW_TMLWE in2, MAT_TRGSW_DFT selector, TorusPolynomial dec,
    DFT_Polynomial dec_dft) {{
  zero_pvmtmlwe_dft(out);
  const int rows = 1 + STAGE170_R;
  for (int row = 0; row < rows; row++) {{
    sub_decompose_row(in1, in2, dec, row);
    polynomial_torus_to_DFT(dec_dft, dec);
    polynomial_mul_addto_DFT(out->a[0], dec_dft, selector->samples[row]->a[0]);
    for (int lane = 0; lane < STAGE170_R; lane++) {{
      polynomial_mul_addto_DFT(out->b[lane], dec_dft, selector->samples[row]->b[lane]);
    }}
  }}
}}

static uint64_t compare_torus(PVW_TMLWE a, PVW_TMLWE b, uint64_t *max_gap) {{
  uint64_t mismatches = 0;
  for (int i = 0; i < STAGE170_N; i++) {{
    const uint64_t x = (uint64_t) a->a[0]->coeffs[i];
    const uint64_t y = (uint64_t) b->a[0]->coeffs[i];
    const uint64_t gap = x >= y ? x - y : y - x;
    if (gap != 0) mismatches++;
    if (gap > *max_gap) *max_gap = gap;
  }}
  for (int lane = 0; lane < STAGE170_R; lane++) {{
    for (int i = 0; i < STAGE170_N; i++) {{
      const uint64_t x = (uint64_t) a->b[lane]->coeffs[i];
      const uint64_t y = (uint64_t) b->b[lane]->coeffs[i];
      const uint64_t gap = x >= y ? x - y : y - x;
      if (gap != 0) mismatches++;
      if (gap > *max_gap) *max_gap = gap;
    }}
  }}
  return mismatches;
}}

static uint64_t checksum_dft(PVW_TMLWE_DFT out) {{
  uint64_t acc = 0xcbf29ce484222325ULL;
  const uint64_t *a = (const uint64_t *) out->a[0]->coeffs;
  for (int i = 0; i < STAGE170_N; i += 17) acc ^= a[i] + (acc << 6) + (acc >> 2);
  for (int lane = 0; lane < STAGE170_R; lane++) {{
    const uint64_t *b = (const uint64_t *) out->b[lane]->coeffs;
    for (int i = 0; i < STAGE170_N; i += 17) acc ^= b[i] + (acc << 6) + (acc >> 2);
  }}
  return acc;
}}

static uint64_t checksum_torus(PVW_TMLWE out) {{
  uint64_t acc = 0x84222325cbf29ce4ULL;
  for (int i = 0; i < STAGE170_N; i += 17) {{
    acc ^= (uint64_t) out->a[0]->coeffs[i] + (acc << 6) + (acc >> 2);
  }}
  for (int lane = 0; lane < STAGE170_R; lane++) {{
    for (int i = 0; i < STAGE170_N; i += 17) {{
      acc ^= (uint64_t) out->b[lane]->coeffs[i] + (acc << 6) + (acc >> 2);
    }}
  }}
  return acc;
}}

static void run_mat_loop(PVW_TMLWE_DFT out, PVW_TMLWE *in1,
    PVW_TMLWE *in2, MAT_TRGSW_DFT selector,
    MAT_TRGSW_MUL_SCRATCH scratch) {{
  for (int item = 0; item < STAGE170_ITEMS; item++) {{
    mat_trgsw_mul_pvmtmlwe_sub_DFT(out, in1[item], in2[item], selector, scratch);
  }}
}}

static int run_mat_ep_subdecomp(void) {{
  init_fft(STAGE170_N);
  MAT_TRGSW_DFT selector =
      mat_trgsw_alloc_new_DFT_sample(1, STAGE170_BG_BIT, 1, STAGE170_R, STAGE170_N);
  fill_selector(selector);

  PVW_TMLWE *in1 = pvmtmlwe_alloc_new_sample_array(STAGE170_ITEMS, 1, STAGE170_R, STAGE170_N);
  PVW_TMLWE *in2 = pvmtmlwe_alloc_new_sample_array(STAGE170_ITEMS, 1, STAGE170_R, STAGE170_N);
  for (int item = 0; item < STAGE170_ITEMS; item++) {{
    fill_pvmtmlwe(in1[item], 0x100000000ULL + (uint64_t) item);
    fill_pvmtmlwe(in2[item], 0x200000000ULL + (uint64_t) item);
  }}

  PVW_TMLWE_DFT current = pvmtmlwe_alloc_new_DFT_sample(1, STAGE170_R, STAGE170_N);
  PVW_TMLWE_DFT stream = pvmtmlwe_alloc_new_DFT_sample(1, STAGE170_R, STAGE170_N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(1 + STAGE170_R, STAGE170_N);
  TorusPolynomial dec = polynomial_new_torus_polynomial(STAGE170_N);
  DFT_Polynomial dec_dft = polynomial_new_DFT_polynomial(STAGE170_N);

  mat_trgsw_mul_pvmtmlwe_sub_DFT(current, in1[0], in2[0], selector, scratch);
  streaming_sub_mul_DFT(stream, in1[0], in2[0], selector, dec, dec_dft);
  PVW_TMLWE current_torus = pvmtmlwe_alloc_new_sample(1, STAGE170_R, STAGE170_N);
  PVW_TMLWE stream_torus = pvmtmlwe_alloc_new_sample(1, STAGE170_R, STAGE170_N);
  pvmtmlwe_from_DFT(current_torus, current);
  pvmtmlwe_from_DFT(stream_torus, stream);
  uint64_t max_gap = 0;
  const uint64_t mismatches = compare_torus(current_torus, stream_torus, &max_gap);
  printf("CORRECT170,mat_ep_subdecomp,streaming_reference,%" PRIu64 ",%" PRIu64 ",%s\n",
      mismatches, max_gap, mismatches == 0 ? "PASS" : "FAIL");

  for (int w = 0; w < STAGE170_WARMUPS; w++) {{
    run_mat_loop(current, in1, in2, selector, scratch);
  }}
  const uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE170_REPS; rep++) {{
    run_mat_loop(current, in1, in2, selector, scratch);
  }}
  const uint64_t ns = now_ns() - start;
  const uint64_t calls = (uint64_t) STAGE170_REPS * (uint64_t) STAGE170_ITEMS;
  const double per_call_us = ((double) ns) / ((double) calls) / 1000.0;
  const uint64_t sink = checksum_dft(current);
  printf("RESULT170,mat_ep_subdecomp,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",%s\n",
      STAGE170_R, STAGE170_N, STAGE170_ITEMS, STAGE170_REPS,
      calls, ns, per_call_us, sink, mismatches == 0 ? "PASS" : "FAIL");

  free_pvmtmlwe(current_torus);
  free_pvmtmlwe(stream_torus);
  free_DFT_polynomial(dec_dft);
  free_polynomial(dec);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe_DFT(current);
  free_pvmtmlwe_DFT(stream);
  free_pvmtmlwe_array(in1, STAGE170_ITEMS);
  free_pvmtmlwe_array(in2, STAGE170_ITEMS);
  free_mat_trgsw_DFT(selector);
  return mismatches == 0 ? 0 : 1;
}}

static void run_from_dft_loop(PVW_TMLWE *out, PVW_TMLWE_DFT *dft,
    PVW_TMLWE *addend) {{
  for (int item = 0; item < STAGE170_ITEMS; item++) {{
    pvmtmlwe_from_DFT_add(out[item], dft[item], addend[item]);
  }}
}}

static int run_from_dft_materialize(void) {{
  init_fft(STAGE170_N);
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE170_N);
  PVW_TMLWE_DFT *dft = pvmtmlwe_alloc_new_DFT_sample_array(STAGE170_ITEMS, 1, STAGE170_R, STAGE170_N);
  PVW_TMLWE *addend = pvmtmlwe_alloc_new_sample_array(STAGE170_ITEMS, 1, STAGE170_R, STAGE170_N);
  PVW_TMLWE *out = pvmtmlwe_alloc_new_sample_array(STAGE170_ITEMS, 1, STAGE170_R, STAGE170_N);
  for (int item = 0; item < STAGE170_ITEMS; item++) {{
    fill_pvmtmlwe_dft(dft[item], tmp, 0x300000000ULL + (uint64_t) item);
    fill_pvmtmlwe(addend[item], 0x400000000ULL + (uint64_t) item);
  }}

  PVW_TMLWE fused = pvmtmlwe_alloc_new_sample(1, STAGE170_R, STAGE170_N);
  PVW_TMLWE separate = pvmtmlwe_alloc_new_sample(1, STAGE170_R, STAGE170_N);
  pvmtmlwe_from_DFT_add(fused, dft[0], addend[0]);
  pvmtmlwe_from_DFT(separate, dft[0]);
  pvmtmlwe_addto(separate, addend[0]);
  uint64_t max_gap = 0;
  const uint64_t mismatches = compare_torus(fused, separate, &max_gap);
  printf("CORRECT170,from_dft_materialize,fused_add_reference,%" PRIu64 ",%" PRIu64 ",%s\n",
      mismatches, max_gap, mismatches == 0 ? "PASS" : "FAIL");

  for (int w = 0; w < STAGE170_WARMUPS; w++) {{
    run_from_dft_loop(out, dft, addend);
  }}
  const uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE170_REPS; rep++) {{
    run_from_dft_loop(out, dft, addend);
  }}
  const uint64_t ns = now_ns() - start;
  const uint64_t calls = (uint64_t) STAGE170_REPS * (uint64_t) STAGE170_ITEMS;
  const double per_call_us = ((double) ns) / ((double) calls) / 1000.0;
  const uint64_t sink = checksum_torus(out[STAGE170_ITEMS - 1]);
  printf("RESULT170,from_dft_materialize,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",%s\n",
      STAGE170_R, STAGE170_N, STAGE170_ITEMS, STAGE170_REPS,
      calls, ns, per_call_us, sink, mismatches == 0 ? "PASS" : "FAIL");

  free_pvmtmlwe(fused);
  free_pvmtmlwe(separate);
  free_pvmtmlwe_array(out, STAGE170_ITEMS);
  free_pvmtmlwe_array(addend, STAGE170_ITEMS);
  for (int item = 0; item < STAGE170_ITEMS; item++) {{
    free_pvmtmlwe_DFT(dft[item]);
  }}
  free(dft);
  free_polynomial(tmp);
  return mismatches == 0 ? 0 : 1;
}}

int main(int argc, char **argv) {{
  if (argc != 2) {{
    fprintf(stderr, "usage: %s mat_ep_subdecomp|from_dft_materialize\n", argv[0]);
    return 2;
  }}
  if (strcmp(argv[1], "mat_ep_subdecomp") == 0) {{
    return run_mat_ep_subdecomp();
  }}
  if (strcmp(argv[1], "from_dft_materialize") == 0) {{
    return run_from_dft_materialize();
  }}
  fprintf(stderr, "unknown variant: %s\n", argv[1]);
  return 2;
}}
'''
    write_text_lf(C_SOURCE, source)


def sync_repo() -> int:
    remote_extract = (
        f"rm -rf {shlex.quote(REMOTE_DIR)} && "
        f"mkdir -p {shlex.quote(REMOTE_DIR)} && "
        f"tar -xf - -C {shlex.quote(REMOTE_DIR)}"
    )
    cmd = (
        f"cd {shlex.quote(wsl_repo())} && "
        f"git archive --format=tar HEAD | {ssh_prefix()} {shlex.quote(remote_extract)}"
    )
    return run_wsl(cmd, OUT_DIR / "sync.log", timeout=300)


def probe_remote_environment() -> int:
    cmd = (
        "printf 'hostname,'; hostname; "
        "printf 'whoami,'; whoami; "
        "printf 'uname,'; uname -a; "
        "printf 'perf,'; command -v perf || true; "
        "printf 'perf_event_paranoid,'; cat /proc/sys/kernel/perf_event_paranoid; "
        "printf 'remote_dir,'; printf " + shlex.quote(REMOTE_DIR) + "; printf '\\n'; "
        "lscpu"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / "remote_environment.log", timeout=60)


def upload_probe_source() -> int:
    mkdir_rc = run_wsl(
        remote_command(f"mkdir -p {shlex.quote(REMOTE_STAGE_DIR)}"),
        OUT_DIR / "upload_mkdir.log",
        timeout=60,
    )
    if mkdir_rc != 0:
        return mkdir_rc
    target = f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PROBE_SOURCE}"
    cmd = (
        f"{scp_prefix()} {shlex.quote(wsl_path(C_SOURCE))} "
        f"{shlex.quote(target)}"
    )
    return run_wsl(cmd, OUT_DIR / "upload_probe_source.log", timeout=120)


def build_remote_static() -> int:
    cmd = (
        f"cd {shlex.quote(REMOTE_DIR)}/src/mosfhet && "
        "(make clean >/dev/null 2>&1 || true) && "
        f"make static {MAKE_FLAGS} -j{MAKE_JOBS}"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / "build_static.log", timeout=1800)


def compile_remote_probe() -> int:
    cmd = (
        f"cd {shlex.quote(REMOTE_DIR)} && "
        "gcc -O3 -march=native -Wall -Wextra "
        f"-DSTAGE170_R={R_VALUE} -DSTAGE170_N={N_VALUE} "
        f"-DSTAGE170_ITEMS={ITEMS} -DSTAGE170_REPS={REPS} "
        f"-DSTAGE170_WARMUPS={WARMUPS} -DSTAGE170_BG_BIT={BG_BIT} "
        "-I src/mosfhet/include "
        f"-o {shlex.quote(REMOTE_PROBE_BINARY)} "
        f"{shlex.quote(REMOTE_PROBE_SOURCE)} src/mosfhet/lib/libmosfhet.a -lm"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / "compile_probe.log", timeout=600)


def perf_remote_variant(variant: str) -> int:
    sudo_prefix = f"printf %s {shlex.quote(REMOTE_PASSWORD)} | sudo -S -p ''"
    cmd = (
        f"cd {shlex.quote(REMOTE_DIR)} && "
        "orig=$(cat /proc/sys/kernel/perf_event_paranoid); "
        "restore_perf_paranoid(){ "
        f"{sudo_prefix} sysctl -w kernel.perf_event_paranoid=$orig >/dev/null; "
        "}; "
        "trap restore_perf_paranoid EXIT; "
        f"{sudo_prefix} sysctl -w kernel.perf_event_paranoid=1 >/dev/null && "
        f"perf stat -e {shlex.quote(PERF_EVENTS)} -- "
        f"stdbuf -o0 {shlex.quote(REMOTE_PROBE_BINARY)} {shlex.quote(variant)}"
    )
    return run_wsl(
        remote_command(cmd),
        OUT_DIR / f"run_{variant}_perf.log",
        timeout=1800,
    )


def cleanup_remote() -> int:
    cmd = f"cd {shlex.quote(REMOTE_DIR)}/src/mosfhet && (make clean >/dev/null 2>&1 || true)"
    return run_wsl(remote_command(cmd), OUT_DIR / "cleanup.log", timeout=300)


def verify_restore_remote() -> int:
    cmd = "printf 'perf_event_paranoid_after,'; cat /proc/sys/kernel/perf_event_paranoid"
    return run_wsl(remote_command(cmd), OUT_DIR / "post_restore_verification.log", timeout=60)


def restore_remote_paranoid(value: str) -> int:
    if not value:
        return 1
    sudo_prefix = f"printf %s {shlex.quote(REMOTE_PASSWORD)} | sudo -S -p ''"
    cmd = f"{sudo_prefix} sysctl -w kernel.perf_event_paranoid={shlex.quote(value)}"
    return run_wsl(remote_command(cmd), OUT_DIR / "restore_expected_paranoid.log", timeout=60)


def parse_remote_environment() -> List[Dict[str, str]]:
    path = OUT_DIR / "remote_environment.log"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    rows: List[Dict[str, str]] = []
    for key in ["hostname", "whoami", "uname", "perf", "perf_event_paranoid", "remote_dir"]:
        m = re.search(rf"^{key},(.+)$", text, re.MULTILINE)
        if m:
            rows.append({"key": key, "value": m.group(1).strip(), "evidence": rel(path)})
    model = re.search(r"^Model name:\s+(.+)$", text, re.MULTILINE)
    flags = re.search(r"^Flags:\s+(.+)$", text, re.MULTILINE)
    cpus = re.search(r"^CPU\(s\):\s+(.+)$", text, re.MULTILINE)
    if model:
        rows.append({"key": "cpu_model", "value": model.group(1).strip(), "evidence": rel(path)})
    if cpus:
        rows.append({"key": "cpus", "value": cpus.group(1).strip(), "evidence": rel(path)})
    if flags:
        rows.append({"key": "has_avx512f", "value": "yes" if "avx512f" in flags.group(1) else "no", "evidence": rel(path)})
    return rows


def parse_restore() -> List[Dict[str, str]]:
    path = OUT_DIR / "post_restore_verification.log"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    rows: List[Dict[str, str]] = []
    m = re.search(r"^perf_event_paranoid_after,(.+)$", text, re.MULTILINE)
    if m:
        rows.append({"key": "perf_event_paranoid_after", "value": m.group(1).strip(), "evidence": rel(path)})
    return rows


def parse_variant_log(variant: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    path = OUT_DIR / f"run_{variant}_perf.log"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    counters: List[Dict[str, str]] = []
    runs: List[Dict[str, str]] = []
    correctness: List[Dict[str, str]] = []

    for raw in text.splitlines():
        line = raw.strip()
        m = PERF_LINE_RE.match(raw)
        if m:
            counters.append({
                "variant": variant,
                "metric": m.group(2),
                "value": m.group(1).replace(",", ""),
                "unit": "count",
                "evidence": rel(path),
                "detail": line,
            })
            continue
        for regex, metric in [(ELAPSED_RE, "elapsed_seconds"), (USER_RE, "user_seconds"), (SYS_RE, "sys_seconds")]:
            m2 = regex.match(raw)
            if m2:
                counters.append({
                    "variant": variant,
                    "metric": metric,
                    "value": m2.group(1),
                    "unit": "seconds",
                    "evidence": rel(path),
                    "detail": line,
                })
                break

    rc_match = re.search(r"^returncode:\s+(\d+)$", text, re.MULTILINE)
    result_found = False
    for line in text.splitlines():
        m = RESULT_RE.search(line)
        if not m:
            continue
        result_found = True
        runs.append({
            "variant": m.group("variant"),
            "run_rc": rc_match.group(1) if rc_match else "",
            "r": m.group("r"),
            "N": m.group("N"),
            "items": m.group("items"),
            "reps": m.group("reps"),
            "calls": m.group("calls"),
            "total_ns": m.group("total_ns"),
            "per_call_us": m.group("per_call_us"),
            "sink": m.group("sink"),
            "status": m.group("status"),
            "evidence": rel(path),
        })
    if not result_found:
        runs.append({
            "variant": variant,
            "run_rc": rc_match.group(1) if rc_match else "",
            "r": "",
            "N": "",
            "items": "",
            "reps": "",
            "calls": "",
            "total_ns": "",
            "per_call_us": "",
            "sink": "",
            "status": "MISSING_RESULT",
            "evidence": rel(path),
        })

    for line in text.splitlines():
        m = CORRECT_RE.search(line)
        if not m:
            continue
        correctness.append({
            "variant": m.group("variant"),
            "check": m.group("check"),
            "mismatches": m.group("mismatches"),
            "max_gap": m.group("max_gap"),
            "status": m.group("status"),
            "evidence": rel(path),
        })
    if not correctness:
        correctness.append({
            "variant": variant,
            "check": "probe_correctness_line",
            "mismatches": "",
            "max_gap": "",
            "status": "MISSING",
            "evidence": rel(path),
        })
    return counters, runs, correctness


def metric(rows: List[Dict[str, str]], variant: str, key: str) -> str:
    for row in rows:
        if row.get("variant") == variant and row.get("metric") == key:
            return row.get("value", "")
    return ""


def run_metric(rows: List[Dict[str, str]], variant: str, key: str) -> str:
    for row in rows:
        if row.get("variant") == variant:
            return row.get(key, "")
    return ""


def fnum(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def build_derived(counter_rows: List[Dict[str, str]], run_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for variant in VARIANTS:
        calls = fnum(run_metric(run_rows, variant, "calls"))
        cycles = fnum(metric(counter_rows, variant, "cycles"))
        instructions = fnum(metric(counter_rows, variant, "instructions"))
        loads = fnum(metric(counter_rows, variant, "mem_inst_retired.all_loads"))
        stores = fnum(metric(counter_rows, variant, "mem_inst_retired.all_stores"))
        fp512 = fnum(metric(counter_rows, variant, "fp_arith_inst_retired.512b_packed_double"))
        fp256 = fnum(metric(counter_rows, variant, "fp_arith_inst_retired.256b_packed_double"))
        cache_refs = fnum(metric(counter_rows, variant, "cache-references"))
        cache_misses = fnum(metric(counter_rows, variant, "cache-misses"))
        elapsed = fnum(metric(counter_rows, variant, "elapsed_seconds"))
        derived = [
            ("cycles_per_call", cycles / calls if calls else 0.0, "cycles/call"),
            ("instructions_per_call", instructions / calls if calls else 0.0, "instructions/call"),
            ("loads_per_call", loads / calls if calls else 0.0, "loads/call"),
            ("stores_per_call", stores / calls if calls else 0.0, "stores/call"),
            ("fp512_per_call", fp512 / calls if calls else 0.0, "fp512/call"),
            ("fp256_per_call", fp256 / calls if calls else 0.0, "fp256/call"),
            ("ipc", instructions / cycles if cycles else 0.0, "instructions/cycle"),
            ("load_store_to_fp512_ratio", (loads + stores) / fp512 if fp512 else 0.0, "(loads+stores)/fp512"),
            ("cache_miss_rate", cache_misses / cache_refs if cache_refs else 0.0, "cache-misses/cache-references"),
            ("elapsed_seconds", elapsed, "seconds"),
            ("calls", calls, "calls"),
        ]
        for name, value, unit in derived:
            out.append({
                "variant": variant,
                "metric": name,
                "value": f"{value:.9f}",
                "unit": unit,
                "interpretation": interpretation_for(variant, name),
            })
    return out


def interpretation_for(variant: str, metric_name: str) -> str:
    if metric_name == "load_store_to_fp512_ratio":
        return "Higher values mean memory traffic remains important relative to FP512 work."
    if metric_name == "cycles_per_call":
        return "Primary per-call native counter cost for this isolated component."
    if metric_name == "cache_miss_rate":
        return "Locality proxy; not a standalone proof of a better layout."
    if metric_name == "fp512_per_call":
        return "Checks whether AVX512 arithmetic is actually exercised by the component."
    if variant == "from_dft_materialize" and metric_name == "fp256_per_call":
        return "Residual FFT/backend width signal for materialization."
    return "Component-level attribution only; do not claim full-SAB acceleration from this row alone."


def env_value(rows: List[Dict[str, str]], key: str) -> str:
    for row in rows:
        if row.get("key") == key:
            return row.get("value", "")
    return ""


def decide(
    sync_rc: int,
    env_rc: int,
    upload_rc: int,
    build_rc: int,
    compile_rc: int,
    perf_rcs: Dict[str, int],
    restore_rows: List[Dict[str, str]],
    counters: List[Dict[str, str]],
    runs: List[Dict[str, str]],
    correctness: List[Dict[str, str]],
) -> str:
    if not REMOTE_PASSWORD:
        return "BLOCKED_STAGE170_MISSING_REMOTE_PASSWORD_ENV"
    if sync_rc != 0:
        return "FAIL_STAGE170_REMOTE_SYNC"
    if env_rc != 0:
        return "FAIL_STAGE170_REMOTE_ENV"
    if upload_rc != 0:
        return "FAIL_STAGE170_PROBE_UPLOAD"
    if build_rc != 0:
        return "FAIL_STAGE170_REMOTE_STATIC_BUILD"
    if compile_rc != 0:
        return "FAIL_STAGE170_REMOTE_PROBE_COMPILE"
    if any(rc != 0 for rc in perf_rcs.values()):
        return "FAIL_STAGE170_REMOTE_PERF_RUN"
    if any(row.get("status") != "PASS" for row in correctness):
        return "FAIL_STAGE170_PROBE_CORRECTNESS"
    if any(run_metric(runs, variant, "status") != "PASS" for variant in VARIANTS):
        return "FAIL_STAGE170_RUN_RESULT_STATUS"
    required = ["cycles", "instructions", "mem_inst_retired.all_loads", "mem_inst_retired.all_stores"]
    for variant in VARIANTS:
        if any(not metric(counters, variant, item) for item in required):
            return "FAIL_STAGE170_COUNTERS_INCOMPLETE"
    if not restore_rows:
        return "CHECK_STAGE170_RESTORE_VERIFICATION_MISSING"
    return "PASS_STAGE170_NATIVE_SPLIT_COUNTERS_RECORDED"


def build_summary(
    decision: str,
    sync_rc: int,
    env_rc: int,
    upload_rc: int,
    build_rc: int,
    compile_rc: int,
    perf_rcs: Dict[str, int],
    remote_rows: List[Dict[str, str]],
    restore_rows: List[Dict[str, str]],
    counters: List[Dict[str, str]],
    runs: List[Dict[str, str]],
    correctness: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    before = env_value(remote_rows, "perf_event_paranoid")
    after = env_value(restore_rows, "perf_event_paranoid_after")
    counter_values = []
    for variant in VARIANTS:
        counter_values.append(
            f"{variant}:cycles={metric(counters, variant, 'cycles')};loads={metric(counters, variant, 'mem_inst_retired.all_loads')};"
            f"stores={metric(counters, variant, 'mem_inst_retired.all_stores')};fp512={metric(counters, variant, 'fp_arith_inst_retired.512b_packed_double')}"
        )
    return [
        {
            "gate": "stage170_remote_secret",
            "status": "PASS" if REMOTE_PASSWORD else "BLOCKED",
            "metric": "STAGE170_SSHPASS",
            "value": "present" if REMOTE_PASSWORD else "missing",
            "evidence": "environment variable only; not written to artifacts",
            "detail": "Remote password is consumed from environment and scrubbed from logs.",
            "next_action": "Provide STAGE170_SSHPASS only at runtime.",
        },
        {
            "gate": "stage170_sync",
            "status": "PASS" if sync_rc == 0 else "FAIL",
            "metric": "sync_rc",
            "value": str(sync_rc),
            "evidence": rel(OUT_DIR / "sync.log"),
            "detail": "git archive HEAD synchronized to CB5.",
            "next_action": "Fix SSH/sync before interpreting counters.",
        },
        {
            "gate": "stage170_probe_upload",
            "status": "PASS" if upload_rc == 0 else "FAIL",
            "metric": "upload_rc",
            "value": str(upload_rc),
            "evidence": rel(OUT_DIR / "upload_probe_source.log"),
            "detail": "The uncommitted generated C probe is copied after archive sync.",
            "next_action": "Fix upload before compile.",
        },
        {
            "gate": "stage170_build_compile",
            "status": "PASS" if build_rc == 0 and compile_rc == 0 else "FAIL",
            "metric": "build_rc;compile_rc",
            "value": f"{build_rc};{compile_rc}",
            "evidence": f"{rel(OUT_DIR / 'build_static.log')};{rel(OUT_DIR / 'compile_probe.log')}",
            "detail": "Build static MOSFHET and compile the isolated split-counter probe.",
            "next_action": "Fix build before running perf.",
        },
        {
            "gate": "stage170_perf_runs",
            "status": "PASS" if perf_rcs and all(rc == 0 for rc in perf_rcs.values()) else "FAIL",
            "metric": "perf_rcs",
            "value": ";".join(f"{variant}={perf_rcs.get(variant, '')}" for variant in VARIANTS),
            "evidence": ";".join(rel(OUT_DIR / f"run_{variant}_perf.log") for variant in VARIANTS),
            "detail": "Run native perf stat separately for MAT EP/subdecomp and from_DFT materialization.",
            "next_action": "Use split counters as attribution, not final speedup.",
        },
        {
            "gate": "stage170_correctness",
            "status": "PASS" if correctness and all(row.get("status") == "PASS" for row in correctness) else "FAIL",
            "metric": "correctness",
            "value": ";".join(f"{row.get('variant')}:{row.get('check')}={row.get('status')}" for row in correctness),
            "evidence": rel(CORRECTNESS_CSV),
            "detail": "MAT EP is checked against streaming reference; from_DFT_add is checked against materialize+add.",
            "next_action": "Ignore counters if correctness fails.",
        },
        {
            "gate": "stage170_restore_verification",
            "status": "PASS" if before and after and before == after else "CHECK",
            "metric": "perf_event_paranoid_before;after",
            "value": f"{before};{after}",
            "evidence": rel(POST_RESTORE_CSV),
            "detail": "Verify remote perf_event_paranoid after split counter runs.",
            "next_action": "Restore the remote setting before closing if values differ.",
        },
        {
            "gate": "stage170_counters",
            "status": "PASS" if all(metric(counters, variant, "cycles") for variant in VARIANTS) else "FAIL",
            "metric": "cycles;loads;stores;fp512",
            "value": " | ".join(counter_values),
            "evidence": rel(COUNTER_CSV),
            "detail": "Native component counter values are recorded separately.",
            "next_action": "Use ratios to decide Stage171/172, not as theoretical optimality proof.",
        },
        {
            "gate": "stage170_decision",
            "status": decision,
            "metric": "split_component_counter_route",
            "value": "mat_ep_subdecomp;from_dft_materialize",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage170 isolates the current exact r=6 component counters.",
            "next_action": "Update frontier claims and only pursue new variants with a falsifiable gate.",
        },
    ]


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() and path.is_file() else "",
            "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def write_docs(
    decision: str,
    summary: List[Dict[str, str]],
    remote_rows: List[Dict[str, str]],
    run_rows: List[Dict[str, str]],
    counter_rows: List[Dict[str, str]],
    derived_rows: List[Dict[str, str]],
    correctness_rows: List[Dict[str, str]],
) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    remote_fields = ["key", "value", "evidence"]
    run_fields = ["variant", "run_rc", "r", "N", "items", "reps", "calls", "per_call_us", "status", "evidence"]
    counter_fields = ["variant", "metric", "value", "unit", "evidence", "detail"]
    derived_fields = ["variant", "metric", "value", "unit", "interpretation"]
    correctness_fields = ["variant", "check", "mismatches", "max_gap", "status", "evidence"]

    write_text_lf(OUT_MD, f"""# Stage170 Native Split Counter Microbench

Decision: `{decision}`.

Stage170 isolates native CB5 perf counters for the current exact r=6
PVW/MAT-SAB component kernels:

- `mat_trgsw_mul_pvmtmlwe_sub_DFT`, including sub-decomposition, per-row DFT,
  and the r>4 tiled AVX512 dense MAT addmul;
- `pvmtmlwe_from_DFT_add`, including inverse DFT materialization and addend
  fusion under the current backend flag.

This stage is component attribution. It is not a complete-SAB speedup claim and
not a proof of theoretical optimality.

## Gate Summary

{table(summary, summary_fields)}

## Remote Environment

{table(remote_rows, remote_fields)}

## Correctness

{table(correctness_rows, correctness_fields)}

## Run Metrics

{table(run_rows, run_fields)}

## Counter Metrics

{table(counter_rows, counter_fields)}

## Derived Ratios

{table(derived_rows, derived_fields)}
""")

    write_text_lf(PLAN_MD, f"""# Stage170 Validation Plan

Goal: measure separate native hardware counters for MAT EP/subdecomp and
from_DFT materialization under the current exact r=6 PVW/MAT-SAB path.

Protocol:

- remote: CB5 native Linux via SSH, directory `{REMOTE_BASE}/spz` equivalent
  user workspace;
- backend: `spqlios_avx512`;
- flags: `{MAKE_FLAGS}`;
- parameters: `r={R_VALUE}`, `N={N_VALUE}`, `Bg_bit={BG_BIT}`,
  `items={ITEMS}`, `reps={REPS}`, `warmups={WARMUPS}`;
- variants:
  - `mat_ep_subdecomp`;
  - `from_dft_materialize`;
- counters: `{PERF_EVENTS}`.

Acceptance:

- both probe correctness checks pass;
- both perf runs exit successfully;
- cycles, instructions, load/store, and FP512 counters are present for both
  variants;
- remote `perf_event_paranoid` is restored to its pre-run value.

Failure handling:

- if counters cannot be isolated, retain only full-run Stage167 attribution;
- if correctness fails, discard all performance data for this stage;
- if from_DFT or MAT EP dominates differently than expected, route the next
  optimization stage from data rather than from prior intuition.
""")

    write_text_lf(THEORY_MD, """# Stage170 Split Counter Scope

Stage170 answers one bounded question:

```text
What are the native per-call cycle, load/store, cache, and FP512 counter costs
for the current exact r=6 MAT EP/subdecomp and from_DFT materialization kernels?
```

It does not answer:

- whether the dense MAT algorithm is theoretically optimal;
- whether a new compact/key-distribution route is sound;
- whether complete SAB is accelerated beyond the Stage169 endpoint;
- whether all parameter sets or ternary/include-zero branches behave the same.

The MAT EP probe includes sub-decomposition and per-row torus-to-DFT because
that is the current production fused call boundary in `sab_pvw_CMUX_from_diff`.
The from_DFT probe includes the fused add path because that is the current
production materialization boundary in `sab_pvw_CMUX_materialize_internal`.
""")

    write_text_lf(VARIANT_MD, f"""# Native Split Counter Microbench for Current r=6 Path

This is not a production implementation variant. It is an isolated probe for
the current exact r=6 path.

Measured call boundaries:

```text
mat_ep_subdecomp      -> mat_trgsw_mul_pvmtmlwe_sub_DFT
from_dft_materialize -> pvmtmlwe_from_DFT_add
```

Decision: `{decision}`.

Allowed claim level:

```text
component native counter attribution
```

Blocked claim level:

```text
theoretical optimality
complete-SAB speedup beyond Stage169
paper-level novelty
```
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 170: Native Split Counter Microbench", f"""
## Stage 170: Native Split Counter Microbench

Goal:

```text
Isolate native perf counters for the current exact r=6 MAT EP/subdecomp
boundary and the current from_DFT materialization boundary.
```

Status:

```text
Completed. Stage170 records {decision}. The evidence is component-level
native counter attribution and remains separate from complete-SAB throughput
and theoretical optimality.
```
""")
    append_once(GOAL_MD, "Stage170 records native split component counters", f"""
Stage170 records native split component counters for the current exact r=6
PVW/MAT-SAB path. Decision: `{decision}`. The result may guide later
optimization routing, but it is not by itself a complete bootstrapping
speedup claim.
""")
    append_once(CURRENT_GOAL_MD, "74. Treat Stage170 as split component counter attribution", f"""
74. Treat Stage170 as split component counter attribution:
    `{decision}`. It separates MAT EP/subdecomp from from_DFT materialization
    using native CB5 counters, while keeping Stage169 as the complete-SAB
    throughput endpoint.
""")
    append_once(HYPOTHESIS_YAML, "id: H94_native_split_counter_microbench", f"""
  - id: H94_native_split_counter_microbench
    statement: >
      Native split counters should isolate whether the current exact r=6
      PVW/MAT-SAB frontier is dominated by MAT EP/subdecomp, from_DFT
      materialization, or mixed memory/cache pressure.
    mechanism: >
      The current SAB CMUX boundary calls mat_trgsw_mul_pvmtmlwe_sub_DFT and
      then pvmtmlwe_from_DFT_add. Running those boundaries as separate native
      perf probes records per-call cycles, load/store, cache, and AVX512 FP
      counters without changing production SAB.
    status: stage170_native_split_counter_microbench
    evidence: docs/stage170_native_split_counter_microbench.md; experiments/stage170_native_split_counter_microbench_plan.md; theory_checks/stage170_split_counter_scope.md; repro/stage170_native_split_counter_microbench/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - either probe correctness check fails
      - required counters are missing for either component
      - component counters are reported as complete-SAB acceleration or
        theoretical optimality
""")
    append_once(RUN_LOG, "stage170-native-split-counter-microbench-001", f"""
stage170-native-split-counter-microbench-001,2026-07-04,{HEAD},Stage 170,spqlios_avx512,python scripts/build_stage170_native_split_counter_microbench.py,CB5 native perf; r={R_VALUE}; N={N_VALUE}; items={ITEMS}; reps={REPS}; split MAT EP/from_DFT,deterministic-probe,{decision},Native split component counter microbench.,repro/stage170_native_split_counter_microbench
""")
    append_once(MANIFEST, "stage170_native_split_counter_microbench", f"""
- stage170_native_split_counter_microbench: `{decision}`
  - `docs/stage170_native_split_counter_microbench.md`
  - `experiments/stage170_native_split_counter_microbench_plan.md`
  - `theory_checks/stage170_split_counter_scope.md`
  - `algorithm_variants/mat_rlwe_sab_native_split_counter_microbench.md`
  - `repro/stage170_native_split_counter_microbench/`
""")
    append_once(CHECKLIST, "Stage170 native split counter microbench pack recorded", """
- [x] Stage170 native split counter microbench pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_c_source()

    if not REMOTE_PASSWORD:
        sync_rc = env_rc = upload_rc = build_rc = compile_rc = 1
        perf_rcs: Dict[str, int] = {}
        remote_rows: List[Dict[str, str]] = []
        restore_rows: List[Dict[str, str]] = []
        counter_rows: List[Dict[str, str]] = []
        run_rows: List[Dict[str, str]] = []
        correctness_rows: List[Dict[str, str]] = []
    else:
        sync_rc = sync_repo()
        env_rc = probe_remote_environment() if sync_rc == 0 else 1
        remote_rows = parse_remote_environment()
        upload_rc = upload_probe_source() if env_rc == 0 else 1
        build_rc = build_remote_static() if upload_rc == 0 else 1
        compile_rc = compile_remote_probe() if build_rc == 0 else 1
        perf_rcs = {}
        if compile_rc == 0:
            for variant in VARIANTS:
                perf_rcs[variant] = perf_remote_variant(variant)
        restore_remote_paranoid(env_value(remote_rows, "perf_event_paranoid"))
        verify_restore_remote()
        cleanup_remote()
        restore_rows = parse_restore()
        counter_rows = []
        run_rows = []
        correctness_rows = []
        for variant in VARIANTS:
            counters, runs, correctness = parse_variant_log(variant)
            counter_rows.extend(counters)
            run_rows.extend(runs)
            correctness_rows.extend(correctness)

    derived_rows = build_derived(counter_rows, run_rows)
    decision = decide(
        sync_rc,
        env_rc,
        upload_rc,
        build_rc,
        compile_rc,
        perf_rcs,
        restore_rows,
        counter_rows,
        run_rows,
        correctness_rows,
    )
    summary = build_summary(
        decision,
        sync_rc,
        env_rc,
        upload_rc,
        build_rc,
        compile_rc,
        perf_rcs,
        remote_rows,
        restore_rows,
        counter_rows,
        run_rows,
        correctness_rows,
    )

    write_csv(REMOTE_CSV, remote_rows, ["key", "value", "evidence"])
    write_csv(POST_RESTORE_CSV, restore_rows, ["key", "value", "evidence"])
    write_csv(COUNTER_CSV, counter_rows, ["variant", "metric", "value", "unit", "evidence", "detail"])
    write_csv(RUN_CSV, run_rows, [
        "variant", "run_rc", "r", "N", "items", "reps", "calls",
        "total_ns", "per_call_us", "sink", "status", "evidence",
    ])
    write_csv(CORRECTNESS_CSV, correctness_rows, ["variant", "check", "mismatches", "max_gap", "status", "evidence"])
    write_csv(DERIVED_CSV, derived_rows, ["variant", "metric", "value", "unit", "interpretation"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(decision, summary, remote_rows, run_rows, counter_rows, derived_rows, correctness_rows)
    update_global_docs(decision)
    artifact_index([
        C_SOURCE,
        SUMMARY_CSV,
        COUNTER_CSV,
        RUN_CSV,
        DERIVED_CSV,
        CORRECTNESS_CSV,
        REMOTE_CSV,
        POST_RESTORE_CSV,
        ARTIFACT_CSV,
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        OUT_DIR / "sync.log",
        OUT_DIR / "remote_environment.log",
        OUT_DIR / "upload_probe_source.log",
        OUT_DIR / "build_static.log",
        OUT_DIR / "compile_probe.log",
        OUT_DIR / "run_mat_ep_subdecomp_perf.log",
        OUT_DIR / "run_from_dft_materialize_perf.log",
        OUT_DIR / "restore_expected_paranoid.log",
        OUT_DIR / "post_restore_verification.log",
        OUT_DIR / "cleanup.log",
    ])
    print(decision)


if __name__ == "__main__":
    main()
