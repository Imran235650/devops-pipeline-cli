from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Optional

from .artifacts import artifact_exists
from .errors import ApprovalRejectedError, ArtifactNotFoundError
from .models import RunResult, StepResult, utc_now_iso

logger = logging.getLogger(__name__)

PIPELINE_STEPS = ["build", "test", "package", "deploy"]


def require_approval(prompt: str = "Approve deployment? (y/N): ", auto_yes: bool = False) -> bool:
    if auto_yes:
        return True
    ans = input(prompt).strip().lower()
    return ans in ("y", "yes", "o", "oui")


def run_pipeline(
    run_id: str,
    artifact: str,
    require_manual_approval: bool,
    auto_yes: bool,
    fail_step: Optional[str],
    simulate_seconds: float,
) -> RunResult:
    started_at = utc_now_iso()
    logger.info("Run started. artifact=%s", artifact, extra={"run_id": run_id})

    if not artifact_exists(artifact):
        logger.error("Unknown artifact: %s", artifact, extra={"run_id": run_id})
        raise ArtifactNotFoundError(f"Unknown artifact: {artifact}")

    approved = True
    if require_manual_approval:
        logger.info("Waiting for manual approval...", extra={"run_id": run_id})
        approved = require_approval(auto_yes=auto_yes)
        if not approved:
            logger.warning("Approval rejected.", extra={"run_id": run_id})
            raise ApprovalRejectedError("Approval rejected by user.")

    step_results: list[StepResult] = []
    overall_status = "success"

    for step in PIPELINE_STEPS:
        step_start = utc_now_iso()
        logger.info("Step started: %s", step, extra={"run_id": run_id})

        time.sleep(max(0.0, simulate_seconds))

        if fail_step and step == fail_step:
            step_end = utc_now_iso()
            msg = f"Simulated failure at step '{step}'."
            logger.error(msg, extra={"run_id": run_id})
            step_results.append(
                StepResult(
                    name=step,
                    status="failed",
                    started_at=step_start,
                    finished_at=step_end,
                    message=msg,
                )
            )
            overall_status = "failed"

            # Remaining steps are skipped
            for remaining in PIPELINE_STEPS[PIPELINE_STEPS.index(step) + 1 :]:
                now = utc_now_iso()
                step_results.append(
                    StepResult(
                        name=remaining,
                        status="skipped",
                        started_at=now,
                        finished_at=now,
                        message="Skipped due to previous failure.",
                    )
                )
            break

        step_end = utc_now_iso()
        step_results.append(
            StepResult(
                name=step,
                status="success",
                started_at=step_start,
                finished_at=step_end,
                message="OK",
            )
        )
        logger.info("Step finished: %s (success)", step, extra={"run_id": run_id})

    finished_at = utc_now_iso()
    result = RunResult(
        run_id=run_id,
        artifact=artifact,
        approved=approved,
        status=overall_status,  # type: ignore[arg-type]
        started_at=started_at,
        finished_at=finished_at,
        steps=step_results,
    )
    logger.info("Run finished. status=%s", result.status, extra={"run_id": run_id})
    return result


def write_json_result(result: RunResult, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
