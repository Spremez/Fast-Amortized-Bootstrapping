import json
import tempfile
import unittest
from pathlib import Path

import scripts.mat_sab_research_state as state_controller
from scripts.mat_sab_research_state import (
    load_state,
    transition_candidate,
    validate_state,
)


ROOT = Path(__file__).resolve().parents[2]
PREDECESSOR_STATE = (
    ROOT / "tests/research/fixtures/predecessor_research_state.json"
)
CURRENT_D_DECISIONS = {
    "PLAN_APPROVED": (
        "CANDIDATE_D_WRITTEN_SPEC_AND_IMPLEMENTATION_PLAN_APPROVED"
    ),
    "D0_BASELINE_FROZEN": "PASS_D0_CANDIDATE_D_BASELINES_FROZEN",
    "D1_NOVELTY_AUDIT_PASS": (
        "PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE"
    ),
    "D2_OPERATOR_CLOSURE_PASS": "PASS_D2_OPERATOR_CLOSURE_G_LE_4",
    "D3_ADMISSION_PASS": (
        "ADMIT_CANDIDATE_D_TO_ISOLATED_ENCRYPTED_OPERATOR_IMPLEMENTATION"
    ),
}
CURRENT_D_SOURCES_BY_STATUS = {
    "PLAN_APPROVED": "DESIGN_APPROVED_PENDING_WRITTEN_SPEC_REVIEW",
    "D0_BASELINE_FROZEN": "PLAN_APPROVED",
    "D1_NOVELTY_AUDIT_PASS": "D0_BASELINE_FROZEN",
    "D2_OPERATOR_CLOSURE_PASS": "D1_NOVELTY_AUDIT_PASS",
    "D3_ADMISSION_PASS": "D2_OPERATOR_CLOSURE_PASS",
}
CURRENT_D_REJECTIONS_BY_SOURCE = {
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
CURRENT_D_INCOMPLETE_EVIDENCE_DECISION = (
    "BLOCK_CANDIDATE_D_INCOMPLETE_EVIDENCE"
)


def candidate_a_state(state, status):
    state["goal_status"] = "ACTIVE"
    state["paper_gate"] = "BLOCKED"
    state["production_hot_path_permission"] = False
    state["active_candidate"] = "A"
    state["last_decision"] = "TEST_CANDIDATE_A_STATE"
    state["candidates"]["A"]["status"] = status
    state["candidates"]["B"]["status"] = "QUEUED"
    state["candidates"]["C"]["status"] = "QUEUED"
    for candidate in state["candidates"].values():
        candidate["equation_revisions_used"] = 0
        candidate["kernel_layouts_used"] = 0
        candidate["full_sab_integrations_used"] = 0
    return state


def candidate_b_state(state, status):
    state["goal_status"] = "ACTIVE"
    state["paper_gate"] = "BLOCKED"
    state["production_hot_path_permission"] = False
    state["active_candidate"] = "B"
    state["last_decision"] = "TEST_CANDIDATE_B_STATE"
    state["candidates"]["A"]["status"] = "REJECTED"
    state["candidates"]["B"]["status"] = status
    state["candidates"]["C"]["status"] = "QUEUED"
    for candidate in state["candidates"].values():
        candidate["equation_revisions_used"] = 0
        candidate["kernel_layouts_used"] = 0
        candidate["full_sab_integrations_used"] = 0
    return state


def candidate_c_state(state, status, *, terminal=False):
    state["goal_status"] = (
        "RESEARCH_CAMPAIGN_EXHAUSTED"
        if status == "REJECTED"
        else (
            "RESEARCH_CAMPAIGN_INCONCLUSIVE"
            if status == "INCONCLUSIVE"
            else "ACTIVE"
        )
    )
    state["paper_gate"] = "BLOCKED"
    state["production_hot_path_permission"] = False
    state["active_candidate"] = "C"
    state["last_decision"] = "TEST_CANDIDATE_C_STATE"
    state["candidates"]["A"]["status"] = "REJECTED"
    state["candidates"]["B"]["status"] = "REJECTED"
    state["candidates"]["C"]["status"] = status
    for candidate in state["candidates"].values():
        candidate["equation_revisions_used"] = 0
        candidate["kernel_layouts_used"] = 0
        candidate["full_sab_integrations_used"] = 0
    if terminal:
        state["candidates"]["C"]["equation_revisions_used"] = 1
    return state


def candidate_d_state(status):
    state = load_state(ROOT / "research_state.yaml")
    state["goal_status"] = "ACTIVE"
    state["paper_gate"] = "BLOCKED"
    state["production_hot_path_permission"] = False
    state["active_candidate"] = "D"
    state["last_decision"] = CURRENT_D_DECISIONS.get(
        status,
        "TEST_CANDIDATE_D_STATE",
    )
    state["last_decision_source_status"] = CURRENT_D_SOURCES_BY_STATUS.get(
        status,
        "TEST_CANDIDATE_D_SOURCE_STATUS",
    )
    state["candidates"]["D"]["status"] = status
    state["candidates"]["D"]["last_reached_status"] = status
    state["candidates"]["E"]["status"] = "RESERVED_FALLBACK_NOT_STARTED"
    state["candidates"]["E"][
        "last_reached_status"
    ] = "RESERVED_FALLBACK_NOT_STARTED"
    for candidate in ("D", "E"):
        state["candidates"][candidate]["equation_revisions_used"] = 0
        state["candidates"][candidate]["kernel_layouts_used"] = 0
        state["candidates"][candidate]["full_sab_integrations_used"] = 0
    return state


def candidate_d_preplan_state():
    state = candidate_d_state(
        "DESIGN_APPROVED_PENDING_WRITTEN_SPEC_REVIEW"
    )
    state["goal_status"] = "CANDIDATE_D_DESIGN_APPROVED_PLAN_BLOCKED"
    state["last_decision"] = (
        "AUTHORIZE_CANDIDATE_D_STANDARD_RLWE_MODULE_LWE_"
        "INTERNAL_SEMANTICS_CAMPAIGN"
    )
    state["last_decision_source_status"] = "RESEARCH_CAMPAIGN_EXHAUSTED"
    return state


def candidate_e_preflight_state():
    return transition_candidate(
        candidate_d_state("D2_OPERATOR_CLOSURE_PASS"),
        "D",
        "REJECTED",
        "REJECT_CANDIDATE_D_BINDING_NOISE_SECURITY_ROUTE_E",
    )


def candidate_d_external_blocked_state(status="D0_BASELINE_FROZEN"):
    state = candidate_d_state(status)
    state["goal_status"] = "EXTERNAL_BLOCKED"
    state["last_decision"] = CURRENT_D_INCOMPLETE_EVIDENCE_DECISION
    state["last_decision_source_status"] = status
    return state


class ResearchStateTests(unittest.TestCase):
    def test_candidate_state_helpers_normalize_all_mutable_fields(self):
        cases = (
            (candidate_a_state, "INTAKE", ("INTAKE", "QUEUED", "QUEUED"), "TEST_CANDIDATE_A_STATE"),
            (candidate_b_state, "INTAKE", ("REJECTED", "INTAKE", "QUEUED"), "TEST_CANDIDATE_B_STATE"),
        )
        for helper, status, expected_statuses, expected_decision in cases:
            with self.subTest(helper=helper.__name__):
                state = load_state(PREDECESSOR_STATE)
                state["goal_status"] = "PAPER_READY"
                state["paper_gate"] = "PASS"
                state["production_hot_path_permission"] = True
                state["last_decision"] = "CLOSEOUT_MUTATION"
                for candidate in state["candidates"].values():
                    candidate["status"] = "REJECTED"
                    candidate["equation_revisions_used"] = 1
                    candidate["kernel_layouts_used"] = 1
                    candidate["full_sab_integrations_used"] = 1

                normalized = helper(state, status)

                self.assertEqual(normalized["goal_status"], "ACTIVE")
                self.assertEqual(normalized["paper_gate"], "BLOCKED")
                self.assertFalse(normalized["production_hot_path_permission"])
                self.assertEqual(normalized["last_decision"], expected_decision)
                self.assertEqual(
                    tuple(
                        normalized["candidates"][candidate]["status"]
                        for candidate in ("A", "B", "C")
                    ),
                    expected_statuses,
                )
                for candidate in normalized["candidates"].values():
                    self.assertEqual(candidate["equation_revisions_used"], 0)
                    self.assertEqual(candidate["kernel_layouts_used"], 0)
                    self.assertEqual(candidate["full_sab_integrations_used"], 0)

    def test_current_repository_state_uses_candidate_d_contract(self):
        state = load_state(ROOT / "research_state.yaml")
        self.assertEqual(
            state["contract"],
            "docs/superpowers/specs/"
            "2026-07-20-lut-late-binding-operator-sab-design.md",
        )
        self.assertEqual(
            state["primary_metric"],
            "complete_sab_T_bootstrap_div_rN_active",
        )
        self.assertEqual(state["candidate_order"], ["A", "B", "C", "D", "E"])
        self.assertEqual(state["active_candidate"], "D")
        self.assertEqual(state["goal_status"], "EXTERNAL_BLOCKED")
        self.assertEqual(
            state["last_decision_source_status"],
            "D0_BASELINE_FROZEN",
        )
        self.assertEqual(
            state["last_decision"],
            CURRENT_D_INCOMPLETE_EVIDENCE_DECISION,
        )
        self.assertEqual(
            state["candidates"]["D"]["last_reached_status"],
            "D0_BASELINE_FROZEN",
        )
        self.assertEqual(
            state["candidates"]["E"]["last_reached_status"],
            "RESERVED_FALLBACK_NOT_STARTED",
        )
        self.assertFalse(state["production_hot_path_permission"])

    def test_candidate_d_incomplete_evidence_overlay_is_valid(self):
        for status in (
            "PLAN_APPROVED",
            "D0_BASELINE_FROZEN",
            "D1_NOVELTY_AUDIT_PASS",
            "D2_OPERATOR_CLOSURE_PASS",
        ):
            with self.subTest(status=status):
                validate_state(candidate_d_external_blocked_state(status))

    def test_candidate_d_incomplete_evidence_overlay_is_tightly_constrained(self):
        mutations = (
            ("active_candidate", "E"),
            ("paper_gate", "PASS"),
            ("production_hot_path_permission", True),
            ("e_status", "SECURITY_NOVELTY_PREFLIGHT"),
            ("d_status", "D3_ADMISSION_PASS"),
            ("d_last_reached_status", "PLAN_APPROVED"),
            ("last_decision", "CHANGED"),
            ("last_decision_source_status", "PLAN_APPROVED"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                state = candidate_d_external_blocked_state()
                if field == "e_status":
                    state["candidates"]["E"]["status"] = value
                    state["candidates"]["E"]["last_reached_status"] = value
                elif field == "d_status":
                    state["candidates"]["D"]["status"] = value
                    state["candidates"]["D"]["last_reached_status"] = value
                    state["last_decision_source_status"] = value
                elif field == "d_last_reached_status":
                    state["candidates"]["D"]["last_reached_status"] = value
                else:
                    state[field] = value
                with self.assertRaises(ValueError):
                    validate_state(state)

    def test_predecessor_state_is_valid_and_locked_to_primary_metric(self):
        state = load_state(PREDECESSOR_STATE)
        validate_state(state)
        self.assertIn(state["goal_status"], {
            "ACTIVE", "PAPER_READY", "ACCEPTED",
            "RESEARCH_CAMPAIGN_EXHAUSTED",
            "RESEARCH_CAMPAIGN_INCONCLUSIVE",
            "EXTERNAL_BLOCKED",
        })
        self.assertEqual(
            state["contract"],
            "docs/superpowers/specs/"
            "2026-07-16-ccs-usenix-mat-sab-research-contract-design.md",
        )
        self.assertEqual(state["target_venue"], "CCS_USENIX_SECURITY")
        self.assertEqual(state["primary_metric"], "complete_sab_T_bootstrap_over_r")
        self.assertEqual(state["baselines"], {
            "B0": "repeated_scalar_SAB",
            "B1": "exact_dense_PVW_MAT_SAB_current_head",
        })
        self.assertIn(state["active_candidate"], ("A", "B", "C"))
        self.assertEqual(
            {name: state["candidates"][name]["name"] for name in ("A", "B", "C")},
            {
                "A": "Star-Cycle Sparse MAT-GGSW",
                "B": "Factorized Star-Cycle",
                "C": "Rank-Bounded Shared-Mask State",
            },
        )
        active = state["candidates"][state["active_candidate"]]["status"]
        if active in {"INTAKE", "TECHGRAPH_ANCHORED", "EQUATIONS_DEFINED"}:
            self.assertFalse(state["production_hot_path_permission"])

    def test_candidate_d_cannot_skip_d0_d3(self):
        state = candidate_d_state("PLAN_APPROVED")
        with self.assertRaisesRegex(ValueError, "invalid transition"):
            transition_candidate(
                state, "D", "D3_ADMISSION_PASS", "SKIP_D0_D2"
            )

    def test_candidate_d_forward_transitions_record_gate_history(self):
        for to_status in (
            "D0_BASELINE_FROZEN",
            "D1_NOVELTY_AUDIT_PASS",
            "D2_OPERATOR_CLOSURE_PASS",
            "D3_ADMISSION_PASS",
        ):
            source_status = CURRENT_D_SOURCES_BY_STATUS[to_status]
            with self.subTest(
                source_status=source_status,
                to_status=to_status,
            ):
                state = candidate_d_state(source_status)
                original = json.loads(json.dumps(state))
                changed = transition_candidate(
                    state,
                    "D",
                    to_status,
                    CURRENT_D_DECISIONS[to_status],
                )
                self.assertEqual(state, original)
                self.assertEqual(
                    changed["last_decision_source_status"],
                    source_status,
                )
                self.assertEqual(
                    changed["candidates"]["D"]["last_reached_status"],
                    to_status,
                )
                self.assertEqual(
                    changed["candidates"]["E"]["last_reached_status"],
                    "RESERVED_FALLBACK_NOT_STARTED",
                )

    def test_candidate_d_rejection_routes_only_to_e(self):
        state = candidate_d_state("D2_OPERATOR_CLOSURE_PASS")
        original = json.loads(json.dumps(state))
        changed = transition_candidate(
            state,
            "D",
            "REJECTED",
            "REJECT_CANDIDATE_D_BINDING_NOISE_SECURITY_ROUTE_E",
        )
        self.assertEqual(changed["active_candidate"], "E")
        self.assertEqual(
            changed["candidates"]["E"]["status"],
            "SECURITY_NOVELTY_PREFLIGHT",
        )
        self.assertEqual(state, original)
        self.assertEqual(
            changed["candidates"]["D"]["last_reached_status"],
            "D2_OPERATOR_CLOSURE_PASS",
        )
        self.assertEqual(
            changed["candidates"]["E"]["last_reached_status"],
            "SECURITY_NOVELTY_PREFLIGHT",
        )
        self.assertFalse(changed["production_hot_path_permission"])

    def test_candidate_d_rejection_matrix_accepts_legitimate_pairs(self):
        for source_status, decisions in CURRENT_D_REJECTIONS_BY_SOURCE.items():
            for decision in decisions:
                with self.subTest(
                    source_status=source_status,
                    decision=decision,
                ):
                    changed = transition_candidate(
                        candidate_d_state(source_status),
                        "D",
                        "REJECTED",
                        decision,
                    )
                    self.assertEqual(changed["active_candidate"], "E")
                    self.assertEqual(
                        changed["candidates"]["E"]["status"],
                        "SECURITY_NOVELTY_PREFLIGHT",
                    )
                    self.assertEqual(changed["last_decision"], decision)
                    self.assertEqual(
                        changed["last_decision_source_status"],
                        source_status,
                    )
                    self.assertEqual(
                        changed["candidates"]["D"]["last_reached_status"],
                        source_status,
                    )
                    self.assertEqual(
                        changed["candidates"]["E"]["last_reached_status"],
                        "SECURITY_NOVELTY_PREFLIGHT",
                    )
                    validate_state(changed)

    def test_persisted_candidate_d_rejections_bind_exact_source_and_decision(
        self,
    ):
        for source_status, decisions in CURRENT_D_REJECTIONS_BY_SOURCE.items():
            other_source = next(
                status
                for status in CURRENT_D_REJECTIONS_BY_SOURCE
                if status != source_status
            )
            other_decision = CURRENT_D_REJECTIONS_BY_SOURCE[other_source][0]
            for decision in decisions:
                with self.subTest(
                    source_status=source_status,
                    decision=decision,
                ):
                    persisted = transition_candidate(
                        candidate_d_state(source_status),
                        "D",
                        "REJECTED",
                        decision,
                    )
                    validate_state(json.loads(json.dumps(persisted)))

                    decision_only = json.loads(json.dumps(persisted))
                    decision_only["last_decision"] = other_decision
                    with self.assertRaisesRegex(ValueError, "last_decision"):
                        validate_state(decision_only)

                    source_only = json.loads(json.dumps(persisted))
                    source_only["last_decision_source_status"] = other_source
                    with self.assertRaisesRegex(
                        ValueError,
                        "last_decision_source_status",
                    ):
                        validate_state(source_only)

                    coordinated_rewrite = json.loads(json.dumps(persisted))
                    coordinated_rewrite["last_decision"] = other_decision
                    coordinated_rewrite[
                        "last_decision_source_status"
                    ] = other_source
                    with self.assertRaisesRegex(
                        ValueError,
                        "last_decision_source_status",
                    ):
                        validate_state(coordinated_rewrite)

                    gate_history_only = json.loads(json.dumps(persisted))
                    gate_history_only["candidates"]["D"][
                        "last_reached_status"
                    ] = other_source
                    with self.assertRaisesRegex(
                        ValueError,
                        "last_decision_source_status",
                    ):
                        validate_state(gate_history_only)

    def test_candidate_d_rejection_matrix_rejects_wrong_pairs(self):
        source_statuses = (
            "PLAN_APPROVED",
            *CURRENT_D_REJECTIONS_BY_SOURCE,
            "D3_ADMISSION_PASS",
        )
        all_decisions = tuple(
            decision
            for decisions in CURRENT_D_REJECTIONS_BY_SOURCE.values()
            for decision in decisions
        )
        for source_status in source_statuses:
            legitimate = CURRENT_D_REJECTIONS_BY_SOURCE.get(source_status, ())
            for decision in all_decisions:
                if decision in legitimate:
                    continue
                with self.subTest(
                    source_status=source_status,
                    decision=decision,
                ):
                    with self.assertRaisesRegex(ValueError, "decision"):
                        transition_candidate(
                            candidate_d_state(source_status),
                            "D",
                            "REJECTED",
                            decision,
                        )

    def test_activate_candidate_d_plan_is_exact_and_does_not_mutate_input(self):
        state = candidate_d_preplan_state()
        original = json.loads(json.dumps(state))

        changed = state_controller.activate_candidate_d_plan(
            state,
            "CANDIDATE_D_WRITTEN_SPEC_AND_IMPLEMENTATION_PLAN_APPROVED",
        )

        self.assertEqual(state, original)
        self.assertEqual(
            state["goal_status"],
            "CANDIDATE_D_DESIGN_APPROVED_PLAN_BLOCKED",
        )
        self.assertEqual(
            state["candidates"]["D"]["status"],
            "DESIGN_APPROVED_PENDING_WRITTEN_SPEC_REVIEW",
        )
        self.assertEqual(changed["goal_status"], "ACTIVE")
        self.assertEqual(changed["candidates"]["D"]["status"], "PLAN_APPROVED")
        self.assertEqual(
            changed["last_decision"],
            "CANDIDATE_D_WRITTEN_SPEC_AND_IMPLEMENTATION_PLAN_APPROVED",
        )
        self.assertEqual(
            changed["last_decision_source_status"],
            "DESIGN_APPROVED_PENDING_WRITTEN_SPEC_REVIEW",
        )
        self.assertEqual(
            changed["candidates"]["D"]["last_reached_status"],
            "PLAN_APPROVED",
        )
        self.assertEqual(
            changed["candidates"]["E"]["last_reached_status"],
            "RESERVED_FALLBACK_NOT_STARTED",
        )

    def test_activate_candidate_d_plan_rejects_an_unbound_decision(self):
        with self.assertRaisesRegex(ValueError, "decision"):
            state_controller.activate_candidate_d_plan(
                candidate_d_preplan_state(),
                "OPAQUE_PLAN_APPROVAL",
            )

    def test_activate_candidate_d_plan_rejects_other_start_states(self):
        mutations = (
            ("goal_status", "ACTIVE"),
            ("candidate_d_status", "PLAN_APPROVED"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                state = candidate_d_preplan_state()
                if field == "candidate_d_status":
                    state["candidates"]["D"]["status"] = value
                else:
                    state[field] = value
                with self.assertRaises(ValueError):
                    state_controller.activate_candidate_d_plan(
                        state,
                        "CANDIDATE_D_WRITTEN_SPEC_AND_IMPLEMENTATION_PLAN_APPROVED",
                    )

    def test_activate_candidate_d_plan_reaches_wrong_gate_guard(self):
        state = candidate_d_state("D0_BASELINE_FROZEN")
        self.assertEqual(state["goal_status"], "ACTIVE")
        self.assertEqual(
            state["candidates"]["D"]["status"],
            "D0_BASELINE_FROZEN",
        )

        with self.assertRaisesRegex(
            ValueError,
            "state is not at the Candidate D plan gate",
        ):
            state_controller.activate_candidate_d_plan(
                state,
                "CANDIDATE_D_WRITTEN_SPEC_AND_IMPLEMENTATION_PLAN_APPROVED",
            )

    def test_current_contract_binds_status_derived_decisions(self):
        states = (
            candidate_d_preplan_state(),
            candidate_d_state("PLAN_APPROVED"),
            candidate_d_state("D0_BASELINE_FROZEN"),
            candidate_d_state("D1_NOVELTY_AUDIT_PASS"),
            candidate_d_state("D2_OPERATOR_CLOSURE_PASS"),
            candidate_d_state("D3_ADMISSION_PASS"),
        )
        for state in states:
            status = state["candidates"]["D"]["status"]
            validate_state(state)
            for field, value in (
                ("last_decision", "OPAQUE_LAST_DECISION_MUTATION"),
                (
                    "last_decision_source_status",
                    "OPAQUE_SOURCE_STATUS_MUTATION",
                ),
            ):
                with self.subTest(status=status, field=field):
                    mutated = json.loads(json.dumps(state))
                    mutated[field] = value
                    with self.assertRaisesRegex(ValueError, field):
                        validate_state(mutated)

    def test_non_rejected_current_candidates_bind_history_to_live_status(self):
        for state in (
            candidate_d_preplan_state(),
            candidate_d_state("PLAN_APPROVED"),
            candidate_d_state("D0_BASELINE_FROZEN"),
            candidate_d_state("D1_NOVELTY_AUDIT_PASS"),
            candidate_d_state("D2_OPERATOR_CLOSURE_PASS"),
            candidate_d_state("D3_ADMISSION_PASS"),
            candidate_e_preflight_state(),
        ):
            for candidate in ("D", "E"):
                status = state["candidates"][candidate]["status"]
                if status == "REJECTED":
                    continue
                with self.subTest(candidate=candidate, status=status):
                    mutated = json.loads(json.dumps(state))
                    mutated["candidates"][candidate][
                        "last_reached_status"
                    ] = "OTHER_REACHED_STATUS"
                    with self.assertRaisesRegex(
                        ValueError,
                        "last_reached_status",
                    ):
                        validate_state(mutated)

    def test_current_contract_rejects_unreviewed_future_d_states(self):
        for status in state_controller.D_PIPELINE[5:]:
            with self.subTest(status=status):
                state = candidate_d_state(status)
                if status == "D8_PAPER_GATE_PASS":
                    state["goal_status"] = "PAPER_READY"
                    state["paper_gate"] = "PASS"
                with self.assertRaisesRegex(
                    ValueError,
                    "invalid status for candidate D",
                ):
                    validate_state(state)

    def test_current_contract_rejects_unreviewed_future_e_states(self):
        for status in state_controller.E_PIPELINE[1:]:
            with self.subTest(status=status):
                state = candidate_e_preflight_state()
                state["candidates"]["E"]["status"] = status
                state["last_decision"] = "OPAQUE_CANDIDATE_E_DECISION"
                if status == "PAPER_GATE_PASS":
                    state["goal_status"] = "PAPER_READY"
                    state["paper_gate"] = "PASS"
                with self.assertRaisesRegex(
                    ValueError,
                    "invalid status for candidate E",
                ):
                    validate_state(state)

    def test_current_transitions_reject_unbound_decisions(self):
        cases = (
            (
                candidate_d_state("PLAN_APPROVED"),
                "D0_BASELINE_FROZEN",
            ),
            (
                candidate_d_state("D2_OPERATOR_CLOSURE_PASS"),
                "REJECTED",
            ),
        )
        for state, to_status in cases:
            with self.subTest(to_status=to_status):
                with self.assertRaisesRegex(ValueError, "decision"):
                    transition_candidate(
                        state,
                        "D",
                        to_status,
                        "OPAQUE_TRANSITION_DECISION",
                    )

    def test_current_contract_rejects_unknown_contracts(self):
        state = candidate_d_state("PLAN_APPROVED")
        state["contract"] = "docs/superpowers/specs/unknown.md"
        with self.assertRaisesRegex(ValueError, "contract"):
            validate_state(state)

    def test_current_contract_requires_rejected_predecessors(self):
        for candidate in ("A", "B", "C"):
            with self.subTest(candidate=candidate):
                state = candidate_d_state("PLAN_APPROVED")
                state["candidates"][candidate]["status"] = "QUEUED"
                with self.assertRaisesRegex(ValueError, "A, B, and C"):
                    validate_state(state)

    def test_current_contract_requires_candidate_c_revision(self):
        state = candidate_d_state("PLAN_APPROVED")
        state["candidates"]["C"]["equation_revisions_used"] = 0
        with self.assertRaisesRegex(ValueError, "Candidate C equation revision"):
            validate_state(state)

    def test_candidate_d_and_e_budgets_are_binary_integers(self):
        fields = (
            "equation_revisions_used",
            "kernel_layouts_used",
            "full_sab_integrations_used",
        )
        for candidate in ("D", "E"):
            for field in fields:
                for value in (-1, 2, False, True):
                    with self.subTest(
                        candidate=candidate,
                        field=field,
                        value=value,
                    ):
                        state = candidate_d_state("PLAN_APPROVED")
                        state["candidates"][candidate][field] = value
                        with self.assertRaisesRegex(
                            ValueError,
                            f"invalid {field}",
                        ):
                            validate_state(state)

    def test_current_hot_path_permission_starts_at_d3(self):
        state = candidate_d_state("D2_OPERATOR_CLOSURE_PASS")
        state["production_hot_path_permission"] = True
        with self.assertRaisesRegex(ValueError, "production hot path"):
            validate_state(state)

        state = candidate_d_state("D3_ADMISSION_PASS")
        state["production_hot_path_permission"] = True
        validate_state(state)

    def test_unreviewed_future_d_and_e_transitions_fail_closed(self):
        cases = (
            (
                candidate_d_state("D3_ADMISSION_PASS"),
                "D",
                "D4_ISOLATED_OPERATOR_PASS",
                "PASS_D4_UNREVIEWED",
            ),
            (
                candidate_e_preflight_state(),
                "E",
                "EQUATIONS_DEFINED",
                "CANDIDATE_E_EQUATIONS_DEFINED",
            ),
        )
        for state, candidate, to_status, decision in cases:
            with self.subTest(candidate=candidate, to_status=to_status):
                with self.assertRaisesRegex(ValueError, "invalid transition"):
                    transition_candidate(
                        state,
                        candidate,
                        to_status,
                        decision,
                    )

    def test_candidate_e_rejection_uses_canonical_preflight_decision(self):
        preflight = candidate_e_preflight_state()
        original = json.loads(json.dumps(preflight))
        self.assertEqual(
            preflight["last_decision_source_status"],
            "D2_OPERATOR_CLOSURE_PASS",
        )
        self.assertEqual(
            preflight["candidates"]["D"]["last_reached_status"],
            "D2_OPERATOR_CLOSURE_PASS",
        )
        self.assertEqual(
            preflight["candidates"]["E"]["last_reached_status"],
            "SECURITY_NOVELTY_PREFLIGHT",
        )
        changed = transition_candidate(
            preflight,
            "E",
            "REJECTED",
            CURRENT_E_PREFLIGHT_REJECTION_DECISION,
        )

        self.assertEqual(preflight, original)
        self.assertEqual(
            changed["goal_status"],
            "RESEARCH_CAMPAIGN_EXHAUSTED",
        )
        self.assertEqual(
            changed["last_decision"],
            CURRENT_E_PREFLIGHT_REJECTION_DECISION,
        )
        self.assertEqual(
            changed["last_decision_source_status"],
            "SECURITY_NOVELTY_PREFLIGHT",
        )
        self.assertEqual(
            changed["candidates"]["D"]["last_reached_status"],
            "D2_OPERATOR_CLOSURE_PASS",
        )
        self.assertEqual(
            changed["candidates"]["E"]["last_reached_status"],
            "SECURITY_NOVELTY_PREFLIGHT",
        )

    def test_candidate_e_rejection_rejects_other_decisions(self):
        with self.assertRaisesRegex(ValueError, "decision"):
            transition_candidate(
                candidate_e_preflight_state(),
                "E",
                "REJECTED",
                "OPAQUE_CANDIDATE_E_REJECTION",
            )

    def test_exhausted_candidate_e_decision_provenance_cannot_be_mutated(self):
        exhausted = transition_candidate(
            candidate_e_preflight_state(),
            "E",
            "REJECTED",
            CURRENT_E_PREFLIGHT_REJECTION_DECISION,
        )
        mutations = (
            ("last_decision", "OPAQUE_LAST_DECISION_MUTATION"),
            ("last_decision_source_status", "D2_OPERATOR_CLOSURE_PASS"),
            ("candidate_e_last_reached_status", "D2_OPERATOR_CLOSURE_PASS"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                state = json.loads(json.dumps(exhausted))
                if field == "candidate_e_last_reached_status":
                    state["candidates"]["E"]["last_reached_status"] = value
                    error_field = "last_reached_status"
                else:
                    state[field] = value
                    error_field = field
                with self.assertRaisesRegex(ValueError, error_field):
                    validate_state(state)

        coordinated_rewrite = json.loads(json.dumps(exhausted))
        coordinated_rewrite["last_decision"] = (
            "REJECT_CANDIDATE_D_PRIOR_ART_SUBSUMPTION_ROUTE_E"
        )
        coordinated_rewrite[
            "last_decision_source_status"
        ] = "D0_BASELINE_FROZEN"
        with self.assertRaises(ValueError):
            validate_state(coordinated_rewrite)

    def test_valid_transition_does_not_mutate_input(self):
        state = candidate_a_state(load_state(PREDECESSOR_STATE), "INTAKE")
        changed = transition_candidate(
            state, "A", "TECHGRAPH_ANCHORED", "CANDIDATE_A_TECHGRAPH_ANCHORED"
        )
        self.assertEqual(state["candidates"]["A"]["status"], "INTAKE")
        self.assertEqual(changed["candidates"]["A"]["status"], "TECHGRAPH_ANCHORED")
        self.assertEqual(changed["last_decision"], "CANDIDATE_A_TECHGRAPH_ANCHORED")

    def test_transition_records_an_opaque_decision(self):
        state = candidate_a_state(load_state(PREDECESSOR_STATE), "INTAKE")
        try:
            changed = transition_candidate(
                state, "A", "TECHGRAPH_ANCHORED", "OPAQUE_TEST_DECISION"
            )
        except ValueError as error:
            self.fail(f"opaque decision was rejected: {error}")
        self.assertEqual(changed["last_decision"], "OPAQUE_TEST_DECISION")

    def test_skipping_a_gate_is_rejected(self):
        state = candidate_a_state(load_state(PREDECESSOR_STATE), "INTAKE")
        with self.assertRaisesRegex(ValueError, "invalid transition"):
            transition_candidate(
                state,
                "A",
                "ISOLATED_KERNEL_PASS",
                "CANDIDATE_A_TECHGRAPH_ANCHORED",
            )

    def test_rejection_routes_to_next_candidate(self):
        state = candidate_a_state(
            load_state(PREDECESSOR_STATE),
            "EQUATIONS_DEFINED",
        )
        changed = transition_candidate(
            state,
            "A",
            "REJECTED",
            "REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B",
        )
        self.assertEqual(changed["active_candidate"], "B")
        self.assertEqual(changed["candidates"]["B"]["status"], "INTAKE")
        self.assertEqual(changed["goal_status"], "ACTIVE")

    def test_immutable_contract_fields_cannot_change(self):
        mutations = (
            ("contract", "docs/other-contract.md"),
            ("target_venue", "OTHER_VENUE"),
            ("primary_metric", "kernel_only_latency"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                state = load_state(PREDECESSOR_STATE)
                state[field] = value
                with self.assertRaises(ValueError):
                    validate_state(state)

    def test_exact_baseline_mapping_cannot_change(self):
        mutations = (
            {"B0": "other", "B1": "exact_dense_PVW_MAT_SAB_current_head"},
            {"B0": "repeated_scalar_SAB", "B1": "other"},
            {
                "B0": "repeated_scalar_SAB",
                "B1": "exact_dense_PVW_MAT_SAB_current_head",
                "B2": "extra",
            },
        )
        for baselines in mutations:
            with self.subTest(baselines=baselines):
                state = load_state(PREDECESSOR_STATE)
                state["baselines"] = baselines
                with self.assertRaisesRegex(ValueError, "baselines changed"):
                    validate_state(state)

    def test_exact_candidate_names_cannot_change(self):
        expected = {
            "A": "Star-Cycle Sparse MAT-GGSW",
            "B": "Factorized Star-Cycle",
            "C": "Rank-Bounded Shared-Mask State",
        }
        for candidate, name in expected.items():
            with self.subTest(candidate=candidate):
                state = load_state(PREDECESSOR_STATE)
                state["candidates"][candidate]["name"] = f"{name} changed"
                with self.assertRaisesRegex(ValueError, "candidate name changed"):
                    validate_state(state)

    def test_candidate_budgets_reject_json_booleans(self):
        fields = (
            "equation_revisions_used",
            "kernel_layouts_used",
            "full_sab_integrations_used",
        )
        for candidate in ("A", "B", "C"):
            for field in fields:
                for value in (False, True):
                    with self.subTest(
                        candidate=candidate, field=field, value=value
                    ):
                        state = load_state(PREDECESSOR_STATE)
                        state["candidates"][candidate][field] = value
                        with self.assertRaisesRegex(ValueError, f"invalid {field}"):
                            validate_state(state)

    def test_hot_path_permission_is_rejected_before_amdahl_projection_pass(self):
        before_amdahl = (
            "INTAKE",
            "TECHGRAPH_ANCHORED",
            "EQUATIONS_DEFINED",
            "ADVERSARIAL_CHECKER_PASS",
            "KEY_SECURITY_NOISE_PREFLIGHT_PASS",
        )
        for status in before_amdahl:
            with self.subTest(status=status):
                state = candidate_a_state(
                    load_state(PREDECESSOR_STATE), status
                )
                state["production_hot_path_permission"] = True
                with self.assertRaisesRegex(ValueError, "production hot path"):
                    validate_state(state)

    def test_hot_path_permission_is_allowed_at_amdahl_projection_pass(self):
        state = candidate_a_state(
            load_state(PREDECESSOR_STATE),
            "AMDAHL_PROJECTION_PASS",
        )
        state["production_hot_path_permission"] = True
        validate_state(state)

    def test_hot_path_permission_requires_a_strict_boolean(self):
        for permission in (0, 1):
            with self.subTest(permission=permission):
                state = load_state(PREDECESSOR_STATE)
                state["production_hot_path_permission"] = permission
                with self.assertRaisesRegex(ValueError, "must be boolean"):
                    validate_state(state)

    def test_paper_gate_rejects_unknown_values(self):
        state = load_state(PREDECESSOR_STATE)
        state["paper_gate"] = "pending-anything"
        with self.assertRaisesRegex(ValueError, "invalid paper_gate"):
            validate_state(state)

    def test_paper_terminal_conditions_must_be_equivalent(self):
        mismatches = (
            ("ACTIVE", "BLOCKED", "PAPER_GATE_PASS"),
            ("ACTIVE", "PASS", "INTAKE"),
            ("ACTIVE", "PASS", "PAPER_GATE_PASS"),
            ("PAPER_READY", "BLOCKED", "INTAKE"),
            ("PAPER_READY", "BLOCKED", "PAPER_GATE_PASS"),
            ("PAPER_READY", "PASS", "INTAKE"),
        )
        for goal_status, paper_gate, active_status in mismatches:
            with self.subTest(
                goal_status=goal_status,
                paper_gate=paper_gate,
                active_status=active_status,
            ):
                state = candidate_b_state(
                    load_state(PREDECESSOR_STATE), active_status
                )
                state["goal_status"] = goal_status
                state["paper_gate"] = paper_gate
                with self.assertRaisesRegex(
                    ValueError,
                    "paper terminal state mismatch",
                ):
                    validate_state(state)

    def test_paper_gate_transition_and_accepted_state_are_valid(self):
        state = candidate_b_state(
            load_state(PREDECESSOR_STATE), "FULL_SAB_PASS"
        )

        changed = transition_candidate(
            state,
            "B",
            "PAPER_GATE_PASS",
            "CANDIDATE_B_PAPER_GATE_PASS",
        )

        self.assertEqual(changed["goal_status"], "PAPER_READY")
        self.assertEqual(changed["paper_gate"], "PASS")
        self.assertEqual(
            changed["candidates"]["B"]["status"],
            "PAPER_GATE_PASS",
        )
        validate_state(changed)
        changed["goal_status"] = "ACCEPTED"
        validate_state(changed)

    def test_candidate_c_inconclusive_terminal_state_is_valid(self):
        state = load_state(PREDECESSOR_STATE)
        state["goal_status"] = "RESEARCH_CAMPAIGN_INCONCLUSIVE"
        state["active_candidate"] = "C"
        state["candidates"]["A"]["status"] = "REJECTED"
        state["candidates"]["B"]["status"] = "REJECTED"
        state["candidates"]["C"]["status"] = "INCONCLUSIVE"
        state["candidates"]["C"]["equation_revisions_used"] = 1
        state["paper_gate"] = "BLOCKED"
        state["production_hot_path_permission"] = False
        validate_state(state)

    def test_candidate_c_inconclusive_state_is_tightly_constrained(self):
        mutations = (
            ("goal_status", "ACTIVE"),
            ("active_candidate", "B"),
            ("paper_gate", "PASS"),
            ("production_hot_path_permission", True),
            ("candidate_a", "INTAKE"),
            ("candidate_b", "INTAKE"),
            ("candidate_c", "REJECTED"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                state = load_state(PREDECESSOR_STATE)
                state["goal_status"] = "RESEARCH_CAMPAIGN_INCONCLUSIVE"
                state["active_candidate"] = "C"
                state["candidates"]["A"]["status"] = "REJECTED"
                state["candidates"]["B"]["status"] = "REJECTED"
                state["candidates"]["C"]["status"] = "INCONCLUSIVE"
                state["candidates"]["C"]["equation_revisions_used"] = 1
                state["paper_gate"] = "BLOCKED"
                state["production_hot_path_permission"] = False
                if field.startswith("candidate_"):
                    state["candidates"][field[-1].upper()]["status"] = value
                else:
                    state[field] = value
                with self.assertRaises(ValueError):
                    validate_state(state)

    def test_transition_candidate_c_to_inconclusive_is_terminal(self):
        state = load_state(PREDECESSOR_STATE)
        state["goal_status"] = "ACTIVE"
        state["active_candidate"] = "C"
        state["candidates"]["A"]["status"] = "REJECTED"
        state["candidates"]["B"]["status"] = "REJECTED"
        state["candidates"]["C"]["status"] = "INTAKE"
        state["candidates"]["C"]["equation_revisions_used"] = 0
        state["paper_gate"] = "BLOCKED"
        state["production_hot_path_permission"] = False
        changed = transition_candidate(
            state,
            "C",
            "INCONCLUSIVE",
            "INCONCLUSIVE_CANDIDATE_C_EVIDENCE_EXHAUSTED",
        )
        self.assertEqual(
            changed["goal_status"],
            "RESEARCH_CAMPAIGN_INCONCLUSIVE",
        )
        self.assertEqual(changed["active_candidate"], "C")
        self.assertEqual(changed["candidates"]["C"]["status"], "INCONCLUSIVE")
        self.assertEqual(
            changed["candidates"]["C"]["equation_revisions_used"],
            1,
        )
        self.assertEqual(changed["paper_gate"], "BLOCKED")
        self.assertFalse(changed["production_hot_path_permission"])
        validate_state(changed)

    def test_candidate_c_precloseout_states_require_zero_equation_revisions(self):
        for status in ("INTAKE", "TECHGRAPH_ANCHORED", "EQUATIONS_DEFINED"):
            with self.subTest(status=status):
                state = candidate_c_state(
                    load_state(PREDECESSOR_STATE),
                    status,
                )
                validate_state(state)
                state["candidates"]["C"]["equation_revisions_used"] = 1
                with self.assertRaisesRegex(
                    ValueError,
                    "Candidate C equation revision",
                ):
                    validate_state(state)

    def test_candidate_c_terminal_states_require_one_equation_revision(self):
        for status in (
            "ADVERSARIAL_CHECKER_PASS",
            "KEY_SECURITY_NOISE_PREFLIGHT_PASS",
            "AMDAHL_PROJECTION_PASS",
            "ISOLATED_KERNEL_PASS",
            "FULL_SAB_PASS",
            "PAPER_GATE_PASS",
            "REJECTED",
            "INCONCLUSIVE",
        ):
            with self.subTest(status=status):
                state = candidate_c_state(
                    load_state(PREDECESSOR_STATE),
                    status,
                    terminal=True,
                )
                if status == "PAPER_GATE_PASS":
                    state["goal_status"] = "PAPER_READY"
                    state["paper_gate"] = "PASS"
                validate_state(state)
                state["candidates"]["C"]["equation_revisions_used"] = 0
                with self.assertRaisesRegex(
                    ValueError,
                    "Candidate C equation revision",
                ):
                    validate_state(state)

    def test_candidate_c_closeout_transitions_consume_exactly_one_revision(self):
        for status in (
            "ADVERSARIAL_CHECKER_PASS",
            "REJECTED",
            "INCONCLUSIVE",
        ):
            with self.subTest(status=status):
                state = candidate_c_state(
                    load_state(PREDECESSOR_STATE),
                    "EQUATIONS_DEFINED",
                )
                changed = transition_candidate(
                    state,
                    "C",
                    status,
                    f"TEST_CANDIDATE_C_{status}",
                )
                self.assertEqual(
                    state["candidates"]["C"]["equation_revisions_used"],
                    0,
                )
                self.assertEqual(
                    changed["candidates"]["C"]["equation_revisions_used"],
                    1,
                )
                validate_state(changed)

    def test_json_valid_yaml_round_trip(self):
        state = load_state(ROOT / "research_state.yaml")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.yaml"
            path.write_text(json.dumps(state, indent=2) + "\n", encoding="ascii")
            self.assertEqual(load_state(path), state)


if __name__ == "__main__":
    unittest.main()
