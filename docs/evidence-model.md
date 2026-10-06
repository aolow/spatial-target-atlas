# Evidence model

Spatial Target Atlas keeps measured observations, source metadata, and model-derived evidence explicitly separated.

Values from different modalities are not placed on a shared numerical scale unless a separate calibration method is introduced and documented.

## Implemented evidence families

### Human Protein Atlas

The HPA connector currently supports:

- Full tissue mass-spectrometry matrices.
- Deep Visual Proteomics cell-type protein intensity.
- Matched DVP transcript abundance for within-source RNA/protein concordance.
- Subcellular immunofluorescence localization.

DVP cellular evidence currently reflects a single healthy female donor. Cell-type resolution therefore must not be mistaken for population depth.

Complete matrices retain blank measurements as `not_detected`. Gene-level specificity summaries use `specific_expression`, which is not equivalent to a measured negative.

### ProteomicsDB

ProteomicsDB contributes grouped tissue mass-spectrometry evidence.

Raw intensities remain in ProteomicsDB units. HPA and ProteomicsDB are compared only through within-source tissue ranks over exact case-insensitive tissue-label matches.

ProteomicsDB is a live API rather than a pinned atlas release, so retrieval timestamps and source metadata are retained.

### PDC/CPTAC

The PDC connector stores quantitative target measurements per aliquot and retains:

- case identity
- sample identity
- original sample type
- tumor vs adjacent-normal context
- study identity
- matrix/biospecimen join method

Tumor and adjacent-normal values are paired only within the same patient. Adjacent normal from a cancer-bearing patient is not treated as a healthy population reference.

Internal reference channels are excluded.

### HuBMAP

HuBMAP currently contributes three layers:

1. A spatial-dataset registry with assay type, organ, donor metadata, access level, DOI, protocol, and identifiers.
2. A targeted-panel coverage audit for supported antibody panels.
3. Optional per-cell target protein values from the HuBMAP Cells API for dataset/marker pairs available in that index.

Panel absence is `not_assayed`, not non-detection. Per-cell values are queried only after the panel audit says the target was assayed.

Cells API values retain the source protein/channel identifier and are summarized within dataset and cell type. Their unit is deliberately labeled `source_scale_intensity`; no cross-dataset normalization or comparability is assumed. Datasets not indexed by the Cells API are retained as explicit query-status failures rather than silently omitted.

### CELLxGENE Census

The optional CELLxGENE connector summarizes spatial transcriptomic raw counts by dataset and donor context.

Before a zero is interpreted, feature presence is checked at the dataset level. If the feature is absent from a dataset's matrix, the state is `not_assayed`.

Counts are summarized within datasets and contexts. They are not normalized or numerically compared across studies.

Pin a Census version for reproducibility.

## Spatial overlay semantics

The spatial renderer uses source-specific transparent layers rather than a shared quantitative scale:

- **C** = Human Protein Atlas tissue protein
- **M** = ProteomicsDB tissue protein
- **Y** = CELLxGENE spatial RNA
- **K** = HuBMAP per-cell spatial protein

C/M/Y are alpha-composited with multiply blending. K is drawn as a dark outline so spatial-protein support remains visible without masking the other channels.

Opacity has source-specific meaning. HPA and ProteomicsDB use within-target, within-source relative tissue intensity with a nonzero floor for positive tissue. CELLxGENE uses positive-spot fraction. HuBMAP uses positive-cell fraction. These strengths are not a common numerical scale and must not be compared across source families.

The report also shows four source-separated small-multiple anatomy maps beside the composite. These are the authoritative way to disambiguate a mixed composite color.

A failed connector is `unknown`, never negative. ProteomicsDB absence is also treated as unknown because its connector records quantified evidence rather than an explicit assayed-negative matrix.

Quantitative views are source- and dataset-specific. HuBMAP median source-scale intensity and CELLxGENE mean raw count may be normalized for bar length **within one dataset only**. The source value and unit remain visible, and values are never normalized across datasets or modalities.

PDC tumor-versus-adjacent evidence is shown separately as disease context rather than mixed into the body positivity palette.

## Detection-state semantics

The project distinguishes measurement coverage from biological absence.

Common states include:

- `detected`
- `not_detected`
- `quantified`
- `specific_expression`
- `assayed`
- `not_assayed`
- `assayed_detected`
- `assayed_not_detected`

These labels are source- and modality-aware. They should not be collapsed into a single boolean target-present field.

## Concordance

### HPA DVP RNA vs protein

RNA/protein concordance is calculated only within matched HPA DVP cell-type groups.

The report includes:

- number of available contexts
- jointly detected contexts
- RNA-only contexts
- protein-only contexts
- neither-detected contexts
- within-gene Spearman rank correlation when at least three jointly positive contexts exist
- largest rank disagreements

RNA nCPM and protein intensity are never directly merged.

### HPA vs ProteomicsDB

Cross-source protein reproducibility uses within-source tissue ranks on exactly matched tissue labels.

Small overlap counts are reported rather than hidden. Ontology-based synonym harmonization is not yet implemented.

## Reference selection

Reference ranking is categorical and auditable rather than a learned composite score.

For the current adult cancer use case:

- adult or unspecified source-labeled normal tissue can be a primary candidate
- cancer-patient adjacent normal is a sensitivity reference
- developmental normal is a separate sensitivity reference
- disease tissue is comparator-only

Low donor depth remains an explicit caveat even when a reference category is otherwise eligible.

Sensitivity summaries stay within modality. Spatial raw-count prevalence and proteomic abundance are not numerically ranked against each other.

## Provenance

`manifest.json` records:

- input specification SHA-256
- generated artifact SHA-256 values
- source release and source URLs
- retrieval timestamps when available
- source-payload hashes
- package version
- Git commit
- Git dirty state
- build time

HPA downloads use release-specific archive hosts rather than silently labeling current data as an older release.

## Model-derived evidence

Model outputs use a separate `ModelDerivedEvidenceRecord` and are never appended to the measured `ProteinEvidenceRecord` table.

PINNACLE import currently records **contextual representation availability** for requested targets and cell-type labels. The representation file can be hashed as provenance, but the vector is not interpreted and no therapeutic-target score is inferred.

The generic model-derived contract can also carry an explicitly named downstream score when one was computed outside this project. Such a record must identify the model, version, target, context, score name, provenance, and interpretation note.

SPATIA's released cell embeddings are not target-specific by themselves, so raw SPATIA embeddings are not treated as target evidence. A future target-level SPATIA downstream quantity can be imported only when that mapping is explicit.

## Schema boundary

The shared record model distinguishes `measured` and `model_derived` evidence origins. These layers remain separate in JSON and in the HTML report.
