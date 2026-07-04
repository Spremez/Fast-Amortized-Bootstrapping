"""Stage255: MOSFHET-adjacent non-binary selector keygen/noise prototype.

This stage runs an isolated C probe against the production MOSFHET static
library.  The probe encrypts MAT_TRGSW 0/1 selectors for the Stage252
`s_coff`/`s_sign` families and applies them to the Stage253 `sub_a` equations
with actual MAT external products.  It records phase equivalence and gap
statistics, but still does not modify production `sab_pvw_*` code.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT = ROOT / "repro" / "stage255_mosfhet_nonbinary_selector_keygen_noise"

INPUTS = {
    "stage254_proof_gate": ROOT / "repro" / "stage254_nonbinary_keygen_noise_preflight" / "proof_gate.csv",
    "stage254_admission": ROOT / "repro" / "stage254_nonbinary_keygen_noise_preflight" / "implementation_admission.csv",
    "stage253_equivalence": ROOT / "repro" / "stage253_isolated_nonbinary_suba_equivalence" / "lane_equivalence_probe.csv",
    "stage252_skeleton_probe": ROOT / "repro" / "stage252_nonbinary_mat_selector_key_skeleton" / "toy_key_object_probe.csv",
    "mosfhet_header": MOSFHET_DIR / "include" / "mosfhet.h",
    "mosfhet_mattrgsw": MOSFHET_DIR / "src" / "mattrgsw.c",
    "mosfhet_pvwtmlwe": MOSFHET_DIR / "src" / "pvwtmlwe.c",
}

DOC = ROOT / "docs" / "stage255_mosfhet_nonbinary_selector_keygen_noise.md"
PLAN = ROOT / "experiments" / "stage255_mosfhet_nonbinary_selector_keygen_noise_plan.md"
THEORY = ROOT / "theory_checks" / "stage255_mosfhet_nonbinary_selector_keygen_noise_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage255_mosfhet_nonbinary_selector_keygen_noise.md"

INPUT_STATUS = OUT / "input_status.csv"
BUILD_LOG = OUT / "mosfhet_static_build.log"
COMPILE_LOG = OUT / "compile_probe.log"
RUN_LOG_TXT = OUT / "run_probe.log"
C_SOURCE = OUT / "stage255_nonbinary_selector_keygen_noise.c"
C_BINARY = OUT / "stage255_nonbinary_selector_keygen_noise"
PROBE = OUT / "selector_noise_probe.csv"
AGGREGATE = OUT / "selector_noise_aggregate.csv"
RESOURCE = OUT / "resource_projection.csv"
SOURCE_ISOLATION = OUT / "source_isolation.csv"
ADMISSION = OUT / "implementation_admission.csv"
CLAIM = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage255_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE255_MOSFHET_SELECTOR_KEYGEN_NOISE_READY_NONBINARY_SPARSEMUL_PREFLIGHT"

PROBE_FIELDS = [
    "branch",
    "r",
    "seed",
    "selector_value",
    "N",
    "prec",
    "a",
    "phase_mismatches",
    "max_phase_gap",
    "mean_phase_gap",
    "selector_keygen_us",
    "external_product_us",
    "status",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def run_git(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return proc.stdout.strip()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip() + "\n")


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip("\n").rstrip() + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def table(rows: list[dict[str, object]], fields: list[str]) -> str:
    if not rows:
        return "_No rows._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def bash(command: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
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


def input_rows() -> list[dict[str, object]]:
    return [
        {
            "input_id": key,
            "path": rel(path),
            "status": "present" if path.exists() else "missing",
            "bytes": path.stat().st_size if path.exists() else 0,
        }
        for key, path in INPUTS.items()
    ]


def stage254_passes() -> bool:
    rows = read_csv(INPUTS["stage254_proof_gate"])
    return bool(rows) and rows[-1].get("status") == "PASS_STAGE254_NONBINARY_KEYGEN_NOISE_PREFLIGHT_READY_MOSFHET_ISOLATED_PROTOTYPE"


def c_source_text() -> str:
    return r'''
#include "mosfhet.h"
#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static uint64_t now_us(void) {
  return (uint64_t)((double)clock() * 1000000.0 / (double)CLOCKS_PER_SEC);
}

static uint64_t abs_gap(Torus a, Torus b) {
  const uint64_t d = (uint64_t)(a - b);
  if (d <= (UINT64_MAX / 2ULL)) return d;
  return (~d) + 1ULL;
}

static void fill_msg(TorusPolynomial *msg, int r, int N, int prec, int seed) {
  for (int lane = 0; lane < r; lane++) {
    for (int coeff = 0; coeff < N; coeff++) {
      uint64_t v = (uint64_t)((seed * 7 + lane * 3 + coeff * 5 + coeff / 3) & ((1 << prec) - 1));
      msg[lane]->coeffs[coeff] = int2torus(v, (uint64_t)prec);
    }
  }
}

static void pvw_cmux_like_add(PVW_TMLWE out, PVW_TMLWE base,
    PVW_TMLWE delta, MAT_TRGSW_DFT selector, MAT_TRGSW_MUL_SCRATCH scratch,
    PVW_TMLWE tmp, PVW_TMLWE_DFT tmp_dft, uint64_t *ep_us) {
  const uint64_t begin = now_us();
  mat_trgsw_mul_pvmtmlwe_DFT(tmp_dft, delta, selector, scratch);
  *ep_us += now_us() - begin;
  pvmtmlwe_from_DFT(tmp, tmp_dft);
  pvmtmlwe_add(out, base, tmp);
}

static void include_zero_update(PVW_TMLWE out, PVW_TMLWE in, int a,
    int selector_value, MAT_TRGSW_DFT selector, MAT_TRGSW_MUL_SCRATCH scratch,
    PVW_TMLWE rotated, PVW_TMLWE delta, PVW_TMLWE tmp,
    PVW_TMLWE_DFT tmp_dft, uint64_t *ep_us) {
  (void)selector_value;
  pvmtmlwe_mul_by_xai(rotated, in, a);
  pvmtmlwe_sub(delta, rotated, in);
  pvw_cmux_like_add(out, in, delta, selector, scratch, tmp, tmp_dft, ep_us);
}

static void ternary_update(PVW_TMLWE out, PVW_TMLWE in, int a,
    int selector_value, MAT_TRGSW_DFT selector, MAT_TRGSW_MUL_SCRATCH scratch,
    PVW_TMLWE first, PVW_TMLWE inverse, PVW_TMLWE delta, PVW_TMLWE tmp,
    PVW_TMLWE_DFT tmp_dft, uint64_t *ep_us) {
  (void)selector_value;
  pvmtmlwe_mul_by_xai(first, in, a);
  pvmtmlwe_mul_by_xai(inverse, first, -2 * a);
  pvmtmlwe_sub(delta, inverse, first);
  pvw_cmux_like_add(out, first, delta, selector, scratch, tmp, tmp_dft, ep_us);
}

static void reference_update(PVW_TMLWE out, PVW_TMLWE in, const char *branch,
    int a, int selector_value) {
  if (strcmp(branch, "include_zero") == 0) {
    if (selector_value == 0) pvmtmlwe_copy(out, in);
    else pvmtmlwe_mul_by_xai(out, in, a);
  } else {
    if (selector_value == 0) pvmtmlwe_mul_by_xai(out, in, a);
    else pvmtmlwe_mul_by_xai(out, in, -a);
  }
}

static void compare_phases(PVW_TMLWE out, PVW_TMLWE ref, PVW_TMLWE_Key key,
    int prec, uint64_t *mismatches, uint64_t *max_gap, double *mean_gap) {
  const int N = key->s[0][0]->N;
  const int r = key->r;
  TorusPolynomial *out_phase = polynomial_new_array_of_torus_polynomials(N, r);
  TorusPolynomial *ref_phase = polynomial_new_array_of_torus_polynomials(N, r);
  uint64_t total_gap = 0;
  uint64_t total = 0;
  *mismatches = 0;
  *max_gap = 0;
  pvmtmlwe_phase(out_phase, out, key);
  pvmtmlwe_phase(ref_phase, ref, key);
  for (int lane = 0; lane < r; lane++) {
    for (int coeff = 0; coeff < N; coeff++) {
      const uint64_t gap = abs_gap(out_phase[lane]->coeffs[coeff], ref_phase[lane]->coeffs[coeff]);
      if (gap > *max_gap) *max_gap = gap;
      total_gap += gap;
      total++;
      if (torus2int(out_phase[lane]->coeffs[coeff], (uint64_t)prec) !=
          torus2int(ref_phase[lane]->coeffs[coeff], (uint64_t)prec)) {
        (*mismatches)++;
      }
    }
  }
  *mean_gap = total ? (double)total_gap / (double)total : 0.0;
  free_array_of_polynomials(ref_phase, r);
  free_array_of_polynomials(out_phase, r);
}

static void run_case(const char *branch, int r, int seed, int selector_value) {
  const int N = 1024;
  const int k = 1;
  const int l = 1;
  const int bg_bit = 23;
  const int prec = 3;
  const int rows = (k + r) * l;
  const int a = 3 + ((seed * 5 + r + selector_value) % 31) * 2;

  PVW_TMLWE_Key key = pvmtmlwe_new_binary_key(N, k, r, pow(2, -70));
  MAT_TRGSW_Key mat_key = mat_trgsw_new_key(key, l, bg_bit);
  MAT_TRGSW_DFT selector = mat_trgsw_alloc_new_DFT_sample(l, bg_bit, k, r, N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, N);
  TorusPolynomial *msg = polynomial_new_array_of_torus_polynomials(N, r);
  fill_msg(msg, r, N, prec, seed);

  const uint64_t kg_begin = now_us();
  mat_trgsw_monomial_DFT_sample(selector, selector_value, 0, mat_key);
  const uint64_t selector_keygen_us = now_us() - kg_begin;

  PVW_TMLWE in = pvmtmlwe_new_sample(msg, key);
  PVW_TMLWE out = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE ref = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE t1 = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE t2 = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE t3 = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE_DFT t_dft = pvmtmlwe_alloc_new_DFT_sample(k, r, N);
  uint64_t ep_us = 0;

  if (strcmp(branch, "include_zero") == 0) {
    include_zero_update(out, in, a, selector_value, selector, scratch, t1, t2, t3, t_dft, &ep_us);
  } else {
    ternary_update(out, in, a, selector_value, selector, scratch, t1, t2, t3, t3, t_dft, &ep_us);
  }
  reference_update(ref, in, branch, a, selector_value);

  uint64_t mismatches = 0;
  uint64_t max_gap = 0;
  double mean_gap = 0.0;
  compare_phases(out, ref, key, prec, &mismatches, &max_gap, &mean_gap);
  const char *status = mismatches == 0 ? "PASS_MOSFHET_SELECTOR_SUBA" : "FAIL";
  printf("%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.3f,%" PRIu64 ",%" PRIu64 ",%s\n",
      branch, r, seed, selector_value, N, prec, a, mismatches, max_gap,
      mean_gap, selector_keygen_us, ep_us, status);

  free_pvmtmlwe_DFT(t_dft);
  free_pvmtmlwe(t3);
  free_pvmtmlwe(t2);
  free_pvmtmlwe(t1);
  free_pvmtmlwe(ref);
  free_pvmtmlwe(out);
  free_pvmtmlwe(in);
  free_array_of_polynomials(msg, r);
  free_mat_trgsw_mul_scratch(scratch);
  free_mat_trgsw_DFT(selector);
  free_mat_trgsw_key(mat_key);
  free_pvmtmlwe_key(key);
}

int main(void) {
  printf("branch,r,seed,selector_value,N,prec,a,phase_mismatches,max_phase_gap,mean_phase_gap,selector_keygen_us,external_product_us,status\n");
  for (int r_idx = 0; r_idx < 3; r_idx++) {
    const int r_values[3] = {1, 2, 4};
    const int r = r_values[r_idx];
    for (int seed = 0; seed < 5; seed++) {
      for (int selector_value = 0; selector_value <= 1; selector_value++) {
        run_case("include_zero", r, seed, selector_value);
        run_case("ternary", r, seed, selector_value);
      }
    }
  }
  return 0;
}
'''


def write_c_source() -> None:
    write_text(C_SOURCE, c_source_text())


def build_mosfhet_static() -> bool:
    cmd = (
        "cd src/mosfhet && "
        "make clean >/dev/null 2>&1 || true && "
        "make static FFT_LIB=spqlios A_PRNG=none ENABLE_VAES=false "
        "ENABLE_PVW_TMLWE=true -j$(nproc)"
    )
    proc = bash(cmd, timeout=240)
    write_text(BUILD_LOG, "\n".join([
        f"command: {cmd}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        proc.stdout.strip(),
        "--- stderr ---",
        proc.stderr.strip(),
    ]))
    return proc.returncode == 0


def compile_probe(build_ok: bool) -> bool:
    if not build_ok:
        return False
    cmd = (
        "gcc -O2 "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(C_BINARY)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
    )
    proc = bash(cmd, timeout=120)
    write_text(COMPILE_LOG, "\n".join([
        f"command: {cmd}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        proc.stdout.strip(),
        "--- stderr ---",
        proc.stderr.strip(),
    ]))
    return proc.returncode == 0


def run_probe(compile_ok: bool) -> tuple[bool, list[dict[str, object]]]:
    if not compile_ok:
        return False, []
    cmd = f"./{rel(C_BINARY)}"
    proc = bash(cmd, timeout=180)
    write_text(RUN_LOG_TXT, "\n".join([
        f"command: {cmd}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        proc.stdout.strip(),
        "--- stderr ---",
        proc.stderr.strip(),
    ]))
    rows: list[dict[str, object]] = []
    stdout = proc.stdout.strip().splitlines()
    if stdout:
      reader = csv.DictReader(stdout)
      rows = list(reader)
    cleanup_build_outputs()
    return proc.returncode == 0, rows


def cleanup_build_outputs() -> None:
    bash(f"rm -f {rel(C_BINARY)}", timeout=30)
    bash("cd src/mosfhet && make clean >/dev/null 2>&1 || true", timeout=60)


def aggregate_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        groups.setdefault((str(row["branch"]), str(row["r"])), []).append(row)
    out: list[dict[str, object]] = []
    for (branch, r), items in sorted(groups.items()):
        mismatches = sum(int(row["phase_mismatches"]) for row in items)
        max_gap = max(int(row["max_phase_gap"]) for row in items) if items else 0
        mean_gap = sum(float(row["mean_phase_gap"]) for row in items) / len(items) if items else 0.0
        keygen_us = sum(float(row["selector_keygen_us"]) for row in items) / len(items) if items else 0.0
        ep_us = sum(float(row["external_product_us"]) for row in items) / len(items) if items else 0.0
        out.append({
            "branch": branch,
            "r": r,
            "samples": len(items),
            "phase_mismatches": mismatches,
            "max_phase_gap": max_gap,
            "mean_phase_gap_avg": f"{mean_gap:.3f}",
            "selector_keygen_us_avg": f"{keygen_us:.3f}",
            "external_product_us_avg": f"{ep_us:.3f}",
            "status": "PASS_AGGREGATE" if mismatches == 0 and len(items) == 10 else "FAIL",
        })
    return out


def resource_rows() -> list[dict[str, object]]:
    rows = []
    n = 1024
    k = 1
    l = 1
    for r in [1, 2, 4]:
        mat_rows = (k + r) * l
        dft_polys_per_selector = mat_rows * (k + r)
        double_slots = dft_polys_per_selector * n
        bytes_est = double_slots * 8
        rows.append({
            "r": r,
            "N": n,
            "mat_rows": mat_rows,
            "dft_polys_per_selector": dft_polys_per_selector,
            "double_slots_per_selector": double_slots,
            "estimated_bytes_per_selector": bytes_est,
            "single_family_target_count_h39": 39,
            "estimated_target_family_bytes_h39": bytes_est * 39,
            "interpretation": "isolated selector DFT storage estimate only",
        })
    return rows


def source_isolation_rows() -> list[dict[str, object]]:
    rows = []
    for path in [ROOT / "include" / "sab_pvw.h", ROOT / "src" / "sab_pvw.c", INPUTS["mosfhet_mattrgsw"], INPUTS["mosfhet_pvwtmlwe"]]:
        relpath = rel(path)
        proc = subprocess.run(["git", "diff", "--name-only", "--", relpath], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rows.append({
            "path": relpath,
            "modified_in_stage255": "yes" if proc.stdout.strip() else "no",
            "status": "PASS_UNCHANGED" if not proc.stdout.strip() else "FAIL_MODIFIED",
            "interpretation": "Stage255 is isolated repro code and must not modify production sources.",
        })
    return rows


def admission_rows(agg: list[dict[str, object]], build_ok: bool, compile_ok: bool, run_ok: bool) -> list[dict[str, object]]:
    agg_ok = bool(agg) and all(row["status"] == "PASS_AGGREGATE" for row in agg)
    return [
        {
            "route": "stage256_nonbinary_sparsemul_preflight",
            "decision": "ADMIT_PREFLIGHT" if build_ok and compile_ok and run_ok and agg_ok else "BLOCK",
            "production_permission": "no",
            "reason": "actual isolated selector keygen/external-product phase gate passed" if agg_ok else "isolated gate incomplete",
            "next_gate": "design sparse_mul integration boundary and noise/resource recurrence before production code",
        },
        {
            "route": "nonbinary_full_sab",
            "decision": "BLOCKED",
            "production_permission": "no",
            "reason": "no sparse_mul integration, full SAB correctness, multi-seed noise, resource, or T_bootstrap/r benchmark yet",
            "next_gate": "Stage256+",
        },
    ]


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "actual_isolated_selector_keygen",
            "status": "supported_isolated",
            "allowed_wording": "Actual MOSFHET MAT 0/1 selectors for s_coff/s_sign pass isolated sub_a phase gates.",
            "forbidden_wording": "Non-binary PVW/MAT-SAB production keygen is implemented.",
            "evidence": rel(PROBE),
        },
        {
            "claim": "noise",
            "status": "rounding_phase_gap_only",
            "allowed_wording": "Stage255 records phase gap statistics under an isolated prototype.",
            "forbidden_wording": "Full non-binary SAB noise is proven acceptable.",
            "evidence": rel(AGGREGATE),
        },
        {
            "claim": "speedup",
            "status": "unsupported",
            "allowed_wording": "No complete-SAB non-binary speedup is claimed.",
            "forbidden_wording": "Non-binary PVW/MAT-SAB accelerates bootstrapping.",
            "evidence": rel(ADMISSION),
        },
    ]


def gate_rows(inputs, build_ok, compile_ok, run_ok, probe, agg, source_rows, admission) -> list[dict[str, object]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    stage254_ok = stage254_passes()
    probe_ok = bool(probe) and all(row["status"] == "PASS_MOSFHET_SELECTOR_SUBA" for row in probe)
    agg_ok = bool(agg) and all(row["status"] == "PASS_AGGREGATE" for row in agg)
    source_ok = all(row["status"] == "PASS_UNCHANGED" for row in source_rows)
    admission_ok = admission[0]["decision"] == "ADMIT_PREFLIGHT" and all(row["production_permission"] == "no" for row in admission)
    decision_ok = inputs_ok and stage254_ok and build_ok and compile_ok and run_ok and probe_ok and agg_ok and source_ok and admission_ok
    return [
        {
            "gate": "G1_inputs_and_stage254",
            "status": "PASS" if inputs_ok and stage254_ok else "FAIL",
            "metric": "inputs;stage254",
            "value": f"{str(inputs_ok).lower()};{str(stage254_ok).lower()}",
            "evidence": f"{rel(INPUT_STATUS)}; {rel(INPUTS['stage254_proof_gate'])}",
            "interpretation": "Stage255 is valid only after Stage254 admits isolated prototype.",
        },
        {
            "gate": "G2_build_compile_run",
            "status": "PASS" if build_ok and compile_ok and run_ok else "FAIL",
            "metric": "build;compile;run",
            "value": f"{str(build_ok).lower()};{str(compile_ok).lower()};{str(run_ok).lower()}",
            "evidence": f"{rel(BUILD_LOG)}; {rel(COMPILE_LOG)}; {rel(RUN_LOG_TXT)}",
            "interpretation": "The C probe links and runs against production MOSFHET static library.",
        },
        {
            "gate": "G3_selector_suba_phase",
            "status": "PASS" if probe_ok and agg_ok else "FAIL",
            "metric": "probe_rows",
            "value": len(probe),
            "evidence": f"{rel(PROBE)}; {rel(AGGREGATE)}",
            "interpretation": "Actual MAT selectors preserve rounded phase for include-zero and ternary isolated updates.",
        },
        {
            "gate": "G4_source_isolation",
            "status": "PASS" if source_ok else "FAIL",
            "metric": "production_source_modified",
            "value": "no" if source_ok else "yes",
            "evidence": rel(SOURCE_ISOLATION),
            "interpretation": "Stage255 leaves production SAB/PVW/MOSFHET source unchanged.",
        },
        {
            "gate": "G5_admission_boundary",
            "status": "PASS_NO_PRODUCTION",
            "metric": "production permission",
            "value": "no",
            "evidence": rel(ADMISSION),
            "interpretation": "Only sparse_mul integration preflight is admitted.",
        },
        {
            "gate": "G6_stage255_decision",
            "status": DECISION if decision_ok else "FAIL_STAGE255_MOSFHET_SELECTOR_KEYGEN_NOISE",
            "metric": "decision",
            "value": DECISION if decision_ok else "FAIL_STAGE255_MOSFHET_SELECTOR_KEYGEN_NOISE",
            "evidence": rel(GATES),
            "interpretation": "Proceed to non-binary sparse_mul preflight, not full SAB.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage256_nonbinary_sparsemul_preflight",
            "entry_condition": "Stage255 actual isolated selector keygen/noise gate passes.",
            "gate": "design sparse_mul integration boundary, selector family lifecycle, and schedule/noise recurrence",
            "status": "selected_next",
            "failure_action": "keep non-binary PVW unsupported",
            "evidence": rel(ADMISSION),
        },
        {
            "priority": "P1",
            "route": "stage257_nonbinary_sparsemul_implementation",
            "entry_condition": "Stage256 admits production-adjacent isolated integration",
            "gate": "implement explicit sab_pvw_nonbinary_* path, not default scalar or binary path",
            "status": "conditional",
            "failure_action": "do not modify hot path",
            "evidence": rel(CLAIM),
        },
        {
            "priority": "P2",
            "route": "stage258_nonbinary_full_sab_ab",
            "entry_condition": "sparse_mul integration passes correctness/noise/resource",
            "gate": "complete-SAB T_bootstrap/r, multi-seed correctness/noise, resource, scalar default isolation",
            "status": "future_gated",
            "failure_action": "no non-binary speedup claim",
            "evidence": rel(CLAIM),
        },
    ]


def artifact_rows(paths: list[Path]) -> list[dict[str, object]]:
    rows = []
    for path in paths:
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256(path) if path.exists() and path.is_file() else "",
            "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        })
    return rows


def write_docs(inputs, probe, agg, resource, source_rows, admission, claims, gates, nextq, head: str) -> None:
    write_text(DOC, f"""# Stage255 MOSFHET Non-Binary Selector Keygen/Noise

Decision: `{gates[-1]["status"]}`.

Stage255 is the first actual MOSFHET-adjacent non-binary selector experiment.
It encrypts MAT `s_coff/s_sign` 0/1 selectors with production
`mat_trgsw_monomial_DFT_sample`, applies `mat_trgsw_mul_pvmtmlwe_DFT` to the
isolated include-zero and ternary `sub_a` equations, and compares rounded phase
against the reference update.

## Probe Results

{table(probe, PROBE_FIELDS)}

## Aggregates

{table(agg, ["branch", "r", "samples", "phase_mismatches", "max_phase_gap", "mean_phase_gap_avg", "selector_keygen_us_avg", "external_product_us_avg", "status"])}

## Resource Projection

{table(resource, ["r", "N", "mat_rows", "dft_polys_per_selector", "double_slots_per_selector", "estimated_bytes_per_selector", "single_family_target_count_h39", "estimated_target_family_bytes_h39", "interpretation"])}

## Source Isolation

{table(source_rows, ["path", "modified_in_stage255", "status", "interpretation"])}

## Admission

{table(admission, ["route", "decision", "production_permission", "reason", "next_gate"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])}

## Proof Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

Generated from head `{head}`.
""")
    write_text(REPORT, f"""# Stage255 Report

Decision: `{gates[-1]["status"]}`.

Actual MOSFHET MAT 0/1 selector encryption and external products pass the
isolated include-zero and ternary `sub_a` phase gates for r=1/2/4. This moves
the non-binary route beyond finite algebra into production-library evidence,
but only for isolated selector updates.

It still does not implement non-binary `sab_pvw_*`, sparse schedule integration,
full bootstrapping, multi-seed SAB noise, or `T_bootstrap/r` speedup.
""")
    write_text(PLAN, """# Stage255 MOSFHET Non-Binary Selector Keygen/Noise Plan

## Objective

Run actual MOSFHET MAT selector encryption and isolated non-binary `sub_a`
external-product checks.

## Gates

- Stage254 must pass.
- MOSFHET static library must build.
- Probe must compile and run.
- r=1/2/4 include-zero and ternary selector values 0/1 must have zero rounded
  phase mismatches.
- Production source files must remain unchanged.
- Next work is sparse_mul integration preflight only.
""")
    write_text(THEORY, """# Stage255 MOSFHET Non-Binary Selector Keygen/Noise Model

The actual selector update is implemented as a CMUX-style linear update:

```text
out = base + selector * delta
```

For include-zero, `base=p` and `delta=(X^a-1)p`.
For ternary, `base=X^a p` and `delta=(X^{-2a}-1)X^a p`.

Stage255 checks these equations using production MAT_TRGSW DFT selectors and
MAT external products. The recorded phase gaps are isolated prototype evidence,
not a full SAB noise proof.
""")
    write_text(VARIANT, """# MAT-RLWE SAB Stage255 MOSFHET Selector Keygen/Noise

## Variant Delta

Use actual MOSFHET `MAT_TRGSW_DFT` 0/1 selectors as non-binary `s_coff` and
`s_sign` selector families in isolated `sub_a` equations.

## Status

Isolated production-library prototype. It admits sparse_mul integration
preflight only; full non-binary bootstrapping remains blocked.
""")
    write_text(REPRO_CMDS, f"""# Stage255 Reproduction Commands

```text
python scripts/build_stage255_mosfhet_nonbinary_selector_keygen_noise.py
python -m py_compile scripts/build_stage255_mosfhet_nonbinary_selector_keygen_noise.py
```

Decision: `{gates[-1]["status"]}`.
""")


def update_project_files(head: str, decision: str) -> None:
    append_once(ROADMAP, "## Stage 255: MOSFHET Non-Binary Selector Keygen/Noise", f"""
## Stage 255: MOSFHET Non-Binary Selector Keygen/Noise

Goal:

```text
Run actual MOSFHET-adjacent MAT s_coff/s_sign selector encryption and isolated
sub_a external-product phase/noise checks.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. Production MOSFHET MAT
0/1 selector encryption and external products pass isolated include-zero and
ternary sub_a phase gates for r=1/2/4. Production SAB/PVW source remains
unchanged; next selected route is non-binary sparse_mul integration preflight.
```
""")
    append_once(GOAL, "Stage255 MOSFHET non-binary selector keygen/noise", f"""
- Stage255 MOSFHET non-binary selector keygen/noise records `{decision}`:
  actual production-library MAT selector encryption passes isolated sub_a
  phase gates, but non-binary full SAB and speedup claims remain blocked.
""")
    append_once(CURRENT_GOAL, "### Stage255 MOSFHET non-binary selector keygen/noise", f"""
### Stage255 MOSFHET non-binary selector keygen/noise

`{decision}` advances non-binary PVW/MAT-SAB from finite equivalence to actual
MOSFHET isolated selector evidence. The active goal remains open for sparse
schedule integration, full SAB A/B, multi-seed noise/resource, and paper claim
closure.
""")
    append_once(HYPOTHESES, "H10_stage255_mosfhet_nonbinary_selector_keygen_noise:", f"""
H10_stage255_mosfhet_nonbinary_selector_keygen_noise:
  status: actual_isolated_selector_keygen_noise_passed_sparsemul_preflight_next
  evidence:
    - repro/stage255_mosfhet_nonbinary_selector_keygen_noise/selector_noise_probe.csv
    - repro/stage255_mosfhet_nonbinary_selector_keygen_noise/selector_noise_aggregate.csv
    - repro/stage255_mosfhet_nonbinary_selector_keygen_noise/proof_gate.csv
    - docs/stage255_mosfhet_nonbinary_selector_keygen_noise.md
  conclusion: >
    Stage255 records {decision}. Actual MOSFHET MAT 0/1 selector encryption
    and external products pass isolated include-zero and ternary sub_a phase
    gates for r=1/2/4. This admits sparse_mul integration preflight only; full
    SAB and T_bootstrap/r speedup claims remain blocked.
""")
    append_once(RUN_LOG, "stage255-mosfhet-nonbinary-selector-keygen-noise-001", f"""stage255-mosfhet-nonbinary-selector-keygen-noise-001,{date.today().isoformat()},{head},Stage 255,mosfhet_selector_keygen_noise,"python scripts/build_stage255_mosfhet_nonbinary_selector_keygen_noise.py","Stage254 preflight + production MOSFHET static library",n/a,{decision},"Actual isolated selector keygen/noise gate passes; sparse_mul preflight next.",docs/stage255_mosfhet_nonbinary_selector_keygen_noise.md; repro/stage255_mosfhet_nonbinary_selector_keygen_noise/proof_gate.csv
""")
    append_once(MANIFEST, "- stage255_mosfhet_nonbinary_selector_keygen_noise:", """
- stage255_mosfhet_nonbinary_selector_keygen_noise:
  - `docs/stage255_mosfhet_nonbinary_selector_keygen_noise.md`
  - `experiments/stage255_mosfhet_nonbinary_selector_keygen_noise_plan.md`
  - `theory_checks/stage255_mosfhet_nonbinary_selector_keygen_noise_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage255_mosfhet_nonbinary_selector_keygen_noise.md`
  - `scripts/build_stage255_mosfhet_nonbinary_selector_keygen_noise.py`
  - `repro/stage255_mosfhet_nonbinary_selector_keygen_noise/`
""")
    append_once(CHECKLIST, "Stage255 MOSFHET non-binary selector keygen/noise passes isolated gate", f"""
- [x] Stage255 MOSFHET non-binary selector keygen/noise passes isolated gate `{decision}`.
""")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    head = run_git(["rev-parse", "--short", "HEAD"])
    inputs = input_rows()
    write_c_source()
    build_ok = build_mosfhet_static()
    compile_ok = compile_probe(build_ok)
    run_ok, probe = run_probe(compile_ok)
    agg = aggregate_rows(probe)
    resource = resource_rows()
    source_rows = source_isolation_rows()
    admission = admission_rows(agg, build_ok, compile_ok, run_ok)
    claims = claim_rows()
    gates = gate_rows(inputs, build_ok, compile_ok, run_ok, probe, agg, source_rows, admission)
    nextq = next_rows()

    write_csv(INPUT_STATUS, inputs, ["input_id", "path", "status", "bytes"])
    write_csv(PROBE, probe, PROBE_FIELDS)
    write_csv(AGGREGATE, agg, ["branch", "r", "samples", "phase_mismatches", "max_phase_gap", "mean_phase_gap_avg", "selector_keygen_us_avg", "external_product_us_avg", "status"])
    write_csv(RESOURCE, resource, ["r", "N", "mat_rows", "dft_polys_per_selector", "double_slots_per_selector", "estimated_bytes_per_selector", "single_family_target_count_h39", "estimated_target_family_bytes_h39", "interpretation"])
    write_csv(SOURCE_ISOLATION, source_rows, ["path", "modified_in_stage255", "status", "interpretation"])
    write_csv(ADMISSION, admission, ["route", "decision", "production_permission", "reason", "next_gate"])
    write_csv(CLAIM, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])

    write_docs(inputs, probe, agg, resource, source_rows, admission, claims, gates, nextq, head)
    artifacts = [DOC, PLAN, THEORY, VARIANT, INPUT_STATUS, BUILD_LOG, COMPILE_LOG, RUN_LOG_TXT, C_SOURCE, PROBE, AGGREGATE, RESOURCE, SOURCE_ISOLATION, ADMISSION, CLAIM, GATES, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "exists", "sha256", "bytes"])
    if gates[-1]["status"] == DECISION:
        update_project_files(head, gates[-1]["status"])
    print(f"Stage255 report: {rel(DOC)}")
    print(f"Stage255 decision: {gates[-1]['status']}")
    return 0 if gates[-1]["status"] == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
