import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
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


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD")


def _fixture_runner(
    imports: str = "", body: str = "", epilogue: str = ""
) -> str:
    return f'''import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
{imports}

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--output-root", required=True)
parser.add_argument("--input-commit", required=True)
parser.add_argument("--controller-commit", required=True)
args = parser.parse_args()
{body}
output = Path(args.output_root)
artifact = output / "fixture/output.txt"
artifact.parent.mkdir(parents=True)
artifact.write_text("derived fixture output\\n", encoding="ascii", newline="")
manifest = {{
    "schema": "candidate-d-stage-replay-v1",
    "stage": "FIXTURE",
    "input_commit": args.input_commit,
    "controller_commit": args.controller_commit,
    "decision": "PASS_FIXTURE_CONTROLLER_MECHANICS",
    "canonical_outputs": ["fixture/output.txt"],
    "scientific_authority": False,
}}
(output / "candidate_d_stage_replay.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\\n",
    encoding="ascii",
    newline="",
)
{epilogue}
'''


def _fixture_contract(*scientific_sources: str) -> replay.StageReplayContract:
    return replay.StageReplayContract(
        stage="FIXTURE",
        runner="scripts/fixture_replayer.py",
        scientific_sources=tuple(scientific_sources),
        required_inputs=(),
        canonical_outputs=("fixture/output.txt",),
        decisions=("PASS_FIXTURE_CONTROLLER_MECHANICS",),
        scientific_authority=False,
    )


class CandidateDReplayContractTests(unittest.TestCase):
    def _repo(self, directory: str) -> Path:
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
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
            _write(root, "scripts/__init__.py", "")
            _write(root, "research/__init__.py", "")
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner("import research.fixture_model"),
            )
            _write(root, "research/fixture_model.py", "MODEL = 'fixture-only'\n")
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: deterministic replay")
            contract = _fixture_contract(
                "research/__init__.py",
                "research/fixture_model.py",
                "scripts/__init__.py",
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

    def test_rejects_undeclared_direct_and_transitive_local_imports(self):
        cases = (
            (
                "direct",
                "import research.direct_source",
                {"research/direct_source.py": "VALUE = 1\n"},
            ),
            (
                "transitive",
                "import research.first_source",
                {
                    "research/first_source.py": "import research.second_source\n",
                    "research/second_source.py": "VALUE = 2\n",
                },
            ),
        )
        for name, imports, sources in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self._repo(directory)
                _write(root, "scripts/__init__.py", "")
                _write(root, "research/__init__.py", "")
                _write(root, "scripts/fixture_replayer.py", _fixture_runner(imports))
                for relative, content in sources.items():
                    _write(root, relative, content)
                _write(root, "fixture/output.txt", "derived fixture output\n")
                commit = _commit(root, f"fixture: {name} import")

                with self.assertRaisesRegex(
                    replay.StageReplayError,
                    "scientific source registry does not match recursive import closure",
                ):
                    replay.execute_stage_replay(
                        root,
                        _fixture_contract(
                            "research/__init__.py", "scripts/__init__.py"
                        ),
                        input_commit=commit,
                        controller_commit=commit,
                    )

    def test_rejects_unsorted_and_duplicate_scientific_registries(self):
        registries = (
            ("scripts/__init__.py", "research/__init__.py"),
            ("scripts/__init__.py", "scripts/__init__.py"),
        )
        for registry in registries:
            with self.subTest(registry=registry), tempfile.TemporaryDirectory() as directory:
                root = self._repo(directory)
                _write(root, "scripts/__init__.py", "")
                _write(root, "research/__init__.py", "")
                _write(root, "scripts/fixture_replayer.py", _fixture_runner())
                _write(root, "fixture/output.txt", "derived fixture output\n")
                commit = _commit(root, "fixture: malformed registry")
                with self.assertRaisesRegex(
                    replay.StageReplayError, "registry must be sorted and unique"
                ):
                    replay.execute_stage_replay(
                        root,
                        _fixture_contract(*registry),
                        input_commit=commit,
                        controller_commit=commit,
                    )

    def test_rejects_unresolved_and_shadowed_local_modules(self):
        cases = (
            ("unresolved", {"research/__init__.py": ""}, "unresolved local module"),
            (
                "shadowed",
                {
                    "research/__init__.py": "",
                    "research/local_source.py": "VALUE = 1\n",
                    "research/local_source/__init__.py": "VALUE = 2\n",
                },
                "shadow package initializer",
            ),
        )
        for name, sources, expected in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self._repo(directory)
                _write(root, "scripts/__init__.py", "")
                for relative, content in sources.items():
                    _write(root, relative, content)
                imported = "missing_source" if name == "unresolved" else "local_source"
                _write(
                    root,
                    "scripts/fixture_replayer.py",
                    _fixture_runner(f"import research.{imported}"),
                )
                _write(root, "fixture/output.txt", "derived fixture output\n")
                commit = _commit(root, f"fixture: {name} local module")
                with self.assertRaisesRegex(replay.StageReplayError, expected):
                    replay.execute_stage_replay(
                        root,
                        _fixture_contract("scripts/__init__.py"),
                        input_commit=commit,
                        controller_commit=commit,
                    )

    def test_relative_import_closure_requires_package_initializers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            _write(root, "scripts/__init__.py", "")
            _write(root, "research/__init__.py", "")
            _write(root, "research/pkg/__init__.py", "")
            _write(root, "research/pkg/entry.py", "from . import helper\n")
            _write(root, "research/pkg/helper.py", "VALUE = 1\n")
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner("import research.pkg.entry"),
            )
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: relative package import")

            with self.assertRaisesRegex(
                replay.StageReplayError,
                "scientific source registry does not match recursive import closure",
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract(
                        "research/__init__.py",
                        "research/pkg/entry.py",
                        "research/pkg/helper.py",
                        "scripts/__init__.py",
                    ),
                    input_commit=commit,
                    controller_commit=commit,
                )

    def test_literal_dynamic_import_must_be_registered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            _write(root, "scripts/__init__.py", "")
            _write(root, "research/__init__.py", "")
            _write(root, "research/dynamic_source.py", "VALUE = 1\n")
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner(
                    "import importlib\nimportlib.import_module('research.dynamic_source')"
                ),
            )
            _write(root, "fixture/output.txt", "derived fixture output\n")
            literal_commit = _commit(root, "fixture: literal dynamic import")
            with self.assertRaisesRegex(
                replay.StageReplayError,
                "scientific source registry does not match recursive import closure",
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract("scripts/__init__.py"),
                    input_commit=literal_commit,
                    controller_commit=literal_commit,
                )

    def test_nonliteral_dynamic_local_import_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            _write(root, "scripts/__init__.py", "")
            _write(root, "research/__init__.py", "")
            _write(root, "research/dynamic_source.py", "VALUE = 1\n")
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner(
                    "import importlib\ntarget = 'research.dynamic_source'\n"
                    "importlib.import_module(target)"
                ),
            )
            _write(root, "fixture/output.txt", "derived fixture output\n")
            nonliteral_commit = _commit(root, "fixture: nonliteral dynamic import")
            with self.assertRaisesRegex(
                replay.StageReplayError, "nonliteral dynamic local import"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract(
                        "research/__init__.py",
                        "research/dynamic_source.py",
                        "scripts/__init__.py",
                    ),
                    input_commit=nonliteral_commit,
                    controller_commit=nonliteral_commit,
                )

    def test_getattr_dynamic_import_alias_must_be_registered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            _write(root, "scripts/__init__.py", "")
            _write(root, "research/__init__.py", "")
            _write(root, "research/dynamic_source.py", "VALUE = 1\n")
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner(
                    "import importlib as module_alias\n"
                    "loader = getattr(module_alias, 'import_module')\n"
                    "loader('research.dynamic_source')"
                ),
            )
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: getattr dynamic import alias")

            with self.assertRaisesRegex(
                replay.StageReplayError,
                "scientific source registry does not match recursive import closure",
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract("scripts/__init__.py"),
                    input_commit=commit,
                    controller_commit=commit,
                )

    def test_unsupported_dynamic_importer_acquisition_fails_before_execution(self):
        attacks = (
            (
                "subscript",
                "module = importlib.__dict__['import_module']('research.extra')",
            ),
            (
                "eval",
                "loader = eval('importlib.import_module')\n"
                "module = loader('research.extra')",
            ),
            (
                "exec",
                "exec('loader = importlib.import_module')\n"
                "module = loader('research.extra')",
            ),
            (
                "wrapper",
                "def recover_importer():\n"
                "    return importlib.import_module\n"
                "module = recover_importer()('research.extra')",
            ),
        )
        for name, attack in attacks:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                root = self._repo(str(base / "repo"))
                marker = base / "UNREGISTERED_IMPORT_EXECUTED"
                _write(root, "scripts/__init__.py", "")
                _write(root, "research/__init__.py", "")
                _write(
                    root,
                    "research/extra.py",
                    f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
                )
                imports = (
                    "import importlib\nimport research\nimport sys\n"
                    + attack
                    + "\ndel sys.modules[module.__name__]"
                )
                _write(
                    root,
                    "scripts/fixture_replayer.py",
                    _fixture_runner(imports),
                )
                _write(root, "fixture/output.txt", "derived fixture output\n")
                commit = _commit(root, f"fixture: {name} importer attack")

                with self.assertRaisesRegex(
                    replay.StageReplayError,
                    "unsupported dynamic importer acquisition",
                ):
                    replay.execute_stage_replay(
                        root,
                        _fixture_contract(
                            "research/__init__.py", "scripts/__init__.py"
                        ),
                        input_commit=commit,
                        controller_commit=commit,
                    )
                self.assertFalse(marker.exists())

    def test_supported_literal_dynamic_import_forms_remain_available(self):
        forms = (
            "import importlib\nimportlib.import_module('research.dynamic_source')",
            "__import__('research.dynamic_source')",
        )
        for imports in forms:
            with self.subTest(imports=imports), tempfile.TemporaryDirectory() as directory:
                root = self._repo(directory)
                _write(root, "scripts/__init__.py", "")
                _write(root, "research/__init__.py", "")
                _write(root, "research/dynamic_source.py", "VALUE = 1\n")
                _write(root, "scripts/fixture_replayer.py", _fixture_runner(imports))
                _write(root, "fixture/output.txt", "derived fixture output\n")
                commit = _commit(root, "fixture: supported literal importer")

                result = replay.execute_stage_replay(
                    root,
                    _fixture_contract(
                        "research/__init__.py",
                        "research/dynamic_source.py",
                        "scripts/__init__.py",
                    ),
                    input_commit=commit,
                    controller_commit=commit,
                )
                self.assertEqual(
                    result.decision, "PASS_FIXTURE_CONTROLLER_MECHANICS"
                )

    def test_import_audit_blocks_unregistered_runpy_before_top_level_code(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = self._repo(str(base / "repo"))
            marker = base / "UNREGISTERED_RUNPY_EXECUTED"
            _write(root, "scripts/__init__.py", "")
            _write(
                root,
                "research/extra.py",
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
            )
            imports = (
                "import runpy\n"
                "runpy.run_path(str(Path(__file__).resolve().parents[1] / "
                "'research/extra.py'), run_name='research.extra')"
            )
            _write(root, "scripts/fixture_replayer.py", _fixture_runner(imports))
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: unregistered runpy attack")

            with self.assertRaisesRegex(
                replay.StageReplayError, "unregistered local code"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract("scripts/__init__.py"),
                    input_commit=commit,
                    controller_commit=commit,
                )
            self.assertFalse(marker.exists())

    def test_import_audit_rejects_active_root_origin_before_spoof_code(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = self._repo(str(base / "repo"))
            marker = base / "ACTIVE_SHADOW_EXECUTED"
            _write(root, "scripts/__init__.py", "")
            _write(root, "research/__init__.py", "")
            _write(root, "research/guarded.py", "VALUE = 'committed'\n")
            imports = (
                f"sys.path.insert(0, {str(root)!r})\n"
                "import research.guarded"
            )
            _write(root, "scripts/fixture_replayer.py", _fixture_runner(imports))
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: committed guarded module")
            spoof = (
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed')\n"
                "expected = Path.cwd() / __file__.replace('\\\\', '/').split('/research/', 1)[1]\n"
            )
            initializer_spoof = (
                "from pathlib import Path\n"
                "expected = Path.cwd() / 'research/__init__.py'\n"
                "__file__ = str(expected)\n"
                "__spec__.origin = str(expected)\n"
            )
            module_spoof = (
                spoof
                + "expected = Path.cwd() / 'research/guarded.py'\n"
                "__file__ = str(expected)\n"
                "__spec__.origin = str(expected)\n"
            )
            _write(root, "research/__init__.py", initializer_spoof)
            _write(root, "research/guarded.py", module_spoof)

            with self.assertRaisesRegex(
                replay.StageReplayError, "import audit origin mismatch"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract(
                        "research/__init__.py",
                        "research/guarded.py",
                        "scripts/__init__.py",
                    ),
                    input_commit=commit,
                    controller_commit=commit,
                )
            self.assertFalse(marker.exists())

    def test_import_audit_cannot_be_bypassed_by_module_unload(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = self._repo(str(base / "repo"))
            alternate = base / "alternate"
            marker = base / "UNLOADED_SHADOW_EXECUTED"
            _write(alternate, "research/__init__.py", "")
            _write(
                alternate,
                "research/guarded.py",
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
            )
            _write(root, "scripts/__init__.py", "")
            _write(root, "research/__init__.py", "")
            _write(root, "research/guarded.py", "VALUE = 'committed'\n")
            imports = (
                f"sys.path.insert(0, {str(alternate)!r})\n"
                "import research.guarded\n"
                "del sys.modules['research.guarded']\n"
                "del sys.modules['research']"
            )
            _write(root, "scripts/fixture_replayer.py", _fixture_runner(imports))
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: unload shadow attack")

            with self.assertRaisesRegex(
                replay.StageReplayError, "import audit origin mismatch"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract(
                        "research/__init__.py",
                        "research/guarded.py",
                        "scripts/__init__.py",
                    ),
                    input_commit=commit,
                    controller_commit=commit,
                )
            self.assertFalse(marker.exists())

    def test_import_audit_rejects_direct_execution_from_any_outside_path(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = self._repo(str(base / "repo"))
            alternate = base / "alternate"
            marker = base / "OUTSIDE_RUNPY_EXECUTED"
            _write(
                alternate,
                "guarded.py",
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
            )
            _write(root, "scripts/__init__.py", "")
            _write(root, "research/__init__.py", "")
            _write(root, "research/guarded.py", "VALUE = 'committed'\n")
            imports = (
                "import runpy\n"
                "if False:\n"
                "    import research.guarded\n"
                f"runpy.run_path({str(alternate / 'guarded.py')!r}, "
                "run_name='research.guarded')"
            )
            _write(root, "scripts/fixture_replayer.py", _fixture_runner(imports))
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: arbitrary outside runpy attack")

            with self.assertRaisesRegex(
                replay.StageReplayError, "import audit outside trusted path"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract(
                        "research/__init__.py",
                        "research/guarded.py",
                        "scripts/__init__.py",
                    ),
                    input_commit=commit,
                    controller_commit=commit,
                )
            self.assertFalse(marker.exists())

    def test_runtime_module_origin_rejects_shadow_source(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = self._repo(str(base / "repo"))
            alternate = base / "alternate"
            _write(alternate, "research/__init__.py", "")
            _write(alternate, "research/shadow_source.py", "VALUE = 'shadow'\n")
            _write(root, "scripts/__init__.py", "")
            _write(root, "research/__init__.py", "")
            _write(root, "research/shadow_source.py", "VALUE = 'committed'\n")
            imports = (
                f"import sys\nsys.path.insert(0, {str(alternate)!r})\n"
                "import research.shadow_source"
            )
            _write(root, "scripts/fixture_replayer.py", _fixture_runner(imports))
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: runtime shadow")

            with self.assertRaisesRegex(
                replay.StageReplayError, "import audit origin mismatch"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract(
                        "research/__init__.py",
                        "research/shadow_source.py",
                        "scripts/__init__.py",
                    ),
                    input_commit=commit,
                    controller_commit=commit,
                )

    def test_untracked_write_anywhere_in_replay_checkout_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            _write(root, "scripts/__init__.py", "")
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner(body="Path(args.root, 'rogue.txt').write_text('write\\n')"),
            )
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: checkout write")

            with self.assertRaisesRegex(
                replay.StageReplayError, "replay checkout was mutated"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract("scripts/__init__.py"),
                    input_commit=commit,
                    controller_commit=commit,
                )

    def test_git_metadata_write_in_replay_checkout_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            _write(root, "scripts/__init__.py", "")
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner(
                    body="Path(args.root, '.git', 'rogue').write_text('write\\n')"
                ),
            )
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: git metadata write")

            with self.assertRaisesRegex(
                replay.StageReplayError, "replay checkout was mutated"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract("scripts/__init__.py"),
                    input_commit=commit,
                    controller_commit=commit,
                )

    def test_detached_clone_has_self_contained_object_store(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = self._repo(str(base / "source"))
            _write(source, "tracked.txt", "self-contained\n")
            commit = _commit(source, "fixture: self-contained clone")
            checkout = base / "checkout"

            replay._clone_detached(source, checkout, commit)

            alternates = checkout / ".git/objects/info/alternates"
            self.assertFalse(alternates.exists())
            source.rename(base / "source-moved")
            self.assertEqual(_git(checkout, "rev-parse", "HEAD"), commit)
            subprocess.run(
                ["git", "fsck", "--full", "--no-dangling"],
                cwd=checkout,
                check=True,
                capture_output=True,
                text=True,
            )

    def test_early_success_without_completion_attestation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            _write(root, "scripts/__init__.py", "")
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner(
                    imports="import os",
                    epilogue=(
                        "print('candidate-d-stage-replay-completion-v1', flush=True)\n"
                        "os._exit(0)"
                    ),
                ),
            )
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: early successful exit")

            with self.assertRaisesRegex(
                replay.StageReplayError, "completion attestation"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract("scripts/__init__.py"),
                    input_commit=commit,
                    controller_commit=commit,
                )

    def test_import_guard_displacement_prevents_completion_attestation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            _write(root, "scripts/__init__.py", "")
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner(epilogue="sys.meta_path.pop(0)"),
            )
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: displace import guard")

            with self.assertRaisesRegex(
                replay.StageReplayError, "import audit guard was displaced"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract("scripts/__init__.py"),
                    input_commit=commit,
                    controller_commit=commit,
                )

    def test_runner_cannot_forge_attestation_from_process_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            _write(root, "scripts/__init__.py", "")
            forge = """raw = next((value for value in sys.orig_argv if value.startswith('{') and '\"nonce\"' in value), None)
if raw is not None:
    control = json.loads(raw)
    forged = {
        'audited_imports': [],
        'nonce': control['nonce'],
        'runner_completed': True,
        'schema': control['attestation_schema'],
    }
    Path(control['attestation_path']).write_text(
        json.dumps(forged, ensure_ascii=True, sort_keys=True, separators=(',', ':')) + '\\n',
        encoding='ascii',
        newline='',
    )
os._exit(0)"""
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner(imports="import os", epilogue=forge),
            )
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: forge command-line attestation")

            with self.assertRaisesRegex(
                replay.StageReplayError, "completion attestation"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract("scripts/__init__.py"),
                    input_commit=commit,
                    controller_commit=commit,
                )

    def test_extra_empty_output_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            _write(root, "scripts/__init__.py", "")
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner(
                    body="Path(args.output_root, 'extra-empty').mkdir()"
                ),
            )
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: extra empty output directory")

            with self.assertRaisesRegex(
                replay.StageReplayError, "noncanonical output tree"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract("scripts/__init__.py"),
                    input_commit=commit,
                    controller_commit=commit,
                )

    @unittest.skipUnless(
        hasattr(os, "mkfifo") and os.name != "nt",
        "FIFO fixture requires POSIX mkfifo",
    )
    def test_special_output_node_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            _write(root, "scripts/__init__.py", "")
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner(
                    imports="import os",
                    body="os.mkfifo(Path(args.output_root, 'rogue-fifo'))",
                ),
            )
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: special output node")

            with self.assertRaisesRegex(
                replay.StageReplayError, "non-regular output node"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract("scripts/__init__.py"),
                    input_commit=commit,
                    controller_commit=commit,
                )

    def test_runner_observes_input_commit_not_active_working_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repo(directory)
            _write(root, "scripts/__init__.py", "")
            _write(root, "scripts/fixture_replayer.py", _fixture_runner())
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: committed runner")
            _write(
                root,
                "scripts/fixture_replayer.py",
                _fixture_runner(body="raise SystemExit('active runner executed')"),
            )

            result = replay.execute_stage_replay(
                root,
                _fixture_contract("scripts/__init__.py"),
                input_commit=commit,
                controller_commit=commit,
            )
            self.assertEqual(result.decision, "PASS_FIXTURE_CONTROLLER_MECHANICS")

    def test_runner_failure_cleans_checkout_and_preserves_active_worktree(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = self._repo(str(base / "repo"))
            observed_root = base / "observed-root.txt"
            _write(root, "scripts/__init__.py", "")
            body = (
                f"Path({str(observed_root)!r}).write_text(args.root, encoding='ascii')\n"
                "Path(args.root, 'runner-write.txt').write_text('write\\n')\n"
                "raise SystemExit(7)"
            )
            _write(root, "scripts/fixture_replayer.py", _fixture_runner(body=body))
            _write(root, "fixture/output.txt", "derived fixture output\n")
            commit = _commit(root, "fixture: failing runner")
            sentinel = root / "active-sentinel.txt"
            sentinel.write_text("preserve\n", encoding="ascii")

            with self.assertRaisesRegex(
                replay.StageReplayError, "canonical replay failed"
            ):
                replay.execute_stage_replay(
                    root,
                    _fixture_contract("scripts/__init__.py"),
                    input_commit=commit,
                    controller_commit=commit,
                )
            checkout = Path(observed_root.read_text(encoding="ascii"))
            self.assertFalse(checkout.exists())
            self.assertEqual(sentinel.read_text(encoding="ascii"), "preserve\n")
            self.assertFalse((root / "runner-write.txt").exists())

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
