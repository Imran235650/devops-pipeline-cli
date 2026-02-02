from __future__ import annotations

import logging
import click
import uuid
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .artifacts import artifact_exists, list_artifacts
from .errors import ApprovalRejectedError, ArtifactNotFoundError, PipelineError
from .logging_conf import setup_logging
from .pipeline import PIPELINE_STEPS, run_pipeline, write_json_result

app = typer.Typer(add_completion=False, help="Simulate a delivery pipeline (artifact -> approval -> run -> logs).")
console = Console()
logger = logging.getLogger(__name__)


def _render_artifacts() -> list[str]:
    arts = list_artifacts()
    table = Table(title="Available Artifacts")
    table.add_column("#", justify="right")
    table.add_column("Artifact")
    table.add_column("Description")
    for i, a in enumerate(arts, start=1):
        table.add_row(str(i), a.key, a.description)
    console.print(table)
    return [a.key for a in arts]


def _pick_artifact_interactive() -> str:
    keys = _render_artifacts()
    while True:
        choice = console.input("Select artifact ([bold]number[/bold]): ").strip()
        if not choice.isdigit():
            console.print("[red]Please enter a number.[/red]")
            continue
        idx = int(choice)
        if 1 <= idx <= len(keys):
            return keys[idx - 1]
        console.print("[red]Invalid selection.[/red]")


@app.command()
def run(
    artifact: Optional[str] = typer.Option(None, "--artifact", "-a", help="Artifact key (skip interactive selection)"),
    require_approval: bool = typer.Option(
        True, "--require-approval/--no-require-approval", help="Require manual approval"
    ),
    yes: bool = typer.Option(False, "--yes", help="Auto-approve (useful for CI)"),
    fail_step: Optional[str] = typer.Option(
        None, "--fail-step", help=f"Simulate failure at a step: {', '.join(PIPELINE_STEPS)}"
    ),
    log_dir: Path = typer.Option(Path("logs"), "--log-dir", help="Directory for log files"),
    json_out: bool = typer.Option(True, "--json/--no-json", help="Write JSON run result next to log file"),
    simulate_seconds: float = typer.Option(0.5, "--simulate-seconds", help="Sleep per step to simulate work"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose console logs (DEBUG)"),
) -> None:
    """
    Run a simulated pipeline:
      1) Select artifact
      2) Manual approval
      3) Execute steps
      4) Write logs (+ optional JSON)
    """
    if artifact is None:
        artifact = _pick_artifact_interactive()
    else:
        if not artifact_exists(artifact):
            raise typer.BadParameter(f"Unknown artifact: {artifact}")

    if fail_step is not None and fail_step not in PIPELINE_STEPS:
        raise typer.BadParameter(f"--fail-step must be one of: {', '.join(PIPELINE_STEPS)}")

    run_id = uuid.uuid4().hex[:12]
    log_file = setup_logging(run_id, log_dir=log_dir, verbose=verbose)
    logger.debug("Logging initialized at %s", str(log_file), extra={"run_id": run_id})

    try:
        result = run_pipeline(
            run_id=run_id,
            artifact=artifact,
            require_manual_approval=require_approval,
            auto_yes=yes,
            fail_step=fail_step,
            simulate_seconds=simulate_seconds,
        )

        if json_out:
            json_path = log_dir / f"{result.run_id}.json"
            write_json_result(result, json_path)

        table = Table(title=f"Pipeline Run Summary (run_id={result.run_id})")
        table.add_column("Step")
        table.add_column("Status")
        table.add_column("Message")
        for s in result.steps:
            table.add_row(s.name, s.status, s.message)
        console.print(table)

        console.print(f"[green]Status:[/green] {result.status}")
        console.print(f"[green]Log file:[/green] {str(log_file)}")
        if json_out:
            console.print(f"[green]JSON result:[/green] {str(log_dir / (result.run_id + '.json'))}")

        raise typer.Exit(code=0 if result.status == "success" else 1)

    except ApprovalRejectedError as e:
        console.print(f"[yellow]Rejected:[/yellow] {e}")
        logger.warning("Run rejected by user.", extra={"run_id": run_id})
        raise typer.Exit(code=1)

    except ArtifactNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.error("Artifact error: %s", str(e), extra={"run_id": run_id})
        raise typer.Exit(code=1)

    except PipelineError as e:
        console.print(f"[red]Pipeline error:[/red] {e}")
        logger.error("Pipeline error: %s", str(e), extra={"run_id": run_id})
        raise typer.Exit(code=1)
    
    except click.exceptions.Exit:
            raise
    
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        logger.exception("Unexpected error", extra={"run_id": run_id})
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
