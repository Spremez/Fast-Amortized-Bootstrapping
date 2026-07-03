#!/usr/bin/env python3
"""Stage174: bounded from_DFT AVX512 direct-scale locality gate."""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import shlex
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage174_from_dft_direct_scale_gate"

C_SOURCE = OUT_DIR / "stage174_from_dft_probe.c"
SUMMARY_CSV = OUT_DIR / "summary.csv"
REMOTE_CSV = OUT_DIR / "remote_environment.csv"
CORRECTNESS_CSV = OUT_DIR / "correctness.csv"
MICROBENCH_CSV = OUT_DIR / "microbench_samples.csv"
MICRO_AGG_CSV = OUT_DIR / "microbench_aggregate.csv"
COMPARISON_CSV = OUT_DIR / "comparison.csv"
FULL_RUN_CSV = OUT_DIR / "full_sab_runs.csv"
FULL_AGG_CSV = OUT_DIR / "full_sab_aggregate.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage174_from_dft_direct_scale_gate.md"
PLAN_MD = ROOT / "experiments" / "stage174_from_dft_direct_scale_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage174_direct_scale_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_from_dft_direct_scale.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

REMOTE_USER = os.environ.get("STAGE174_REMOTE_USER", "delld")
REMOTE_HOST = os.environ.get("STAGE174_REMOTE_HOST", "192.168.107.220")
REMOTE_BASE = os.environ.get("STAGE174_REMOTE_BASE", "/home/delld/spz")
REMOTE_PASSWORD = os.environ.get("STAGE174_SSHPASS", "")
MAKE_JOBS = os.environ.get("STAGE174_JOBS", "$(nproc)")

R_VALUE = int(os.environ.get("STAGE174_R", "6"))
N_VALUE = int(os.environ.get("STAGE174_N", "2048"))
ITEMS = int(os.environ.get("STAGE174_ITEMS", "256"))
RUNS = int(os.environ.get("STAGE174_RUNS", "7"))
REPS = int(os.environ.get("STAGE174_REPS", "8"))
WARMUPS = int(os.environ.get("STAGE174_WARMUPS", "2"))
FULL_RUNS = int(os.environ.get("STAGE174_FULL_RUNS", "3"))
MICRO_PROMOTE_MEAN = float(os.environ.get("STAGE174_MICRO_PROMOTE_MEAN", "1.02"))
MICRO_PROMOTE_MIN = float(os.environ.get("STAGE174_MICRO_PROMOTE_MIN", "1.00"))

HEAD = subprocess.check_output(
    ["git", "rev-parse", "--short", "HEAD"],
    cwd=ROOT,
    text=True,
).strip()
REMOTE_DIR_NAME = f"Fast-Amortized-Bootstrapping-stage174-{HEAD}"
REMOTE_DIR = f"{REMOTE_BASE}/{REMOTE_DIR_NAME}"
REMOTE_STAGE_DIR = f"{REMOTE_DIR}/repro/stage174_from_dft_direct_scale_gate"
REMOTE_PROBE_SOURCE = f"{REMOTE_STAGE_DIR}/stage174_from_dft_probe.c"

BASE_STATIC_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "ENABLE_PVW_TMLWE=true SAB_PVW_BACKEND_FROM_DFT_ADD=true"
)
FULL_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
    "SAB_PVW_SUB_DECOMP_FUSION=true "
    "SAB_PVW_BENCH=true SAB_PVW_BENCH_R=6 SAB_PVW_BENCH_REPS=1"
)

VARIANTS = [
    {"name": "baseline", "flag": "false", "binary": "stage174_probe_baseline"},
    {"name": "direct_scale", "flag": "true", "binary": "stage174_probe_direct_scale"},
]

CORRECT_RE = re.compile(
    r"CORRECT174,(?P<variant>[^,]+),(?P<check>[^,]+),"
    r"(?P<mismatches>\d+),(?P<max_gap>\d+),(?P<status>[^,\s]+)"
)
BENCH_RE = re.compile(
    r"BENCH174,(?P<variant>[^,]+),(?P<run>\d+),(?P<r>\d+),"
    r"(?P<N>\d+),(?P<items>\d+),(?P<components>\d+),(?P<reps>\d+),"
    r"(?P<calls>\d+),(?P<total_ns>\d+),(?P<per_call_us>[0-9.]+),"
    r"(?P<sink>\d+),(?P<status>[^,\s]+)"
)
FULL_RE = re.compile(
    r"SAB_PVW_BENCH summary target_full r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw>[0-9.]+).*?pvw_lane_avg_us=(?P<pvw_lane>[0-9.]+) "
    r"scalar_repeated_avg_us=(?P<scalar>[0-9.]+).*?scalar_lane_avg_us=(?P<scalar_lane>[0-9.]+) "
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x"
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


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


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


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


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
        "-o UserKnownHostsFile=/tmp/codex_stage174_known_hosts "
        "-o ConnectTimeout=12 "
        f"{shlex.quote(REMOTE_USER + '@' + REMOTE_HOST)}"
    )


def scp_prefix() -> str:
    return (
        f"sshpass -p {shlex.quote(REMOTE_PASSWORD)} scp "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/tmp/codex_stage174_known_hosts "
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
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE174_R
#define STAGE174_R {R_VALUE}
#endif
#ifndef STAGE174_N
#define STAGE174_N {N_VALUE}
#endif
#ifndef STAGE174_ITEMS
#define STAGE174_ITEMS {ITEMS}
#endif
#ifndef STAGE174_RUNS
#define STAGE174_RUNS {RUNS}
#endif
#ifndef STAGE174_REPS
#define STAGE174_REPS {REPS}
#endif
#ifndef STAGE174_WARMUPS
#define STAGE174_WARMUPS {WARMUPS}
#endif

static inline uint64_t now_ns(void) {{
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ((uint64_t) ts.tv_sec * 1000000000ULL) + (uint64_t) ts.tv_nsec;
}}

static inline int idx_of(int item, int component) {{
  return item * (1 + STAGE174_R) + component;
}}

static void fill_source(TorusPolynomial p, int item, int component) {{
  uint64_t x = 0x9e3779b97f4a7c15ULL ^ ((uint64_t) item << 32) ^ (uint64_t) component;
  for (int i = 0; i < p->N; i++) {{
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    p->coeffs[i] = (Torus) (x * 0x2545f4914f6cdd1dULL + (uint64_t) (i + 17 * component));
  }}
}}

static void fill_addend(TorusPolynomial p, int item, int component) {{
  uint64_t x = 0xd1b54a32d192ed03ULL ^ ((uint64_t) component << 40) ^ (uint64_t) item;
  for (int i = 0; i < p->N; i++) {{
    x += 0x9e3779b97f4a7c15ULL + (uint64_t) (i * 1315423911U);
    x ^= x >> 29;
    p->coeffs[i] = (Torus) (x + ((uint64_t) item << 11) + (uint64_t) component);
  }}
}}

static void addto_poly(TorusPolynomial out, TorusPolynomial in) {{
#if defined(__AVX512F__)
  __m512i *out_v = (__m512i *) out->coeffs;
  const __m512i *in_v = (const __m512i *) in->coeffs;
  for (int i = 0; i < out->N / 8; i++) {{
    out_v[i] = _mm512_add_epi64(out_v[i], in_v[i]);
  }}
#else
  polynomial_addto_torus_polynomial(out, in);
#endif
}}

static void prepare_inputs(DFT_Polynomial *dft, TorusPolynomial *addend) {{
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE174_N);
  for (int item = 0; item < STAGE174_ITEMS; item++) {{
    for (int component = 0; component < 1 + STAGE174_R; component++) {{
      const int idx = idx_of(item, component);
      dft[idx] = polynomial_new_DFT_polynomial(STAGE174_N);
      addend[idx] = polynomial_new_torus_polynomial(STAGE174_N);
      fill_source(tmp, item, component);
      polynomial_torus_to_DFT(dft[idx], tmp);
      fill_addend(addend[idx], item, component);
    }}
  }}
  free_polynomial(tmp);
}}

static void run_from_dft_add(DFT_Polynomial *dft, TorusPolynomial *addend,
    TorusPolynomial *out) {{
  for (int item = 0; item < STAGE174_ITEMS; item++) {{
    for (int component = 0; component < 1 + STAGE174_R; component++) {{
      const int idx = idx_of(item, component);
      polynomial_DFT_to_torus_add(out[idx], dft[idx], addend[idx]);
    }}
  }}
}}

static uint64_t checksum_outputs(TorusPolynomial *out, int total) {{
  uint64_t acc = 0x84222325cbf29ce4ULL;
  for (int idx = 0; idx < total; idx++) {{
    for (int i = 0; i < STAGE174_N; i += 17) {{
      const uint64_t v = (uint64_t) out[idx]->coeffs[i];
      acc ^= v + 0x9e3779b97f4a7c15ULL + (acc << 6) + (acc >> 2);
    }}
  }}
  return acc;
}}

static void compare_outputs(const char *variant, TorusPolynomial *ref,
    TorusPolynomial *got, int total) {{
  uint64_t mismatches = 0;
  uint64_t max_gap = 0;
  for (int idx = 0; idx < total; idx++) {{
    for (int i = 0; i < STAGE174_N; i++) {{
      const uint64_t a = (uint64_t) ref[idx]->coeffs[i];
      const uint64_t b = (uint64_t) got[idx]->coeffs[i];
      const uint64_t gap = (a >= b) ? (a - b) : (b - a);
      if (gap != 0) mismatches++;
      if (gap > max_gap) max_gap = gap;
    }}
  }}
  printf("CORRECT174,%s,separate_reference,%" PRIu64 ",%" PRIu64 ",%s\n",
      variant, mismatches, max_gap, mismatches == 0 ? "PASS" : "FAIL");
}}

static uint64_t bench_variant(DFT_Polynomial *dft, TorusPolynomial *addend,
    TorusPolynomial *out) {{
  for (int w = 0; w < STAGE174_WARMUPS; w++) {{
    run_from_dft_add(dft, addend, out);
  }}
  const uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE174_REPS; rep++) {{
    run_from_dft_add(dft, addend, out);
  }}
  return now_ns() - start;
}}

int main(int argc, char **argv) {{
  if (argc != 2) {{
    fprintf(stderr, "usage: %s baseline|direct_scale\n", argv[0]);
    return 2;
  }}
  const char *variant = argv[1];
  const int components = 1 + STAGE174_R;
  const int total = STAGE174_ITEMS * components;
  init_fft(STAGE174_N);

  DFT_Polynomial *dft = (DFT_Polynomial *) calloc((size_t) total, sizeof(*dft));
  TorusPolynomial *addend = (TorusPolynomial *) calloc((size_t) total, sizeof(*addend));
  TorusPolynomial *ref = polynomial_new_array_of_torus_polynomials(STAGE174_N, total);
  TorusPolynomial *out = polynomial_new_array_of_torus_polynomials(STAGE174_N, total);
  if (!dft || !addend || !ref || !out) {{
    fprintf(stderr, "allocation failed\n");
    return 2;
  }}

  prepare_inputs(dft, addend);
  for (int idx = 0; idx < total; idx++) {{
    polynomial_DFT_to_torus(ref[idx], dft[idx]);
    addto_poly(ref[idx], addend[idx]);
  }}
  run_from_dft_add(dft, addend, out);
  compare_outputs(variant, ref, out, total);

  for (int run = 0; run < STAGE174_RUNS; run++) {{
    const uint64_t ns = bench_variant(dft, addend, out);
    const uint64_t calls = (uint64_t) STAGE174_REPS * (uint64_t) total;
    const double per_call_us = ((double) ns) / ((double) calls) / 1000.0;
    const uint64_t sink = checksum_outputs(out, total);
    printf("BENCH174,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",PASS\n",
        variant, run, STAGE174_R, STAGE174_N, STAGE174_ITEMS, components,
        STAGE174_REPS, calls, ns, per_call_us, sink);
  }}

  for (int idx = 0; idx < total; idx++) {{
    free_DFT_polynomial(dft[idx]);
    free_polynomial(addend[idx]);
  }}
  free(dft);
  free(addend);
  free_array_of_polynomials(ref, total);
  free_array_of_polynomials(out, total);
  return 0;
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
        "printf 'remote_dir,'; printf " + shlex.quote(REMOTE_DIR) + "; printf '\\n'; "
        "lscpu"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / "remote_environment.log", timeout=60)


def upload_file(local: Path, remote: str, log_name: str) -> int:
    remote_parent = str(Path(remote).parent).replace("\\", "/")
    mkdir_cmd = f"mkdir -p {shlex.quote(remote_parent)}"
    mkdir_rc = run_wsl(remote_command(mkdir_cmd), OUT_DIR / f"{log_name}_mkdir.log", timeout=60)
    if mkdir_rc != 0:
        return mkdir_rc
    target = f"{REMOTE_USER}@{REMOTE_HOST}:{remote}"
    cmd = f"{scp_prefix()} {shlex.quote(wsl_path(local))} {shlex.quote(target)}"
    return run_wsl(cmd, OUT_DIR / f"{log_name}.log", timeout=120)


def upload_worktree_overrides() -> int:
    uploads = [
        (ROOT / "src" / "mosfhet" / "Makefile.def", f"{REMOTE_DIR}/src/mosfhet/Makefile.def", "upload_makefile_def"),
        (ROOT / "src" / "mosfhet" / "src" / "fft" / "spqlios" / "fft_processor_spqlios.c", f"{REMOTE_DIR}/src/mosfhet/src/fft/spqlios/fft_processor_spqlios.c", "upload_fft_processor"),
        (C_SOURCE, REMOTE_PROBE_SOURCE, "upload_probe_source"),
    ]
    for local, remote, log_name in uploads:
        rc = upload_file(local, remote, log_name)
        if rc != 0:
            return rc
    return 0


def build_static(variant: Dict[str, str]) -> int:
    cmd = (
        f"cd {shlex.quote(REMOTE_DIR)}/src/mosfhet && "
        "(make clean >/dev/null 2>&1 || true) && "
        f"make static {BASE_STATIC_FLAGS} SPQLIOS_AVX512_DIRECT_SCALE={variant['flag']} -j{MAKE_JOBS}"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / f"build_static_{variant['name']}.log", timeout=1800)


def compile_probe(variant: Dict[str, str]) -> int:
    binary = f"{REMOTE_STAGE_DIR}/{variant['binary']}"
    cmd = (
        f"cd {shlex.quote(REMOTE_DIR)} && "
        "gcc -O3 -march=native -Wall -Wextra "
        f"-DSTAGE174_R={R_VALUE} -DSTAGE174_N={N_VALUE} "
        f"-DSTAGE174_ITEMS={ITEMS} -DSTAGE174_RUNS={RUNS} "
        f"-DSTAGE174_REPS={REPS} -DSTAGE174_WARMUPS={WARMUPS} "
        "-I src/mosfhet/include "
        f"-o {shlex.quote(binary)} {shlex.quote(REMOTE_PROBE_SOURCE)} "
        "src/mosfhet/lib/libmosfhet.a -lm"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / f"compile_probe_{variant['name']}.log", timeout=600)


def run_probe(variant: Dict[str, str]) -> int:
    binary = f"{REMOTE_STAGE_DIR}/{variant['binary']}"
    cmd = f"cd {shlex.quote(REMOTE_DIR)} && stdbuf -o0 {shlex.quote(binary)} {shlex.quote(variant['name'])}"
    return run_wsl(remote_command(cmd), OUT_DIR / f"run_probe_{variant['name']}.log", timeout=1800)


def build_full_sab(variant: Dict[str, str]) -> int:
    cmd = (
        f"cd {shlex.quote(REMOTE_DIR)} && "
        "(make clean >/dev/null 2>&1 || true) && "
        f"make {FULL_FLAGS} SPQLIOS_AVX512_DIRECT_SCALE={variant['flag']} -j{MAKE_JOBS}"
    )
    return run_wsl(remote_command(cmd), OUT_DIR / f"build_full_{variant['name']}.log", timeout=1800)


def run_full_sab(variant: Dict[str, str], run_id: int) -> int:
    cmd = f"cd {shlex.quote(REMOTE_DIR)} && stdbuf -o0 ./main"
    return run_wsl(remote_command(cmd), OUT_DIR / f"run_full_{variant['name']}_{run_id}.log", timeout=2400)


def cleanup_remote() -> int:
    cmd = f"cd {shlex.quote(REMOTE_DIR)} && (make clean >/dev/null 2>&1 || true) && (cd src/mosfhet && make clean >/dev/null 2>&1 || true)"
    return run_wsl(remote_command(cmd), OUT_DIR / "cleanup.log", timeout=300)


def parse_remote_environment() -> List[Dict[str, str]]:
    path = OUT_DIR / "remote_environment.log"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    rows: List[Dict[str, str]] = []
    for key in ["hostname", "whoami", "uname", "remote_dir"]:
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


def parse_probe_log(variant: Dict[str, str]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    path = OUT_DIR / f"run_probe_{variant['name']}.log"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    correctness: List[Dict[str, str]] = []
    bench: List[Dict[str, str]] = []
    rc_match = re.search(r"^returncode:\s+(\d+)$", text, re.MULTILINE)
    for line in text.splitlines():
        m = CORRECT_RE.search(line)
        if m:
            correctness.append({
                "variant": m.group("variant"),
                "check": m.group("check"),
                "mismatches": m.group("mismatches"),
                "max_gap": m.group("max_gap"),
                "status": m.group("status"),
                "evidence": rel(path),
            })
        m2 = BENCH_RE.search(line)
        if m2:
            bench.append({
                "variant": m2.group("variant"),
                "run": m2.group("run"),
                "run_rc": rc_match.group(1) if rc_match else "",
                "r": m2.group("r"),
                "N": m2.group("N"),
                "items": m2.group("items"),
                "components": m2.group("components"),
                "reps": m2.group("reps"),
                "calls": m2.group("calls"),
                "total_ns": m2.group("total_ns"),
                "per_call_us": m2.group("per_call_us"),
                "sink": m2.group("sink"),
                "status": m2.group("status"),
                "evidence": rel(path),
            })
    if not correctness:
        correctness.append({
            "variant": variant["name"],
            "check": "separate_reference",
            "mismatches": "",
            "max_gap": "",
            "status": "MISSING",
            "evidence": rel(path),
        })
    return correctness, bench


def t_critical_95(n: int) -> float:
    table_by_df = {
        1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
        6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
    }
    return table_by_df.get(max(n - 1, 1), 1.960)


def aggregate(rows: List[Dict[str, str]], metric: str = "per_call_us") -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for variant in [item["name"] for item in VARIANTS]:
        vals = [
            float(row[metric]) for row in rows
            if row.get("variant") == variant and row.get(metric) and row.get("status") == "PASS"
        ]
        if not vals:
            continue
        n = len(vals)
        stdev = statistics.stdev(vals) if n > 1 else 0.0
        half = t_critical_95(n) * stdev / math.sqrt(n) if n > 1 else 0.0
        out.append({
            "variant": variant,
            "metric": metric,
            "samples": str(n),
            "mean": f"{statistics.mean(vals):.9f}",
            "median": f"{statistics.median(vals):.9f}",
            "min": f"{min(vals):.9f}",
            "max": f"{max(vals):.9f}",
            "stdev": f"{stdev:.9f}",
            "ci95_low": f"{statistics.mean(vals) - half:.9f}",
            "ci95_high": f"{statistics.mean(vals) + half:.9f}",
            "unit": "us_per_call" if metric == "per_call_us" else metric,
        })
    return out


def agg_value(rows: List[Dict[str, str]], variant: str, field: str) -> float:
    for row in rows:
        if row.get("variant") == variant:
            try:
                return float(row.get(field, "0") or "0")
            except ValueError:
                return 0.0
    return 0.0


def build_comparison(micro_agg: List[Dict[str, str]], full_agg: List[Dict[str, str]], full_attempted: bool) -> List[Dict[str, str]]:
    base_mean = agg_value(micro_agg, "baseline", "mean")
    var_mean = agg_value(micro_agg, "direct_scale", "mean")
    base_min = agg_value(micro_agg, "baseline", "min")
    var_max = agg_value(micro_agg, "direct_scale", "max")
    micro_speed = base_mean / var_mean if var_mean else 0.0
    micro_minmax = base_min / var_max if var_max else 0.0
    rows = [{
        "scope": "microbench",
        "metric": "baseline_mean/direct_scale_mean;baseline_min/direct_scale_max",
        "value": f"{micro_speed:.9f};{micro_minmax:.9f}",
        "promotion_threshold": f"mean>={MICRO_PROMOTE_MEAN};minmax>={MICRO_PROMOTE_MIN}",
        "status": "PROMOTE_TO_FULL_SAB" if micro_speed >= MICRO_PROMOTE_MEAN and micro_minmax >= MICRO_PROMOTE_MIN else "NEUTRAL_OR_REJECT",
        "evidence": rel(MICRO_AGG_CSV),
    }]
    if full_attempted:
        base_full = agg_value(full_agg, "baseline", "mean")
        var_full = agg_value(full_agg, "direct_scale", "mean")
        full_speed = base_full / var_full if var_full else 0.0
        rows.append({
            "scope": "full_sab",
            "metric": "baseline_pvw_lane_mean/direct_scale_pvw_lane_mean",
            "value": f"{full_speed:.9f}",
            "promotion_threshold": "full_sab_speedup>1.01 and correctness all PASS",
            "status": "PROMOTE" if full_speed > 1.01 else "NEUTRAL_OR_REJECT",
            "evidence": rel(FULL_AGG_CSV),
        })
    else:
        rows.append({
            "scope": "full_sab",
            "metric": "not_run",
            "value": "microbench_not_promoted",
            "promotion_threshold": "microbench must promote first",
            "status": "SKIPPED_BY_GATE",
            "evidence": rel(COMPARISON_CSV),
        })
    return rows


def parse_full_log(variant: Dict[str, str], run_id: int) -> Dict[str, str]:
    path = OUT_DIR / f"run_full_{variant['name']}_{run_id}.log"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    row = {
        "variant": variant["name"],
        "run": str(run_id),
        "run_rc": "",
        "correctness": "PASS" if re.search(r"SAB_PVW_BENCH correctness target_full .* Pass", text) else "FAIL",
        "r": "",
        "pvw_avg_us": "",
        "pvw_lane_avg_us": "",
        "scalar_repeated_avg_us": "",
        "scalar_lane_avg_us": "",
        "speedup_vs_scalar_repeated": "",
        "evidence": rel(path),
    }
    rc_match = re.search(r"^returncode:\s+(\d+)$", text, re.MULTILINE)
    if rc_match:
        row["run_rc"] = rc_match.group(1)
    for line in text.splitlines():
        m = FULL_RE.search(line)
        if m:
            row.update({
                "r": m.group("r"),
                "pvw_avg_us": m.group("pvw"),
                "pvw_lane_avg_us": m.group("pvw_lane"),
                "scalar_repeated_avg_us": m.group("scalar"),
                "scalar_lane_avg_us": m.group("scalar_lane"),
                "speedup_vs_scalar_repeated": m.group("speedup"),
            })
            break
    return row


def aggregate_full(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for metric in ["pvw_lane_avg_us", "speedup_vs_scalar_repeated"]:
        for variant in [item["name"] for item in VARIANTS]:
            vals = [
                float(row[metric]) for row in rows
                if row.get("variant") == variant and row.get("correctness") == "PASS" and row.get(metric)
            ]
            if not vals:
                continue
            n = len(vals)
            stdev = statistics.stdev(vals) if n > 1 else 0.0
            half = t_critical_95(n) * stdev / math.sqrt(n) if n > 1 else 0.0
            out.append({
                "variant": variant,
                "metric": metric,
                "samples": str(n),
                "mean": f"{statistics.mean(vals):.9f}",
                "median": f"{statistics.median(vals):.9f}",
                "min": f"{min(vals):.9f}",
                "max": f"{max(vals):.9f}",
                "stdev": f"{stdev:.9f}",
                "ci95_low": f"{statistics.mean(vals) - half:.9f}",
                "ci95_high": f"{statistics.mean(vals) + half:.9f}",
                "unit": "us_per_lane" if metric.endswith("_us") else "x",
            })
    return out


def parse_all_microbench() -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    correctness: List[Dict[str, str]] = []
    bench: List[Dict[str, str]] = []
    for variant in VARIANTS:
        corr, samples = parse_probe_log(variant)
        correctness.extend(corr)
        bench.extend(samples)
    return correctness, bench


def build_next_queue(decision: str) -> List[Dict[str, str]]:
    if decision.startswith("PROMOTE"):
        return [{
            "priority": "P0",
            "stage": "175",
            "name": "direct-scale full-SAB claim refresh",
            "entry_condition": "Stage174 full-SAB A/B promoted the direct-scale backend flag.",
            "gate": "Refresh Stage172 claim matrix with complete-SAB evidence and decide default enablement.",
            "failure_rule": "Do not enable by default without correctness/resource/backend boundaries.",
        }]
    return [
        {
            "priority": "P0",
            "stage": "175",
            "name": "post-Stage174 frontier refresh",
            "entry_condition": "Stage174 did not promote direct-scale.",
            "gate": "Record neutral/reject and choose a different bounded route.",
            "failure_rule": "Do not keep tuning direct-scale blindly.",
        },
        {
            "priority": "P1",
            "stage": "173",
            "name": "structured compact proof route",
            "entry_condition": "Engineering direct-scale route is neutral/rejected and user wants algorithmic proof route.",
            "gate": "Formal phase/noise toy for compact keygen.",
            "failure_rule": "Keep compact blocked if equations do not close.",
        },
    ]


def decide(
    sync_rc: int,
    env_rc: int,
    upload_rc: int,
    build_rcs: Dict[str, int],
    compile_rcs: Dict[str, int],
    run_rcs: Dict[str, int],
    correctness: List[Dict[str, str]],
    micro_comparison: List[Dict[str, str]],
    full_attempted: bool,
    full_runs: List[Dict[str, str]],
    full_comparison_status: str,
) -> str:
    if not REMOTE_PASSWORD:
        return "BLOCKED_STAGE174_MISSING_REMOTE_PASSWORD_ENV"
    if sync_rc != 0:
        return "FAIL_STAGE174_REMOTE_SYNC"
    if env_rc != 0:
        return "FAIL_STAGE174_REMOTE_ENV"
    if upload_rc != 0:
        return "FAIL_STAGE174_UPLOAD"
    if any(rc != 0 for rc in build_rcs.values()):
        return "FAIL_STAGE174_STATIC_BUILD"
    if any(rc != 0 for rc in compile_rcs.values()):
        return "FAIL_STAGE174_PROBE_COMPILE"
    if any(rc != 0 for rc in run_rcs.values()):
        return "FAIL_STAGE174_PROBE_RUN"
    if any(row.get("status") != "PASS" for row in correctness):
        return "FAIL_STAGE174_MICRO_CORRECTNESS"
    micro_status = next((row["status"] for row in micro_comparison if row["scope"] == "microbench"), "")
    if micro_status != "PROMOTE_TO_FULL_SAB":
        return "NEUTRAL_STAGE174_DIRECT_SCALE_MICROBENCH_NOT_PROMOTED"
    if full_attempted and any(row.get("correctness") != "PASS" for row in full_runs):
        return "FAIL_STAGE174_FULL_SAB_CORRECTNESS"
    if full_comparison_status == "PROMOTE":
        return "PROMOTE_STAGE174_DIRECT_SCALE_FULL_SAB_POSITIVE"
    return "NEUTRAL_STAGE174_DIRECT_SCALE_FULL_SAB_NOT_PROMOTED"


def build_summary(
    decision: str,
    sync_rc: int,
    env_rc: int,
    upload_rc: int,
    build_rcs: Dict[str, int],
    compile_rcs: Dict[str, int],
    run_rcs: Dict[str, int],
    correctness: List[Dict[str, str]],
    comparison: List[Dict[str, str]],
    full_attempted: bool,
) -> List[Dict[str, str]]:
    return [
        {
            "gate": "stage174_remote_secret",
            "status": "PASS" if REMOTE_PASSWORD else "BLOCKED",
            "metric": "STAGE174_SSHPASS",
            "value": "present" if REMOTE_PASSWORD else "missing",
            "evidence": "environment variable only; not written to artifacts",
            "detail": "Remote password is consumed from environment and scrubbed from logs.",
            "next_action": "Provide STAGE174_SSHPASS only at runtime.",
        },
        {
            "gate": "stage174_sync_upload",
            "status": "PASS" if sync_rc == 0 and upload_rc == 0 else "FAIL",
            "metric": "sync_rc;env_rc;upload_rc",
            "value": f"{sync_rc};{env_rc};{upload_rc}",
            "evidence": f"{rel(OUT_DIR / 'sync.log')};{rel(OUT_DIR / 'upload_fft_processor.log')}",
            "detail": "Archive HEAD to CB5 and upload uncommitted flag/backend/probe files.",
            "next_action": "Fix remote state before interpreting results.",
        },
        {
            "gate": "stage174_build_compile",
            "status": "PASS" if build_rcs and compile_rcs and all(rc == 0 for rc in build_rcs.values()) and all(rc == 0 for rc in compile_rcs.values()) else "FAIL",
            "metric": "build_rcs;compile_rcs",
            "value": f"{build_rcs};{compile_rcs}",
            "evidence": rel(OUT_DIR),
            "detail": "Build baseline and direct_scale static libraries and probes.",
            "next_action": "Fix compile before using timings.",
        },
        {
            "gate": "stage174_micro_correctness",
            "status": "PASS" if correctness and all(row.get("status") == "PASS" for row in correctness) else "FAIL",
            "metric": "correctness",
            "value": ";".join(f"{row.get('variant')}={row.get('status')}" for row in correctness),
            "evidence": rel(CORRECTNESS_CSV),
            "detail": "Each variant must match separate materialize+add.",
            "next_action": "Reject variant if exactness fails.",
        },
        {
            "gate": "stage174_microbench",
            "status": next((row["status"] for row in comparison if row["scope"] == "microbench"), "MISSING"),
            "metric": "baseline/direct_scale",
            "value": next((row["value"] for row in comparison if row["scope"] == "microbench"), ""),
            "evidence": rel(COMPARISON_CSV),
            "detail": "Microbench promotion requires stable speedup before full-SAB A/B.",
            "next_action": "Run full-SAB only on microbench promotion.",
        },
        {
            "gate": "stage174_full_sab",
            "status": next((row["status"] for row in comparison if row["scope"] == "full_sab"), "MISSING"),
            "metric": "full_attempted",
            "value": "yes" if full_attempted else "no",
            "evidence": rel(FULL_AGG_CSV) if full_attempted else rel(COMPARISON_CSV),
            "detail": "Complete-SAB promotion remains the only allowed bootstrapping speedup claim.",
            "next_action": "Do not claim complete-SAB speedup if skipped or neutral.",
        },
        {
            "gate": "stage174_decision",
            "status": decision,
            "metric": "direct_scale_route",
            "value": "explicit_flag",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage174 tests one bounded backend/SIMD locality candidate.",
            "next_action": "Promote only if full-SAB evidence is positive; otherwise record neutral/reject.",
        },
    ]


def artifact_index(paths: List[Path]) -> None:
    fields = ["path", "exists", "sha256", "bytes"]
    rows = []
    for path in paths:
        if path == ARTIFACT_CSV:
            continue
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() and path.is_file() else "",
            "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
        })
    write_csv(ARTIFACT_CSV, rows, fields)
    rows.append({
        "path": rel(ARTIFACT_CSV),
        "exists": "yes",
        "sha256": sha256_file(ARTIFACT_CSV),
        "bytes": str(ARTIFACT_CSV.stat().st_size),
    })
    write_csv(ARTIFACT_CSV, rows, fields)


def write_docs(
    decision: str,
    summary: List[Dict[str, str]],
    remote_rows: List[Dict[str, str]],
    correctness: List[Dict[str, str]],
    micro_rows: List[Dict[str, str]],
    micro_agg: List[Dict[str, str]],
    comparison: List[Dict[str, str]],
    full_rows: List[Dict[str, str]],
    full_agg: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    remote_fields = ["key", "value", "evidence"]
    correctness_fields = ["variant", "check", "mismatches", "max_gap", "status", "evidence"]
    micro_fields = ["variant", "run", "r", "N", "items", "components", "reps", "calls", "per_call_us", "status", "evidence"]
    agg_fields = ["variant", "metric", "samples", "mean", "median", "min", "max", "stdev", "ci95_low", "ci95_high", "unit"]
    comparison_fields = ["scope", "metric", "value", "promotion_threshold", "status", "evidence"]
    full_fields = ["variant", "run", "run_rc", "correctness", "r", "pvw_lane_avg_us", "scalar_lane_avg_us", "speedup_vs_scalar_repeated", "evidence"]
    next_fields = ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"]

    write_text_lf(OUT_MD, f"""# Stage174 From-DFT Direct-Scale Gate

Decision: `{decision}`.

Stage174 tests one bounded from_DFT backend/SIMD locality candidate:

```text
SPQLIOS_AVX512_DIRECT_SCALE=true
```

The candidate replaces the 256-bit inline-assembly scale/copy loop before
`execute_direct_torus64[_add]` with a 512-bit intrinsic loop under an explicit
flag. Baseline behavior remains unchanged when the flag is off.

This is not an algorithmic MAT-SAB improvement unless it passes the complete
SAB gate. Microbench evidence is only a promotion filter.

## Gate Summary

{table(summary, summary_fields)}

## Remote Environment

{table(remote_rows, remote_fields)}

## Correctness

{table(correctness, correctness_fields)}

## Microbench Samples

{table(micro_rows[:20], micro_fields)}

## Microbench Aggregate

{table(micro_agg, agg_fields)}

## Comparison

{table(comparison, comparison_fields)}

## Full SAB Runs

{table(full_rows, full_fields)}

## Full SAB Aggregate

{table(full_agg, agg_fields)}

## Next Queue

{table(next_rows, next_fields)}
""")

    write_text_lf(PLAN_MD, f"""# Stage174 Validation Plan

Goal: test one concrete from_DFT locality/SIMD candidate without repeating
Stage163's rejected component-major batching.

Candidate:

```text
SPQLIOS_AVX512_DIRECT_SCALE=true
```

Protocol:

- build baseline and direct-scale probes on CB5 native Linux;
- correctness: each variant equals separate `DFT_to_torus + add`;
- microbench endpoint: `pvmtmlwe_from_DFT_add` call time for r={R_VALUE};
- promotion threshold: mean speedup >= {MICRO_PROMOTE_MEAN} and min/max guard >= {MICRO_PROMOTE_MIN};
- full-SAB A/B is run only if microbench promotes.

Failure handling:

- correctness failure rejects immediately;
- microbench neutral skips full-SAB and records a neutral result;
- full-SAB neutral prevents any bootstrapping-speedup claim.
""")

    write_text_lf(THEORY_MD, """# Stage174 Direct-Scale Model

The current spqlios `execute_direct_torus64_add` path has three coarse phases:

```text
1. scale/copy DFT coefficients into the backend direct buffer
2. run spqlios direct FFT
3. convert doubles to torus and add the torus addend
```

Stage174 modifies only phase 1 under an explicit flag. The theoretical maximum
benefit is bounded by the share of phase 1 inside from_DFT; the FFT and final
torus/add conversion remain unchanged. Therefore a small or neutral result is
expected and must be preserved as evidence.

This is a backend/SIMD optimization. It does not reduce SAB materialization
count, MAT external-product count, or asymptotic complexity.
""")

    write_text_lf(VARIANT_MD, f"""# From-DFT AVX512 Direct-Scale Variant

Flag:

```text
SPQLIOS_AVX512_DIRECT_SCALE=true
```

Decision:

```text
{decision}
```

Scope:

```text
backend/SIMD constant-factor candidate for spqlios_avx512 from_DFT
```

Blocked unless full-SAB gate promotes:

```text
complete SAB acceleration claim
default enablement
algorithmic complexity claim
```
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 174: From-DFT Direct-Scale Gate", f"""
## Stage 174: From-DFT Direct-Scale Gate

Goal:

```text
Test a bounded from_DFT locality/SIMD candidate by replacing the direct
spqlios scale/copy loop with an explicit AVX512 path behind a flag.
```

Status:

```text
Completed. Stage174 records {decision}. Microbench evidence is a promotion
filter; complete-SAB claims require the full-SAB gate.
```
""")
    append_once(GOAL_MD, "Stage174 records the from_DFT direct-scale gate", f"""
Stage174 records the from_DFT direct-scale gate. Decision: `{decision}`. The
candidate is backend/SIMD-only and remains behind `SPQLIOS_AVX512_DIRECT_SCALE`.
""")
    append_once(CURRENT_GOAL_MD, "77. Treat Stage174 as bounded from_DFT backend gate", f"""
77. Treat Stage174 as bounded from_DFT backend gate:
    `{decision}`. It does not change MAT/SAB algorithmic claims unless the
    complete-SAB promotion gate passes.
""")
    append_once(HYPOTHESIS_YAML, "id: H97_from_dft_direct_scale", f"""
  - id: H97_from_dft_direct_scale
    statement: >
      Replacing the spqlios direct torus64 scale/copy loop with an explicit
      AVX512 implementation may reduce from_DFT materialization time enough to
      matter for complete SAB.
    mechanism: >
      The current direct conversion path uses a 256-bit inline assembly
      scale/copy loop before the direct FFT; a 512-bit loop can reduce that
      phase's instruction count, but cannot reduce FFT cost or materialization
      count.
    status: stage174_from_dft_direct_scale_gate
    evidence: docs/stage174_from_dft_direct_scale_gate.md; experiments/stage174_from_dft_direct_scale_gate_plan.md; theory_checks/stage174_direct_scale_model.md; repro/stage174_from_dft_direct_scale_gate/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - variant output differs from separate DFT-to-torus plus add
      - microbench fails promotion threshold
      - full-SAB A/B fails to improve after microbench promotion
      - backend-only evidence is reported as algorithmic SAB acceleration
""")
    append_once(RUN_LOG, "stage174-from-dft-direct-scale-gate-001", f"""
stage174-from-dft-direct-scale-gate-001,2026-07-04,{git_head()},Stage 174,spqlios_avx512,python scripts/build_stage174_from_dft_direct_scale_gate.py,CB5 native; r={R_VALUE}; items={ITEMS}; runs={RUNS}; reps={REPS}; direct-scale flag,deterministic-probe,{decision},From-DFT direct-scale backend gate.,repro/stage174_from_dft_direct_scale_gate
""")
    append_once(MANIFEST, "stage174_from_dft_direct_scale_gate", f"""
- stage174_from_dft_direct_scale_gate: `{decision}`
  - `docs/stage174_from_dft_direct_scale_gate.md`
  - `experiments/stage174_from_dft_direct_scale_gate_plan.md`
  - `theory_checks/stage174_direct_scale_model.md`
  - `algorithm_variants/mat_rlwe_sab_from_dft_direct_scale.md`
  - `repro/stage174_from_dft_direct_scale_gate/`
""")
    append_once(CHECKLIST, "Stage174 from_DFT direct-scale gate pack recorded", """
- [x] Stage174 from_DFT direct-scale gate pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_c_source()

    if not REMOTE_PASSWORD:
        sync_rc = env_rc = upload_rc = 1
        build_rcs: Dict[str, int] = {}
        compile_rcs: Dict[str, int] = {}
        run_rcs: Dict[str, int] = {}
        remote_rows: List[Dict[str, str]] = []
    else:
        sync_rc = sync_repo()
        env_rc = probe_remote_environment() if sync_rc == 0 else 1
        remote_rows = parse_remote_environment()
        upload_rc = upload_worktree_overrides() if env_rc == 0 else 1
        build_rcs = {}
        compile_rcs = {}
        run_rcs = {}
        if upload_rc == 0:
            for variant in VARIANTS:
                build_rcs[variant["name"]] = build_static(variant)
                compile_rcs[variant["name"]] = compile_probe(variant) if build_rcs[variant["name"]] == 0 else 1
                run_rcs[variant["name"]] = run_probe(variant) if compile_rcs[variant["name"]] == 0 else 1

    correctness, micro_rows = parse_all_microbench()
    micro_agg = aggregate(micro_rows)
    comparison = build_comparison(micro_agg, [], False)
    micro_promoted = next((row["status"] for row in comparison if row["scope"] == "microbench"), "") == "PROMOTE_TO_FULL_SAB"

    full_attempted = False
    full_rows: List[Dict[str, str]] = []
    full_agg: List[Dict[str, str]] = []
    if REMOTE_PASSWORD and micro_promoted:
        full_attempted = True
        for variant in VARIANTS:
            build_full_rc = build_full_sab(variant)
            build_rcs[f"full_{variant['name']}"] = build_full_rc
            if build_full_rc == 0:
                for run_id in range(1, FULL_RUNS + 1):
                    rc = run_full_sab(variant, run_id)
                    run_rcs[f"full_{variant['name']}_{run_id}"] = rc
                    full_rows.append(parse_full_log(variant, run_id))
        full_agg = aggregate_full(full_rows)
        comparison = build_comparison(micro_agg, full_agg, True)

    full_comparison_status = next((row["status"] for row in comparison if row["scope"] == "full_sab"), "")
    decision = decide(
        sync_rc,
        env_rc,
        upload_rc,
        build_rcs,
        compile_rcs,
        run_rcs,
        correctness,
        comparison,
        full_attempted,
        full_rows,
        full_comparison_status,
    )
    next_rows = build_next_queue(decision)
    summary = build_summary(
        decision,
        sync_rc,
        env_rc,
        upload_rc,
        build_rcs,
        compile_rcs,
        run_rcs,
        correctness,
        comparison,
        full_attempted,
    )

    cleanup_remote() if REMOTE_PASSWORD else None

    write_csv(REMOTE_CSV, remote_rows, ["key", "value", "evidence"])
    write_csv(CORRECTNESS_CSV, correctness, ["variant", "check", "mismatches", "max_gap", "status", "evidence"])
    write_csv(MICROBENCH_CSV, micro_rows, ["variant", "run", "run_rc", "r", "N", "items", "components", "reps", "calls", "total_ns", "per_call_us", "sink", "status", "evidence"])
    write_csv(MICRO_AGG_CSV, micro_agg, ["variant", "metric", "samples", "mean", "median", "min", "max", "stdev", "ci95_low", "ci95_high", "unit"])
    write_csv(COMPARISON_CSV, comparison, ["scope", "metric", "value", "promotion_threshold", "status", "evidence"])
    write_csv(FULL_RUN_CSV, full_rows, ["variant", "run", "run_rc", "correctness", "r", "pvw_avg_us", "pvw_lane_avg_us", "scalar_repeated_avg_us", "scalar_lane_avg_us", "speedup_vs_scalar_repeated", "evidence"])
    write_csv(FULL_AGG_CSV, full_agg, ["variant", "metric", "samples", "mean", "median", "min", "max", "stdev", "ci95_low", "ci95_high", "unit"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(decision, summary, remote_rows, correctness, micro_rows, micro_agg, comparison, full_rows, full_agg, next_rows)
    update_global_docs(decision)
    artifact_index([
        C_SOURCE,
        SUMMARY_CSV,
        REMOTE_CSV,
        CORRECTNESS_CSV,
        MICROBENCH_CSV,
        MICRO_AGG_CSV,
        COMPARISON_CSV,
        FULL_RUN_CSV,
        FULL_AGG_CSV,
        NEXT_CSV,
        ARTIFACT_CSV,
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        OUT_DIR / "sync.log",
        OUT_DIR / "remote_environment.log",
        OUT_DIR / "upload_makefile_def.log",
        OUT_DIR / "upload_fft_processor.log",
        OUT_DIR / "upload_probe_source.log",
        OUT_DIR / "build_static_baseline.log",
        OUT_DIR / "build_static_direct_scale.log",
        OUT_DIR / "compile_probe_baseline.log",
        OUT_DIR / "compile_probe_direct_scale.log",
        OUT_DIR / "run_probe_baseline.log",
        OUT_DIR / "run_probe_direct_scale.log",
        OUT_DIR / "cleanup.log",
    ] + [
        OUT_DIR / f"build_full_{variant['name']}.log" for variant in VARIANTS
    ] + [
        OUT_DIR / f"run_full_{variant['name']}_{run_id}.log"
        for variant in VARIANTS for run_id in range(1, FULL_RUNS + 1)
    ])
    print(decision)


if __name__ == "__main__":
    main()
