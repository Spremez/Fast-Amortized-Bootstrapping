#!/usr/bin/env python3
"""Stage187: compact/shared-output MAT-SAB proof obligation draft."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage187_compact_proof_obligation_draft"

SUMMARY_CSV = OUT_DIR / "summary.csv"
THEOREM_CSV = OUT_DIR / "theorem_matrix.csv"
ASSUMPTION_CSV = OUT_DIR / "assumption_ledger.csv"
DEPENDENCY_CSV = OUT_DIR / "proof_dependency_graph.csv"
GATE_CSV = OUT_DIR / "falsification_gates.csv"
ENTRY_CSV = OUT_DIR / "implementation_entry_rule.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage187_compact_proof_obligation_draft.md"
PLAN_MD = ROOT / "experiments" / "stage187_compact_proof_obligation_draft_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage187_compact_proof_obligations.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_compact_proof_obligation_draft.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE186_SUMMARY = ROOT / "repro" / "stage186_compact_proof_unlock_audit" / "summary.csv"
STAGE186_OBLIGATIONS = ROOT / "repro" / "stage186_compact_proof_unlock_audit" / "proof_obligation_matrix.csv"
STAGE186_PERMISSION = ROOT / "repro" / "stage186_compact_proof_unlock_audit" / "implementation_permission.csv"
STAGE138_RATIOS = ROOT / "repro" / "stage138_shared_mask_compact_gate" / "ratio_summary.csv"
STAGE139_SUMMARY = ROOT / "repro" / "stage139_compact_closure_audit" / "summary.csv"
STAGE173_PROOF = ROOT / "repro" / "stage173_structured_compact_phase_noise_toy" / "proof_status_update.csv"
STAGE176_EVIDENCE = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "evidence_matrix.csv"
STAGE177_CLAIM = ROOT / "repro" / "stage177_verified_literature_novelty_gate" / "claim_policy.csv"

DECISION = "PASS_STAGE187_COMPACT_PROOF_DRAFT_IMPLEMENTATION_STILL_DENIED"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{name: row.get(name, "") for name in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv_dicts(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def build_theorem_rows() -> List[Dict[str, str]]:
    return [
        {
            "id": "T1_key_distribution",
            "statement": "Structured compact selector public key is computationally indistinguishable from a permitted public key distribution.",
            "inputs": "Dense MAT_TRGSW keygen, omitted body-cross zero rows, PVW/MAT secret distribution.",
            "current_status": "OPEN",
            "needed_proof": "Hybrid/simulation proof or explicit new structured-key assumption with leakage analysis.",
            "falsifier": "Any distinguisher using missing or deterministic body-cross rows, or any proof that simulator needs secret selector data.",
            "code_permission_if_unproven": "DENY",
        },
        {
            "id": "T2_closed_state",
            "statement": "Every compact CMUX/NCMUX/RGSW update returns a closed one-mask/r-body PVW_TMLWE state.",
            "inputs": "MAT_TRGSW_COMPACT_OUTPUT_DFT, sab_pvw accumulator invariant, Stage139 nonclosure rows.",
            "current_status": "OPEN_BLOCKED_BY_STAGE139",
            "needed_proof": "New accumulator API or conversion that removes lane-local masks without dense re-expansion.",
            "falsifier": "Any lane-specific output mask after one CMUX step, or conversion cost that reintroduces dense full-MAT work.",
            "code_permission_if_unproven": "DENY",
        },
        {
            "id": "T3_phase_equivalence",
            "statement": "Compact production polynomial/RLWE CMUX schedule has the same phase as dense structured MAT-SAB.",
            "inputs": "Stage173 finite toy, production polynomial rotations, gadget decomposition, DFT conversions.",
            "current_status": "TOY_ONLY",
            "needed_proof": "Coefficient-domain theorem plus deterministic MOSFHET DFT equivalence tests over r=2/4/6 and target N.",
            "falsifier": "Any coefficient/phase mismatch versus dense structured reference at a CMUX, RGSW, sparse_mul, or extract boundary.",
            "code_permission_if_unproven": "DENY",
        },
        {
            "id": "T4_noise_bound",
            "statement": "Compact route has noise no worse than accepted parameters or admits a valid parameter adjustment.",
            "inputs": "Structured selector noise, omitted zero rows, repeated SAB schedule, extraction/key switching.",
            "current_status": "TOY_ONLY",
            "needed_proof": "RLWE noise recurrence with correlations and modulus effects, followed by multi-seed final/stage noise gates.",
            "falsifier": "Failure rate or noise sigma gap exceeding scalar/exact PVW baseline under target parameters.",
            "code_permission_if_unproven": "DENY",
        },
        {
            "id": "T5_performance_survival",
            "statement": "Compact proof route survives complete SAB T_bootstrap/r after all required conversions and keygen changes.",
            "inputs": "Stage138 kernel signal, closed-state API, full SAB integration, key size/resource overhead.",
            "current_status": "KERNEL_ONLY",
            "needed_proof": "Full-SAB A/B benchmark plus resource/noise gates; kernel-only speedup is insufficient.",
            "falsifier": "Complete-SAB mean speedup not positive after repeated runs, or unacceptable memory/keygen/key-size growth.",
            "code_permission_if_unproven": "DENY_FINAL_CLAIM",
        },
        {
            "id": "T6_novelty_scope",
            "statement": "Any compact/shared-output claim is distinct from verified adjacent amortized/PVW/MAT/TFHE prior work.",
            "inputs": "Stage177 related-work matrix, future citation-level review, complete compact implementation.",
            "current_status": "STRONG_CLAIM_DENIED",
            "needed_proof": "Citation-supported comparison after proof and implementation gates pass.",
            "falsifier": "Direct prior art or unsupported novelty wording.",
            "code_permission_if_unproven": "DENY_PAPER_NOVELTY",
        },
    ]


def build_assumption_rows() -> List[Dict[str, str]]:
    return [
        {
            "id": "A0_current_exact_full_mat",
            "type": "implemented_baseline",
            "description": "Current exact full-MAT PVW/MAT-SAB uses dense encrypted selector rows and closed PVW_TMLWE state.",
            "status": "AVAILABLE",
            "risk": "Dense cost limits speedup but security/API are current baseline.",
        },
        {
            "id": "A1_zero_cross_logical_structure",
            "type": "algorithmic_structure",
            "description": "Structured compact assumes body-cross terms are logical zeros in the intended selector map.",
            "status": "TOY_SUPPORTED",
            "risk": "Logical zeros are not free encrypted rows under public-key distribution.",
        },
        {
            "id": "A2_delete_or_constrain_zero_rows",
            "type": "security_assumption",
            "description": "Omitting/constraining body-cross zero encryptions does not leak or distinguish keys.",
            "status": "UNPROVEN",
            "risk": "Main blocker for implementation and novelty.",
        },
        {
            "id": "A3_closed_compact_accumulator",
            "type": "api_invariant",
            "description": "Compact output can be represented as one shared mask plus r bodies after every SAB update.",
            "status": "CONTRADICTED_BY_CURRENT_OUTPUT",
            "risk": "Stage139 shows current compact diagonal output has lane-local masks.",
        },
        {
            "id": "A4_kernel_gain_survives_full_sab",
            "type": "performance_assumption",
            "description": "Stage138 kernel speedup survives CMUX/RGSW/sparse schedule and resource overhead.",
            "status": "UNTESTED",
            "risk": "No complete-SAB compact path exists.",
        },
    ]


def build_dependency_rows() -> List[Dict[str, str]]:
    return [
        {"from": "A1_zero_cross_logical_structure", "to": "T3_phase_equivalence", "relation": "required_for_formula"},
        {"from": "A2_delete_or_constrain_zero_rows", "to": "T1_key_distribution", "relation": "main_security_claim"},
        {"from": "A3_closed_compact_accumulator", "to": "T2_closed_state", "relation": "main_api_claim"},
        {"from": "T1_key_distribution", "to": "implementation_entry", "relation": "must_pass"},
        {"from": "T2_closed_state", "to": "implementation_entry", "relation": "must_pass"},
        {"from": "T3_phase_equivalence", "to": "implementation_entry", "relation": "must_pass"},
        {"from": "T4_noise_bound", "to": "implementation_entry", "relation": "must_pass"},
        {"from": "implementation_entry", "to": "T5_performance_survival", "relation": "precondition_for_full_sab_bench"},
        {"from": "T5_performance_survival", "to": "T6_novelty_scope", "relation": "precondition_for_algorithmic_claim"},
    ]


def build_gate_rows() -> List[Dict[str, str]]:
    return [
        {
            "gate": "G1_distribution_hybrid",
            "target": "T1_key_distribution",
            "method": "written proof plus finite simulator showing public rows do not encode secret-dependent omissions",
            "pass_condition": "reviewed proof or explicit assumption recorded; no hidden secret-dependent public metadata",
            "fail_action": "compact implementation remains denied",
        },
        {
            "gate": "G2_closed_state_api",
            "target": "T2_closed_state",
            "method": "define compact accumulator type and one-step CMUX/NCMUX reference checker",
            "pass_condition": "all output masks are one shared mask or proven convertible without dense re-expansion",
            "fail_action": "do not wire compact output into sab_pvw_*",
        },
        {
            "gate": "G3_phase_equivalence",
            "target": "T3_phase_equivalence",
            "method": "coefficient and DFT equivalence against dense structured reference for r=2/4/6 and target N",
            "pass_condition": "zero mismatches at CMUX, RGSW monomial, sparse_mul, and extract boundaries",
            "fail_action": "repair equations before performance work",
        },
        {
            "gate": "G4_noise_bound",
            "target": "T4_noise_bound",
            "method": "symbolic recurrence plus multi-seed stage/final-output noise campaign",
            "pass_condition": "failure/noise not worse than baseline or parameter change justified",
            "fail_action": "no final SAB claim",
        },
        {
            "gate": "G5_complete_sab_performance",
            "target": "T5_performance_survival",
            "method": "same-backend repeated complete-SAB A/B using T_bootstrap/r",
            "pass_condition": "stable positive throughput after key/memory/keygen/resource reporting",
            "fail_action": "record compact as negative/neutral",
        },
        {
            "gate": "G6_citation_novelty",
            "target": "T6_novelty_scope",
            "method": "citation-level related-work verification against 2025/686, 2025/696, amortized/batch, PVW, TFHE/FHEW",
            "pass_condition": "claim is source-supported and narrowly distinguished",
            "fail_action": "downgrade to engineering/future-work wording",
        },
    ]


def build_entry_rows() -> List[Dict[str, str]]:
    return [
        {
            "entry": "production_sab_code",
            "permission": "DENY",
            "required_before_allow": "G1,G2,G3,G4 pass",
            "current_reason": "Stage186 shows key distribution and closed shared-mask state are blocked.",
        },
        {
            "entry": "isolated_proof_probe",
            "permission": "ALLOW",
            "required_before_allow": "No sab_pvw_* hot-path changes; must target one theorem gate.",
            "current_reason": "Finite/proof probes can reduce proof uncertainty without claiming implementation.",
        },
        {
            "entry": "complete_sab_benchmark",
            "permission": "DENY_UNTIL_IMPLEMENTED",
            "required_before_allow": "Production implementation after G1-G4 pass.",
            "current_reason": "No compact complete-SAB path exists.",
        },
        {
            "entry": "paper_novelty_claim",
            "permission": "DENY",
            "required_before_allow": "G1-G6 pass and citation-level support.",
            "current_reason": "Stage177 denies strong novelty and Stage186 denies implementation.",
        },
    ]


def build_summary_rows() -> List[Dict[str, str]]:
    inputs = [STAGE186_SUMMARY, STAGE186_OBLIGATIONS, STAGE186_PERMISSION]
    ok = all(path.exists() for path in inputs)
    return [
        {
            "gate": "stage187_inputs",
            "status": "PASS" if ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if ok else "0",
            "evidence": f"{rel(STAGE186_SUMMARY)}; {rel(STAGE186_OBLIGATIONS)}",
            "detail": "Stage187 consumes the Stage186 compact unlock audit and current source/API facts.",
            "next_action": "Repair Stage186 if missing.",
        },
        {
            "gate": "stage187_proof_draft",
            "status": "PASS_DRAFTED",
            "metric": "theorems;assumptions;falsification_gates",
            "value": "6;5;6",
            "evidence": f"{rel(THEOREM_CSV)}; {rel(ASSUMPTION_CSV)}; {rel(GATE_CSV)}",
            "detail": "Proof obligations are written as falsifiable gates with implementation entry rules.",
            "next_action": "Only isolated proof probes are allowed.",
        },
        {
            "gate": "stage187_implementation_permission",
            "status": "DENY_PRODUCTION_CODE",
            "metric": "production_sab_code_permission",
            "value": "0",
            "evidence": rel(ENTRY_CSV),
            "detail": "No compact sab_pvw_* implementation is permitted from this draft alone.",
            "next_action": "Run a targeted proof probe or draft scoped manuscript.",
        },
        {
            "gate": "stage187_decision",
            "status": DECISION,
            "metric": "route",
            "value": "proof_probe_or_scoped_paper",
            "evidence": rel(SUMMARY_CSV),
            "detail": "The theory route is bounded by explicit gates, avoiding an open-ended theory loop.",
            "next_action": "Proceed to Stage188 manuscript skeleton or a single theorem-targeted proof probe.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    theorem_rows: List[Dict[str, str]],
    assumption_rows: List[Dict[str, str]],
    dependency_rows: List[Dict[str, str]],
    gate_rows: List[Dict[str, str]],
    entry_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage187 Compact Proof Obligation Draft

Decision: `{DECISION}`.

Stage187 translates the compact/shared-output MAT-SAB blockers into a bounded
proof program. It does not unlock implementation. Its purpose is to make the
next proof or experiment falsifiable:

- six theorem obligations;
- five assumption/representation risks;
- six concrete falsification gates;
- explicit implementation entry rules.

Production `sab_pvw_*` code remains denied until key distribution, closed-state
API, phase, and noise obligations pass.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Theorem Matrix

{table(theorem_rows, ["id", "statement", "inputs", "current_status", "needed_proof", "falsifier", "code_permission_if_unproven"])}
## Assumption Ledger

{table(assumption_rows, ["id", "type", "description", "status", "risk"])}
## Dependency Graph

{table(dependency_rows, ["from", "to", "relation"])}
## Falsification Gates

{table(gate_rows, ["gate", "target", "method", "pass_condition", "fail_action"])}
## Implementation Entry Rule

{table(entry_rows, ["entry", "permission", "required_before_allow", "current_reason"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage187 Plan

Goal: convert compact/shared-output MAT-SAB proof blockers into a concrete,
falsifiable proof program.

Rules:

- no production SAB code;
- each theorem must have a falsifier and implementation consequence;
- proof probes are allowed only when they target one listed gate;
- kernel-only timing remains motivation, not complete-SAB evidence.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage187 Compact Proof Obligations

The compact route can become an implementation candidate only if four
mathematical obligations pass before code:

1. Key distribution: public compact key material must be simulatable or stated
   under an explicit reviewed assumption.
2. Closed state: every update must return one shared mask plus r bodies.
3. Phase equivalence: production polynomial/RLWE operations must match the
   dense structured reference.
4. Noise bound: the repeated SAB schedule must remain within accepted
   parameters.

Only after those pass can complete-SAB `T_bootstrap/r` benchmarking and novelty
review upgrade the route.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Compact Proof Obligation Variant

This variant is not an implementation. It is a proof-gated candidate card.

Current status:

- Stage138 kernel signal: useful motivation.
- Stage139 closure: current compact output is not PVW_TMLWE closed.
- Stage176 security/API: implementation denied.
- Stage177 novelty: strong novelty denied.

Allowed next work: isolated proof probes targeting T1-T4.
Denied next work: production compact SAB code.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 187: Compact Proof Obligation Draft",
        f"""
## Stage 187: Compact Proof Obligation Draft

Goal:

```text
Convert compact/shared-output MAT-SAB blockers into theorem obligations,
falsification gates, and implementation entry rules.
```

Status:

```text
Completed. Stage187 records {DECISION}. It allows isolated proof probes but
keeps production compact SAB code denied until key distribution, closed-state,
phase, and noise obligations pass.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage187 records the compact proof obligation draft",
        f"""
Stage187 records the compact proof obligation draft. Decision: `{DECISION}`.
It turns the compact/shared-output route into a bounded theorem/gate program
and keeps implementation denied.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage187 as the compact proof obligation draft",
        f"""
91. Treat Stage187 as the compact proof obligation draft:
    `{DECISION}`. Compact/shared-output MAT-SAB now has explicit theorem
    obligations and falsification gates. Only isolated proof probes are allowed;
    production SAB code remains denied.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H111_compact_proof_obligation_draft",
        f"""
  - id: H111_compact_proof_obligation_draft
    statement: >
      Compact/shared-output MAT-SAB can only proceed through explicit theorem
      obligations and falsification gates; proof-draft evidence alone must not
      authorize production SAB code.
    mechanism: >
      Stage187 converts Stage186 blockers into theorem, assumption, dependency,
      and implementation-entry matrices.
    status: stage187_compact_proof_obligation_draft
    evidence: docs/stage187_compact_proof_obligation_draft.md; experiments/stage187_compact_proof_obligation_draft_plan.md; theory_checks/stage187_compact_proof_obligations.md; repro/stage187_compact_proof_obligation_draft/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - production compact SAB code is written before T1-T4 pass
      - kernel-only compact timing is reported as complete-SAB speedup
      - novelty is claimed before T1-T6 and citation-level review pass
""",
    )

    append_once(
        RUN_LOG,
        "stage187-compact-proof-obligation-draft-001",
        f"""
stage187-compact-proof-obligation-draft-001,2026-07-04,{git_head()},Stage 187,analysis,python scripts/build_stage187_compact_proof_obligation_draft.py,Stage186 compact blockers,none,{DECISION},Compact/shared-output proof obligation draft.,repro/stage187_compact_proof_obligation_draft
""",
    )

    append_once(
        MANIFEST,
        "stage187_compact_proof_obligation_draft",
        f"""
- stage187_compact_proof_obligation_draft: `{DECISION}`
  - `docs/stage187_compact_proof_obligation_draft.md`
  - `experiments/stage187_compact_proof_obligation_draft_plan.md`
  - `theory_checks/stage187_compact_proof_obligations.md`
  - `algorithm_variants/mat_rlwe_sab_compact_proof_obligation_draft.md`
  - `repro/stage187_compact_proof_obligation_draft/`
""",
    )

    append_once(CHECKLIST, "Stage187 compact proof obligation draft recorded", """
- [x] Stage187 compact proof obligation draft recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path),
                "bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    theorem_rows = build_theorem_rows()
    assumption_rows = build_assumption_rows()
    dependency_rows = build_dependency_rows()
    gate_rows = build_gate_rows()
    entry_rows = build_entry_rows()
    summary_rows = build_summary_rows()

    write_csv(THEOREM_CSV, theorem_rows, ["id", "statement", "inputs", "current_status", "needed_proof", "falsifier", "code_permission_if_unproven"])
    write_csv(ASSUMPTION_CSV, assumption_rows, ["id", "type", "description", "status", "risk"])
    write_csv(DEPENDENCY_CSV, dependency_rows, ["from", "to", "relation"])
    write_csv(GATE_CSV, gate_rows, ["gate", "target", "method", "pass_condition", "fail_action"])
    write_csv(ENTRY_CSV, entry_rows, ["entry", "permission", "required_before_allow", "current_reason"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, theorem_rows, assumption_rows, dependency_rows, gate_rows, entry_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            SUMMARY_CSV,
            THEOREM_CSV,
            ASSUMPTION_CSV,
            DEPENDENCY_CSV,
            GATE_CSV,
            ENTRY_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
