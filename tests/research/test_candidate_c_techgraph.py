import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GRAPH_PATH = ROOT / "paper_techgraphs" / "candidate_c_rank_bounded_state.yaml"
GRAPH_MD_PATH = (
    ROOT / "paper_techgraphs" / "candidate_c_rank_bounded_state_graph.md"
)
GAPS_PATH = (
    ROOT / "paper_techgraphs" / "candidate_c_rank_bounded_state_gaps.md"
)
MODEL_PATH = (
    ROOT / "theory_checks" / "candidate_c_rank_bounded_state_model.md"
)
TEST_PATH = Path(__file__)

EXPECTED_ANCHORS = {
    "sab_pvw_cmux": (
        "src/sab_pvw.c",
        "void sab_pvw_CMUX(",
    ),
    "sab_pvw_ncmux": (
        "src/sab_pvw.c",
        "void sab_pvw_NCMUX(",
    ),
    "sab_pvw_rgsw_monomial_state": (
        "src/sab_pvw.c",
        "static uint64_t sab_pvw_RGSW_monomial_mul_state(",
    ),
    "sab_pvw_sparse_mul_binary": (
        "src/sab_pvw.c",
        "void sab_pvw_sparse_mul_binary(",
    ),
    "sab_pvw_sub_a_binary_to": (
        "src/sab_pvw.c",
        "static void sab_pvw_sub_a_binary_to(",
    ),
    "pvmtmlwe_mul_by_xai": (
        "src/mosfhet/src/pvwtmlwe.c",
        "void pvmtmlwe_mul_by_xai(",
    ),
    "mat_trgsw_mul_pvmtmlwe_dft": (
        "src/mosfhet/src/mattrgsw.c",
        "void mat_trgsw_mul_pvmtmlwe_DFT(",
    ),
    "default_target": (
        "main.c",
        (
            "return (SAB_PVW_Target_Params){2048, 1, 2048, 1, 1, "
            "23, 3, 39, 7,"
        ),
    ),
    "candidate_b_terminal_summary": (
        "repro/candidate_b_factorized_gate/summary.csv",
        "REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C",
    ),
    "stage203_star_cycle_equations": (
        "repro/stage203_production_selector_equation_probe/equation_map.csv",
        (
            "r,row,col,equation_class,semantic_role,is_public_row,"
            "may_skip_after_proof"
        ),
    ),
    "stage345_exact_dense_baseline": (
        "repro/stage345_binary_matrix_synthesis/summary.csv",
        "PASS_STAGE345_BINARY_MATRIX_SYNTHESIS_SCOPED_READY",
    ),
}

STAR_CYCLE_EQUATIONS = [
    "mask_output_from_body_input",
    "body_output_from_mask_input",
    "lane_self_body_interaction",
    "lane_neighbor_body_interaction",
]

TRANSFORMATIONS = {
    "cmux",
    "ncmux",
    "butterfly",
    "rgsw_monomial",
    "sub_a_binary",
    "rotation",
}


def load_graph():
    return json.loads(GRAPH_PATH.read_text(encoding="ascii"))


def split_c_initializer(initializer):
    values = []
    start = 0
    depth = 0
    for index, character in enumerate(initializer):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced initializer parentheses")
        elif character == "," and depth == 0:
            values.append(initializer[start:index].strip())
            start = index + 1
    if depth != 0:
        raise ValueError("unbalanced initializer parentheses")
    values.append(initializer[start:].strip())
    if any(not value for value in values):
        raise ValueError("empty initializer value")
    return values


def parse_default_target_params(source):
    declaration = re.search(
        r"typedef\s+struct\s*\{(?P<body>.*?)\}"
        r"\s*SAB_PVW_Target_Params\s*;",
        source,
        flags=re.DOTALL,
    )
    if declaration is None:
        raise ValueError("SAB_PVW_Target_Params declaration not found")
    fields = re.findall(
        r"^\s*(?:int|double)\s+([A-Za-z_][A-Za-z0-9_]*)\s*;\s*$",
        declaration.group("body"),
        flags=re.MULTILINE,
    )
    if not fields:
        raise ValueError("SAB_PVW_Target_Params fields not found")
    if len(fields) != len(set(fields)):
        raise ValueError("duplicate SAB_PVW_Target_Params field")

    target_function = re.search(
        r"static\s+SAB_PVW_Target_Params\s+"
        r"sab_pvw_target_params\s*\(\s*void\s*\)\s*\{"
        r"(?P<body>.*?)#endif\s*\}",
        source,
        flags=re.DOTALL,
    )
    if target_function is None:
        raise ValueError("sab_pvw_target_params function not found")
    default_initializer = re.search(
        r"#else\s*return\s*\(SAB_PVW_Target_Params\)\s*"
        r"\{(?P<values>.*?)\}\s*;",
        target_function.group("body"),
        flags=re.DOTALL,
    )
    if default_initializer is None:
        raise ValueError("default SAB_PVW_Target_Params initializer not found")
    values = split_c_initializer(default_initializer.group("values"))
    if len(fields) != len(values):
        raise ValueError(
            "SAB_PVW_Target_Params field/initializer length mismatch"
        )
    return dict(zip(fields, values, strict=True))


class CandidateCTechgraphTests(unittest.TestCase):
    def test_source_anchors_resolve_to_exact_current_tokens(self):
        graph = load_graph()
        anchors = {anchor["id"]: anchor for anchor in graph["source_anchors"]}
        self.assertEqual(set(anchors), set(EXPECTED_ANCHORS))

        for anchor_id, (relative_path, token) in EXPECTED_ANCHORS.items():
            with self.subTest(anchor=anchor_id):
                anchor = anchors[anchor_id]
                self.assertEqual(anchor["path"], relative_path)
                self.assertEqual(anchor["symbol_or_token"], token)
                source = (ROOT / relative_path).read_text(
                    encoding="utf-8",
                    errors="strict",
                )
                self.assertIn(token, source)
                self.assertEqual(anchor["anchor_status"], "PASS")

    def test_historical_and_parameter_anchors_preserve_scope(self):
        graph = load_graph()

        self.assertEqual(
            graph["predecessor"],
            {
                "candidate": "B",
                "decision": (
                    "REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_"
                    "FACTORIZATION_ROUTE_TO_C"
                ),
                "route": "candidate_c_rank_bounded_shared_mask_state",
            },
        )
        self.assertEqual(graph["star_cycle_equations"], STAR_CYCLE_EQUATIONS)
        stage203 = (
            ROOT
            / EXPECTED_ANCHORS["stage203_star_cycle_equations"][0]
        ).read_text(encoding="ascii")
        for equation in STAR_CYCLE_EQUATIONS:
            self.assertIn(equation, stage203)

        self.assertEqual(
            graph["baseline"],
            {
                "kind": "current_exact_dense_pvw_mat_sab",
                "evidence": (
                    "repro/stage345_binary_matrix_synthesis/summary.csv"
                ),
                "scope": (
                    "historical scoped binary baseline; no Candidate C "
                    "comparison"
                ),
            },
        )

    def test_default_target_is_derived_from_struct_field_order(self):
        source = (ROOT / "main.c").read_text(encoding="utf-8")
        target = parse_default_target_params(source)
        self.assertEqual(int(target["out_N"], 0), 2048)
        self.assertEqual(int(target["out_k"], 0), 1)
        self.assertEqual(int(target["l"], 0), 1)
        graph = load_graph()
        self.assertEqual(
            graph["default_target_parameters"],
            {
                "out_N": int(target["out_N"], 0),
                "out_k": int(target["out_k"], 0),
                "l": int(target["l"], 0),
            },
        )

        reordered = source.replace(
            "  int out_N;\n  int out_k;",
            "  int out_k;\n  int out_N;",
            1,
        )
        reordered_target = parse_default_target_params(reordered)
        with self.assertRaises(AssertionError):
            self.assertEqual(int(reordered_target["out_N"], 0), 2048)

        malformed = source.replace("  int out_N;\n", "", 1)
        with self.assertRaisesRegex(ValueError, "length mismatch"):
            parse_default_target_params(malformed)

    def test_rank_bounded_state_invariant_is_explicit(self):
        graph = load_graph()
        invariant = graph["state_invariant"]
        self.assertEqual(
            invariant["lane_mask"],
            (
                "a_q = a_shared + sum_(t=1..rho) "
                "lambda[q,t] delta_a[t]"
            ),
        )
        self.assertEqual(invariant["phase"], "phase_q = b_q - a_q s_q")
        self.assertEqual(
            invariant["rank"],
            "rho = rank({a_q-a_0 : q=1,...,r-1})",
        )
        self.assertEqual(invariant["normalization"], "lambda[0,t]=0")
        self.assertEqual(
            invariant["reference_lane_rule"],
            "changing the reference lane does not change rho",
        )

    def test_real_schedule_transformations_have_complete_obligations(self):
        graph = load_graph()
        transformations = {
            item["id"]: item for item in graph["schedule_transformations"]
        }
        self.assertEqual(set(transformations), TRANSFORMATIONS)
        required = {
            "input_state",
            "newly_introduced_independent_mask_directions",
            "output_phase_equation",
            "output_rho_rule",
            "next_schedule_consumer",
            "current_exact_dense_closure",
            "proposed_compact_obligation",
        }
        for transformation_id, transformation in transformations.items():
            with self.subTest(transformation=transformation_id):
                self.assertTrue(required <= set(transformation))
                self.assertTrue(
                    all(transformation[field] for field in required)
                )
                self.assertEqual(
                    transformation["current_exact_dense_closure"],
                    "rho=0",
                )
                if transformation_id == "ncmux":
                    self.assertNotIn("public_linear_operation", transformation)
                    self.assertTrue(
                        {
                            "public_permutation_and_wiring",
                            "automorphism_evaluation_key_work",
                            "encrypted_selector_cmux",
                        }
                        <= set(transformation)
                    )
                else:
                    self.assertIn("public_linear_operation", transformation)
        for transformation_id in ("cmux", "ncmux", "butterfly"):
            self.assertIn(
                "may introduce lane-dependent mask directions",
                transformations[transformation_id][
                    "proposed_compact_obligation"
                ],
            )

        self.assertEqual(
            graph["real_schedule"],
            [
                "rgsw_monomial",
                "sub_a_binary",
                "rgsw_monomial",
            ],
        )
        self.assertEqual(
            graph["real_schedule_repetition"],
            (
                "repeat [rgsw_monomial, sub_a_binary] h times, "
                "then rgsw_monomial"
            ),
        )

    def test_ncmux_separates_public_and_encrypted_operation_classes(self):
        graph = load_graph()
        ncmux = next(
            item
            for item in graph["schedule_transformations"]
            if item["id"] == "ncmux"
        )
        self.assertNotIn("public_linear_operation", ncmux)
        self.assertEqual(
            ncmux["public_permutation_and_wiring"],
            (
                "public gen=2N-1 fixes tau_-1; polynomial_permute "
                "applies that coefficient permutation before public "
                "wiring feeds the evaluated result to the CMUX "
                "right-hand input"
            ),
        )
        self.assertEqual(
            ncmux["automorphism_evaluation_key_work"],
            (
                "pvmtmlwe_keyswitch(out,out,sab->aut_minus1) applies "
                "automorphism evaluation-key/key-switch work to the "
                "publicly permuted ciphertext; this is not public "
                "linear work"
            ),
        )
        self.assertEqual(
            ncmux["encrypted_selector_cmux"],
            (
                "sab_pvw_CMUX applies the encrypted MAT_TRGSW selector "
                "to the transformed right-hand input; this is not public "
                "linear work"
            ),
        )
        automorphism_source = (
            ROOT / "src/mosfhet/src/pvwtmlwe.c"
        ).read_text(encoding="utf-8")
        automorphism_start = automorphism_source.index(
            "void pvmtmlwe_eval_automorphism("
        )
        automorphism_end = automorphism_source.index(
            "\n}",
            automorphism_start,
        )
        automorphism = automorphism_source[
            automorphism_start:automorphism_end
        ]
        self.assertIn("polynomial_permute(", automorphism)
        self.assertIn("pvmtmlwe_keyswitch(out, out, ks_key);", automorphism)
        self.assertLess(
            automorphism.index("polynomial_permute("),
            automorphism.index("pvmtmlwe_keyswitch(out, out, ks_key);"),
        )
        graph_md = GRAPH_MD_PATH.read_text(encoding="ascii")
        gaps = GAPS_PATH.read_text(encoding="ascii")
        model = MODEL_PATH.read_text(encoding="ascii")
        for content in (graph_md, gaps, model):
            self.assertRegex(
                content,
                r"(?i)public\s+permutation\s+and\s+wiring",
            )
            self.assertRegex(
                content,
                (
                    r"(?i)evaluation-key/key-switch\s+work\s+is\s+not\s+"
                    r"public\s+linear\s+work"
                ),
            )
            self.assertRegex(
                content,
                (
                    r"(?i)encrypted-selector\s+CMUX\s+is\s+not\s+public\s+"
                    r"linear\s+work"
                ),
            )

    def test_exactly_three_finite_variants_are_registered(self):
        graph = load_graph()
        variants = graph["variants"]
        self.assertEqual(
            [variant["id"] for variant in variants],
            ["C0", "C1", "C2"],
        )
        self.assertEqual(
            [variant["name"] for variant in variants],
            [
                "independent_lane_directions",
                "rank_two_basis_with_public_lambda",
                (
                    "rank_two_basis_with_periodic_public_"
                    "relinearization"
                ),
            ],
        )
        self.assertEqual(variants[0]["control"], "negative")
        self.assertEqual(variants[1]["conversion_policy"], "none")
        self.assertEqual(variants[1]["required_bound"], "rho<=2")
        self.assertEqual(
            variants[2]["allowed_boundary"],
            "after a public block of butterfly steps",
        )
        self.assertEqual(
            variants[2]["forbidden_boundary"],
            "after every CMUX",
        )

    def test_claim_gates_and_task_one_conclusion_are_bounded(self):
        graph = load_graph()
        self.assertEqual(
            graph["claim_gates"],
            {
                "security": "BLOCKED",
                "noise": "BLOCKED",
                "amdahl": "BLOCKED",
                "kernel": "BLOCKED",
                "full_sab": "BLOCKED",
                "novelty": "BLOCKED",
                "production": "BLOCKED",
            },
        )
        self.assertFalse(graph["production_hot_path_permission"])
        self.assertEqual(
            graph["task1_conclusion"],
            (
                "The current state equations and schedule obligations "
                "are source anchored."
            ),
        )

    def test_human_artifacts_cover_model_and_claim_boundary(self):
        model = MODEL_PATH.read_text(encoding="ascii")
        required_model_fragments = [
            "a_q = a_shared + sum_(t=1..rho) lambda[q,t] delta_a[t]",
            "phase_q = b_q - a_q s_q",
            "rho = rank({a_q-a_0 : q=1,...,r-1})",
            "lambda[0,t]=0",
            "changing the reference lane does not change rho",
            "CMUX",
            "NCMUX",
            "butterfly",
            "RGSW monomial",
            "sub_a",
            "pvmtmlwe_mul_by_xai",
            "rho=0",
            "may introduce lane-dependent mask directions",
        ]
        for fragment in required_model_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, model)

        graph_md = GRAPH_MD_PATH.read_text(encoding="ascii")
        gaps = GAPS_PATH.read_text(encoding="ascii")
        for content in (graph_md, gaps, model):
            self.assertIn(
                (
                    "The current state equations and schedule obligations "
                    "are source anchored."
                ),
                content,
            )
            self.assertIn("Production hot-path permission: `false`.", content)
        self.assertIn("C0", graph_md)
        self.assertIn("C1", graph_md)
        self.assertIn("C2", graph_md)
        self.assertIn("All claim gates remain `BLOCKED`.", gaps)

    def test_all_owned_artifacts_are_ascii_and_graph_is_json_valid_yaml(self):
        paths = [GRAPH_PATH, GRAPH_MD_PATH, GAPS_PATH, MODEL_PATH, TEST_PATH]
        for path in paths:
            with self.subTest(path=path.name):
                path.read_bytes().decode("ascii")
        self.assertEqual(load_graph()["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
