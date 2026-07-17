import unittest

from research.mat_sab.factorized_selector_model import (
    constant_error_homomorphic_image,
    expected_phase,
    external_product,
    factor_cost,
    full_rank_homomorphic_image,
    homomorphic_image_fits_inner_dimension,
    homomorphic_image_rank,
    low_rank_homomorphic_image_control,
    phase,
    standard_selector,
    torus_normal_from_uniform_pair,
)


PRIME = 257


def deterministic_inputs(r):
    size = r + 1
    secret = tuple((index + 2) for index in range(r))
    masks = tuple((2 * index + 5) for index in range(size))
    digits = tuple((3 * index + 7) for index in range(size))
    errors = tuple(
        tuple((row + 1) * (column + 2) for column in range(r))
        for row in range(size)
    )
    return secret, masks, digits, errors


class FactorizedSelectorModelTests(unittest.TestCase):
    def test_hand_derived_r2_oracle_fixes_orientation_and_sign(self):
        secret = (2, 3)
        masks = (5, 7, 11)
        digits = (7, 10, 13)
        errors = ((2, 3), (4, 6), (6, 9))
        selector = standard_selector(
            secret,
            1,
            masks,
            errors,
            PRIME,
            gadget=3,
        )
        self.assertEqual(
            selector,
            (
                (8, 12, 18),
                (7, 21, 27),
                (11, 28, 45),
            ),
        )
        output = external_product(digits, selector, PRIME)
        self.assertEqual(output, (12, 144, 210))
        self.assertEqual(phase(output, secret, PRIME), (120, 174))
        self.assertEqual(
            expected_phase(
                digits,
                errors,
                secret,
                1,
                PRIME,
                gadget=3,
            ),
            (120, 174),
        )

    def test_standard_selector_phase_identity_covers_target_r_and_selector_bits(self):
        for r in (2, 4, 6):
            secret, masks, digits, errors = deterministic_inputs(r)
            for mu in (0, 1):
                with self.subTest(r=r, mu=mu):
                    selector = standard_selector(
                        secret,
                        mu,
                        masks,
                        errors,
                        PRIME,
                        gadget=3,
                    )
                    output = external_product(digits, selector, PRIME)
                    self.assertEqual(
                        phase(output, secret, PRIME),
                        expected_phase(
                            digits,
                            errors,
                            secret,
                            mu,
                            PRIME,
                            gadget=3,
                        ),
                    )

    def test_error_mutation_changes_exactly_the_expected_phase_lane(self):
        r = 4
        secret, masks, digits, errors = deterministic_inputs(r)
        before = expected_phase(
            digits,
            errors,
            secret,
            1,
            PRIME,
        )
        changed = [list(row) for row in errors]
        changed[0][2] = (changed[0][2] + 1) % PRIME
        after = expected_phase(
            digits,
            changed,
            secret,
            1,
            PRIME,
        )
        delta = tuple((right - left) % PRIME for left, right in zip(before, after))
        self.assertEqual(delta, (0, 0, digits[0] % PRIME, 0))
        changed_selector = standard_selector(
            secret,
            1,
            masks,
            changed,
            PRIME,
        )
        changed_output = external_product(digits, changed_selector, PRIME)
        self.assertEqual(phase(changed_output, secret, PRIME), after)

    def test_full_rank_homomorphic_image_rejects_every_q_below_r(self):
        for r in (2, 4, 6):
            image = full_rank_homomorphic_image(r)
            self.assertEqual(homomorphic_image_rank(image), r)
            for q in range(1, r):
                with self.subTest(r=r, q=q):
                    self.assertFalse(
                        homomorphic_image_fits_inner_dimension(image, q)
                    )

    def test_constructed_low_rank_image_controls_are_admitted_at_exact_rank(self):
        for r in (2, 4, 6):
            for q in range(1, r):
                image = low_rank_homomorphic_image_control(r, q)
                with self.subTest(r=r, q=q):
                    self.assertEqual(homomorphic_image_rank(image), q)
                    self.assertTrue(
                        homomorphic_image_fits_inner_dimension(image, q)
                    )
                    if q > 1:
                        self.assertFalse(
                            homomorphic_image_fits_inner_dimension(
                                image,
                                q - 1,
                            )
                        )

    def test_parity_evaluation_is_a_multiplicative_ring_image_not_raw_coefficient(self):
        # phi(f) is the parity of the sum of coefficients, i.e. f(1) mod 2.
        polynomials = (
            (
                (1, 2, 3),
                (2, 2),
            ),
            (
                (0, 0, 5),
                (7,),
            ),
        )
        self.assertEqual(
            constant_error_homomorphic_image(polynomials),
            ((0, 0), (1, 1)),
        )

    def test_current_sampler_formula_has_explicit_even_and_odd_support_witnesses(self):
        sigma = 2 ** -50
        even = torus_normal_from_uniform_pair(
            0x9E3779B97F4A7C15,
            0xA36A9465A325DA06,
            sigma,
        )
        odd = torus_normal_from_uniform_pair(
            0x3C6EF372FE94F82A,
            0x751FDE9874B8C709,
            sigma,
        )
        self.assertEqual(even, -11446)
        self.assertEqual(odd, 1791)
        self.assertEqual(even % 2, 0)
        self.assertEqual(odd % 2, 1)

    def test_cost_counts_polynomial_components_not_vector_objects(self):
        for r in (2, 4, 6):
            full_rank = factor_cost(r, r)
            size = r + 1
            self.assertEqual(full_rank.dense_products, size * size)
            self.assertEqual(full_rank.generic_left_products, size * r)
            self.assertEqual(full_rank.generic_right_products, r * r)
            self.assertEqual(full_rank.separate_diagonal_products, size)
            self.assertGreaterEqual(
                full_rank.generic_dense_factor_products,
                full_rank.dense_products,
            )
            self.assertFalse(full_rank.generic_dense_factor_beats_dense)
            self.assertEqual(
                full_rank.retained_dense_error_products,
                size * r,
            )
            self.assertTrue(full_rank.retained_dense_error_is_quadratic)

    def test_shape_and_parameter_errors_are_rejected(self):
        secret, masks, digits, errors = deterministic_inputs(2)
        bad_calls = (
            lambda: standard_selector(
                secret,
                1,
                masks[:-1],
                errors,
                PRIME,
            ),
            lambda: standard_selector(
                secret,
                1,
                masks,
                errors[:-1],
                PRIME,
            ),
            lambda: standard_selector(
                secret,
                1,
                masks,
                (errors[0][:-1],) + errors[1:],
                PRIME,
            ),
            lambda: external_product(digits, [[1, 0], [0, 1]], PRIME),
            lambda: phase((1, 2), secret, PRIME),
            lambda: expected_phase(
                digits[:-1],
                errors,
                secret,
                1,
                PRIME,
            ),
            lambda: full_rank_homomorphic_image(0),
            lambda: low_rank_homomorphic_image_control(2, 0),
            lambda: low_rank_homomorphic_image_control(2, 2),
            lambda: homomorphic_image_fits_inner_dimension(
                full_rank_homomorphic_image(2),
                -1,
            ),
            lambda: homomorphic_image_rank(((1,),), modulus=4),
            lambda: constant_error_homomorphic_image(()),
            lambda: torus_normal_from_uniform_pair(0, 0, 2 ** -50),
            lambda: torus_normal_from_uniform_pair(0, 1, 0),
            lambda: factor_cost(0, 1),
            lambda: factor_cost(2, -1),
        )
        for call in bad_calls:
            with self.subTest(call=call):
                with self.assertRaises(ValueError):
                    call()


if __name__ == "__main__":
    unittest.main()
