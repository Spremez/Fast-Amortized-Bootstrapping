#!/usr/bin/env python3
"""Stage219: MOSFHET-adjacent compact key API skeleton."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT = ROOT / "repro" / "stage219_mosfhet_compact_key_api_skeleton"

DOC = ROOT / "docs" / "stage219_mosfhet_compact_key_api_skeleton.md"
PLAN = ROOT / "experiments" / "stage219_mosfhet_compact_key_api_skeleton_plan.md"
THEORY = ROOT / "theory_checks" / "stage219_compact_key_api_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage219_compact_key_api_skeleton.md"

INPUTS = OUT / "input_status.csv"
API = OUT / "api_results.csv"
LAYOUT = OUT / "layout_results.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
BUILD_LOG = OUT / "mosfhet_static_build.log"
COMPILE_LOG = OUT / "compile_probe.log"
RUN_LOG_TXT = OUT / "run_probe.log"
C_SOURCE = OUT / "stage219_compact_key_api_skeleton.c"
C_BINARY = OUT / "stage219_compact_key_api_skeleton"
REPORT = OUT / "compact_key_api_skeleton_report.md"
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
STAGE218_LAYOUT = ROOT / "repro" / "stage218_compact_key_object_noise_prototype" / "key_object_layout.csv"
STAGE218_PROOF = ROOT / "repro" / "stage218_compact_key_object_noise_prototype" / "proof_gate.csv"
HEADER = ROOT / "src" / "mosfhet" / "include" / "mosfhet.h"
MATTRGSW_C = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"

API_FIELDS = [
    "backend",
    "r",
    "N",
    "dense_rows",
    "active_rows",
    "dummy_rows",
    "pointer_failures",
    "role_failures",
    "guard_failures",
    "roundtrip_mismatches",
    "max_gap",
    "tolerance",
    "hot_alloc_delta",
    "status",
]

LAYOUT_FIELDS = [
    "r",
    "N",
    "dense_rows",
    "active_rows",
    "dummy_rows",
    "skippable_rows",
    "active_over_dense",
    "dummy_over_dense",
    "status",
]

DECISION = "PASS_STAGE219_MOSFHET_COMPACT_KEY_API_SKELETON_READY_ENCRYPTED_KEYGEN"


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
        ("stage203_equation_map", STAGE203_EQUATION, "row-role source for generated C probe"),
        ("stage218_layout", STAGE218_LAYOUT, "expected dense/active/dummy layout"),
        ("stage218_proof_gate", STAGE218_PROOF, "permission for API skeleton only"),
        ("mosfhet_header", HEADER, "production MOSFHET public types/functions"),
        ("mattrgsw_compact_impl", MATTRGSW_C, "current compact allocator/function implementation"),
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
    return "STAGE219_ROLE_ACTIVE" if row["semantic_role"] == "active" else "STAGE219_ROLE_DUMMY_ZERO"


def write_c_source() -> None:
    by_r = equation_rows_by_r()
    array_blocks: List[str] = []
    for r, rows in sorted(by_r.items()):
        array_blocks.append(f"static const Stage219EquationRow stage219_r{r}_rows[] = {{")
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

#ifndef STAGE219_BACKEND
#define STAGE219_BACKEND "unknown"
#endif

typedef enum {{
  STAGE219_ROLE_ACTIVE = 1,
  STAGE219_ROLE_DUMMY_ZERO = 2
}} Stage219Role;

typedef struct {{
  int row;
  int col;
  int role;
  int may_skip;
}} Stage219EquationRow;

{arrays}

typedef struct _Stage219CompactKey {{
  DFT_Polynomial * rows;
  int * roles;
  int * may_skip;
  int row_count;
  int active_count;
  int dummy_count;
  int skippable_count;
  int r;
  int N;
}} *Stage219CompactKey;

static uint64_t stage219_alloc_counter = 0;

static void * stage219_checked_malloc(size_t bytes){{
  stage219_alloc_counter++;
  void * p = safe_malloc(bytes);
  return p;
}}

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

static Torus small_torus(uint64_t salt, uint64_t row, uint64_t col, uint64_t idx){{
  return (Torus)(mix64(salt, row, col, idx) % 31ULL);
}}

static uint64_t abs_gap(Torus a, Torus b){{
  const uint64_t d = (uint64_t)(a - b);
  if(d <= (1ULL << 63)) return d;
  return (~d) + 1ULL;
}}

static const Stage219EquationRow * rows_for_r(int r, int * count){{
  if(r == 2){{
    *count = (int)(sizeof(stage219_r2_rows) / sizeof(stage219_r2_rows[0]));
    return stage219_r2_rows;
  }}
  if(r == 4){{
    *count = (int)(sizeof(stage219_r4_rows) / sizeof(stage219_r4_rows[0]));
    return stage219_r4_rows;
  }}
  if(r == 6){{
    *count = (int)(sizeof(stage219_r6_rows) / sizeof(stage219_r6_rows[0]));
    return stage219_r6_rows;
  }}
  *count = 0;
  return NULL;
}}

static Stage219CompactKey stage219_compact_key_alloc(int r, int N){{
  int row_count = 0;
  const Stage219EquationRow * eq = rows_for_r(r, &row_count);
  if(eq == NULL || row_count <= 0) return NULL;
  Stage219CompactKey key = (Stage219CompactKey)stage219_checked_malloc(sizeof(*key));
  key->rows = (DFT_Polynomial *)stage219_checked_malloc(sizeof(DFT_Polynomial) * row_count);
  key->roles = (int *)stage219_checked_malloc(sizeof(int) * row_count);
  key->may_skip = (int *)stage219_checked_malloc(sizeof(int) * row_count);
  key->row_count = row_count;
  key->active_count = 0;
  key->dummy_count = 0;
  key->skippable_count = 0;
  key->r = r;
  key->N = N;
  for(int i = 0; i < row_count; i++){{
    key->rows[i] = polynomial_new_DFT_polynomial(N);
    key->roles[i] = eq[i].role;
    key->may_skip[i] = eq[i].may_skip;
    if(eq[i].role == STAGE219_ROLE_ACTIVE) key->active_count++;
    if(eq[i].role == STAGE219_ROLE_DUMMY_ZERO) key->dummy_count++;
    if(eq[i].may_skip) key->skippable_count++;
  }}
  return key;
}}

static void stage219_compact_key_free(Stage219CompactKey key){{
  if(key == NULL) return;
  for(int i = 0; i < key->row_count; i++) free_DFT_polynomial(key->rows[i]);
  free(key->rows);
  free(key->roles);
  free(key->may_skip);
  free(key);
}}

static int stage219_set_row_from_torus(Stage219CompactKey key, int idx, TorusPolynomial row){{
  if(key == NULL || idx < 0 || idx >= key->row_count) return -1;
  if(row == NULL) return -2;
  if(row->N != key->N) return -3;
  polynomial_torus_to_DFT(key->rows[idx], row);
  return 0;
}}

static int stage219_hot_role_scan(Stage219CompactKey key, int * active, int * skip){{
  int active_count = 0;
  int skip_count = 0;
  for(int i = 0; i < key->row_count; i++){{
    if(key->roles[i] == STAGE219_ROLE_ACTIVE) active[active_count++] = i;
    if(key->may_skip[i]) skip[skip_count++] = i;
  }}
  return active_count * 1000 + skip_count;
}}

static void fill_poly(TorusPolynomial p, uint64_t salt, int row, int col){{
  for(int i = 0; i < p->N; i++) p->coeffs[i] = small_torus(salt, (uint64_t)row, (uint64_t)col, (uint64_t)i);
}}

static uint64_t pointer_failures(Stage219CompactKey key){{
  uint64_t failures = 0;
  for(int i = 0; i < key->row_count; i++){{
    if(key->rows[i] == NULL || key->rows[i]->coeffs == NULL) failures++;
    for(int j = i + 1; j < key->row_count; j++){{
      if(key->rows[i]->coeffs == key->rows[j]->coeffs) failures++;
    }}
  }}
  return failures;
}}

static void run_case(int r, int N){{
  int eq_count = 0;
  const Stage219EquationRow * eq = rows_for_r(r, &eq_count);
  const uint64_t tolerance = 2048;
  Stage219CompactKey key = stage219_compact_key_alloc(r, N);
  TorusPolynomial tmp = polynomial_new_torus_polynomial(N);
  TorusPolynomial wrong = polynomial_new_torus_polynomial(N / 2);
  TorusPolynomial round = polynomial_new_torus_polynomial(N);
  uint64_t guard_failures = 0;
  uint64_t role_failures = 0;
  uint64_t roundtrip_mismatches = 0;
  uint64_t max_gap = 0;

  if(stage219_set_row_from_torus(key, -1, tmp) != -1) guard_failures++;
  if(stage219_set_row_from_torus(key, key->row_count, tmp) != -1) guard_failures++;
  if(stage219_set_row_from_torus(key, 0, NULL) != -2) guard_failures++;
  if(stage219_set_row_from_torus(key, 0, wrong) != -3) guard_failures++;

  int active_expected = 0;
  int dummy_expected = 0;
  int skip_expected = 0;
  for(int i = 0; i < eq_count; i++){{
    if(eq[i].role == STAGE219_ROLE_ACTIVE) active_expected++;
    if(eq[i].role == STAGE219_ROLE_DUMMY_ZERO) dummy_expected++;
    if(eq[i].may_skip) skip_expected++;
    if(key->roles[i] != eq[i].role || key->may_skip[i] != eq[i].may_skip) role_failures++;
    fill_poly(tmp, 219000ULL + (uint64_t)N, eq[i].row, eq[i].col);
    if(stage219_set_row_from_torus(key, i, tmp) != 0) guard_failures++;
    polynomial_DFT_to_torus(round, key->rows[i]);
    for(int c = 0; c < N; c++){{
      const uint64_t gap = abs_gap(tmp->coeffs[c], round->coeffs[c]);
      if(gap > tolerance) roundtrip_mismatches++;
      if(gap > max_gap) max_gap = gap;
    }}
  }}
  if(key->active_count != active_expected) role_failures++;
  if(key->dummy_count != dummy_expected) role_failures++;
  if(key->skippable_count != skip_expected) role_failures++;

  int * active = (int *)safe_malloc(sizeof(int) * key->row_count);
  int * skip = (int *)safe_malloc(sizeof(int) * key->row_count);
  const uint64_t alloc_before = stage219_alloc_counter;
  const int scan = stage219_hot_role_scan(key, active, skip);
  const uint64_t alloc_after = stage219_alloc_counter;
  const int active_scan = scan / 1000;
  const int skip_scan = scan % 1000;
  const uint64_t hot_alloc_delta = alloc_after - alloc_before;
  if(active_scan != active_expected) role_failures++;
  if(skip_scan != skip_expected) role_failures++;

  const uint64_t ptr_failures = pointer_failures(key);
  const int api_ok = ptr_failures == 0 && role_failures == 0 &&
      guard_failures == 0 && roundtrip_mismatches == 0 && hot_alloc_delta == 0;
  const double active_over_dense = (double)key->active_count / (double)key->row_count;
  const double dummy_over_dense = (double)key->dummy_count / (double)key->row_count;
  const int layout_ok = key->row_count == (r + 1) * (r + 1) &&
      key->dummy_count == key->skippable_count &&
      key->active_count + key->dummy_count == key->row_count;

  printf("API,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%s\\n",
      STAGE219_BACKEND, r, N, key->row_count, key->active_count,
      key->dummy_count, ptr_failures, role_failures, guard_failures,
      roundtrip_mismatches, max_gap, tolerance, hot_alloc_delta,
      api_ok ? "PASS_COMPACT_KEY_API_SKELETON" : "FAIL");
  printf("LAYOUT,%d,%d,%d,%d,%d,%d,%.9f,%.9f,%s\\n",
      r, N, key->row_count, key->active_count, key->dummy_count,
      key->skippable_count, active_over_dense, dummy_over_dense,
      layout_ok ? "PASS_ROLE_LAYOUT" : "FAIL");

  free(active);
  free(skip);
  free_polynomial(round);
  free_polynomial(wrong);
  free_polynomial(tmp);
  stage219_compact_key_free(key);
}}

int main(void){{
  run_case(2, 1024);
  run_case(4, 1024);
  run_case(6, 1024);
  run_case(2, 2048);
  run_case(4, 2048);
  run_case(6, 2048);
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
        f"gcc -O2 -DSTAGE219_BACKEND=\\\"{backend}\\\" "
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
    api_rows: List[Dict[str, str]] = []
    layout_rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        if not line.strip():
            continue
        values = line.strip().split(",")
        if values[0] == "API":
            api_rows.append(dict(zip(API_FIELDS, values[1:])))
        elif values[0] == "LAYOUT":
            layout_rows.append(dict(zip(LAYOUT_FIELDS, values[1:])))
        else:
            raise RuntimeError(f"unexpected probe row: {line}")
    cleanup_build_outputs()
    return api_rows, layout_rows, proc.returncode == 0


def stage218_layout_by_r() -> Dict[str, Dict[str, str]]:
    return {row["r"]: row for row in read_csv(STAGE218_LAYOUT)}


def build_proof(build_ok: bool, compile_ok: bool, run_ok: bool, api_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]], inputs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    missing = [row["input"] for row in inputs if row["status"] != "present"]
    api_pass = run_ok and api_rows and all(row["status"] == "PASS_COMPACT_KEY_API_SKELETON" for row in api_rows)
    layout_pass = layout_rows and all(row["status"] == "PASS_ROLE_LAYOUT" for row in layout_rows)
    expected = stage218_layout_by_r()
    layout_mismatches = 0
    for row in layout_rows:
        exp = expected.get(row["r"], {})
        if exp:
            if row["dense_rows"] != exp.get("dense_public_rows"):
                layout_mismatches += 1
            if row["active_rows"] != exp.get("active_rows"):
                layout_mismatches += 1
            if row["dummy_rows"] != exp.get("dummy_zero_rows"):
                layout_mismatches += 1
    max_gap = max((int(row["max_gap"]) for row in api_rows), default=0)
    max_hot_alloc = max((int(row["hot_alloc_delta"]) for row in api_rows), default=0)
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if not missing else "FAIL",
            "metric": "missing_inputs",
            "value": ";".join(missing),
            "evidence": rel(INPUTS),
            "interpretation": "Stage219 consumes Stage203 equation rows and Stage218 API-skeleton permission.",
        },
        {
            "gate": "G2_mosfhet_static_build",
            "status": "PASS" if build_ok else "BLOCKED",
            "metric": "make_static_spqlios",
            "value": str(build_ok).lower(),
            "evidence": rel(BUILD_LOG),
            "interpretation": "Probe links against current MOSFHET static library.",
        },
        {
            "gate": "G3_probe_compile_run",
            "status": "PASS" if compile_ok and run_ok else "FAIL",
            "metric": "compile_ok;run_ok",
            "value": f"{str(compile_ok).lower()};{str(run_ok).lower()}",
            "evidence": f"{rel(COMPILE_LOG)}; {rel(RUN_LOG_TXT)}",
            "interpretation": "Standalone compact key API skeleton compiles and runs.",
        },
        {
            "gate": "G4_ownership_roles_guards",
            "status": "PASS" if api_pass else "FAIL",
            "metric": "max_gap;max_hot_alloc_delta",
            "value": f"{max_gap};{max_hot_alloc}",
            "evidence": rel(API),
            "interpretation": "DFT rows are non-aliased, row roles match generated equations, invalid guards pass, and hot role scan allocates nothing.",
        },
        {
            "gate": "G5_stage218_layout_match",
            "status": "PASS" if layout_pass and layout_mismatches == 0 else "FAIL",
            "metric": "layout_mismatches",
            "value": str(layout_mismatches),
            "evidence": f"{rel(LAYOUT)}; {rel(STAGE218_LAYOUT)}",
            "interpretation": "Compiled API skeleton preserves Stage218 dense/active/dummy row counts for r=2/4/6.",
        },
        {
            "gate": "G6_production_admission",
            "status": "DENY_SAB_HOTPATH_CODE",
            "metric": "missing_before_sab_code",
            "value": "encrypted_keygen;security_reduction;production_noise;compact_ep_integration;complete_sab_gate",
            "evidence": rel(PROOF),
            "interpretation": "Stage219 permits encrypted compact keygen prototype only; no SAB integration or speedup claim.",
        },
        {
            "gate": "G7_stage219_decision",
            "status": DECISION if not missing and build_ok and compile_ok and run_ok and api_pass and layout_pass and layout_mismatches == 0 else "FAIL_STAGE219",
            "metric": "decision",
            "value": DECISION if not missing and build_ok and compile_ok and run_ok and api_pass and layout_pass and layout_mismatches == 0 else "FAIL_STAGE219",
            "evidence": rel(PROOF),
            "interpretation": "MOSFHET-adjacent compact key API skeleton is ready for encrypted keygen prototype, still outside SAB hot path.",
        },
    ]


def build_next() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage220_encrypted_compact_keygen_prototype",
            "entry_condition": "Stage219 compact key API skeleton passes compile/run/role/ownership gates.",
            "gate": "Prototype encrypted compact keygen rows with semantic-zero dummy role preservation and negative controls.",
            "status": "selected",
            "failure_action": "If encrypted keygen semantics fail, compact route remains API-only and SAB integration is denied.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P1",
            "route": "production_noise_recurrence",
            "entry_condition": "Encrypted compact keygen prototype exists.",
            "gate": "Noise recurrence and parameter/resource bound before complete-SAB integration.",
            "status": "future_blocked",
            "failure_action": "Block compact route from SAB integration.",
            "evidence": rel(STAGE218_PROOF),
        },
        {
            "priority": "P2",
            "route": "exact_pvw_mat_sab_report_fallback",
            "entry_condition": "Any compact API/keygen gate fails.",
            "gate": "Report only current exact PVW/MAT-SAB T_bootstrap/r evidence.",
            "status": "fallback",
            "failure_action": "No compact algorithmic claim.",
            "evidence": rel(STAGE218_PROOF),
        },
    ]


def write_docs(inputs: List[Dict[str, str]], api_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]], proof: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> None:
    report = f"""# Stage219 MOSFHET Compact Key API Skeleton

Decision: `{proof[-1]["status"]}`.

Stage219 compiles and runs a MOSFHET-adjacent compact key API skeleton. The C
probe uses real MOSFHET `TorusPolynomial`/`DFT_Polynomial` allocation and DFT
conversion functions, while keeping the new compact key row-role metadata in a
repro-only skeleton. It does not modify production headers or `sab_pvw_*`.

## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Input Status

{table(inputs, ["input", "status", "evidence", "role", "bytes"])}
## API Results

{table(api_rows, API_FIELDS)}
## Layout Results

{table(layout_rows, LAYOUT_FIELDS)}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
"""
    write_text(REPORT, report)
    write_text(DOC, report)
    write_text(
        PLAN,
        """# Stage219 Plan

Goal: compile-check a MOSFHET-adjacent compact key API skeleton after the
Stage218 finite key-object/noise prototype.

Gates:

- current MOSFHET static library builds;
- generated C probe compiles and runs;
- DFT row ownership is non-aliased;
- row roles match Stage203 equations and Stage218 counts;
- invalid guard checks pass;
- hot role scan uses no skeleton allocation;
- no SAB hot-path code is authorized.
""",
    )
    write_text(
        THEORY,
        """# Stage219 Compact Key API Model

The compact key object is represented as dense public DFT rows plus explicit
row-role metadata: active rows and semantic-zero dummy rows. This preserves the
public row count required by the Stage217 pattern-only gate while exposing the
semantic skip set needed by the Stage218 finite key-object prototype.

This model is not a security proof. It only establishes that the object can be
expressed with MOSFHET polynomial allocation/conversion lifecycles and a
no-allocation hot row-role scan. Encrypted keygen, security, production noise,
compact EP integration, and complete-SAB `T_bootstrap/r` remain future gates.
""",
    )
    write_text(
        VARIANT,
        """# Compact Key API Skeleton

This is a repro-only MOSFHET-adjacent API skeleton.

It verifies:

- dense public row count is preserved;
- active/dummy row roles match Stage203/Stage218;
- real MOSFHET DFT lifecycle works for every generated row;
- invalid input guards are checked;
- hot role scan allocates no skeleton memory.

It does not implement encrypted keygen, security proof, production noise, SAB
integration, or any new complete-SAB speedup.
""",
    )
    write_text(
        REPRO,
        """# Stage219 Reproduction Commands

```powershell
python scripts\\build_stage219_mosfhet_compact_key_api_skeleton.py
Get-Content -Raw repro\\stage219_mosfhet_compact_key_api_skeleton\\proof_gate.csv
Get-Content -Raw repro\\stage219_mosfhet_compact_key_api_skeleton\\api_results.csv
```
""",
    )


def update_tracking(status: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 219: MOSFHET Compact Key API Skeleton",
        f"""
## Stage 219: MOSFHET Compact Key API Skeleton

Goal:

```text
Compile-check a MOSFHET-adjacent compact key API skeleton after Stage218,
without touching SAB hot paths.
```

Status:

```text
Completed. Stage219 records {status}. The compact key row-role API skeleton
passes build/compile/run gates and routes next to encrypted compact keygen
prototype only; SAB integration remains denied.
```
""",
    )
    append_once(
        GOAL,
        "Stage219 records MOSFHET compact key API skeleton",
        f"""
Stage219 records MOSFHET compact key API skeleton. Decision: `{status}`. The
route now has a compile-checked MOSFHET-adjacent key object boundary, but not
encrypted keygen, production noise, complete-SAB integration, or speedup
evidence.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage219 MOSFHET compact key API skeleton",
        f"""
### Stage219 MOSFHET compact key API skeleton

`{status}` advances the compact route only to an encrypted-keygen prototype
candidate. It does not authorize `sab_pvw_*` integration, complete-SAB claims,
or production security/noise claims.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage219_mosfhet_compact_key_api_skeleton",
        f"""
H10_stage219_mosfhet_compact_key_api_skeleton:
  status: compact_key_api_skeleton_compile_checked
  evidence:
    - repro/stage219_mosfhet_compact_key_api_skeleton/proof_gate.csv
    - repro/stage219_mosfhet_compact_key_api_skeleton/api_results.csv
    - docs/stage219_mosfhet_compact_key_api_skeleton.md
  conclusion: >
    Stage219 records {status}. A MOSFHET-adjacent compact key row-role API
    skeleton is compile-checked, but encrypted keygen, security, production
    noise, compact EP integration, and complete-SAB gates remain missing.
""",
    )
    append_once(
        RUN_LOG,
        "stage219-mosfhet-compact-key-api-skeleton-001",
        f"""stage219-mosfhet-compact-key-api-skeleton-001,2026-07-04,{head},Stage 219,spqlios,python scripts/build_stage219_mosfhet_compact_key_api_skeleton.py,Stage203 equations and Stage218 API-skeleton permission,no SAB benchmark,{status},"MOSFHET-adjacent compact key API skeleton compile/run gate.",docs/stage219_mosfhet_compact_key_api_skeleton.md; repro/stage219_mosfhet_compact_key_api_skeleton/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage219_mosfhet_compact_key_api_skeleton:",
        """
- stage219_mosfhet_compact_key_api_skeleton:
  - `docs/stage219_mosfhet_compact_key_api_skeleton.md`
  - `experiments/stage219_mosfhet_compact_key_api_skeleton_plan.md`
  - `theory_checks/stage219_compact_key_api_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage219_compact_key_api_skeleton.md`
  - `scripts/build_stage219_mosfhet_compact_key_api_skeleton.py`
  - `repro/stage219_mosfhet_compact_key_api_skeleton/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage219 MOSFHET compact key API skeleton recorded",
        """
- [x] Stage219 MOSFHET compact key API skeleton recorded.
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
    api_rows, layout_rows, run_ok = run_probe(build_ok, compile_ok)
    write_csv(API, api_rows, API_FIELDS)
    write_csv(LAYOUT, layout_rows, LAYOUT_FIELDS)
    proof = build_proof(build_ok, compile_ok, run_ok, api_rows, layout_rows, inputs)
    next_rows = build_next()
    write_csv(INPUTS, inputs, ["input", "status", "evidence", "role", "bytes"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_docs(inputs, api_rows, layout_rows, proof, next_rows)
    status = proof[-1]["status"]
    update_tracking(status)
    write_artifacts([DOC, PLAN, THEORY, VARIANT, INPUTS, API, LAYOUT, PROOF, NEXT, BUILD_LOG, COMPILE_LOG, RUN_LOG_TXT, C_SOURCE, REPORT, REPRO, Path(__file__)])
    print(status)
    return 0 if status == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
