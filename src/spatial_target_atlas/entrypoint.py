"""Dependency-light console entry point for the optional CLI."""

from __future__ import annotations

from importlib.util import find_spec


def main() -> None:
    """Run the CLI or explain how to install its optional dependencies."""
    missing = [
        package
        for package in ("httpx", "typer", "yaml")
        if find_spec(package) is None
    ]
    if missing:
        raise SystemExit(
            "Spatial Target Atlas CLI dependencies are not installed. "
            'Install with: pip install "spatial-target-atlas[cli]" '
            "or, from a checkout, pip install -e '.[cli]'."
        )

    from .cli import app

    app()
