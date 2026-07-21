from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

import scripts.apply_candidate_d_admission as closeout
from scripts.mat_sab_research_state import load_state, validate_state, write_state
from scripts.run_candidate_d_admission import (
    ADMIT,
    BLOCK,
    REJECT_BINDING_NOISE_SECURITY,
    REJECT_CLOSURE,
    REJECT_COMPLETE_COST,
    REJECT_PRIOR_ART,
    evaluate_candidate_d_admission,
)


ROOT = Path(__file__).resolve().parents[2]
CONTROLLER_COMMIT = subprocess.run(
    [
        "git",
        "log",
        "-1",
        "--format=%H",
        "--",
        "scripts/run_candidate_d_admission.py",
        "scripts/apply_candidate_d_admission.py",
        "research/mat_sab/candidate_d_stage_replay.py",
        "docs/candidate_d_task9_replay_contract.md",
    ],
    cwd=ROOT,
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
RUN_DATE = "2026-07-21"
EXECUTION_PLATFORM = (
    "Windows-PowerShell; CPython-3.12; evidence-controller-only; "
    "no-performance-claim"
)
RUN_HEADER = (ROOT / "repro/run_log.csv").read_text(encoding="ascii").splitlines()[0]


class CandidateDCloseoutTests(unittest.TestCase):
    def setUp(self):
        self.result = evaluate_candidate_d_admission(
            ROOT,
            input_commit=closeout.CURRENT_INPUT_COMMIT,
            controller_commit=CONTROLLER_COMMIT,
            run_date=RUN_DATE,
            execution_platform=EXECUTION_PLATFORM,
        )
        self.assertEqual(self.result.decision, BLOCK)

    def _route_result(self, decision: str):
        passing = replace(
            self.result,
            d1_status="PASS",
            d1_decision="PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE",
            d1_missing_evidence=(),
            d2_status="PASS",
            d2_decision="PASS_D2_OPERATOR_CLOSURE_G_LE_4",
            d2_replay_authenticated=True,
            d3_replay_authenticated=True,
            gamma_count=2,
            negative_controls_status="PASS",
            binding_status="PASS",
            security_status="PASS",
            noise_status="PASS",
            complete_cost_status="PASS",
            resource_status="PASS",
            pessimistic_projection="1.10",
            decision=ADMIT,
            resume_condition="none",
        )
        changes = {
            ADMIT: {},
            REJECT_PRIOR_ART: {
                "d1_status": "REJECT",
                "d1_decision": "REJECT_D1_CANDIDATE_D_SUBSUMED_BY_PRIOR_WORK",
                "d2_status": "SKIPPED_D1_REJECT",
                "d2_decision": "",
                "gamma_count": None,
                "negative_controls_status": "SKIPPED_D1_REJECT",
                "binding_status": "SKIPPED_D1_REJECT",
                "security_status": "SKIPPED_D1_REJECT",
                "noise_status": "SKIPPED_D1_REJECT",
                "complete_cost_status": "SKIPPED_D1_REJECT",
                "resource_status": "SKIPPED_D1_REJECT",
                "pessimistic_projection": "",
                "decision": REJECT_PRIOR_ART,
            },
            REJECT_CLOSURE: {
                "d2_status": "REJECT",
                "d2_decision": "REJECT_D2_PHASE_EQUIVALENCE",
                "binding_status": "SKIPPED_D2_REJECT",
                "security_status": "SKIPPED_D2_REJECT",
                "noise_status": "SKIPPED_D2_REJECT",
                "complete_cost_status": "SKIPPED_D2_REJECT",
                "resource_status": "SKIPPED_D2_REJECT",
                "pessimistic_projection": "",
                "decision": REJECT_CLOSURE,
            },
            REJECT_BINDING_NOISE_SECURITY: {
                "binding_status": "REJECT",
                "decision": REJECT_BINDING_NOISE_SECURITY,
            },
            REJECT_COMPLETE_COST: {
                "complete_cost_status": "REJECT",
                "pessimistic_projection": "1.09",
                "decision": REJECT_COMPLETE_COST,
            },
            BLOCK: {
                "noise_status": "BLOCK",
                "decision": BLOCK,
                "resume_condition": "Regenerate the blocked D3 noise evidence.",
            },
        }
        return replace(passing, **changes[decision])

    def _root(self, directory: str, result=None) -> Path:
        selected = self.result if result is None else result
        root = Path(directory)
        (root / "hypotheses").mkdir(parents=True)
        (root / "repro").mkdir(parents=True)
        (root / "hypotheses/hypothesis_register.yaml").write_bytes(
            b"# hypotheses\n"
        )
        (root / "repro/artifact_manifest.md").write_bytes(b"# artifacts\n")
        (root / "repro/reproduction_checklist.md").write_bytes(
            b"# checklist\n"
        )
        (root / "repro/run_log.csv").write_bytes(
            (RUN_HEADER + "\n").encode("ascii")
        )
        state = load_state(ROOT / "research_state.yaml")
        state["goal_status"] = "ACTIVE"
        state["active_candidate"] = "D"
        state["paper_gate"] = "BLOCKED"
        state["production_hot_path_permission"] = False
        last_reached = closeout._expected_last_reached(selected)
        decisions = {
            "PLAN_APPROVED": "CANDIDATE_D_WRITTEN_SPEC_AND_IMPLEMENTATION_PLAN_APPROVED",
            "D0_BASELINE_FROZEN": "PASS_D0_CANDIDATE_D_BASELINES_FROZEN",
            "D1_NOVELTY_AUDIT_PASS": (
                "PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE"
            ),
            "D2_OPERATOR_CLOSURE_PASS": "PASS_D2_OPERATOR_CLOSURE_G_LE_4",
        }
        sources = {
            "PLAN_APPROVED": "DESIGN_APPROVED_PENDING_WRITTEN_SPEC_REVIEW",
            "D0_BASELINE_FROZEN": "PLAN_APPROVED",
            "D1_NOVELTY_AUDIT_PASS": "D0_BASELINE_FROZEN",
            "D2_OPERATOR_CLOSURE_PASS": "D1_NOVELTY_AUDIT_PASS",
        }
        state["last_decision"] = decisions[last_reached]
        state["last_decision_source_status"] = sources[last_reached]
        state["candidates"]["D"]["status"] = last_reached
        state["candidates"]["D"]["last_reached_status"] = last_reached
        state["candidates"]["E"]["status"] = "RESERVED_FALLBACK_NOT_STARTED"
        state["candidates"]["E"]["last_reached_status"] = (
            "RESERVED_FALLBACK_NOT_STARTED"
        )
        write_state(root / "research_state.yaml", state)
        return root

    def _apply(self, root: Path, result=None) -> str:
        selected = self.result if result is None else result
        with (
            patch.object(
                closeout, "verify_candidate_d_artifacts", return_value=selected
            ),
            patch.object(closeout, "_validate_historical_block_ledgers"),
        ):
            return closeout.apply_candidate_d_decision(root, selected)

    @staticmethod
    def _snapshot(root: Path) -> dict[str, bytes]:
        paths = (
            "research_state.yaml",
            "hypotheses/hypothesis_register.yaml",
            "repro/artifact_manifest.md",
            "repro/reproduction_checklist.md",
            "repro/run_log.csv",
        )
        return {path: (root / path).read_bytes() for path in paths}

    def test_block_preserves_d0_and_does_not_activate_e(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            self.assertEqual(self._apply(root), BLOCK)
            state = load_state(root / "research_state.yaml")
            self.assertEqual(state["goal_status"], "EXTERNAL_BLOCKED")
            self.assertEqual(state["active_candidate"], "D")
            self.assertEqual(state["paper_gate"], "BLOCKED")
            self.assertFalse(state["production_hot_path_permission"])
            self.assertEqual(
                state["candidates"]["D"]["status"],
                "D0_BASELINE_FROZEN",
            )
            self.assertEqual(
                state["candidates"]["D"]["last_reached_status"],
                "D0_BASELINE_FROZEN",
            )
            self.assertEqual(
                state["candidates"]["E"]["status"],
                "RESERVED_FALLBACK_NOT_STARTED",
            )
            self.assertEqual(state["last_decision"], BLOCK)
            self.assertEqual(
                state["last_decision_source_status"],
                "D0_BASELINE_FROZEN",
            )
            validate_state(state)

    def test_all_six_terminal_routes_apply_route_specific_state_and_ledgers(self):
        decisions = (
            ADMIT,
            REJECT_PRIOR_ART,
            REJECT_CLOSURE,
            REJECT_BINDING_NOISE_SECURITY,
            REJECT_COMPLETE_COST,
            BLOCK,
        )
        for decision in decisions:
            with self.subTest(decision=decision):
                result = self._route_result(decision)
                with tempfile.TemporaryDirectory() as directory:
                    root = self._root(directory, result)
                    self.assertEqual(self._apply(root, result), decision)
                    state = load_state(root / "research_state.yaml")
                    self.assertEqual(state["last_decision"], decision)
                    if decision == ADMIT:
                        self.assertEqual(state["active_candidate"], "D")
                        self.assertTrue(state["production_hot_path_permission"])
                        self.assertEqual(
                            state["candidates"]["D"]["status"],
                            "D3_ADMISSION_PASS",
                        )
                    elif decision == BLOCK:
                        self.assertEqual(state["active_candidate"], "D")
                        self.assertEqual(state["goal_status"], "EXTERNAL_BLOCKED")
                        self.assertFalse(state["production_hot_path_permission"])
                    else:
                        self.assertEqual(state["active_candidate"], "E")
                        self.assertEqual(
                            state["candidates"]["D"]["status"], "REJECTED"
                        )
                        self.assertEqual(
                            state["candidates"]["E"]["status"],
                            "SECURITY_NOVELTY_PREFLIGHT",
                        )
                    ledgers = "\n".join(
                        (root / relative).read_text(encoding="ascii")
                        for relative in (*closeout.LEDGER_PATHS, closeout.RUN_LOG_PATH)
                    )
                    self.assertIn(decision, ledgers)
                    if decision != BLOCK:
                        self.assertNotIn(
                            "D1 is externally blocked only by the missing",
                            ledgers,
                        )

    def test_admit_second_apply_is_byte_for_byte_idempotent(self):
        result = self._route_result(ADMIT)
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory, result)
            self._apply(root, result)
            first = self._snapshot(root)
            self._apply(root, result)
            self.assertEqual(self._snapshot(root), first)

    def test_committed_block_resumes_by_appending_a_new_terminal_record(self):
        resumed = replace(
            self._route_result(ADMIT),
            input_commit="a" * 40,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            self._apply(root)
            historical = self._snapshot(root)

            self._apply(root, resumed)
            first_resumed = self._snapshot(root)
            state = load_state(root / "research_state.yaml")
            self.assertEqual(state["goal_status"], "ACTIVE")
            self.assertEqual(state["active_candidate"], "D")
            self.assertTrue(state["production_hot_path_permission"])
            self.assertEqual(
                state["candidates"]["D"]["status"], "D3_ADMISSION_PASS"
            )
            for relative in closeout.LEDGER_PATHS:
                before = historical[relative]
                after = first_resumed[relative]
                self.assertIn(before, after)
                self.assertIn(resumed.input_commit[:12].encode("ascii"), after)
            run_log = first_resumed[closeout.RUN_LOG_PATH].decode("ascii")
            self.assertIn(closeout.RUN_MARKER, run_log)
            self.assertIn(
                closeout._run_marker_for(resumed),
                run_log,
            )

            self._apply(root, resumed)
            self.assertEqual(self._snapshot(root), first_resumed)

    def test_resumed_same_input_divergence_and_old_replay_are_rejected(self):
        resumed = replace(
            self._route_result(ADMIT),
            input_commit="b" * 40,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            self._apply(root)
            self._apply(root, resumed)
            before = self._snapshot(root)

            divergent = replace(
                resumed,
                complete_cost_status="REJECT",
                pessimistic_projection="1.09",
                decision=REJECT_COMPLETE_COST,
            )
            with self.assertRaises(ValueError):
                self._apply(root, divergent)
            with self.assertRaises(ValueError):
                self._apply(root, self.result)
            self.assertEqual(self._snapshot(root), before)

    def test_resume_rejects_unrelated_external_block_state(self):
        resumed = replace(
            self._route_result(ADMIT),
            input_commit="c" * 40,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            self._apply(root)
            state = load_state(root / "research_state.yaml")
            state["last_decision_source_status"] = "PLAN_APPROVED"
            (root / "research_state.yaml").write_text(
                json.dumps(state, indent=2) + "\n", encoding="ascii"
            )
            before = self._snapshot(root)
            with self.assertRaises(ValueError):
                self._apply(root, resumed)
            self.assertEqual(self._snapshot(root), before)

    def test_admit_divergent_second_apply_is_rejected_without_mutation(self):
        result = self._route_result(ADMIT)
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory, result)
            self._apply(root, result)
            before = self._snapshot(root)
            divergent = replace(
                result,
                complete_cost_status="REJECT",
                pessimistic_projection="1.09",
                decision=REJECT_COMPLETE_COST,
            )
            with self.assertRaises(ValueError):
                self._apply(root, divergent)
            self.assertEqual(self._snapshot(root), before)

    def test_identical_second_apply_is_byte_for_byte_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            self._apply(root)
            first = self._snapshot(root)
            self._apply(root)
            self.assertEqual(self._snapshot(root), first)
            marker_specs = (
                (
                    "hypotheses/hypothesis_register.yaml",
                    closeout.HYPOTHESIS_START,
                    closeout.HYPOTHESIS_END,
                ),
                (
                    "repro/artifact_manifest.md",
                    closeout.MANIFEST_START,
                    closeout.MANIFEST_END,
                ),
                (
                    "repro/reproduction_checklist.md",
                    closeout.CHECKLIST_START,
                    closeout.CHECKLIST_END,
                ),
                (
                    "hypotheses/hypothesis_register.yaml",
                    closeout.ERRATUM_HYPOTHESIS_START,
                    closeout.ERRATUM_HYPOTHESIS_END,
                ),
                (
                    "repro/reproduction_checklist.md",
                    closeout.ERRATUM_CHECKLIST_START,
                    closeout.ERRATUM_CHECKLIST_END,
                ),
            )
            for relative, start, end in marker_specs:
                text = (root / relative).read_text(encoding="ascii")
                self.assertEqual(text.count(start), 1)
                self.assertEqual(text.count(end), 1)
            run_log = (root / "repro/run_log.csv").read_text(encoding="ascii")
            self.assertEqual(run_log.count(closeout.RUN_MARKER), 1)

    def test_divergent_second_apply_is_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            self._apply(root)
            before = self._snapshot(root)
            divergent = replace(
                self.result,
                d1_status="PASS",
                d1_decision=(
                    "PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE"
                ),
                d1_missing_evidence=(),
                d2_status="PASS",
                d2_decision="PASS_D2_OPERATOR_CLOSURE_G_LE_4",
                gamma_count=2,
                negative_controls_status="PASS",
                binding_status="PASS",
                security_status="PASS",
                noise_status="PASS",
                complete_cost_status="PASS",
                resource_status="PASS",
                pessimistic_projection="1.10",
                decision=ADMIT,
                resume_condition="none",
            )
            with self.assertRaises(ValueError):
                self._apply(root, divergent)
            self.assertEqual(self._snapshot(root), before)

    def test_partial_or_changed_ledger_marker_is_rejected(self):
        cases = (
            closeout.HYPOTHESIS_START + "\n",
            (
                closeout.HYPOTHESIS_START
                + "\nchanged\n"
                + closeout.HYPOTHESIS_END
                + "\n"
            ),
        )
        for content in cases:
            with self.subTest(content=content):
                with tempfile.TemporaryDirectory() as directory:
                    root = self._root(directory)
                    path = root / "hypotheses/hypothesis_register.yaml"
                    path.write_text(content, encoding="ascii")
                    before = self._snapshot(root)
                    with self.assertRaises(ValueError):
                        self._apply(root)
                    self.assertEqual(self._snapshot(root), before)

    def test_run_log_marker_with_different_content_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            run_log = root / "repro/run_log.csv"
            run_log.write_text(
                RUN_HEADER + "\n" + closeout.RUN_MARKER + ",changed\n",
                encoding="ascii",
            )
            before = self._snapshot(root)
            with self.assertRaises(ValueError):
                self._apply(root)
            self.assertEqual(self._snapshot(root), before)

    def test_historical_block_bytes_reject_any_field_mutation(self):
        paths = (*closeout.LEDGER_PATHS, closeout.RUN_LOG_PATH)
        canonical = {
            relative: closeout._git_blob(
                ROOT, closeout.HISTORICAL_BLOCK_COMMIT, relative
            )
            for relative in paths
        }
        closeout._validate_historical_block_ledgers(ROOT, canonical)
        mutations = (
            (
                "hypotheses/hypothesis_register.yaml",
                b"primary_metric: complete_sab_T_bootstrap_div_rN_active",
                b"primary_metric: changed_metric",
            ),
            (
                closeout.RUN_LOG_PATH,
                b"python-stdlib-evidence-controller",
                b"changed-backend",
            ),
        )
        for relative, old, new in mutations:
            with self.subTest(relative=relative):
                changed = dict(canonical)
                self.assertIn(old, changed[relative])
                changed[relative] = changed[relative].replace(old, new, 1)
                with self.assertRaises(ValueError):
                    closeout._validate_historical_block_ledgers(ROOT, changed)

    def test_historical_erratum_is_complete_bounded_and_byte_idempotent(self):
        contents = closeout._erratum_contents(self.result)
        self.assertEqual(
            tuple(relative for relative, *_ in contents),
            (
                "hypotheses/hypothesis_register.yaml",
                "repro/reproduction_checklist.md",
            ),
        )
        joined = "\n".join(content for *_, content in contents)
        self.assertIn("historical and superseded", joined)
        self.assertIn("D0 PASS", joined)
        self.assertIn("D1 BLOCK", joined)
        self.assertIn("D2/D3 SKIPPED/NOT_REACHED", joined)
        self.assertIn("production permission is false", joined)
        self.assertIn("docs/candidate_d_admission_report.md", joined)
        self.assertIn(closeout._generator_command(self.result), joined)
        self.assertIn(closeout._apply_command(self.result), joined)
        joined.encode("ascii")

        for relative, start, end, content in contents:
            before = (ROOT / relative).read_bytes()
            first = closeout._plan_bounded_append(
                before, start, end, content, relative
            )
            second = closeout._plan_bounded_append(
                first, start, end, content, relative
            )
            self.assertEqual(first, second)
            self.assertEqual(first.count(start.encode("ascii")), 1)
            self.assertEqual(first.count(end.encode("ascii")), 1)

    def test_new_controller_supersedes_exact_prior_erratum_in_place(self):
        prior = replace(
            self.result,
            controller_commit="47173c44729430c23d7078d8cc4368dabd0fa528",
        )
        current = replace(self.result, controller_commit="b" * 40)
        prior_contents = {
            relative: (start, end, content)
            for relative, start, end, content in closeout._erratum_contents(prior)
        }
        for relative, start, end, content in closeout._erratum_contents(current):
            prior_start, prior_end, prior_content = prior_contents[relative]
            self.assertEqual((prior_start, prior_end), (start, end))
            ledger = closeout._plan_bounded_append(
                b"# ledger\n", start, end, prior_content, relative
            )
            updated = closeout._plan_superseding_erratum(
                ledger,
                start,
                end,
                content,
                relative,
                current,
            )
            replayed = closeout._plan_superseding_erratum(
                updated,
                start,
                end,
                content,
                relative,
                current,
            )
            self.assertEqual(updated, replayed)
            self.assertEqual(updated.count(start.encode("ascii")), 1)
            self.assertIn(("--controller-commit " + "b" * 40).encode(), updated)
            self.assertNotIn(prior.controller_commit.encode(), updated)

    def test_erratum_plan_preserves_exact_historical_blocks_and_run_row(self):
        planned = closeout._plan_closeout(ROOT, self.result)
        current = {
            relative: (ROOT / relative).read_bytes()
            for relative in (*closeout.LEDGER_PATHS, closeout.RUN_LOG_PATH)
        }
        after = dict(current)
        for path, content in planned.items():
            relative = path.relative_to(ROOT).as_posix()
            if relative in after:
                after[relative] = content
        closeout._validate_historical_block_ledgers(ROOT, after)
        self.assertEqual(after[closeout.RUN_LOG_PATH], current[closeout.RUN_LOG_PATH])
        for relative, start, end, _content in closeout._erratum_contents(
            self.result
        ):
            self.assertIn(start.encode("ascii"), after[relative])
            self.assertIn(end.encode("ascii"), after[relative])

    def test_real_resumed_reject_verifier_apply_check_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            clone = Path(directory) / "repo"
            subprocess.run(
                ["git", "clone", "-q", "--shared", str(ROOT), str(clone)],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Candidate D integration"],
                cwd=clone,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "config",
                    "user.email",
                    "candidate-d-integration@example.invalid",
                ],
                cwd=clone,
                check=True,
            )
            literature = textwrap.dedent(
                """
                PASS_D1 = "PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE"
                REJECT_D1 = "REJECT_D1_CANDIDATE_D_SUBSUMED_BY_PRIOR_WORK"
                BLOCK_D1 = "BLOCK_D1_REQUIRED_FULLTEXT_OR_REVIEW_MISSING"
                """
            ).lstrip()
            runner = textwrap.dedent(
                '''
                # Integration fixture only: it exercises D1 REJECT routing and has
                # no scientific or admission authority.
                from pathlib import Path
                from research.mat_sab.candidate_d_literature import REJECT_D1

                OUTPUTS = {
                    Path("docs/candidate_d_d1_novelty_audit.md"): b"# Non-scientific D1 reject integration fixture\\n",
                    Path("repro/candidate_d_admission/literature_sources.csv"): (
                        b"source_id,title,year,official_url,fulltext_url,registry_status,verification_status,pdf_sha256,text_sha256,page_range,source_binding_sha256,validation_errors\\n"
                        b"FIXTURE,fixture,2026,fixture,fixture,TEST_ONLY,FULLTEXT_REVIEWED,,,1,,\\n"
                    ),
                    Path("repro/candidate_d_admission/claim_overlap.csv"): b"fixture,status\\nnon_scientific,REJECT\\n",
                    Path("repro/candidate_d_admission/novelty_gate.csv"): b"decision\\nREJECT_D1_CANDIDATE_D_SUBSUMED_BY_PRIOR_WORK\\n",
                }

                def build_candidate_d_d1_artifacts(root):
                    return REJECT_D1, OUTPUTS
                '''
            ).lstrip()
            (clone / "research/mat_sab/candidate_d_literature.py").write_text(
                literature, encoding="ascii", newline=""
            )
            (clone / "scripts/run_candidate_d_d1_literature.py").write_text(
                runner, encoding="ascii", newline=""
            )
            fixture_outputs = {
                Path("docs/candidate_d_d1_novelty_audit.md"): (
                    b"# Non-scientific D1 reject integration fixture\n"
                ),
                Path("repro/candidate_d_admission/literature_sources.csv"): (
                    b"source_id,title,year,official_url,fulltext_url,registry_status,verification_status,pdf_sha256,text_sha256,page_range,source_binding_sha256,validation_errors\n"
                    b"FIXTURE,fixture,2026,fixture,fixture,TEST_ONLY,FULLTEXT_REVIEWED,,,1,,\n"
                ),
                Path("repro/candidate_d_admission/claim_overlap.csv"): (
                    b"fixture,status\nnon_scientific,REJECT\n"
                ),
                Path("repro/candidate_d_admission/novelty_gate.csv"): (
                    b"decision\nREJECT_D1_CANDIDATE_D_SUBSUMED_BY_PRIOR_WORK\n"
                ),
            }
            for relative, content in fixture_outputs.items():
                path = clone / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            subprocess.run(["git", "add", "-u"], cwd=clone, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "fixture: D1 reject resume route"],
                cwd=clone,
                check=True,
            )
            input_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=clone,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            common = [
                "--root",
                str(clone),
                "--input-commit",
                input_commit,
                "--controller-commit",
                CONTROLLER_COMMIT,
                "--run-date",
                RUN_DATE,
                "--execution-platform",
                EXECUTION_PLATFORM,
            ]
            generate = [
                sys.executable,
                str(clone / "scripts/run_candidate_d_admission.py"),
                *common,
            ]
            apply = [
                sys.executable,
                str(clone / "scripts/apply_candidate_d_admission.py"),
                *common,
            ]
            def run_checked(command: list[str]) -> None:
                completed = subprocess.run(
                    command,
                    cwd=clone,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    completed.returncode,
                    0,
                    msg=completed.stdout + completed.stderr,
                )

            run_checked(generate)
            run_checked([*apply, "--check"])
            run_checked(apply)
            run_checked([*apply, "--check"])
            first = self._snapshot(clone)
            run_checked(apply)
            run_checked([*apply, "--check"])
            self.assertEqual(self._snapshot(clone), first)
            state = load_state(clone / "research_state.yaml")
            self.assertEqual(state["active_candidate"], "E")
            self.assertFalse(state["production_hot_path_permission"])
            self.assertEqual(state["candidates"]["D"]["status"], "REJECTED")

    def test_write_failure_rolls_back_all_closeout_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            before = self._snapshot(root)
            original = closeout._write_bytes_atomic
            calls = 0

            def fail_on_third(path, content):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("injected write failure")
                return original(path, content)

            with patch.object(
                closeout,
                "verify_candidate_d_artifacts",
                return_value=self.result,
            ), patch.object(closeout, "_write_bytes_atomic", side_effect=fail_on_third):
                with self.assertRaisesRegex(OSError, "injected"):
                    closeout.apply_candidate_d_decision(root, self.result)
            self.assertEqual(self._snapshot(root), before)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_ledger_parent_outside_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = self._root(str(base / "repo"))
            outside = base / "outside"
            outside.mkdir()
            hypotheses = root / "hypotheses"
            for child in hypotheses.iterdir():
                child.unlink()
            hypotheses.rmdir()
            try:
                hypotheses.symlink_to(outside, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlinks unavailable: {error}")
            with self.assertRaises(ValueError):
                self._apply(root)
            self.assertEqual(tuple(outside.iterdir()), ())

    def test_closeout_text_is_ascii_and_names_exact_resume_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            self._apply(root)
            for relative in (
                "hypotheses/hypothesis_register.yaml",
                "repro/artifact_manifest.md",
                "repro/reproduction_checklist.md",
                "repro/run_log.csv",
            ):
                data = (root / relative).read_bytes()
                data.decode("ascii")
                self.assertNotIn(b"\r", data)
            joined = "\n".join(
                (root / relative).read_text(encoding="ascii")
                for relative in (
                    "hypotheses/hypothesis_register.yaml",
                    "repro/reproduction_checklist.md",
                )
            )
            self.assertIn("NTRU_AMORT_2026_068", joined)
            self.assertIn("NTRU_AMORT_FULLTEXT_PATH", joined)
            self.assertIn("latest second revision", joined)
            self.assertIn("2026-07-16", joined)
            self.assertNotIn("Candidate E is active", joined)

    def test_cli_requires_explicit_input_commit(self):
        with self.assertRaises(SystemExit):
            closeout.main([])


if __name__ == "__main__":
    unittest.main()
