import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.build_mat_sab_selector_techgraph import build_graph, write_outputs


ROOT = Path(__file__).resolve().parents[2]
REPRODUCTION_COMMAND = "python scripts/build_mat_sab_selector_techgraph.py"
DISCOVERY_COMMAND = (
    'python -m unittest discover -s tests/research -p "test_*.py" -v'
)
REPRODUCTION_SECTION = "\n".join([
    "## Reproduction",
    "",
    "```powershell",
    REPRODUCTION_COMMAND,
    DISCOVERY_COMMAND,
    "```",
])


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

    def test_graph_consumes_the_current_campaign_state(self):
        graph = build_graph(ROOT)
        self.assertEqual(
            graph["campaign_state"],
            {
                "goal_status": "ACTIVE",
                "paper_gate": "BLOCKED",
                "active_candidate": "B",
                "active_candidate_status": "INTAKE",
                "candidate_a_status": "REJECTED",
                "candidate_b_status": "INTAKE",
                "last_decision": (
                    "REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B"
                ),
            },
        )
        self.assertNotIn(
            "standard PVW randomization dimension",
            graph["open_gaps"],
        )

    def test_graph_records_the_stable_reproduction_command(self):
        graph = build_graph(ROOT)
        self.assertEqual(graph["reproduction_command"], REPRODUCTION_COMMAND)

    def test_reproduction_command_executes_from_the_repository_root(self):
        completed = subprocess.run(
            [sys.executable, "scripts/build_mat_sab_selector_techgraph.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout.strip(),
            "PASS_CANDIDATE_A_TECHGRAPH_ANCHORED",
        )

    def test_markdown_outputs_record_exact_reproduction_commands(self):
        graph = build_graph(ROOT)
        paths = write_outputs(ROOT, graph)
        for path in paths[1:]:
            with self.subTest(path=path.name):
                self.assertIn(
                    REPRODUCTION_SECTION,
                    path.read_text(encoding="ascii"),
                )

    def test_markdown_outputs_render_current_route_without_reopening_a(self):
        graph = build_graph(ROOT)
        paths = write_outputs(ROOT, graph)
        for path in paths[1:]:
            content = path.read_text(encoding="ascii")
            with self.subTest(path=path.name):
                self.assertIn("Candidate A: `REJECTED`", content)
                self.assertIn("Candidate B: `INTAKE` (active)", content)
                self.assertIn(
                    "Candidate B is active at `INTAKE`; its equations and "
                    "implementation have not begun.",
                    content,
                )
                self.assertNotIn(
                    "The next gate tests `P M = mu P` and the standard PVW "
                    "randomization",
                    content,
                )

    def test_gaps_document_preserves_the_finite_field_claim_boundary(self):
        graph = build_graph(ROOT)
        gaps = write_outputs(ROOT, graph)[2].read_text(encoding="ascii")
        self.assertIn(
            "does not infer cryptographic security or complete-SAB performance",
            gaps,
        )

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
