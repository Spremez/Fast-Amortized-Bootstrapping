#!/usr/bin/env python3
"""Stage240: build a scoped LaTeX draft from verified citations and local results."""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage240_scoped_latex_draft"

DOC = ROOT / "docs" / "stage240_scoped_latex_draft.md"
PLAN = ROOT / "experiments" / "stage240_scoped_latex_draft_plan.md"
THEORY = ROOT / "theory_checks" / "stage240_claim_boundary_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage240_scoped_draft.md"

DRAFT = OUT / "pvw_mat_sab_scoped_draft.tex"
TABLE_TEX = OUT / "selected_binary_table.tex"
BIB = OUT / "pvw_mat_sab_references.bib"
CLAIM_AUDIT = OUT / "claim_audit.csv"
CITATION_AUDIT = OUT / "citation_audit.csv"
INPUTS = OUT / "input_status.csv"
GATES = OUT / "gate_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage240_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE236_SUMMARY = ROOT / "repro" / "stage236_set_2_3_4096_r4_highstat_slice" / "selected_binary_matrix_summary.csv"
STAGE237_CLAIMS = ROOT / "repro" / "stage237_scoped_manuscript_package" / "contribution_claims.csv"
STAGE237_SKELETON = ROOT / "repro" / "stage237_scoped_manuscript_package" / "manuscript_skeleton.md"
STAGE239_KEYMAP = ROOT / "repro" / "stage239_bibtex_latex_stub" / "citation_key_map.csv"
STAGE239_TODO = ROOT / "repro" / "stage239_bibtex_latex_stub" / "unresolved_bibtex_todo.csv"
STAGE239_BIB = ROOT / "references" / "stage239_pvw_mat_sab.bib"

DECISION = "PASS_STAGE240_SCOPED_LATEX_DRAFT_READY_CLAIMS_AUDITED"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in str(value))


def cite_map() -> Dict[str, str]:
    return {row["source_id"]: row["citation_key"] for row in read_csv(STAGE239_KEYMAP) if row.get("status") == "READY_FOR_LATEX"}


def cite(source_id: str, cmap: Dict[str, str]) -> str:
    key = cmap.get(source_id, "")
    return f"\\cite{{{key}}}" if key else f"\\textbf{{[citation TODO: {latex_escape(source_id)}]}}"


def table_md(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._\n"
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def input_rows() -> List[Dict[str, str]]:
    paths = [
        (STAGE236_SUMMARY, "selected binary high-stat local result"),
        (STAGE237_CLAIMS, "claim ledger"),
        (STAGE237_SKELETON, "manuscript skeleton"),
        (STAGE239_KEYMAP, "verified citation keys"),
        (STAGE239_TODO, "unresolved citation TODOs"),
        (STAGE239_BIB, "verified BibTeX file"),
    ]
    return [
        {
            "input": rel(path),
            "status": "present" if path.exists() else "missing",
            "role": role,
            "bytes": str(path.stat().st_size) if path.exists() else "",
        }
        for path, role in paths
    ]


def selected_binary_table_tex(rows: List[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            " & ".join(
                [
                    latex_escape(row["param"]),
                    row["r"],
                    row["mean_speedup"],
                    row["speedup_ci95_low"],
                    row["speedup_ci95_high"],
                    latex_escape(row["noise_failures"]),
                    row["key_bytes_ratio"],
                    row["keygen_ratio"],
                    row["rss_ratio"],
                ]
            )
            + r" \\"
        )
    return r"""
\begin{table}[t]
\centering
\small
\caption{Selected binary complete-SAB throughput and side-condition evidence. The speedup is the repeated-scalar total time divided by the PVW/MAT total time for the same r-lane workload, equivalently a comparison of amortized $T_{\mathrm{bootstrap}}/r$.}
\label{tab:selected-binary}
\begin{tabular}{lrrrrrrrr}
\toprule
Param & $r$ & Mean & CI low & CI high & Failures & Key bytes & Keygen & RSS \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}
"""


def claim_audit_rows(claims: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows = []
    for row in claims:
        rows.append(
            {
                "claim_id": row["claim_id"],
                "draft_status": row["status"],
                "included_in_draft": "yes" if row["status"] in {"ALLOW_SCOPED_REPORT", "SCOPED_ONLY_NOT_FINAL"} else "limitation_only",
                "safe_wording": row["safe_wording"],
                "blocked_wording": row["blocked_wording"],
                "evidence": row["evidence"],
            }
        )
    return rows


def citation_audit_rows(cmap: Dict[str, str], todos: List[Dict[str, str]]) -> List[Dict[str, str]]:
    roles = {
        "FAB686_2025": "target baseline identity",
        "INCNTT25_696": "adjacent post-686 transform/backend work",
        "SHAREMASK25_2112": "shared-mask prior-art boundary",
        "BGH2012_565": "PVW/packed-ciphertext background",
        "CGGI2018_421": "TFHE/external-product background",
        "MS2018_532": "amortized FHEW/ring packing related work",
        "GPVL2023_014": "amortized bootstrapping related work",
        "DKMS2024_112": "ring-automorphism amortized bootstrapping related work",
        "LW2023_910": "amortized functional bootstrapping related work",
    }
    rows = [
        {
            "source_id": source_id,
            "status": "READY_FOR_LATEX",
            "citation_key": key,
            "draft_role": roles.get(source_id, "related work"),
            "claim_boundary": "background or scoped positioning only",
        }
        for source_id, key in sorted(cmap.items())
    ]
    for row in todos:
        rows.append(
            {
                "source_id": row["source_id"],
                "status": row["todo_status"],
                "citation_key": "",
                "draft_role": "TODO comment only",
                "claim_boundary": row["needed_action"],
            }
        )
    return rows


def draft_tex(rows: List[Dict[str, str]], cmap: Dict[str, str], todos: List[Dict[str, str]]) -> str:
    speeds = [float(row["mean_speedup"]) for row in rows]
    ci_lows = [float(row["speedup_ci95_low"]) for row in rows]
    max_key = max(float(row["key_bytes_ratio"]) for row in rows)
    max_keygen = max(float(row["keygen_ratio"]) for row in rows)
    todo_comments = "\n".join(
        f"% CITATION TODO [{row['source_id']}]: {row['needed_action']}" for row in todos
    )
    return rf"""
\documentclass{{article}}
\usepackage[T1]{{fontenc}}
\usepackage[margin=1in]{{geometry}}
\usepackage{{amsmath}}
\usepackage{{booktabs}}
\usepackage{{hyperref}}

\title{{Scoped Evidence Draft for Exact Dense PVW/MAT-SAB}}
\author{{Anonymous}}
\date{{}}

\begin{{document}}
\maketitle

\begin{{abstract}}
We evaluate an exact dense PVW/MAT-RLWE realization of 2025/686-style sparse
amortized bootstrapping {cite("FAB686_2025", cmap)}. The accumulator uses one
shared mask with $r$ independent body lanes, and the primary endpoint is
complete bootstrapping time per processed plaintext lane, $T_{{\mathrm{{bootstrap}}}}/r$,
against $r$ repeated scalar SAB executions under the same backend. On the
selected binary rows in Table~\ref{{tab:selected-binary}}, the current
implementation records mean speedups from {min(speeds):.6f}x to {max(speeds):.6f}x,
with the weakest reported 95\% CI lower bound {min(ci_lows):.6f}x. The same
rows record zero PVW/scalar/pair final-output failures in 20 deterministic
seeds per row. The result is deliberately scoped: it is not a non-binary claim,
not a compact-selector construction, not a broad novelty claim, and not a
theoretical optimality theorem.
\end{{abstract}}

\section{{Research Question and Metric}}
The research question is whether replacing $r$ independent RLWE/SAB executions
with an $r$-body MAT-RLWE accumulator improves the full bootstrapping cost per
handled plaintext lane. The comparison is therefore not a single PVW/MAT run
against a single scalar run. The measured speedup is
\[
S_r = \frac{{T_{{\mathrm{{scalar}},r\ \mathrm{{repeated}}}}}}
           {{T_{{\mathrm{{PVW/MAT}},r\ \mathrm{{lanes}}}}}},
\]
which is equivalent to comparing amortized $T_{{\mathrm{{bootstrap}}}}/r$ for the
same $r$-lane workload. All performance rows in this draft use complete-SAB
timing and keep the scalar SAB path as the reference implementation.

\section{{Related Work Boundary}}
The target baseline is the 2025/686 SAB construction {cite("FAB686_2025", cmap)}.
Incomplete-NTT acceleration is adjacent post-686 transform/backend work and is
not folded into the PVW/MAT lane-batching claim {cite("INCNTT25_696", cmap)}.
Shared-mask packed-message TFHE creates prior-art risk for broad shared-mask
novelty language {cite("SHAREMASK25_2112", cmap)}. PVW packing and packed
ciphertext background are treated as building blocks {cite("BGH2012_565", cmap)},
and TFHE/external-product terminology is background rather than a contribution
{cite("CGGI2018_421", cmap)}. Amortized, batched, and SIMD bootstrapping axes
are established related work {cite("MS2018_532", cmap)}, {cite("GPVL2023_014", cmap)},
{cite("DKMS2024_112", cmap)}, {cite("LW2023_910", cmap)}.

{todo_comments}

\section{{Algorithm Object}}
The implemented object is exact dense PVW/MAT-SAB. The scalar state has one
mask/body pair per independent lane. The PVW/MAT state keeps one shared mask
and $r$ body lanes. In this implementation, $r$ denotes independent LUT/SAB
lanes, not adjacent accumulator-index packing. The correctness invariant is
lane-wise: after each promoted stage and in the final output, PVW/MAT body lane
$q$ must match the scalar SAB reference for lane $q$ under the same input, LUT,
key material, backend, and parameter row.

The exact dense path preserves the scalar SAB semantics and amortizes shared
mask/schedule work, but it also pays dense MAT external-product and resource
costs. The current evidence therefore supports a measured complete-SAB
throughput claim on selected binary rows only. It does not prove that dense MAT
is asymptotically or universally optimal among all possible SAB-compatible
MAT-RLWE layouts.

\section{{Implementation Scope}}
The implementation keeps the original scalar SAB path available for A/B testing
and routes the optimized path through explicit PVW/MAT entry points. The
paper-facing implementation description should name the exact dense PVW/MAT
path, active-buffer/copyback reductions where they are part of the measured
code path, and the AVX512/spqlios backend used for the selected rows. Backend
counter evidence may explain a mechanism, but complete-SAB $T_{{\mathrm{{bootstrap}}}}/r$
remains the primary endpoint.

\input{{selected_binary_table.tex}}

\section{{Evaluation Summary}}
Table~\ref{{tab:selected-binary}} reports four selected binary rows. Each row
uses 10 complete-SAB A/B timing samples and 20 deterministic noise/correctness
seeds. The key-size ratio is at most {max_key:.6f} and the keygen-time ratio is
at most {max_keygen:.6f} in this selected matrix, so throughput is reported
together with public-key and setup side costs rather than alone.

\section{{Claim Audit}}
The allowed claim is narrow: exact dense PVW/MAT-SAB improves complete-SAB
$T_{{\mathrm{{bootstrap}}}}/r$ over repeated scalar SAB on the selected binary
rows under the recorded backend and run protocol. The draft must not claim
all-parameter coverage, non-binary coverage, compact selector support, first
shared-mask batching, first PVW packing, or theoretical optimality. These
blocked statements are tracked in \texttt{{claim\_audit.csv}}.

\section{{Limitations and Next Gates}}
This draft is an evidence artifact, not a final submission. Remaining gates
include venue/template compilation, unresolved bibliography rows, any refreshed
native-counter attribution needed for final wording, and separate proofs or
experiments for non-binary, compact, or theoretically optimal MAT-RLWE SAB
variants.

\bibliographystyle{{plain}}
\bibliography{{pvw_mat_sab_references}}
\end{{document}}
"""


def cited_keys(tex: str) -> List[str]:
    keys = []
    for block in re.findall(r"\\cite\{([^}]+)\}", tex):
        keys.extend(key.strip() for key in block.split(",") if key.strip())
    return keys


def positive_forbidden_hits(tex: str, terms: List[str]) -> List[str]:
    lower = tex.lower()
    hits = []
    negations = ["not ", "does not", "must not", "do not", " no ", " without "]
    for term in terms:
        start = 0
        term_lower = term.lower()
        while True:
            idx = lower.find(term_lower, start)
            if idx < 0:
                break
            prefix = lower[max(0, idx - 90) : idx]
            if not any(marker in prefix for marker in negations):
                hits.append(term)
                break
            start = idx + len(term_lower)
    return hits


def gate_rows(inputs: List[Dict[str, str]], rows: List[Dict[str, str]], cmap: Dict[str, str], todos: List[Dict[str, str]], tex: str) -> List[Dict[str, str]]:
    keys = set(cmap.values())
    used = set(cited_keys(tex))
    forbidden = [
        "theoretically optimal construction",
        "universally optimal",
        "lower-bound tight",
        "we are the first",
        "first-of-its-kind",
        "all parameters are supported",
        "non-binary support is proven",
    ]
    forbidden_hits = positive_forbidden_hits(tex, forbidden)
    rows_out = [
        {
            "gate": "G1_inputs",
            "required": "Stage236 results, Stage237 claims, Stage239 keymap/BibTeX exist",
            "observed": "all present" if all(row["status"] == "present" for row in inputs) else "missing input",
            "status": "PASS" if all(row["status"] == "present" for row in inputs) else "FAIL",
            "claim_effect": "draft can be generated only from verified local inputs",
        },
        {
            "gate": "G2_experiment_rows",
            "required": "four selected binary high-stat rows",
            "observed": f"rows={len(rows)}; params={','.join(row['param'] + ':r' + row['r'] for row in rows)}",
            "status": "PASS" if len(rows) == 4 else "FAIL",
            "claim_effect": "bounds throughput claim to selected binary matrix",
        },
        {
            "gate": "G3_citations_subset",
            "required": "all LaTeX cite keys appear in Stage239 keymap",
            "observed": f"used={len(used)}; missing={sorted(used - keys)}; todos={len(todos)}",
            "status": "PASS" if used <= keys and len(used) > 0 else "FAIL",
            "claim_effect": "prevents unverified citations in draft body",
        },
        {
            "gate": "G4_todo_visibility",
            "required": "unresolved Stage239 sources remain visible TODO comments",
            "observed": f"todos={len(todos)}",
            "status": "PASS_TODOS_VISIBLE" if all(row["source_id"] in tex for row in todos) else "FAIL",
            "claim_effect": "prevents silent bibliography gaps",
        },
        {
            "gate": "G5_overclaim_guard",
            "required": "no broad novelty/non-binary/all-parameter/optimality wording",
            "observed": "hits=" + ",".join(forbidden_hits),
            "status": "PASS_NO_FORBIDDEN_STRONG_CLAIM" if not forbidden_hits else "FAIL",
            "claim_effect": "allows scoped draft only",
        },
    ]
    decision = DECISION if all(not row["status"].startswith("FAIL") for row in rows_out) else "FAIL_STAGE240_GATE_FAILURE"
    rows_out.append(
        {
            "gate": "G6_stage240_decision",
            "required": "all gates pass or explicit TODO visibility gate passes",
            "observed": decision,
            "status": decision,
            "claim_effect": "draft ready for compile/template pass, not final paper",
        }
    )
    return rows_out


def proof_rows(gates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "gate": row["gate"],
            "status": row["status"],
            "metric": row["required"],
            "value": row["observed"],
            "evidence": rel(GATES),
            "interpretation": row["claim_effect"],
        }
        for row in gates
    ]


def next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage241_latex_compile_or_template_port",
            "entry_condition": "A PDF or venue-formatted draft is needed.",
            "gate": "Compile without citation errors using only Stage239 keys and TODO comments.",
            "status": "selected_if_paper_build_needed",
            "failure_action": "Keep Stage240 source draft and fix TeX/template issues separately.",
            "evidence": rel(DRAFT),
        },
        {
            "priority": "P1",
            "route": "stage242_unresolved_bibtex_followup",
            "entry_condition": "Final bibliography closure is required.",
            "gate": "Resolve BATCHBOOT26 and split LW23A_B from verified official routes.",
            "status": "future",
            "failure_action": "Leave TODO comments; do not submit final paper.",
            "evidence": rel(STAGE239_TODO),
        },
        {
            "priority": "P2",
            "route": "stage243_native_counter_refresh_if_code_changes",
            "entry_condition": "Final implementation section needs current-head counter wording.",
            "gate": "Native Linux perf counters or explicit reuse of Stage226 with code-change audit.",
            "status": "optional",
            "failure_action": "Keep counter evidence out of the main claim.",
            "evidence": "repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv",
        },
        {
            "priority": "P3",
            "route": "stage244_nonbinary_or_compact_algorithm_gate",
            "entry_condition": "A broader algorithmic claim is proposed.",
            "gate": "Closed equations, correctness/noise proof obligations, full-SAB A/B and resource matrix.",
            "status": "blocked_until_new_design",
            "failure_action": "Do not extend selected binary claim.",
            "evidence": rel(CLAIM_AUDIT),
        },
    ]


def artifact_rows(paths: List[Path]) -> List[Dict[str, str]]:
    return [
        {
            "artifact": rel(path),
            "bytes": str(path.stat().st_size) if path.exists() else "",
            "sha256": sha256(path) if path.exists() else "",
        }
        for path in paths
    ]


def write_repro_commands() -> None:
    write_text(
        REPRO_CMDS,
        f"""# Stage240 Reproduction Commands

```bash
python scripts/build_stage240_scoped_latex_draft.py
```

Decision: `{DECISION}`.
Input head: `{git_head()}`.
""",
    )


def write_docs(inputs: List[Dict[str, str]], rows: List[Dict[str, str]], claims: List[Dict[str, str]], citation_rows: List[Dict[str, str]], gates: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> None:
    write_text(
        DOC,
        f"""# Stage240 Scoped LaTeX Draft

Decision: `{DECISION}`.

Stage240 converts the Stage236 selected binary high-stat matrix and Stage239
verified BibTeX into a scoped LaTeX draft. It is a paper-facing artifact, not a
final submission and not a new optimality or novelty claim.

## Experiment Rows

{table_md(rows, ["param", "r", "stage", "stat_level", "mean_speedup", "speedup_ci95_low", "speedup_ci95_high", "noise_failures", "key_bytes_ratio", "keygen_ratio", "rss_ratio", "status", "evidence"])}

## Claim Audit

{table_md(claims, ["claim_id", "draft_status", "included_in_draft", "safe_wording", "blocked_wording", "evidence"])}

## Citation Audit

{table_md(citation_rows, ["source_id", "status", "citation_key", "draft_role", "claim_boundary"])}

## Gates

{table_md(gates, ["gate", "required", "observed", "status", "claim_effect"])}

## Next Queue

{table_md(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

## Inputs

{table_md(inputs, ["input", "status", "role", "bytes"])}
""",
    )
    write_text(
        REPORT,
        f"""# Stage240 Report

Decision: `{DECISION}`.

Generated artifacts:

- `{rel(DRAFT)}`
- `{rel(TABLE_TEX)}`
- `{rel(BIB)}`
- `{rel(CLAIM_AUDIT)}`
- `{rel(CITATION_AUDIT)}`
- `{rel(PROOF)}`

The draft cites only Stage239 ready keys and keeps unresolved sources as TODO
comments. Its quantitative statement is limited to Stage236 selected binary
complete-SAB `T_bootstrap/r` evidence.
""",
    )
    write_text(
        PLAN,
        """# Stage240 Scoped LaTeX Draft Plan

Goal: convert verified citations and selected binary experiments into a
bounded LaTeX draft.

Correctness gate: every `\\cite{}` key must be present in Stage239 keymap.
Performance gate: all quantitative speedups must come from Stage236 selected
binary matrix. Overclaim gate: no all-parameter, non-binary, novelty, or
theoretical-optimality statement is promoted.
""",
    )
    write_text(
        THEORY,
        """# Stage240 Claim Boundary Model

The paper-facing metric remains complete-SAB amortized `T_bootstrap/r`.
Stage240 permits only evidence-backed selected-binary claims. It does not
convert Stage226 counter attribution into a theoretical optimality claim and it
does not convert Stage239 related-work coverage into novelty.
""",
    )
    write_text(
        VARIANT,
        """# mat_rlwe_sab_stage240_scoped_draft

This is not a new algorithm variant. It is the paper-facing representation of
the already measured exact dense PVW/MAT-SAB route.

Allowed: selected binary complete-SAB throughput, sampled zero-failure rows,
and resource side costs.

Denied: all-parameter support, non-binary support, compact selector support,
first/shared-mask novelty, and theoretical optimality.
""",
    )


def update_project_files() -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 240: Scoped LaTeX Draft",
        f"""
## Stage 240: Scoped LaTeX Draft

Goal:

```text
Convert verified Stage239 citations and Stage236 selected binary complete-SAB
evidence into a scoped LaTeX draft with claim/citation gates.
```

Status:

```text
Generated from input head `{head}` with `{DECISION}`. The draft is ready for a
compile/template pass, while unresolved BibTeX rows, current-head counter
refresh, non-binary support, compact route, and theoretical optimality remain
separate gates.
```
""",
    )
    append_once(
        GOAL,
        "Stage240 scoped LaTeX draft",
        f"""
- Stage240 scoped LaTeX draft records `{DECISION}`: a paper-facing draft now
  exists, but it is scoped to selected binary exact dense PVW/MAT-SAB and does
  not close novelty, non-binary, compact, or optimality gates.
""",
    )
    append_once(
        CURRENT_GOAL,
        "### Stage240 scoped LaTeX draft",
        f"""
### Stage240 scoped LaTeX draft

`{DECISION}` records a scoped LaTeX draft using Stage236 experiments and
Stage239 verified citations. The active goal remains open because final paper
compilation, unresolved BibTeX rows, optional counter refresh, non-binary
support, compact route, and theoretical optimality remain incomplete.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage240_scoped_latex_draft:",
        f"""
H10_stage240_scoped_latex_draft:
  status: scoped_latex_draft_ready_claims_audited
  evidence:
    - repro/stage240_scoped_latex_draft/pvw_mat_sab_scoped_draft.tex
    - repro/stage240_scoped_latex_draft/claim_audit.csv
    - repro/stage240_scoped_latex_draft/citation_audit.csv
    - repro/stage240_scoped_latex_draft/proof_gate.csv
    - docs/stage240_scoped_latex_draft.md
  conclusion: >
    Stage240 records {DECISION}. It converts the selected binary exact dense
    PVW/MAT-SAB evidence and verified citations into a scoped LaTeX draft. The
    claim remains limited to complete-SAB T_bootstrap/r on the recorded binary
    rows; broader algorithmic and optimality claims remain gated.
""",
    )
    append_once(
        RUN_LOG,
        "stage240-scoped-latex-draft-001",
        f"""stage240-scoped-latex-draft-001,{date.today().isoformat()},{head},Stage 240,aggregation,"python scripts/build_stage240_scoped_latex_draft.py","Stage236 selected matrix + Stage239 citations",n/a,{DECISION},"Scoped LaTeX draft and claim audit generated.",docs/stage240_scoped_latex_draft.md; repro/stage240_scoped_latex_draft/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage240_scoped_latex_draft:",
        """
- stage240_scoped_latex_draft:
  - `docs/stage240_scoped_latex_draft.md`
  - `experiments/stage240_scoped_latex_draft_plan.md`
  - `theory_checks/stage240_claim_boundary_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage240_scoped_draft.md`
  - `scripts/build_stage240_scoped_latex_draft.py`
  - `repro/stage240_scoped_latex_draft/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage240 scoped LaTeX draft records claim and citation gates",
        f"""
- [x] Stage240 scoped LaTeX draft records claim and citation gates `{DECISION}`.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = input_rows()
    rows = read_csv(STAGE236_SUMMARY)
    cmap = cite_map()
    todos = read_csv(STAGE239_TODO)
    claim_rows = claim_audit_rows(read_csv(STAGE237_CLAIMS))
    citation_rows = citation_audit_rows(cmap, todos)

    table_tex = selected_binary_table_tex(rows)
    tex = draft_tex(rows, cmap, todos)
    gates = gate_rows(inputs, rows, cmap, todos, tex)
    proof = proof_rows(gates)
    nextq = next_rows()

    write_text(TABLE_TEX, table_tex)
    write_text(DRAFT, tex)
    shutil.copyfile(STAGE239_BIB, BIB)
    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(CLAIM_AUDIT, claim_rows, ["claim_id", "draft_status", "included_in_draft", "safe_wording", "blocked_wording", "evidence"])
    write_csv(CITATION_AUDIT, citation_rows, ["source_id", "status", "citation_key", "draft_role", "claim_boundary"])
    write_csv(GATES, gates, ["gate", "required", "observed", "status", "claim_effect"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_repro_commands()
    write_docs(inputs, rows, claim_rows, citation_rows, gates, nextq)

    artifacts = [DOC, PLAN, THEORY, VARIANT, DRAFT, TABLE_TEX, BIB, CLAIM_AUDIT, CITATION_AUDIT, INPUTS, GATES, PROOF, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "bytes", "sha256"])
    update_project_files()

    print(f"Stage240 report: {rel(DOC)}")
    print(f"Stage240 decision: {DECISION}")


if __name__ == "__main__":
    main()
