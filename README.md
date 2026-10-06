# Spatial Target Atlas

A research prototype for assembling target evidence across tissues, cell types, spatial datasets, and proteomic cohorts without collapsing unlike assays into a single opaque score.

**Project status:** the core evidence-integration pipeline is implemented and tested. The broader interactive atlas product is not finished.

## What is implemented

| Area | Status |
| --- | --- |
| Versioned target-evidence data model | Implemented |
| Human Protein Atlas tissue, DVP cell-type, and subcellular evidence | Implemented |
| ProteomicsDB tissue-level replication | Implemented |
| PDC/CPTAC patient-matched tumor vs adjacent-normal proteomics | Implemented |
| HuBMAP spatial-dataset registry with donor context | Implemented |
| HuBMAP targeted-panel coverage audit | Implemented |
| CELLxGENE spatial transcriptomic summaries | Implemented as optional dependency |
| Within-HPA RNA/protein concordance | Implemented |
| HPA vs ProteomicsDB tissue-rank concordance | Implemented |
| Transparent reference-context audit | Implemented |
| SHA-256 build provenance and artifact manifest | Implemented |
| Gene-symbol and Ensembl input resolution | Implemented |
| Target-level HuBMAP per-cell protein extraction | Implemented for Cells API-indexed targeted panels |
| Self-contained local HTML evidence report | Implemented |
| Body → organ → cell → subcellular spatial overlay | Implemented schematic view |
| Dataset-resolved within-source intensity views | Implemented |
| Registered histology/image-coordinate viewer | Not yet implemented |
| PINNACLE target/context representation coverage | Implemented import |
| Generic model-derived target evidence contract | Implemented |
| Direct SPATIA target-scoring pipeline | Not yet implemented |
| open-cohort-factory context adapter | Implemented |

The code is therefore useful as a reproducible **evidence-integration and reference-audit pipeline**, not yet as a complete spatial atlas application.

## Install

Python 3.11+.

For library use such as importing the Pydantic evidence models, the base install stays minimal:

```bash
pip install -e .
```

The base package depends only on Pydantic. It does not install Typer, Rich, HTTP clients, or YAML support.

For the command-line workflows:

```bash
pip install -e ".[cli]"
```

For development:

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy src
```

The `spatial` extra includes the CLI stack plus CELLxGENE Census:

```bash
pip install -e ".[spatial]"
```

The GitHub CI verifies both the dependency-light library install and the full development stack.

## Quick start

The example uses three LUAD-related gene symbols. Ensembl gene IDs are also accepted.

```bash
spatial-target-atlas build examples/luad_targets.yaml -o outputs/luad
```

This writes:

- `target_identities.json`
- `evidence.json` and `evidence.tsv`
- `concordance.json`
- `cross_source_concordance.json`
- `paired_tumor_normal.json`
- `spatial_datasets.json`
- `spatial_target_coverage.json`
- `source_status.json`
- `manifest.json`

Leave `tissues` empty to retain body-wide HPA matrices. Add tissues only when you intentionally want a subset.

Targets may now be supplied as human gene symbols or Ensembl gene IDs. Resolution is written to `target_identities.json` with source URLs and payload hashes.

### Optional HuBMAP per-cell protein values

For targeted spatial-proteomic panels that are indexed by the HuBMAP Cells API:

```bash
spatial-target-atlas build-hubmap-cells examples/luad_targets.yaml \
  -o outputs/luad-hubmap-cells
```

This first audits whether each target was actually present in the source antibody panel, then queries per-cell source-scale values only for assayed target/dataset pairs. It writes raw JSONL, within-dataset summaries, and a query-status file for datasets or markers unavailable through the Cells API.

A local guard refuses datasets above 200,000 indexed cells unless `--max-cells-per-dataset` is raised explicitly. Values are never normalized across datasets.

### Optional CELLxGENE spatial transcriptomics

This uses a larger dependency stack:

```bash
pip install -e ".[spatial]"

spatial-target-atlas build-spatial-census examples/luad_targets.yaml \
  --census-version 2025-11-08 \
  --tissue lung \
  -o outputs/luad-census-spatial
```

Then combine spatial reference context with the core protein evidence:

```bash
spatial-target-atlas reference-audit examples/luad_targets.yaml \
  --spatial-expression outputs/luad-census-spatial/census_spatial_expression.json \
  --core-evidence outputs/luad/evidence.json \
  -o outputs/luad-reference-audit.json
```

### Model-derived evidence

Model outputs are kept separate from measured assays.

PINNACLE's published labels can be imported as **representation coverage**, meaning that a context-specific protein representation exists for the target in that cell type:

```bash
spatial-target-atlas import-pinnacle \
  path/to/pinnacle_labels_dict.txt \
  --target-identities outputs/luad/target_identities.json \
  --embedding-file path/to/pinnacle_protein_embed.pth \
  -o outputs/luad-pinnacle
```

The embedding file is hashed for provenance but is not loaded, so PINNACLE/PyTorch is not a runtime dependency of this project. Representation availability is not converted into a target-prioritization score.

Other model-derived target outputs, including future SPATIA downstream scores, can use the same normalized JSON contract and be checked with:

```bash
spatial-target-atlas validate-model-evidence model_evidence.json
```

Pass `--model-evidence model_evidence.json` to `render-atlas` to show those records in a separate model-derived section.

### Spatial overlay

The atlas now includes a CMYK-inspired spatial view at body, organ, cell-context, and subcellular scales.

- **C**: HPA tissue protein support
- **M**: ProteomicsDB tissue protein support
- **Y**: CELLxGENE spatial RNA positivity
- **K**: HuBMAP spatial protein positivity, shown as a dark outline so it does not erase the C/M/Y mixture

Cross-source colors encode **categorical support only**. They do not pool intensity values.

Build the inspectable overlay payload directly:

```bash
spatial-target-atlas build-overlay \
  --core outputs/luad \
  --hubmap-cells outputs/luad-hubmap-cells \
  --spatial-census outputs/luad-census-spatial \
  -o outputs/luad-overlay.json
```

When quantitative values are available, the HTML atlas also shows separate dataset cards with intensity bars normalized **within that dataset only**. Raw/source-scale values remain visible beside the bars.

See [examples/vignettes/README.md](examples/vignettes/README.md) for checked-in visual design examples.

### Local HTML atlas report

Once you have built the evidence layers you want, render a self-contained report:

```bash
spatial-target-atlas render-atlas \
  --core outputs/luad \
  --hubmap-cells outputs/luad-hubmap-cells \
  --spatial-census outputs/luad-census-spatial \
  --reference-audit outputs/luad-reference-audit.json \
  -o outputs/luad-atlas.html
```

Only `--core` is required. The report adds optional HuBMAP cell, CELLxGENE, and reference-audit sections when those outputs are supplied. It has no external JavaScript, CSS, or network dependency and does not combine source-specific intensity scales.

## Design principles

### Keep unlike measurements separate

The project does not numerically merge RNA counts, tissue proteomics, TMT ratios, immunofluorescence, or targeted spatial panels.

Cross-source comparisons use within-source ranks or clearly labeled descriptive summaries.

### Distinguish absence from non-detection

The data model separates states such as:

- measured and detected
- measured and not detected
- not assayed
- source-specific summary evidence

For targeted HuBMAP panels, a missing target is reported as `not_assayed`, not as protein absence.

### Keep reference context explicit

Cancer-patient adjacent tissue is not labeled as healthy control tissue. Developmental normal tissue, adult source-labeled normal tissue, and disease tissue remain separate reference contexts.

### Preserve provenance

Each build records source releases, URLs, retrieval metadata, source-payload hashes, generated artifact hashes, package version, Git commit, and Git dirty state.

## Important limitations

- Most external connectors depend on live public APIs. Exact record counts and current compatibility can change as those services change.
- Core builds isolate connector failures after target resolution: successful sources are still written, while failures are recorded in `source_status.json` and `manifest.json["source_failures"]`. Treat a partial build as incomplete evidence, not as evidence that the failed source was negative.
- Pull-request CI uses mocked source responses for deterministic behavior. A separate weekly/manual smoke workflow checks lightweight live compatibility with Ensembl, HPA, ProteomicsDB, PDC study lookup, and HuBMAP discovery.
- CELLxGENE can be pinned to a stable Census release; ProteomicsDB is a live API.
- HuBMAP per-cell protein extraction depends on the separate Cells API index; not every public spatial dataset is indexed there.
- The body/organ maps are schematic anatomical views. They are not registered histology images or coordinate-accurate spatial assay viewers.
- PINNACLE import records contextual representation coverage, but this project does not run PINNACLE/SPATIA models or infer target relevance from embeddings.
- Source data retain their own licenses and citation requirements. The MIT license applies to this software.

## Example results

A live LUAD example was run and documented on **September 7, 2026**. It demonstrated the implemented HPA, ProteomicsDB, PDC, HuBMAP, CELLxGENE, and reference-audit workflows.

Those numbers are a dated validation snapshot, not guaranteed current output from live APIs.

See [docs/luad-example.md](docs/luad-example.md).

## Evidence semantics

See [docs/evidence-model.md](docs/evidence-model.md) for the measurement, detection-state, concordance, and reference-selection rules.

## Relationship to open-cohort-factory

Spatial Target Atlas can optionally consume an `open-cohort-factory` `manifest.json` when building a reference audit:

```bash
spatial-target-atlas reference-audit examples/luad_targets.yaml \
  --spatial-expression outputs/luad-census-spatial/census_spatial_expression.json \
  --core-evidence outputs/luad/evidence.json \
  --cohort-manifest ../open-cohort-factory/outputs/luad/manifest.json \
  -o outputs/luad-reference-audit.json
```

This imports the validated disease population, declared reference panels, materialized donor counts, source contexts, and cohort warnings without creating a Python package dependency between the projects. Spatial evidence remains separate from cohort construction; the adapter carries context, not expression values or a composite score.
