import csv
from dataclasses import replace
import hashlib
import importlib
import inspect
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
APPROVED_TERMINAL_HASH = (
    "8ad876708aa4a736c0f0f9adae33bab766272f411e90fbc23a5ac23e10a73cb6"
)
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
    "research/mat_sab/candidate_c_operator_tensor.py",
    "research/mat_sab/candidate_c_registered_replay.py",
    "research/mat_sab/candidate_c_schedule.py",
    "research/mat_sab/finite_linear.py",
    "research/mat_sab/rank_bounded_state_model.py",
    "research/mat_sab/star_cycle_model.py",
    "scripts/run_candidate_c_rank_bounded_gate.py",
    "src/mosfhet/Makefile.def",
    "src/mosfhet/src/mattrgsw.c",
    "src/sab_pvw.c",
    "src/sparse_amortized_bootstrap.c",
    "theory_checks/candidate_c_rank_bounded_state_model.md",
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
                    row["path"]: row["sha256"]
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(set(manifest), set(EXPECTED_COMPUTATIONAL_INPUTS))
            for relative, digest in manifest.items():
                committed = self.gate._git_regular_blob(
                    ROOT,
                    self.input_commit,
                    relative,
                )
                self.assertEqual(hashlib.sha256(committed).hexdigest(), digest)
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


if __name__ == "__main__":
    unittest.main()
