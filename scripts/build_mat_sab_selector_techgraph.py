#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mat_sab_research_state import load_state
from scripts.run_candidate_c_rank_bounded_gate import (
    GateEvidenceError,
    _resolve_under_root,
    _resolved_directory,
    _restore_file_atomic,
    _validated_input_rows,
)


OUT_DIR = ROOT / "paper_techgraphs"
JSON_OUT = OUT_DIR / "2025_686_mat_sab_selector.yaml"
GRAPH_OUT = OUT_DIR / "2025_686_mat_sab_selector_graph.md"
GAPS_OUT = OUT_DIR / "2025_686_mat_sab_selector_gaps.md"
DISCOVERY_COMMAND = (
    'python -m unittest discover -s tests/research -p "test_*.py" -v'
)
SELECTOR_IMPLEMENTATION_INPUTS = (
    "scripts/build_mat_sab_selector_techgraph.py",
    "scripts/mat_sab_research_state.py",
    "scripts/run_candidate_c_rank_bounded_gate.py",
)

NODE_SPECS = (
    ("sab_schedule", "src/sparse_amortized_bootstrap.c", "void RGSW_monomial_mul(", "scalar SAB butterfly and sparse schedule"),
    ("pvw_phase", "src/mosfhet/src/pvwtmlwe.c", "void pvmtmlwe_phase(", "phase map b_q - a*s_q"),
    ("pvw_randomization", "src/mosfhet/src/pvwtmlwe.c", "void pvmtmlwe_sample(", "shared random mask and r body corrections"),
    ("dense_keygen", "src/mosfhet/src/mattrgsw.c", "void mat_trgsw_monomial_sample(", "standard dense MAT-GGSW row sampling"),
    ("dense_decompose", "src/mosfhet/src/mattrgsw.c", "pvmtmlwe_decompose(scratch->dec", "decompose all k+r components"),
    ("dense_addmul", "src/mosfhet/src/mattrgsw.c", "static void mat_trgsw_mul_pvmtmlwe_DFT_from_dec(", "dense selector-output products"),
    ("compact_kernel", "src/mosfhet/src/mattrgsw.c", "void mat_trgsw_compact_mul_pvmtmlwe_DFT(", "lane-local compact evaluator"),
    ("generalized_lane_pair", "repro/stage134_generalized_lane_pair_input_ep_gate/summary.csv", "", "closure-restoring but performance-negative lane-pair input"),
    ("shared_mask_kernel", "repro/stage138_shared_mask_compact_gate/summary.csv", "", "positive isolated compact-kernel evidence"),
    ("closure_failure", "repro/stage139_compact_closure_audit/summary.csv", "", "compact output not closed as standard PVW state"),
    ("star_cycle_support", "repro/stage203_production_selector_equation_probe/equation_map.csv", "lane_neighbor_body_interaction", "4r declared active support"),
    ("neighbor_gap", "repro/stage222_isolated_compact_ep_integration/expressiveness_results.csv", "", "lane-local API lacks neighbor-capable selector"),
    ("distribution_blocker", "repro/stage249_structured_compact_distribution_security/claim_boundary.csv", "", "public compact-saving pattern remains distinguishable"),
    ("finite_semantic_zero", "repro/stage329_formal_compact_selector_checker/summary.csv", "", "finite semantic-zero pass with security open"),
)

EDGES = (
    ("sab_schedule", "dense_decompose", "each MAT CMUX invokes external-product decomposition"),
    ("dense_decompose", "dense_addmul", "m*T streams feed m*m*T products"),
    ("pvw_randomization", "dense_keygen", "every selector column is a PVW ciphertext sample"),
    ("pvw_phase", "closure_failure", "output must preserve all r phase equations"),
    ("shared_mask_kernel", "closure_failure", "local speedup alone does not close the SAB state"),
    ("generalized_lane_pair", "closure_failure", "closure restoration repeats expensive transforms"),
    ("star_cycle_support", "neighbor_gap", "cycle terms require neighbor-capable output"),
    ("star_cycle_support", "distribution_blocker", "semantic sparsity must not become public leakage"),
    ("finite_semantic_zero", "distribution_blocker", "finite algebra is not a distribution proof"),
)

PRE_GATE_OPEN_GAPS = (
    "standard PVW randomization dimension",
    "production key distribution and assumption comparison",
    "noise recurrence under the admitted selector representation",
    "Amdahl projection against exact-dense complete SAB",
    "isolated kernel and complete-SAB evidence",
)
POST_A_REJECTION_OPEN_GAPS = (
    "Candidate B factorized-operator equation gate (not begun)",
    "production key distribution and assumption comparison for an admitted representation",
    "noise recurrence under an admitted selector representation",
    "Amdahl projection against exact-dense complete SAB",
    "isolated kernel and complete-SAB evidence",
)
POST_B_REJECTION_OPEN_GAPS = (
    "Candidate C rank-bounded shared-mask state equation gate (not begun)",
    "phase and rank-growth checks for the admitted accumulator state",
    "public relinearization cost and lane-phase preservation",
    "Amdahl projection against exact-dense complete SAB",
    "isolated kernel and complete-SAB evidence",
)
TERMINAL_CAMPAIGN_BOUNDARIES = (
    (
        "Task 3B has no C2 seed or material; Task 4 is "
        "SKIPPED_NO_REGISTERED_OPERATOR with no numeric complete-cost or "
        "Amdahl values."
    ),
    (
        "The exact-dense PVW/MAT-SAB implementation and its scoped measured "
        "result remain preserved."
    ),
    (
        "No Candidate D is opened automatically; any continuation requires "
        "a separately approved research design."
    ),
)


def _safe_source_file(root: Path, relative: str, label: str) -> Path:
    path = _resolve_under_root(
        root,
        root / relative,
        label,
        strict=False,
    )
    if not path.is_file():
        raise GateEvidenceError(f"{label} is not a file: {path}")
    return path


def _load_state_safe(root: Path) -> dict[str, object]:
    state_path = _safe_source_file(
        root,
        "research_state.yaml",
        "selector state source",
    )
    return load_state(state_path)


def _node(root: Path, spec: tuple[str, str, str, str]) -> dict[str, object]:
    node_id, relative, needle, role = spec
    path = _safe_source_file(
        root,
        relative,
        f"selector node source {node_id}",
    )
    contains = (
        not needle
        or needle in path.read_text(encoding="utf-8", errors="replace")
    )
    return {
        "id": node_id,
        "path": relative,
        "symbol_or_token": needle,
        "role": role,
        "anchor_status": "PASS" if contains else "FAIL",
    }


def _campaign_view(state: Mapping[str, object]) -> dict[str, object]:
    candidates = state["candidates"]
    active_candidate = str(state["active_candidate"])
    active_status = str(candidates[active_candidate]["status"])
    campaign_state = {
        "goal_status": state["goal_status"],
        "paper_gate": state["paper_gate"],
        "active_candidate": active_candidate,
        "active_candidate_status": active_status,
        "candidate_a_status": candidates["A"]["status"],
        "candidate_b_status": candidates["B"]["status"],
        "candidate_c_status": candidates["C"]["status"],
        "last_decision": state["last_decision"],
    }
    if (
        state["goal_status"] == "RESEARCH_CAMPAIGN_EXHAUSTED"
        and active_candidate == "C"
        and all(
            candidates[candidate]["status"] == "REJECTED"
            for candidate in ("A", "B", "C")
        )
    ):
        disposition = (
            "The finite A/B/C mechanism campaign is exhausted; Candidate C "
            "closed on its scoped C1 nonpositive structural-cost failure."
        )
        next_step = (
            "Task 3B and Task 4 were skipped; exact-dense PVW/MAT-SAB "
            "evidence is preserved; no Candidate D is opened automatically."
        )
        open_gaps = TERMINAL_CAMPAIGN_BOUNDARIES
    elif (
        candidates["A"]["status"] == "REJECTED"
        and active_candidate == "B"
    ):
        disposition = (
            "Candidate A is closed after failing the standard-PVW "
            "randomization necessary condition."
        )
        next_step = (
            f"Candidate B is active at `{active_status}`; its equations and "
            "implementation have not begun."
        )
        open_gaps = POST_A_REJECTION_OPEN_GAPS
    elif (
        candidates["A"]["status"] == "REJECTED"
        and candidates["B"]["status"] == "REJECTED"
        and active_candidate == "C"
    ):
        disposition = (
            "Candidate B is closed after failing the exact standard-PVW "
            "factorization gate."
        )
        next_step = (
            f"Candidate C is active at `{active_status}`; its equations and "
            "implementation have not begun."
        )
        open_gaps = POST_B_REJECTION_OPEN_GAPS
    else:
        disposition = (
            f"Candidate A remains at `{candidates['A']['status']}`."
        )
        next_step = (
            f"Candidate {active_candidate} is active at `{active_status}`."
        )
        open_gaps = PRE_GATE_OPEN_GAPS
    return {
        "campaign_state": campaign_state,
        "candidate_a_disposition": disposition,
        "next_step": next_step,
        "open_gaps": list(open_gaps),
    }


def build_graph(
    root: Path = ROOT,
    *,
    input_commit: str,
) -> dict[str, object]:
    source_root = _resolved_directory(root, "selector source root")
    resolved_commit, _input_rows = _validated_input_rows(
        source_root,
        input_commit,
        SELECTOR_IMPLEMENTATION_INPUTS,
    )
    state = _load_state_safe(source_root)
    graph = {
        "schema_version": 1,
        "contract": state["contract"],
        "candidate": "A",
        "production_code_permission": state["production_hot_path_permission"],
        "implementation_input_commit": resolved_commit,
        "reproduction_command": (
            "python scripts/build_mat_sab_selector_techgraph.py "
            f"--input-commit {resolved_commit}"
        ),
        "nodes": [_node(source_root, spec) for spec in NODE_SPECS],
        "edges": [
            {"from": source, "to": target, "relation": relation}
            for source, target, relation in EDGES
        ],
    }
    graph.update(_campaign_view(state))
    return graph


def _reproduction_markdown(graph: Mapping[str, object]) -> list[str]:
    return [
        "",
        "## Reproduction",
        "",
        "```powershell",
        str(graph["reproduction_command"]),
        DISCOVERY_COMMAND,
        "```",
    ]


def _campaign_markdown(graph: Mapping[str, object]) -> list[str]:
    state = graph["campaign_state"]
    return [
        "## Campaign State",
        "",
        f'- Goal: `{state["goal_status"]}`',
        f'- Paper gate: `{state["paper_gate"]}`',
        (
            f'- Candidate A: `{state["candidate_a_status"]}`'
            + (
                " (active)"
                if state["active_candidate"] == "A"
                else ""
            )
        ),
        (
            f'- Candidate B: `{state["candidate_b_status"]}`'
            + (
                " (active)"
                if state["active_candidate"] == "B"
                else ""
            )
        ),
        (
            f'- Candidate C: `{state["candidate_c_status"]}`'
            + (
                " (active)"
                if state["active_candidate"] == "C"
                else ""
            )
        ),
        f'- Last decision: `{state["last_decision"]}`',
        f'- Disposition: {graph["candidate_a_disposition"]}',
        "",
        str(graph["next_step"]),
    ]


def _graph_markdown(graph: Mapping[str, object]) -> str:
    lines = [
        "# 2025/686 MAT-SAB Selector And State Graph",
        "",
    ]
    lines.extend(_campaign_markdown(graph))
    lines.extend([
        "",
        "```mermaid",
        "flowchart TD",
    ])
    for node in graph["nodes"]:
        lines.append(f'  {node["id"]}["{node["id"]}: {node["role"]}"]')
    for edge in graph["edges"]:
        lines.append(f'  {edge["from"]} -->|"{edge["relation"]}"| {edge["to"]}')
    lines.extend(["```", "", "## Anchors", "", "| node | path | status |", "| --- | --- | --- |"])
    for node in graph["nodes"]:
        lines.append(f'| {node["id"]} | `{node["path"]}` | {node["anchor_status"]} |')
    lines.extend(_reproduction_markdown(graph))
    return "\n".join(lines) + "\n"


def _gaps_markdown(graph: Mapping[str, object]) -> str:
    lines = [
        "# MAT-SAB Campaign Gaps",
        "",
    ]
    lines.extend(_campaign_markdown(graph))
    lines.extend([
        "",
        (
            "Production code permission: "
            f'`{str(graph["production_code_permission"]).lower()}`.'
        ),
        "",
        (
            "The closed Candidate A result is a finite-field "
            "necessary-condition rejection; it does not infer cryptographic "
            "security or complete-SAB performance."
        ),
        "",
        "## Open Obligations",
        "",
    ])
    lines.extend(f"- {gap}" for gap in graph["open_gaps"])
    lines.extend(_reproduction_markdown(graph))
    return "\n".join(lines) + "\n"


def _selector_relative_paths() -> tuple[Path, Path, Path]:
    return (
        Path("paper_techgraphs") / JSON_OUT.name,
        Path("paper_techgraphs") / GRAPH_OUT.name,
        Path("paper_techgraphs") / GAPS_OUT.name,
    )


def _preflight_selector_destinations(destination: Path) -> None:
    for relative in _selector_relative_paths():
        candidate = destination / relative
        resolved = _resolve_under_root(
            destination,
            candidate,
            f"selector destination {relative.as_posix()}",
            strict=False,
        )
        if candidate.exists() and not resolved.is_file():
            raise GateEvidenceError(
                f"selector destination is not a file: {resolved}"
            )


def _render_selector_outputs(
    destination: Path,
    graph: Mapping[str, object],
) -> tuple[Path, Path, Path]:
    paths = tuple(
        destination / relative
        for relative in _selector_relative_paths()
    )
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    paths[0].write_text(
        json.dumps(graph, indent=2) + "\n",
        encoding="ascii",
        newline="\n",
    )
    paths[1].write_text(
        _graph_markdown(graph),
        encoding="ascii",
        newline="\n",
    )
    paths[2].write_text(
        _gaps_markdown(graph),
        encoding="ascii",
        newline="\n",
    )
    return paths


def _publish_selector_outputs(
    destination: Path,
    stage: Path,
) -> tuple[Path, Path, Path]:
    relative_paths = _selector_relative_paths()
    snapshots = {
        relative: (
            (destination / relative).read_bytes()
            if (destination / relative).is_file()
            else None
        )
        for relative in relative_paths
    }
    published: list[Path] = []
    try:
        for relative in relative_paths:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            _resolve_under_root(
                destination,
                target,
                f"selector destination {relative.as_posix()}",
                strict=False,
            )
            os.replace(stage / relative, target)
            published.append(relative)
    except Exception:
        for relative in reversed(published):
            _restore_file_atomic(
                destination / relative,
                snapshots[relative],
            )
        raise
    return tuple(destination / relative for relative in relative_paths)


def write_outputs(
    root: Path,
    graph: Mapping[str, object],
) -> tuple[Path, Path, Path]:
    destination = _resolved_directory(root, "selector destination root")
    _preflight_selector_destinations(destination)
    stage = Path(
        tempfile.mkdtemp(
            prefix=".selector-techgraph-stage-",
            dir=destination,
        )
    )
    _resolve_under_root(
        destination,
        stage,
        "selector staging directory",
        strict=True,
    )
    try:
        _preflight_selector_destinations(stage)
        _render_selector_outputs(stage, graph)
        return _publish_selector_outputs(destination, stage)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--destination-root", type=Path)
    parser.add_argument("--input-commit", required=True)
    args = parser.parse_args()
    graph = build_graph(
        args.root,
        input_commit=args.input_commit,
    )
    failed = [node["id"] for node in graph["nodes"] if node["anchor_status"] != "PASS"]
    if failed:
        print("FAIL_TECHGRAPH_ANCHORS:" + ",".join(failed))
        return 1
    write_outputs(args.destination_root or args.root, graph)
    print("PASS_CANDIDATE_A_TECHGRAPH_ANCHORED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
