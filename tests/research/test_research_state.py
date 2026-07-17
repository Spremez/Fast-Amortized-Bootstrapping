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

    def test_valid_transition_does_not_mutate_input(self):
        state = candidate_a_state(load_state(ROOT / "research_state.yaml"), "INTAKE")
        changed = transition_candidate(
            state, "A", "TECHGRAPH_ANCHORED", "CANDIDATE_A_TECHGRAPH_ANCHORED"
        )
        self.assertEqual(state["candidates"]["A"]["status"], "INTAKE")
        self.assertEqual(changed["candidates"]["A"]["status"], "TECHGRAPH_ANCHORED")
        self.assertEqual(changed["last_decision"], "CANDIDATE_A_TECHGRAPH_ANCHORED")

    def test_transition_records_an_opaque_decision(self):
        state = candidate_a_state(load_state(ROOT / "research_state.yaml"), "INTAKE")
        try:
            changed = transition_candidate(
                state, "A", "TECHGRAPH_ANCHORED", "OPAQUE_TEST_DECISION"
            )
        except ValueError as error:
            self.fail(f"opaque decision was rejected: {error}")
        self.assertEqual(changed["last_decision"], "OPAQUE_TEST_DECISION")

    def test_skipping_a_gate_is_rejected(self):
        state = candidate_a_state(load_state(ROOT / "research_state.yaml"), "INTAKE")
        with self.assertRaisesRegex(ValueError, "invalid transition"):
            transition_candidate(
                state,
                "A",
                "ISOLATED_KERNEL_PASS",
                "CANDIDATE_A_TECHGRAPH_ANCHORED",
            )

    def test_rejection_routes_to_next_candidate(self):
        state = candidate_a_state(load_state(ROOT / "research_state.yaml"), "EQUATIONS_DEFINED")
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
                state = load_state(ROOT / "research_state.yaml")
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
                state = load_state(ROOT / "research_state.yaml")
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
                state = load_state(ROOT / "research_state.yaml")
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
                        state = load_state(ROOT / "research_state.yaml")
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
                    load_state(ROOT / "research_state.yaml"), status
                )
                state["production_hot_path_permission"] = True
                with self.assertRaisesRegex(ValueError, "production hot path"):
                    validate_state(state)

    def test_hot_path_permission_is_allowed_at_amdahl_projection_pass(self):
        state = candidate_a_state(
            load_state(ROOT / "research_state.yaml"), "AMDAHL_PROJECTION_PASS"
        )
        state["production_hot_path_permission"] = True
        validate_state(state)

    def test_hot_path_permission_requires_a_strict_boolean(self):
        for permission in (0, 1):
            with self.subTest(permission=permission):
                state = load_state(ROOT / "research_state.yaml")
                state["production_hot_path_permission"] = permission
                with self.assertRaisesRegex(ValueError, "must be boolean"):
                    validate_state(state)

    def test_paper_gate_rejects_unknown_values(self):
        state = load_state(ROOT / "research_state.yaml")
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
                state = load_state(ROOT / "research_state.yaml")
                state["goal_status"] = goal_status
                state["paper_gate"] = paper_gate
                state["candidates"]["B"]["status"] = active_status
                with self.assertRaisesRegex(
                    ValueError,
                    "paper terminal state mismatch",
                ):
                    validate_state(state)

    def test_paper_gate_transition_and_accepted_state_are_valid(self):
        state = load_state(ROOT / "research_state.yaml")
        state["candidates"]["B"]["status"] = "FULL_SAB_PASS"

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

    def test_json_valid_yaml_round_trip(self):
        state = load_state(ROOT / "research_state.yaml")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.yaml"
            path.write_text(json.dumps(state, indent=2) + "\n", encoding="ascii")
            self.assertEqual(load_state(path), state)


if __name__ == "__main__":
    unittest.main()
