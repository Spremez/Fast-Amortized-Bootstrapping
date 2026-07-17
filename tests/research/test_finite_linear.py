import unittest

from research.mat_sab.finite_linear import rank, rref, solve_affine


class FiniteLinearTests(unittest.TestCase):
    def test_rref_and_rank_over_prime_field(self):
        reduced, pivots = rref([[1, 2, 3], [2, 4, 7]], 257)
        self.assertEqual(pivots, [0, 2])
        self.assertEqual(reduced, [[1, 2, 0], [0, 0, 1]])
        self.assertEqual(rank([[1, 2], [2, 4]], 257), 1)

    def test_affine_solution_reports_dimension_and_particular(self):
        solution = solve_affine([[1, 1, 0], [0, 1, 1]], [3, 5], 257)
        self.assertTrue(solution.consistent)
        self.assertEqual(solution.rank, 2)
        self.assertEqual(solution.dimension, 1)
        self.assertEqual(solution.particular, (255, 5, 0))

    def test_inconsistent_system_is_detected(self):
        solution = solve_affine([[1], [1]], [0, 1], 257)
        self.assertFalse(solution.consistent)
        self.assertEqual(solution.dimension, -1)
        self.assertEqual(solution.particular, ())


if __name__ == "__main__":
    unittest.main()
