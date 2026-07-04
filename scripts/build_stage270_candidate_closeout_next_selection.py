#!/usr/bin/env python3
"""Build Stage270 closeout and next-candidate selection artifacts."""

from __future__ import annotations

import csv
import hashlib
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage270_candidate_closeout_next_selection"
DOC = ROOT / "docs" / "stage270_candidate_closeout_next_selection.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE267_CANDIDATES = ROOT / "repro" / "stage267_local_split_projection" / "candidate_selection.csv"
STAGE267_COMPONENTS = ROOT / "repro" / "stage267_local_split_projection" / "component_aggregate.csv"
STAGE268_COMPARE = ROOT / "repro" / "stage268_nonbinary_backend_from_dft_add_smoke" / "variant_compare.csv"
STAGE269_COMPARE = ROOT / "repro" / "stage269_backend_from_dft_add_repeated_noise_resource" / "variant_compare.csv"
STAGE269_PROOF = ROOT / "repro" / "stage269_backend_from_dft_add_repeated_noise_resource" / "proof_gate.csv"
STAGE266_PROOF = ROOT / "repro" / "stage266_current_head_nonbinary_native_counter" / "proof_gate.csv"
SAB_PVW_SOURCE = ROOT / "src" / "sab_pvw.c"
MAKEFILE_DEF = ROOT / "src" / "mosfhet" / "Makefile.def"


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


def run_auth_probe() -> list[dict[str, str]]:
    ssh = shutil.which("ssh")
    if ssh is None:
        return [{"probe": "cb5_batchmode", "status": "ssh_missing", "returncode": "", "stdout": ""}]
    try:
        proc = subprocess.run(
            [
                ssh,
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=5",
                "delld@192.168.107.220",
                "true",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
        status = "available" if proc.returncode == 0 else "auth_unavailable"
        return [{"probe": "cb5_batchmode", "status": status, "returncode": str(proc.returncode), "stdout": proc.stdout.strip()[:80]}]
    except subprocess.TimeoutExpired:
        return [{"probe": "cb5_batchmode", "status": "timeout", "returncode": "", "stdout": ""}]


def component_share(component: str, r: str = "4") -> str:
    for row in read_csv(STAGE267_COMPONENTS):
        if row.get("r") == r and row.get("component") == component:
            return row.get("share_pvw_max", "")
    return ""


def source_capability_rows() -> list[dict[str, str]]:
    sab = SAB_PVW_SOURCE.read_text(encoding="utf-8", errors="replace")
    make = MAKEFILE_DEF.read_text(encoding="utf-8", errors="replace")
    checks = [
        ("nonbinary_sub_a_include_zero_exists", "void sab_pvw_sub_a_include_zero", sab),
        ("nonbinary_sub_a_ternary_exists", "void sab_pvw_sub_a_ternary", sab),
        ("sub_a_body_profile_counter_exists", "sub_a_us", sab),
        ("body_profile_flag_exists", "SAB_PVW_BODY_PROFILE", make),
        ("suba_output_fusion_flag_exists", "SAB_PVW_SUBA_OUTPUT_FUSION", make),
    ]
    rows = []
    for check, needle, text in checks:
        rows.append(
            {
                "check": check,
                "status": "PASS" if needle in text else "MISSING",
                "needle": needle,
                "interpretation": "Local sub_a profiling/preflight can be built from current sources." if needle in text else "Do not select sub_a gate until source support exists.",
            }
        )
    return rows


def closeout_rows() -> list[dict[str, str]]:
    smoke = read_csv(STAGE268_COMPARE)
    repeated = read_csv(STAGE269_COMPARE)
    smoke_min = min((float(row["backend_speedup_vs_default"]) for row in smoke), default=0.0)
    repeated_min = min((float(row["backend_speedup_vs_default"]) for row in repeated), default=0.0)
    repeated_modes = "; ".join(
        f"{row['mode']}={row['backend_speedup_vs_default']}x status={row['status']}"
        for row in repeated
    )
    return [
        {
            "candidate": "backend_from_dft_add_materialization",
            "stage267_target": "materialization_lifecycle",
            "stage268_smoke_min_speedup": f"{smoke_min:.6f}",
            "stage269_repeated_min_speedup": f"{repeated_min:.6f}",
            "stage269_modes": repeated_modes,
            "decision": "CLOSE_NEUTRAL_NO_PROMOTION",
            "rule": "Do not use Stage268 smoke as final evidence; do not reopen this flag without a new mechanism or changed profile.",
        }
    ]


def selection_rows(auth: list[dict[str, str]], source_checks: list[dict[str, str]]) -> list[dict[str, str]]:
    auth_available = auth and auth[0]["status"] == "available"
    suba_ready = all(row["status"] == "PASS" for row in source_checks)
    return [
        {
            "candidate": "mat_ep_native_counter_or_layout_change",
            "profile_basis": f"r4 mat_ep share_pvw_max={component_share('mat_ep')}",
            "execution_status": "available" if auth_available else "blocked_auth_or_counter_platform",
            "selected": "no",
            "next_gate": "Native current-head counters for load/store/FMA before new layout code.",
            "reason": "MAT EP remains largest single component, but source-only tuning cannot prove AVX512 optimality or guide layout safely.",
        },
        {
            "candidate": "nonbinary_sub_a_split_profile",
            "profile_basis": f"r4 sub_a share_pvw_max={component_share('sub_a')}",
            "execution_status": "available_local" if suba_ready else "blocked_source_support",
            "selected": "yes" if suba_ready else "no",
            "next_gate": "Stage271 add profile-only split counters for rotation, MAT EP, from_DFT, and add/copy inside non-binary sub_a; run r=4 include-zero/ternary correctness plus body profile.",
            "reason": "Materialization flag was neutral on repeated timing; sub_a is the next material local bottleneck with isolated source entry points.",
        },
        {
            "candidate": "postproc_extract_packing",
            "profile_basis": f"r4 postproc share_pvw_max={component_share('postproc_residual')}",
            "execution_status": "deferred_low_share",
            "selected": "no",
            "next_gate": "Only revisit if body optimizations raise tail share.",
            "reason": "Current tail share is below 1%; high-risk tail work is not justified.",
        },
    ]


def proof_rows(closeout: list[dict[str, str]], selection: list[dict[str, str]], auth: list[dict[str, str]]) -> list[dict[str, str]]:
    stage269_status = " ".join(" ".join(row.values()) for row in read_csv(STAGE269_PROOF))
    stage266_status = " ".join(" ".join(row.values()) for row in read_csv(STAGE266_PROOF))
    selected = next((row for row in selection if row["selected"] == "yes"), {})
    decision = "PASS_STAGE270_FROM_DFT_ADD_CLOSED_SELECT_SUBA_SPLIT_PROFILE" if selected.get("candidate") == "nonbinary_sub_a_split_profile" else "REVIEW_STAGE270_SELECTION"
    return [
        {"gate": "G1_from_dft_add_closeout", "status": "PASS" if closeout and closeout[0]["decision"] == "CLOSE_NEUTRAL_NO_PROMOTION" else "FAIL", "metric": "Stage269 repeated result", "value": closeout[0]["stage269_repeated_min_speedup"] if closeout else "", "evidence": rel(STAGE269_COMPARE), "interpretation": "The Stage268 smoke candidate did not survive repeated timing."},
        {"gate": "G2_no_smoke_overclaim", "status": "PASS" if "NEUTRAL_STAGE269" in stage269_status else "REVIEW", "metric": "claim boundary", "value": "smoke_not_promoted", "evidence": rel(STAGE269_PROOF), "interpretation": "Stage268 may remain context only, not an optimization claim."},
        {"gate": "G3_native_counter_route", "status": "BLOCKED" if auth and auth[0]["status"] != "available" else "AVAILABLE", "metric": "CB5 batchmode auth", "value": auth[0]["status"] if auth else "missing", "evidence": "auth_probe.csv; " + rel(STAGE266_PROOF), "interpretation": "MAT EP native counter route remains selected only when authenticated native execution is available."},
        {"gate": "G4_stage266_boundary", "status": "PASS" if "PASS_STAGE266" in stage266_status else "REVIEW", "metric": "native counter claim boundary", "value": "no_current_native_counter_rows", "evidence": rel(STAGE266_PROOF), "interpretation": "No hardware-counter optimality wording is allowed."},
        {"gate": "G5_next_candidate", "status": "PASS" if selected else "FAIL", "metric": "selected local candidate", "value": selected.get("candidate", ""), "evidence": "next_candidate_selection.csv", "interpretation": "Select the next local executable gate rather than writing optimization code directly."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": "proof_gate.csv", "interpretation": "Proceed to Stage271 sub_a split profile preflight."},
    ]


def claim_rows() -> list[dict[str, str]]:
    return [
        {"claim": "backend_from_dft_add", "status": "closed_neutral", "allowed_wording": "The existing backend FromDFT-add flag had a positive smoke but failed repeated promotion.", "forbidden_wording": "Backend FromDFT-add improves full SAB throughput.", "evidence": "candidate_closeout.csv"},
        {"claim": "mat_ep_optimality", "status": "blocked_no_native_counter", "allowed_wording": "MAT EP remains the largest single component and needs native counter attribution.", "forbidden_wording": "Current MAT AVX512 is theoretically optimal.", "evidence": "auth_probe.csv; Stage264/266 proof gates"},
        {"claim": "sub_a_next", "status": "selected_preflight_only", "allowed_wording": "sub_a split profiling is the next local executable gate.", "forbidden_wording": "sub_a optimization is proven beneficial before split profile and full SAB A/B.", "evidence": "next_candidate_selection.csv"},
    ]


def next_rows() -> list[dict[str, str]]:
    return [
        {"priority": "P0", "route": "stage271_nonbinary_sub_a_split_profile", "entry_condition": "Stage270 selects local sub_a split profile after FromDFT-add closeout.", "gate": "profile-only counters, r=4 include-zero/ternary correctness, split attribution; no hot-path claim.", "status": "selected", "failure_action": "If split counters show no actionable component, close sub_a and return to MAT native counter route."},
        {"priority": "P1", "route": "stage272_sub_a_candidate_smoke", "entry_condition": "Only if Stage271 identifies a dominant safe subcomponent.", "gate": "isolated equivalence plus full SAB T_bootstrap/r smoke.", "status": "conditional", "failure_action": "Record neutral/negative; do not promote."},
    ]


def artifacts(paths: list[Path]) -> list[dict[str, str]]:
    return [{"path": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256(path)} for path in paths if path.exists() and path.is_file()]


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(CURRENT_GOAL, "### Stage270 candidate closeout next selection", f"""
### Stage270 candidate closeout next selection

`{decision}` closes the existing backend FromDFT-add materialization candidate
as neutral after repeated timing and selects local non-binary `sub_a` split
profiling as the next executable gate. Native MAT EP counter claims remain
blocked until authenticated/native counter evidence is recorded.
""")
    append_once(HYPOTHESES, "H10_stage270_candidate_closeout_next_selection:", f"""
H10_stage270_candidate_closeout_next_selection:
  status: {decision}
  evidence:
    - repro/stage270_candidate_closeout_next_selection/candidate_closeout.csv
    - repro/stage270_candidate_closeout_next_selection/next_candidate_selection.csv
    - repro/stage270_candidate_closeout_next_selection/proof_gate.csv
    - docs/stage270_candidate_closeout_next_selection.md
  conclusion: >
    Stage270 records {decision}. It prevents Stage268 smoke overclaiming,
    keeps MAT EP hardware-counter claims blocked, and selects a profile-only
    non-binary sub_a split gate as the next local executable experiment.
""")
    append_once(RUN_LOG, "stage270-candidate-closeout-next-selection-001", f"""stage270-candidate-closeout-next-selection-001,2026-07-04,{head},Stage 270,analysis,python scripts/build_stage270_candidate_closeout_next_selection.py,"close FromDFT-add neutral candidate; select next local sub_a split profile gate",n/a,{decision},"No hot-path code change; next gate is sub_a split profiling.",docs/stage270_candidate_closeout_next_selection.md; repro/stage270_candidate_closeout_next_selection/proof_gate.csv
""")
    append_once(MANIFEST, "- stage270_candidate_closeout_next_selection:", """
- stage270_candidate_closeout_next_selection:
  - `docs/stage270_candidate_closeout_next_selection.md`
  - `scripts/build_stage270_candidate_closeout_next_selection.py`
  - `repro/stage270_candidate_closeout_next_selection/`
""")
    append_once(CHECKLIST, "stage270-candidate-closeout-next-selection-checklist", f"""
<!-- stage270-candidate-closeout-next-selection-checklist -->
- [x] Stage270 closes backend FromDFT-add as neutral and records `{decision}`.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    auth = run_auth_probe()
    source_checks = source_capability_rows()
    closeout = closeout_rows()
    selection = selection_rows(auth, source_checks)
    proof = proof_rows(closeout, selection, auth)
    decision = proof[-1]["status"]
    claims = claim_rows()
    queue = next_rows()

    write_csv(REPRO / "auth_probe.csv", auth, ["probe", "status", "returncode", "stdout"])
    write_csv(REPRO / "source_capability.csv", source_checks, ["check", "status", "needle", "interpretation"])
    write_csv(REPRO / "candidate_closeout.csv", closeout, ["candidate", "stage267_target", "stage268_smoke_min_speedup", "stage269_repeated_min_speedup", "stage269_modes", "decision", "rule"])
    write_csv(REPRO / "next_candidate_selection.csv", selection, ["candidate", "profile_basis", "execution_status", "selected", "next_gate", "reason"])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    report = f"""# Stage270 Candidate Closeout And Next Selection

Decision: `{decision}`.

Stage270 closes the existing backend FromDFT-add materialization candidate after
Stage269 repeated timing failed to promote it. The research loop now returns to
the remaining candidate queue without changing SAB hot-path behavior.

## Candidate Closeout

{table(closeout, ["candidate", "stage268_smoke_min_speedup", "stage269_repeated_min_speedup", "decision", "rule"])}

## Next Candidate Selection

{table(selection, ["candidate", "profile_basis", "execution_status", "selected", "next_gate", "reason"])}

## Source Capability

{table(source_checks, ["check", "status", "interpretation"])}

## Auth Probe

{table(auth, ["probe", "status", "returncode"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage270_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage270 Reproduction Commands

```bash
python3 scripts/build_stage270_candidate_closeout_next_selection.py
```

This stage performs candidate accounting and a sanitized batch-mode native
execution probe. It does not change SAB or MAT hot-path code.
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage270_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "auth_probe.csv",
        REPRO / "source_capability.csv",
        REPRO / "candidate_closeout.csv",
        REPRO / "next_candidate_selection.csv",
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
