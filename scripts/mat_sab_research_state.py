#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE = ROOT / "research_state.yaml"
PREDECESSOR_CONTRACT = (
    "docs/superpowers/specs/"
    "2026-07-16-ccs-usenix-mat-sab-research-contract-design.md"
)
CURRENT_CONTRACT = (
    "docs/superpowers/specs/"
    "2026-07-20-lut-late-binding-operator-sab-design.md"
)
PREDECESSOR_ORDER = ("A", "B", "C")
CURRENT_ORDER = ("A", "B", "C", "D", "E")
CURRENT_PRIMARY_METRIC = "complete_sab_T_bootstrap_div_rN_active"
D_PIPELINE = (
    "PLAN_APPROVED",
    "D0_BASELINE_FROZEN",
    "D1_NOVELTY_AUDIT_PASS",
    "D2_OPERATOR_CLOSURE_PASS",
    "D3_ADMISSION_PASS",
    "D4_ISOLATED_OPERATOR_PASS",
    "D5_FULL_SAB_PASS",
    "D6_OPTIMIZATION_COMPLETE",
    "D7_EVIDENCE_MATRIX_PASS",
    "D8_PAPER_GATE_PASS",
)
E_PIPELINE = (
    "SECURITY_NOVELTY_PREFLIGHT",
    "EQUATIONS_DEFINED",
    "ADVERSARIAL_CHECKER_PASS",
    "KEY_SECURITY_NOISE_PREFLIGHT_PASS",
    "AMDAHL_PROJECTION_PASS",
    "ISOLATED_KERNEL_PASS",
    "FULL_SAB_PASS",
    "PAPER_GATE_PASS",
)
CURRENT_BASELINES = {
    "B0a": "repeated_scalar_SAB",
    "B0b": (
        "shared_output_key_independent_mask_"
        "repeated_scalar_control_required"
    ),
    "B1": "exact_dense_PVW_MAT_SAB_current_head",
    "B2": "BatchBoot_same_backend_local_reproduction_required",
}
APPROVED_VENUE = "CCS_USENIX_SECURITY"
PREDECESSOR_PRIMARY_METRIC = "complete_sab_T_bootstrap_over_r"
PREDECESSOR_BASELINES = {
    "B0": "repeated_scalar_SAB",
    "B1": "exact_dense_PVW_MAT_SAB_current_head",
}
PREDECESSOR_CANDIDATE_NAMES = {
    "A": "Star-Cycle Sparse MAT-GGSW",
    "B": "Factorized Star-Cycle",
    "C": "Rank-Bounded Shared-Mask State",
}
CURRENT_CANDIDATE_NAMES = {
    **PREDECESSOR_CANDIDATE_NAMES,
    "D": "LUT-Late-Binding Operator SAB",
    "E": "Extension-Ring Tensor Lane-Packed SAB",
}
PREDECESSOR_PIPELINE = (
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
CANDIDATE_C_PRE_REVISION_STATUSES = {
    "QUEUED",
    "INTAKE",
    "TECHGRAPH_ANCHORED",
    "EQUATIONS_DEFINED",
}
CURRENT_D_PREPLAN_STATUS = (
    "DESIGN_APPROVED_PENDING_WRITTEN_SPEC_REVIEW"
)
CURRENT_D_PREPLAN_GOAL = "CANDIDATE_D_DESIGN_APPROVED_PLAN_BLOCKED"
CURRENT_D_ACTIVATION_DECISION = (
    "CANDIDATE_D_WRITTEN_SPEC_AND_IMPLEMENTATION_PLAN_APPROVED"
)
CURRENT_D_PREPLAN_DECISION_SOURCE_STATUS = "RESEARCH_CAMPAIGN_EXHAUSTED"
CURRENT_D_DECISIONS_BY_STATUS = {
    CURRENT_D_PREPLAN_STATUS: (
        "AUTHORIZE_CANDIDATE_D_STANDARD_RLWE_MODULE_LWE_"
        "INTERNAL_SEMANTICS_CAMPAIGN"
    ),
    "PLAN_APPROVED": CURRENT_D_ACTIVATION_DECISION,
    "D0_BASELINE_FROZEN": "PASS_D0_CANDIDATE_D_BASELINES_FROZEN",
    "D1_NOVELTY_AUDIT_PASS": (
        "PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE"
    ),
    "D2_OPERATOR_CLOSURE_PASS": "PASS_D2_OPERATOR_CLOSURE_G_LE_4",
    "D3_ADMISSION_PASS": (
        "ADMIT_CANDIDATE_D_TO_ISOLATED_ENCRYPTED_OPERATOR_IMPLEMENTATION"
    ),
}
CURRENT_D_DECISION_SOURCES_BY_STATUS = {
    CURRENT_D_PREPLAN_STATUS: CURRENT_D_PREPLAN_DECISION_SOURCE_STATUS,
    "PLAN_APPROVED": CURRENT_D_PREPLAN_STATUS,
    "D0_BASELINE_FROZEN": "PLAN_APPROVED",
    "D1_NOVELTY_AUDIT_PASS": "D0_BASELINE_FROZEN",
    "D2_OPERATOR_CLOSURE_PASS": "D1_NOVELTY_AUDIT_PASS",
    "D3_ADMISSION_PASS": "D2_OPERATOR_CLOSURE_PASS",
}
CURRENT_D_REJECTION_DECISIONS_BY_SOURCE = {
    "D0_BASELINE_FROZEN": (
        "REJECT_CANDIDATE_D_PRIOR_ART_SUBSUMPTION_ROUTE_E",
    ),
    "D1_NOVELTY_AUDIT_PASS": (
        "REJECT_CANDIDATE_D_OPERATOR_CLOSURE_ROUTE_E",
    ),
    "D2_OPERATOR_CLOSURE_PASS": (
        "REJECT_CANDIDATE_D_BINDING_NOISE_SECURITY_ROUTE_E",
        "REJECT_CANDIDATE_D_NONPOSITIVE_COMPLETE_COST_ROUTE_E",
    ),
}
CURRENT_E_PREFLIGHT_REJECTION_DECISION = (
    "REJECT_CANDIDATE_E_SECURITY_NOVELTY_PREFLIGHT_CAMPAIGN_EXHAUSTED"
)
CURRENT_D_RESEARCH_ENVELOPE = (
    "internal_semantics_may_change_standard_RLWE_"
    "Module_LWE_reduction_required"
)


def load_state(path: Path = DEFAULT_STATE) -> dict[str, object]:
    state = json.loads(path.read_text(encoding="ascii"))
    validate_state(state)
    return state


def _validate_predecessor_state(state: Mapping[str, object]) -> None:
    if state.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if state.get("contract") != PREDECESSOR_CONTRACT:
        raise ValueError("contract changed")
    if state.get("target_venue") != APPROVED_VENUE:
        raise ValueError("target venue changed")
    if state.get("candidate_order") != list(PREDECESSOR_ORDER):
        raise ValueError("candidate_order must be A, B, C")
    if state.get("primary_metric") != PREDECESSOR_PRIMARY_METRIC:
        raise ValueError("primary metric changed")
    if state.get("baselines") != PREDECESSOR_BASELINES:
        raise ValueError("baselines changed")
    if state.get("goal_status") not in {
        "ACTIVE",
        "PAPER_READY",
        "ACCEPTED",
        "RESEARCH_CAMPAIGN_EXHAUSTED",
        "RESEARCH_CAMPAIGN_INCONCLUSIVE",
        "EXTERNAL_BLOCKED",
    }:
        raise ValueError("invalid goal_status")
    if state.get("active_candidate") not in PREDECESSOR_ORDER:
        raise ValueError("invalid active_candidate")
    candidates = state.get("candidates")
    if (
        not isinstance(candidates, Mapping)
        or set(candidates) != set(PREDECESSOR_ORDER)
    ):
        raise ValueError("candidates must contain A, B, C")
    allowed = set(PREDECESSOR_PIPELINE) | {
        "QUEUED",
        "REJECTED",
        "INCONCLUSIVE",
    }
    for name in PREDECESSOR_ORDER:
        candidate = candidates[name]
        if not isinstance(candidate, Mapping) or candidate.get("status") not in allowed:
            raise ValueError(f"invalid status for candidate {name}")
        if candidate.get("name") != PREDECESSOR_CANDIDATE_NAMES[name]:
            raise ValueError(f"candidate name changed for {name}")
        for field, limit in (
            ("equation_revisions_used", 2),
            ("kernel_layouts_used", 2),
            ("full_sab_integrations_used", 1),
        ):
            value = candidate.get(field)
            if type(value) is not int or value < 0 or value > limit:
                raise ValueError(f"invalid {field} for candidate {name}")
    candidate_c = candidates["C"]
    expected_candidate_c_revisions = (
        0
        if candidate_c["status"] in CANDIDATE_C_PRE_REVISION_STATUSES
        else 1
    )
    if (
        candidate_c["equation_revisions_used"]
        != expected_candidate_c_revisions
    ):
        raise ValueError(
            "Candidate C equation revision count must be "
            f"{expected_candidate_c_revisions} at "
            f"{candidate_c['status']}"
        )
    active_index = PREDECESSOR_ORDER.index(state["active_candidate"])
    if state.get("goal_status") == "RESEARCH_CAMPAIGN_EXHAUSTED":
        if state.get("active_candidate") != "C" or any(
            candidates[name]["status"] != "REJECTED"
            for name in PREDECESSOR_ORDER
        ):
            raise ValueError("exhausted campaign must have A, B, C rejected")
    elif state.get("goal_status") == "RESEARCH_CAMPAIGN_INCONCLUSIVE":
        if not (
            state.get("active_candidate") == "C"
            and candidates["A"]["status"] == "REJECTED"
            and candidates["B"]["status"] == "REJECTED"
            and candidates["C"]["status"] == "INCONCLUSIVE"
            and state.get("paper_gate") == "BLOCKED"
            and state.get("production_hot_path_permission") is False
        ):
            raise ValueError(
                "inconclusive campaign must have A and B rejected and C "
                "active inconclusive"
            )
    else:
        if candidates[state["active_candidate"]]["status"] in {
            "QUEUED",
            "REJECTED",
            "INCONCLUSIVE",
        }:
            raise ValueError("active candidate is not active")
        if any(
            candidates[name]["status"] != "REJECTED"
            for name in PREDECESSOR_ORDER[:active_index]
        ):
            raise ValueError("candidates before the active candidate must be rejected")
        if any(
            candidates[name]["status"] != "QUEUED"
            for name in PREDECESSOR_ORDER[active_index + 1:]
        ):
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
    amdahl_index = PREDECESSOR_PIPELINE.index(
        "AMDAHL_PROJECTION_PASS"
    )
    if permission and (
        active_status not in PREDECESSOR_PIPELINE
        or PREDECESSOR_PIPELINE.index(active_status) < amdahl_index
    ):
        raise ValueError(
            "production hot path permission requires AMDAHL_PROJECTION_PASS"
        )


def _validate_current_state(state: Mapping[str, object]) -> None:
    if state.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if state.get("contract") != CURRENT_CONTRACT:
        raise ValueError("contract changed")
    if state.get("predecessor_contract") != PREDECESSOR_CONTRACT:
        raise ValueError("predecessor contract changed")
    if state.get("target_venue") != APPROVED_VENUE:
        raise ValueError("target venue changed")
    if state.get("candidate_order") != list(CURRENT_ORDER):
        raise ValueError("candidate_order must be A, B, C, D, E")
    if state.get("primary_metric") != CURRENT_PRIMARY_METRIC:
        raise ValueError("primary metric changed")
    if state.get("baselines") != CURRENT_BASELINES:
        raise ValueError("baselines changed")

    candidates = state.get("candidates")
    if (
        not isinstance(candidates, Mapping)
        or set(candidates) != set(CURRENT_ORDER)
    ):
        raise ValueError("candidates must contain A, B, C, D, E")
    for name in CURRENT_ORDER:
        candidate = candidates[name]
        if not isinstance(candidate, Mapping):
            raise ValueError(f"invalid candidate {name}")
        if candidate.get("name") != CURRENT_CANDIDATE_NAMES[name]:
            raise ValueError(f"candidate name changed for {name}")
    if any(
        candidates[name].get("status") != "REJECTED"
        for name in PREDECESSOR_ORDER
    ):
        raise ValueError("Candidates A, B, and C must be REJECTED")
    for name in PREDECESSOR_ORDER:
        for field, limit in (
            ("equation_revisions_used", 2),
            ("kernel_layouts_used", 2),
            ("full_sab_integrations_used", 1),
        ):
            value = candidates[name].get(field)
            if type(value) is not int or value < 0 or value > limit:
                raise ValueError(f"invalid {field} for candidate {name}")
    if candidates["C"].get("equation_revisions_used") != 1:
        raise ValueError(
            "Candidate C equation revision count must be 1"
        )
    for name in ("D", "E"):
        for field in (
            "equation_revisions_used",
            "kernel_layouts_used",
            "full_sab_integrations_used",
        ):
            value = candidates[name].get(field)
            if type(value) is not int or value < 0 or value > 1:
                raise ValueError(f"invalid {field} for candidate {name}")
    if (
        candidates["D"].get("research_envelope")
        != CURRENT_D_RESEARCH_ENVELOPE
    ):
        raise ValueError("Candidate D research envelope changed")

    d_status = candidates["D"].get("status")
    e_status = candidates["E"].get("status")
    allowed_d = set(CURRENT_D_DECISIONS_BY_STATUS) | {"REJECTED"}
    allowed_e = {
        "RESERVED_FALLBACK_NOT_STARTED",
        "SECURITY_NOVELTY_PREFLIGHT",
        "REJECTED",
    }
    if d_status not in allowed_d:
        raise ValueError("invalid status for candidate D")
    if e_status not in allowed_e:
        raise ValueError("invalid status for candidate E")

    d_last_reached_status = candidates["D"].get("last_reached_status")
    e_last_reached_status = candidates["E"].get("last_reached_status")
    if d_status == "REJECTED":
        if d_last_reached_status not in CURRENT_D_REJECTION_DECISIONS_BY_SOURCE:
            raise ValueError(
                "Candidate D last_reached_status must be a rejectable source"
            )
    elif d_last_reached_status != d_status:
        raise ValueError(
            "Candidate D last_reached_status must equal its live status"
        )
    if e_status == "REJECTED":
        if e_last_reached_status != "SECURITY_NOVELTY_PREFLIGHT":
            raise ValueError(
                "Candidate E last_reached_status must be a rejectable source"
            )
    elif e_last_reached_status != e_status:
        raise ValueError(
            "Candidate E last_reached_status must equal its live status"
        )

    active_candidate = state.get("active_candidate")
    if d_status == "REJECTED":
        if active_candidate != "E":
            raise ValueError("Candidate E must be active after D rejection")
        if e_status == "RESERVED_FALLBACK_NOT_STARTED":
            raise ValueError("Candidate E must start after D rejection")
    else:
        if active_candidate != "D":
            raise ValueError("Candidate D must remain active")
        if e_status != "RESERVED_FALLBACK_NOT_STARTED":
            raise ValueError("Candidate E must remain reserved")

    paper_gate = state.get("paper_gate")
    if paper_gate not in {"BLOCKED", "PASS"}:
        raise ValueError("invalid paper_gate")
    goal_status = state.get("goal_status")
    active_status = candidates[active_candidate]["status"]
    terminal_status = (
        active_status == "D8_PAPER_GATE_PASS"
        or active_status == "PAPER_GATE_PASS"
    )
    terminal_flags = (
        goal_status in {"PAPER_READY", "ACCEPTED"},
        paper_gate == "PASS",
        terminal_status,
    )
    if len(set(terminal_flags)) != 1:
        raise ValueError("paper terminal state mismatch")
    if d_status == CURRENT_D_PREPLAN_STATUS:
        if goal_status != CURRENT_D_PREPLAN_GOAL:
            raise ValueError("invalid Candidate D pre-plan goal status")
    elif e_status == "REJECTED":
        if goal_status != "RESEARCH_CAMPAIGN_EXHAUSTED":
            raise ValueError("rejected Candidate E must exhaust campaign")
    elif not terminal_status and goal_status != "ACTIVE":
        raise ValueError("active current campaign must have ACTIVE goal")

    last_decision = state.get("last_decision")
    last_decision_source_status = state.get(
        "last_decision_source_status"
    )
    expected_decision = CURRENT_D_DECISIONS_BY_STATUS.get(d_status)
    expected_source_status = CURRENT_D_DECISION_SOURCES_BY_STATUS.get(
        d_status
    )
    if (
        expected_decision is not None
        and last_decision != expected_decision
    ):
        raise ValueError(
            f"last_decision must be {expected_decision} at {d_status}"
        )
    if (
        expected_source_status is not None
        and last_decision_source_status != expected_source_status
    ):
        raise ValueError(
            "last_decision_source_status must be "
            f"{expected_source_status} at {d_status}"
        )
    if (
        d_status == "REJECTED"
        and e_status == "SECURITY_NOVELTY_PREFLIGHT"
    ):
        if last_decision_source_status != d_last_reached_status:
            raise ValueError(
                "last_decision_source_status must equal "
                "Candidate D last_reached_status"
            )
        source_decisions = CURRENT_D_REJECTION_DECISIONS_BY_SOURCE.get(
            d_last_reached_status,
            (),
        )
        if last_decision not in source_decisions:
            raise ValueError(
                "last_decision must be documented for "
                "last_decision_source_status at Candidate D rejection"
            )
    if (
        d_status == "REJECTED"
        and e_status == "REJECTED"
        and last_decision_source_status != e_last_reached_status
    ):
        raise ValueError(
            "last_decision_source_status must equal "
            "Candidate E last_reached_status"
        )
    if (
        d_status == "REJECTED"
        and e_status == "REJECTED"
        and last_decision != CURRENT_E_PREFLIGHT_REJECTION_DECISION
    ):
        raise ValueError(
            "last_decision must be the Candidate E preflight rejection"
        )

    permission = state.get("production_hot_path_permission")
    if not isinstance(permission, bool):
        raise ValueError(
            "production_hot_path_permission must be boolean"
        )
    d3_index = D_PIPELINE.index("D3_ADMISSION_PASS")
    if permission and (
        active_candidate != "D"
        or d_status not in D_PIPELINE
        or D_PIPELINE.index(d_status) < d3_index
    ):
        raise ValueError(
            "production hot path permission requires D3_ADMISSION_PASS"
        )
    if active_candidate == "E" and permission:
        raise ValueError(
            "production hot path permission is disabled for Candidate E"
        )


def validate_state(state: Mapping[str, object]) -> None:
    contract = state.get("contract")
    if contract == PREDECESSOR_CONTRACT:
        _validate_predecessor_state(state)
    elif contract == CURRENT_CONTRACT:
        _validate_current_state(state)
    else:
        raise ValueError("contract changed")


def _transition_predecessor_candidate(
    state: Mapping[str, object], candidate: str, to_status: str, decision: str
) -> dict[str, object]:
    if candidate not in PREDECESSOR_ORDER:
        raise ValueError(f"unknown candidate {candidate}")
    changed = copy.deepcopy(dict(state))
    current = changed["candidates"][candidate]["status"]
    if to_status in {"REJECTED", "INCONCLUSIVE"}:
        allowed = (
            current in PREDECESSOR_PIPELINE
            and current != "PAPER_GATE_PASS"
        )
        if to_status == "INCONCLUSIVE":
            allowed = allowed and candidate == "C"
    else:
        allowed = (
            current in PREDECESSOR_PIPELINE
            and PREDECESSOR_PIPELINE.index(current) + 1
            < len(PREDECESSOR_PIPELINE)
        )
        allowed = (
            allowed
            and PREDECESSOR_PIPELINE[
                PREDECESSOR_PIPELINE.index(current) + 1
            ]
            == to_status
        )
    if not allowed:
        raise ValueError(f"invalid transition {candidate}: {current} -> {to_status}")
    changed["candidates"][candidate]["status"] = to_status
    if (
        candidate == "C"
        and to_status not in CANDIDATE_C_PRE_REVISION_STATUSES
    ):
        changed["candidates"]["C"]["equation_revisions_used"] = 1
    changed["last_decision"] = decision
    if to_status == "REJECTED":
        index = PREDECESSOR_ORDER.index(candidate)
        if index + 1 == len(PREDECESSOR_ORDER):
            changed["goal_status"] = "RESEARCH_CAMPAIGN_EXHAUSTED"
            changed["production_hot_path_permission"] = False
        else:
            next_candidate = PREDECESSOR_ORDER[index + 1]
            changed["active_candidate"] = next_candidate
            changed["candidates"][next_candidate]["status"] = "INTAKE"
            changed["production_hot_path_permission"] = False
    elif to_status == "INCONCLUSIVE":
        changed["active_candidate"] = "C"
        changed["goal_status"] = "RESEARCH_CAMPAIGN_INCONCLUSIVE"
        changed["paper_gate"] = "BLOCKED"
        changed["production_hot_path_permission"] = False
    elif to_status == "PAPER_GATE_PASS":
        changed["paper_gate"] = "PASS"
        changed["goal_status"] = "PAPER_READY"
    validate_state(changed)
    return changed


def _transition_current_candidate(
    state: Mapping[str, object],
    candidate: str,
    to_status: str,
    decision: str,
) -> dict[str, object]:
    if candidate not in ("D", "E"):
        raise ValueError(f"unknown candidate {candidate}")
    if state["active_candidate"] != candidate:
        current = state["candidates"][candidate]["status"]
        raise ValueError(
            f"invalid transition {candidate}: {current} -> {to_status}"
        )
    pipeline = D_PIPELINE if candidate == "D" else E_PIPELINE
    changed = copy.deepcopy(dict(state))
    current = changed["candidates"][candidate]["status"]
    if to_status == "REJECTED":
        if candidate == "D":
            expected_decisions = (
                CURRENT_D_REJECTION_DECISIONS_BY_SOURCE.get(current, ())
            )
        else:
            expected_decisions = (
                (CURRENT_E_PREFLIGHT_REJECTION_DECISION,)
                if current == "SECURITY_NOVELTY_PREFLIGHT"
                else ()
            )
        if decision not in expected_decisions:
            raise ValueError(
                f"invalid transition decision {candidate}: "
                f"{current} -> {to_status}"
            )
        allowed = bool(expected_decisions)
    else:
        expected_decision = (
            CURRENT_D_DECISIONS_BY_STATUS.get(to_status)
            if candidate == "D"
            else None
        )
        allowed = (
            current in pipeline
            and pipeline.index(current) + 1 < len(pipeline)
            and pipeline[pipeline.index(current) + 1] == to_status
            and expected_decision is not None
        )
    if not allowed:
        raise ValueError(
            f"invalid transition {candidate}: {current} -> {to_status}"
        )
    if to_status != "REJECTED" and decision != expected_decision:
        raise ValueError(
            f"invalid transition decision {candidate}: "
            f"{current} -> {to_status}"
        )

    changed["candidates"][candidate]["status"] = to_status
    if to_status != "REJECTED":
        changed["candidates"][candidate][
            "last_reached_status"
        ] = to_status
    changed["last_decision"] = decision
    changed["last_decision_source_status"] = current
    if to_status == "REJECTED" and candidate == "D":
        changed["active_candidate"] = "E"
        changed["candidates"]["E"][
            "status"
        ] = "SECURITY_NOVELTY_PREFLIGHT"
        changed["candidates"]["E"][
            "last_reached_status"
        ] = "SECURITY_NOVELTY_PREFLIGHT"
        changed["goal_status"] = "ACTIVE"
        changed["paper_gate"] = "BLOCKED"
        changed["production_hot_path_permission"] = False
    elif to_status == "REJECTED":
        changed["goal_status"] = "RESEARCH_CAMPAIGN_EXHAUSTED"
        changed["paper_gate"] = "BLOCKED"
        changed["production_hot_path_permission"] = False
    elif to_status == pipeline[-1]:
        changed["paper_gate"] = "PASS"
        changed["goal_status"] = "PAPER_READY"
    validate_state(changed)
    return changed


def transition_candidate(
    state: Mapping[str, object],
    candidate: str,
    to_status: str,
    decision: str,
) -> dict[str, object]:
    validate_state(state)
    if state["contract"] == PREDECESSOR_CONTRACT:
        return _transition_predecessor_candidate(
            state,
            candidate,
            to_status,
            decision,
        )
    return _transition_current_candidate(
        state,
        candidate,
        to_status,
        decision,
    )


def activate_candidate_d_plan(
    state: Mapping[str, object],
    decision: str,
) -> dict[str, object]:
    validate_state(state)
    if decision != CURRENT_D_ACTIVATION_DECISION:
        raise ValueError("invalid Candidate D plan activation decision")
    candidates = state["candidates"]
    if (
        state["contract"] != CURRENT_CONTRACT
        or state["goal_status"] != CURRENT_D_PREPLAN_GOAL
        or candidates["D"]["status"] != CURRENT_D_PREPLAN_STATUS
    ):
        raise ValueError("state is not at the Candidate D plan gate")
    changed = copy.deepcopy(dict(state))
    changed["goal_status"] = "ACTIVE"
    changed["candidates"]["D"]["status"] = "PLAN_APPROVED"
    changed["candidates"]["D"]["last_reached_status"] = "PLAN_APPROVED"
    changed["last_decision"] = decision
    changed["last_decision_source_status"] = CURRENT_D_PREPLAN_STATUS
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
    transition.add_argument("candidate", choices=CURRENT_ORDER)
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
