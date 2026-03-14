"""Management CLI for vertaling.

Requires: pip install "vertaling[cli]"

Usage::

    vertaling translate --locales nl,de,fr
    vertaling stats
    vertaling retry-failed
"""

from __future__ import annotations

try:
    import typer
except ImportError as e:
    raise ImportError("The CLI requires the 'cli' extra: pip install 'vertaling[cli]'") from e

app = typer.Typer(
    name="vertaling",
    help="Manage translations for your vertaling pipeline.",
    no_args_is_help=True,
)


@app.command()
def translate(
    locales: str = typer.Option(..., help="Comma-separated target locales, e.g. nl,de,fr"),
) -> None:
    """Translate pending units for the given locales."""
    typer.echo(f"Would translate pending units for locales: {locales}")


@app.command()
def retry_failed() -> None:
    """Retry all failed translations."""
    typer.echo("Would retry all failed translations.")


@app.command()
def stats() -> None:
    """Show translation statistics."""
    typer.echo("Would show translation statistics.")


if __name__ == "__main__":
    app()
