import csv
from decimal import ROUND_DOWN, localcontext
import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import research.mat_sab.candidate_d_baseline as baseline


ROOT = Path(__file__).resolve().parents[2]

EXPECTED_ANCHORS = {
    "repro/candidate_a_star_cycle_gate/summary.csv": (
        "c7a003c39d8e56f1cc4ca0845cffe7e68f81cd41a8979d661f8a3df525a96d09"
    ),
    "repro/candidate_b_factorized_gate/summary.csv": (
        "c758785b0ce7d4d6ef56bb44639b381780ef0d529dc17c8f2544ec67ce3b7a91"
    ),
    "repro/candidate_c_rank_bounded_gate/terminal_record.csv": (
        "7c7e60bd9a201d4ed943d411dbd40be76ece8f4942822ca31ed278d53c8863d7"
    ),
    "repro/stage331_current_head_highstat_refresh/summary.csv": (
        "23d3c2611329f189a88f6bdc645e9ed1ac237d19159e79401d2fc11b9c03ad56"
    ),
    "repro/stage345_binary_matrix_synthesis/binary_matrix.csv": (
        "97014b127ad5061dc10fbd3cb3ab53fb06d9ebc69b436011760778425208ea9b"
    ),
    "src/sab_pvw.c": (
        "6aaabf61f010e0154b826855286137afc39de9b2520ee09e2ca43d5accf5e2ac"
    ),
    "src/mosfhet/src/mattrgsw.c": (
        "5da51089a748f7f1f54b56f81c2948ced14f0be4dd431bcffb2339af97c527fa"
    ),
    "main.c": (
        "d402980a203aacbaf6b281a9f7245cf14b72c2c80468e5a05050f35373eb11f8"
    ),
}


class CandidateDBaselineTests(unittest.TestCase):
    @staticmethod
    def _copy_inputs(destination: Path) -> None:
        for relative in EXPECTED_ANCHORS:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)

    @staticmethod
    def _rewrite_csv(path: Path, update) -> None:
        with path.open("r", encoding="ascii", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            fieldnames = tuple(reader.fieldnames or ())
            rows = list(reader)
        update(rows)
        with path.open("w", encoding="ascii", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _patched_hashes(root: Path) -> dict[str, str]:
        return {
            relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
            for relative in EXPECTED_ANCHORS
        }

    def test_registered_anchor_hashes_match_normative_bytes(self):
        self.assertEqual(baseline.EXPECTED_ANCHORS, EXPECTED_ANCHORS)
        anchors = baseline.validate_baseline_anchors(ROOT)
        self.assertEqual(
            tuple(anchor.path for anchor in anchors),
            tuple(EXPECTED_ANCHORS),
        )
        self.assertEqual(
            tuple(anchor.sha256 for anchor in anchors),
            tuple(EXPECTED_ANCHORS.values()),
        )
        self.assertTrue(all(anchor.role for anchor in anchors))
        for relative, expected in EXPECTED_ANCHORS.items():
            with self.subTest(relative=relative):
                self.assertEqual(baseline.sha256_file(ROOT / relative), expected)

    def test_each_anchor_is_immutable_and_must_be_a_regular_file(self):
        for relative in EXPECTED_ANCHORS:
            for mutation in ("delete", "change", "replace"):
                with self.subTest(relative=relative, mutation=mutation):
                    with tempfile.TemporaryDirectory() as tmp:
                        root = Path(tmp)
                        self._copy_inputs(root)
                        target = root / relative
                        if mutation == "delete":
                            target.unlink()
                        elif mutation == "change":
                            target.write_bytes(target.read_bytes() + b"\n")
                        else:
                            target.unlink()
                            target.mkdir()
                        with self.assertRaises(baseline.BaselineEvidenceError):
                            baseline.validate_baseline_anchors(root)

    def test_manifest_paths_cannot_escape_repository_root(self):
        outside = "../outside.csv"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_inputs(root)
            expected = dict(EXPECTED_ANCHORS)
            expected[outside] = "0" * 64
            with patch.object(baseline, "EXPECTED_ANCHORS", expected):
                with self.assertRaisesRegex(
                    baseline.BaselineEvidenceError,
                    "outside repository root",
                ):
                    baseline.validate_baseline_anchors(root)

    def test_target_parameters_are_parsed_from_field_order(self):
        params = baseline.parse_target_parameters(ROOT)
        self.assertEqual(
            params,
            {
                "in_N": 2048,
                "out_N": 2048,
                "out_k": 1,
                "l": 1,
                "bg_bit": 23,
                "prec": 3,
                "h": 39,
                "r_prec": 7,
                "sigma_out": 2.0**-50,
                "H": 573440,
            },
        )

    def test_missing_target_parameter_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_inputs(root)
            main = root / "main.c"
            source = main.read_text(encoding="utf-8")
            main.write_text(
                source.replace("  int out_N;\n", "", 1),
                encoding="utf-8",
                newline="\n",
            )
            with self.assertRaisesRegex(
                baseline.BaselineEvidenceError,
                "target parameter",
            ):
                baseline.parse_target_parameters(root)

    def test_terminal_predecessor_decisions_are_exact(self):
        baseline.validate_terminal_predecessors(ROOT)
        mutations = {
            "repro/candidate_a_star_cycle_gate/summary.csv": "decision",
            "repro/candidate_b_factorized_gate/summary.csv": "decision",
            "repro/candidate_c_rank_bounded_gate/terminal_record.csv": (
                "decision"
            ),
        }
        for relative, field in mutations.items():
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    self._copy_inputs(root)
                    path = root / relative
                    self._rewrite_csv(
                        path,
                        lambda rows: rows[0].__setitem__(field, "CHANGED"),
                    )
                    with patch.object(
                        baseline,
                        "EXPECTED_ANCHORS",
                        self._patched_hashes(root),
                    ):
                        with self.assertRaisesRegex(
                            baseline.BaselineEvidenceError,
                            "predecessor decision",
                        ):
                            baseline.build_d0_artifacts(root, root / "out")

    def test_builder_recovers_exact_metrics_and_unmeasured_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            decision = baseline.build_d0_artifacts(ROOT, out)
            self.assertEqual(
                decision,
                "PASS_D0_CANDIDATE_D_BASELINES_FROZEN",
            )
            manifest = out / "repro/candidate_d_admission/baseline_manifest.csv"
            with manifest.open("r", encoding="ascii", newline="") as handle:
                rows = list(csv.DictReader(handle, strict=True))
            by_id = {row["baseline_id"]: row for row in rows}
            self.assertEqual(tuple(by_id), ("B0a", "B0b", "B1", "B2"))
            self.assertEqual(
                by_id["B0a"]["status"],
                "FROZEN_HISTORICAL_HIGHSTAT",
            )
            self.assertEqual(
                by_id["B0b"]["status"],
                "REQUIRED_NOT_YET_LOCAL",
            )
            self.assertEqual(
                by_id["B1"]["status"],
                "FROZEN_HISTORICAL_HIGHSTAT",
            )
            self.assertEqual(
                by_id["B2"]["status"],
                "REQUIRED_NOT_YET_LOCAL",
            )
            self.assertEqual(by_id["B1"]["r"], "4")
            self.assertEqual(by_id["B1"]["n_active"], "2048")
            self.assertEqual(by_id["B1"]["t_complete_bootstrap_us"], "24468333.700")
            self.assertEqual(by_id["B1"]["t_over_r_us"], "6117083.425")
            self.assertEqual(
                by_id["B1"]["t_over_r_n_active_us"],
                "2986.857141113",
            )
            self.assertEqual(by_id["B0a"]["t_over_r_us"], "10690503.200")
            self.assertEqual(
                by_id["B0a"]["t_over_r_n_active_us"],
                "5219.972265625",
            )
            self.assertEqual(by_id["B1"]["speedup_vs_b0a"], "1.747647")
            self.assertEqual(by_id["B1"]["pair_failures"], "0")
            self.assertEqual(by_id["B1"]["pair_trials"], "10")
            self.assertEqual(
                by_id["B1"]["primary_metric"],
                "T_complete_bootstrap/(r*N_active)",
            )
            self.assertEqual(by_id["B1"]["metric_unit"], "us")
            self.assertEqual(
                by_id["B1"]["performance_claim"],
                "HISTORICAL_WSL_HIGHSTAT_NOT_FORMAL_NATIVE_PERFORMANCE",
            )

    def test_changed_b1_numeric_row_is_rejected_semantically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_inputs(root)
            path = (
                root
                / "repro/stage331_current_head_highstat_refresh/summary.csv"
            )
            self._rewrite_csv(
                path,
                lambda rows: rows[0].__setitem__(
                    "t_bootstrap_over_r_mean_us",
                    "6117083.426",
                ),
            )
            with patch.object(
                baseline,
                "EXPECTED_ANCHORS",
                self._patched_hashes(root),
            ):
                with self.assertRaisesRegex(
                    baseline.BaselineEvidenceError,
                    "B1 numeric row",
                ):
                    baseline.build_d0_artifacts(root, root / "out")

    def test_nonzero_historical_pair_failure_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_inputs(root)
            path = (
                root
                / "repro/stage331_current_head_highstat_refresh/summary.csv"
            )
            self._rewrite_csv(
                path,
                lambda rows: rows[0].__setitem__(
                    "noise_pair_failures",
                    "1",
                ),
            )
            with patch.object(
                baseline,
                "EXPECTED_ANCHORS",
                self._patched_hashes(root),
            ):
                with self.assertRaisesRegex(
                    baseline.BaselineEvidenceError,
                    "pair-failure",
                ):
                    baseline.build_d0_artifacts(root, root / "out")

    def test_duplicate_artifact_rows_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_inputs(root)
            path = (
                root
                / "repro/stage331_current_head_highstat_refresh/summary.csv"
            )

            def duplicate(rows):
                rows.append(dict(rows[0]))

            self._rewrite_csv(path, duplicate)
            with patch.object(
                baseline,
                "EXPECTED_ANCHORS",
                self._patched_hashes(root),
            ):
                with self.assertRaisesRegex(
                    baseline.BaselineEvidenceError,
                    "duplicate artifact rows",
                ):
                    baseline.build_d0_artifacts(root, root / "out")

    def test_missing_trailing_csv_cell_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_inputs(root)
            path = (
                root
                / "repro/candidate_c_rank_bounded_gate/terminal_record.csv"
            )
            with path.open("r", encoding="ascii", newline="") as handle:
                rows = list(csv.reader(handle, strict=True))
            rows[1] = rows[1][:-1]
            with path.open("w", encoding="ascii", newline="") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerows(rows)
            with patch.object(
                baseline,
                "EXPECTED_ANCHORS",
                self._patched_hashes(root),
            ):
                with self.assertRaisesRegex(
                    baseline.BaselineEvidenceError,
                    "malformed artifact row",
                ):
                    baseline.build_d0_artifacts(root, root / "out")

    def test_artifacts_are_ascii_lf_only_and_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as first_tmp:
            with tempfile.TemporaryDirectory() as second_tmp:
                first = Path(first_tmp)
                second = Path(second_tmp)
                baseline.build_d0_artifacts(ROOT, first)
                baseline.build_d0_artifacts(ROOT, second)
                relatives = (
                    "docs/candidate_d_d0_baseline.md",
                    "repro/candidate_d_admission/baseline_manifest.csv",
                    "repro/candidate_d_admission/environment.csv",
                    "repro/candidate_d_admission/reproduction_commands.md",
                )
                for relative in relatives:
                    with self.subTest(relative=relative):
                        first_bytes = (first / relative).read_bytes()
                        second_bytes = (second / relative).read_bytes()
                        self.assertEqual(first_bytes, second_bytes)
                        first_bytes.decode("ascii")
                        self.assertNotIn(b"\r", first_bytes)
                        self.assertTrue(first_bytes.endswith(b"\n"))

    def test_artifacts_ignore_hostile_decimal_context(self):
        with tempfile.TemporaryDirectory() as expected_tmp:
            with tempfile.TemporaryDirectory() as hostile_tmp:
                expected = Path(expected_tmp)
                hostile = Path(hostile_tmp)
                baseline.build_d0_artifacts(ROOT, expected)
                with localcontext() as context:
                    context.prec = 6
                    context.rounding = ROUND_DOWN
                    baseline.build_d0_artifacts(ROOT, hostile)
                relatives = (
                    "docs/candidate_d_d0_baseline.md",
                    "repro/candidate_d_admission/baseline_manifest.csv",
                    "repro/candidate_d_admission/environment.csv",
                    "repro/candidate_d_admission/reproduction_commands.md",
                )
                for relative in relatives:
                    with self.subTest(relative=relative):
                        self.assertEqual(
                            (expected / relative).read_bytes(),
                            (hostile / relative).read_bytes(),
                        )

    def test_reproduction_commands_separate_smoke_from_performance(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            baseline.build_d0_artifacts(ROOT, out)
            environment_path = (
                out / "repro/candidate_d_admission/environment.csv"
            )
            with environment_path.open(
                "r",
                encoding="ascii",
                newline="",
            ) as handle:
                environment_rows = list(
                    csv.DictReader(handle, strict=True)
                )
            environment = {
                row["key"]: row["value"] for row in environment_rows
            }
            self.assertEqual(
                environment["wsl_smoke_disposition"],
                "ENVIRONMENT_BLOCKED",
            )
            self.assertEqual(
                environment["wsl_smoke_failure_reason"],
                (
                    "ATTEMPT_INTERRUPTED_AFTER_TRACKED_STAGE33_OUTPUT_WRITE;"
                    "NO_VALID_ISOLATED_SMOKE_RESULT"
                ),
            )
            self.assertEqual(
                environment["stage33_restoration"],
                "VERIFIED_1164B3F_GIT_BLOB_IDENTITY",
            )
            commands = (
                out
                / "repro/candidate_d_admission/reproduction_commands.md"
            ).read_text(encoding="ascii")
            required = (
                "python -m unittest discover -s tests/research -v",
                "bash scripts/run_stage33_current_smoke.sh",
                "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false",
                "KEY=BINARY PARAM=SET_2_3_2048",
                "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true",
                "MAT_TRGSW_AVX512_SUB_DECOMP=true",
                "MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true",
                "SAB_PVW_BACKEND_FROM_DFT_ADD=true",
                "SAB_PVW_SUB_DECOMP_FUSION=true",
                "SAB_PVW_DUAL_SUB_CMUX=true",
                "SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true",
                "SAB_PVW_TARGET_TEST=true -j$(nproc)",
                "./main",
                (
                    "SAB_PVW target full bootstrap binary lane "
                    "equivalence ... Pass"
                ),
                "ENVIRONMENT_BLOCKED",
            )
            for token in required:
                with self.subTest(token=token):
                    self.assertIn(token, commands)
            self.assertIn("not formal performance evidence", commands)
            self.assertIn(
                "do not run it with the tracked Stage 33 output directory",
                commands,
            )
            self.assertIn(
                "STAGE33_OUT_DIR=/tmp/candidate-d-stage33-smoke",
                commands,
            )
            self.assertIn(
                "NO_VALID_ISOLATED_SMOKE_RESULT",
                commands,
            )


if __name__ == "__main__":
    unittest.main()
