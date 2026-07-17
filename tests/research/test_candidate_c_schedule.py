import shutil
import tempfile
import unittest
from collections import Counter, deque
from pathlib import Path
from unittest.mock import patch

import research.mat_sab.candidate_c_schedule as candidate_c_schedule
from research.mat_sab.candidate_c_schedule import (
    ScheduleInconclusiveError,
    iter_binary_schedule_events,
    load_binary_target_schedule,
    replay_variant_schedule,
)
from research.mat_sab.rank_bounded_state_model import (
    append_mask_directions as canonical_append_mask_directions,
)
from research.mat_sab.rank_bounded_state_model import (
    linear_combine_states as canonical_linear_combine_states,
)


ROOT = Path(__file__).resolve().parents[2]
INCONCLUSIVE = "INCONCLUSIVE_MISSING_NUMERIC_OPERATOR_MAPPING"


class MutatedRoot:
    def __init__(self, relative_path, old, new):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        for source_path in (
            Path("main.c"),
            Path("src/sparse_amortized_bootstrap.c"),
            Path("src/sab_pvw.c"),
            Path("src/mosfhet/Makefile.def"),
            Path(
                "repro/stage203_production_selector_equation_probe/"
                "equation_map.csv"
            ),
        ):
            destination = self.root / source_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / source_path, destination)
        path = self.root / relative_path
        source = path.read_text(encoding="utf-8")
        if old not in source:
            raise AssertionError(f"mutation anchor not found: {old!r}")
        path.write_text(source.replace(old, new, 1), encoding="utf-8")

    def __enter__(self):
        return self.root

    def __exit__(self, *_):
        self.temporary.cleanup()


class BinaryTargetScheduleParsingTests(unittest.TestCase):
    def test_default_parameters_and_counts_are_source_derived(self):
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
        self.assertEqual(schedule.butterfly_steps, 280)
        self.assertEqual(
            schedule.selector_applications,
            schedule.butterfly_steps * schedule.in_N,
        )
        self.assertEqual(schedule.selector_applications, 573440)
        self.assertFalse(schedule.dual_sub_enabled)

    def test_target_parameter_change_is_not_hard_coded(self):
        old = (
            "return (SAB_PVW_Target_Params)"
            "{2048, 1, 2048, 1, 1, 23, 3, 39, 7,"
        )
        new = (
            "return (SAB_PVW_Target_Params)"
            "{2048, 1, 2048, 1, 1, 23, 3, 40, 7,"
        )
        with MutatedRoot("main.c", old, new) as root:
            schedule = load_binary_target_schedule(root)

        self.assertEqual(schedule.h, 40)
        self.assertEqual(schedule.monomial_calls, 41)
        self.assertEqual(
            schedule.selector_applications,
            41 * schedule.r_prec * schedule.in_N,
        )

    def test_changed_target_shape_is_inconclusive(self):
        with MutatedRoot("main.c", "  int r_prec;\n", "") as root:
            with self.assertRaisesRegex(
                ScheduleInconclusiveError,
                "field/initializer length mismatch",
            ):
                load_binary_target_schedule(root)

    def test_reordered_sparse_calls_are_inconclusive_even_when_tokens_remain(self):
        old = (
            "    sab_pvw_RGSW_monomial_mul(p, sab->s[a_idx][step], sab);\n"
            "    sab_pvw_sub_a_binary(p, a, sab);"
        )
        new = (
            "    sab_pvw_sub_a_binary(p, a, sab);\n"
            "    sab_pvw_RGSW_monomial_mul(p, sab->s[a_idx][step], sab);"
        )
        with MutatedRoot("src/sab_pvw.c", old, new) as root:
            with self.assertRaisesRegex(
                ScheduleInconclusiveError,
                "ordered monomial/sub_a",
            ):
                load_binary_target_schedule(root)

    def test_nonnested_wrap_call_is_inconclusive_when_token_remains(self):
        old = (
            "      for (size_t j = 0; j < power; j++){\n"
            "        NCMUX(p[out][j], p[in][j], "
            "p[in][in_N - power + j], e[i], sab);\n"
            "      }"
        )
        new = (
            "      NCMUX(p[out][0], p[in][0], "
            "p[in][in_N - power], e[i], sab);\n"
            "      for (size_t j = 0; j < power; j++){\n"
            "        trlwe_copy(p[out][j], p[in][j]);\n"
            "      }"
        )
        with MutatedRoot(
            "src/sparse_amortized_bootstrap.c",
            old,
            new,
        ) as root:
            with self.assertRaisesRegex(
                ScheduleInconclusiveError,
                "wrap loop",
            ):
                load_binary_target_schedule(root)

    def test_changed_direct_loop_association_is_inconclusive(self):
        old = (
            "    for (size_t j = direct_start; j < in_N - power; j++){\n"
            "#ifdef SAB_PVW_SCHEDULE_FUSED_CMUX\n"
            "      sab_pvw_schedule_CMUX(p[out][j + power], "
            "p[in][j + power], p[in][j],\n"
            "          e[bit], sab);"
        )
        new = (
            "    sab_pvw_schedule_CMUX(p[out][power], "
            "p[in][power], p[in][0], e[bit], sab);\n"
            "    for (size_t j = direct_start; j < in_N - power; j++){\n"
            "#ifdef SAB_PVW_SCHEDULE_FUSED_CMUX\n"
            "      pvmtmlwe_copy(p[out][j + power], p[in][j + power]);"
        )
        with MutatedRoot("src/sab_pvw.c", old, new) as root:
            with self.assertRaisesRegex(
                ScheduleInconclusiveError,
                "direct loop",
            ):
                load_binary_target_schedule(root)


class StreamingScheduleEventTests(unittest.TestCase):
    def test_default_generator_traverses_every_exact_schedule_event(self):
        schedule = load_binary_target_schedule(ROOT)
        counts = Counter()
        last_events = deque(maxlen=2)
        first_event = None

        for event in iter_binary_schedule_events(schedule):
            if first_event is None:
                first_event = event
            counts[event.kind] += 1
            last_events.append(event)

        self.assertEqual(first_event.kind, "ncmux")
        self.assertEqual(first_event.monomial, 0)
        self.assertEqual(first_event.bit, 0)
        self.assertEqual(first_event.index, 0)
        self.assertEqual(counts["ncmux"], 5080)
        self.assertEqual(counts["cmux"], 568360)
        self.assertEqual(
            counts["ncmux"] + counts["cmux"],
            schedule.selector_applications,
        )
        self.assertEqual(counts["butterfly_boundary"], 280)
        self.assertEqual(counts["monomial_boundary"], 40)
        self.assertEqual(counts["sub_a_boundary"], 39)
        self.assertEqual(
            sum(counts.values()),
            573440 + 280 + 40 + 39,
        )
        self.assertEqual(last_events[-1].kind, "monomial_boundary")
        self.assertEqual(last_events[-1].monomial, 39)

    def test_dual_sub_branch_streams_two_selectors_per_pair(self):
        schedule = load_binary_target_schedule(ROOT)
        counts = Counter(
            (event.kind, event.branch)
            for event in iter_binary_schedule_events(
                schedule,
                dual_sub_enabled=True,
            )
        )

        self.assertEqual(counts[("ncmux", "dual_sub_pair")], 5080)
        self.assertEqual(counts[("cmux", "dual_sub_pair")], 5080)
        selector_count = sum(
            count
            for (kind, _), count in counts.items()
            if kind in {"ncmux", "cmux"}
        )
        self.assertEqual(selector_count, schedule.selector_applications)

    def test_replay_consumes_the_generator_instead_of_assigning_counts(self):
        schedule = load_binary_target_schedule(ROOT)
        real_generator = candidate_c_schedule.iter_binary_schedule_events
        traversed = Counter()

        def observed_generator(*args, **kwargs):
            for event in real_generator(*args, **kwargs):
                traversed[event.kind] += 1
                yield event

        with patch.object(
            candidate_c_schedule,
            "iter_binary_schedule_events",
            side_effect=observed_generator,
        ):
            trace = replay_variant_schedule("C1", 4, 257)

        self.assertEqual(
            traversed["ncmux"] + traversed["cmux"],
            schedule.selector_applications,
        )
        self.assertEqual(traversed["monomial_boundary"], 40)
        self.assertEqual(traversed["sub_a_boundary"], 39)
        self.assertEqual(trace.selector_boundaries_checked, 573440)


class CandidateGateReplayTests(unittest.TestCase):
    def assert_full_schedule_traversed(self, trace):
        self.assertEqual(trace.selector_boundaries_checked, 573440)
        self.assertEqual(trace.ncmux_events_checked, 5080)
        self.assertEqual(trace.cmux_events_checked, 568360)
        self.assertEqual(trace.butterfly_boundaries_checked, 280)
        self.assertEqual(trace.monomial_boundaries_checked, 40)
        self.assertEqual(trace.sub_a_boundaries_checked, 39)
        self.assertEqual(trace.completed_butterflies, 573440)

    def test_c0_remains_an_explicit_rejecting_negative_control(self):
        for r in (4, 6):
            with self.subTest(r=r):
                trace = replay_variant_schedule("C0", r, 257)

                self.assertEqual(trace.max_rho, r - 1)
                self.assertEqual(trace.closure_gate, "REJECT_EXPECTED")
                self.assert_full_schedule_traversed(trace)

    def test_c1_has_no_operator_dependent_rank_or_closure_conclusion(self):
        for r in (2, 4, 6):
            with self.subTest(r=r):
                trace = replay_variant_schedule("C1", r, 257)

                self.assertIsNone(trace.max_rho)
                self.assertIsNone(trace.first_rank_overflow)
                self.assertIsNone(trace.first_missing_edge)
                self.assertEqual(trace.closure_gate, INCONCLUSIVE)
                self.assertEqual(trace.phase_gate, INCONCLUSIVE)
                self.assertEqual(trace.operator_mapping_gate, INCONCLUSIVE)
                self.assertEqual(trace.compressions, 0)
                self.assert_full_schedule_traversed(trace)

    def test_code_contains_no_incidence_based_candidate_verdicts(self):
        source = (
            ROOT / "research/mat_sab/candidate_c_schedule.py"
        ).read_text(encoding="ascii")

        self.assertNotIn("_cycle_direction_matrix", source)
        self.assertNotIn("PASS_FINITE_CLOSURE", source)
        self.assertNotIn("FAIL_MINIMUM_CYCLE_RANK", source)


class PeriodicCompressionBoundaryTests(unittest.TestCase):
    BLOCK_LENGTHS = (1, 2, 4, 8, 16, 32, 64)

    def test_all_21_cases_stream_real_events_and_remain_inconclusive(self):
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
                self.assertEqual(trace.rho_bound, min(2, r - 1))
                self.assertIsNone(trace.max_rho)
                self.assertIsNone(trace.first_rank_overflow)
                self.assertEqual(trace.closure_gate, INCONCLUSIVE)
                self.assertEqual(trace.phase_gate, INCONCLUSIVE)
                self.assertEqual(trace.operator_mapping_gate, INCONCLUSIVE)
                self.assertEqual(trace.compressions, 0)
                self.assertEqual(
                    trace.compression_boundaries_checked,
                    573440 // block_length,
                )
                self.assertEqual(
                    trace.steps_before_compression,
                    block_length,
                )
                CandidateGateReplayTests().assert_full_schedule_traversed(
                    trace
                )
                if block_length == 1:
                    self.assertEqual(
                        trace.boundary_gate,
                        "REJECT_PER_CMUX_CONTROL",
                    )
                else:
                    self.assertEqual(
                        trace.boundary_gate,
                        "PASS_STRUCTURAL_BOUNDARIES",
                    )

    def test_c2_rejects_unregistered_block_lengths(self):
        for block_length in (None, 0, 3, 65):
            with self.subTest(block_length=block_length):
                with self.assertRaisesRegex(ValueError, "block length"):
                    replay_variant_schedule(
                        "C2",
                        4,
                        257,
                        block_length=block_length,
                    )


class ValidatorDrivenMutationTests(unittest.TestCase):
    def test_cycle_coefficient_mutation_fails_operator_mapping_gate(self):
        trace = replay_variant_schedule(
            "C1",
            4,
            257,
            mutation="cycle_coefficient",
        )

        self.assertEqual(
            trace.operator_mapping_gate,
            "FAIL_UNREGISTERED_CYCLE_COEFFICIENT_MUTATION",
        )
        self.assertEqual(trace.closure_gate, INCONCLUSIVE)
        self.assertEqual(trace.boundary_gate, "PASS_STRUCTURAL_SCHEDULE")

    def test_boundary_mutation_is_detected_at_the_real_event_position(self):
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
        self.assertEqual(trace.first_boundary_mismatch, 4)
        self.assertEqual(trace.closure_gate, INCONCLUSIVE)
        self.assertEqual(trace.selector_boundaries_checked, 573440)

    def test_provenance_mutation_hits_live_canonical_state_validation(self):
        trace = replay_variant_schedule(
            "C1",
            2,
            257,
            mutation="provenance_identifier",
        )

        self.assertEqual(
            trace.provenance_gate,
            "FAIL_MUTATED_PROVENANCE_AT_SELECTOR_1",
        )
        self.assertEqual(trace.closure_gate, INCONCLUSIVE)
        self.assertEqual(trace.selector_boundaries_checked, 573440)

    def test_replay_uses_task2_canonical_identity_operations(self):
        self.assertIs(
            candidate_c_schedule.append_mask_directions,
            canonical_append_mask_directions,
        )
        self.assertIs(
            candidate_c_schedule.linear_combine_states,
            canonical_linear_combine_states,
        )


if __name__ == "__main__":
    unittest.main()
