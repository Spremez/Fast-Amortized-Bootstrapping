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
    state["transition_history"] = []
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
        self.assertIsInstance(state.get("transition_history"), list)
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
        self.assertEqual(state["transition_history"], [])
        self.assertEqual(changed["transition_history"], [{
            "candidate": "A",
            "from_status": "INTAKE",
            "to_status": "TECHGRAPH_ANCHORED",
            "decision": "CANDIDATE_A_TECHGRAPH_ANCHORED",
            "evidence_type": "technical_graph_artifact",
            "evidence_path": "paper_techgraphs/2025_686_mat_sab_selector.yaml",
        }])

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
        self.assertEqual(changed["transition_history"], [{
            "candidate": "A",
            "from_status": "EQUATIONS_DEFINED",
            "to_status": "REJECTED",
            "decision": (
                "REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B"
            ),
            "evidence_type": "checker_summary",
            "evidence_path": "repro/candidate_a_star_cycle_gate/summary.csv",
        }])

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

    def test_transition_history_is_required_and_registry_backed(self):
        state = load_state(ROOT / "research_state.yaml")
        state.pop("transition_history", None)
        with self.assertRaisesRegex(ValueError, "transition_history"):
            validate_state(state)

        state = load_state(ROOT / "research_state.yaml")
        state["transition_history"] = [{
            "candidate": "A",
            "from_status": "INTAKE",
            "to_status": "TECHGRAPH_ANCHORED",
            "decision": "CANDIDATE_A_TECHGRAPH_ANCHORED",
            "evidence_type": "technical_graph_artifact",
            "evidence_path": "../outside.yaml",
        }]
        with self.assertRaisesRegex(ValueError, "transition_history"):
            validate_state(state)

    def test_unsupported_transition_decision_is_rejected(self):
        state = candidate_a_state(load_state(ROOT / "research_state.yaml"), "INTAKE")
        with self.assertRaisesRegex(ValueError, "unknown transition decision"):
            transition_candidate(
                state, "A", "TECHGRAPH_ANCHORED", "UNSUPPORTED_DECISION"
            )

    def test_registered_decision_must_match_the_transition(self):
        state = candidate_a_state(load_state(ROOT / "research_state.yaml"), "INTAKE")
        with self.assertRaisesRegex(ValueError, "decision does not match transition"):
            transition_candidate(
                state,
                "A",
                "TECHGRAPH_ANCHORED",
                "CANDIDATE_A_PRODUCTION_EQUATIONS_DEFINED",
            )

    def test_registered_decisions_append_fixed_evidence(self):
        cases = (
            (
                "INTAKE",
                "TECHGRAPH_ANCHORED",
                "CANDIDATE_A_TECHGRAPH_ANCHORED",
                "technical_graph_artifact",
                "paper_techgraphs/2025_686_mat_sab_selector.yaml",
            ),
            (
                "TECHGRAPH_ANCHORED",
                "EQUATIONS_DEFINED",
                "CANDIDATE_A_PRODUCTION_EQUATIONS_DEFINED",
                "derivation_artifact",
                "theory_checks/candidate_a_star_cycle_production_equations.md",
            ),
            (
                "EQUATIONS_DEFINED",
                "ADVERSARIAL_CHECKER_PASS",
                "ADMIT_CANDIDATE_A_REVISION_OR_KEYGEN_PREFLIGHT",
                "checker_summary",
                "repro/candidate_a_star_cycle_gate/summary.csv",
            ),
            (
                "EQUATIONS_DEFINED",
                "REJECTED",
                "REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B",
                "checker_summary",
                "repro/candidate_a_star_cycle_gate/summary.csv",
            ),
        )
        for from_status, to_status, decision, evidence_type, evidence_path in cases:
            with self.subTest(decision=decision):
                state = candidate_a_state(
                    load_state(ROOT / "research_state.yaml"), from_status
                )
                changed = transition_candidate(
                    state, "A", to_status, decision
                )
                self.assertEqual(changed["transition_history"], [{
                    "candidate": "A",
                    "from_status": from_status,
                    "to_status": to_status,
                    "decision": decision,
                    "evidence_type": evidence_type,
                    "evidence_path": evidence_path,
                }])

    def test_json_valid_yaml_round_trip(self):
        state = load_state(ROOT / "research_state.yaml")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.yaml"
            path.write_text(json.dumps(state, indent=2) + "\n", encoding="ascii")
            self.assertEqual(load_state(path), state)


if __name__ == "__main__":
    unittest.main()
