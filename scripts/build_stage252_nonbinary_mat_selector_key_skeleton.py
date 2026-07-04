"""Stage252: non-binary MAT selector/key skeleton.

This stage follows Stage251 by defining a non-production PVW/MAT selector key
skeleton for ternary/include-zero branches.  It compiles and runs an isolated C
probe for selector-family layout and API guards, but it does not modify
production sab_pvw headers or hot paths.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage252_nonbinary_mat_selector_key_skeleton"

INPUTS = {
    "stage251_proof_gate": ROOT / "repro" / "stage251_nonbinary_selector_semantics" / "proof_gate.csv",
    "stage251_semantic_equations": ROOT / "repro" / "stage251_nonbinary_selector_semantics" / "semantic_equation_matrix.csv",
    "stage251_selector_gaps": ROOT / "repro" / "stage251_nonbinary_selector_semantics" / "selector_gap_matrix.csv",
    "stage251_admission": ROOT / "repro" / "stage251_nonbinary_selector_semantics" / "admission_decision.csv",
    "sab_header": ROOT / "include" / "sab.h",
    "sab_pvw_header": ROOT / "include" / "sab_pvw.h",
    "scalar_sab_source": ROOT / "src" / "sparse_amortized_bootstrap.c",
    "pvw_sab_source": ROOT / "src" / "sab_pvw.c",
    "mosfhet_header": ROOT / "src" / "mosfhet" / "include" / "mosfhet.h",
}

DOC = ROOT / "docs" / "stage252_nonbinary_mat_selector_key_skeleton.md"
PLAN = ROOT / "experiments" / "stage252_nonbinary_mat_selector_key_skeleton_plan.md"
THEORY = ROOT / "theory_checks" / "stage252_nonbinary_mat_selector_key_skeleton_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage252_nonbinary_mat_selector_key_skeleton.md"

INPUT_STATUS = OUT / "input_status.csv"
DESIGN = OUT / "skeleton_design_matrix.csv"
LAYOUT = OUT / "key_layout_projection.csv"
API_CONTRACT = OUT / "api_contract_matrix.csv"
PROBE = OUT / "toy_key_object_probe.csv"
COMPILE_LOG = OUT / "compile_probe.log"
RUN_LOG_TXT = OUT / "run_probe.log"
C_SOURCE = OUT / "stage252_nonbinary_selector_key_skeleton.c"
C_BINARY = OUT / "stage252_nonbinary_selector_key_skeleton.exe"
SOURCE_ISOLATION = OUT / "source_isolation.csv"
ADMISSION = OUT / "admission_decision.csv"
CLAIM = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage252_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE252_NONBINARY_MAT_SELECTOR_KEY_SKELETON_READY_ISOLATED_EQUIVALENCE"

PROBE_FIELDS = [
    "case",
    "r",
    "h",
    "r_prec",
    "include_zero",
    "ternary",
    "distance_count",
    "coff_count",
    "sign_count",
    "total_count",
    "expected_total",
    "role_mismatches",
    "guard_failures",
    "hot_alloc_delta",
    "status",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return proc.stdout.strip()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip() + "\n")


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


def stage251_passes() -> bool:
    rows = read_csv(INPUTS["stage251_proof_gate"])
    return bool(rows) and rows[-1].get("status") == "PASS_STAGE251_NONBINARY_SELECTOR_SEMANTICS_PREFLIGHT_BLOCKS_IMPLEMENTATION"


def design_rows() -> list[dict[str, object]]:
    return [
        {
            "component": "distance_bits",
            "selector_family": "s",
            "role": "binary sparse distance bits shared across r body lanes",
            "count_per_key": "(h + 1) * r_prec",
            "mat_object": "MAT_TRGSW_DFT",
            "source_delta": "matches current SAB_PVW_Key::s",
            "production_status": "existing_binary_only",
        },
        {
            "component": "include_zero_presence",
            "selector_family": "s_coff",
            "role": "presence selector c in {0,1}: p + c((X^a - 1)p)",
            "count_per_key": "h if include_zero",
            "mat_object": "MAT_TRGSW_DFT",
            "source_delta": "new non-production skeleton family",
            "production_status": "not_implemented",
        },
        {
            "component": "ternary_sign",
            "selector_family": "s_sign",
            "role": "sign selector s in {0,1}: choose X^a or X^-a",
            "count_per_key": "h if ternary",
            "mat_object": "MAT_TRGSW_DFT",
            "source_delta": "new non-production skeleton family",
            "production_status": "not_implemented",
        },
        {
            "component": "selector_api_boundary",
            "selector_family": "stage252_key",
            "role": "own optional selector families without changing SAB_PVW_Key",
            "count_per_key": "distance + optional s_coff + optional s_sign",
            "mat_object": "metadata-only C skeleton in repro",
            "source_delta": "no production header/source edit",
            "production_status": "isolated_preflight_only",
        },
    ]


def layout_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    params = [
        ("target_SET_2_3_2048", 39, 7),
        ("added_SET_4_5_2048", 42, 7),
        ("added_SET_2_3_4096", 32, 8),
    ]
    for name, h, r_prec in params:
        base = (h + 1) * r_prec
        for branch, include_zero, ternary in [
            ("binary", 0, 0),
            ("include_zero", 1, 0),
            ("ternary", 0, 1),
            ("include_zero_plus_ternary_stress", 1, 1),
        ]:
            extra = h * include_zero + h * ternary
            rows.append({
                "param": name,
                "branch": branch,
                "h": h,
                "r_prec": r_prec,
                "distance_count": base,
                "coff_count": h if include_zero else 0,
                "sign_count": h if ternary else 0,
                "total_selector_objects": base + extra,
                "count_ratio_vs_binary": f"{(base + extra) / base:.6f}",
                "interpretation": "selector-object count only; not byte, noise, or speed evidence",
            })
    return rows


def api_contract_rows() -> list[dict[str, object]]:
    return [
        {
            "api": "stage252_key_alloc",
            "inputs": "r, h, r_prec, include_zero, ternary",
            "positive_contract": "allocates distance bits plus requested optional selector families",
            "negative_contract": "rejects r<=0, h<=0, r_prec<=0",
            "hot_path_status": "non_production",
        },
        {
            "api": "stage252_selector_at",
            "inputs": "family, step, bit",
            "positive_contract": "returns distance/coff/sign selector metadata in range",
            "negative_contract": "rejects missing family and out-of-range indices",
            "hot_path_status": "non_production",
        },
        {
            "api": "stage252_hot_scan",
            "inputs": "key object",
            "positive_contract": "counts selector families without allocation",
            "negative_contract": "detects role/count mismatches",
            "hot_path_status": "no hot allocation in probe",
        },
        {
            "api": "stage253_entry_requirement",
            "inputs": "skeleton plus scalar equation target",
            "positive_contract": "may proceed to isolated sub_a equivalence only",
            "negative_contract": "does not authorize full SAB or production keygen",
            "hot_path_status": "blocked",
        },
    ]


def c_source_text() -> str:
    return r'''
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

typedef enum {
  STAGE252_FAMILY_DISTANCE = 1,
  STAGE252_FAMILY_COFF = 2,
  STAGE252_FAMILY_SIGN = 3
} Stage252Family;

typedef struct {
  int family;
  int step;
  int bit;
  int role;
} Stage252SelectorSlot;

typedef struct {
  int r;
  int h;
  int r_prec;
  int include_zero;
  int ternary;
  int distance_count;
  int coff_count;
  int sign_count;
  int total_count;
  Stage252SelectorSlot *distance;
  Stage252SelectorSlot *coff;
  Stage252SelectorSlot *sign;
} Stage252Key;

static uint64_t stage252_alloc_counter = 0;

static void *stage252_malloc(size_t bytes) {
  stage252_alloc_counter++;
  return calloc(1, bytes);
}

static void stage252_free(Stage252Key *key) {
  if (key == NULL) return;
  free(key->distance);
  free(key->coff);
  free(key->sign);
  free(key);
}

static Stage252Key *stage252_key_alloc(int r, int h, int r_prec, int include_zero, int ternary) {
  if (r <= 0 || h <= 0 || r_prec <= 0) return NULL;
  Stage252Key *key = (Stage252Key *)stage252_malloc(sizeof(*key));
  key->r = r;
  key->h = h;
  key->r_prec = r_prec;
  key->include_zero = include_zero ? 1 : 0;
  key->ternary = ternary ? 1 : 0;
  key->distance_count = (h + 1) * r_prec;
  key->coff_count = include_zero ? h : 0;
  key->sign_count = ternary ? h : 0;
  key->total_count = key->distance_count + key->coff_count + key->sign_count;
  key->distance = (Stage252SelectorSlot *)stage252_malloc(sizeof(Stage252SelectorSlot) * (size_t)key->distance_count);
  key->coff = key->coff_count ? (Stage252SelectorSlot *)stage252_malloc(sizeof(Stage252SelectorSlot) * (size_t)key->coff_count) : NULL;
  key->sign = key->sign_count ? (Stage252SelectorSlot *)stage252_malloc(sizeof(Stage252SelectorSlot) * (size_t)key->sign_count) : NULL;
  for (int step = 0; step < h + 1; step++) {
    for (int bit = 0; bit < r_prec; bit++) {
      int idx = step * r_prec + bit;
      key->distance[idx] = (Stage252SelectorSlot){STAGE252_FAMILY_DISTANCE, step, bit, 1};
    }
  }
  for (int step = 0; step < key->coff_count; step++) {
    key->coff[step] = (Stage252SelectorSlot){STAGE252_FAMILY_COFF, step, -1, 2};
  }
  for (int step = 0; step < key->sign_count; step++) {
    key->sign[step] = (Stage252SelectorSlot){STAGE252_FAMILY_SIGN, step, -1, 3};
  }
  return key;
}

static const Stage252SelectorSlot *stage252_selector_at(const Stage252Key *key, int family, int step, int bit) {
  if (key == NULL) return NULL;
  if (family == STAGE252_FAMILY_DISTANCE) {
    if (step < 0 || step > key->h || bit < 0 || bit >= key->r_prec) return NULL;
    return &key->distance[step * key->r_prec + bit];
  }
  if (family == STAGE252_FAMILY_COFF) {
    if (!key->include_zero || bit != -1 || step < 0 || step >= key->h) return NULL;
    return &key->coff[step];
  }
  if (family == STAGE252_FAMILY_SIGN) {
    if (!key->ternary || bit != -1 || step < 0 || step >= key->h) return NULL;
    return &key->sign[step];
  }
  return NULL;
}

static int stage252_role_mismatches(const Stage252Key *key) {
  int failures = 0;
  for (int step = 0; step < key->h + 1; step++) {
    for (int bit = 0; bit < key->r_prec; bit++) {
      const Stage252SelectorSlot *slot = stage252_selector_at(key, STAGE252_FAMILY_DISTANCE, step, bit);
      if (slot == NULL || slot->family != STAGE252_FAMILY_DISTANCE || slot->step != step || slot->bit != bit) failures++;
    }
  }
  for (int step = 0; step < key->h; step++) {
    const Stage252SelectorSlot *coff = stage252_selector_at(key, STAGE252_FAMILY_COFF, step, -1);
    if (key->include_zero) {
      if (coff == NULL || coff->family != STAGE252_FAMILY_COFF || coff->step != step) failures++;
    } else if (coff != NULL) failures++;
    const Stage252SelectorSlot *sign = stage252_selector_at(key, STAGE252_FAMILY_SIGN, step, -1);
    if (key->ternary) {
      if (sign == NULL || sign->family != STAGE252_FAMILY_SIGN || sign->step != step) failures++;
    } else if (sign != NULL) failures++;
  }
  return failures;
}

static int stage252_guard_failures(const Stage252Key *key) {
  int failures = 0;
  if (stage252_key_alloc(0, key->h, key->r_prec, key->include_zero, key->ternary) != NULL) failures++;
  if (stage252_key_alloc(key->r, 0, key->r_prec, key->include_zero, key->ternary) != NULL) failures++;
  if (stage252_key_alloc(key->r, key->h, 0, key->include_zero, key->ternary) != NULL) failures++;
  if (stage252_selector_at(key, STAGE252_FAMILY_DISTANCE, key->h + 1, 0) != NULL) failures++;
  if (stage252_selector_at(key, STAGE252_FAMILY_DISTANCE, 0, key->r_prec) != NULL) failures++;
  if (stage252_selector_at(key, STAGE252_FAMILY_COFF, key->h, -1) != NULL) failures++;
  if (stage252_selector_at(key, STAGE252_FAMILY_SIGN, key->h, -1) != NULL) failures++;
  if (stage252_selector_at(key, 99, 0, 0) != NULL) failures++;
  return failures;
}

static int stage252_hot_scan(const Stage252Key *key) {
  int total = 0;
  for (int i = 0; i < key->distance_count; i++) total += key->distance[i].role == 1;
  for (int i = 0; i < key->coff_count; i++) total += key->coff[i].role == 2;
  for (int i = 0; i < key->sign_count; i++) total += key->sign[i].role == 3;
  return total;
}

static void run_case(const char *name, int r, int h, int r_prec, int include_zero, int ternary) {
  Stage252Key *key = stage252_key_alloc(r, h, r_prec, include_zero, ternary);
  const int expected_distance = (h + 1) * r_prec;
  const int expected_coff = include_zero ? h : 0;
  const int expected_sign = ternary ? h : 0;
  const int expected_total = expected_distance + expected_coff + expected_sign;
  int role_mismatches = stage252_role_mismatches(key);
  int guard_failures = stage252_guard_failures(key);
  const uint64_t alloc_before = stage252_alloc_counter;
  int hot_total = stage252_hot_scan(key);
  const uint64_t hot_alloc_delta = stage252_alloc_counter - alloc_before;
  if (hot_total != expected_total) role_mismatches++;
  const int count_ok = key->distance_count == expected_distance &&
      key->coff_count == expected_coff &&
      key->sign_count == expected_sign &&
      key->total_count == expected_total;
  const int pass = count_ok && role_mismatches == 0 && guard_failures == 0 && hot_alloc_delta == 0;
  printf("%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%u,%s\n",
      name, r, h, r_prec, include_zero, ternary,
      key->distance_count, key->coff_count, key->sign_count,
      key->total_count, expected_total, role_mismatches, guard_failures,
      (unsigned)hot_alloc_delta,
      pass ? "PASS_STAGE252_KEY_SKELETON" : "FAIL");
  stage252_free(key);
}

int main(void) {
  run_case("binary_target", 4, 39, 7, 0, 0);
  run_case("include_zero_target", 4, 39, 7, 1, 0);
  run_case("ternary_target", 4, 39, 7, 0, 1);
  run_case("include_zero_ternary_stress", 4, 39, 7, 1, 1);
  run_case("include_zero_r2", 2, 39, 7, 1, 0);
  run_case("ternary_r2", 2, 39, 7, 0, 1);
  run_case("added_2048_r4", 4, 42, 7, 1, 1);
  run_case("added_4096_r4", 4, 32, 8, 1, 1);
  return 0;
}
'''


def write_c_source() -> None:
    write_text(C_SOURCE, c_source_text())


def compile_probe() -> bool:
    proc = subprocess.run(
        [
            "gcc",
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-o",
            str(C_BINARY),
            str(C_SOURCE),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    write_text(
        COMPILE_LOG,
        "\n".join(
            [
                "command: gcc -std=c11 -O2 -Wall -Wextra -Werror",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                proc.stdout.strip(),
                "--- stderr ---",
                proc.stderr.strip(),
            ]
        ),
    )
    return proc.returncode == 0


def run_probe(compile_ok: bool) -> tuple[bool, list[dict[str, object]]]:
    if not compile_ok:
        return False, []
    proc = subprocess.run(
        [str(C_BINARY)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    write_text(
        RUN_LOG_TXT,
        "\n".join(
            [
                f"command: {rel(C_BINARY)}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                proc.stdout.strip(),
                "--- stderr ---",
                proc.stderr.strip(),
            ]
        ),
    )
    rows: list[dict[str, object]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        values = line.split(",")
        rows.append(dict(zip(PROBE_FIELDS, values)))
    try:
        C_BINARY.unlink()
    except FileNotFoundError:
        pass
    return proc.returncode == 0, rows


def source_isolation_rows() -> list[dict[str, object]]:
    rows = []
    for path in [INPUTS["sab_pvw_header"], INPUTS["pvw_sab_source"], INPUTS["sab_header"], INPUTS["scalar_sab_source"]]:
        relpath = rel(path)
        proc = subprocess.run(["git", "diff", "--name-only", "--", relpath], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rows.append({
            "path": relpath,
            "tracked_source": "yes",
            "modified_in_stage252": "yes" if proc.stdout.strip() else "no",
            "status": "PASS_UNCHANGED" if not proc.stdout.strip() else "FAIL_MODIFIED",
            "interpretation": "Stage252 must not change production SAB/PVW source.",
        })
    return rows


def admission_rows() -> list[dict[str, object]]:
    return [
        {
            "route": "stage252_key_skeleton",
            "decision": "ADMITTED_NON_PRODUCTION",
            "production_permission": "no",
            "allowed_next_step": "Stage253 isolated sub_a equivalence",
            "blocked_before": "production keygen; full sparse_mul; full SAB; speed claim",
        },
        {
            "route": "include_zero_pvw",
            "decision": "SKELETON_ONLY",
            "production_permission": "no",
            "allowed_next_step": "prove p + c((X^a - 1)p) per lane using MAT s_coff",
            "blocked_before": "noise/resource/full-SAB evidence",
        },
        {
            "route": "ternary_pvw",
            "decision": "SKELETON_ONLY",
            "production_permission": "no",
            "allowed_next_step": "prove X^a vs X^-a per lane using MAT s_sign",
            "blocked_before": "noise/resource/full-SAB evidence",
        },
    ]


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "nonbinary_selector_key_skeleton",
            "status": "supported_nonproduction",
            "allowed_wording": "A non-production MAT selector key skeleton for s_coff/s_sign is defined and compile-probed.",
            "forbidden_wording": "Non-binary PVW/MAT-SAB is implemented.",
            "evidence": rel(PROBE),
        },
        {
            "claim": "nonbinary_speedup",
            "status": "unsupported",
            "allowed_wording": "No non-binary speedup is claimed.",
            "forbidden_wording": "Ternary/include-zero PVW bootstrapping is faster than scalar.",
            "evidence": rel(ADMISSION),
        },
        {
            "claim": "source_isolation",
            "status": "supported",
            "allowed_wording": "Stage252 does not change production SAB/PVW source files.",
            "forbidden_wording": "Stage252 productionizes non-binary support.",
            "evidence": rel(SOURCE_ISOLATION),
        },
    ]


def gate_rows(
    inputs: list[dict[str, object]],
    probe_rows: list[dict[str, object]],
    source_rows: list[dict[str, object]],
    admission: list[dict[str, object]],
    compile_ok: bool,
    run_ok: bool,
) -> list[dict[str, object]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    stage251_ok = stage251_passes()
    probe_ok = bool(probe_rows) and all(row["status"] == "PASS_STAGE252_KEY_SKELETON" for row in probe_rows)
    source_ok = all(row["status"] == "PASS_UNCHANGED" for row in source_rows)
    admission_ok = all(row["production_permission"] == "no" for row in admission)
    decision_ok = inputs_ok and stage251_ok and compile_ok and run_ok and probe_ok and source_ok and admission_ok
    return [
        {
            "gate": "G1_inputs_and_stage251",
            "status": "PASS" if inputs_ok and stage251_ok else "FAIL",
            "metric": "inputs;stage251",
            "value": f"{str(inputs_ok).lower()};{str(stage251_ok).lower()}",
            "evidence": f"{rel(INPUT_STATUS)}; {rel(INPUTS['stage251_proof_gate'])}",
            "interpretation": "Stage252 is valid only after Stage251 blocks current production non-binary PVW.",
        },
        {
            "gate": "G2_compile_run",
            "status": "PASS" if compile_ok and run_ok else "FAIL",
            "metric": "compile;run",
            "value": f"{str(compile_ok).lower()};{str(run_ok).lower()}",
            "evidence": f"{rel(COMPILE_LOG)}; {rel(RUN_LOG_TXT)}",
            "interpretation": "The skeleton compiles and runs as an isolated C key-object probe.",
        },
        {
            "gate": "G3_layout_roles",
            "status": "PASS" if probe_ok else "FAIL",
            "metric": "probe_rows",
            "value": len(probe_rows),
            "evidence": rel(PROBE),
            "interpretation": "Distance, s_coff, and s_sign selector-family counts and guards match the skeleton contract.",
        },
        {
            "gate": "G4_source_isolation",
            "status": "PASS" if source_ok else "FAIL",
            "metric": "production_source_modified",
            "value": "no" if source_ok else "yes",
            "evidence": rel(SOURCE_ISOLATION),
            "interpretation": "Stage252 leaves scalar/default and sab_pvw production sources unchanged.",
        },
        {
            "gate": "G5_admission_boundary",
            "status": "PASS_NO_PRODUCTION",
            "metric": "production_permission",
            "value": "no",
            "evidence": rel(ADMISSION),
            "interpretation": "Stage252 admits only Stage253 isolated equivalence.",
        },
        {
            "gate": "G6_stage252_decision",
            "status": DECISION if decision_ok else "FAIL_STAGE252_NONBINARY_KEY_SKELETON",
            "metric": "decision",
            "value": DECISION if decision_ok else "FAIL_STAGE252_NONBINARY_KEY_SKELETON",
            "evidence": rel(GATES),
            "interpretation": "Proceed to isolated include-zero/ternary sub_a equivalence, not production SAB integration.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage253_isolated_nonbinary_pvw_sub_a_equivalence",
            "entry_condition": "Stage252 skeleton passes compile/layout/source-isolation gates.",
            "gate": "prove include-zero and ternary sub_a equations per lane against scalar reference",
            "status": "selected_next",
            "failure_action": "keep non-binary PVW unsupported",
            "evidence": rel(PROBE),
        },
        {
            "priority": "P1",
            "route": "stage254_nonbinary_selector_keygen_noise_preflight",
            "entry_condition": "Stage253 isolated equivalence passes.",
            "gate": "define encrypted MAT s_coff/s_sign keygen and noise/resource side conditions",
            "status": "conditional",
            "failure_action": "do not integrate full SAB",
            "evidence": rel(ADMISSION),
        },
        {
            "priority": "P2",
            "route": "stage255_nonbinary_full_sab",
            "entry_condition": "keygen/noise preflight passes and production implementation is explicitly admitted",
            "gate": "same-backend complete-SAB T_bootstrap/r, multi-seed correctness/noise, resource",
            "status": "future_gated",
            "failure_action": "no non-binary speedup claim",
            "evidence": rel(CLAIM),
        },
    ]


def artifact_rows(paths: list[Path]) -> list[dict[str, object]]:
    return [
        {
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256(path) if path.exists() and path.is_file() else "",
            "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        }
        for path in paths
    ]


def write_docs(
    inputs: list[dict[str, object]],
    design: list[dict[str, object]],
    layout: list[dict[str, object]],
    api: list[dict[str, object]],
    probe: list[dict[str, object]],
    source_rows: list[dict[str, object]],
    admission: list[dict[str, object]],
    claims: list[dict[str, object]],
    gates: list[dict[str, object]],
    nextq: list[dict[str, object]],
    head: str,
) -> None:
    write_text(DOC, f"""# Stage252 Non-Binary MAT Selector Key Skeleton

Decision: `{gates[-1]["status"]}`.

Stage252 defines a non-production key skeleton for extending binary
PVW/MAT-SAB to include-zero and ternary selector semantics. It adds no
production source and makes no speed claim.

## Skeleton Design

{table(design, ["component", "selector_family", "role", "count_per_key", "mat_object", "source_delta", "production_status"])}

## Layout Projection

{table(layout, ["param", "branch", "h", "r_prec", "distance_count", "coff_count", "sign_count", "total_selector_objects", "count_ratio_vs_binary", "interpretation"])}

## API Contract

{table(api, ["api", "inputs", "positive_contract", "negative_contract", "hot_path_status"])}

## C Probe

{table(probe, PROBE_FIELDS)}

## Source Isolation

{table(source_rows, ["path", "tracked_source", "modified_in_stage252", "status", "interpretation"])}

## Admission

{table(admission, ["route", "decision", "production_permission", "allowed_next_step", "blocked_before"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])}

## Proof Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

Generated from head `{head}`.
""")
    write_text(REPORT, f"""# Stage252 Report

Decision: `{gates[-1]["status"]}`.

The skeleton keeps the current binary distance-bit selector family and adds
optional MAT selector families for `s_coff` and `s_sign`. For target
`h=39,r_prec=7`, binary has 280 distance-bit selector objects per input-key
component; include-zero or ternary adds 39 more, and the stress case with both
families has 358. These are selector-object counts only, not byte, noise, or
speed evidence.

Production SAB/PVW source files remain unchanged. The only admitted next step
is isolated `sub_a` equivalence for include-zero and ternary equations.
""")
    write_text(PLAN, """# Stage252 Non-Binary MAT Selector Key Skeleton Plan

## Objective

Define the key/storage/API skeleton required before any non-binary PVW/MAT-SAB
implementation.

## Gates

- Stage251 must pass and keep production non-binary implementation blocked.
- The skeleton must compile and run as an isolated C probe.
- Distance, `s_coff`, and `s_sign` selector-family counts must match the
  scalar equations.
- Production SAB/PVW source files must remain unchanged.
- Next work is isolated equivalence only, not full SAB integration.
""")
    write_text(THEORY, """# Stage252 Non-Binary MAT Selector Key Skeleton Model

For each input-key component, the current binary PVW/MAT key stores
`(h+1) * r_prec` distance-bit selector objects. Non-binary scalar SAB requires
extra selector families:

- include-zero: `h` selectors for `s_coff`;
- ternary: `h` selectors for `s_sign`.

The MAT extension must provide those selector families as shared-mask,
r-body-compatible `MAT_TRGSW_DFT` objects. This skeleton records the required
object topology and API contracts only. It deliberately does not define
encrypted keygen noise, external-product composition, full sparse schedule
integration, or performance claims.
""")
    write_text(VARIANT, """# MAT-RLWE SAB Stage252 Non-Binary Selector Key Skeleton

## Variant Delta

Add optional non-production MAT selector families:

- `s_coff_mat` for include-zero presence;
- `s_sign_mat` for ternary sign.

The existing binary selector family remains the distance-bit family.

## Status

This is an API/key-storage skeleton only. It authorizes Stage253 isolated
equivalence tests and nothing beyond that.
""")
    write_text(REPRO_CMDS, f"""# Stage252 Reproduction Commands

```text
python scripts/build_stage252_nonbinary_mat_selector_key_skeleton.py
python -m py_compile scripts/build_stage252_nonbinary_mat_selector_key_skeleton.py
```

Decision: `{gates[-1]["status"]}`.
""")


def update_project_files(head: str, decision: str) -> None:
    append_once(ROADMAP, "## Stage 252: Non-Binary MAT Selector Key Skeleton", f"""
## Stage 252: Non-Binary MAT Selector Key Skeleton

Goal:

```text
Define the non-production MAT selector key/storage/API skeleton needed for
include-zero and ternary PVW/MAT-SAB branches.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. Stage252 compiles and
runs an isolated selector-key skeleton with existing distance bits plus
optional `s_coff` and `s_sign` MAT selector families. Production SAB/PVW source
files remain unchanged; Stage253 isolated sub_a equivalence is the only
admitted next step.
```
""")
    append_once(GOAL, "Stage252 non-binary MAT selector key skeleton", f"""
- Stage252 non-binary MAT selector key skeleton records `{decision}`: the
  required `s_coff/s_sign` MAT selector storage is now defined as a
  non-production skeleton, but non-binary PVW/MAT-SAB remains unimplemented.
""")
    append_once(CURRENT_GOAL, "### Stage252 non-binary MAT selector key skeleton", f"""
### Stage252 non-binary MAT selector key skeleton

`{decision}` advances non-binary support from semantics to a compile-probed
selector/key skeleton. The active goal remains open for isolated equivalence,
keygen/noise/resource, full SAB A/B, and paper claim closure.
""")
    append_once(HYPOTHESES, "H10_stage252_nonbinary_mat_selector_key_skeleton:", f"""
H10_stage252_nonbinary_mat_selector_key_skeleton:
  status: nonbinary_selector_key_skeleton_ready_isolated_equivalence
  evidence:
    - repro/stage252_nonbinary_mat_selector_key_skeleton/skeleton_design_matrix.csv
    - repro/stage252_nonbinary_mat_selector_key_skeleton/toy_key_object_probe.csv
    - repro/stage252_nonbinary_mat_selector_key_skeleton/source_isolation.csv
    - repro/stage252_nonbinary_mat_selector_key_skeleton/proof_gate.csv
    - docs/stage252_nonbinary_mat_selector_key_skeleton.md
  conclusion: >
    Stage252 records {decision}. It defines a non-production MAT selector
    key/storage skeleton for distance bits plus optional s_coff and s_sign,
    compile-probes layout/guard/hot-scan invariants, and keeps production
    SAB/PVW source unchanged. Only isolated equivalence is admitted next.
""")
    append_once(RUN_LOG, "stage252-nonbinary-mat-selector-key-skeleton-001", f"""stage252-nonbinary-mat-selector-key-skeleton-001,{date.today().isoformat()},{head},Stage 252,selector_key_skeleton,"python scripts/build_stage252_nonbinary_mat_selector_key_skeleton.py","Stage251 semantics/admission + C skeleton compile probe",n/a,{decision},"Non-binary selector key skeleton ready for isolated equivalence only.",docs/stage252_nonbinary_mat_selector_key_skeleton.md; repro/stage252_nonbinary_mat_selector_key_skeleton/proof_gate.csv
""")
    append_once(MANIFEST, "- stage252_nonbinary_mat_selector_key_skeleton:", """
- stage252_nonbinary_mat_selector_key_skeleton:
  - `docs/stage252_nonbinary_mat_selector_key_skeleton.md`
  - `experiments/stage252_nonbinary_mat_selector_key_skeleton_plan.md`
  - `theory_checks/stage252_nonbinary_mat_selector_key_skeleton_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage252_nonbinary_mat_selector_key_skeleton.md`
  - `scripts/build_stage252_nonbinary_mat_selector_key_skeleton.py`
  - `repro/stage252_nonbinary_mat_selector_key_skeleton/`
""")
    append_once(CHECKLIST, "Stage252 non-binary MAT selector key skeleton ready for isolated equivalence", f"""
- [x] Stage252 non-binary MAT selector key skeleton ready for isolated equivalence `{decision}`.
""")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    head = run_git(["rev-parse", "--short", "HEAD"])
    inputs = input_rows()
    design = design_rows()
    layout = layout_rows()
    api = api_contract_rows()
    write_c_source()
    compile_ok = compile_probe()
    run_ok, probe = run_probe(compile_ok)
    source_rows = source_isolation_rows()
    admission = admission_rows()
    claims = claim_rows()
    gates = gate_rows(inputs, probe, source_rows, admission, compile_ok, run_ok)
    nextq = next_rows()

    write_csv(INPUT_STATUS, inputs, ["input_id", "path", "status", "bytes"])
    write_csv(DESIGN, design, ["component", "selector_family", "role", "count_per_key", "mat_object", "source_delta", "production_status"])
    write_csv(LAYOUT, layout, ["param", "branch", "h", "r_prec", "distance_count", "coff_count", "sign_count", "total_selector_objects", "count_ratio_vs_binary", "interpretation"])
    write_csv(API_CONTRACT, api, ["api", "inputs", "positive_contract", "negative_contract", "hot_path_status"])
    write_csv(PROBE, probe, PROBE_FIELDS)
    write_csv(SOURCE_ISOLATION, source_rows, ["path", "tracked_source", "modified_in_stage252", "status", "interpretation"])
    write_csv(ADMISSION, admission, ["route", "decision", "production_permission", "allowed_next_step", "blocked_before"])
    write_csv(CLAIM, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])

    write_docs(inputs, design, layout, api, probe, source_rows, admission, claims, gates, nextq, head)
    artifacts = [
        DOC,
        PLAN,
        THEORY,
        VARIANT,
        INPUT_STATUS,
        DESIGN,
        LAYOUT,
        API_CONTRACT,
        PROBE,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        SOURCE_ISOLATION,
        ADMISSION,
        CLAIM,
        GATES,
        NEXT,
        REPORT,
        REPRO_CMDS,
    ]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "exists", "sha256", "bytes"])
    if gates[-1]["status"] == DECISION:
        update_project_files(head, gates[-1]["status"])
    print(f"Stage252 report: {rel(DOC)}")
    print(f"Stage252 decision: {gates[-1]['status']}")
    return 0 if gates[-1]["status"] == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
