import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.build_mat_sab_selector_techgraph import (
    _campaign_markdown,
    _campaign_view,
    build_graph,
    write_outputs,
)
from scripts.mat_sab_research_state import load_state


ROOT = Path(__file__).resolve().parents[2]
UNIT_INPUT_COMMIT = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    cwd=ROOT,
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
DISCOVERY_COMMAND = (
    'python -m unittest discover -s tests/research -p "test_*.py" -v'
)
TRACKED_OUTPUTS = (
    "2025_686_mat_sab_selector.yaml",
    "2025_686_mat_sab_selector_graph.md",
    "2025_686_mat_sab_selector_gaps.md",
)


def reproduction_command(commit):
    return (
        "python scripts/build_mat_sab_selector_techgraph.py "
        f"--input-commit {commit}"
    )


def reproduction_section(commit):
    return "\n".join([
        "## Reproduction",
        "",
        "```powershell",
        reproduction_command(commit),
        DISCOVERY_COMMAND,
        "```",
    ])


def published_input_commit():
    path = ROOT / "repro/candidate_c_rank_bounded_gate/environment.csv"
    with path.open(newline="", encoding="ascii") as handle:
        environment = {
            row["key"]: row["value"] for row in csv.DictReader(handle)
        }
    return environment["input_head"]


def synthetic_campaign_state(active_candidate):
    statuses = {"A": "QUEUED", "B": "QUEUED", "C": "QUEUED"}
    for candidate in ("A", "B", "C"):
        if candidate == active_candidate:
            statuses[candidate] = "INTAKE"
            break
        statuses[candidate] = "REJECTED"
    return {
        "goal_status": "ACTIVE",
        "paper_gate": "BLOCKED",
        "production_hot_path_permission": False,
        "active_candidate": active_candidate,
        "candidates": {
            candidate: {"status": status}
            for candidate, status in statuses.items()
        },
        "last_decision": f"TEST_ROUTE_TO_{active_candidate}",
    }


def terminal_rejected_campaign_state():
    return {
        "goal_status": "RESEARCH_CAMPAIGN_EXHAUSTED",
        "paper_gate": "BLOCKED",
        "production_hot_path_permission": False,
        "active_candidate": "C",
        "candidates": {
            candidate: {"status": "REJECTED"}
            for candidate in ("A", "B", "C")
        },
        "last_decision": (
            "REJECT_CANDIDATE_C_RANK_BOUNDED_STATE_CAMPAIGN_EXHAUSTED"
        ),
    }


class SelectorTechgraphTests(unittest.TestCase):
    def test_all_source_and_artifact_anchors_resolve(self):
        graph = build_graph(ROOT, input_commit=UNIT_INPUT_COMMIT)
        self.assertTrue(all(node["anchor_status"] == "PASS" for node in graph["nodes"]))

    def test_required_mechanism_nodes_are_present(self):
        graph = build_graph(ROOT, input_commit=UNIT_INPUT_COMMIT)
        node_ids = {node["id"] for node in graph["nodes"]}
        self.assertTrue({
            "sab_schedule", "pvw_phase", "pvw_randomization", "dense_keygen",
            "dense_decompose", "dense_addmul", "compact_kernel",
            "star_cycle_support", "closure_failure", "distribution_blocker",
        }.issubset(node_ids))

    def test_graph_records_the_production_code_boundary(self):
        graph = build_graph(ROOT, input_commit=UNIT_INPUT_COMMIT)
        self.assertFalse(graph["production_code_permission"])

    def test_graph_consumes_the_current_campaign_state(self):
        graph = build_graph(ROOT, input_commit=UNIT_INPUT_COMMIT)
        state = load_state(ROOT / "research_state.yaml")
        self.assertEqual(
            graph["campaign_state"],
            {
                "goal_status": state["goal_status"],
                "paper_gate": state["paper_gate"],
                "active_candidate": state["active_candidate"],
                "active_candidate_status": state["candidates"][
                    state["active_candidate"]
                ]["status"],
                "candidate_a_status": state["candidates"]["A"]["status"],
                "candidate_b_status": state["candidates"]["B"]["status"],
                "candidate_c_status": state["candidates"]["C"]["status"],
                "last_decision": state["last_decision"],
            },
        )

    def test_campaign_routes_mark_the_active_candidate(self):
        for active_candidate in ("A", "B", "C"):
            with self.subTest(active_candidate=active_candidate):
                graph = _campaign_view(synthetic_campaign_state(active_candidate))
                campaign = "\n".join(_campaign_markdown(graph))
                self.assertIn(
                    f"Candidate {active_candidate}: `INTAKE` (active)",
                    campaign,
                )
                self.assertEqual(campaign.count("(active)"), 1)

    def test_terminal_campaign_records_candidate_c_closeout_boundary(self):
        graph = _campaign_view(terminal_rejected_campaign_state())
        campaign = "\n".join(_campaign_markdown(graph))
        rendered = "\n".join(
            (
                campaign,
                str(graph["candidate_a_disposition"]),
                str(graph["next_step"]),
                *graph["open_gaps"],
            )
        )
        required = (
            "finite A/B/C mechanism campaign is exhausted",
            "scoped C1 nonpositive structural-cost failure",
            "Task 3B and Task 4 were skipped",
            "exact-dense PVW/MAT-SAB evidence is preserved",
            "no Candidate D is opened automatically",
        )
        for text in required:
            with self.subTest(text=text):
                self.assertIn(text, rendered)
        for forbidden in ("not begun", "unstarted", "active research"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered)

    def test_graph_records_the_stable_reproduction_command(self):
        graph = build_graph(ROOT, input_commit=UNIT_INPUT_COMMIT)
        self.assertEqual(
            graph["reproduction_command"],
            reproduction_command(UNIT_INPUT_COMMIT),
        )
        self.assertEqual(
            graph["implementation_input_commit"],
            UNIT_INPUT_COMMIT,
        )

    def test_reproduction_command_executes_from_the_repository_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/build_mat_sab_selector_techgraph.py"),
                    "--root",
                    str(ROOT),
                    "--destination-root",
                    tmp,
                    "--input-commit",
                    UNIT_INPUT_COMMIT,
                ],
                cwd=tmp,
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
        graph = build_graph(ROOT, input_commit=UNIT_INPUT_COMMIT)
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_outputs(Path(tmp), graph)
            for path in paths[1:]:
                with self.subTest(path=path.name):
                    self.assertIn(
                        reproduction_section(UNIT_INPUT_COMMIT),
                        path.read_text(encoding="ascii"),
                    )

    def test_markdown_outputs_render_current_campaign_state(self):
        graph = build_graph(ROOT, input_commit=UNIT_INPUT_COMMIT)
        state = load_state(ROOT / "research_state.yaml")
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_outputs(Path(tmp), graph)
            for path in paths[1:]:
                content = path.read_text(encoding="ascii")
                with self.subTest(path=path.name):
                    for candidate in ("A", "B", "C"):
                        active = " (active)" if candidate == state["active_candidate"] else ""
                        self.assertIn(
                            f"Candidate {candidate}: `"
                            f"{state['candidates'][candidate]['status']}`{active}",
                            content,
                        )
                    self.assertIn(graph["next_step"], content)
                    self.assertNotIn(
                        "The next gate tests `P M = mu P` and the standard PVW "
                        "randomization",
                        content,
                    )

    def test_gaps_document_preserves_the_finite_field_claim_boundary(self):
        graph = build_graph(ROOT, input_commit=UNIT_INPUT_COMMIT)
        with tempfile.TemporaryDirectory() as tmp:
            gaps = write_outputs(Path(tmp), graph)[2].read_text(encoding="ascii")
        self.assertIn(
            "does not infer cryptographic security or complete-SAB performance",
            gaps,
        )

    def test_outputs_are_json_valid_and_deterministic(self):
        graph = build_graph(ROOT, input_commit=UNIT_INPUT_COMMIT)
        with tempfile.TemporaryDirectory() as tmp:
            first = write_outputs(Path(tmp), graph)
            before = [path.read_bytes() for path in first]
            second = write_outputs(Path(tmp), graph)
            self.assertEqual(before, [path.read_bytes() for path in second])
            parsed = json.loads(first[0].read_text(encoding="ascii"))
        self.assertEqual(parsed["schema_version"], 1)

    def test_tracked_outputs_match_a_fresh_render(self):
        bound_commit = published_input_commit()
        graph = build_graph(ROOT, input_commit=bound_commit)
        with tempfile.TemporaryDirectory() as tmp:
            fresh_paths = write_outputs(Path(tmp), graph)
            for fresh_path in fresh_paths:
                tracked_path = ROOT / "paper_techgraphs" / fresh_path.name
                with self.subTest(path=fresh_path.name):
                    self.assertIn(fresh_path.name, TRACKED_OUTPUTS)
                    self.assertEqual(
                        tracked_path.read_bytes(),
                        fresh_path.read_bytes(),
                    )


if __name__ == "__main__":
    unittest.main()
