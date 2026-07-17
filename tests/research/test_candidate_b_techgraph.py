import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GRAPH_PATH = ROOT / "paper_techgraphs" / "candidate_b_factorized_selector.yaml"
GRAPH_MD_PATH = (
    ROOT / "paper_techgraphs" / "candidate_b_factorized_selector_graph.md"
)
GAPS_PATH = (
    ROOT / "paper_techgraphs" / "candidate_b_factorized_selector_gaps.md"
)
MODEL_PATH = (
    ROOT / "theory_checks" / "candidate_b_factorized_standard_pvw_model.md"
)

EXPECTED_ANCHORS = {
    "pvw_ciphertext_type": (
        "src/mosfhet/include/mosfhet.h",
        "typedef struct _PVW_TMLWE{",
    ),
    "pvw_sample": (
        "src/mosfhet/src/pvwtmlwe.c",
        "void pvmtmlwe_sample(",
    ),
    "pvw_phase": (
        "src/mosfhet/src/pvwtmlwe.c",
        "void pvmtmlwe_phase(",
    ),
    "torus_error_sampler": (
        "src/mosfhet/src/misc.c",
        "out[i] = double2torus(generate_normal_random(sigma));",
    ),
    "mat_selector_sample": (
        "src/mosfhet/src/mattrgsw.c",
        "void mat_trgsw_monomial_sample(",
    ),
    "dense_external_product": (
        "src/mosfhet/src/mattrgsw.c",
        "void mat_trgsw_mul_pvmtmlwe_DFT(",
    ),
    "sab_pvw_cmux": (
        "src/sab_pvw.c",
        "void sab_pvw_CMUX(",
    ),
    "target_k_t_one": (
        "main.c",
        "return (SAB_PVW_Target_Params){2048, 1, 2048, 1, 1, 23, 3, 39, 7,",
    ),
}


def load_graph():
    return json.loads(GRAPH_PATH.read_text(encoding="ascii"))


class CandidateBTechgraphTests(unittest.TestCase):
    def test_source_anchors_resolve_to_current_implementation(self):
        graph = load_graph()
        anchors = {anchor["id"]: anchor for anchor in graph["source_anchors"]}
        self.assertEqual(set(anchors), set(EXPECTED_ANCHORS))

        for anchor_id, (relative_path, token) in EXPECTED_ANCHORS.items():
            with self.subTest(anchor=anchor_id):
                anchor = anchors[anchor_id]
                self.assertEqual(anchor["path"], relative_path)
                self.assertEqual(anchor["symbol_or_token"], token)
                source = (ROOT / relative_path).read_text(
                    encoding="utf-8", errors="strict"
                )
                self.assertIn(token, source)
                self.assertEqual(anchor["anchor_status"], "PASS")

    def test_graph_separates_semantics_from_complete_distribution(self):
        graph = load_graph()
        nodes = {node["id"]: node for node in graph["nodes"]}
        self.assertIn("star_cycle_semantics", nodes)
        self.assertIn("standard_selector_distribution", nodes)
        self.assertIn("independent_error_rank", nodes)
        self.assertEqual(
            nodes["star_cycle_semantics"]["claim_scope"],
            "semantic_support_only",
        )
        self.assertEqual(
            nodes["standard_selector_distribution"]["claim_scope"],
            "complete_encrypted_distribution",
        )
        self.assertFalse(
            nodes["star_cycle_semantics"]["proves_standard_distribution"]
        )
        self.assertTrue(
            any(
                edge["from"] == "star_cycle_semantics"
                and edge["to"] == "standard_selector_distribution"
                and edge["relation"] == "does_not_imply"
                for edge in graph["edges"]
            )
        )

    def test_graph_records_historical_intake_snapshot_only(self):
        graph = load_graph()
        state = graph["candidate_state"]
        self.assertEqual(state["candidate"], "B")
        self.assertEqual(state["repository_status"], "INTAKE")
        self.assertEqual(
            state["in_memory_progression"],
            ["INTAKE", "TECHGRAPH_ANCHORED", "EQUATIONS_DEFINED"],
        )
        self.assertFalse(state["repository_state_mutated"])
        self.assertFalse(graph["production_hot_path_permission"])

    def test_source_behavior_and_target_cost_assumptions_are_anchored(self):
        pvw = (ROOT / "src/mosfhet/src/pvwtmlwe.c").read_text(
            encoding="utf-8"
        )
        sample = pvw[
            pvw.index("void pvmtmlwe_sample("):
            pvw.index("PVW_TMLWE pvmtmlwe_new_sample(")
        ]
        self.assertIn("for (size_t i = 0; i < key->r; i++)", sample)
        self.assertIn("generate_torus_normal_random_array", sample)
        self.assertIn("polynomial_mul_addto_torus", sample)
        phase_start = pvw.index("void pvmtmlwe_phase(")
        phase_end = pvw.index("void print_pvmtmlwe_msg(")
        phase_source = pvw[phase_start:phase_end]
        self.assertIn(
            "polynomial_mul_addto_torus(out[i], in->a[j], key->s[j][i])",
            phase_source,
        )
        self.assertIn(
            "polynomial_sub_torus_polynomials(out[i], in->b[i], out[i])",
            phase_source,
        )

        mat = (ROOT / "src/mosfhet/src/mattrgsw.c").read_text(
            encoding="utf-8"
        )
        keygen = mat[
            mat.index("void mat_trgsw_monomial_sample("):
            mat.index("void mat_trgsw_to_DFT(")
        ]
        self.assertIn("pvmtmlwe_sample(out->samples[i], NULL", keygen)
        self.assertIn("out->samples[j * l + i]->a[j]", keygen)
        self.assertIn("out->samples[(k + j) * l + i]->b[j]", keygen)
        dense = mat[
            mat.index(
                "static void mat_trgsw_mul_pvmtmlwe_DFT_from_dec("
            ):
            mat.index("void mat_trgsw_mul_pvmtmlwe_DFT(")
        ]
        self.assertIn("for (size_t row = 1; row < rows; row++)", dense)
        self.assertIn("for (size_t j = 0; j < k; j++)", dense)
        self.assertIn("for (size_t j = 0; j < r; j++)", dense)

        sab = (ROOT / "src/sab_pvw.c").read_text(encoding="utf-8")
        cmux_materialize = sab[
            sab.index("static void sab_pvw_CMUX_from_sub_internal("):
            sab.index("static void sab_pvw_CMUX_from_diff_internal(")
        ]
        public_cmux = sab[
            sab.index("void sab_pvw_CMUX("):
            sab.index("void sab_pvw_NCMUX(")
        ]
        self.assertIn("mat_trgsw_mul_pvmtmlwe_DFT", cmux_materialize)
        self.assertIn("sab_pvw_CMUX_internal", public_cmux)

        graph = load_graph()
        anchors = {anchor["id"]: anchor for anchor in graph["source_anchors"]}
        self.assertIn("out_k=1", anchors["target_k_t_one"]["role"])
        self.assertIn("l=1", anchors["target_k_t_one"]["role"])
        self.assertIn("Theta(r)", graph["research_question"])

    def test_equation_model_contains_all_task_one_obligations(self):
        model = MODEL_PATH.read_text(encoding="ascii")
        required_fragments = [
            "C = mu h I_(k+r) + V [I_k | S] + [0 | E]",
            "C = mu h I_m + v w^T + [0 | E]",
            "m = r + 1",
            "P(a, b) = b - a S",
            "P(d^T C) = mu h P(d) + d^T E",
            "phi(f) = f(1) mod 2",
            "rank_GF(2)(phi(E)) = r",
            "q < r",
            "q=O(1)",
            "m^2 = (r+1)^2",
            "(r+1)q + qr",
            "polynomial components",
            "DFT",
            "relinearization",
            "key switching",
            "T_bootstrap/r",
        ]
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, model)

    def test_owned_artifacts_do_not_assert_blocked_results(self):
        graph = load_graph()
        self.assertEqual(
            graph["claim_gates"],
            {
                "security": "BLOCKED",
                "noise": "BLOCKED",
                "kernel_speedup": "BLOCKED",
                "complete_sab_speedup": "BLOCKED",
                "novelty": "BLOCKED",
                "production_algorithm": "BLOCKED",
            },
        )
        paths = [GRAPH_PATH, GRAPH_MD_PATH, GAPS_PATH, MODEL_PATH]
        content = "\n".join(path.read_text(encoding="ascii") for path in paths)
        forbidden = (
            "Candidate B is secure",
            "complete-SAB speedup achieved",
            "proves a general impossibility",
            '"production_hot_path_permission": true',
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, content)

    def test_human_graph_and_gap_files_preserve_claim_boundary(self):
        graph_md = GRAPH_MD_PATH.read_text(encoding="ascii")
        gaps = GAPS_PATH.read_text(encoding="ascii")

        self.assertIn(
            "Semantic star-cycle support does not prove the complete "
            "encrypted selector distribution.",
            graph_md,
        )
        for content in (graph_md, gaps):
            self.assertIn("historical pre-closeout INTAKE snapshot", content)
            self.assertIn("Current campaign disposition is recorded elsewhere.", content)
            self.assertNotIn("active at repository state", content)
            self.assertNotIn("in repository state", content)
        self.assertIn(
            "`INTAKE -> TECHGRAPH_ANCHORED -> EQUATIONS_DEFINED` in memory",
            graph_md,
        )
        self.assertIn(
            "This rank argument is an exact-support obstruction, not a "
            "general security impossibility theorem.",
            gaps,
        )
        self.assertIn(
            "No complete-SAB speedup is claimed by this intake package.",
            gaps,
        )
        self.assertIn("Candidate C", gaps)

    def test_all_owned_artifacts_are_ascii_and_graph_is_json_valid_yaml(self):
        paths = [GRAPH_PATH, GRAPH_MD_PATH, GAPS_PATH, MODEL_PATH]
        for path in paths:
            with self.subTest(path=path.name):
                path.read_bytes().decode("ascii")
        self.assertEqual(load_graph()["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
