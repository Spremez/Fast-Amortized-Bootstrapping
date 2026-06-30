#!/usr/bin/env python3
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "repro" / "final_goal_completion_audit.csv"
OUT_MD = ROOT / "docs" / "final_goal_completion_audit.md"

READINESS = ROOT / "repro" / "stage27_completion_readiness_audit.csv"
PERFORMANCE = ROOT / "repro" / "stage27_final_evidence_package" / "performance_scope.csv"
NOISE = ROOT / "repro" / "stage27_final_evidence_package" / "noise_scope.csv"
RESOURCE = ROOT / "repro" / "stage27_final_evidence_package" / "resource_scope.csv"
CLAIMS = ROOT / "repro" / "stage27_final_evidence_package" / "claim_scope.csv"
MANIFEST = ROOT / "repro" / "stage27_final_evidence_package" / "manifest.csv"
STAGE28 = ROOT / "repro" / "stage28_native_perf_counter_gate" / "summary.csv"
EXTERNAL = ROOT / "repro" / "external_evidence_intake" / "summary.csv"
STAGE101_CB5 = ROOT / "repro" / "stage101_cb5_remote_native_perf" / "summary.csv"
STAGE102_686_REVIEW = ROOT / "repro" / "stage102_686_source_anchor_review" / "summary.csv"
STAGE103_NOVELTY_REVIEW = ROOT / "repro" / "stage103_related_work_novelty_review" / "summary.csv"
STAGE33 = ROOT / "repro" / "stage33_current_smoke" / "summary.csv"
STAGE36_TARGET_PERF = ROOT / "repro" / "stage36_target_perf_summary.csv"
STAGE36_TARGET_NOISE = ROOT / "repro" / "stage36_target_noise_seeds50" / "aggregate.csv"
STAGE36_STAGE_NOISE = ROOT / "repro" / "stage36_stage_noise_seeds10" / "aggregate.csv"
STAGE36_RESOURCE = ROOT / "repro" / "stage36_resource_summary.csv"
STAGE36_ADDED_PERF = ROOT / "repro" / "stage36_added_params_runs10_seeds20" / "performance_stats.csv"
STAGE36_ADDED_NOISE = ROOT / "repro" / "stage36_added_params_runs10_seeds20" / "noise_summary.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"


@dataclass
class AuditRow:
    item_id: str
    category: str
    requirement: str
    status: str
    evidence: str
    scope: str
    remaining_action: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_csv_if_exists(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return read_csv(path)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_csv(path: Path, rows: list[AuditRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "item_id",
                "category",
                "requirement",
                "status",
                "evidence",
                "scope",
                "remaining_action",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def row_by(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    for row in rows:
        if row.get(key) == value:
            return row
    return None


def rows_by(rows: list[dict[str, str]], key: str, value: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get(key) == value]


def as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "nan"))


def as_int(row: dict[str, str], key: str) -> int:
    return int(float(row.get(key, "0")))


def existing_manifest_paths(rows: list[dict[str, str]]) -> tuple[bool, str]:
    missing = []
    for row in rows:
        path = row.get("path", "")
        if path and not (ROOT / path).exists():
            missing.append(path)
    if missing:
        return False, "; ".join(missing)
    return True, "all final package manifest paths exist"


def audit() -> list[AuditRow]:
    readiness = read_csv(READINESS)
    performance = read_csv(PERFORMANCE)
    noise = read_csv(NOISE)
    resource = read_csv(RESOURCE)
    claims = read_csv(CLAIMS)
    manifest = read_csv(MANIFEST)
    stage28 = read_csv(STAGE28)
    external = read_csv_if_exists(EXTERNAL)
    stage101 = read_csv_if_exists(STAGE101_CB5)
    stage102 = read_csv_if_exists(STAGE102_686_REVIEW)
    stage103 = read_csv_if_exists(STAGE103_NOVELTY_REVIEW)
    stage33 = read_csv_if_exists(STAGE33)
    run_log = read_csv(RUN_LOG)

    out: list[AuditRow] = []

    final_ready = [
        row
        for row in readiness
        if row.get("category") == "final_standard"
        and row.get("status", "").startswith("SATISFIED")
    ]
    out.append(
        AuditRow(
            "A1",
            "scoped_engineering",
            "Final engineering standards F1-F8 are mapped to evidence",
            "PASS_SCOPED" if len(final_ready) == 8 else "FAIL_INCOMPLETE",
            rel(READINESS),
            f"{len(final_ready)}/8 final standards satisfied or scoped-satisfied",
            "Fill missing final-standard evidence before claiming scoped engineering completion.",
        )
    )

    target_perf = [
        row
        for row in performance
        if row.get("scope") == "target_binary_final_rerun"
        and row.get("param") == "SET_2_3_2048"
        and row.get("r") in {"2", "4"}
        and row.get("status", "").lower() == "pass"
        and as_float(row, "mean_speedup") > 1.0
    ]
    out.append(
        AuditRow(
            "A2",
            "performance",
            "Target complete-SAB r=2/r=4 speedups over repeated scalar are positive under the same backend",
            "PASS_SCOPED" if len(target_perf) == 2 else "FAIL_INCOMPLETE",
            rel(PERFORMANCE),
            "target binary SET_2_3_2048, r=2/r=4, spqlios_avx512 final rerun",
            "Re-run target full-SAB A/B until both r=2 and r=4 pass with positive speedup.",
        )
    )

    stage36_perf = read_csv_if_exists(STAGE36_TARGET_PERF)
    if stage36_perf:
        stage36_target_perf = [
            row
            for row in stage36_perf
            if row.get("r") in {"2", "4"}
            and row.get("decision") == "PASS_TARGET_PERF_10RUN"
            and as_int(row, "samples") >= 10
            and as_float(row, "mean_speedup") > 1.0
        ]
        out.append(
            AuditRow(
                "A2b",
                "performance_high_stat",
                "Stage 36 target complete-SAB r=2/r=4 has 10-run same-backend performance support",
                "PASS_10RUN_TARGET_PERF"
                if len(stage36_target_perf) == 2
                else "FAIL_STAGE36_TARGET_PERF",
                rel(STAGE36_TARGET_PERF),
                "optional stronger statistical target-performance evidence",
                "Fix or rerun Stage 36 target_perf before using 10-run statistical wording.",
            )
        )
    else:
        out.append(
            AuditRow(
                "A2b",
                "performance_high_stat",
                "Stage 36 target complete-SAB r=2/r=4 has 10-run same-backend performance support",
                "NOT_RUN_OPTIONAL",
                "",
                "optional; not required for current scoped engineering claim",
                "Run STAGE36_MODE=target_perf STAGE36_EXECUTE=1 before using 10-run statistical wording.",
            )
        )

    target_noise = [
        row
        for row in noise
        if row.get("scope") == "target_binary_50_seed"
        and row.get("param") == "SET_2_3_2048"
        and row.get("r") in {"2", "4"}
        and row.get("status") == "PASS"
        and as_int(row, "seeds") >= 50
        and as_int(row, "pvw_failures") == 0
        and as_int(row, "scalar_failures") == 0
        and as_int(row, "pair_failures") == 0
    ]
    out.append(
        AuditRow(
            "A3",
            "correctness_noise",
            "Target promoted path has 50-seed final-output noise/correctness support",
            "PASS_SCOPED" if len(target_noise) == 2 else "FAIL_INCOMPLETE",
            rel(NOISE),
            "target binary SET_2_3_2048, r=2/r=4",
            "Expand or rerun final-output noise until both target r values pass 50 seeds.",
        )
    )

    stage36_target_noise = read_csv_if_exists(STAGE36_TARGET_NOISE)
    if stage36_target_noise:
        stage36_target_noise_passed = {
            row.get("r")
            for row in stage36_target_noise
            if row.get("r") in {"2", "4"}
            and row.get("status") == "PASS"
            and as_int(row, "seeds") >= 50
            and as_int(row, "pvw_failures") == 0
            and as_int(row, "scalar_failures") == 0
            and as_int(row, "pair_failures") == 0
        }
        out.append(
            AuditRow(
                "A3c",
                "target_noise_high_stat",
                "Stage 36 target r=2/r=4 final-output noise rerun has 50-seed zero-failure support",
                "PASS_TARGET_NOISE_50SEED"
                if {"2", "4"}.issubset(stage36_target_noise_passed)
                else "FAIL_STAGE36_TARGET_NOISE",
                rel(STAGE36_TARGET_NOISE),
                "optional stronger target final-output noise evidence",
                "Fix or rerun Stage 36 target_noise before using refreshed target-noise statistical wording.",
            )
        )
    else:
        out.append(
            AuditRow(
                "A3c",
                "target_noise_high_stat",
                "Stage 36 target r=2/r=4 final-output noise rerun has 50-seed zero-failure support",
                "NOT_RUN_OPTIONAL",
                "",
                "optional; not required for current scoped engineering claim",
                "Run STAGE36_MODE=target_noise STAGE36_EXECUTE=1 before using refreshed target-noise statistical wording.",
            )
        )

    stage36_stage_noise = read_csv_if_exists(STAGE36_STAGE_NOISE)
    if stage36_stage_noise:
        expected_stages = {
            ("2", "blind_rotate_coeff0"),
            ("2", "extract"),
            ("2", "materialize_tlwe"),
            ("2", "packing_ks"),
            ("2", "hw_ks"),
            ("4", "blind_rotate_coeff0"),
            ("4", "extract"),
            ("4", "materialize_tlwe"),
            ("4", "packing_ks"),
            ("4", "hw_ks"),
        }
        passed_stages = {
            (row.get("r"), row.get("stage"))
            for row in stage36_stage_noise
            if row.get("status") == "PASS"
            and as_int(row, "seeds") >= 10
            and as_int(row, "pair_failures") == 0
        }
        out.append(
            AuditRow(
                "A3b",
                "stage_noise_high_stat",
                "Stage 36 r=2/r=4 stage-level noise has 10-seed zero-failure support",
                "PASS_STAGE_NOISE_10SEED"
                if expected_stages.issubset(passed_stages)
                else "FAIL_STAGE36_STAGE_NOISE",
                rel(STAGE36_STAGE_NOISE),
                "optional stage-level statistical noise evidence",
                "Fix or rerun Stage 36 stage_noise before using stage-by-stage noise wording.",
            )
        )
    else:
        out.append(
            AuditRow(
                "A3b",
                "stage_noise_high_stat",
                "Stage 36 r=2/r=4 stage-level noise has 10-seed zero-failure support",
                "NOT_RUN_OPTIONAL",
                "",
                "optional; not required for current scoped engineering claim",
                "Run STAGE36_MODE=stage_noise STAGE36_EXECUTE=1 before using stage-by-stage noise wording.",
            )
        )

    resource_modes = {
        (row.get("r"), row.get("mode"))
        for row in resource
        if row.get("scope") == "target_binary_resource_smoke"
    }
    expected_resource = {
        ("1", "pvw"),
        ("1", "scalar"),
        ("2", "pvw"),
        ("2", "scalar"),
        ("4", "pvw"),
        ("4", "scalar"),
    }
    out.append(
        AuditRow(
            "A4",
            "resources",
            "Resource snapshot covers scalar and PVW r=1/2/4 key/time/RSS fields",
            "PASS_SMOKE_RESOURCE"
            if expected_resource.issubset(resource_modes)
            else "FAIL_INCOMPLETE",
            rel(RESOURCE),
            "resource smoke, not statistical resource campaign",
            "Repeat resource matrix if final paper requires statistical resource tables.",
        )
    )

    stage36_resource = read_csv_if_exists(STAGE36_RESOURCE)
    if stage36_resource:
        expected = {
            ("1", "pvw"),
            ("1", "scalar"),
            ("2", "pvw"),
            ("2", "scalar"),
            ("4", "pvw"),
            ("4", "scalar"),
        }
        passed = {
            (row.get("r"), row.get("mode"))
            for row in stage36_resource
            if row.get("decision") == "PASS_RESOURCE_3RUN"
            and as_int(row, "runs") >= 3
        }
        out.append(
            AuditRow(
                "A4b",
                "resources_high_stat",
                "Stage 36 resource matrix has 3-run scalar/PVW r=1/2/4 support",
                "PASS_RESOURCE_3RUN" if expected.issubset(passed) else "FAIL_STAGE36_RESOURCE",
                rel(STAGE36_RESOURCE),
                "optional statistical resource evidence",
                "Fix or rerun Stage 36 resource before using statistical resource wording.",
            )
        )
    else:
        out.append(
            AuditRow(
                "A4b",
                "resources_high_stat",
                "Stage 36 resource matrix has 3-run scalar/PVW r=1/2/4 support",
                "NOT_RUN_OPTIONAL",
                "",
                "optional; not required for current scoped engineering claim",
                "Run STAGE36_MODE=resource STAGE36_EXECUTE=1 before using statistical resource wording.",
            )
        )

    manifest_ok, manifest_detail = existing_manifest_paths(manifest)
    run_log_has_stage28 = any(
        row.get("run_id") == "stage28-native-perf-counter-gate-001"
        for row in run_log
    )
    out.append(
        AuditRow(
            "A5",
            "reproducibility",
            "Final evidence package manifest paths exist and Stage 28 gate is logged",
            "PASS_SCOPED" if manifest_ok and run_log_has_stage28 else "FAIL_INCOMPLETE",
            f"{rel(MANIFEST)}; {rel(RUN_LOG)}",
            manifest_detail,
            "Fix missing manifest paths or run-log entries before claiming reproducibility.",
        )
    )

    stage33_expected = {
        "scalar_binary_full_run",
        "pvw_target_full_gate",
        "scalar_ternary_build",
    }
    stage33_passed = {
        row.get("step")
        for row in stage33
        if row.get("status") == "PASS"
    }
    out.append(
        AuditRow(
            "A5b",
            "current_smoke",
            "Current commit scalar baseline, PVW target gate, and scalar ternary build smoke pass",
            "PASS_CURRENT_SMOKE"
            if stage33_expected.issubset(stage33_passed)
            else "MISSING_CURRENT_SMOKE",
            rel(STAGE33) if STAGE33.exists() else "",
            "current commit smoke only; not a performance claim",
            "Run bash scripts/run_stage33_current_smoke.sh before relying on current-commit smoke evidence.",
        )
    )

    claim_ids = {row.get("claim_id"): row for row in claims}
    blocked_claims = ["C7", "C8", "C10"]
    blocked_ok = all(
        claim_ids.get(claim_id, {}).get("status_label", "").startswith("BLOCKED")
        for claim_id in blocked_claims
    )
    stage103_decision = row_by(stage103, "gate", "stage103_decision")
    stage103_done = (
        stage103_decision or {}
    ).get("status") == "PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED"
    if blocked_ok and stage103_done:
        a6_status = "PASS_SCOPED_BOUNDARY_REVIEWED"
        a6_evidence = f"{rel(CLAIMS)}; {rel(STAGE103_NOVELTY_REVIEW)}"
        a6_scope = (
            "broad novelty/non-binary/theorem claims remain blocked; related-work review "
            "supports only scoped systems wording"
        )
        a6_action = "Keep rejected broad novelty wording out of paper claims unless new theorem-level evidence is added."
    else:
        a6_status = "PASS_BLOCKED_BOUNDARY" if blocked_ok else "FAIL_OVERCLAIM_RISK"
        a6_evidence = rel(CLAIMS)
        a6_scope = "blocked claims are preserved as part of the evidence chain"
        a6_action = "Restore blocked labels before drafting stronger manuscript claims."
    out.append(
        AuditRow(
            "A6",
            "claim_boundary",
            "Novelty, non-binary support, and theorem-level 2025/686 citation claims remain explicitly blocked",
            a6_status,
            a6_evidence,
            a6_scope,
            a6_action,
        )
    )

    added_perf = [
        row
        for row in performance
        if row.get("scope") == "added_binary_small_sample"
        and row.get("status") == "PASS"
        and as_float(row, "mean_speedup") > 1.0
    ]
    added_noise = [
        row
        for row in noise
        if row.get("scope") == "added_binary_5_seed"
        and row.get("status") == "PASS"
        and as_int(row, "pvw_failures") == 0
        and as_int(row, "scalar_failures") == 0
        and as_int(row, "pair_failures") == 0
    ]
    stage36_added_perf = read_csv_if_exists(STAGE36_ADDED_PERF)
    stage36_added_noise = read_csv_if_exists(STAGE36_ADDED_NOISE)
    expected_added_keys = {
        ("SET_4_5_2048", "2"),
        ("SET_4_5_2048", "4"),
        ("SET_2_3_4096", "2"),
        ("SET_2_3_4096", "4"),
    }
    stage36_perf_passed = {
        (row.get("param"), row.get("r"))
        for row in stage36_added_perf
        if row.get("decision") == "PASS_ADDED_PARAM_10RUN"
        and as_int(row, "runs") >= 10
        and as_float(row, "mean_speedup") > 1.0
    }
    stage36_noise_passed = {
        (row.get("param"), row.get("r"))
        for row in stage36_added_noise
        if row.get("decision") == "PASS_ADDED_PARAM_20SEED"
        and as_int(row, "seeds") >= 20
        and as_int(row, "pvw_failures") == 0
        and as_int(row, "scalar_failures") == 0
        and as_int(row, "pair_failures") == 0
    }
    if expected_added_keys.issubset(stage36_perf_passed) and expected_added_keys.issubset(stage36_noise_passed):
        a7_status = "PASS_ADDED_PARAM_10RUN_20SEED"
        a7_evidence = f"{rel(STAGE36_ADDED_PERF)}; {rel(STAGE36_ADDED_NOISE)}"
        a7_scope = "added binary SET_4_5_2048 and SET_2_3_4096, r=2/r=4, 10-run performance and 20-seed noise"
        a7_action = "Keep non-binary and all-parameter claims blocked unless separate implementations and gates are added."
    else:
        a7_status = "PASS_SMALL_SAMPLE" if len(added_perf) == 4 and len(added_noise) == 4 else "FAIL_INCOMPLETE"
        a7_evidence = f"{rel(PERFORMANCE)}; {rel(NOISE)}"
        a7_scope = "small-sample only; not broad all-parameter evidence"
        a7_action = "Increase runs/seeds before broad parameter-generalization claims."
    out.append(
        AuditRow(
            "A7",
            "generalization",
            "Added binary parameters have r=2/r=4 performance and noise support",
            a7_status,
            a7_evidence,
            a7_scope,
            a7_action,
        )
    )

    external_statuses = {row.get("evidence_id"): row for row in external}
    fulltext_status = external_statuses.get("fab686_fulltext", {}).get("status", "MISSING")
    native_perf_status = external_statuses.get("stage28_native_perf_summary", {}).get("status", "MISSING")
    stage101_done = (
        row_by(stage101, "gate", "stage101_cb5_decision") or {}
    ).get("status") == "PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED"
    stage102_done = (
        row_by(stage102, "gate", "stage102_decision") or {}
    ).get("status") == "PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED"

    gate = row_by(stage28, "probe", "hardware_counter_gate")
    stage28_status = gate.get("status", "") if gate else "MISSING"
    if native_perf_status == "PASS_COUNTER_ATTRIBUTION_AVAILABLE" and stage101_done:
        stage28_audit_status = "PASS_COUNTER_ATTRIBUTION_EXTERNAL"
        stage28_evidence = f"{rel(EXTERNAL)}; {rel(STAGE101_CB5)}" if EXTERNAL.exists() else rel(STAGE101_CB5)
        stage28_scope = "native/perf-enabled Stage 28 summary and Stage101 counter metrics are registered"
        stage28_action = "Interpret hardware counters against Stage 22 timing and objdump evidence before claiming theoretical optimality."
    elif native_perf_status == "PASS_COUNTER_ATTRIBUTION_AVAILABLE":
        stage28_audit_status = "PASS_COUNTER_ATTRIBUTION_EXTERNAL"
        stage28_evidence = rel(EXTERNAL) if EXTERNAL.exists() else rel(STAGE28)
        stage28_scope = "native/perf-enabled Stage 28 summary registered through external evidence intake"
        stage28_action = "Run Stage101 parser before relying on detailed counter attribution metrics."
    elif stage28_status == "PASS":
        stage28_audit_status = "PASS_COUNTER_ATTRIBUTION"
        stage28_evidence = rel(STAGE28)
        stage28_scope = gate.get("detail", "missing Stage 28 gate") if gate else "missing Stage 28 gate"
        stage28_action = "Interpret hardware counters against Stage 22 timing and objdump evidence before claiming theoretical optimality."
    elif stage28_status == "READY_FOR_BENCH":
        stage28_audit_status = "CONDITIONAL_COUNTER_SMOKE_ONLY"
        stage28_evidence = rel(STAGE28)
        stage28_scope = gate.get("detail", "missing Stage 28 gate") if gate else "missing Stage 28 gate"
        stage28_action = "Run Stage 28 with STAGE28_RUN_BENCH=1 before claiming theoretical optimality."
    elif stage28_status == "BLOCKED":
        stage28_audit_status = "BLOCKED_EXTERNAL"
        stage28_evidence = rel(STAGE28)
        stage28_scope = gate.get("detail", "missing Stage 28 gate") if gate else "missing Stage 28 gate"
        stage28_action = "Run Stage 28 on native Linux or perf-enabled WSL with STAGE28_RUN_BENCH=1 before claiming theoretical optimality."
    else:
        stage28_audit_status = "FAIL_MISSING"
        stage28_evidence = rel(STAGE28)
        stage28_scope = gate.get("detail", "missing Stage 28 gate") if gate else "missing Stage 28 gate"
        stage28_action = "Run Stage 28 on native Linux or perf-enabled WSL with STAGE28_RUN_BENCH=1 before claiming theoretical optimality."
    out.append(
        AuditRow(
            "A8",
            "theory_backend",
            "MAT-AVX512 theoretical load/store optimality has hardware-counter support",
            stage28_audit_status,
            stage28_evidence,
            stage28_scope,
            stage28_action,
        )
    )

    if (
        fulltext_status == "AVAILABLE_UNREVIEWED"
        and native_perf_status == "PASS_COUNTER_ATTRIBUTION_AVAILABLE"
        and stage101_done
        and stage102_done
        and stage103_done
    ):
        external_audit_status = "PASS_EXTERNAL_EVIDENCE_REVIEWED"
        external_scope = (
            "2025/686 full-text anchors reviewed, related-work novelty boundary scoped, "
            "and native perf/counter evidence registered; broad novelty/theory claims remain bounded"
        )
        external_action = (
            "No missing external-evidence gate remains for CB5/CB6/CB7; keep scoped claim guardrails unless new evidence is added."
        )
    elif fulltext_status == "AVAILABLE_UNREVIEWED" or native_perf_status == "PASS_COUNTER_ATTRIBUTION_AVAILABLE":
        external_audit_status = "EXTERNAL_EVIDENCE_AVAILABLE_REVIEW_REQUIRED"
        external_scope = (
            "external artifact registered; manual citation/perf interpretation gates "
            "still required before claim upgrade"
        )
        external_action = "Register external artifacts with scripts/register_external_evidence.py, then rerun final recheck."
    elif fulltext_status == "MISSING" and native_perf_status == "MISSING":
        external_audit_status = "MISSING_OPTIONAL_EXTERNAL_EVIDENCE"
        external_scope = "no full-text or native perf external evidence registered"
        external_action = "Register external artifacts with scripts/register_external_evidence.py, then rerun final recheck."
    else:
        external_audit_status = "EXTERNAL_EVIDENCE_INTAKE_RECORDED"
        external_scope = f"fab686_fulltext={fulltext_status}; native_perf={native_perf_status}"
        external_action = "Register external artifacts with scripts/register_external_evidence.py, then rerun final recheck."
    out.append(
        AuditRow(
            "A8b",
            "external_evidence",
            "Optional external full-text and native perf artifacts are registered when supplied",
            external_audit_status,
            rel(EXTERNAL) if EXTERNAL.exists() else "",
            external_scope,
            external_action,
        )
    )

    scoped_ready_ids = {"A1", "A2", "A3", "A4", "A5", "A5b", "A6", "A7"}
    if STAGE36_TARGET_PERF.exists():
        scoped_ready_ids.add("A2b")
    if STAGE36_TARGET_NOISE.exists():
        scoped_ready_ids.add("A3c")
    if STAGE36_STAGE_NOISE.exists():
        scoped_ready_ids.add("A3b")
    if STAGE36_RESOURCE.exists():
        scoped_ready_ids.add("A4b")
    status_by_id = {row.item_id: row.status for row in out}
    scoped_ready = all(
        status_by_id.get(item_id, "").startswith("PASS")
        for item_id in scoped_ready_ids
    )
    theory_status = status_by_id.get("A8", "")
    external_status = status_by_id.get("A8b", "")
    if scoped_ready and theory_status in {
        "BLOCKED_EXTERNAL",
        "CONDITIONAL_COUNTER_SMOKE_ONLY",
    }:
        if external_status == "EXTERNAL_EVIDENCE_AVAILABLE_REVIEW_REQUIRED":
            overall_status = "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEW_REQUIRED"
        else:
            overall_status = "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED"
    elif (
        scoped_ready
        and theory_status in {"PASS_COUNTER_ATTRIBUTION", "PASS_COUNTER_ATTRIBUTION_EXTERNAL"}
        and external_status == "PASS_EXTERNAL_EVIDENCE_REVIEWED"
    ):
        overall_status = "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED"
    elif scoped_ready and theory_status in {"PASS_COUNTER_ATTRIBUTION", "PASS_COUNTER_ATTRIBUTION_EXTERNAL"}:
        overall_status = "SCOPED_ENGINEERING_CHAIN_READY__COUNTER_EVIDENCE_AVAILABLE_REVIEW_REQUIRED"
    else:
        overall_status = "NOT_READY"

    if overall_status == "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED":
        overall_scope = (
            "scoped engineering acceleration evidence is complete and the former CB5/CB6/CB7 external blockers "
            "are resolved by native counter evidence, source-anchor review, and scoped novelty boundaries"
        )
        overall_action = (
            "Use scoped systems/engineering wording; do not upgrade to broad novelty, all-parameter, non-binary, "
            "or theoretical-optimality claims without new evidence."
        )
    else:
        overall_scope = (
            "complete scoped engineering acceleration evidence exists; novelty/theory/all-parameter claims are not complete"
        )
        overall_action = (
            "Keep the active goal open until external full-text/perf/native evidence is supplied or the scope is explicitly narrowed."
        )

    out.append(
        AuditRow(
            "A9",
            "overall",
            "Original optimization goal status under current evidence",
            overall_status,
            f"{rel(OUT_CSV)}; {rel(OUT_MD)}",
            overall_scope,
            overall_action,
        )
    )

    return out


def markdown_table(rows: list[AuditRow]) -> str:
    columns = [
        "item_id",
        "category",
        "status",
        "requirement",
        "scope",
        "remaining_action",
    ]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        data = row.__dict__
        lines.append("| " + " | ".join(data[col] for col in columns) + " |")
    return "\n".join(lines)


def write_markdown(path: Path, rows: list[AuditRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    decision = rows[-1]
    body = f"""# Final Goal Completion Audit

Date: 2026-06-25

## Purpose

This generated audit maps the active PVW/MAT-SAB optimization goal to current
authoritative evidence. It deliberately separates the scoped engineering
acceleration package from stronger claims that still require external evidence.

Generator:

```text
scripts/build_final_goal_completion_audit.py
```

Primary CSV:

```text
repro/final_goal_completion_audit.csv
```

## Decision

```text
{decision.status}
```

Interpretation:

```text
{decision.scope}
```

## Matrix

{markdown_table(rows)}
"""
    path.write_text(body, encoding="utf-8", newline="\n")


def main() -> None:
    rows = audit()
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, rows)
    print(f"Wrote {rel(OUT_CSV)}")
    print(f"Wrote {rel(OUT_MD)}")


if __name__ == "__main__":
    main()
