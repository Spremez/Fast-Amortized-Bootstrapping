#!/usr/bin/env python3
"""Stage176: bounded security/API gate for structured compact MAT-SAB."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage176_structured_compact_security_api_gate"

SUMMARY_CSV = OUT_DIR / "summary.csv"
EVIDENCE_CSV = OUT_DIR / "evidence_matrix.csv"
API_CSV = OUT_DIR / "api_options.csv"
DECISION_CSV = OUT_DIR / "decision.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage176_structured_compact_security_api_gate.md"
PLAN_MD = ROOT / "experiments" / "stage176_structured_compact_security_api_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage176_structured_compact_security_api_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_structured_compact_security_api.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE139_SUMMARY = ROOT / "repro" / "stage139_compact_closure_audit" / "summary.csv"
STAGE171_PROOF = ROOT / "repro" / "stage171_structured_compact_keygen_feasibility" / "proof_obligations.csv"
STAGE173_PROOF = ROOT / "repro" / "stage173_structured_compact_phase_noise_toy" / "proof_status_update.csv"
MATTRGSW_C = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"
SAB_PVW_C = ROOT / "src" / "sab_pvw.c"
MOSFHET_H = ROOT / "src" / "mosfhet" / "include" / "mosfhet.h"

DECISION = "BLOCK_STAGE176_STRUCTURED_COMPACT_SECURITY_API_NOT_CLOSED_REDIRECT_FULL_MAT"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    normalized = [{field: row.get(field, "") for field in fields} for row in row_list]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


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


def append_once(path: Path, marker: str, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text_lf(path, current + text.lstrip("\n"))


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
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pattern_status(path: Path, pattern: str) -> str:
    return "PRESENT" if pattern in read_text(path) else "MISSING"


def build_evidence_rows() -> List[Dict[str, str]]:
    return [
        {
            "item": "dense_mat_keygen_all_rows_are_rlwe_samples",
            "source": rel(MATTRGSW_C),
            "status": pattern_status(MATTRGSW_C, "pvmtmlwe_sample(out->samples[i], NULL, key->trlwe_key);"),
            "evidence": "mat_trgsw_monomial_sample samples every row before adding diagonal gadget messages.",
            "implication": "Deleting body-cross rows changes the public bootstrapping-key distribution unless a reduction or new assumption is supplied.",
        },
        {
            "item": "dense_body_rows_contribute_masks",
            "source": rel(MATTRGSW_C),
            "status": pattern_status(MATTRGSW_C, "out->samples[(k + j) * l + i]->b[j]->coeffs[e] += m * h;"),
            "evidence": "Body rows carry the diagonal message in b[j] but still have sampled a/b components from PVW_TMLWE encryption.",
            "implication": "Keeping diagonal body rows without body-cross terms creates lane-local mask contributions unless the representation changes.",
        },
        {
            "item": "compact_output_has_per_lane_masks",
            "source": rel(MOSFHET_H),
            "status": pattern_status(MOSFHET_H, "typedef struct _MAT_TRGSW_COMPACT_OUTPUT_DFT"),
            "evidence": "MAT_TRGSW_COMPACT_OUTPUT_DFT stores DFT_Polynomial *a, *b with r outputs.",
            "implication": "The existing compact kernel output is not a PVW_TMLWE_DFT shared-mask state.",
        },
        {
            "item": "compact_kernel_returns_compact_output_not_pvw_state",
            "source": rel(MATTRGSW_C),
            "status": pattern_status(MATTRGSW_C, "void mat_trgsw_compact_mul_pvmtmlwe_DFT(MAT_TRGSW_COMPACT_OUTPUT_DFT out"),
            "evidence": "The production compact kernel writes MAT_TRGSW_COMPACT_OUTPUT_DFT, not PVW_TMLWE_DFT.",
            "implication": "Direct SAB CMUX integration would require a conversion boundary or a new closed accumulator type.",
        },
        {
            "item": "sab_pvw_cmux_consumes_closed_pvw_state",
            "source": rel(SAB_PVW_C),
            "status": pattern_status(SAB_PVW_C, "mat_trgsw_mul_pvmtmlwe_DFT(sab->tmp->tmlwe_dft, sub,"),
            "evidence": "sab_pvw_CMUX_from_sub_internal writes sab->tmp->tmlwe_dft and then materializes PVW_TMLWE.",
            "implication": "Current full SAB path requires one shared mask and r bodies after each CMUX/NCMUX.",
        },
        {
            "item": "stage139_nonclosure_input",
            "source": rel(STAGE139_SUMMARY),
            "status": "PRESENT" if STAGE139_SUMMARY.exists() else "MISSING",
            "evidence": "Stage139 found compact diagonal output has lane-specific masks and is not directly PVW_TMLWE closed.",
            "implication": "Stage176 cannot promote direct compact SAB integration without a new closure proof.",
        },
        {
            "item": "stage173_phase_noise_toy_input",
            "source": rel(STAGE173_PROOF),
            "status": "PRESENT" if STAGE173_PROOF.exists() else "MISSING",
            "evidence": "Stage173 finite phase/noise toy passes under zero body-cross constraints.",
            "implication": "This keeps the route theoretically interesting but does not close security or API.",
        },
    ]


def build_api_rows() -> List[Dict[str, str]]:
    return [
        {
            "option": "A_current_full_mat_pvw",
            "state": "PVW_TMLWE_DFT/PVW_TMLWE with one shared mask and r bodies",
            "security_status": "standard current distribution",
            "api_status": "closed and implemented",
            "implementation_permission": "YES_FOR_EXACT_FULL_MAT_ONLY",
            "risk": "performance bounded by dense MAT term count and from_DFT materialization",
        },
        {
            "option": "B_existing_compact_diagonal_output",
            "state": "MAT_TRGSW_COMPACT_OUTPUT_DFT with r lane-local masks",
            "security_status": "isolated kernel only",
            "api_status": "not closed for SAB PVW_TMLWE accumulator",
            "implementation_permission": "NO_DIRECT_SAB",
            "risk": "would need dense re-expansion or secret-dependent correction",
        },
        {
            "option": "C_omit_body_cross_zero_encryptions",
            "state": "attempt shared-output compact selector by deleting logical zero rows",
            "security_status": "no standard RLWE reduction recorded",
            "api_status": "phase toy passes, mask closure unresolved",
            "implementation_permission": "NO",
            "risk": "public BK distribution and output covariance change",
        },
        {
            "option": "D_new_structured_shared_mask_encryption",
            "state": "non-standard selector samples constrained to keep one shared mask",
            "security_status": "new assumption or proof required",
            "api_status": "not implemented",
            "implementation_permission": "NO",
            "risk": "may leak secret selector bits if masking is weakened",
        },
        {
            "option": "E_compact_then_dense_reexpand",
            "state": "compact internal product followed by dense PVW_TMLWE reconstruction",
            "security_status": "could be explored after proof",
            "api_status": "closed only after re-expansion",
            "implementation_permission": "NO_NOW",
            "risk": "likely cancels compact term-count benefit; must be microbench-gated",
        },
    ]


def build_summary_rows(evidence_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    required_present = all(row["status"] == "PRESENT" for row in evidence_rows)
    return [
        {
            "gate": "stage176_inputs",
            "status": "PASS" if required_present else "FAIL",
            "metric": "required_evidence_present",
            "value": "1" if required_present else "0",
            "evidence": rel(EVIDENCE_CSV),
            "detail": "Stage176 consumes Stage139 closure, Stage171 obligations, Stage173 toy proof status, and current code APIs.",
            "next_action": "Repair missing evidence before interpreting this gate.",
        },
        {
            "gate": "stage176_standard_security_distribution",
            "status": "BLOCKED_PROOF",
            "metric": "standard_rlwe_reduction_available",
            "value": "0",
            "evidence": f"{rel(MATTRGSW_C)}; {rel(STAGE171_PROOF)}",
            "detail": "Dense MAT keygen samples all rows as PVW_TMLWE encryptions. Omitting body-cross zero rows or forcing public/no-mask rows changes the public key distribution.",
            "next_action": "No compact SAB implementation until a reduction, simulation argument, or explicit new assumption is written and reviewed.",
        },
        {
            "gate": "stage176_shared_mask_closure",
            "status": "BLOCKED_API",
            "metric": "direct_compact_output_is_pvw_tmlwe",
            "value": "0",
            "evidence": f"{rel(STAGE139_SUMMARY)}; {rel(MOSFHET_H)}; {rel(SAB_PVW_C)}",
            "detail": "Existing compact output has lane-local masks, while SAB CMUX requires a closed PVW_TMLWE/PVW_TMLWE_DFT shared-mask state.",
            "next_action": "Do not wire MAT_TRGSW_COMPACT_OUTPUT_DFT into sab_pvw_CMUX without a new closed state or proven conversion.",
        },
        {
            "gate": "stage176_phase_noise_context",
            "status": "PARTIAL_PASS",
            "metric": "stage173_toy_passes",
            "value": "1",
            "evidence": rel(STAGE173_PROOF),
            "detail": "Finite phase and toy variance support the algebraic direction only; they do not cover mask distribution, security, or full RLWE noise.",
            "next_action": "Use as background evidence, not implementation permission.",
        },
        {
            "gate": "stage176_implementation_permission",
            "status": "DENY_COMPACT_SAB",
            "metric": "permission_yes",
            "value": "0",
            "evidence": f"{rel(API_CSV)}; {rel(DECISION_CSV)}",
            "detail": "Security and closed-state API are not both satisfied.",
            "next_action": "Redirect executable optimization to the exact full-MAT PVW path.",
        },
        {
            "gate": "stage176_decision",
            "status": DECISION,
            "metric": "route",
            "value": "full_mat_exact_path",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Structured compact remains a theory/literature branch; the engineering branch continues on current closed full-MAT SAB.",
            "next_action": "Run literature verification before novelty claims and use full-MAT complete-SAB gates for implementation work.",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "177",
            "name": "verified literature and novelty boundary",
            "entry_condition": "Stage176 denies compact implementation but structured compact remains theoretically interesting.",
            "gate": "Cite real SAB/PVW/MAT/multi-output/FHE-kernel papers; no novelty claim without verified source support.",
            "failure_rule": "If sources do not support novelty, label compact route as internal theoretical exploration only.",
        },
        {
            "priority": "P1",
            "stage": "178",
            "name": "full-MAT exact path per-bit throughput frontier",
            "entry_condition": "Compact SAB implementation permission denied.",
            "gate": "Re-normalize all current complete-SAB evidence as T_bootstrap/r and select the next exact-path implementation candidate from measured component shares.",
            "failure_rule": "If no component has a plausible complete-SAB gain path, stop engineering churn and write the negative frontier.",
        },
        {
            "priority": "P2",
            "stage": "179",
            "name": "optional compact proof attempt",
            "entry_condition": "Stage177 finds a real proof technique or related assumption worth adapting.",
            "gate": "Close keygen distribution, security, noise, and shared-mask API on paper before code.",
            "failure_rule": "If any item remains open, compact remains non-implementation.",
        },
    ]


def build_decision_rows() -> List[Dict[str, str]]:
    return [
        {
            "claim": "complete_sab_speedup_claim",
            "stage176_position": "unchanged_from_stage172_173",
            "allowed_wording": "Current exact PVW/MAT-SAB has measured complete-SAB T_bootstrap/r throughput evidence; Stage176 adds no new speedup.",
            "forbidden_wording": "Structured compact SAB is implemented or accelerates complete SAB.",
        },
        {
            "claim": "compact_algorithm_claim",
            "stage176_position": "blocked",
            "allowed_wording": "Structured compact has finite/toy support but is blocked by security/API closure.",
            "forbidden_wording": "Omitting encrypted zero rows is free under standard RLWE.",
        },
        {
            "claim": "implementation_route",
            "stage176_position": "redirect_full_mat",
            "allowed_wording": "Proceed with exact full-MAT sab_pvw_* optimizations behind flags.",
            "forbidden_wording": "Modify sab_pvw_* to consume compact output directly.",
        },
    ]


def write_docs(summary_rows: List[Dict[str, str]], evidence_rows: List[Dict[str, str]],
               api_rows: List[Dict[str, str]], decision_rows: List[Dict[str, str]],
               next_rows: List[Dict[str, str]]) -> None:
    write_text_lf(OUT_MD, f"""# Stage176 Structured Compact Security/API Gate

Decision: `{DECISION}`.

Stage176 is a bounded go/no-go gate. It asks whether the structured compact
MAT-SAB route can be implemented now under the current scalar/PVW SAB API and
standard security expectations.

The answer is no. Stage173 supports finite-field phase and toy variance, but
the compact route still fails two implementation requirements:

- a standard public bootstrapping-key distribution after deleting or replacing
  encrypted body-cross zero rows;
- a closed SAB accumulator API with one shared mask and r body lanes.

The executable branch therefore returns to exact full-MAT `sab_pvw_*`
optimization. The compact branch is retained only as a proof/literature branch.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Evidence Matrix

{table(evidence_rows, ["item", "source", "status", "evidence", "implication"])}
## API Options

{table(api_rows, ["option", "state", "security_status", "api_status", "implementation_permission", "risk"])}
## Claim Boundary

{table(decision_rows, ["claim", "stage176_position", "allowed_wording", "forbidden_wording"])}
## Next Queue

{table(next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])}
""")

    write_text_lf(PLAN_MD, f"""# Stage176 Plan

Goal: decide whether structured compact MAT-SAB may enter implementation.

Inputs:

- `{rel(STAGE139_SUMMARY)}` for compact-output non-closure.
- `{rel(STAGE171_PROOF)}` for open proof obligations.
- `{rel(STAGE173_PROOF)}` for finite phase/noise toy status.
- `{rel(MATTRGSW_C)}`, `{rel(MOSFHET_H)}`, and `{rel(SAB_PVW_C)}` for current code API facts.

Correctness gate:

- Stage173 toy evidence may count only as partial algebraic evidence.
- API closure requires direct production of `PVW_TMLWE_DFT` or a proven closed
  replacement state.

Security gate:

- The dense row distribution in `mat_trgsw_monomial_sample` may not be replaced
  by omission/public zeros without a written reduction, simulation argument, or
  explicitly stated new assumption.

Failure handling:

- If either security or API closure is not proven, deny compact SAB
  implementation and redirect executable work to exact full-MAT SAB.

Decision: `{DECISION}`.
""")

    write_text_lf(THEORY_MD, """# Stage176 Security/API Model

Let a PVW/MAT-RLWE ciphertext be `(a, b_1, ..., b_r)`, where the mask `a` is
shared across all body lanes. The current dense MAT external product consumes
the decomposition of all `1+r` components and adds encrypted selector rows.

For a body diagonal row, dense keygen still samples a full PVW_TMLWE encryption
before adding the diagonal body message. The row contributes both a mask term
and body terms to the output. If only the target body's term is retained, the
resulting output has a lane-specific mask contribution. This is the Stage139
non-closure problem.

If the body-row mask contribution is deleted to force one shared mask, the
selector sample is no longer the current standard PVW_TMLWE encryption row. For
secret-dependent selector messages, replacing that row with a public/no-mask
object needs a security proof or a new assumption. Stage173's finite-field
phase toy does not address that distributional question.

Therefore the current implementation-permission rule is:

```text
compact SAB implementation allowed
iff standard/security assumption is written
and closed shared-mask accumulator API is specified
and full-SAB correctness/noise gate is planned.
```

Stage176 does not satisfy the first two conditions.
""")

    write_text_lf(VARIANT_MD, """# Structured Compact MAT-SAB Security/API Variant

Status: blocked for implementation.

The variant would replace the dense MAT selector with a compact structured
selector that omits body-to-body cross terms. Stage173 shows this is algebraic
phase-compatible in a finite toy model under zero-cross constraints.

The variant is not currently an executable SAB algorithm because:

- current dense MAT keygen encrypts all rows;
- deleting zero rows lacks a standard security reduction;
- existing compact output has lane-local masks;
- `sab_pvw_*` requires a closed PVW_TMLWE accumulator with one shared mask.

Executable work should continue on exact full-MAT `sab_pvw_*` until these
conditions are closed by a proof and API design.
""")


def write_global_updates() -> None:
    append_once(ROADMAP_MD, "## Stage 176: Structured Compact Security/API Gate", f"""
## Stage 176: Structured Compact Security/API Gate

Goal:

```text
Decide whether the structured compact route has enough security/API closure to
enter SAB implementation.
```

Status:

```text
Completed. Stage176 records {DECISION}. Compact SAB implementation permission
is denied because standard key-distribution proof and shared-mask accumulator
closure are not both satisfied. Executable optimization returns to the exact
full-MAT PVW/MAT-SAB path.
```
""")
    append_once(GOAL_MD, "Stage176 denies compact SAB implementation", f"""
Stage176 denies compact SAB implementation permission. Decision:
`{DECISION}`. Structured compact remains a proof/literature branch; complete
SAB acceleration work continues on the closed exact full-MAT `sab_pvw_*` path.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage176 as the compact security/API boundary", f"""
80. Treat Stage176 as the compact security/API boundary:
    `{DECISION}`. Stage173 phase/noise toy evidence does not overcome missing
    standard security distribution and shared-mask API closure. Do not implement
    compact SAB directly; continue exact full-MAT `T_bootstrap/r` work.
""")
    append_once(HYPOTHESIS_YAML, "H100_structured_compact_security_api", f"""
  - id: H100_structured_compact_security_api
    statement: >
      Structured compact MAT-SAB cannot enter implementation unless deleting or
      replacing body-cross zero encryptions preserves a defensible public
      key distribution and the compact external product returns a closed
      shared-mask PVW_TMLWE state.
    mechanism: >
      Dense MAT keygen samples every selector row as a PVW_TMLWE encryption.
      Existing compact output stores lane-local masks, while SAB CMUX/NCMUX
      requires one shared mask and r bodies after each step.
    status: stage176_structured_compact_security_api_gate
    evidence: docs/stage176_structured_compact_security_api_gate.md; experiments/stage176_structured_compact_security_api_gate_plan.md; theory_checks/stage176_structured_compact_security_api_model.md; repro/stage176_structured_compact_security_api_gate/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - compact output is wired into SAB without a closed shared-mask state
      - omitted encrypted zero rows are assumed secure without reduction or
        explicit assumption
      - Stage173 toy evidence is reported as implemented compact SAB speedup
""")
    append_once(RUN_LOG, "stage176-structured-compact-security-api-gate-001", f"""
stage176-structured-compact-security-api-gate-001,2026-07-04,{git_head()},Stage 176,analysis,python scripts/build_stage176_structured_compact_security_api_gate.py,Stage139/171/173/code API evidence,none,{DECISION},Structured compact security/API implementation-permission gate.,repro/stage176_structured_compact_security_api_gate
""")
    append_once(MANIFEST, "stage176_structured_compact_security_api_gate", f"""
- stage176_structured_compact_security_api_gate: `{DECISION}`
  - `docs/stage176_structured_compact_security_api_gate.md`
  - `experiments/stage176_structured_compact_security_api_gate_plan.md`
  - `theory_checks/stage176_structured_compact_security_api_model.md`
  - `algorithm_variants/mat_rlwe_sab_structured_compact_security_api.md`
  - `repro/stage176_structured_compact_security_api_gate/`
""")
    append_once(CHECKLIST, "Stage176 structured compact security/API gate pack recorded", """
- [x] Stage176 structured compact security/API gate pack recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path),
            "bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    evidence_rows = build_evidence_rows()
    api_rows = build_api_rows()
    summary_rows = build_summary_rows(evidence_rows)
    decision_rows = build_decision_rows()
    next_rows = build_next_rows()

    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_csv(EVIDENCE_CSV, evidence_rows, ["item", "source", "status", "evidence", "implication"])
    write_csv(API_CSV, api_rows, ["option", "state", "security_status", "api_status", "implementation_permission", "risk"])
    write_csv(DECISION_CSV, decision_rows, ["claim", "stage176_position", "allowed_wording", "forbidden_wording"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_docs(summary_rows, evidence_rows, api_rows, decision_rows, next_rows)
    write_global_updates()
    write_artifacts([
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        EVIDENCE_CSV,
        API_CSV,
        DECISION_CSV,
        NEXT_CSV,
        Path(__file__),
    ])
    print(DECISION)


if __name__ == "__main__":
    main()
