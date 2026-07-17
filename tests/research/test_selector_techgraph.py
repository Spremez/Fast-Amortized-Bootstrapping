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
