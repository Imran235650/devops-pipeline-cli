from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Literal


StepStatus = Literal["success", "failed", "skipped"]
RunStatus = Literal["success", "failed", "rejected"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class StepResult:
    name: str
    status: StepStatus
    started_at: str
    finished_at: str
    message: str = ""


@dataclass(frozen=True)
class RunResult:
    run_id: str
    artifact: str
    approved: bool
    status: RunStatus
    started_at: str
    finished_at: str
    steps: list[StepResult]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
