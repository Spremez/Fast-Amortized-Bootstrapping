#!/usr/bin/env python3
"""Stage161: post-fusion MAT EP attribution gate."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage161_post_fusion_attribution"

SUMMARY_CSV = OUT_DIR / "summary.csv"
RUN_METRICS_CSV = OUT_DIR / "run_metrics.csv"
PERF_STATUS_CSV = OUT_DIR / "perf_status.csv"
INSTRUCTION_CSV = OUT_DIR / "instruction_counts.csv"
SOURCE_MAP_CSV = OUT_DIR / "source_kernel_map.csv"
STAGE160_LINK_CSV = OUT_DIR / "stage160_linkage.csv"
HISTORICAL_COUNTER_CSV = OUT_DIR / "historical_native_counter_reference.csv"
NEXT_QUEUE_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage161_post_fusion_attribution.md"
PLAN_MD = ROOT / "experiments" / "stage161_post_fusion_attribution_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage161_post_fusion_attribution_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_post_fusion_attribution.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE160_PROFILE = ROOT / "repro" / "stage160_post_fusion_frontier" / "profile_sample.csv"
STAGE160_COMPONENT = ROOT / "repro" / "stage160_post_fusion_frontier" / "component_shares.csv"
STAGE101_COUNTERS = ROOT / "repro" / "stage101_cb5_remote_native_perf" / "counter_metrics.csv"

R_VALUE = int(os.environ.get("STAGE161_R", "6"))
BENCH_REPS = int(os.environ.get("STAGE161_BENCH_REPS", "1"))
MAKE_JOBS = os.environ.get("STAGE161_JOBS", "$(nproc)")

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
    "SAB_PVW_SUB_DECOMP_FUSION=true "
    f"SAB_PVW_BENCH=true SAB_PVW_BENCH_R={R_VALUE} "
    f"SAB_PVW_BENCH_REPS={BENCH_REPS}"
)

PERF_EVENTS = (
    "cycles,instructions,cache-references,cache-misses,branches,branch-misses,"
    "mem_inst_retired.all_loads,mem_inst_retired.all_stores,"
    "fp_arith_inst_retired.512b_packed_double,"
    "fp_arith_inst_retired.256b_packed_double"
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    clean = "".join(ch if ch in "\n\t" or 32 <= ord(ch) < 127 else "?" for ch in text)
    return "\n".join(line.rstrip() for line in clean.splitlines()).rstrip() + "\n"


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
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
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def wsl_repo() -> str:
    drive = ROOT.drive.rstrip(":").lower()
    rest = ROOT.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


def run_wsl(command: str, log: Path, timeout: int = 1800) -> int:
    bash_cmd = f"cd {wsl_repo()} && {command}"
    print(f"[stage161] {command}", flush=True)
    proc = subprocess.run(
        ["wsl", "bash", "-lc", bash_cmd],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    output = proc.stdout.decode("utf-8", errors="ignore")
    write_text_lf(log, sanitize("\n".join([
        f"command: {command}",
        f"returncode: {proc.returncode}",
        "--- output ---",
        output,
    ])))
    return proc.returncode


def extract_fields(line: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for token in line.split():
        if "=" in token:
            key, value = token.split("=", 1)
            fields[key] = value.rstrip("x")
    return fields


def find_last_line(path: Path, marker: str) -> str:
    found = ""
    if not path.exists():
        return found
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if marker in line:
            found = line
    return found


def detect_perf() -> Dict[str, str]:
    probe_log = OUT_DIR / "perf_probe.log"
    rc = run_wsl(
        "if command -v perf >/dev/null 2>&1; then command -v perf; perf stat true; else echo PERF_MISSING; fi",
        probe_log,
        timeout=60,
    )
    text = probe_log.read_text(encoding="utf-8", errors="replace")
    if "PERF_MISSING" in text or "command not found" in text:
        return {
            "perf_available": "false",
            "perf_probe_rc": str(rc),
            "perf_status": "missing",
            "perf_detail": "perf not found in WSL",
            "source_log": rel(probe_log),
        }
    if rc == 0:
        return {
            "perf_available": "true",
            "perf_probe_rc": str(rc),
            "perf_status": "available",
            "perf_detail": "perf stat true succeeded",
            "source_log": rel(probe_log),
        }
    return {
        "perf_available": "true",
        "perf_probe_rc": str(rc),
        "perf_status": "probe_failed",
        "perf_detail": "perf exists but probe failed",
        "source_log": rel(probe_log),
    }


def build_and_run(perf_status: Dict[str, str]) -> tuple[int, int, str]:
    build_rc = run_wsl(
        f"make clean >/dev/null 2>&1 || true && make {BASE_FLAGS} -j{MAKE_JOBS}",
        OUT_DIR / "build.log",
        timeout=1200,
    )
    run_rc = 1
    run_mode = "not_run"
    if build_rc == 0 and perf_status["perf_status"] == "available":
        run_mode = "perf_stat"
        run_rc = run_wsl(
            f"perf stat -e {PERF_EVENTS} -- stdbuf -o0 ./main",
            OUT_DIR / "run_perf.log",
            timeout=2400,
        )
        if run_rc != 0:
            run_mode = "time_fallback_after_perf_failed"
            run_rc = run_wsl(
                "/usr/bin/time -v stdbuf -o0 ./main",
                OUT_DIR / "run_time.log",
                timeout=2400,
            )
    elif build_rc == 0:
        run_mode = "time_fallback_perf_missing"
        run_rc = run_wsl(
            "/usr/bin/time -v stdbuf -o0 ./main",
            OUT_DIR / "run_time.log",
            timeout=2400,
        )
    run_wsl("make clean >/dev/null 2>&1 || true", OUT_DIR / "cleanup.log", timeout=300)
    return build_rc, run_rc, run_mode


def run_objdump() -> int:
    return run_wsl(
        "objdump -d build/mattrgsw.o build/polynomial.o > repro/stage161_post_fusion_attribution/objdump_full.txt && "
        "sed -i 's/[[:space:]]*$//' repro/stage161_post_fusion_attribution/objdump_full.txt && "
        "grep -E '<mat_trgsw_mul_pvmtmlwe|<polynomial_|vfmadd|vfnmadd|vfmsub|vfm|zmm|ymm|vmov|vbroadcast|vperm|vmul|vadd|vsub' "
        "repro/stage161_post_fusion_attribution/objdump_full.txt | head -n 400 > repro/stage161_post_fusion_attribution/objdump_filtered.txt && "
        "sed -i 's/[[:space:]]*$//' repro/stage161_post_fusion_attribution/objdump_filtered.txt",
        OUT_DIR / "objdump_driver.log",
        timeout=300,
    )


def instruction_counts() -> List[Dict[str, str]]:
    path = OUT_DIR / "objdump_full.txt"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    patterns = {
        "vfmadd": r"\bvfmadd",
        "vfnmadd": r"\bvfnmadd",
        "vfmsub": r"\bvfmsub",
        "fma_family": r"\bvfmadd|\bvfnmadd|\bvfmsub",
        "zmm_refs": r"%zmm",
        "ymm_refs": r"%ymm",
        "xmm_refs": r"%xmm",
        "vmovapd": r"\bvmovapd",
        "vmovupd": r"\bvmovupd",
        "vmovsd": r"\bvmovsd",
        "vbroadcastsd": r"\bvbroadcastsd",
        "vpermpd_or_vperm": r"\bvperm",
        "vmulpd": r"\bvmulpd",
        "vaddpd": r"\bvaddpd",
        "vsubpd": r"\bvsubpd",
    }
    rows = []
    scopes = {
        "build/mattrgsw.o+build/polynomial.o": text,
        "active:mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512": function_body(
            text, "mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512"
        ),
    }
    for scope, scope_text in scopes.items():
        for name, pattern in patterns.items():
            rows.append({
                "scope": scope,
                "metric": name,
                "count": str(len(re.findall(pattern, scope_text))),
                "evidence": rel(path) if path.exists() else "missing",
            })
    return rows


def function_body(objdump_text: str, symbol: str) -> str:
    match = re.search(rf"^[0-9a-f]+ <{re.escape(symbol)}>:\n", objdump_text, re.MULTILINE)
    if not match:
        return ""
    rest = objdump_text[match.end():]
    next_symbol = re.search(r"^[0-9a-f]+ <[^>]+>:\n", rest, re.MULTILINE)
    if not next_symbol:
        return rest
    return rest[:next_symbol.start()]


def parse_run_metrics(run_mode: str) -> Dict[str, str]:
    log = OUT_DIR / ("run_perf.log" if (OUT_DIR / "run_perf.log").exists() else "run_time.log")
    correctness_line = find_last_line(log, "SAB_PVW_BENCH correctness target_full")
    summary_line = find_last_line(log, "SAB_PVW_BENCH summary target_full")
    summary = extract_fields(summary_line)
    max_rss = ""
    elapsed = ""
    user = ""
    sys = ""
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines() if log.exists() else []:
        if "Maximum resident set size" in line:
            max_rss = line.split(":", 1)[1].strip()
        if "Elapsed (wall clock) time" in line:
            elapsed = line.split("):", 1)[1].strip() if "):" in line else line.split(":", 1)[1].strip()
        if "User time (seconds)" in line:
            user = line.split(":", 1)[1].strip()
        if "System time (seconds)" in line:
            sys = line.split(":", 1)[1].strip()
    return {
        "run_mode": run_mode,
        "correctness": correctness_line.rsplit(" ", 1)[-1] if correctness_line else "MISSING",
        "r": summary.get("r", ""),
        "reps": summary.get("reps", ""),
        "pvw_avg_us": summary.get("pvw_avg_us", ""),
        "pvw_lane_avg_us": summary.get("pvw_lane_avg_us", ""),
        "scalar_repeated_avg_us": summary.get("scalar_repeated_avg_us", ""),
        "scalar_lane_avg_us": summary.get("scalar_lane_avg_us", ""),
        "speedup_vs_scalar_repeated": summary.get("speedup_vs_scalar_repeated", ""),
        "time_elapsed": elapsed,
        "time_user_seconds": user,
        "time_sys_seconds": sys,
        "time_max_rss_kb": max_rss,
        "source_log": rel(log),
    }


def perf_counter_rows() -> List[Dict[str, str]]:
    log = OUT_DIR / "run_perf.log"
    if not log.exists():
        return []
    rows = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        clean = line.replace(",", "").strip()
        parts = clean.split()
        if len(parts) >= 2 and re.fullmatch(r"[0-9.]+", parts[0]):
            metric = parts[1]
            if metric in PERF_EVENTS.split(",") or metric in {"seconds"}:
                rows.append({
                    "metric": metric,
                    "value": parts[0],
                    "unit": "count",
                    "evidence": rel(log),
                    "detail": line.strip(),
                })
    return rows


def source_map_rows() -> List[Dict[str, str]]:
    return [
        {
            "layer": "SAB CMUX",
            "symbol_or_flag": "SAB_PVW_SUB_DECOMP_FUSION=true",
            "role": "routes CMUX difference directly into MAT EP input decomposition",
            "evidence": "src/sab_pvw.c",
        },
        {
            "layer": "MAT EP entry",
            "symbol_or_flag": "mat_trgsw_mul_pvmtmlwe_sub_DFT",
            "role": "calls mat_trgsw_sub_decompose then mat_trgsw_mul_pvmtmlwe_DFT_from_dec",
            "evidence": "src/mosfhet/src/mattrgsw.c",
        },
        {
            "layer": "r>4 AVX512 dispatch",
            "symbol_or_flag": "MAT_TRGSW_AVX512_RGT4_FUSED=true",
            "role": "selects mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512 for r=6 current path",
            "evidence": "src/mosfhet/src/mattrgsw.c; src/mosfhet/Makefile.def",
        },
        {
            "layer": "materialization",
            "symbol_or_flag": "SAB_PVW_BACKEND_FROM_DFT_ADD=true",
            "role": "keeps backend FromDFT-add materialization fused with add, but does not reduce materialization count",
            "evidence": "src/sab_pvw.c",
        },
    ]


def stage160_link_rows() -> List[Dict[str, str]]:
    component = read_csv(STAGE160_COMPONENT)
    profile = read_csv(STAGE160_PROFILE)
    rows = []
    for row in component:
        if row.get("component") in {"mat_ep_plus_subdecomp", "from_dft_materialization", "explicit_sub"}:
            rows.append({
                "source_stage": "Stage160",
                "metric": row.get("component", ""),
                "value": row.get("share_of_full", ""),
                "evidence": rel(STAGE160_COMPONENT),
                "interpretation": row.get("interpretation", ""),
            })
    if profile:
        p = profile[0]
        rows.append({
            "source_stage": "Stage160",
            "metric": "mat_ep_calls;from_dft_calls",
            "value": f"{p.get('mat_ep_calls', '')};{p.get('cmux_from_dft_calls', '')}",
            "evidence": rel(STAGE160_PROFILE),
            "interpretation": "Stage161 attribution applies to a path with unchanged 573440 MAT EP/materialization calls.",
        })
    return rows


def historical_counter_rows() -> List[Dict[str, str]]:
    selected = []
    keep = {
        "cycles", "instructions", "cache-references", "cache-misses",
        "mem_inst_retired.all_loads", "mem_inst_retired.all_stores",
        "fp_arith_inst_retired.512b_packed_double",
        "fp_arith_inst_retired.256b_packed_double",
    }
    for row in read_csv(STAGE101_COUNTERS):
        if row.get("source") == "attribution_perf" and row.get("metric") in keep:
            selected.append({
                "source_stage": "Stage101 historical r=4 native",
                "metric": row.get("metric", ""),
                "value": row.get("value", ""),
                "unit": row.get("unit", ""),
                "evidence": row.get("evidence", ""),
                "scope_note": "Historical native counter reference; not a current r=6 post-fusion proof.",
            })
    return selected


def next_queue_rows(perf_status: Dict[str, str], summary_decision: str) -> List[Dict[str, str]]:
    native_needed = perf_status["perf_status"] != "available"
    return [
        {
            "priority": "P0",
            "stage": "162",
            "name": "materialization-count reduction feasibility",
            "reason": "Stage160 from_DFT materialization remains 33.8201% and Stage161 proxy cannot prove MAT EP theoretical optimality.",
            "gate": "Prove closure/equivalence before full SAB; reject if materialization count stays 573440.",
        },
        {
            "priority": "P0" if native_needed else "P1",
            "stage": "161N",
            "name": "native post-fusion counter run",
            "reason": "Current WSL perf status is " + perf_status["perf_status"] + "; native counters are required to classify FMA vs memory/spill limits.",
            "gate": "cycles, instructions, cache, loads/stores, and AVX512 FP counters on current r=6 post-fusion path.",
        },
        {
            "priority": "P1",
            "stage": "163",
            "name": "explicit best-path policy boundary",
            "reason": f"Stage161 decision is {summary_decision}; Stage159 remains an explicit promotion candidate.",
            "gate": "No scalar/default behavior change without a separate policy commit.",
        },
    ]


def build_summary(
    build_rc: int,
    run_rc: int,
    objdump_rc: int,
    perf_status: Dict[str, str],
    run_metrics: Dict[str, str],
    instr: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    active_counts = {
        row["metric"]: int(row["count"])
        for row in instr
        if row["scope"] == "active:mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512"
    }
    fma_ok = active_counts.get("fma_family", 0) > 0 and active_counts.get("zmm_refs", 0) > 0
    correctness_ok = run_metrics.get("correctness") == "Pass"
    build_run_ok = build_rc == 0 and run_rc == 0 and correctness_ok
    if build_run_ok and objdump_rc == 0 and fma_ok and perf_status["perf_status"] == "available":
        decision = "PASS_STAGE161_NATIVE_COUNTER_ATTRIBUTION_RECORDED"
        next_action = "Interpret counters before claiming MAT EP theoretical optimality."
    elif build_run_ok and objdump_rc == 0 and fma_ok:
        decision = "PASS_STAGE161_PROXY_ATTRIBUTION_NATIVE_COUNTER_REQUIRED"
        next_action = "Proceed to Stage162 and schedule native counter run for current r=6 post-fusion path."
    else:
        decision = "FAIL_STAGE161_POST_FUSION_ATTRIBUTION"
        next_action = "Repair build/run/objdump/correctness before using attribution evidence."
    return [
        {
            "gate": "stage161_build_run_correctness",
            "status": "PASS" if build_run_ok else "FAIL",
            "metric": "build_rc;run_rc;correctness",
            "value": f"{build_rc};{run_rc};{run_metrics.get('correctness', '')}",
            "evidence": rel(RUN_METRICS_CSV),
            "detail": "Build and run the current r=6 post-fusion explicit path without body-profile overhead.",
            "next_action": "",
        },
        {
            "gate": "stage161_perf_status",
            "status": perf_status["perf_status"],
            "metric": "perf_available",
            "value": perf_status["perf_available"],
            "evidence": perf_status["source_log"],
            "detail": perf_status["perf_detail"],
            "next_action": "Native counters are required for FMA-vs-memory classification if perf is missing.",
        },
        {
            "gate": "stage161_objdump_proxy",
            "status": "PASS" if objdump_rc == 0 and fma_ok else "FAIL",
            "metric": "fma_family;zmm_refs",
            "value": f"{active_counts.get('fma_family', 0)};{active_counts.get('zmm_refs', 0)}",
            "evidence": f"{rel(INSTRUCTION_CSV)}; {rel(OUT_DIR / 'objdump_filtered.txt')}",
            "detail": "Proxy confirms the active rgt4 tiled function contains AVX512/FMA-family instructions, but not throughput optimality.",
            "next_action": "",
        },
        {
            "gate": "stage161_decision",
            "status": decision,
            "metric": "attribution_scope",
            "value": "native" if perf_status["perf_status"] == "available" else "proxy_only",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage161 decides how far current attribution evidence can support the MAT EP frontier.",
            "next_action": next_action,
        },
    ]


def write_docs(
    summary: List[Dict[str, str]],
    run_metrics: Dict[str, str],
    perf_status: Dict[str, str],
    instr: List[Dict[str, str]],
    stage160: List[Dict[str, str]],
    queue: List[Dict[str, str]],
) -> None:
    decision = summary[-1]["status"]
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage161 Post-Fusion Attribution Plan",
        "",
        "Date: 2026-07-03",
        "",
        "Goal: attribute the Stage160 dominant `mat_ep_plus_subdecomp` frontier on the current r=6 post-fusion path.",
        "",
        "Endpoint: complete-SAB correctness and timing remain checked, but Stage161 is an attribution gate, not a final performance claim.",
        "",
        "Evidence hierarchy: native perf counters if available; otherwise objdump/time proxy labeled non-final.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage161 Post-Fusion Attribution Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage160 shows the fused MAT EP/decompose block is the largest component. Stage161 tests what can be concluded about that block from the current platform.",
        "",
        "Proxy evidence can verify that the compiled path uses AVX512/FMA-family instructions. It cannot prove the kernel is theoretically optimal, FMA-bound, memory-bound, or spill-bound. Those require native hardware counters for the current r=6 post-fusion build.",
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# MAT-RLWE SAB Post-Fusion Attribution Variant",
        "",
        "Date: 2026-07-03",
        "",
        "Profiled explicit path:",
        "",
        "```text",
        "MAT_TRGSW_AVX512_RGT4_FUSED=true",
        "SAB_PVW_ACTIVE_BUFFER_FUSION=true",
        "SAB_PVW_BACKEND_FROM_DFT_ADD=true",
        "SAB_PVW_SUB_DECOMP_FUSION=true",
        "```",
        "",
        "The source dispatch is `mat_trgsw_mul_pvmtmlwe_sub_DFT -> mat_trgsw_sub_decompose -> mat_trgsw_mul_pvmtmlwe_DFT_from_dec -> rgt4_tiled_avx512` for r=6.",
    ]) + "\n")
    instr_focus = [
        row for row in instr
        if row["scope"] == "active:mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512"
        and row["metric"] in {"fma_family", "zmm_refs", "ymm_refs", "vmovupd", "vmovapd"}
    ]
    write_text_lf(OUT_MD, "\n".join([
        "# Stage161 Post-Fusion Attribution",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "## Summary Gates",
        "",
        table(summary, ["gate", "status", "metric", "value", "detail", "next_action"]),
        "",
        "## Run Metrics",
        "",
        table([run_metrics], ["run_mode", "correctness", "pvw_lane_avg_us", "speedup_vs_scalar_repeated", "time_max_rss_kb", "source_log"]),
        "",
        "## Perf Status",
        "",
        table([perf_status], ["perf_available", "perf_status", "perf_detail", "source_log"]),
        "",
        "## Instruction Proxy",
        "",
        table(instr_focus, ["metric", "count", "evidence"]),
        "",
        "## Stage160 Linkage",
        "",
        table(stage160, ["metric", "value", "interpretation"]),
        "",
        "## Next Queue",
        "",
        table(queue, ["priority", "stage", "name", "reason", "gate"]),
        "",
        "Interpretation: the current WSL platform cannot provide perf counters. Stage161 therefore verifies the active AVX512/FMA proxy path and preserves complete-SAB correctness, but does not claim MAT EP theoretical optimality.",
    ]) + "\n")


def update_global(summary: List[Dict[str, str]]) -> None:
    decision = summary[-1]["status"]
    append_once(ROADMAP_MD, "## Stage 161: Post-Fusion Attribution", f"""
## Stage 161: Post-Fusion Attribution

Goal:

```text
Attribute the Stage160 dominant fused MAT EP/decompose block with native
counters if available, otherwise with explicitly scoped proxy evidence.
```

Status:

```text
Completed. Stage161 records {decision}; WSL perf is not treated as native
counter evidence when unavailable.
```
""")
    append_once(GOAL_MD, "Stage161 records post-fusion attribution scope", f"""
Stage161 records post-fusion attribution scope for the dominant MAT EP block.
Decision: `{decision}`. Proxy objdump evidence confirms the AVX512/FMA build
path, but native counters remain required for FMA-vs-memory optimality claims.
""")
    append_once(CURRENT_GOAL_MD, "65. Treat Stage161 as the post-fusion attribution gate", f"""
65. Treat Stage161 as the post-fusion attribution gate:
    `{decision}`. It prevents overclaiming by separating objdump/time proxy
    evidence from native hardware-counter proof.
""")
    append_once(HYPOTHESIS_YAML, "H85_post_fusion_attribution", f"""
  - id: H85_post_fusion_attribution
    statement: >
      The Stage160 dominant fused MAT EP/decompose block should be attributed
      with native counters before making theoretical optimality claims; if
      native counters are unavailable, objdump/time evidence is proxy-only.
    mechanism: >
      Stage161 builds and runs the current r=6 post-fusion path, records perf
      availability, instruction-family counts, source dispatch, and Stage160
      component linkage.
    status: stage161_post_fusion_attribution
    evidence: docs/stage161_post_fusion_attribution.md; experiments/stage161_post_fusion_attribution_plan.md; theory_checks/stage161_post_fusion_attribution_model.md; repro/stage161_post_fusion_attribution/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - current post-fusion full-SAB correctness fails
      - objdump does not show expected AVX512/FMA-family instructions
      - proxy evidence is reported as theoretical optimality
""")
    append_once(RUN_LOG, "stage161-post-fusion-attribution-001", f"stage161-post-fusion-attribution-001,2026-07-03,{git_head()},Stage 161,spqlios_avx512,python scripts/build_stage161_post_fusion_attribution.py,r={R_VALUE}; bench_reps={BENCH_REPS}; perf_or_time; objdump,default-rng,{decision},Post-fusion MAT EP attribution gate.,{rel(OUT_DIR)}\n")
    append_once(MANIFEST, "stage161_post_fusion_attribution", f"""
- stage161_post_fusion_attribution: `{decision}`
  - `docs/stage161_post_fusion_attribution.md`
  - `experiments/stage161_post_fusion_attribution_plan.md`
  - `theory_checks/stage161_post_fusion_attribution_model.md`
  - `repro/stage161_post_fusion_attribution/`
""")
    append_once(CHECKLIST, "Stage161 post-fusion attribution pack", """
- [x] Stage161 post-fusion attribution pack recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() else "",
            "size_bytes": str(path.stat().st_size) if path.exists() else "",
        })
    write_csv(ARTIFACT_CSV, rows, ["artifact", "exists", "sha256", "size_bytes"])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    perf_status = detect_perf()
    build_rc = run_wsl(
        f"make clean >/dev/null 2>&1 || true && make {BASE_FLAGS} -j{MAKE_JOBS}",
        OUT_DIR / "build.log",
        timeout=1200,
    )
    objdump_rc = run_objdump() if build_rc == 0 else 1
    run_rc = 1
    run_mode = "not_run"
    if build_rc == 0 and perf_status["perf_status"] == "available":
        run_mode = "perf_stat"
        run_rc = run_wsl(
            f"perf stat -e {PERF_EVENTS} -- stdbuf -o0 ./main",
            OUT_DIR / "run_perf.log",
            timeout=2400,
        )
        if run_rc != 0:
            run_mode = "time_fallback_after_perf_failed"
            run_rc = run_wsl(
                "/usr/bin/time -v stdbuf -o0 ./main",
                OUT_DIR / "run_time.log",
                timeout=2400,
            )
    elif build_rc == 0:
        run_mode = "time_fallback_perf_missing"
        run_rc = run_wsl(
            "/usr/bin/time -v stdbuf -o0 ./main",
            OUT_DIR / "run_time.log",
            timeout=2400,
        )
    run_wsl("make clean >/dev/null 2>&1 || true", OUT_DIR / "cleanup.log", timeout=300)

    run_metrics = parse_run_metrics(run_mode)
    instr = instruction_counts()
    perf_status_rows = [perf_status]
    perf_counter = perf_counter_rows()
    source_map = source_map_rows()
    stage160 = stage160_link_rows()
    historical = historical_counter_rows()
    summary = build_summary(build_rc, run_rc, objdump_rc, perf_status, run_metrics, instr)
    queue = next_queue_rows(perf_status, summary[-1]["status"])

    write_csv(RUN_METRICS_CSV, [run_metrics], ["run_mode", "correctness", "r", "reps", "pvw_avg_us", "pvw_lane_avg_us", "scalar_repeated_avg_us", "scalar_lane_avg_us", "speedup_vs_scalar_repeated", "time_elapsed", "time_user_seconds", "time_sys_seconds", "time_max_rss_kb", "source_log"])
    write_csv(PERF_STATUS_CSV, perf_status_rows + perf_counter, ["perf_available", "perf_probe_rc", "perf_status", "perf_detail", "metric", "value", "unit", "evidence", "detail", "source_log"])
    write_csv(INSTRUCTION_CSV, instr, ["scope", "metric", "count", "evidence"])
    write_csv(SOURCE_MAP_CSV, source_map, ["layer", "symbol_or_flag", "role", "evidence"])
    write_csv(STAGE160_LINK_CSV, stage160, ["source_stage", "metric", "value", "evidence", "interpretation"])
    write_csv(HISTORICAL_COUNTER_CSV, historical, ["source_stage", "metric", "value", "unit", "evidence", "scope_note"])
    write_csv(NEXT_QUEUE_CSV, queue, ["priority", "stage", "name", "reason", "gate"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(summary, run_metrics, perf_status, instr, stage160, queue)
    update_global(summary)
    write_artifacts([
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, RUN_METRICS_CSV,
        PERF_STATUS_CSV, INSTRUCTION_CSV, SOURCE_MAP_CSV, STAGE160_LINK_CSV,
        HISTORICAL_COUNTER_CSV, NEXT_QUEUE_CSV, OUT_DIR / "perf_probe.log",
        OUT_DIR / "build.log", OUT_DIR / "run_time.log", OUT_DIR / "run_perf.log",
        OUT_DIR / "objdump_driver.log", OUT_DIR / "objdump_filtered.txt",
        OUT_DIR / "objdump_full.txt", OUT_DIR / "cleanup.log",
        Path(__file__).resolve(),
    ])

    decision = summary[-1]["status"]
    print(f"Stage161 post-fusion attribution: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
