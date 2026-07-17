from __future__ import annotations

import unittest
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

from research.mat_sab import candidate_c_registered_replay as registered_replay
from research.mat_sab.candidate_c_operator_tensor import (
    ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY,
    REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
    RING_MODULUS,
    ROUTE_PHASE_CORRECT_HIGH_RANK_OPERATOR_TO_C2,
    run_c1_operator_gate,
    verify_operator_gate_result,
)
from research.mat_sab.candidate_c_registered_replay import (
    AdmittedReplayNotImplemented,
    CandidateCTerminalRecord,
    ConversionBoundaryMutation,
    ConversionKeyIdentityMutation,
    NoRegisteredCandidateCOperator,
    RegisteredScheduleTrace,
    RejectedConversionEnvelope,
    StateEdgeMutation,
    UnsupportedC2Material,
    registered_operator_for_task4,
    replay_registered_operator,
    terminal_record_for_task5,
)


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SCHEDULE_HASH = (
    "a42e89d07964b289fa3ca06156a566887c4b4c76b6e68533dac32e59fd76f1b9"
)
EXPECTED_EVENT_DIGEST = (
    "e84ce09a73d801386aea0b332759f938ca1b72c3288b8cf93f7c7bd13f23cb39"
)
EXPECTED_STATE_EDGE_DIGEST = (
    "0a1344da71fe2e1c853ca3ec9386de4a7f1f3540278d06dca8d953b0cbb77d6d"
)
EXPECTED_RESULT_HASHES = (
    "41d9629ceab043f9b18b97cafa7edb7c2f84d7d85feac0816c8951a887cadbf8",
    "2dfa7574c3c0a2708c69ec4c918c30ca01a239f119c458c7c4d9d5d5bd817a78",
    "553247432086c35f913b21e1706e620f5978b555c44e8c315a8943750c8ba36d",
)


@lru_cache(maxsize=1)
def _operator_results():
    return tuple(
        run_c1_operator_gate(ROOT, r, RING_MODULUS)
        for r in (2, 4, 6)
    )


@lru_cache(maxsize=1)
def _terminal_record():
    return terminal_record_for_task5(ROOT)


def _mutate_first_coefficient(value):
    if type(value) is int:
        return (value + 1) % RING_MODULUS, True
    items = list(value)
    for index, item in enumerate(items):
        replacement, changed = _mutate_first_coefficient(item)
        if changed:
            items[index] = replacement
            return tuple(items), True
    return value, False


class RegisteredReplayInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = _operator_results()

    def test_actual_results_verify_and_rejection_skips_registered_replay(self):
        for result in self.results:
            with self.subTest(r=result.r):
                self.assertTrue(verify_operator_gate_result(result))
                self.assertEqual(
                    result.decision,
                    REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
                )
                with patch.object(
                    registered_replay,
                    "iter_binary_schedule_events",
                ) as events:
                    self.assertIsNone(
                        replay_registered_operator(ROOT, result, None)
                    )
                events.assert_not_called()

    def test_fabricated_admission_fails_before_replay(self):
        forged = replace(
            self.results[0],
            decision=ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY,
        )
        with self.assertRaisesRegex(ValueError, "C1 decision"):
            replay_registered_operator(ROOT, forged, None)

    def test_internally_consistent_c1_or_c2_route_has_no_executor(self):
        for decision in (
            ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY,
            ROUTE_PHASE_CORRECT_HIGH_RANK_OPERATOR_TO_C2,
        ):
            with self.subTest(decision=decision):
                admitted = replace(
                    self.results[0],
                    decision=decision,
                )
                with (
                    patch.object(
                        registered_replay,
                        "run_c1_operator_gate",
                        return_value=admitted,
                    ),
                    patch.object(
                        registered_replay,
                        "verify_operator_gate_result",
                        return_value=True,
                    ),
                    patch.object(
                        registered_replay,
                        "iter_binary_schedule_events",
                    ) as events,
                ):
                    with self.assertRaises(
                        AdmittedReplayNotImplemented
                    ):
                        replay_registered_operator(
                            ROOT,
                            admitted,
                            None,
                        )
                events.assert_not_called()

    def test_internally_consistent_admission_cannot_authorize_task4(self):
        admitted = replace(
            self.results[0],
            decision=ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY,
        )
        with (
            patch.object(
                registered_replay,
                "run_c1_operator_gate",
                return_value=admitted,
            ),
            patch.object(
                registered_replay,
                "verify_operator_gate_result",
                return_value=True,
            ),
        ):
            with self.assertRaises(AdmittedReplayNotImplemented):
                registered_operator_for_task4(ROOT)

    def test_one_tensor_coefficient_mutation_fails_distinct_gate(self):
        result = self.results[0]
        tensor = result.tensors[0]
        mutated_masks, changed = _mutate_first_coefficient(
            tensor.mask_polynomials
        )
        self.assertTrue(changed)
        mutated_tensor = replace(
            tensor,
            mask_polynomials=mutated_masks,
        )
        forged = replace(
            result,
            tensors=(mutated_tensor, result.tensors[1]),
        )
        with self.assertRaisesRegex(ValueError, "C1 tensor coefficient"):
            replay_registered_operator(ROOT, forged, None)

    def test_typed_c1_state_edge_mutation_fails_distinct_gate(self):
        forged = replace(self.results[0], schedule_hash="0" * 64)
        with self.assertRaisesRegex(
            StateEdgeMutation,
            "C1 state/schedule edge",
        ):
            replay_registered_operator(ROOT, forged, None)

    def test_support_only_and_random_witness_inputs_are_not_operators(self):
        support_rows = {
            "source": "Stage203",
            "classification": "SUPPORT_ONLY_NO_NUMERIC_COEFFICIENTS",
            "rows": (("2", "0", "0"),),
        }
        with self.assertRaisesRegex(ValueError, "Stage203 support-only"):
            replay_registered_operator(ROOT, support_rows, None)

        random_witness = {
            "source": "Stage329",
            "classification": "RANDOM_WITNESS_MATRIX",
            "matrix": ((1, 2), (3, 4)),
        }
        with self.assertRaisesRegex(ValueError, "Stage329 random witness"):
            replay_registered_operator(ROOT, random_witness, None)

    def test_untyped_c2_claim_is_unsupported(self):
        conversion_claim = {
            "decision": "ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY",
            "conversion_material": {"key_id": "fabricated"},
        }
        with self.assertRaisesRegex(
            UnsupportedC2Material,
            "typed rejection-only",
        ):
            replay_registered_operator(
                ROOT,
                self.results[0],
                conversion_claim,
            )

    def test_typed_c2_claim_is_rejected_without_task3b(self):
        envelope = RejectedConversionEnvelope.from_unverified_claim(
            claimed_decision=(
                "ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY"
            ),
            boundaries=("monomial:0/bit:0",),
            conversion_key_identities=("candidate-c-key:0",),
        )
        with self.assertRaisesRegex(
            UnsupportedC2Material,
            "no verified Task 3B result",
        ):
            replay_registered_operator(
                ROOT,
                self.results[0],
                envelope,
            )

    def test_conversion_boundary_mutation_fails_distinct_public_gate(self):
        envelope = RejectedConversionEnvelope.from_unverified_claim(
            claimed_decision=(
                "ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY"
            ),
            boundaries=("monomial:0/bit:0",),
            conversion_key_identities=("candidate-c-key:0",),
        )
        mutated = replace(
            envelope,
            boundaries=("monomial:0/bit:1",),
        )
        with self.assertRaisesRegex(
            ConversionBoundaryMutation,
            "conversion boundary",
        ):
            replay_registered_operator(
                ROOT,
                self.results[0],
                mutated,
            )

        malformed_digest = replace(
            envelope,
            boundary_digest="not-a-sha256",
        )
        with self.assertRaisesRegex(
            ConversionBoundaryMutation,
            "conversion boundary",
        ):
            replay_registered_operator(
                ROOT,
                self.results[0],
                malformed_digest,
            )

    def test_conversion_key_mutation_fails_distinct_public_gate(self):
        envelope = RejectedConversionEnvelope.from_unverified_claim(
            claimed_decision=(
                "ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY"
            ),
            boundaries=("monomial:0/bit:0",),
            conversion_key_identities=("candidate-c-key:0",),
        )
        mutated = replace(
            envelope,
            conversion_key_identities=("candidate-c-key:1",),
        )
        with self.assertRaisesRegex(
            ConversionKeyIdentityMutation,
            "conversion-key identity",
        ):
            replay_registered_operator(
                ROOT,
                self.results[0],
                mutated,
            )

        malformed_digest = replace(
            envelope,
            key_identity_digest="not-a-sha256",
        )
        with self.assertRaisesRegex(
            ConversionKeyIdentityMutation,
            "conversion-key identity",
        ):
            replay_registered_operator(
                ROOT,
                self.results[0],
                malformed_digest,
            )


class TraceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = _operator_results()[0]
        cls.record = _terminal_record()

    def _unverified_trace(self):
        record = self.record
        provisional = RegisteredScheduleTrace(
            schema="candidate-c-task-3c-trace-v2",
            canonical_version="candidate-c-typed-canonical-v2",
            canonical_domain="candidate-c/registered-schedule-trace",
            r=2,
            operator_result_hash=self.result.result_hash,
            schedule_hash=record.schedule_hash,
            schedule_event_digest=record.schedule_event_digest,
            state_edge_digest=record.state_edge_digest,
            state_identity_digest="0" * 64,
            h=record.h,
            monomial_calls=record.monomial_calls,
            r_prec=record.r_prec,
            in_N=record.in_N,
            selector_events=record.selector_events,
            ncmux_events=record.ncmux_events,
            cmux_events=record.cmux_events,
            butterfly_boundaries=record.butterfly_boundaries,
            monomial_boundaries=record.monomial_boundaries,
            sub_a_boundaries=record.sub_a_boundaries,
            phase_checks=record.selector_events,
            rank_checks=record.selector_events,
            accumulator_state_identities=record.monomial_calls * record.in_N,
            max_rho=self.result.rho,
            status="UNVERIFIED_REPLAY_CLAIM",
            trace_hash="",
        )
        return replace(
            provisional,
            trace_hash=provisional.recomputed_hash(),
        )

    def test_trace_binds_complete_schedule_dimensions_and_fails_closed(self):
        trace = self._unverified_trace()
        self.assertEqual(
            (trace.h, trace.monomial_calls, trace.r_prec, trace.in_N),
            (39, 40, 7, 2048),
        )
        self.assertEqual(trace.trace_hash, trace.recomputed_hash())
        with self.assertRaises(AdmittedReplayNotImplemented):
            trace.validate(ROOT)

    def test_trace_dimensions_are_verified_against_fresh_schedule(self):
        trace = self._unverified_trace()
        for name in ("h", "monomial_calls", "r_prec", "in_N"):
            with self.subTest(field=name):
                mutated = replace(
                    trace,
                    **{name: getattr(trace, name) + 1},
                    trace_hash="",
                )
                mutated = replace(
                    mutated,
                    trace_hash=mutated.recomputed_hash(),
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "registered trace schedule binding",
                ):
                    mutated.validate(ROOT)

    def test_trace_type_substitution_fails_before_hashing(self):
        trace = self._unverified_trace()
        substituted = replace(
            trace,
            canonical_domain=["candidate-c/registered-schedule-trace"],
        )
        with self.assertRaisesRegex(TypeError, "canonical_domain must be str"):
            substituted.canonical_bytes()


class TerminalRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = _terminal_record()

    def test_terminal_record_binds_all_real_gate_results_and_schedule(self):
        record = self.record
        self.assertIsInstance(record, CandidateCTerminalRecord)
        self.assertEqual(record.schema, "candidate-c-task-3c-terminal-v2")
        self.assertEqual(
            record.canonical_version,
            "candidate-c-typed-canonical-v2",
        )
        self.assertEqual(
            record.canonical_domain,
            "candidate-c/terminal-record",
        )
        self.assertEqual(record.classification, "REJECT")
        self.assertEqual(
            record.decision,
            REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
        )
        self.assertEqual(
            record.replay_status,
            "SKIPPED_NO_REGISTERED_OPERATOR",
        )
        self.assertEqual(
            record.task4_status,
            "SKIPPED_NO_REGISTERED_OPERATOR",
        )
        self.assertEqual(
            record.conversion_status,
            "NO_VERIFIED_TASK3B_RESULT",
        )
        self.assertEqual(record.r_values, (2, 4, 6))
        self.assertEqual(
            tuple(result.result_hash for result in record.operator_results),
            EXPECTED_RESULT_HASHES,
        )
        self.assertEqual(
            tuple(
                result.schedule_hash
                for result in record.operator_results
            ),
            (EXPECTED_SCHEDULE_HASH,) * 3,
        )
        self.assertTrue(record.verify(ROOT))

    def test_terminal_record_binds_exact_event_digest_and_counts(self):
        record = self.record
        self.assertEqual(record.schedule_hash, EXPECTED_SCHEDULE_HASH)
        self.assertEqual(record.schedule_event_digest, EXPECTED_EVENT_DIGEST)
        self.assertEqual(record.state_edge_digest, EXPECTED_STATE_EDGE_DIGEST)
        self.assertEqual(record.h, 39)
        self.assertEqual(record.monomial_calls, 40)
        self.assertEqual(record.r_prec, 7)
        self.assertEqual(record.in_N, 2048)
        self.assertEqual(record.selector_events, 573440)
        self.assertEqual(record.ncmux_events, 5080)
        self.assertEqual(record.cmux_events, 568360)
        self.assertEqual(record.butterfly_boundaries, 280)
        self.assertEqual(record.monomial_boundaries, 40)
        self.assertEqual(record.sub_a_boundaries, 39)

    def test_task4_is_unreachable_with_exact_terminal_reason(self):
        with self.assertRaises(NoRegisteredCandidateCOperator) as caught:
            registered_operator_for_task4(ROOT)
        self.assertEqual(
            caught.exception.reason,
            REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
        )

    def test_terminal_classification_and_skip_status_cannot_be_relabelled(self):
        forged_classification = replace(
            self.record,
            classification="INCONCLUSIVE",
        )
        with self.assertRaisesRegex(ValueError, "terminal classification"):
            forged_classification.validate(ROOT)
        self.assertFalse(forged_classification.verify(ROOT))

        forged_skip = replace(self.record, task4_status="AUTHORIZED")
        with self.assertRaisesRegex(ValueError, "Task 4 skipped status"):
            forged_skip.validate(ROOT)
        self.assertFalse(forged_skip.verify(ROOT))

    def test_bound_state_edge_mutation_fails_real_terminal_validator(self):
        forged = replace(self.record, state_edge_digest="0" * 64)
        with self.assertRaisesRegex(
            StateEdgeMutation,
            "state/schedule edge",
        ):
            forged.validate(ROOT)

    def test_complete_structural_counts_are_bound_by_real_verifier(self):
        result = self.record.operator_results[0]
        changed_counts = replace(
            result.evaluator_counts,
            add_multiplies=result.evaluator_counts.add_multiplies + 1,
        )
        changed_result = replace(
            result,
            evaluator_counts=changed_counts,
        )
        forged = replace(
            self.record,
            operator_results=(
                changed_result,
                *self.record.operator_results[1:],
            ),
        )
        with self.assertRaisesRegex(ValueError, "Task 3A operator gate result"):
            forged.validate(ROOT)

    def test_tuple_list_substitution_is_not_canonically_equivalent(self):
        tuple_hash = registered_replay._sha256(
            "candidate-c/test-sequence-type",
            ("r", 2, 4, 6),
        )
        list_hash = registered_replay._sha256(
            "candidate-c/test-sequence-type",
            ["r", 2, 4, 6],
        )
        self.assertNotEqual(tuple_hash, list_hash)

        substituted = replace(
            self.record,
            r_values=list(self.record.r_values),
        )
        with self.assertRaisesRegex(TypeError, "r_values must be tuple"):
            substituted.canonical_bytes()

    def test_repeated_terminal_generation_is_byte_identical(self):
        repeated = terminal_record_for_task5(ROOT)
        self.assertEqual(repeated, self.record)
        self.assertEqual(
            repeated.canonical_bytes(),
            self.record.canonical_bytes(),
        )
        self.assertEqual(repeated.record_hash, self.record.record_hash)


if __name__ == "__main__":
    unittest.main()
