import ast
import csv
from dataclasses import replace
import hashlib
import importlib
import inspect
import marshal
import os
import shutil
import subprocess
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
APPROVED_TERMINAL_HASH = (
    "8ad876708aa4a736c0f0f9adae33bab766272f411e90fbc23a5ac23e10a73cb6"
)
C1_ADMIT = "ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY"
C2_ADMIT = "ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY"
REGISTERED_ADMIT_LABELS = (C1_ADMIT, C2_ADMIT)
C1_PHASE_REJECTION = "REJECT_C1_PHASE_IDENTITY_TERMINAL"
C1_RELATION_REJECTION = (
    "REJECT_C1_REGISTERED_SHORT_ERROR_RELATION_TERMINAL"
)
C1_STRUCTURAL_REJECTION = (
    "REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL"
)
C1_AMDAHL_REJECTION = (
    "REJECT_C1_NEGATIVE_PESSIMISTIC_AMDAHL_PROJECTION_TERMINAL"
)
C2_CLOSURE_REJECTION = "REJECT_C2_CONVERSION_CLOSURE"
C2_STRUCTURAL_REJECTION = "REJECT_C2_NONPOSITIVE_STRUCTURAL_COST"
REGISTERED_REJECTION_LABELS = (
    C1_PHASE_REJECTION,
    C1_RELATION_REJECTION,
    C1_STRUCTURAL_REJECTION,
    C1_AMDAHL_REJECTION,
    C2_CLOSURE_REJECTION,
    C2_STRUCTURAL_REJECTION,
)
EXPECTED_ARTIFACTS = {
    "summary.csv",
    "source_mapping.csv",
    "schedule_trace.csv",
    "operator_tensor.csv",
    "evaluator_sample_relations.csv",
    "conversion_material.csv",
    "registered_object_hash.csv",
    "terminal_record.csv",
    "rank_growth.csv",
    "compression_gate.csv",
    "complete_cost.csv",
    "amdahl_projection.csv",
    "mechanism_matrix.csv",
    "proof_gate.csv",
    "decision_evidence.json",
    "input_manifest.csv",
    "closeout_executable_manifest.csv",
    "environment.csv",
    "artifact_index.csv",
    "reproduction_commands.md",
}
EXPECTED_COMPUTATIONAL_INPUTS = (
    "main.c",
    "paper_techgraphs/candidate_c_rank_bounded_state.yaml",
    "repro/stage203_production_selector_equation_probe/equation_map.csv",
    "repro/stage222_isolated_compact_ep_integration/proof_gate.csv",
    "repro/stage345_binary_matrix_synthesis/proof_gate.csv",
    "research/__init__.py",
    "research/mat_sab/__init__.py",
    "research/mat_sab/candidate_c_operator_tensor.py",
    "research/mat_sab/candidate_c_registered_replay.py",
    "research/mat_sab/candidate_c_schedule.py",
    "research/mat_sab/finite_linear.py",
    "research/mat_sab/rank_bounded_state_model.py",
    "research/mat_sab/star_cycle_model.py",
    "scripts/__init__.py",
    "scripts/apply_candidate_c_rank_bounded_gate.py",
    "scripts/mat_sab_research_state.py",
    "scripts/run_candidate_c_rank_bounded_gate.py",
    "src/mosfhet/Makefile.def",
    "src/mosfhet/src/mattrgsw.c",
    "src/sab_pvw.c",
    "src/sparse_amortized_bootstrap.c",
    "theory_checks/candidate_c_rank_bounded_state_model.md",
)
GENERATOR_LOCAL_IMPORT_CLOSURE = (
    "research/__init__.py",
    "research/mat_sab/__init__.py",
    "research/mat_sab/candidate_c_operator_tensor.py",
    "research/mat_sab/candidate_c_registered_replay.py",
    "research/mat_sab/candidate_c_schedule.py",
    "research/mat_sab/finite_linear.py",
    "research/mat_sab/rank_bounded_state_model.py",
    "scripts/__init__.py",
    "scripts/run_candidate_c_rank_bounded_gate.py",
)
WORKING_CLI_PATHS = (
    "scripts/__init__.py",
    "scripts/apply_candidate_c_rank_bounded_gate.py",
    "scripts/build_mat_sab_selector_techgraph.py",
    "scripts/run_candidate_c_rank_bounded_gate.py",
)


def load_gate():
    return importlib.import_module("scripts.run_candidate_c_rank_bounded_gate")


def git_head(root=ROOT):
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def published_input_commit():
    path = ROOT / "repro/candidate_c_rank_bounded_gate/environment.csv"
    with path.open(newline="", encoding="ascii") as handle:
        environment = {
            row["key"]: row["value"] for row in csv.DictReader(handle)
        }
    return environment["input_head"]


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


def fixture_mechanism(gate):
    return gate.MechanismEvaluation(
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


def fixture_raw_evidence(gate, decision):
    mechanism = fixture_mechanism(gate)
    if decision == gate.ADMIT:
        classification = "ADMIT"
        terminal_decision = "ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY"
        exhausted = False
        replay_status = "PASS"
        task4_status = "PASS"
    elif decision == gate.REJECT:
        classification = "REJECT"
        terminal_decision = (
            "REJECT_C1_NEGATIVE_PESSIMISTIC_AMDAHL_PROJECTION_TERMINAL"
        )
        exhausted = False
        replay_status = "PASS"
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
    raw = gate.RawDecisionEvidence(
        schema=gate.DECISION_EVIDENCE_SCHEMA,
        binding_kind=gate.FIXTURE_EVIDENCE,
        claimed_decision=decision,
        terminal_classification=classification,
        terminal_decision=terminal_decision,
        terminal_record_hash="",
        terminal_evidence_exhausted=exhausted,
        replay_status=replay_status,
        task3b_status=(
            "PASS" if decision != gate.INCONCLUSIVE
            else "EVIDENCE_EXHAUSTED"
        ),
        task4_status=task4_status,
        mechanisms=(mechanism,),
    )
    return gate.bind_fixture_decision_evidence(raw)


def registered_admit_evidence(gate, mechanism_id, *, label_family=None):
    raw = fixture_raw_evidence(gate, gate.ADMIT)
    terminal_decision = {
        "C1": C1_ADMIT,
        "C2": C2_ADMIT,
    }[mechanism_id if label_family is None else label_family]
    mechanism = replace(
        raw.mechanisms[0],
        mechanism_id=mechanism_id,
    )
    return gate.bind_fixture_decision_evidence(
        replace(
            raw,
            terminal_decision=terminal_decision,
            terminal_record_hash="",
            mechanisms=(mechanism,),
        )
    )


def registered_rejection_evidence(gate, label):
    mechanism = fixture_mechanism(gate)
    replay_status = gate.SKIPPED
    task3b_status = gate.NO_VERIFIED_TASK3B_RESULT
    task4_status = gate.SKIPPED
    mechanism = replace(
        mechanism,
        complete_cost_status=gate.SKIPPED,
        complete_cost=None,
        amdahl_status=gate.SKIPPED,
        amdahl_projection=None,
        amdahl_pessimistic_projection=None,
        failure_reason=label,
    )
    if label == C1_PHASE_REJECTION:
        mechanism = replace(mechanism, phase_status="FAIL")
    elif label == C1_RELATION_REJECTION:
        mechanism = replace(
            mechanism,
            symbolic_independence_status="REGISTERED_SHORT_ERROR_RELATION_FAIL",
        )
    elif label == C1_STRUCTURAL_REJECTION:
        mechanism = replace(
            mechanism,
            compression_status=label,
            compression_interval=0,
            closed_next_state_consumption=False,
            structural_cost_status=label,
        )
    elif label == C1_AMDAHL_REJECTION:
        replay_status = "PASS"
        task3b_status = "PASS"
        task4_status = "PASS"
        mechanism = replace(
            fixture_mechanism(gate),
            amdahl_pessimistic_projection=-0.01,
            failure_reason=label,
        )
    elif label == C2_CLOSURE_REJECTION:
        task3b_status = "PASS"
        mechanism = replace(
            mechanism,
            mechanism_id="C2",
            compression_status=label,
            closed_next_state_consumption=False,
        )
    elif label == C2_STRUCTURAL_REJECTION:
        task3b_status = "PASS"
        mechanism = replace(
            mechanism,
            mechanism_id="C2",
            compression_status=label,
            compression_interval=0,
            structural_cost_status=label,
        )
    else:
        raise ValueError(label)
    return gate.bind_fixture_decision_evidence(
        gate.RawDecisionEvidence(
            schema=gate.DECISION_EVIDENCE_SCHEMA,
            binding_kind=gate.FIXTURE_EVIDENCE,
            claimed_decision=gate.REJECT,
            terminal_classification="REJECT",
            terminal_decision=label,
            terminal_record_hash="",
            terminal_evidence_exhausted=False,
            replay_status=replay_status,
            task3b_status=task3b_status,
            task4_status=task4_status,
            mechanisms=(mechanism,),
        )
    )


def multiple_registered_phase_rejection_evidence(gate):
    raw = registered_rejection_evidence(gate, C1_PHASE_REJECTION)
    c1_failure = raw.mechanisms[0]
    c2_pass = replace(
        c1_failure,
        mechanism_id="C2",
        phase_status="PASS",
        failure_reason="",
    )
    return gate.bind_fixture_decision_evidence(
        replace(
            raw,
            terminal_record_hash="",
            mechanisms=(c2_pass, c1_failure),
        )
    )


def relabel_fixture_rejection(gate, raw, label, *, mechanism_id=None):
    mechanism = replace(
        raw.mechanisms[0],
        mechanism_id=(
            raw.mechanisms[0].mechanism_id
            if mechanism_id is None
            else mechanism_id
        ),
        failure_reason=label,
    )
    return gate.bind_fixture_decision_evidence(
        replace(
            raw,
            terminal_decision=label,
            terminal_record_hash="",
            mechanisms=(mechanism,),
        )
    )


class CandidateCDecisionVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        cls.input_commit = git_head()
        cls.terminal = cls.gate.terminal_record_for_task5(ROOT)

    def test_actual_raw_evidence_requires_the_approved_task3c_terminal(self):
        terminal = self.terminal
        cases = {
            "nonapproved_hash": replace(
                terminal,
                record_hash="f" * 64,
            ),
            "inconclusive": replace(
                terminal,
                classification="INCONCLUSIVE",
                decision="TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED",
                record_hash="e" * 64,
            ),
            "alternate_terminal": replace(
                terminal,
                decision=C1_PHASE_REJECTION,
                record_hash="d" * 64,
            ),
        }
        for name, changed in cases.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    self.gate.GateEvidenceError,
                    "approved actual Task 3C",
                ):
                    self.gate._raw_decision_evidence_from_terminal(changed)

    def test_actual_raw_evidence_requires_approved_mechanism_facts(self):
        terminal = self.terminal
        first = replace(
            terminal.operator_results[0],
            phase_identity_passed=False,
        )
        changed = replace(
            terminal,
            operator_results=(first, *terminal.operator_results[1:]),
        )
        with self.assertRaisesRegex(
            self.gate.GateEvidenceError,
            "approved actual mechanism facts",
        ):
            self.gate._raw_decision_evidence_from_terminal(changed)

    def test_registered_rejection_registry_accepts_exact_semantics(self):
        self.assertEqual(
            set(REGISTERED_REJECTION_LABELS),
            set(self.gate.REGISTERED_REJECTION_LABELS),
        )
        for label in REGISTERED_REJECTION_LABELS:
            with self.subTest(label=label):
                raw = registered_rejection_evidence(self.gate, label)
                verified = self.gate.verify_decision_evidence(
                    raw,
                    allow_fixture=True,
                )
                self.assertEqual(verified.decision, self.gate.REJECT)

    def test_registered_admit_registry_accepts_exact_c1_and_c2_families(self):
        self.assertEqual(
            set(REGISTERED_ADMIT_LABELS),
            set(getattr(self.gate, "REGISTERED_ADMIT_LABELS", ())),
        )
        for mechanism_id in ("C1", "C2"):
            with self.subTest(mechanism_id=mechanism_id):
                raw = registered_admit_evidence(
                    self.gate,
                    mechanism_id,
                )
                verified = self.gate.verify_decision_evidence(
                    raw,
                    allow_fixture=True,
                )
                result = self.gate.gate_result_from_decision_evidence(
                    raw,
                    allow_fixture=True,
                )
                self.assertEqual(verified.decision, self.gate.ADMIT)
                self.assertEqual(
                    self.gate._primary_mechanism(result).mechanism_id,
                    mechanism_id,
                )

    def test_admit_family_mismatches_are_rejected_by_verifier_and_result(self):
        for mechanism_id, label_family in (
            ("C2", "C1"),
            ("C1", "C2"),
        ):
            raw = registered_admit_evidence(
                self.gate,
                mechanism_id,
                label_family=label_family,
            )
            with self.subTest(
                mechanism_id=mechanism_id,
                label_family=label_family,
                boundary="verifier",
            ):
                with self.assertRaisesRegex(
                    self.gate.GateEvidenceError,
                    "does not derive",
                ):
                    self.gate.verify_decision_evidence(
                        raw,
                        allow_fixture=True,
                    )
            with self.subTest(
                mechanism_id=mechanism_id,
                label_family=label_family,
                boundary="gate_result",
            ):
                with self.assertRaisesRegex(
                    self.gate.GateEvidenceError,
                    "does not derive",
                ):
                    self.gate.gate_result_from_decision_evidence(
                        raw,
                        allow_fixture=True,
                    )

    def test_canonical_summary_rejects_admit_family_mismatches(self):
        for mechanism_id, label_family in (
            ("C2", "C1"),
            ("C1", "C2"),
        ):
            valid = registered_admit_evidence(
                self.gate,
                mechanism_id,
            )
            result = self.gate.gate_result_from_decision_evidence(
                valid,
                allow_fixture=True,
            )
            probe = registered_admit_evidence(
                self.gate,
                mechanism_id,
                label_family=label_family,
            )
            forged = replace(
                result,
                decision_evidence=probe,
                terminal_decision=probe.terminal_decision,
                terminal_record_hash=probe.terminal_record_hash,
                mechanisms=probe.mechanisms,
            )
            with self.subTest(
                mechanism_id=mechanism_id,
                label_family=label_family,
            ):
                with self.assertRaisesRegex(
                    self.gate.GateEvidenceError,
                    "does not derive",
                ):
                    self.gate.canonical_summary_record(
                        forged,
                        root=ROOT,
                        input_commit=self.input_commit,
                        allow_fixture=True,
                    )

    def test_decision_evidence_rejects_multiple_registered_mechanisms(self):
        raw = multiple_registered_phase_rejection_evidence(self.gate)
        with self.assertRaisesRegex(
            self.gate.GateEvidenceError,
            "unique registered mechanism",
        ):
            self.gate.verify_decision_evidence(
                raw,
                allow_fixture=True,
            )
        with self.assertRaisesRegex(
            self.gate.GateEvidenceError,
            "unique registered mechanism",
        ):
            self.gate.gate_result_from_decision_evidence(
                raw,
                allow_fixture=True,
            )

    def test_rejection_result_selects_exact_verified_mechanism(self):
        raw = registered_rejection_evidence(
            self.gate,
            C2_CLOSURE_REJECTION,
        )
        unregistered = replace(
            fixture_mechanism(self.gate),
            registered=False,
            fully_evaluated=False,
        )
        raw = self.gate.bind_fixture_decision_evidence(
            replace(
                raw,
                terminal_record_hash="",
                mechanisms=(unregistered, raw.mechanisms[0]),
            )
        )
        result = self.gate.gate_result_from_decision_evidence(
            raw,
            allow_fixture=True,
        )
        selected = self.gate._primary_mechanism(result)
        self.assertEqual(selected, raw.mechanisms[1])
        self.assertEqual(selected.mechanism_id, "C2")
        self.assertEqual(
            selected.compression_status,
            C2_CLOSURE_REJECTION,
        )

    def test_each_rejection_label_requires_its_exact_failure_fields(self):
        repairs = {
            C1_PHASE_REJECTION: {"phase_status": "PASS"},
            C1_RELATION_REJECTION: {
                "symbolic_independence_status": "PASS",
            },
            C1_STRUCTURAL_REJECTION: {
                "structural_cost_status": "PASS",
            },
            C1_AMDAHL_REJECTION: {
                "amdahl_pessimistic_projection": 0.0,
            },
            C2_CLOSURE_REJECTION: {
                "closed_next_state_consumption": True,
            },
            C2_STRUCTURAL_REJECTION: {
                "structural_cost_status": "PASS",
            },
        }
        incompatible = {
            C1_PHASE_REJECTION: {"schedule_status": "FAIL"},
            C1_RELATION_REJECTION: {"phase_status": "FAIL"},
            C1_STRUCTURAL_REJECTION: {"phase_status": "FAIL"},
            C1_AMDAHL_REJECTION: {"complete_cost_status": "FAIL"},
            C2_CLOSURE_REJECTION: {"structural_cost_status": "FAIL"},
            C2_STRUCTURAL_REJECTION: {
                "closed_next_state_consumption": False,
            },
        }
        self.assertEqual(set(repairs), set(REGISTERED_REJECTION_LABELS))
        self.assertEqual(set(incompatible), set(REGISTERED_REJECTION_LABELS))
        for label in REGISTERED_REJECTION_LABELS:
            raw = registered_rejection_evidence(self.gate, label)
            for case, mutation in (
                ("repaired_failure", repairs[label]),
                ("incompatible_failure", incompatible[label]),
            ):
                with self.subTest(label=label, case=case):
                    mechanism = replace(raw.mechanisms[0], **mutation)
                    changed = self.gate.bind_fixture_decision_evidence(
                        replace(
                            raw,
                            terminal_record_hash="",
                            mechanisms=(mechanism,),
                        )
                    )
                    with self.assertRaisesRegex(
                        self.gate.GateEvidenceError,
                        "does not derive",
                    ):
                        self.gate.verify_decision_evidence(
                            changed,
                            allow_fixture=True,
                        )

    def test_rejection_registry_rejects_unknown_family_and_field_mismatches(self):
        amdahl = registered_rejection_evidence(
            self.gate,
            C1_AMDAHL_REJECTION,
        )
        cases = {
            "unknown_label": relabel_fixture_rejection(
                self.gate,
                amdahl,
                "REJECT_C1_COMPLETE_COST_TERMINAL",
            ),
            "c1_label_on_c2": relabel_fixture_rejection(
                self.gate,
                amdahl,
                C1_AMDAHL_REJECTION,
                mechanism_id="C2",
            ),
            "c2_label_on_c1": relabel_fixture_rejection(
                self.gate,
                amdahl,
                C2_CLOSURE_REJECTION,
            ),
            "reviewer_phase_probe": relabel_fixture_rejection(
                self.gate,
                amdahl,
                C1_PHASE_REJECTION,
            ),
            "structural_label_with_structural_pass": (
                relabel_fixture_rejection(
                    self.gate,
                    amdahl,
                    C1_STRUCTURAL_REJECTION,
                )
            ),
            "closure_label_with_closed_state": relabel_fixture_rejection(
                self.gate,
                amdahl,
                C2_CLOSURE_REJECTION,
                mechanism_id="C2",
            ),
        }
        for name, changed in cases.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    self.gate.GateEvidenceError,
                    "does not derive",
                ):
                    self.gate.verify_decision_evidence(
                        changed,
                        allow_fixture=True,
                    )

    def test_canonical_summary_rejects_amdahl_failure_relabelled_as_phase(self):
        amdahl = registered_rejection_evidence(
            self.gate,
            C1_AMDAHL_REJECTION,
        )
        valid = self.gate.gate_result_from_decision_evidence(
            amdahl,
            allow_fixture=True,
        )
        probe = relabel_fixture_rejection(
            self.gate,
            amdahl,
            C1_PHASE_REJECTION,
        )
        forged = replace(
            valid,
            decision_evidence=probe,
            terminal_decision=probe.terminal_decision,
            terminal_record_hash=probe.terminal_record_hash,
            mechanisms=probe.mechanisms,
        )
        with self.assertRaisesRegex(
            self.gate.GateEvidenceError,
            "does not derive",
        ):
            self.gate.canonical_summary_record(
                forged,
                root=ROOT,
                input_commit=self.input_commit,
                allow_fixture=True,
            )


class CandidateCGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        cls.input_commit = git_head()
        cls.result = cls.gate.evaluate_candidate_c(
            ROOT,
            input_commit=cls.input_commit,
        )

    @staticmethod
    def _clone_working_generator(directory):
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
        for relative in WORKING_CLI_PATHS:
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
                "working generator launcher",
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
    def _run_generator(root, commit, destination, *, environment=None):
        return subprocess.run(
            [
                sys.executable,
                "scripts/run_candidate_c_rank_bounded_gate.py",
                "--destination-root",
                str(destination),
                "--input-commit",
                commit,
            ],
            cwd=root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def _summary(self, result=None):
        selected = self.result if result is None else result
        with patch.object(
            self.gate,
            "evaluate_candidate_c",
            return_value=self.result,
        ):
            return self.gate.canonical_summary_record(
                selected,
                root=ROOT,
                input_commit=self.input_commit,
            )

    def _write(self, destination, *, result=None, input_commit=None):
        selected = self.result if result is None else result
        commit = self.input_commit if input_commit is None else input_commit
        with patch.object(
            self.gate,
            "evaluate_candidate_c",
            return_value=self.result,
        ):
            return self.gate.write_gate_artifacts(
                ROOT,
                selected,
                input_commit=commit,
                destination_root=destination,
            )

    def test_actual_terminal_route_is_scoped_reject(self):
        result = self.result
        self.assertEqual(result.decision, self.gate.REJECT)
        self.assertEqual(result.terminal_classification, "REJECT")
        self.assertEqual(
            result.terminal_decision,
            "REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL",
        )
        self.assertEqual(result.terminal_record_hash, APPROVED_TERMINAL_HASH)
        self.assertEqual(result.task4_status, self.gate.SKIPPED)
        self.assertEqual(result.complete_cost_status, self.gate.SKIPPED)
        self.assertEqual(result.amdahl_status, self.gate.SKIPPED)
        self.assertIsNone(result.complete_cost)
        self.assertIsNone(result.amdahl_projection)
        self.assertIsNone(result.amdahl_pessimistic_projection)
        self.assertFalse(result.production_hot_path_permission)
        self.assertEqual(
            tuple(operator.r for operator in result.terminal_record.operator_results),
            (2, 4, 6),
        )
        self.assertTrue(
            all(
                operator.decision
                == "REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL"
                and not operator.structural_improvement
                for operator in result.terminal_record.operator_results
            )
        )

    def test_canonical_summary_has_every_required_gate(self):
        summary = self._summary()
        self.assertEqual(tuple(summary), self.gate.SUMMARY_FIELDS)
        self.assertEqual(summary["phase_status"], "PASS")
        self.assertEqual(summary["rank_status"], "PASS")
        self.assertEqual(
            summary["compression_status"],
            "REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL",
        )
        self.assertEqual(summary["closed_next_state_consumption"], "no")
        self.assertEqual(summary["complete_cost_status"], self.gate.SKIPPED)
        self.assertEqual(summary["amdahl_status"], self.gate.SKIPPED)
        self.assertEqual(summary["complete_cost"], "")
        self.assertEqual(summary["amdahl_projection"], "")
        self.assertEqual(summary["amdahl_pessimistic_projection"], "")

    def test_every_mechanism_field_is_bound_to_fresh_terminal_evidence(self):
        mechanism = self.result.mechanisms[0]
        mutations = {
            "mechanism_id": "C9",
            "registered": False,
            "source_status": "FAIL",
            "equation_status": "FAIL",
            "symbolic_independence_status": "PASS",
            "phase_status": "FAIL",
            "schedule_status": "FAIL",
            "rank_status": "FAIL",
            "max_rho": mechanism.max_rho + 1,
            "compression_status": "PASS",
            "compression_interval": 1,
            "b_min": 2,
            "closed_next_state_consumption": True,
            "structural_cost_status": "PASS",
            "complete_cost_status": "PASS",
            "complete_cost": 1.0,
            "amdahl_status": "PASS",
            "amdahl_projection": 1.01,
            "amdahl_pessimistic_projection": 0.0,
            "fully_evaluated": False,
            "failure_reason": "FORGED",
            "object_hashes": ("0" * 64,),
        }
        self.assertEqual(
            set(mutations),
            set(mechanism.__dataclass_fields__),
        )
        for field, value in mutations.items():
            with self.subTest(field=field):
                changed = replace(mechanism, **{field: value})
                forged = replace(
                    self.result,
                    mechanisms=(changed, *self.result.mechanisms[1:]),
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "freshly verified",
                ):
                    self._summary(forged)

    def test_verified_decision_evidence_derives_all_three_routes(self):
        for decision in (
            self.gate.ADMIT,
            self.gate.REJECT,
            self.gate.INCONCLUSIVE,
        ):
            with self.subTest(decision=decision):
                raw = fixture_raw_evidence(self.gate, decision)
                verified = self.gate.verify_decision_evidence(
                    raw,
                    allow_fixture=True,
                )
                result = self.gate.gate_result_from_decision_evidence(
                    raw,
                    allow_fixture=True,
                )
                self.assertEqual(verified.decision, decision)
                self.assertEqual(result.decision, decision)
                self.assertEqual(
                    self.gate.canonical_summary_record(
                        result,
                        root=ROOT,
                        input_commit=self.input_commit,
                        allow_fixture=True,
                    )["decision"],
                    decision,
                )

    def test_fixture_evidence_is_disabled_without_explicit_test_mode(self):
        raw = fixture_raw_evidence(self.gate, self.gate.ADMIT)
        with self.assertRaisesRegex(
            self.gate.GateEvidenceError,
            "fixture decision evidence is disabled",
        ):
            self.gate.verify_decision_evidence(raw)

    def test_admit_requires_every_typed_mechanism_gate(self):
        raw = fixture_raw_evidence(self.gate, self.gate.ADMIT)
        mechanism = raw.mechanisms[0]
        mutations = {
            "mechanism_id": "C3",
            "registered": False,
            "phase_status": "FAIL",
            "max_rho": 3,
            "closed_next_state_consumption": False,
            "compression_status": "FAIL",
            "compression_interval": mechanism.b_min - 1,
            "complete_cost_status": "MISSING",
            "complete_cost": None,
            "amdahl_status": "FAIL",
            "amdahl_projection": 1.0,
            "amdahl_pessimistic_projection": -0.01,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                changed = replace(mechanism, **{field: value})
                changed_raw = self.gate.bind_fixture_decision_evidence(
                    replace(raw, mechanisms=(changed,))
                )
                with self.assertRaisesRegex(
                    self.gate.GateEvidenceError,
                    "does not derive",
                ):
                    self.gate.verify_decision_evidence(
                        changed_raw,
                        allow_fixture=True,
                    )

    def test_reject_after_cost_requires_registered_fully_evaluated_failure(self):
        raw = fixture_raw_evidence(self.gate, self.gate.REJECT)
        verified = self.gate.verify_decision_evidence(
            raw,
            allow_fixture=True,
        )
        self.assertEqual(verified.decision, self.gate.REJECT)
        for changed in (
            replace(raw.mechanisms[0], registered=False),
            replace(raw.mechanisms[0], fully_evaluated=False),
            replace(raw.mechanisms[0], failure_reason=""),
        ):
            with self.subTest(changed=changed):
                changed_raw = self.gate.bind_fixture_decision_evidence(
                    replace(raw, mechanisms=(changed,))
                )
                with self.assertRaisesRegex(
                    self.gate.GateEvidenceError,
                    "does not derive",
                ):
                    self.gate.verify_decision_evidence(
                        changed_raw,
                        allow_fixture=True,
                    )

    def test_inconclusive_requires_hash_bound_exhaustion_without_numerics(self):
        raw = fixture_raw_evidence(self.gate, self.gate.INCONCLUSIVE)
        self.assertEqual(
            self.gate.verify_decision_evidence(
                raw,
                allow_fixture=True,
            ).decision,
            self.gate.INCONCLUSIVE,
        )
        mutations = (
            replace(raw, terminal_evidence_exhausted=False),
            replace(raw, task4_status="PASS"),
            replace(
                raw,
                mechanisms=(
                    replace(raw.mechanisms[0], complete_cost=1.0),
                ),
            ),
            replace(raw, terminal_record_hash="0" * 64),
        )
        for changed in mutations:
            with self.subTest(changed=changed):
                if changed.terminal_record_hash != "0" * 64:
                    changed = self.gate.bind_fixture_decision_evidence(changed)
                with self.assertRaises(self.gate.GateEvidenceError):
                    self.gate.verify_decision_evidence(
                        changed,
                        allow_fixture=True,
                    )

    def test_unknown_task3c_exception_is_not_converted_to_inconclusive(self):
        with patch.object(
            self.gate,
            "terminal_record_for_task5",
            side_effect=RuntimeError("unexpected programmer failure"),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "unexpected programmer failure",
            ):
                self.gate._evaluate_verified_terminal(ROOT)

    def test_terminal_labels_hash_and_task4_fields_are_fresh_bound(self):
        mutations = {
            "decision": self.gate.ADMIT,
            "terminal_classification": "INCONCLUSIVE",
            "terminal_decision": "FORGED_TERMINAL",
            "terminal_record_hash": "0" * 64,
            "task4_status": "PASS",
            "complete_cost_status": "PASS",
            "complete_cost": 1.0,
            "amdahl_status": "PASS",
            "amdahl_projection": 1.01,
            "amdahl_pessimistic_projection": 0.0,
            "production_hot_path_permission": True,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                with self.assertRaisesRegex(
                    ValueError,
                    "freshly verified",
                ):
                    self._summary(replace(self.result, **{field: value}))

    def test_terminal_mechanism_sources_are_independently_mutation_checked(self):
        terminal = self.result.terminal_record
        first = terminal.operator_results[0]
        operator_mutations = {
            "phase_identity_passed": False,
            "joint_ranks": (first.joint_ranks[0] + 1, first.joint_ranks[1]),
            "joint_rank_passed": False,
            "structural_improvement": True,
            "decision": "FORGED_OPERATOR_DECISION",
            "result_hash": "0" * 64,
        }
        for field, value in operator_mutations.items():
            with self.subTest(operator_field=field):
                changed_operator = replace(first, **{field: value})
                changed_terminal = replace(
                    terminal,
                    operator_results=(
                        changed_operator,
                        *terminal.operator_results[1:],
                    ),
                )
                forged = replace(
                    self.result,
                    terminal_record=changed_terminal,
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "freshly verified",
                ):
                    self._summary(forged)

        terminal_mutations = {
            "classification": "INCONCLUSIVE",
            "decision": "FORGED_TERMINAL_DECISION",
            "replay_status": "PASS",
            "task4_status": "PASS",
            "conversion_status": "FORGED_TASK3B",
            "record_hash": "f" * 64,
        }
        for field, value in terminal_mutations.items():
            with self.subTest(terminal_field=field):
                forged = replace(
                    self.result,
                    terminal_record=replace(
                        terminal,
                        **{field: value},
                    ),
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "freshly verified",
                ):
                    self._summary(forged)

    def test_generator_api_and_cli_require_explicit_input_commit(self):
        parameter = inspect.signature(
            self.gate.evaluate_candidate_c
        ).parameters["input_commit"]
        self.assertEqual(parameter.default, inspect.Parameter.empty)
        with self.assertRaises(TypeError):
            self.gate.evaluate_candidate_c(ROOT)
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/run_candidate_c_rank_bounded_gate.py"),
                "--root",
                str(ROOT),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--input-commit", completed.stderr)

    def test_invalid_and_nonancestor_commits_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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
            tracked = root / "input.txt"
            tracked.write_text("input\n", encoding="ascii", newline="\n")
            subprocess.run(["git", "add", "input.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "input"],
                cwd=root,
                check=True,
            )
            with self.assertRaisesRegex(
                self.gate.GateEvidenceError,
                "invalid implementation-input commit",
            ):
                self.gate._resolve_input_commit(root, "not-a-commit")
            tree = subprocess.run(
                ["git", "write-tree"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            side = subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Candidate C Test",
                    "-c",
                    "user.email=candidate-c-test@example.invalid",
                    "commit-tree",
                    tree,
                ],
                cwd=root,
                input="independent test commit\n",
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            with self.assertRaisesRegex(
                self.gate.GateEvidenceError,
                "not an ancestor",
            ):
                self.gate._resolve_input_commit(root, side)

    def test_manifest_blob_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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
            path = root / "input.txt"
            path.write_text("committed\n", encoding="ascii", newline="\n")
            subprocess.run(["git", "add", "input.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "input"],
                cwd=root,
                check=True,
            )
            commit = git_head(root)
            path.write_text("mutated\n", encoding="ascii", newline="\n")
            with self.assertRaisesRegex(
                self.gate.GateEvidenceError,
                "does not match implementation-input commit",
            ):
                self.gate._validated_input_rows(
                    root,
                    commit,
                    ("input.txt",),
                )

    def test_manifest_is_the_complete_internal_dependency_set(self):
        self.assertEqual(
            self.gate.COMPUTATIONAL_INPUTS,
            EXPECTED_COMPUTATIONAL_INPUTS,
        )
        self.assertIn(
            "research/mat_sab/finite_linear.py",
            self.gate.COMPUTATIONAL_INPUTS,
        )
        self.assertIn(
            "scripts/apply_candidate_c_rank_bounded_gate.py",
            self.gate.COMPUTATIONAL_INPUTS,
        )
        self.assertIn(
            "scripts/mat_sab_research_state.py",
            self.gate.COMPUTATIONAL_INPUTS,
        )
        self.assertIn(
            "scripts/__init__.py",
            self.gate.COMPUTATIONAL_INPUTS,
        )

    def _check_generator_registry_matches_recursive_local_import_closure(self):
        tree = ast.parse(
            (
                ROOT / "scripts/run_candidate_c_rank_bounded_gate.py"
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
        with tempfile.TemporaryDirectory() as tmp:
            root, commit = self._clone_working_generator(tmp)
            derived = self.gate._derive_local_import_closure(
                root,
                commit,
                self.gate.GENERATOR_LOCAL_IMPORT_ROOTS,
            )
        self.assertEqual(derived, GENERATOR_LOCAL_IMPORT_CLOSURE)
        self.assertEqual(
            derived,
            self.gate.GENERATOR_EXECUTABLE_INPUTS,
        )

    def _check_generator_dynamic_import_binding_model_tracks_aliases(self):
        tree = ast.parse(
            "\n".join(
                (
                    "import importlib as module_alias",
                    (
                        "from importlib import import_module "
                        "as imported_loader"
                    ),
                    "assigned_loader = module_alias.import_module",
                    "copied_loader = imported_loader",
                    "assigned_loader('research.alias_one')",
                    "copied_loader('research.alias_two')",
                )
            )
        )
        self.assertEqual(
            self.gate._literal_dynamic_imports(
                tree,
                "generator_alias_probe.py",
            ),
            ("research.alias_one", "research.alias_two"),
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
            self.gate.LocalImportPreflightError,
            "nonliteral dynamic import",
        ):
            self.gate._literal_dynamic_imports(
                nonliteral,
                "generator_alias_probe.py",
            )

    def _check_real_generator_cli_current_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, commit = self._clone_working_generator(tmp)
            destination = Path(tmp) / "output"
            destination.mkdir()
            completed = self._run_generator(
                root,
                commit,
                destination,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout.strip(), self.gate.REJECT)
            self.assertEqual(
                {
                    path.name
                    for path in (
                        destination
                        / "repro/candidate_c_rank_bounded_gate"
                    ).iterdir()
                },
                EXPECTED_ARTIFACTS,
            )

    def _check_real_generator_cli_rejects_cross_checkout_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, commit = self._clone_working_generator(tmp)
            destination = Path(tmp) / "output"
            destination.mkdir()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(
                        ROOT
                        / "scripts/run_candidate_c_rank_bounded_gate.py"
                    ),
                    "--root",
                    str(root),
                    "--destination-root",
                    str(destination),
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
            self.assertFalse(any(destination.rglob("*")))

    def _check_real_generator_cli_rejects_aliased_dynamic_imports(self):
        cases = (
            (
                "literal_alias",
                "\n".join(
                    (
                        "import importlib as generator_importlib",
                        (
                            "generator_loader = "
                            "generator_importlib.import_module"
                        ),
                        (
                            "generator_loader("
                            "'research.mat_sab.generator_alias_probe')"
                        ),
                        "",
                    )
                ),
                "executable registry does not match recursive import closure",
            ),
            (
                "nonliteral_alias",
                "\n".join(
                    (
                        (
                            "from importlib import import_module "
                            "as imported_generator_loader"
                        ),
                        "generator_loader = imported_generator_loader",
                        (
                            "generator_target = "
                            "'research.mat_sab.generator_alias_probe'"
                        ),
                        "generator_loader(generator_target)",
                        "",
                    )
                ),
                "nonliteral dynamic import",
            ),
        )
        for name, source, expected_error in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root, _ = self._clone_working_generator(tmp)
                dependency = root / "research/mat_sab/finite_linear.py"
                dependency.write_text(
                    dependency.read_text(encoding="ascii") + "\n" + source,
                    encoding="ascii",
                    newline="\n",
                )
                marker = root / "UNVERIFIED_GENERATOR_ALIAS_EXECUTED"
                probe = root / "research/mat_sab/generator_alias_probe.py"
                probe.write_text(
                    "\n".join(
                        (
                            "from pathlib import Path",
                            (
                                "Path('UNVERIFIED_GENERATOR_ALIAS_EXECUTED')"
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
                commit = git_head(root)
                destination = Path(tmp) / "output"
                destination.mkdir()
                completed = self._run_generator(
                    root,
                    commit,
                    destination,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(expected_error, completed.stderr)
                self.assertFalse(marker.exists())
                self.assertFalse(any(destination.rglob("*")))

    def _check_real_generator_cli_ignores_valid_adjacent_timestamp_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, commit = self._clone_working_generator(tmp)
            destination = Path(tmp) / "output"
            destination.mkdir()
            no_write_environment = os.environ.copy()
            no_write_environment["PYTHONDONTWRITEBYTECODE"] = "1"
            baseline = self._run_generator(
                root,
                commit,
                destination,
                environment=no_write_environment,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr)
            generated = (
                destination / "repro/candidate_c_rank_bounded_gate"
            )
            before_outputs = {
                path.name: path.read_bytes()
                for path in generated.iterdir()
            }
            for cache_dir in sorted(
                root.rglob("__pycache__"),
                reverse=True,
            ):
                shutil.rmtree(cache_dir)
            marker = root / "STALE_GENERATOR_CACHE_EXECUTED"
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
            before_caches = _adjacent_cache_snapshot(root)
            completed = self._run_generator(
                root,
                commit,
                destination,
                environment=environment,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout.strip(), self.gate.REJECT)
            self.assertFalse(marker.exists())
            self.assertEqual(
                before_outputs,
                {
                    path.name: path.read_bytes()
                    for path in generated.iterdir()
                },
            )
            self.assertEqual(
                before_caches,
                _adjacent_cache_snapshot(root),
            )

    def test_generator_emits_complete_byte_identical_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            first = self._write(destination)
            before = {
                path.relative_to(destination).as_posix(): path.read_bytes()
                for path in first
            }
            second = self._write(destination)
            after = {
                path.relative_to(destination).as_posix(): path.read_bytes()
                for path in second
            }
            generated = destination / "repro/candidate_c_rank_bounded_gate"
            self.assertEqual(
                {path.name for path in generated.iterdir()},
                EXPECTED_ARTIFACTS,
            )
            self.assertEqual(before, after)

    def test_staged_publish_failure_restores_all_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            paths = self._write(destination)
            before = {
                path.relative_to(destination).as_posix(): path.read_bytes()
                for path in paths
            }
            original_replace = os.replace

            def fail_on_variant(source, target):
                if Path(target) == (
                    destination
                    / "algorithm_variants/candidate_c_rank_bounded_state.md"
                ):
                    raise OSError("injected staged publish failure")
                return original_replace(source, target)

            with (
                patch.object(
                    self.gate.os,
                    "replace",
                    side_effect=fail_on_variant,
                ),
                self.assertRaisesRegex(
                    OSError,
                    "injected staged publish failure",
                ),
            ):
                self._write(destination)
            after = {
                path.relative_to(destination).as_posix(): path.read_bytes()
                for path in paths
            }
            self.assertEqual(before, after)
            self.assertFalse(
                any(
                    path.name.startswith(".candidate-c-stage-")
                    for path in destination.iterdir()
                )
            )

    def test_manifest_index_and_docs_bind_explicit_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            self._write(destination)
            generated = destination / "repro/candidate_c_rank_bounded_gate"
            with (generated / "artifact_index.csv").open(
                newline="",
                encoding="ascii",
            ) as handle:
                index = {
                    row["path"]: row["sha256"]
                    for row in csv.DictReader(handle)
                }
            for relative, digest in index.items():
                self.assertEqual(
                    hashlib.sha256(
                        (destination / relative).read_bytes()
                    ).hexdigest(),
                    digest,
                )
            with (generated / "input_manifest.csv").open(
                newline="",
                encoding="ascii",
            ) as handle:
                manifest = {
                    row["path"]: (row["availability"], row["sha256"])
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(set(manifest), set(EXPECTED_COMPUTATIONAL_INPUTS))
            for relative, (availability, digest) in manifest.items():
                self.assertEqual(availability, "PRESENT")
                committed = self.gate._git_regular_blob(
                    ROOT,
                    self.input_commit,
                    relative,
                )
                self.assertEqual(hashlib.sha256(committed).hexdigest(), digest)
            with (generated / "closeout_executable_manifest.csv").open(
                newline="",
                encoding="ascii",
            ) as handle:
                executables = tuple(csv.DictReader(handle))
            self.assertEqual(
                {row["path"] for row in executables},
                set(self.gate.CLOSEOUT_EXECUTABLE_INPUTS),
            )
            for row in executables:
                self.assertEqual(
                    row["sha256"],
                    manifest[row["path"]][1],
                )
            documents = (
                generated / "reproduction_commands.md",
                destination / "docs/candidate_c_rank_bounded_mechanism_gate.md",
                destination / "algorithm_variants/candidate_c_rank_bounded_state.md",
                destination / "experiments/candidate_c_rank_bounded_gate_plan.md",
            )
            for document in documents:
                with self.subTest(document=document.name):
                    self.assertIn(
                        self.input_commit,
                        document.read_text(encoding="ascii"),
                    )
            reproduction = (
                generated / "reproduction_commands.md"
            ).read_text(encoding="ascii")
            self.assertNotIn(
                "build_mat_sab_selector_techgraph.py",
                reproduction,
            )
            for script in (
                "scripts/run_candidate_c_rank_bounded_gate.py",
                "scripts/apply_candidate_c_rank_bounded_gate.py",
            ):
                self.assertIn(
                    f"python {script} --input-commit "
                    f"{self.input_commit}",
                    reproduction,
                )

    @unittest.skipUnless(
        hasattr(os, "symlink"),
        "symbolic links are not supported",
    )
    def test_source_symlink_escape_is_rejected_without_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "root"
            root.mkdir()
            outside = base / "outside.txt"
            outside.write_text("outside\n", encoding="ascii", newline="\n")
            try:
                os.symlink(outside, root / "input.txt")
            except OSError as error:
                if getattr(error, "winerror", None) == 1314:
                    self.skipTest(f"symbolic links unavailable: {error}")
                raise
            with self.assertRaisesRegex(
                self.gate.GateEvidenceError,
                "escapes declared root",
            ):
                self.gate._resolve_under_root(
                    root,
                    root / "input.txt",
                    "manifest source input.txt",
                    strict=False,
                )
            self.assertEqual(outside.read_text(encoding="ascii"), "outside\n")

    @unittest.skipUnless(
        hasattr(os, "symlink"),
        "symbolic links are not supported",
    )
    def test_destination_symlink_escape_is_rejected_without_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            destination = base / "destination"
            outside = base / "outside"
            destination.mkdir()
            outside.mkdir()
            try:
                os.symlink(
                    outside,
                    destination / "repro",
                    target_is_directory=True,
                )
            except OSError as error:
                if getattr(error, "winerror", None) == 1314:
                    self.skipTest(f"symbolic links unavailable: {error}")
                raise
            with self.assertRaisesRegex(
                self.gate.GateEvidenceError,
                "escapes declared root",
            ):
                self._write(destination)
            self.assertEqual(tuple(outside.iterdir()), ())

    def test_generated_pack_is_ascii(self):
        with tempfile.TemporaryDirectory() as tmp:
            for path in self._write(Path(tmp)):
                with self.subTest(path=path.name):
                    path.read_bytes().decode("ascii")

    def test_task5_clis_import_from_outside_repository(self):
        scripts = (
            "scripts/run_candidate_c_rank_bounded_gate.py",
            "scripts/apply_candidate_c_rank_bounded_gate.py",
        )
        for relative in scripts:
            with self.subTest(script=relative):
                with tempfile.TemporaryDirectory() as tmp:
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(ROOT / relative),
                            "--help",
                        ],
                        cwd=tmp,
                        capture_output=True,
                        text=True,
                    )
                self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_final_head_fresh_render_matches_all_tracked_artifacts(self):
        bound_commit = published_input_commit()
        result = self.gate.evaluate_candidate_c(
            ROOT,
            input_commit=bound_commit,
        )
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            paths = self.gate.write_gate_artifacts(
                ROOT,
                result,
                input_commit=bound_commit,
                destination_root=destination,
            )
            for fresh in paths:
                tracked = ROOT / fresh.relative_to(destination)
                with self.subTest(path=fresh.relative_to(destination)):
                    self.assertEqual(tracked.read_bytes(), fresh.read_bytes())


class CandidateCGeneratorBootstrapTests(unittest.TestCase):
    gate = load_gate()
    _clone_working_generator = staticmethod(
        CandidateCGateTests._clone_working_generator
    )
    _run_generator = staticmethod(CandidateCGateTests._run_generator)
    test_generator_registry_matches_recursive_local_import_closure = (
        CandidateCGateTests
        ._check_generator_registry_matches_recursive_local_import_closure
    )
    test_generator_dynamic_import_binding_model_tracks_aliases = (
        CandidateCGateTests
        ._check_generator_dynamic_import_binding_model_tracks_aliases
    )
    test_real_generator_cli_current_path = (
        CandidateCGateTests._check_real_generator_cli_current_path
    )
    test_real_generator_cli_rejects_cross_checkout_root = (
        CandidateCGateTests
        ._check_real_generator_cli_rejects_cross_checkout_root
    )
    test_real_generator_cli_rejects_aliased_dynamic_imports = (
        CandidateCGateTests
        ._check_real_generator_cli_rejects_aliased_dynamic_imports
    )
    test_real_generator_cli_ignores_valid_adjacent_timestamp_cache = (
        CandidateCGateTests
        ._check_real_generator_cli_ignores_valid_adjacent_timestamp_cache
    )


if __name__ == "__main__":
    unittest.main()
