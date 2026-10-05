"""Command-line interface."""

import csv
import json
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any, TypeVar

import typer

from .cohort_adapter import load_open_cohort_context
from .concordance import summarize_concordance
from .config import load_spec
from .cross_source import summarize_cross_source
from .hubmap_cells import HuBMAPCellsClient, summarize_cell_measurements
from .identifiers import TargetResolver
from .model_evidence import import_pinnacle_contexts, load_model_evidence
from .models import ProteinEvidenceRecord, SpatialTranscriptomicSummaryRecord
from .paired import summarize_paired
from .provenance import build_manifest
from .reference_selection import build_reference_audit
from .sources.hpa import HPAClient
from .sources.hubmap import HuBMAPClient
from .sources.pdc import PDCClient
from .sources.proteomicsdb import ProteomicsDBClient

app = typer.Typer(no_args_is_help=True)

_T = TypeVar("_T")


def _collect(
    stage: str,
    fetch: Callable[[], list[_T]],
    failures: list[dict[str, Any]],
) -> list[_T]:
    """Run one connector and record failures without aborting the full build."""
    try:
        return fetch()
    except Exception as exc:  # noqa: BLE001 - connector isolation is intentional
        failures.append(
            {
                "stage": stage,
                "error_type": type(exc).__name__,
                "error": str(exc)[:500],
            }
        )
        typer.echo(f"warning: {stage} failed: {type(exc).__name__}: {exc}", err=True)
        return []


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
    failures: list[dict[str, Any]] = []
    records = []
    client = HPAClient(release=project.hpa_release)

    # Identity resolution is intentionally fatal. Without target identities,
    # downstream source queries are not meaningful.
    identities = TargetResolver(hpa=client).resolve(project.genes)
    ensembl_ids = [identity.ensembl_id for identity in identities]

    def _fetch_hpa_tissue() -> list[ProteinEvidenceRecord]:
        return client.fetch_complete(ensembl_ids, project.tissues)

    def _fetch_hpa_annotations() -> list[ProteinEvidenceRecord]:
        output: list[ProteinEvidenceRecord] = []
        for identity in identities:
            output.extend(client.fetch_annotations(identity.ensembl_id))
        return output

    def _fetch_proteomicsdb() -> list[ProteinEvidenceRecord]:
        proteomicsdb = ProteomicsDBClient()
        output: list[ProteinEvidenceRecord] = []
        for identity in identities:
            if identity.uniprot_id:
                output.extend(
                    proteomicsdb.fetch(
                        identity.gene_symbol,
                        identity.ensembl_id,
                        identity.uniprot_id,
                        project.tissues,
                    )
                )
        return output

    identity_map = {
        identity.gene_symbol: (identity.ensembl_id, identity.uniprot_id)
        for identity in identities
    }

    records.extend(_collect("hpa.tissue", _fetch_hpa_tissue, failures))
    records.extend(_collect("hpa.annotations", _fetch_hpa_annotations, failures))
    records.extend(_collect("proteomicsdb", _fetch_proteomicsdb, failures))

    pdc = PDCClient()

    def _fetch_pdc_study(study_id: str) -> Callable[[], list[ProteinEvidenceRecord]]:
        return lambda: pdc.fetch(study_id, identity_map)

    for study_id in project.pdc_studies:
        records.extend(_collect(f"pdc.{study_id}", _fetch_pdc_study(study_id), failures))

    hubmap = HuBMAPClient()
    identity_tuples = [
        (identity.ensembl_id, identity.gene_symbol, identity.uniprot_id)
        for identity in identities
    ]
    spatial_datasets = _collect(
        "hubmap.spatial_registry",
        lambda: hubmap.fetch_spatial_registry(project.hubmap_organs),
        failures,
    )
    spatial_coverage = (
        _collect(
            "hubmap.target_coverage",
            lambda: hubmap.fetch_target_coverage(spatial_datasets, identity_tuples),
            failures,
        )
        if spatial_datasets
        else []
    )
    output.mkdir(parents=True, exist_ok=True)
    serialized = [record.model_dump(mode="json") for record in records]
    identities_json = output / "target_identities.json"
    evidence_json = output / "evidence.json"
    concordance_json = output / "concordance.json"
    cross_source_json = output / "cross_source_concordance.json"
    paired_json = output / "paired_tumor_normal.json"
    spatial_json = output / "spatial_datasets.json"
    spatial_coverage_json = output / "spatial_target_coverage.json"
    source_status_json = output / "source_status.json"
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
    source_status_json.write_text(
        json.dumps({"ok": len(failures) == 0, "failures": failures}, indent=2),
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
        source_status_json,
    ]
    if evidence_tsv.exists():
        artifacts.append(evidence_tsv)
    manifest = build_manifest(spec, records, artifacts, source_failures=failures)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    suffix = f" ({len(failures)} source(s) failed)" if failures else ""
    typer.echo(f"Built {len(records)} evidence records in {output}{suffix}")


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


@app.command("import-pinnacle")
def import_pinnacle(
    labels: Annotated[Path, typer.Argument(exists=True, readable=True)],
    target_identities: Annotated[
        Path, typer.Option("--target-identities", exists=True, readable=True)
    ],
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("outputs/pinnacle"),
    embedding_file: Annotated[
        Path | None, typer.Option("--embedding-file", exists=True, readable=True)
    ] = None,
) -> None:
    """Import PINNACLE target/context representation coverage as model-derived evidence."""
    records, summary = import_pinnacle_contexts(labels, target_identities, embedding_file)
    output.mkdir(parents=True, exist_ok=True)
    (output / "model_evidence.json").write_text(
        json.dumps([record.model_dump(mode="json") for record in records], indent=2),
        encoding="utf-8",
    )
    (output / "model_evidence_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    typer.echo(
        f"Imported {len(records)} PINNACLE target-context representation records in {output}"
    )


@app.command("validate-model-evidence")
def validate_model_evidence(
    evidence: Annotated[Path, typer.Argument(exists=True, readable=True)],
) -> None:
    """Validate normalized model-derived target evidence without merging it into measurements."""
    records = load_model_evidence(evidence)
    typer.echo(f"Valid model-derived evidence: {len(records)} records")


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
    model_evidence: Annotated[
        Path | None,
        typer.Option("--model-evidence", exists=True, dir_okay=False, readable=True),
    ] = None,
) -> None:
    """Render a self-contained local HTML atlas report from saved outputs."""
    from .visualization import render_atlas_html

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_atlas_html(
            core,
            hubmap_cells,
            spatial_census,
            reference_audit,
            model_evidence,
        ),
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
    cohort_manifest: Annotated[
        Path | None,
        typer.Option("--cohort-manifest", exists=True, dir_okay=False, readable=True),
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
    cohort = (
        load_open_cohort_context(cohort_manifest)
        if cohort_manifest is not None
        else None
    )
    target_population = dict(project.target_population)
    if cohort is not None:
        target_population["open_cohort_factory"] = cohort.disease_population
    audit = build_reference_audit(
        spatial,
        protein,
        target_population,
        cohort.model_dump(mode="json") if cohort is not None else None,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    typer.echo(f"Built reference audit with {len(audit['candidates'])} candidate contexts")


if __name__ == "__main__":
    app()
