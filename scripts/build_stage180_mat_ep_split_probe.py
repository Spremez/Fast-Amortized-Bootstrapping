#!/usr/bin/env python3
"""Stage180: split MAT EP/subdecomp into decompose, DFT, and addmul phases."""

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
OUT_DIR = ROOT / "repro" / "stage180_mat_ep_split_probe"

C_SOURCE = OUT_DIR / "stage180_mat_ep_split_probe.c"
SUMMARY_CSV = OUT_DIR / "summary.csv"
RUN_CSV = OUT_DIR / "run_metrics.csv"
COUNTER_CSV = OUT_DIR / "counter_metrics.csv"
CORRECTNESS_CSV = OUT_DIR / "correctness.csv"
DERIVED_CSV = OUT_DIR / "derived_projection.csv"
REMOTE_CSV = OUT_DIR / "remote_environment.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage180_mat_ep_split_probe.md"
PLAN_MD = ROOT / "experiments" / "stage180_mat_ep_split_probe_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage180_mat_ep_split_probe_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_mat_ep_split_probe.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE179_SUMMARY = ROOT / "repro" / "stage179_mat_ep_microarch_audit" / "summary.csv"

REMOTE_USER = os.environ.get("STAGE180_REMOTE_USER", "delld")
REMOTE_HOST = os.environ.get("STAGE180_REMOTE_HOST", "192.168.107.220")
REMOTE_BASE = os.environ.get("STAGE180_REMOTE_BASE", "/home/delld/spz")
REMOTE_PASSWORD = (
    os.environ.get("STAGE180_SSHPASS")
    or os.environ.get("STAGE170_SSHPASS")
    or os.environ.get("STAGE169_SSHPASS")
    or ""
)
MAKE_JOBS = os.environ.get("STAGE180_JOBS", "$(nproc)")
R_VALUE = int(os.environ.get("STAGE180_R", "6"))
N_VALUE = int(os.environ.get("STAGE180_N", "2048"))
ITEMS = int(os.environ.get("STAGE180_ITEMS", "128"))
REPS = int(os.environ.get("STAGE180_REPS", "8"))
WARMUPS = int(os.environ.get("STAGE180_WARMUPS", "2"))
BG_BIT = int(os.environ.get("STAGE180_BG_BIT", "23"))
MAT_EP_FULL_SHARE = float(os.environ.get("STAGE180_MAT_EP_FULL_SHARE", "0.603899465"))

HEAD = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
REMOTE_DIR_NAME = f"Fast-Amortized-Bootstrapping-stage180-{HEAD}"
REMOTE_DIR = f"{REMOTE_BASE}/{REMOTE_DIR_NAME}"
REMOTE_STAGE_DIR = f"{REMOTE_DIR}/repro/stage180_mat_ep_split_probe"
REMOTE_PROBE_SOURCE = f"{REMOTE_STAGE_DIR}/stage180_mat_ep_split_probe.c"
REMOTE_PROBE_BINARY = f"{REMOTE_STAGE_DIR}/stage180_mat_ep_split_probe"

MAKE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "ENABLE_PVW_TMLWE=true MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
    "SAB_PVW_SUB_DECOMP_FUSION=true"
)

COMPILE_FLAGS = (
    "-O3 -march=native -Wall -Wextra "
    "-DUSE_SPQLIOS -DAVX512_OPT "
    "-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED "
    "-DMAT_TRGSW_AVX512_RGT4_FUSED "
)

PERF_EVENTS = (
    "cycles,instructions,cache-references,cache-misses,branches,branch-misses,"
    "mem_inst_retired.all_loads,mem_inst_retired.all_stores,"
    "fp_arith_inst_retired.512b_packed_double,"
    "fp_arith_inst_retired.256b_packed_double"
)

VARIANTS = [
    "sub_decompose",
    "torus_to_dft_rows",
    "addmul_from_dec_dft",
    "combined_current",
]

PERF_LINE_RE = re.compile(r"^\s*([\d,]+)\s+([A-Za-z0-9_.-]+)\b")
ELAPSED_RE = re.compile(r"^\s*([\d.]+)\s+seconds time elapsed")
USER_RE = re.compile(r"^\s*([\d.]+)\s+seconds user")
SYS_RE = re.compile(r"^\s*([\d.]+)\s+seconds sys")
RESULT_RE = re.compile(
    r"RESULT180,(?P<variant>[^,]+),(?P<r>\d+),(?P<N>\d+),"
    r"(?P<items>\d+),(?P<reps>\d+),(?P<calls>\d+),"
    r"(?P<total_ns>\d+),(?P<per_call_us>[0-9.]+),(?P<sink>\d+),"
    r"(?P<status>[^,\s]+)"
)
CORRECT_RE = re.compile(
    r"CORRECT180,(?P<check>[^,]+),(?P<mismatches>\d+),"
    r"(?P<max_gap>\d+),(?P<status>[^,\s]+)"
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


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
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out) + "\n"


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text_lf(path, current + text.lstrip("\n"))


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
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
        "-o UserKnownHostsFile=/tmp/codex_stage180_known_hosts "
        "-o ConnectTimeout=12 "
        f"{shlex.quote(REMOTE_USER + '@' + REMOTE_HOST)}"
    )


def scp_prefix() -> str:
    return (
        f"sshpass -p {shlex.quote(REMOTE_PASSWORD)} scp "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage180_known_hosts "
        "-o ConnectTimeout=12 "
    )


def remote_command(command: str) -> str:
    return f"{ssh_prefix()} {shlex.quote(command)}"


def write_c_source() -> None:
    source = f'''
#include "mosfhet.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE180_R
#define STAGE180_R {R_VALUE}
#endif
#ifndef STAGE180_N
#define STAGE180_N {N_VALUE}
#endif
#ifndef STAGE180_ITEMS
#define STAGE180_ITEMS {ITEMS}
#endif
#ifndef STAGE180_REPS
#define STAGE180_REPS {REPS}
#endif
#ifndef STAGE180_WARMUPS
#define STAGE180_WARMUPS {WARMUPS}
#endif
#ifndef STAGE180_BG_BIT
#define STAGE180_BG_BIT {BG_BIT}
#endif

#define static
#include "src/mosfhet/src/mattrgsw.c"
#undef static

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

static void fill_selector(MAT_TRGSW_DFT selector) {{
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE180_N);
  const int rows = 1 + STAGE180_R;
  for (int row = 0; row < rows; row++) {{
    fill_poly(tmp, 0xabcdef0011223344ULL ^ (uint64_t) row);
    polynomial_torus_to_DFT(selector->samples[row]->a[0], tmp);
    for (int lane = 0; lane < STAGE180_R; lane++) {{
      fill_poly(tmp, 0x6677889900aabbccULL ^ ((uint64_t) row << 16) ^ (uint64_t) lane);
      polynomial_torus_to_DFT(selector->samples[row]->b[lane], tmp);
    }}
  }}
  free_polynomial(tmp);
}}

static uint64_t checksum_torus_rows(TorusPolynomial *rows, int count) {{
  uint64_t acc = 0xcbf29ce484222325ULL;
  for (int row = 0; row < count; row++) {{
    for (int i = 0; i < rows[row]->N; i += 17) {{
      acc ^= (uint64_t) rows[row]->coeffs[i] + (acc << 6) + (acc >> 2);
    }}
  }}
  return acc;
}}

static uint64_t checksum_dft_rows(DFT_Polynomial *rows, int count) {{
  uint64_t acc = 0x84222325cbf29ce4ULL;
  for (int row = 0; row < count; row++) {{
    const uint64_t *v = (const uint64_t *) rows[row]->coeffs;
    for (int i = 0; i < rows[row]->N; i += 17) {{
      acc ^= v[i] + (acc << 6) + (acc >> 2);
    }}
  }}
  return acc;
}}

static uint64_t checksum_dft_out(PVW_TMLWE_DFT out) {{
  uint64_t acc = 0x6a09e667f3bcc909ULL;
  const uint64_t *a = (const uint64_t *) out->a[0]->coeffs;
  for (int i = 0; i < STAGE180_N; i += 17) acc ^= a[i] + (acc << 6) + (acc >> 2);
  for (int lane = 0; lane < STAGE180_R; lane++) {{
    const uint64_t *b = (const uint64_t *) out->b[lane]->coeffs;
    for (int i = 0; i < STAGE180_N; i += 17) acc ^= b[i] + (acc << 6) + (acc >> 2);
  }}
  return acc;
}}

static uint64_t compare_torus(PVW_TMLWE a, PVW_TMLWE b, uint64_t *max_gap) {{
  uint64_t mismatches = 0;
  for (int i = 0; i < STAGE180_N; i++) {{
    uint64_t x = (uint64_t) a->a[0]->coeffs[i];
    uint64_t y = (uint64_t) b->a[0]->coeffs[i];
    uint64_t gap = x >= y ? x - y : y - x;
    if (gap != 0) mismatches++;
    if (gap > *max_gap) *max_gap = gap;
  }}
  for (int lane = 0; lane < STAGE180_R; lane++) {{
    for (int i = 0; i < STAGE180_N; i++) {{
      uint64_t x = (uint64_t) a->b[lane]->coeffs[i];
      uint64_t y = (uint64_t) b->b[lane]->coeffs[i];
      uint64_t gap = x >= y ? x - y : y - x;
      if (gap != 0) mismatches++;
      if (gap > *max_gap) *max_gap = gap;
    }}
  }}
  return mismatches;
}}

static void fill_dec_bank(TorusPolynomial *bank, int rows) {{
  for (int item = 0; item < STAGE180_ITEMS; item++) {{
    for (int row = 0; row < rows; row++) {{
      fill_poly(bank[item * rows + row], 0x1111222233334444ULL ^ ((uint64_t)item << 8) ^ (uint64_t)row);
    }}
  }}
}}

static void fill_dec_dft_bank(DFT_Polynomial *bank, int rows) {{
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE180_N);
  for (int item = 0; item < STAGE180_ITEMS; item++) {{
    for (int row = 0; row < rows; row++) {{
      fill_poly(tmp, 0x5555666677778888ULL ^ ((uint64_t)item << 8) ^ (uint64_t)row);
      polynomial_torus_to_DFT(bank[item * rows + row], tmp);
    }}
  }}
  free_polynomial(tmp);
}}

static uint64_t run_variant(const char *variant) {{
  const int rows = 1 + STAGE180_R;
  init_fft(STAGE180_N);
  MAT_TRGSW_DFT selector =
      mat_trgsw_alloc_new_DFT_sample(1, STAGE180_BG_BIT, 1, STAGE180_R, STAGE180_N);
  fill_selector(selector);
  PVW_TMLWE *in1 = pvmtmlwe_alloc_new_sample_array(STAGE180_ITEMS, 1, STAGE180_R, STAGE180_N);
  PVW_TMLWE *in2 = pvmtmlwe_alloc_new_sample_array(STAGE180_ITEMS, 1, STAGE180_R, STAGE180_N);
  for (int item = 0; item < STAGE180_ITEMS; item++) {{
    fill_pvmtmlwe(in1[item], 0x100000000ULL + (uint64_t)item);
    fill_pvmtmlwe(in2[item], 0x200000000ULL + (uint64_t)item);
  }}
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, STAGE180_N);
  PVW_TMLWE_DFT out = pvmtmlwe_alloc_new_DFT_sample(1, STAGE180_R, STAGE180_N);
  TorusPolynomial *dec_bank = polynomial_new_array_of_torus_polynomials(STAGE180_N, rows * STAGE180_ITEMS);
  DFT_Polynomial *dft_bank = polynomial_new_array_of_polynomials_DFT(STAGE180_N, rows * STAGE180_ITEMS);
  fill_dec_bank(dec_bank, rows);
  fill_dec_dft_bank(dft_bank, rows);

  PVW_TMLWE_DFT current = pvmtmlwe_alloc_new_DFT_sample(1, STAGE180_R, STAGE180_N);
  PVW_TMLWE_DFT split = pvmtmlwe_alloc_new_DFT_sample(1, STAGE180_R, STAGE180_N);
  mat_trgsw_mul_pvmtmlwe_sub_DFT(current, in1[0], in2[0], selector, scratch);
  mat_trgsw_sub_decompose(in1[0], in2[0], scratch->dec, selector->Q, selector->T);
  for (int row = 0; row < rows; row++) {{
    polynomial_torus_to_DFT(scratch->dec_dft[row], scratch->dec[row]);
  }}
  mat_trgsw_mul_pvmtmlwe_DFT_from_dec(split, selector, scratch->dec_dft);
  PVW_TMLWE current_torus = pvmtmlwe_alloc_new_sample(1, STAGE180_R, STAGE180_N);
  PVW_TMLWE split_torus = pvmtmlwe_alloc_new_sample(1, STAGE180_R, STAGE180_N);
  pvmtmlwe_from_DFT(current_torus, current);
  pvmtmlwe_from_DFT(split_torus, split);
  uint64_t max_gap = 0;
  uint64_t mismatches = compare_torus(current_torus, split_torus, &max_gap);
  printf("CORRECT180,combined_vs_split,%" PRIu64 ",%" PRIu64 ",%s\\n",
      mismatches, max_gap, mismatches == 0 ? "PASS" : "FAIL");

  uint64_t sink = 0;
  for (int w = 0; w < STAGE180_WARMUPS; w++) {{
    for (int item = 0; item < STAGE180_ITEMS; item++) {{
      if (strcmp(variant, "sub_decompose") == 0) {{
        mat_trgsw_sub_decompose(in1[item], in2[item], scratch->dec,
            selector->Q, selector->T);
      }} else if (strcmp(variant, "torus_to_dft_rows") == 0) {{
        for (int row = 0; row < rows; row++) {{
          polynomial_torus_to_DFT(scratch->dec_dft[row], dec_bank[item * rows + row]);
        }}
      }} else if (strcmp(variant, "addmul_from_dec_dft") == 0) {{
        mat_trgsw_mul_pvmtmlwe_DFT_from_dec(out, selector, &dft_bank[item * rows]);
      }} else if (strcmp(variant, "combined_current") == 0) {{
        mat_trgsw_mul_pvmtmlwe_sub_DFT(out, in1[item], in2[item], selector, scratch);
      }}
    }}
  }}
  uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE180_REPS; rep++) {{
    for (int item = 0; item < STAGE180_ITEMS; item++) {{
      if (strcmp(variant, "sub_decompose") == 0) {{
        mat_trgsw_sub_decompose(in1[item], in2[item], scratch->dec,
            selector->Q, selector->T);
      }} else if (strcmp(variant, "torus_to_dft_rows") == 0) {{
        for (int row = 0; row < rows; row++) {{
          polynomial_torus_to_DFT(scratch->dec_dft[row], dec_bank[item * rows + row]);
        }}
      }} else if (strcmp(variant, "addmul_from_dec_dft") == 0) {{
        mat_trgsw_mul_pvmtmlwe_DFT_from_dec(out, selector, &dft_bank[item * rows]);
      }} else if (strcmp(variant, "combined_current") == 0) {{
        mat_trgsw_mul_pvmtmlwe_sub_DFT(out, in1[item], in2[item], selector, scratch);
      }} else {{
        fprintf(stderr, "unknown variant: %s\\n", variant);
        return 2;
      }}
    }}
  }}
  if (strcmp(variant, "sub_decompose") == 0) {{
    sink = checksum_torus_rows(scratch->dec, rows);
  }} else if (strcmp(variant, "torus_to_dft_rows") == 0) {{
    sink = checksum_dft_rows(scratch->dec_dft, rows);
  }} else {{
    sink = checksum_dft_out(out);
  }}
  uint64_t ns = now_ns() - start;
  uint64_t calls = (uint64_t) STAGE180_REPS * (uint64_t) STAGE180_ITEMS;
  double per_call_us = ((double)ns) / ((double)calls) / 1000.0;
  printf("RESULT180,%s,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",%s\\n",
      variant, STAGE180_R, STAGE180_N, STAGE180_ITEMS, STAGE180_REPS,
      calls, ns, per_call_us, sink, mismatches == 0 ? "PASS" : "FAIL");

  free_pvmtmlwe(current_torus);
  free_pvmtmlwe(split_torus);
  free_pvmtmlwe_DFT(current);
  free_pvmtmlwe_DFT(split);
  for (int i = 0; i < rows * STAGE180_ITEMS; i++) free_DFT_polynomial(dft_bank[i]);
  free(dft_bank);
  free_array_of_polynomials(dec_bank, rows * STAGE180_ITEMS);
  free_pvmtmlwe_DFT(out);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe_array(in1, STAGE180_ITEMS);
  free_pvmtmlwe_array(in2, STAGE180_ITEMS);
  free_mat_trgsw_DFT(selector);
  return mismatches == 0 ? 0 : 1;
}}

int main(int argc, char **argv) {{
  if (argc != 2) {{
    fprintf(stderr, "usage: %s sub_decompose|torus_to_dft_rows|addmul_from_dec_dft|combined_current\\n", argv[0]);
    return 2;
  }}
  return (int) run_variant(argv[1]);
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
    mkdir_rc = run_wsl(remote_command(f"mkdir -p {shlex.quote(REMOTE_STAGE_DIR)}"), OUT_DIR / "upload_mkdir.log", timeout=60)
    if mkdir_rc != 0:
        return mkdir_rc
    target = f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PROBE_SOURCE}"
    cmd = f"{scp_prefix()} {shlex.quote(wsl_path(C_SOURCE))} {shlex.quote(target)}"
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
        f"gcc {COMPILE_FLAGS} "
        f"-DSTAGE180_R={R_VALUE} -DSTAGE180_N={N_VALUE} "
        f"-DSTAGE180_ITEMS={ITEMS} -DSTAGE180_REPS={REPS} "
        f"-DSTAGE180_WARMUPS={WARMUPS} -DSTAGE180_BG_BIT={BG_BIT} "
        "-I . -I src/mosfhet/include "
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
    return run_wsl(remote_command(cmd), OUT_DIR / f"run_{variant}_perf.log", timeout=1800)


def cleanup_remote() -> int:
    cmd = f"cd {shlex.quote(REMOTE_DIR)}/src/mosfhet && (make clean >/dev/null 2>&1 || true)"
    return run_wsl(remote_command(cmd), OUT_DIR / "cleanup.log", timeout=300)


def verify_restore_remote() -> int:
    cmd = "printf 'perf_event_paranoid_after,'; cat /proc/sys/kernel/perf_event_paranoid"
    return run_wsl(remote_command(cmd), OUT_DIR / "post_restore_verification.log", timeout=60)


def parse_remote_environment() -> List[Dict[str, str]]:
    text = read_text(OUT_DIR / "remote_environment.log")
    rows: List[Dict[str, str]] = []
    for key in ["hostname", "whoami", "uname", "perf", "perf_event_paranoid", "remote_dir"]:
        m = re.search(rf"^{key},(.+)$", text, re.MULTILINE)
        if m:
            rows.append({"key": key, "value": m.group(1).strip(), "evidence": rel(OUT_DIR / "remote_environment.log")})
    model = re.search(r"^Model name:\s+(.+)$", text, re.MULTILINE)
    flags = re.search(r"^Flags:\s+(.+)$", text, re.MULTILINE)
    if model:
        rows.append({"key": "cpu_model", "value": model.group(1).strip(), "evidence": rel(OUT_DIR / "remote_environment.log")})
    if flags:
        rows.append({"key": "has_avx512f", "value": "yes" if "avx512f" in flags.group(1) else "no", "evidence": rel(OUT_DIR / "remote_environment.log")})
    return rows


def parse_variant_log(variant: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    path = OUT_DIR / f"run_{variant}_perf.log"
    text = read_text(path)
    counters: List[Dict[str, str]] = []
    runs: List[Dict[str, str]] = []
    correctness: List[Dict[str, str]] = []
    rc_match = re.search(r"^returncode:\s+(\d+)$", text, re.MULTILINE)
    run_rc = rc_match.group(1) if rc_match else ""

    for raw in text.splitlines():
        m = PERF_LINE_RE.match(raw)
        if m:
            counters.append({
                "variant": variant,
                "metric": m.group(2),
                "value": m.group(1).replace(",", ""),
                "unit": "count",
                "evidence": rel(path),
                "detail": raw.strip(),
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
                    "detail": raw.strip(),
                })
                break

    for line in text.splitlines():
        m = RESULT_RE.search(line)
        if m:
            runs.append({
                "variant": variant,
                "run_rc": run_rc,
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
        c = CORRECT_RE.search(line)
        if c:
            correctness.append({
                "variant": variant,
                "check": c.group("check"),
                "mismatches": c.group("mismatches"),
                "max_gap": c.group("max_gap"),
                "status": c.group("status"),
                "evidence": rel(path),
            })
    if not runs:
        runs.append({
            "variant": variant,
            "run_rc": run_rc,
            "r": str(R_VALUE),
            "N": str(N_VALUE),
            "items": str(ITEMS),
            "reps": str(REPS),
            "calls": "0",
            "total_ns": "0",
            "per_call_us": "",
            "sink": "",
            "status": "NO_RESULT",
            "evidence": rel(path),
        })
    return counters, runs, correctness


def run_remote_pipeline() -> Dict[str, int]:
    rcs: Dict[str, int] = {}
    rcs["env"] = probe_remote_environment()
    rcs["sync"] = sync_repo()
    rcs["upload"] = upload_probe_source() if rcs["sync"] == 0 else 1
    rcs["build"] = build_remote_static() if rcs["upload"] == 0 else 1
    rcs["compile"] = compile_remote_probe() if rcs["build"] == 0 else 1
    for variant in VARIANTS:
        rcs[f"run_{variant}"] = perf_remote_variant(variant) if rcs["compile"] == 0 else 1
    rcs["restore_check"] = verify_restore_remote() if rcs["env"] == 0 else 1
    rcs["cleanup"] = cleanup_remote() if rcs["sync"] == 0 else 1
    return rcs


def build_derived_rows(run_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_variant = {row["variant"]: row for row in run_rows if row.get("per_call_us")}
    rows: List[Dict[str, str]] = []
    if "combined_current" not in by_variant:
        return [{
            "metric": "stage180_projection",
            "value": "missing_combined_current",
            "unit": "",
            "evidence": rel(RUN_CSV),
            "interpretation": "No projection because combined current timing is missing.",
        }]
    combined = float(by_variant["combined_current"]["per_call_us"])
    split_sum = 0.0
    for variant in ["sub_decompose", "torus_to_dft_rows", "addmul_from_dec_dft"]:
        if variant in by_variant:
            val = float(by_variant[variant]["per_call_us"])
            split_sum += val
            rows.append({
                "metric": f"{variant}_share_of_combined",
                "value": f"{val / combined:.9f}",
                "unit": "share",
                "evidence": rel(RUN_CSV),
                "interpretation": f"{variant} share relative to current combined MAT EP/subdecomp probe.",
            })
    rows.append({
        "metric": "split_sum_over_combined",
        "value": f"{split_sum / combined:.9f}",
        "unit": "ratio",
        "evidence": rel(RUN_CSV),
        "interpretation": "Split probes are isolated microbenches; ratio checks whether they roughly cover the combined path.",
    })
    for variant in ["sub_decompose", "torus_to_dft_rows", "addmul_from_dec_dft"]:
        if variant in by_variant:
            share_combined = float(by_variant[variant]["per_call_us"]) / combined
            full_share = share_combined * MAT_EP_FULL_SHARE
            required_component_speedup = full_share / ((1 / 1.03) - (1 - full_share)) if full_share > 0 else 0.0
            rows.append({
                "metric": f"{variant}_full_sab_share_and_3pct_requirement",
                "value": f"{full_share:.9f};{required_component_speedup:.9f}",
                "unit": "share;speedup",
                "evidence": rel(RUN_CSV),
                "interpretation": "Estimated full-SAB share and subcomponent speedup needed for a 3% complete-SAB gain.",
            })
    return rows


def build_next_rows(decision: str) -> List[Dict[str, str]]:
    if decision == "PASS_STAGE180_SPLIT_PROBE_RECORDED":
        return [
            {
                "priority": "P0",
                "stage": "181",
                "name": "decide conditional implementation",
                "entry_condition": "Stage180 split rows are complete and correctness passes.",
                "gate": "Open an implementation only if one subcomponent can plausibly yield >=3% full-SAB gain.",
                "failure_rule": "If projection is too small, close exact-path tuning.",
            },
            {
                "priority": "P1",
                "stage": "182",
                "name": "negative frontier or implementation",
                "entry_condition": "Stage181 decision.",
                "gate": "Either write a flag-only implementation or write the negative frontier.",
                "failure_rule": "No speculative retuning.",
            },
        ]
    return [
        {
            "priority": "P0",
            "stage": "180-rerun",
            "name": "rerun split probe with remote credentials",
            "entry_condition": "Remote credentials or compile/runtime blocker resolved.",
            "gate": "All variants produce RESULT180 and correctness PASS.",
            "failure_rule": "Do not implement code before split probe data exists.",
        }
    ]


def build_summary_rows(rcs: Dict[str, int], run_rows: List[Dict[str, str]], correctness_rows: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
    if not REMOTE_PASSWORD:
        decision = "SKIP_STAGE180_REMOTE_SECRET_MISSING"
    elif any(rcs.get(k, 1) != 0 for k in ["env", "sync", "upload", "build", "compile"]):
        decision = "BLOCK_STAGE180_REMOTE_SETUP_OR_COMPILE_FAILED"
    elif any(row.get("status") != "PASS" for row in run_rows):
        decision = "BLOCK_STAGE180_PROBE_RUN_FAILED"
    elif any(row.get("status") != "PASS" for row in correctness_rows):
        decision = "BLOCK_STAGE180_CORRECTNESS_FAILED"
    else:
        decision = "PASS_STAGE180_SPLIT_PROBE_RECORDED"
    rows = [
        {
            "gate": "stage180_inputs",
            "status": "PASS" if STAGE179_SUMMARY.exists() else "FAIL",
            "metric": "stage179_summary_present",
            "value": "1" if STAGE179_SUMMARY.exists() else "0",
            "evidence": rel(STAGE179_SUMMARY),
            "detail": "Stage180 follows the Stage179 no-code split-probe route.",
            "next_action": "Repair Stage179 first if missing.",
        },
        {
            "gate": "stage180_remote_secret",
            "status": "PASS" if REMOTE_PASSWORD else "SKIPPED",
            "metric": "STAGE180_SSHPASS",
            "value": "present" if REMOTE_PASSWORD else "missing",
            "evidence": "environment variable only; not written to artifacts",
            "detail": "Remote password is consumed from environment and scrubbed from logs.",
            "next_action": "Set STAGE180_SSHPASS for CB5 execution.",
        },
        {
            "gate": "stage180_remote_pipeline",
            "status": "PASS" if rcs and all(v == 0 for k, v in rcs.items() if k.startswith("run_") or k in ["env", "sync", "upload", "build", "compile"]) else ("SKIPPED" if not REMOTE_PASSWORD else "FAIL"),
            "metric": "rcs",
            "value": ";".join(f"{k}={v}" for k, v in sorted(rcs.items())) if rcs else "not_run",
            "evidence": rel(OUT_DIR),
            "detail": "Builds MOSFHET and runs split variants under native perf on CB5.",
            "next_action": "Fix first nonzero rc before interpreting timings.",
        },
        {
            "gate": "stage180_correctness",
            "status": "PASS" if correctness_rows and all(row.get("status") == "PASS" for row in correctness_rows) else ("SKIPPED" if not correctness_rows else "FAIL"),
            "metric": "checks",
            "value": ";".join(f"{row['variant']}:{row['status']}" for row in correctness_rows) if correctness_rows else "none",
            "evidence": rel(CORRECTNESS_CSV),
            "detail": "Combined current path is checked against split decomposition/DFT/addmul for each variant run.",
            "next_action": "Do not use timings if correctness fails.",
        },
        {
            "gate": "stage180_decision",
            "status": decision,
            "metric": "route",
            "value": "stage181" if decision == "PASS_STAGE180_SPLIT_PROBE_RECORDED" else "rerun_or_fix",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage180 either records split data or explicitly blocks code permission.",
            "next_action": "Proceed only according to next_stage_queue.",
        },
    ]
    return decision, rows


def write_docs(decision: str, summary_rows: List[Dict[str, str]], run_rows: List[Dict[str, str]],
               derived_rows: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> None:
    write_text_lf(OUT_MD, f"""# Stage180 MAT EP Split Probe

Decision: `{decision}`.

Stage180 measures the internal pieces of `mat_trgsw_mul_pvmtmlwe_sub_DFT`:

- `sub_decompose`
- `torus_to_dft_rows`
- `addmul_from_dec_dft`
- `combined_current`

The probe includes the current `mattrgsw.c` so it can call the current static
`mat_trgsw_sub_decompose` and `mat_trgsw_mul_pvmtmlwe_DFT_from_dec` boundaries.
This is a measurement gate, not an implementation change.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Run Metrics

{table(run_rows, ["variant", "run_rc", "r", "N", "items", "reps", "calls", "total_ns", "per_call_us", "status", "evidence"])}
## Derived Projection

{table(derived_rows, ["metric", "value", "unit", "evidence", "interpretation"])}
## Next Queue

{table(next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])}
""")

    write_text_lf(PLAN_MD, """# Stage180 Plan

Goal: split the current exact MAT EP/subdecomp hot block before granting any
new AVX512 implementation permission.

Correctness gate:

- Combined current output must match split decompose -> DFT -> addmul output.

Performance gate:

- Record per-call timings and perf counters for `sub_decompose`,
  `torus_to_dft_rows`, `addmul_from_dec_dft`, and `combined_current`.
- A later implementation branch needs a projection to at least 3% complete-SAB
  gain.

Failure handling:

- Missing remote credentials, compile failure, run failure, or correctness
  failure all block code work.
""")

    write_text_lf(THEORY_MD, """# Stage180 Split-Probe Model

Stage178 showed the combined MAT EP/subdecomp block is hot, but Stage179
denied code permission because the block was not internally split.

Stage180 makes the split explicit:

```text
combined_current ~= sub_decompose + row torus_to_DFT + tiled addmul
```

The split probes are isolated microbenchmarks, so their sum is not expected to
match the combined path perfectly. They are used for routing: only a large
subcomponent with a plausible speedup mechanism can open implementation work.
""")

    write_text_lf(VARIANT_MD, """# MAT EP Split Probe Variant

This stage adds no production variant.

The generated C probe is a measurement harness that includes the current
`mattrgsw.c` and calls the internal split boundaries. Results are valid only as
microarchitecture evidence for selecting or rejecting a future implementation
branch.
""")


def write_global_updates(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 180: MAT EP Split Probe", f"""
## Stage 180: MAT EP Split Probe

Goal:

```text
Measure sub_decompose, torus_to_DFT, and tiled addmul inside the current exact
MAT EP/subdecomp block before opening any new code branch.
```

Status:

```text
Completed for this run. Stage180 records {decision}. Code implementation remains
blocked unless split data supports a complete-SAB T_bootstrap/r gain path.
```
""")
    append_once(GOAL_MD, "Stage180 records MAT EP split probe", f"""
Stage180 records MAT EP split probe evidence. Decision: `{decision}`. This
stage does not change production SAB; it only decides whether code permission
can proceed after split measurements.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage180 as the MAT EP split probe", f"""
84. Treat Stage180 as the MAT EP split probe:
    `{decision}`. Production code remains unchanged. Any Stage181
    implementation requires split data, correctness, and projected complete-SAB
    `T_bootstrap/r` impact.
""")
    append_once(HYPOTHESIS_YAML, "H104_mat_ep_split_probe", f"""
  - id: H104_mat_ep_split_probe
    statement: >
      The combined MAT EP/subdecomp block should be split into decompose,
      torus_to_DFT, and addmul before any further exact full-MAT AVX512
      implementation branch is justified.
    mechanism: >
      A native CB5 probe calls current internal boundaries from mattrgsw.c and
      records correctness, per-call timing, and perf counters for each phase.
    status: stage180_mat_ep_split_probe
    evidence: docs/stage180_mat_ep_split_probe.md; experiments/stage180_mat_ep_split_probe_plan.md; theory_checks/stage180_mat_ep_split_probe_model.md; repro/stage180_mat_ep_split_probe/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - timings are interpreted without correctness PASS
      - code is written before split data exists
      - microbench-only evidence is reported as complete-SAB acceleration
""")
    append_once(RUN_LOG, "stage180-mat-ep-split-probe-001", f"""
stage180-mat-ep-split-probe-001,2026-07-04,{HEAD},Stage 180,spqlios_avx512,python scripts/build_stage180_mat_ep_split_probe.py,r={R_VALUE}; N={N_VALUE}; items={ITEMS}; reps={REPS},deterministic-probe,{decision},MAT EP/subdecomp split probe.,repro/stage180_mat_ep_split_probe
""")
    append_once(MANIFEST, "stage180_mat_ep_split_probe", f"""
- stage180_mat_ep_split_probe: `{decision}`
  - `docs/stage180_mat_ep_split_probe.md`
  - `experiments/stage180_mat_ep_split_probe_plan.md`
  - `theory_checks/stage180_mat_ep_split_probe_model.md`
  - `algorithm_variants/mat_rlwe_sab_mat_ep_split_probe.md`
  - `repro/stage180_mat_ep_split_probe/`
""")
    append_once(CHECKLIST, "Stage180 MAT EP split probe pack recorded", """
- [x] Stage180 MAT EP split probe pack recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path),
            "bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_c_source()
    rcs: Dict[str, int] = {}
    if REMOTE_PASSWORD:
        rcs = run_remote_pipeline()
    write_csv(REMOTE_CSV, parse_remote_environment(), ["key", "value", "evidence"])
    all_counter_rows: List[Dict[str, str]] = []
    all_run_rows: List[Dict[str, str]] = []
    all_correctness_rows: List[Dict[str, str]] = []
    for variant in VARIANTS:
        counters, runs, correctness = parse_variant_log(variant)
        all_counter_rows.extend(counters)
        all_run_rows.extend(runs)
        all_correctness_rows.extend(correctness)
    write_csv(COUNTER_CSV, all_counter_rows, ["variant", "metric", "value", "unit", "evidence", "detail"])
    write_csv(RUN_CSV, all_run_rows, ["variant", "run_rc", "r", "N", "items", "reps", "calls", "total_ns", "per_call_us", "sink", "status", "evidence"])
    write_csv(CORRECTNESS_CSV, all_correctness_rows, ["variant", "check", "mismatches", "max_gap", "status", "evidence"])
    derived_rows = build_derived_rows(all_run_rows)
    write_csv(DERIVED_CSV, derived_rows, ["metric", "value", "unit", "evidence", "interpretation"])
    decision, summary_rows = build_summary_rows(rcs, all_run_rows, all_correctness_rows)
    next_rows = build_next_rows(decision)
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_docs(decision, summary_rows, all_run_rows, derived_rows, next_rows)
    write_global_updates(decision)
    write_artifacts([
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        RUN_CSV,
        COUNTER_CSV,
        CORRECTNESS_CSV,
        DERIVED_CSV,
        NEXT_CSV,
        C_SOURCE,
        Path(__file__),
    ])
    print(decision)


if __name__ == "__main__":
    main()
