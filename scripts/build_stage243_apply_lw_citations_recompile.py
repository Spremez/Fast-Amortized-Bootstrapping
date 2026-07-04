#!/usr/bin/env python3
"""Stage243: apply verified LW23A/LW23B citations and recompile the draft."""

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
OUT = ROOT / "repro" / "stage243_apply_lw_citations_recompile"
BUILD = OUT / "build"

DOC = ROOT / "docs" / "stage243_apply_lw_citations_recompile.md"
PLAN = ROOT / "experiments" / "stage243_apply_lw_citations_recompile_plan.md"
THEORY = ROOT / "theory_checks" / "stage243_draft_patch_claim_boundary.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage243_draft_patch.md"

INPUTS = OUT / "input_status.csv"
PATCH_AUDIT = OUT / "draft_patch_audit.csv"
COMMANDS = OUT / "command_log.csv"
COMPILE_CHECKS = OUT / "compile_checks.csv"
CITATION_CHECKS = OUT / "citation_resolution.csv"
TODO_AUDIT = OUT / "todo_visibility.csv"
PDF_ARTIFACT = OUT / "pdf_artifact.csv"
GATES = OUT / "gate_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage243_report.md"
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
STAGE240_PROOF = STAGE240 / "proof_gate.csv"
STAGE241_PROOF = ROOT / "repro" / "stage241_latex_compile_package" / "proof_gate.csv"
STAGE242 = ROOT / "repro" / "stage242_unresolved_bibtex_followup"
STAGE242_KEYMAP = STAGE242 / "updated_citation_key_map.csv"
STAGE242_REMAINING = STAGE242 / "remaining_unresolved_bibtex_todo.csv"
STAGE242_BIB = STAGE242 / "merged_references_stage242.bib"
STAGE242_PROOF = STAGE242 / "proof_gate.csv"

BUILD_TEX = BUILD / "pvw_mat_sab_scoped_draft.tex"
BUILD_TABLE = BUILD / "selected_binary_table.tex"
BUILD_BIB = BUILD / "pvw_mat_sab_references.bib"
BUILD_PDF = BUILD / "pvw_mat_sab_scoped_draft.pdf"
BUILD_LOG = BUILD / "pvw_mat_sab_scoped_draft.log"
BUILD_AUX = BUILD / "pvw_mat_sab_scoped_draft.aux"
BUILD_BBL = BUILD / "pvw_mat_sab_scoped_draft.bbl"
BUILD_BLG = BUILD / "pvw_mat_sab_scoped_draft.blg"

DECISION = "PASS_STAGE243_LW_CITATIONS_APPLIED_RECOMPILED_BATCHBOOT_TODO"


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
        (STAGE240_TEX, "Stage240 scoped draft source"),
        (STAGE240_TABLE, "Stage240 selected binary table"),
        (STAGE240_PROOF, "Stage240 claim/citation gates"),
        (STAGE241_PROOF, "Stage241 compile proof gates"),
        (STAGE242_KEYMAP, "Stage242 updated citation keymap"),
        (STAGE242_REMAINING, "Stage242 remaining TODOs"),
        (STAGE242_BIB, "Stage242 merged verified references"),
        (STAGE242_PROOF, "Stage242 BibTeX follow-up proof gates"),
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


def patched_tex() -> str:
    text = read_text(STAGE240_TEX)
    old = """are established related work \\cite{DBLP:conf/icalp/MicciancoS18}, \\cite{DBLP:conf/asiacrypt/GuimaraesPL23},
\\cite{DBLP:conf/pkc/MicheliKMS24}, \\cite{DBLP:conf/asiacrypt/LiuW23}.

% CITATION TODO [BATCHBOOT26]: no_hits
% CITATION TODO [LW23A_B]: Stage230 source row combines Batch Bootstrapping I and II; split into two verified BibTeX entries before LaTeX.
"""
    new = """are established related work \\cite{DBLP:conf/icalp/MicciancoS18}, \\cite{DBLP:conf/asiacrypt/GuimaraesPL23},
\\cite{DBLP:conf/pkc/MicheliKMS24}, \\cite{DBLP:conf/asiacrypt/LiuW23},
\\cite{DBLP:conf/eurocrypt/LiuW23}, and \\cite{DBLP:conf/eurocrypt/LiuW23a}.

% CITATION TODO [BATCHBOOT26]: Official USENIX page/PDF are accessible and DBLP search was probed, but no verified BibTeX export was found.
"""
    if old not in text:
        raise RuntimeError("Stage240 related-work TODO block did not match expected text.")
    return text.replace(old, new)


def compile_safe_bibtex() -> str:
    text = read_text(STAGE242_BIB)
    # DBLP's LW23B title contains O{\~}(1), which BibTeX passes through in a
    # form that pdfLaTeX rejects. This keeps the same O-tilde notation in the
    # build-local bibliography without changing the verified Stage242 source.
    return text.replace(r"O{\~}(1)", r"{\~{O}}(1)")


def prepare_build() -> None:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True, exist_ok=True)
    write_text(BUILD_TEX, patched_tex())
    shutil.copyfile(STAGE240_TABLE, BUILD_TABLE)
    write_text(BUILD_BIB, compile_safe_bibtex())


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
        rc = completed.returncode
        status = "PASS" if rc == 0 else "FAIL"
    except FileNotFoundError as exc:
        output = f"{type(exc).__name__}: {exc}"
        rc = 127
        status = "FAIL_TOOL_MISSING"
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + "\nTIMEOUT"
        rc = 124
        status = "FAIL_TIMEOUT"
    write_text(log_path, output)
    return {"step": step, "command": " ".join(command), "return_code": str(rc), "status": status, "log": rel(log_path)}


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


def patch_audit_rows() -> List[Dict[str, str]]:
    tex = read_text(BUILD_TEX)
    bib = read_text(BUILD_BIB)
    return [
        {
            "check": "lw23a_cite_present",
            "observed": "DBLP:conf/eurocrypt/LiuW23" if "DBLP:conf/eurocrypt/LiuW23" in tex else "",
            "status": "PASS" if "DBLP:conf/eurocrypt/LiuW23" in tex else "FAIL",
            "evidence": rel(BUILD_TEX),
        },
        {
            "check": "lw23b_cite_present",
            "observed": "DBLP:conf/eurocrypt/LiuW23a" if "DBLP:conf/eurocrypt/LiuW23a" in tex else "",
            "status": "PASS" if "DBLP:conf/eurocrypt/LiuW23a" in tex else "FAIL",
            "evidence": rel(BUILD_TEX),
        },
        {
            "check": "old_composite_todo_removed",
            "observed": "LW23A_B" if "LW23A_B" in tex else "",
            "status": "PASS" if "LW23A_B" not in tex else "FAIL",
            "evidence": rel(BUILD_TEX),
        },
        {
            "check": "batchboot_todo_retained",
            "observed": "BATCHBOOT26" if "BATCHBOOT26" in tex else "",
            "status": "PASS" if "BATCHBOOT26" in tex else "FAIL",
            "evidence": rel(BUILD_TEX),
        },
        {
            "check": "lw23b_otilde_compile_safe",
            "observed": r"{\~{O}}(1)" if r"{\~{O}}(1)" in bib else "",
            "status": "PASS" if r"{\~{O}}(1)" in bib and r"O{\~}(1)" not in bib else "FAIL",
            "evidence": rel(BUILD_BIB),
        },
    ]


def compile_check_rows(commands: List[Dict[str, str]]) -> List[Dict[str, str]]:
    final_log = read_text(BUILD_LOG)
    pdf_ok = BUILD_PDF.exists() and BUILD_PDF.stat().st_size > 0
    undefined_citations = sorted(set(re.findall(r"Citation `([^']+)' .* undefined", final_log)))
    undefined_refs = sorted(set(re.findall(r"Reference `([^']+)' .* undefined", final_log)))
    fatal = "Fatal error" in final_log or "Emergency stop" in final_log or "! " in final_log
    bbl_items = len(re.findall(r"\\bibitem\{", read_text(BUILD_BBL)))
    source_keys = set(source_cite_keys(read_text(BUILD_TEX)))
    return [
        {"check": "all_commands_return_zero", "observed": ";".join(row["step"] + "=" + row["return_code"] for row in commands), "status": "PASS" if all(row["return_code"] == "0" for row in commands) else "FAIL", "evidence": rel(COMMANDS)},
        {"check": "pdf_exists", "observed": f"exists={pdf_ok}; bytes={BUILD_PDF.stat().st_size if BUILD_PDF.exists() else 0}", "status": "PASS" if pdf_ok else "FAIL", "evidence": rel(BUILD_PDF)},
        {"check": "no_undefined_citations", "observed": ",".join(undefined_citations), "status": "PASS" if not undefined_citations else "FAIL", "evidence": rel(BUILD_LOG)},
        {"check": "no_undefined_references", "observed": ",".join(undefined_refs), "status": "PASS" if not undefined_refs else "FAIL", "evidence": rel(BUILD_LOG)},
        {"check": "no_fatal_latex_error", "observed": f"fatal={fatal}", "status": "PASS" if not fatal else "FAIL", "evidence": rel(BUILD_LOG)},
        {"check": "bbl_matches_cite_count", "observed": f"cite_keys={len(source_keys)}; bibitems={bbl_items}", "status": "PASS" if bbl_items == len(source_keys) and bbl_items == 11 else "FAIL", "evidence": rel(BUILD_BBL)},
        {"check": "overclaim_guard", "observed": "hits=" + ",".join(positive_forbidden_hits(read_text(BUILD_TEX))), "status": "PASS" if not positive_forbidden_hits(read_text(BUILD_TEX)) else "FAIL", "evidence": rel(BUILD_TEX)},
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


def todo_rows() -> List[Dict[str, str]]:
    tex = read_text(BUILD_TEX)
    return [
        {
            "todo_id": "BATCHBOOT26",
            "visible_in_tex": "yes" if "BATCHBOOT26" in tex else "no",
            "has_cite_key": "yes" if "TODO_BatchBoot" in tex or "\\cite{BATCHBOOT" in tex else "no",
            "status": "PASS" if "BATCHBOOT26" in tex and "\\cite{BATCHBOOT" not in tex else "FAIL",
            "evidence": rel(BUILD_TEX),
        },
        {
            "todo_id": "LW23A_B",
            "visible_in_tex": "yes" if "LW23A_B" in tex else "no",
            "has_cite_key": "n/a",
            "status": "PASS" if "LW23A_B" not in tex else "FAIL",
            "evidence": rel(BUILD_TEX),
        },
    ]


def pdf_rows() -> List[Dict[str, str]]:
    paths = [BUILD_PDF, BUILD_LOG, BUILD_BBL, BUILD_BLG, BUILD_AUX, BUILD_TEX, BUILD_BIB, BUILD_TABLE]
    return [
        {
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "bytes": str(path.stat().st_size) if path.exists() else "0",
            "sha256": sha256(path) if path.exists() else "",
        }
        for path in paths
    ]


def gate_rows(inputs: List[Dict[str, str]], patch: List[Dict[str, str]], commands: List[Dict[str, str]], checks: List[Dict[str, str]], cites: List[Dict[str, str]], todos: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows = [
        {"gate": "G1_inputs", "required": "Stage240/241/242 source, proof, keymap, merged BibTeX exist", "observed": "all present" if all(row["status"] == "present" for row in inputs) else "missing input", "status": "PASS" if all(row["status"] == "present" for row in inputs) else "FAIL", "claim_effect": "draft patch starts from verified prior-stage artifacts"},
        {"gate": "G2_patch_applied", "required": "LW23A/LW23B citations present, LW23A_B TODO removed, BatchBoot TODO retained", "observed": ";".join(row["check"] + "=" + row["status"] for row in patch), "status": "PASS" if all(row["status"] == "PASS" for row in patch) else "FAIL", "claim_effect": "verified Batch Bootstrapping I/II citations replace composite TODO"},
        {"gate": "G3_compile_chain", "required": "pdflatex, bibtex, pdflatex, pdflatex all return zero", "observed": ";".join(row["step"] + "=" + row["return_code"] for row in commands), "status": "PASS" if all(row["return_code"] == "0" for row in commands) else "FAIL", "claim_effect": "patched draft is mechanically buildable"},
        {"gate": "G4_compile_checks", "required": "PDF exists; no undefined cites/refs/fatal errors; bbl count is 11", "observed": ";".join(row["check"] + "=" + row["status"] for row in checks), "status": "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL", "claim_effect": "patched PDF has resolved bibliography and table references"},
        {"gate": "G5_citation_resolution", "required": "all 11 cite keys appear in aux and bbl", "observed": f"citation_rows={len(cites)}", "status": "PASS" if len(cites) == 11 and all(row["status"] == "PASS" for row in cites) else "FAIL", "claim_effect": "LW23A/LW23B are fully compiled citations"},
        {"gate": "G6_todo_boundary", "required": "BatchBoot remains visible TODO, not bibliography entry; LW23A_B TODO removed", "observed": ";".join(row["todo_id"] + "=" + row["status"] for row in todos), "status": "PASS" if all(row["status"] == "PASS" for row in todos) else "FAIL", "claim_effect": "prevents fabricated BatchBoot citation while removing resolved composite TODO"},
    ]
    decision = DECISION if all(not row["status"].startswith("FAIL") for row in rows) else "FAIL_STAGE243_PATCH_RECOMPILE"
    rows.append({"gate": "G7_stage243_decision", "required": "all patch/recompile/citation gates pass", "observed": decision, "status": decision, "claim_effect": "scoped draft updated and recompiled; final bibliography closure still waits for BatchBoot official BibTeX"})
    return rows


def proof_rows(gates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [{"gate": row["gate"], "status": row["status"], "metric": row["required"], "value": row["observed"], "evidence": rel(GATES), "interpretation": row["claim_effect"]} for row in gates]


def next_rows() -> List[Dict[str, str]]:
    return [
        {"priority": "P0", "route": "stage244_batchboot_official_bibtex_monitor", "entry_condition": "Final bibliography closure requires BatchBoot entry.", "gate": "Use official USENIX/DBLP/Crossref route only; no generated BibTeX.", "status": "blocked_until_source_available", "failure_action": "Leave BatchBoot as TODO and do not submit final paper.", "evidence": rel(STAGE242_REMAINING)},
        {"priority": "P1", "route": "stage245_native_counter_refresh_if_code_changes", "entry_condition": "Final implementation section needs current-head counter wording.", "gate": "Native Linux perf counters or explicit reuse of Stage226 with code-change audit.", "status": "optional", "failure_action": "Keep counter evidence out of the main claim.", "evidence": "repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv"},
        {"priority": "P2", "route": "stage246_nonbinary_or_compact_algorithm_gate", "entry_condition": "A broader algorithmic claim is proposed.", "gate": "Closed equations, correctness/noise proof obligations, full-SAB A/B and resource matrix.", "status": "blocked_until_new_design", "failure_action": "Do not extend selected binary claim.", "evidence": "repro/stage240_scoped_latex_draft/claim_audit.csv"},
    ]


def artifact_rows(paths: List[Path]) -> List[Dict[str, str]]:
    return [{"artifact": rel(path), "bytes": str(path.stat().st_size) if path.exists() else "", "sha256": sha256(path) if path.exists() else ""} for path in paths]


def write_repro_commands() -> None:
    write_text(REPRO_CMDS, f"""# Stage243 Reproduction Commands

```bash
python scripts/build_stage243_apply_lw_citations_recompile.py
```

Decision: `{DECISION}`.
Input head: `{git_head()}`.
""")


def write_docs(inputs: List[Dict[str, str]], patch: List[Dict[str, str]], commands: List[Dict[str, str]], checks: List[Dict[str, str]], cites: List[Dict[str, str]], todos: List[Dict[str, str]], pdfs: List[Dict[str, str]], gates: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> None:
    write_text(DOC, f"""# Stage243 Apply LW Citations and Recompile

Decision: `{gates[-1]["status"]}`.

Stage243 applies the verified `LW23A` and `LW23B` citations from Stage242 to the
scoped draft, keeps `BATCHBOOT26` as a visible TODO, and reruns the full
LaTeX/BibTeX compile gate. This is a paper-evidence update only.

## Patch Audit

{table(patch, ["check", "observed", "status", "evidence"])}

## Commands

{table(commands, ["step", "command", "return_code", "status", "log"])}

## Compile Checks

{table(checks, ["check", "observed", "status", "evidence"])}

## Citation Resolution

{table(cites, ["citation_key", "in_tex", "in_aux", "in_bbl", "status"])}

## TODO Boundary

{table(todos, ["todo_id", "visible_in_tex", "has_cite_key", "status", "evidence"])}

## PDF Artifacts

{table(pdfs, ["artifact", "exists", "bytes", "sha256"])}

## Gates

{table(gates, ["gate", "required", "observed", "status", "claim_effect"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

## Inputs

{table(inputs, ["input", "status", "role", "bytes"])}
""")
    write_text(REPORT, f"""# Stage243 Report

Decision: `{gates[-1]["status"]}`.

The patched compiled PDF is `{rel(BUILD_PDF)}`. Citation count is 11, including
`DBLP:conf/eurocrypt/LiuW23` and `DBLP:conf/eurocrypt/LiuW23a`. `BATCHBOOT26`
remains a TODO and is not included as a bibliography entry.
""")
    write_text(PLAN, """# Stage243 Apply LW Citations and Recompile Plan

Goal: replace the resolved composite Batch Bootstrapping TODO with the two
verified DBLP citations and recompile the scoped draft.

Gates: cite count increases to 11, all citations resolve through BibTeX, the
old `LW23A_B` TODO disappears, `BATCHBOOT26` remains visible as TODO, and no
algorithmic claim boundary is expanded.
""")
    write_text(THEORY, """# Stage243 Draft Patch Claim Boundary

Stage243 does not change the PVW/MAT-SAB algorithm or its measured claims. It
only makes related-work citation support more precise by replacing a composite
TODO with two verified bibliography entries.
""")
    write_text(VARIANT, """# mat_rlwe_sab_stage243_draft_patch

This is not an algorithm variant. It is a patched and recompiled draft package
that applies verified Batch Bootstrapping I/II citations while preserving the
selected-binary claim boundary.
""")


def update_project_files(decision: str) -> None:
    head = git_head()
    append_once(ROADMAP, "## Stage 243: Apply LW Citations and Recompile", f"""
## Stage 243: Apply LW Citations and Recompile

Goal:

```text
Patch the scoped draft with verified LW23A/LW23B citations and rerun compile
gates while keeping BatchBoot as TODO.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. The scoped draft now
compiles with 11 resolved citation keys, including Batch Bootstrapping I/II.
`BATCHBOOT26` remains a visible TODO until official BibTeX is available.
```
""")
    append_once(GOAL, "Stage243 apply LW citations and recompile", f"""
- Stage243 apply-LW-citations/recompile records `{decision}`: the scoped draft
  now cites Batch Bootstrapping I/II as separate verified entries and still
  keeps BatchBoot out of the bibliography.
""")
    append_once(CURRENT_GOAL, "### Stage243 apply LW citations and recompile", f"""
### Stage243 apply LW citations and recompile

`{decision}` records a patched, recompiled scoped draft with 11 resolved
citations. The active goal remains open because BatchBoot final citation
closure, optional current-head counter refresh, non-binary support, compact
route, and theoretical optimality remain incomplete.
""")
    append_once(HYPOTHESES, "H10_stage243_apply_lw_citations_recompile:", f"""
H10_stage243_apply_lw_citations_recompile:
  status: lw_citations_applied_recompiled_batchboot_todo
  evidence:
    - repro/stage243_apply_lw_citations_recompile/build/pvw_mat_sab_scoped_draft.pdf
    - repro/stage243_apply_lw_citations_recompile/citation_resolution.csv
    - repro/stage243_apply_lw_citations_recompile/todo_visibility.csv
    - repro/stage243_apply_lw_citations_recompile/proof_gate.csv
    - docs/stage243_apply_lw_citations_recompile.md
  conclusion: >
    Stage243 records {decision}. It applies verified LW23A/LW23B citations,
    recompiles the scoped draft with 11 resolved bibliography entries, and
    leaves BATCHBOOT26 as a visible TODO. No algorithmic claim is expanded.
""")
    append_once(RUN_LOG, "stage243-apply-lw-citations-recompile-001", f"""stage243-apply-lw-citations-recompile-001,{date.today().isoformat()},{head},Stage 243,latex_compile,"python scripts/build_stage243_apply_lw_citations_recompile.py","Stage240 draft + Stage242 merged BibTeX",n/a,{decision},"Applied verified LW23A/LW23B citations and recompiled scoped draft.",docs/stage243_apply_lw_citations_recompile.md; repro/stage243_apply_lw_citations_recompile/proof_gate.csv
""")
    append_once(MANIFEST, "- stage243_apply_lw_citations_recompile:", """
- stage243_apply_lw_citations_recompile:
  - `docs/stage243_apply_lw_citations_recompile.md`
  - `experiments/stage243_apply_lw_citations_recompile_plan.md`
  - `theory_checks/stage243_draft_patch_claim_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage243_draft_patch.md`
  - `scripts/build_stage243_apply_lw_citations_recompile.py`
  - `repro/stage243_apply_lw_citations_recompile/`
""")
    append_once(CHECKLIST, "Stage243 apply LW citations and recompile records 11-citation compile gates", f"""
- [x] Stage243 apply LW citations and recompile records 11-citation compile gates `{decision}`.
""")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = input_rows()
    prepare_build()
    commands = compile_draft()
    normalize_compile_artifacts(commands)
    patch = patch_audit_rows()
    checks = compile_check_rows(commands)
    cites = citation_rows()
    todos = todo_rows()
    pdfs = pdf_rows()
    gates = gate_rows(inputs, patch, commands, checks, cites, todos)
    proof = proof_rows(gates)
    nextq = next_rows()
    decision = gates[-1]["status"]

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(PATCH_AUDIT, patch, ["check", "observed", "status", "evidence"])
    write_csv(COMMANDS, commands, ["step", "command", "return_code", "status", "log"])
    write_csv(COMPILE_CHECKS, checks, ["check", "observed", "status", "evidence"])
    write_csv(CITATION_CHECKS, cites, ["citation_key", "in_tex", "in_aux", "in_bbl", "status"])
    write_csv(TODO_AUDIT, todos, ["todo_id", "visible_in_tex", "has_cite_key", "status", "evidence"])
    write_csv(PDF_ARTIFACT, pdfs, ["artifact", "exists", "bytes", "sha256"])
    write_csv(GATES, gates, ["gate", "required", "observed", "status", "claim_effect"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_repro_commands()
    write_docs(inputs, patch, commands, checks, cites, todos, pdfs, gates, nextq)

    artifacts = [
        DOC, PLAN, THEORY, VARIANT, INPUTS, PATCH_AUDIT, COMMANDS,
        COMPILE_CHECKS, CITATION_CHECKS, TODO_AUDIT, PDF_ARTIFACT, GATES,
        PROOF, NEXT, REPORT, REPRO_CMDS, BUILD_TEX, BUILD_TABLE, BUILD_BIB,
        BUILD_PDF, BUILD_LOG, BUILD_BBL, BUILD_BLG, BUILD_AUX,
    ] + [ROOT / row["log"] for row in commands]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "bytes", "sha256"])
    update_project_files(decision)

    print(f"Stage243 report: {rel(DOC)}")
    print(f"Stage243 decision: {decision}")


if __name__ == "__main__":
    main()
