import json
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

import research.mat_sab.candidate_d_stage_replay as replay
import scripts.run_candidate_d_admission as gate


ROOT = Path(__file__).resolve().parents[2]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="ascii", newline="")


class CandidateDReplayContractTests(unittest.TestCase):
    def _repo(self, directory: str) -> Path:
        root = Path(directory)
        _git(root, "init", "-q")
        _git(root, "config", "user.name", "Candidate D fixture")
        _git(root, "config", "user.email", "candidate-d-fixture@example.invalid")
        return root

    def test_handwritten_d2_outputs_have_no_authority_without_canonical_replayer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            for relative in gate.D2_OUTPUTS:
                _write(root, relative, "self_reported_equal_hashes=0\n")
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "fixture: handwritten D2")
            commit = _git(root, "rev-parse", "HEAD")

            with self.assertRaises(replay.StageReplayUnavailable):
                replay.execute_stage_replay(
                    root,
                    gate.D2_REPLAY_CONTRACT,
                    input_commit=commit,
                    controller_commit=commit,
                )

    def test_handwritten_d3_outputs_have_no_authority_without_canonical_replayer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            for relative in gate.D3_OUTPUTS:
                _write(root, relative, "fabricated_anchor_projection=100\n")
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "fixture: handwritten D3")
            commit = _git(root, "rev-parse", "HEAD")

            with self.assertRaises(replay.StageReplayUnavailable):
                replay.execute_stage_replay(
                    root,
                    gate.D3_REPLAY_CONTRACT,
                    input_commit=commit,
                    controller_commit=commit,
                )

    def test_non_scientific_fixture_replayer_proves_controller_mechanics_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            runner = textwrap.dedent(
                """
                import argparse
                import json
                from pathlib import Path

                parser = argparse.ArgumentParser()
                parser.add_argument("--root", required=True)
                parser.add_argument("--output-root", required=True)
                parser.add_argument("--input-commit", required=True)
                parser.add_argument("--controller-commit", required=True)
                args = parser.parse_args()
                output = Path(args.output_root)
                artifact = output / "fixture/output.txt"
                artifact.parent.mkdir(parents=True)
                with artifact.open("w", encoding="ascii", newline="") as handle:
                    handle.write("derived fixture output\\n")
                manifest = {
                    "schema": "candidate-d-stage-replay-v1",
                    "stage": "FIXTURE",
                    "input_commit": args.input_commit,
                    "controller_commit": args.controller_commit,
                    "decision": "PASS_FIXTURE_CONTROLLER_MECHANICS",
                    "canonical_outputs": ["fixture/output.txt"],
                    "scientific_authority": False,
                }
                (output / "candidate_d_stage_replay.json").write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\\n",
                    encoding="ascii",
                )
                """
            ).lstrip()
            _write(root, "scripts/fixture_replayer.py", runner)
            _write(root, "research/fixture_model.py", "MODEL = 'fixture-only'\n")
            _write(root, "fixture/output.txt", "derived fixture output\n")
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "fixture: deterministic replay")
            commit = _git(root, "rev-parse", "HEAD")
            contract = replay.StageReplayContract(
                stage="FIXTURE",
                runner="scripts/fixture_replayer.py",
                scientific_sources=("research/fixture_model.py",),
                required_inputs=(),
                canonical_outputs=("fixture/output.txt",),
                decisions=("PASS_FIXTURE_CONTROLLER_MECHANICS",),
                scientific_authority=False,
            )

            result = replay.execute_stage_replay(
                root,
                contract,
                input_commit=commit,
                controller_commit=commit,
            )
            self.assertEqual(result.decision, "PASS_FIXTURE_CONTROLLER_MECHANICS")
            self.assertFalse(result.scientific_authority)
            self.assertEqual(result.output_hashes[0][0], "fixture/output.txt")

    def test_controller_commit_rejects_uncommitted_runtime_and_wrong_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            for relative in gate.RUNTIME_SOURCES:
                _write(root, relative, f"committed:{relative}\n")
            _git(root, "add", ".")
            _git(root, "commit", "-qm", "fixture: controller")
            controller = _git(root, "rev-parse", "HEAD")

            hashes = gate._controller_source_hashes(root, controller)
            self.assertEqual(tuple(path for path, _ in hashes), gate.RUNTIME_SOURCES)
            _write(root, gate.RUNTIME_SOURCES[0], "uncommitted mutation\n")
            with self.assertRaisesRegex(
                gate.AdmissionEvidenceError, "controller source differs"
            ):
                gate._controller_source_hashes(root, controller)
            with self.assertRaises(gate.AdmissionEvidenceError):
                gate._controller_source_hashes(root, "0" * 40)

    def test_resume_text_has_explicit_early_exit_branches(self):
        text = gate.resume_condition_for(
            "D1_BLOCK", controller_commit="a" * 40
        )
        self.assertIn("D1 REJECT/BLOCK", text)
        self.assertIn("do not run D2", text)
        self.assertIn("D2 REJECT/BLOCK", text)
        self.assertIn("do not run D3", text)
        self.assertIn("--controller-commit " + "a" * 40, text)
        self.assertNotIn("--input-commit <new-D3-commit> and", text)

    def test_production_contracts_name_all_mandatory_semantic_sources(self):
        self.assertTrue(gate.D2_REPLAY_CONTRACT.scientific_authority)
        self.assertTrue(gate.D3_REPLAY_CONTRACT.scientific_authority)
        self.assertIn(
            "research/mat_sab/candidate_d_operator_closure.py",
            gate.D2_REPLAY_CONTRACT.scientific_sources,
        )
        self.assertIn(
            "research/mat_sab/candidate_d_admission.py",
            gate.D3_REPLAY_CONTRACT.scientific_sources,
        )
        self.assertIn(
            "repro/stage331_current_head_highstat_refresh/summary.csv",
            gate.D3_REPLAY_CONTRACT.required_inputs,
        )
        self.assertIn(
            "repro/stage322_schedule_profile_attribution/profile_summary.csv",
            gate.D3_REPLAY_CONTRACT.required_inputs,
        )


if __name__ == "__main__":
    unittest.main()
