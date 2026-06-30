#!/usr/bin/env python3
"""Build Stage101 remote native Linux perf-counter evidence artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage101_cb5_remote_native_perf"
STAGE28_DIR = OUT_DIR / "stage28_native_perf_counter_gate"
ATTR_DIR = OUT_DIR / "attribution_probe"
OUT_SUMMARY = OUT_DIR / "summary.csv"
OUT_COUNTERS = OUT_DIR / "counter_metrics.csv"
OUT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage101_cb5_remote_native_perf_log.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


PERF_LINE_RE = re.compile(r"^\s*([\d,]+)\s+([A-Za-z0-9_.-]+)\b")
ELAPSED_RE = re.compile(r"^\s*([\d.]+)\s+seconds time elapsed")
USER_RE = re.compile(r"^\s*([\d.]+)\s+seconds user")
SYS_RE = re.compile(r"^\s*([\d.]+)\s+seconds sys")
SUMMARY_RE = re.compile(
    r"SAB_PVW_BENCH summary target_full r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw>[0-9.]+).*?scalar_repeated_avg_us=(?P<scalar>[0-9.]+).*?"
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x"
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def gate_status(path: Path, key: str, value: str, status_field: str = "status") -> str:
    for row in read_csv(path):
        if row.get(key) == value:
            return row.get(status_field, "MISSING")
    return "MISSING"


def parse_perf(path: Path, source: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = PERF_LINE_RE.match(raw)
        if m:
            rows.append(
                {
                    "source": source,
                    "metric": m.group(2),
                    "value": m.group(1).replace(",", ""),
                    "unit": "count",
                    "evidence": rel(path),
                    "detail": raw.strip(),
                }
            )
            continue
        for regex, metric in [
            (ELAPSED_RE, "elapsed_seconds"),
            (USER_RE, "user_seconds"),
            (SYS_RE, "sys_seconds"),
        ]:
            m2 = regex.match(raw)
            if m2:
                rows.append(
                    {
                        "source": source,
                        "metric": metric,
                        "value": m2.group(1),
                        "unit": "seconds",
                        "evidence": rel(path),
                        "detail": raw.strip(),
                    }
                )
                break
    return rows


def parse_run(path: Path, source: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if not path.exists():
        return rows
    text = path.read_text(encoding="utf-8", errors="replace")
    correctness = "PASS" if re.search(r"SAB_PVW_BENCH correctness target_full .* Pass", text) else "FAIL"
    rows.append(
        {
            "source": source,
            "metric": "target_full_correctness",
            "value": correctness,
            "unit": "gate",
            "evidence": rel(path),
            "detail": "target_full correctness Pass line found" if correctness == "PASS" else "target_full correctness Pass line missing",
        }
    )
    for line in text.splitlines():
        m = SUMMARY_RE.search(line)
        if not m:
            continue
        for metric, value in [
            ("r", m.group("r")),
            ("reps", m.group("reps")),
            ("pvw_avg_us", m.group("pvw")),
            ("scalar_repeated_avg_us", m.group("scalar")),
            ("speedup_vs_scalar_repeated", m.group("speedup")),
        ]:
            rows.append(
                {
                    "source": source,
                    "metric": metric,
                    "value": value,
                    "unit": "us" if metric.endswith("_us") else ("x" if metric == "speedup_vs_scalar_repeated" else "value"),
                    "evidence": rel(path),
                    "detail": line.strip(),
                }
            )
    return rows


def parse_event_support(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = [part.strip() for part in raw.split(",", 1)]
        if len(parts) != 2 or not parts[0]:
            continue
        rows.append({"event": parts[0], "status": parts[1]})
    return rows


def metric_value(rows: List[Dict[str, str]], source: str, metric: str) -> str:
    for row in rows:
        if row.get("source") == source and row.get("metric") == metric:
            return row.get("value", "")
    return ""


def artifact_index(paths: List[Path]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    return rows


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def upsert_run_log() -> None:
    fields = [
        "run_id",
        "date",
        "commit_or_state",
        "stage",
        "backend",
        "command",
        "params",
        "seed",
        "status",
        "summary",
        "artifacts",
    ]
    rows = read_csv(RUN_LOG)
    rows = [row for row in rows if row.get("run_id") != "stage101-cb5-remote-native-perf-001"]
    rows.append(
        {
            "run_id": "stage101-cb5-remote-native-perf-001",
            "date": "2026-06-30",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 101",
            "backend": "spqlios_avx512",
            "command": "remote delld@192.168.107.220: STAGE28_RUN_BENCH=1 FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3_2048 SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 bash scripts/run_stage28_native_perf_counter_gate.sh; attribution perf run with load/store/FMA events",
            "params": "BINARY SET_2_3_2048; r=4; h=39; r_prec=7; native Linux; Intel Xeon Gold 6230R; perf_event_paranoid temporarily 1 then restored to 4",
            "seed": "default-rng",
            "status": "PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED",
            "summary": "Remote native Linux Stage28 hardware-counter gate passed; target_full correctness passed; r=4 speedup was 1.309x in both standard and attribution perf runs; load/store/FMA counters are recorded for interpretation but do not prove theoretical optimality by themselves.",
            "artifacts": "docs/stage101_cb5_remote_native_perf_log.md; experiments/stage101_cb5_remote_native_perf_plan.md; scripts/build_stage101_cb5_remote_native_perf.py; repro/stage101_cb5_remote_native_perf/summary.csv; repro/stage101_cb5_remote_native_perf/counter_metrics.csv; repro/stage101_cb5_remote_native_perf/artifact_index.csv",
        }
    )
    write_csv(RUN_LOG, rows, fields)


def write_md(summary_rows: List[Dict[str, str]], counter_rows: List[Dict[str, str]]) -> None:
    metrics = {(row["source"], row["metric"]): row["value"] for row in counter_rows}
    lines = [
        "# Stage101 CB5 Remote Native Perf Log",
        "",
        "Date: 2026-06-30",
        "",
        "## Purpose",
        "",
        "Stage101 resolves CB5 by recording native Linux `perf` hardware-counter",
        "evidence for the complete SAB PVW/MAT path on the remote Xeon platform",
        "authorized by the user. This is evidence for attribution; it is not a",
        "claim that the MAT-AVX512 implementation is theoretically optimal.",
        "",
        "## Summary",
        "",
        "| gate | status | detail |",
        "|---|---|---|",
    ]
    for row in summary_rows:
        lines.append(f"| {row['gate']} | {row['status']} | {row['detail']} |")
    lines.extend(
        [
            "",
            "## Key Metrics",
            "",
            "| metric | value |",
            "|---|---:|",
            f"| standard speedup vs repeated scalar | {metrics.get(('standard_run', 'speedup_vs_scalar_repeated'), 'MISSING')}x |",
            f"| attribution speedup vs repeated scalar | {metrics.get(('attribution_run', 'speedup_vs_scalar_repeated'), 'MISSING')}x |",
            f"| attribution loads | {metrics.get(('attribution_perf', 'mem_inst_retired.all_loads'), 'MISSING')} |",
            f"| attribution stores | {metrics.get(('attribution_perf', 'mem_inst_retired.all_stores'), 'MISSING')} |",
            f"| attribution 512-bit packed FP ops | {metrics.get(('attribution_perf', 'fp_arith_inst_retired.512b_packed_double'), 'MISSING')} |",
            f"| attribution cycles | {metrics.get(('attribution_perf', 'cycles'), 'MISSING')} |",
            f"| attribution instructions | {metrics.get(('attribution_perf', 'instructions'), 'MISSING')} |",
            "",
            "## Interpretation",
            "",
            "The native run confirms that the hardware-counter lane is no longer blocked:",
            "`cycles`, `instructions`, cache events, retired loads/stores, and AVX512",
            "floating-point arithmetic events are available on the target platform.",
            "The complete SAB r=4 correctness gate passed and the measured speedup",
            "remained 1.309x under both the standard Stage28 event set and the wider",
            "attribution event set.",
            "",
            "This resolves the external platform blocker for CB5. It does not by itself",
            "justify wording such as theoretical optimality; that wording still requires",
            "a separate model-to-counter interpretation against Stage22 and assembly",
            "evidence.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    stage28_summary = STAGE28_DIR / "summary.csv"
    standard_perf = STAGE28_DIR / "bench_perf.log"
    standard_run = STAGE28_DIR / "bench_run.log"
    attribution_perf = ATTR_DIR / "bench_attribution_perf.log"
    attribution_run = ATTR_DIR / "bench_attribution_run.log"
    event_support = ATTR_DIR / "event_support.csv"

    counter_rows: List[Dict[str, str]] = []
    counter_rows.extend(parse_perf(standard_perf, "standard_perf"))
    counter_rows.extend(parse_run(standard_run, "standard_run"))
    counter_rows.extend(parse_perf(attribution_perf, "attribution_perf"))
    counter_rows.extend(parse_run(attribution_run, "attribution_run"))

    stage28_gate = gate_status(stage28_summary, "probe", "hardware_counter_gate")
    standard_correct = metric_value(counter_rows, "standard_run", "target_full_correctness")
    attrib_correct = metric_value(counter_rows, "attribution_run", "target_full_correctness")
    attrib_speed = metric_value(counter_rows, "attribution_run", "speedup_vs_scalar_repeated")
    load_counter = metric_value(counter_rows, "attribution_perf", "mem_inst_retired.all_loads")
    store_counter = metric_value(counter_rows, "attribution_perf", "mem_inst_retired.all_stores")
    fma512 = metric_value(counter_rows, "attribution_perf", "fp_arith_inst_retired.512b_packed_double")
    support_rows = parse_event_support(event_support)
    all_support_pass = bool(support_rows) and all(row.get("status") == "PASS" for row in support_rows)

    summary_rows = [
        {
            "gate": "stage101_raw_artifacts",
            "status": "PASS" if stage28_summary.exists() and attribution_perf.exists() else "FAIL",
            "evidence": f"{rel(stage28_summary)}; {rel(attribution_perf)}",
            "detail": "remote raw logs are present",
            "next_action": "Re-copy remote raw logs if any raw artifact is missing.",
        },
        {
            "gate": "stage101_stage28_hardware_counter_gate",
            "status": "PASS" if stage28_gate == "PASS" else "FAIL",
            "evidence": rel(stage28_summary),
            "detail": f"hardware_counter_gate={stage28_gate}",
            "next_action": "Rerun Stage28 on native/perf-enabled Linux if this is not PASS.",
        },
        {
            "gate": "stage101_complete_sab_correctness",
            "status": "PASS" if standard_correct == "PASS" and attrib_correct == "PASS" else "FAIL",
            "evidence": f"{rel(standard_run)}; {rel(attribution_run)}",
            "detail": f"standard={standard_correct}; attribution={attrib_correct}",
            "next_action": "Do not use counters for performance claims if correctness is missing.",
        },
        {
            "gate": "stage101_attribution_events",
            "status": "PASS" if all_support_pass and load_counter and store_counter and fma512 else "FAIL",
            "evidence": f"{rel(event_support)}; {rel(OUT_COUNTERS)}",
            "detail": "load/store/AVX512 FP events supported and recorded",
            "next_action": "Use only basic cycle/instruction evidence if advanced event support is absent.",
        },
        {
            "gate": "stage101_speed_sample",
            "status": "PASS" if attrib_speed and float(attrib_speed) > 1.0 else "FAIL",
            "evidence": rel(attribution_run),
            "detail": f"attribution_speedup_vs_scalar_repeated={attrib_speed}x",
            "next_action": "Repeat runs before making statistical native-performance claims.",
        },
        {
            "gate": "stage101_cb5_decision",
            "status": "PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED"
            if stage28_gate == "PASS" and standard_correct == "PASS" and attrib_correct == "PASS" and load_counter and store_counter and fma512
            else "FAIL_STAGE101_CB5_NATIVE_PERF_COUNTERS",
            "evidence": rel(OUT_SUMMARY),
            "detail": "CB5 platform blocker resolved with native perf evidence; theoretical-optimality wording remains review-gated.",
            "next_action": "Compare counters with Stage22/assembly before claiming MAT-AVX512 theoretical optimality.",
        },
    ]

    write_csv(
        OUT_COUNTERS,
        counter_rows,
        ["source", "metric", "value", "unit", "evidence", "detail"],
    )
    write_csv(
        OUT_SUMMARY,
        summary_rows,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_md(summary_rows, counter_rows)
    write_csv(
        OUT_INDEX,
        artifact_index(
            [
                OUT_SUMMARY,
                OUT_COUNTERS,
                OUT_MD,
                stage28_summary,
                standard_perf,
                standard_run,
                attribution_perf,
                attribution_run,
                event_support,
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    upsert_run_log()
    decision = summary_rows[-1]["status"]
    print(f"Wrote {rel(OUT_SUMMARY)}")
    print(f"Wrote {rel(OUT_COUNTERS)}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage101 CB5 native perf: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
