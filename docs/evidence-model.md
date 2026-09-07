# Evidence model

Every record declares whether it is measured or model-derived, its assay modality, spatial scale,
source release, identifier mapping, detection state, support, and provenance. Values from different
modalities are not placed on a shared numerical scale without a separately documented calibration.

## Initial HPA interpretation

The v25.1 gene JSON fields used in milestone 1 are specificity summaries, not complete matrices.
`specific_expression` therefore means HPA selected that tissue or cell type as specific for the gene;
absence from the response does not mean the protein was measured and found absent.

Deep Visual Proteomics contributes cell-type-resolved mass-spectrometry evidence from one healthy
female donor. Tissue MS and subcellular immunofluorescence remain separate records.

Complete matrices retain blank intensity cells as `not_detected`; they are not converted to numeric
zero. Gene-level specificity summaries remain labeled `specific_expression`. An empty `tissues`
selection preserves the complete body-wide matrices, while a populated list explicitly subsets them.

## Planned evidence families

- HPA full tissue and DVP matrices
- ProteomicsDB multi-experiment tissue MS
- CPTAC/PDC tumor and adjacent-tissue proteomics
- HuBMAP imaging MS and spatial molecular assays
- CELLxGENE spatial transcriptomics
- PINNACLE and SPATIA model-derived representations

## Concordance

RNA–protein concordance is calculated only within the matched HPA DVP cell-type-group table. The
output includes the complete context count, both-detected pairs, RNA-only, protein-only, and
neither-detected contexts. Spearman rank correlation is withheld when fewer than three contexts have
positive values in both modalities. Rank discordance never compares HPA intensity numerically with
nCPM; it compares only their within-gene order across matched contexts.
