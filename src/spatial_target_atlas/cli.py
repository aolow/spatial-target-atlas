"""Command-line interface."""

import csv
import json
from pathlib import Path
from typing import Annotated

import typer

from .concordance import summarize_concordance
from .config import load_spec
from .cross_source import summarize_cross_source
from .paired import summarize_paired
from .provenance import build_manifest
from .sources.hpa import HPAClient
from .sources.pdc import PDCClient
from .sources.proteomicsdb import ProteomicsDBClient

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
    client = HPAClient(release=project.hpa_release)
    records.extend(client.fetch_complete(project.genes, project.tissues))
    identities = []
    for identifier in project.genes:
        if not identifier.startswith("ENSG"):
            raise typer.BadParameter(f"HPA milestone 1 requires an Ensembl ID: {identifier}")
        records.extend(client.fetch_annotations(identifier))
        identities.append((identifier, *client.resolve_uniprot(identifier)))
    proteomicsdb = ProteomicsDBClient()
    for identifier, gene_symbol, uniprot_id in identities:
        if uniprot_id:
            records.extend(proteomicsdb.fetch(gene_symbol, identifier, uniprot_id, project.tissues))
    identity_map = {
        gene_symbol: (identifier, uniprot_id)
        for identifier, gene_symbol, uniprot_id in identities
    }
    pdc = PDCClient()
    for study_id in project.pdc_studies:
        records.extend(pdc.fetch(study_id, identity_map))
    output.mkdir(parents=True, exist_ok=True)
    serialized = [record.model_dump(mode="json") for record in records]
    evidence_json = output / "evidence.json"
    concordance_json = output / "concordance.json"
    cross_source_json = output / "cross_source_concordance.json"
    paired_json = output / "paired_tumor_normal.json"
    evidence_tsv = output / "evidence.tsv"
    evidence_json.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
    concordance_json.write_text(
        json.dumps(summarize_concordance(records), indent=2), encoding="utf-8"
    )
    cross_source_json.write_text(
        json.dumps(summarize_cross_source(records), indent=2), encoding="utf-8"
    )
    paired_json.write_text(
        json.dumps(summarize_paired(records), indent=2), encoding="utf-8"
    )
    if serialized:
        with evidence_tsv.open("w", encoding="utf-8", newline="") as handle:
            flat = [
                {**row, "metadata": json.dumps(row["metadata"], sort_keys=True)}
                for row in serialized
            ]
            writer = csv.DictWriter(handle, fieldnames=list(flat[0]), delimiter="\t")
            writer.writeheader()
            writer.writerows(flat)
    artifacts = [evidence_json, concordance_json, cross_source_json, paired_json]
    if evidence_tsv.exists():
        artifacts.append(evidence_tsv)
    manifest = build_manifest(spec, records, artifacts)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    typer.echo(f"Built {len(records)} evidence records in {output}")


if __name__ == "__main__":
    app()
