"""Deterministic, commit-pinned replay boundary for Candidate D stages."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


REPLAY_MANIFEST = "candidate_d_stage_replay.json"
REPLAY_SCHEMA = "candidate-d-stage-replay-v1"


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


def _working_file(root: Path, relative: str) -> Path:
    declared = Path(relative)
    if declared.is_absolute() or ".." in declared.parts:
        raise StageReplayError(f"replay path escapes repository: {relative}")
    path = root / declared
    current = root
    for part in declared.parts:
        current = current / part
        if current.is_symlink():
            raise StageReplayError(f"replay path may not be a symlink: {relative}")
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise StageReplayUnavailable(f"replay input is missing: {relative}") from error
    if not resolved.is_file():
        raise StageReplayUnavailable(
            f"replay input is not a regular file: {relative}"
        )
    return resolved


def _verify_pinned_paths(
    root: Path, commit: str, paths: tuple[str, ...]
) -> tuple[tuple[str, str], ...]:
    hashes = []
    for relative in paths:
        blob = _git_blob(root, commit, relative)
        if _working_file(root, relative).read_bytes() != blob:
            raise StageReplayError(
                f"working replay input differs from input commit: {relative}"
            )
        hashes.append((relative, _sha256(blob)))
    return tuple(hashes)


def _tracked_status(root: Path) -> bytes:
    try:
        return subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=no"],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise StageReplayError("tracked repository status cannot be read") from error


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
    _verify_pinned_paths(root, input_commit, contract.pinned_paths)
    before = _tracked_status(root)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    with tempfile.TemporaryDirectory(prefix="candidate-d-stage-replay-") as directory:
        output_root = Path(directory)
        command = (
            sys.executable,
            contract.runner,
            "--root",
            str(root),
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
                cwd=root,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                timeout=600,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise StageReplayError(
                f"{contract.stage} canonical replay could not execute"
            ) from error
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise StageReplayError(
                f"{contract.stage} canonical replay failed: {detail[:300]}"
            )
        if _tracked_status(root) != before:
            raise StageReplayError(
                f"{contract.stage} canonical replay mutated tracked repository files"
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
            committed = _working_file(root, relative).read_bytes()
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
