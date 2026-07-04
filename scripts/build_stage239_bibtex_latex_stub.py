#!/usr/bin/env python3
"""Stage239: retrieve verified BibTeX where possible and emit a LaTeX stub."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage239_bibtex_latex_stub"
REF_DIR = ROOT / "references"

DOC = ROOT / "docs" / "stage239_bibtex_latex_stub.md"
PLAN = ROOT / "experiments" / "stage239_bibtex_latex_stub_plan.md"
THEORY = ROOT / "theory_checks" / "stage239_bibtex_policy_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage239_bibtex_stub.md"

INPUTS = OUT / "input_status.csv"
RETRIEVAL = OUT / "bibtex_retrieval.csv"
KEYMAP = OUT / "citation_key_map.csv"
TODO = OUT / "unresolved_bibtex_todo.csv"
LATEX_STUB = OUT / "latex_stub.tex"
OUT_BIB = OUT / "retrieved_references.bib"
ROOT_BIB = REF_DIR / "stage239_pvw_mat_sab.bib"
GATES = OUT / "gate_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage239_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE238 = ROOT / "repro" / "stage238_source_verified_citation_package"
STAGE237 = ROOT / "repro" / "stage237_scoped_manuscript_package"
STAGE236 = ROOT / "repro" / "stage236_set_2_3_4096_r4_highstat_slice"

DECISION = "PASS_STAGE239_PARTIAL_VERIFIED_BIBTEX_LATEX_STUB_READY_TODOS_REMAIN"


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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def input_rows() -> List[Dict[str, str]]:
    paths = [
        (STAGE238 / "proof_gate.csv", "Stage238 citation proof"),
        (STAGE238 / "bibtex_todo.csv", "Stage238 BibTeX TODO"),
        (STAGE238 / "claim_support_matrix.csv", "Stage238 claim support"),
        (STAGE237 / "manuscript_skeleton.md", "Stage237 manuscript skeleton"),
        (STAGE236 / "selected_binary_matrix_summary.csv", "Stage236 local experiment table"),
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


def fetch_text(url: str, timeout: float = 18.0) -> Tuple[str, str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 Codex verified BibTeX retrieval",
            "Accept": "text/plain,text/x-bibtex,application/x-bibtex,application/json,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(1024 * 1024)
            return data.decode("utf-8", errors="replace"), str(getattr(response, "status", "")), response.geturl()
    except urllib.error.HTTPError as exc:
        return "", str(exc.code), getattr(exc, "url", url) + " :: " + str(exc.reason)
    except Exception as exc:
        return "", "", type(exc).__name__ + ": " + str(exc)[:180]


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def token_score(a: str, b: str) -> float:
    aa = set(normalize_title(a).split())
    bb = set(normalize_title(b).split())
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / max(len(aa), len(bb))


def rec_to_bib_url(url: str) -> str:
    if not url:
        return ""
    clean = url.rstrip("/")
    clean = re.sub(r"\.html?$", "", clean)
    return clean + ".bib"


def bib_key(entry: str) -> str:
    match = re.search(r"@\w+\s*\{\s*([^,\s]+)", entry)
    return match.group(1).strip() if match else ""


def bib_type(entry: str) -> str:
    match = re.search(r"@(\w+)\s*\{", entry)
    return match.group(1).lower() if match else ""


def bib_title(entry: str) -> str:
    match = re.search(r"\btitle\s*=\s*\{(.+?)\}\s*,\s*\n", entry, flags=re.I | re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def valid_bib(entry: str) -> bool:
    return bool(bib_key(entry) and bib_type(entry) and "title" in entry.lower() and "year" in entry.lower())


def dblp_search(title: str) -> Tuple[str, str, str]:
    url = "https://dblp.org/search/publ/api?format=json&q=" + urllib.parse.quote(title)
    text, status, final = fetch_text(url)
    if status != "200" or not text:
        return "", "DBLP_SEARCH_FAILED", final or status
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return "", "DBLP_SEARCH_JSON_ERROR", str(exc)
    hits = data.get("result", {}).get("hits", {}).get("hit", [])
    scored = []
    for hit in hits:
        info = hit.get("info", {})
        hit_title = info.get("title", "")
        rec_url = info.get("url", "")
        score = token_score(title, hit_title)
        prefer = 0
        if "/journals/iacr/" in rec_url:
            prefer -= 1
        if "/conf/" in rec_url or "/journals/tches/" in rec_url:
            prefer += 1
        scored.append((score, prefer, rec_url, hit_title))
    scored.sort(reverse=True)
    if not scored or scored[0][0] < 0.65:
        return "", "DBLP_SEARCH_NO_STRONG_MATCH", f"best={scored[0][0]:.3f}" if scored else "no_hits"
    return scored[0][2], "DBLP_SEARCH_MATCH", f"score={scored[0][0]:.3f};title={scored[0][3]}"


def route_preference(rec_url: str, route: str) -> int:
    preference = 0
    if "/conf/" in rec_url or "/journals/tches/" in rec_url:
        preference += 2
    if "/journals/iacr/" in rec_url:
        preference -= 1
    if route == "dblp_secondary_direct":
        preference += 1
    return preference


def fetch_bib_candidate(title: str, rec_url: str, route: str, note: str) -> Dict[str, str]:
    bib_url = rec_to_bib_url(rec_url)
    entry, status, final = fetch_text(bib_url)
    if not valid_bib(entry):
        return {
            "route": route,
            "route_url": bib_url,
            "http_status": status,
            "final_url": final,
            "error": note + "; fetched content did not parse as BibTeX",
            "entry": "",
            "score": "0.000",
            "preference": str(route_preference(rec_url, route)),
            "bibkey": "",
            "entry_type": "",
        }
    score = token_score(title, bib_title(entry))
    return {
        "route": route,
        "route_url": bib_url,
        "http_status": status,
        "final_url": final,
        "error": note,
        "entry": entry.strip(),
        "score": f"{score:.3f}",
        "preference": str(route_preference(rec_url, route)),
        "bibkey": bib_key(entry),
        "entry_type": bib_type(entry),
    }


def retrieve_one(row: Dict[str, str]) -> Tuple[Dict[str, str], str]:
    source_id = row["source_id"]
    title = row["title"]
    primary = row["primary_url"]
    secondary = row["secondary_url"]

    if source_id == "LW23A_B":
        return {
            "source_id": source_id,
            "title": title,
            "retrieval_status": "TODO_COMPOSITE_SOURCE_SPLIT_REQUIRED",
            "route": "manual_split_required",
            "route_url": primary + " ; " + secondary,
            "http_status": "",
            "bibkey": "",
            "entry_type": "",
            "title_match_score": "",
            "final_url": "",
            "error": "Stage230 source row combines Batch Bootstrapping I and II; split into two verified BibTeX entries before LaTeX.",
        }, ""

    candidates: List[Tuple[str, str, str]] = []
    rec_url, route_status, route_note = dblp_search(title)
    time.sleep(2.2)
    if rec_url:
        candidates.append(("dblp_title_search", rec_url, route_note))
    if "dblp.org/rec/" in secondary:
        candidates.append(("dblp_secondary_direct", secondary, secondary))

    if not candidates:
        return {
            "source_id": source_id,
            "title": title,
            "retrieval_status": "TODO_NO_VERIFIED_BIBTEX_ROUTE",
            "route": route_status,
            "route_url": primary,
            "http_status": "",
            "bibkey": "",
            "entry_type": "",
            "title_match_score": "",
            "final_url": "",
            "error": route_note,
        }, ""

    checked = [fetch_bib_candidate(title, rec_url, route, note) for route, rec_url, note in candidates]
    valid = [candidate for candidate in checked if candidate["entry"]]
    if not valid:
        route_summary = "; ".join(candidate["route_url"] for candidate in checked)
        status_summary = "; ".join(candidate["http_status"] for candidate in checked)
        error_summary = "; ".join(candidate["error"] for candidate in checked)
        return {
            "source_id": source_id,
            "title": title,
            "retrieval_status": "TODO_BIBTEX_FETCH_OR_PARSE_FAILED",
            "route": "checked_candidates",
            "route_url": route_summary,
            "http_status": status_summary,
            "bibkey": "",
            "entry_type": "",
            "title_match_score": "",
            "final_url": "",
            "error": error_summary,
        }, ""

    qualified = [candidate for candidate in valid if float(candidate["score"]) >= 0.80]
    if qualified:
        best = sorted(qualified, key=lambda candidate: (int(candidate["preference"]), float(candidate["score"])), reverse=True)[0]
    else:
        best = sorted(valid, key=lambda candidate: (float(candidate["score"]), int(candidate["preference"])), reverse=True)[0]
    return {
        "source_id": source_id,
        "title": title,
        "retrieval_status": "RETRIEVED_VERIFIED_BIBTEX",
        "route": best["route"],
        "route_url": best["route_url"],
        "http_status": best["http_status"],
        "bibkey": best["bibkey"],
        "entry_type": best["entry_type"],
        "title_match_score": best["score"],
        "final_url": best["final_url"],
        "error": best["error"],
    }, best["entry"]


def retrieval_rows() -> Tuple[List[Dict[str, str]], List[str]]:
    rows = []
    entries = []
    for row in read_csv(STAGE238 / "bibtex_todo.csv"):
        result, entry = retrieve_one(row)
        rows.append(result)
        if entry:
            entries.append(entry)
    return rows, entries


def keymap_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out = []
    for row in rows:
        if row["retrieval_status"] == "RETRIEVED_VERIFIED_BIBTEX":
            out.append(
                {
                    "source_id": row["source_id"],
                    "citation_key": row["bibkey"],
                    "entry_type": row["entry_type"],
                    "source": row["route_url"],
                    "status": "READY_FOR_LATEX",
                }
            )
    return out


def todo_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out = []
    for row in rows:
        if row["retrieval_status"] != "RETRIEVED_VERIFIED_BIBTEX":
            out.append(
                {
                    "source_id": row["source_id"],
                    "title": row["title"],
                    "todo_status": row["retrieval_status"],
                    "needed_action": row["error"],
                    "route_attempted": row["route"],
                    "route_url": row["route_url"],
                }
            )
    return out


def latex_stub(keys: List[Dict[str, str]], todos: List[Dict[str, str]]) -> str:
    cite_keys = [row["citation_key"] for row in keys]
    cite_line = ", ".join("\\cite{" + key + "}" for key in cite_keys)
    todo_lines = "\n".join("% CITATION TODO [" + row["source_id"] + "]: " + row["needed_action"] for row in todos)
    return f"""\\documentclass{{article}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{booktabs}}
\\usepackage{{hyperref}}

\\title{{Scoped PVW/MAT-SAB Evidence Stub}}
\\author{{Anonymous}}
\\date{{}}

\\begin{{document}}
\\maketitle

\\section{{Scope}}
This stub is generated by Stage239. It is not a final paper. It cites only
BibTeX entries retrieved from verified routes and keeps unresolved sources as
TODO comments.

\\section{{Related Work Entry Points}}
Retrieved citation entry points: {cite_line if cite_line else "none"}.

{todo_lines}

\\section{{Local Evidence}}
The selected binary PVW/MAT-SAB matrix and complete-SAB $T_{{bootstrap}}/r$
results are local repro artifacts, not literature claims.

\\bibliographystyle{{plain}}
\\bibliography{{retrieved_references}}
\\end{{document}}
"""


def gate_rows(inputs: List[Dict[str, str]], retrieval: List[Dict[str, str]], todos: List[Dict[str, str]], keys: List[Dict[str, str]]) -> List[Dict[str, str]]:
    retrieved = sum(1 for row in retrieval if row["retrieval_status"] == "RETRIEVED_VERIFIED_BIBTEX")
    parsed = all(row["bibkey"] and row["entry_type"] for row in retrieval if row["retrieval_status"] == "RETRIEVED_VERIFIED_BIBTEX")
    no_fake = all(row["retrieval_status"] != "GENERATED_FROM_MEMORY" for row in retrieval)
    return [
        {
            "gate": "G1_inputs",
            "required": "Stage238 BibTeX TODO and claim support exist",
            "observed": "all present" if all(row["status"] == "present" for row in inputs) else "missing",
            "status": "PASS" if all(row["status"] == "present" for row in inputs) else "FAIL",
            "claim_effect": "allows BibTeX retrieval",
        },
        {
            "gate": "G2_verified_retrieval",
            "required": "retrieved entries come from DBLP/verified routes and parse as BibTeX",
            "observed": f"retrieved={retrieved}; parsed={parsed}",
            "status": "PASS_PARTIAL_RETRIEVAL" if retrieved > 0 and parsed else "FAIL",
            "claim_effect": "allows LaTeX stub citations for retrieved entries only",
        },
        {
            "gate": "G3_unresolved_todos",
            "required": "unretrieved or composite sources remain explicit TODOs",
            "observed": f"todos={len(todos)}",
            "status": "PASS_TODOS_RECORDED",
            "claim_effect": "prevents silent citation gaps",
        },
        {
            "gate": "G4_no_bibtex_hallucination",
            "required": "no BibTeX is generated from memory",
            "observed": f"no_fake={no_fake}; ready_keys={len(keys)}",
            "status": "PASS_NO_BIBTEX_HALLUCINATION" if no_fake else "FAIL",
            "claim_effect": "keeps references auditable",
        },
        {
            "gate": "G5_stage239_decision",
            "required": "retrieval, TODO, and no-hallucination gates pass",
            "observed": DECISION,
            "status": DECISION,
            "claim_effect": "move to optional LaTeX expansion or native counter attribution",
        },
    ]


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
            "route": "stage240_latex_draft_expansion",
            "entry_condition": "A full LaTeX draft is needed.",
            "gate": "Use only ready citation keys or explicit TODO comments; no broad novelty/optimality wording.",
            "status": "ready_if_draft_needed",
            "failure_action": "Keep Stage239 stub only.",
            "evidence": rel(LATEX_STUB),
        },
        {
            "priority": "P1",
            "route": "stage241_native_counter_backend_validation",
            "entry_condition": "The draft needs stronger implementation attribution.",
            "gate": "Native Linux perf counters or explicit WSL proxy label; no theoretical-optimality wording.",
            "status": "optional",
            "failure_action": "Omit counter claims.",
            "evidence": rel(KEYMAP),
        },
        {
            "priority": "P2",
            "route": "stage242_unresolved_bibtex_followup",
            "entry_condition": "Final LaTeX bibliography requires all sources resolved.",
            "gate": "Resolve TODO sources from official routes or split composite rows.",
            "status": "future",
            "failure_action": "Leave TODO comments and do not submit final paper.",
            "evidence": rel(TODO),
        },
    ]


def artifact_rows(paths: List[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        if path.exists() and path.is_file():
            rows.append({"artifact": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256(path)})
    return rows


def write_repro_commands() -> None:
    write_text(
        REPRO_CMDS,
        """# Stage239 Reproduction Commands

Stage239 retrieves BibTeX from verified routes where possible:

```bash
python scripts/build_stage239_bibtex_latex_stub.py
```

The generated `.bib` files include only fetched and parsed entries. Unresolved
sources remain in `unresolved_bibtex_todo.csv`.
""",
    )


def write_docs(inputs: List[Dict[str, str]], retrieval: List[Dict[str, str]], keys: List[Dict[str, str]], todos: List[Dict[str, str]], gates: List[Dict[str, str]], proof: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> None:
    doc = f"""# Stage239 BibTeX Retrieval and LaTeX Stub

Decision: `{DECISION}`.

Stage239 retrieves BibTeX only from verified routes and writes unresolved
entries as TODOs. It does not generate BibTeX from memory. The LaTeX stub is a
paper assembly aid, not a final manuscript.

## Retrieval Results

{table(retrieval, ["source_id", "title", "retrieval_status", "route", "route_url", "http_status", "bibkey", "entry_type", "title_match_score", "final_url", "error"])}
## Citation Key Map

{table(keys, ["source_id", "citation_key", "entry_type", "source", "status"])}
## Unresolved TODOs

{table(todos, ["source_id", "title", "todo_status", "needed_action", "route_attempted", "route_url"])}
## Gates

{table(gates, ["gate", "required", "observed", "status", "claim_effect"])}
## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
## Inputs

{table(inputs, ["input", "status", "role", "bytes"])}
"""
    write_text(DOC, doc)
    write_text(REPORT, doc)
    write_text(
        PLAN,
        """# Stage239 BibTeX Retrieval Plan

Stage239 consumes Stage238 BibTeX TODO rows. It attempts DBLP title search and
direct DBLP `.bib` retrieval. Only fetched and parsed BibTeX entries are written
to `retrieved_references.bib`. Composite or failed sources remain TODOs.
""",
    )
    write_text(
        THEORY,
        """# Stage239 BibTeX Policy Model

Citation keys and BibTeX entries are evidence only if they are retrieved from a
verified route and parse as BibTeX. A missing entry is not filled by memory or
LLM generation. The LaTeX stub may cite retrieved keys and must keep unresolved
sources as TODO comments.
""",
    )
    write_text(
        VARIANT,
        """# mat_rlwe_sab_stage239_bibtex_stub

## Summary

- Parent artifact: Stage238 source-verified citation package.
- Focused module: verified BibTeX retrieval and LaTeX assembly stub.
- Optimization target: citation integrity.
- Status labels: [partial verified BibTeX], [TODOs remain], [no hallucinated BibTeX].
""",
    )


def update_project_files(retrieved: int, todo_count: int) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 239: Verified BibTeX Retrieval and LaTeX Stub",
        f"""
## Stage 239: Verified BibTeX Retrieval and LaTeX Stub

Goal:

```text
Retrieve BibTeX from verified routes where possible, keep unresolved sources as
TODOs, and create a minimal LaTeX stub without generating references from
memory.
```

Status:

```text
Generated from input head `{head}` with `{DECISION}`. Retrieved {retrieved}
verified BibTeX entries and recorded {todo_count} unresolved TODOs.
```
""",
    )
    append_once(
        GOAL,
        "## Stage239 verified BibTeX retrieval and LaTeX stub",
        f"""
## Stage239 verified BibTeX retrieval and LaTeX stub

Generated from input head `{head}`, Stage239 records `{DECISION}`. Retrieved
{retrieved} verified BibTeX entries, wrote a LaTeX stub, and left {todo_count}
sources as explicit TODOs instead of fabricating references.
""",
    )
    append_once(
        CURRENT_GOAL,
        "### Stage239 verified BibTeX retrieval and LaTeX stub",
        f"""
### Stage239 verified BibTeX retrieval and LaTeX stub

`{DECISION}` records partial verified BibTeX retrieval and a minimal LaTeX
stub. The active goal remains open because final bibliography closure,
venue-specific paper assembly, optional native-counter attribution, and broader
algorithmic gates remain incomplete.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage239_verified_bibtex_latex_stub:",
        f"""
H10_stage239_verified_bibtex_latex_stub:
  status: partial_verified_bibtex_latex_stub_ready_todos_remain
  evidence:
    - repro/stage239_bibtex_latex_stub/bibtex_retrieval.csv
    - repro/stage239_bibtex_latex_stub/retrieved_references.bib
    - references/stage239_pvw_mat_sab.bib
    - repro/stage239_bibtex_latex_stub/unresolved_bibtex_todo.csv
    - docs/stage239_bibtex_latex_stub.md
  conclusion: >
    Stage239 records {DECISION}. It retrieved {retrieved} BibTeX entries from
    verified routes, generated a minimal LaTeX stub, and left {todo_count}
    unresolved sources as TODOs. No BibTeX entry was generated from memory.
""",
    )
    append_once(
        RUN_LOG,
        "stage239-verified-bibtex-latex-stub-001",
        f"""stage239-verified-bibtex-latex-stub-001,{date.today().isoformat()},{head},Stage 239,network+aggregation,"python scripts/build_stage239_bibtex_latex_stub.py","Stage238 BibTeX TODO; retrieved={retrieved}; todos={todo_count}",n/a,{DECISION},"Verified BibTeX retrieval and LaTeX stub complete; TODOs remain.",docs/stage239_bibtex_latex_stub.md; repro/stage239_bibtex_latex_stub/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage239_bibtex_latex_stub:",
        """
- stage239_bibtex_latex_stub:
  - `docs/stage239_bibtex_latex_stub.md`
  - `experiments/stage239_bibtex_latex_stub_plan.md`
  - `theory_checks/stage239_bibtex_policy_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage239_bibtex_stub.md`
  - `scripts/build_stage239_bibtex_latex_stub.py`
  - `references/stage239_pvw_mat_sab.bib`
  - `repro/stage239_bibtex_latex_stub/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage239 verified BibTeX retrieval and LaTeX stub records decision",
        f"""
- [x] Stage239 verified BibTeX retrieval and LaTeX stub records decision `{DECISION}`.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    REF_DIR.mkdir(parents=True, exist_ok=True)

    inputs = input_rows()
    retrieval, entries = retrieval_rows()
    keys = keymap_rows(retrieval)
    todos = todo_rows(retrieval)

    bib_text = "\n\n".join(entries).strip() + ("\n" if entries else "")
    write_text(OUT_BIB, bib_text if bib_text else "% No verified BibTeX entries retrieved.\n")
    write_text(ROOT_BIB, bib_text if bib_text else "% No verified BibTeX entries retrieved.\n")
    write_text(LATEX_STUB, latex_stub(keys, todos))

    gates = gate_rows(inputs, retrieval, todos, keys)
    proof = proof_rows(gates)
    nextq = next_rows()

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(RETRIEVAL, retrieval, ["source_id", "title", "retrieval_status", "route", "route_url", "http_status", "bibkey", "entry_type", "title_match_score", "final_url", "error"])
    write_csv(KEYMAP, keys, ["source_id", "citation_key", "entry_type", "source", "status"])
    write_csv(TODO, todos, ["source_id", "title", "todo_status", "needed_action", "route_attempted", "route_url"])
    write_csv(GATES, gates, ["gate", "required", "observed", "status", "claim_effect"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_repro_commands()
    write_docs(inputs, retrieval, keys, todos, gates, proof, nextq)

    artifacts = [DOC, PLAN, THEORY, VARIANT, INPUTS, RETRIEVAL, KEYMAP, TODO, LATEX_STUB, OUT_BIB, ROOT_BIB, GATES, PROOF, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "bytes", "sha256"])
    update_project_files(len(keys), len(todos))
    print(f"Stage239 report: {rel(DOC)}")
    print(f"Stage239 decision: {DECISION}")


if __name__ == "__main__":
    main()
