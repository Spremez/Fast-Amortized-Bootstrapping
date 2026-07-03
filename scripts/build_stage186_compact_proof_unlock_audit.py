#!/usr/bin/env python3
"""Stage186: compact/shared-output MAT-SAB proof unlock audit."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage186_compact_proof_unlock_audit"

SUMMARY_CSV = OUT_DIR / "summary.csv"
OBLIGATION_CSV = OUT_DIR / "proof_obligation_matrix.csv"
EVIDENCE_CSV = OUT_DIR / "compact_evidence_index.csv"
IMPLEMENTATION_CSV = OUT_DIR / "implementation_permission.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage186_compact_proof_unlock_audit.md"
PLAN_MD = ROOT / "experiments" / "stage186_compact_proof_unlock_audit_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage186_compact_proof_unlock_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_compact_unlock_audit.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE138_SUMMARY = ROOT / "repro" / "stage138_shared_mask_compact_gate" / "summary.csv"
STAGE138_RATIOS = ROOT / "repro" / "stage138_shared_mask_compact_gate" / "ratio_summary.csv"
STAGE139_SUMMARY = ROOT / "repro" / "stage139_compact_closure_audit" / "summary.csv"
STAGE139_CLOSURE = ROOT / "repro" / "stage139_compact_closure_audit" / "closure_rows.csv"
STAGE173_SUMMARY = ROOT / "repro" / "stage173_structured_compact_phase_noise_toy" / "summary.csv"
STAGE173_PROOF = ROOT / "repro" / "stage173_structured_compact_phase_noise_toy" / "proof_status_update.csv"
STAGE176_SUMMARY = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "summary.csv"
STAGE176_API = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "api_options.csv"
STAGE176_EVIDENCE = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "evidence_matrix.csv"
STAGE177_SUMMARY = ROOT / "repro" / "stage177_verified_literature_novelty_gate" / "summary.csv"
STAGE177_CLAIM = ROOT / "repro" / "stage177_verified_literature_novelty_gate" / "claim_policy.csv"
STAGE185_REQ = ROOT / "repro" / "stage185_research_repro_package_refresh" / "requirement_matrix.csv"

DECISION = "BLOCK_STAGE186_COMPACT_PROOF_UNLOCK_NOT_READY"


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


def stage138_r4_speedup() -> str:
    vals = []
    for row in read_csv_dicts(STAGE138_RATIOS):
        if row.get("r") == "4":
            vals.append(row.get("per_bit_speedup", ""))
    vals = [v for v in vals if v]
    if not vals:
        return ""
    floats = [float(v) for v in vals]
    return f"{min(floats):.6f};{max(floats):.6f}"


def build_obligation_rows() -> List[Dict[str, str]]:
    return [
        {
            "obligation": "keygen_distribution",
            "status": "BLOCKED",
            "current_evidence": f"{rel(STAGE176_EVIDENCE)}; {rel(STAGE173_PROOF)}",
            "what_passes": "Toy equations identify omitted zero-cross terms.",
            "what_fails_or_missing": "No standard RLWE/PVW distribution reduction for deleting or constraining body-cross encrypted zero rows.",
            "unlock_condition": "Formal hybrid/simulation proof or explicit reviewed structured-key assumption.",
            "implementation_permission": "NO",
        },
        {
            "obligation": "closed_shared_mask_state",
            "status": "BLOCKED",
            "current_evidence": f"{rel(STAGE139_SUMMARY)}; {rel(STAGE176_API)}",
            "what_passes": "Shared-mask compact independent-lane kernel has positive per-bit kernel evidence.",
            "what_fails_or_missing": "Stage139 records lane-local masks; existing compact output is not a closed PVW_TMLWE/PVW_TMLWE_DFT SAB accumulator.",
            "unlock_condition": "New closed accumulator API or proven conversion without dense re-expansion.",
            "implementation_permission": "NO",
        },
        {
            "obligation": "phase_invariant",
            "status": "PARTIAL_TOY_PASS",
            "current_evidence": rel(STAGE173_SUMMARY),
            "what_passes": "Finite-field SAB-like CMUX/NCMUX phase toy has zero structured mismatches.",
            "what_fails_or_missing": "No formal polynomial/RLWE phase proof for production SAB schedule and parameters.",
            "unlock_condition": "Production-level phase theorem plus deterministic coefficient/DFT equivalence gate.",
            "implementation_permission": "NO",
        },
        {
            "obligation": "noise_accounting",
            "status": "PARTIAL_TOY_PASS",
            "current_evidence": rel(STAGE173_PROOF),
            "what_passes": "Toy variance does not exceed dense zero-padded variance.",
            "what_fails_or_missing": "No full RLWE noise proof with correlations, modulus effects, key distribution, and SAB repetition.",
            "unlock_condition": "Noise theorem plus multi-seed stage/final-output validation after implementation.",
            "implementation_permission": "NO",
        },
        {
            "obligation": "performance_path",
            "status": "KERNEL_ONLY",
            "current_evidence": f"{rel(STAGE138_RATIOS)}; {rel(STAGE185_REQ)}",
            "what_passes": f"Stage138 r=4 per-bit compact kernel speedup range {stage138_r4_speedup()}x.",
            "what_fails_or_missing": "No complete-SAB compact path or T_bootstrap/r benchmark exists.",
            "unlock_condition": "Only after security/API proof: isolated CMUX, RGSW/sparse, full-SAB A/B, noise/resource.",
            "implementation_permission": "NO",
        },
        {
            "obligation": "literature_novelty",
            "status": "BLOCKED_STRONG_CLAIM",
            "current_evidence": f"{rel(STAGE177_SUMMARY)}; {rel(STAGE177_CLAIM)}",
            "what_passes": "Bounded related-work matrix exists and permits cautious engineering wording.",
            "what_fails_or_missing": "Strong novelty is denied; 2025/696 and amortized/batch prior art create high novelty risk.",
            "unlock_condition": "Citation-level review plus comparison after a complete-SAB compact implementation exists.",
            "implementation_permission": "NO_FOR_PAPER_CLAIM",
        },
    ]


def build_evidence_rows() -> List[Dict[str, str]]:
    paths = [
        ("stage138_kernel_signal", STAGE138_RATIOS, "kernel-level compact per-bit performance signal"),
        ("stage139_nonclosure", STAGE139_SUMMARY, "direct compact output not PVW_TMLWE closed"),
        ("stage173_toy_phase_noise", STAGE173_PROOF, "finite/toy proof status"),
        ("stage176_security_api_block", STAGE176_SUMMARY, "implementation permission denied"),
        ("stage177_literature_boundary", STAGE177_SUMMARY, "strong novelty denied"),
    ]
    return [
        {
            "artifact": name,
            "path": rel(path),
            "sha256": sha256_file(path),
            "role": role,
        }
        for name, path, role in paths
    ]


def build_permission_rows() -> List[Dict[str, str]]:
    return [
        {
            "candidate": "existing_compact_diagonal_output",
            "permission": "DENY",
            "reason": "Not closed as PVW_TMLWE shared-mask SAB state.",
            "evidence": f"{rel(STAGE139_SUMMARY)}; {rel(STAGE176_API)}",
        },
        {
            "candidate": "omit_body_cross_zero_encryptions",
            "permission": "DENY",
            "reason": "Changes public bootstrapping-key distribution without reduction.",
            "evidence": f"{rel(STAGE176_EVIDENCE)}; {rel(STAGE173_PROOF)}",
        },
        {
            "candidate": "new_structured_shared_mask_encryption",
            "permission": "PROOF_ONLY",
            "reason": "Potential route, but requires new assumption/reduction and closed-state API.",
            "evidence": rel(STAGE176_API),
        },
        {
            "candidate": "compact_then_dense_reexpand",
            "permission": "DEFER",
            "reason": "May cancel compact benefit; no proof or microbench gate yet.",
            "evidence": rel(STAGE176_API),
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "187",
            "name": "compact proof obligation draft",
            "entry_condition": "User wants to pursue compact/shared-output MAT-SAB theory.",
            "gate": "Write formal key distribution, closed-state API, phase, and noise proof outline before code.",
            "failure_rule": "If any obligation remains unresolved, implementation remains denied.",
        },
        {
            "priority": "P1",
            "stage": "188",
            "name": "scoped manuscript skeleton",
            "entry_condition": "Use current implemented exact PVW/MAT-SAB result for paper/report.",
            "gate": "Use Stage185/186 claim boundaries; compact remains future work.",
            "failure_rule": "Reject novelty/compact speedup claims without complete-SAB implementation.",
        },
    ]


def build_summary_rows() -> List[Dict[str, str]]:
    inputs = [
        STAGE138_SUMMARY,
        STAGE138_RATIOS,
        STAGE139_SUMMARY,
        STAGE173_SUMMARY,
        STAGE176_SUMMARY,
        STAGE177_SUMMARY,
        STAGE185_REQ,
    ]
    ok = all(path.exists() for path in inputs)
    return [
        {
            "gate": "stage186_inputs",
            "status": "PASS" if ok else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if ok else "0",
            "evidence": f"{rel(STAGE138_SUMMARY)}; {rel(STAGE176_SUMMARY)}; {rel(STAGE177_SUMMARY)}",
            "detail": "Stage186 consumes compact kernel, closure, toy proof, security/API, literature, and Stage185 requirement evidence.",
            "next_action": "Repair missing inputs before unlock audit.",
        },
        {
            "gate": "stage186_kernel_signal",
            "status": "PASS_KERNEL_ONLY",
            "metric": "stage138_r4_per_bit_speedup_min_max",
            "value": stage138_r4_speedup(),
            "evidence": rel(STAGE138_RATIOS),
            "detail": "Compact remains interesting, but this is not complete-SAB acceleration.",
            "next_action": "Do not implement until proof/API gates pass.",
        },
        {
            "gate": "stage186_unlock_obligations",
            "status": "BLOCKED",
            "metric": "blocked_or_partial_obligations",
            "value": "6",
            "evidence": rel(OBLIGATION_CSV),
            "detail": "Security distribution, closed state, phase proof, noise proof, full-SAB performance, and novelty remain open or partial.",
            "next_action": "Keep compact implementation denied.",
        },
        {
            "gate": "stage186_decision",
            "status": DECISION,
            "metric": "implementation_permission",
            "value": "denied",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Existing evidence does not unlock compact/shared-output MAT-SAB implementation.",
            "next_action": "Proceed only to proof-obligation drafting or scoped manuscript work.",
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    obligation_rows: List[Dict[str, str]],
    evidence_rows: List[Dict[str, str]],
    permission_rows: List[Dict[str, str]],
    next_rows: List[Dict[str, str]],
) -> None:
    write_text_lf(
        OUT_MD,
        f"""# Stage186 Compact Proof Unlock Audit

Decision: `{DECISION}`.

Stage186 audits whether the compact/shared-output MAT-SAB route is ready to
enter production SAB implementation. It is not ready.

The route still has a real kernel-level signal: Stage138 reports r=4
per-bit compact kernel speedup `{stage138_r4_speedup()}x`. But Stage139,
Stage176, and Stage177 prevent implementation and paper-level claims:

- compact output is not closed as the one-shared-mask PVW_TMLWE SAB state;
- deleting/replacing encrypted body-cross zero rows lacks a standard security
  distribution proof;
- phase/noise evidence is toy-level only;
- there is no complete-SAB compact `T_bootstrap/r` benchmark;
- strong novelty remains denied.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Proof Obligation Matrix

{table(obligation_rows, ["obligation", "status", "current_evidence", "what_passes", "what_fails_or_missing", "unlock_condition", "implementation_permission"])}
## Evidence Index

{table(evidence_rows, ["artifact", "path", "sha256", "role"])}
## Implementation Permission

{table(permission_rows, ["candidate", "permission", "reason", "evidence"])}
## Next Queue

{table(next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])}
""",
    )

    write_text_lf(
        PLAN_MD,
        """# Stage186 Plan

Goal: audit compact/shared-output MAT-SAB unlock conditions without writing
production SAB code.

Acceptance:

- list every proof/API/noise/literature obligation;
- map each obligation to current evidence;
- deny implementation if any required obligation remains blocked;
- preserve Stage138 kernel signal as future-work evidence only.
""",
    )

    write_text_lf(
        THEORY_MD,
        """# Stage186 Compact Unlock Model

Compact/shared-output MAT-SAB would be a representation-changing algorithmic
route, not a local AVX512 optimization. It can only enter implementation when
all of the following are simultaneously true:

1. Public key distribution is simulatable or reducible after omitting or
   constraining body-cross zero rows.
2. Every CMUX/NCMUX/RGSW/sparse step returns a closed one-mask/r-body
   PVW_TMLWE state, or a proven conversion exists that does not erase the
   compact benefit.
3. Phase and noise are proven for the production polynomial/RLWE setting.
4. Complete-SAB `T_bootstrap/r` benchmarks pass after implementation.
5. Related-work review permits the precise claim.

Current evidence does not satisfy 1, 2, 3, 4, or 5, so implementation remains
denied.
""",
    )

    write_text_lf(
        VARIANT_MD,
        """# Compact Unlock Audit Variant

This is a no-code proof unlock audit.

Allowed now:

- cite Stage138 as kernel-level motivation;
- cite Stage173 as finite/toy phase-noise support;
- cite Stage176/177 as blockers.

Denied now:

- wiring compact outputs into sab_pvw_*;
- claiming compact SAB complete-bootstrapping speedup;
- claiming novelty or security under standard RLWE.
""",
    )


def update_global_docs() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 186: Compact Proof Unlock Audit",
        f"""
## Stage 186: Compact Proof Unlock Audit

Goal:

```text
Audit whether compact/shared-output MAT-SAB has enough proof, security, API,
noise, performance, and literature evidence to enter production SAB code.
```

Status:

```text
Completed. Stage186 records {DECISION}. Stage138 provides a kernel-level
signal, but Stage139/176/177 still block implementation and strong claims.
Compact/shared-output MAT-SAB remains a proof route only.
```
""",
    )

    append_once(
        GOAL_MD,
        "Stage186 records the compact proof unlock audit",
        f"""
Stage186 records the compact proof unlock audit. Decision: `{DECISION}`.
The compact/shared-output route remains blocked for implementation despite
kernel-level signal, because security distribution, closed shared-mask state,
production noise/phase proof, complete-SAB benchmark, and novelty gates are
not all satisfied.
""",
    )

    append_once(
        CURRENT_GOAL_MD,
        "Treat Stage186 as the compact proof unlock audit",
        f"""
90. Treat Stage186 as the compact proof unlock audit:
    `{DECISION}`. Compact/shared-output MAT-SAB is not unlocked for
    implementation. Stage138 remains kernel-level motivation only; Stage139,
    Stage176, and Stage177 continue to block full SAB code and strong claims.
""",
    )

    append_once(
        HYPOTHESIS_YAML,
        "H110_compact_proof_unlock_audit",
        f"""
  - id: H110_compact_proof_unlock_audit
    statement: >
      Compact/shared-output MAT-SAB should remain blocked unless security
      distribution, closed-state API, phase/noise proof, full-SAB performance,
      and literature gates are all satisfied.
    mechanism: >
      Stage186 audits Stage138 kernel signal against Stage139 closure,
      Stage173 toy proof, Stage176 security/API, Stage177 literature, and
      Stage185 requirement evidence.
    status: stage186_compact_proof_unlock_audit
    evidence: docs/stage186_compact_proof_unlock_audit.md; experiments/stage186_compact_proof_unlock_audit_plan.md; theory_checks/stage186_compact_proof_unlock_model.md; repro/stage186_compact_proof_unlock_audit/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - compact SAB is implemented without closing proof obligations
      - Stage138 kernel-only timing is reported as complete-SAB acceleration
      - broad novelty is claimed before citation-level review
""",
    )

    append_once(
        RUN_LOG,
        "stage186-compact-proof-unlock-audit-001",
        f"""
stage186-compact-proof-unlock-audit-001,2026-07-04,{git_head()},Stage 186,analysis,python scripts/build_stage186_compact_proof_unlock_audit.py,Stage138/139/173/176/177/185 evidence,none,{DECISION},Compact/shared-output MAT-SAB proof unlock audit.,repro/stage186_compact_proof_unlock_audit
""",
    )

    append_once(
        MANIFEST,
        "stage186_compact_proof_unlock_audit",
        f"""
- stage186_compact_proof_unlock_audit: `{DECISION}`
  - `docs/stage186_compact_proof_unlock_audit.md`
  - `experiments/stage186_compact_proof_unlock_audit_plan.md`
  - `theory_checks/stage186_compact_proof_unlock_model.md`
  - `algorithm_variants/mat_rlwe_sab_compact_unlock_audit.md`
  - `repro/stage186_compact_proof_unlock_audit/`
""",
    )

    append_once(CHECKLIST, "Stage186 compact proof unlock audit recorded", """
- [x] Stage186 compact proof unlock audit recorded.
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
    obligation_rows = build_obligation_rows()
    evidence_rows = build_evidence_rows()
    permission_rows = build_permission_rows()
    next_rows = build_next_rows()
    summary_rows = build_summary_rows()

    write_csv(
        OBLIGATION_CSV,
        obligation_rows,
        ["obligation", "status", "current_evidence", "what_passes", "what_fails_or_missing", "unlock_condition", "implementation_permission"],
    )
    write_csv(EVIDENCE_CSV, evidence_rows, ["artifact", "path", "sha256", "role"])
    write_csv(IMPLEMENTATION_CSV, permission_rows, ["candidate", "permission", "reason", "evidence"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, obligation_rows, evidence_rows, permission_rows, next_rows)
    update_global_docs()
    write_artifacts(
        [
            OUT_MD,
            PLAN_MD,
            THEORY_MD,
            VARIANT_MD,
            SUMMARY_CSV,
            OBLIGATION_CSV,
            EVIDENCE_CSV,
            IMPLEMENTATION_CSV,
            NEXT_CSV,
            Path(__file__),
        ]
    )
    print(DECISION)


if __name__ == "__main__":
    main()
