#!/usr/bin/env python3
"""Stage157: sub+decompose fusion preflight.

Stage156 rejects a DFT-only lazy accumulator. This stage checks a smaller,
same-format candidate: compute gadget decomposition of (in2 - in1) directly,
instead of materializing a full PVW_TMLWE sub sample and then decomposing it.

The stage is an isolated C microbench only. It does not modify production
headers or SAB code.
"""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage157_sub_decompose_fusion_preflight"
C_SRC = OUT_DIR / "stage157_sub_decompose_probe.c"
EXE = OUT_DIR / "stage157_sub_decompose_probe.exe"
BUILD_LOG = OUT_DIR / "build.log"
RUN_LOG_FILE = OUT_DIR / "run.log"

SUMMARY_CSV = OUT_DIR / "summary.csv"
RESULTS_CSV = OUT_DIR / "microbench_results.csv"
CORRECTNESS_CSV = OUT_DIR / "correctness.csv"
DECISION_CSV = OUT_DIR / "decision.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

DOC_STAGE = ROOT / "docs" / "stage157_sub_decompose_fusion_preflight.md"
DOC_PLAN = ROOT / "experiments" / "stage157_sub_decompose_fusion_preflight_plan.md"
DOC_THEORY = ROOT / "theory_checks" / "stage157_sub_decompose_fusion_model.md"
DOC_VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_sub_decompose_fusion.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_DOC = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"


C_CODE = r'''
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static uint64_t xs64(uint64_t *s) {
  uint64_t x = *s;
  x ^= x << 13;
  x ^= x >> 7;
  x ^= x << 17;
  *s = x;
  return x;
}

static double now_seconds(void) {
  return (double) clock() / (double) CLOCKS_PER_SEC;
}

static uint64_t dense_offset(int bg_bit, int l) {
  const int word_size = 64;
  uint64_t offset = 0;
  for (int i = 0; i < l; i++) {
    offset += (1ULL << (word_size - i * bg_bit - 1));
  }
  return offset;
}

static uint64_t decomp_dense_coeff(uint64_t x, int bg_bit, int l, int level) {
  const int word_size = 64;
  const uint64_t half_bg = (1ULL << (bg_bit - 1));
  const uint64_t h_mask = (1ULL << bg_bit) - 1;
  const uint64_t h_bit = (uint64_t)(word_size - (level + 1) * bg_bit);
  const uint64_t coeff_off = x + dense_offset(bg_bit, l);
  return ((coeff_off >> h_bit) & h_mask) - half_bg;
}

static uint64_t separate_sub_then_decompose(
    uint64_t *dec, uint64_t *sub, const uint64_t *in1, const uint64_t *in2,
    int components, int n, int bg_bit, int l) {
  uint64_t checksum = 0;
  const int total = components * n;
  for (int i = 0; i < total; i++) {
    sub[i] = in2[i] - in1[i];
  }
  for (int level = 0; level < l; level++) {
    for (int comp = 0; comp < components; comp++) {
      for (int c = 0; c < n; c++) {
        const int idx = comp * n + c;
        const int out_idx = (comp * l + level) * n + c;
        dec[out_idx] = decomp_dense_coeff(sub[idx], bg_bit, l, level);
        checksum += dec[out_idx] + (uint64_t)(out_idx + 1);
      }
    }
  }
  return checksum;
}

static uint64_t fused_sub_decompose(
    uint64_t *dec, const uint64_t *in1, const uint64_t *in2,
    int components, int n, int bg_bit, int l) {
  uint64_t checksum = 0;
  for (int level = 0; level < l; level++) {
    for (int comp = 0; comp < components; comp++) {
      for (int c = 0; c < n; c++) {
        const int idx = comp * n + c;
        const int out_idx = (comp * l + level) * n + c;
        const uint64_t diff = in2[idx] - in1[idx];
        dec[out_idx] = decomp_dense_coeff(diff, bg_bit, l, level);
        checksum += dec[out_idx] + (uint64_t)(out_idx + 1);
      }
    }
  }
  return checksum;
}

static int run_case(const char *name, int components, int n, int bg_bit, int l, int reps) {
  const int total = components * n;
  const int dec_total = components * l * n;
  uint64_t *in1 = (uint64_t *) malloc((size_t) total * sizeof(uint64_t));
  uint64_t *in2 = (uint64_t *) malloc((size_t) total * sizeof(uint64_t));
  uint64_t *sub = (uint64_t *) malloc((size_t) total * sizeof(uint64_t));
  uint64_t *dec_sep = (uint64_t *) malloc((size_t) dec_total * sizeof(uint64_t));
  uint64_t *dec_fused = (uint64_t *) malloc((size_t) dec_total * sizeof(uint64_t));
  if (!in1 || !in2 || !sub || !dec_sep || !dec_fused) {
    fprintf(stderr, "allocation failed\n");
    return 2;
  }

  uint64_t seed = 0x5354414745313537ULL;
  for (int i = 0; i < total; i++) {
    in1[i] = xs64(&seed);
    in2[i] = xs64(&seed);
  }

  uint64_t c1 = separate_sub_then_decompose(dec_sep, sub, in1, in2, components, n, bg_bit, l);
  uint64_t c2 = fused_sub_decompose(dec_fused, in1, in2, components, n, bg_bit, l);
  int mismatches = 0;
  int first = -1;
  for (int i = 0; i < dec_total; i++) {
    if (dec_sep[i] != dec_fused[i]) {
      mismatches++;
      if (first < 0) first = i;
    }
  }

  volatile uint64_t sink = c1 ^ c2;
  double start = now_seconds();
  for (int r = 0; r < reps; r++) {
    sink ^= separate_sub_then_decompose(dec_sep, sub, in1, in2, components, n, bg_bit, l);
  }
  double sep_s = now_seconds() - start;

  start = now_seconds();
  for (int r = 0; r < reps; r++) {
    sink ^= fused_sub_decompose(dec_fused, in1, in2, components, n, bg_bit, l);
  }
  double fused_s = now_seconds() - start;

  const double sep_ns = (sep_s * 1000000000.0) / (double) reps;
  const double fused_ns = (fused_s * 1000000000.0) / (double) reps;
  const double speedup = fused_ns > 0.0 ? sep_ns / fused_ns : 0.0;
  printf("%s,%d,%d,%d,%d,%d,%d,%d,%.3f,%.3f,%.6f,%" PRIu64 "\n",
      name, components, n, bg_bit, l, reps, mismatches, first,
      sep_ns, fused_ns, speedup, sink);

  free(in1);
  free(in2);
  free(sub);
  free(dec_sep);
  free(dec_fused);
  return mismatches ? 1 : 0;
}

int main(void) {
  printf("case,components,N,Bg_bit,l,reps,mismatches,first_mismatch,separate_ns,fused_ns,speedup,sink\n");
  int rc = 0;
  rc |= run_case("target_r6_N2048_l1_bg23", 7, 2048, 23, 1, 8000);
  rc |= run_case("control_r4_N2048_l1_bg23", 5, 2048, 23, 1, 10000);
  rc |= run_case("control_r6_N2048_l2_bg8", 7, 2048, 8, 2, 5000);
  return rc;
}
'''


def write_csv(path: Path, rows: List[Dict[str, object]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cmd(cmd: List[str], log: Path) -> int:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log.write_text("command: " + " ".join(cmd) + "\n" + proc.stdout, encoding="ascii", errors="ignore")
    return proc.returncode


def parse_results(text: str) -> List[Dict[str, object]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    reader = csv.DictReader(lines)
    return [dict(row) for row in reader]


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    C_SRC.write_text(C_CODE, encoding="ascii", newline="\n")

    gcc = shutil.which("gcc")
    if not gcc:
      decision = "BLOCKED_STAGE157_NO_GCC"
      result_rows: List[Dict[str, object]] = []
      correctness_rows = [{"case": "all", "status": "BLOCKED", "detail": "gcc not found"}]
    else:
      compile_cmd = [gcc, "-O3", "-march=native", str(C_SRC), "-o", str(EXE)]
      build_rc = run_cmd(compile_cmd, BUILD_LOG)
      if build_rc != 0:
        decision = "FAIL_STAGE157_BUILD"
        result_rows = []
        correctness_rows = [{"case": "all", "status": "FAIL", "detail": "C probe did not compile"}]
      else:
        proc = subprocess.run([str(EXE)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        RUN_LOG_FILE.write_text(proc.stdout, encoding="ascii", errors="ignore")
        result_rows = parse_results(proc.stdout)
        correctness_rows = [
            {
                "case": row.get("case", ""),
                "status": "PASS" if row.get("mismatches") == "0" else "FAIL",
                "mismatches": row.get("mismatches", ""),
                "first_mismatch": row.get("first_mismatch", ""),
            }
            for row in result_rows
        ]
        if proc.returncode != 0 or any(row.get("status") != "PASS" for row in correctness_rows):
            decision = "FAIL_STAGE157_CORRECTNESS"
        else:
            target = next((row for row in result_rows if row.get("case") == "target_r6_N2048_l1_bg23"), {})
            speedup = float(target.get("speedup", "0") or 0)
            if speedup >= 1.05:
                decision = "PASS_STAGE157_SUB_DECOMP_FUSION_PREFLIGHT_POSITIVE_IMPLEMENTATION_CANDIDATE"
            elif speedup >= 0.98:
                decision = "NEUTRAL_STAGE157_SUB_DECOMP_FUSION_PREFLIGHT_LOW_SIGNAL"
            else:
                decision = "REJECT_STAGE157_SUB_DECOMP_FUSION_PREFLIGHT_SLOWER"

    result_fields = [
        "case", "components", "N", "Bg_bit", "l", "reps", "mismatches",
        "first_mismatch", "separate_ns", "fused_ns", "speedup", "sink",
    ]
    write_csv(RESULTS_CSV, result_rows, result_fields)
    write_csv(CORRECTNESS_CSV, correctness_rows, ["case", "status", "mismatches", "first_mismatch", "detail"])

    target = next((row for row in result_rows if row.get("case") == "target_r6_N2048_l1_bg23"), {})
    target_speedup = target.get("speedup", "0")
    decision_rows = [
        {
            "gate": "stage157_build",
            "status": "PASS" if gcc and (not BUILD_LOG.exists() or "error:" not in BUILD_LOG.read_text(encoding="ascii", errors="ignore").lower()) else ("BLOCKED" if not gcc else "SEE_LOG"),
            "metric": "gcc",
            "value": gcc or "MISSING",
            "evidence": rel(BUILD_LOG) if BUILD_LOG.exists() else "",
            "detail": "Standalone C probe compile gate.",
            "next_action": "Install/use gcc before interpreting microbench if blocked.",
        },
        {
            "gate": "stage157_correctness",
            "status": "PASS" if correctness_rows and all(row.get("status") == "PASS" for row in correctness_rows) else ("BLOCKED" if not gcc else "FAIL"),
            "metric": "mismatches",
            "value": ";".join(str(row.get("mismatches", "")) for row in correctness_rows),
            "evidence": rel(CORRECTNESS_CSV),
            "detail": "Fused sub-decompose must match separate sub then dense pvmtmlwe_decompose exactly.",
            "next_action": "Do not implement if any mismatch appears.",
        },
        {
            "gate": "stage157_microbench",
            "status": "PASS" if result_rows else ("BLOCKED" if not gcc else "FAIL"),
            "metric": "target_speedup",
            "value": target_speedup,
            "evidence": rel(RESULTS_CSV),
            "detail": "Standalone loop preflight only; no full-SAB claim.",
            "next_action": "Only open production implementation if target speedup exceeds preflight threshold.",
        },
        {
            "gate": "stage157_decision",
            "status": decision,
            "metric": "candidate_route",
            "value": "sub_decompose_fusion",
            "evidence": rel(DECISION_CSV),
            "detail": "Decide whether direct decompose(in2-in1) is worth implementing behind a flag.",
            "next_action": "If positive, add an explicit MAT EP from precomputed decomposed-difference path; otherwise route to compact/cache work.",
        },
    ]
    write_csv(DECISION_CSV, decision_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_csv(SUMMARY_CSV, decision_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(result_rows, correctness_rows, decision_rows, decision)
    update_global_docs(decision)

    artifacts = [
        SUMMARY_CSV, RESULTS_CSV, CORRECTNESS_CSV, DECISION_CSV, C_SRC,
        BUILD_LOG, RUN_LOG_FILE, DOC_STAGE, DOC_PLAN, DOC_THEORY, DOC_VARIANT,
    ]
    artifact_rows = [
        {"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in artifacts if path.exists()
    ]
    write_csv(ARTIFACT_CSV, artifact_rows, ["path", "sha256", "bytes"])

    print(f"Stage157 sub-decompose fusion preflight: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")


def write_docs(
    result_rows: List[Dict[str, object]],
    correctness_rows: List[Dict[str, object]],
    decision_rows: List[Dict[str, object]],
    decision: str,
) -> None:
    DOC_STAGE.write_text(f"""# Stage157 Sub-Decompose Fusion Preflight

Decision: `{decision}`

Stage157 tests an isolated same-format candidate after Stage156 rejects naive
DFT-only state: compute `decompose(in2-in1)` directly instead of first writing
the `sub` PVW_TMLWE and then decomposing it. This is a standalone C microbench;
it does not alter production code.

## Correctness

{md_table(correctness_rows, ["case", "status", "mismatches", "first_mismatch"])}

## Microbench

{md_table(result_rows, ["case", "components", "N", "Bg_bit", "l", "reps", "separate_ns", "fused_ns", "speedup"])}

## Decision

{md_table(decision_rows, ["gate", "status", "metric", "value", "next_action"])}

Interpretation: this preflight targets memory traffic around `pvmtmlwe_sub`
and dense `pvmtmlwe_decompose`, not the DFT or MAT addmul itself. A positive
result is only permission to implement a guarded production path and rerun
complete SAB `T_bootstrap/r`.
""", encoding="utf-8", newline="\n")

    DOC_PLAN.write_text("""# Stage157 Experiment Plan

Goal: test whether fusing `sub = in2 - in1` with dense gadget decomposition is
worth implementing in production.

Method:

- generate a standalone C probe;
- use the dense `pvmtmlwe_decompose` offset formula;
- compare separate sub+decompose against direct decompose(in2-in1);
- benchmark target `k=1,r=6,N=2048,l=1,Bg_bit=23`.

Correctness gate: exact digit equality for every component and coefficient.

Performance gate: target fused/separate speedup must exceed the positive
threshold before production implementation.

Failure handling: if neutral or negative, keep the result as an ablation and
route to compact/cache representation work.
""", encoding="utf-8", newline="\n")

    DOC_THEORY.write_text("""# Stage157 Sub-Decompose Fusion Model

Stage156 showed that decomposition cannot be maintained linearly across SAB
updates. Stage157 tests a narrower mechanism that remains exact:

```text
separate: sub = in2 - in1; D = decompose(sub)
fused:    D = decompose(in2 - in1)
```

The fused form does not change the decomposition formula or selector semantics.
It only removes the full intermediate sub write/read in the microbench. It
therefore targets the Stage155 `sub` share and possibly part of the memory
traffic immediately before MAT EP. It cannot reduce the 573440 external-product
or materialization count.
""", encoding="utf-8", newline="\n")

    DOC_VARIANT.write_text("""# MAT-RLWE SAB Sub-Decompose Fusion Variant

Candidate:

```text
Add a guarded internal path that accepts two PVW_TMLWE operands and computes
DFT gadget digits for their difference directly.
```

Required later production shape if Stage157 is positive:

- keep scalar/default SAB unchanged;
- add a new explicit flag;
- preserve `sab_pvw_CMUX_from_sub_internal` as reference;
- validate exact per-step phase equality;
- run complete SAB `T_bootstrap/r` A/B.

Stage157 itself is only an isolated preflight.
""", encoding="utf-8", newline="\n")


def update_global_docs(decision: str) -> None:
    append_once(
        ROADMAP,
        "## Stage 157: Sub-Decompose Fusion Preflight",
        f"""## Stage 157: Sub-Decompose Fusion Preflight

Goal:

```text
Test whether direct decompose(in2-in1) is a viable same-format implementation
candidate after naive lazy DFT is rejected.
```

Status:

```text
Completed. Stage157 records {decision}. It is an isolated C microbench only;
any positive result still requires a guarded production path and full-SAB
T_bootstrap/r gate.
```
""",
    )
    append_once(
        GOAL_DOC,
        "Stage157 tests sub-decompose fusion",
        f"""Stage157 tests sub-decompose fusion as a narrow same-format candidate after
Stage156. Decision: `{decision}`. This preflight targets the intermediate
`pvmtmlwe_sub` plus dense decomposition memory path only and does not claim
complete-SAB acceleration without later integration.
""",
    )
    append_once(
        CURRENT_GOAL,
        "61. Treat Stage157 as the sub-decompose fusion preflight",
        f"""61. Treat Stage157 as the sub-decompose fusion preflight:
    `{decision}`. It gives or denies permission to implement direct
    `decompose(in2-in1)` behind an explicit PVW/MAT-SAB flag.
""",
    )
    append_once(
        HYPOTHESES,
        "H81_sub_decompose_fusion",
        f"""  - id: H81_sub_decompose_fusion
    statement: >
      Directly computing decompose(in2-in1) may reduce same-format
      PVW/MAT-SAB memory traffic enough to justify a guarded production path.
    mechanism: >
      The fused loop removes the intermediate PVW_TMLWE sub write/read while
      preserving the exact dense pvmtmlwe_decompose formula.
    status: stage157_sub_decompose_fusion_preflight
    evidence: docs/stage157_sub_decompose_fusion_preflight.md; experiments/stage157_sub_decompose_fusion_preflight_plan.md; theory_checks/stage157_sub_decompose_fusion_model.md; algorithm_variants/mat_rlwe_sab_sub_decompose_fusion.md; repro/stage157_sub_decompose_fusion_preflight/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - fused digits mismatch separate sub then decomposition
      - target standalone speedup is neutral or negative
      - complete SAB T_bootstrap_per_lane does not improve after guarded integration
""",
    )
    append_once(
        RUN_LOG,
        "stage157-sub-decompose-fusion-preflight-001",
        f"2026-07-03,stage157-sub-decompose-fusion-preflight-001,microbench,none,SET_2_3_2048,BINARY,{decision},docs/stage157_sub_decompose_fusion_preflight.md;repro/stage157_sub_decompose_fusion_preflight/summary.csv\n",
    )
    append_once(
        MANIFEST,
        "stage157_sub_decompose_fusion_preflight",
        "- `repro/stage157_sub_decompose_fusion_preflight/`: Stage157 sub-decompose fusion preflight outputs.\n",
    )
    append_once(
        CHECKLIST,
        "Stage157 sub-decompose fusion preflight",
        "- [x] Stage157 sub-decompose fusion standalone C microbench generated and recorded.\n",
    )


def md_table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(out)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


if __name__ == "__main__":
    build()
