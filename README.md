# Spatial Target Atlas

A research prototype for assembling target evidence across tissues, cell types, spatial datasets, and proteomic cohorts without collapsing unlike assays into a single opaque score.

**Project status:** the first evidence-integration milestone is implemented and tested. The broader "atlas" product is not finished.

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
| Gene-symbol input resolution | Not yet implemented |
| Target-level HuBMAP cell-intensity extraction | Not yet implemented |
| Interactive body → tissue → cell → compartment visualization | Not yet implemented |
| PINNACLE/SPATIA or other model-derived evidence | Not yet implemented |
| open-cohort-factory adapter | Not yet implemented |

The code is therefore useful as a reproducible **evidence-integration and reference-audit pipeline**, not yet as a complete spatial atlas application.

## Install

Python 3.11+:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run quality checks:

```bash
pytest
ruff check .
mypy src
```

The GitHub CI runs linting, strict mypy, and pytest with a 70% coverage floor.

## Quick start

The example uses three LUAD-related targets and expects Ensembl gene IDs.

```bash
spatial-target-atlas build examples/luad_targets.yaml -o outputs/luad
```

This writes:

- `evidence.json` and `evidence.tsv`
- `concordance.json`
- `cross_source_concordance.json`
- `paired_tumor_normal.json`
- `spatial_datasets.json`
- `spatial_target_coverage.json`
- `manifest.json`

Leave `tissues` empty to retain body-wide HPA matrices. Add tissues only when you intentionally want a subset.

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

- Core builds currently require Ensembl IDs because automatic identifier resolution is not implemented.
- Most external connectors depend on live public APIs. Exact record counts and current compatibility can change as those services change.
- CI uses mocked source responses for deterministic connector behavior. It does not continuously run full live-data integration tests.
- CELLxGENE can be pinned to a stable Census release; ProteomicsDB is a live API.
- HuBMAP target coverage currently audits targeted panels but does not yet extract per-cell target intensity.
- No visualization layer exists yet.
- Model-derived evidence is represented in the schema but not populated by a model connector.
- Source data retain their own licenses and citation requirements. The MIT license applies to this software.

## Example results

A live LUAD example was run and documented on **September 7, 2026**. It demonstrated the implemented HPA, ProteomicsDB, PDC, HuBMAP, CELLxGENE, and reference-audit workflows.

Those numbers are a dated validation snapshot, not guaranteed current output from live APIs.

See [docs/luad-example.md](docs/luad-example.md).

## Evidence semantics

See [docs/evidence-model.md](docs/evidence-model.md) for the measurement, detection-state, concordance, and reference-selection rules.

## Relationship to open-cohort-factory

The project runs independently today. An adapter for `open-cohort-factory` population manifests is still planned and is not implemented.
