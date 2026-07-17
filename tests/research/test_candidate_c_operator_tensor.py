from __future__ import annotations

import math
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import research.mat_sab.candidate_c_operator_tensor as operator_tensor
from research.mat_sab.candidate_c_operator_tensor import (
    ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY,
    NO_RETAINED_MESSAGE_RELATION,
    REGISTERED_SHORT_ERROR_RELATION_FAIL,
    RELATION_RECORDED_NO_SECURITY_DECISION,
    REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
    EvaluatorCounts,
    SourceBindingError,
    audit_evaluator_sample_relations,
    build_dense_control_tensor,
    build_evaluator_sample_matrix,
    build_joint_rank_escape_control,
    build_phase_projection,
    build_rank_bounded_tensor,
    concatenated_mask_difference_rank,
    level_mask_difference_ranks,
    negacyclic_multiply,
    run_c1_operator_gate,
    verify_joint_rank_factorization,
    verify_operator_gate_result,
    verify_phase_identity,
)


ROOT = Path(__file__).resolve().parents[2]
PRIME = 257
N = 8
GADGET = (1, 16)


def secrets_for(r: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple((17 * (lane + 1) + 11 * coefficient + 3) % PRIME for coefficient in range(N))
        for lane in range(r)
    )


def public_lambda_for(r: int, rho: int) -> tuple[tuple[int, ...], ...]:
    if rho == 1:
        return ((1, 0), (1, 1))
    return tuple(
        (1, 0, 0) if lane == 0 else (1, lane, lane * lane % PRIME)
        for lane in range(r)
    )


class MutatedRoot:
    REQUIRED_PATHS = (
        "main.c",
        "src/sparse_amortized_bootstrap.c",
        "src/sab_pvw.c",
        "src/mosfhet/Makefile.def",
        "src/mosfhet/src/mattrgsw.c",
        "research/mat_sab/star_cycle_model.py",
        "research/mat_sab/candidate_c_schedule.py",
        "repro/stage203_production_selector_equation_probe/equation_map.csv",
        "repro/stage222_isolated_compact_ep_integration/proof_gate.csv",
        "repro/stage345_binary_matrix_synthesis/proof_gate.csv",
    )

    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        for relative in self.REQUIRED_PATHS:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)

    def replace(self, relative: str, old: str, new: str) -> None:
        path = self.root / relative
        source = path.read_text(encoding="utf-8")
        if old not in source:
            raise AssertionError(f"mutation token is absent from {relative}: {old!r}")
        path.write_text(source.replace(old, new, 1), encoding="utf-8")

    def close(self) -> None:
        self.temporary.cleanup()


class MissingEvidenceRoutingTests(unittest.TestCase):
    def test_missing_stage203_support_map_emits_typed_hash_bound_exhaustion(self):
        mutated = MutatedRoot()
        try:
            missing = (
                mutated.root
                / "repro/stage203_production_selector_equation_probe/"
                "equation_map.csv"
            )
            missing.unlink()
            first = run_c1_operator_gate(mutated.root, 4, PRIME)
            second = run_c1_operator_gate(mutated.root, 4, PRIME)
            verified = (
                operator_tensor.verify_task3a_evidence_exhaustion(
                    first,
                    mutated.root,
                )
            )
        finally:
            mutated.close()

        self.assertIsInstance(
            first,
            operator_tensor.Task3AEvidenceExhaustion,
        )
        self.assertEqual(
            first.condition,
            operator_tensor.MISSING_STAGE203_SUPPORT_MAP,
        )
        self.assertEqual(
            first.missing_path,
            "repro/stage203_production_selector_equation_probe/"
            "equation_map.csv",
        )
        self.assertEqual(
            first.decision,
            operator_tensor.TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED,
        )
        self.assertEqual(first, second)
        self.assertTrue(verified)
        self.assertRegex(first.missing_evidence_hash, r"^[0-9a-f]{64}$")
        self.assertRegex(first.record_hash, r"^[0-9a-f]{64}$")

    def test_other_missing_or_tampered_task3a_inputs_do_not_become_inconclusive(self):
        for relative in (
            "repro/stage222_isolated_compact_ep_integration/proof_gate.csv",
            "src/mosfhet/src/mattrgsw.c",
        ):
            mutated = MutatedRoot()
            try:
                (mutated.root / relative).unlink()
                with self.subTest(relative=relative):
                    with self.assertRaises((OSError, SourceBindingError)):
                        run_c1_operator_gate(mutated.root, 4, PRIME)
            finally:
                mutated.close()


class ExactRingAndPhaseProjectionTests(unittest.TestCase):
    def test_negacyclic_multiplication_wraps_x_to_the_eighth_as_minus_one(self):
        x = (0, 1, 0, 0, 0, 0, 0, 0)
        x_to_seven = (0, 0, 0, 0, 0, 0, 0, 1)
        self.assertEqual(
            negacyclic_multiply(x, x_to_seven, PRIME),
            (PRIME - 1, 0, 0, 0, 0, 0, 0, 0),
        )

    def test_phase_projection_uses_ordered_mask_then_body_inputs(self):
        secrets = secrets_for(4)
        public_lambda = public_lambda_for(4, 2)
        projection = build_phase_projection(public_lambda, secrets, 1, PRIME)

        self.assertEqual(projection.input_components, ("M_0", "M_1", "M_2", "B_0", "B_1", "B_2", "B_3"))
        self.assertEqual(projection.entries[2][1], tuple((-2 * value) % PRIME for value in secrets[2]))
        self.assertEqual(projection.entries[2][4], (0, 0, 0, 0, 0, 0, 0, 0))
        self.assertEqual(projection.entries[2][5], (1, 0, 0, 0, 0, 0, 0, 0))

    def test_exact_surrogate_rejects_wrong_ring_or_modulus(self):
        secrets = secrets_for(2)
        with self.assertRaisesRegex(ValueError, "n must equal 8"):
            build_rank_bounded_tensor(
                2, 1, 1, secrets, GADGET, 4, PRIME, public_lambda_for(2, 1)
            )
        with self.assertRaisesRegex(ValueError, "modulus must equal 257"):
            build_rank_bounded_tensor(
                2, 1, 1, secrets, GADGET, N, 263, public_lambda_for(2, 1)
            )


class ConcreteTensorPhaseTests(unittest.TestCase):
    def test_k0_and_k1_pass_every_phase_equation_for_all_registered_r(self):
        for r in (2, 4, 6):
            rho = min(2, r - 1)
            secrets = secrets_for(r)
            public_lambda = public_lambda_for(r, rho)
            for mu in (0, 1):
                with self.subTest(r=r, mu=mu):
                    tensor = build_rank_bounded_tensor(
                        r, rho, mu, secrets, GADGET, N, PRIME, public_lambda
                    )
                    projection = build_phase_projection(public_lambda, secrets, mu, PRIME)
                    self.assertEqual(tensor.mu, mu)
                    self.assertTrue(verify_phase_identity(tensor, projection))
                    self.assertTrue(
                        all(
                            len(polynomial) == N
                            for level in tensor.mask_polynomials
                            for basis in level
                            for polynomial in basis
                        )
                    )
                    self.assertTrue(
                        all(
                            len(polynomial) == N
                            for level in tensor.body_polynomials
                            for lane in level
                            for polynomial in lane
                        )
                    )

    def test_dense_positive_control_passes_and_one_body_coefficient_mutation_fails(self):
        secrets = secrets_for(4)
        dense = build_dense_control_tensor(4, 1, secrets, GADGET, N, PRIME)
        projection = build_phase_projection(dense.public_lambda, secrets, 1, PRIME)
        self.assertTrue(verify_phase_identity(dense, projection))

        bodies = [
            [list(component_polynomials) for component_polynomials in level]
            for level in dense.body_polynomials
        ]
        changed = list(bodies[0][2][1])
        changed[5] = (changed[5] + 1) % PRIME
        bodies[0][2][1] = tuple(changed)
        mutated = replace(
            dense,
            body_polynomials=tuple(
                tuple(tuple(lane) for lane in level)
                for level in bodies
            ),
        )
        self.assertFalse(verify_phase_identity(mutated, projection))

    def test_verifiers_reject_trailing_material_omitted_from_structural_counts(self):
        tensor = build_rank_bounded_tensor(
            4, 2, 1, secrets_for(4), GADGET, N, PRIME, public_lambda_for(4, 2)
        )
        projection = build_phase_projection(
            tensor.public_lambda, tensor.secrets, tensor.mu, PRIME
        )
        extra_body = replace(
            tensor,
            body_polynomials=tuple(
                tuple(
                    lane + ((0,) * N,)
                    for lane in level
                )
                for level in tensor.body_polynomials
            ),
        )
        self.assertFalse(verify_phase_identity(extra_body, projection))

        extra_mask = replace(
            tensor,
            mask_polynomials=tuple(
                tuple(
                    basis + ((0,) * N,)
                    for basis in level
                )
                for level in tensor.mask_polynomials
            ),
        )
        with self.assertRaisesRegex(ValueError, "shape"):
            concatenated_mask_difference_rank(extra_mask)
        with self.assertRaisesRegex(ValueError, "shape"):
            build_evaluator_sample_matrix(extra_mask)


class JointRankGateTests(unittest.TestCase):
    def test_common_lambda_has_exact_concatenated_module_rank_surrogate(self):
        for r in (2, 4, 6):
            rho = min(2, r - 1)
            tensor = build_rank_bounded_tensor(
                r,
                rho,
                1,
                secrets_for(r),
                GADGET,
                N,
                PRIME,
                public_lambda_for(r, rho),
            )
            with self.subTest(r=r):
                self.assertTrue(verify_joint_rank_factorization(tensor))
                self.assertEqual(concatenated_mask_difference_rank(tensor), rho * N)
                self.assertTrue(all(value <= rho * N for value in level_mask_difference_ranks(tensor)))

    def test_full_rank_c0_control_reaches_lane_maximum(self):
        for r in (2, 4, 6):
            rho = r - 1
            tensor = build_rank_bounded_tensor(
                r,
                rho,
                1,
                secrets_for(r),
                GADGET,
                N,
                PRIME,
                public_lambda_for(r, rho) if rho <= 2 else tuple(
                    (1,) + tuple(1 if column == lane else 0 for column in range(1, r))
                    for lane in range(r)
                ),
            )
            self.assertEqual(concatenated_mask_difference_rank(tensor), (r - 1) * N)

    def test_per_level_bounds_do_not_replace_the_joint_span_check(self):
        control = build_joint_rank_escape_control(
            6, 2, 1, secrets_for(6), GADGET, N, PRIME
        )
        self.assertTrue(all(value <= 2 * N for value in level_mask_difference_ranks(control)))
        self.assertGreater(concatenated_mask_difference_rank(control), 2 * N)


class EvaluatorSampleRelationTests(unittest.TestCase):
    def test_sample_matrix_orientation_and_audits_are_selector_local(self):
        for mu, expected_status in (
            (0, NO_RETAINED_MESSAGE_RELATION),
            (1, RELATION_RECORDED_NO_SECURITY_DECISION),
        ):
            tensor = build_rank_bounded_tensor(
                4,
                2,
                mu,
                secrets_for(4),
                GADGET,
                N,
                PRIME,
                public_lambda_for(4, 2),
            )
            sample_matrix, messages = build_evaluator_sample_matrix(tensor)
            self.assertEqual(len(sample_matrix), len(GADGET) * (3 + 4))
            self.assertEqual(len(sample_matrix[0]), 3 * N)
            self.assertEqual(len(messages), 4)
            self.assertEqual(len(messages[0]), len(sample_matrix))

            audit = audit_evaluator_sample_relations(
                tensor,
                build_phase_projection(
                    tensor.public_lambda, tensor.secrets, mu, PRIME
                ),
            )
            self.assertEqual(audit.mu, mu)
            self.assertEqual(audit.status, expected_status)
            self.assertFalse(audit.security_decision)
            for relation in audit.relations:
                self.assertEqual(
                    relation.l1_norm,
                    sum(
                        abs(value)
                        for value in relation.centered_coefficients
                    ),
                )
                self.assertAlmostEqual(
                    relation.l2_norm,
                    math.sqrt(
                        sum(
                            value * value
                            for value in relation.centered_coefficients
                        )
                    ),
                )
                self.assertIsNotNone(relation.symbolic_error_multiplier)

    def test_shared_and_independent_controls_do_not_invent_insecurity_decisions(self):
        shared = build_dense_control_tensor(4, 1, secrets_for(4), GADGET, N, PRIME)
        independent = build_rank_bounded_tensor(
            4, 3, 1, secrets_for(4), GADGET, N, PRIME, tuple(
                (1,) + tuple(1 if column == lane else 0 for column in range(1, 4))
                for lane in range(4)
            )
        )
        for tensor in (shared, independent):
            audit = audit_evaluator_sample_relations(
                tensor,
                build_phase_projection(
                    tensor.public_lambda, tensor.secrets, tensor.mu, PRIME
                ),
            )
            self.assertNotEqual(audit.status, REGISTERED_SHORT_ERROR_RELATION_FAIL)
            self.assertFalse(audit.security_decision)

    def test_same_secret_zero_error_cancellation_is_a_decisive_synthetic_fail(self):
        secret = secrets_for(1)[0]
        tensor = build_rank_bounded_tensor(
            4,
            2,
            1,
            (secret, secret, secret, secret),
            GADGET,
            N,
            PRIME,
            public_lambda_for(4, 2),
        )
        synthetic = replace(
            tensor,
            relation_error_distribution="SYNTHETIC_SAME_SECRET_ZERO_ERROR",
            registered_sigma=0.0,
            registered_error_bound=0.0,
            decision_inequality="retained_gap > combined_error_bound",
        )
        audit = audit_evaluator_sample_relations(
            synthetic,
            build_phase_projection(
                synthetic.public_lambda, synthetic.secrets, synthetic.mu, PRIME
            ),
        )
        self.assertEqual(audit.status, REGISTERED_SHORT_ERROR_RELATION_FAIL)
        self.assertTrue(audit.security_decision)

    def test_forged_or_malformed_relation_registrations_are_rejected(self):
        secret = secrets_for(1)[0]
        tensor = build_rank_bounded_tensor(
            4,
            2,
            1,
            (secret, secret, secret, secret),
            GADGET,
            N,
            PRIME,
            public_lambda_for(4, 2),
        )
        projection = build_phase_projection(
            tensor.public_lambda, tensor.secrets, tensor.mu, PRIME
        )
        valid = {
            "relation_error_distribution": (
                "SYNTHETIC_SAME_SECRET_ZERO_ERROR"
            ),
            "registered_sigma": 0.0,
            "registered_error_bound": 0.0,
            "decision_inequality": (
                "retained_gap > combined_error_bound"
            ),
        }
        cases = (
            (
                "forged distribution",
                {"relation_error_distribution": "FORGED_ZERO_ERROR"},
            ),
            (
                "forged inequality",
                {"decision_inequality": "FORGED_INEQUALITY"},
            ),
            ("negative sigma", {"registered_sigma": -1.0}),
            ("infinite sigma", {"registered_sigma": math.inf}),
            ("nan sigma", {"registered_sigma": math.nan}),
            ("negative bound", {"registered_error_bound": -1.0}),
            ("infinite bound", {"registered_error_bound": math.inf}),
            ("nan bound", {"registered_error_bound": math.nan}),
            ("nonzero synthetic sigma", {"registered_sigma": 1.0}),
            (
                "nonzero synthetic bound",
                {"registered_error_bound": 1.0},
            ),
            (
                "partial registration",
                {
                    "registered_sigma": None,
                    "registered_error_bound": None,
                    "decision_inequality": None,
                },
            ),
        )
        for label, mutation in cases:
            with self.subTest(label=label):
                malformed = replace(tensor, **(valid | mutation))
                with self.assertRaisesRegex(ValueError, "registration"):
                    audit_evaluator_sample_relations(
                        malformed, projection
                    )

    def test_message_mutation_changes_the_relation_diagnostic(self):
        tensor = build_rank_bounded_tensor(
            4, 2, 1, secrets_for(4), GADGET, N, PRIME, public_lambda_for(4, 2)
        )
        projection = build_phase_projection(
            tensor.public_lambda, tensor.secrets, tensor.mu, PRIME
        )
        baseline = audit_evaluator_sample_relations(tensor, projection)

        bodies = [
            [list(component_polynomials) for component_polynomials in level]
            for level in tensor.body_polynomials
        ]
        changed = list(bodies[1][0][6])
        changed[0] = (changed[0] + 1) % PRIME
        bodies[1][0][6] = tuple(changed)
        mutated = replace(
            tensor,
            body_polynomials=tuple(
                tuple(tuple(lane) for lane in level)
                for level in bodies
            ),
        )
        diagnostic = audit_evaluator_sample_relations(mutated, projection)
        self.assertNotEqual(diagnostic.diagnostic_hash, baseline.diagnostic_hash)


class SourceBindingAndDecisionTests(unittest.TestCase):
    def test_gate_binds_sources_counts_and_emits_one_recomputed_terminal_result(self):
        expected_counts = {
            2: (
                EvaluatorCounts(
                    2, 32, 32, 16, 4, 32, 12, 3, 2280, True
                ),
                EvaluatorCounts(
                    2, 12, 24, 12, 3, 18, 9, 2, 1754, True
                ),
            ),
            4: (
                EvaluatorCounts(
                    2, 84, 112, 28, 7, 98, 21, 10, 5689, True
                ),
                EvaluatorCounts(
                    2, 20, 80, 20, 5, 50, 15, 4, 3767, True
                ),
            ),
            6: (
                EvaluatorCounts(
                    2, 108, 216, 36, 9, 162, 27, 16, 9346, True
                ),
                EvaluatorCounts(
                    2, 28, 168, 28, 7, 98, 21, 6, 6767, True
                ),
            ),
        }
        for r in (2, 4, 6):
            with self.subTest(r=r):
                result = run_c1_operator_gate(ROOT, r, PRIME)
                self.assertEqual(len(result.tensors), 2)
                self.assertEqual(
                    tuple(tensor.mu for tensor in result.tensors), (0, 1)
                )
                self.assertTrue(result.phase_identity_passed)
                self.assertTrue(result.joint_rank_passed)
                self.assertFalse(result.structural_improvement)
                self.assertEqual(
                    (result.evaluator_counts, result.dense_counts),
                    expected_counts[r],
                )
                self.assertEqual(
                    tuple(
                        audit.status
                        for audit in result.relation_audits
                    ),
                    (
                        NO_RETAINED_MESSAGE_RELATION,
                        RELATION_RECORDED_NO_SECURITY_DECISION,
                    ),
                )
                self.assertEqual(
                    result.decision,
                    REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
                )
                self.assertNotEqual(
                    result.decision, ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY
                )
                self.assertTrue(result.seed_hash)
                self.assertTrue(result.schedule_hash)
                self.assertEqual(
                    {
                        binding.classification
                        for binding in result.source_bindings
                    },
                    {
                        "EXACT_SOURCE",
                        "EXACT_ARTIFACT",
                        "SUPPORT_ONLY_NO_NUMERIC_COEFFICIENTS",
                    },
                )
                self.assertTrue(verify_operator_gate_result(result))
                for metric in operator_tensor._STRUCTURAL_COUNT_FIELDS:
                    forged_counts = replace(
                        result.evaluator_counts,
                        **{
                            metric: getattr(
                                result.evaluator_counts, metric
                            )
                            + 1
                        },
                    )
                    self.assertFalse(
                        verify_operator_gate_result(
                            replace(
                                result,
                                evaluator_counts=forged_counts,
                            )
                        )
                    )

    def test_gate_material_rejects_noncanonical_rho_and_alternate_lambda(self):
        r = 4
        secrets = secrets_for(r)
        noncanonical_lambda = tuple(
            (1, 0) if lane == 0 else (1, lane)
            for lane in range(r)
        )
        noncanonical_tensors = tuple(
            build_rank_bounded_tensor(
                r,
                1,
                mu,
                secrets,
                GADGET,
                N,
                PRIME,
                noncanonical_lambda,
            )
            for mu in (0, 1)
        )
        noncanonical_projections = tuple(
            build_phase_projection(
                noncanonical_lambda, secrets, mu, PRIME
            )
            for mu in (0, 1)
        )
        with self.assertRaisesRegex(ValueError, "canonical rho"):
            operator_tensor._evaluate_gate_material(
                noncanonical_tensors, noncanonical_projections
            )

        alternate_lambda = tuple(
            (1, 0, 0)
            if lane == 0
            else (1, 2 * lane, lane * lane % PRIME)
            for lane in range(r)
        )
        alternate_tensors = tuple(
            build_rank_bounded_tensor(
                r,
                2,
                mu,
                secrets,
                GADGET,
                N,
                PRIME,
                alternate_lambda,
            )
            for mu in (0, 1)
        )
        alternate_projections = tuple(
            build_phase_projection(
                alternate_lambda, secrets, mu, PRIME
            )
            for mu in (0, 1)
        )
        with self.assertRaisesRegex(ValueError, "canonical Lambda"):
            operator_tensor._evaluate_gate_material(
                alternate_tensors, alternate_projections
            )

    def test_structural_policy_uses_every_count_and_recomputes_rejection(self):
        required_metrics = (
            "selector_objects",
            "mask_roots",
            "body_polynomials",
            "gadget_rows",
            "decomposition_inputs",
            "add_multiplies",
            "transforms",
            "public_mixing_coefficients",
            "bytes",
        )
        candidate = EvaluatorCounts(
            selector_objects=1,
            mask_roots=9,
            body_polynomials=9,
            gadget_rows=9,
            decomposition_inputs=9,
            add_multiplies=9,
            transforms=9,
            public_mixing_coefficients=9,
            bytes=9,
            reconstructs_quadratic_body_work=False,
        )
        dense = replace(
            candidate,
            selector_objects=2,
            mask_roots=10,
            body_polynomials=10,
            gadget_rows=10,
            decomposition_inputs=10,
            add_multiplies=10,
            transforms=10,
            public_mixing_coefficients=10,
            bytes=10,
        )
        self.assertTrue(
            operator_tensor._has_strict_pareto_improvement(
                candidate, dense
            )
        )
        for metric in required_metrics:
            with self.subTest(metric=metric):
                mutated = replace(candidate, **{metric: 11})
                self.assertFalse(
                    operator_tensor._has_strict_pareto_improvement(
                        mutated, dense
                    )
                )
                self.assertEqual(
                    operator_tensor._derive_decision(
                        phase_identity_passed=True,
                        joint_rank_passed=True,
                        relation_audits=(),
                        structural_improvement=False,
                    ),
                    REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
                )
        self.assertFalse(
            operator_tensor._has_strict_pareto_improvement(
                replace(
                    candidate,
                    reconstructs_quadratic_body_work=True,
                ),
                dense,
            )
        )

    def test_changing_only_the_decision_field_fails_recomputation(self):
        result = run_c1_operator_gate(ROOT, 2, PRIME)
        forged = replace(result, decision=ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY)
        self.assertFalse(verify_operator_gate_result(forged))

    def test_stage203_numeric_coefficient_claim_is_rejected(self):
        mutated = MutatedRoot()
        try:
            path = (
                mutated.root
                / "repro/stage203_production_selector_equation_probe/equation_map.csv"
            )
            lines = path.read_text(encoding="utf-8").splitlines()
            lines = [lines[0] + ",coefficient"] + [line + ",7" for line in lines[1:]]
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(SourceBindingError, "support-only"):
                run_c1_operator_gate(mutated.root, 4, PRIME)
        finally:
            mutated.close()

    def test_dense_keygen_or_operator_token_change_breaks_source_binding(self):
        mutated = MutatedRoot()
        try:
            mutated.replace(
                "src/mosfhet/src/mattrgsw.c",
                "return l * (k + r);",
                "return l * (k + r + 1);",
            )
            with self.assertRaisesRegex(SourceBindingError, "MAT dense source token"):
                run_c1_operator_gate(mutated.root, 4, PRIME)
        finally:
            mutated.close()

    def test_theory_record_states_scope_equations_dimensions_and_terminal_route(self):
        record = (ROOT / "theory_checks/candidate_c_operator_tensor.md").read_text(
            encoding="ascii"
        )
        for token in (
            "R_257,8 = GF(257)[X]/(X^8+1)",
            "B_mu[t,q,c] - s_q sum_v Lambda[q,v] A_mu[t,v,c]",
            "R_mu",
            "T_mu",
            "field-expanded finite surrogate of module rank rho",
            "SUPPORT_ONLY_NO_NUMERIC_COEFFICIENTS",
            "RELATION_RECORDED_NO_SECURITY_DECISION",
            "REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL",
            "SYNTHETIC_SAME_SECRET_ZERO_ERROR",
            "strict-Pareto policy",
            "canonical JSON",
            "not a security proof",
            "not a universal impossibility theorem",
            "Task 3B is not entered",
        ):
            self.assertIn(token, record)


if __name__ == "__main__":
    unittest.main()
