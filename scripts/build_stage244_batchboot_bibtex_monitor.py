#!/usr/bin/env python3
"""Stage244: monitor official BatchBoot BibTeX availability."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import urllib.parse
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage244_batchboot_bibtex_monitor"

DOC = ROOT / "docs" / "stage244_batchboot_bibtex_monitor.md"
PLAN = ROOT / "experiments" / "stage244_batchboot_bibtex_monitor_plan.md"
THEORY = ROOT / "theory_checks" / "stage244_batchboot_citation_boundary.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage244_batchboot_monitor.md"

INPUTS = OUT / "input_status.csv"
PROBES = OUT / "source_probe.csv"
LINKS = OUT / "candidate_links.csv"
SUMMARY = OUT / "monitor_summary.csv"
REMAINING = OUT / "remaining_todo.csv"
GATES = OUT / "gate_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage244_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE242_REMAINING = ROOT / "repro" / "stage242_unresolved_bibtex_followup" / "remaining_unresolved_bibtex_todo.csv"
STAGE243_PROOF = ROOT / "repro" / "stage243_apply_lw_citations_recompile" / "proof_gate.csv"
STAGE243_TODO = ROOT / "repro" / "stage243_apply_lw_citations_recompile" / "todo_visibility.csv"

TITLE = "BatchBoot: Fast Batched Bootstrapping for TFHE scheme and Practical Applications"
USENIX_PAGE = "https://www.usenix.org/conference/usenixsecurity26/presentation/li-zhihao"
USENIX_PDF = "https://www.usenix.org/system/files/conference/usenixsecurity26/sec26_prepub_li-zhihao.pdf"
DBLP_SEARCH = "https://dblp.org/search/publ/api?format=json&q=" + urllib.parse.quote(TITLE)
CROSSREF_SEARCH = "https://api.crossref.org/works?rows=5&query.title=" + urllib.parse.quote(TITLE)

DECISION = "PASS_STAGE244_BATCHBOOT_MONITOR_RECORDED_NO_VERIFIED_BIBTEX"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[Tuple[str, str]] = []
        self._href = ""
        self._text: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self._href = ""
            self._text = []
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self._href = value

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = ""
            self._text = []


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


def fetch(url: str, accept: str = "text/html,application/json,application/pdf,*/*") -> Tuple[str, str, str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Codex Stage244 BatchBoot monitor", "Accept": accept})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            data = response.read(2 * 1024 * 1024)
            text = data.decode("utf-8", errors="replace")
            return text, str(getattr(response, "status", "")), response.geturl(), ""
    except Exception as exc:
        return "", "", url, type(exc).__name__ + ": " + str(exc)[:180]


def input_rows() -> List[Dict[str, str]]:
    paths = [
        (STAGE242_REMAINING, "Stage242 remaining BatchBoot TODO"),
        (STAGE243_PROOF, "Stage243 patched draft compile proof"),
        (STAGE243_TODO, "Stage243 TODO visibility proof"),
    ]
    return [
        {"input": rel(path), "status": "present" if path.exists() else "missing", "role": role, "bytes": str(path.stat().st_size) if path.exists() else ""}
        for path, role in paths
    ]


def page_link_rows(html: str) -> List[Dict[str, str]]:
    parser = LinkParser()
    parser.feed(html)
    rows = []
    for href, text in parser.links:
        haystack = (href + " " + text).lower()
        if any(token in haystack for token in ["bib", "citation", "cite", "ris", "endnote"]):
            rows.append({"source_id": "BATCHBOOT26", "href": href, "text": text, "classification": "candidate_citation_link"})
    return rows


def probe_rows() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, str]]:
    probes: List[Dict[str, str]] = []
    links: List[Dict[str, str]] = []
    summary = {
        "official_page_ok": "no",
        "official_pdf_ok": "no",
        "page_has_citation_meta": "no",
        "page_has_bibtex_entry": "no",
        "candidate_citation_links": "0",
        "dblp_hits": "0",
        "crossref_exact_hits": "0",
        "verified_bibtex_available": "no",
    }

    page, status, final_url, error = fetch(USENIX_PAGE)
    summary["official_page_ok"] = "yes" if status == "200" else "no"
    citation_meta = bool(re.search(r"citation_(title|author|publication_date|doi)", page, flags=re.I))
    bibtex_entry = bool(re.search(r"@\w+\s*\{", page))
    summary["page_has_citation_meta"] = "yes" if citation_meta else "no"
    summary["page_has_bibtex_entry"] = "yes" if bibtex_entry else "no"
    links = page_link_rows(page)
    summary["candidate_citation_links"] = str(len(links))
    probes.append({"route": "usenix_page", "url": USENIX_PAGE, "http_status": status, "final_url": final_url, "finding": f"citation_meta={citation_meta}; bibtex_entry={bibtex_entry}; candidate_links={len(links)}", "error": error})

    pdf, status, final_url, error = fetch(USENIX_PDF, "application/pdf,*/*")
    summary["official_pdf_ok"] = "yes" if status == "200" else "no"
    probes.append({"route": "usenix_pdf", "url": USENIX_PDF, "http_status": status, "final_url": final_url, "finding": f"bytes_or_text_head={len(pdf)}", "error": error})

    dblp, status, final_url, error = fetch(DBLP_SEARCH, "application/json,*/*")
    dblp_hits = "0"
    if dblp:
        try:
            data = json.loads(dblp)
            dblp_hits = str(data.get("result", {}).get("hits", {}).get("@total", "0"))
        except Exception as exc:
            dblp_hits = "parse_error:" + type(exc).__name__
    summary["dblp_hits"] = dblp_hits
    probes.append({"route": "dblp_title_search", "url": DBLP_SEARCH, "http_status": status, "final_url": final_url, "finding": "hits=" + dblp_hits, "error": error})

    crossref, status, final_url, error = fetch(CROSSREF_SEARCH, "application/json,*/*")
    exact_hits = "0"
    if crossref:
        try:
            data = json.loads(crossref)
            items = data.get("message", {}).get("items", [])
            exact = [item for item in items if TITLE.lower() in " ".join(item.get("title", [])).lower()]
            exact_hits = str(len(exact))
        except Exception as exc:
            exact_hits = "parse_error:" + type(exc).__name__
    summary["crossref_exact_hits"] = exact_hits
    probes.append({"route": "crossref_title_search", "url": CROSSREF_SEARCH, "http_status": status, "final_url": final_url, "finding": "exact_title_hits=" + exact_hits, "error": error})

    if bibtex_entry or int(dblp_hits or "0") > 0 or int(exact_hits or "0") > 0:
        summary["verified_bibtex_available"] = "candidate_needs_manual_verification"
    return probes, links, summary


def summary_rows(summary: Dict[str, str]) -> List[Dict[str, str]]:
    return [{"metric": key, "value": value, "interpretation": interpretation_for(key, value)} for key, value in summary.items()]


def interpretation_for(key: str, value: str) -> str:
    if key == "verified_bibtex_available":
        return "No accepted BibTeX entry is written unless this becomes yes through a verified source route."
    if key in {"official_page_ok", "official_pdf_ok"}:
        return "Official USENIX source is reachable." if value == "yes" else "Official route not reachable in this probe."
    return "Monitor signal only; not a bibliography entry."


def remaining_rows(summary: Dict[str, str]) -> List[Dict[str, str]]:
    return [
        {
            "source_id": "BATCHBOOT26",
            "title": TITLE,
            "todo_status": "TODO_OFFICIAL_BIBTEX_NOT_AVAILABLE" if summary["verified_bibtex_available"] == "no" else "TODO_CANDIDATE_NEEDS_MANUAL_VERIFICATION",
            "needed_action": "Wait for official USENIX/DBLP/Crossref BibTeX route; do not generate from memory.",
            "route_attempted": "usenix_page;usenix_pdf;dblp_title_search;crossref_title_search",
            "route_url": USENIX_PAGE,
        }
    ]


def gate_rows(inputs: List[Dict[str, str]], summary: Dict[str, str]) -> List[Dict[str, str]]:
    input_ok = all(row["status"] == "present" for row in inputs)
    official_ok = summary["official_page_ok"] == "yes" and summary["official_pdf_ok"] == "yes"
    no_bib = summary["verified_bibtex_available"] == "no"
    return [
        {"gate": "G1_inputs", "required": "Stage242 remaining TODO and Stage243 compile proof exist", "observed": "all present" if input_ok else "missing input", "status": "PASS" if input_ok else "FAIL", "claim_effect": "monitor starts from current paper package state"},
        {"gate": "G2_official_routes_reachable", "required": "USENIX page and PDF are reachable for monitoring", "observed": f"page={summary['official_page_ok']}; pdf={summary['official_pdf_ok']}", "status": "PASS" if official_ok else "WARN_ROUTE_UNREACHABLE", "claim_effect": "external source was checked at current date"},
        {"gate": "G3_no_verified_bibtex", "required": "do not write a BatchBoot BibTeX entry unless verified source exists", "observed": f"available={summary['verified_bibtex_available']}; dblp_hits={summary['dblp_hits']}; crossref_exact_hits={summary['crossref_exact_hits']}", "status": "PASS_TODO_RETAINED" if no_bib else "REVIEW_CANDIDATE_ROUTE", "claim_effect": "prevents fabricated BatchBoot citation"},
        {"gate": "G4_stage244_decision", "required": "monitor recorded and TODO state explicit", "observed": DECISION, "status": DECISION, "claim_effect": "proceed to optional counter or broader algorithm gates; final bibliography still has BatchBoot TODO"},
    ]


def proof_rows(gates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [{"gate": row["gate"], "status": row["status"], "metric": row["required"], "value": row["observed"], "evidence": rel(GATES), "interpretation": row["claim_effect"]} for row in gates]


def next_rows() -> List[Dict[str, str]]:
    return [
        {"priority": "P0", "route": "stage245_native_counter_refresh_if_code_changes", "entry_condition": "Final implementation section needs current-head counter wording.", "gate": "Native Linux perf counters or explicit reuse of Stage226 with code-change audit.", "status": "selected_optional", "failure_action": "Keep counter evidence out of the main claim.", "evidence": "repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv"},
        {"priority": "P1", "route": "stage246_nonbinary_or_compact_algorithm_gate", "entry_condition": "A broader algorithmic claim is proposed.", "gate": "Closed equations, correctness/noise proof obligations, full-SAB A/B and resource matrix.", "status": "blocked_until_new_design", "failure_action": "Do not extend selected binary claim.", "evidence": "repro/stage240_scoped_latex_draft/claim_audit.csv"},
        {"priority": "P2", "route": "stage247_batchboot_monitor_rerun", "entry_condition": "Before final submission or after USENIX metadata changes.", "gate": "Official source route only; no generated BibTeX.", "status": "future_monitor", "failure_action": "Leave BatchBoot TODO.", "evidence": rel(REMAINING)},
    ]


def artifact_rows(paths: List[Path]) -> List[Dict[str, str]]:
    return [{"artifact": rel(path), "bytes": str(path.stat().st_size) if path.exists() else "", "sha256": sha256(path) if path.exists() else ""} for path in paths]


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._\n"
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|").replace("\n", "<br>") for field in fields) + " |")
    return "\n".join(out) + "\n"


def write_repro_commands() -> None:
    write_text(REPRO_CMDS, f"""# Stage244 Reproduction Commands

```bash
python scripts/build_stage244_batchboot_bibtex_monitor.py
```

Decision: `{DECISION}`.
Input head: `{git_head()}`.
""")


def write_docs(inputs: List[Dict[str, str]], probes: List[Dict[str, str]], links: List[Dict[str, str]], summary: List[Dict[str, str]], remaining: List[Dict[str, str]], gates: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> None:
    write_text(DOC, f"""# Stage244 BatchBoot BibTeX Monitor

Decision: `{DECISION}`.

Stage244 reprobes official and bibliographic routes for BatchBoot. No verified
BibTeX route is currently available, so the scoped draft must keep BatchBoot as
a TODO and must not generate a bibliography entry from memory.

## Source Probes

{table(probes, ["route", "url", "http_status", "final_url", "finding", "error"])}

## Candidate Links

{table(links, ["source_id", "href", "text", "classification"])}

## Summary

{table(summary, ["metric", "value", "interpretation"])}

## Remaining TODO

{table(remaining, ["source_id", "title", "todo_status", "needed_action", "route_attempted", "route_url"])}

## Gates

{table(gates, ["gate", "required", "observed", "status", "claim_effect"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

## Inputs

{table(inputs, ["input", "status", "role", "bytes"])}
""")
    write_text(REPORT, f"""# Stage244 Report

Decision: `{DECISION}`.

USENIX page and PDF were probed, alongside DBLP and Crossref title searches.
No verified BibTeX entry was accepted. `BATCHBOOT26` remains an explicit TODO.
""")
    write_text(PLAN, """# Stage244 BatchBoot BibTeX Monitor Plan

Goal: recheck official BatchBoot BibTeX availability without fabricating a
reference.

Gate: only USENIX, DBLP, or Crossref verified metadata may introduce a
BatchBoot bibliography entry. Otherwise the TODO remains visible.
""")
    write_text(THEORY, """# Stage244 BatchBoot Citation Boundary

Stage244 is a source-monitor gate. It does not affect PVW/MAT-SAB algorithm
claims, performance claims, or novelty boundaries.
""")
    write_text(VARIANT, """# mat_rlwe_sab_stage244_batchboot_monitor

This is not an algorithm variant. It records that BatchBoot still lacks a
verified BibTeX route in the monitored sources.
""")


def update_project_files(decision: str) -> None:
    head = git_head()
    append_once(ROADMAP, "## Stage 244: BatchBoot BibTeX Monitor", f"""
## Stage 244: BatchBoot BibTeX Monitor

Goal:

```text
Reprobe official BatchBoot citation routes and preserve no-hallucination
bibliography policy.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. No verified BatchBoot
BibTeX export was found through USENIX, DBLP, or Crossref probes. BatchBoot
remains an explicit TODO.
```
""")
    append_once(GOAL, "Stage244 BatchBoot BibTeX monitor", f"""
- Stage244 BatchBoot BibTeX monitor records `{decision}`: external sources were
  rechecked and BatchBoot remains a TODO, with no fabricated bibliography
  entry.
""")
    append_once(CURRENT_GOAL, "### Stage244 BatchBoot BibTeX monitor", f"""
### Stage244 BatchBoot BibTeX monitor

`{decision}` records a current external-source monitor for BatchBoot. The active
goal remains open because optional current-head counter refresh, non-binary
support, compact route, theoretical optimality, and final BatchBoot citation
closure remain incomplete.
""")
    append_once(HYPOTHESES, "H10_stage244_batchboot_bibtex_monitor:", f"""
H10_stage244_batchboot_bibtex_monitor:
  status: batchboot_monitor_recorded_no_verified_bibtex
  evidence:
    - repro/stage244_batchboot_bibtex_monitor/source_probe.csv
    - repro/stage244_batchboot_bibtex_monitor/monitor_summary.csv
    - repro/stage244_batchboot_bibtex_monitor/remaining_todo.csv
    - docs/stage244_batchboot_bibtex_monitor.md
  conclusion: >
    Stage244 records {decision}. It reprobes USENIX, DBLP, and Crossref routes
    for BatchBoot and keeps the source as a TODO because no verified BibTeX
    entry is available. No bibliography entry was generated from memory.
""")
    append_once(RUN_LOG, "stage244-batchboot-bibtex-monitor-001", f"""stage244-batchboot-bibtex-monitor-001,{date.today().isoformat()},{head},Stage 244,network_monitor,"python scripts/build_stage244_batchboot_bibtex_monitor.py","BatchBoot official/DBLP/Crossref probes",n/a,{decision},"BatchBoot remains TODO; no verified BibTeX route found.",docs/stage244_batchboot_bibtex_monitor.md; repro/stage244_batchboot_bibtex_monitor/proof_gate.csv
""")
    append_once(MANIFEST, "- stage244_batchboot_bibtex_monitor:", """
- stage244_batchboot_bibtex_monitor:
  - `docs/stage244_batchboot_bibtex_monitor.md`
  - `experiments/stage244_batchboot_bibtex_monitor_plan.md`
  - `theory_checks/stage244_batchboot_citation_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage244_batchboot_monitor.md`
  - `scripts/build_stage244_batchboot_bibtex_monitor.py`
  - `repro/stage244_batchboot_bibtex_monitor/`
""")
    append_once(CHECKLIST, "Stage244 BatchBoot BibTeX monitor records no verified BibTeX route", f"""
- [x] Stage244 BatchBoot BibTeX monitor records no verified BibTeX route `{decision}`.
""")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = input_rows()
    probes, links, raw_summary = probe_rows()
    summary = summary_rows(raw_summary)
    remaining = remaining_rows(raw_summary)
    gates = gate_rows(inputs, raw_summary)
    proof = proof_rows(gates)
    nextq = next_rows()

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(PROBES, probes, ["route", "url", "http_status", "final_url", "finding", "error"])
    write_csv(LINKS, links, ["source_id", "href", "text", "classification"])
    write_csv(SUMMARY, summary, ["metric", "value", "interpretation"])
    write_csv(REMAINING, remaining, ["source_id", "title", "todo_status", "needed_action", "route_attempted", "route_url"])
    write_csv(GATES, gates, ["gate", "required", "observed", "status", "claim_effect"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_repro_commands()
    write_docs(inputs, probes, links, summary, remaining, gates, nextq)
    artifacts = [DOC, PLAN, THEORY, VARIANT, INPUTS, PROBES, LINKS, SUMMARY, REMAINING, GATES, PROOF, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "bytes", "sha256"])
    update_project_files(gates[-1]["status"])
    print(f"Stage244 report: {rel(DOC)}")
    print(f"Stage244 decision: {gates[-1]['status']}")


if __name__ == "__main__":
    main()
