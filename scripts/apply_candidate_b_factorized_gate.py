#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mat_sab_research_state import (
    load_state,
    transition_candidate,
    validate_state,
    write_state,
)
from scripts.run_candidate_b_factorized_gate import (
    ADMIT,
    REJECT,
    SUMMARY_FIELDS,
    canonical_summary_record,
    evaluate_candidate_b,
)


RUN_MARKER = "candidate-b-factorized-gate-001"
HYPOTHESIS_START = "# candidate-b-factorized-gate-hypothesis-start"
HYPOTHESIS_END = "# candidate-b-factorized-gate-hypothesis-end"
MANIFEST_START = "<!-- candidate-b-factorized-gate-manifest-start -->"
MANIFEST_END = "<!-- candidate-b-factorized-gate-manifest-end -->"
CHECKLIST_START = "<!-- candidate-b-factorized-gate-checklist-start -->"
CHECKLIST_END = "<!-- candidate-b-factorized-gate-checklist-end -->"
PREDECESSOR_DECISION = (
    "REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B"
)
TECHGRAPH_DECISION = "CANDIDATE_B_TECHGRAPH_ANCHORED"
EQUATIONS_DECISION = "CANDIDATE_B_EQUATIONS_DEFINED"
GRAPH_PATH = "paper_techgraphs/candidate_b_factorized_selector.yaml"
MODEL_PATH = "theory_checks/candidate_b_factorized_standard_pvw_model.md"
GRAPH_ANCHORS = {
    "pvw_ciphertext_type",
    "pvw_sample",
    "pvw_phase",
    "torus_error_sampler",
    "mat_selector_sample",
    "dense_external_product",
    "sab_pvw_cmux",
    "target_k_t_one",
}
MODEL_FRAGMENTS = (
    "C = mu h I_(k+r) + V [I_k | S] + [0 | E]",
    "C = mu h I_m + v w^T + [0 | E]",
    "P(d^T C) = mu h P(d) + d^T E",
    "phi(f) = f(1) mod 2",
    "q=O(1)",
    "m^2 = (r+1)^2",
    "T_bootstrap/r",
)


def _resolved_root(root: Path) -> Path:
    resolved = root.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"root is not a directory: {resolved}")
    return resolved


def _resolved_under_root(
    root: Path,
    path: Path,
    label: str,
    *,
    strict: bool,
) -> Path:
    resolved = path.resolve(strict=strict)
    if not resolved.is_relative_to(root):
        raise ValueError(f"{label} escapes root: {resolved}")
    return resolved


def _read_text(path: Path) -> str:
    return path.read_text(encoding="ascii") if path.exists() else ""


def _bounded_block(start: str, end: str, content: str) -> str:
    return f"{start}\n{content.rstrip()}\n{end}"


def _check_append(path: Path, start: str, end: str, content: str) -> bool:
    current = _read_text(path)
    lines = current.splitlines()
    if any(
        marker in line and line != marker
        for marker in (start, end)
        for line in lines
    ):
        raise ValueError(f"ledger block marker mismatch in {path}: {start}")
    start_lines = [index for index, line in enumerate(lines) if line == start]
    end_lines = [index for index, line in enumerate(lines) if line == end]
    if not start_lines and not end_lines:
        return True
    if len(start_lines) != 1 or len(end_lines) != 1:
        raise ValueError(f"ledger block marker mismatch in {path}: {start}")
    start_index = start_lines[0]
    end_index = end_lines[0]
    if end_index < start_index:
        raise ValueError(f"ledger block marker mismatch in {path}: {start}")
    actual = "\n".join(lines[start_index : end_index + 1])
    if actual != _bounded_block(start, end, content):
        raise ValueError(f"ledger block/content mismatch in {path}: {start}")
    return False


def _append_once(path: Path, start: str, end: str, content: str) -> None:
    if not _check_append(path, start, end, content):
        return
    current = _read_text(path)
    separator = "" if not current or current.endswith("\n") else "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        current + separator + _bounded_block(start, end, content) + "\n",
        encoding="ascii",
        newline="\n",
    )


def _summary_record(summary_path: Path) -> dict[str, str]:
    try:
        with summary_path.open(newline="", encoding="ascii") as handle:
            records = list(csv.reader(handle, strict=True))
    except (csv.Error, UnicodeError) as error:
        raise ValueError(
            "summary must contain one canonical decision"
        ) from error
    if len(records) != 2:
        raise ValueError("summary must contain one canonical decision")
    fields, row = records
    structurally_valid = (
        tuple(fields) == SUMMARY_FIELDS
        and len(set(fields)) == len(fields)
        and len(row) == len(fields)
        and all(value != "" for value in row)
    )
    if not structurally_valid:
        raise ValueError("summary must contain one canonical decision")
    decision = row[fields.index("decision")]
    if decision not in {ADMIT, REJECT}:
        raise ValueError("summary must contain one canonical decision")
    return dict(zip(fields, row))


def _validate_prerequisites(root: Path) -> None:
    try:
        graph_path = _resolved_under_root(
            root,
            root / GRAPH_PATH,
            "Candidate B techgraph",
            strict=True,
        )
        model_path = _resolved_under_root(
            root,
            root / MODEL_PATH,
            "Candidate B equation model",
            strict=True,
        )
        graph = json.loads(graph_path.read_text(encoding="ascii"))
        model = model_path.read_text(encoding="ascii")
        anchors = {
            anchor["id"]: anchor
            for anchor in graph["source_anchors"]
            if isinstance(anchor, dict) and "id" in anchor
        }
        state = graph["candidate_state"]
        graph_valid = (
            graph["schema_version"] == 1
            and graph["candidate"] == "B"
            and graph["production_hot_path_permission"] is False
            and "Theta(r)" in graph["research_question"]
            and set(anchors) == GRAPH_ANCHORS
            and all(
                anchor.get("anchor_status") == "PASS"
                for anchor in anchors.values()
            )
            and state["candidate"] == "B"
            and state["repository_status"] == "INTAKE"
            and state["in_memory_progression"]
            == ["INTAKE", "TECHGRAPH_ANCHORED", "EQUATIONS_DEFINED"]
            and state["repository_state_mutated"] is False
        )
        model_valid = all(fragment in model for fragment in MODEL_FRAGMENTS)
    except (
        FileNotFoundError,
        UnicodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
    ) as error:
        raise ValueError(
            "Candidate B source/equation prerequisites are incomplete"
        ) from error
    if not graph_valid or not model_valid:
        raise ValueError(
            "Candidate B source/equation prerequisites are incomplete"
        )


def _run_row(decision: str) -> dict[str, str]:
    return {
        "run_id": RUN_MARKER,
        "date": "2026-07-17",
        "commit_or_state": "candidate-b-factorized-mechanism-gate",
        "stage": "Candidate B mechanism gate",
        "backend": "finite-field-standard-library",
        "command": "python scripts/run_candidate_b_factorized_gate.py",
        "params": "r=2/4/6; mu=0/1; q=1,...,r; image=GF(2)",
        "seed": "deterministic",
        "status": decision,
        "summary": (
            "Exact standard-PVW factor rank and complete-cost gates decide "
            "Candidate B routing."
        ),
        "artifacts": "repro/candidate_b_factorized_gate/",
    }


def _run_log_plan(root: Path, decision: str) -> tuple[Path, list[str], bool]:
    path = _resolved_under_root(
        root,
        root / "repro/run_log.csv",
        "run-log destination",
        strict=True,
    )
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            records = list(csv.reader(handle, strict=True))
    except csv.Error as error:
        raise ValueError(
            "run log header must match canonical schema"
        ) from error
    fields = records[0] if records else []
    expected_fields = list(_run_row(decision))
    if fields != expected_fields or len(fields) != len(set(fields)):
        raise ValueError("run log header must match canonical schema")
    physical_rows = records[1:]
    if any(len(row) != len(fields) for row in physical_rows):
        raise ValueError("run log rows must match canonical schema")
    rows = [dict(zip(fields, row)) for row in physical_rows]
    matches = [row for row in rows if row.get("run_id") == RUN_MARKER]
    if len(matches) > 1:
        raise ValueError(f"duplicate run-log marker: {RUN_MARKER}")
    if matches:
        expected = _run_row(decision)
        if any(
            matches[0].get(field) != value
            for field, value in expected.items()
        ):
            raise ValueError(f"run-log marker/content mismatch: {RUN_MARKER}")
        return path, fields, False
    return path, fields, True


def _append_run(
    path: Path,
    fields: list[str],
    decision: str,
    needed: bool,
) -> None:
    if not needed:
        return
    row = _run_row(decision)
    if path.stat().st_size:
        with path.open("rb") as handle:
            handle.seek(-1, 2)
            has_line_terminator = handle.read(1) in {b"\r", b"\n"}
        if not has_line_terminator:
            with path.open("ab") as handle:
                handle.write(b"\n")
    with path.open("a", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writerow({field: row.get(field, "") for field in fields})


def _ledger_entries(
    decision: str,
) -> tuple[tuple[str, str, str, str], ...]:
    hypothesis = f"""H_candidate_b_factorized_mechanism:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/candidate_b_factorized_gate/summary.csv
    - repro/candidate_b_factorized_gate/phase_identity.csv
    - repro/candidate_b_factorized_gate/rank_controls.csv
    - repro/candidate_b_factorized_gate/factor_cost.csv
    - repro/candidate_b_factorized_gate/mechanism_matrix.csv
    - theory_checks/candidate_b_factorized_standard_pvw_model.md
  conclusion: >
    Candidate B is decided by source-anchored phase, multiplicative-image
    rank, complete-distribution, and full-cost gates. This result makes no
    general impossibility, security, noise, production, or speedup claim.
"""
    manifest = """- candidate_b_factorized_gate:
  - `research/mat_sab/factorized_selector_model.py`
  - `theory_checks/candidate_b_factorized_standard_pvw_model.md`
  - `paper_techgraphs/candidate_b_factorized_selector.yaml`
  - `docs/candidate_b_factorized_mechanism_gate.md`
  - `scripts/run_candidate_b_factorized_gate.py`
  - `scripts/apply_candidate_b_factorized_gate.py`
  - `repro/candidate_b_factorized_gate/`
"""
    checklist = f"""- [x] Candidate B records `{decision}` from source, phase, mutation,
  multiplicative-image rank, factor-cost, and concrete-mechanism gates;
  production hot-path permission remains false. Reproduce with
  `python scripts/run_candidate_b_factorized_gate.py` followed by
  `python scripts/apply_candidate_b_factorized_gate.py`.
"""
    return (
        (
            "hypotheses/hypothesis_register.yaml",
            HYPOTHESIS_START,
            HYPOTHESIS_END,
            hypothesis,
        ),
        (
            "repro/artifact_manifest.md",
            MANIFEST_START,
            MANIFEST_END,
            manifest,
        ),
        (
            "repro/reproduction_checklist.md",
            CHECKLIST_START,
            CHECKLIST_END,
            checklist,
        ),
    )


def _validate_pre_state(state: dict[str, object]) -> None:
    candidates = state["candidates"]
    expected = (
        state["goal_status"] == "ACTIVE"
        and state["paper_gate"] == "BLOCKED"
        and state["production_hot_path_permission"] is False
        and state["active_candidate"] == "B"
        and state.get("last_decision") == PREDECESSOR_DECISION
        and candidates["A"]["status"] == "REJECTED"
        and candidates["B"]["status"] == "INTAKE"
        and candidates["C"]["status"] == "QUEUED"
    )
    if not expected:
        raise ValueError("state is not at the Candidate B mechanism gate")


def _validate_applied_state(
    state: dict[str, object],
    decision: str,
) -> None:
    candidates = state["candidates"]
    common = (
        state["goal_status"] == "ACTIVE"
        and state["paper_gate"] == "BLOCKED"
        and state["production_hot_path_permission"] is False
        and state.get("last_decision") == decision
        and candidates["A"]["status"] == "REJECTED"
    )
    if decision == ADMIT:
        branch = (
            state["active_candidate"] == "B"
            and candidates["B"]["status"] == "ADVERSARIAL_CHECKER_PASS"
            and candidates["C"]["status"] == "QUEUED"
        )
    else:
        branch = (
            state["active_candidate"] == "C"
            and candidates["B"]["status"] == "REJECTED"
            and candidates["C"]["status"] == "INTAKE"
        )
    if not common or not branch:
        raise ValueError(
            f"state/decision mismatch: {candidates['B']['status']} and "
            f"{decision}"
        )
    validate_state(state)


def _transition_initial_state(
    state: dict[str, object],
    decision: str,
) -> dict[str, object]:
    _validate_pre_state(state)
    changed = transition_candidate(
        state,
        "B",
        "TECHGRAPH_ANCHORED",
        TECHGRAPH_DECISION,
    )
    changed = transition_candidate(
        changed,
        "B",
        "EQUATIONS_DEFINED",
        EQUATIONS_DECISION,
    )
    target = "ADVERSARIAL_CHECKER_PASS" if decision == ADMIT else "REJECTED"
    changed = transition_candidate(changed, "B", target, decision)
    _validate_applied_state(changed, decision)
    return changed


def _snapshot_outputs(paths: tuple[Path, ...]) -> dict[Path, bytes | None]:
    return {
        path: path.read_bytes() if path.exists() else None
        for path in paths
    }


def _restore_outputs(snapshot: dict[Path, bytes | None]) -> None:
    for path, content in snapshot.items():
        if content is None:
            if path.exists():
                path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def apply_gate(
    root: Path,
    state_path: Path,
    summary_path: Path,
) -> str:
    root = _resolved_root(root)
    state_path = _resolved_under_root(
        root,
        state_path,
        "state path",
        strict=True,
    )
    summary_path = _resolved_under_root(
        root,
        summary_path,
        "summary path",
        strict=True,
    )
    summary_record = _summary_record(summary_path)
    recomputed_record = canonical_summary_record(evaluate_candidate_b(root))
    if summary_record != recomputed_record:
        raise ValueError("summary does not match recomputed gate evidence")
    _validate_prerequisites(root)
    decision = summary_record["decision"]
    state = load_state(state_path)

    entries = tuple(
        (
            _resolved_under_root(
                root,
                root / relative,
                f"ledger destination {relative}",
                strict=False,
            ),
            start,
            end,
            content,
        )
        for relative, start, end, content in _ledger_entries(decision)
    )
    for path, start, end, content in entries:
        _check_append(path, start, end, content)
    run_path, run_fields, append_run = _run_log_plan(root, decision)

    current = state["candidates"]["B"]["status"]
    if current == "INTAKE":
        changed = _transition_initial_state(state, decision)
    elif current in {"ADVERSARIAL_CHECKER_PASS", "REJECTED"}:
        _validate_applied_state(state, decision)
        changed = None
    else:
        raise ValueError("state is not at the Candidate B mechanism gate")

    output_paths = (
        state_path,
        *(path for path, _start, _end, _content in entries),
        run_path,
    )
    snapshot = _snapshot_outputs(output_paths)
    try:
        if changed is not None:
            write_state(state_path, changed)
        for path, start, end, content in entries:
            _append_once(path, start, end, content)
        _append_run(run_path, run_fields, decision, append_run)
    except Exception:
        _restore_outputs(snapshot)
        raise
    return decision


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    state = args.state or args.root / "research_state.yaml"
    summary = (
        args.summary
        or args.root / "repro/candidate_b_factorized_gate/summary.csv"
    )
    print(apply_gate(args.root, state, summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
