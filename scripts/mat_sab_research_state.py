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
APPROVED_CONTRACT = (
    "docs/superpowers/specs/"
    "2026-07-16-ccs-usenix-mat-sab-research-contract-design.md"
)
APPROVED_VENUE = "CCS_USENIX_SECURITY"
PRIMARY_METRIC = "complete_sab_T_bootstrap_over_r"
APPROVED_BASELINES = {
    "B0": "repeated_scalar_SAB",
    "B1": "exact_dense_PVW_MAT_SAB_current_head",
}
APPROVED_CANDIDATE_NAMES = {
    "A": "Star-Cycle Sparse MAT-GGSW",
    "B": "Factorized Star-Cycle",
    "C": "Rank-Bounded Shared-Mask State",
}
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
    if state.get("contract") != APPROVED_CONTRACT:
        raise ValueError("contract changed")
    if state.get("target_venue") != APPROVED_VENUE:
        raise ValueError("target venue changed")
    if state.get("candidate_order") != list(ORDER):
        raise ValueError("candidate_order must be A, B, C")
    if state.get("primary_metric") != PRIMARY_METRIC:
        raise ValueError("primary metric changed")
    if state.get("baselines") != APPROVED_BASELINES:
        raise ValueError("baselines changed")
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
        if candidate.get("name") != APPROVED_CANDIDATE_NAMES[name]:
            raise ValueError(f"candidate name changed for {name}")
        for field, limit in (
            ("equation_revisions_used", 2),
            ("kernel_layouts_used", 2),
            ("full_sab_integrations_used", 1),
        ):
            value = candidate.get(field)
            if type(value) is not int or value < 0 or value > limit:
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
    paper_gate = state.get("paper_gate")
    if paper_gate not in {"BLOCKED", "PASS"}:
        raise ValueError("invalid paper_gate")
    active_status = candidates[state["active_candidate"]]["status"]
    terminal_flags = (
        state.get("goal_status") in {"PAPER_READY", "ACCEPTED"},
        paper_gate == "PASS",
        active_status == "PAPER_GATE_PASS",
    )
    if len(set(terminal_flags)) != 1:
        raise ValueError("paper terminal state mismatch")
    permission = state.get("production_hot_path_permission")
    if not isinstance(permission, bool):
        raise ValueError("production_hot_path_permission must be boolean")
    amdahl_index = PIPELINE.index("AMDAHL_PROJECTION_PASS")
    if permission and (
        active_status not in PIPELINE
        or PIPELINE.index(active_status) < amdahl_index
    ):
        raise ValueError(
            "production hot path permission requires AMDAHL_PROJECTION_PASS"
        )


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
