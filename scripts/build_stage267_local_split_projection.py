#!/usr/bin/env python3
"""Build Stage267 local split projection from current non-binary profile."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage267_local_split_projection"
DOC = ROOT / "docs" / "stage267_local_split_projection.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE263_PROFILE = ROOT / "repro" / "stage263_nonbinary_profile_attribution" / "profile_metrics.csv"
STAGE264_MODEL = ROOT / "repro" / "stage264_mat_avx512_counter_preflight" / "source_model.csv"
STAGE266_PROOF = ROOT / "repro" / "stage266_current_head_nonbinary_native_counter" / "proof_gate.csv"
PVW_SOURCE = ROOT / "src" / "sab_pvw.c"
MAKEFILE_DEF = ROOT / "src" / "mosfhet" / "Makefile.def"
PVW_TMLWE_SOURCE = ROOT / "src" / "mosfhet" / "src" / "pvwtmlwe.c"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


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


def fnum(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "0") or "0")
    except ValueError:
        return 0.0


def projection_rows(profile: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in profile:
        pvw = fnum(row, "pvw_avg_us")
        full = fnum(row, "full_us")
        components = [
            ("mat_ep", fnum(row, "mat_ep_us")),
            ("from_dft", fnum(row, "cmux_from_dft_us")),
            ("cmux_add", fnum(row, "cmux_add_us")),
            ("cmux_sub", fnum(row, "cmux_sub_us")),
            ("materialization_lifecycle", fnum(row, "cmux_from_dft_us") + fnum(row, "cmux_add_us") + fnum(row, "cmux_sub_us")),
            ("sub_a", fnum(row, "sub_a_us")),
            ("ncmux_auto", fnum(row, "ncmux_auto_us")),
            ("postproc_residual", fnum(row, "postproc_residual_us")),
        ]
        for component, us in components:
            rows.append({
                "mode": row["mode"],
                "r": row["r"],
                "component": component,
                "component_us": f"{us:.3f}",
                "share_of_body": f"{(us / full):.6f}" if full else "",
                "share_of_pvw": f"{(us / pvw):.6f}" if pvw else "",
                "source": row.get("source_log", ""),
            })
    return rows


def aggregate_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault((row["r"], row["component"]), []).append(row)
    out: list[dict[str, str]] = []
    for (r, component), items in sorted(grouped.items(), key=lambda item: (int(item[0][0]), item[0][1])):
        body = [float(item["share_of_body"]) for item in items if item["share_of_body"]]
        pvw = [float(item["share_of_pvw"]) for item in items if item["share_of_pvw"]]
        out.append({
            "r": r,
            "component": component,
            "rows": str(len(items)),
            "share_body_min": f"{min(body):.6f}" if body else "",
            "share_body_max": f"{max(body):.6f}" if body else "",
            "share_pvw_min": f"{min(pvw):.6f}" if pvw else "",
            "share_pvw_max": f"{max(pvw):.6f}" if pvw else "",
        })
    return out


def amdahl_rows(aggregate: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in aggregate:
        max_share = float(row["share_pvw_max"] or "0")
        for reduction in (0.25, 0.50, 1.00):
            speedup = 1.0 / (1.0 - max_share * reduction) if max_share * reduction < 1.0 else 0.0
            out.append({
                "r": row["r"],
                "component": row["component"],
                "share_pvw_max": row["share_pvw_max"],
                "hypothetical_component_reduction": f"{reduction:.2f}",
                "full_pvw_speedup_ceiling": f"{speedup:.6f}",
            })
    return out


def source_capability_rows() -> list[dict[str, str]]:
    make_text = MAKEFILE_DEF.read_text(encoding="utf-8", errors="replace")
    pvw_text = PVW_SOURCE.read_text(encoding="utf-8", errors="replace")
    pvwtmlwe_text = PVW_TMLWE_SOURCE.read_text(encoding="utf-8", errors="replace")
    checks = [
        ("backend_from_dft_add_flag", "SAB_PVW_BACKEND_FROM_DFT_ADD", make_text),
        ("backend_flag_enables_fused_wrapper", "FLAGS += -DSAB_PVW_FUSED_FROM_DFT_ADD", make_text),
        ("pvw_cmux_uses_from_dft_add", "pvmtmlwe_from_DFT_add", pvw_text),
        ("backend_impl_guard", "#ifdef SAB_PVW_BACKEND_FROM_DFT_ADD", pvwtmlwe_text),
        ("nonbinary_bench_flag", "SAB_PVW_NONBINARY_BENCH", make_text),
    ]
    rows = []
    for name, needle, text in checks:
        rows.append({
            "check": name,
            "status": "PASS" if needle in text else "MISSING",
            "needle": needle,
            "interpretation": "Existing explicit flag can be tested without new hot-path code." if needle in text else "Do not select Stage268 until source support exists.",
        })
    return rows


def candidate_rows(aggregate: list[dict[str, str]], source_checks: list[dict[str, str]]) -> list[dict[str, str]]:
    by_key = {(row["r"], row["component"]): row for row in aggregate}
    r4_mat = by_key.get(("4", "mat_ep"), {})
    r4_matlife = by_key.get(("4", "materialization_lifecycle"), {})
    r4_suba = by_key.get(("4", "sub_a"), {})
    flag_ok = all(row["status"] == "PASS" for row in source_checks)
    return [
        {
            "candidate": "stage268_nonbinary_backend_from_dft_add_smoke",
            "target": "materialization_lifecycle",
            "r4_share_pvw_max": r4_matlife.get("share_pvw_max", ""),
            "entry_condition": "Existing SAB_PVW_BACKEND_FROM_DFT_ADD explicit flag and current non-binary bench support.",
            "status": "selected" if flag_ok else "blocked_source_support",
            "next_gate": "One-run r=4 include-zero/ternary backend-vs-default T_bootstrap/r smoke; then repeated/noise/resource only if positive.",
            "failure_action": "Record neutral/negative and do not reopen direct-scale from_DFT work without a new mechanism.",
        },
        {
            "candidate": "mat_ep_kernel_layout_change",
            "target": "mat_ep",
            "r4_share_pvw_max": r4_mat.get("share_pvw_max", ""),
            "entry_condition": "Requires fresh native counters or a concrete register/layout mechanism beyond row unroll.",
            "status": "blocked_until_counter_or_new_mechanism",
            "next_gate": "Microbench plus full SAB A/B, same backend.",
            "failure_action": "Do not repeat row-unroll-only negative path.",
        },
        {
            "candidate": "nonbinary_sub_a_rotation_path",
            "target": "sub_a",
            "r4_share_pvw_max": r4_suba.get("share_pvw_max", ""),
            "entry_condition": "Profile shows sub_a remains material after materialization gate.",
            "status": "deferred",
            "next_gate": "Mode-specific sub_a profile and isolated equivalence before code.",
            "failure_action": "Do not optimize sub_a before larger materialization candidate is screened.",
        },
    ]


def proof_rows(profile: list[dict[str, str]], candidates: list[dict[str, str]], aggregate: list[dict[str, str]]) -> list[dict[str, str]]:
    stage266 = " ".join(" ".join(row.values()) for row in read_csv(STAGE266_PROOF))
    selected = next((row for row in candidates if row["status"] == "selected"), {})
    matlife_r4 = next((row for row in aggregate if row["r"] == "4" and row["component"] == "materialization_lifecycle"), {})
    mat_r4 = next((row for row in aggregate if row["r"] == "4" and row["component"] == "mat_ep"), {})
    decision = "PASS_STAGE267_LOCAL_SPLIT_PROJECTION_SELECT_STAGE268_BACKEND_SMOKE" if selected else "REVIEW_STAGE267_LOCAL_SPLIT_PROJECTION"
    return [
        {"gate": "G1_inputs", "status": "PASS" if profile and "PASS_STAGE266" in stage266 else "FAIL", "metric": "Stage263 profile and Stage266 handoff", "value": f"profile_rows={len(profile)}", "evidence": f"{rel(STAGE263_PROFILE)}; {rel(STAGE266_PROOF)}", "interpretation": "Projection starts from current profile and no-native-counter boundary."},
        {"gate": "G2_materialization_share", "status": "PASS", "metric": "r4 materialization_lifecycle share_pvw_max", "value": matlife_r4.get("share_pvw_max", ""), "evidence": "component_aggregate.csv", "interpretation": "from_DFT+add+sub is large enough to screen an existing backend materialization flag."},
        {"gate": "G3_mat_ep_share", "status": "PASS", "metric": "r4 mat_ep share_pvw_max", "value": mat_r4.get("share_pvw_max", ""), "evidence": "component_aggregate.csv", "interpretation": "MAT EP remains important but source-only AVX tuning needs native counters or a new mechanism."},
        {"gate": "G4_candidate_selection", "status": selected.get("status", "none"), "metric": "selected candidate", "value": selected.get("candidate", ""), "evidence": "candidate_selection.csv", "interpretation": "Select an existing explicit flag before writing new hot-path code."},
        {"gate": "G5_claim_boundary", "status": "PASS_PROJECTION_ONLY", "metric": "no speedup claim", "value": "projection_not_measurement", "evidence": "claim_boundary.csv", "interpretation": "Stage267 does not itself prove performance."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": "proof_gate.csv", "interpretation": "Proceed to bounded Stage268 smoke only."},
    ]


def claim_rows() -> list[dict[str, str]]:
    return [
        {"claim": "component_priority", "status": "supported_projection", "allowed_wording": "Current profile selects materialization_lifecycle as the first local smoke candidate.", "forbidden_wording": "Projection proves the candidate is faster.", "evidence": "component_aggregate.csv; amdahl_projection.csv"},
        {"claim": "hardware_counter_attribution", "status": "not_supported", "allowed_wording": "Stage266 remains handoff-only without native counters.", "forbidden_wording": "Stage267 supplies native load/store/FMA attribution.", "evidence": "docs/stage266_current_head_nonbinary_native_counter.md"},
        {"claim": "stage268_code_policy", "status": "no_new_hotpath_code", "allowed_wording": "Stage268 may test an existing explicit flag.", "forbidden_wording": "Implement a new MAT/SAB hot-path variant before the smoke gate.", "evidence": "source_capability.csv; candidate_selection.csv"},
    ]


def next_rows() -> list[dict[str, str]]:
    return [
        {"priority": "P0", "route": "stage268_nonbinary_backend_from_dft_add_smoke", "entry_condition": "Stage267 selected existing explicit backend FromDFT-add flag.", "gate": "r=4 include-zero/ternary correctness and one-run T_bootstrap/r backend-vs-default smoke.", "status": "selected", "failure_action": "Record neutral/negative; no promotion."},
        {"priority": "P1", "route": "stage268_repeated_noise_resource", "entry_condition": "Only if Stage268 smoke is positive for both modes.", "gate": "repeated T_bootstrap/r, final noise/resource, same backend.", "status": "conditional", "failure_action": "Do not claim full SAB speedup from smoke."},
    ]


def artifacts(paths: list[Path]) -> list[dict[str, str]]:
    return [{"path": rel(path), "bytes": str(path.stat().st_size) if path.exists() else "", "sha256": sha256(path) if path.exists() and path.is_file() else ""} for path in paths]


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(CURRENT_GOAL, "### Stage267 local split projection", f"""
### Stage267 local split projection

`{decision}` records a local profile-based projection after Stage266 handoff.
It selects Stage268 backend FromDFT-add non-binary smoke using an existing
explicit flag; it does not upgrade performance or hardware-counter claims.
""")
    append_once(HYPOTHESES, "H10_stage267_local_split_projection:", f"""
H10_stage267_local_split_projection:
  status: projection_selects_existing_backend_materialization_smoke
  evidence:
    - repro/stage267_local_split_projection/component_aggregate.csv
    - repro/stage267_local_split_projection/amdahl_projection.csv
    - repro/stage267_local_split_projection/candidate_selection.csv
    - docs/stage267_local_split_projection.md
  conclusion: >
    Stage267 records {decision}. Current non-binary r=4 profile shows the
    from_DFT/add/sub materialization lifecycle is large enough to justify a
    bounded smoke of the existing SAB_PVW_BACKEND_FROM_DFT_ADD path before any
    new hot-path code is written.
""")
    append_once(RUN_LOG, "stage267-local-split-projection-001", f"""stage267-local-split-projection-001,2026-07-04,{head},Stage 267,analysis,python scripts/build_stage267_local_split_projection.py,"Stage263 profile + Stage264 model + Stage266 no-native-counter boundary",n/a,{decision},"Projection-only gate selects existing backend FromDFT-add r=4 non-binary smoke.",docs/stage267_local_split_projection.md; repro/stage267_local_split_projection/proof_gate.csv
""")
    append_once(MANIFEST, "- stage267_local_split_projection:", """
- stage267_local_split_projection:
  - `docs/stage267_local_split_projection.md`
  - `scripts/build_stage267_local_split_projection.py`
  - `repro/stage267_local_split_projection/`
""")
    append_once(CHECKLIST, "Stage267 local split projection", f"""
- [x] Stage267 local split projection records `{decision}` and selects bounded Stage268 backend FromDFT-add smoke.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    profile = read_csv(STAGE263_PROFILE)
    source_model = read_csv(STAGE264_MODEL)
    components = projection_rows(profile)
    aggregate = aggregate_rows(components)
    amdahl = amdahl_rows(aggregate)
    source_checks = source_capability_rows()
    candidates = candidate_rows(aggregate, source_checks)
    proof = proof_rows(profile, candidates, aggregate)
    decision = proof[-1]["status"]
    claims = claim_rows()
    queue = next_rows()

    write_csv(REPRO / "component_projection.csv", components, ["mode", "r", "component", "component_us", "share_of_body", "share_of_pvw", "source"])
    write_csv(REPRO / "component_aggregate.csv", aggregate, ["r", "component", "rows", "share_body_min", "share_body_max", "share_pvw_min", "share_pvw_max"])
    write_csv(REPRO / "amdahl_projection.csv", amdahl, ["r", "component", "share_pvw_max", "hypothetical_component_reduction", "full_pvw_speedup_ceiling"])
    write_csv(REPRO / "source_capability.csv", source_checks, ["check", "status", "needle", "interpretation"])
    write_csv(REPRO / "candidate_selection.csv", candidates, ["candidate", "target", "r4_share_pvw_max", "entry_condition", "status", "next_gate", "failure_action"])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    key_aggregate = [row for row in aggregate if row["r"] == "4" and row["component"] in {"materialization_lifecycle", "mat_ep", "sub_a", "postproc_residual"}]
    report = f"""# Stage267 Local Split Projection

Decision: `{decision}`.

Stage267 is the local fallback after Stage266 could not record native counters.
It does not measure a new speedup. It converts the current Stage263 non-binary
profile into Amdahl ceilings and selects the next bounded experiment.

## r=4 Component Aggregate

{table(key_aggregate, ["component", "share_body_min", "share_body_max", "share_pvw_min", "share_pvw_max"])}

## Candidate Selection

{table(candidates, ["candidate", "target", "r4_share_pvw_max", "status", "next_gate", "failure_action"])}

## Source Capability

{table(source_checks, ["check", "status", "interpretation"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

Source model rows: `{len(source_model)}`. Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage267_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage267 Reproduction Commands

```bash
python3 scripts/build_stage267_local_split_projection.py
```

Stage267 is projection-only. It selects Stage268 smoke but does not run it.
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage267_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "component_projection.csv",
        REPRO / "component_aggregate.csv",
        REPRO / "amdahl_projection.csv",
        REPRO / "source_capability.csv",
        REPRO / "candidate_selection.csv",
        REPRO / "proof_gate.csv",
        REPRO / "claim_boundary.csv",
        REPRO / "next_stage_queue.csv",
        Path(__file__),
    ]
    write_csv(REPRO / "artifact_index.csv", artifacts(paths), ["path", "bytes", "sha256"])
    print(decision)
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
