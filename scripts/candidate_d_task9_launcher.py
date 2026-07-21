#!/usr/bin/env python3
"""Launch Candidate D Task 9 from an authenticated composite source tree."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile


LAUNCHER_PATH = "scripts/candidate_d_task9_launcher.py"
CONTROLLER_OVERLAY_PATHS = tuple(
    sorted(
        (
            "docs/candidate_d_task9_replay_contract.md",
            "docs/candidate_d_task9_threat_model.md",
            "research/__init__.py",
            "research/mat_sab/__init__.py",
            "research/mat_sab/candidate_d_stage_replay.py",
            "scripts/__init__.py",
            LAUNCHER_PATH,
            "scripts/apply_candidate_d_admission.py",
            "scripts/mat_sab_research_state.py",
            "scripts/run_candidate_d_admission.py",
        )
    )
)
RUN_EXECUTION_CLOSURE = tuple(
    sorted(
        (
            "research/__init__.py",
            "research/mat_sab/__init__.py",
            "research/mat_sab/candidate_d_baseline.py",
            "research/mat_sab/candidate_d_literature.py",
            "research/mat_sab/candidate_d_stage_replay.py",
            "scripts/__init__.py",
            "scripts/mat_sab_research_state.py",
            "scripts/run_candidate_d_admission.py",
            "scripts/run_candidate_d_d1_literature.py",
        )
    )
)
APPLY_EXECUTION_CLOSURE = tuple(
    sorted((*RUN_EXECUTION_CLOSURE, "scripts/apply_candidate_d_admission.py"))
)
ENTRYPOINTS = {
    "run": "scripts/run_candidate_d_admission.py",
    "apply": "scripts/apply_candidate_d_admission.py",
}
EXPECTED_CLOSURES = {
    "run": RUN_EXECUTION_CLOSURE,
    "apply": APPLY_EXECUTION_CLOSURE,
}


class LauncherError(RuntimeError):
    pass


def _git_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    return environment


def _child_environment() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith(("GIT_", "PYTHON"))
    }


def _git(
    root: Path,
    arguments: tuple[str, ...],
    *,
    text: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            env=_git_environment(),
            check=check,
            capture_output=True,
            text=text,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise LauncherError("Git operation failed before Task 9 launch") from error


def _repository_root(value: Path) -> Path:
    try:
        root = value.resolve(strict=True)
    except OSError as error:
        raise LauncherError("caller repository root cannot be resolved") from error
    if not root.is_dir():
        raise LauncherError("caller repository root is not a directory")
    inside = _git(
        root, ("rev-parse", "--is-inside-work-tree"), text=True
    ).stdout.strip()
    prefix = _git(root, ("rev-parse", "--show-prefix"), text=True).stdout.strip()
    if inside != "true" or prefix:
        raise LauncherError("--root must name the caller repository top level")
    return root


def _full_commit(root: Path, value: str, label: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise LauncherError(f"{label} must be a full lowercase SHA-1")
    completed = _git(
        root,
        ("rev-parse", "--verify", value),
        text=True,
    )
    if completed.stdout.strip() != value:
        raise LauncherError(f"{label} did not resolve exactly")
    object_type = _git(root, ("cat-file", "-t", value), text=True).stdout.strip()
    if object_type != "commit":
        raise LauncherError(f"{label} does not name a commit")
    ancestor = _git(
        root,
        ("merge-base", "--is-ancestor", value, "HEAD"),
        check=False,
    )
    if ancestor.returncode != 0:
        raise LauncherError(f"{label} is not an ancestor of caller HEAD")
    return value


def _safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or "\\" in value
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != value
    ):
        raise LauncherError(f"unsafe composite-tree path: {value}")
    return path


def _git_blob(root: Path, commit: str, relative: str) -> bytes:
    _safe_relative(relative)
    entry = _git(
        root,
        ("ls-tree", commit, "--", relative),
        text=True,
    ).stdout.rstrip("\n")
    if not entry or "\t" not in entry:
        raise LauncherError(f"commit-pinned source is missing: {relative}")
    metadata, recorded = entry.split("\t", 1)
    try:
        mode, object_type, object_id = metadata.split()
    except ValueError as error:
        raise LauncherError(f"malformed Git entry: {relative}") from error
    if (
        recorded != relative
        or object_type != "blob"
        or mode not in {"100644", "100755"}
    ):
        raise LauncherError(f"commit-pinned source is not a regular file: {relative}")
    return _git(root, ("cat-file", "blob", object_id)).stdout


def _git_paths(root: Path, commit: str) -> tuple[str, ...]:
    raw = _git(root, ("ls-tree", "-r", "--name-only", "-z", commit)).stdout
    try:
        paths = tuple(
            value.decode("utf-8") for value in raw.split(b"\0") if value
        )
    except UnicodeError as error:
        raise LauncherError("commit tree contains a non-UTF-8 path") from error
    for path in paths:
        _safe_relative(path)
    return paths


def _alternates_path(checkout: Path) -> Path:
    return checkout / ".git/objects/info/alternates"


def _reject_alternates(checkout: Path) -> None:
    if os.path.lexists(_alternates_path(checkout)):
        raise LauncherError("composite checkout has an alternate object store")


def _clone_input_tree(source_root: Path, checkout: Path, input_commit: str) -> None:
    try:
        subprocess.run(
            [
                "git",
                "clone",
                "--no-local",
                "--no-checkout",
                "-q",
                str(source_root),
                str(checkout),
            ],
            env=_git_environment(),
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise LauncherError("self-contained composite checkout cannot be cloned") from error
    _reject_alternates(checkout)
    _git(checkout, ("config", "core.autocrlf", "false"))
    _git(checkout, ("checkout", "--detach", "-q", input_commit))
    actual = _git(checkout, ("rev-parse", "HEAD"), text=True).stdout.strip()
    status = _git(
        checkout,
        ("status", "--porcelain=v1", "--untracked-files=all"),
    ).stdout
    _reject_alternates(checkout)
    if actual != input_commit or status:
        raise LauncherError("input-commit checkout is not exact")


def _write_controller_overlay(
    checkout: Path, controller_commit: str
) -> None:
    for relative in CONTROLLER_OVERLAY_PATHS:
        content = _git_blob(checkout, controller_commit, relative)
        destination = checkout.joinpath(*_safe_relative(relative).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if os.path.lexists(destination) and (
            destination.is_symlink() or not destination.is_file()
        ):
            raise LauncherError(f"composite overlay target is unsafe: {relative}")
        destination.write_bytes(content)


def _module_source(
    module: str, tree_paths: set[str]
) -> tuple[str, bool] | None:
    stem = module.replace(".", "/")
    module_path = stem + ".py"
    package_path = stem + "/__init__.py"
    matches = tuple(
        path for path in (module_path, package_path) if path in tree_paths
    )
    if len(matches) > 1:
        raise LauncherError(f"ambiguous local module/package: {module}")
    if not matches:
        return None
    return matches[0], matches[0].endswith("/__init__.py")


def _module_name(relative: str) -> str:
    path = PurePosixPath(relative)
    if path.name == "__init__.py":
        parts = path.parent.parts
    elif path.suffix == ".py":
        parts = (*path.parent.parts, path.stem)
    else:
        raise LauncherError(f"non-Python execution path: {relative}")
    if not parts or any(not part.isidentifier() for part in parts):
        raise LauncherError(f"invalid local module path: {relative}")
    return ".".join(parts)


def _imports_from_source(
    module: str,
    relative: str,
    content: bytes,
    *,
    is_package: bool,
    tree_paths: set[str],
    local_top_levels: set[str],
) -> tuple[str, ...]:
    try:
        tree = ast.parse(content, filename=relative)
    except (SyntaxError, UnicodeError) as error:
        raise LauncherError(f"cannot parse execution source: {relative}") from error
    imports: set[str] = set()

    def add_if_local(requested: str, *, mandatory: bool) -> None:
        if not requested:
            return
        source = _module_source(requested, tree_paths)
        if source is not None:
            imports.add(requested)
            return
        if mandatory or requested.split(".", 1)[0] in local_top_levels:
            raise LauncherError(
                f"unresolved local import {requested!r} in {relative}"
            )

    package = module if is_package else module.rpartition(".")[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add_if_local(alias.name, mandatory=False)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                if not package:
                    raise LauncherError(
                        f"relative import without a package in {relative}"
                    )
                requested = "." * node.level + (node.module or "")
                try:
                    base = importlib.util.resolve_name(requested, package)
                except (ImportError, ValueError) as error:
                    raise LauncherError(
                        f"invalid relative import in {relative}"
                    ) from error
            else:
                base = node.module or ""
            add_if_local(base, mandatory=False)
            for alias in node.names:
                if alias.name != "*":
                    candidate = f"{base}.{alias.name}" if base else alias.name
                    if _module_source(candidate, tree_paths) is not None:
                        imports.add(candidate)
        elif isinstance(node, ast.Call):
            dynamic = (
                isinstance(node.func, ast.Name) and node.func.id == "__import__"
            ) or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
            )
            if dynamic:
                if (
                    not node.args
                    or not isinstance(node.args[0], ast.Constant)
                    or not isinstance(node.args[0].value, str)
                ):
                    raise LauncherError(
                        f"nonliteral dynamic import in {relative}"
                    )
                requested = node.args[0].value
                if requested.startswith("."):
                    if not package:
                        raise LauncherError(
                            f"relative dynamic import without package in {relative}"
                        )
                    requested = importlib.util.resolve_name(requested, package)
                add_if_local(requested, mandatory=False)
    return tuple(sorted(imports))


def _derive_closure(
    checkout: Path,
    input_commit: str,
    entrypoint: str,
) -> tuple[str, ...]:
    tree_paths = set(_git_paths(checkout, input_commit))
    tree_paths.update(CONTROLLER_OVERLAY_PATHS)
    local_top_levels = {
        path.split("/", 1)[0].removesuffix(".py")
        for path in tree_paths
        if path.endswith(".py")
    }
    pending = [_module_name(entrypoint)]
    seen: set[str] = set()
    closure: set[str] = set()
    while pending:
        module = pending.pop()
        if module in seen:
            continue
        seen.add(module)
        source = _module_source(module, tree_paths)
        if source is None:
            raise LauncherError(f"execution module is missing: {module}")
        relative, is_package = source
        closure.add(relative)
        parts = module.split(".")
        for index in range(1, len(parts)):
            package = ".".join(parts[:index])
            package_source = _module_source(package, tree_paths)
            if package_source is not None:
                pending.append(package)
        content = (checkout / relative).read_bytes()
        pending.extend(
            _imports_from_source(
                module,
                relative,
                content,
                is_package=is_package,
                tree_paths=tree_paths,
                local_top_levels=local_top_levels,
            )
        )
    return tuple(sorted(closure))


def _verify_designated_sources(
    checkout: Path,
    input_commit: str,
    controller_commit: str,
    paths: tuple[str, ...],
) -> None:
    controller_paths = set(CONTROLLER_OVERLAY_PATHS)
    for relative in paths:
        commit = controller_commit if relative in controller_paths else input_commit
        expected = _git_blob(checkout, commit, relative)
        path = checkout.joinpath(*_safe_relative(relative).parts)
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(checkout)
        except (OSError, ValueError) as error:
            raise LauncherError(
                f"composite execution source is missing: {relative}"
            ) from error
        if path.is_symlink() or not path.is_file() or path.read_bytes() != expected:
            raise LauncherError(
                f"composite source differs from designated commit: {relative}"
            )


def _authenticate_composite_tree(
    checkout: Path,
    *,
    mode: str,
    input_commit: str,
    controller_commit: str,
) -> None:
    expected = EXPECTED_CLOSURES[mode]
    actual = _derive_closure(checkout, input_commit, ENTRYPOINTS[mode])
    if actual != expected:
        raise LauncherError(
            "recorded Task 9 execution closure does not match recursive local imports"
        )
    _verify_designated_sources(
        checkout,
        input_commit,
        controller_commit,
        tuple(sorted(set((*CONTROLLER_OVERLAY_PATHS, *actual)))),
    )
    _reject_alternates(checkout)


def _launch(args: argparse.Namespace) -> int:
    if sys.flags.isolated != 1 or sys.flags.no_site != 1:
        raise LauncherError("launcher requires python -I -S")
    root = _repository_root(args.root)
    input_commit = _full_commit(root, args.input_commit, "input commit")
    controller_commit = _full_commit(
        root, args.controller_commit, "controller commit"
    )
    with tempfile.TemporaryDirectory(prefix="candidate-d-task9-launch-") as directory:
        checkout = Path(directory) / "composite"
        _clone_input_tree(root, checkout, input_commit)
        _write_controller_overlay(checkout, controller_commit)
        _authenticate_composite_tree(
            checkout,
            mode=args.mode,
            input_commit=input_commit,
            controller_commit=controller_commit,
        )
        command = [
            sys.executable,
            "-I",
            "-S",
            str(checkout / ENTRYPOINTS[args.mode]),
            "--root",
            str(root),
            "--input-commit",
            input_commit,
            "--controller-commit",
            controller_commit,
            "--run-date",
            args.run_date,
            "--execution-platform",
            args.execution_platform,
        ]
        if args.check:
            command.append("--check")
        try:
            completed = subprocess.run(
                command,
                cwd=checkout,
                env=_child_environment(),
                check=False,
            )
        except OSError as error:
            raise LauncherError("authenticated Task 9 child cannot execute") from error
        return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=tuple(ENTRYPOINTS), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--input-commit", required=True)
    parser.add_argument("--controller-commit", required=True)
    parser.add_argument("--run-date", required=True)
    parser.add_argument("--execution-platform", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        return _launch(args)
    except LauncherError as error:
        print(f"Candidate D Task 9 launcher rejected execution: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
