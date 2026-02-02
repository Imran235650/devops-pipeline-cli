class PipelineError(Exception):
    """Base exception for known pipeline failures."""


class ArtifactNotFoundError(PipelineError):
    pass


class ApprovalRejectedError(PipelineError):
    pass
