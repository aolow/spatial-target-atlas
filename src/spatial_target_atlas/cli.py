"""Command-line interface."""

import csv
import json
from pathlib import Path
from typing import Annotated

import typer

from .concordance import summarize_concordance
from .config import load_spec
from .sources.hpa import HPAClient

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """Build spatially resolved, multimodal target evidence bundles."""


@app.command()
def build(
    spec: Annotated[Path, typer.Argument(exists=True, readable=True)],
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("outputs/latest"),
) -> None:
    """Build a versioned measured-evidence bundle."""
    project = load_spec(spec)
    records = []
    client = HPAClient()
    records.extend(client.fetch_complete(project.genes, project.tissues))
    for identifier in project.genes:
        if not identifier.startswith("ENSG"):
            raise typer.BadParameter(f"HPA milestone 1 requires an Ensembl ID: {identifier}")
        records.extend(client.fetch_annotations(identifier))
    output.mkdir(parents=True, exist_ok=True)
    serialized = [record.model_dump(mode="json") for record in records]
    (output / "evidence.json").write_text(json.dumps(serialized, indent=2), encoding="utf-8")
    (output / "concordance.json").write_text(
        json.dumps(summarize_concordance(records), indent=2), encoding="utf-8"
    )
    if serialized:
        with (output / "evidence.tsv").open("w", encoding="utf-8", newline="") as handle:
            flat = [
                {**row, "metadata": json.dumps(row["metadata"], sort_keys=True)}
                for row in serialized
            ]
            writer = csv.DictWriter(handle, fieldnames=list(flat[0]), delimiter="\t")
            writer.writeheader()
            writer.writerows(flat)
    typer.echo(f"Built {len(records)} evidence records in {output}")


if __name__ == "__main__":
    app()
