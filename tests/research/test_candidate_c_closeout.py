import csv
import ast
from dataclasses import replace
import importlib
import inspect
import json
import marshal
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.mat_sab_research_state import validate_state
import scripts.run_candidate_c_rank_bounded_gate as gate


ROOT = Path(__file__).resolve().parents[2]
RUN_MARKER = "candidate-c-rank-bounded-gate-001"
HYPOTHESIS_START = "# candidate-c-rank-bounded-gate-hypothesis-start"
HYPOTHESIS_END = "# candidate-c-rank-bounded-gate-hypothesis-end"
MANIFEST_START = "<!-- candidate-c-rank-bounded-gate-manifest-start -->"
MANIFEST_END = "<!-- candidate-c-rank-bounded-gate-manifest-end -->"
CHECKLIST_START = "<!-- candidate-c-rank-bounded-gate-checklist-start -->"
CHECKLIST_END = "<!-- candidate-c-rank-bounded-gate-checklist-end -->"
PREDECESSOR = "REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C"
C1_ADMIT = "ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY"
C2_ADMIT = "ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY"
C1_PHASE_REJECTION = "REJECT_C1_PHASE_IDENTITY_TERMINAL"
WORKING_IMPLEMENTATION_PATHS = (
    "research/mat_sab/candidate_c_operator_tensor.py",
    "research/mat_sab/candidate_c_registered_replay.py",
    "scripts/apply_candidate_c_rank_bounded_gate.py",
    "scripts/mat_sab_research_state.py",
    "scripts/run_candidate_c_rank_bounded_gate.py",
)
CLOSEOUT_LOCAL_IMPORT_CLOSURE = (
    "research/__init__.py",
    "research/mat_sab/__init__.py",
    "research/mat_sab/candidate_c_operator_tensor.py",
    "research/mat_sab/candidate_c_registered_replay.py",
    "research/mat_sab/candidate_c_schedule.py",
    "research/mat_sab/finite_linear.py",
    "research/mat_sab/rank_bounded_state_model.py",
    "scripts/apply_candidate_c_rank_bounded_gate.py",
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


def load_closeout():
    return importlib.import_module(
        "scripts.apply_candidate_c_rank_bounded_gate"
    )


def fixture_raw_evidence(decision):
    mechanism = gate.MechanismEvaluation(
        mechanism_id="C1",
        registered=True,
        source_status="PASS",
        equation_status="PASS",
        symbolic_independence_status="PASS",
        phase_status="PASS",
        schedule_status="PASS",
        rank_status="PASS",
        max_rho=2,
        compression_status="PASS",
        compression_interval=4,
        b_min=4,
        closed_next_state_consumption=True,
        structural_cost_status="PASS",
        complete_cost_status="PASS",
        complete_cost=100.0,
        amdahl_status="PASS",
        amdahl_projection=1.01,
        amdahl_pessimistic_projection=0.0,
        fully_evaluated=True,
        failure_reason="",
        object_hashes=("1" * 64,),
    )
    if decision == gate.ADMIT:
        classification = "ADMIT"
        terminal_decision = "ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY"
        exhausted = False
        replay_status = "PASS"
        task3b_status = "PASS"
        task4_status = "PASS"
    elif decision == gate.REJECT:
        classification = "REJECT"
        terminal_decision = (
            "REJECT_C1_NEGATIVE_PESSIMISTIC_AMDAHL_PROJECTION_TERMINAL"
        )
        exhausted = False
        replay_status = "PASS"
        task3b_status = "PASS"
        task4_status = "PASS"
        mechanism = replace(
            mechanism,
            amdahl_pessimistic_projection=-0.01,
            failure_reason=terminal_decision,
        )
    elif decision == gate.INCONCLUSIVE:
        classification = "INCONCLUSIVE"
        terminal_decision = (
            "TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED"
        )
        exhausted = True
        replay_status = gate.SKIPPED
        task3b_status = "EVIDENCE_EXHAUSTED"
        task4_status = gate.SKIPPED
        mechanism = replace(
            mechanism,
            registered=False,
            symbolic_independence_status="EVIDENCE_EXHAUSTED",
            phase_status="EVIDENCE_EXHAUSTED",
            schedule_status="EVIDENCE_EXHAUSTED",
            rank_status="EVIDENCE_EXHAUSTED",
            compression_status="EVIDENCE_EXHAUSTED",
            compression_interval=0,
            closed_next_state_consumption=False,
            structural_cost_status="EVIDENCE_EXHAUSTED",
            complete_cost_status=gate.SKIPPED,
            complete_cost=None,
            amdahl_status=gate.SKIPPED,
            amdahl_projection=None,
            amdahl_pessimistic_projection=None,
            fully_evaluated=False,
            failure_reason=terminal_decision,
            object_hashes=(),
        )
    else:
        raise ValueError(decision)
    return gate.bind_fixture_decision_evidence(
        gate.RawDecisionEvidence(
            schema=gate.DECISION_EVIDENCE_SCHEMA,
            binding_kind=gate.FIXTURE_EVIDENCE,
            claimed_decision=decision,
            terminal_classification=classification,
            terminal_decision=terminal_decision,
            terminal_record_hash="",
            terminal_evidence_exhausted=exhausted,
            replay_status=replay_status,
            task3b_status=task3b_status,
            task4_status=task4_status,
            mechanisms=(mechanism,),
        )
    )


def relabel_fixture_rejection(raw, label):
    mechanism = replace(raw.mechanisms[0], failure_reason=label)
    return gate.bind_fixture_decision_evidence(
        replace(
            raw,
            terminal_decision=label,
            terminal_record_hash="",
            mechanisms=(mechanism,),
        )
    )


def registered_admit_evidence(mechanism_id, *, label_family=None):
    raw = fixture_raw_evidence(gate.ADMIT)
    terminal_decision = {
        "C1": C1_ADMIT,
        "C2": C2_ADMIT,
    }[mechanism_id if label_family is None else label_family]
    return gate.bind_fixture_decision_evidence(
        replace(
            raw,
            terminal_decision=terminal_decision,
            terminal_record_hash="",
            mechanisms=(
                replace(
                    raw.mechanisms[0],
                    mechanism_id=mechanism_id,
                ),
            ),
        )
    )


def multiple_registered_phase_rejection_evidence():
    admitted = fixture_raw_evidence(gate.ADMIT)
    c1_failure = replace(
        admitted.mechanisms[0],
        phase_status="FAIL",
        complete_cost_status=gate.SKIPPED,
        complete_cost=None,
        amdahl_status=gate.SKIPPED,
        amdahl_projection=None,
        amdahl_pessimistic_projection=None,
        failure_reason=C1_PHASE_REJECTION,
    )
    c2_pass = replace(
        c1_failure,
        mechanism_id="C2",
        phase_status="PASS",
        failure_reason="",
    )
    return gate.bind_fixture_decision_evidence(
        replace(
            admitted,
            claimed_decision=gate.REJECT,
            terminal_classification="REJECT",
            terminal_decision=C1_PHASE_REJECTION,
            terminal_record_hash="",
            replay_status=gate.SKIPPED,
            task3b_status=gate.NO_VERIFIED_TASK3B_RESULT,
            task4_status=gate.SKIPPED,
            mechanisms=(c2_pass, c1_failure),
        )
    )


class CandidateCCloseoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.closeout = load_closeout()
        cls.input_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        cls.previous_input_commit = subprocess.run(
            ["git", "rev-parse", "HEAD^"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    @staticmethod
    def _make_root(directory):
        root = Path(directory)
        (root / "hypotheses").mkdir(parents=True)
        (root / "repro").mkdir()
        state = json.loads(
            (ROOT / "research_state.yaml").read_text(encoding="ascii")
        )
        state["goal_status"] = "ACTIVE"
        state["paper_gate"] = "BLOCKED"
        state["production_hot_path_permission"] = False
        state["active_candidate"] = "C"
        state["candidates"]["A"]["status"] = "REJECTED"
        state["candidates"]["B"]["status"] = "REJECTED"
        state["candidates"]["C"]["status"] = "INTAKE"
        state["candidates"]["C"]["equation_revisions_used"] = 0
        state["last_decision"] = PREDECESSOR
        state_path = root / "research_state.yaml"
        state_path.write_text(
            json.dumps(state, indent=2) + "\n",
            encoding="ascii",
            newline="\n",
        )
        (root / "repro/run_log.csv").write_text(
            "run_id,date,commit_or_state,stage,backend,command,params,seed,"
            "status,summary,artifacts\n",
            encoding="ascii",
            newline="\n",
        )
        return root, state_path

    @staticmethod
    def _clone_working_closeout(directory):
        root = Path(directory) / "root"
        subprocess.run(
            ["git", "clone", "--shared", "-q", str(ROOT), str(root)],
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Candidate C Test"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "config",
                "user.email",
                "candidate-c-test@example.invalid",
            ],
            cwd=root,
            check=True,
        )
        for relative in CLOSEOUT_LOCAL_IMPORT_CLOSURE:
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
                "working closeout launcher",
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

    @staticmethod
    def _remove_bounded_block(path, start, end):
        text = path.read_text(encoding="ascii")
        pattern = re.compile(
            rf"(?m)^{re.escape(start)}\r?\n.*?^{re.escape(end)}(?:\r?\n)?",
            re.DOTALL,
        )
        path.write_text(
            pattern.sub("", text),
            encoding="ascii",
            newline="\n",
        )

    @classmethod
    def _make_committed_missing_evidence_root(cls, directory):
        root = Path(directory) / "root"
        subprocess.run(
            ["git", "clone", "--shared", "-q", str(ROOT), str(root)],
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Candidate C Test"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "config",
                "user.email",
                "candidate-c-test@example.invalid",
            ],
            cwd=root,
            check=True,
        )
        for relative in WORKING_IMPLEMENTATION_PATHS:
            shutil.copyfile(ROOT / relative, root / relative)

        state_path = root / "research_state.yaml"
        state = json.loads(state_path.read_text(encoding="ascii"))
        state["goal_status"] = "ACTIVE"
        state["paper_gate"] = "BLOCKED"
        state["production_hot_path_permission"] = False
        state["active_candidate"] = "C"
        state["candidates"]["A"]["status"] = "REJECTED"
        state["candidates"]["B"]["status"] = "REJECTED"
        state["candidates"]["C"]["status"] = "INTAKE"
        state["candidates"]["C"]["equation_revisions_used"] = 0
        state["last_decision"] = PREDECESSOR
        state_path.write_text(
            json.dumps(state, indent=2) + "\n",
            encoding="ascii",
            newline="\n",
        )

        cls._remove_bounded_block(
            root / "hypotheses/hypothesis_register.yaml",
            HYPOTHESIS_START,
            HYPOTHESIS_END,
        )
        cls._remove_bounded_block(
            root / "repro/artifact_manifest.md",
            MANIFEST_START,
            MANIFEST_END,
        )
        cls._remove_bounded_block(
            root / "repro/reproduction_checklist.md",
            CHECKLIST_START,
            CHECKLIST_END,
        )
        run_log = root / "repro/run_log.csv"
        with run_log.open(newline="", encoding="ascii") as handle:
            rows = list(csv.reader(handle, strict=True))
        with run_log.open("w", newline="", encoding="ascii") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerows(
                row for row in rows
                if not row or row[0] != RUN_MARKER
            )

        missing = (
            root
            / "repro/stage203_production_selector_equation_probe/"
            "equation_map.csv"
        )
        missing.unlink()
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "missing Task 3A evidence"],
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
        return root, state_path, missing, commit

    def _write_fixture_pack(self, root, raw):
        result = gate.gate_result_from_decision_evidence(
            raw,
            allow_fixture=True,
        )
        summary_record = gate.canonical_summary_record(
            result,
            root=root,
            input_commit=self.input_commit,
            allow_fixture=True,
        )
        summary = root / "summary.csv"
        with summary.open("w", newline="", encoding="ascii") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=gate.SUMMARY_FIELDS,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerow(summary_record)
        evidence = root / "decision_evidence.json"
        evidence.write_text(
            gate.decision_evidence_json(raw),
            encoding="ascii",
            newline="\n",
        )
        return summary, evidence

    @staticmethod
    def _tracked(root, state_path):
        paths = (
            state_path,
            root / "hypotheses/hypothesis_register.yaml",
            root / "repro/run_log.csv",
            root / "repro/artifact_manifest.md",
            root / "repro/reproduction_checklist.md",
        )
        return {
            path: path.read_bytes() if path.exists() else None
            for path in paths
        }

    @staticmethod
    def _assert_markers_once(root):
        markers = (
            (root / "hypotheses/hypothesis_register.yaml", HYPOTHESIS_START),
            (root / "hypotheses/hypothesis_register.yaml", HYPOTHESIS_END),
            (root / "repro/run_log.csv", RUN_MARKER),
            (root / "repro/artifact_manifest.md", MANIFEST_START),
            (root / "repro/artifact_manifest.md", MANIFEST_END),
            (root / "repro/reproduction_checklist.md", CHECKLIST_START),
            (root / "repro/reproduction_checklist.md", CHECKLIST_END),
        )
        for path, marker in markers:
            with unittest.TestCase().subTest(path=path.name, marker=marker):
                text = path.read_text(encoding="ascii")
                unittest.TestCase().assertEqual(text.count(marker), 1)

    def _apply_twice(self, root, state_path, raw):
        summary, evidence = self._write_fixture_pack(root, raw)
        first = self.closeout.apply_gate(
            root,
            state_path,
            summary,
            input_commit=self.input_commit,
            evidence_path=evidence,
            allow_fixture=True,
        )
        after_first = self._tracked(root, state_path)
        second = self.closeout.apply_gate(
            root,
            state_path,
            summary,
            input_commit=self.input_commit,
            evidence_path=evidence,
            allow_fixture=True,
        )
        self.assertEqual(first, raw.claimed_decision)
        self.assertEqual(second, raw.claimed_decision)
        self.assertEqual(after_first, self._tracked(root, state_path))
        self._assert_markers_once(root)
        return json.loads(state_path.read_text(encoding="ascii"))

    def test_admit_fixture_pack_advances_only_to_adversarial_checker_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            state = self._apply_twice(
                root,
                state_path,
                fixture_raw_evidence(gate.ADMIT),
            )
        self.assertEqual(state["active_candidate"], "C")
        self.assertEqual(
            state["candidates"]["C"]["status"],
            "ADVERSARIAL_CHECKER_PASS",
        )
        self.assertEqual(state["goal_status"], "ACTIVE")
        self.assertEqual(state["paper_gate"], "BLOCKED")
        self.assertFalse(state["production_hot_path_permission"])
        self.assertEqual(state["last_decision"], gate.ADMIT)
        self.assertEqual(
            state["candidates"]["C"]["equation_revisions_used"],
            1,
        )
        validate_state(state)

    def test_matching_c1_and_c2_admit_fixture_packs_advance(self):
        for mechanism_id in ("C1", "C2"):
            with self.subTest(mechanism_id=mechanism_id):
                with tempfile.TemporaryDirectory() as tmp:
                    root, state_path = self._make_root(tmp)
                    state = self._apply_twice(
                        root,
                        state_path,
                        registered_admit_evidence(mechanism_id),
                    )
                self.assertEqual(
                    state["candidates"]["C"]["status"],
                    "ADVERSARIAL_CHECKER_PASS",
                )
                self.assertEqual(
                    state["candidates"]["C"]["equation_revisions_used"],
                    1,
                )
                self.assertEqual(state["last_decision"], gate.ADMIT)
                validate_state(state)

    def test_reject_after_cost_fixture_pack_exhausts_campaign(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            state = self._apply_twice(
                root,
                state_path,
                fixture_raw_evidence(gate.REJECT),
            )
        self.assertEqual(state["active_candidate"], "C")
        self.assertEqual(state["candidates"]["A"]["status"], "REJECTED")
        self.assertEqual(state["candidates"]["B"]["status"], "REJECTED")
        self.assertEqual(state["candidates"]["C"]["status"], "REJECTED")
        self.assertEqual(state["goal_status"], "RESEARCH_CAMPAIGN_EXHAUSTED")
        self.assertEqual(state["paper_gate"], "BLOCKED")
        self.assertFalse(state["production_hot_path_permission"])
        self.assertEqual(state["last_decision"], gate.REJECT)
        self.assertEqual(
            state["candidates"]["C"]["equation_revisions_used"],
            1,
        )
        validate_state(state)

    def test_inconclusive_fixture_pack_closes_without_external_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            state = self._apply_twice(
                root,
                state_path,
                fixture_raw_evidence(gate.INCONCLUSIVE),
            )
        self.assertEqual(state["active_candidate"], "C")
        self.assertEqual(state["candidates"]["C"]["status"], "INCONCLUSIVE")
        self.assertEqual(
            state["goal_status"],
            "RESEARCH_CAMPAIGN_INCONCLUSIVE",
        )
        self.assertNotEqual(state["goal_status"], "EXTERNAL_BLOCKED")
        self.assertEqual(state["paper_gate"], "BLOCKED")
        self.assertFalse(state["production_hot_path_permission"])
        self.assertEqual(state["last_decision"], gate.INCONCLUSIVE)
        self.assertEqual(
            state["candidates"]["C"]["equation_revisions_used"],
            1,
        )
        validate_state(state)

    def test_actual_committed_missing_evidence_generator_and_closeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path, _missing, input_commit = (
                self._make_committed_missing_evidence_root(tmp)
            )
            generator = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_candidate_c_rank_bounded_gate.py",
                    "--root",
                    str(root),
                    "--input-commit",
                    input_commit,
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(generator.returncode, 0, generator.stderr)
            self.assertEqual(
                generator.stdout.strip(),
                gate.INCONCLUSIVE,
            )
            summary = (
                root / "repro/candidate_c_rank_bounded_gate/summary.csv"
            )
            with summary.open(newline="", encoding="ascii") as handle:
                summary_row = next(csv.DictReader(handle))
            self.assertEqual(summary_row["decision"], gate.INCONCLUSIVE)
            self.assertEqual(
                summary_row["terminal_classification"],
                "INCONCLUSIVE",
            )
            self.assertRegex(
                summary_row["terminal_record_hash"],
                r"^[0-9a-f]{64}$",
            )
            with (
                root
                / "repro/candidate_c_rank_bounded_gate/input_manifest.csv"
            ).open(newline="", encoding="ascii") as handle:
                input_rows = {
                    row["path"]: row for row in csv.DictReader(handle)
                }
            missing_row = input_rows[
                "repro/stage203_production_selector_equation_probe/"
                "equation_map.csv"
            ]
            self.assertEqual(
                missing_row["availability"],
                "MISSING_RECOGNIZED_EVIDENCE",
            )
            self.assertEqual(
                missing_row["sha256"],
                gate.MISSING_STAGE203_EVIDENCE_HASH,
            )
            with (
                root
                / "repro/candidate_c_rank_bounded_gate/"
                "closeout_executable_manifest.csv"
            ).open(newline="", encoding="ascii") as handle:
                executable_rows = tuple(csv.DictReader(handle))
            self.assertEqual(
                tuple(row["path"] for row in executable_rows),
                gate.CLOSEOUT_EXECUTABLE_INPUTS,
            )

            commands = (
                [
                    sys.executable,
                    "scripts/apply_candidate_c_rank_bounded_gate.py",
                    "--root",
                    str(root),
                    "--input-commit",
                    input_commit,
                ],
            ) * 2
            before_second = None
            for index, command in enumerate(commands):
                completed = subprocess.run(
                    command,
                    cwd=root,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(
                    completed.stdout.strip(),
                    gate.INCONCLUSIVE,
                )
                if index == 0:
                    before_second = self._tracked(root, state_path)
                else:
                    self.assertEqual(
                        before_second,
                        self._tracked(root, state_path),
                    )
            state = json.loads(state_path.read_text(encoding="ascii"))
            self.assertEqual(state["candidates"]["C"]["status"], "INCONCLUSIVE")
            self.assertEqual(
                state["candidates"]["C"]["equation_revisions_used"],
                1,
            )
            self.assertEqual(
                state["goal_status"],
                "RESEARCH_CAMPAIGN_INCONCLUSIVE",
            )
            validate_state(state)

    def test_stale_and_wrong_committed_closeout_executables_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in gate.CLOSEOUT_EXECUTABLE_INPUTS:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / relative).read_bytes())
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.name", "Candidate C Test"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "config",
                    "user.email",
                    "candidate-c-test@example.invalid",
                ],
                cwd=root,
                check=True,
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "closeout executables"],
                cwd=root,
                check=True,
            )
            first_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            _, first_rows = gate._validated_input_rows(
                root,
                first_commit,
                gate.CLOSEOUT_EXECUTABLE_INPUTS,
            )
            pack = root / "pack"
            pack.mkdir()
            with (pack / "input_manifest.csv").open(
                "w",
                newline="",
                encoding="ascii",
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=("path", "availability", "sha256"),
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerows(first_rows)
            with (pack / "closeout_executable_manifest.csv").open(
                "w",
                newline="",
                encoding="ascii",
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=("role", "path", "sha256"),
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerows(gate._closeout_executable_rows(first_rows))

            state_script = root / "scripts/mat_sab_research_state.py"
            original_state_script = state_script.read_bytes()
            state_script.write_bytes(original_state_script + b"\n")
            with self.assertRaisesRegex(
                gate.GateEvidenceError,
                "does not match implementation-input commit",
            ):
                gate._validated_input_rows(
                    root,
                    first_commit,
                    gate.CLOSEOUT_EXECUTABLE_INPUTS,
                )
            state_script.write_bytes(original_state_script)

            apply_script = (
                root / "scripts/apply_candidate_c_rank_bounded_gate.py"
            )
            apply_script.write_bytes(
                apply_script.read_bytes()
                + b"\n# committed executable mismatch probe\n"
            )
            subprocess.run(
                ["git", "add", str(apply_script.relative_to(root))],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-q", "-m", "changed executable"],
                cwd=root,
                check=True,
            )
            second_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            sentinel = root / "state-ledger-sentinel"
            sentinel.write_text("unchanged\n", encoding="ascii", newline="\n")
            before = sentinel.read_bytes()
            with (
                patch.object(
                    self.closeout,
                    "_input_paths",
                    return_value=gate.CLOSEOUT_EXECUTABLE_INPUTS,
                ),
                self.assertRaisesRegex(
                    ValueError,
                    "published input manifest",
                ),
            ):
                self.closeout._validate_published_manifests(
                    root,
                    pack,
                    second_commit,
                    object(),
                )
            self.assertEqual(sentinel.read_bytes(), before)

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
            self.closeout._literal_dynamic_imports(tree, "alias_probe.py"),
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
                    "import importlib as module_alias",
                    "loader = module_alias.import_module",
                    "target = 'research.alias_probe'",
                    "loader(target)",
                )
            )
        )
        with self.assertRaisesRegex(
            self.closeout.LocalImportPreflightError,
            "nonliteral dynamic import",
        ):
            self.closeout._literal_dynamic_imports(
                nonliteral,
                "alias_probe.py",
            )

    def test_real_cli_rejects_aliased_dynamic_imports_before_mutation(self):
        cases = (
            (
                "module_alias_literal",
                "\n".join(
                    (
                        "import importlib as closeout_importlib",
                        (
                            "closeout_importlib.import_module("
                            "'research.mat_sab.closeout_alias_probe')"
                        ),
                        "",
                    )
                ),
                "executable registry does not match recursive import closure",
            ),
            (
                "callable_alias_nonliteral",
                "\n".join(
                    (
                        (
                            "from importlib import import_module "
                            "as closeout_loader"
                        ),
                        (
                            "closeout_target = "
                            "'research.mat_sab.closeout_alias_probe'"
                        ),
                        "closeout_loader(closeout_target)",
                        "",
                    )
                ),
                "nonliteral dynamic import",
            ),
        )
        for name, source, expected_error in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root, _ = self._clone_working_closeout(tmp)
                dependency = root / "research/mat_sab/finite_linear.py"
                dependency.write_text(
                    dependency.read_text(encoding="ascii") + "\n" + source,
                    encoding="ascii",
                    newline="\n",
                )
                marker = root / "UNVERIFIED_CLOSEOUT_ALIAS_EXECUTED"
                probe = root / "research/mat_sab/closeout_alias_probe.py"
                probe.write_text(
                    "\n".join(
                        (
                            "from pathlib import Path",
                            (
                                "Path('UNVERIFIED_CLOSEOUT_ALIAS_EXECUTED')"
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
                state_path = root / "research_state.yaml"
                before = self._tracked(root, state_path)
                environment = os.environ.copy()
                environment["PYTHONDONTWRITEBYTECODE"] = "1"
                completed = subprocess.run(
                    [
                        sys.executable,
                        "scripts/apply_candidate_c_rank_bounded_gate.py",
                        "--input-commit",
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
                self.assertEqual(before, self._tracked(root, state_path))

    def test_real_cli_rejects_cross_checkout_root_before_mutation(self):
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
            state_path = other_root / "research_state.yaml"
            before = self._tracked(other_root, state_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(
                        ROOT
                        / "scripts/apply_candidate_c_rank_bounded_gate.py"
                    ),
                    "--root",
                    str(other_root),
                    "--input-commit",
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
            self.assertEqual(before, self._tracked(other_root, state_path))

    def test_real_cli_ignores_valid_adjacent_timestamp_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, commit = self._clone_working_closeout(tmp)
            no_write_environment = os.environ.copy()
            no_write_environment["PYTHONDONTWRITEBYTECODE"] = "1"
            generator = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_candidate_c_rank_bounded_gate.py",
                    "--input-commit",
                    commit,
                ],
                cwd=root,
                env=no_write_environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(generator.returncode, 0, generator.stderr)
            baseline = subprocess.run(
                [
                    sys.executable,
                    "scripts/apply_candidate_c_rank_bounded_gate.py",
                    "--input-commit",
                    commit,
                ],
                cwd=root,
                env=no_write_environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr)

            for cache_dir in sorted(
                root.rglob("__pycache__"),
                reverse=True,
            ):
                shutil.rmtree(cache_dir)
            marker = root / "STALE_CLOSEOUT_CACHE_EXECUTED"
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

            state_path = root / "research_state.yaml"
            before_outputs = self._tracked(root, state_path)
            before_caches = _adjacent_cache_snapshot(root)
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/apply_candidate_c_rank_bounded_gate.py",
                    "--input-commit",
                    commit,
                ],
                cwd=root,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout.strip(), gate.REJECT)
            self.assertFalse(marker.exists())
            self.assertEqual(
                before_outputs,
                self._tracked(root, state_path),
            )
            self.assertEqual(
                before_caches,
                _adjacent_cache_snapshot(root),
            )

    def test_closeout_registry_matches_recursive_local_import_closure(self):
        tree = ast.parse(
            (
                ROOT / "scripts/apply_candidate_c_rank_bounded_gate.py"
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
        derived = self.closeout._derive_local_import_closure(
            ROOT,
            self.input_commit,
            self.closeout.CLOSEOUT_LOCAL_IMPORT_ROOTS,
        )
        self.assertEqual(derived, CLOSEOUT_LOCAL_IMPORT_CLOSURE)
        self.assertEqual(derived, gate.CLOSEOUT_EXECUTABLE_INPUTS)

    def test_real_cli_preflights_initializers_and_transitive_imports(self):
        probes = (
            "research/__init__.py",
            "research/mat_sab/__init__.py",
            "research/mat_sab/finite_linear.py",
            "research/mat_sab/rank_bounded_state_model.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            subprocess.run(
                ["git", "clone", "--shared", "-q", str(ROOT), str(root)],
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Candidate C Test"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "config",
                    "user.email",
                    "candidate-c-test@example.invalid",
                ],
                cwd=root,
                check=True,
            )
            for relative in CLOSEOUT_LOCAL_IMPORT_CLOSURE:
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
                    "closeout preflight inputs",
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
            state_path = root / "research_state.yaml"
            before = self._tracked(root, state_path)
            marker = root / "UNVERIFIED_CLOSEOUT_IMPORT_EXECUTED"
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            for relative in probes:
                path = root / relative
                original = path.read_bytes()
                path.write_bytes(
                    original
                    + (
                        b"\nopen('UNVERIFIED_CLOSEOUT_IMPORT_EXECUTED', "
                        b"'w').write('executed')\n"
                    )
                )
                with self.subTest(relative=relative):
                    completed = subprocess.run(
                        [
                            sys.executable,
                            "scripts/apply_candidate_c_rank_bounded_gate.py",
                            "--root",
                            str(root),
                            "--input-commit",
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
                    self.assertEqual(before, self._tracked(root, state_path))
                path.write_bytes(original)
                marker.unlink(missing_ok=True)

    def test_actual_manifest_failure_precedes_state_and_ledger_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            fixture = fixture_raw_evidence(gate.REJECT)
            summary, evidence = self._write_fixture_pack(root, fixture)
            actual = replace(fixture, binding_kind=gate.ACTUAL_EVIDENCE)
            result = replace(
                gate.gate_result_from_decision_evidence(
                    fixture,
                    allow_fixture=True,
                ),
                decision_evidence=actual,
            )
            before = self._tracked(root, state_path)
            with (
                patch.object(
                    self.closeout,
                    "load_decision_evidence",
                    return_value=actual,
                ),
                patch.object(
                    self.closeout,
                    "evaluate_candidate_c",
                    return_value=result,
                ),
                patch.object(
                    self.closeout,
                    "_validate_published_manifests",
                    side_effect=ValueError("published executable mismatch"),
                ),
                patch.object(self.closeout, "load_state") as load_state_mock,
                self.assertRaisesRegex(
                    ValueError,
                    "published executable mismatch",
                ),
            ):
                self.closeout.apply_gate(
                    root,
                    state_path,
                    summary,
                    input_commit=self.input_commit,
                    evidence_path=evidence,
                )
            load_state_mock.assert_not_called()
            self.assertEqual(before, self._tracked(root, state_path))

    def test_unrelated_noncanonical_legacy_row_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            run_log = root / "repro/run_log.csv"
            legacy = "legacy-stage,row-without-canonical-width\n"
            with run_log.open("a", encoding="ascii", newline="") as handle:
                handle.write(legacy)
            self._apply_twice(
                root,
                state_path,
                fixture_raw_evidence(gate.REJECT),
            )
            self.assertIn(legacy, run_log.read_text(encoding="ascii"))

    def test_marker_outside_canonical_run_id_is_rejected(self):
        rows = (
            (
                "other,2026-07-17,state,stage,backend,command,params,seed,"
                f"{RUN_MARKER},summary,artifacts\n"
            ),
            f"legacy,{RUN_MARKER},extra\n",
        )
        for row in rows:
            with self.subTest(row=row):
                with tempfile.TemporaryDirectory() as tmp:
                    root, state_path = self._make_root(tmp)
                    run_log = root / "repro/run_log.csv"
                    with run_log.open(
                        "a",
                        encoding="ascii",
                        newline="",
                    ) as handle:
                        handle.write(row)
                    summary, evidence = self._write_fixture_pack(
                        root,
                        fixture_raw_evidence(gate.REJECT),
                    )
                    before = self._tracked(root, state_path)
                    with self.assertRaisesRegex(
                        ValueError,
                        "run log rows must match canonical schema",
                    ):
                        self.closeout.apply_gate(
                            root,
                            state_path,
                            summary,
                            input_commit=self.input_commit,
                            evidence_path=evidence,
                            allow_fixture=True,
                        )
                    self.assertEqual(before, self._tracked(root, state_path))

    def test_summary_tamper_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary, evidence = self._write_fixture_pack(
                root,
                fixture_raw_evidence(gate.REJECT),
            )
            text = summary.read_text(encoding="ascii")
            summary.write_text(
                text.replace(gate.REJECT, gate.ADMIT, 1),
                encoding="ascii",
                newline="\n",
            )
            before = self._tracked(root, state_path)
            with self.assertRaisesRegex(
                ValueError,
                "summary does not match recomputed gate evidence",
            ):
                self.closeout.apply_gate(
                    root,
                    state_path,
                    summary,
                    input_commit=self.input_commit,
                    evidence_path=evidence,
                    allow_fixture=True,
                )
            self.assertEqual(before, self._tracked(root, state_path))

    def test_apply_rejects_amdahl_failure_relabelled_as_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            raw = fixture_raw_evidence(gate.REJECT)
            summary, evidence = self._write_fixture_pack(root, raw)
            probe = relabel_fixture_rejection(raw, C1_PHASE_REJECTION)
            evidence.write_text(
                gate.decision_evidence_json(probe),
                encoding="ascii",
                newline="\n",
            )
            with summary.open(newline="", encoding="ascii") as handle:
                record = next(csv.DictReader(handle))
            record["terminal_decision"] = probe.terminal_decision
            record["terminal_record_hash"] = probe.terminal_record_hash
            with summary.open("w", newline="", encoding="ascii") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=gate.SUMMARY_FIELDS,
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerow(record)
            before = self._tracked(root, state_path)
            with self.assertRaisesRegex(
                gate.GateEvidenceError,
                "does not derive",
            ):
                self.closeout.apply_gate(
                    root,
                    state_path,
                    summary,
                    input_commit=self.input_commit,
                    evidence_path=evidence,
                    allow_fixture=True,
                )
            self.assertEqual(before, self._tracked(root, state_path))

    def test_apply_rejects_multiple_registered_mechanisms_before_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            probe = multiple_registered_phase_rejection_evidence()
            valid_raw = gate.bind_fixture_decision_evidence(
                replace(
                    probe,
                    terminal_record_hash="",
                    mechanisms=(probe.mechanisms[1],),
                )
            )
            valid_result = gate.gate_result_from_decision_evidence(
                valid_raw,
                allow_fixture=True,
            )
            forged_result = replace(
                valid_result,
                decision_evidence=probe,
                mechanisms=probe.mechanisms,
                terminal_record_hash=probe.terminal_record_hash,
            )
            summary = root / "summary.csv"
            with summary.open("w", newline="", encoding="ascii") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=gate.SUMMARY_FIELDS,
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerow(
                    gate._summary_from_verified_result(forged_result)
                )
            evidence = root / "decision_evidence.json"
            evidence.write_text(
                gate.decision_evidence_json(probe),
                encoding="ascii",
                newline="\n",
            )
            before = self._tracked(root, state_path)
            with (
                patch.object(
                    self.closeout,
                    "_transition_initial_state",
                    wraps=self.closeout._transition_initial_state,
                ) as transition,
                self.assertRaisesRegex(
                    gate.GateEvidenceError,
                    "unique registered mechanism",
                ),
            ):
                self.closeout.apply_gate(
                    root,
                    state_path,
                    summary,
                    input_commit=self.input_commit,
                    evidence_path=evidence,
                    allow_fixture=True,
                )
            transition.assert_not_called()
            self.assertEqual(before, self._tracked(root, state_path))

    def test_apply_rejects_admit_family_mismatches_before_transition(self):
        for mechanism_id, label_family in (
            ("C2", "C1"),
            ("C1", "C2"),
        ):
            with self.subTest(
                mechanism_id=mechanism_id,
                label_family=label_family,
            ):
                with tempfile.TemporaryDirectory() as tmp:
                    root, state_path = self._make_root(tmp)
                    valid = registered_admit_evidence(mechanism_id)
                    result = gate.gate_result_from_decision_evidence(
                        valid,
                        allow_fixture=True,
                    )
                    probe = registered_admit_evidence(
                        mechanism_id,
                        label_family=label_family,
                    )
                    record = gate._summary_from_verified_result(result)
                    record["terminal_decision"] = probe.terminal_decision
                    record["terminal_record_hash"] = (
                        probe.terminal_record_hash
                    )
                    summary = root / "summary.csv"
                    with summary.open(
                        "w",
                        newline="",
                        encoding="ascii",
                    ) as handle:
                        writer = csv.DictWriter(
                            handle,
                            fieldnames=gate.SUMMARY_FIELDS,
                            lineterminator="\n",
                        )
                        writer.writeheader()
                        writer.writerow(record)
                    evidence = root / "decision_evidence.json"
                    evidence.write_text(
                        gate.decision_evidence_json(probe),
                        encoding="ascii",
                        newline="\n",
                    )
                    before = self._tracked(root, state_path)
                    with (
                        patch.object(
                            self.closeout,
                            "_transition_initial_state",
                            wraps=self.closeout._transition_initial_state,
                        ) as transition,
                        self.assertRaisesRegex(
                            gate.GateEvidenceError,
                            "does not derive",
                        ),
                    ):
                        self.closeout.apply_gate(
                            root,
                            state_path,
                            summary,
                            input_commit=self.input_commit,
                            evidence_path=evidence,
                            allow_fixture=True,
                        )
                    transition.assert_not_called()
                    self.assertEqual(
                        before,
                        self._tracked(root, state_path),
                    )

    def test_closeout_provenance_commands_pin_exact_input_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            self._apply_twice(
                root,
                state_path,
                fixture_raw_evidence(gate.REJECT),
            )
            with (root / "repro/run_log.csv").open(
                newline="",
                encoding="ascii",
            ) as handle:
                row = next(
                    record
                    for record in csv.DictReader(handle)
                    if record["run_id"] == RUN_MARKER
                )
            checklist = (
                root / "repro/reproduction_checklist.md"
            ).read_text(encoding="ascii")

        commands = [row["command"], *re.findall(r"`(python [^`]+)`", checklist)]
        expected_scripts = {
            "scripts/run_candidate_c_rank_bounded_gate.py",
            "scripts/apply_candidate_c_rank_bounded_gate.py",
        }
        self.assertEqual(
            {shlex.split(command)[1] for command in commands},
            expected_scripts,
        )
        for command in commands:
            with self.subTest(command=command):
                tokens = shlex.split(command)
                self.assertEqual(
                    tokens[-2:],
                    ["--input-commit", self.input_commit],
                )
                self.assertEqual(command.count(self.input_commit), 1)

    def test_closeout_refreshes_exact_legacy_unpinned_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary, evidence = self._write_fixture_pack(
                root,
                fixture_raw_evidence(gate.REJECT),
            )
            legacy_checklist = f"""{CHECKLIST_START}
- [x] Candidate C records `{gate.REJECT}` from hash-bound source,
  equation, symbolic-independence, phase, schedule, rank, compression,
  complete-cost, and Amdahl fields. Reproduce with
  `python scripts/run_candidate_c_rank_bounded_gate.py` followed by
  `python scripts/apply_candidate_c_rank_bounded_gate.py`; production hot-path
  permission remains false.
{CHECKLIST_END}
"""
            (root / "repro/reproduction_checklist.md").write_text(
                legacy_checklist,
                encoding="ascii",
                newline="\n",
            )
            with (root / "repro/run_log.csv").open(
                "a",
                newline="",
                encoding="ascii",
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=(
                        "run_id",
                        "date",
                        "commit_or_state",
                        "stage",
                        "backend",
                        "command",
                        "params",
                        "seed",
                        "status",
                        "summary",
                        "artifacts",
                    ),
                    lineterminator="\n",
                )
                writer.writerow(
                    {
                        "run_id": RUN_MARKER,
                        "date": "2026-07-17",
                        "commit_or_state": (
                            "candidate-c-rank-bounded-mechanism-gate"
                        ),
                        "stage": "Candidate C mechanism gate",
                        "backend": "exact-finite-ring-symbolic",
                        "command": (
                            "python scripts/"
                            "run_candidate_c_rank_bounded_gate.py"
                        ),
                        "params": (
                            "C1/C2;r=2/4/6;rho<=2;"
                            "Task4=registered-only"
                        ),
                        "seed": "deterministic",
                        "status": gate.REJECT,
                        "summary": (
                            "Hash-bound source, equation, symbolic, phase, "
                            "schedule, rank, compression, complete-cost, and "
                            "Amdahl gates close Candidate C."
                        ),
                        "artifacts": (
                            "repro/candidate_c_rank_bounded_gate/"
                        ),
                    }
                )

            self.closeout.apply_gate(
                root,
                state_path,
                summary,
                input_commit=self.input_commit,
                evidence_path=evidence,
                allow_fixture=True,
            )
            run_log = (root / "repro/run_log.csv").read_text(
                encoding="ascii"
            )
            checklist = (
                root / "repro/reproduction_checklist.md"
            ).read_text(encoding="ascii")

        pinned = f"--input-commit {self.input_commit}"
        self.assertEqual(run_log.count(pinned), 1)
        self.assertEqual(checklist.count(pinned), 2)
        self.assertNotIn(
            "`python scripts/run_candidate_c_rank_bounded_gate.py`",
            checklist,
        )

    def test_closeout_refreshes_exact_prior_pinned_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary, evidence = self._write_fixture_pack(
                root,
                fixture_raw_evidence(gate.REJECT),
            )
            previous = self.previous_input_commit
            checklist = f"""{CHECKLIST_START}
- [x] Candidate C records `{gate.REJECT}` from hash-bound source,
  equation, symbolic-independence, phase, schedule, rank, compression,
  complete-cost, and Amdahl fields. Reproduce with
  `python scripts/run_candidate_c_rank_bounded_gate.py --input-commit {previous}` followed by
  `python scripts/apply_candidate_c_rank_bounded_gate.py --input-commit {previous}`; production hot-path
  permission remains false.
{CHECKLIST_END}
"""
            (root / "repro/reproduction_checklist.md").write_text(
                checklist,
                encoding="ascii",
                newline="\n",
            )
            with (root / "repro/run_log.csv").open(
                "a",
                newline="",
                encoding="ascii",
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=self.closeout._run_row(
                        gate.REJECT,
                        previous,
                    ),
                    lineterminator="\n",
                )
                writer.writerow(
                    self.closeout._run_row(gate.REJECT, previous)
                )

            try:
                self.closeout.apply_gate(
                    root,
                    state_path,
                    summary,
                    input_commit=self.input_commit,
                    evidence_path=evidence,
                    allow_fixture=True,
                )
            except ValueError as error:
                self.fail(f"exact prior pinned provenance was rejected: {error}")
            run_log = (root / "repro/run_log.csv").read_text(
                encoding="ascii"
            )
            updated_checklist = (
                root / "repro/reproduction_checklist.md"
            ).read_text(encoding="ascii")

        pinned = f"--input-commit {self.input_commit}"
        self.assertEqual(run_log.count(pinned), 1)
        self.assertEqual(updated_checklist.count(pinned), 2)
        self.assertNotIn(previous, run_log)
        self.assertNotIn(previous, updated_checklist)

    def test_write_failure_rolls_back_every_closeout_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            summary, evidence = self._write_fixture_pack(
                root,
                fixture_raw_evidence(gate.REJECT),
            )
            before = self._tracked(root, state_path)
            with patch.object(
                self.closeout,
                "_append_once",
                side_effect=OSError("injected write failure"),
            ):
                with self.assertRaisesRegex(OSError, "injected write failure"):
                    self.closeout.apply_gate(
                        root,
                        state_path,
                        summary,
                        input_commit=self.input_commit,
                        evidence_path=evidence,
                        allow_fixture=True,
                    )
            self.assertEqual(before, self._tracked(root, state_path))
            rolled_back = json.loads(state_path.read_text(encoding="ascii"))
            self.assertEqual(
                rolled_back["candidates"]["C"]["equation_revisions_used"],
                0,
            )

    def test_closeout_outputs_are_ascii(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, state_path = self._make_root(tmp)
            self._apply_twice(
                root,
                state_path,
                fixture_raw_evidence(gate.REJECT),
            )
            for path in self._tracked(root, state_path):
                with self.subTest(path=path.name):
                    path.read_bytes().decode("ascii")

    def test_closeout_requires_explicit_input_commit(self):
        parameter = inspect.signature(
            self.closeout.apply_gate
        ).parameters["input_commit"]
        self.assertEqual(parameter.default, inspect.Parameter.empty)


if __name__ == "__main__":
    unittest.main()
