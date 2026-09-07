# Spatial Target Atlas

Spatial Target Atlas maps target evidence across body, tissue, anatomical region, cell type, and
subcellular scales. It keeps measured observations separate from model-derived hypotheses and never
collapses unlike assays into an opaque safety score.

## First milestone

- Versioned `ProteinEvidenceRecord` interchange schema
- Human Protein Atlas v25.1 tissue MS, Deep Visual Proteomics, and subcellular localization connector
- Explicit detection, donor-support, modality, spatial-scale, and provenance fields
- JSON and TSV evidence bundles

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/spatial-target-atlas build examples/luad_targets.yaml -o outputs/luad
```

The HPA DVP atlas is cell-type resolved but currently derives from one healthy female donor. The
software retains that limitation rather than allowing cellular resolution to imply population depth.
HPA data remain subject to the source's own licence and citation requirements; this repository's MIT
licence applies only to the software.

See [`docs/evidence-model.md`](docs/evidence-model.md) for detection-state semantics and the planned
measured/model-derived evidence boundary.

## Roadmap

1. HPA identifier resolution and RNA–protein discordance
2. ProteomicsDB and CPTAC/PDC quantitative proteomics
3. HuBMAP and CELLxGENE spatial evidence
4. Body → tissue → cell → compartment visualization
5. PINNACLE and SPATIA model-derived evidence, clearly separated from measurements

## Relationship to open-cohort-factory

This repository can run independently. A future adapter will accept an `open-cohort-factory`
manifest to inherit explicit disease and reference-population definitions.
