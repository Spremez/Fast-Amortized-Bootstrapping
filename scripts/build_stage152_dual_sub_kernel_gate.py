#!/usr/bin/env python3
"""Build Stage152 isolated dual-subtraction kernel gate for PVW/MAT-SAB."""

from __future__ import annotations

import csv
import hashlib
import math
import os
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage152_dual_sub_kernel_gate"

STAGE151_SUMMARY = ROOT / "repro" / "stage151_h14_r6_fulltile_backend_smoke" / "summary.csv"
STAGE86_CANDIDATES = ROOT / "repro" / "stage86_secondary_cmux_materialization" / "candidates.csv"
STAGE151_VARIANTS = ROOT / "repro" / "stage151_h14_r6_fulltile_backend_smoke" / "variant_results.csv"

C_SRC = OUT_DIR / "stage152_dual_sub_kernel_gate.c"
EXE = OUT_DIR / "stage152_dual_sub_kernel_gate"
BUILD_TXT = OUT_DIR / "build.txt"
RUN_TXT = OUT_DIR / "run.txt"
SAMPLES_CSV = OUT_DIR / "samples.csv"
RAW_CSV = OUT_DIR / "raw_results.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
PRIOR_CSV = OUT_DIR / "prior_evidence.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage152_dual_sub_kernel_gate.md"
PLAN_MD = ROOT / "experiments" / "stage152_dual_sub_kernel_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage152_dual_sub_kernel_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_dual_sub_kernel.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

R_VALUE = int(os.environ.get("STAGE152_R", "6"))
N_VALUE = int(os.environ.get("STAGE152_N", "2048"))
REPS = int(os.environ.get("STAGE152_REPS", "20000"))
RUNS = int(os.environ.get("STAGE152_RUNS", "5"))
RUN_GATE = os.environ.get("STAGE152_RUN_GATE", "1") not in {"0", "false", "False"}

PRIOR_FIELDS = ["source", "item", "status", "metric", "value", "evidence", "detail"]
SAMPLE_FIELDS = [
    "run", "r", "N", "reps", "current_us", "fused_us", "speedup",
    "checksum_current", "checksum_fused", "correctness",
]
RAW_FIELDS = [
    "r", "N", "reps", "runs", "current_us_mean", "fused_us_mean",
    "speedup_mean", "speedup_min", "speedup_max", "checksum_current",
    "checksum_fused", "correctness", "predicted_body_speedup", "sub_share_source",
    "decision",
]
SUMMARY_FIELDS = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = []
    for ch in text:
        code = ord(ch)
        if ch == "\n" or ch == "\t" or 32 <= code <= 126:
            cleaned.append(ch)
        else:
            cleaned.append("?")
    return "\n".join(line.rstrip() for line in "".join(cleaned).splitlines()).rstrip()


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


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def fnum(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def status_by_gate(rows: List[Dict[str, str]], gate: str) -> str:
    for row in rows:
        if row.get("gate") == gate:
            return row.get("status", "")
    return "MISSING"


def collect_prior() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    stage151 = read_csv(STAGE151_SUMMARY)
    rows.append({
        "source": "Stage151",
        "item": "stage151_decision",
        "status": status_by_gate(stage151, "stage151_decision"),
        "metric": "candidate_route",
        "value": "h14_r6_backend_fulltile",
        "evidence": rel(STAGE151_SUMMARY),
        "detail": "Fulltile backend smoke is weak, so Stage152 should avoid repeating MAT tile tweaks.",
    })
    candidates = read_csv(STAGE86_CANDIDATES)
    for row in candidates:
        if row.get("candidate_id") == "H14-C3-dual-butterfly-shared-input-wrapper":
            rows.append({
                "source": "Stage86",
                "item": row.get("candidate_id", ""),
                "status": row.get("status", ""),
                "metric": "expected_bound",
                "value": row.get("expected_bound", ""),
                "evidence": rel(STAGE86_CANDIDATES),
                "detail": row.get("mechanism", ""),
            })
    variants = read_csv(STAGE151_VARIANTS)
    tile4 = next((row for row in variants if row.get("variant") == "backend_tile4_r6"), {})
    body = fnum(tile4.get("body_full_us", "0"))
    sub = fnum(tile4.get("cmux_sub_us", "0"))
    sub_share = sub / body if body else 0.0
    rows.append({
        "source": "Stage151",
        "item": "current_r6_sub_share",
        "status": "PROFILE_ONLY",
        "metric": "cmux_sub_us/body_full_us",
        "value": f"{sub_share:.6f}",
        "evidence": rel(STAGE151_VARIANTS),
        "detail": "Current H14 backend tile4 r=6 profile gives the local Amdahl weight for dual-sub.",
    })
    return rows


def c_source() -> str:
    return r'''
#include <errno.h>
#include <immintrin.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct {
  uint64_t *a;
  uint64_t **b;
  int r;
  int N;
} sample_t;

static uint64_t splitmix64(uint64_t *x) {
  uint64_t z = (*x += UINT64_C(0x9e3779b97f4a7c15));
  z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
  z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
  return z ^ (z >> 31);
}

static uint64_t now_us(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (uint64_t) ts.tv_sec * UINT64_C(1000000) + (uint64_t) ts.tv_nsec / UINT64_C(1000);
}

static void *aligned_malloc_or_die(size_t bytes) {
  void *p = NULL;
  const int rc = posix_memalign(&p, 64, bytes);
  if (rc != 0 || p == NULL) {
    fprintf(stderr, "posix_memalign failed: %s\n", strerror(rc ? rc : errno));
    exit(2);
  }
  return p;
}

static sample_t sample_alloc(int r, int N) {
  sample_t s;
  s.r = r;
  s.N = N;
  s.a = (uint64_t *) aligned_malloc_or_die((size_t) N * sizeof(uint64_t));
  s.b = (uint64_t **) aligned_malloc_or_die((size_t) r * sizeof(uint64_t *));
  for (int lane = 0; lane < r; lane++) {
    s.b[lane] = (uint64_t *) aligned_malloc_or_die((size_t) N * sizeof(uint64_t));
  }
  return s;
}

static void sample_free(sample_t *s) {
  for (int lane = 0; lane < s->r; lane++) {
    free(s->b[lane]);
  }
  free(s->b);
  free(s->a);
  s->b = NULL;
  s->a = NULL;
}

static void sample_fill(sample_t *s, uint64_t seed) {
  uint64_t x = seed;
  for (int i = 0; i < s->N; i++) {
    s->a[i] = splitmix64(&x);
  }
  for (int lane = 0; lane < s->r; lane++) {
    for (int i = 0; i < s->N; i++) {
      s->b[lane][i] = splitmix64(&x);
    }
  }
}

static uint64_t sample_checksum(const sample_t *s) {
  uint64_t acc = UINT64_C(0x123456789abcdef0);
  for (int i = 0; i < s->N; i += 17) {
    acc ^= s->a[i] + UINT64_C(0x9e3779b97f4a7c15) + (acc << 6) + (acc >> 2);
  }
  for (int lane = 0; lane < s->r; lane++) {
    for (int i = lane; i < s->N; i += 19) {
      acc ^= s->b[lane][i] + UINT64_C(0xbf58476d1ce4e5b9) + (acc << 5) + (acc >> 3);
    }
  }
  return acc;
}

__attribute__((noinline))
static void sample_sub(sample_t *out, const sample_t *in1, const sample_t *in2) {
  const int vecs = in1->N / 8;
  const __m512i *a1 = (const __m512i *) in1->a;
  const __m512i *a2 = (const __m512i *) in2->a;
  __m512i *ao = (__m512i *) out->a;
  for (int i = 0; i < vecs; i++) {
    ao[i] = _mm512_sub_epi64(a1[i], a2[i]);
  }
  for (int lane = 0; lane < in1->r; lane++) {
    const __m512i *b1 = (const __m512i *) in1->b[lane];
    const __m512i *b2 = (const __m512i *) in2->b[lane];
    __m512i *bo = (__m512i *) out->b[lane];
    for (int i = 0; i < vecs; i++) {
      bo[i] = _mm512_sub_epi64(b1[i], b2[i]);
    }
  }
}

__attribute__((noinline))
static void current_pair(sample_t *direct_out, sample_t *ncmux_out,
    const sample_t *shared, const sample_t *direct_rhs, const sample_t *rotated) {
  sample_sub(direct_out, shared, direct_rhs);
  sample_sub(ncmux_out, rotated, shared);
}

__attribute__((noinline))
static void fused_pair(sample_t *direct_out, sample_t *ncmux_out,
    const sample_t *shared, const sample_t *direct_rhs, const sample_t *rotated) {
  const int vecs = shared->N / 8;
  const __m512i *sa = (const __m512i *) shared->a;
  const __m512i *da = (const __m512i *) direct_rhs->a;
  const __m512i *ra = (const __m512i *) rotated->a;
  __m512i *doa = (__m512i *) direct_out->a;
  __m512i *noa = (__m512i *) ncmux_out->a;
  for (int i = 0; i < vecs; i++) {
    const __m512i x = sa[i];
    doa[i] = _mm512_sub_epi64(x, da[i]);
    noa[i] = _mm512_sub_epi64(ra[i], x);
  }
  for (int lane = 0; lane < shared->r; lane++) {
    const __m512i *sb = (const __m512i *) shared->b[lane];
    const __m512i *db = (const __m512i *) direct_rhs->b[lane];
    const __m512i *rb = (const __m512i *) rotated->b[lane];
    __m512i *dob = (__m512i *) direct_out->b[lane];
    __m512i *nob = (__m512i *) ncmux_out->b[lane];
    for (int i = 0; i < vecs; i++) {
      const __m512i x = sb[i];
      dob[i] = _mm512_sub_epi64(x, db[i]);
      nob[i] = _mm512_sub_epi64(rb[i], x);
    }
  }
}

static int samples_equal(const sample_t *x, const sample_t *y) {
  if (memcmp(x->a, y->a, (size_t) x->N * sizeof(uint64_t)) != 0) {
    return 0;
  }
  for (int lane = 0; lane < x->r; lane++) {
    if (memcmp(x->b[lane], y->b[lane], (size_t) x->N * sizeof(uint64_t)) != 0) {
      return 0;
    }
  }
  return 1;
}

int main(int argc, char **argv) {
  const int r = argc > 1 ? atoi(argv[1]) : 6;
  const int N = argc > 2 ? atoi(argv[2]) : 2048;
  const int reps = argc > 3 ? atoi(argv[3]) : 20000;
  if (r <= 0 || N <= 0 || (N % 8) != 0 || reps <= 0) {
    fprintf(stderr, "invalid args r=%d N=%d reps=%d\n", r, N, reps);
    return 2;
  }

  sample_t shared = sample_alloc(r, N);
  sample_t direct_rhs = sample_alloc(r, N);
  sample_t rotated = sample_alloc(r, N);
  sample_t cur_direct = sample_alloc(r, N);
  sample_t cur_ncmux = sample_alloc(r, N);
  sample_t fused_direct = sample_alloc(r, N);
  sample_t fused_ncmux = sample_alloc(r, N);

  sample_fill(&shared, UINT64_C(0x15200001));
  sample_fill(&direct_rhs, UINT64_C(0x15200002));
  sample_fill(&rotated, UINT64_C(0x15200003));

  current_pair(&cur_direct, &cur_ncmux, &shared, &direct_rhs, &rotated);
  fused_pair(&fused_direct, &fused_ncmux, &shared, &direct_rhs, &rotated);
  const int ok = samples_equal(&cur_direct, &fused_direct) &&
      samples_equal(&cur_ncmux, &fused_ncmux);

  uint64_t checksum_current = 0;
  uint64_t checksum_fused = 0;
  const uint64_t current_begin = now_us();
  for (int rep = 0; rep < reps; rep++) {
    current_pair(&cur_direct, &cur_ncmux, &shared, &direct_rhs, &rotated);
  }
  const uint64_t current_us = now_us() - current_begin;
  checksum_current = sample_checksum(&cur_direct) +
      (sample_checksum(&cur_ncmux) << 1) + (uint64_t) reps;

  const uint64_t fused_begin = now_us();
  for (int rep = 0; rep < reps; rep++) {
    fused_pair(&fused_direct, &fused_ncmux, &shared, &direct_rhs, &rotated);
  }
  const uint64_t fused_us = now_us() - fused_begin;
  checksum_fused = sample_checksum(&fused_direct) +
      (sample_checksum(&fused_ncmux) << 1) + (uint64_t) reps;

  printf("STAGE152_DUAL_SUB r=%d N=%d reps=%d current_us=%" PRIu64
         " fused_us=%" PRIu64 " speedup=%.6f correctness=%s"
         " checksum_current=%" PRIu64 " checksum_fused=%" PRIu64 "\n",
         r, N, reps, current_us, fused_us,
         fused_us ? (double) current_us / (double) fused_us : 0.0,
         ok ? "PASS" : "FAIL", checksum_current, checksum_fused);

  sample_free(&shared);
  sample_free(&direct_rhs);
  sample_free(&rotated);
  sample_free(&cur_direct);
  sample_free(&cur_ncmux);
  sample_free(&fused_direct);
  sample_free(&fused_ncmux);
  return ok ? 0 : 1;
}
'''


def parse_stage152_stdout(stdout: str, run_idx: int) -> Dict[str, str]:
    values: Dict[str, str] = {"run": str(run_idx), "r": str(R_VALUE), "N": str(N_VALUE), "reps": str(REPS)}
    for token in stdout.split():
        if "=" in token:
            key, value = token.split("=", 1)
            values[key] = value
    values.setdefault("correctness", "FAIL")
    if values.get("checksum_current") != values.get("checksum_fused"):
        values["correctness"] = "FAIL"
    return values


def run_gate() -> Dict[str, str]:
    if not RUN_GATE and RAW_CSV.exists():
        rows = read_csv(RAW_CSV)
        return rows[0] if rows else {}
    write_text_lf(C_SRC, c_source().strip() + "\n")
    build = subprocess.run(
        [
            "bash", "-lc",
            f"gcc -O3 -march=native -mavx512f -Wall -Wextra "
        f"{rel(C_SRC)} -o {rel(EXE)}"
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )
    write_text_lf(BUILD_TXT, "\n".join([
        f"returncode: {build.returncode}",
        "--- stdout ---",
        sanitize(build.stdout),
        "--- stderr ---",
        sanitize(build.stderr),
    ]).rstrip() + "\n")
    if build.returncode != 0:
        return {
            "r": str(R_VALUE),
            "N": str(N_VALUE),
            "reps": str(REPS),
            "correctness": "BUILD_FAIL",
            "decision": "FAIL_STAGE152_DUAL_SUB_BUILD",
        }
    sample_rows: List[Dict[str, str]] = []
    log_parts: List[str] = []
    all_return_ok = True
    for run_idx in range(RUNS):
        run = subprocess.run(
            ["bash", "-lc", f"{rel(EXE)} {R_VALUE} {N_VALUE} {REPS}"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
        )
        all_return_ok = all_return_ok and run.returncode == 0
        log_parts.extend([
            f"run: {run_idx}",
            f"returncode: {run.returncode}",
            "--- stdout ---",
            sanitize(run.stdout),
            "--- stderr ---",
            sanitize(run.stderr),
            "",
        ])
        sample_rows.append(parse_stage152_stdout(run.stdout, run_idx))
    write_text_lf(RUN_TXT, "\n".join(log_parts).rstrip() + "\n")
    write_csv(SAMPLES_CSV, sample_rows, SAMPLE_FIELDS)

    current_values = [fnum(row.get("current_us", "0")) for row in sample_rows if row.get("current_us")]
    fused_values = [fnum(row.get("fused_us", "0")) for row in sample_rows if row.get("fused_us")]
    speedups = [fnum(row.get("speedup", "0")) for row in sample_rows if row.get("speedup")]
    correctness_ok = (
        all_return_ok
        and len(sample_rows) == RUNS
        and all(row.get("correctness") == "PASS" for row in sample_rows)
    )
    values = {
        "r": str(R_VALUE),
        "N": str(N_VALUE),
        "reps": str(REPS),
        "runs": str(len(sample_rows)),
        "current_us_mean": f"{mean(current_values):.3f}",
        "fused_us_mean": f"{mean(fused_values):.3f}",
        "speedup_mean": f"{mean(speedups):.6f}",
        "speedup_min": f"{min(speedups) if speedups else 0.0:.6f}",
        "speedup_max": f"{max(speedups) if speedups else 0.0:.6f}",
        "checksum_current": sample_rows[-1].get("checksum_current", "") if sample_rows else "",
        "checksum_fused": sample_rows[-1].get("checksum_fused", "") if sample_rows else "",
        "correctness": "PASS" if correctness_ok else "FAIL",
    }

    prior = collect_prior()
    sub_share_row = next((row for row in prior if row["item"] == "current_r6_sub_share"), {})
    sub_share = fnum(sub_share_row.get("value", "0"))
    speedup = fnum(values.get("speedup_mean", "0"))
    speedup_min = fnum(values.get("speedup_min", "0"))
    predicted = 1.0 / (1.0 - sub_share + sub_share / speedup) if speedup > 0 else 0.0
    values["predicted_body_speedup"] = f"{predicted:.6f}"
    values["sub_share_source"] = sub_share_row.get("value", "")
    if values.get("correctness") != "PASS":
        decision = "FAIL_STAGE152_DUAL_SUB_CORRECTNESS"
    elif speedup >= 1.10 and speedup_min > 1.0 and predicted >= 1.01:
        decision = "PASS_STAGE152_DUAL_SUB_LOCAL_POSITIVE_INTEGRATION_CANDIDATE"
    elif speedup > 1.0:
        decision = "WEAK_STAGE152_DUAL_SUB_LOCAL_POSITIVE_BELOW_INTEGRATION_GATE"
    else:
        decision = "NEUTRAL_STAGE152_DUAL_SUB_NOT_SELECTED"
    values["decision"] = decision
    return values


def build_summary(prior_rows: List[Dict[str, str]], raw: Dict[str, str]) -> List[Dict[str, str]]:
    stage151_ok = any(
        row["source"] == "Stage151"
        and row["item"] == "stage151_decision"
        and row["status"] == "WEAK_STAGE151_H14_R6_FULLTILE_BACKEND_TINY_POSITIVE_REPEAT_OPTIONAL"
        for row in prior_rows
    )
    correctness = raw.get("correctness", "")
    speedup = fnum(raw.get("speedup_mean", "0"))
    speedup_min = fnum(raw.get("speedup_min", "0"))
    predicted = fnum(raw.get("predicted_body_speedup", "0"))
    decision = raw.get("decision", "FAIL_STAGE152_MISSING_RESULT")
    if decision == "PASS_STAGE152_DUAL_SUB_LOCAL_POSITIVE_INTEGRATION_CANDIDATE":
        next_action = "Implement an explicit SAB dual-sub CMUX/NCMUX integration candidate and run full-SAB A/B."
    elif decision.startswith("WEAK_"):
        next_action = "Record as weak local evidence; do not integrate unless a stronger paired-sub design is proposed."
    elif decision.startswith("NEUTRAL_"):
        next_action = "Reject this local candidate and choose a different hot-path branch."
    else:
        next_action = "Repair the isolated gate before making any routing decision."
    return [
        {
            "gate": "stage152_precondition",
            "status": "PASS" if stage151_ok else "REVIEW",
            "metric": "stage151_decision",
            "value": next((row["status"] for row in prior_rows if row["item"] == "stage151_decision"), "MISSING"),
            "evidence": rel(STAGE151_SUMMARY),
            "detail": "Stage152 follows Stage151 because MAT tile composition was too weak to promote.",
            "next_action": "",
        },
        {
            "gate": "stage152_correctness",
            "status": "PASS" if correctness == "PASS" else "FAIL",
            "metric": "dual_sub_equivalence",
            "value": correctness,
            "evidence": f"{rel(RAW_CSV)}; {rel(RUN_TXT)}",
            "detail": "Fused shared-input dual subtraction must match two current pvmtmlwe_sub-equivalent operations.",
            "next_action": "Do not use timing if correctness fails.",
        },
        {
            "gate": "stage152_local_perf",
            "status": "PASS" if speedup >= 1.10 and speedup_min > 1.0 else ("WEAK" if speedup > 1.0 else "NEUTRAL"),
            "metric": "mean_speedup;min_speedup",
            "value": f"{speedup:.6f};{speedup_min:.6f}",
            "evidence": f"{rel(SAMPLES_CSV)}; {rel(RAW_CSV)}",
            "detail": "Repeated local sub-kernel speedup must be large enough to matter under the Stage151 sub-share.",
            "next_action": "",
        },
        {
            "gate": "stage152_predicted_body_impact",
            "status": "PASS" if predicted >= 1.01 else ("WEAK" if predicted > 1.0 else "NEUTRAL"),
            "metric": "amdahl_body_speedup",
            "value": f"{predicted:.6f}",
            "evidence": f"{rel(RAW_CSV)}; {rel(STAGE151_VARIANTS)}",
            "detail": "Predicted body impact uses the current r=6 cmux_sub/body share, not the whole SAB claim.",
            "next_action": "",
        },
        {
            "gate": "stage152_decision",
            "status": decision,
            "metric": "candidate_route",
            "value": "h14_c3_dual_sub",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage152 decides whether dual-sub is worth integrating into complete SAB.",
            "next_action": next_action,
        },
    ]


def write_docs(prior_rows: List[Dict[str, str]], raw_rows: List[Dict[str, str]], summary_rows: List[Dict[str, str]]) -> None:
    decision = status_by_gate(summary_rows, "stage152_decision")
    raw = raw_rows[0] if raw_rows else {}
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage152 Dual-Sub Kernel Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Test H14-C3 at the smallest meaningful implementation boundary before touching full SAB: can a shared-input dual-subtraction kernel beat two current `pvmtmlwe_sub`-equivalent operations by enough to justify integration?",
        "",
        "## Gate",
        "",
        "- Correctness: direct output equals `shared - direct_rhs`; NCMUX output equals `rotated - shared`.",
        "- Local performance: fused/current speedup must be at least `1.10x`.",
        "- Predicted body impact: Amdahl projection using current r=6 `cmux_sub/body` share must be at least `1.01x`.",
        "- Scope: this is isolated kernel evidence, not a complete SAB claim.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage152 Dual-Sub Kernel Model",
        "",
        "Date: 2026-07-03",
        "",
        "## Mechanism",
        "",
        "In each sparse butterfly bit, the sample `p[j]` participates in two nearby CMUX subtractions: a direct update computes `p[j] - p[j+power]`, while the NCMUX side computes `rotated(p[N-power+j]) - p[j]`. The existing code performs these as two independent `pvmtmlwe_sub` calls, loading the shared sample twice.",
        "",
        "The isolated Stage152 kernel computes both outputs in one pass over the shared input:",
        "",
        "```text",
        "direct_tmp = shared - direct_rhs",
        "ncmux_tmp  = rotated - shared",
        "```",
        "",
        "This can reduce shared-input loads in the subtraction stage, but it does not reduce MAT EP calls, DFT materialization, automorphism, or final extraction. Its complete-SAB ceiling is therefore bounded by the current `cmux_sub` share.",
        "",
        "## Promotion Boundary",
        "",
        "A local win is necessary but insufficient. Full SAB integration is justified only when local speedup and Amdahl projection clear the gate, then a later stage must prove phase equivalence and `T_bootstrap/r` improvement.",
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# MAT-RLWE SAB Dual-Sub Kernel Candidate",
        "",
        "Date: 2026-07-03",
        "",
        "## Candidate",
        "",
        "`H76`: shared-input dual subtraction for adjacent direct/NCMUX butterfly updates inside PVW/MAT-SAB.",
        "",
        "## Baseline",
        "",
        "Two independent `pvmtmlwe_sub`-equivalent AVX512 loops over a k=1,r=6,N=2048 PVW_TMLWE sample.",
        "",
        "## Candidate Delta",
        "",
        "One AVX512 loop computes both outputs while loading the shared sample once.",
        "",
        "## Current Status",
        "",
        f"`{decision}`",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage152 Dual-Sub Kernel Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "Stage152 tests H14-C3 as an isolated kernel gate. It does not modify `sab_pvw_*` or scalar SAB.",
        "",
        "## Summary Gates",
        "",
        table(summary_rows, ["gate", "status", "metric", "value", "detail", "next_action"]),
        "",
        "## Prior Evidence",
        "",
        table(prior_rows, PRIOR_FIELDS),
        "",
        "## Raw Result",
        "",
        table(raw_rows, RAW_FIELDS),
        "",
        "## Interpretation",
        "",
        f"The isolated dual-sub mean/min speedup is `{raw.get('speedup_mean', '')}`/`{raw.get('speedup_min', '')}` and the predicted body speedup is `{raw.get('predicted_body_speedup', '')}`. This is only a local gate; complete SAB `T_bootstrap/r` remains unclaimed until an integration stage passes.",
    ]) + "\n")


def update_longform(summary_rows: List[Dict[str, str]], raw: Dict[str, str]) -> None:
    decision = status_by_gate(summary_rows, "stage152_decision")
    block = f"""
## Stage 152: Dual-Sub Kernel Gate

Goal:

```text
Test H14-C3 shared-input dual subtraction as an isolated kernel before any
complete-SAB integration.
```

Status:

```text
Completed. Stage152 records {decision}. Isolated local speedup is
{raw.get('speedup_mean', '')} mean / {raw.get('speedup_min', '')} min and predicted r=6 body speedup is
{raw.get('predicted_body_speedup', '')}. This is not a complete SAB claim.
```
"""
    append_once(ROADMAP_MD, "## Stage 152: Dual-Sub Kernel Gate", block)
    append_once(GOAL_MD, "Stage152 tests dual-subtraction as an isolated H14-C3 gate", f"""
Stage152 tests dual-subtraction as an isolated H14-C3 gate after Stage151's
fulltile composition remains weak. It measures a shared-input AVX512
dual-subtraction kernel against two current `pvmtmlwe_sub`-equivalent loops
for k=1,r=6,N=2048. Decision: `{decision}`.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage152 as the isolated dual-sub kernel gate", f"""
56. Treat Stage152 as the isolated dual-sub kernel gate:
    `{decision}`. It is necessary evidence for H14-C3 but cannot be used as a
    complete SAB speedup claim. Full integration requires a later `T_bootstrap/r`
    gate if this local result is strong enough.
""")
    append_once(HYPOTHESIS_YAML, "H76_dual_sub_kernel_gate", f"""
  - id: H76_dual_sub_kernel_gate
    statement: >
      A shared-input dual-subtraction kernel may reduce the H14-C3 CMUX sub
      cost enough to justify complete-SAB integration if it outperforms two
      current pvmtmlwe_sub-equivalent loops and clears the Stage151 Amdahl gate.
    mechanism: >
      Adjacent direct/NCMUX butterfly updates reuse `p[j]` with opposite signs;
      the fused kernel loads this shared sample once and writes both subtraction
      outputs.
    status: stage152_dual_sub_kernel_gate
    evidence: docs/stage152_dual_sub_kernel_gate.md; experiments/stage152_dual_sub_kernel_gate_plan.md; theory_checks/stage152_dual_sub_kernel_model.md; scripts/build_stage152_dual_sub_kernel_gate.py; repro/stage152_dual_sub_kernel_gate/summary.csv; repro/stage152_dual_sub_kernel_gate/raw_results.csv
    current_decision: >
      {decision}
    failure_criteria:
      - fused dual-sub output differs from two scalar subtractions
      - local speedup is too small to move complete SAB T_bootstrap/r
      - isolated kernel result is written as a full SAB claim
""")


def update_repro(summary_rows: List[Dict[str, str]]) -> None:
    decision = status_by_gate(summary_rows, "stage152_decision")
    existing = read_csv(RUN_LOG)
    run_fields = list(existing[0].keys()) if existing else [
        "run_id", "date", "commit_or_state", "stage", "backend", "command",
        "params", "seed", "status", "summary", "artifacts",
    ]
    base_row = {field: "" for field in run_fields}
    base_row.update({
        "run_id": "stage152-dual-sub-kernel-gate-001",
        "date": "2026-07-03",
        "commit_or_state": git_head(),
        "stage": "Stage 152",
        "backend": "standalone AVX512 sub-kernel",
        "command": "python scripts/build_stage152_dual_sub_kernel_gate.py",
        "params": f"k=1; r={R_VALUE}; N={N_VALUE}; reps={REPS}; runs={RUNS}; current two-sub vs fused shared-input dual-sub",
        "seed": "deterministic splitmix64",
        "status": decision,
        "summary": "H14-C3 isolated dual-subtraction kernel correctness/performance/Amdahl gate.",
        "artifacts": rel(OUT_DIR),
    })
    run_row = {field: base_row.get(field, "") for field in run_fields}
    existing = [
        row for row in existing
        if row.get("run_id") != run_row["run_id"]
        and row.get("stage") != run_row["stage"]
    ]
    existing.append(run_row)
    write_csv(RUN_LOG, existing, run_fields)
    append_once(GLOBAL_MANIFEST, "stage152_dual_sub_kernel_gate", f"""
- stage152_dual_sub_kernel_gate: `{decision}`
  - `docs/stage152_dual_sub_kernel_gate.md`
  - `experiments/stage152_dual_sub_kernel_gate_plan.md`
  - `theory_checks/stage152_dual_sub_kernel_model.md`
  - `algorithm_variants/mat_rlwe_sab_dual_sub_kernel.md`
  - `repro/stage152_dual_sub_kernel_gate/`
""")
    append_once(CHECKLIST_MD, "Stage152 dual-sub kernel gate pack", """
- [x] Stage152 dual-sub kernel gate pack recorded.
""")


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
        else:
            rows.append({
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            })
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prior_rows = collect_prior()
    raw = run_gate()
    raw_rows = [raw]
    write_csv(PRIOR_CSV, prior_rows, PRIOR_FIELDS)
    write_csv(RAW_CSV, raw_rows, RAW_FIELDS)
    summary_rows = build_summary(prior_rows, raw)
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)
    write_docs(prior_rows, raw_rows, summary_rows)
    update_longform(summary_rows, raw)
    update_repro(summary_rows)
    artifacts = [
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD,
        C_SRC, BUILD_TXT, RUN_TXT, PRIOR_CSV, SAMPLES_CSV, RAW_CSV, SUMMARY_CSV,
        ARTIFACT_INDEX, Path(__file__).resolve(),
    ]
    write_artifact_index(artifacts)
    decision = status_by_gate(summary_rows, "stage152_decision")
    print(f"Stage152 dual-sub kernel gate: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if decision.startswith(("PASS_", "WEAK_", "NEUTRAL_")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
