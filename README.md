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
- HPA–ProteomicsDB tissue-rank reproducibility without raw-scale merging
- CPTAC/PDC aliquot proteomics with patient-matched tumor–adjacent comparisons
- SHA-256 build manifest with input, artifact, source-release, software, and Git provenance
- HuBMAP spatial-dataset registry with donor covariates and public/protected access labels
- HuBMAP targeted-panel coverage audit that separates `not_assayed` from non-detection

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/spatial-target-atlas build examples/luad_targets.yaml -o outputs/luad

# Optional spatial-transcriptomics connector (larger dependency set)
.venv/bin/pip install -e '.[spatial]'
.venv/bin/spatial-target-atlas build-spatial-census examples/luad_targets.yaml \
  --census-version 2025-11-08 --tissue lung -o outputs/luad-census-spatial
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
2. Target-level HuBMAP cell-intensity extraction for assayed panels
3. Body → tissue → cell → compartment visualization
4. PINNACLE and SPATIA model-derived evidence, clearly separated from measurements

## Verified LUAD example

The body-wide HPA v25.1 build emits 328 records for CEACAM5, EPCAM, and MSLN. Across the 24 matched
DVP cell-type groups, EPCAM has 11 contexts detected by both modalities and modest RNA–protein rank
agreement (Spearman ρ = 0.336). CEACAM5 and MSLN each have only one jointly detected context, so the
software reports no correlation rather than manufacturing one from insufficient pairs. Detection
quadrants reveal RNA-only and protein-only contexts separately.

The independent ProteomicsDB run returns 13 tissues for CEACAM5, 36 for EPCAM, and 22 for MSLN.
Across exactly matched, jointly detected tissue labels, HPA–ProteomicsDB rank correlations are 1.0
for CEACAM5 (4 tissues), 0.643 for EPCAM (8), and 0.3 for MSLN (5). These small overlap counts are
reported alongside the correlations; broader ontology-based tissue harmonization is intentionally a
future step rather than an implicit synonym merge.

The LUAD example also queries the latest PDC version behind `PDC000153`, maps aliquots using the
authoritative PDC biospecimen `sample_type`, and emits `paired_tumor_normal.json`. Effects are
calculated within patients as tumor minus adjacent-normal TMT log2 ratios. “Solid Tissue Normal” is
represented as `adjacent_normal` and `not_healthy_reference`: it is tissue from a cancer-bearing
patient, not a population healthy control. Pooled/internal reference channels are excluded.

The verified live build contains 639 biological PDC target measurements: 112 tumors and 101
adjacent-normal samples per gene, yielding 101 patient-matched pairs. Internal-reference channels
are excluded using PDC's reference flag with an identifier fallback for incompletely flagged study
records. Median tumor-minus-adjacent log2-ratio
differences are +0.584 for CEACAM5, +0.516 for EPCAM, and −0.701 for MSLN; the corresponding
fractions of patients with higher tumor abundance are 68%, 79%, and 29%. These descriptive paired
effects establish heterogeneity without presenting a cohort median as universal target biology.

Every build also writes `manifest.json` with the input-spec checksum, output checksums, exact source
releases and URLs, retrieval timestamps where supplied, package version, Git commit, and build time.

`spatial_datasets.json` inventories published HuBMAP spatial assays for configured organ codes before
large expression assets are downloaded. It retains donor age, sex, race, BMI, cause of death,
medical history and other available ontology-backed fields, alongside access level, DOI, protocol,
dataset UUID and donor UUID. This makes “normal” donor context visible during dataset selection.
The verified lung registry currently finds 11 public spatial-proteomic datasets: eight PhenoCycler
acquisitions and three DeepCell/SPRM-derived datasets. Covariates are retained without collapsing
multiple medical-history or pathology entries into a single label.

`spatial_target_coverage.json` then follows processed PhenoCycler datasets to their raw parent,
reads the source-declared antibody TSV, and matches targets using UniProt accessions (with an exact
channel-name fallback). It retains channel metadata, antibody RRIDs, panel URL, and SHA-256 checksum.
The three currently available DeepCell/SPRM lung datasets use 39- or 45-antibody panels that do not
include CEACAM5, EPCAM, or MSLN, so these targets are reported as `not_assayed`. This is a panel
coverage limitation, not protein non-detection. Large AnnData, image, and per-cell feature assets
are therefore not downloaded for targets that the panel could not measure.

The optional CELLxGENE Census command queries the spatial corpus separately because its TileDB-SOMA
stack is substantially larger than the core package. It emits a dataset registry with citations and
donor contexts plus raw-count summaries stratified by dataset, donor, disease, sex, ethnicity,
developmental stage, assay, tissue, cell-type annotation, and primary-data status. Per-dataset feature presence is checked
before zeros are interpreted. Counts are never normalized across studies. Pin `--census-version` for
reproducibility; the verified build uses the stable `2025-11-08` release.

That release contains 22 lung spatial datasets and 275,274 spots. The apparent reference pool is
not a homogeneous adult healthy cohort: 11 source-labeled-normal donors are fetal (12–20 weeks
post-fertilization), two are adults (age 59 and seventh decade), and seven Slide-seqV2 datasets are
lung metastasis tissue from a 61-year-old donor with renal cell carcinoma. The output therefore
labels developmental normal, adult/unspecified normal, and disease tissue separately.

## Relationship to open-cohort-factory

This repository can run independently. A future adapter will accept an `open-cohort-factory`
manifest to inherit explicit disease and reference-population definitions.
