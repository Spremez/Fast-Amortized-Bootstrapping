# Candidate A Star-Cycle Mechanism Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a source-anchored, executable pre-production gate that either admits Candidate A to key/security/noise preflight or rejects its direct sparse standard-PVW realization and deterministically routes the research campaign to Candidate B.

**Architecture:** Keep all SAB and MOSFHET C hot paths unchanged. Add a small Python standard-library research package that models the PVW phase map `P`, solves the constrained selector equation `P M = mu P` over finite fields, measures the affine randomization dimension of dense and star-cycle supports, and emits deterministic machine-readable evidence. A separate research-state tool records transitions so a failed mechanism cannot silently become production code or start an unbounded sequence of stages.

**Tech Stack:** Python 3 standard library (`argparse`, `csv`, `dataclasses`, `hashlib`, `json`, `pathlib`, `unittest`), existing C source as read-only evidence, Markdown, CSV, JSON syntax stored as YAML 1.2.

## Global Constraints

- The controlling contract is `docs/superpowers/specs/2026-07-16-ccs-usenix-mat-sab-research-contract-design.md` at or after commit `147666f`.
- The primary paper metric remains complete-SAB `T_bootstrap/r`; this work package makes no latency or speedup claim.
- Repeated scalar SAB and exact-dense PVW/MAT-SAB remain immutable baselines.
- Do not modify `src/sab_pvw.c`, `src/sparse_amortized_bootstrap.c`, `src/mosfhet/src/mattrgsw.c`, `src/mosfhet/src/pvwtmlwe.c`, public C headers, `main.c`, or the `Makefile` in this work package.
- No SAB hot-path implementation is authorized unless the mechanism, key/security/noise, and Amdahl gates pass in later reviewed plans.
- Use only Python standard-library modules; do not add a production or development dependency.
- `research_state.yaml` uses JSON syntax so it is valid YAML 1.2 and can be parsed with `json` without PyYAML.
- The checker must distinguish phase correctness from encryption randomization; a finite-field pass is not a cryptographic security proof.
- Candidate order is finite: A then B then C. A rejection activates B; C rejection produces `RESEARCH_CAMPAIGN_EXHAUSTED` and does not invent another candidate.
- Candidate A may use at most two equation revisions, two isolated kernel layouts, and one full-SAB integration across the whole campaign. This mechanism gate consumes no kernel layout and performs no full-SAB integration.
- Every generated artifact must be deterministic, idempotent, source-anchored, and accompanied by an exact reproduction command.
- Use ASCII in all new source and documentation files.
- Run research tests with `python -m unittest discover -s tests/research -p "test_*.py" -v`.

## File Map

| Path | Responsibility |
| --- | --- |
| `research_state.yaml` | Single machine-readable campaign state and route budget. |
| `scripts/mat_sab_research_state.py` | Validate and transition the finite A/B/C state machine. |
| `docs/current_mat_sab_ccs_goal.md` | Concise active Goal; old stage ledgers become historical references. |
| `scripts/build_mat_sab_selector_techgraph.py` | Verify source/artifact anchors and generate the selector/state graph. |
| `paper_techgraphs/2025_686_mat_sab_selector.yaml` | Machine-readable source/evidence graph in JSON-valid YAML. |
| `paper_techgraphs/2025_686_mat_sab_selector_graph.md` | Human-readable graph and call/equation flow. |
| `paper_techgraphs/2025_686_mat_sab_selector_gaps.md` | Exact open obligations before production code. |
| `research/mat_sab/finite_linear.py` | Dependency-free modular linear algebra and affine solver. |
| `research/mat_sab/star_cycle_model.py` | PVW phase map, supports, selector constraints, and randomization analysis. |
| `scripts/run_candidate_a_star_cycle_gate.py` | Execute the Candidate A adversarial gate and generate evidence. |
| `scripts/apply_mat_sab_candidate_gate.py` | Apply the computed decision to state, hypothesis, run log, and manifests. |
| `theory_checks/candidate_a_star_cycle_production_equations.md` | Formal equation derivation and scope boundary. |
| `algorithm_variants/candidate_a_star_cycle_sparse_mat_ggsw.md` | Candidate card with the computed disposition. |
| `experiments/candidate_a_star_cycle_gate_plan.md` | Registered inputs, controls, gates, and failure routing. |
| `docs/candidate_a_star_cycle_mechanism_gate.md` | Human-readable gate report. |
| `repro/candidate_a_star_cycle_gate/` | CSV evidence, commands, report, and checksums. |
| `tests/research/` | Unit and integration tests for state, graph, algebra, gate, and closeout. |

---

### Task 1: Freeze The Active Goal And Research State

**Files:**
- Create: `research_state.yaml`
- Create: `scripts/mat_sab_research_state.py`
- Create: `tests/research/test_research_state.py`
- Create: `docs/current_mat_sab_ccs_goal.md`
- Modify: `docs/current_codex_goal_sab_completion.md:1`
- Modify: `docs/roadmap_stage19_plus.md:1`

**Interfaces:**
- Produces: `load_state(path: Path) -> dict[str, object]`
- Produces: `validate_state(state: Mapping[str, object]) -> None`
- Produces: `transition_candidate(state: Mapping[str, object], candidate: str, to_status: str, decision: str) -> dict[str, object]`
- Produces: CLI commands `validate` and `transition` used by Tasks 2, 3, and 5.

- [ ] **Step 1: Write the failing state-machine tests**

Create `tests/research/test_research_state.py` with this complete test module:

```python
import json
import tempfile
import unittest
from pathlib import Path

from scripts.mat_sab_research_state import (
    load_state,
    transition_candidate,
    validate_state,
)


ROOT = Path(__file__).resolve().parents[2]


def candidate_a_state(state, status):
    state["goal_status"] = "ACTIVE"
    state["paper_gate"] = "BLOCKED"
    state["production_hot_path_permission"] = False
    state["active_candidate"] = "A"
    state["candidates"]["A"]["status"] = status
    state["candidates"]["B"]["status"] = "QUEUED"
    state["candidates"]["C"]["status"] = "QUEUED"
    return state


class ResearchStateTests(unittest.TestCase):
    def test_repository_state_is_valid_and_locked_to_primary_metric(self):
        state = load_state(ROOT / "research_state.yaml")
        validate_state(state)
        self.assertIn(state["goal_status"], {
            "ACTIVE", "PAPER_READY", "ACCEPTED",
            "RESEARCH_CAMPAIGN_EXHAUSTED", "EXTERNAL_BLOCKED",
        })
        self.assertEqual(state["primary_metric"], "complete_sab_T_bootstrap_over_r")
        self.assertIn(state["active_candidate"], ("A", "B", "C"))
        active = state["candidates"][state["active_candidate"]]["status"]
        if active in {"INTAKE", "TECHGRAPH_ANCHORED", "EQUATIONS_DEFINED"}:
            self.assertFalse(state["production_hot_path_permission"])

    def test_valid_transition_does_not_mutate_input(self):
        state = candidate_a_state(load_state(ROOT / "research_state.yaml"), "INTAKE")
        changed = transition_candidate(
            state, "A", "TECHGRAPH_ANCHORED", "CANDIDATE_A_TECHGRAPH_ANCHORED"
        )
        self.assertEqual(state["candidates"]["A"]["status"], "INTAKE")
        self.assertEqual(changed["candidates"]["A"]["status"], "TECHGRAPH_ANCHORED")
        self.assertEqual(changed["last_decision"], "CANDIDATE_A_TECHGRAPH_ANCHORED")

    def test_skipping_a_gate_is_rejected(self):
        state = candidate_a_state(load_state(ROOT / "research_state.yaml"), "INTAKE")
        with self.assertRaisesRegex(ValueError, "invalid transition"):
            transition_candidate(state, "A", "ISOLATED_KERNEL_PASS", "INVALID_SKIP")

    def test_rejection_routes_to_next_candidate(self):
        state = candidate_a_state(load_state(ROOT / "research_state.yaml"), "EQUATIONS_DEFINED")
        changed = transition_candidate(state, "A", "REJECTED", "A_REJECTED")
        self.assertEqual(changed["active_candidate"], "B")
        self.assertEqual(changed["candidates"]["B"]["status"], "INTAKE")
        self.assertEqual(changed["goal_status"], "ACTIVE")

    def test_json_valid_yaml_round_trip(self):
        state = load_state(ROOT / "research_state.yaml")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.yaml"
            path.write_text(json.dumps(state, indent=2) + "\n", encoding="ascii")
            self.assertEqual(load_state(path), state)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the state tests and verify the expected import failure**

Run:

```powershell
python -m unittest tests.research.test_research_state -v
```

Expected: `ERROR` with `ModuleNotFoundError: No module named 'scripts.mat_sab_research_state'`.

- [ ] **Step 3: Create the initial machine-readable campaign state**

Create `research_state.yaml` with this exact JSON object:

```json
{
  "schema_version": 1,
  "contract": "docs/superpowers/specs/2026-07-16-ccs-usenix-mat-sab-research-contract-design.md",
  "goal_status": "ACTIVE",
  "target_venue": "CCS_USENIX_SECURITY",
  "primary_metric": "complete_sab_T_bootstrap_over_r",
  "baselines": {
    "B0": "repeated_scalar_SAB",
    "B1": "exact_dense_PVW_MAT_SAB_current_head"
  },
  "active_candidate": "A",
  "candidate_order": ["A", "B", "C"],
  "candidates": {
    "A": {
      "name": "Star-Cycle Sparse MAT-GGSW",
      "status": "INTAKE",
      "equation_revisions_used": 0,
      "kernel_layouts_used": 0,
      "full_sab_integrations_used": 0
    },
    "B": {
      "name": "Factorized Star-Cycle",
      "status": "QUEUED",
      "equation_revisions_used": 0,
      "kernel_layouts_used": 0,
      "full_sab_integrations_used": 0
    },
    "C": {
      "name": "Rank-Bounded Shared-Mask State",
      "status": "QUEUED",
      "equation_revisions_used": 0,
      "kernel_layouts_used": 0,
      "full_sab_integrations_used": 0
    }
  },
  "paper_gate": "BLOCKED",
  "production_hot_path_permission": false,
  "last_decision": "CONTRACT_APPROVED"
}
```

- [ ] **Step 4: Implement state validation and transitions**

Create `scripts/mat_sab_research_state.py` with this complete implementation:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE = ROOT / "research_state.yaml"
ORDER = ("A", "B", "C")
PIPELINE = (
    "INTAKE",
    "TECHGRAPH_ANCHORED",
    "EQUATIONS_DEFINED",
    "ADVERSARIAL_CHECKER_PASS",
    "KEY_SECURITY_NOISE_PREFLIGHT_PASS",
    "AMDAHL_PROJECTION_PASS",
    "ISOLATED_KERNEL_PASS",
    "FULL_SAB_PASS",
    "PAPER_GATE_PASS",
)


def load_state(path: Path = DEFAULT_STATE) -> dict[str, object]:
    state = json.loads(path.read_text(encoding="ascii"))
    validate_state(state)
    return state


def validate_state(state: Mapping[str, object]) -> None:
    if state.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if state.get("candidate_order") != list(ORDER):
        raise ValueError("candidate_order must be A, B, C")
    if state.get("primary_metric") != "complete_sab_T_bootstrap_over_r":
        raise ValueError("primary metric changed")
    if state.get("goal_status") not in {
        "ACTIVE", "PAPER_READY", "ACCEPTED", "RESEARCH_CAMPAIGN_EXHAUSTED", "EXTERNAL_BLOCKED"
    }:
        raise ValueError("invalid goal_status")
    if state.get("active_candidate") not in ORDER:
        raise ValueError("invalid active_candidate")
    candidates = state.get("candidates")
    if not isinstance(candidates, Mapping) or set(candidates) != set(ORDER):
        raise ValueError("candidates must contain A, B, C")
    allowed = set(PIPELINE) | {"QUEUED", "REJECTED"}
    for name in ORDER:
        candidate = candidates[name]
        if not isinstance(candidate, Mapping) or candidate.get("status") not in allowed:
            raise ValueError(f"invalid status for candidate {name}")
        for field, limit in (
            ("equation_revisions_used", 2),
            ("kernel_layouts_used", 2),
            ("full_sab_integrations_used", 1),
        ):
            value = candidate.get(field)
            if not isinstance(value, int) or value < 0 or value > limit:
                raise ValueError(f"invalid {field} for candidate {name}")
    active_index = ORDER.index(state["active_candidate"])
    if state.get("goal_status") == "RESEARCH_CAMPAIGN_EXHAUSTED":
        if state.get("active_candidate") != "C" or any(
            candidates[name]["status"] != "REJECTED" for name in ORDER
        ):
            raise ValueError("exhausted campaign must have A, B, C rejected")
    else:
        if candidates[state["active_candidate"]]["status"] in {"QUEUED", "REJECTED"}:
            raise ValueError("active candidate is not active")
        if any(candidates[name]["status"] != "REJECTED" for name in ORDER[:active_index]):
            raise ValueError("candidates before the active candidate must be rejected")
        if any(candidates[name]["status"] != "QUEUED" for name in ORDER[active_index + 1:]):
            raise ValueError("candidates after the active candidate must be queued")
    if state.get("paper_gate") == "PASS" and state.get("goal_status") not in {"PAPER_READY", "ACCEPTED"}:
        raise ValueError("paper gate and goal status disagree")
    if state.get("goal_status") in {"PAPER_READY", "ACCEPTED"} and state.get("paper_gate") != "PASS":
        raise ValueError("completed paper state requires paper gate pass")
    if state.get("production_hot_path_permission") not in {True, False}:
        raise ValueError("production_hot_path_permission must be boolean")


def transition_candidate(
    state: Mapping[str, object], candidate: str, to_status: str, decision: str
) -> dict[str, object]:
    validate_state(state)
    if candidate not in ORDER:
        raise ValueError(f"unknown candidate {candidate}")
    changed = copy.deepcopy(dict(state))
    current = changed["candidates"][candidate]["status"]
    if to_status == "REJECTED":
        allowed = current in PIPELINE and current != "PAPER_GATE_PASS"
    else:
        allowed = current in PIPELINE and PIPELINE.index(current) + 1 < len(PIPELINE)
        allowed = allowed and PIPELINE[PIPELINE.index(current) + 1] == to_status
    if not allowed:
        raise ValueError(f"invalid transition {candidate}: {current} -> {to_status}")
    changed["candidates"][candidate]["status"] = to_status
    changed["last_decision"] = decision
    if to_status == "REJECTED":
        index = ORDER.index(candidate)
        if index + 1 == len(ORDER):
            changed["goal_status"] = "RESEARCH_CAMPAIGN_EXHAUSTED"
            changed["production_hot_path_permission"] = False
        else:
            next_candidate = ORDER[index + 1]
            changed["active_candidate"] = next_candidate
            changed["candidates"][next_candidate]["status"] = "INTAKE"
            changed["production_hot_path_permission"] = False
    elif to_status == "PAPER_GATE_PASS":
        changed["paper_gate"] = "PASS"
        changed["goal_status"] = "PAPER_READY"
    validate_state(changed)
    return changed


def write_state(path: Path, state: Mapping[str, object]) -> None:
    validate_state(state)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="ascii", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    transition = sub.add_parser("transition")
    transition.add_argument("candidate", choices=ORDER)
    transition.add_argument("to_status")
    transition.add_argument("--decision", required=True)
    args = parser.parse_args()
    state = load_state(args.state)
    if args.command == "validate":
        print("PASS_RESEARCH_STATE_VALID")
        return 0
    changed = transition_candidate(state, args.candidate, args.to_status, args.decision)
    write_state(args.state, changed)
    print(args.decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Add the concise active Goal and archive banners**

Create `docs/current_mat_sab_ccs_goal.md` with this content:

```markdown
# Current MAT-SAB CCS/USENIX Goal

The controlling contract is
`docs/superpowers/specs/2026-07-16-ccs-usenix-mat-sab-research-contract-design.md`.

The objective is a source-testable r-body MAT-RLWE SAB algorithm whose complete
bootstrapping latency per plaintext lane, `T_bootstrap/r`, beats both repeated
scalar SAB and the current exact-dense PVW/MAT-SAB baseline under the contract's
correctness, security-scope, noise, resource, statistical, literature, and
artifact gates.

The exact-dense implementation and its measured speedups remain a baseline,
not Goal completion. Candidate exploration is finite: A (Star-Cycle Sparse
MAT-GGSW), then B (Factorized Star-Cycle), then C (Rank-Bounded Shared-Mask
State). The active state and budgets are recorded in `research_state.yaml`.

No production hot-path change is allowed before the active candidate passes
the mechanism, key/security/noise, and Amdahl gates. Conference acceptance is
external; the repository-controlled success state is `PAPER_READY`.
```

Insert this banner before line 1 of both historical files:

```markdown
> Historical stage ledger. The active research contract is
> `docs/superpowers/specs/2026-07-16-ccs-usenix-mat-sab-research-contract-design.md`;
> the concise Goal is `docs/current_mat_sab_ccs_goal.md`; machine state is
> `research_state.yaml`. Do not append new automatic stages to this ledger.

```

- [ ] **Step 6: Run the tests and state validator**

Run:

```powershell
python -m unittest tests.research.test_research_state -v
python scripts/mat_sab_research_state.py validate
```

Expected: 5 tests report `OK`, followed by `PASS_RESEARCH_STATE_VALID`.

- [ ] **Step 7: Commit the state freeze**

```powershell
git add research_state.yaml scripts/mat_sab_research_state.py tests/research/test_research_state.py docs/current_mat_sab_ccs_goal.md docs/current_codex_goal_sab_completion.md docs/roadmap_stage19_plus.md
git commit -m "Freeze finite MAT-SAB research state"
```

Expected: one commit containing only the six listed paths.

---

### Task 2: Build The Source-Anchored Selector And State Techgraph

**Files:**
- Create: `scripts/build_mat_sab_selector_techgraph.py`
- Create: `tests/research/test_selector_techgraph.py`
- Create: `paper_techgraphs/2025_686_mat_sab_selector.yaml`
- Create: `paper_techgraphs/2025_686_mat_sab_selector_graph.md`
- Create: `paper_techgraphs/2025_686_mat_sab_selector_gaps.md`
- Modify: `research_state.yaml`

**Interfaces:**
- Consumes: repository root and the `research_state.yaml` transition CLI from Task 1.
- Produces: `build_graph(root: Path) -> dict[str, object]`
- Produces: `write_outputs(root: Path, graph: Mapping[str, object]) -> tuple[Path, Path, Path]`
- Produces: graph nodes `sab_schedule`, `pvw_phase`, `pvw_randomization`, `dense_keygen`, `dense_decompose`, `dense_addmul`, `compact_kernel`, `star_cycle_support`, `closure_failure`, and `distribution_blocker`.

- [ ] **Step 1: Write the failing techgraph tests**

Create `tests/research/test_selector_techgraph.py`:

```python
import json
import unittest
from pathlib import Path

from scripts.build_mat_sab_selector_techgraph import build_graph, write_outputs


ROOT = Path(__file__).resolve().parents[2]


class SelectorTechgraphTests(unittest.TestCase):
    def test_all_source_and_artifact_anchors_resolve(self):
        graph = build_graph(ROOT)
        self.assertTrue(all(node["anchor_status"] == "PASS" for node in graph["nodes"]))

    def test_required_mechanism_nodes_are_present(self):
        graph = build_graph(ROOT)
        node_ids = {node["id"] for node in graph["nodes"]}
        self.assertTrue({
            "sab_schedule", "pvw_phase", "pvw_randomization", "dense_keygen",
            "dense_decompose", "dense_addmul", "compact_kernel",
            "star_cycle_support", "closure_failure", "distribution_blocker",
        }.issubset(node_ids))

    def test_graph_records_the_production_code_boundary(self):
        graph = build_graph(ROOT)
        self.assertFalse(graph["production_code_permission"])
        self.assertIn("standard PVW randomization dimension", graph["open_gaps"])

    def test_outputs_are_json_valid_and_deterministic(self):
        graph = build_graph(ROOT)
        first = write_outputs(ROOT, graph)
        before = [path.read_bytes() for path in first]
        second = write_outputs(ROOT, graph)
        self.assertEqual(before, [path.read_bytes() for path in second])
        parsed = json.loads(first[0].read_text(encoding="ascii"))
        self.assertEqual(parsed["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the techgraph tests and verify the expected import failure**

Run:

```powershell
python -m unittest tests.research.test_selector_techgraph -v
```

Expected: `ERROR` with `ModuleNotFoundError: No module named 'scripts.build_mat_sab_selector_techgraph'`.

- [ ] **Step 3: Implement the techgraph builder**

Create `scripts/build_mat_sab_selector_techgraph.py` with these exact anchors and deterministic rendering rules:

```python
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
```

- [ ] **Step 4: Generate and inspect the techgraph**

Run:

```powershell
python scripts/build_mat_sab_selector_techgraph.py
python -m unittest tests.research.test_selector_techgraph -v
```

Expected: `PASS_CANDIDATE_A_TECHGRAPH_ANCHORED`; 4 tests report `OK`; every generated node has `anchor_status=PASS`.

- [ ] **Step 5: Record the guarded state transition**

Run:

```powershell
python scripts/mat_sab_research_state.py transition A TECHGRAPH_ANCHORED --decision CANDIDATE_A_TECHGRAPH_ANCHORED
python scripts/mat_sab_research_state.py validate
```

Expected: the transition decision, then `PASS_RESEARCH_STATE_VALID`; `production_hot_path_permission` remains `false`.

- [ ] **Step 6: Commit the source graph**

```powershell
git add scripts/build_mat_sab_selector_techgraph.py tests/research/test_selector_techgraph.py paper_techgraphs research_state.yaml
git commit -m "Anchor the MAT-SAB selector techgraph"
```

Expected: generated graph files and the single state transition are committed together.

---

### Task 3: Implement The PVW Selector Equation And Randomization Model

**Files:**
- Create: `research/__init__.py`
- Create: `research/mat_sab/__init__.py`
- Create: `research/mat_sab/finite_linear.py`
- Create: `research/mat_sab/star_cycle_model.py`
- Create: `tests/research/test_finite_linear.py`
- Create: `tests/research/test_star_cycle_model.py`
- Create: `theory_checks/candidate_a_star_cycle_production_equations.md`
- Modify: `research_state.yaml`

**Interfaces:**
- Produces: `AffineSolution`, `rref`, `rank`, and `solve_affine`.
- Produces: `SupportAnalysis`, `phase_matrix`, `kernel_vector`, `selector_from_kernel`, `dense_support`, `star_cycle_support`, `support_from_stage203`, `phase_constraints`, `analyze_support`, and `phase_residual`.
- Defines matrix orientation as `M[output_component][input_component]` with component 0 the shared mask and components 1 through r the body lanes.

- [ ] **Step 1: Write the failing modular-linear-algebra tests**

Create `tests/research/test_finite_linear.py`:

```python
import unittest

from research.mat_sab.finite_linear import rank, rref, solve_affine


class FiniteLinearTests(unittest.TestCase):
    def test_rref_and_rank_over_prime_field(self):
        reduced, pivots = rref([[1, 2, 3], [2, 4, 7]], 257)
        self.assertEqual(pivots, [0, 2])
        self.assertEqual(reduced, [[1, 2, 0], [0, 0, 1]])
        self.assertEqual(rank([[1, 2], [2, 4]], 257), 1)

    def test_affine_solution_reports_dimension_and_particular(self):
        solution = solve_affine([[1, 1, 0], [0, 1, 1]], [3, 5], 257)
        self.assertTrue(solution.consistent)
        self.assertEqual(solution.rank, 2)
        self.assertEqual(solution.dimension, 1)
        self.assertEqual(solution.particular, (255, 5, 0))

    def test_inconsistent_system_is_detected(self):
        solution = solve_affine([[1], [1]], [0, 1], 257)
        self.assertFalse(solution.consistent)
        self.assertEqual(solution.dimension, -1)
        self.assertEqual(solution.particular, ())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the linear tests and verify the expected import failure**

Run:

```powershell
python -m unittest tests.research.test_finite_linear -v
```

Expected: `ERROR` with `ModuleNotFoundError: No module named 'research.mat_sab'`.

- [ ] **Step 3: Implement the modular affine solver**

Create `research/__init__.py` containing `"""Research-only analysis package."""`
and `research/mat_sab/__init__.py` containing
`"""MAT-SAB algebra models."""`, then create
`research/mat_sab/finite_linear.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class AffineSolution:
    consistent: bool
    rank: int
    variables: int
    dimension: int
    particular: tuple[int, ...]


def mod_inv(value: int, modulus: int) -> int:
    value %= modulus
    if value == 0:
        raise ZeroDivisionError("zero has no modular inverse")
    return pow(value, -1, modulus)


def rref(matrix: Sequence[Sequence[int]], modulus: int) -> tuple[list[list[int]], list[int]]:
    if modulus <= 1:
        raise ValueError("modulus must exceed one")
    rows = [list(value % modulus for value in row) for row in matrix]
    if not rows:
        return [], []
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("ragged matrix")
    pivots: list[int] = []
    pivot_row = 0
    for column in range(width):
        selected = next((row for row in range(pivot_row, len(rows)) if rows[row][column]), None)
        if selected is None:
            continue
        rows[pivot_row], rows[selected] = rows[selected], rows[pivot_row]
        inverse = mod_inv(rows[pivot_row][column], modulus)
        rows[pivot_row] = [(value * inverse) % modulus for value in rows[pivot_row]]
        for row in range(len(rows)):
            if row == pivot_row or rows[row][column] == 0:
                continue
            factor = rows[row][column]
            rows[row] = [
                (value - factor * pivot) % modulus
                for value, pivot in zip(rows[row], rows[pivot_row])
            ]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == len(rows):
            break
    return rows, pivots


def rank(matrix: Sequence[Sequence[int]], modulus: int) -> int:
    return len(rref(matrix, modulus)[1])


def solve_affine(
    coefficients: Sequence[Sequence[int]], rhs: Sequence[int], modulus: int
) -> AffineSolution:
    if len(coefficients) != len(rhs):
        raise ValueError("coefficient and rhs row counts differ")
    if not coefficients:
        raise ValueError("at least one equation is required")
    variables = len(coefficients[0])
    if any(len(row) != variables for row in coefficients):
        raise ValueError("ragged coefficient matrix")
    augmented = [list(row) + [value] for row, value in zip(coefficients, rhs)]
    reduced, pivots = rref(augmented, modulus)
    inconsistent = any(
        all(value == 0 for value in row[:variables]) and row[variables] != 0
        for row in reduced
    )
    coefficient_pivots = [pivot for pivot in pivots if pivot < variables]
    if inconsistent:
        return AffineSolution(False, len(coefficient_pivots), variables, -1, ())
    particular = [0] * variables
    for row_index, pivot in enumerate(coefficient_pivots):
        particular[pivot] = reduced[row_index][variables]
    return AffineSolution(
        True,
        len(coefficient_pivots),
        variables,
        variables - len(coefficient_pivots),
        tuple(particular),
    )
```

- [ ] **Step 4: Run the linear tests and verify they pass**

Run:

```powershell
python -m unittest tests.research.test_finite_linear -v
```

Expected: 3 tests report `OK`.

- [ ] **Step 5: Write the failing PVW/star-cycle model tests**

Create `tests/research/test_star_cycle_model.py`:

```python
import unittest
from pathlib import Path

from research.mat_sab.star_cycle_model import (
    analyze_support,
    dense_support,
    matmul,
    phase_matrix,
    phase_residual,
    selector_from_kernel,
    star_cycle_support,
    support_from_stage203,
)


ROOT = Path(__file__).resolve().parents[2]
PRIME = 257
SECRETS = {
    2: (2, 3),
    4: (2, 3, 5, 7),
    6: (2, 3, 5, 7, 11, 13),
}


class StarCycleModelTests(unittest.TestCase):
    def test_dense_selector_has_one_randomizer_per_input_column(self):
        for r, secret in SECRETS.items():
            analysis = analyze_support(secret, 1, dense_support(r), PRIME)
            self.assertTrue(analysis.consistent)
            self.assertEqual(analysis.affine_dimension, r + 1)
            self.assertEqual(analysis.column_dimensions, (1,) * (r + 1))
            self.assertTrue(analysis.full_pvw_randomization)

    def test_kernel_construction_satisfies_phase_equation(self):
        secret = SECRETS[4]
        matrix = selector_from_kernel(secret, 7, (1, 2, 3, 4, 5), PRIME)
        self.assertEqual(phase_residual(secret, matrix, 7, PRIME), [[0] * 5 for _ in range(4)])
        self.assertEqual(len(matmul(phase_matrix(secret, PRIME), matrix, PRIME)), 4)

    def test_star_cycle_support_matches_stage203_and_has_4r_terms(self):
        path = ROOT / "repro/stage203_production_selector_equation_probe/equation_map.csv"
        for r in SECRETS:
            expected = star_cycle_support(r)
            self.assertEqual(len(expected), 4 * r)
            self.assertEqual(support_from_stage203(path, r), expected)
            self.assertEqual((r + 1) ** 2 - len(expected), (r - 1) ** 2)

    def test_star_cycle_loses_standard_pvw_randomization(self):
        expected_dimensions = {
            2: (0, 1, 1),
            4: (0, 0, 0, 0, 0),
            6: (0, 0, 0, 0, 0, 0, 0),
        }
        for r, secret in SECRETS.items():
            for mu in (0, 1):
                analysis = analyze_support(secret, mu, star_cycle_support(r), PRIME)
                self.assertTrue(analysis.consistent)
                self.assertEqual(analysis.column_dimensions, expected_dimensions[r])
                self.assertFalse(analysis.full_pvw_randomization)
                self.assertEqual(
                    phase_residual(secret, analysis.particular_matrix, mu, PRIME),
                    [[0] * (r + 1) for _ in range(r)],
                )

    def test_generic_dense_randomizer_is_not_star_representable(self):
        secret = SECRETS[4]
        matrix = selector_from_kernel(secret, 1, (1, 2, 3, 4, 5), PRIME)
        outside = [
            matrix[row][column]
            for row in range(5)
            for column in range(5)
            if (row, column) not in star_cycle_support(4)
        ]
        self.assertTrue(all(value != 0 for value in outside))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: Run the model tests and verify the expected import failure**

Run:

```powershell
python -m unittest tests.research.test_star_cycle_model -v
```

Expected: `ERROR` with `ModuleNotFoundError: No module named 'research.mat_sab.star_cycle_model'`.

- [ ] **Step 7: Implement the PVW selector model**

Create `research/mat_sab/star_cycle_model.py`:

```python
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .finite_linear import rank, solve_affine


Matrix = list[list[int]]
Support = frozenset[tuple[int, int]]


@dataclass(frozen=True)
class SupportAnalysis:
    r: int
    modulus: int
    support_size: int
    consistent: bool
    affine_dimension: int
    column_dimensions: tuple[int, ...]
    full_pvw_randomization: bool
    particular_matrix: tuple[tuple[int, ...], ...]


def phase_matrix(secret: Sequence[int], modulus: int) -> Matrix:
    r = len(secret)
    matrix = [[0] * (r + 1) for _ in range(r)]
    for lane, value in enumerate(secret):
        matrix[lane][0] = (-value) % modulus
        matrix[lane][lane + 1] = 1
    return matrix


def kernel_vector(secret: Sequence[int], modulus: int) -> list[int]:
    return [1] + [value % modulus for value in secret]


def identity(size: int) -> Matrix:
    return [[1 if row == column else 0 for column in range(size)] for row in range(size)]


def outer(left: Sequence[int], right: Sequence[int], modulus: int) -> Matrix:
    return [[(a * b) % modulus for b in right] for a in left]


def matmul(left: Sequence[Sequence[int]], right: Sequence[Sequence[int]], modulus: int) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise ValueError("incompatible matrix dimensions")
    return [
        [
            sum(left[row][inner] * right[inner][column] for inner in range(len(right))) % modulus
            for column in range(len(right[0]))
        ]
        for row in range(len(left))
    ]


def selector_from_kernel(
    secret: Sequence[int], mu: int, weights: Sequence[int], modulus: int
) -> Matrix:
    size = len(secret) + 1
    if len(weights) != size:
        raise ValueError("one randomization weight is required per input column")
    base = identity(size)
    randomizer = outer(kernel_vector(secret, modulus), weights, modulus)
    return [
        [((mu * base[row][column]) + randomizer[row][column]) % modulus for column in range(size)]
        for row in range(size)
    ]


def dense_support(r: int) -> Support:
    return frozenset((row, column) for row in range(r + 1) for column in range(r + 1))


def star_cycle_support(r: int) -> Support:
    support: set[tuple[int, int]] = set()
    for body in range(1, r + 1):
        support.add((0, body))
        support.add((body, 0))
        support.add((body, body))
        support.add((body, 1 + (body % r)))
    return frozenset(support)


def support_from_stage203(path: Path, r: int) -> Support:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = csv.DictReader(handle)
        return frozenset(
            (int(row["row"]), int(row["col"]))
            for row in rows
            if int(row["r"]) == r and row["semantic_role"] == "active"
        )


def phase_constraints(
    secret: Sequence[int], mu: int, support: Iterable[tuple[int, int]], modulus: int
) -> tuple[Matrix, list[int], tuple[tuple[int, int], ...]]:
    p_matrix = phase_matrix(secret, modulus)
    index = tuple(sorted(set(support)))
    size = len(secret) + 1
    coefficients: Matrix = []
    rhs: list[int] = []
    for phase_row in range(len(secret)):
        for input_column in range(size):
            equation = [0] * len(index)
            for variable, (output_row, column) in enumerate(index):
                if column == input_column:
                    equation[variable] = p_matrix[phase_row][output_row]
            coefficients.append(equation)
            rhs.append((mu * p_matrix[phase_row][input_column]) % modulus)
    return coefficients, rhs, index


def _matrix_from_vector(
    values: Sequence[int], index: Sequence[tuple[int, int]], size: int
) -> tuple[tuple[int, ...], ...]:
    matrix = [[0] * size for _ in range(size)]
    for value, (row, column) in zip(values, index):
        matrix[row][column] = value
    return tuple(tuple(row) for row in matrix)


def _column_dimensions(
    secret: Sequence[int], support: Support, modulus: int
) -> tuple[int, ...]:
    p_matrix = phase_matrix(secret, modulus)
    dimensions: list[int] = []
    for column in range(len(secret) + 1):
        outputs = sorted(row for row, input_column in support if input_column == column)
        restricted = [[phase_row[row] for row in outputs] for phase_row in p_matrix]
        dimensions.append(len(outputs) - rank(restricted, modulus))
    return tuple(dimensions)


def analyze_support(
    secret: Sequence[int], mu: int, support: Support, modulus: int
) -> SupportAnalysis:
    coefficients, rhs, index = phase_constraints(secret, mu, support, modulus)
    solution = solve_affine(coefficients, rhs, modulus)
    dimensions = _column_dimensions(secret, support, modulus)
    size = len(secret) + 1
    matrix = _matrix_from_vector(solution.particular, index, size) if solution.consistent else tuple()
    return SupportAnalysis(
        r=len(secret),
        modulus=modulus,
        support_size=len(support),
        consistent=solution.consistent,
        affine_dimension=solution.dimension,
        column_dimensions=dimensions,
        full_pvw_randomization=solution.consistent and all(value >= 1 for value in dimensions),
        particular_matrix=matrix,
    )


def phase_residual(
    secret: Sequence[int], matrix: Sequence[Sequence[int]], mu: int, modulus: int
) -> Matrix:
    p_matrix = phase_matrix(secret, modulus)
    actual = matmul(p_matrix, matrix, modulus)
    expected = [[(mu * value) % modulus for value in row] for row in p_matrix]
    return [
        [(actual[row][column] - expected[row][column]) % modulus for column in range(len(expected[0]))]
        for row in range(len(expected))
    ]
```

- [ ] **Step 8: Run all algebra tests**

Run:

```powershell
python -m unittest tests.research.test_finite_linear tests.research.test_star_cycle_model -v
```

Expected: 8 tests report `OK`. Dense support has affine dimension `r+1`; the Stage203 support is phase-consistent for `mu=0/1` but lacks one standard PVW randomizer in every input column.

- [ ] **Step 9: Write the formal production-equation derivation**

Create `theory_checks/candidate_a_star_cycle_production_equations.md` with the following derivation and no security overclaim:

```markdown
# Candidate A Star-Cycle Production Equations

## Orientation And Phase Map

For k=1 and r bodies, order a PVW ciphertext as
`x=(a,b_0,...,b_(r-1))`. Let `s=(s_0,...,s_(r-1))`. The r phases are

```text
P x, where P = [-s | I_r].
```

A selector that multiplies every phase by `mu` must satisfy

```text
P M = mu P.
```

Rows of `M` are output components and columns are decomposed input components.
The current dense MAT external product samples one PVW ciphertext per gadget
column and evaluates every selector-column/output-row pair.

## Standard PVW Key Distribution

For each decomposed input column `c`, standard PVW sampling chooses a fresh
shared mask coordinate `w_c` and publishes the component vector

```text
mu e_c + w_c (1,s_0,...,s_(r-1))^T + phase-error terms.
```

The mask coordinate and all r matching body corrections are part of one PVW
ciphertext sample. The public shape is independent of the selector value, and
the dense key contains one such sample for each gadget level and input column.
The exact ring distribution and error law are inherited from
`pvmtmlwe_sample`; this gate models only its component-level kernel direction.

## Unrestricted Solution

`ker(P)` is generated by `v=(1,s_0,...,s_(r-1))^T`. Therefore every solution
over a field has the form

```text
M = mu I_(r+1) + v w^T,
```

where `w` has one free coordinate per input column. This gives affine
dimension `r+1`. The `v w^T` term is exactly the algebraic direction created
by a shared random mask together with its r body corrections in
`pvmtmlwe_sample`.

## Stage203 Star-Cycle Constraint

The declared support is

```text
{(0,j),(j,0),(j,j),(j,1+(j mod r)) : j in [1,r]}.
```

It has `4r` entries. For the mask-input column 0, row `(0,0)` is absent, so
the coefficient of the kernel direction is fixed and no randomizer remains.
For a body-input column and r at least 3, any omitted body row with nonzero
secret coefficient forces that column's kernel coefficient to zero. Thus the
direct sparse representation can satisfy the phase equation while losing the
standard PVW randomization degree. For r=2, body columns retain a degree, but
the mask-input column still has none.

Restoring an unrestricted standard-PVW randomizer for a column requires the
support of the complete kernel vector `(1,s_0,...,s_(r-1))`. With nonzero
secret components this means all r+1 output positions for that column. Doing
so for every input column reconstructs dense `(r+1)^2` support, so an O(r)
public-support revision cannot preserve the standard distribution merely by
adding a small number of direct entries. A factorized realization with dense-
looking standard encrypted operators is a different representation and is
therefore evaluated as Candidate B.

## Scope

The executable checker validates these linear claims for deterministic prime
fields and r=2/4/6, and the derivation identifies the general kernel argument.
This is a mechanism/key-format preflight, not a proof of RLWE security, a noise
bound, or a complete-SAB speedup. If the standard-PVW randomization gate fails,
the direct sparse Candidate A route is rejected and the campaign moves to
Candidate B, which may realize the same semantic operator through factorized
standard encrypted operators without publishing sparse ciphertext support.
```

- [ ] **Step 10: Record `EQUATIONS_DEFINED` without granting code permission**

Run:

```powershell
python scripts/mat_sab_research_state.py transition A EQUATIONS_DEFINED --decision CANDIDATE_A_PRODUCTION_EQUATIONS_DEFINED
python scripts/mat_sab_research_state.py validate
```

Expected: the state advances by one gate and `production_hot_path_permission` remains `false`.

- [ ] **Step 11: Commit the equation model**

```powershell
git add research tests/research/test_finite_linear.py tests/research/test_star_cycle_model.py theory_checks/candidate_a_star_cycle_production_equations.md research_state.yaml
git commit -m "Model Candidate A selector randomization"
```

Expected: the reusable algebra package, tests, derivation, and guarded state transition form one reviewable commit.

---

### Task 4: Execute The Adversarial Candidate A Mechanism Gate

**Files:**
- Create: `scripts/run_candidate_a_star_cycle_gate.py`
- Create: `tests/research/test_candidate_a_gate.py`
- Create: `algorithm_variants/candidate_a_star_cycle_sparse_mat_ggsw.md`
- Create: `experiments/candidate_a_star_cycle_gate_plan.md`
- Create: `docs/candidate_a_star_cycle_mechanism_gate.md`
- Create: `repro/candidate_a_star_cycle_gate/summary.csv`
- Create: `repro/candidate_a_star_cycle_gate/phase_constraints.csv`
- Create: `repro/candidate_a_star_cycle_gate/randomization_dimension.csv`
- Create: `repro/candidate_a_star_cycle_gate/negative_controls.csv`
- Create: `repro/candidate_a_star_cycle_gate/source_mapping.csv`
- Create: `repro/candidate_a_star_cycle_gate/proof_gate.csv`
- Create: `repro/candidate_a_star_cycle_gate/artifact_index.csv`
- Create: `repro/candidate_a_star_cycle_gate/reproduction_commands.md`

**Interfaces:**
- Consumes: the Task 3 model and Stage203 equation map.
- Produces: `evaluate_candidate_a(root: Path) -> GateResult`.
- Produces: `write_gate_artifacts(root: Path, result: GateResult) -> tuple[Path, ...]`.
- Produces exactly one computed decision: `ADMIT_CANDIDATE_A_REVISION_OR_KEYGEN_PREFLIGHT` or `REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B`.
- Does not read or modify `research_state.yaml`; Task 5 owns decision application.

- [ ] **Step 1: Write the failing gate tests**

Create `tests/research/test_candidate_a_gate.py`:

```python
import unittest
from pathlib import Path

from scripts.run_candidate_a_star_cycle_gate import (
    REJECT,
    evaluate_candidate_a,
    write_gate_artifacts,
)


ROOT = Path(__file__).resolve().parents[2]


class CandidateAGateTests(unittest.TestCase):
    def test_current_stage203_support_is_rejected_by_standard_pvw_gate(self):
        result = evaluate_candidate_a(ROOT)
        self.assertEqual(result.decision, REJECT)
        self.assertTrue(result.support_gate)
        self.assertTrue(result.phase_gate)
        self.assertTrue(result.dense_control_gate)
        self.assertTrue(result.negative_control_gate)
        self.assertFalse(result.randomization_gate)
        self.assertFalse(result.production_code_permission)

    def test_r2_r4_r6_and_zero_one_semantics_are_covered(self):
        result = evaluate_candidate_a(ROOT)
        self.assertEqual(
            {(row["r"], row["mu"]) for row in result.phase_rows},
            {(r, mu) for r in (2, 4, 6) for mu in (0, 1)},
        )
        self.assertTrue(all(row["phase_status"] == "PASS" for row in result.phase_rows))

    def test_dense_control_keeps_one_randomizer_per_column(self):
        result = evaluate_candidate_a(ROOT)
        dense = [row for row in result.randomization_rows if row["support"] == "dense"]
        self.assertTrue(all(row["full_pvw_randomization"] == "PASS" for row in dense))

    def test_generated_artifacts_are_idempotent(self):
        result = evaluate_candidate_a(ROOT)
        first = write_gate_artifacts(ROOT, result)
        before = {path: path.read_bytes() for path in first}
        second = write_gate_artifacts(ROOT, result)
        self.assertEqual(before, {path: path.read_bytes() for path in second})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the gate tests and verify the expected import failure**

Run:

```powershell
python -m unittest tests.research.test_candidate_a_gate -v
```

Expected: `ERROR` with `ModuleNotFoundError: No module named 'scripts.run_candidate_a_star_cycle_gate'`.

- [ ] **Step 3: Implement the computed gate and CSV evidence**

Create `scripts/run_candidate_a_star_cycle_gate.py`. Use the following complete data model and evaluation logic; rendering helpers must preserve the listed CSV field order:

````python
#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.mat_sab.star_cycle_model import (
    analyze_support,
    dense_support,
    phase_residual,
    selector_from_kernel,
    star_cycle_support,
    support_from_stage203,
)


OUT = Path("repro/candidate_a_star_cycle_gate")
ADMIT = "ADMIT_CANDIDATE_A_REVISION_OR_KEYGEN_PREFLIGHT"
REJECT = "REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B"
PRIME = 257
SECRETS = {
    2: (2, 3),
    4: (2, 3, 5, 7),
    6: (2, 3, 5, 7, 11, 13),
}


@dataclass(frozen=True)
class GateResult:
    decision: str
    support_gate: bool
    phase_gate: bool
    dense_control_gate: bool
    negative_control_gate: bool
    randomization_gate: bool
    production_code_permission: bool
    phase_rows: tuple[dict[str, object], ...]
    randomization_rows: tuple[dict[str, object], ...]
    negative_rows: tuple[dict[str, object], ...]
    source_rows: tuple[dict[str, object], ...]


def _zero_count(matrix: Iterable[Iterable[int]]) -> int:
    return sum(value != 0 for row in matrix for value in row)


def evaluate_candidate_a(root: Path = ROOT) -> GateResult:
    stage203 = root / "repro/stage203_production_selector_equation_probe/equation_map.csv"
    phase_rows: list[dict[str, object]] = []
    randomization_rows: list[dict[str, object]] = []
    negative_rows: list[dict[str, object]] = []
    support_gate = True
    phase_gate = True
    dense_control_gate = True
    randomization_gate = True
    removal_outcomes: dict[int, set[str]] = {r: set() for r in SECRETS}

    for r, secret in SECRETS.items():
        star = star_cycle_support(r)
        declared = support_from_stage203(stage203, r)
        support_match = star == declared and len(star) == 4 * r
        support_gate &= support_match
        for mu in (0, 1):
            analysis = analyze_support(secret, mu, star, PRIME)
            residual_count = _zero_count(
                phase_residual(secret, analysis.particular_matrix, mu, PRIME)
            ) if analysis.consistent else -1
            passed = analysis.consistent and residual_count == 0
            phase_gate &= passed
            phase_rows.append({
                "r": r,
                "mu": mu,
                "prime": PRIME,
                "support_terms": len(star),
                "stage203_match": "PASS" if support_match else "FAIL",
                "consistent": "PASS" if analysis.consistent else "FAIL",
                "affine_dimension": analysis.affine_dimension,
                "residual_nonzero": residual_count,
                "phase_status": "PASS" if passed else "FAIL",
            })

        star_analysis = analyze_support(secret, 1, star, PRIME)
        dense_analysis = analyze_support(secret, 1, dense_support(r), PRIME)
        randomization_gate &= star_analysis.full_pvw_randomization
        dense_control_gate &= dense_analysis.full_pvw_randomization
        for name, analysis in (("star_cycle", star_analysis), ("dense", dense_analysis)):
            randomization_rows.append({
                "r": r,
                "support": name,
                "support_terms": analysis.support_size,
                "affine_dimension": analysis.affine_dimension,
                "column_dimensions": ";".join(str(value) for value in analysis.column_dimensions),
                "full_pvw_randomization": "PASS" if analysis.full_pvw_randomization else "FAIL",
            })

        generic = selector_from_kernel(secret, 1, tuple(range(1, r + 2)), PRIME)
        outside_nonzero = sum(
            generic[row][column] != 0
            for row in range(r + 1)
            for column in range(r + 1)
            if (row, column) not in star
        )
        negative_rows.append({
            "r": r,
            "control": "generic_dense_randomizer_outside_star",
            "observed": outside_nonzero,
            "expected": ">0",
            "status": "PASS" if outside_nonzero > 0 else "FAIL",
        })
        for removed in sorted(star):
            reduced = analyze_support(secret, 1, frozenset(star - {removed}), PRIME)
            observed = "consistent" if reduced.consistent else "inconsistent"
            removal_outcomes[r].add(observed)
            negative_rows.append({
                "r": r,
                "control": f"remove_{removed[0]}_{removed[1]}",
                "observed": observed,
                "expected": "coverage_contains_consistent_and_inconsistent",
                "status": "PASS",
            })

    source_specs = (
        ("phase_map", "src/mosfhet/src/pvwtmlwe.c", "void pvmtmlwe_phase("),
        ("pvw_randomization", "src/mosfhet/src/pvwtmlwe.c", "void pvmtmlwe_sample("),
        ("dense_keygen", "src/mosfhet/src/mattrgsw.c", "void mat_trgsw_monomial_sample("),
        ("dense_evaluator", "src/mosfhet/src/mattrgsw.c", "static void mat_trgsw_mul_pvmtmlwe_DFT_from_dec("),
        ("star_support", "repro/stage203_production_selector_equation_probe/equation_map.csv", "lane_neighbor_body_interaction"),
    )
    source_rows = []
    for claim, relative, token in source_specs:
        path = root / relative
        present = path.is_file() and token in path.read_text(encoding="utf-8", errors="replace")
        source_rows.append({
            "claim": claim,
            "path": relative,
            "token": token,
            "status": "PASS" if present else "FAIL",
        })
    source_gate = all(row["status"] == "PASS" for row in source_rows)
    support_gate &= source_gate
    generic_rows = [
        row for row in negative_rows
        if row["control"] == "generic_dense_randomizer_outside_star"
    ]
    generic_gate = len(generic_rows) == len(SECRETS) and all(
        row["status"] == "PASS"
        for row in generic_rows
    )
    negative_gate = generic_gate and all(
        outcomes == {"consistent", "inconsistent"}
        for outcomes in removal_outcomes.values()
    )
    admitted = support_gate and phase_gate and dense_control_gate and negative_gate and randomization_gate
    return GateResult(
        decision=ADMIT if admitted else REJECT,
        support_gate=support_gate,
        phase_gate=phase_gate,
        dense_control_gate=dense_control_gate,
        negative_control_gate=negative_gate,
        randomization_gate=randomization_gate,
        production_code_permission=False,
        phase_rows=tuple(phase_rows),
        randomization_rows=tuple(randomization_rows),
        negative_rows=tuple(negative_rows),
        source_rows=tuple(source_rows),
    )


def _write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="ascii", newline="\n")


def write_gate_artifacts(root: Path, result: GateResult) -> tuple[Path, ...]:
    out = root / OUT
    out.mkdir(parents=True, exist_ok=True)
    summary = out / "summary.csv"
    phase = out / "phase_constraints.csv"
    randomization = out / "randomization_dimension.csv"
    negative = out / "negative_controls.csv"
    source = out / "source_mapping.csv"
    proof = out / "proof_gate.csv"
    commands = out / "reproduction_commands.md"
    report = root / "docs/candidate_a_star_cycle_mechanism_gate.md"
    variant = root / "algorithm_variants/candidate_a_star_cycle_sparse_mat_ggsw.md"
    experiment = root / "experiments/candidate_a_star_cycle_gate_plan.md"
    index = out / "artifact_index.csv"

    _write_csv(summary, [{
        "decision": result.decision,
        "support_gate": "PASS" if result.support_gate else "FAIL",
        "phase_gate": "PASS" if result.phase_gate else "FAIL",
        "dense_control_gate": "PASS" if result.dense_control_gate else "FAIL",
        "negative_control_gate": "PASS" if result.negative_control_gate else "FAIL",
        "standard_pvw_randomization_gate": "PASS" if result.randomization_gate else "FAIL",
        "production_code_permission": "yes" if result.production_code_permission else "no",
        "route": "candidate_a_keygen_preflight" if result.decision == ADMIT else "candidate_b_factorized_star_cycle",
    }], [
        "decision", "support_gate", "phase_gate", "dense_control_gate", "negative_control_gate",
        "standard_pvw_randomization_gate", "production_code_permission", "route",
    ])
    _write_csv(phase, result.phase_rows, [
        "r", "mu", "prime", "support_terms", "stage203_match", "consistent",
        "affine_dimension", "residual_nonzero", "phase_status",
    ])
    _write_csv(randomization, result.randomization_rows, [
        "r", "support", "support_terms", "affine_dimension", "column_dimensions",
        "full_pvw_randomization",
    ])
    _write_csv(negative, result.negative_rows, ["r", "control", "observed", "expected", "status"])
    _write_csv(source, result.source_rows, ["claim", "path", "token", "status"])
    gates = (
        ("source_and_support", result.support_gate, "Stage203 equals the 4r star-cycle support"),
        ("phase_zero_one", result.phase_gate, "P M = mu P for r=2/4/6 and mu=0/1"),
        ("dense_control", result.dense_control_gate, "dense support retains one PVW kernel degree per column"),
        ("negative_controls", result.negative_control_gate, "generic dense and omitted-term controls cover expected failure modes"),
        ("standard_pvw_randomization", result.randomization_gate, "star support retains one PVW kernel degree per column"),
        ("production_code", result.production_code_permission, "later security/noise/Amdahl gates are required"),
    )
    _write_csv(proof, ({
        "gate": name,
        "status": "PASS" if passed else "FAIL",
        "interpretation": interpretation,
    } for name, passed, interpretation in gates), ["gate", "status", "interpretation"])
    _write_text(commands, """# Candidate A Star-Cycle Gate Reproduction

```powershell
python -m unittest discover -s tests/research -p \"test_*.py\" -v
python scripts/run_candidate_a_star_cycle_gate.py
```

This command performs no SAB hot-path modification and makes no security or
complete-SAB performance claim.
""")
    body = f"""# Candidate A Star-Cycle Mechanism Gate

Decision: `{result.decision}`.

The Stage203 `4r` support satisfies sampled zero/one phase equations, while
the standard PVW randomization gate is `{'PASS' if result.randomization_gate else 'FAIL'}`.
Dense support is the positive control. Production code permission remains
`false`; finite-field linear algebra is not an RLWE security proof.

Failure of the direct sparse standard-PVW representation routes the finite
campaign to Candidate B, Factorized Star-Cycle. Existing scalar and exact-dense
SAB paths are unchanged.
"""
    _write_text(report, body)
    _write_text(variant, f"""# Candidate A: Star-Cycle Sparse MAT-GGSW

- Decision: `{result.decision}`
- Semantic target: `P M = mu P`
- Declared work: `4r` selector-output terms
- Dense baseline work: `(r+1)^2` terms
- Production code permission: `false`
- Security scope: no claim from the finite checker
- Next route: `{'Candidate A key/security/noise preflight' if result.decision == ADMIT else 'Candidate B factorized realization'}`
""")
    _write_text(experiment, """# Candidate A Star-Cycle Gate Registration

- Field: prime 257
- Lane counts: r=2, r=4, r=6
- Selector semantics: mu=0 and mu=1
- Secrets: deterministic nonzero vectors registered in the gate source
- Positive control: unrestricted dense support
- Negative control: generic dense kernel randomizer outside star support
- Primary gate: at least one kernel-randomization degree per input column
- Failure action: reject the direct sparse standard-PVW route and activate B
- C hot-path changes: prohibited
""")

    indexed = [summary, phase, randomization, negative, source, proof, commands, report, variant, experiment]
    index_rows = []
    for path in indexed:
        data = path.read_bytes()
        index_rows.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    _write_csv(index, index_rows, ["path", "bytes", "sha256"])
    return tuple(indexed + [index])


def main() -> int:
    result = evaluate_candidate_a(ROOT)
    write_gate_artifacts(ROOT, result)
    print(result.decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
````

- [ ] **Step 4: Run the gate and inspect the computed result**

Run:

```powershell
python scripts/run_candidate_a_star_cycle_gate.py
python -m unittest tests.research.test_candidate_a_gate -v
```

Expected for the current Stage203 support: `REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B`; 4 tests report `OK`; phase, dense, and negative controls pass; star-cycle standard-PVW randomization fails; production code permission is `no`.

- [ ] **Step 5: Verify that the result is diagnostic rather than hard-coded**

Run:

```powershell
rg -n "admitted = support_gate and phase_gate and dense_control_gate and negative_gate and randomization_gate" scripts/run_candidate_a_star_cycle_gate.py
Import-Csv repro/candidate_a_star_cycle_gate/randomization_dimension.csv | Format-Table
Import-Csv repro/candidate_a_star_cycle_gate/proof_gate.csv | Format-Table
```

Expected: one decision expression is shown; dense rows report `PASS`; star-cycle rows report `FAIL`; the proof table separates phase, randomization, and production-code gates.

- [ ] **Step 6: Commit the isolated mechanism gate**

```powershell
git add scripts/run_candidate_a_star_cycle_gate.py tests/research/test_candidate_a_gate.py docs/candidate_a_star_cycle_mechanism_gate.md theory_checks/candidate_a_star_cycle_production_equations.md algorithm_variants/candidate_a_star_cycle_sparse_mat_ggsw.md experiments/candidate_a_star_cycle_gate_plan.md repro/candidate_a_star_cycle_gate
git commit -m "Execute Candidate A star-cycle mechanism gate"
python scripts/run_candidate_a_star_cycle_gate.py
git status --short
```

Expected: the rerun prints the same computed decision and `git status --short` is empty, proving generator idempotence at the committed state.

---

### Task 5: Apply The Decision And Close The Reproducibility Loop

**Files:**
- Create: `scripts/apply_mat_sab_candidate_gate.py`
- Create: `tests/research/test_candidate_a_closeout.py`
- Modify: `research_state.yaml`
- Modify: `hypotheses/hypothesis_register.yaml`
- Modify: `repro/run_log.csv`
- Modify: `repro/artifact_manifest.md`
- Modify: `repro/reproduction_checklist.md`

**Interfaces:**
- Consumes: `repro/candidate_a_star_cycle_gate/summary.csv` and Task 1 state functions.
- Produces: `apply_gate(root: Path, state_path: Path, summary_path: Path) -> str`.
- On current evidence, transitions A from `EQUATIONS_DEFINED` to `REJECTED`, activates B at `INTAKE`, and leaves the overall Goal `ACTIVE`.
- If future evidence computes the admit decision, transitions A only to `ADVERSARIAL_CHECKER_PASS`; it still does not grant production hot-path permission.

- [ ] **Step 1: Write the failing closeout tests**

Create `tests/research/test_candidate_a_closeout.py`:

```python
import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.apply_mat_sab_candidate_gate import apply_gate
from scripts.run_candidate_a_star_cycle_gate import REJECT


ROOT = Path(__file__).resolve().parents[2]


class CandidateACloseoutTests(unittest.TestCase):
    def test_reject_decision_activates_b_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "hypotheses").mkdir()
            (root / "repro").mkdir()
            state = json.loads((ROOT / "research_state.yaml").read_text(encoding="ascii"))
            state["goal_status"] = "ACTIVE"
            state["paper_gate"] = "BLOCKED"
            state["production_hot_path_permission"] = False
            state["active_candidate"] = "A"
            state["candidates"]["A"]["status"] = "EQUATIONS_DEFINED"
            state["candidates"]["B"]["status"] = "QUEUED"
            state["candidates"]["C"]["status"] = "QUEUED"
            state_path = root / "research_state.yaml"
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="ascii")
            summary = root / "summary.csv"
            with summary.open("w", newline="", encoding="ascii") as handle:
                writer = csv.DictWriter(handle, fieldnames=["decision"])
                writer.writeheader()
                writer.writerow({"decision": REJECT})
            (root / "repro/run_log.csv").write_text(
                "run_id,date,commit_or_state,stage,backend,command,params,seed,status,summary,artifacts\n",
                encoding="ascii",
            )
            first = apply_gate(root, state_path, summary)
            second = apply_gate(root, state_path, summary)
            changed = json.loads(state_path.read_text(encoding="ascii"))
            self.assertEqual(first, REJECT)
            self.assertEqual(second, REJECT)
            self.assertEqual(changed["candidates"]["A"]["status"], "REJECTED")
            self.assertEqual(changed["candidates"]["B"]["status"], "INTAKE")
            self.assertEqual(changed["active_candidate"], "B")
            self.assertEqual(changed["goal_status"], "ACTIVE")
            self.assertFalse(changed["production_hot_path_permission"])
            self.assertEqual((root / "hypotheses/hypothesis_register.yaml").read_text().count("H_candidate_a_star_cycle_mechanism:"), 1)
            self.assertEqual((root / "repro/run_log.csv").read_text().count("candidate-a-star-cycle-gate-001"), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the closeout test and verify the expected import failure**

Run:

```powershell
python -m unittest tests.research.test_candidate_a_closeout -v
```

Expected: `ERROR` with `ModuleNotFoundError: No module named 'scripts.apply_mat_sab_candidate_gate'`.

- [ ] **Step 3: Implement idempotent state and evidence closeout**

Create `scripts/apply_mat_sab_candidate_gate.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mat_sab_research_state import load_state, transition_candidate, write_state
from scripts.run_candidate_a_star_cycle_gate import ADMIT, REJECT


def _append_once(path: Path, marker: str, content: str) -> None:
    current = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    separator = "" if not current or current.endswith("\n") else "\n"
    path.write_text(current + separator + content.rstrip() + "\n", encoding="utf-8", newline="\n")


def _decision(summary_path: Path) -> str:
    with summary_path.open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1 or rows[0].get("decision") not in {ADMIT, REJECT}:
        raise ValueError("summary must contain one recognized decision")
    return rows[0]["decision"]


def _append_run(root: Path, decision: str) -> None:
    path = root / "repro/run_log.csv"
    marker = "candidate-a-star-cycle-gate-001"
    if path.exists() and marker in path.read_text(encoding="utf-8", errors="replace"):
        return
    with path.open(newline="", encoding="utf-8-sig") as handle:
        fields = list(csv.DictReader(handle).fieldnames or [])
    row = {
        "run_id": marker,
        "date": "2026-07-17",
        "commit_or_state": "candidate-a-mechanism-gate",
        "stage": "Candidate A mechanism gate",
        "backend": "finite-field-standard-library",
        "command": "python scripts/run_candidate_a_star_cycle_gate.py",
        "params": "r=2/4/6; mu=0/1; prime=257",
        "seed": "deterministic",
        "status": decision,
        "summary": "Phase equations pass; standard PVW randomization decides the A-to-B route.",
        "artifacts": "repro/candidate_a_star_cycle_gate/",
    }
    with path.open("a", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writerow({field: row.get(field, "") for field in fields})


def apply_gate(root: Path, state_path: Path, summary_path: Path) -> str:
    decision = _decision(summary_path)
    state = load_state(state_path)
    current = state["candidates"]["A"]["status"]
    if current == "EQUATIONS_DEFINED":
        target = "ADVERSARIAL_CHECKER_PASS" if decision == ADMIT else "REJECTED"
        state = transition_candidate(state, "A", target, decision)
        write_state(state_path, state)
    elif decision == ADMIT and current != "ADVERSARIAL_CHECKER_PASS":
        raise ValueError(f"state/decision mismatch: {current} and {decision}")
    elif decision == REJECT and current != "REJECTED":
        raise ValueError(f"state/decision mismatch: {current} and {decision}")

    _append_once(
        root / "hypotheses/hypothesis_register.yaml",
        "H_candidate_a_star_cycle_mechanism:",
        f"""H_candidate_a_star_cycle_mechanism:
  status: {decision}
  primary_metric: mechanism_preflight_for_complete_sab_T_bootstrap_over_r
  evidence:
    - repro/candidate_a_star_cycle_gate/summary.csv
    - repro/candidate_a_star_cycle_gate/phase_constraints.csv
    - repro/candidate_a_star_cycle_gate/randomization_dimension.csv
    - theory_checks/candidate_a_star_cycle_production_equations.md
  conclusion: >
    Candidate A is decided by the source-anchored phase and standard-PVW
    randomization gate. No finite-checker security or performance claim is made.
""",
    )
    _append_once(
        root / "repro/artifact_manifest.md",
        "<!-- candidate-a-star-cycle-gate-manifest -->",
        """<!-- candidate-a-star-cycle-gate-manifest -->
- candidate_a_star_cycle_gate:
  - `research/mat_sab/`
  - `theory_checks/candidate_a_star_cycle_production_equations.md`
  - `docs/candidate_a_star_cycle_mechanism_gate.md`
  - `repro/candidate_a_star_cycle_gate/`
""",
    )
    _append_once(
        root / "repro/reproduction_checklist.md",
        "<!-- candidate-a-star-cycle-gate-checklist -->",
        f"""<!-- candidate-a-star-cycle-gate-checklist -->
- [x] Candidate A records `{decision}` from source, phase, dense-control, and
  standard-PVW randomization gates; production hot-path permission remains false.
""",
    )
    _append_run(root, decision)
    return decision


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    state = args.state or args.root / "research_state.yaml"
    summary = args.summary or args.root / "repro/candidate_a_star_cycle_gate/summary.csv"
    print(apply_gate(args.root, state, summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the closeout test and apply the real decision**

Run:

```powershell
python -m unittest tests.research.test_candidate_a_closeout -v
python scripts/apply_mat_sab_candidate_gate.py
python scripts/mat_sab_research_state.py validate
```

Expected: the test reports `OK`; the current decision is printed; state validation passes. For current Stage203 evidence, A is `REJECTED`, B is `INTAKE`, Goal remains `ACTIVE`, and hot-path permission remains `false`.

- [ ] **Step 5: Run the complete research test suite**

Run:

```powershell
python -m unittest discover -s tests/research -p "test_*.py" -v
```

Expected: all state, techgraph, algebra, gate, and closeout tests report `OK` with no skipped tests.

- [ ] **Step 6: Verify reproducibility and repository hygiene**

Run:

```powershell
python scripts/build_mat_sab_selector_techgraph.py
python scripts/run_candidate_a_star_cycle_gate.py
python scripts/apply_mat_sab_candidate_gate.py
python scripts/mat_sab_research_state.py validate
git diff --check
rg -n "FIXME|XXX|pass[ ]+#" research scripts tests/research paper_techgraphs theory_checks/candidate_a_star_cycle_production_equations.md algorithm_variants/candidate_a_star_cycle_sparse_mat_ggsw.md experiments/candidate_a_star_cycle_gate_plan.md docs/candidate_a_star_cycle_mechanism_gate.md repro/candidate_a_star_cycle_gate
```

Expected: deterministic pass/reject outputs repeat without duplicate ledger entries; state validates; `git diff --check` is silent; the final search is silent.

- [ ] **Step 7: Confirm the C hot path is untouched**

Run:

```powershell
git diff 147666f -- src include main.c Makefile
```

Expected: no output. Any C or build-system diff blocks completion of this work package.

- [ ] **Step 8: Commit the closeout and route decision**

```powershell
git add scripts/apply_mat_sab_candidate_gate.py tests/research/test_candidate_a_closeout.py research_state.yaml hypotheses/hypothesis_register.yaml repro/run_log.csv repro/artifact_manifest.md repro/reproduction_checklist.md
git commit -m "Record Candidate A mechanism decision"
git status --short
```

Expected: the commit succeeds and the worktree is clean.

## Work-Package Exit Gate

This plan is complete only when all of the following are true:

1. The active Goal is concise and the A/B/C campaign is machine-state bounded.
2. Every techgraph source/evidence anchor resolves at the execution commit.
3. Dense support passes phase and per-column standard-PVW randomization controls.
4. Stage203 support is checked for r=2/4/6 and selector values 0/1.
5. The Candidate A decision is computed from gates, not selected by a constant.
6. No C hot-path or build-system file changed.
7. The computed decision is recorded once in state, hypothesis register, run log, manifest, and checklist.
8. The repository either advances A only to key/security/noise preflight or rejects A and activates B. It does not begin a kernel implementation from this plan.

Failure of the per-column randomization condition is an early necessary-
condition rejection. In that case, CMUX/NCMUX, RGSW monomial, `sparse_mul`,
noise, Amdahl, kernel, and full-SAB gates remain explicitly unexecuted rather
than being inferred from the linear checker.

The next implementation plan is conditional. An admitted A receives a
key-distribution, assumption-comparison, noise-recurrence, and Amdahl preflight
plan. A rejected A receives a Candidate B factorized-operator equation plan
that tests whether `M = mu I + v w^T` can be evaluated with `Theta(r)` standard
encrypted operator work without recreating dense MAT cost.
