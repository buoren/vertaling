"""Management CLI for vertaling.

Requires: pip install "vertaling[cli]"

Usage::

    vertaling translate --locales nl,de,fr
    vertaling translate --source po --locales nl
    vertaling translate --source models --tenant-id 42 --locales nl,de
    vertaling stats
    vertaling translate --dry-run
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
    source: str | None = typer.Option(None, help="Restrict to 'po' or 'models'. Default: both."),
    tenant_id: str | None = typer.Option(None, help="Restrict model translation to this tenant."),
    dry_run: bool = typer.Option(
        False, help="Show what would be translated without calling the backend."
    ),
) -> None:
    """Translate pending units — static .po strings, model fields, or both."""
    ...


@app.command()
def stats() -> None:
    """Show translation coverage statistics."""
    ...


if __name__ == "__main__":
    app()
