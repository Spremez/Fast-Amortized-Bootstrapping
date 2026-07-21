"""Deterministic, commit-pinned replay boundary for Candidate D stages."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


REPLAY_MANIFEST = "candidate_d_stage_replay.json"
REPLAY_SCHEMA = "candidate-d-stage-replay-v1"
_DYNAMIC_IMPORT_CALLABLE = "dynamic-import-callable"
_IMPORTLIB_MODULE = "importlib-module"
_BUILTINS_MODULE = "builtins-module"

_RUNTIME_BOOTSTRAP = r'''
import json
from pathlib import Path
import runpy
import sys

config = json.loads(sys.argv[1])
checkout = Path(config["checkout"]).resolve(strict=True)
runner = (checkout / config["runner"]).resolve(strict=True)
expected = {
    name: (checkout / relative).resolve(strict=True)
    for name, relative in config["modules"].items()
}
allowed_paths = set(expected.values()) | {runner}

for name in expected:
    if name in sys.modules:
        raise RuntimeError(f"preloaded repository-local module: {name}")

sys.dont_write_bytecode = True
sys.pycache_prefix = config["cache_root"]
sys.path.insert(0, str(checkout))
sys.argv = [str(runner), *sys.argv[2:]]
exit_code = 0
try:
    runpy.run_path(str(runner), run_name="__main__")
except SystemExit as error:
    exit_code = error.code
    if exit_code is None:
        exit_code = 0

for name, expected_path in expected.items():
    module = sys.modules.get(name)
    if module is None:
        continue
    origin = getattr(module, "__file__", None)
    try:
        actual = Path(origin).resolve(strict=True)
    except (OSError, TypeError) as error:
        raise RuntimeError(
            f"loaded local module origin mismatch: {name}"
        ) from error
    if actual != expected_path:
        raise RuntimeError(f"loaded local module origin mismatch: {name}")

for name, module in tuple(sys.modules.items()):
    origin = getattr(module, "__file__", None)
    if origin is None:
        continue
    try:
        actual = Path(origin).resolve(strict=True)
        actual.relative_to(checkout)
    except (OSError, TypeError, ValueError):
        continue
    if actual not in allowed_paths:
        raise RuntimeError(f"loaded unregistered local module: {name}")

if exit_code not in (0, False):
    raise SystemExit(exit_code)
'''.lstrip()


class StageReplayError(RuntimeError):
    """A present replay implementation violated its deterministic contract."""


class StageReplayUnavailable(StageReplayError):
    """The reviewed replay implementation or a required input is absent."""


@dataclass(frozen=True)
class StageReplayContract:
    stage: str
    runner: str
    scientific_sources: tuple[str, ...]
    required_inputs: tuple[str, ...]
    canonical_outputs: tuple[str, ...]
    decisions: tuple[str, ...]
    scientific_authority: bool

    @property
    def pinned_paths(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                (
                    self.runner,
                    *self.scientific_sources,
                    *self.required_inputs,
                    *self.canonical_outputs,
                )
            )
        )


@dataclass(frozen=True)
class StageReplayResult:
    stage: str
    decision: str
    output_hashes: tuple[tuple[str, str], ...]
    scientific_authority: bool


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _full_commit(root: Path, value: str, label: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise StageReplayError(f"{label} must be a full lowercase SHA-1")
    try:
        resolved = subprocess.run(
            ["git", "rev-parse", "--verify", value],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise StageReplayError(f"{label} cannot be resolved") from error
    if resolved != value:
        raise StageReplayError(f"{label} did not resolve exactly")
    try:
        object_type = subprocess.run(
            ["git", "cat-file", "-t", resolved],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise StageReplayError(f"{label} type cannot be read") from error
    if object_type != "commit":
        raise StageReplayError(f"{label} does not name a commit")
    return resolved


def _git_blob(root: Path, commit: str, relative: str) -> bytes:
    try:
        entry = subprocess.run(
            ["git", "ls-tree", commit, "--", relative],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.rstrip("\n")
    except (OSError, subprocess.CalledProcessError) as error:
        raise StageReplayUnavailable(
            f"replay input cannot be inspected: {relative}"
        ) from error
    if not entry or "\t" not in entry:
        raise StageReplayUnavailable(f"replay input is missing: {relative}")
    metadata, recorded_path = entry.split("\t", 1)
    fields = metadata.split()
    if (
        len(fields) != 3
        or fields[1] != "blob"
        or fields[0] not in {"100644", "100755"}
        or recorded_path != relative
    ):
        raise StageReplayUnavailable(
            f"replay input is not a regular file: {relative}"
        )
    try:
        return subprocess.run(
            ["git", "cat-file", "blob", fields[2]],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise StageReplayUnavailable(
            f"replay input cannot be read: {relative}"
        ) from error


def _safe_relative(relative: str) -> Path:
    declared = Path(relative)
    if (
        declared.is_absolute()
        or not declared.parts
        or ".." in declared.parts
        or declared.as_posix() != relative
    ):
        raise StageReplayError(f"replay path escapes repository: {relative}")
    return declared


def _verify_pinned_paths(
    root: Path, commit: str, paths: tuple[str, ...]
) -> tuple[tuple[str, str], ...]:
    hashes = []
    for relative in paths:
        _safe_relative(relative)
        blob = _git_blob(root, commit, relative)
        hashes.append((relative, _sha256(blob)))
    return tuple(hashes)


def _git_paths(root: Path, commit: str) -> tuple[str, ...]:
    try:
        payload = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "-z", commit],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise StageReplayError("committed repository tree cannot be read") from error
    try:
        return tuple(
            item.decode("utf-8") for item in payload.split(b"\0") if item
        )
    except UnicodeError as error:
        raise StageReplayError("committed repository path is malformed") from error


def _module_name(relative: str) -> str:
    path = _safe_relative(relative)
    if path.suffix != ".py":
        raise StageReplayError(f"local Python source is not a .py file: {relative}")
    if path.name == "__init__.py":
        parts = path.parent.parts
    else:
        parts = path.with_suffix("").parts
    if not parts or any(not part.isidentifier() for part in parts):
        raise StageReplayError(f"invalid local Python module path: {relative}")
    return ".".join(parts)


def _module_source(
    root: Path, commit: str, module: str, tree_paths: set[str]
) -> tuple[str, bytes, bool] | None:
    stem = module.replace(".", "/")
    candidates = (
        (f"{stem}.py", False),
        (f"{stem}/__init__.py", True),
    )
    found = [item for item in candidates if item[0] in tree_paths]
    if len(found) > 1:
        raise StageReplayError(f"shadow package initializer for local module: {module}")
    if not found:
        return None
    relative, is_package = found[0]
    return relative, _git_blob(root, commit, relative), is_package


def _binding_kind(expression: ast.AST, bindings: dict[str, str]) -> str | None:
    if isinstance(expression, ast.Name):
        return bindings.get(expression.id)
    if isinstance(expression, ast.Attribute):
        owner = _binding_kind(expression.value, bindings)
        if owner == _IMPORTLIB_MODULE and expression.attr == "import_module":
            return _DYNAMIC_IMPORT_CALLABLE
        if owner == _BUILTINS_MODULE and expression.attr == "__import__":
            return _DYNAMIC_IMPORT_CALLABLE
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "getattr"
        and len(expression.args) == 2
        and not expression.keywords
        and isinstance(expression.args[1], ast.Constant)
        and isinstance(expression.args[1].value, str)
    ):
        owner = _binding_kind(expression.args[0], bindings)
        attribute = expression.args[1].value
        if owner == _IMPORTLIB_MODULE and attribute == "import_module":
            return _DYNAMIC_IMPORT_CALLABLE
        if owner == _BUILTINS_MODULE and attribute == "__import__":
            return _DYNAMIC_IMPORT_CALLABLE
    return None


def _dynamic_bindings(tree: ast.AST, relative: str) -> dict[str, str]:
    bindings = {"__import__": _DYNAMIC_IMPORT_CALLABLE}
    nodes = tuple(ast.walk(tree))
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    bindings[alias.asname or "importlib"] = _IMPORTLIB_MODULE
                elif alias.name.startswith("importlib.") and alias.asname is None:
                    bindings["importlib"] = _IMPORTLIB_MODULE
                elif alias.name == "builtins":
                    bindings[alias.asname or "builtins"] = _BUILTINS_MODULE
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module in {"builtins", "importlib"}
        ):
            for alias in node.names:
                if alias.name == "*":
                    raise StageReplayError(
                        f"wildcard dynamic import binding in {relative}"
                    )
                if alias.name in {"import_module", "__import__"}:
                    bindings[alias.asname or alias.name] = _DYNAMIC_IMPORT_CALLABLE
    assignments = []
    for node in nodes:
        if isinstance(node, ast.Assign):
            assignments.append((node.targets, node.value))
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            assignments.append(((node.target,), node.value))
        elif isinstance(node, ast.NamedExpr):
            assignments.append(((node.target,), node.value))
    changed = True
    while changed:
        changed = False
        for targets, value in assignments:
            kind = _binding_kind(value, bindings)
            if kind is None:
                continue
            for target in targets:
                if not isinstance(target, ast.Name):
                    raise StageReplayError(
                        f"unsupported dynamic import alias target in {relative}"
                    )
                previous = bindings.get(target.id)
                if previous is not None and previous != kind:
                    raise StageReplayError(
                        f"ambiguous dynamic import binding in {relative}"
                    )
                if previous is None:
                    bindings[target.id] = kind
                    changed = True
    return bindings


def _imports_from_source(
    module: str,
    relative: str,
    content: bytes,
    *,
    is_package: bool,
    source_for,
    local_top_levels: set[str],
) -> tuple[str, ...]:
    try:
        tree = ast.parse(content, filename=relative)
    except (SyntaxError, UnicodeError) as error:
        raise StageReplayError(f"cannot parse committed local module: {relative}") from error
    package = module if is_package else module.rpartition(".")[0]
    imports = set()

    def add_if_local(name: str, *, mandatory: bool) -> bool:
        source = source_for(name)
        if source is not None:
            imports.add(name)
            return True
        if mandatory or name.partition(".")[0] in local_top_levels:
            raise StageReplayError(f"unresolved local module: {name}")
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add_if_local(alias.name, mandatory=False)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            if not package:
                raise StageReplayError(f"relative import without package in {relative}")
            requested = "." * node.level + (node.module or "")
            try:
                base = importlib.util.resolve_name(requested, package)
            except (ImportError, ValueError) as error:
                raise StageReplayError(f"invalid relative import in {relative}") from error
            base_is_local = add_if_local(base, mandatory=True)
        else:
            base = node.module or ""
            base_is_local = add_if_local(base, mandatory=False) if base else False
        if not base_is_local:
            continue
        base_source = source_for(base)
        if base_source is None or not base_source[2]:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            candidate = f"{base}.{alias.name}"
            if source_for(candidate) is not None:
                imports.add(candidate)

    bindings = _dynamic_bindings(tree, relative)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _binding_kind(node.func, bindings) != _DYNAMIC_IMPORT_CALLABLE:
            continue
        if (
            not node.args
            or not isinstance(node.args[0], ast.Constant)
            or not isinstance(node.args[0].value, str)
        ):
            raise StageReplayError(
                f"nonliteral dynamic local import in {relative}"
            )
        requested = node.args[0].value
        if requested.startswith("."):
            if not package:
                raise StageReplayError(f"relative dynamic import without package in {relative}")
            requested = importlib.util.resolve_name(requested, package)
        add_if_local(requested, mandatory=False)
    return tuple(sorted(imports))


def _derive_python_closure(
    root: Path, commit: str, runner: str
) -> tuple[str, ...]:
    runner_module = _module_name(runner)
    tree_paths = set(_git_paths(root, commit))
    local_top_levels = {
        path.split("/", 1)[0].removesuffix(".py")
        for path in tree_paths
        if path.endswith(".py")
    }
    cache: dict[str, tuple[str, bytes, bool] | None] = {}

    def source_for(module: str) -> tuple[str, bytes, bool] | None:
        if module not in cache:
            cache[module] = _module_source(root, commit, module, tree_paths)
        return cache[module]

    pending = [runner_module]
    seen = set()
    paths = set()
    while pending:
        module = pending.pop()
        if module in seen:
            continue
        seen.add(module)
        source = source_for(module)
        if source is None:
            raise StageReplayUnavailable(f"replay runner is missing: {runner}")
        relative, content, is_package = source
        paths.add(relative)
        parts = module.split(".")
        for index in range(1, len(parts)):
            package = ".".join(parts[:index])
            package_source = source_for(package)
            if package_source is not None:
                pending.append(package)
        pending.extend(
            _imports_from_source(
                module,
                relative,
                content,
                is_package=is_package,
                source_for=source_for,
                local_top_levels=local_top_levels,
            )
        )
    return tuple(sorted(paths))


def _authenticated_closure(
    root: Path,
    commit: str,
    contract: StageReplayContract,
) -> tuple[str, ...]:
    registry = contract.scientific_sources
    if registry != tuple(sorted(registry)) or len(registry) != len(set(registry)):
        raise StageReplayError(
            "scientific source registry must be sorted and unique"
        )
    closure = _derive_python_closure(root, commit, contract.runner)
    scientific_closure = tuple(path for path in closure if path != contract.runner)
    if scientific_closure != registry:
        raise StageReplayError(
            "scientific source registry does not match recursive import closure"
        )
    return closure


def _checkout_status(root: Path) -> bytes:
    try:
        return subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise StageReplayError("replay checkout status cannot be read") from error


def _tree_snapshot(root: Path) -> tuple[tuple[str, str, str], ...]:
    entries = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] == ".git":
            continue
        name = relative.as_posix()
        if path.is_symlink():
            entries.append((name, "symlink", os.readlink(path)))
        elif path.is_dir():
            entries.append((name, "directory", ""))
        elif path.is_file():
            entries.append((name, "file", _sha256(path.read_bytes())))
        else:
            entries.append((name, "other", ""))
    return tuple(sorted(entries))


def _verify_checkout_files(
    checkout: Path, source_root: Path, commit: str, paths: tuple[str, ...]
) -> None:
    for relative in paths:
        expected = _git_blob(source_root, commit, relative)
        path = checkout / _safe_relative(relative)
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(checkout)
        except (OSError, ValueError) as error:
            raise StageReplayError(
                f"checked-out replay input is missing: {relative}"
            ) from error
        if path.is_symlink() or not resolved.is_file() or path.read_bytes() != expected:
            raise StageReplayError(
                f"checked-out replay input differs from commit: {relative}"
            )


def _clone_detached(source_root: Path, checkout: Path, commit: str) -> None:
    try:
        subprocess.run(
            ["git", "clone", "--shared", "--no-checkout", "-q", str(source_root), str(checkout)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "core.autocrlf", "false"],
            cwd=checkout,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "--detach", "-q", commit],
            cwd=checkout,
            check=True,
            capture_output=True,
        )
        actual = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=checkout,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise StageReplayError("clean detached replay checkout cannot be created") from error
    if actual != commit or _checkout_status(checkout):
        raise StageReplayError("clean detached replay checkout is not exact")


def _output_files(output_root: Path) -> tuple[str, ...]:
    files = []
    for path in output_root.rglob("*"):
        if path.is_symlink():
            raise StageReplayError("stage replay output may not contain symlinks")
        if path.is_file():
            files.append(path.relative_to(output_root).as_posix())
    return tuple(sorted(files))


def _manifest(
    output_root: Path,
    contract: StageReplayContract,
    input_commit: str,
    controller_commit: str,
) -> dict[str, object]:
    path = output_root / REPLAY_MANIFEST
    try:
        payload = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise StageReplayError("stage replay manifest is malformed") from error
    expected_keys = {
        "schema",
        "stage",
        "input_commit",
        "controller_commit",
        "decision",
        "canonical_outputs",
        "scientific_authority",
    }
    if set(payload) != expected_keys:
        raise StageReplayError("stage replay manifest fields are malformed")
    if (
        payload["schema"] != REPLAY_SCHEMA
        or payload["stage"] != contract.stage
        or payload["input_commit"] != input_commit
        or payload["controller_commit"] != controller_commit
        or payload["canonical_outputs"] != list(contract.canonical_outputs)
        or payload["scientific_authority"] is not contract.scientific_authority
        or payload["decision"] not in contract.decisions
    ):
        raise StageReplayError("stage replay manifest does not match its contract")
    return payload


def execute_stage_replay(
    root: Path,
    contract: StageReplayContract,
    *,
    input_commit: str,
    controller_commit: str,
) -> StageReplayResult:
    """Replay one stage and compare every output to its committed artifact."""

    root = Path(root).resolve(strict=True)
    input_commit = _full_commit(root, input_commit, "input commit")
    controller_commit = _full_commit(root, controller_commit, "controller commit")
    closure = _authenticated_closure(root, input_commit, contract)
    _verify_pinned_paths(root, input_commit, contract.pinned_paths)
    with tempfile.TemporaryDirectory(prefix="candidate-d-stage-replay-") as directory:
        temporary_root = Path(directory)
        checkout = temporary_root / "checkout"
        output_root = temporary_root / "output"
        cache_root = temporary_root / "pycache"
        _clone_detached(root, checkout, input_commit)
        output_root.mkdir()
        cache_root.mkdir()
        _verify_checkout_files(
            checkout, root, input_commit, contract.pinned_paths
        )
        before_status = _checkout_status(checkout)
        before_snapshot = _tree_snapshot(checkout)
        module_paths = {
            _module_name(relative): relative
            for relative in closure
            if relative != contract.runner
        }
        config = json.dumps(
            {
                "cache_root": str(cache_root),
                "checkout": str(checkout),
                "modules": module_paths,
                "runner": contract.runner,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        command = (
            sys.executable,
            "-I",
            "-c",
            _RUNTIME_BOOTSTRAP,
            config,
            "--root",
            str(checkout),
            "--output-root",
            str(output_root),
            "--input-commit",
            input_commit,
            "--controller-commit",
            controller_commit,
        )
        try:
            completed = subprocess.run(
                command,
                cwd=checkout,
                check=False,
                capture_output=True,
                text=True,
                timeout=600,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise StageReplayError(
                f"{contract.stage} canonical replay could not execute"
            ) from error
        checkout_mutated = (
            _checkout_status(checkout) != before_status
            or _tree_snapshot(checkout) != before_snapshot
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            mutation = "; replay checkout was mutated" if checkout_mutated else ""
            raise StageReplayError(
                f"{contract.stage} canonical replay failed{mutation}: {detail[:300]}"
            )
        if checkout_mutated:
            raise StageReplayError(
                f"{contract.stage} replay checkout was mutated"
            )
        expected_files = tuple(
            sorted((*contract.canonical_outputs, REPLAY_MANIFEST))
        )
        if _output_files(output_root) != expected_files:
            raise StageReplayError(
                f"{contract.stage} canonical replay emitted a noncanonical output set"
            )
        payload = _manifest(
            output_root, contract, input_commit, controller_commit
        )
        hashes = []
        for relative in contract.canonical_outputs:
            replayed = (output_root / relative).read_bytes()
            committed = _git_blob(root, input_commit, relative)
            if replayed != committed:
                raise StageReplayError(
                    f"{contract.stage} replay differs from committed artifact: {relative}"
                )
            hashes.append((relative, _sha256(replayed)))
    return StageReplayResult(
        stage=contract.stage,
        decision=str(payload["decision"]),
        output_hashes=tuple(hashes),
        scientific_authority=contract.scientific_authority,
    )
