"""Command-line interface."""

import csv
import json
from pathlib import Path
from typing import Annotated

import typer

from .concordance import summarize_concordance
from .config import load_spec
from .cross_source import summarize_cross_source
from .hubmap_cells import HuBMAPCellsClient, summarize_cell_measurements
from .identifiers import TargetResolver
from .models import ProteinEvidenceRecord, SpatialTranscriptomicSummaryRecord
from .paired import summarize_paired
from .provenance import build_manifest
from .reference_selection import build_reference_audit
from .sources.hpa import HPAClient
from .sources.hubmap import HuBMAPClient
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
    identities = TargetResolver(hpa=client).resolve(project.genes)
    ensembl_ids = [identity.ensembl_id for identity in identities]
    records.extend(client.fetch_complete(ensembl_ids, project.tissues))
    for identity in identities:
        records.extend(client.fetch_annotations(identity.ensembl_id))
    proteomicsdb = ProteomicsDBClient()
    for identity in identities:
        if identity.uniprot_id:
            records.extend(
                proteomicsdb.fetch(
                    identity.gene_symbol,
                    identity.ensembl_id,
                    identity.uniprot_id,
                    project.tissues,
                )
            )
    identity_map = {
        identity.gene_symbol: (identity.ensembl_id, identity.uniprot_id)
        for identity in identities
    }
    pdc = PDCClient()
    for study_id in project.pdc_studies:
        records.extend(pdc.fetch(study_id, identity_map))
    hubmap = HuBMAPClient()
    spatial_datasets = hubmap.fetch_spatial_registry(project.hubmap_organs)
    identity_tuples = [
        (identity.ensembl_id, identity.gene_symbol, identity.uniprot_id)
        for identity in identities
    ]
    spatial_coverage = hubmap.fetch_target_coverage(spatial_datasets, identity_tuples)
    output.mkdir(parents=True, exist_ok=True)
    serialized = [record.model_dump(mode="json") for record in records]
    identities_json = output / "target_identities.json"
    evidence_json = output / "evidence.json"
    concordance_json = output / "concordance.json"
    cross_source_json = output / "cross_source_concordance.json"
    paired_json = output / "paired_tumor_normal.json"
    spatial_json = output / "spatial_datasets.json"
    spatial_coverage_json = output / "spatial_target_coverage.json"
    evidence_tsv = output / "evidence.tsv"
    identities_json.write_text(
        json.dumps([identity.model_dump(mode="json") for identity in identities], indent=2),
        encoding="utf-8",
    )
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
    spatial_json.write_text(
        json.dumps([record.model_dump(mode="json") for record in spatial_datasets], indent=2),
        encoding="utf-8",
    )
    spatial_coverage_json.write_text(
        json.dumps([record.model_dump(mode="json") for record in spatial_coverage], indent=2),
        encoding="utf-8",
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
    artifacts = [
        identities_json,
        evidence_json,
        concordance_json,
        cross_source_json,
        paired_json,
        spatial_json,
        spatial_coverage_json,
    ]
    if evidence_tsv.exists():
        artifacts.append(evidence_tsv)
    manifest = build_manifest(spec, records, artifacts)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    typer.echo(f"Built {len(records)} evidence records in {output}")


@app.command("build-spatial-census")
def build_spatial_census(
    spec: Annotated[Path, typer.Argument(exists=True, readable=True)],
    tissue: Annotated[str, typer.Option("--tissue")] = "lung",
    census_version: Annotated[str, typer.Option("--census-version")] = "stable",
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("outputs/census-spatial"),
) -> None:
    """Build raw-count spatial summaries from a versioned CELLxGENE Census release."""
    from .sources.cellxgene import CensusSpatialClient

    project = load_spec(spec)
    identities = TargetResolver().resolve(project.genes)
    datasets, summaries = CensusSpatialClient(census_version).fetch(
        [identity.ensembl_id for identity in identities],
        tissue,
    )
    output.mkdir(parents=True, exist_ok=True)
    identities_json = output / "target_identities.json"
    dataset_json = output / "census_spatial_datasets.json"
    summary_json = output / "census_spatial_expression.json"
    identities_json.write_text(
        json.dumps([identity.model_dump(mode="json") for identity in identities], indent=2),
        encoding="utf-8",
    )
    dataset_json.write_text(
        json.dumps([record.model_dump(mode="json") for record in datasets], indent=2),
        encoding="utf-8",
    )
    summary_json.write_text(
        json.dumps([record.model_dump(mode="json") for record in summaries], indent=2),
        encoding="utf-8",
    )
    release = summaries[0].source_release if summaries else census_version
    manifest = build_manifest(
        spec,
        [],
        [identities_json, dataset_json, summary_json],
        extra_sources=[{
            "source": "CZ CELLxGENE Census",
            "release": release,
            "record_count": len(summaries),
            "retrieved_at": [],
            "source_urls": ["https://cellxgene.cziscience.com/"],
            "source_payload_sha256": [],
        }],
    )
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    typer.echo(
        f"Built {len(summaries)} spatial summaries from {len(datasets)} datasets in {output}"
    )


@app.command("build-hubmap-cells")
def build_hubmap_cells(
    spec: Annotated[Path, typer.Argument(exists=True, readable=True)],
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("outputs/hubmap-cells"),
    page_size: Annotated[int, typer.Option("--page-size")] = 5000,
    max_cells_per_dataset: Annotated[
        int, typer.Option("--max-cells-per-dataset")
    ] = 200000,
) -> None:
    """Fetch target-level per-cell HuBMAP protein values for assayed public panels."""
    project = load_spec(spec)
    hpa = HPAClient(release=project.hpa_release)
    identities = TargetResolver(hpa=hpa).resolve(project.genes)
    identity_by_gene = {identity.gene_symbol: identity for identity in identities}
    identity_tuples = [
        (identity.ensembl_id, identity.gene_symbol, identity.uniprot_id)
        for identity in identities
    ]

    hubmap = HuBMAPClient()
    datasets = hubmap.fetch_spatial_registry(project.hubmap_organs)
    dataset_by_uuid = {dataset.dataset_uuid: dataset for dataset in datasets}
    coverage = hubmap.fetch_target_coverage(datasets, identity_tuples)

    cells = HuBMAPCellsClient()
    records = []
    statuses = []
    seen_queries: set[tuple[str, str, str]] = set()
    for item in coverage:
        if item.coverage_state != "assayed":
            continue
        identity = identity_by_gene[item.gene_symbol]
        dataset = dataset_by_uuid[item.dataset_uuid]
        channels = sorted({
            str(row.get("channel_id") or "").strip()
            for row in item.matched_channels
            if str(row.get("channel_id") or "").strip()
        })
        if not channels:
            channels = [item.gene_symbol]
        for protein_id in channels:
            query_key = (dataset.dataset_uuid, identity.gene_symbol, protein_id)
            if query_key in seen_queries:
                continue
            seen_queries.add(query_key)
            target_records, status = cells.fetch_target(
                dataset,
                identity,
                protein_id,
                page_size=page_size,
                max_cells=max_cells_per_dataset,
            )
            records.extend(target_records)
            statuses.append(status)

    output.mkdir(parents=True, exist_ok=True)
    identities_json = output / "target_identities.json"
    datasets_json = output / "spatial_datasets.json"
    coverage_json = output / "spatial_target_coverage.json"
    cells_jsonl = output / "hubmap_cell_protein.jsonl"
    summary_json = output / "hubmap_cell_protein_summary.json"
    status_json = output / "hubmap_cell_query_status.json"

    identities_json.write_text(
        json.dumps([identity.model_dump(mode="json") for identity in identities], indent=2),
        encoding="utf-8",
    )
    datasets_json.write_text(
        json.dumps([dataset.model_dump(mode="json") for dataset in datasets], indent=2),
        encoding="utf-8",
    )
    coverage_json.write_text(
        json.dumps([item.model_dump(mode="json") for item in coverage], indent=2),
        encoding="utf-8",
    )
    with cells_jsonl.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.model_dump(mode="json"), sort_keys=True) + "\n")
    summary_json.write_text(
        json.dumps(summarize_cell_measurements(records), indent=2),
        encoding="utf-8",
    )
    status_json.write_text(json.dumps(statuses, indent=2), encoding="utf-8")

    artifacts = [
        identities_json,
        datasets_json,
        coverage_json,
        cells_jsonl,
        summary_json,
        status_json,
    ]
    manifest = build_manifest(
        spec,
        [],
        artifacts,
        extra_sources=[{
            "source": "HuBMAP Cells API",
            "release": "live",
            "record_count": len(records),
            "retrieved_at": sorted({
                record.retrieved_at for record in records
            }),
            "source_urls": ["https://cells.api.hubmapconsortium.org/api"],
            "source_payload_sha256": sorted(cells.payload_hashes),
        }],
    )
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    complete = sum(status["status"] == "complete" for status in statuses)
    typer.echo(
        f"Built {len(records)} per-cell measurements from {complete} target-dataset queries "
        f"in {output}"
    )


@app.command("render-atlas")
def render_atlas(
    core: Annotated[Path, typer.Option("--core", exists=True, file_okay=False, readable=True)],
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("atlas.html"),
    hubmap_cells: Annotated[
        Path | None,
        typer.Option("--hubmap-cells", exists=True, file_okay=False, readable=True),
    ] = None,
    spatial_census: Annotated[
        Path | None,
        typer.Option("--spatial-census", exists=True, file_okay=False, readable=True),
    ] = None,
    reference_audit: Annotated[
        Path | None,
        typer.Option("--reference-audit", exists=True, dir_okay=False, readable=True),
    ] = None,
) -> None:
    """Render a self-contained local HTML atlas report from saved outputs."""
    from .visualization import render_atlas_html

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_atlas_html(core, hubmap_cells, spatial_census, reference_audit),
        encoding="utf-8",
    )
    typer.echo(f"Rendered atlas report: {output}")


@app.command("reference-audit")
def reference_audit(
    spec: Annotated[Path, typer.Argument(exists=True, readable=True)],
    spatial_expression: Annotated[
        Path, typer.Option("--spatial-expression", exists=True, readable=True)
    ],
    core_evidence: Annotated[
        Path | None, typer.Option("--core-evidence", exists=True, readable=True)
    ] = None,
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("reference_audit.json"),
) -> None:
    """Rank reference roles and show target sensitivity without mixing assay scales."""
    project = load_spec(spec)
    spatial = [
        SpatialTranscriptomicSummaryRecord.model_validate(row)
        for row in json.loads(spatial_expression.read_text(encoding="utf-8"))
    ]
    protein = [] if core_evidence is None else [
        ProteinEvidenceRecord.model_validate(row)
        for row in json.loads(core_evidence.read_text(encoding="utf-8"))
    ]
    audit = build_reference_audit(spatial, protein, project.target_population)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    typer.echo(f"Built reference audit with {len(audit['candidates'])} candidate contexts")


if __name__ == "__main__":
    app()
