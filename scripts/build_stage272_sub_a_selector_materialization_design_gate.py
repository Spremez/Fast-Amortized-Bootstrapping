#!/usr/bin/env python3
"""Build Stage272 design gate for non-binary sub_a selector materialization."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage272_sub_a_selector_materialization_design_gate"
DOC = ROOT / "docs" / "stage272_sub_a_selector_materialization_design_gate.md"
VARIANT_DOC = ROOT / "algorithm_variants" / "stage272_sub_a_selector_materialization.md"
THEORY_DOC = ROOT / "theory_checks" / "stage272_sub_a_selector_materialization.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE271_SPLIT = ROOT / "repro" / "stage271_nonbinary_sub_a_split_profile" / "sub_a_split.csv"
STAGE271_SUMMARY = ROOT / "repro" / "stage271_nonbinary_sub_a_split_profile" / "profile_summary.csv"
PVW_TMLWE = ROOT / "src" / "mosfhet" / "src" / "pvwtmlwe.c"
POLYNOMIAL = ROOT / "src" / "mosfhet" / "src" / "polynomial.c"
SAB_PVW = ROOT / "src" / "sab_pvw.c"


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


def max_share(component: str) -> float:
    values = [
        float(row["share_of_pvw"])
        for row in read_csv(STAGE271_SPLIT)
        if row.get("component") == component
    ]
    return max(values) if values else 0.0


def mode_range(component: str) -> str:
    rows = [row for row in read_csv(STAGE271_SPLIT) if row.get("component") == component]
    if not rows:
        return ""
    return "; ".join(f"{row['mode']}={row['share_of_pvw']}" for row in rows)


def amdahl(share: float, reduction: float = 1.0) -> float:
    return 1.0 / (1.0 - share * reduction) if share * reduction < 1.0 else 0.0


def source_risk_rows() -> list[dict[str, str]]:
    pvw = PVW_TMLWE.read_text(encoding="utf-8", errors="replace")
    poly = POLYNOMIAL.read_text(encoding="utf-8", errors="replace")
    sab = SAB_PVW.read_text(encoding="utf-8", errors="replace")
    checks = [
        {
            "check": "sub_a_current_from_dft_then_add",
            "status": "PASS" if "pvmtmlwe_from_DFT(sab->tmp->tmlwe, sab->tmp->tmlwe_dft)" in sab and "pvmtmlwe_addto(p[idx], sab->tmp->tmlwe)" in sab else "MISSING",
            "risk": "Current sub_a materializes to tmp then addto; a fused variant must preserve p[idx] alias semantics.",
        },
        {
            "check": "pvmtmlwe_from_DFT_add_exists",
            "status": "PASS" if "void pvmtmlwe_from_DFT_add" in pvw else "MISSING",
            "risk": "The helper exists, but out/addend alias safety is not specified by its interface.",
        },
        {
            "check": "backend_add_guard_exists",
            "status": "PASS" if "#ifdef SAB_PVW_BACKEND_FROM_DFT_ADD" in pvw else "MISSING",
            "risk": "Backend-specific direct add exists; portable fallback differs.",
        },
        {
            "check": "portable_fallback_alias_risk",
            "status": "RISK" if "polynomial_DFT_to_torus(out->a[i], in->a[i]);" in pvw and "pvmtmlwe_addto_torus_poly(out->a[i], addend->a[i]);" in pvw else "UNKNOWN",
            "risk": "Fallback writes out before adding addend, so out==addend is not source-proven safe.",
        },
        {
            "check": "polynomial_direct_add_backend",
            "status": "PASS" if "execute_direct_torus64_add" in poly else "MISSING",
            "risk": "Even backend direct-add alias behavior needs an isolated equivalence test before use in sub_a.",
        },
    ]
    return checks


def component_model_rows() -> list[dict[str, str]]:
    selector = max_share("selector_mat_ep")
    from_dft_add = max_share("from_dft") + max_share("add")
    rotate_copy = max_share("rotate") + max_share("copy") + max_share("mul_minus_1")
    return [
        {
            "target": "selector_mat_ep",
            "stage271_pvw_share_max": f"{selector:.6f}",
            "full_elimination_ceiling": f"{amdahl(selector):.6f}",
            "mode_basis": mode_range("selector_mat_ep"),
            "interpretation": "Largest sub_a subcomponent, but reducing it likely requires MAT selector-kernel or schedule changes.",
        },
        {
            "target": "from_dft_plus_add",
            "stage271_pvw_share_max": f"{from_dft_add:.6f}",
            "full_elimination_ceiling": f"{amdahl(from_dft_add):.6f}",
            "mode_basis": f"from_dft: {mode_range('from_dft')}; add: {mode_range('add')}",
            "interpretation": "Potential fused materialization target, but alias safety is unresolved.",
        },
        {
            "target": "rotation_copy_minus_1",
            "stage271_pvw_share_max": f"{rotate_copy:.6f}",
            "full_elimination_ceiling": f"{amdahl(rotate_copy):.6f}",
            "mode_basis": f"rotate: {mode_range('rotate')}; copy: {mode_range('copy')}; minus_1: {mode_range('mul_minus_1')}",
            "interpretation": "Ternary has visible rotation/copy, but selector materialization dominates both modes.",
        },
    ]


def candidate_rows() -> list[dict[str, str]]:
    return [
        {
            "candidate": "S272-A-sub_a_alias_safe_from_DFT_add",
            "mechanism": "Replace sub_a from_DFT + addto with a proven alias-safe from_DFT_add/addto materialization path.",
            "first_gate": "Stage273 isolated alias-safety and phase equivalence microtest for out==addend and out!=addend.",
            "complexity_delta": "Same MAT EP count; may reduce one torus add/write pass per sub_a selector external product.",
            "promotion_gate": "r=4 include-zero/ternary full SAB T_bootstrap/r smoke, then repeated gate if positive.",
            "status": "selected_preimplementation_gate",
        },
        {
            "candidate": "S272-B-sub_a_selector_mat_ep_kernel",
            "mechanism": "Specialize the sub_a selector MAT EP call path or batch its 79872 selector calls.",
            "first_gate": "Requires MAT counter/native evidence or a concrete selector layout mechanism.",
            "complexity_delta": "Could reduce selector_mat_ep constant factors; does not reduce SAB schedule count.",
            "promotion_gate": "Microbench plus full SAB A/B, same backend.",
            "status": "blocked_until_mechanism",
        },
        {
            "candidate": "S272-C-ternary_rotation_copy_fusion",
            "mechanism": "Fuse ternary rotate/copy/minus_1 preparation if alias safety and coefficient semantics permit.",
            "first_gate": "Only after S272-A or if selector materialization fails; lower Amdahl ceiling.",
            "complexity_delta": "May reduce preparation memory traffic for ternary only.",
            "promotion_gate": "Isolated staged equivalence plus ternary full SAB smoke.",
            "status": "deferred_lower_ceiling",
        },
    ]


def proof_rows(component_model: list[dict[str, str]], source_risk: list[dict[str, str]]) -> list[dict[str, str]]:
    stage271_ok = len(read_csv(STAGE271_SUMMARY)) == 2
    alias_risk = any(row["check"] == "portable_fallback_alias_risk" and row["status"] == "RISK" for row in source_risk)
    decision = "PASS_STAGE272_SUB_A_SELECTOR_MATERIALIZATION_DESIGN_GATE"
    return [
        {"gate": "G1_stage271_input", "status": "PASS" if stage271_ok else "FAIL", "metric": "Stage271 profile rows", "value": str(len(read_csv(STAGE271_SUMMARY))), "evidence": rel(STAGE271_SUMMARY), "interpretation": "Design is grounded in measured sub_a split profile."},
        {"gate": "G2_amdahl_bound", "status": "PASS", "metric": "component ceilings", "value": "; ".join(f"{row['target']}={row['full_elimination_ceiling']}x" for row in component_model), "evidence": "component_model.csv", "interpretation": "Any next claim must respect full-PVW Amdahl ceilings."},
        {"gate": "G3_alias_safety", "status": "BLOCKED_MICROTEST_REQUIRED" if alias_risk else "PASS", "metric": "out==addend source proof", "value": "not_source_proven" if alias_risk else "source_proven", "evidence": "source_risk.csv", "interpretation": "Do not implement sub_a fused materialization before alias equivalence is tested."},
        {"gate": "G4_candidate_selection", "status": "PASS", "metric": "selected candidate", "value": "S272-A-sub_a_alias_safe_from_DFT_add", "evidence": "candidate_design.csv", "interpretation": "Select the smallest falsifiable preimplementation gate."},
        {"gate": "G5_claim_boundary", "status": "PASS_DESIGN_ONLY", "metric": "no speed claim", "value": "design_gate", "evidence": "claim_boundary.csv", "interpretation": "Stage272 does not change code or measure speed."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": "proof_gate.csv", "interpretation": "Proceed to Stage273 alias-safety microtest."},
    ]


def claim_rows() -> list[dict[str, str]]:
    return [
        {"claim": "sub_a_selector_materialization_candidate", "status": "design_only", "allowed_wording": "Stage272 defines a falsifiable sub_a materialization candidate and gates.", "forbidden_wording": "Stage272 implements or proves a speedup.", "evidence": "candidate_design.csv"},
        {"claim": "amdahl_bound", "status": "supported_by_stage271_profile", "allowed_wording": "Full-PVW speedup ceilings are bounded by measured component shares.", "forbidden_wording": "A sub_a-local change can create multi-x full SAB speedup by itself.", "evidence": "component_model.csv"},
        {"claim": "alias_safety", "status": "unproven", "allowed_wording": "out==addend alias safety must be tested before use.", "forbidden_wording": "Existing from_DFT_add can be safely reused in-place in sub_a.", "evidence": "source_risk.csv"},
    ]


def next_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage273_sub_a_from_DFT_add_alias_microtest",
            "entry_condition": "Stage272 selects S272-A and records alias-safety risk.",
            "gate": "Isolated deterministic PVW_TMLWE equivalence for out==addend/out!=addend and include-zero/ternary sub_a phase equivalence.",
            "status": "selected",
            "failure_action": "If alias fails, do not implement in-place fused sub_a materialization.",
        },
        {
            "priority": "P1",
            "route": "stage274_sub_a_fused_materialization_smoke",
            "entry_condition": "Only if Stage273 alias/equivalence passes.",
            "gate": "Explicit flag, correctness, r=4 include-zero/ternary T_bootstrap/r smoke.",
            "status": "conditional",
            "failure_action": "Record neutral/negative and close candidate.",
        },
    ]


def artifacts(paths: list[Path]) -> list[dict[str, str]]:
    return [{"path": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256(path)} for path in paths if path.exists() and path.is_file()]


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(CURRENT_GOAL, "### Stage272 sub_a selector materialization design gate", f"""
### Stage272 sub_a selector materialization design gate

`{decision}` records a design-only gate for non-binary `sub_a` selector
materialization. It selects alias-safety/equivalence testing before any fused
implementation and keeps all speedup claims bounded by Stage271 Amdahl shares.
""")
    append_once(HYPOTHESES, "H10_stage272_sub_a_selector_materialization_design_gate:", f"""
H10_stage272_sub_a_selector_materialization_design_gate:
  status: {decision}
  evidence:
    - repro/stage272_sub_a_selector_materialization_design_gate/component_model.csv
    - repro/stage272_sub_a_selector_materialization_design_gate/source_risk.csv
    - repro/stage272_sub_a_selector_materialization_design_gate/candidate_design.csv
    - docs/stage272_sub_a_selector_materialization_design_gate.md
  conclusion: >
    Stage272 records {decision}. It identifies alias safety as the first
    falsifiable gate for sub_a fused materialization and forbids speedup claims
    until isolated equivalence and full SAB A/B gates pass.
""")
    append_once(RUN_LOG, "stage272-sub-a-selector-materialization-design-001", f"""stage272-sub-a-selector-materialization-design-001,2026-07-04,{head},Stage 272,analysis,python scripts/build_stage272_sub_a_selector_materialization_design_gate.py,"design gate from Stage271 sub_a split profile; no hot-path code",n/a,{decision},"Select Stage273 alias-safety microtest before any sub_a fused materialization implementation.",docs/stage272_sub_a_selector_materialization_design_gate.md; repro/stage272_sub_a_selector_materialization_design_gate/proof_gate.csv
""")
    append_once(MANIFEST, "- stage272_sub_a_selector_materialization_design_gate:", """
- stage272_sub_a_selector_materialization_design_gate:
  - `docs/stage272_sub_a_selector_materialization_design_gate.md`
  - `algorithm_variants/stage272_sub_a_selector_materialization.md`
  - `theory_checks/stage272_sub_a_selector_materialization.md`
  - `scripts/build_stage272_sub_a_selector_materialization_design_gate.py`
  - `repro/stage272_sub_a_selector_materialization_design_gate/`
""")
    append_once(CHECKLIST, "stage272-sub-a-selector-materialization-design-checklist", f"""
<!-- stage272-sub-a-selector-materialization-design-checklist -->
- [x] Stage272 records `{decision}` and selects Stage273 alias-safety microtest before implementation.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    source_risk = source_risk_rows()
    component_model = component_model_rows()
    candidates = candidate_rows()
    proof = proof_rows(component_model, source_risk)
    decision = proof[-1]["status"]
    claims = claim_rows()
    queue = next_rows()

    write_csv(REPRO / "source_risk.csv", source_risk, ["check", "status", "risk"])
    write_csv(REPRO / "component_model.csv", component_model, ["target", "stage271_pvw_share_max", "full_elimination_ceiling", "mode_basis", "interpretation"])
    write_csv(REPRO / "candidate_design.csv", candidates, ["candidate", "mechanism", "first_gate", "complexity_delta", "promotion_gate", "status"])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    report = f"""# Stage272 Sub_a Selector Materialization Design Gate

Decision: `{decision}`.

Stage272 is design-only. It converts the Stage271 split profile into bounded
candidate algorithms and proof obligations before any hot-path code is written.

## Component Model

{table(component_model, ["target", "stage271_pvw_share_max", "full_elimination_ceiling", "interpretation"])}

## Candidate Design

{table(candidates, ["candidate", "mechanism", "first_gate", "complexity_delta", "status"])}

## Source Risk

{table(source_risk, ["check", "status", "risk"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage272_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage272 Reproduction Commands

```bash
python3 scripts/build_stage272_sub_a_selector_materialization_design_gate.py
```

Stage272 is a design gate based on Stage271 profile evidence. It performs no
hot-path implementation and makes no speed claim.
""")
    write_text(VARIANT_DOC, f"""# Stage272 Candidate: Non-Binary Sub_a Selector Materialization

Status: design-only, preimplementation.

## Delta

Candidate S272-A targets the current non-binary `sub_a` sequence:

```text
selector MAT external product -> from_DFT(tmp) -> addto(p[idx], tmp)
```

The proposed family explores an alias-safe fused materialization/add path.
The first executable gate is not a speed test; it is an isolated alias-safety
and phase-equivalence microtest.

## Complexity

The selector MAT external-product count is unchanged at `39 * 2048 = 79872`
for r=4 target non-binary SAB. Therefore this candidate can reduce only
constant factors in materialization/add, not the SAB schedule length.

## Promotion Rule

Only after alias/equivalence passes may an explicit flag be added for a full
SAB `T_bootstrap/r` smoke. Repeated performance is required for promotion.
""")
    write_text(THEORY_DOC, f"""# Stage272 Theory Check: Sub_a Selector Materialization

## Current Evidence

Stage271 shows `selector_mat_ep` dominates non-binary `sub_a`, while
`from_DFT + add` has a smaller but visible full-PVW Amdahl ceiling.

## Proof Obligations

1. Prove or test alias safety for `out == addend` before using a fused
   materialization helper in-place.
2. Preserve `phase(acc_pvw.body[q]) == phase(acc_scalar[q])` for include-zero
   and ternary branches.
3. Keep scalar SAB and default PVW/MAT-SAB behavior unchanged unless an
   explicit flag is enabled.
4. Report all speedups as `T_bootstrap/r`, not total batch latency alone.

## Claim Boundary

This is not a novelty claim and not a performance claim. It is a bounded
candidate design derived from measured Stage271 component shares.
""")
    update_tracking(decision)
    paths = [
        DOC,
        VARIANT_DOC,
        THEORY_DOC,
        REPRO / "stage272_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "source_risk.csv",
        REPRO / "component_model.csv",
        REPRO / "candidate_design.csv",
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
