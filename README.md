# Spatial Target Atlas

Spatial Target Atlas maps target evidence across body, tissue, anatomical region, cell type, and
subcellular scales. It keeps measured observations separate from model-derived hypotheses and never
collapses unlike assays into an opaque safety score.

## First milestone

- Versioned `ProteinEvidenceRecord` interchange schema
- Human Protein Atlas v25.1 tissue MS, Deep Visual Proteomics, and subcellular localization connector
- Explicit detection, donor-support, modality, spatial-scale, and provenance fields
- JSON and TSV evidence bundles
- Within-DVP RNA–protein rank concordance and discordant cell contexts

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/spatial-target-atlas build examples/luad_targets.yaml -o outputs/luad
```

Leave `tissues` empty to retain all available tissues and DVP cell-type groups for body-wide
concordance analysis; provide tissue names only when an explicit subset is intended.

The HPA DVP atlas is cell-type resolved but currently derives from one healthy female donor. The
software retains that limitation rather than allowing cellular resolution to imply population depth.
HPA data remain subject to the source's own licence and citation requirements; this repository's MIT
licence applies only to the software.

See [`docs/evidence-model.md`](docs/evidence-model.md) for detection-state semantics and the planned
measured/model-derived evidence boundary.

## Roadmap

1. Gene-symbol identifier resolution
2. ProteomicsDB and CPTAC/PDC quantitative proteomics
3. HuBMAP and CELLxGENE spatial evidence
4. Body → tissue → cell → compartment visualization
5. PINNACLE and SPATIA model-derived evidence, clearly separated from measurements

## Verified LUAD example

The body-wide HPA v25.1 build emits 328 records for CEACAM5, EPCAM, and MSLN. Across the 24 matched
DVP cell-type groups, EPCAM has 11 contexts detected by both modalities and modest RNA–protein rank
agreement (Spearman ρ = 0.336). CEACAM5 and MSLN each have only one jointly detected context, so the
software reports no correlation rather than manufacturing one from insufficient pairs. Detection
quadrants reveal RNA-only and protein-only contexts separately.

## Relationship to open-cohort-factory

This repository can run independently. A future adapter will accept an `open-cohort-factory`
manifest to inherit explicit disease and reference-population definitions.
