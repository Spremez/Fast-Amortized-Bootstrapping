from dataclasses import replace
import unittest
from unittest.mock import patch

from research.mat_sab.finite_linear import rank as finite_rank
from research.mat_sab.rank_bounded_state_model import (
    MaskSpanState,
    append_mask_directions,
    compress_state,
    excess_rank,
    lane_difference_matrix,
    linear_combine_states,
    phase_vector,
    rotate_state,
    schedule_step,
    shared_state,
)


PRIME = 257


def state_with_two_symbols():
    return MaskSpanState(
        lane_coefficients=((0, 0), (1, 0), (0, 1)),
        body_constants=(11, 13, 17),
        mask_symbols=(5, 7),
        provenance=("alpha", "beta"),
        modulus=PRIME,
    )


def compressible_rank_two_state():
    return MaskSpanState(
        lane_coefficients=(
            (0, 0, 0),
            (1, 0, 1),
            (0, 1, 1),
            (1, 1, 2),
        ),
        body_constants=(11, 13, 17, 19),
        mask_symbols=(5, 7, 11),
        provenance=("alpha", "beta", "gamma"),
        modulus=PRIME,
    )


def matrix_product(lhs, rhs, modulus):
    return tuple(
        tuple(
            sum(
                lhs[row][inner] * rhs[inner][column]
                for inner in range(len(rhs))
            )
            % modulus
            for column in range(len(rhs[0]))
        )
        for row in range(len(lhs))
    )


class RankBoundedStateValidationTests(unittest.TestCase):
    def test_modulus_must_be_positive_and_prime(self):
        for modulus in (-3, 0, 1, 4, 15):
            with self.subTest(modulus=modulus):
                with self.assertRaises(ValueError):
                    shared_state(2, modulus)

    def test_lane_coefficients_must_be_rectangular(self):
        with self.assertRaises(ValueError):
            MaskSpanState(
                lane_coefficients=((0,), (1, 2)),
                body_constants=(0, 0),
                mask_symbols=(3,),
                provenance=("alpha",),
                modulus=PRIME,
            )

    def test_body_count_must_match_lane_count(self):
        with self.assertRaises(ValueError):
            MaskSpanState(
                lane_coefficients=((0,), (1,)),
                body_constants=(0,),
                mask_symbols=(3,),
                provenance=("alpha",),
                modulus=PRIME,
            )

    def test_secret_count_must_match_body_count(self):
        with self.assertRaises(ValueError):
            phase_vector(state_with_two_symbols(), (2, 3), PRIME)

    def test_reference_lane_coefficients_must_be_normalized_to_zero(self):
        with self.assertRaises(ValueError):
            MaskSpanState(
                lane_coefficients=((1,), (0,)),
                body_constants=(0, 0),
                mask_symbols=(3,),
                provenance=("alpha",),
                modulus=PRIME,
            )

    def test_projection_dimensions_must_match_symbol_count(self):
        with self.assertRaises(ValueError):
            compress_state(state_with_two_symbols(), ((1, 0, 0),))

    def test_projection_must_be_an_immutable_public_matrix(self):
        with self.assertRaises(ValueError):
            compress_state(state_with_two_symbols(), [[1, 0], [0, 1]])


class RankGrowthControlTests(unittest.TestCase):
    def test_exact_rank_is_invariant_under_every_reference_lane(self):
        for r in (2, 4, 6):
            patterns = tuple(
                (0, 0)
                if lane == 0
                else (
                    1 if lane == 1 else 0,
                    1 if lane == 2 else lane - 1,
                )
                for lane in range(r)
            )
            state = append_mask_directions(
                shared_state(r, PRIME),
                patterns,
            )
            expected_rank = min(2, r - 1)

            for reference_lane in range(r):
                with self.subTest(r=r, reference_lane=reference_lane):
                    differences = lane_difference_matrix(
                        state,
                        reference_lane=reference_lane,
                    )
                    self.assertEqual(len(differences), r - 1)
                    self.assertEqual(
                        finite_rank(differences, PRIME),
                        expected_rank,
                    )

    def test_shared_and_independent_direction_controls_use_exact_rank(self):
        for r in (2, 4, 6):
            with self.subTest(r=r, control="shared"):
                shared = shared_state(r, PRIME)
                self.assertEqual(lane_difference_matrix(shared), tuple(
                    () for _ in range(r - 1)
                ))
                self.assertEqual(excess_rank(shared), 0)

            one_pattern = tuple(
                (0,) if lane == 0 else (lane,)
                for lane in range(r)
            )
            with self.subTest(r=r, control="one"):
                self.assertEqual(
                    excess_rank(append_mask_directions(shared, one_pattern)),
                    1,
                )

            two_patterns = tuple(
                (0, 0)
                if lane == 0
                else (
                    1 if lane == 1 else 0,
                    1 if lane == 2 else (lane if lane > 2 else 0),
                )
                for lane in range(r)
            )
            with self.subTest(r=r, control="two"):
                self.assertEqual(
                    excess_rank(append_mask_directions(shared, two_patterns)),
                    min(2, r - 1),
                )

            identity_patterns = (tuple(0 for _ in range(r - 1)),) + tuple(
                tuple(
                    1 if column == lane - 1 else 0
                    for column in range(r - 1)
                )
                for lane in range(1, r)
            )
            with self.subTest(r=r, control="identity"):
                self.assertEqual(
                    excess_rank(
                        append_mask_directions(shared, identity_patterns)
                    ),
                    r - 1,
                )

    def test_excess_rank_calls_exact_finite_field_elimination(self):
        state = state_with_two_symbols()
        differences = ((1, 0), (0, 1))
        with patch(
            "research.mat_sab.rank_bounded_state_model.rank",
            wraps=finite_rank,
        ) as exact_rank:
            self.assertEqual(excess_rank(state), 2)
        exact_rank.assert_called_once_with(differences, PRIME)


class IndependentProvenanceTests(unittest.TestCase):
    def test_independent_operands_keep_disjoint_symbol_provenance(self):
        base = shared_state(4, PRIME)
        lhs = append_mask_directions(
            base,
            ((0,), (1,), (0,), (0,)),
        )
        rhs = append_mask_directions(
            base,
            ((0,), (0,), (1,), (0,)),
        )
        self.assertTrue(set(lhs.provenance).isdisjoint(rhs.provenance))

        combined = linear_combine_states(lhs, rhs, 1, 1)
        self.assertEqual(excess_rank(combined), 2)
        self.assertEqual(len(combined.provenance), 2)

    def test_merged_independent_identifier_is_rejected_before_false_low_rank(self):
        base = shared_state(4, PRIME)
        lhs = append_mask_directions(
            base,
            ((0,), (1,), (0,), (0,)),
        )
        rhs = append_mask_directions(
            base,
            ((0,), (0,), (1,), (0,)),
        )
        unsafe_merged = MaskSpanState(
            lane_coefficients=((0,), (1,), (1,), (0,)),
            body_constants=(0, 0, 0, 0),
            mask_symbols=lhs.mask_symbols,
            provenance=lhs.provenance,
            modulus=PRIME,
        )
        self.assertEqual(excess_rank(unsafe_merged), 1)

        mutated_rhs = replace(rhs, provenance=lhs.provenance)
        with self.assertRaisesRegex(ValueError, "independent provenance"):
            linear_combine_states(lhs, mutated_rhs, 1, 1)


class PhaseControlTests(unittest.TestCase):
    def test_scalar_related_rotation_cancels_to_zero_rank(self):
        for modulus in (2, 3, PRIME):
            with self.subTest(modulus=modulus):
                state = MaskSpanState(
                    lane_coefficients=((0, 0), (1, 0), (0, 1)),
                    body_constants=(1, 2, 3),
                    mask_symbols=(1, 2),
                    provenance=("alpha", "beta"),
                    modulus=modulus,
                )
                cancelled = linear_combine_states(
                    state,
                    rotate_state(state, 1),
                    1,
                    1,
                )

                self.assertEqual(
                    phase_vector(cancelled, (1, 1, 1), modulus),
                    (0, 0, 0),
                )
                self.assertEqual(excess_rank(cancelled), 0)
                self.assertEqual(cancelled.provenance, ())
                self.assertEqual(cancelled.mask_symbols, ())

    def test_appended_direction_phase_witnesses_do_not_depend_on_call_order(self):
        base = shared_state(3, PRIME)
        pattern = ((0, 0), (1, 2), (3, 5))
        first = append_mask_directions(base, pattern)
        append_mask_directions(
            shared_state(6, PRIME),
            ((0,), (1,), (2,), (3,), (4,), (5,)),
        )
        second = append_mask_directions(base, pattern)

        self.assertTrue(set(first.provenance).isdisjoint(second.provenance))
        self.assertEqual(first.mask_symbols, second.mask_symbols)
        self.assertEqual(
            phase_vector(first, (2, 3, 5), PRIME),
            phase_vector(second, (2, 3, 5), PRIME),
        )

    def test_hand_derived_r2_phase_oracle_fixes_orientation_and_sign(self):
        state = MaskSpanState(
            lane_coefficients=((0, 0), (2, 3)),
            body_constants=(11, 13),
            mask_symbols=(5, 7),
            provenance=("alpha", "beta"),
            modulus=PRIME,
        )
        self.assertEqual(phase_vector(state, (2, 3), PRIME), (11, 177))

    def test_addition_and_subtraction_preserve_exact_lane_phases(self):
        lhs = MaskSpanState(
            lane_coefficients=((0,), (2,)),
            body_constants=(11, 13),
            mask_symbols=(5,),
            provenance=("lhs",),
            modulus=PRIME,
        )
        rhs = MaskSpanState(
            lane_coefficients=((0,), (3,)),
            body_constants=(17, 19),
            mask_symbols=(7,),
            provenance=("rhs",),
            modulus=PRIME,
        )
        secrets = (2, 3)
        lhs_phase = phase_vector(lhs, secrets, PRIME)
        rhs_phase = phase_vector(rhs, secrets, PRIME)

        added = linear_combine_states(lhs, rhs, 1, 1)
        subtracted = linear_combine_states(lhs, rhs, 1, -1)
        self.assertEqual(
            phase_vector(added, secrets, PRIME),
            tuple(
                (left + right) % PRIME
                for left, right in zip(lhs_phase, rhs_phase)
            ),
        )
        self.assertEqual(
            phase_vector(subtracted, secrets, PRIME),
            tuple(
                (left - right) % PRIME
                for left, right in zip(lhs_phase, rhs_phase)
            ),
        )

    def test_rotation_applies_the_same_deterministic_map_to_mask_and_body(self):
        state = state_with_two_symbols()
        secrets = (2, 3, 5)
        exponent = 3
        factor = pow(-1, exponent, PRIME)
        rotated = rotate_state(state, exponent)

        self.assertEqual(
            rotated.lane_coefficients,
            tuple(
                tuple(factor * value % PRIME for value in row)
                for row in state.lane_coefficients
            ),
        )
        self.assertEqual(rotated.mask_symbols, state.mask_symbols)
        self.assertEqual(excess_rank(rotated), excess_rank(state))
        self.assertEqual(
            phase_vector(rotated, secrets, PRIME),
            tuple(
                factor * value % PRIME
                for value in phase_vector(state, secrets, PRIME)
            ),
        )

    def test_rotation_is_invertible_for_positive_and_negative_exponents_in_gf2(
        self,
    ):
        state = MaskSpanState(
            lane_coefficients=((0, 0), (1, 0), (0, 1)),
            body_constants=(1, 0, 1),
            mask_symbols=(1, 1),
            provenance=("alpha", "beta"),
            modulus=2,
        )
        secrets = (1, 1, 1)
        expected_phase = phase_vector(state, secrets, 2)

        for exponent in (1, -1, 2, -2):
            with self.subTest(exponent=exponent):
                rotated = rotate_state(state, exponent)
                restored = rotate_state(rotated, -exponent)
                self.assertEqual(
                    phase_vector(rotated, secrets, 2),
                    expected_phase,
                )
                self.assertEqual(restored, state)
                self.assertEqual(excess_rank(rotated), excess_rank(state))

    def test_accumulated_rotation_provenance_is_canonical(self):
        state = state_with_two_symbols()
        for first, second in ((5, -2), (5, -3), (-1, -2), (2, 4)):
            with self.subTest(first=first, second=second):
                nested = rotate_state(
                    rotate_state(state, first),
                    second,
                )
                direct = rotate_state(state, first + second)

                self.assertEqual(nested, direct)
                self.assertEqual(nested.provenance, direct.provenance)
                self.assertEqual(
                    nested._provenance_tokens,
                    direct._provenance_tokens,
                )
                combined = linear_combine_states(nested, direct, 1, 1)
                self.assertEqual(
                    len(combined.provenance),
                    len(state.provenance),
                )
                self.assertEqual(excess_rank(combined), excess_rank(state))

    def test_omitting_a_phase_active_direction_changes_the_oracle(self):
        complete = MaskSpanState(
            lane_coefficients=((0, 0), (2, 3)),
            body_constants=(11, 13),
            mask_symbols=(5, 7),
            provenance=("alpha", "beta"),
            modulus=PRIME,
        )
        omitted = MaskSpanState(
            lane_coefficients=((0,), (2,)),
            body_constants=complete.body_constants,
            mask_symbols=(5,),
            provenance=("alpha",),
            modulus=PRIME,
        )
        complete_phase = phase_vector(complete, (2, 3), PRIME)
        omitted_phase = phase_vector(omitted, (2, 3), PRIME)
        self.assertNotEqual(omitted_phase, complete_phase)
        self.assertEqual(
            tuple(
                (left - right) % PRIME
                for left, right in zip(omitted_phase, complete_phase)
            ),
            (0, 63),
        )


class CompressionSemanticsTests(unittest.TestCase):
    def test_identity_recompression_preserves_canonical_source_identity(self):
        state = compressible_rank_two_state()
        projection = ((1, 0, 1), (0, 1, 1))
        first = compress_state(state, projection).compressed_state

        recompressed = compress_state(
            first,
            ((1, 0), (0, 1)),
        ).compressed_state

        self.assertEqual(recompressed, first)
        self.assertEqual(
            recompressed._provenance_tokens,
            first._provenance_tokens,
        )
        cancelled = linear_combine_states(first, recompressed, 1, -1)
        self.assertEqual(excess_rank(cancelled), 0)
        self.assertEqual(cancelled.provenance, ())

    def test_composed_public_maps_match_their_matrix_product(self):
        state = compressible_rank_two_state()
        projection = ((1, 0, 1), (0, 1, 1))
        second_projection = ((1, 1), (1, 2))
        composed_projection = matrix_product(
            second_projection,
            projection,
            PRIME,
        )

        nested = compress_state(
            compress_state(state, projection).compressed_state,
            second_projection,
        ).compressed_state
        direct = compress_state(
            state,
            composed_projection,
        ).compressed_state

        self.assertEqual(nested, direct)
        self.assertEqual(
            nested._provenance_tokens,
            direct._provenance_tokens,
        )
        cancelled = linear_combine_states(nested, direct, 1, -1)
        self.assertEqual(excess_rank(cancelled), 0)
        self.assertEqual(cancelled.provenance, ())

    def test_compression_commutes_with_rotation_on_source_identity(self):
        state = compressible_rank_two_state()
        projection = ((1, 0, 1), (0, 1, 1))
        exponent = -3

        rotate_then_compress = compress_state(
            rotate_state(state, exponent),
            projection,
        ).compressed_state
        compress_then_rotate = rotate_state(
            compress_state(state, projection).compressed_state,
            exponent,
        )

        self.assertEqual(rotate_then_compress, compress_then_rotate)
        self.assertEqual(
            rotate_then_compress._provenance_tokens,
            compress_then_rotate._provenance_tokens,
        )
        cancelled = linear_combine_states(
            rotate_then_compress,
            compress_then_rotate,
            1,
            -1,
        )
        self.assertEqual(excess_rank(cancelled), 0)
        self.assertEqual(cancelled.provenance, ())

    def test_rho_zero_compression_discards_existing_inactive_symbols(self):
        state = MaskSpanState(
            lane_coefficients=((0, 0), (0, 0), (0, 0)),
            body_constants=(11, 13, 17),
            mask_symbols=(5, 7),
            provenance=("inactive-alpha", "inactive-beta"),
            modulus=PRIME,
        )
        self.assertEqual(excess_rank(state), 0)

        result = compress_state(state, ())

        self.assertTrue(result.phase_preserved)
        self.assertEqual(result.discarded_directions, 2)
        self.assertEqual(result.online_product_count, 0)
        self.assertEqual(result.key_component_count, 0)
        self.assertEqual(result.compressed_state.provenance, ())
        self.assertEqual(result.compressed_state.mask_symbols, ())
        self.assertEqual(
            result.compressed_state.lane_coefficients,
            ((), (), ()),
        )
        self.assertEqual(
            phase_vector(result.compressed_state, (2, 3, 5), PRIME),
            phase_vector(state, (2, 3, 5), PRIME),
        )

    def test_shared_state_has_truthful_zero_dimensional_compression(self):
        state = MaskSpanState(
            lane_coefficients=((), (), (), ()),
            body_constants=(11, 13, 17, 19),
            mask_symbols=(),
            provenance=(),
            modulus=PRIME,
        )

        result = compress_state(state, ())

        self.assertEqual(result.compressed_state, state)
        self.assertTrue(result.phase_preserved)
        self.assertEqual(result.discarded_directions, 0)
        self.assertEqual(result.online_product_count, 0)
        self.assertEqual(result.key_component_count, 0)
        self.assertEqual(excess_rank(result.compressed_state), 0)
        self.assertEqual(
            phase_vector(
                result.compressed_state,
                (2, 3, 5, 7),
                PRIME,
            ),
            phase_vector(state, (2, 3, 5, 7), PRIME),
        )

    def test_identical_compressions_derive_shareable_symbol_identity(self):
        state = MaskSpanState(
            lane_coefficients=(
                (0, 0, 0),
                (1, 0, 1),
                (0, 1, 1),
            ),
            body_constants=(11, 13, 17),
            mask_symbols=(5, 7, 11),
            provenance=("alpha", "beta", "gamma"),
            modulus=PRIME,
        )
        projection = ((1, 0, 1), (0, 1, 1))

        first = compress_state(state, projection).compressed_state
        second = compress_state(state, projection).compressed_state

        self.assertEqual(first.provenance, second.provenance)
        self.assertEqual(
            first._provenance_tokens,
            second._provenance_tokens,
        )
        combined = linear_combine_states(first, second, 1, 1)
        self.assertEqual(len(combined.provenance), 2)
        self.assertEqual(excess_rank(combined), 2)

    def test_compression_keeps_independent_hidden_roots_disjoint(self):
        lhs = MaskSpanState(
            lane_coefficients=((0,), (1,)),
            body_constants=(11, 13),
            mask_symbols=(5,),
            provenance=("alpha",),
            modulus=PRIME,
        )
        rhs = MaskSpanState(
            lane_coefficients=((0,), (1,)),
            body_constants=(11, 13),
            mask_symbols=(5,),
            provenance=("alpha",),
            modulus=PRIME,
        )
        lhs_compressed = compress_state(lhs, ((1,),)).compressed_state
        rhs_compressed = compress_state(rhs, ((1,),)).compressed_state

        self.assertEqual(
            lhs_compressed.provenance,
            rhs_compressed.provenance,
        )
        self.assertNotEqual(
            lhs_compressed._provenance_tokens,
            rhs_compressed._provenance_tokens,
        )
        with self.assertRaisesRegex(ValueError, "independent provenance"):
            linear_combine_states(
                lhs_compressed,
                rhs_compressed,
                1,
                1,
            )

    def test_online_products_count_returned_lane_component_equations(self):
        state = MaskSpanState(
            lane_coefficients=(
                (0, 0, 0),
                (1, 0, 1),
                (0, 1, 1),
            ),
            body_constants=(11, 13, 17),
            mask_symbols=(5, 7, 11),
            provenance=("alpha", "beta", "gamma"),
            modulus=PRIME,
        )
        projection = ((1, 0, 1), (0, 1, 1))
        self.assertEqual(
            sum(value != 0 for row in projection for value in row),
            4,
        )

        result = compress_state(state, projection)

        self.assertEqual(
            result.compressed_state.lane_coefficients,
            ((0, 0), (1, 0), (0, 1)),
        )
        self.assertEqual(result.online_product_count, 2)
        self.assertEqual(result.key_component_count, 2)

    def test_rank_two_exact_span_projection_preserves_every_lane_phase(self):
        state = MaskSpanState(
            lane_coefficients=(
                (0, 0, 0),
                (1, 0, 1),
                (0, 1, 1),
                (2, 3, 5),
            ),
            body_constants=(11, 13, 17, 19),
            mask_symbols=(5, 7, 11),
            provenance=("alpha", "beta", "gamma"),
            modulus=PRIME,
        )
        projection = ((1, 0, 1), (0, 1, 1))
        result = compress_state(state, projection)

        self.assertTrue(result.phase_preserved)
        self.assertEqual(result.discarded_directions, 1)
        self.assertEqual(result.online_product_count, 4)
        self.assertEqual(result.key_component_count, 2)
        self.assertEqual(
            result.compressed_state.lane_coefficients,
            ((0, 0), (1, 0), (0, 1), (2, 3)),
        )
        self.assertEqual(result.compressed_state.mask_symbols, (16, 18))
        self.assertEqual(excess_rank(result.compressed_state), 2)
        self.assertEqual(
            phase_vector(
                result.compressed_state,
                (2, 3, 5, 7),
                PRIME,
            ),
            phase_vector(state, (2, 3, 5, 7), PRIME),
        )

    def test_projection_cannot_discard_a_phase_active_direction(self):
        state = state_with_two_symbols()
        with self.assertRaisesRegex(ValueError, "phase-active"):
            compress_state(state, ((1, 0),))


class ScheduleStepTests(unittest.TestCase):
    def test_schedule_step_dispatches_public_rank_and_rotation_operations(self):
        appended = schedule_step(
            shared_state(3, PRIME),
            {
                "operation": "append_mask_directions",
                "lane_coefficients": ((0,), (1,), (2,)),
            },
        )
        self.assertEqual(excess_rank(appended), 1)

        rotated = schedule_step(
            appended,
            {"operation": "rotate", "exponent": 3},
        )
        self.assertEqual(
            phase_vector(rotated, (2, 3, 5), PRIME),
            tuple(
                -value % PRIME
                for value in phase_vector(appended, (2, 3, 5), PRIME)
            ),
        )

    def test_schedule_step_rejects_unknown_operations(self):
        with self.assertRaisesRegex(ValueError, "unknown schedule operation"):
            schedule_step(
                shared_state(2, PRIME),
                {"operation": "secret_projection"},
            )


if __name__ == "__main__":
    unittest.main()
