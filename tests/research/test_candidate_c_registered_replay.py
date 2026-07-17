from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from research.mat_sab.candidate_c_operator_tensor import (
    ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY,
    REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
    RING_MODULUS,
    run_c1_operator_gate,
    verify_operator_gate_result,
)
from research.mat_sab.candidate_c_registered_replay import (
    NO_REGISTERED_CONVERSION_BOUNDARY_DIGEST,
    NO_REGISTERED_CONVERSION_KEY_IDENTITY_DIGEST,
    CandidateCTerminalRecord,
    NoRegisteredCandidateCOperator,
    registered_operator_for_task4,
    replay_registered_operator,
    terminal_record_for_task5,
)


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SCHEDULE_HASH = (
    "a42e89d07964b289fa3ca06156a566887c4b4c76b6e68533dac32e59fd76f1b9"
)
EXPECTED_EVENT_DIGEST = (
    "8e8836b8c74c679b48d65268fcd80ffbb2a2ab96cbe708c6871ed83bcc8ac739"
)
EXPECTED_STATE_EDGE_DIGEST = (
    "e2ed0754ad34389c5c630ad989e5f7677c04083421d876f3700ca24e0d473dbd"
)
EXPECTED_RESULT_HASHES = (
    "41d9629ceab043f9b18b97cafa7edb7c2f84d7d85feac0816c8951a887cadbf8",
    "2dfa7574c3c0a2708c69ec4c918c30ca01a239f119c458c7c4d9d5d5bd817a78",
    "553247432086c35f913b21e1706e620f5978b555c44e8c315a8943750c8ba36d",
)


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
        cls.results = tuple(
            run_c1_operator_gate(ROOT, r, RING_MODULUS)
            for r in (2, 4, 6)
        )

    def test_actual_results_verify_and_rejection_skips_registered_replay(self):
        for result in self.results:
            with self.subTest(r=result.r):
                self.assertTrue(verify_operator_gate_result(result))
                self.assertEqual(
                    result.decision,
                    REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
                )
                with patch(
                    "research.mat_sab.candidate_c_registered_replay."
                    "iter_binary_schedule_events"
                ) as events:
                    self.assertIsNone(
                        replay_registered_operator(ROOT, result, None)
                    )
                events.assert_not_called()

    def test_fabricated_admission_and_changed_decision_fail_closed(self):
        forged = replace(
            self.results[0],
            decision=ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY,
        )
        with self.assertRaisesRegex(ValueError, "C1 decision"):
            replay_registered_operator(ROOT, forged, None)

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

    def test_changed_c1_schedule_edge_fails_distinct_gate(self):
        forged = replace(self.results[0], schedule_hash="0" * 64)
        with self.assertRaisesRegex(ValueError, "C1 state/schedule edge"):
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

    def test_any_c2_claim_is_unregistered_without_task3b(self):
        conversion_claim = {
            "decision": "ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY",
            "conversion_material": {"key_id": "fabricated"},
        }
        with self.assertRaisesRegex(
            ValueError,
            "C2 admission without a verified Task 3B result",
        ):
            replay_registered_operator(
                ROOT,
                self.results[0],
                conversion_claim,
            )


class TerminalRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = terminal_record_for_task5(ROOT)

    def test_terminal_record_binds_all_real_gate_results_and_schedule(self):
        record = self.record
        self.assertIsInstance(record, CandidateCTerminalRecord)
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

    def test_state_conversion_boundary_and_key_mutations_fail_distinctly(self):
        mutations = (
            (
                {"state_edge_digest": "0" * 64},
                "C1 state/schedule edge",
            ),
            (
                {"conversion_boundary_digest": "0" * 64},
                "C2 conversion boundary",
            ),
            (
                {"conversion_key_identity_digest": "0" * 64},
                "C2 conversion-key identity",
            ),
        )
        self.assertEqual(
            self.record.conversion_boundary_digest,
            NO_REGISTERED_CONVERSION_BOUNDARY_DIGEST,
        )
        self.assertEqual(
            self.record.conversion_key_identity_digest,
            NO_REGISTERED_CONVERSION_KEY_IDENTITY_DIGEST,
        )
        for fields, message in mutations:
            with self.subTest(field=next(iter(fields))):
                forged = replace(self.record, **fields)
                with self.assertRaisesRegex(ValueError, message):
                    forged.validate(ROOT)
                self.assertFalse(forged.verify(ROOT))

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
        self.assertFalse(forged.verify(ROOT))

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
