import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.apply_candidate_c_rank_bounded_gate as closeout
import scripts.build_mat_sab_selector_techgraph as selector
import scripts.run_candidate_c_rank_bounded_gate as gate


ROOT = Path(__file__).resolve().parents[2]
WORKING_LOCAL_PATHS = (
    "research/__init__.py",
    "research/mat_sab/__init__.py",
    "research/mat_sab/candidate_c_operator_tensor.py",
    "research/mat_sab/candidate_c_registered_replay.py",
    "research/mat_sab/candidate_c_schedule.py",
    "research/mat_sab/finite_linear.py",
    "research/mat_sab/rank_bounded_state_model.py",
    "scripts/__init__.py",
    "scripts/apply_candidate_c_rank_bounded_gate.py",
    "scripts/build_mat_sab_selector_techgraph.py",
    "scripts/mat_sab_research_state.py",
    "scripts/run_candidate_c_rank_bounded_gate.py",
)
MUTABLE_CLOSEOUT_PATHS = (
    "research_state.yaml",
    "hypotheses/hypothesis_register.yaml",
    "repro/run_log.csv",
    "repro/artifact_manifest.md",
    "repro/reproduction_checklist.md",
)


def _git_head(root):
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class CandidateCCliRuntimeTests(unittest.TestCase):
    @staticmethod
    def _clone_working_cli(directory):
        root = Path(directory) / "root"
        subprocess.run(
            ["git", "clone", "--shared", "-q", str(ROOT), str(root)],
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Candidate C CLI Test"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "config",
                "user.email",
                "candidate-c-cli-test@example.invalid",
            ],
            cwd=root,
            check=True,
        )
        for relative in WORKING_LOCAL_PATHS:
            source = ROOT / relative
            if not source.exists():
                continue
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "commit",
                "--allow-empty",
                "-q",
                "-m",
                "working unified CLI bootstrap",
            ],
            cwd=root,
            check=True,
        )
        return root, _git_head(root)

    @staticmethod
    def _run(root, arguments, *, environment=None):
        return subprocess.run(
            [sys.executable, *arguments],
            cwd=root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    @staticmethod
    def _snapshot(root):
        return {
            relative: (
                (root / relative).read_bytes()
                if (root / relative).exists()
                else None
            )
            for relative in MUTABLE_CLOSEOUT_PATHS
        }

    def test_every_cli_registry_includes_scripts_initializer(self):
        self.assertIn(
            "scripts/__init__.py",
            gate.GENERATOR_EXECUTABLE_INPUTS,
        )
        self.assertIn(
            "scripts/__init__.py",
            closeout.CLOSEOUT_EXECUTABLE_INPUTS,
        )
        self.assertIn(
            "scripts/__init__.py",
            selector.SELECTOR_EXECUTABLE_INPUTS,
        )
        self.assertIn(
            (ROOT / "scripts/__init__.py").read_bytes(),
            (b"", b"\n"),
        )

    def test_loaded_module_origin_validation_rejects_wrong_path(self):
        local_module = sys.modules["research"]
        for launcher, paths in (
            (gate, gate.GENERATOR_EXECUTABLE_INPUTS),
            (closeout, closeout.CLOSEOUT_EXECUTABLE_INPUTS),
            (selector, selector.SELECTOR_EXECUTABLE_INPUTS),
        ):
            with self.subTest(launcher=launcher.__name__):
                with (
                    patch.object(
                        local_module,
                        "__file__",
                        str(ROOT / "wrong/research/__init__.py"),
                    ),
                    self.assertRaisesRegex(
                        launcher.LocalImportPreflightError,
                        "loaded local module origin mismatch: research",
                    ),
                ):
                    launcher._validate_loaded_local_module_origins(
                        ROOT,
                        paths,
                    )

    def test_real_clis_prefer_verified_root_over_earlier_import_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, commit = self._clone_working_cli(tmp)
            alternate = Path(tmp) / "alternate"
            alternate_research_marker = (
                Path(tmp) / "ALTERNATE_RESEARCH_EXECUTED"
            )
            alternate_scripts_marker = (
                Path(tmp) / "ALTERNATE_SCRIPTS_EXECUTED"
            )
            for package, marker in (
                ("research", alternate_research_marker),
                ("scripts", alternate_scripts_marker),
            ):
                initializer = alternate / package / "__init__.py"
                initializer.parent.mkdir(parents=True, exist_ok=True)
                initializer.write_text(
                    "\n".join(
                        (
                            "from pathlib import Path",
                            (
                                f"Path({str(marker)!r}).write_text("
                                "'executed\\n', encoding='ascii')"
                            ),
                            "",
                        )
                    ),
                    encoding="ascii",
                    newline="\n",
                )
            environment = os.environ.copy()
            prior_path = environment.get("PYTHONPATH")
            environment["PYTHONPATH"] = os.pathsep.join(
                part
                for part in (
                    str(alternate),
                    str(root),
                    prior_path,
                )
                if part
            )

            selector_output = Path(tmp) / "selector-output"
            selector_output.mkdir()
            selected = self._run(
                root,
                (
                    "scripts/build_mat_sab_selector_techgraph.py",
                    "--destination-root",
                    str(selector_output),
                    "--source-state-commit",
                    commit,
                ),
                environment=environment,
            )
            self.assertEqual(selected.returncode, 0, selected.stderr)

            generated = self._run(
                root,
                (
                    "scripts/run_candidate_c_rank_bounded_gate.py",
                    "--input-commit",
                    commit,
                ),
                environment=environment,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertEqual(generated.stdout.strip(), gate.REJECT)

            applied = self._run(
                root,
                (
                    "scripts/apply_candidate_c_rank_bounded_gate.py",
                    "--input-commit",
                    commit,
                ),
                environment=environment,
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual(applied.stdout.strip(), gate.REJECT)
            self.assertFalse(alternate_research_marker.exists())
            self.assertFalse(alternate_scripts_marker.exists())

    def test_real_clis_reject_preloaded_local_module_before_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, commit = self._clone_working_cli(tmp)
            before = self._snapshot(root)
            commands = (
                (
                    "generator",
                    "scripts/run_candidate_c_rank_bounded_gate.py",
                    (
                        "--destination-root",
                        str(Path(tmp) / "generator-output"),
                        "--input-commit",
                        commit,
                    ),
                ),
                (
                    "closeout",
                    "scripts/apply_candidate_c_rank_bounded_gate.py",
                    ("--input-commit", commit),
                ),
                (
                    "selector",
                    "scripts/build_mat_sab_selector_techgraph.py",
                    (
                        "--destination-root",
                        str(Path(tmp) / "selector-output"),
                        "--source-state-commit",
                        commit,
                    ),
                ),
            )
            for name, script, arguments in commands:
                destination = next(
                    (
                        Path(arguments[index + 1])
                        for index, value in enumerate(arguments)
                        if value == "--destination-root"
                    ),
                    None,
                )
                if destination is not None:
                    destination.mkdir()
                wrapper = "\n".join(
                    (
                        "import runpy",
                        "import sys",
                        "import types",
                        "module = types.ModuleType('research')",
                        (
                            "module.__file__ = "
                            f"{str(Path(tmp) / 'fake/research/__init__.py')!r}"
                        ),
                        (
                            "module.__path__ = "
                            f"[{str(Path(tmp) / 'fake/research')!r}]"
                        ),
                        "sys.modules['research'] = module",
                        f"sys.argv = {[script, *arguments]!r}",
                        f"runpy.run_path({script!r}, run_name='__main__')",
                    )
                )
                completed = self._run(
                    root,
                    ("-c", wrapper),
                )
                with self.subTest(name=name):
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn(
                        "declared local module already loaded: research",
                        completed.stderr,
                    )
                    if destination is not None:
                        self.assertFalse(any(destination.rglob("*")))
                    self.assertEqual(before, self._snapshot(root))


if __name__ == "__main__":
    unittest.main()
