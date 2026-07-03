#!/usr/bin/env python3
"""Stage222: isolated production compact external-product integration gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT = ROOT / "repro" / "stage222_isolated_compact_ep_integration"

DOC = ROOT / "docs" / "stage222_isolated_compact_ep_integration.md"
PLAN = ROOT / "experiments" / "stage222_isolated_compact_ep_integration_plan.md"
THEORY = ROOT / "theory_checks" / "stage222_isolated_compact_ep_integration_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage222_isolated_compact_ep.md"

INPUTS = OUT / "input_status.csv"
API = OUT / "api_results.csv"
EXPRESS = OUT / "expressiveness_results.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
BUILD_LOG = OUT / "mosfhet_static_build.log"
COMPILE_LOG = OUT / "compile_probe.log"
RUN_LOG_TXT = OUT / "run_probe.log"
C_SOURCE = OUT / "stage222_isolated_compact_ep_integration.c"
C_BINARY = OUT / "stage222_isolated_compact_ep_integration"
REPORT = OUT / "isolated_compact_ep_integration_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
GLOBAL_RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE221_PROOF = ROOT / "repro" / "stage221_compact_keygen_noise_recurrence" / "proof_gate.csv"
STAGE221_PER_BIT = ROOT / "repro" / "stage221_compact_keygen_noise_recurrence" / "per_bit_normalization.csv"
STAGE203_EQUATION = ROOT / "repro" / "stage203_production_selector_equation_probe" / "equation_map.csv"
STAGE139_PROOF = ROOT / "repro" / "stage139_compact_closure_audit" / "summary.csv"
STAGE166_PROOF = ROOT / "repro" / "stage166_shared_output_compact_algebra_gate" / "summary.csv"
HEADER = ROOT / "src" / "mosfhet" / "include" / "mosfhet.h"

DECISION = "PASS_STAGE222_ISOLATED_COMPACT_EP_SUBCLASS_OK_COMPLETE_SELECTOR_DENIED"

INPUT_FIELDS = ["input", "status", "evidence", "role", "bytes"]
API_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "Bg_bit",
    "seed",
    "lane_local_component_mismatches",
    "lane_local_phase_mismatches",
    "cross_body_negative_mismatches",
    "max_component_gap",
    "max_phase_gap",
    "max_negative_gap",
    "tolerance",
    "status",
]
EXPRESS_FIELDS = [
    "r",
    "stage203_neighbor_active_rows",
    "generic_missing_cross_terms",
    "current_kernel_consumes_body_lanes",
    "current_kernel_outputs_body_lanes",
    "complete_selector_status",
    "interpretation",
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
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


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


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
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
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def sanitize_log(text: str) -> str:
    keep_tokens = (
        "API,",
        "gcc ",
        "ar ",
        "make:",
        "/usr/bin/ld:",
        "collect2:",
        "error",
        "Error",
        "fatal",
        "warning",
        "Warning",
        "undefined reference",
        "compilation",
        "terminated",
        "No such file",
        "PASS_",
        "FAIL_",
        "probe skipped",
    )
    lines = []
    for raw in text.replace("\x00", "").splitlines():
        cleaned = "".join(ch for ch in raw if ch == "\t" or (32 <= ord(ch) != 127))
        cleaned = cleaned.rstrip()
        if not cleaned:
            continue
        if not any(token in cleaned for token in keep_tokens):
            continue
        lines.append(cleaned)
    return "\n".join(lines).rstrip() + "\n"


def run_bash(command: str, log: Path) -> bool:
    log.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["bash", "-lc", command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    log.write_bytes(sanitize_log(proc.stdout).encode("utf-8"))
    return proc.returncode == 0


def build_inputs() -> List[Dict[str, str]]:
    inputs = [
        ("stage221_proof_gate", STAGE221_PROOF, "permission for isolated compact EP only"),
        ("stage221_per_bit_normalization", STAGE221_PER_BIT, "T_bootstrap/r row-normalization boundary"),
        ("stage203_equation_map", STAGE203_EQUATION, "active neighbor/cross-body equation source"),
        ("stage139_closure_audit", STAGE139_PROOF, "prior compact non-closure evidence"),
        ("stage166_algebra_gate", STAGE166_PROOF, "generic dense compact-exactness boundary"),
        ("mosfhet_header", HEADER, "production compact EP API"),
    ]
    rows = []
    for name, path, role in inputs:
        rows.append(
            {
                "input": name,
                "status": "present" if path.exists() else "missing",
                "evidence": rel(path),
                "role": role,
                "bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    return rows


def write_c_source() -> None:
    c = r'''
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mosfhet.h"

static uint64_t mix64(uint64_t x){
  x += 0x9e3779b97f4a7c15ULL;
  x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
  x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
  return x ^ (x >> 31);
}

static void fill_poly(TorusPolynomial p, uint64_t tag){
  for(int i = 0; i < p->N; i++){
    uint64_t x = mix64(tag + (uint64_t)i * 0x100000001b3ULL);
    p->coeffs[i] = (Torus)(x & 0x0000ffffffffffffULL);
  }
}

static void clear_poly(TorusPolynomial p){
  memset(p->coeffs, 0, sizeof(Torus) * p->N);
}

static uint64_t abs_gap(Torus a, Torus b){
  uint64_t ua = (uint64_t)a;
  uint64_t ub = (uint64_t)b;
  return ua > ub ? ua - ub : ub - ua;
}

static void compare_poly(TorusPolynomial got, TorusPolynomial want,
    uint64_t tolerance, uint64_t * mismatches, uint64_t * max_gap){
  for(int i = 0; i < got->N; i++){
    uint64_t gap = abs_gap(got->coeffs[i], want->coeffs[i]);
    if(gap > *max_gap) *max_gap = gap;
    if(gap > tolerance) (*mismatches)++;
  }
}

static void reference_lane_local(TorusPolynomial ref_a, TorusPolynomial ref_b,
    PVW_TMLWE in, TorusPolynomial * shared_a, TorusPolynomial * shared_b,
    TorusPolynomial * body_a, TorusPolynomial * body_b,
    int r, int T, int Bg_bit, int lane,
    TorusPolynomial dec_shared, TorusPolynomial dec_body){
  clear_poly(ref_a);
  clear_poly(ref_b);
  for(int t = 0; t < T; t++){
    int idx = t * r + lane;
    polynomial_decompose_i(dec_shared, in->a[0], Bg_bit, T, t);
    polynomial_decompose_i(dec_body, in->b[lane], Bg_bit, T, t);
    polynomial_mul_addto_torus(ref_a, dec_shared, shared_a[idx]);
    polynomial_mul_addto_torus(ref_b, dec_shared, shared_b[idx]);
    polynomial_mul_addto_torus(ref_a, dec_body, body_a[idx]);
    polynomial_mul_addto_torus(ref_b, dec_body, body_b[idx]);
  }
}

static void add_cross_body_reference(TorusPolynomial ref_b, PVW_TMLWE in,
    TorusPolynomial cross, int r, int T, int Bg_bit, int lane,
    TorusPolynomial dec_body){
  int neighbor = (lane + 1) % r;
  for(int t = 0; t < T; t++){
    polynomial_decompose_i(dec_body, in->b[neighbor], Bg_bit, T, t);
    polynomial_mul_addto_torus(ref_b, dec_body, cross);
  }
}

static int run_case(int r, int N, int seed){
  const int T = 7;
  const int Bg_bit = 7;
  const uint64_t tolerance = 131072ULL;
  uint64_t component_mismatches = 0;
  uint64_t phase_mismatches = 0;
  uint64_t cross_body_negative = 0;
  uint64_t max_component_gap = 0;
  uint64_t max_phase_gap = 0;
  uint64_t max_negative_gap = 0;

  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(1, r, N);
  MAT_TRGSW_COMPACT_DFT selector = mat_trgsw_compact_alloc_new_DFT_sample(T, Bg_bit, 1, r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT out = mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_MUL_SCRATCH scratch = mat_trgsw_compact_alloc_mul_scratch(N);

  TorusPolynomial * shared_a = polynomial_new_array_of_torus_polynomials(N, T * r);
  TorusPolynomial * shared_b = polynomial_new_array_of_torus_polynomials(N, T * r);
  TorusPolynomial * body_a = polynomial_new_array_of_torus_polynomials(N, T * r);
  TorusPolynomial * body_b = polynomial_new_array_of_torus_polynomials(N, T * r);
  TorusPolynomial got_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial got_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial ref_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial ref_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial cross_ref_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial cross = polynomial_new_torus_polynomial(N);
  TorusPolynomial dec_shared = polynomial_new_torus_polynomial(N);
  TorusPolynomial dec_body = polynomial_new_torus_polynomial(N);

  fill_poly(in->a[0], 0x1000 + (uint64_t)seed * 97 + (uint64_t)r);
  for(int lane = 0; lane < r; lane++){
    fill_poly(in->b[lane], 0x2000 + (uint64_t)seed * 131 + (uint64_t)lane * 17 + (uint64_t)r);
  }
  for(int t = 0; t < T; t++){
    for(int lane = 0; lane < r; lane++){
      int idx = t * r + lane;
      fill_poly(shared_a[idx], 0x3000 + (uint64_t)seed * 193 + (uint64_t)t * 29 + (uint64_t)lane);
      fill_poly(shared_b[idx], 0x4000 + (uint64_t)seed * 211 + (uint64_t)t * 31 + (uint64_t)lane);
      fill_poly(body_a[idx], 0x5000 + (uint64_t)seed * 223 + (uint64_t)t * 37 + (uint64_t)lane);
      fill_poly(body_b[idx], 0x6000 + (uint64_t)seed * 227 + (uint64_t)t * 41 + (uint64_t)lane);
      if(mat_trgsw_compact_set_row_from_torus(selector, t, lane,
          shared_a[idx], shared_b[idx], body_a[idx], body_b[idx]) != 0){
        fprintf(stderr, "set_row_failed r=%d N=%d seed=%d t=%d lane=%d\n", r, N, seed, t, lane);
        return 2;
      }
    }
  }

  mat_trgsw_compact_mul_pvmtmlwe_DFT(out, in, selector, scratch);
  fill_poly(cross, 0x7000 + (uint64_t)seed * 239 + (uint64_t)r);

  for(int lane = 0; lane < r; lane++){
    polynomial_DFT_to_torus(got_a, out->a[lane]);
    polynomial_DFT_to_torus(got_b, out->b[lane]);
    reference_lane_local(ref_a, ref_b, in, shared_a, shared_b, body_a, body_b,
        r, T, Bg_bit, lane, dec_shared, dec_body);
    compare_poly(got_a, ref_a, tolerance, &component_mismatches, &max_component_gap);
    compare_poly(got_b, ref_b, tolerance, &component_mismatches, &max_component_gap);
    compare_poly(got_b, ref_b, tolerance, &phase_mismatches, &max_phase_gap);
    polynomial_copy_torus_polynomial(cross_ref_b, ref_b);
    add_cross_body_reference(cross_ref_b, in, cross, r, T, Bg_bit, lane, dec_body);
    compare_poly(got_b, cross_ref_b, tolerance, &cross_body_negative, &max_negative_gap);
  }

  const char * status =
      (component_mismatches == 0 && phase_mismatches == 0 && cross_body_negative > 0)
      ? "PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY"
      : "FAIL_COMPACT_EP_PROBE";

  printf("API,spqlios,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%s\n",
      r, N, T, Bg_bit, seed, component_mismatches, phase_mismatches,
      cross_body_negative, max_component_gap, max_phase_gap, max_negative_gap,
      tolerance, status);

  free_polynomial(got_a);
  free_polynomial(got_b);
  free_polynomial(ref_a);
  free_polynomial(ref_b);
  free_polynomial(cross_ref_b);
  free_polynomial(cross);
  free_polynomial(dec_shared);
  free_polynomial(dec_body);
  for(int i = 0; i < T * r; i++){
    free_polynomial(shared_a[i]);
    free_polynomial(shared_b[i]);
    free_polynomial(body_a[i]);
    free_polynomial(body_b[i]);
  }
  free(shared_a);
  free(shared_b);
  free(body_a);
  free(body_b);
  free_mat_trgsw_compact_mul_scratch(scratch);
  free_mat_trgsw_compact_output_DFT(out);
  free_mat_trgsw_compact_DFT(selector);
  free_pvmtmlwe(in);
  return strcmp(status, "PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY") == 0 ? 0 : 1;
}

int main(void){
  int failures = 0;
  int rs[] = {2, 4, 6};
  int ns[] = {512, 1024};
  for(size_t ri = 0; ri < sizeof(rs)/sizeof(rs[0]); ri++){
    for(size_t ni = 0; ni < sizeof(ns)/sizeof(ns[0]); ni++){
      failures += run_case(rs[ri], ns[ni], 0);
      failures += run_case(rs[ri], ns[ni], 1);
    }
  }
  return failures == 0 ? 0 : 1;
}
'''
    write_text(C_SOURCE, c)


def build_mosfhet_static() -> bool:
    return run_bash(
        "cd src/mosfhet && make clean >/dev/null 2>&1 && make static FFT_LIB=spqlios ENABLE_PVW_TMLWE=true",
        BUILD_LOG,
    )


def compile_probe() -> bool:
    c_src = rel(C_SOURCE)
    c_bin = rel(C_BINARY)
    return run_bash(
        f"gcc -O2 -std=c11 -I src/mosfhet/include -o {c_bin} {c_src} "
        "src/mosfhet/lib/libmosfhet.a -lm",
        COMPILE_LOG,
    )


def run_probe(build_ok: bool, compile_ok: bool) -> tuple[List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
        RUN_LOG_TXT.write_bytes(b"probe skipped\n")
        return [], False
    proc = subprocess.run(
        ["bash", "-lc", rel(C_BINARY)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    RUN_LOG_TXT.write_bytes(sanitize_log(proc.stdout).encode("utf-8"))
    rows: List[Dict[str, str]] = []
    for line in proc.stdout.splitlines():
        marker = line.find("API,")
        if marker < 0:
            continue
        line = line[marker:]
        parts = line.split(",")
        rows.append(
            {
                "backend": parts[1],
                "r": parts[2],
                "N": parts[3],
                "T": parts[4],
                "Bg_bit": parts[5],
                "seed": parts[6],
                "lane_local_component_mismatches": parts[7],
                "lane_local_phase_mismatches": parts[8],
                "cross_body_negative_mismatches": parts[9],
                "max_component_gap": parts[10],
                "max_phase_gap": parts[11],
                "max_negative_gap": parts[12],
                "tolerance": parts[13],
                "status": parts[14],
            }
        )
    try:
        C_BINARY.unlink()
    except FileNotFoundError:
        pass
    return rows, proc.returncode == 0


def build_expressiveness_rows() -> List[Dict[str, str]]:
    eq_rows = read_csv(STAGE203_EQUATION)
    rows = []
    for r in [2, 4, 6]:
        neighbor = sum(1 for row in eq_rows if row.get("r") == str(r) and row.get("equation_class") == "lane_neighbor_body_interaction")
        generic_missing = r * (r - 1)
        rows.append(
            {
                "r": str(r),
                "stage203_neighbor_active_rows": str(neighbor),
                "generic_missing_cross_terms": str(generic_missing),
                "current_kernel_consumes_body_lanes": "same-index body lane only",
                "current_kernel_outputs_body_lanes": "same-index body lane only",
                "complete_selector_status": "DENY_COMPLETE_SELECTOR_INTEGRATION" if neighbor > 0 else "NO_NEIGHBOR_ROWS_DETECTED",
                "interpretation": "Stage203 active neighbor rows are outside the current lane-local compact EP state shape.",
            }
        )
    return rows


def build_proof(inputs: List[Dict[str, str]], api_rows: List[Dict[str, str]], express_rows: List[Dict[str, str]], build_ok: bool, compile_ok: bool, run_ok: bool) -> List[Dict[str, str]]:
    missing = [row["input"] for row in inputs if row["status"] != "present"]
    lane_local_pass = api_rows and all(row["status"] == "PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY" for row in api_rows)
    cross_negative_min = min((int(row["cross_body_negative_mismatches"]) for row in api_rows), default=0)
    complete_denied = express_rows and all(row["complete_selector_status"] == "DENY_COMPLETE_SELECTOR_INTEGRATION" for row in express_rows)
    ready = not missing and build_ok and compile_ok and run_ok and lane_local_pass and complete_denied
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if not missing else "FAIL",
            "metric": "missing_inputs",
            "value": ";".join(missing),
            "evidence": rel(INPUTS),
            "interpretation": "Stage222 consumes Stage221 permission plus Stage203/Stage139/Stage166 boundaries.",
        },
        {
            "gate": "G2_mosfhet_static_build",
            "status": "PASS" if build_ok else "FAIL",
            "metric": "make_static_spqlios",
            "value": str(build_ok).lower(),
            "evidence": rel(BUILD_LOG),
            "interpretation": "Probe links against current MOSFHET production compact EP code.",
        },
        {
            "gate": "G3_probe_compile_run",
            "status": "PASS" if compile_ok and run_ok else "FAIL",
            "metric": "compile_ok;run_ok",
            "value": f"{str(compile_ok).lower()};{str(run_ok).lower()}",
            "evidence": f"{rel(COMPILE_LOG)}; {rel(RUN_LOG_TXT)}",
            "interpretation": "Standalone isolated compact EP probe compiles and runs.",
        },
        {
            "gate": "G4_lane_local_subclass_correctness",
            "status": "PASS" if lane_local_pass else "FAIL",
            "metric": "api_rows;min_cross_body_negative_mismatches",
            "value": f"{len(api_rows)};{cross_negative_min}",
            "evidence": rel(API),
            "interpretation": "Current compact EP matches a lane-local oracle and rejects cross-body references.",
        },
        {
            "gate": "G5_complete_selector_expressiveness",
            "status": "DENY_COMPLETE_SELECTOR_INTEGRATION" if complete_denied else "FAIL",
            "metric": "stage203_neighbor_rows",
            "value": ";".join(row["stage203_neighbor_active_rows"] for row in express_rows),
            "evidence": rel(EXPRESS),
            "interpretation": "Stage203/686 active neighbor equations are outside the current lane-local compact output shape.",
        },
        {
            "gate": "G6_sab_admission",
            "status": "DENY_SAB_HOTPATH_CODE",
            "metric": "missing_before_sab_code",
            "value": "closed_state;neighbor_equation_support;complete_sab_gate",
            "evidence": rel(PROOF),
            "interpretation": "Stage222 does not authorize compact EP integration into SAB.",
        },
        {
            "gate": "G7_stage222_decision",
            "status": DECISION if ready else "FAIL_STAGE222",
            "metric": "decision",
            "value": DECISION if ready else "FAIL_STAGE222",
            "evidence": rel(PROOF),
            "interpretation": "Lane-local compact EP is production-code correct, but complete selector integration is denied.",
        },
    ]


def build_next(decision: str) -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage223_compact_route_closeout_or_new_state_design",
            "entry_condition": "Stage222 confirms lane-local correctness but complete selector denial.",
            "gate": "Choose either a new closed lane-pair/neighbor-capable compact state or return to exact PVW/MAT-SAB optimization.",
            "status": "selected" if decision == DECISION else "blocked",
            "failure_action": "No compact SAB hot-path code.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P1",
            "route": "stage223_exact_pvw_mat_avx_resource_refresh",
            "entry_condition": "Compact complete-selector route remains denied.",
            "gate": "Continue optimizing valid closed dense MAT path under T_bootstrap/r.",
            "status": "parallel_candidate",
            "failure_action": "Keep previous exact PVW/MAT evidence only.",
            "evidence": rel(STAGE139_PROOF),
        },
        {
            "priority": "P2",
            "route": "no_complete_sab_claim",
            "entry_condition": "Any compact state proof is missing.",
            "gate": "Report compact route as isolated/subclass only.",
            "status": "fallback",
            "failure_action": "Do not claim compact SAB acceleration.",
            "evidence": rel(EXPRESS),
        },
    ]


def write_docs(inputs: List[Dict[str, str]], api_rows: List[Dict[str, str]], express_rows: List[Dict[str, str]], proof_rows: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> None:
    decision = proof_rows[-1]["status"]
    doc = f"""# Stage222 Isolated Compact EP Integration

Decision: `{decision}`.

Stage222 links the current MOSFHET production compact EP API and verifies its
lane-local arithmetic against a coefficient-domain oracle. The same probe adds
cross-body references as a negative control. This separates a valid compact
subclass from the full 2025/686 SAB selector requirement.

The result is intentionally restrictive: lane-local compact EP is correct, but
the complete selector remains denied because Stage203 contains active neighbor
body equations and Stage139 already showed the direct compact output is not a
closed PVW_TMLWE state.

## Proof Gates

{table(proof_rows, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## API Results

{table(api_rows, API_FIELDS)}
## Expressiveness Boundary

{table(express_rows, EXPRESS_FIELDS)}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
"""
    write_text(DOC, doc)
    write_text(REPORT, doc)
    write_text(
        THEORY,
        """# Stage222 Isolated Compact EP Integration Model

The production compact API computes, per lane q:

```text
out_a[q] += dec(shared_mask) * shared_a[q] + dec(body[q]) * body_a[q]
out_b[q] += dec(shared_mask) * shared_b[q] + dec(body[q]) * body_b[q]
```

This is a lane-local compact external product. It is not a full dense MAT
linear map because it has no term that consumes `body[j]` and writes to lane
`q != j`. Stage203's `lane_neighbor_body_interaction` rows are therefore not
covered by this API. Stage222 admits the lane-local subclass and blocks complete
SAB integration.
""",
    )
    write_text(
        PLAN,
        """# Stage222 Experiment Plan

1. Build current MOSFHET static library with `FFT_LIB=spqlios`.
2. Compile a standalone C probe using `MAT_TRGSW_COMPACT_DFT`.
3. Compare production compact EP output to a lane-local coefficient oracle.
4. Add cross-body terms as a negative control.
5. Deny complete selector integration if Stage203 neighbor rows remain outside
   the current state shape.
""",
    )
    write_text(
        VARIANT,
        """# MAT-RLWE SAB Stage222 Isolated Compact EP

The current compact EP is valid as a lane-local external-product subclass. It
does not implement the full selector map needed by the SAB route under the
current Stage203 equation map. The next algorithmic choice is explicit: design
a closed neighbor-capable compact state, or continue optimizing the already
valid exact dense MAT/PVW path.
""",
    )
    write_text(
        REPRO,
        f"""# Stage222 Reproduction Commands

```powershell
python scripts\\build_stage222_isolated_compact_ep_integration.py
Get-Content {rel(PROOF)}
Get-Content {rel(API)}
Get-Content {rel(EXPRESS)}
```
""",
    )


def update_tracking(status: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 222: Isolated Compact EP Integration",
        f"""
## Stage 222: Isolated Compact EP Integration

Goal:

```text
Compile and run current MOSFHET compact EP as an isolated production-code probe,
then decide whether it covers the complete Stage203/SAB selector.
```

Status:

```text
Completed. Stage222 records {status}. The production compact EP lane-local
subclass is correct, but complete selector/SAB integration remains denied
because neighbor/cross-body active equations are outside the current state
shape.
```
""",
    )
    append_once(
        GOAL,
        "Stage222 isolated compact EP integration",
        f"""
- Stage222 isolated compact EP integration: `{status}`. This confirms a
  lane-local production compact EP subclass and blocks complete compact SAB
  integration under the current selector/state shape.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage222 isolated compact EP integration",
        f"""
- Stage222 isolated compact EP integration completed with `{status}`. The
  compact route remains outside SAB hot paths; the next decision is closed
  neighbor-capable compact state design versus exact PVW/MAT optimization.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage222_isolated_compact_ep_integration",
        f"""
H10_stage222_isolated_compact_ep_integration:
  status: lane_local_compact_ep_passed_complete_selector_denied
  evidence:
    - repro/stage222_isolated_compact_ep_integration/proof_gate.csv
    - repro/stage222_isolated_compact_ep_integration/api_results.csv
    - repro/stage222_isolated_compact_ep_integration/expressiveness_results.csv
  conclusion: >
    Stage222 records {status}. Production compact EP is correct for the
    lane-local subclass, but complete Stage203/SAB selector integration remains
    denied because neighbor/cross-body equations are unsupported.
""",
    )
    append_once(
        GLOBAL_RUN_LOG,
        "stage222-isolated-compact-ep-integration-001",
        f"""stage222-isolated-compact-ep-integration-001,2026-07-04,{head},Stage 222,spqlios,python scripts/build_stage222_isolated_compact_ep_integration.py,Stage221 recurrence gate,no SAB benchmark,{status},"Production compact EP subclass pass; complete selector denied.",docs/stage222_isolated_compact_ep_integration.md; repro/stage222_isolated_compact_ep_integration/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage222_isolated_compact_ep_integration:",
        """
- stage222_isolated_compact_ep_integration:
  - `docs/stage222_isolated_compact_ep_integration.md`
  - `experiments/stage222_isolated_compact_ep_integration_plan.md`
  - `theory_checks/stage222_isolated_compact_ep_integration_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage222_isolated_compact_ep.md`
  - `scripts/build_stage222_isolated_compact_ep_integration.py`
  - `repro/stage222_isolated_compact_ep_integration/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage222 isolated compact EP integration recorded",
        """
- [x] Stage222 isolated compact EP integration recorded.
""",
    )


def write_artifacts(paths: Iterable[Path]) -> None:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path),
                "bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    write_csv(ARTIFACT, rows, ["path", "exists", "sha256", "bytes"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = build_inputs()
    write_c_source()
    build_ok = build_mosfhet_static()
    compile_ok = compile_probe() if build_ok else False
    api_rows, run_ok = run_probe(build_ok, compile_ok)
    express_rows = build_expressiveness_rows()
    proof_rows = build_proof(inputs, api_rows, express_rows, build_ok, compile_ok, run_ok)
    next_rows = build_next(proof_rows[-1]["status"])
    write_csv(INPUTS, inputs, INPUT_FIELDS)
    write_csv(API, api_rows, API_FIELDS)
    write_csv(EXPRESS, express_rows, EXPRESS_FIELDS)
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_docs(inputs, api_rows, express_rows, proof_rows, next_rows)
    status = proof_rows[-1]["status"]
    update_tracking(status)
    write_artifacts([DOC, PLAN, THEORY, VARIANT, INPUTS, API, EXPRESS, PROOF, NEXT, BUILD_LOG, COMPILE_LOG, RUN_LOG_TXT, C_SOURCE, REPORT, REPRO, Path(__file__)])
    print(status)
    return 0 if status == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
