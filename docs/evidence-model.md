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

## Planned evidence families

- HPA full tissue and DVP matrices
- ProteomicsDB multi-experiment tissue MS
- CPTAC/PDC tumor and adjacent-tissue proteomics
- HuBMAP imaging MS and spatial molecular assays
- CELLxGENE spatial transcriptomics
- PINNACLE and SPATIA model-derived representations
