#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import atexit
import csv
import importlib
import io
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]

ADMIT = "ADMIT_CANDIDATE_C_KEY_SECURITY_NOISE_PREFLIGHT"
REJECT = "REJECT_CANDIDATE_C_RANK_BOUNDED_STATE_CAMPAIGN_EXHAUSTED"
INCONCLUSIVE = "INCONCLUSIVE_CANDIDATE_C_EVIDENCE_EXHAUSTED"
ACTUAL_EVIDENCE = "ACTUAL_TASK3C"
SUMMARY_FIELDS: tuple[str, ...] = ()
CLOSEOUT_LOCAL_IMPORT_ROOTS = (
    "scripts.apply_candidate_c_rank_bounded_gate",
)
CLOSEOUT_EXECUTABLE_INPUTS = (
    "research/__init__.py",
    "research/mat_sab/__init__.py",
    "research/mat_sab/candidate_c_operator_tensor.py",
    "research/mat_sab/candidate_c_registered_replay.py",
    "research/mat_sab/candidate_c_schedule.py",
    "research/mat_sab/finite_linear.py",
    "research/mat_sab/rank_bounded_state_model.py",
    "scripts/__init__.py",
    "scripts/apply_candidate_c_rank_bounded_gate.py",
    "scripts/mat_sab_research_state.py",
    "scripts/run_candidate_c_rank_bounded_gate.py",
)
_LOCAL_IMPORT_PREFIXES = ("research", "scripts")
_LOCAL_DEPENDENCIES_LOADED = False
_LOCAL_CACHE_PREFIX: Path | None = None
_BINDING_IMPORTLIB_MODULE = "IMPORTLIB_MODULE"
_BINDING_BUILTINS_MODULE = "BUILTINS_MODULE"
_BINDING_IMPORT_CALLABLE = "IMPORT_CALLABLE"

RUN_MARKER = "candidate-c-rank-bounded-gate-001"
HYPOTHESIS_START = "# candidate-c-rank-bounded-gate-hypothesis-start"
HYPOTHESIS_END = "# candidate-c-rank-bounded-gate-hypothesis-end"
MANIFEST_START = "<!-- candidate-c-rank-bounded-gate-manifest-start -->"
MANIFEST_END = "<!-- candidate-c-rank-bounded-gate-manifest-end -->"
CHECKLIST_START = "<!-- candidate-c-rank-bounded-gate-checklist-start -->"
CHECKLIST_END = "<!-- candidate-c-rank-bounded-gate-checklist-end -->"
PREDECESSOR_DECISION = (
    "REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C"
)
TECHGRAPH_DECISION = "CANDIDATE_C_TECHGRAPH_ANCHORED"
EQUATIONS_DECISION = "CANDIDATE_C_EQUATIONS_DEFINED"
DECISIONS = {ADMIT, REJECT, INCONCLUSIVE}
PINNED_GENERATOR_COMMAND = re.compile(
    r"python scripts/run_candidate_c_rank_bounded_gate\.py "
    r"--input-commit ([0-9a-f]{40})"
)


class LocalImportPreflightError(RuntimeError):
    pass


def _local_import_error(message: str) -> LocalImportPreflightError:
    return LocalImportPreflightError(f"local import preflight: {message}")


def _preflight_root(root: Path) -> Path:
    try:
        resolved = Path(root).resolve(strict=True)
    except OSError as error:
        raise _local_import_error("source root cannot be resolved") from error
    if not resolved.is_dir():
        raise _local_import_error("source root is not a directory")
    return resolved


def _preflight_launcher_root(root: Path) -> Path:
    resolved = _preflight_root(root)
    if resolved != ROOT:
        raise _local_import_error(
            "requested root does not match launcher checkout root"
        )
    return resolved


def _preflight_commit(root: Path, input_commit: str) -> str:
    if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", input_commit) is None:
        raise _local_import_error(
            "commit must be one lowercase 40-or-64-hex SHA"
        )
    try:
        resolved = subprocess.run(
            [
                "git",
                "rev-parse",
                "--verify",
                input_commit,
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise _local_import_error("cannot resolve commit") from error
    if resolved != input_commit:
        raise _local_import_error("commit did not resolve exactly")
    try:
        object_type = subprocess.run(
            ["git", "cat-file", "-t", resolved],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise _local_import_error("cannot inspect commit type") from error
    if object_type != "commit":
        raise _local_import_error("input object is not a commit")
    try:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", resolved, "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
        )
    except OSError as error:
        raise _local_import_error("cannot verify commit ancestry") from error
    if ancestor.returncode != 0:
        raise _local_import_error("commit is not an ancestor of HEAD")
    return resolved


def _preflight_git_blob(
    root: Path,
    commit: str,
    relative: str,
    *,
    allow_absent: bool,
) -> bytes | None:
    try:
        result = subprocess.run(
            ["git", "ls-tree", "-z", commit, "--", relative],
            cwd=root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise _local_import_error(
            f"cannot inspect committed path: {relative}"
        ) from error
    entry = result.stdout.rstrip(b"\0")
    if not entry:
        if allow_absent:
            return None
        raise _local_import_error(f"commit has no local module: {relative}")
    if b"\t" not in entry:
        raise _local_import_error(f"malformed committed path: {relative}")
    metadata, recorded_path = entry.split(b"\t", 1)
    try:
        mode, object_type, object_id = metadata.decode("ascii").split()
        recorded = recorded_path.decode("utf-8")
    except (UnicodeError, ValueError) as error:
        raise _local_import_error(
            f"malformed committed path: {relative}"
        ) from error
    if (
        recorded != relative
        or object_type != "blob"
        or mode not in {"100644", "100755"}
    ):
        raise _local_import_error(
            f"committed local module is not a regular file: {relative}"
        )
    try:
        return subprocess.run(
            ["git", "cat-file", "blob", object_id],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise _local_import_error(
            f"cannot read committed local module: {relative}"
        ) from error


def _is_local_module(module: str) -> bool:
    return any(
        module == prefix or module.startswith(prefix + ".")
        for prefix in _LOCAL_IMPORT_PREFIXES
    )


def _committed_module_source(
    root: Path,
    commit: str,
    module: str,
) -> tuple[str, bytes, bool] | None:
    stem = module.replace(".", "/")
    candidates = (
        (f"{stem}.py", False),
        (f"{stem}/__init__.py", True),
    )
    found = []
    for relative, is_package in candidates:
        content = _preflight_git_blob(
            root,
            commit,
            relative,
            allow_absent=True,
        )
        if content is not None:
            found.append((relative, content, is_package))
    if len(found) > 1:
        raise _local_import_error(f"ambiguous local module: {module}")
    return found[0] if found else None


def _record_dynamic_import_binding(
    bindings: dict[str, str],
    name: str,
    kind: str,
    relative: str,
) -> bool:
    previous = bindings.get(name)
    if previous is not None and previous != kind:
        raise _local_import_error(
            f"ambiguous dynamic import binding in {relative}: {name}"
        )
    if previous == kind:
        return False
    bindings[name] = kind
    return True


def _dynamic_import_binding_kind(
    expression: ast.AST,
    bindings: dict[str, str],
) -> str | None:
    if isinstance(expression, ast.Name):
        return bindings.get(expression.id)
    if isinstance(expression, ast.Attribute):
        owner = _dynamic_import_binding_kind(
            expression.value,
            bindings,
        )
        if (
            owner == _BINDING_IMPORTLIB_MODULE
            and expression.attr == "import_module"
        ):
            return _BINDING_IMPORT_CALLABLE
        if (
            owner == _BINDING_BUILTINS_MODULE
            and expression.attr == "__import__"
        ):
            return _BINDING_IMPORT_CALLABLE
        return None
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id == "getattr"
        and len(expression.args) == 2
        and not expression.keywords
        and isinstance(expression.args[1], ast.Constant)
        and isinstance(expression.args[1].value, str)
    ):
        owner = _dynamic_import_binding_kind(
            expression.args[0],
            bindings,
        )
        attribute = expression.args[1].value
        if (
            owner == _BINDING_IMPORTLIB_MODULE
            and attribute == "import_module"
        ):
            return _BINDING_IMPORT_CALLABLE
        if (
            owner == _BINDING_BUILTINS_MODULE
            and attribute == "__import__"
        ):
            return _BINDING_IMPORT_CALLABLE
    return None


def _dynamic_import_bindings(
    tree: ast.AST,
    relative: str,
) -> dict[str, str]:
    bindings = {"__import__": _BINDING_IMPORT_CALLABLE}
    nodes = tuple(ast.walk(tree))
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    _record_dynamic_import_binding(
                        bindings,
                        alias.asname or "importlib",
                        _BINDING_IMPORTLIB_MODULE,
                        relative,
                    )
                elif (
                    alias.name.startswith("importlib.")
                    and alias.asname is None
                ):
                    _record_dynamic_import_binding(
                        bindings,
                        "importlib",
                        _BINDING_IMPORTLIB_MODULE,
                        relative,
                    )
                elif alias.name == "builtins":
                    _record_dynamic_import_binding(
                        bindings,
                        alias.asname or "builtins",
                        _BINDING_BUILTINS_MODULE,
                        relative,
                    )
            continue
        if (
            not isinstance(node, ast.ImportFrom)
            or node.level
            or node.module not in {"builtins", "importlib"}
        ):
            continue
        for alias in node.names:
            if alias.name == "*":
                raise _local_import_error(
                    f"wildcard dynamic import binding in {relative}"
                )
            if (
                node.module == "importlib"
                and alias.name == "import_module"
            ) or (
                node.module == "builtins"
                and alias.name == "__import__"
            ):
                _record_dynamic_import_binding(
                    bindings,
                    alias.asname or alias.name,
                    _BINDING_IMPORT_CALLABLE,
                    relative,
                )

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
            kind = _dynamic_import_binding_kind(value, bindings)
            if kind is None:
                continue
            for target in targets:
                if not isinstance(target, ast.Name):
                    raise _local_import_error(
                        "unsupported dynamic import alias target in "
                        f"{relative}"
                    )
                changed = (
                    _record_dynamic_import_binding(
                        bindings,
                        target.id,
                        kind,
                        relative,
                    )
                    or changed
                )
    return bindings


def _literal_dynamic_imports(
    tree: ast.AST,
    relative: str,
) -> tuple[str, ...]:
    bindings = _dynamic_import_bindings(tree, relative)
    imports = []
    for node in ast.walk(tree):
        if (
            not isinstance(node, ast.Call)
            or _dynamic_import_binding_kind(node.func, bindings)
            != _BINDING_IMPORT_CALLABLE
        ):
            continue
        if (
            not node.args
            or not isinstance(node.args[0], ast.Constant)
            or not isinstance(node.args[0].value, str)
        ):
            raise _local_import_error(
                f"nonliteral dynamic import in {relative}"
            )
        imports.append(node.args[0].value)
    return tuple(imports)


def _local_imports_from_source(
    module: str,
    relative: str,
    content: bytes,
    *,
    is_package: bool,
    source_for,
) -> tuple[str, ...]:
    try:
        tree = ast.parse(content, filename=relative)
    except (SyntaxError, UnicodeError) as error:
        raise _local_import_error(
            f"cannot parse committed local module: {relative}"
        ) from error
    package = module if is_package else module.rpartition(".")[0]
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(
                alias.name
                for alias in node.names
                if _is_local_module(alias.name)
            )
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            if not package:
                raise _local_import_error(
                    f"relative import without package in {relative}"
                )
            requested = "." * node.level + (node.module or "")
            try:
                base = importlib.util.resolve_name(requested, package)
            except (ImportError, ValueError) as error:
                raise _local_import_error(
                    f"invalid relative import in {relative}"
                ) from error
        else:
            base = node.module or ""
        if not _is_local_module(base):
            continue
        base_source = source_for(base)
        if base_source is not None:
            imports.add(base)
        if base_source is None or not base_source[2]:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            candidate = f"{base}.{alias.name}"
            if source_for(candidate) is not None:
                imports.add(candidate)
    imports.update(
        name
        for name in _literal_dynamic_imports(tree, relative)
        if _is_local_module(name)
    )
    return tuple(sorted(imports))


def _derive_local_import_closure(
    root: Path,
    input_commit: str,
    root_modules: tuple[str, ...],
) -> tuple[str, ...]:
    source_root = _preflight_root(root)
    commit = _preflight_commit(source_root, input_commit)
    cache: dict[str, tuple[str, bytes, bool] | None] = {}

    def source_for(module: str) -> tuple[str, bytes, bool] | None:
        if module not in cache:
            cache[module] = _committed_module_source(
                source_root,
                commit,
                module,
            )
        return cache[module]

    pending = list(root_modules)
    seen = set()
    paths = set()
    while pending:
        module = pending.pop()
        if module in seen:
            continue
        seen.add(module)
        source = source_for(module)
        if source is None:
            raise _local_import_error(f"cannot resolve local module: {module}")
        relative, content, is_package = source
        paths.add(relative)
        parts = module.split(".")
        for index in range(1, len(parts)):
            package = ".".join(parts[:index])
            if source_for(package) is not None:
                pending.append(package)
        pending.extend(
            _local_imports_from_source(
                module,
                relative,
                content,
                is_package=is_package,
                source_for=source_for,
            )
        )
    return tuple(sorted(paths))


def _preflight_local_import_closure(
    root: Path,
    input_commit: str,
    root_modules: tuple[str, ...],
    expected_paths: tuple[str, ...],
) -> tuple[str, ...]:
    source_root = _preflight_root(root)
    commit = _preflight_commit(source_root, input_commit)
    if (
        expected_paths != tuple(sorted(expected_paths))
        or len(expected_paths) != len(set(expected_paths))
    ):
        raise _local_import_error("executable registry must be sorted")
    derived = _derive_local_import_closure(
        source_root,
        commit,
        root_modules,
    )
    if derived != expected_paths:
        raise _local_import_error(
            "executable registry does not match recursive import closure"
        )
    for relative in derived:
        path = source_root / relative
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise _local_import_error(
                f"working local module cannot be resolved: {relative}"
            ) from error
        if (
            path.is_symlink()
            or not resolved.is_relative_to(source_root)
            or not resolved.is_file()
        ):
            raise _local_import_error(
                f"working local module is not a regular file: {relative}"
            )
        committed = _preflight_git_blob(
            source_root,
            commit,
            relative,
            allow_absent=False,
        )
        if path.read_bytes() != committed:
            raise _local_import_error(
                f"working local module does not match commit: {relative}"
            )
    shadow_candidates = set()
    for relative in derived:
        parts = Path(relative).parts
        package_parts = parts[:-1]
        for index in range(1, len(package_parts) + 1):
            shadow_candidates.add(
                Path(*package_parts[:index], "__init__.py").as_posix()
            )
        if parts[-1] != "__init__.py":
            shadow_candidates.add(
                (Path(relative).with_suffix("") / "__init__.py").as_posix()
            )
    for relative in sorted(shadow_candidates.difference(derived)):
        committed = _preflight_git_blob(
            source_root,
            commit,
            relative,
            allow_absent=True,
        )
        if committed is not None or (source_root / relative).exists():
            raise _local_import_error(
                "unregistered package initializer shadows closure: "
                f"{relative}"
            )
    return derived


def _activate_local_import_cache_isolation() -> Path:
    global _LOCAL_CACHE_PREFIX
    if _LOCAL_DEPENDENCIES_LOADED:
        raise _local_import_error(
            "cache isolation must precede repository-local imports"
        )
    if _LOCAL_CACHE_PREFIX is not None:
        return _LOCAL_CACHE_PREFIX
    try:
        prefix = Path(
            tempfile.mkdtemp(prefix="candidate-c-closeout-pycache-")
        ).resolve(strict=True)
    except OSError as error:
        raise _local_import_error(
            "cannot create isolated local-module cache prefix"
        ) from error
    if not prefix.is_dir() or any(prefix.iterdir()):
        shutil.rmtree(prefix, ignore_errors=True)
        raise _local_import_error(
            "local-module cache prefix is not an empty directory"
        )
    sys.pycache_prefix = str(prefix)
    sys.dont_write_bytecode = True
    importlib.invalidate_caches()
    atexit.register(shutil.rmtree, prefix, ignore_errors=True)
    _LOCAL_CACHE_PREFIX = prefix
    return prefix


def _module_name_for_path(relative: str) -> str:
    path = Path(relative)
    if path.name == "__init__.py":
        parts = path.parent.parts
    else:
        parts = path.with_suffix("").parts
    if not parts:
        raise _local_import_error(
            f"cannot derive local module name: {relative}"
        )
    return ".".join(parts)


def _preflight_launcher_file_origin(
    root: Path,
    launcher_relative: str,
) -> None:
    expected = (root / launcher_relative).resolve(strict=True)
    try:
        actual = Path(__file__).resolve(strict=True)
    except OSError as error:
        raise _local_import_error(
            "launcher file cannot be resolved"
        ) from error
    if actual != expected:
        raise _local_import_error(
            "launcher file does not belong to requested root"
        )


def _reject_preloaded_local_modules(
    expected_paths: tuple[str, ...],
) -> None:
    for relative in expected_paths:
        module_name = _module_name_for_path(relative)
        if module_name in sys.modules:
            raise _local_import_error(
                f"declared local module already loaded: {module_name}"
            )


def _activate_verified_import_root(root: Path) -> None:
    retained = []
    for entry in sys.path:
        try:
            resolved = Path(entry or Path.cwd()).resolve()
        except OSError:
            retained.append(entry)
            continue
        if resolved != root:
            retained.append(entry)
    sys.path[:] = [str(root), *retained]
    importlib.invalidate_caches()


def _validate_loaded_local_module_origins(
    root: Path,
    expected_paths: tuple[str, ...],
) -> None:
    for relative in expected_paths:
        module_name = _module_name_for_path(relative)
        module = sys.modules.get(module_name)
        if module is None:
            continue
        origin = getattr(module, "__file__", None)
        try:
            actual = Path(origin).resolve(strict=True)
            expected = (root / relative).resolve(strict=True)
        except (OSError, TypeError) as error:
            raise _local_import_error(
                f"loaded local module origin mismatch: {module_name}"
            ) from error
        if actual != expected:
            raise _local_import_error(
                f"loaded local module origin mismatch: {module_name}"
            )


def _load_local_dependencies() -> None:
    global _LOCAL_DEPENDENCIES_LOADED
    if _LOCAL_DEPENDENCIES_LOADED:
        return
    state_module = importlib.import_module(
        "scripts.mat_sab_research_state"
    )
    gate_module = importlib.import_module(
        "scripts.run_candidate_c_rank_bounded_gate"
    )
    if tuple(gate_module.CLOSEOUT_EXECUTABLE_INPUTS) != (
        CLOSEOUT_EXECUTABLE_INPUTS
    ):
        raise RuntimeError("closeout executable registry mismatch")
    expected_constants = {
        "ACTUAL_EVIDENCE": ACTUAL_EVIDENCE,
        "ADMIT": ADMIT,
        "INCONCLUSIVE": INCONCLUSIVE,
        "REJECT": REJECT,
    }
    for name, expected in expected_constants.items():
        if getattr(gate_module, name) != expected:
            raise RuntimeError(f"Candidate C constant mismatch: {name}")
    state_names = (
        "load_state",
        "transition_candidate",
        "validate_state",
        "write_state",
    )
    gate_names = (
        "SUMMARY_FIELDS",
        "canonical_summary_record",
        "evaluate_candidate_c",
        "gate_result_from_decision_evidence",
        "load_decision_evidence",
        "_closeout_executable_rows",
        "_input_paths",
        "_validated_input_rows",
    )
    for name in state_names:
        globals()[name] = getattr(state_module, name)
    for name in gate_names:
        globals()[name] = getattr(gate_module, name)
    _LOCAL_DEPENDENCIES_LOADED = True


def _resolved_root(root: Path) -> Path:
    resolved = Path(root).resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"root is not a directory: {resolved}")
    return resolved


def _resolved_under_root(
    root: Path,
    path: Path,
    label: str,
    *,
    strict: bool,
) -> Path:
    resolved = Path(path).resolve(strict=strict)
    if not resolved.is_relative_to(root):
        raise ValueError(f"{label} escapes root: {resolved}")
    return resolved


def _read_text(path: Path) -> str:
    return path.read_text(encoding="ascii") if path.exists() else ""


def _bounded_block(start: str, end: str, content: str) -> str:
    return f"{start}\n{content.rstrip()}\n{end}"


def _check_append(
    path: Path,
    start: str,
    end: str,
    content: str,
    accepted_previous: tuple[str, ...] = (),
) -> str:
    current = _read_text(path)
    lines = current.splitlines()
    if any(
        marker in line and line != marker
        for marker in (start, end)
        for line in lines
    ):
        raise ValueError(f"ledger block marker mismatch in {path}: {start}")
    starts = [index for index, line in enumerate(lines) if line == start]
    ends = [index for index, line in enumerate(lines) if line == end]
    if not starts and not ends:
        return "append"
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        raise ValueError(f"ledger block marker mismatch in {path}: {start}")
    actual = "\n".join(lines[starts[0] : ends[0] + 1])
    if actual == _bounded_block(start, end, content):
        return "unchanged"
    if any(
        actual == _bounded_block(start, end, previous)
        for previous in accepted_previous
    ):
        return "replace"
    raise ValueError(f"ledger block/content mismatch in {path}: {start}")


def _append_once(
    path: Path,
    start: str,
    end: str,
    content: str,
    accepted_previous: tuple[str, ...] = (),
) -> None:
    action = _check_append(
        path,
        start,
        end,
        content,
        accepted_previous,
    )
    if action == "unchanged":
        return
    current = _read_text(path)
    if action == "replace":
        previous = next(
            previous
            for previous in accepted_previous
            if _bounded_block(start, end, previous) in current
        )
        current = current.replace(
            _bounded_block(start, end, previous),
            _bounded_block(start, end, content),
            1,
        )
        path.write_text(
            current,
            encoding="ascii",
            newline="\n",
        )
        return
    separator = "" if not current or current.endswith("\n") else "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        current + separator + _bounded_block(start, end, content) + "\n",
        encoding="ascii",
        newline="\n",
    )


def _summary_record(path: Path) -> dict[str, str]:
    try:
        with path.open(newline="", encoding="ascii") as handle:
            records = list(csv.reader(handle, strict=True))
    except (csv.Error, UnicodeError) as error:
        raise ValueError(
            "summary must contain one canonical decision"
        ) from error
    if len(records) != 2:
        raise ValueError("summary must contain one canonical decision")
    fields, row = records
    if (
        tuple(fields) != SUMMARY_FIELDS
        or len(fields) != len(set(fields))
        or len(row) != len(fields)
    ):
        raise ValueError("summary must contain one canonical decision")
    record = dict(zip(fields, row))
    if record["decision"] not in DECISIONS:
        raise ValueError("summary must contain one canonical decision")
    optional_numeric = {
        "complete_cost",
        "amdahl_projection",
        "amdahl_pessimistic_projection",
    }
    if any(
        value == "" and field not in optional_numeric
        for field, value in record.items()
    ):
        raise ValueError("summary must contain one canonical decision")
    if record["complete_cost"] == "" and (
        record["complete_cost_status"] != "SKIPPED_NO_REGISTERED_OPERATOR"
    ):
        raise ValueError("blank complete cost requires skipped Task 4")
    if record["amdahl_projection"] == "" and (
        record["amdahl_status"] != "SKIPPED_NO_REGISTERED_OPERATOR"
    ):
        raise ValueError("blank Amdahl projection requires skipped Task 4")
    if record["amdahl_pessimistic_projection"] == "" and (
        record["amdahl_status"] != "SKIPPED_NO_REGISTERED_OPERATOR"
    ):
        raise ValueError(
            "blank pessimistic Amdahl projection requires skipped Task 4"
        )
    return record


def _strict_csv_rows(
    path: Path,
    fields: tuple[str, ...],
    label: str,
) -> tuple[dict[str, str], ...]:
    try:
        with path.open(newline="", encoding="ascii") as handle:
            records = list(csv.reader(handle, strict=True))
    except (csv.Error, UnicodeError) as error:
        raise ValueError(f"{label} is malformed") from error
    if (
        not records
        or tuple(records[0]) != fields
        or len(records[0]) != len(set(records[0]))
        or any(len(row) != len(fields) for row in records[1:])
    ):
        raise ValueError(f"{label} is malformed")
    return tuple(dict(zip(fields, row)) for row in records[1:])


def _validate_published_manifests(
    root: Path,
    pack: Path,
    input_commit: str,
    recomputed_result,
) -> None:
    _resolved_commit, expected_inputs = _validated_input_rows(
        root,
        input_commit,
        _input_paths(root, recomputed_result),
    )
    input_manifest = _resolved_under_root(
        root,
        pack / "input_manifest.csv",
        "published input manifest",
        strict=True,
    )
    actual_inputs = _strict_csv_rows(
        input_manifest,
        ("path", "availability", "sha256"),
        "published input manifest",
    )
    if actual_inputs != expected_inputs:
        raise ValueError(
            "published input manifest does not match committed inputs"
        )

    executable_manifest = _resolved_under_root(
        root,
        pack / "closeout_executable_manifest.csv",
        "published closeout executable manifest",
        strict=True,
    )
    actual_executables = _strict_csv_rows(
        executable_manifest,
        ("role", "path", "sha256"),
        "published closeout executable manifest",
    )
    expected_executables = _closeout_executable_rows(expected_inputs)
    if (
        tuple(row["path"] for row in actual_executables)
        != CLOSEOUT_EXECUTABLE_INPUTS
        or actual_executables != expected_executables
    ):
        raise ValueError(
            "published closeout executable manifest does not match "
            "committed executables"
        )


def _generator_command(input_commit: str) -> str:
    return (
        "python scripts/run_candidate_c_rank_bounded_gate.py "
        f"--input-commit {input_commit}"
    )


def _closeout_command(input_commit: str) -> str:
    return (
        "python scripts/apply_candidate_c_rank_bounded_gate.py "
        f"--input-commit {input_commit}"
    )


def _run_row(decision: str, input_commit: str) -> dict[str, str]:
    return {
        "run_id": RUN_MARKER,
        "date": "2026-07-17",
        "commit_or_state": "candidate-c-rank-bounded-mechanism-gate",
        "stage": "Candidate C mechanism gate",
        "backend": "exact-finite-ring-symbolic",
        "command": _generator_command(input_commit),
        "params": "C1/C2;r=2/4/6;rho<=2;Task4=registered-only",
        "seed": "deterministic",
        "status": decision,
        "summary": (
            "Hash-bound source, equation, symbolic, phase, schedule, rank, "
            "compression, complete-cost, and Amdahl gates close Candidate C."
        ),
        "artifacts": "repro/candidate_c_rank_bounded_gate/",
    }


def _legacy_run_row(decision: str) -> dict[str, str]:
    row = _run_row(decision, "")
    row["command"] = "python scripts/run_candidate_c_rank_bounded_gate.py"
    return row


def _run_log_plan(
    root: Path,
    decision: str,
    input_commit: str,
    *,
    allow_fixture: bool,
) -> tuple[Path, list[str], str, str | None]:
    path = _resolved_under_root(
        root,
        root / "repro/run_log.csv",
        "run-log destination",
        strict=True,
    )
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            records = list(csv.reader(handle, strict=True))
    except (csv.Error, UnicodeError) as error:
        raise ValueError("run log header must match canonical schema") from error
    fields = records[0] if records else []
    expected = list(_run_row(decision, input_commit))
    if fields != expected or len(fields) != len(set(fields)):
        raise ValueError("run log header must match canonical schema")
    rows = []
    for physical in records[1:]:
        marker_positions = [
            index for index, value in enumerate(physical)
            if value == RUN_MARKER
        ]
        if len(physical) == len(fields):
            if any(index != 0 for index in marker_positions):
                raise ValueError("run log rows must match canonical schema")
            rows.append(dict(zip(fields, physical)))
        elif marker_positions:
            raise ValueError("run log rows must match canonical schema")
    matches = [row for row in rows if row["run_id"] == RUN_MARKER]
    if len(matches) > 1:
        raise ValueError(f"duplicate run-log marker: {RUN_MARKER}")
    if matches:
        if matches[0] == _run_row(decision, input_commit):
            return path, fields, "unchanged", None
        if matches[0] == _legacy_run_row(decision):
            return path, fields, "replace", None
        command = matches[0]["command"]
        pinned = PINNED_GENERATOR_COMMAND.fullmatch(command)
        if pinned is not None:
            previous_input_commit = pinned.group(1)
            if matches[0] == _run_row(decision, previous_input_commit):
                if not allow_fixture:
                    ancestor = subprocess.run(
                        [
                            "git",
                            "merge-base",
                            "--is-ancestor",
                            previous_input_commit,
                            input_commit,
                        ],
                        cwd=root,
                        check=False,
                        capture_output=True,
                    )
                    if ancestor.returncode != 0:
                        raise ValueError(
                            "run-log prior input commit is not an ancestor"
                        )
                return (
                    path,
                    fields,
                    "replace",
                    previous_input_commit,
                )
        raise ValueError(f"run-log marker/content mismatch: {RUN_MARKER}")
    return path, fields, "append", None


def _serialized_run_row(
    fields: list[str],
    row: dict[str, str],
) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fields,
        lineterminator="\n",
    )
    writer.writerow(row)
    return buffer.getvalue()


def _append_run(
    path: Path,
    fields: list[str],
    decision: str,
    input_commit: str,
    action: str,
    previous_input_commit: str | None,
) -> None:
    if action == "unchanged":
        return
    if action == "replace":
        current = path.read_text(encoding="ascii")
        previous_row = (
            _legacy_run_row(decision)
            if previous_input_commit is None
            else _run_row(decision, previous_input_commit)
        )
        legacy = _serialized_run_row(fields, previous_row)
        if current.count(legacy) != 1:
            raise ValueError(
                f"run-log legacy row bytes changed: {RUN_MARKER}"
            )
        path.write_text(
            current.replace(
                legacy,
                _serialized_run_row(
                    fields,
                    _run_row(decision, input_commit),
                ),
                1,
            ),
            encoding="ascii",
            newline="\n",
        )
        return
    if path.stat().st_size:
        with path.open("rb") as handle:
            handle.seek(-1, 2)
            terminated = handle.read(1) in {b"\r", b"\n"}
        if not terminated:
            with path.open("ab") as handle:
                handle.write(b"\n")
    with path.open("a", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writerow(_run_row(decision, input_commit))


def _legacy_checklist(decision: str) -> str:
    return f"""- [x] Candidate C records `{decision}` from hash-bound source,
  equation, symbolic-independence, phase, schedule, rank, compression,
  complete-cost, and Amdahl fields. Reproduce with
  `python scripts/run_candidate_c_rank_bounded_gate.py` followed by
  `python scripts/apply_candidate_c_rank_bounded_gate.py`; production hot-path
  permission remains false.
"""


def _pinned_checklist(decision: str, input_commit: str) -> str:
    return f"""- [x] Candidate C records `{decision}` from hash-bound source,
  equation, symbolic-independence, phase, schedule, rank, compression,
  complete-cost, and Amdahl fields. Reproduce with
  `{_generator_command(input_commit)}` followed by
  `{_closeout_command(input_commit)}`; production hot-path
  permission remains false.
"""


def _ledger_entries(
    decision: str,
    input_commit: str,
    previous_input_commit: str | None,
) -> tuple[tuple[str, str, str, str, tuple[str, ...]], ...]:
    hypothesis = f"""H_candidate_c_rank_bounded_mechanism:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/candidate_c_rank_bounded_gate/summary.csv
    - repro/candidate_c_rank_bounded_gate/terminal_record.csv
    - repro/candidate_c_rank_bounded_gate/rank_growth.csv
    - repro/candidate_c_rank_bounded_gate/compression_gate.csv
    - repro/candidate_c_rank_bounded_gate/complete_cost.csv
    - repro/candidate_c_rank_bounded_gate/amdahl_projection.csv
  conclusion: >
    Candidate C closes the finite C1/C2 rank-bounded-state campaign. Task 4
    remains SKIPPED_NO_REGISTERED_OPERATOR on the actual route, with no
    fabricated complete-cost or Amdahl values. Production permission is false.
"""
    manifest = """- candidate_c_rank_bounded_gate:
  - `research/mat_sab/candidate_c_operator_tensor.py`
  - `research/mat_sab/candidate_c_registered_replay.py`
  - `scripts/run_candidate_c_rank_bounded_gate.py`
  - `scripts/apply_candidate_c_rank_bounded_gate.py`
  - `docs/candidate_c_rank_bounded_mechanism_gate.md`
  - `algorithm_variants/candidate_c_rank_bounded_state.md`
  - `experiments/candidate_c_rank_bounded_gate_plan.md`
  - `repro/candidate_c_rank_bounded_gate/`
"""
    accepted_checklists = [_legacy_checklist(decision)]
    if previous_input_commit is not None:
        accepted_checklists.append(
            _pinned_checklist(decision, previous_input_commit)
        )
    return (
        (
            "hypotheses/hypothesis_register.yaml",
            HYPOTHESIS_START,
            HYPOTHESIS_END,
            hypothesis,
            (),
        ),
        (
            "repro/artifact_manifest.md",
            MANIFEST_START,
            MANIFEST_END,
            manifest,
            (),
        ),
        (
            "repro/reproduction_checklist.md",
            CHECKLIST_START,
            CHECKLIST_END,
            _pinned_checklist(decision, input_commit),
            tuple(accepted_checklists),
        ),
    )


def _validate_pre_state(state: dict[str, object]) -> None:
    candidates = state["candidates"]
    if not (
        state["goal_status"] == "ACTIVE"
        and state["paper_gate"] == "BLOCKED"
        and state["production_hot_path_permission"] is False
        and state["active_candidate"] == "C"
        and state.get("last_decision") == PREDECESSOR_DECISION
        and candidates["A"]["status"] == "REJECTED"
        and candidates["B"]["status"] == "REJECTED"
        and candidates["C"]["status"] == "INTAKE"
        and candidates["C"]["equation_revisions_used"] == 0
    ):
        raise ValueError("state is not at the Candidate C mechanism gate")


def _validate_applied_state(
    state: dict[str, object],
    decision: str,
) -> None:
    candidates = state["candidates"]
    common = (
        state["active_candidate"] == "C"
        and state["paper_gate"] == "BLOCKED"
        and state["production_hot_path_permission"] is False
        and state.get("last_decision") == decision
        and candidates["A"]["status"] == "REJECTED"
        and candidates["B"]["status"] == "REJECTED"
        and candidates["C"]["equation_revisions_used"] == 1
    )
    if decision == ADMIT:
        branch = (
            candidates["C"]["status"] == "ADVERSARIAL_CHECKER_PASS"
            and state["goal_status"] == "ACTIVE"
        )
    elif decision == REJECT:
        branch = (
            candidates["C"]["status"] == "REJECTED"
            and state["goal_status"] == "RESEARCH_CAMPAIGN_EXHAUSTED"
        )
    elif decision == INCONCLUSIVE:
        branch = (
            candidates["C"]["status"] == "INCONCLUSIVE"
            and state["goal_status"] == "RESEARCH_CAMPAIGN_INCONCLUSIVE"
        )
    else:
        branch = False
    if not common or not branch:
        raise ValueError(
            f"state/decision mismatch: {candidates['C']['status']} and "
            f"{decision}"
        )
    validate_state(state)


def _transition_initial_state(
    state: dict[str, object],
    decision: str,
) -> dict[str, object]:
    _validate_pre_state(state)
    changed = transition_candidate(
        state,
        "C",
        "TECHGRAPH_ANCHORED",
        TECHGRAPH_DECISION,
    )
    changed = transition_candidate(
        changed,
        "C",
        "EQUATIONS_DEFINED",
        EQUATIONS_DECISION,
    )
    targets = {
        ADMIT: "ADVERSARIAL_CHECKER_PASS",
        REJECT: "REJECTED",
        INCONCLUSIVE: "INCONCLUSIVE",
    }
    changed = transition_candidate(
        changed,
        "C",
        targets[decision],
        decision,
    )
    _validate_applied_state(changed, decision)
    return changed


def _snapshot_outputs(
    paths: tuple[Path, ...],
) -> dict[Path, bytes | None]:
    return {
        path: path.read_bytes() if path.exists() else None
        for path in paths
    }


def _restore_outputs(snapshot: dict[Path, bytes | None]) -> None:
    for path, content in snapshot.items():
        if content is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)


def apply_gate(
    root: Path,
    state_path: Path,
    summary_path: Path,
    *,
    input_commit: str,
    evidence_path: Path | None = None,
    allow_fixture: bool = False,
) -> str:
    resolved_root = _resolved_root(root)
    state = _resolved_under_root(
        resolved_root,
        state_path,
        "state path",
        strict=True,
    )
    summary = _resolved_under_root(
        resolved_root,
        summary_path,
        "summary path",
        strict=True,
    )
    evidence = _resolved_under_root(
        resolved_root,
        (
            evidence_path
            if evidence_path is not None
            else summary.parent / "decision_evidence.json"
        ),
        "decision evidence path",
        strict=True,
    )
    summary_record = _summary_record(summary)
    raw_evidence = load_decision_evidence(evidence)
    if raw_evidence.binding_kind == ACTUAL_EVIDENCE:
        recomputed_result = evaluate_candidate_c(
            resolved_root,
            input_commit=input_commit,
        )
        if raw_evidence != recomputed_result.decision_evidence:
            raise ValueError(
                "decision evidence does not match fresh repository evidence"
            )
        _validate_published_manifests(
            resolved_root,
            summary.parent,
            input_commit,
            recomputed_result,
        )
    else:
        recomputed_result = gate_result_from_decision_evidence(
            raw_evidence,
            allow_fixture=allow_fixture,
        )
    recomputed = canonical_summary_record(
        recomputed_result,
        root=resolved_root,
        input_commit=input_commit,
        allow_fixture=allow_fixture,
    )
    if summary_record != recomputed:
        raise ValueError("summary does not match recomputed gate evidence")
    decision = summary_record["decision"]
    current_state = load_state(state)

    (
        run_path,
        run_fields,
        run_action,
        previous_input_commit,
    ) = _run_log_plan(
        resolved_root,
        decision,
        input_commit,
        allow_fixture=allow_fixture,
    )
    entries = tuple(
        (
            _resolved_under_root(
                resolved_root,
                resolved_root / relative,
                f"ledger destination {relative}",
                strict=False,
            ),
            start,
            end,
            content,
            accepted_previous,
        )
        for relative, start, end, content, accepted_previous
        in _ledger_entries(
            decision,
            input_commit,
            previous_input_commit,
        )
    )
    for path, start, end, content, accepted_previous in entries:
        _check_append(
            path,
            start,
            end,
            content,
            accepted_previous,
        )
    current = current_state["candidates"]["C"]["status"]
    if current == "INTAKE":
        changed = _transition_initial_state(current_state, decision)
    elif current in {
        "ADVERSARIAL_CHECKER_PASS",
        "REJECTED",
        "INCONCLUSIVE",
    }:
        _validate_applied_state(current_state, decision)
        changed = None
    else:
        raise ValueError("state is not at the Candidate C mechanism gate")

    outputs = (
        state,
        *(
            path
            for path, _start, _end, _content, _accepted_previous
            in entries
        ),
        run_path,
    )
    snapshot = _snapshot_outputs(outputs)
    try:
        if changed is not None:
            write_state(state, changed)
        for path, start, end, content, accepted_previous in entries:
            _append_once(
                path,
                start,
                end,
                content,
                accepted_previous,
            )
        _append_run(
            run_path,
            run_fields,
            decision,
            input_commit,
            run_action,
            previous_input_commit,
        )
    except Exception:
        _restore_outputs(snapshot)
        raise
    return decision


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--input-commit", required=True)
    args = parser.parse_args()
    source_root = _preflight_launcher_root(args.root)
    _preflight_local_import_closure(
        source_root,
        args.input_commit,
        CLOSEOUT_LOCAL_IMPORT_ROOTS,
        CLOSEOUT_EXECUTABLE_INPUTS,
    )
    _preflight_launcher_file_origin(
        source_root,
        "scripts/apply_candidate_c_rank_bounded_gate.py",
    )
    _reject_preloaded_local_modules(CLOSEOUT_EXECUTABLE_INPUTS)
    _activate_verified_import_root(source_root)
    _activate_local_import_cache_isolation()
    _load_local_dependencies()
    _validate_loaded_local_module_origins(
        source_root,
        CLOSEOUT_EXECUTABLE_INPUTS,
    )
    state = args.state or source_root / "research_state.yaml"
    summary = (
        args.summary
        or source_root
        / "repro/candidate_c_rank_bounded_gate/summary.csv"
    )
    print(
        apply_gate(
            source_root,
            state,
            summary,
            input_commit=args.input_commit,
            evidence_path=args.evidence,
        )
    )
    return 0


if __name__ != "__main__":
    _load_local_dependencies()
else:
    raise SystemExit(main())
