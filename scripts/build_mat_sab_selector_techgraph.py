#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import atexit
import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]

OUT_DIR = ROOT / "paper_techgraphs"
JSON_OUT = OUT_DIR / "2025_686_mat_sab_selector.yaml"
GRAPH_OUT = OUT_DIR / "2025_686_mat_sab_selector_graph.md"
GAPS_OUT = OUT_DIR / "2025_686_mat_sab_selector_gaps.md"
DISCOVERY_COMMAND = (
    'python -m unittest discover -s tests/research -p "test_*.py" -v'
)
SELECTOR_LOCAL_IMPORT_ROOTS = (
    "scripts.build_mat_sab_selector_techgraph",
)
SELECTOR_EXECUTABLE_INPUTS = (
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
SELECTOR_IMPLEMENTATION_INPUTS = SELECTOR_EXECUTABLE_INPUTS
_LOCAL_IMPORT_PREFIXES = ("research", "scripts")
_LOCAL_DEPENDENCIES_LOADED = False
_LOCAL_CACHE_PREFIX: Path | None = None
_BINDING_IMPORTLIB_MODULE = "IMPORTLIB_MODULE"
_BINDING_BUILTINS_MODULE = "BUILTINS_MODULE"
_BINDING_IMPORT_CALLABLE = "IMPORT_CALLABLE"

NODE_SPECS = (
    ("sab_schedule", "src/sparse_amortized_bootstrap.c", "void RGSW_monomial_mul(", "scalar SAB butterfly and sparse schedule"),
    ("pvw_phase", "src/mosfhet/src/pvwtmlwe.c", "void pvmtmlwe_phase(", "phase map b_q - a*s_q"),
    ("pvw_randomization", "src/mosfhet/src/pvwtmlwe.c", "void pvmtmlwe_sample(", "shared random mask and r body corrections"),
    ("dense_keygen", "src/mosfhet/src/mattrgsw.c", "void mat_trgsw_monomial_sample(", "standard dense MAT-GGSW row sampling"),
    ("dense_decompose", "src/mosfhet/src/mattrgsw.c", "pvmtmlwe_decompose(scratch->dec", "decompose all k+r components"),
    ("dense_addmul", "src/mosfhet/src/mattrgsw.c", "static void mat_trgsw_mul_pvmtmlwe_DFT_from_dec(", "dense selector-output products"),
    ("compact_kernel", "src/mosfhet/src/mattrgsw.c", "void mat_trgsw_compact_mul_pvmtmlwe_DFT(", "lane-local compact evaluator"),
    ("generalized_lane_pair", "repro/stage134_generalized_lane_pair_input_ep_gate/summary.csv", "", "closure-restoring but performance-negative lane-pair input"),
    ("shared_mask_kernel", "repro/stage138_shared_mask_compact_gate/summary.csv", "", "positive isolated compact-kernel evidence"),
    ("closure_failure", "repro/stage139_compact_closure_audit/summary.csv", "", "compact output not closed as standard PVW state"),
    ("star_cycle_support", "repro/stage203_production_selector_equation_probe/equation_map.csv", "lane_neighbor_body_interaction", "4r declared active support"),
    ("neighbor_gap", "repro/stage222_isolated_compact_ep_integration/expressiveness_results.csv", "", "lane-local API lacks neighbor-capable selector"),
    ("distribution_blocker", "repro/stage249_structured_compact_distribution_security/claim_boundary.csv", "", "public compact-saving pattern remains distinguishable"),
    ("finite_semantic_zero", "repro/stage329_formal_compact_selector_checker/summary.csv", "", "finite semantic-zero pass with security open"),
)
SELECTOR_SOURCE_STATE_INPUTS = tuple(
    sorted(
        {
            *SELECTOR_IMPLEMENTATION_INPUTS,
            "research_state.yaml",
            *(spec[1] for spec in NODE_SPECS),
        }
    )
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
            tempfile.mkdtemp(prefix="mat-sab-selector-pycache-")
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
    globals()["load_state"] = state_module.load_state
    gate_names = (
        "GateEvidenceError",
        "_resolve_under_root",
        "_resolved_directory",
        "_restore_file_atomic",
        "_validated_input_rows",
    )
    for name in gate_names:
        globals()[name] = getattr(gate_module, name)
    _LOCAL_DEPENDENCIES_LOADED = True


EDGES = (
    ("sab_schedule", "dense_decompose", "each MAT CMUX invokes external-product decomposition"),
    ("dense_decompose", "dense_addmul", "m*T streams feed m*m*T products"),
    ("pvw_randomization", "dense_keygen", "every selector column is a PVW ciphertext sample"),
    ("pvw_phase", "closure_failure", "output must preserve all r phase equations"),
    ("shared_mask_kernel", "closure_failure", "local speedup alone does not close the SAB state"),
    ("generalized_lane_pair", "closure_failure", "closure restoration repeats expensive transforms"),
    ("star_cycle_support", "neighbor_gap", "cycle terms require neighbor-capable output"),
    ("star_cycle_support", "distribution_blocker", "semantic sparsity must not become public leakage"),
    ("finite_semantic_zero", "distribution_blocker", "finite algebra is not a distribution proof"),
)

PRE_GATE_OPEN_GAPS = (
    "standard PVW randomization dimension",
    "production key distribution and assumption comparison",
    "noise recurrence under the admitted selector representation",
    "Amdahl projection against exact-dense complete SAB",
    "isolated kernel and complete-SAB evidence",
)
POST_A_REJECTION_OPEN_GAPS = (
    "Candidate B factorized-operator equation gate (not begun)",
    "production key distribution and assumption comparison for an admitted representation",
    "noise recurrence under an admitted selector representation",
    "Amdahl projection against exact-dense complete SAB",
    "isolated kernel and complete-SAB evidence",
)
POST_B_REJECTION_OPEN_GAPS = (
    "Candidate C rank-bounded shared-mask state equation gate (not begun)",
    "phase and rank-growth checks for the admitted accumulator state",
    "public relinearization cost and lane-phase preservation",
    "Amdahl projection against exact-dense complete SAB",
    "isolated kernel and complete-SAB evidence",
)
TERMINAL_CAMPAIGN_BOUNDARIES = (
    (
        "Task 3B has no C2 seed or material; Task 4 is "
        "SKIPPED_NO_REGISTERED_OPERATOR with no numeric complete-cost or "
        "Amdahl values."
    ),
    (
        "The exact-dense PVW/MAT-SAB implementation and its scoped measured "
        "result remain preserved."
    ),
    (
        "No Candidate D is opened automatically; any continuation requires "
        "a separately approved research design."
    ),
)
CURRENT_TERMINAL_CAMPAIGN_BOUNDARIES = (
    (
        "Candidate E was the only reserved fallback and is now closed; no "
        "additional mechanism is opened automatically."
    ),
    (
        "The exact-dense PVW/MAT-SAB implementation and any completed "
        "Candidate D/E evidence remain preserved."
    ),
)


def _safe_source_file(root: Path, relative: str, label: str) -> Path:
    path = _resolve_under_root(
        root,
        root / relative,
        label,
        strict=False,
    )
    if not path.is_file():
        raise GateEvidenceError(f"{label} is not a file: {path}")
    return path


def _load_state_safe(root: Path) -> dict[str, object]:
    state_path = _safe_source_file(
        root,
        "research_state.yaml",
        "selector state source",
    )
    return load_state(state_path)


def _node(
    root: Path,
    spec: tuple[str, str, str, str],
    source_hashes: Mapping[str, str] | None = None,
) -> dict[str, object]:
    node_id, relative, needle, role = spec
    path = _safe_source_file(
        root,
        relative,
        f"selector node source {node_id}",
    )
    contains = (
        not needle
        or needle in path.read_text(encoding="utf-8", errors="replace")
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if (
        source_hashes is not None
        and source_hashes.get(relative) != digest
    ):
        raise GateEvidenceError(
            f"selector node source hash changed: {relative}"
        )
    return {
        "id": node_id,
        "path": relative,
        "symbol_or_token": needle,
        "role": role,
        "anchor_status": "PASS" if contains else "FAIL",
        "sha256": digest,
    }


def _campaign_view(state: Mapping[str, object]) -> dict[str, object]:
    candidates = state["candidates"]
    candidate_order = tuple(state["candidate_order"])
    active_candidate = str(state["active_candidate"])
    active_status = str(candidates[active_candidate]["status"])
    candidate_e_exhausted = (
        state["goal_status"] == "RESEARCH_CAMPAIGN_EXHAUSTED"
        and active_candidate == "E"
        and candidates.get("D", {}).get("status") == "REJECTED"
        and candidates.get("E", {}).get("status") == "REJECTED"
    )
    campaign_state = {
        "goal_status": state["goal_status"],
        "paper_gate": state["paper_gate"],
        "active_candidate": (
            None if candidate_e_exhausted else active_candidate
        ),
        "active_candidate_status": (
            None if candidate_e_exhausted else active_status
        ),
    }
    campaign_state.update(
        {
            f"candidate_{candidate.lower()}_status": (
                candidates[candidate]["status"]
            )
            for candidate in candidate_order
        }
    )
    campaign_state["last_decision"] = state["last_decision"]
    if (
        state["goal_status"] == "RESEARCH_CAMPAIGN_EXHAUSTED"
        and active_candidate == "C"
        and all(
            candidates[candidate]["status"] == "REJECTED"
            for candidate in ("A", "B", "C")
        )
    ):
        disposition = (
            "The finite A/B/C mechanism campaign is exhausted; Candidate C "
            "closed on its scoped C1 nonpositive structural-cost failure."
        )
        next_step = (
            "Task 3B and Task 4 were skipped; exact-dense PVW/MAT-SAB "
            "evidence is preserved; no Candidate D is opened automatically."
        )
        open_gaps = TERMINAL_CAMPAIGN_BOUNDARIES
    elif candidate_e_exhausted:
        disposition = (
            "Candidate D is rejected and Candidate E is rejected; the "
            "current Candidate D/E campaign is exhausted."
        )
        next_step = (
            "No active candidate remains; preserve the completed evidence "
            "and require a separately approved design for any continuation."
        )
        open_gaps = CURRENT_TERMINAL_CAMPAIGN_BOUNDARIES
    elif (
        all(
            candidates[candidate]["status"] == "REJECTED"
            for candidate in ("A", "B", "C")
        )
        and active_candidate == "D"
    ):
        disposition = (
            "Candidates A, B, and C are closed under the predecessor "
            "contract."
        )
        next_step = (
            f"Candidate D is active at `{active_status}` under the current "
            "contract."
        )
        open_gaps = PRE_GATE_OPEN_GAPS
    elif (
        "D" in candidates
        and candidates["D"]["status"] == "REJECTED"
        and active_candidate == "E"
    ):
        disposition = (
            "Candidate D is rejected; the reserved Candidate E fallback "
            "is now active."
        )
        next_step = (
            f"Candidate E is active at `{active_status}` under the current "
            "contract."
        )
        open_gaps = PRE_GATE_OPEN_GAPS
    elif (
        candidates["A"]["status"] == "REJECTED"
        and active_candidate == "B"
    ):
        disposition = (
            "Candidate A is closed after failing the standard-PVW "
            "randomization necessary condition."
        )
        next_step = (
            f"Candidate B is active at `{active_status}`; its equations and "
            "implementation have not begun."
        )
        open_gaps = POST_A_REJECTION_OPEN_GAPS
    elif (
        candidates["A"]["status"] == "REJECTED"
        and candidates["B"]["status"] == "REJECTED"
        and active_candidate == "C"
    ):
        disposition = (
            "Candidate B is closed after failing the exact standard-PVW "
            "factorization gate."
        )
        next_step = (
            f"Candidate C is active at `{active_status}`; its equations and "
            "implementation have not begun."
        )
        open_gaps = POST_B_REJECTION_OPEN_GAPS
    else:
        disposition = (
            f"Candidate A remains at `{candidates['A']['status']}`."
        )
        next_step = (
            f"Candidate {active_candidate} is active at `{active_status}`."
        )
        open_gaps = PRE_GATE_OPEN_GAPS
    return {
        "campaign_state": campaign_state,
        "candidate_a_disposition": disposition,
        "next_step": next_step,
        "open_gaps": list(open_gaps),
    }


def build_graph(
    root: Path = ROOT,
    *,
    source_state_commit: str,
) -> dict[str, object]:
    source_root = _resolved_directory(root, "selector source root")
    resolved_commit, input_rows = _validated_input_rows(
        source_root,
        source_state_commit,
        SELECTOR_SOURCE_STATE_INPUTS,
    )
    if any(row["availability"] != "PRESENT" for row in input_rows):
        raise GateEvidenceError(
            "selector source/state manifest requires present files"
        )
    source_hashes = {
        row["path"]: row["sha256"] for row in input_rows
    }
    state = _load_state_safe(source_root)
    graph = {
        "schema_version": 3,
        "contract": state["contract"],
        "candidate": "A",
        "production_code_permission": state["production_hot_path_permission"],
        "selector_source_state_commit": resolved_commit,
        "selector_source_manifest": list(input_rows),
        "selector_executable_manifest": [
            row
            for row in input_rows
            if row["path"] in SELECTOR_EXECUTABLE_INPUTS
        ],
        "research_state_sha256": source_hashes["research_state.yaml"],
        "reproduction_command": (
            "python scripts/build_mat_sab_selector_techgraph.py "
            f"--source-state-commit {resolved_commit}"
        ),
        "nodes": [
            _node(source_root, spec, source_hashes)
            for spec in NODE_SPECS
        ],
        "edges": [
            {"from": source, "to": target, "relation": relation}
            for source, target, relation in EDGES
        ],
    }
    graph.update(_campaign_view(state))
    return graph


def _reproduction_markdown(graph: Mapping[str, object]) -> list[str]:
    return [
        "",
        "## Reproduction",
        "",
        "```powershell",
        str(graph["reproduction_command"]),
        DISCOVERY_COMMAND,
        "```",
    ]


def _campaign_markdown(graph: Mapping[str, object]) -> list[str]:
    state = graph["campaign_state"]
    lines = [
        "## Campaign State",
        "",
        f'- Goal: `{state["goal_status"]}`',
        f'- Paper gate: `{state["paper_gate"]}`',
    ]
    for key, status in state.items():
        match = re.fullmatch(r"candidate_([a-z]+)_status", key)
        if match is None:
            continue
        candidate = match.group(1).upper()
        active = " (active)" if state["active_candidate"] == candidate else ""
        lines.append(f"- Candidate {candidate}: `{status}`{active}")
    lines.extend([
        f'- Last decision: `{state["last_decision"]}`',
        f'- Disposition: {graph["candidate_a_disposition"]}',
        "",
        str(graph["next_step"]),
    ])
    return lines


def _graph_markdown(graph: Mapping[str, object]) -> str:
    lines = [
        "# 2025/686 MAT-SAB Selector And State Graph",
        "",
    ]
    lines.extend(_campaign_markdown(graph))
    lines.extend([
        "",
        "```mermaid",
        "flowchart TD",
    ])
    for node in graph["nodes"]:
        lines.append(f'  {node["id"]}["{node["id"]}: {node["role"]}"]')
    for edge in graph["edges"]:
        lines.append(f'  {edge["from"]} -->|"{edge["relation"]}"| {edge["to"]}')
    lines.extend(["```", "", "## Anchors", "", "| node | path | status |", "| --- | --- | --- |"])
    for node in graph["nodes"]:
        lines.append(f'| {node["id"]} | `{node["path"]}` | {node["anchor_status"]} |')
    lines.extend(_reproduction_markdown(graph))
    return "\n".join(lines) + "\n"


def _gaps_markdown(graph: Mapping[str, object]) -> str:
    lines = [
        "# MAT-SAB Campaign Gaps",
        "",
    ]
    lines.extend(_campaign_markdown(graph))
    lines.extend([
        "",
        (
            "Production code permission: "
            f'`{str(graph["production_code_permission"]).lower()}`.'
        ),
        "",
        (
            "The closed Candidate A result is a finite-field "
            "necessary-condition rejection; it does not infer cryptographic "
            "security or complete-SAB performance."
        ),
        "",
        "## Open Obligations",
        "",
    ])
    lines.extend(f"- {gap}" for gap in graph["open_gaps"])
    lines.extend(_reproduction_markdown(graph))
    return "\n".join(lines) + "\n"


def _selector_relative_paths() -> tuple[Path, Path, Path]:
    return (
        Path("paper_techgraphs") / JSON_OUT.name,
        Path("paper_techgraphs") / GRAPH_OUT.name,
        Path("paper_techgraphs") / GAPS_OUT.name,
    )


def _preflight_selector_destinations(destination: Path) -> None:
    for relative in _selector_relative_paths():
        candidate = destination / relative
        resolved = _resolve_under_root(
            destination,
            candidate,
            f"selector destination {relative.as_posix()}",
            strict=False,
        )
        if candidate.exists() and not resolved.is_file():
            raise GateEvidenceError(
                f"selector destination is not a file: {resolved}"
            )


def _render_selector_outputs(
    destination: Path,
    graph: Mapping[str, object],
) -> tuple[Path, Path, Path]:
    paths = tuple(
        destination / relative
        for relative in _selector_relative_paths()
    )
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    paths[0].write_text(
        json.dumps(graph, indent=2) + "\n",
        encoding="ascii",
        newline="\n",
    )
    paths[1].write_text(
        _graph_markdown(graph),
        encoding="ascii",
        newline="\n",
    )
    paths[2].write_text(
        _gaps_markdown(graph),
        encoding="ascii",
        newline="\n",
    )
    return paths


def _publish_selector_outputs(
    destination: Path,
    stage: Path,
) -> tuple[Path, Path, Path]:
    relative_paths = _selector_relative_paths()
    snapshots = {
        relative: (
            (destination / relative).read_bytes()
            if (destination / relative).is_file()
            else None
        )
        for relative in relative_paths
    }
    published: list[Path] = []
    try:
        for relative in relative_paths:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            _resolve_under_root(
                destination,
                target,
                f"selector destination {relative.as_posix()}",
                strict=False,
            )
            os.replace(stage / relative, target)
            published.append(relative)
    except Exception:
        for relative in reversed(published):
            _restore_file_atomic(
                destination / relative,
                snapshots[relative],
            )
        raise
    return tuple(destination / relative for relative in relative_paths)


def write_outputs(
    root: Path,
    graph: Mapping[str, object],
) -> tuple[Path, Path, Path]:
    destination = _resolved_directory(root, "selector destination root")
    _preflight_selector_destinations(destination)
    stage = Path(
        tempfile.mkdtemp(
            prefix=".selector-techgraph-stage-",
            dir=destination,
        )
    )
    _resolve_under_root(
        destination,
        stage,
        "selector staging directory",
        strict=True,
    )
    try:
        _preflight_selector_destinations(stage)
        _render_selector_outputs(stage, graph)
        return _publish_selector_outputs(destination, stage)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--destination-root", type=Path)
    parser.add_argument("--source-state-commit", required=True)
    args = parser.parse_args()
    source_root = _preflight_launcher_root(args.root)
    _preflight_local_import_closure(
        source_root,
        args.source_state_commit,
        SELECTOR_LOCAL_IMPORT_ROOTS,
        SELECTOR_EXECUTABLE_INPUTS,
    )
    _preflight_launcher_file_origin(
        source_root,
        "scripts/build_mat_sab_selector_techgraph.py",
    )
    _reject_preloaded_local_modules(SELECTOR_EXECUTABLE_INPUTS)
    _activate_verified_import_root(source_root)
    _activate_local_import_cache_isolation()
    _load_local_dependencies()
    _validate_loaded_local_module_origins(
        source_root,
        SELECTOR_EXECUTABLE_INPUTS,
    )
    graph = build_graph(
        source_root,
        source_state_commit=args.source_state_commit,
    )
    failed = [node["id"] for node in graph["nodes"] if node["anchor_status"] != "PASS"]
    if failed:
        print("FAIL_TECHGRAPH_ANCHORS:" + ",".join(failed))
        return 1
    write_outputs(args.destination_root or source_root, graph)
    print("PASS_CANDIDATE_A_TECHGRAPH_ANCHORED")
    return 0


if __name__ != "__main__":
    _load_local_dependencies()
else:
    raise SystemExit(main())
