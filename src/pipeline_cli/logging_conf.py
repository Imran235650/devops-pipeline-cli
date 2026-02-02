from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(run_id: str, log_dir: Path, verbose: bool = False) -> Path:
    """
    Configure root logger:
      - Console handler (INFO or DEBUG if verbose)
      - File handler (DEBUG)
    Returns the created log file path.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{run_id}.log"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Avoid duplicate handlers (important in tests / repeated runs)
    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = logging.Formatter(
        fmt="%(asctime)sZ %(levelname)s run_id=%(run_id)s %(name)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    class RunIdFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if not hasattr(record, "run_id"):
                record.run_id = run_id  # type: ignore[attr-defined]
            return True

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if verbose else logging.INFO)
    ch.setFormatter(fmt)
    ch.addFilter(RunIdFilter())
    root.addHandler(ch)

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    fh.addFilter(RunIdFilter())
    root.addHandler(fh)

    return log_file
