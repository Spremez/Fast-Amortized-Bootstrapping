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
