#!/usr/bin/env python3
"""Build Stage264 MAT-AVX512 counter/assembly preflight artifacts."""

from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage264_mat_avx512_counter_preflight"
RAW = REPRO / "raw"
DOC = ROOT / "docs" / "stage264_mat_avx512_counter_preflight.md"
SRC = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="\n", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def markdown_table(rows: list[dict[str, str]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |"]
    out.append("| " + " | ".join("---" for _ in fields) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def parse_key_values(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def source_model_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for r in (2, 4):
        m = r + 1
        repeated_scalar_products = 4 * r
        dense_mat_products = m * m
        generic_vector_ops = 8 * m * m - 2 * m
        mat_aware_vector_ops = 2 * m * m + 4 * m
        dec_loads = 2 * m
        selector_loads = 2 * m * m
        output_stores = 2 * m
        output_loads = 0
        vmulpd_like = 2 * m
        fma_like = 2 * m + 4 * (m - 1) * m
        rows.append(
            {
                "scope": "k=1,l=1,one_avx512_complex_coeff_block",
                "r": str(r),
                "m_rows_outputs": str(m),
                "repeated_scalar_complex_products": str(repeated_scalar_products),
                "dense_mat_complex_products": str(dense_mat_products),
                "dense_mat_over_repeated_scalar": f"{dense_mat_products / repeated_scalar_products:.6f}",
                "generic_vector_memory_ops": str(generic_vector_ops),
                "mat_aware_vector_memory_ops": str(mat_aware_vector_ops),
                "predicted_memory_op_reduction": f"{generic_vector_ops / mat_aware_vector_ops:.6f}",
                "mat_aware_dec_vector_loads": str(dec_loads),
                "mat_aware_selector_vector_loads": str(selector_loads),
                "mat_aware_output_vector_stores": str(output_stores),
                "mat_aware_output_vector_loads": str(output_loads),
                "source_model_vmulpd_like_ops": str(vmulpd_like),
                "source_model_fma_like_ops": str(fma_like),
                "interpretation": (
                    "r=4 keeps a larger memory-op reduction but also has 25 dense MAT complex products versus 16 scalar-repeated products"
                    if r == 4
                    else "r=2 is the easiest register-resident small-r case"
                ),
            }
        )
    return rows


def extract_symbol_block(objdump: str, symbol: str) -> str:
    marker = re.compile(rf"^[0-9a-f]+ <{re.escape(symbol)}>:$", re.MULTILINE)
    match = marker.search(objdump)
    if not match:
        return ""
    start = match.start()
    next_symbol = re.search(r"^[0-9a-f]+ <[^>]+>:$", objdump[match.end() :], re.MULTILINE)
    if not next_symbol:
        return objdump[start:]
    return objdump[start : match.end() + next_symbol.start()]


def instruction_counts(block: str, scope: str) -> dict[str, str]:
    mnemonics: list[str] = []
    for line in block.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            mnemonic = parts[2].strip().split(" ", 1)[0]
            if mnemonic:
                mnemonics.append(mnemonic)
    def count_exact(name: str) -> int:
        return sum(1 for item in mnemonics if item == name)

    def count_prefix(prefix: str) -> int:
        return sum(1 for item in mnemonics if item.startswith(prefix))

    return {
        "scope": scope,
        "instruction_lines": str(len(mnemonics)),
        "zmm_lines": str(sum("zmm" in line for line in block.splitlines())),
        "ymm_lines": str(sum("ymm" in line for line in block.splitlines())),
        "xmm_lines": str(sum("xmm" in line for line in block.splitlines())),
        "stack_memory_reference_lines": str(sum("[rsp" in line or "[rbp" in line for line in block.splitlines())),
        "vmulpd": str(count_exact("vmulpd")),
        "vfmadd_prefix": str(count_prefix("vfmadd")),
        "vfmsub_prefix": str(count_prefix("vfmsub")),
        "vfnmadd_prefix": str(count_prefix("vfnmadd")),
        "vfnmsub_prefix": str(count_prefix("vfnmsub")),
        "vmovapd": str(count_exact("vmovapd")),
        "vmovupd": str(count_exact("vmovupd")),
        "call": str(count_exact("call")),
        "jmp": str(count_exact("jmp")),
        "note": "objdump proxy; static small-r helpers may be inlined into dispatch",
    }


def tool_rows() -> list[dict[str, str]]:
    env = parse_key_values(read_text(RAW / "environment.log"))
    tool = parse_key_values(read_text(RAW / "tool_probe.log"))
    perf_probe = read_text(RAW / "perf_probe.log")
    perf_available = bool(env.get("perf_path"))
    avx512 = "avx512f" in env.get("cpu_flags", "")
    rows = [
        {
            "tool_or_signal": "cpu_avx512_flags",
            "status": "PASS_AVX512_EXPOSED" if avx512 else "MISSING_AVX512",
            "evidence": "raw/environment.log",
            "detail": env.get("cpu_model", ""),
            "claim_effect": "AVX512 code paths can be built/run, but this is not a performance-counter claim.",
        },
        {
            "tool_or_signal": "perf",
            "status": "AVAILABLE" if perf_available else "MISSING",
            "evidence": "raw/perf_probe.log",
            "detail": perf_probe.replace("\n", " ")[:240],
            "claim_effect": "Hardware-counter-backed MAT-AVX512 optimality remains blocked if perf is missing.",
        },
        {
            "tool_or_signal": "perf_event_paranoid",
            "status": "RECORDED",
            "evidence": "raw/environment.log",
            "detail": env.get("perf_event_paranoid", ""),
            "claim_effect": "Permission context only; perf is absent in this WSL probe.",
        },
        {
            "tool_or_signal": "objdump",
            "status": "AVAILABLE" if tool.get("objdump_path") else "MISSING",
            "evidence": "raw/tool_probe.log; raw/mattrgsw_objdump.log",
            "detail": tool.get("objdump_path", ""),
            "claim_effect": "Assembly proxy can check expected AVX512/FMA presence, not retired counters.",
        },
        {
            "tool_or_signal": "nm",
            "status": "AVAILABLE" if tool.get("nm_path") else "MISSING",
            "evidence": "raw/tool_probe.log; raw/mattrgsw_nm.log",
            "detail": tool.get("nm_path", ""),
            "claim_effect": "Symbol-level dispatch audit available.",
        },
        {
            "tool_or_signal": "build/mattrgsw.o",
            "status": "PRESENT" if tool.get("mattrgsw_o") == "present" else "MISSING",
            "evidence": "raw/tool_probe.log",
            "detail": tool.get("mattrgsw_o", ""),
            "claim_effect": "Object-level proxy audit can be built from current artifact.",
        },
    ]
    return rows


def symbol_rows(nm_text: str, src_text: str) -> list[dict[str, str]]:
    checks = [
        ("public_mat_ep_entry", "mat_trgsw_mul_pvmtmlwe_DFT", "nm"),
        ("dispatch_from_dec", "mat_trgsw_mul_pvmtmlwe_DFT_from_dec", "nm"),
        ("generic_poly_mul_ref", "polynomial_mul_DFT", "nm"),
        ("generic_poly_addmul_ref", "polynomial_mul_addto_DFT", "nm"),
        ("r2_smallr_source", "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r2_avx512", "source"),
        ("r4_smallr_source", "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_avx512", "source"),
        ("r4_unrolled_experimental_source", "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_unrolled_avx512", "source"),
        ("smallr_dispatch_macro", "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED", "source"),
        ("r4_unrolled_flag", "MAT_TRGSW_AVX512_R4_UNROLLED_ROWS", "source"),
    ]
    rows: list[dict[str, str]] = []
    for check, pattern, source in checks:
        haystack = src_text if source == "source" else nm_text
        rows.append(
            {
                "check": check,
                "pattern": pattern,
                "source": source,
                "status": "PASS" if pattern in haystack else "MISSING",
                "interpretation": (
                    "r=2/r=4 source specializations are present; object symbols may be inlined"
                    if "smallr" in check or "r2_" in check or "r4_" in check
                    else "entry/symbol reference found"
                ),
            }
        )
    return rows


def proof_rows(
    tools: list[dict[str, str]],
    symbols: list[dict[str, str]],
    model: list[dict[str, str]],
    asm: list[dict[str, str]],
) -> list[dict[str, str]]:
    by_tool = {row["tool_or_signal"]: row for row in tools}
    all_symbols = all(row["status"] == "PASS" for row in symbols)
    avx_proxy = any(int(row.get("zmm_lines", "0")) > 0 for row in asm) and any(
        int(row.get("vfmadd_prefix", "0")) + int(row.get("vfmsub_prefix", "0")) > 0
        for row in asm
    )
    reductions = [float(row["predicted_memory_op_reduction"]) for row in model]
    dense_ratios = [float(row["dense_mat_over_repeated_scalar"]) for row in model]
    perf_missing = by_tool.get("perf", {}).get("status") == "MISSING"
    decision = (
        "PASS_STAGE264_MAT_AVX512_COUNTER_PREFLIGHT_PROXY_ONLY"
        if all_symbols
        and avx_proxy
        and min(reductions) > 2.0
        and max(dense_ratios) > 1.5
        and perf_missing
        else "REVIEW_STAGE264_MAT_AVX512_COUNTER_PREFLIGHT"
    )
    return [
        {
            "gate": "G1_tooling",
            "status": "PASS_PROXY_TOOLS" if by_tool.get("objdump", {}).get("status") == "AVAILABLE" else "FAIL",
            "metric": "objdump/nm availability",
            "value": f"objdump={by_tool.get('objdump', {}).get('status','')}; nm={by_tool.get('nm', {}).get('status','')}",
            "evidence": "tool_matrix.csv",
            "interpretation": "Object-level assembly proxy can be generated.",
        },
        {
            "gate": "G2_native_perf",
            "status": "BLOCKED_PERF_MISSING" if perf_missing else "REVIEW_PERF_AVAILABLE",
            "metric": "perf counter availability",
            "value": by_tool.get("perf", {}).get("detail", ""),
            "evidence": "raw/perf_probe.log",
            "interpretation": "No retired load/store/FMA counter claim is allowed from this environment.",
        },
        {
            "gate": "G3_source_memory_model",
            "status": "PASS",
            "metric": "predicted MAT-aware memory-op reduction",
            "value": f"{min(reductions):.3f}x..{max(reductions):.3f}x",
            "evidence": "source_model.csv",
            "interpretation": "The memory model supports the MAT-aware AVX hypothesis while also exposing dense r=4 arithmetic cost.",
        },
        {
            "gate": "G4_assembly_proxy",
            "status": "PASS_AVX512_FMA_PROXY" if avx_proxy else "FAIL",
            "metric": "zmm/FMA mnemonics in dispatch object",
            "value": ";".join(f"{row['scope']}:zmm={row['zmm_lines']},fma={int(row['vfmadd_prefix']) + int(row['vfmsub_prefix'])}" for row in asm),
            "evidence": "instruction_proxy.csv; raw/mattrgsw_objdump.log",
            "interpretation": "Expected AVX512/FMA instructions are present, but this is not a retired-counter or optimality proof.",
        },
        {
            "gate": "G5_symbol_source_guard",
            "status": "PASS" if all_symbols else "FAIL",
            "metric": "small-r source and dispatch presence",
            "value": f"{sum(row['status'] == 'PASS' for row in symbols)}/{len(symbols)}",
            "evidence": "symbol_matrix.csv",
            "interpretation": "Stage264 audits the intended MAT external-product implementation, not an unrelated object.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "evidence": "proof_gate.csv",
            "interpretation": "Proceed to native perf if available; otherwise use this as a claim guard and move to full-SAB A/B only for concrete variants.",
        },
    ]


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    nm_text = read_text(RAW / "mattrgsw_nm.log")
    objdump = read_text(RAW / "mattrgsw_objdump.log")
    src_text = read_text(SRC)

    model = source_model_rows()
    tools = tool_rows()
    symbols = symbol_rows(nm_text, src_text)
    from_dec = extract_symbol_block(objdump, "mat_trgsw_mul_pvmtmlwe_DFT_from_dec")
    public_entry = extract_symbol_block(objdump, "mat_trgsw_mul_pvmtmlwe_DFT")
    asm = [
        instruction_counts(from_dec, "mat_trgsw_mul_pvmtmlwe_DFT_from_dec_whole_dispatch_proxy"),
        instruction_counts(public_entry, "mat_trgsw_mul_pvmtmlwe_DFT_public_entry_proxy"),
    ]
    proof = proof_rows(tools, symbols, model, asm)
    decision = proof[-1]["status"]

    write_csv(
        REPRO / "source_model.csv",
        model,
        [
            "scope",
            "r",
            "m_rows_outputs",
            "repeated_scalar_complex_products",
            "dense_mat_complex_products",
            "dense_mat_over_repeated_scalar",
            "generic_vector_memory_ops",
            "mat_aware_vector_memory_ops",
            "predicted_memory_op_reduction",
            "mat_aware_dec_vector_loads",
            "mat_aware_selector_vector_loads",
            "mat_aware_output_vector_stores",
            "mat_aware_output_vector_loads",
            "source_model_vmulpd_like_ops",
            "source_model_fma_like_ops",
            "interpretation",
        ],
    )
    write_csv(REPRO / "tool_matrix.csv", tools, ["tool_or_signal", "status", "evidence", "detail", "claim_effect"])
    write_csv(REPRO / "symbol_matrix.csv", symbols, ["check", "pattern", "source", "status", "interpretation"])
    write_csv(
        REPRO / "instruction_proxy.csv",
        asm,
        [
            "scope",
            "instruction_lines",
            "zmm_lines",
            "ymm_lines",
            "xmm_lines",
            "stack_memory_reference_lines",
            "vmulpd",
            "vfmadd_prefix",
            "vfmsub_prefix",
            "vfnmadd_prefix",
            "vfnmsub_prefix",
            "vmovapd",
            "vmovupd",
            "call",
            "jmp",
            "note",
        ],
    )
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])

    claim_rows = [
        {
            "claim": "mat_aware_avx512_memory_model",
            "status": "supported_theory_model",
            "allowed_wording": "For k=1,l=1,r=2/4, MAT-aware AVX512 register accumulation has a source-level memory-op advantage over a generic single-poly style loop.",
            "forbidden_wording": "The current MAT-AVX512 kernel has reached the theoretical optimum.",
            "evidence": "source_model.csv; theory_checks/mat_avx_memory_model.md",
        },
        {
            "claim": "assembly_proxy_presence",
            "status": "supported_proxy",
            "allowed_wording": "The current object contains AVX512/FMA instructions in the audited MAT external-product dispatch region.",
            "forbidden_wording": "Objdump proxy proves retired load/store behavior or absence of spills.",
            "evidence": "instruction_proxy.csv; raw/mattrgsw_objdump.log",
        },
        {
            "claim": "native_counter_attribution",
            "status": "blocked_perf_missing",
            "allowed_wording": "Native/perf-backed MAT-AVX512 attribution remains blocked in this WSL probe because perf is missing.",
            "forbidden_wording": "Stage264 provides hardware-counter-backed load/store/FMA attribution.",
            "evidence": "raw/perf_probe.log; tool_matrix.csv",
        },
        {
            "claim": "complete_sab_speedup",
            "status": "not_measured_in_stage264",
            "allowed_wording": "Stage264 only constrains kernel-audit claims; complete SAB T_bootstrap/r speedups still come from Stage262/263 and future A/B runs.",
            "forbidden_wording": "Stage264 itself improves or proves complete SAB acceleration.",
            "evidence": "docs/stage262_nonbinary_target_repeated_stats.md; docs/stage263_nonbinary_profile_attribution.md",
        },
    ]
    write_csv(
        REPRO / "claim_boundary.csv",
        claim_rows,
        ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"],
    )

    commands = """# Stage264 Reproduction Commands

Current local route, from repository root:

```powershell
New-Item -ItemType Directory -Force repro/stage264_mat_avx512_counter_preflight/raw
# In WSL/Linux from the same repository:
nm -C build/mattrgsw.o > repro/stage264_mat_avx512_counter_preflight/raw/mattrgsw_nm.log 2>&1
objdump -d -M intel build/mattrgsw.o > repro/stage264_mat_avx512_counter_preflight/raw/mattrgsw_objdump.log 2>&1
perf stat -e cycles,instructions,cache-references,cache-misses,branches,branch-misses -- true > repro/stage264_mat_avx512_counter_preflight/raw/perf_probe.log 2>&1
python3 scripts/build_stage264_mat_avx512_counter_preflight.py
```

If `perf` is unavailable, keep the result as proxy-only. Do not use this stage
to upgrade MAT-AVX512 theoretical-optimality wording.
"""
    write_text_lf(REPRO / "reproduction_commands.md", commands)

    report = f"""# Stage264 MAT-AVX512 Counter/Assembly Preflight

Decision: `{decision}`.

Stage264 answers a narrow question: whether the current MAT external-product
AVX512 path can be treated as theoretically optimal. It cannot. The source
model supports the MAT-aware memory-traffic hypothesis, and the object-level
proxy confirms AVX512/FMA instructions are present, but WSL lacks `perf`, so no
retired load/store/FMA attribution is available.

## Tool Matrix

{markdown_table(tools, ["tool_or_signal", "status", "detail", "claim_effect"])}

## Source-Level Model

{markdown_table(model, ["r", "m_rows_outputs", "repeated_scalar_complex_products", "dense_mat_complex_products", "dense_mat_over_repeated_scalar", "generic_vector_memory_ops", "mat_aware_vector_memory_ops", "predicted_memory_op_reduction", "source_model_vmulpd_like_ops", "source_model_fma_like_ops"])}

## Assembly Proxy

{markdown_table(asm, ["scope", "instruction_lines", "zmm_lines", "stack_memory_reference_lines", "vmulpd", "vfmadd_prefix", "vfmsub_prefix", "vmovapd", "vmovupd", "note"])}

## Symbol / Source Guard

{markdown_table(symbols, ["check", "source", "status", "interpretation"])}

## Interpretation

- The MAT-aware model predicts fewer vector memory operations than a generic
  single-poly style MAT loop: `2.200x` fewer at r=2 and `2.714x` fewer at r=4.
- That model does not make r=4 arithmetically cheap: dense MAT uses `25`
  complex products versus `16` repeated scalar products at the same simplified
  k=1,l=1 shape.
- The current object contains AVX512/FMA proxy evidence in the MAT dispatch
  region, but the static proxy cannot count retired loads/stores or prove that
  register pressure and spills are optimal.
- Therefore Stage264 is a guard against overclaiming. It narrows the next
  action to either a native perf run or a concrete code variant followed by
  full SAB `T_bootstrap/r` A/B.

## Proof Gate

{markdown_table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{markdown_table(claim_rows, ["claim", "status", "allowed_wording", "forbidden_wording"])}

Generated from input head `{git_head()}`.
"""
    write_text_lf(REPRO / "stage264_report.md", report)
    write_text_lf(DOC, report)

    artifacts: list[dict[str, str]] = []
    for path in sorted(REPRO.glob("*")) + sorted(RAW.glob("*")):
        if path.is_file():
            artifacts.append({"path": rel(path), "bytes": str(path.stat().st_size)})
    artifacts.append({"path": rel(DOC), "bytes": str(DOC.stat().st_size)})
    write_csv(REPRO / "artifact_index.csv", artifacts, ["path", "bytes"])

    print(decision)
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
