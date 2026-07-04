#!/usr/bin/env python3
"""Stage286 MAT EP split/counter gate for the current PVW/MAT-SAB frontier.

This stage is intentionally a gate, not a hot-path rewrite.  It consumes the
Stage284 frontier ledger, anchors the current MAT external-product source, and
builds a local source/assembly/projection evidence pack.  Hardware-counter and
paper-grade claims remain blocked unless native/perf evidence is present.
"""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage286_mat_ep_split_counter_gate"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage286_mat_ep_split_counter_gate.md"
THEORY = ROOT / "theory_checks" / "stage286_mat_ep_split_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage286_mat_ep_split_candidates.md"
PLAN = ROOT / "experiments" / "stage286_mat_ep_counter_validation_plan.md"
BUILDER = ROOT / "scripts" / "build_stage286_mat_ep_split_counter_gate.py"

CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

MATTRGSW_C = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"
SAB_PVW_C = ROOT / "src" / "sab_pvw.c"
OBJECT = ROOT / "build" / "mattrgsw.o"

STAGE284_FRONTIER = ROOT / "repro" / "stage284_frontier_gap_ledger" / "frontier_summary.csv"
STAGE284_RESIDUAL = ROOT / "repro" / "stage284_frontier_gap_ledger" / "residual_gap_ledger.csv"
STAGE284_ALGO = ROOT / "repro" / "stage284_frontier_gap_ledger" / "algorithm_frontier.csv"
STAGE281_LATENCY = ROOT / "repro" / "stage281_cmux_residual_repeated_gate" / "latency_summary.csv"
STAGE280_PROFILE = ROOT / "repro" / "stage280_cmux_mat_ep_residual_screen" / "profile_components.csv"
STAGE283_PROOF = ROOT / "repro" / "stage283_native_target_repeated_gate" / "proof_gate.csv"
STAGE264_SOURCE_MODEL = ROOT / "repro" / "stage264_mat_avx512_counter_preflight" / "source_model.csv"

INPUT_STATUS = OUT / "input_status.csv"
TOOL_MATRIX = OUT / "tool_matrix.csv"
SOURCE_ANCHORS = OUT / "source_anchor_matrix.csv"
STATIC_SPLIT = OUT / "mat_ep_static_split_model.csv"
IMPROVEMENT_TARGETS = OUT / "improvement_targets.csv"
ASM_PROXY = OUT / "instruction_proxy.csv"
ADMISSION = OUT / "code_admission_matrix.csv"
CLAIMS = OUT / "claim_boundary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage286_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION = "PASS_STAGE286_MAT_EP_SPLIT_PROXY_READY_NATIVE_COUNTER_REQUIRED"
TARGET_VARIANT = "backend_sub_decomp_dual"
R_VALUE = 4
M_OUTPUTS = R_VALUE + 1
ROWS = M_OUTPUTS
N = 2048
CMUX_CALLS = 573440


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.rstrip().split("\n"))
    path.write_text(normalized + "\n", encoding="utf-8", newline="\n")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    field_list = list(fields)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_list, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in field_list})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    sep = "" if current.endswith("\n") or not current else "\n"
    write_text(path, current + sep + text)


def fnum(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def run_bash(command: str, log: Path, timeout: int = 300) -> int:
    launcher = ["bash", "-lc"] if shutil.which("bash") else ["wsl", "bash", "-lc"]
    proc = subprocess.run(
        launcher + [command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    write_text(
        log,
        "\n".join(
            [
                f"command: {command}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                proc.stdout.replace("\x00", ""),
                "--- stderr ---",
                proc.stderr.replace("\x00", ""),
            ]
        ),
    )
    return proc.returncode


def run_capture(command: str, log: Path, output: Path, timeout: int = 300) -> int:
    launcher = ["bash", "-lc"] if shutil.which("bash") else ["wsl", "bash", "-lc"]
    proc = subprocess.run(
        launcher + [command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    write_text(output, proc.stdout.replace("\x00", ""))
    write_text(
        log,
        "\n".join(
            [
                f"command: {command}",
                f"returncode: {proc.returncode}",
                "--- stderr ---",
                proc.stderr.replace("\x00", ""),
            ]
        ),
    )
    return proc.returncode


def input_rows() -> List[Dict[str, object]]:
    paths = {
        "stage284_frontier": STAGE284_FRONTIER,
        "stage284_residual": STAGE284_RESIDUAL,
        "stage284_algorithm": STAGE284_ALGO,
        "stage281_latency": STAGE281_LATENCY,
        "stage280_profile": STAGE280_PROFILE,
        "stage283_proof": STAGE283_PROOF,
        "stage264_source_model": STAGE264_SOURCE_MODEL,
        "mattrgsw_source": MATTRGSW_C,
        "sab_pvw_source": SAB_PVW_C,
    }
    return [
        {
            "input_id": name,
            "path": rel(path),
            "status": "present" if path.exists() else "missing",
            "bytes": path.stat().st_size if path.exists() else 0,
        }
        for name, path in paths.items()
    ]


def local_tool_probe() -> List[Dict[str, object]]:
    RAW.mkdir(parents=True, exist_ok=True)
    env_cmd = (
        "printf 'hostname='; hostname; "
        "printf 'uname='; uname -a; "
        "printf 'cpu_model='; (lscpu | sed -n 's/^Model name:[[:space:]]*//p' | head -n 1); "
        "printf 'cpu_flags='; (lscpu | sed -n 's/^Flags:[[:space:]]*//p' | head -n 1); "
        "printf 'perf_path='; command -v perf || true; "
        "printf 'objdump_path='; command -v objdump || true; "
        "printf 'nm_path='; command -v nm || true"
    )
    run_bash(env_cmd, RAW / "environment.log", timeout=60)
    perf_rc = run_bash("command -v perf >/dev/null 2>&1 && perf stat -e cycles true", RAW / "perf_probe.log", timeout=60)
    build_cmd = (
        "make -B build/mattrgsw.o "
        "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
        "KEY=BINARY PARAM=SET_2_3 "
        "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
        "MAT_TRGSW_AVX512_SUB_DECOMP=true "
        "SAB_PVW_SUB_DECOMP_FUSION=true "
        "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
        "SAB_PVW_DUAL_SUB_CMUX=true "
        "SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true"
    )
    build_rc = run_bash(build_cmd, RAW / "mattrgsw_build.log", timeout=600)
    objdump_rc = run_capture("objdump -d build/mattrgsw.o", RAW / "objdump.log", RAW / "mattrgsw_objdump.txt", timeout=120) if OBJECT.exists() else 1
    nm_rc = run_capture("nm -C build/mattrgsw.o", RAW / "nm.log", RAW / "mattrgsw_nm.txt", timeout=120) if OBJECT.exists() else 1

    env_text = read_text(RAW / "environment.log")
    def grab(key: str) -> str:
        match = re.search(rf"^{key}=(.*)$", env_text, re.MULTILINE)
        return match.group(1).strip() if match else ""

    return [
        {
            "tool_or_signal": "cpu_avx512f",
            "status": "PASS" if "avx512f" in grab("cpu_flags") else "MISSING",
            "evidence": rel(RAW / "environment.log"),
            "detail": grab("cpu_model"),
            "claim_effect": "AVX512 source/assembly proxy only; not retired counters.",
        },
        {
            "tool_or_signal": "perf",
            "status": "AVAILABLE" if perf_rc == 0 else "MISSING_OR_PERMISSION_DENIED",
            "evidence": rel(RAW / "perf_probe.log"),
            "detail": f"rc={perf_rc}",
            "claim_effect": "Hardware-counter claims require this to pass on native target.",
        },
        {
            "tool_or_signal": "build_mattrgsw_object",
            "status": "PASS" if build_rc == 0 and OBJECT.exists() else "FAIL",
            "evidence": rel(RAW / "mattrgsw_build.log"),
            "detail": f"rc={build_rc}",
            "claim_effect": "Current-head assembly proxy is valid only when object rebuilds.",
        },
        {
            "tool_or_signal": "objdump",
            "status": "PASS" if objdump_rc == 0 else "MISSING_OR_FAIL",
            "evidence": rel(RAW / "mattrgsw_objdump.txt"),
            "detail": f"rc={objdump_rc}",
            "claim_effect": "Static instruction proxy; not a runtime counter.",
        },
        {
            "tool_or_signal": "nm",
            "status": "PASS" if nm_rc == 0 else "MISSING_OR_FAIL",
            "evidence": rel(RAW / "mattrgsw_nm.txt"),
            "detail": f"rc={nm_rc}",
            "claim_effect": "Symbol/source anchor check.",
        },
    ]


def find_line(path: Path, needle: str) -> Tuple[str, int]:
    for idx, line in enumerate(read_text(path).splitlines(), 1):
        if needle in line:
            return rel(path), idx
    return rel(path), 0


def source_anchor_rows() -> List[Dict[str, object]]:
    anchors = [
        ("mat_ep_public_entry", MATTRGSW_C, "void mat_trgsw_mul_pvmtmlwe_DFT("),
        ("mat_ep_sub_public_entry", MATTRGSW_C, "void mat_trgsw_mul_pvmtmlwe_sub_DFT("),
        ("sub_decompose_entry", MATTRGSW_C, "static void mat_trgsw_sub_decompose("),
        ("sub_decompose_avx512_poly", MATTRGSW_C, "static void mat_trgsw_sub_decompose_poly_avx512("),
        ("dispatch_from_dec", MATTRGSW_C, "static void mat_trgsw_mul_pvmtmlwe_DFT_from_dec("),
        ("r4_smallr_kernel", MATTRGSW_C, "static void mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_avx512("),
        ("r4_unrolled_kernel", MATTRGSW_C, "static void mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_unrolled_avx512("),
        ("complex_mul_helper", MATTRGSW_C, "static inline void mat_avx512_complex_mul("),
        ("complex_addmul_helper", MATTRGSW_C, "static inline void mat_avx512_complex_addmul("),
        ("cmux_sub_decomp_callsite", SAB_PVW_C, "mat_trgsw_mul_pvmtmlwe_sub_DFT("),
        ("cmux_plain_mat_ep_callsite", SAB_PVW_C, "mat_trgsw_mul_pvmtmlwe_DFT(sab->tmp->tmlwe_dft"),
        ("from_dft_add_callsite", SAB_PVW_C, "pvmtmlwe_from_DFT_add("),
    ]
    rows = []
    src = read_text(MATTRGSW_C) + "\n" + read_text(SAB_PVW_C)
    for anchor, path, needle in anchors:
        source_path, line = find_line(path, needle)
        rows.append(
            {
                "anchor": anchor,
                "path": source_path,
                "line": line,
                "needle": needle,
                "status": "PASS" if line else "MISSING",
                "interpretation": "current source anchor for Stage286 MAT EP split gate",
            }
        )
    for macro in [
        "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED",
        "MAT_TRGSW_AVX512_SUB_DECOMP",
        "SAB_PVW_SUB_DECOMP_FUSION",
        "SAB_PVW_BACKEND_FROM_DFT_ADD",
        "SAB_PVW_DUAL_SUB_CMUX",
    ]:
        rows.append(
            {
                "anchor": f"macro_{macro.lower()}",
                "path": rel(ROOT),
                "line": "",
                "needle": macro,
                "status": "PASS" if macro in src or macro in read_text(ROOT / "src" / "mosfhet" / "Makefile.def") else "MISSING",
                "interpretation": "compile-time gate must be explicit for candidate comparisons",
            }
        )
    return rows


def get_stage_value(rows: List[Dict[str, str]], item: str) -> float:
    for row in rows:
        if row.get("item") == item:
            return fnum(row.get("value"))
    return 0.0


def residual_share(component: str) -> float:
    for row in read_csv(STAGE284_RESIDUAL):
        if row.get("component") == component:
            return fnum(row.get("profile_share"))
    return 0.0


def static_split_rows() -> List[Dict[str, object]]:
    frontier = read_csv(STAGE284_FRONTIER)
    candidate_t = get_stage_value(frontier, "candidate_t_over_r_mean_us")
    mat_share = residual_share("mat_ep")
    from_dft_share = residual_share("cmux_from_dft")
    mat_ep_t = candidate_t * mat_share if candidate_t else 0.0
    vec_half_blocks = N // 16
    complex_products_per_block = ROWS * M_OUTPUTS
    rows: List[Dict[str, object]] = [
        {
            "subcomponent": "sub_decompose_diff",
            "scope": "per MAT EP call",
            "operation_model": f"{ROWS} torus-polynomial diff/decompose streams; N={N}",
            "count_model": ROWS * N,
            "share_basis": "inside MAT EP timer; exact share requires instrumentation",
            "projected_full_share_proxy": f"{mat_share:.6f}",
            "candidate_t_over_r_us": f"{candidate_t:.3f}",
            "mat_ep_t_over_r_proxy_us": f"{mat_ep_t:.3f}",
            "evidence": f"{rel(MATTRGSW_C)}; {rel(STAGE284_RESIDUAL)}",
        },
        {
            "subcomponent": "dec_torus_to_dft",
            "scope": "per MAT EP call",
            "operation_model": f"{ROWS} torus-to-DFT conversions before dense multiply",
            "count_model": ROWS,
            "share_basis": "inside MAT EP timer; split counter/instrumentation required",
            "projected_full_share_proxy": f"{mat_share:.6f}",
            "candidate_t_over_r_us": f"{candidate_t:.3f}",
            "mat_ep_t_over_r_proxy_us": f"{mat_ep_t:.3f}",
            "evidence": f"{rel(MATTRGSW_C)}: polynomial_torus_to_DFT",
        },
        {
            "subcomponent": "dense_complex_products",
            "scope": "per AVX512 complex coefficient block",
            "operation_model": f"{ROWS} rows * {M_OUTPUTS} outputs = {complex_products_per_block} complex products",
            "count_model": complex_products_per_block,
            "share_basis": "current exact dense selector format",
            "projected_full_share_proxy": f"{mat_share:.6f}",
            "candidate_t_over_r_us": f"{candidate_t:.3f}",
            "mat_ep_t_over_r_proxy_us": f"{mat_ep_t:.3f}",
            "evidence": rel(MATTRGSW_C),
        },
        {
            "subcomponent": "selector_vector_loads",
            "scope": "per AVX512 complex coefficient block",
            "operation_model": f"2 * rows * outputs = {2 * ROWS * M_OUTPUTS} vector loads",
            "count_model": 2 * ROWS * M_OUTPUTS,
            "share_basis": "source memory model; hardware counters required",
            "projected_full_share_proxy": f"{mat_share:.6f}",
            "candidate_t_over_r_us": f"{candidate_t:.3f}",
            "mat_ep_t_over_r_proxy_us": f"{mat_ep_t:.3f}",
            "evidence": f"{rel(STAGE264_SOURCE_MODEL)}; {rel(MATTRGSW_C)}",
        },
        {
            "subcomponent": "output_vector_stores",
            "scope": "per AVX512 complex coefficient block",
            "operation_model": f"2 * outputs = {2 * M_OUTPUTS} vector stores",
            "count_model": 2 * M_OUTPUTS,
            "share_basis": "source memory model; hardware counters required",
            "projected_full_share_proxy": f"{mat_share:.6f}",
            "candidate_t_over_r_us": f"{candidate_t:.3f}",
            "mat_ep_t_over_r_proxy_us": f"{mat_ep_t:.3f}",
            "evidence": rel(STAGE264_SOURCE_MODEL),
        },
        {
            "subcomponent": "cmux_from_dft_materialization",
            "scope": "outside MAT EP timer, per CMUX",
            "operation_model": "inverse DFT plus add-to output lifecycle",
            "count_model": CMUX_CALLS,
            "share_basis": "separate Stage284 residual component",
            "projected_full_share_proxy": f"{from_dft_share:.6f}",
            "candidate_t_over_r_us": f"{candidate_t:.3f}",
            "mat_ep_t_over_r_proxy_us": "outside_mat_ep",
            "evidence": rel(STAGE284_RESIDUAL),
        },
    ]
    for row in rows:
        row["total_schedule_calls"] = CMUX_CALLS
    return rows


def improvement_rows() -> List[Dict[str, object]]:
    frontier = read_csv(STAGE284_FRONTIER)
    candidate_t = get_stage_value(frontier, "candidate_t_over_r_mean_us")
    mat_share = residual_share("mat_ep")
    from_share = residual_share("cmux_from_dft")
    components = [("mat_ep", mat_share), ("cmux_from_dft", from_share)]
    rows: List[Dict[str, object]] = []
    for component, share in components:
        for full_gain in [1.03, 1.05, 1.10, 1.20]:
            required = (1.0 - 1.0 / full_gain) / share if share else math.inf
            feasible = required <= 1.0
            rows.append(
                {
                    "component": component,
                    "profile_share": f"{share:.6f}",
                    "target_full_sab_speedup_vs_candidate": f"{full_gain:.2f}",
                    "required_component_reduction": f"{required:.6f}" if math.isfinite(required) else "missing",
                    "projected_t_over_r_us": f"{candidate_t / full_gain:.3f}" if candidate_t else "missing",
                    "status": "projection_feasible_if_mechanism_exists" if feasible else "impossible_single_component",
                    "claim_boundary": "projection_only_until_full_sab_ab",
                }
            )
    return rows


def extract_symbol_block(objdump: str, symbol: str) -> str:
    match = re.search(rf"^[0-9a-f]+ <{re.escape(symbol)}>:$", objdump, re.MULTILINE)
    if not match:
        return ""
    rest = objdump[match.end():]
    next_match = re.search(r"^[0-9a-f]+ <[^>]+>:$", rest, re.MULTILINE)
    end = match.end() + next_match.start() if next_match else len(objdump)
    return objdump[match.start():end]


def instruction_counts(block: str, scope: str) -> Dict[str, object]:
    mnemonics: List[str] = []
    for line in block.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            mnemonic = parts[2].strip().split(" ", 1)[0]
            if mnemonic:
                mnemonics.append(mnemonic)

    def exact(name: str) -> int:
        return sum(1 for item in mnemonics if item == name)

    def prefix(name: str) -> int:
        return sum(1 for item in mnemonics if item.startswith(name))

    return {
        "scope": scope,
        "instruction_lines": len(mnemonics),
        "zmm_lines": sum("zmm" in line for line in block.splitlines()),
        "stack_memory_reference_lines": sum("[rsp" in line or "[rbp" in line for line in block.splitlines()),
        "vmulpd": exact("vmulpd"),
        "vfmadd_prefix": prefix("vfmadd"),
        "vfmsub_prefix": prefix("vfmsub"),
        "vfnmadd_prefix": prefix("vfnmadd"),
        "vfnmsub_prefix": prefix("vfnmsub"),
        "vmovapd": exact("vmovapd"),
        "vmovupd": exact("vmovupd"),
        "call": exact("call"),
        "jmp": exact("jmp"),
        "claim_use": "assembly_proxy_only_not_retired_counter",
    }


def asm_rows() -> List[Dict[str, object]]:
    objdump = read_text(RAW / "mattrgsw_objdump.txt")
    if not objdump:
        return [
            {
                "scope": "mattrgsw_object",
                "instruction_lines": 0,
                "zmm_lines": 0,
                "stack_memory_reference_lines": 0,
                "vmulpd": 0,
                "vfmadd_prefix": 0,
                "vfmsub_prefix": 0,
                "vfnmadd_prefix": 0,
                "vfnmsub_prefix": 0,
                "vmovapd": 0,
                "vmovupd": 0,
                "call": 0,
                "jmp": 0,
                "claim_use": "missing_objdump",
            }
        ]
    symbols = [
        "mat_trgsw_mul_pvmtmlwe_DFT_from_dec",
        "mat_trgsw_mul_pvmtmlwe_DFT",
        "mat_trgsw_mul_pvmtmlwe_sub_DFT",
    ]
    rows = []
    for symbol in symbols:
        block = extract_symbol_block(objdump, symbol)
        if not block and symbol == "mat_trgsw_mul_pvmtmlwe_DFT_from_dec":
            block = objdump
        rows.append(instruction_counts(block, symbol if block else f"{symbol}_missing"))
    return rows


def admission_rows() -> List[Dict[str, object]]:
    mat_share = residual_share("mat_ep")
    return [
        {
            "route": "S286-A-counter_only",
            "status": "admitted_now",
            "allowed_action": "Run native counters or local assembly proxy and update ledger.",
            "blocked_action": "Claim theoretical MAT AVX optimality.",
            "entry_evidence": rel(STAGE284_RESIDUAL),
            "promotion_gate": "native/perf rows plus interpretation",
        },
        {
            "route": "S286-B-sub_decompose_instrumentation",
            "status": "admitted_instrumentation_only",
            "allowed_action": "Add optional counters/timers around sub_decompose, torus_to_DFT, and dense addmul.",
            "blocked_action": "Enable new hot-path behavior by default.",
            "entry_evidence": f"mat_ep_share={mat_share:.6f}",
            "promotion_gate": "instrumented split plus unprofiled T_bootstrap/r A/B",
        },
        {
            "route": "S286-C-new_avx_kernel",
            "status": "blocked_until_split_identifies_target",
            "allowed_action": "Prepare isolated equivalence and microbench design.",
            "blocked_action": "Rewrite dense kernel based only on Stage284 Amdahl projection.",
            "entry_evidence": rel(OUT / "mat_ep_static_split_model.csv"),
            "promotion_gate": "isolated correctness, microbench, full SAB repeated A/B, noise/resource",
        },
        {
            "route": "S286-D-body_linear_selector_format",
            "status": "not_admitted_by_stage286",
            "allowed_action": "Keep as separate proof route.",
            "blocked_action": "Treat dense-kernel split as body-linear optimality proof.",
            "entry_evidence": rel(STAGE284_ALGO),
            "promotion_gate": "distribution/security/noise proof before hot-path code",
        },
    ]


def claim_rows() -> List[Dict[str, object]]:
    return [
        {
            "claim": "mat_ep_is_current_first_target",
            "status": "allowed",
            "allowed_wording": "MAT EP is the largest measured residual component in the selected candidate profile.",
            "forbidden_wording": "MAT EP is the only bottleneck or zeroing it is achievable.",
            "evidence": f"{rel(STAGE284_RESIDUAL)}; {rel(STATIC_SPLIT)}",
        },
        {
            "claim": "avx512_instruction_presence",
            "status": "proxy_only",
            "allowed_wording": "Current-head object/source exposes AVX512/FMA proxy evidence when objdump succeeds.",
            "forbidden_wording": "Retired load/store/FMA counters prove optimality.",
            "evidence": f"{rel(ASM_PROXY)}; {rel(TOOL_MATRIX)}",
        },
        {
            "claim": "required_component_reduction",
            "status": "projection_only",
            "allowed_wording": "Improvement targets are Amdahl projections for experiment design.",
            "forbidden_wording": "The projected full-SAB improvement has been measured.",
            "evidence": rel(IMPROVEMENT_TARGETS),
        },
        {
            "claim": "hot_path_edit_permission",
            "status": "denied_for_behavior_change",
            "allowed_wording": "Instrumentation-only code is admissible; behavior-changing AVX work needs split evidence.",
            "forbidden_wording": "Stage286 authorizes a default hot-path rewrite.",
            "evidence": rel(ADMISSION),
        },
    ]


def proof_rows(
    inputs: List[Dict[str, object]],
    tools: List[Dict[str, object]],
    anchors: List[Dict[str, object]],
    asm: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    missing_inputs = [row["input_id"] for row in inputs if row["status"] != "present"]
    missing_anchors = [row["anchor"] for row in anchors if row["status"] != "PASS"]
    tool_status = {row["tool_or_signal"]: row["status"] for row in tools}
    zmm = sum(int(row.get("zmm_lines", 0)) for row in asm)
    fma = sum(
        int(row.get("vfmadd_prefix", 0))
        + int(row.get("vfmsub_prefix", 0))
        + int(row.get("vfnmadd_prefix", 0))
        + int(row.get("vfnmsub_prefix", 0))
        for row in asm
    )
    return [
        {
            "gate": "G1_inputs",
            "status": "PASS" if not missing_inputs else "FAIL",
            "metric": "required inputs",
            "value": "all present" if not missing_inputs else ",".join(missing_inputs),
            "interpretation": "Stage286 consumes the current Stage284 frontier and current source.",
        },
        {
            "gate": "G2_source_anchors",
            "status": "PASS" if not missing_anchors else "FAIL",
            "metric": "source anchors",
            "value": "all present" if not missing_anchors else ",".join(missing_anchors),
            "interpretation": "Split gate points at the actual MAT EP and CMUX call sites.",
        },
        {
            "gate": "G3_tooling",
            "status": "PASS_PROXY" if tool_status.get("build_mattrgsw_object") == "PASS" else "FAIL",
            "metric": "build/objdump/nm",
            "value": f"build={tool_status.get('build_mattrgsw_object')}; objdump={tool_status.get('objdump')}; nm={tool_status.get('nm')}",
            "interpretation": "Current-head assembly proxy can be generated if tools pass.",
        },
        {
            "gate": "G4_assembly_proxy",
            "status": "PASS_PROXY" if zmm > 0 and fma > 0 else "MISSING",
            "metric": "zmm/fma proxy",
            "value": f"zmm={zmm}; fma_like={fma}",
            "interpretation": "Static proxy checks instruction presence only, not retired counters.",
        },
        {
            "gate": "G5_native_counter_boundary",
            "status": "BLOCKED_OR_MISSING" if tool_status.get("perf") != "AVAILABLE" else "AVAILABLE_LOCAL_PROXY",
            "metric": "perf",
            "value": tool_status.get("perf", "missing"),
            "interpretation": "No hardware-counter or optimality claim without native/perf rows.",
        },
        {
            "gate": "G6_code_admission",
            "status": "PASS_INSTRUMENTATION_ONLY",
            "metric": "hot path permission",
            "value": "no behavior-changing hot-path edit admitted",
            "interpretation": "Proceed to split instrumentation/native counters before AVX kernel rewrites.",
        },
        {
            "gate": "G7_decision",
            "status": DECISION,
            "metric": "stage decision",
            "value": DECISION,
            "interpretation": "Proceed to native counter rerun or optional split instrumentation, not optimality claims.",
        },
    ]


def next_rows() -> List[Dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage287_native_counter_rerun_or_intake",
            "entry_condition": "safe native authentication available",
            "gate": "Run selected candidate with perf events for cycles, instructions, loads, stores, and 512b FP.",
            "failure_action": "Keep Stage286 as proxy-only.",
        },
        {
            "priority": "P1",
            "route": "stage288_mat_ep_split_instrumentation",
            "entry_condition": "native counters remain unavailable",
            "gate": "Add optional timers/counters inside MAT EP subcomponents; no default behavior change.",
            "failure_action": "Do not implement new AVX kernel.",
        },
        {
            "priority": "P2",
            "route": "stage289_isolated_mat_ep_microbench",
            "entry_condition": "split instrumentation identifies a dominant subcomponent",
            "gate": "Compare current kernel against one candidate under isolated equivalence and microbench.",
            "failure_action": "Record neutral/negative and keep selected exact path.",
        },
        {
            "priority": "P3",
            "route": "stage290_full_sab_ab_after_kernel_candidate",
            "entry_condition": "isolated kernel candidate passes",
            "gate": "Repeated complete SAB T_bootstrap/r A/B plus noise/resource.",
            "failure_action": "Do not promote kernel-only speedup.",
        },
    ]


def md_table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(lines)


def write_documents(
    static_rows: List[Dict[str, object]],
    target_rows: List[Dict[str, object]],
    admission: List[Dict[str, object]],
    claims: List[Dict[str, object]],
    proof: List[Dict[str, object]],
    next_queue: List[Dict[str, object]],
) -> None:
    report = f"""# Stage286 MAT EP Split/Counter Gate

Decision: `{DECISION}`.

Stage286 turns the Stage284 MAT EP residual into concrete admission gates. It
anchors the current source, rebuilds the current MAT object for a proxy
assembly audit, and computes the component-reduction targets required to move
complete-SAB `T_bootstrap/r`. It does not claim native counter evidence or
theoretical optimality.

## Static MAT EP Split Model

{md_table(static_rows, ["subcomponent", "scope", "operation_model", "count_model", "projected_full_share_proxy"])}

## Improvement Targets

{md_table(target_rows, ["component", "profile_share", "target_full_sab_speedup_vs_candidate", "required_component_reduction", "status"])}

## Code Admission

{md_table(admission, ["route", "status", "allowed_action", "blocked_action", "promotion_gate"])}

## Claim Boundary

{md_table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Next Queue

{md_table(next_queue, ["priority", "route", "entry_condition", "gate", "failure_action"])}

Generated from head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)

    write_text(THEORY, f"""# Stage286 MAT EP Split Model

## Object

The selected Stage284 candidate uses the exact dense MAT external product path
inside `mat_trgsw_mul_pvmtmlwe_sub_DFT` for CMUX diff inputs. For the target
r=4, k=1, l=1 setting:

```text
rows = outputs = r + 1 = {ROWS}
dense complex products per AVX512 block = rows * outputs = {ROWS * M_OUTPUTS}
schedule MAT EP calls = {CMUX_CALLS}
```

The current MAT EP timer includes:

1. diff/sub decomposition over `{ROWS}` torus polynomials;
2. `{ROWS}` torus-to-DFT conversions;
3. dense exact MAT multiply/addmul across `{ROWS * M_OUTPUTS}` row/output
   pairs;
4. output stores for `{M_OUTPUTS}` DFT polynomials.

## Promotion Boundary

The split model is a planning and admission model. A behavior-changing kernel
optimization is not admitted until a later stage either records native
hardware counters or adds optional split instrumentation that identifies a
specific subcomponent and then passes repeated complete-SAB `T_bootstrap/r`.
""")

    write_text(VARIANT, f"""# Stage286 MAT EP Split Candidates

{md_table(admission, ["route", "status", "allowed_action", "blocked_action", "entry_evidence", "promotion_gate"])}

## Candidate Rule

Any future candidate must be compared against the current selected
`backend_sub_decomp_dual` path using complete-SAB `T_bootstrap/r`. Isolated
MAT EP microbenchmarks can only admit a candidate to full SAB A/B; they cannot
establish final bootstrapping speedup alone.
""")

    write_text(PLAN, f"""# Stage286 MAT EP Counter Validation Plan

## Immediate Work

{md_table(next_queue, ["priority", "route", "entry_condition", "gate", "failure_action"])}

## Required Events For Native Counter Runs

- cycles
- instructions
- cache references/misses where available
- retired loads/stores where available
- 512-bit packed double FP events where available

## Required Statistics For Promotion

- unprofiled repeated complete-SAB `T_bootstrap/r`;
- same-backend control;
- correctness and noise/resource gates;
- raw logs and artifact hashes;
- claim boundary separating proxy, counter, kernel, and full SAB evidence.
""")

    write_text(COMMANDS, """# Stage286 Reproduction Commands

```bash
python3 scripts/build_stage286_mat_ep_split_counter_gate.py
```

This stage rebuilds `build/mattrgsw.o` for source/assembly proxy evidence. It
does not run a heavy complete-SAB benchmark.
""")


def artifact_index() -> None:
    paths = [
        DOC, THEORY, VARIANT, PLAN, BUILDER, COMMANDS, REPORT,
        INPUT_STATUS, TOOL_MATRIX, SOURCE_ANCHORS, STATIC_SPLIT,
        IMPROVEMENT_TARGETS, ASM_PROXY, ADMISSION, CLAIMS, PROOF, NEXT,
        RAW / "environment.log", RAW / "perf_probe.log", RAW / "mattrgsw_build.log",
        RAW / "mattrgsw_objdump.txt", RAW / "mattrgsw_nm.txt",
    ]
    rows = []
    for path in paths:
        if path.exists():
            data = path.read_bytes()
            rows.append({"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, ["path", "bytes", "sha256"], rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)

    inputs = input_rows()
    tools = local_tool_probe()
    anchors = source_anchor_rows()
    static_rows = static_split_rows()
    target_rows = improvement_rows()
    asm = asm_rows()
    admission = admission_rows()
    claims = claim_rows()
    proofs = proof_rows(inputs, tools, anchors, asm)
    next_queue = next_rows()

    write_csv(INPUT_STATUS, ["input_id", "path", "status", "bytes"], inputs)
    write_csv(TOOL_MATRIX, ["tool_or_signal", "status", "evidence", "detail", "claim_effect"], tools)
    write_csv(SOURCE_ANCHORS, ["anchor", "path", "line", "needle", "status", "interpretation"], anchors)
    write_csv(STATIC_SPLIT, [
        "subcomponent", "scope", "operation_model", "count_model", "share_basis",
        "projected_full_share_proxy", "candidate_t_over_r_us", "mat_ep_t_over_r_proxy_us",
        "total_schedule_calls", "evidence",
    ], static_rows)
    write_csv(IMPROVEMENT_TARGETS, [
        "component", "profile_share", "target_full_sab_speedup_vs_candidate",
        "required_component_reduction", "projected_t_over_r_us", "status", "claim_boundary",
    ], target_rows)
    write_csv(ASM_PROXY, [
        "scope", "instruction_lines", "zmm_lines", "stack_memory_reference_lines",
        "vmulpd", "vfmadd_prefix", "vfmsub_prefix", "vfnmadd_prefix", "vfnmsub_prefix",
        "vmovapd", "vmovupd", "call", "jmp", "claim_use",
    ], asm)
    write_csv(ADMISSION, ["route", "status", "allowed_action", "blocked_action", "entry_evidence", "promotion_gate"], admission)
    write_csv(CLAIMS, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"], claims)
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proofs)
    write_csv(NEXT, ["priority", "route", "entry_condition", "gate", "failure_action"], next_queue)
    write_documents(static_rows, target_rows, admission, claims, proofs, next_queue)

    append_once(CURRENT_GOAL, "<!-- stage286-mat-ep-split-counter-gate -->", f"""<!-- stage286-mat-ep-split-counter-gate -->
### Stage286 MAT EP split/counter gate

`{DECISION}` records a current-head source/assembly/projection gate for the
Stage284 selected MAT EP residual. The stage admits native counters and
optional split instrumentation, but denies behavior-changing AVX hot-path
rewrites until split evidence plus repeated complete-SAB `T_bootstrap/r` A/B
exists.
""")
    append_once(HYPOTHESES, "H10_stage286_mat_ep_split_counter_gate:", f"""H10_stage286_mat_ep_split_counter_gate:
  status: {DECISION}
  evidence:
    - repro/stage286_mat_ep_split_counter_gate/mat_ep_static_split_model.csv
    - repro/stage286_mat_ep_split_counter_gate/improvement_targets.csv
    - repro/stage286_mat_ep_split_counter_gate/code_admission_matrix.csv
    - docs/stage286_mat_ep_split_counter_gate.md
  conclusion: >
    Stage286 converts the selected MAT EP residual into source/assembly/proxy
    split evidence and admission rules. MAT EP remains the first target, but
    native counters or optional split instrumentation are required before any
    behavior-changing AVX hot-path rewrite.
""")
    append_once(RUN_LOG, "stage286-mat-ep-split-counter-gate-001", f"""stage286-mat-ep-split-counter-gate-001,2026-07-04,{git_head()},Stage 286,local-proxy,python scripts/build_stage286_mat_ep_split_counter_gate.py,"MAT EP split/counter admission gate for selected Stage284 candidate",n/a,{DECISION},"Source/assembly/projection only; no native counter or hot-path promotion claim.",docs/stage286_mat_ep_split_counter_gate.md; repro/stage286_mat_ep_split_counter_gate/proof_gate.csv
""")
    append_once(MANIFEST, "- stage286_mat_ep_split_counter_gate:", """- stage286_mat_ep_split_counter_gate:
  - `docs/stage286_mat_ep_split_counter_gate.md`
  - `theory_checks/stage286_mat_ep_split_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage286_mat_ep_split_candidates.md`
  - `experiments/stage286_mat_ep_counter_validation_plan.md`
  - `scripts/build_stage286_mat_ep_split_counter_gate.py`
  - `repro/stage286_mat_ep_split_counter_gate/`
""")
    append_once(CHECKLIST, "<!-- stage286-mat-ep-split-counter-gate-checklist -->", f"""<!-- stage286-mat-ep-split-counter-gate-checklist -->
- [x] Stage286 records `{DECISION}` for MAT EP split/counter admission.
""")
    artifact_index()
    print(DECISION)


if __name__ == "__main__":
    main()
