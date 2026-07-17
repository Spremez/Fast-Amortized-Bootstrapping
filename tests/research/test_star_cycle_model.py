import unittest
from pathlib import Path

from research.mat_sab.star_cycle_model import (
    analyze_support,
    dense_support,
    matmul,
    phase_matrix,
    phase_residual,
    selector_from_kernel,
    star_cycle_support,
    support_from_stage203,
)


ROOT = Path(__file__).resolve().parents[2]
PRIME = 257
SECRETS = {
    2: (2, 3),
    4: (2, 3, 5, 7),
    6: (2, 3, 5, 7, 11, 13),
}


class StarCycleModelTests(unittest.TestCase):
    def test_dense_selector_has_one_randomizer_per_input_column(self):
        for r, secret in SECRETS.items():
            analysis = analyze_support(secret, 1, dense_support(r), PRIME)
            self.assertTrue(analysis.consistent)
            self.assertEqual(analysis.affine_dimension, r + 1)
            self.assertEqual(analysis.column_dimensions, (1,) * (r + 1))
            self.assertTrue(analysis.full_pvw_randomization)

    def test_kernel_construction_satisfies_phase_equation(self):
        secret = SECRETS[4]
        matrix = selector_from_kernel(secret, 7, (1, 2, 3, 4, 5), PRIME)
        self.assertEqual(phase_residual(secret, matrix, 7, PRIME), [[0] * 5 for _ in range(4)])
        self.assertEqual(len(matmul(phase_matrix(secret, PRIME), matrix, PRIME)), 4)

    def test_star_cycle_support_matches_stage203_and_has_4r_terms(self):
        path = ROOT / "repro/stage203_production_selector_equation_probe/equation_map.csv"
        for r in SECRETS:
            expected = star_cycle_support(r)
            self.assertEqual(len(expected), 4 * r)
            self.assertEqual(support_from_stage203(path, r), expected)
            self.assertEqual((r + 1) ** 2 - len(expected), (r - 1) ** 2)

    def test_star_cycle_loses_standard_pvw_randomization(self):
        expected_dimensions = {
            2: (0, 1, 1),
            4: (0, 0, 0, 0, 0),
            6: (0, 0, 0, 0, 0, 0, 0),
        }
        for r, secret in SECRETS.items():
            for mu in (0, 1):
                analysis = analyze_support(secret, mu, star_cycle_support(r), PRIME)
                self.assertTrue(analysis.consistent)
                self.assertEqual(analysis.column_dimensions, expected_dimensions[r])
                self.assertFalse(analysis.full_pvw_randomization)
                self.assertEqual(
                    phase_residual(secret, analysis.particular_matrix, mu, PRIME),
                    [[0] * (r + 1) for _ in range(r)],
                )

    def test_generic_dense_randomizer_is_not_star_representable(self):
        secret = SECRETS[4]
        matrix = selector_from_kernel(secret, 1, (1, 2, 3, 4, 5), PRIME)
        outside = [
            matrix[row][column]
            for row in range(5)
            for column in range(5)
            if (row, column) not in star_cycle_support(4)
        ]
        self.assertTrue(all(value != 0 for value in outside))


if __name__ == "__main__":
    unittest.main()
