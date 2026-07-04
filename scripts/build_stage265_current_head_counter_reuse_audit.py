#!/usr/bin/env python3
"""Build Stage265 current-head counter reuse audit artifacts."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage265_current_head_counter_reuse_audit"
DOC = ROOT / "docs" / "stage265_current_head_counter_reuse_audit.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE245_ANCHOR = "0888285"
STAGE264_HEAD = "6f04818"
HOT_PATHS = ["main.c", "Makefile", "include", "src"]
MAT_KERNEL_PATHS = ["src/mosfhet/src/mattrgsw.c"]

STAGE101_SUMMARY = ROOT / "repro" / "stage101_cb5_remote_native_perf" / "summary.csv"
STAGE226_PROOF = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "proof_gate.csv"
STAGE226_ATTR = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "attribution_summary.csv"
STAGE245_PROOF = ROOT / "repro" / "stage245_current_head_counter_bridge" / "proof_gate.csv"
STAGE263_PROOF = ROOT / "repro" / "stage263_nonbinary_profile_attribution" / "proof_gate.csv"
STAGE264_PROOF = ROOT / "repro" / "stage264_mat_avx512_counter_preflight" / "proof_gate.csv"
STAGE264_SOURCE_MODEL = ROOT / "repro" / "stage264_mat_avx512_counter_preflight" / "source_model.csv"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="\n", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text.lstrip())
        if not text.endswith("\n"):
            handle.write("\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def table(rows: list[dict[str, str]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |"]
    out.append("| " + " | ".join("---" for _ in fields) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def diff_name_status(base: str, paths: list[str]) -> list[dict[str, str]]:
    output = git("diff", "--name-status", f"{base}..HEAD", "--", *paths)
    rows: list[dict[str, str]] = []
    if not output:
        rows.append({
            "base": base,
            "head": git("rev-parse", "--short", "HEAD"),
            "path": ";".join(paths),
            "status": "NO_DIFF",
            "classification": "unchanged",
            "claim_effect": "prior attribution may remain structurally reusable for this path set",
        })
        return rows
    for line in output.splitlines():
        parts = line.split("\t")
        status = parts[0]
        path = parts[-1]
        if path == "src/mosfhet/src/mattrgsw.c":
            classification = "mat_kernel"
            effect = "MAT EP source changed; previous kernel counters require refresh"
        elif path.startswith("src/sab_pvw") or path == "include/sab_pvw.h":
            classification = "pvw_sab_hot_path"
            effect = "Complete-SAB counter attribution for PVW/MAT path requires fresh current-head native run"
        elif path == "main.c":
            classification = "benchmark_and_protocol_harness"
            effect = "Benchmark semantics and current target claims require fresh current-head evidence"
        elif path.endswith("Makefile.def") or path == "Makefile":
            classification = "build_flags"
            effect = "Backend/flag build semantics require current-binary verification"
        else:
            classification = "other_executable_scope"
            effect = "Treat as refresh-required until manually classified"
        rows.append({
            "base": base,
            "head": git("rev-parse", "--short", "HEAD"),
            "path": path,
            "status": status,
            "classification": classification,
            "claim_effect": effect,
        })
    return rows


def csv_status(path: Path, expected_prefix: str | None = None) -> str:
    rows = read_csv(path)
    if not rows:
        return "missing_or_empty"
    text = " ".join(" ".join(row.values()) for row in rows)
    if expected_prefix and expected_prefix not in text:
        return "present_unexpected"
    return "present"


def evidence_reuse_rows(hot_delta: list[dict[str, str]], mat_delta: list[dict[str, str]]) -> list[dict[str, str]]:
    hotpath_changed = not (len(hot_delta) == 1 and hot_delta[0]["status"] == "NO_DIFF")
    mat_kernel_unchanged = len(mat_delta) == 1 and mat_delta[0]["status"] == "NO_DIFF"
    stage226_attr = {row.get("metric", ""): row for row in read_csv(STAGE226_ATTR)}
    return [
        {
            "evidence": "Stage101 CB5 native r=4 binary counters",
            "artifact": rel(ROOT / "docs" / "stage101_cb5_remote_native_perf_log.md"),
            "input_status": csv_status(STAGE101_SUMMARY, "PASS_STAGE101"),
            "reuse_for_current_nonbinary_claim": "historical_context_only",
            "reason": "Stage101 predates the current non-binary SAB path and does not measure include-zero/ternary target T_bootstrap/r.",
        },
        {
            "evidence": "Stage226 exact backend-vs-wrapper native counters",
            "artifact": rel(STAGE226_ATTR),
            "input_status": csv_status(STAGE226_PROOF, "PASS_STAGE226"),
            "reuse_for_current_nonbinary_claim": "not_directly_reusable" if hotpath_changed else "attribution_only",
            "reason": (
                "PVW/SAB hot-path and benchmark code changed after the Stage245 bridge; Stage226 remains exact-route mechanism context only."
                if hotpath_changed
                else "No hot-path delta detected; attribution-only reuse may be allowed."
            ),
        },
        {
            "evidence": "Stage245 current-head counter bridge",
            "artifact": rel(STAGE245_PROOF),
            "input_status": csv_status(STAGE245_PROOF, "PASS_STAGE245"),
            "reuse_for_current_nonbinary_claim": "expired_by_current_hotpath_delta" if hotpath_changed else "still_valid",
            "reason": "Stage245 bridged only through commit 0888285; current HEAD changes include main.c, sab_pvw.c, sab_pvw.h, and Makefile.def.",
        },
        {
            "evidence": "Stage263 current non-binary profile",
            "artifact": rel(STAGE263_PROOF),
            "input_status": csv_status(STAGE263_PROOF, "PASS_STAGE263"),
            "reuse_for_current_nonbinary_claim": "current_profile_evidence",
            "reason": "Stage263 measures current non-binary schedule/profile but not native hardware counters.",
        },
        {
            "evidence": "Stage264 current MAT-AVX512 proxy",
            "artifact": rel(STAGE264_PROOF),
            "input_status": csv_status(STAGE264_PROOF, "PASS_STAGE264"),
            "reuse_for_current_nonbinary_claim": "current_proxy_only",
            "reason": "Stage264 audits the current object/source proxy; WSL perf is missing, so it is not native counter evidence.",
        },
        {
            "evidence": "MAT external-product kernel source",
            "artifact": "src/mosfhet/src/mattrgsw.c",
            "input_status": "unchanged_since_stage245" if mat_kernel_unchanged else "changed",
            "reuse_for_current_nonbinary_claim": "kernel_structure_context" if mat_kernel_unchanged else "refresh_required",
            "reason": "The MAT EP source is unchanged, but complete-SAB native counters still require fresh measurement after wrapper/protocol deltas.",
        },
        {
            "evidence": "Stage226 attribution ratios",
            "artifact": rel(STAGE226_ATTR),
            "input_status": "present" if stage226_attr else "missing",
            "reuse_for_current_nonbinary_claim": "context_only",
            "reason": (
                f"Prior exact-route ratios: cycles={stage226_attr.get('stage226_cycles_wrapper_over_backend', {}).get('value', '')}, "
                f"loads={stage226_attr.get('stage226_loads_wrapper_over_backend', {}).get('value', '')}, "
                f"stores={stage226_attr.get('stage226_stores_wrapper_over_backend', {}).get('value', '')}."
            ),
        },
    ]


def claim_rows() -> list[dict[str, str]]:
    return [
        {
            "claim": "current_nonbinary_t_bootstrap_over_r",
            "status": "supported_by_stage262_263_wsl",
            "allowed_wording": "Use Stage262 repeated WSL and Stage263 profile evidence for current non-binary T_bootstrap/r claims.",
            "forbidden_wording": "Treat historical native counters as current non-binary native-counter evidence.",
            "evidence": "docs/stage262_nonbinary_target_repeated_stats.md; docs/stage263_nonbinary_profile_attribution.md",
        },
        {
            "claim": "current_head_native_counter_attribution",
            "status": "fresh_native_run_required",
            "allowed_wording": "Historical counters are context; current non-binary include-zero/ternary native counters must be rerun on the current binary.",
            "forbidden_wording": "Stage101/226 counters prove current non-binary MAT-SAB hardware behavior.",
            "evidence": "repro/stage265_current_head_counter_reuse_audit/code_delta_hotpath.csv",
        },
        {
            "claim": "mat_kernel_source_stability",
            "status": "supported",
            "allowed_wording": "mattrgsw.c is unchanged from the Stage245 bridge anchor, so source-level MAT EP structure is stable.",
            "forbidden_wording": "Stable source alone proves retired counter behavior or theoretical optimality.",
            "evidence": "repro/stage265_current_head_counter_reuse_audit/code_delta_mat_kernel.csv",
        },
        {
            "claim": "theoretical_optimality",
            "status": "blocked",
            "allowed_wording": "Keep MAT-AVX512 optimality open pending lower-bound/counter/model closure.",
            "forbidden_wording": "The current MAT-AVX512 implementation has reached theoretical optimum.",
            "evidence": "docs/stage264_mat_avx512_counter_preflight.md",
        },
    ]


def next_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage266_current_head_nonbinary_native_counter",
            "entry_condition": "Need hardware-counter attribution for current non-binary include-zero/ternary T_bootstrap/r.",
            "gate": "Native perf on current HEAD, same backend, full SAB correctness, counters for r=4 include-zero and ternary.",
            "status": "selected_if_remote_available",
            "failure_action": "Keep native-counter claim historical/context-only.",
        },
        {
            "priority": "P1",
            "route": "stage266_local_nonbinary_split_projection",
            "entry_condition": "Native perf unavailable but local WSL can run current binary.",
            "gate": "Profile split projection only; no hardware-counter or optimality wording.",
            "status": "fallback",
            "failure_action": "Do not alter SAB hot path without full T_bootstrap/r A/B gate.",
        },
        {
            "priority": "P2",
            "route": "new_hotpath_variant",
            "entry_condition": "A concrete implementation mechanism is selected after Stage266 evidence.",
            "gate": "correctness, noise/resource, repeated complete-SAB T_bootstrap/r, backend separation.",
            "status": "blocked_until_evidence",
            "failure_action": "Record neutral/negative; preserve scalar baseline.",
        },
    ]


def proof_rows(hot_delta: list[dict[str, str]], mat_delta: list[dict[str, str]], reuse: list[dict[str, str]]) -> list[dict[str, str]]:
    inputs_ok = all(row["input_status"] != "missing_or_empty" for row in reuse)
    hotpath_changed = not (len(hot_delta) == 1 and hot_delta[0]["status"] == "NO_DIFF")
    mat_kernel_unchanged = len(mat_delta) == 1 and mat_delta[0]["status"] == "NO_DIFF"
    decision = (
        "PASS_STAGE265_CURRENT_HEAD_COUNTER_REUSE_AUDIT_REFRESH_REQUIRED"
        if inputs_ok and hotpath_changed and mat_kernel_unchanged
        else "REVIEW_STAGE265_CURRENT_HEAD_COUNTER_REUSE_AUDIT"
    )
    return [
        {
            "gate": "G1_inputs",
            "status": "PASS" if inputs_ok else "REVIEW",
            "metric": "required prior evidence",
            "value": ";".join(f"{row['evidence']}={row['input_status']}" for row in reuse),
            "evidence": "evidence_reuse_matrix.csv",
            "interpretation": "Prior native/proxy/profile artifacts must be present before reuse is classified.",
        },
        {
            "gate": "G2_hotpath_delta",
            "status": "REFRESH_REQUIRED" if hotpath_changed else "NO_REFRESH_REQUIRED",
            "metric": "Stage245 anchor to current HEAD executable diff",
            "value": "diff_present" if hotpath_changed else "no_diff",
            "evidence": "code_delta_hotpath.csv",
            "interpretation": "Current non-binary complete-SAB native counter claims require a fresh current-head run.",
        },
        {
            "gate": "G3_mat_kernel_delta",
            "status": "PASS_UNCHANGED" if mat_kernel_unchanged else "REFRESH_KERNEL_AUDIT_REQUIRED",
            "metric": "mattrgsw.c delta",
            "value": "no_diff" if mat_kernel_unchanged else "diff_present",
            "evidence": "code_delta_mat_kernel.csv",
            "interpretation": "MAT EP source stability preserves source-structure context but not complete-SAB counter reuse.",
        },
        {
            "gate": "G4_claim_boundary",
            "status": "PASS",
            "metric": "historical counters scoped",
            "value": "context_only",
            "evidence": "claim_boundary.csv",
            "interpretation": "Stage101/226 counters must not be cited as current non-binary native evidence.",
        },
        {
            "gate": "G5_next_route",
            "status": "SELECT_STAGE266_CURRENT_HEAD_NATIVE_COUNTER",
            "metric": "next executable route",
            "value": "stage266_current_head_nonbinary_native_counter",
            "evidence": "next_stage_queue.csv",
            "interpretation": "The next non-theory step is fresh current-head non-binary native-counter attribution if remote execution is available.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "evidence": "proof_gate.csv",
            "interpretation": "Stage265 prevents overclaiming historical counters and selects a concrete next experiment.",
        },
    ]


def artifacts(paths: list[Path]) -> list[dict[str, str]]:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
            "sha256": sha256(path) if path.exists() and path.is_file() else "",
        })
    return rows


def update_tracking(decision: str) -> None:
    head = git("rev-parse", "--short", "HEAD")
    append_once(CURRENT_GOAL, "### Stage265 current-head counter reuse audit", f"""
### Stage265 current-head counter reuse audit

`{decision}` records that historical native counters are context-only for the
current non-binary PVW/MAT-SAB path. The active research goal remains open:
the selected next executable route is a fresh current-head non-binary native
counter run or a local split-projection fallback that cannot upgrade hardware
counter claims.
""")
    append_once(HYPOTHESES, "H10_stage265_current_head_counter_reuse_audit:", f"""
H10_stage265_current_head_counter_reuse_audit:
  status: current_head_counter_reuse_refresh_required
  evidence:
    - repro/stage265_current_head_counter_reuse_audit/code_delta_hotpath.csv
    - repro/stage265_current_head_counter_reuse_audit/evidence_reuse_matrix.csv
    - repro/stage265_current_head_counter_reuse_audit/proof_gate.csv
    - docs/stage265_current_head_counter_reuse_audit.md
  conclusion: >
    Stage265 records {decision}. Stage101/226 native counters remain historical
    context, while current non-binary include-zero/ternary native-counter
    attribution requires a fresh current-head run because PVW/SAB hot-path and
    benchmark sources changed after the Stage245 bridge. The MAT EP source is
    unchanged, so source-structure context remains valid.
""")
    append_once(RUN_LOG, "stage265-current-head-counter-reuse-audit-001", f"""stage265-current-head-counter-reuse-audit-001,2026-07-04,{head},Stage 265,analysis,python scripts/build_stage265_current_head_counter_reuse_audit.py,"Stage264 proxy + Stage101/226 native counters + current-head hot-path diff",n/a,{decision},"Historical native counters scoped to context; fresh current-head non-binary native counters selected next.",docs/stage265_current_head_counter_reuse_audit.md; repro/stage265_current_head_counter_reuse_audit/proof_gate.csv
""")
    append_once(MANIFEST, "- stage265_current_head_counter_reuse_audit:", """
- stage265_current_head_counter_reuse_audit:
  - `docs/stage265_current_head_counter_reuse_audit.md`
  - `scripts/build_stage265_current_head_counter_reuse_audit.py`
  - `repro/stage265_current_head_counter_reuse_audit/`
""")
    append_once(CHECKLIST, "Stage265 current-head counter reuse audit", f"""
- [x] Stage265 current-head counter reuse audit records `{decision}` and selects fresh current-head non-binary native-counter attribution as the next executable route.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    head = git("rev-parse", "--short", "HEAD")
    hot_delta = diff_name_status(STAGE245_ANCHOR, HOT_PATHS)
    mat_delta = diff_name_status(STAGE245_ANCHOR, MAT_KERNEL_PATHS)
    reuse = evidence_reuse_rows(hot_delta, mat_delta)
    claims = claim_rows()
    queue = next_rows()
    proof = proof_rows(hot_delta, mat_delta, reuse)
    decision = proof[-1]["status"]

    write_csv(REPRO / "code_delta_hotpath.csv", hot_delta, ["base", "head", "path", "status", "classification", "claim_effect"])
    write_csv(REPRO / "code_delta_mat_kernel.csv", mat_delta, ["base", "head", "path", "status", "classification", "claim_effect"])
    write_csv(REPRO / "evidence_reuse_matrix.csv", reuse, ["evidence", "artifact", "input_status", "reuse_for_current_nonbinary_claim", "reason"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])

    report = f"""# Stage265 Current-Head Counter Reuse Audit

Decision: `{decision}`.

Stage265 reconciles the current-head Stage264 proxy audit with the older
Stage101/226 native counter evidence. It does not run a new benchmark and does
not change SAB code. Its purpose is to prevent using historical native counters
as proof for the current non-binary include-zero/ternary `T_bootstrap/r` path.

## Code Delta From Stage245 Bridge Anchor

{table(hot_delta, ["path", "status", "classification", "claim_effect"])}

## MAT Kernel Delta

{table(mat_delta, ["path", "status", "classification", "claim_effect"])}

## Evidence Reuse Matrix

{table(reuse, ["evidence", "input_status", "reuse_for_current_nonbinary_claim", "reason"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Stage Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{head}`. Stage264 baseline head: `{STAGE264_HEAD}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage265_report.md", report)
    write_text(REPRO / "reproduction_commands.md", f"""# Stage265 Reproduction Commands

```bash
python3 scripts/build_stage265_current_head_counter_reuse_audit.py
git diff --name-status {STAGE245_ANCHOR}..HEAD -- main.c Makefile include src
git diff --name-status {STAGE245_ANCHOR}..HEAD -- src/mosfhet/src/mattrgsw.c
```

Decision: `{decision}`.
""")

    update_tracking(decision)
    artifact_paths = [
        DOC,
        REPRO / "stage265_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "code_delta_hotpath.csv",
        REPRO / "code_delta_mat_kernel.csv",
        REPRO / "evidence_reuse_matrix.csv",
        REPRO / "claim_boundary.csv",
        REPRO / "next_stage_queue.csv",
        REPRO / "proof_gate.csv",
        Path(__file__),
    ]
    write_csv(REPRO / "artifact_index.csv", artifacts(artifact_paths), ["path", "bytes", "sha256"])
    print(decision)
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
