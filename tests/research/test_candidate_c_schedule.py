import shutil
import tempfile
import unittest
from pathlib import Path

from research.mat_sab.candidate_c_schedule import (
    ScheduleTrace,
    ScheduleInconclusiveError,
    load_binary_target_schedule,
    replay_variant_schedule,
)
from research.mat_sab.rank_bounded_state_model import (
    append_mask_directions as canonical_append_mask_directions,
)
import research.mat_sab.candidate_c_schedule as candidate_c_schedule


ROOT = Path(__file__).resolve().parents[2]


class BinaryTargetScheduleParsingTests(unittest.TestCase):
    def test_default_selector_count_is_derived_from_target_and_control_flow(self):
        schedule = load_binary_target_schedule(ROOT)

        self.assertEqual(schedule.target, "SET_2_3_2048")
        self.assertEqual(schedule.h, 39)
        self.assertEqual(schedule.r_prec, 7)
        self.assertEqual(schedule.in_N, 2048)
        self.assertEqual(schedule.monomial_calls, schedule.h + 1)
        self.assertEqual(schedule.monomial_calls, 40)
        self.assertEqual(
            schedule.butterfly_steps,
            schedule.monomial_calls * schedule.r_prec,
        )
        self.assertEqual(
            schedule.selector_applications,
            schedule.butterfly_steps * schedule.in_N,
        )
        self.assertEqual(schedule.selector_applications, 573440)

    def test_required_binary_source_anchors_are_recorded(self):
        schedule = load_binary_target_schedule(ROOT)

        self.assertEqual(
            schedule.source_anchors,
            (
                ("main.c", "sab_pvw_target_params"),
                (
                    "src/sparse_amortized_bootstrap.c",
                    "RGSW_monomial_mul",
                ),
                (
                    "src/sparse_amortized_bootstrap.c",
                    "sparse_mul",
                ),
                ("src/sab_pvw.c", "sab_pvw_RGSW_monomial_mul_state"),
                ("src/sab_pvw.c", "sab_pvw_sparse_mul_binary"),
                ("src/sab_pvw.c", "sab_pvw_sub_a_binary_to"),
            ),
        )

    def test_target_parameter_changes_are_derived_not_hard_coded(self):
        old = (
            "return (SAB_PVW_Target_Params)"
            "{2048, 1, 2048, 1, 1, 23, 3, 39, 7,"
        )
        new = (
            "return (SAB_PVW_Target_Params)"
            "{2048, 1, 2048, 1, 1, 23, 3, 40, 7,"
        )
        with self._mutated_root("main.c", old, new) as root:
            schedule = load_binary_target_schedule(root)

        self.assertEqual(schedule.h, 40)
        self.assertEqual(schedule.monomial_calls, 41)
        self.assertEqual(
            schedule.selector_applications,
            41 * schedule.r_prec * schedule.in_N,
        )

    def test_changed_target_shape_is_inconclusive(self):
        with self._mutated_root(
            "main.c",
            "  int r_prec;\n",
            "",
        ) as root:
            with self.assertRaisesRegex(
                ScheduleInconclusiveError,
                "field/initializer length mismatch",
            ):
                load_binary_target_schedule(root)

    def test_missing_binary_schedule_branch_is_inconclusive(self):
        with self._mutated_root(
            "src/sab_pvw.c",
            "void sab_pvw_sparse_mul_binary(",
            "void sab_pvw_sparse_mul_binary_removed(",
        ) as root:
            with self.assertRaisesRegex(
                ScheduleInconclusiveError,
                "sab_pvw_sparse_mul_binary",
            ):
                load_binary_target_schedule(root)

    def test_missing_scalar_schedule_branch_is_inconclusive(self):
        with self._mutated_root(
            "src/sparse_amortized_bootstrap.c",
            "void sparse_mul(",
            "void sparse_mul_removed(",
        ) as root:
            with self.assertRaisesRegex(
                ScheduleInconclusiveError,
                "sparse_mul",
            ):
                load_binary_target_schedule(root)

    def test_changed_butterfly_loop_shape_is_inconclusive(self):
        with self._mutated_root(
            "src/sab_pvw.c",
            (
                "const uint32_t r_prec = sab->r_prec, in_N = sab->in_N;\n"
                "  for (size_t bit = 0; bit < r_prec; bit++){"
            ),
            (
                "const uint32_t r_prec = sab->r_prec, in_N = sab->in_N;\n"
                "  for (size_t bit = 1; bit < r_prec; bit++){"
            ),
        ) as root:
            with self.assertRaisesRegex(
                ScheduleInconclusiveError,
                "source shape changed",
            ):
                load_binary_target_schedule(root)

    def _mutated_root(self, relative_path, old, new):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for source_path in (
            Path("main.c"),
            Path("src/sparse_amortized_bootstrap.c"),
            Path("src/sab_pvw.c"),
            Path(
                "repro/stage203_production_selector_equation_probe/"
                "equation_map.csv"
            ),
        ):
            destination = root / source_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / source_path, destination)
        path = root / relative_path
        source = path.read_text(encoding="utf-8")
        self.assertIn(old, source)
        path.write_text(source.replace(old, new, 1), encoding="utf-8")

        class TemporaryRoot:
            def __enter__(self):
                return root

            def __exit__(self, *_):
                temporary.cleanup()

        return TemporaryRoot()


class NegativeControlReplayTests(unittest.TestCase):
    def test_c0_reaches_full_nonreference_lane_rank(self):
        for r in (4, 6):
            with self.subTest(r=r):
                trace = replay_variant_schedule("C0", r, 257)

                self.assertIsInstance(trace, ScheduleTrace)
                self.assertEqual(trace.max_rho, r - 1)
                self.assertEqual(trace.rho_bound, min(2, r - 1))
                self.assertEqual(trace.completed_butterflies, 1)
                self.assertEqual(trace.closure_gate, "REJECT_EXPECTED")
                self.assertEqual(
                    trace.phase_gate,
                    "NOT_APPLICABLE_NEGATIVE_CONTROL",
                )

    def test_replay_imports_the_canonical_direction_algebra(self):
        self.assertIs(
            candidate_c_schedule.append_mask_directions,
            canonical_append_mask_directions,
        )


class EvidenceDerivedC1ReplayTests(unittest.TestCase):
    def test_c1_uses_corrected_rank_target_at_r2(self):
        schedule = load_binary_target_schedule(ROOT)
        trace = replay_variant_schedule("C1", 2, 257)

        self.assertEqual(trace.rho_bound, 1)
        self.assertEqual(trace.max_rho, 1)
        self.assertIsNone(trace.first_rank_overflow)
        self.assertIsNone(trace.first_missing_edge)
        self.assertEqual(
            trace.completed_butterflies,
            trace.selector_applications,
        )
        self.assertEqual(trace.closure_gate, "PASS_FINITE_CLOSURE")
        self.assertEqual(
            trace.phase_gate,
            "INCONCLUSIVE_MISSING_OPERATOR_MAPPING",
        )
        self.assertEqual(
            trace.selector_boundaries_checked,
            schedule.selector_applications,
        )
        self.assertEqual(trace.monomial_boundaries_checked, schedule.h + 1)
        self.assertEqual(trace.sub_a_boundaries_checked, schedule.h)

    def test_c1_names_first_cycle_edge_outside_every_rank_two_prefix(self):
        for r in (4, 6):
            with self.subTest(r=r):
                trace = replay_variant_schedule("C1", r, 257)

                self.assertEqual(trace.rho_bound, 2)
                self.assertEqual(trace.max_rho, r - 1)
                self.assertEqual(trace.first_rank_overflow, 1)
                self.assertEqual(
                    trace.first_missing_edge,
                    (
                        "lane_neighbor_body_interaction:"
                        "row=3,col=4;butterfly=NCMUX:bit=0,j=0"
                    ),
                )
                self.assertEqual(trace.completed_butterflies, 0)
                self.assertEqual(
                    trace.closure_gate,
                    "FAIL_MINIMUM_CYCLE_RANK",
                )
                self.assertEqual(
                    trace.phase_gate,
                    "INCONCLUSIVE_MISSING_OPERATOR_MAPPING",
                )
                self.assertEqual(trace.selector_boundaries_checked, 1)
                self.assertEqual(trace.monomial_boundaries_checked, 0)
                self.assertEqual(trace.sub_a_boundaries_checked, 0)

    def test_missing_stage203_cycle_edge_is_inconclusive(self):
        edge = (
            "4,3,4,lane_neighbor_body_interaction,active,1,0\n"
        )
        with BinaryTargetScheduleParsingTests()._mutated_root(
            (
                "repro/stage203_production_selector_equation_probe/"
                "equation_map.csv"
            ),
            edge,
            "",
        ) as root:
            with self.assertRaisesRegex(
                ScheduleInconclusiveError,
                "equation map shape changed",
            ):
                replay_variant_schedule("C1", 4, 257, root=root)


class PeriodicCompressionC2ReplayTests(unittest.TestCase):
    BLOCK_LENGTHS = (1, 2, 4, 8, 16, 32, 64)

    def test_c2_sweeps_every_required_block_and_lane_count(self):
        traces = {
            (r, block_length): replay_variant_schedule(
                "C2",
                r,
                257,
                block_length=block_length,
            )
            for r in (2, 4, 6)
            for block_length in self.BLOCK_LENGTHS
        }

        self.assertEqual(len(traces), 21)
        for (r, block_length), trace in traces.items():
            with self.subTest(r=r, block_length=block_length):
                self.assertEqual(
                    trace.steps_before_compression,
                    block_length,
                )
                self.assertEqual(trace.max_rho, r - 1)
                self.assertEqual(
                    trace.phase_gate,
                    "INCONCLUSIVE_MISSING_OPERATOR_MAPPING",
                )
                if block_length == 1:
                    self.assertEqual(trace.compressions, 1)
                    self.assertEqual(trace.completed_butterflies, 1)
                    self.assertEqual(
                        trace.boundary_gate,
                        "REJECT_PER_CMUX_CONTROL",
                    )
                    self.assertEqual(
                        trace.closure_gate,
                        "REJECT_FORBIDDEN_BOUNDARY",
                    )
                elif r == 2:
                    self.assertIsNone(trace.first_rank_overflow)
                    self.assertEqual(
                        trace.compressions,
                        trace.selector_applications // block_length,
                    )
                    self.assertEqual(
                        trace.completed_butterflies,
                        trace.selector_applications,
                    )
                    self.assertEqual(trace.boundary_gate, "PASS")
                    self.assertEqual(
                        trace.closure_gate,
                        "PASS_FINITE_CLOSURE",
                    )
                else:
                    self.assertEqual(trace.first_rank_overflow, 1)
                    self.assertEqual(trace.compressions, 1)
                    self.assertEqual(
                        trace.completed_butterflies,
                        block_length,
                    )
                    self.assertEqual(trace.boundary_gate, "PASS")
                    self.assertEqual(
                        trace.closure_gate,
                        "FAIL_MINIMUM_CYCLE_RANK",
                    )

    def test_c2_requires_a_registered_public_block_length(self):
        with self.assertRaisesRegex(ValueError, "block length"):
            replay_variant_schedule("C2", 4, 257)
        with self.assertRaisesRegex(ValueError, "block length"):
            replay_variant_schedule("C2", 4, 257, block_length=3)


class ScheduleMutationControlTests(unittest.TestCase):
    def test_cycle_coefficient_mutation_fails_closure_only(self):
        trace = replay_variant_schedule(
            "C1",
            2,
            257,
            mutation="cycle_coefficient",
        )

        self.assertEqual(trace.closure_gate, "FAIL_CYCLE_COEFFICIENT")
        self.assertEqual(trace.boundary_gate, "NOT_APPLICABLE")
        self.assertEqual(trace.provenance_gate, "PASS")

    def test_compression_boundary_mutation_fails_boundary_only(self):
        trace = replay_variant_schedule(
            "C2",
            2,
            257,
            block_length=4,
            mutation="compression_boundary",
        )

        self.assertEqual(
            trace.boundary_gate,
            "FAIL_MUTATED_COMPRESSION_BOUNDARY",
        )
        self.assertEqual(
            trace.closure_gate,
            "INCONCLUSIVE_AFTER_BOUNDARY_FAILURE",
        )
        self.assertEqual(trace.provenance_gate, "PASS")

    def test_provenance_identifier_mutation_fails_provenance_only(self):
        trace = replay_variant_schedule(
            "C1",
            2,
            257,
            mutation="provenance_identifier",
        )

        self.assertEqual(
            trace.provenance_gate,
            "FAIL_MUTATED_PROVENANCE",
        )
        self.assertEqual(trace.phase_gate, "FAIL_PROVENANCE_IDENTITY")
        self.assertEqual(
            trace.closure_gate,
            "INCONCLUSIVE_AFTER_PROVENANCE_FAILURE",
        )
        self.assertEqual(trace.boundary_gate, "NOT_APPLICABLE")


if __name__ == "__main__":
    unittest.main()
