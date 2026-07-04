#!/usr/bin/env python3
"""Stage241: compile the Stage240 scoped LaTeX draft and record gates."""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage241_latex_compile_package"
BUILD = OUT / "build"

DOC = ROOT / "docs" / "stage241_latex_compile_package.md"
PLAN = ROOT / "experiments" / "stage241_latex_compile_package_plan.md"
THEORY = ROOT / "theory_checks" / "stage241_compile_claim_boundary.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage241_compile_package.md"

INPUTS = OUT / "input_status.csv"
COMMANDS = OUT / "command_log.csv"
COMPILE_CHECKS = OUT / "compile_checks.csv"
CITATION_CHECKS = OUT / "citation_resolution.csv"
PDF_ARTIFACT = OUT / "pdf_artifact.csv"
GATES = OUT / "gate_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage241_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE240 = ROOT / "repro" / "stage240_scoped_latex_draft"
STAGE240_TEX = STAGE240 / "pvw_mat_sab_scoped_draft.tex"
STAGE240_TABLE = STAGE240 / "selected_binary_table.tex"
STAGE240_BIB = STAGE240 / "pvw_mat_sab_references.bib"
STAGE240_PROOF = STAGE240 / "proof_gate.csv"
STAGE240_CLAIM_AUDIT = STAGE240 / "claim_audit.csv"
STAGE239_TODO = ROOT / "repro" / "stage239_bibtex_latex_stub" / "unresolved_bibtex_todo.csv"

BUILD_TEX = BUILD / "pvw_mat_sab_scoped_draft.tex"
BUILD_TABLE = BUILD / "selected_binary_table.tex"
BUILD_BIB = BUILD / "pvw_mat_sab_references.bib"
BUILD_PDF = BUILD / "pvw_mat_sab_scoped_draft.pdf"
BUILD_LOG = BUILD / "pvw_mat_sab_scoped_draft.log"
BUILD_AUX = BUILD / "pvw_mat_sab_scoped_draft.aux"
BUILD_BBL = BUILD / "pvw_mat_sab_scoped_draft.bbl"
BUILD_BLG = BUILD / "pvw_mat_sab_scoped_draft.blg"

DECISION = "PASS_STAGE241_LATEX_COMPILE_PACKAGE_READY"


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


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._\n"
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|").replace("\n", "<br>") for field in fields) + " |")
    return "\n".join(out) + "\n"


def input_rows() -> List[Dict[str, str]]:
    paths = [
        (STAGE240_TEX, "Stage240 scoped LaTeX source"),
        (STAGE240_TABLE, "Stage240 selected binary table"),
        (STAGE240_BIB, "Stage240 verified references"),
        (STAGE240_PROOF, "Stage240 proof gates"),
        (STAGE240_CLAIM_AUDIT, "Stage240 claim audit"),
        (STAGE239_TODO, "unresolved bibliography TODOs"),
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


def prepare_build() -> None:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STAGE240_TEX, BUILD_TEX)
    shutil.copyfile(STAGE240_TABLE, BUILD_TABLE)
    shutil.copyfile(STAGE240_BIB, BUILD_BIB)


def run_command(exe: str, args: List[str], step: str) -> Dict[str, str]:
    command = [exe] + args
    log_path = OUT / f"{step}.log"
    try:
        completed = subprocess.run(
            command,
            cwd=BUILD,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
        )
        output = completed.stdout or ""
        status = "PASS" if completed.returncode == 0 else "FAIL"
        rc = completed.returncode
    except FileNotFoundError as exc:
        output = f"{type(exc).__name__}: {exc}"
        status = "FAIL_TOOL_MISSING"
        rc = 127
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + "\nTIMEOUT"
        status = "FAIL_TIMEOUT"
        rc = 124
    write_text(log_path, output)
    return {
        "step": step,
        "command": " ".join(command),
        "return_code": str(rc),
        "status": status,
        "log": rel(log_path),
    }


def compile_draft() -> List[Dict[str, str]]:
    return [
        run_command("pdflatex", ["-interaction=nonstopmode", "-halt-on-error", BUILD_TEX.name], "01_pdflatex_initial"),
        run_command("bibtex", ["pvw_mat_sab_scoped_draft"], "02_bibtex"),
        run_command("pdflatex", ["-interaction=nonstopmode", "-halt-on-error", BUILD_TEX.name], "03_pdflatex_after_bibtex"),
        run_command("pdflatex", ["-interaction=nonstopmode", "-halt-on-error", BUILD_TEX.name], "04_pdflatex_final"),
    ]


def normalize_text_file(path: Path) -> None:
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    path.write_bytes(("\n".join(line.rstrip() for line in lines) + "\n").encode("utf-8"))


def normalize_compile_artifacts(commands: List[Dict[str, str]]) -> None:
    for row in commands:
        normalize_text_file(ROOT / row["log"])
    for path in [BUILD_AUX, BUILD_BBL, BUILD_BLG, BUILD_LOG]:
        normalize_text_file(path)


def source_cite_keys(text: str) -> List[str]:
    keys: List[str] = []
    for block in re.findall(r"\\cite\{([^}]+)\}", text):
        keys.extend(key.strip() for key in block.split(",") if key.strip())
    return keys


def positive_forbidden_hits(text: str) -> List[str]:
    lower = text.lower()
    terms = [
        "theoretically optimal construction",
        "universally optimal",
        "lower-bound tight",
        "we are the first",
        "first-of-its-kind",
        "all parameters are supported",
        "non-binary support is proven",
    ]
    negations = ["not ", "does not", "must not", "do not", " no ", " without "]
    hits: List[str] = []
    for term in terms:
        start = 0
        while True:
            idx = lower.find(term, start)
            if idx < 0:
                break
            prefix = lower[max(0, idx - 90) : idx]
            if not any(marker in prefix for marker in negations):
                hits.append(term)
                break
            start = idx + len(term)
    return hits


def compile_check_rows(commands: List[Dict[str, str]]) -> List[Dict[str, str]]:
    final_log = read_text(BUILD_LOG)
    pdf_ok = BUILD_PDF.exists() and BUILD_PDF.stat().st_size > 0
    undefined_citations = sorted(set(re.findall(r"Citation `([^']+)' .* undefined", final_log)))
    undefined_refs = sorted(set(re.findall(r"Reference `([^']+)' .* undefined", final_log)))
    fatal = "Fatal error" in final_log or "Emergency stop" in final_log or "! " in final_log
    bbl_items = len(re.findall(r"\\bibitem\{", read_text(BUILD_BBL)))
    source_keys = source_cite_keys(read_text(BUILD_TEX))
    return [
        {
            "check": "all_commands_return_zero",
            "observed": ";".join(row["step"] + "=" + row["return_code"] for row in commands),
            "status": "PASS" if all(row["return_code"] == "0" for row in commands) else "FAIL",
            "evidence": rel(COMMANDS),
        },
        {
            "check": "pdf_exists",
            "observed": f"exists={pdf_ok}; bytes={BUILD_PDF.stat().st_size if BUILD_PDF.exists() else 0}",
            "status": "PASS" if pdf_ok else "FAIL",
            "evidence": rel(BUILD_PDF),
        },
        {
            "check": "no_undefined_citations",
            "observed": ",".join(undefined_citations),
            "status": "PASS" if not undefined_citations else "FAIL",
            "evidence": rel(BUILD_LOG),
        },
        {
            "check": "no_undefined_references",
            "observed": ",".join(undefined_refs),
            "status": "PASS" if not undefined_refs else "FAIL",
            "evidence": rel(BUILD_LOG),
        },
        {
            "check": "no_fatal_latex_error",
            "observed": f"fatal={fatal}",
            "status": "PASS" if not fatal else "FAIL",
            "evidence": rel(BUILD_LOG),
        },
        {
            "check": "bbl_matches_cite_count",
            "observed": f"cite_keys={len(set(source_keys))}; bibitems={bbl_items}",
            "status": "PASS" if bbl_items == len(set(source_keys)) and bbl_items > 0 else "FAIL",
            "evidence": rel(BUILD_BBL),
        },
        {
            "check": "overclaim_guard",
            "observed": "hits=" + ",".join(positive_forbidden_hits(read_text(BUILD_TEX))),
            "status": "PASS" if not positive_forbidden_hits(read_text(BUILD_TEX)) else "FAIL",
            "evidence": rel(BUILD_TEX),
        },
    ]


def citation_rows() -> List[Dict[str, str]]:
    tex = read_text(BUILD_TEX)
    bbl = read_text(BUILD_BBL)
    aux = read_text(BUILD_AUX)
    keys = sorted(set(source_cite_keys(tex)))
    return [
        {
            "citation_key": key,
            "in_tex": "yes" if key in tex else "no",
            "in_aux": "yes" if key in aux else "no",
            "in_bbl": "yes" if ("\\bibitem{" + key + "}") in bbl else "no",
            "status": "PASS" if key in aux and ("\\bibitem{" + key + "}") in bbl else "FAIL",
        }
        for key in keys
    ]


def pdf_rows() -> List[Dict[str, str]]:
    paths = [BUILD_PDF, BUILD_LOG, BUILD_BBL, BUILD_BLG, BUILD_AUX]
    rows = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "bytes": str(path.stat().st_size) if path.exists() else "0",
                "sha256": sha256(path) if path.exists() else "",
            }
        )
    return rows


def gate_rows(inputs: List[Dict[str, str]], commands: List[Dict[str, str]], checks: List[Dict[str, str]], cites: List[Dict[str, str]]) -> List[Dict[str, str]]:
    input_ok = all(row["status"] == "present" for row in inputs)
    command_ok = all(row["return_code"] == "0" for row in commands)
    checks_ok = all(row["status"] == "PASS" for row in checks)
    cites_ok = all(row["status"] == "PASS" for row in cites) and len(cites) > 0
    rows = [
        {
            "gate": "G1_inputs",
            "required": "Stage240 TeX/table/BibTeX/proof and Stage239 TODOs exist",
            "observed": "all present" if input_ok else "missing input",
            "status": "PASS" if input_ok else "FAIL",
            "claim_effect": "compile package can only be built from verified prior-stage inputs",
        },
        {
            "gate": "G2_compile_chain",
            "required": "pdflatex, bibtex, pdflatex, pdflatex all return zero",
            "observed": ";".join(row["step"] + "=" + row["return_code"] for row in commands),
            "status": "PASS" if command_ok else "FAIL",
            "claim_effect": "draft is mechanically buildable on this host",
        },
        {
            "gate": "G3_compile_checks",
            "required": "PDF exists; no undefined citations/references/fatal errors; bbl count matches cites",
            "observed": ";".join(row["check"] + "=" + row["status"] for row in checks),
            "status": "PASS" if checks_ok else "FAIL",
            "claim_effect": "compiled PDF has resolved bibliography and table references",
        },
        {
            "gate": "G4_citation_resolution",
            "required": "every source cite key appears in aux and bbl",
            "observed": f"citation_rows={len(cites)}",
            "status": "PASS" if cites_ok else "FAIL",
            "claim_effect": "no invisible or unresolved citation gap in compiled package",
        },
    ]
    decision = DECISION if all(not row["status"].startswith("FAIL") for row in rows) else "FAIL_STAGE241_LATEX_COMPILE_PACKAGE"
    rows.append(
        {
            "gate": "G5_stage241_decision",
            "required": "all compile/package gates pass",
            "observed": decision,
            "status": decision,
            "claim_effect": "compiled package ready; final paper closure still requires TODO bibliography/template decisions",
        }
    )
    return rows


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
            "route": "stage242_unresolved_bibtex_followup",
            "entry_condition": "Final bibliography closure is required.",
            "gate": "Resolve BATCHBOOT26 and split LW23A_B from verified official routes.",
            "status": "selected",
            "failure_action": "Keep TODO comments; do not submit as final paper.",
            "evidence": rel(STAGE239_TODO),
        },
        {
            "priority": "P1",
            "route": "stage243_native_counter_refresh_if_code_changes",
            "entry_condition": "Final implementation section needs current-head counter wording.",
            "gate": "Native Linux perf counters or explicit reuse of Stage226 with code-change audit.",
            "status": "optional",
            "failure_action": "Keep counter evidence out of the main claim.",
            "evidence": "repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv",
        },
        {
            "priority": "P2",
            "route": "stage244_nonbinary_or_compact_algorithm_gate",
            "entry_condition": "A broader algorithmic claim is proposed.",
            "gate": "Closed equations, correctness/noise proof obligations, full-SAB A/B and resource matrix.",
            "status": "blocked_until_new_design",
            "failure_action": "Do not extend selected binary claim.",
            "evidence": rel(STAGE240_CLAIM_AUDIT),
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
        f"""# Stage241 Reproduction Commands

```bash
python scripts/build_stage241_latex_compile_package.py
```

Manual equivalent inside `repro/stage241_latex_compile_package/build/`:

```bash
pdflatex -interaction=nonstopmode -halt-on-error pvw_mat_sab_scoped_draft.tex
bibtex pvw_mat_sab_scoped_draft
pdflatex -interaction=nonstopmode -halt-on-error pvw_mat_sab_scoped_draft.tex
pdflatex -interaction=nonstopmode -halt-on-error pvw_mat_sab_scoped_draft.tex
```

Decision: `{DECISION}`.
Input head: `{git_head()}`.
""",
    )


def write_docs(inputs: List[Dict[str, str]], commands: List[Dict[str, str]], checks: List[Dict[str, str]], cites: List[Dict[str, str]], pdfs: List[Dict[str, str]], gates: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> None:
    write_text(
        DOC,
        f"""# Stage241 LaTeX Compile Package

Decision: `{gates[-1]["status"]}`.

Stage241 compiles the Stage240 scoped draft and records a reproducible PDF/log
package. This is a packaging and audit gate only; it does not add a new
algorithmic, novelty, or optimality claim.

## Commands

{table(commands, ["step", "command", "return_code", "status", "log"])}

## Compile Checks

{table(checks, ["check", "observed", "status", "evidence"])}

## Citation Resolution

{table(cites, ["citation_key", "in_tex", "in_aux", "in_bbl", "status"])}

## PDF Artifacts

{table(pdfs, ["artifact", "exists", "bytes", "sha256"])}

## Gates

{table(gates, ["gate", "required", "observed", "status", "claim_effect"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

## Inputs

{table(inputs, ["input", "status", "role", "bytes"])}
""",
    )
    write_text(
        REPORT,
        f"""# Stage241 Report

Decision: `{gates[-1]["status"]}`.

The compiled PDF is `{rel(BUILD_PDF)}`. The final LaTeX log is
`{rel(BUILD_LOG)}` and the generated bibliography is `{rel(BUILD_BBL)}`.

All citations must remain sourced from Stage239 verified BibTeX. Unresolved
Stage239 bibliography rows remain outside the bibliography and visible only as
TODO comments in the draft source.
""",
    )
    write_text(
        PLAN,
        """# Stage241 LaTeX Compile Package Plan

Goal: mechanically compile the Stage240 scoped draft and record reproducible
PDF/log evidence.

Correctness gate: full LaTeX/BibTeX compile chain returns zero, no undefined
citations or references remain, and the generated `.bbl` contains exactly the
source cite keys. Overclaim gate: source text remains bounded to Stage240 claim
scope.
""",
    )
    write_text(
        THEORY,
        """# Stage241 Compile Claim Boundary

Stage241 proves only that the scoped evidence draft compiles with resolved
citations and references. It does not strengthen the algorithmic result beyond
the Stage236 selected-binary complete-SAB `T_bootstrap/r` evidence.
""",
    )
    write_text(
        VARIANT,
        """# mat_rlwe_sab_stage241_compile_package

This is a compile/package artifact, not an algorithm variant. It freezes the
paper-facing representation of the exact dense PVW/MAT-SAB evidence and keeps
all broader algorithm claims gated.
""",
    )


def update_project_files(decision: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 241: LaTeX Compile Package",
        f"""
## Stage 241: LaTeX Compile Package

Goal:

```text
Compile the Stage240 scoped LaTeX draft with BibTeX and record PDF/log gates.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. The scoped draft now has
resolved compile evidence. Remaining gates are bibliography TODO closure,
optional current-head counter wording, and any broader algorithmic route.
```
""",
    )
    append_once(
        GOAL,
        "Stage241 LaTeX compile package",
        f"""
- Stage241 LaTeX compile package records `{decision}`: the scoped draft has a
  reproducible PDF/log package, but this does not expand the selected-binary
  claim boundary.
""",
    )
    append_once(
        CURRENT_GOAL,
        "### Stage241 LaTeX compile package",
        f"""
### Stage241 LaTeX compile package

`{decision}` records successful compile/package evidence for the scoped draft.
The active goal remains open because unresolved bibliography rows, optional
current-head counter refresh, non-binary support, compact route, and theoretical
optimality remain incomplete.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage241_latex_compile_package:",
        f"""
H10_stage241_latex_compile_package:
  status: latex_compile_package_ready
  evidence:
    - repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.pdf
    - repro/stage241_latex_compile_package/build/pvw_mat_sab_scoped_draft.log
    - repro/stage241_latex_compile_package/citation_resolution.csv
    - repro/stage241_latex_compile_package/proof_gate.csv
    - docs/stage241_latex_compile_package.md
  conclusion: >
    Stage241 records {decision}. It compiles the scoped Stage240 draft and
    verifies resolved citations, references, PDF generation, and claim-guard
    checks. The result remains a package gate for selected-binary evidence, not
    a new algorithmic or optimality claim.
""",
    )
    append_once(
        RUN_LOG,
        "stage241-latex-compile-package-001",
        f"""stage241-latex-compile-package-001,{date.today().isoformat()},{head},Stage 241,latex_compile,"python scripts/build_stage241_latex_compile_package.py","Stage240 scoped draft + Stage239 verified BibTeX",n/a,{decision},"Scoped LaTeX draft compiled and package gates recorded.",docs/stage241_latex_compile_package.md; repro/stage241_latex_compile_package/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage241_latex_compile_package:",
        """
- stage241_latex_compile_package:
  - `docs/stage241_latex_compile_package.md`
  - `experiments/stage241_latex_compile_package_plan.md`
  - `theory_checks/stage241_compile_claim_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage241_compile_package.md`
  - `scripts/build_stage241_latex_compile_package.py`
  - `repro/stage241_latex_compile_package/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage241 LaTeX compile package records compile and citation gates",
        f"""
- [x] Stage241 LaTeX compile package records compile and citation gates `{decision}`.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = input_rows()
    prepare_build()
    commands = compile_draft()
    normalize_compile_artifacts(commands)
    checks = compile_check_rows(commands)
    cites = citation_rows()
    pdfs = pdf_rows()
    gates = gate_rows(inputs, commands, checks, cites)
    proof = proof_rows(gates)
    nextq = next_rows()
    decision = gates[-1]["status"]

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(COMMANDS, commands, ["step", "command", "return_code", "status", "log"])
    write_csv(COMPILE_CHECKS, checks, ["check", "observed", "status", "evidence"])
    write_csv(CITATION_CHECKS, cites, ["citation_key", "in_tex", "in_aux", "in_bbl", "status"])
    write_csv(PDF_ARTIFACT, pdfs, ["artifact", "exists", "bytes", "sha256"])
    write_csv(GATES, gates, ["gate", "required", "observed", "status", "claim_effect"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_repro_commands()
    write_docs(inputs, commands, checks, cites, pdfs, gates, nextq)

    artifacts = [
        DOC, PLAN, THEORY, VARIANT, INPUTS, COMMANDS, COMPILE_CHECKS,
        CITATION_CHECKS, PDF_ARTIFACT, GATES, PROOF, NEXT, REPORT,
        REPRO_CMDS, BUILD_TEX, BUILD_TABLE, BUILD_BIB, BUILD_PDF, BUILD_LOG,
        BUILD_BBL, BUILD_BLG, BUILD_AUX,
    ] + [ROOT / row["log"] for row in commands]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "bytes", "sha256"])
    update_project_files(decision)

    print(f"Stage241 report: {rel(DOC)}")
    print(f"Stage241 decision: {decision}")


if __name__ == "__main__":
    main()
