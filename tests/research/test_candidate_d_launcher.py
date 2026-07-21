import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import scripts.apply_candidate_d_admission as closeout
import scripts.run_candidate_d_admission as gate


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = "scripts/candidate_d_task9_launcher.py"
RUN_DATE = "2026-07-21"
EXECUTION_PLATFORM = (
    "Windows-PowerShell; CPython-3.12; evidence-controller-only; "
    "no-performance-claim"
)
CONTROLLER_PATHS = (
    LAUNCHER_PATH,
    "scripts/run_candidate_d_admission.py",
    "scripts/apply_candidate_d_admission.py",
    "scripts/mat_sab_research_state.py",
    "research/mat_sab/candidate_d_stage_replay.py",
    "docs/candidate_d_task9_replay_contract.md",
    "docs/candidate_d_task9_threat_model.md",
)


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=check,
        capture_output=True,
        text=True,
    )


def _controller_commit(root: Path = ROOT) -> str:
    return _git(
        root,
        "log",
        "-1",
        "--format=%H",
        "--",
        *CONTROLLER_PATHS,
    ).stdout.strip()


class CandidateDLauncherTests(unittest.TestCase):
    def _clone(self, directory: str) -> Path:
        clone = Path(directory) / "repo"
        subprocess.run(
            ["git", "clone", "--no-local", "-q", str(ROOT), str(clone)],
            check=True,
            capture_output=True,
            text=True,
        )
        source_evidence = ROOT / "references/candidate_d_fulltext"
        destination_evidence = clone / "references/candidate_d_fulltext"
        for source in source_evidence.iterdir():
            if source.is_file() and source.name != ".gitignore":
                shutil.copy2(source, destination_evidence / source.name)
        return clone

    def _launcher_blob(self, root: Path, controller_commit: str) -> bytes:
        completed = subprocess.run(
            ["git", "show", f"{controller_commit}:{LAUNCHER_PATH}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        self.assertEqual(
            completed.returncode,
            0,
            "the controller commit does not provide the authoritative launcher",
        )
        return completed.stdout

    def _invoke(
        self,
        root: Path,
        *,
        controller_commit: str,
        input_commit: str = gate.CURRENT_INPUT_COMMIT,
        environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        launcher = self._launcher_blob(root, controller_commit)
        return subprocess.run(
            [
                sys.executable,
                "-I",
                "-S",
                "-",
                "--mode",
                "run",
                "--root",
                str(root),
                "--input-commit",
                input_commit,
                "--controller-commit",
                controller_commit,
                "--run-date",
                RUN_DATE,
                "--execution-platform",
                EXECUTION_PLATFORM,
            ],
            cwd=root,
            input=launcher,
            check=False,
            capture_output=True,
            env=environment,
        )

    def test_authoritative_commands_use_git_blob_isolated_launcher(self):
        result = closeout.AdmissionResult(
            d0_status="PASS",
            d0_decision="PASS_D0_CANDIDATE_D_BASELINES_FROZEN",
            d1_status="BLOCK",
            d1_decision="BLOCK_D1_REQUIRED_FULLTEXT_OR_REVIEW_MISSING",
            d1_missing_evidence=("NTRU_AMORT_2026_068",),
            d2_status="SKIPPED_D1_BLOCK",
            d2_decision="",
            d2_replay_authenticated=False,
            d3_replay_authenticated=False,
            gamma_count=None,
            negative_controls_status="SKIPPED_D1_BLOCK",
            binding_status="SKIPPED_D1_BLOCK",
            security_status="SKIPPED_D1_BLOCK",
            noise_status="SKIPPED_D1_BLOCK",
            complete_cost_status="SKIPPED_D1_BLOCK",
            resource_status="SKIPPED_D1_BLOCK",
            pessimistic_projection="",
            pre_application_permission=False,
            decision=gate.BLOCK,
            resume_condition="blocked",
            input_commit=gate.CURRENT_INPUT_COMMIT,
            controller_commit="a" * 40,
            run_date=RUN_DATE,
            execution_platform=EXECUTION_PLATFORM,
            source_hashes=(),
            runtime_source_hashes=(),
        )

        generator = closeout._generator_command(result)
        apply = closeout._apply_command(result)
        for command, mode in ((generator, "run"), (apply, "apply")):
            self.assertTrue(
                command.startswith(
                    f"git show {'a' * 40}:{LAUNCHER_PATH} | python -I -S - "
                )
            )
            self.assertIn(f"--mode {mode}", command)
            self.assertNotIn(f"python scripts/{mode}_candidate_d_admission.py", command)

    def test_recorded_runtime_closure_includes_launcher_and_package_initializers(self):
        required = {
            LAUNCHER_PATH,
            "scripts/__init__.py",
            "research/__init__.py",
            "research/mat_sab/__init__.py",
            "scripts/run_candidate_d_admission.py",
            "scripts/apply_candidate_d_admission.py",
            "scripts/mat_sab_research_state.py",
            "research/mat_sab/candidate_d_stage_replay.py",
        }

        self.assertTrue(required.issubset(set(gate.RUNTIME_SOURCES)))

    def test_pythonpath_shadow_cannot_execute_before_controller_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._clone(directory)
            marker = Path(directory) / "pythonpath-shadow-executed"
            shadow = Path(directory) / "shadow"
            shadow.mkdir()
            (shadow / "csv.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed', encoding='ascii')\n"
                "raise RuntimeError('PYTHONPATH shadow executed')\n",
                encoding="ascii",
                newline="",
            )
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(shadow)

            completed = self._invoke(
                root,
                controller_commit=_controller_commit(),
                environment=environment,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr.decode())
            self.assertEqual(completed.stdout.decode().strip(), gate.BLOCK)
            self.assertFalse(marker.exists())

    def test_script_directory_shadow_cannot_execute_before_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._clone(directory)
            marker = Path(directory) / "script-directory-shadow-executed"
            (root / "scripts/csv.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed', encoding='ascii')\n"
                "raise RuntimeError('script-directory shadow executed')\n",
                encoding="ascii",
                newline="",
            )

            completed = self._invoke(root, controller_commit=_controller_commit())

            self.assertEqual(completed.returncode, 0, completed.stderr.decode())
            self.assertEqual(completed.stdout.decode().strip(), gate.BLOCK)
            self.assertFalse(marker.exists())

    def test_modified_worktree_modules_and_initializers_never_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._clone(directory)
            attacked = (
                "scripts/__init__.py",
                "research/__init__.py",
                "research/mat_sab/__init__.py",
                "scripts/mat_sab_research_state.py",
                "research/mat_sab/candidate_d_literature.py",
            )
            markers = []
            for index, relative in enumerate(attacked):
                path = root / relative
                marker = Path(directory) / f"mutable-import-{index}"
                markers.append(marker)
                injection = (
                    "from pathlib import Path as _AttackPath\n"
                    f"_AttackPath({str(marker)!r}).write_text("
                    "'executed', encoding='ascii')\n"
                )
                original = path.read_text(encoding="ascii")
                future = "from __future__ import annotations\n"
                if future in original:
                    changed = original.replace(future, future + injection, 1)
                else:
                    changed = injection + original
                path.write_text(changed, encoding="ascii", newline="")

            completed = self._invoke(root, controller_commit=_controller_commit())

            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue(
                b"working input differs from pinned commit" in completed.stderr
                or b"working controller source differs from controller commit"
                in completed.stderr,
                completed.stderr.decode(),
            )
            self.assertTrue(all(not marker.exists() for marker in markers))

    def test_composite_tree_uses_future_input_science_under_frozen_controller(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._clone(directory)
            controller = _controller_commit()
            _git(root, "config", "user.name", "Candidate D launcher fixture")
            _git(
                root,
                "config",
                "user.email",
                "candidate-d-launcher@example.invalid",
            )
            future_block = "BLOCK_D1_FUTURE_REVIEWED_INPUT"
            literature = root / "research/mat_sab/candidate_d_literature.py"
            source = literature.read_text(encoding="ascii")
            source = source.replace(
                'BLOCK_D1 = "BLOCK_D1_REQUIRED_FULLTEXT_OR_REVIEW_MISSING"',
                f'BLOCK_D1 = "{future_block}"',
                1,
            )
            literature.write_text(source, encoding="ascii", newline="")
            registry = root / "literature/candidate_d_source_registry.json"
            registry.write_text(
                registry.read_text(encoding="ascii") + " ",
                encoding="ascii",
                newline="",
            )
            generated = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    str(root / "scripts/run_candidate_d_d1_literature.py"),
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertEqual(generated.stdout.strip(), future_block)
            _git(root, "add", "research/mat_sab/candidate_d_literature.py")
            _git(root, "add", "literature/candidate_d_source_registry.json")
            for relative in gate.D1_OUTPUTS:
                _git(root, "add", relative)
            _git(root, "commit", "-qm", "fixture: future reviewed D1 input")
            input_commit = _git(root, "rev-parse", "HEAD").stdout.strip()

            completed = self._invoke(
                root,
                controller_commit=controller,
                input_commit=input_commit,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr.decode())
            self.assertEqual(completed.stdout.decode().strip(), gate.BLOCK)
            evidence = json.loads(
                (root / "repro/candidate_d_admission/decision_evidence.json").read_text(
                    encoding="ascii"
                )
            )
            self.assertEqual(evidence["gate_evidence"]["d1_decision"], future_block)


if __name__ == "__main__":
    unittest.main()
