from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Artifact:
    key: str
    description: str


DEFAULT_ARTIFACTS: list[Artifact] = [
    Artifact("api-service@1.0.0", "API service container image"),
    Artifact("web-frontend@2.3.1", "Web frontend static bundle"),
    Artifact("worker@0.9.5", "Background worker binary"),
]


def list_artifacts() -> list[Artifact]:
    return DEFAULT_ARTIFACTS


def artifact_exists(key: str) -> bool:
    return any(a.key == key for a in DEFAULT_ARTIFACTS)
