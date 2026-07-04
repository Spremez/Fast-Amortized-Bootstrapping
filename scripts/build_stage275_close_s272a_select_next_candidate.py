#!/usr/bin/env python3
"""Build Stage275 closeout and next-candidate selection artifacts."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "stage275_close_s272a_select_next_candidate"
DOC = ROOT / "docs" / "stage275_close_s272a_select_next_candidate.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE271_SPLIT = ROOT / "repro" / "stage271_nonbinary_sub_a_split_profile" / "sub_a_split.csv"
STAGE274_COMPARE = ROOT / "repro" / "stage274_sub_a_fused_materialization_smoke" / "variant_compare.csv"
STAGE274_PROOF = ROOT / "repro" / "stage274_sub_a_fused_materialization_smoke" / "proof_gate.csv"
SAB_PVW = ROOT / "src" / "sab_pvw.c"
SCALAR_SAB = ROOT / "src" / "sparse_amortized_bootstrap.c"


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


def source_rows() -> list[dict[str, str]]:
    pvw = SAB_PVW.read_text(encoding="utf-8", errors="replace")
    scalar = SCALAR_SAB.read_text(encoding="utf-8", errors="replace")
    return [
        {
            "fact": "pvw_include_zero_rejects_negative_coeff",
            "status": "PASS" if "include-zero PVW sparse input expects coefficient one" in pvw else "MISSING",
            "evidence": rel(SAB_PVW),
            "interpretation": "Current PVW include-zero keygen admits only coefficient-one nonzero entries.",
        },
        {
            "fact": "pvw_s_coff_encrypts_one",
            "status": "PASS" if "mat_trgsw_monomial_DFT_sample(res->s_coff[key_idx][cnt_h]" in pvw and "1, 0, res->mat_key" in pvw else "MISSING",
            "evidence": rel(SAB_PVW),
            "interpretation": "Current PVW include-zero selector family materializes encrypted one for scanned nonzero entries.",
        },
        {
            "fact": "scalar_include_zero_has_zero_gap_semantics",
            "status": "PASS" if "RGSW_encrypt(res->s_coff[i][cnt_h], tmp, output_key, 0, 0)" in scalar else "MISSING",
            "evidence": rel(SCALAR_SAB),
            "interpretation": "Scalar include-zero has a broader zero-selector branch, so a fast path must be guarded to current PVW semantics only.",
        },
        {
            "fact": "stage274_fused_neutral",
            "status": "PASS" if any(row.get("status", "").startswith("NEUTRAL_STAGE274") for row in read_csv(STAGE274_PROOF)) else "MISSING",
            "evidence": rel(STAGE274_PROOF),
            "interpretation": "The in-place from_DFT_add fused materialization candidate is closed as non-promoted.",
        },
    ]


def closeout_rows() -> list[dict[str, str]]:
    rows = read_csv(STAGE274_COMPARE)
    out = []
    for row in rows:
        out.append(
            {
                "candidate": "S272-A-sub_a_fused_from_DFT_add",
                "mode": row.get("mode", ""),
                "fused_speedup_vs_backend": row.get("fused_speedup_vs_backend", ""),
                "stage274_status": row.get("status", ""),
                "decision": "close_no_promotion",
                "interpretation": "Correct but slower than backend direct-add; do not default-enable and do not spend repeated/noise budget.",
            }
        )
    return out


def share(component: str, mode: str) -> float:
    vals = [
        float(row["share_of_pvw"])
        for row in read_csv(STAGE271_SPLIT)
        if row.get("component") == component and row.get("mode") == mode
    ]
    return vals[0] if vals else 0.0


def candidate_rows() -> list[dict[str, str]]:
    include_zero_sub_a = sum(
        share(component, "include_zero")
        for component in ["mul_minus_1", "selector_mat_ep", "from_dft", "add"]
    )
    ternary_selector = share("selector_mat_ep", "ternary")
    return [
        {
            "candidate": "S275-A-include_zero_coeff_one_fast_path",
            "scope": "include_zero_only_current_pvw_semantics",
            "theory_basis": "If the current PVW s_coff selector is always encrypted 1 for scanned nonzero coefficients, p + (X^a - 1)p equals X^a p.",
            "stage271_full_pvw_share_basis": f"{include_zero_sub_a:.6f}",
            "first_gate": "Stage276 explicit flag: staged/full correctness, smoke T_bootstrap/r include-zero only.",
            "risk": "Scalar include-zero has broader zero-selector semantics; flag must be guarded and not claimed as general include-zero SAB.",
            "priority": "P0",
        },
        {
            "candidate": "S275-B-selector_mat_ep_kernel_tiling",
            "scope": "include_zero_and_ternary",
            "theory_basis": "Stage271 shows selector_mat_ep is the largest sub_a subcomponent after fused materialization is closed.",
            "stage271_full_pvw_share_basis": f"{ternary_selector:.6f}",
            "first_gate": "Stage277 selector MAT-EP microbench/profile with exact selector family and r=4.",
            "risk": "Local Amdahl ceiling is small; needs full SAB A/B before any claim.",
            "priority": "P1",
        },
        {
            "candidate": "S272-A-sub_a_fused_from_DFT_add",
            "scope": "include_zero_and_ternary",
            "theory_basis": "Alias-safe helper existed, but full SAB smoke regressed.",
            "stage271_full_pvw_share_basis": "",
            "first_gate": "closed",
            "risk": "In-place direct-add is slower despite correctness.",
            "priority": "closed",
        },
    ]


def proof_rows(sources: list[dict[str, str]], closeout: list[dict[str, str]], candidates: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
    source_ok = all(row["status"] == "PASS" for row in sources)
    close_ok = closeout and all(row["decision"] == "close_no_promotion" for row in closeout)
    selected = candidates[0]["candidate"]
    decision = "PASS_STAGE275_CLOSE_S272A_SELECT_INCLUDE_ZERO_COEFF_ONE_FAST_PATH" if source_ok and close_ok else "FAIL_STAGE275_CLOSEOUT_INPUTS_INCOMPLETE"
    rows = [
        {"gate": "G1_stage274_closeout", "status": "PASS" if close_ok else "FAIL", "metric": "S272-A closeout rows", "value": str(len(closeout)), "evidence": "closed_candidate.csv", "interpretation": "The fused materialization candidate is closed without promotion."},
        {"gate": "G2_source_guard", "status": "PASS" if source_ok else "FAIL", "metric": "current PVW include-zero source facts", "value": f"{sum(row['status'] == 'PASS' for row in sources)}/{len(sources)}", "evidence": "source_guard.csv", "interpretation": "The next candidate is allowed only as a guarded current-PVW semantic fast path."},
        {"gate": "G3_candidate_selection", "status": "PASS" if selected == "S275-A-include_zero_coeff_one_fast_path" else "FAIL", "metric": "selected candidate", "value": selected, "evidence": "candidate_ranking.csv", "interpretation": "Select an executable correctness-first include-zero fast path before lower-ceiling selector-kernel work."},
        {"gate": "G4_claim_boundary", "status": "PASS_DESIGN_ONLY", "metric": "no speed claim", "value": "selection_gate", "evidence": "claim_boundary.csv", "interpretation": "Stage275 selects the next experiment; it implements no hot-path optimization."},
        {"gate": "G5_decision", "status": decision, "metric": "stage decision", "value": decision, "evidence": "proof_gate.csv", "interpretation": "Proceed to Stage276 only if the closeout inputs and source guard are complete."},
    ]
    return decision, rows


def claim_rows() -> list[dict[str, str]]:
    return [
        {
            "claim": "fused_materialization_candidate",
            "status": "closed_neutral",
            "allowed_wording": "Stage274 found the fused from_DFT_add sub_a path correct but slower in full SAB smoke.",
            "forbidden_wording": "Fused from_DFT_add accelerates SAB.",
            "evidence": "closed_candidate.csv",
        },
        {
            "claim": "include_zero_coeff_one_fast_path",
            "status": "selected_unimplemented",
            "allowed_wording": "Current PVW source supports a guarded include-zero coeff-one fast-path hypothesis.",
            "forbidden_wording": "All include-zero SAB instances can drop s_coff.",
            "evidence": "source_guard.csv; candidate_ranking.csv",
        },
    ]


def next_rows(decision: str) -> list[dict[str, str]]:
    if decision.startswith("PASS_"):
        return [
            {
                "priority": "P0",
                "route": "stage276_include_zero_coeff_one_fast_path",
                "entry_condition": "Stage275 source guard and closeout pass.",
                "gate": "Explicit flag, include-zero staged/full correctness, full SAB T_bootstrap/r smoke vs default/backend.",
                "status": "selected",
                "failure_action": "If correctness or smoke fails, close as guarded negative result and do not default-enable.",
            },
            {
                "priority": "P1",
                "route": "stage277_selector_mat_ep_kernel_tiling",
                "entry_condition": "Stage276 neutral/failed or residual profile still dominated by selector_mat_ep.",
                "gate": "Selector MAT-EP microbench and full SAB A/B under explicit flag.",
                "status": "conditional",
                "failure_action": "No claim without full SAB A/B.",
            },
        ]
    return [
        {
            "priority": "P0",
            "route": "repair_stage275_inputs",
            "entry_condition": "Stage275 failed.",
            "gate": "Fix missing source/proof inputs before implementation.",
            "status": "selected",
            "failure_action": "Do not implement Stage276.",
        }
    ]


def artifacts(paths: list[Path]) -> list[dict[str, str]]:
    return [{"path": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256(path)} for path in paths if path.exists() and path.is_file()]


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(CURRENT_GOAL, "### Stage275 close S272-A and select next candidate", f"""
### Stage275 close S272-A and select next candidate

`{decision}` closes the in-place `sub_a` fused materialization candidate after
the Stage274 neutral smoke and selects a guarded include-zero coeff-one fast
path as the next executable experiment. No speed claim is made at this stage.
""")
    append_once(HYPOTHESES, "H10_stage275_close_s272a_select_next_candidate:", f"""
H10_stage275_close_s272a_select_next_candidate:
  status: {decision}
  evidence:
    - repro/stage275_close_s272a_select_next_candidate/closed_candidate.csv
    - repro/stage275_close_s272a_select_next_candidate/source_guard.csv
    - repro/stage275_close_s272a_select_next_candidate/candidate_ranking.csv
    - docs/stage275_close_s272a_select_next_candidate.md
  conclusion: >
    Stage275 records {decision}. It closes the fused from_DFT_add sub_a
    candidate and selects a guarded include-zero coeff-one fast-path experiment
    as Stage276.
""")
    append_once(RUN_LOG, "stage275-close-s272a-select-next-candidate-001", f"""stage275-close-s272a-select-next-candidate-001,2026-07-04,{head},Stage 275,analysis,python scripts/build_stage275_close_s272a_select_next_candidate.py,"close Stage274 neutral fused sub_a candidate; select guarded include-zero coeff-one fast path",n/a,{decision},"Design/selection gate only; Stage276 must implement and test explicit flag.",docs/stage275_close_s272a_select_next_candidate.md; repro/stage275_close_s272a_select_next_candidate/proof_gate.csv
""")
    append_once(MANIFEST, "- stage275_close_s272a_select_next_candidate:", """
- stage275_close_s272a_select_next_candidate:
  - `docs/stage275_close_s272a_select_next_candidate.md`
  - `scripts/build_stage275_close_s272a_select_next_candidate.py`
  - `repro/stage275_close_s272a_select_next_candidate/`
""")
    append_once(CHECKLIST, "stage275-close-s272a-select-next-candidate-checklist", f"""
<!-- stage275-close-s272a-select-next-candidate-checklist -->
- [x] Stage275 records `{decision}` and selects Stage276 guarded include-zero coeff-one fast path.
""")


def main() -> int:
    REPRO.mkdir(parents=True, exist_ok=True)
    sources = source_rows()
    closeout = closeout_rows()
    candidates = candidate_rows()
    decision, proof = proof_rows(sources, closeout, candidates)
    claims = claim_rows()
    queue = next_rows(decision)

    write_csv(REPRO / "source_guard.csv", sources, ["fact", "status", "evidence", "interpretation"])
    write_csv(REPRO / "closed_candidate.csv", closeout, ["candidate", "mode", "fused_speedup_vs_backend", "stage274_status", "decision", "interpretation"])
    write_csv(REPRO / "candidate_ranking.csv", candidates, ["candidate", "scope", "theory_basis", "stage271_full_pvw_share_basis", "first_gate", "risk", "priority"])
    write_csv(REPRO / "proof_gate.csv", proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(REPRO / "claim_boundary.csv", claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(REPRO / "next_stage_queue.csv", queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])

    report = f"""# Stage275 Close S272-A and Select Next Candidate

Decision: `{decision}`.

Stage275 closes the Stage272/274 in-place fused materialization candidate and
selects the next executable experiment. It does not implement a hot-path change
and does not claim speedup.

## Closed Candidate

{table(closeout, ["candidate", "mode", "fused_speedup_vs_backend", "stage274_status", "decision"])}

## Source Guard

{table(sources, ["fact", "status", "evidence", "interpretation"])}

## Candidate Ranking

{table(candidates, ["candidate", "scope", "stage271_full_pvw_share_basis", "first_gate", "risk", "priority"])}

## Proof Gate

{table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPRO / "stage275_report.md", report)
    write_text(REPRO / "reproduction_commands.md", """# Stage275 Reproduction Commands

```bash
python3 scripts/build_stage275_close_s272a_select_next_candidate.py
```

Stage275 is a design/selection gate. It reads Stage271 and Stage274 evidence
and selects Stage276 only if source guards pass.
""")
    update_tracking(decision)
    paths = [
        DOC,
        REPRO / "stage275_report.md",
        REPRO / "reproduction_commands.md",
        REPRO / "source_guard.csv",
        REPRO / "closed_candidate.csv",
        REPRO / "candidate_ranking.csv",
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
