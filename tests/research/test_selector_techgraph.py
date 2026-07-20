import ast
import csv
import importlib.util
import json
import marshal
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.build_mat_sab_selector_techgraph as selector
from scripts.build_mat_sab_selector_techgraph import (
    _campaign_markdown,
    _campaign_view,
    build_graph,
    write_outputs,
)
from scripts.mat_sab_research_state import (
    load_state,
    transition_candidate,
    validate_state,
)


ROOT = Path(__file__).resolve().parents[2]
PREDECESSOR_STATE = (
    ROOT / "tests/research/fixtures/predecessor_research_state.json"
)
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
SELECTOR_LOCAL_IMPORT_CLOSURE = (
    "research/__init__.py",
    "research/mat_sab/__init__.py",
    "research/mat_sab/candidate_c_operator_tensor.py",
    "research/mat_sab/candidate_c_registered_replay.py",
    "research/mat_sab/candidate_c_schedule.py",
    "research/mat_sab/finite_linear.py",
    "research/mat_sab/rank_bounded_state_model.py",
    "scripts/__init__.py",
    "scripts/build_mat_sab_selector_techgraph.py",
    "scripts/mat_sab_research_state.py",
    "scripts/run_candidate_c_rank_bounded_gate.py",
)


def _install_valid_timestamp_cache(source, marker_name):
    stat = source.stat()
    marker_source = "\n".join(
        (
            "from pathlib import Path",
            (
                f"Path({marker_name!r}).write_text("
                "'stale cache executed\\n', encoding='ascii')"
            ),
            "",
        )
    )
    code = compile(marker_source, str(source), "exec")
    cache = (
        source.parent
        / "__pycache__"
        / f"{source.stem}.{sys.implementation.cache_tag}.pyc"
    )
    cache.parent.mkdir(parents=True, exist_ok=True)
    header = importlib.util.MAGIC_NUMBER + struct.pack(
        "<III",
        0,
        int(stat.st_mtime) & 0xFFFFFFFF,
        stat.st_size & 0xFFFFFFFF,
    )
    cache.write_bytes(header + marshal.dumps(code))
    return cache


def _adjacent_cache_snapshot(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*.pyc"))
    }


def reproduction_command(commit):
    return (
        "python scripts/build_mat_sab_selector_techgraph.py "
        f"--source-state-commit {commit}"
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
    graph = json.loads(
        (
            ROOT / "paper_techgraphs/2025_686_mat_sab_selector.yaml"
        ).read_text(encoding="ascii")
    )
    return graph["selector_source_state_commit"]


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
        "candidate_order": ["A", "B", "C"],
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
        "candidate_order": ["A", "B", "C"],
        "candidates": {
            candidate: {"status": "REJECTED"}
            for candidate in ("A", "B", "C")
        },
        "last_decision": (
            "REJECT_CANDIDATE_C_RANK_BOUNDED_STATE_CAMPAIGN_EXHAUSTED"
        ),
    }


class SelectorTechgraphTests(unittest.TestCase):
    @staticmethod
    def _clone_working_selector(directory):
        root = Path(directory) / "root"
        subprocess.run(
            ["git", "clone", "--shared", "-q", str(ROOT), str(root)],
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Selector Test"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "config",
                "user.email",
                "selector@example.invalid",
            ],
            cwd=root,
            check=True,
        )
        for relative in SELECTOR_LOCAL_IMPORT_CLOSURE:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "commit",
                "--allow-empty",
                "-q",
                "-m",
                "working selector launcher",
            ],
            cwd=root,
            check=True,
        )
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return root, commit

    def test_all_source_and_artifact_anchors_resolve(self):
        graph = build_graph(
            ROOT, source_state_commit=UNIT_INPUT_COMMIT
        )
        self.assertTrue(all(node["anchor_status"] == "PASS" for node in graph["nodes"]))

    def test_required_mechanism_nodes_are_present(self):
        graph = build_graph(
            ROOT, source_state_commit=UNIT_INPUT_COMMIT
        )
        node_ids = {node["id"] for node in graph["nodes"]}
        self.assertTrue({
            "sab_schedule", "pvw_phase", "pvw_randomization", "dense_keygen",
            "dense_decompose", "dense_addmul", "compact_kernel",
            "star_cycle_support", "closure_failure", "distribution_blocker",
        }.issubset(node_ids))

    def test_graph_records_the_production_code_boundary(self):
        graph = build_graph(
            ROOT, source_state_commit=UNIT_INPUT_COMMIT
        )
        self.assertFalse(graph["production_code_permission"])

    def test_graph_consumes_the_current_campaign_state(self):
        graph = build_graph(
            ROOT, source_state_commit=UNIT_INPUT_COMMIT
        )
        state = load_state(ROOT / "research_state.yaml")
        expected = {
            "goal_status": state["goal_status"],
            "paper_gate": state["paper_gate"],
            "active_candidate": state["active_candidate"],
            "active_candidate_status": state["candidates"][
                state["active_candidate"]
            ]["status"],
        }
        expected.update(
            {
                f"candidate_{candidate.lower()}_status": (
                    state["candidates"][candidate]["status"]
                )
                for candidate in state["candidate_order"]
            }
        )
        expected["last_decision"] = state["last_decision"]
        self.assertEqual(graph["campaign_state"], expected)

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

    def test_current_campaign_renders_all_five_candidates(self):
        state = load_state(ROOT / "research_state.yaml")
        campaign = "\n".join(_campaign_markdown(_campaign_view(state)))
        expected = (
            "Candidate A: `REJECTED`",
            "Candidate B: `REJECTED`",
            "Candidate C: `REJECTED`",
            "Candidate D: `PLAN_APPROVED` (active)",
            "Candidate E: `RESERVED_FALLBACK_NOT_STARTED`",
        )
        for text in expected:
            with self.subTest(text=text):
                self.assertIn(text, campaign)
        self.assertEqual(campaign.count("(active)"), 1)

    def test_predecessor_campaign_fixture_still_renders_three_candidates(self):
        state = load_state(PREDECESSOR_STATE)
        campaign = "\n".join(_campaign_markdown(_campaign_view(state)))
        for candidate in ("A", "B", "C"):
            active = " (active)" if candidate == "C" else ""
            self.assertIn(
                f"Candidate {candidate}: `REJECTED`{active}",
                campaign,
            )
        self.assertNotIn("Candidate D:", campaign)
        self.assertNotIn("Candidate E:", campaign)

    def test_exhausted_candidate_e_renders_no_active_candidate_or_open_gates(self):
        state = load_state(ROOT / "research_state.yaml")
        state["candidates"]["D"]["status"] = "D2_OPERATOR_CLOSURE_PASS"
        state["last_decision"] = "PASS_D2_OPERATOR_CLOSURE_G_LE_4"
        state["last_decision_source_status"] = "D1_NOVELTY_AUDIT_PASS"
        validate_state(state)
        state = transition_candidate(
            state,
            "D",
            "REJECTED",
            "REJECT_CANDIDATE_D_BINDING_NOISE_SECURITY_ROUTE_E",
        )
        state = transition_candidate(
            state,
            "E",
            "REJECTED",
            "REJECT_CANDIDATE_E_SECURITY_NOVELTY_PREFLIGHT_"
            "CAMPAIGN_EXHAUSTED",
        )

        graph = _campaign_view(state)
        campaign = "\n".join(_campaign_markdown(graph))
        rendered = "\n".join(
            (
                campaign,
                str(graph["candidate_a_disposition"]),
                str(graph["next_step"]),
                *graph["open_gaps"],
            )
        )

        self.assertIsNone(graph["campaign_state"]["active_candidate"])
        self.assertIsNone(
            graph["campaign_state"]["active_candidate_status"]
        )
        self.assertNotIn("(active)", campaign)
        self.assertIn("Candidate E is rejected", rendered)
        self.assertIn("current Candidate D/E campaign is exhausted", rendered)
        self.assertNotIn("Candidate E is active", rendered)
        self.assertTrue(
            set(graph["open_gaps"]).isdisjoint(
                selector.PRE_GATE_OPEN_GAPS
            )
        )

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
        graph = build_graph(
            ROOT,
            source_state_commit=UNIT_INPUT_COMMIT,
        )
        self.assertEqual(
            graph["reproduction_command"],
            reproduction_command(UNIT_INPUT_COMMIT),
        )
        self.assertEqual(
            graph["selector_source_state_commit"],
            UNIT_INPUT_COMMIT,
        )
        manifest = {
            row["path"]: row["sha256"]
            for row in graph["selector_source_manifest"]
        }
        self.assertIn("research_state.yaml", manifest)
        self.assertEqual(
            set(manifest),
            set(selector.SELECTOR_SOURCE_STATE_INPUTS),
        )
        self.assertEqual(
            graph["selector_executable_manifest"],
            [
                row
                for row in graph["selector_source_manifest"]
                if row["path"] in selector.SELECTOR_EXECUTABLE_INPUTS
            ],
        )
        for node in graph["nodes"]:
            self.assertEqual(node["sha256"], manifest[node["path"]])

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
                    "--source-state-commit",
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
        graph = build_graph(
            ROOT, source_state_commit=UNIT_INPUT_COMMIT
        )
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_outputs(Path(tmp), graph)
            for path in paths[1:]:
                with self.subTest(path=path.name):
                    self.assertIn(
                        reproduction_section(UNIT_INPUT_COMMIT),
                        path.read_text(encoding="ascii"),
                    )

    def test_markdown_outputs_render_current_campaign_state(self):
        graph = build_graph(
            ROOT, source_state_commit=UNIT_INPUT_COMMIT
        )
        state = load_state(ROOT / "research_state.yaml")
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_outputs(Path(tmp), graph)
            for path in paths[1:]:
                content = path.read_text(encoding="ascii")
                with self.subTest(path=path.name):
                    for candidate in state["candidate_order"]:
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
        graph = build_graph(
            ROOT, source_state_commit=UNIT_INPUT_COMMIT
        )
        with tempfile.TemporaryDirectory() as tmp:
            gaps = write_outputs(Path(tmp), graph)[2].read_text(encoding="ascii")
        self.assertIn(
            "does not infer cryptographic security or complete-SAB performance",
            gaps,
        )

    def test_outputs_are_json_valid_and_deterministic(self):
        graph = build_graph(
            ROOT, source_state_commit=UNIT_INPUT_COMMIT
        )
        with tempfile.TemporaryDirectory() as tmp:
            first = write_outputs(Path(tmp), graph)
            before = [path.read_bytes() for path in first]
            second = write_outputs(Path(tmp), graph)
            self.assertEqual(before, [path.read_bytes() for path in second])
            parsed = json.loads(first[0].read_text(encoding="ascii"))
        self.assertEqual(parsed["schema_version"], 3)

    @unittest.skipUnless(
        hasattr(os, "symlink"),
        "symbolic links are not supported",
    )
    def test_node_source_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "root"
            root.mkdir()
            outside = base / "outside.txt"
            outside.write_text("needle\n", encoding="ascii", newline="\n")
            try:
                os.symlink(outside, root / "node.txt")
            except OSError as error:
                if getattr(error, "winerror", None) == 1314:
                    self.skipTest(f"symbolic links unavailable: {error}")
                raise
            with self.assertRaisesRegex(
                selector.GateEvidenceError,
                "escapes declared root",
            ):
                selector._node(
                    root,
                    ("node", "node.txt", "needle", "test node"),
                )

    def test_node_source_parent_escape_is_rejected_everywhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "root"
            root.mkdir()
            (base / "outside.txt").write_text(
                "needle\n",
                encoding="ascii",
                newline="\n",
            )
            with self.assertRaisesRegex(
                selector.GateEvidenceError,
                "escapes declared root",
            ):
                selector._node(
                    root,
                    ("node", "../outside.txt", "needle", "test node"),
                )

    @unittest.skipUnless(
        hasattr(os, "symlink"),
        "symbolic links are not supported",
    )
    def test_state_source_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "root"
            root.mkdir()
            outside = base / "research_state.yaml"
            outside.write_text("{}\n", encoding="ascii", newline="\n")
            try:
                os.symlink(outside, root / "research_state.yaml")
            except OSError as error:
                if getattr(error, "winerror", None) == 1314:
                    self.skipTest(f"symbolic links unavailable: {error}")
                raise
            with self.assertRaisesRegex(
                selector.GateEvidenceError,
                "escapes declared root",
            ):
                selector._load_state_safe(root)

    @unittest.skipUnless(
        hasattr(os, "symlink"),
        "symbolic links are not supported",
    )
    def test_destination_symlink_escape_is_rejected(self):
        graph = build_graph(
            ROOT, source_state_commit=UNIT_INPUT_COMMIT
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            destination = base / "destination"
            outside = base / "outside"
            destination.mkdir()
            outside.mkdir()
            try:
                os.symlink(
                    outside,
                    destination / "paper_techgraphs",
                    target_is_directory=True,
                )
            except OSError as error:
                if getattr(error, "winerror", None) == 1314:
                    self.skipTest(f"symbolic links unavailable: {error}")
                raise
            with self.assertRaisesRegex(
                selector.GateEvidenceError,
                "escapes declared root",
            ):
                write_outputs(destination, graph)
            self.assertEqual(tuple(outside.iterdir()), ())

    def test_mid_publish_failure_rolls_back_all_selector_outputs(self):
        graph = build_graph(
            ROOT, source_state_commit=UNIT_INPUT_COMMIT
        )
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            paths = write_outputs(destination, graph)
            before = {path: path.read_bytes() for path in paths}
            original_replace = os.replace

            def fail_on_graph(source, target):
                if Path(target).name == TRACKED_OUTPUTS[1]:
                    raise OSError("injected selector publish failure")
                return original_replace(source, target)

            with (
                patch.object(
                    selector.os,
                    "replace",
                    side_effect=fail_on_graph,
                ),
                self.assertRaisesRegex(
                    OSError,
                    "injected selector publish failure",
                ),
            ):
                write_outputs(destination, graph)
            self.assertEqual(
                before,
                {path: path.read_bytes() for path in paths},
            )
            self.assertFalse(
                any(
                    path.name.startswith(".selector-techgraph-stage-")
                    for path in destination.iterdir()
                )
            )

    def test_tracked_outputs_match_a_fresh_render(self):
        bound_commit = published_input_commit()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            historical_root = base / "historical-root"
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--shared",
                    "-q",
                    str(ROOT),
                    str(historical_root),
                ],
                check=True,
            )
            subprocess.run(
                ["git", "checkout", "--detach", "-q", bound_commit],
                cwd=historical_root,
                check=True,
            )
            graph = build_graph(
                historical_root,
                source_state_commit=bound_commit,
            )
            fresh_root = base / "fresh"
            fresh_root.mkdir()
            fresh_paths = write_outputs(fresh_root, graph)
            for fresh_path in fresh_paths:
                tracked_path = ROOT / "paper_techgraphs" / fresh_path.name
                with self.subTest(path=fresh_path.name):
                    self.assertIn(fresh_path.name, TRACKED_OUTPUTS)
                    self.assertEqual(
                        tracked_path.read_bytes(),
                        fresh_path.read_bytes(),
                    )

    def test_live_state_and_node_sources_must_match_declared_commit(self):
        paths = selector.SELECTOR_SOURCE_STATE_INPUTS
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in paths:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / relative).read_bytes())
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.name", "Selector Test"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "config",
                    "user.email",
                    "selector@example.invalid",
                ],
                cwd=root,
                check=True,
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "selector inputs"],
                cwd=root,
                check=True,
            )
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            for relative in (
                "research_state.yaml",
                selector.NODE_SPECS[0][1],
            ):
                path = root / relative
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                with self.subTest(relative=relative):
                    with self.assertRaisesRegex(
                        selector.GateEvidenceError,
                        "does not match implementation-input commit",
                    ):
                        build_graph(
                            root,
                            source_state_commit=commit,
                        )
                path.write_bytes(original)

    def test_dynamic_import_binding_model_tracks_aliases(self):
        tree = ast.parse(
            "\n".join(
                (
                    "import importlib as module_alias",
                    (
                        "from importlib import import_module "
                        "as imported_loader"
                    ),
                    "import builtins as builtins_alias",
                    (
                        "from builtins import __import__ "
                        "as imported_builtin"
                    ),
                    "assigned_loader = module_alias.import_module",
                    "copied_loader = imported_loader",
                    "assigned_loader('research.alias_one')",
                    "copied_loader('research.alias_two')",
                    "builtins_alias.__import__('research.alias_three')",
                    "imported_builtin('research.alias_four')",
                )
            )
        )
        self.assertEqual(
            selector._literal_dynamic_imports(tree, "alias_probe.py"),
            (
                "research.alias_one",
                "research.alias_two",
                "research.alias_three",
                "research.alias_four",
            ),
        )
        nonliteral = ast.parse(
            "\n".join(
                (
                    "from importlib import import_module as imported_loader",
                    "loader = imported_loader",
                    "target = 'research.alias_probe'",
                    "loader(target)",
                )
            )
        )
        with self.assertRaisesRegex(
            selector.LocalImportPreflightError,
            "nonliteral dynamic import",
        ):
            selector._literal_dynamic_imports(
                nonliteral,
                "alias_probe.py",
            )

    def test_real_cli_rejects_aliased_dynamic_imports_before_outputs(self):
        cases = (
            (
                "assigned_alias_literal",
                "\n".join(
                    (
                        "import importlib as selector_importlib",
                        (
                            "selector_loader = "
                            "selector_importlib.import_module"
                        ),
                        (
                            "selector_loader("
                            "'research.mat_sab.selector_alias_probe')"
                        ),
                        "",
                    )
                ),
                "executable registry does not match recursive import closure",
            ),
            (
                "copied_alias_nonliteral",
                "\n".join(
                    (
                        (
                            "from importlib import import_module "
                            "as imported_selector_loader"
                        ),
                        "selector_loader = imported_selector_loader",
                        (
                            "selector_target = "
                            "'research.mat_sab.selector_alias_probe'"
                        ),
                        "selector_loader(selector_target)",
                        "",
                    )
                ),
                "nonliteral dynamic import",
            ),
        )
        for name, source, expected_error in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root, _ = self._clone_working_selector(tmp)
                dependency = root / "research/mat_sab/finite_linear.py"
                dependency.write_text(
                    dependency.read_text(encoding="ascii") + "\n" + source,
                    encoding="ascii",
                    newline="\n",
                )
                marker = root / "UNVERIFIED_SELECTOR_ALIAS_EXECUTED"
                probe = root / "research/mat_sab/selector_alias_probe.py"
                probe.write_text(
                    "\n".join(
                        (
                            "from pathlib import Path",
                            (
                                "Path('UNVERIFIED_SELECTOR_ALIAS_EXECUTED')"
                                ".write_text('executed\\n', encoding='ascii')"
                            ),
                            "",
                        )
                    ),
                    encoding="ascii",
                    newline="\n",
                )
                subprocess.run(["git", "add", "-A"], cwd=root, check=True)
                subprocess.run(
                    ["git", "commit", "-q", "-m", name],
                    cwd=root,
                    check=True,
                )
                commit = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                destination = root / "selector-alias-output"
                destination.mkdir()
                environment = os.environ.copy()
                environment["PYTHONDONTWRITEBYTECODE"] = "1"
                completed = subprocess.run(
                    [
                        sys.executable,
                        "scripts/build_mat_sab_selector_techgraph.py",
                        "--destination-root",
                        str(destination),
                        "--source-state-commit",
                        commit,
                    ],
                    cwd=root,
                    env=environment,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(expected_error, completed.stderr)
                self.assertFalse(marker.exists())
                self.assertFalse(any(destination.rglob("*")))

    def test_real_cli_rejects_cross_checkout_root_before_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            other_root = Path(tmp) / "other-root"
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--shared",
                    "-q",
                    str(ROOT),
                    str(other_root),
                ],
                check=True,
            )
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=other_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            destination = Path(tmp) / "selector-output"
            destination.mkdir()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(
                        ROOT
                        / "scripts/build_mat_sab_selector_techgraph.py"
                    ),
                    "--root",
                    str(other_root),
                    "--destination-root",
                    str(destination),
                    "--source-state-commit",
                    commit,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn(
                "requested root does not match launcher checkout root",
                completed.stderr,
            )
            self.assertFalse(any(destination.rglob("*")))

    def test_real_cli_ignores_valid_adjacent_timestamp_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, commit = self._clone_working_selector(tmp)
            no_write_environment = os.environ.copy()
            no_write_environment["PYTHONDONTWRITEBYTECODE"] = "1"
            baseline = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_mat_sab_selector_techgraph.py",
                    "--source-state-commit",
                    commit,
                ],
                cwd=root,
                env=no_write_environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr)
            outputs = tuple(
                root / "paper_techgraphs" / name
                for name in TRACKED_OUTPUTS
            )
            before_outputs = {
                path: path.read_bytes()
                for path in outputs
            }

            for cache_dir in sorted(
                root.rglob("__pycache__"),
                reverse=True,
            ):
                shutil.rmtree(cache_dir)
            marker = root / "STALE_SELECTOR_CACHE_EXECUTED"
            source = root / "research/__init__.py"
            _install_valid_timestamp_cache(source, marker.name)
            environment = os.environ.copy()
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            environment.pop("PYTHONPYCACHEPREFIX", None)
            control = subprocess.run(
                [sys.executable, "-c", "import research"],
                cwd=root,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(control.returncode, 0, control.stderr)
            self.assertTrue(marker.exists())
            marker.unlink()

            before_caches = _adjacent_cache_snapshot(root)
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_mat_sab_selector_techgraph.py",
                    "--source-state-commit",
                    commit,
                ],
                cwd=root,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                completed.stdout.strip(),
                "PASS_CANDIDATE_A_TECHGRAPH_ANCHORED",
            )
            self.assertFalse(marker.exists())
            self.assertEqual(
                before_outputs,
                {path: path.read_bytes() for path in outputs},
            )
            self.assertEqual(
                before_caches,
                _adjacent_cache_snapshot(root),
            )

    def test_executable_registry_matches_recursive_local_import_closure(self):
        tree = ast.parse(
            (
                ROOT / "scripts/build_mat_sab_selector_techgraph.py"
            ).read_text(encoding="ascii")
        )
        local_imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                local_imports.extend(
                    alias.name
                    for alias in node.names
                    if alias.name.startswith(("research", "scripts"))
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith(("research", "scripts")):
                    local_imports.append(node.module)
        self.assertEqual(local_imports, [])
        with tempfile.TemporaryDirectory() as tmp:
            root, commit = self._clone_working_selector(tmp)
            derived = selector._derive_local_import_closure(
                root,
                commit,
                selector.SELECTOR_LOCAL_IMPORT_ROOTS,
            )
        self.assertEqual(derived, SELECTOR_LOCAL_IMPORT_CLOSURE)
        self.assertEqual(derived, selector.SELECTOR_EXECUTABLE_INPUTS)

    def test_real_cli_preflights_every_local_dependency_class(self):
        probes = tuple(
            relative
            for relative in SELECTOR_LOCAL_IMPORT_CLOSURE
            if relative != "scripts/build_mat_sab_selector_techgraph.py"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            subprocess.run(
                ["git", "clone", "--shared", "-q", str(ROOT), str(root)],
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Selector Test"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "config",
                    "user.email",
                    "selector@example.invalid",
                ],
                cwd=root,
                check=True,
            )
            for relative in SELECTOR_LOCAL_IMPORT_CLOSURE:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / relative).read_bytes())
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "commit",
                    "--allow-empty",
                    "-q",
                    "-m",
                    "selector preflight inputs",
                ],
                cwd=root,
                check=True,
            )
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            marker = root / "UNVERIFIED_SELECTOR_IMPORT_EXECUTED"
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            for index, relative in enumerate(probes):
                path = root / relative
                original = path.read_bytes()
                path.write_bytes(
                    original
                    + (
                        b"\nopen('UNVERIFIED_SELECTOR_IMPORT_EXECUTED', "
                        b"'w').write('executed')\n"
                    )
                )
                destination = root / f"selector-probe-output-{index}"
                destination.mkdir()
                with self.subTest(relative=relative):
                    completed = subprocess.run(
                        [
                            sys.executable,
                            "scripts/build_mat_sab_selector_techgraph.py",
                            "--root",
                            str(root),
                            "--destination-root",
                            str(destination),
                            "--source-state-commit",
                            commit,
                        ],
                        cwd=root,
                        env=environment,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn(
                        "local import preflight",
                        completed.stderr,
                    )
                    self.assertFalse(marker.exists())
                    self.assertFalse(any(destination.rglob("*")))
                path.write_bytes(original)
                marker.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
