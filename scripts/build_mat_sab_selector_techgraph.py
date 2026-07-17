#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "paper_techgraphs"
JSON_OUT = OUT_DIR / "2025_686_mat_sab_selector.yaml"
GRAPH_OUT = OUT_DIR / "2025_686_mat_sab_selector_graph.md"
GAPS_OUT = OUT_DIR / "2025_686_mat_sab_selector_gaps.md"

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

OPEN_GAPS = (
    "standard PVW randomization dimension",
    "production key distribution and assumption comparison",
    "noise recurrence under the admitted selector representation",
    "Amdahl projection against exact-dense complete SAB",
    "isolated kernel and complete-SAB evidence",
)


def _node(root: Path, spec: tuple[str, str, str, str]) -> dict[str, object]:
    node_id, relative, needle, role = spec
    path = root / relative
    exists = path.is_file()
    contains = exists and (not needle or needle in path.read_text(encoding="utf-8", errors="replace"))
    return {
        "id": node_id,
        "path": relative,
        "symbol_or_token": needle,
        "role": role,
        "anchor_status": "PASS" if contains else "FAIL",
    }


def build_graph(root: Path = ROOT) -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract": "docs/superpowers/specs/2026-07-16-ccs-usenix-mat-sab-research-contract-design.md",
        "candidate": "A",
        "production_code_permission": False,
        "nodes": [_node(root, spec) for spec in NODE_SPECS],
        "edges": [
            {"from": source, "to": target, "relation": relation}
            for source, target, relation in EDGES
        ],
        "open_gaps": list(OPEN_GAPS),
    }


def _graph_markdown(graph: Mapping[str, object]) -> str:
    lines = [
        "# 2025/686 MAT-SAB Selector And State Graph",
        "",
        "```mermaid",
        "flowchart TD",
    ]
    for node in graph["nodes"]:
        lines.append(f'  {node["id"]}["{node["id"]}: {node["role"]}"]')
    for edge in graph["edges"]:
        lines.append(f'  {edge["from"]} -->|"{edge["relation"]}"| {edge["to"]}')
    lines.extend(["```", "", "## Anchors", "", "| node | path | status |", "| --- | --- | --- |"])
    for node in graph["nodes"]:
        lines.append(f'| {node["id"]} | `{node["path"]}` | {node["anchor_status"]} |')
    return "\n".join(lines) + "\n"


def _gaps_markdown(graph: Mapping[str, object]) -> str:
    lines = [
        "# Candidate A Pre-Production Gaps",
        "",
        "Production code permission: `false`.",
        "",
    ]
    lines.extend(f"- {gap}" for gap in graph["open_gaps"])
    lines.extend([
        "",
        "The next gate tests `P M = mu P` and the standard PVW randomization",
        "dimension. It does not infer cryptographic security from finite arithmetic.",
    ])
    return "\n".join(lines) + "\n"


def write_outputs(root: Path, graph: Mapping[str, object]) -> tuple[Path, Path, Path]:
    out_dir = root / "paper_techgraphs"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = (
        out_dir / JSON_OUT.name,
        out_dir / GRAPH_OUT.name,
        out_dir / GAPS_OUT.name,
    )
    paths[0].write_text(json.dumps(graph, indent=2) + "\n", encoding="ascii", newline="\n")
    paths[1].write_text(_graph_markdown(graph), encoding="ascii", newline="\n")
    paths[2].write_text(_gaps_markdown(graph), encoding="ascii", newline="\n")
    return paths


def main() -> int:
    graph = build_graph(ROOT)
    failed = [node["id"] for node in graph["nodes"] if node["anchor_status"] != "PASS"]
    if failed:
        print("FAIL_TECHGRAPH_ANCHORS:" + ",".join(failed))
        return 1
    write_outputs(ROOT, graph)
    print("PASS_CANDIDATE_A_TECHGRAPH_ANCHORED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
