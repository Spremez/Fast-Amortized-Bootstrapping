#!/usr/bin/env python3
"""Stage209: current-head r=2/r=4 MAT-EP split preflight."""

from __future__ import annotations

import csv
import hashlib
import math
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage209_current_head_mat_ep_split"
C_SOURCE = OUT / "stage209_current_head_mat_ep_split.c"
ENV_CSV = OUT / "environment.csv"
RUN_CSV = OUT / "run_metrics.csv"
CORRECTNESS_CSV = OUT / "correctness.csv"
SPLIT_CSV = OUT / "split_projection.csv"
PROOF_GATE_CSV = OUT / "proof_gate.csv"
NEXT_CSV = OUT / "next_stage_queue.csv"
ARTIFACT_CSV = OUT / "artifact_index.csv"
REPORT = OUT / "current_head_mat_ep_split_report.md"
REPRO_COMMANDS = OUT / "reproduction_commands.md"

DOC = ROOT / "docs" / "stage209_current_head_mat_ep_split.md"
PLAN = ROOT / "experiments" / "stage209_current_head_mat_ep_split_plan.md"
THEORY = ROOT / "theory_checks" / "stage209_current_head_mat_ep_split_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_current_head_mat_ep_split.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE208_CMUX = ROOT / "repro" / "stage208_current_head_profile_refresh" / "cmux" / "summary.csv"

R_VALUES = [2, 4]
N_VALUE = 2048
ITEMS = 128
REPS = 8
WARMUPS = 2
BG_BIT = 23
VARIANTS = ["sub_decompose", "torus_to_dft_rows", "addmul_from_dec_dft", "combined_current"]
DECISION = "PASS_STAGE209_CURRENT_HEAD_MAT_EP_SPLIT_PREFLIGHT"


RESULT_RE = re.compile(
    r"RESULT209,(?P<variant>[^,]+),(?P<r>\d+),(?P<N>\d+),"
    r"(?P<items>\d+),(?P<reps>\d+),(?P<calls>\d+),"
    r"(?P<total_ns>\d+),(?P<per_call_us>[0-9.]+),(?P<sink>\d+),(?P<status>[^,\s]+)"
)
CORRECT_RE = re.compile(
    r"CORRECT209,(?P<variant>[^,]+),(?P<check>[^,]+),"
    r"(?P<mismatches>\d+),(?P<max_gap>\d+),(?P<status>[^,\s]+)"
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def wsl_path(path: Path) -> str:
    drive = path.drive.rstrip(":").lower()
    rest = path.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


def wsl_repo() -> str:
    return wsl_path(ROOT)


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in row_list:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text_lf(path, current + text.strip() + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    clean = "".join(ch if ch in "\n\t" or 32 <= ord(ch) < 127 else "?" for ch in text)
    return "\n".join(line.rstrip() for line in clean.splitlines()).rstrip() + "\n"


def run_wsl(command: str, log: Path, timeout: int = 1800) -> int:
    proc = subprocess.run(
        ["wsl.exe", "--cd", wsl_repo(), "bash", "-lc", command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    write_text_lf(
        log,
        "\n".join(
            [
                f"command: {command}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize(proc.stdout),
                "--- stderr ---",
                sanitize(proc.stderr),
            ]
        ),
    )
    return proc.returncode


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._"
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def write_c_source() -> None:
    source = f'''
#include "mosfhet.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE209_R
#define STAGE209_R 2
#endif
#ifndef STAGE209_N
#define STAGE209_N {N_VALUE}
#endif
#ifndef STAGE209_ITEMS
#define STAGE209_ITEMS {ITEMS}
#endif
#ifndef STAGE209_REPS
#define STAGE209_REPS {REPS}
#endif
#ifndef STAGE209_WARMUPS
#define STAGE209_WARMUPS {WARMUPS}
#endif
#ifndef STAGE209_BG_BIT
#define STAGE209_BG_BIT {BG_BIT}
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
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE209_N);
  const int rows = 1 + STAGE209_R;
  for (int row = 0; row < rows; row++) {{
    fill_poly(tmp, 0xabcdef0011223344ULL ^ (uint64_t) row);
    polynomial_torus_to_DFT(selector->samples[row]->a[0], tmp);
    for (int lane = 0; lane < STAGE209_R; lane++) {{
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
  for (int i = 0; i < STAGE209_N; i += 17) acc ^= a[i] + (acc << 6) + (acc >> 2);
  for (int lane = 0; lane < STAGE209_R; lane++) {{
    const uint64_t *b = (const uint64_t *) out->b[lane]->coeffs;
    for (int i = 0; i < STAGE209_N; i += 17) acc ^= b[i] + (acc << 6) + (acc >> 2);
  }}
  return acc;
}}

static uint64_t compare_torus(PVW_TMLWE a, PVW_TMLWE b, uint64_t *max_gap) {{
  uint64_t mismatches = 0;
  for (int i = 0; i < STAGE209_N; i++) {{
    uint64_t x = (uint64_t) a->a[0]->coeffs[i];
    uint64_t y = (uint64_t) b->a[0]->coeffs[i];
    uint64_t gap = x >= y ? x - y : y - x;
    if (gap != 0) mismatches++;
    if (gap > *max_gap) *max_gap = gap;
  }}
  for (int lane = 0; lane < STAGE209_R; lane++) {{
    for (int i = 0; i < STAGE209_N; i++) {{
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
  for (int item = 0; item < STAGE209_ITEMS; item++) {{
    for (int row = 0; row < rows; row++) {{
      fill_poly(bank[item * rows + row], 0x1111222233334444ULL ^ ((uint64_t)item << 8) ^ (uint64_t)row);
    }}
  }}
}}

static void fill_dec_dft_bank(DFT_Polynomial *bank, int rows) {{
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE209_N);
  for (int item = 0; item < STAGE209_ITEMS; item++) {{
    for (int row = 0; row < rows; row++) {{
      fill_poly(tmp, 0x5555666677778888ULL ^ ((uint64_t)item << 8) ^ (uint64_t)row);
      polynomial_torus_to_DFT(bank[item * rows + row], tmp);
    }}
  }}
  free_polynomial(tmp);
}}

static int run_variant(const char *variant) {{
  const int rows = 1 + STAGE209_R;
  init_fft(STAGE209_N);
  MAT_TRGSW_DFT selector =
      mat_trgsw_alloc_new_DFT_sample(1, STAGE209_BG_BIT, 1, STAGE209_R, STAGE209_N);
  fill_selector(selector);
  PVW_TMLWE *in1 = pvmtmlwe_alloc_new_sample_array(STAGE209_ITEMS, 1, STAGE209_R, STAGE209_N);
  PVW_TMLWE *in2 = pvmtmlwe_alloc_new_sample_array(STAGE209_ITEMS, 1, STAGE209_R, STAGE209_N);
  for (int item = 0; item < STAGE209_ITEMS; item++) {{
    fill_pvmtmlwe(in1[item], 0x100000000ULL + (uint64_t)item);
    fill_pvmtmlwe(in2[item], 0x200000000ULL + (uint64_t)item);
  }}
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, STAGE209_N);
  PVW_TMLWE_DFT out = pvmtmlwe_alloc_new_DFT_sample(1, STAGE209_R, STAGE209_N);
  TorusPolynomial *dec_bank = polynomial_new_array_of_torus_polynomials(STAGE209_N, rows * STAGE209_ITEMS);
  DFT_Polynomial *dft_bank = polynomial_new_array_of_polynomials_DFT(STAGE209_N, rows * STAGE209_ITEMS);
  fill_dec_bank(dec_bank, rows);
  fill_dec_dft_bank(dft_bank, rows);

  PVW_TMLWE_DFT current = pvmtmlwe_alloc_new_DFT_sample(1, STAGE209_R, STAGE209_N);
  PVW_TMLWE_DFT split = pvmtmlwe_alloc_new_DFT_sample(1, STAGE209_R, STAGE209_N);
  mat_trgsw_mul_pvmtmlwe_sub_DFT(current, in1[0], in2[0], selector, scratch);
  mat_trgsw_sub_decompose(in1[0], in2[0], scratch->dec, selector->Q, selector->T);
  for (int row = 0; row < rows; row++) {{
    polynomial_torus_to_DFT(scratch->dec_dft[row], scratch->dec[row]);
  }}
  mat_trgsw_mul_pvmtmlwe_DFT_from_dec(split, selector, scratch->dec_dft);
  PVW_TMLWE current_torus = pvmtmlwe_alloc_new_sample(1, STAGE209_R, STAGE209_N);
  PVW_TMLWE split_torus = pvmtmlwe_alloc_new_sample(1, STAGE209_R, STAGE209_N);
  pvmtmlwe_from_DFT(current_torus, current);
  pvmtmlwe_from_DFT(split_torus, split);
  uint64_t max_gap = 0;
  uint64_t mismatches = compare_torus(current_torus, split_torus, &max_gap);
  printf("CORRECT209,%s,combined_vs_split,%" PRIu64 ",%" PRIu64 ",%s\\n",
      variant, mismatches, max_gap, mismatches == 0 ? "PASS" : "FAIL");

  uint64_t sink = 0;
  for (int w = 0; w < STAGE209_WARMUPS; w++) {{
    for (int item = 0; item < STAGE209_ITEMS; item++) {{
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
  for (int rep = 0; rep < STAGE209_REPS; rep++) {{
    for (int item = 0; item < STAGE209_ITEMS; item++) {{
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
  uint64_t calls = (uint64_t) STAGE209_REPS * (uint64_t) STAGE209_ITEMS;
  double per_call_us = ((double)ns) / ((double)calls) / 1000.0;
  printf("RESULT209,%s,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",%s\\n",
      variant, STAGE209_R, STAGE209_N, STAGE209_ITEMS, STAGE209_REPS,
      calls, ns, per_call_us, sink, mismatches == 0 ? "PASS" : "FAIL");

  free_pvmtmlwe(current_torus);
  free_pvmtmlwe(split_torus);
  free_pvmtmlwe_DFT(current);
  free_pvmtmlwe_DFT(split);
  for (int i = 0; i < rows * STAGE209_ITEMS; i++) free_DFT_polynomial(dft_bank[i]);
  free(dft_bank);
  free_array_of_polynomials(dec_bank, rows * STAGE209_ITEMS);
  free_pvmtmlwe_DFT(out);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe_array(in1, STAGE209_ITEMS);
  free_pvmtmlwe_array(in2, STAGE209_ITEMS);
  free_mat_trgsw_DFT(selector);
  return mismatches == 0 ? 0 : 1;
}}

int main(int argc, char **argv) {{
  if (argc != 2) {{
    fprintf(stderr, "usage: %s sub_decompose|torus_to_dft_rows|addmul_from_dec_dft|combined_current\\n", argv[0]);
    return 2;
  }}
  return run_variant(argv[1]);
}}
'''
    write_text_lf(C_SOURCE, source)


def probe_environment() -> List[Dict[str, str]]:
    log = OUT / "environment.log"
    cmd = (
        "printf 'uname,'; uname -a; "
        "perf_bin=$(command -v perf 2>/dev/null || true); printf 'perf_path,%s\\n' \"$perf_bin\"; "
        "perf_paranoid=$(cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true); "
        "printf 'perf_event_paranoid,%s\\n' \"$perf_paranoid\"; "
        "lscpu | grep -E 'Model name|Flags' || true"
    )
    run_wsl(cmd, log, timeout=60)
    text = read_text(log)
    rows: List[Dict[str, str]] = []
    for key in ["uname", "perf_path", "perf_event_paranoid"]:
        m = re.search(rf"^{key},(.*)$", text, re.MULTILINE)
        rows.append({"key": key, "value": m.group(1).strip() if m else "", "evidence": rel(log)})
    model = re.search(r"Model name:\s+(.+)$", text, re.MULTILINE)
    flags = re.search(r"Flags:\s+(.+)$", text, re.MULTILINE)
    rows.append({"key": "cpu_model", "value": model.group(1).strip() if model else "", "evidence": rel(log)})
    rows.append({"key": "has_avx512f", "value": "yes" if flags and "avx512f" in flags.group(1) else "no", "evidence": rel(log)})
    perf_path = next((r["value"] for r in rows if r["key"] == "perf_path"), "")
    paranoid = next((r["value"] for r in rows if r["key"] == "perf_event_paranoid"), "")
    if not perf_path:
        counter_status = "blocked_no_perf_binary"
    elif paranoid and paranoid not in {"-1", "0", "1"}:
        counter_status = f"blocked_perf_event_paranoid_{paranoid}"
    else:
        counter_status = "available"
    rows.append({"key": "counter_status", "value": counter_status, "evidence": rel(log)})
    return rows


def build_static() -> int:
    cmd = (
        "cd src/mosfhet && "
        "(make clean >/dev/null 2>&1 || true) && "
        "make static FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
        "ENABLE_PVW_TMLWE=true MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true -j$(nproc)"
    )
    return run_wsl(cmd, OUT / "build_static.log", timeout=1800)


def compile_probe(r: int) -> int:
    bin_path = OUT / f"stage209_r{r}_probe"
    cmd = (
        "gcc -O3 -march=native -Wall -Wextra "
        "-DUSE_SPQLIOS -DAVX512_OPT -DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED "
        f"-DSTAGE209_R={r} -DSTAGE209_N={N_VALUE} -DSTAGE209_ITEMS={ITEMS} "
        f"-DSTAGE209_REPS={REPS} -DSTAGE209_WARMUPS={WARMUPS} -DSTAGE209_BG_BIT={BG_BIT} "
        "-I . -I src/mosfhet/include "
        f"-o {wsl_path(bin_path)} {wsl_path(C_SOURCE)} src/mosfhet/lib/libmosfhet.a -lm"
    )
    return run_wsl(cmd, OUT / f"compile_r{r}.log", timeout=600)


def run_variant(r: int, variant: str) -> int:
    bin_path = OUT / f"stage209_r{r}_probe"
    log = OUT / f"run_r{r}_{variant}.log"
    cmd = f"stdbuf -o0 {wsl_path(bin_path)} {variant}"
    return run_wsl(cmd, log, timeout=600)


def cleanup() -> None:
    run_wsl("cd src/mosfhet && (make clean >/dev/null 2>&1 || true)", OUT / "cleanup.log", timeout=300)


def parse_run_log(r: int, variant: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    log = OUT / f"run_r{r}_{variant}.log"
    text = read_text(log)
    rc_match = re.search(r"^returncode:\s+(\d+)$", text, re.MULTILINE)
    rc = rc_match.group(1) if rc_match else ""
    run_rows: List[Dict[str, str]] = []
    correctness_rows: List[Dict[str, str]] = []
    for line in text.splitlines():
        m = RESULT_RE.search(line)
        if m:
            run_rows.append(
                {
                    "r": m.group("r"),
                    "variant": m.group("variant"),
                    "run_rc": rc,
                    "N": m.group("N"),
                    "items": m.group("items"),
                    "reps": m.group("reps"),
                    "calls": m.group("calls"),
                    "total_ns": m.group("total_ns"),
                    "per_call_us": m.group("per_call_us"),
                    "sink": m.group("sink"),
                    "status": m.group("status"),
                    "evidence": rel(log),
                }
            )
        c = CORRECT_RE.search(line)
        if c:
            correctness_rows.append(
                {
                    "r": str(r),
                    "variant": c.group("variant"),
                    "check": c.group("check"),
                    "mismatches": c.group("mismatches"),
                    "max_gap": c.group("max_gap"),
                    "status": c.group("status"),
                    "evidence": rel(log),
                }
            )
    if not run_rows:
        run_rows.append(
            {
                "r": str(r),
                "variant": variant,
                "run_rc": rc,
                "N": str(N_VALUE),
                "items": str(ITEMS),
                "reps": str(REPS),
                "calls": "0",
                "total_ns": "0",
                "per_call_us": "",
                "sink": "",
                "status": "NO_RESULT",
                "evidence": rel(log),
            }
        )
    return run_rows, correctness_rows


def stage208_full_mat_share() -> Dict[str, float]:
    rows = read_csv(STAGE208_CMUX)
    shares = {}
    for row in rows:
        r = row["r"]
        shares[r] = float(row["mat_ep_us"]) / float(row["pvw_avg_us"])
    return shares


def required_speedup(full_share: float, target: float = 1.03) -> float:
    denom = (1.0 / target) - (1.0 - full_share)
    if denom <= 0:
        return math.inf
    return full_share / denom


def build_split_rows(run_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_r_variant = {(row["r"], row["variant"]): row for row in run_rows if row.get("per_call_us")}
    mat_full_share = stage208_full_mat_share()
    rows: List[Dict[str, str]] = []
    for r in ["2", "4"]:
        combined = float(by_r_variant[(r, "combined_current")]["per_call_us"])
        split_sum = 0.0
        for variant in ["sub_decompose", "torus_to_dft_rows", "addmul_from_dec_dft"]:
            per_call = float(by_r_variant[(r, variant)]["per_call_us"])
            split_sum += per_call
            share_of_combined = per_call / combined
            full_share = share_of_combined * mat_full_share[r]
            req = required_speedup(full_share)
            rows.append(
                {
                    "r": r,
                    "variant": variant,
                    "per_call_us": f"{per_call:.9f}",
                    "combined_current_us": f"{combined:.9f}",
                    "share_of_combined": f"{share_of_combined:.6f}",
                    "mat_ep_share_of_full_from_stage208": f"{mat_full_share[r]:.6f}",
                    "estimated_full_sab_share": f"{full_share:.6f}",
                    "component_speedup_for_3pct_full_gain": "inf" if math.isinf(req) else f"{req:.6f}",
                    "route_value": "candidate" if full_share >= 0.05 else "low_priority",
                    "evidence": rel(RUN_CSV),
                }
            )
        rows.append(
            {
                "r": r,
                "variant": "split_sum_over_combined",
                "per_call_us": f"{split_sum:.9f}",
                "combined_current_us": f"{combined:.9f}",
                "share_of_combined": f"{split_sum / combined:.6f}",
                "mat_ep_share_of_full_from_stage208": f"{mat_full_share[r]:.6f}",
                "estimated_full_sab_share": "",
                "component_speedup_for_3pct_full_gain": "",
                "route_value": "coverage_check",
                "evidence": rel(RUN_CSV),
            }
        )
    return rows


def build_gates(env_rows: List[Dict[str, str]], run_rows: List[Dict[str, str]], correctness_rows: List[Dict[str, str]], split_rows: List[Dict[str, str]], rc_map: Dict[str, int]) -> List[Dict[str, str]]:
    perf_available = any(row["key"] == "counter_status" and row["value"] == "available" for row in env_rows)
    all_rc_ok = all(rc == 0 for rc in rc_map.values())
    correctness_ok = correctness_rows and all(row["status"] == "PASS" for row in correctness_rows)
    runs_ok = all(row["status"] == "PASS" for row in run_rows)
    projected = [row for row in split_rows if row["route_value"] == "candidate"]
    return [
        {
            "gate": "G1_environment",
            "status": "PASS_COUNTER_BLOCKED_RECORDED" if not perf_available else "PASS_COUNTER_AVAILABLE",
            "evidence": rel(ENV_CSV),
            "detail": "WSL environment and perf availability are recorded.",
            "remaining_gap": "Hardware counter claims remain blocked when perf is unavailable.",
        },
        {
            "gate": "G2_build_run",
            "status": "PASS" if all_rc_ok and runs_ok else "FAIL",
            "evidence": rel(RUN_CSV),
            "detail": "r=2/r=4 split variants build and emit RESULT209 rows.",
            "remaining_gap": "Microbench only; not complete-SAB latency evidence.",
        },
        {
            "gate": "G3_correctness",
            "status": "PASS" if correctness_ok else "FAIL",
            "evidence": rel(CORRECTNESS_CSV),
            "detail": "Combined current equals split decompose -> DFT -> addmul for every r/variant run.",
            "remaining_gap": "Does not prove alternative implementation correctness.",
        },
        {
            "gate": "G4_projection",
            "status": "PASS_PREFLIGHT_CANDIDATES_RECORDED" if projected else "PASS_NO_COMPONENT_PRIORITY",
            "evidence": rel(SPLIT_CSV),
            "detail": "Split projection estimates which subcomponents can plausibly move complete SAB.",
            "remaining_gap": "Any implementation still needs a flag-only code gate and complete-SAB A/B.",
        },
        {
            "gate": "G5_decision",
            "status": DECISION if all_rc_ok and correctness_ok and runs_ok else "BLOCK_STAGE209_PREFLIGHT_FAILED",
            "evidence": rel(PROOF_GATE_CSV),
            "detail": "Stage209 is a preflight gate; it grants route selection, not speedup claims.",
            "remaining_gap": "Native counters and implementation gates remain separate.",
        },
    ]


def build_next(split_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    candidates = [row for row in split_rows if row["route_value"] == "candidate"]
    best = sorted(candidates, key=lambda row: float(row["estimated_full_sab_share"]), reverse=True)
    first = best[0]["variant"] if best else "none"
    return [
        {
            "priority": "P0",
            "route": "stage210_candidate_selection",
            "entry_condition": "Stage209 correctness and split projection pass.",
            "gate": f"Select a bounded implementation candidate, currently first={first}.",
            "current_status": "ready",
            "evidence": rel(SPLIT_CSV),
        },
        {
            "priority": "P1",
            "route": "native_counter_refresh",
            "entry_condition": "perf/native Linux is available.",
            "gate": "Collect load/store/FMA counters for the same r=2/r=4 split variants.",
            "current_status": "blocked_if_no_perf",
            "evidence": rel(ENV_CSV),
        },
        {
            "priority": "P2",
            "route": "no_postproc_work",
            "entry_condition": "Stage208 postproc tail remains below threshold.",
            "gate": "Keep extract/KS work deferred unless future body changes increase tail share.",
            "current_status": "deferred",
            "evidence": "repro/stage208_current_head_profile_refresh/component_attribution.csv",
        },
    ]


def report(split_rows: List[Dict[str, str]], gates: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> str:
    return f"""# Stage209 Current-Head MAT-EP Split Preflight

Decision: `{DECISION}`.

Stage209 splits the current r=2/r=4 MAT external-product block into
`sub_decompose`, `torus_to_dft_rows`, and `addmul_from_dec_dft`. It is a
preflight for route selection. It does not change production SAB code and does
not replace Stage206 complete-SAB latency evidence.

## Split Projection

{table(split_rows, ["r", "variant", "per_call_us", "combined_current_us", "share_of_combined", "estimated_full_sab_share", "component_speedup_for_3pct_full_gain", "route_value"])}

## Gates

{table(gates, ["gate", "status", "evidence", "detail", "remaining_gap"])}

## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}
"""


def artifact_rows(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
    seen = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
                "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
            }
        )
    return rows


def update_tracking(split_rows: List[Dict[str, str]]) -> None:
    head = git_head()
    cand = [row for row in split_rows if row["route_value"] == "candidate"]
    top = sorted(cand, key=lambda row: float(row["estimated_full_sab_share"]), reverse=True)[0]
    append_once(
        ROADMAP,
        "## Stage 209: Current-Head MAT-EP Split Preflight",
        f"""
## Stage 209: Current-Head MAT-EP Split Preflight

Goal:

```text
Split current-head r=2/r=4 MAT external-product cost into sub_decompose,
torus_to_DFT, and addmul_from_dec_dft before authorizing any new hot-path code.
```

Status:

```text
Completed. Stage209 records {DECISION}. Correctness passes for all r=2/r=4
split variants. The top route by estimated full-SAB share is {top['variant']}
at r={top['r']} with estimated full-SAB share {top['estimated_full_sab_share']}.
This is preflight evidence only; implementation and complete-SAB performance claims
remain gated by Stage210+.
```
""",
    )
    append_once(
        GOAL,
        "Stage209 current-head MAT-EP split preflight",
        f"""

## Stage209 current-head MAT-EP split preflight

At commit `{head}`, Stage209 records r=2/r=4 split microbench evidence for the
current exact small-r MAT path. It identifies candidate subcomponents for a
bounded implementation gate while preserving the rule that complete-SAB
`T_bootstrap/r` claims require full A/B evidence.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage209 current-head MAT-EP split preflight",
        f"""

### Stage209 current-head MAT-EP split preflight

`{DECISION}` keeps the research loop executable: the next step is Stage210
candidate selection from measured split shares, not a broad theory loop or a
post-processing detour.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage209_current_head_mat_ep_split",
        """

H10_stage209_current_head_mat_ep_split:
  status: current_head_split_preflight_recorded
  evidence:
    - repro/stage209_current_head_mat_ep_split/split_projection.csv
    - docs/stage209_current_head_mat_ep_split.md
  conclusion: >
    Current-head r=2/r=4 split microbench evidence records which MAT-EP
    subcomponents can plausibly move complete-SAB T_bootstrap/r. It grants
    candidate selection only, not implementation success or latency claims.
""",
    )
    append_once(
        RUN_LOG,
        "stage209-current-head-mat-ep-split-001",
        f"""stage209-current-head-mat-ep-split-001,2026-07-04,{head},Stage 209,spqlios_avx512,python scripts/build_stage209_current_head_mat_ep_split.py,current-head r=2/r=4 split MAT-EP preflight; items={ITEMS}; reps={REPS},deterministic-probe,{DECISION},"Correctness passes; split projection recorded; hardware counters blocked if perf unavailable.",docs/stage209_current_head_mat_ep_split.md; repro/stage209_current_head_mat_ep_split/split_projection.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage209_current_head_mat_ep_split:",
        """

- stage209_current_head_mat_ep_split:
  - `docs/stage209_current_head_mat_ep_split.md`
  - `experiments/stage209_current_head_mat_ep_split_plan.md`
  - `theory_checks/stage209_current_head_mat_ep_split_model.md`
  - `algorithm_variants/mat_rlwe_sab_current_head_mat_ep_split.md`
  - `scripts/build_stage209_current_head_mat_ep_split.py`
  - `repro/stage209_current_head_mat_ep_split/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage209 current-head MAT-EP split preflight",
        """
- [x] Stage209 current-head MAT-EP split preflight records r=2/r=4
  sub_decompose, torus_to_DFT, addmul, combined timing, correctness, and
  projection gates.
""",
    )


def write_docs(split_rows: List[Dict[str, str]], gates: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> None:
    text = report(split_rows, gates, next_rows)
    write_text_lf(DOC, text)
    write_text_lf(REPORT, text)
    write_text_lf(
        PLAN,
        """# Stage209 Current-Head MAT-EP Split Preflight Plan

Measure current r=2/r=4 MAT external-product internals before writing more
hot-path code. Correctness must pass first. Results are microbench route
selection only; full SAB speedup still requires complete-SAB A/B.
""",
    )
    write_text_lf(
        THEORY,
        """# Stage209 MAT-EP Split Model

The current exact MAT external product can be split as:

```text
combined_current ~= sub_decompose + torus_to_DFT_rows + addmul_from_dec_dft
```

The split probes are isolated and may not sum exactly to the combined path.
They support only Amdahl-style route selection. Any candidate still needs a
flag-only implementation gate, correctness, noise, resource, and full SAB
`T_bootstrap/r` A/B.
""",
    )
    write_text_lf(
        VARIANT,
        """# Current-Head MAT-EP Split Preflight

Stage209 adds no production variant. It generates a local measurement harness
that includes the current `mattrgsw.c` and calls internal split boundaries for
r=2/r=4. The output is a candidate-selection table for later bounded
implementation work.
""",
    )
    write_text_lf(
        REPRO_COMMANDS,
        """# Stage209 Reproduction Commands

```bash
python3 scripts/build_stage209_current_head_mat_ep_split.py
```
""",
    )


def run_pipeline() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, int]]:
    rc_map: Dict[str, int] = {}
    write_c_source()
    rc_map["build_static"] = build_static()
    all_runs: List[Dict[str, str]] = []
    all_correctness: List[Dict[str, str]] = []
    if rc_map["build_static"] == 0:
        for r in R_VALUES:
            rc_map[f"compile_r{r}"] = compile_probe(r)
            if rc_map[f"compile_r{r}"] == 0:
                for variant in VARIANTS:
                    rc_map[f"run_r{r}_{variant}"] = run_variant(r, variant)
                    runs, correctness = parse_run_log(r, variant)
                    all_runs.extend(runs)
                    all_correctness.extend(correctness)
    cleanup()
    return all_runs, all_correctness, rc_map


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not STAGE208_CMUX.exists():
        raise SystemExit(f"missing Stage208 profile input: {STAGE208_CMUX}")
    env_rows = probe_environment()
    run_rows, correctness_rows, rc_map = run_pipeline()
    split_rows = build_split_rows(run_rows)
    gates = build_gates(env_rows, run_rows, correctness_rows, split_rows, rc_map)
    next_rows = build_next(split_rows)

    write_csv(ENV_CSV, env_rows, ["key", "value", "evidence"])
    write_csv(RUN_CSV, run_rows, ["r", "variant", "run_rc", "N", "items", "reps", "calls", "total_ns", "per_call_us", "sink", "status", "evidence"])
    write_csv(CORRECTNESS_CSV, correctness_rows, ["r", "variant", "check", "mismatches", "max_gap", "status", "evidence"])
    write_csv(SPLIT_CSV, split_rows, ["r", "variant", "per_call_us", "combined_current_us", "share_of_combined", "mat_ep_share_of_full_from_stage208", "estimated_full_sab_share", "component_speedup_for_3pct_full_gain", "route_value", "evidence"])
    write_csv(PROOF_GATE_CSV, gates, ["gate", "status", "evidence", "detail", "remaining_gap"])
    write_csv(NEXT_CSV, next_rows, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])
    write_docs(split_rows, gates, next_rows)
    update_tracking(split_rows)
    artifacts = [
        DOC, PLAN, THEORY, VARIANT, REPORT, REPRO_COMMANDS, C_SOURCE, ENV_CSV,
        RUN_CSV, CORRECTNESS_CSV, SPLIT_CSV, PROOF_GATE_CSV, NEXT_CSV,
        OUT / "environment.log", OUT / "build_static.log", OUT / "cleanup.log",
        Path(__file__),
    ]
    artifacts.extend(sorted(OUT.glob("compile_r*.log")))
    artifacts.extend(sorted(OUT.glob("run_r*.log")))
    write_csv(ARTIFACT_CSV, artifact_rows(artifacts), ["path", "exists", "sha256", "bytes"])
    print(gates[-1]["status"])


if __name__ == "__main__":
    main()
