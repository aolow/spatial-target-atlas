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
For DVP comparisons, RNA is detected at nCPM ≥ 1 and protein is detected when intensity is non-missing,
matching HPA's published definitions. Bulk and DVP MS records identify the single healthy female
donor design. Subcellular localization is represented as immunofluorescence rather than IHC.

## Planned evidence families

- HPA full tissue and DVP matrices
- ProteomicsDB grouped tissue MS
- CPTAC/PDC tumor and adjacent-tissue proteomics (configurable studies implemented)
- HuBMAP imaging MS and spatial molecular assays
- CELLxGENE spatial transcriptomics
- PINNACLE and SPATIA model-derived representations

## Concordance

RNA–protein concordance is calculated only within the matched HPA DVP cell-type-group table. The
output includes the complete context count, both-detected pairs, RNA-only, protein-only, and
neither-detected contexts. Spearman rank correlation is withheld when fewer than three contexts have
positive values in both modalities. Rank discordance never compares HPA intensity numerically with
nCPM; it compares only their within-gene order across matched contexts.

HPA–ProteomicsDB replication is assessed using within-source tissue ranks over exact,
case-insensitive tissue-name matches. Raw intensities remain in source-specific units. ProteomicsDB
records retain BRENDA Tissue Ontology identifiers, sample counts, intensity ranges, and the iBAQ
aggregation parameters returned by the API.

ProteomicsDB is a live API rather than a pinned atlas archive. Each record therefore includes its
retrieval timestamp and declares `API v1.1 live` as the source release. Tissue labels that appear
unusual remain unchanged until an auditable ontology crosswalk is introduced.

## PDC tumor–adjacent comparisons

PDC quantitative values are stored per aliquot with `case_id`, `specimen_context`, and the original
`sample_type`. Tumor and adjacent-normal values are paired only when PDC assigns both aliquots to the
same case. The summary reports the median paired difference and fraction of patients with a positive
difference; it does not treat adjacent tissue as healthy or pool TMT ratios across studies. Stable
PDC accessions resolve to the latest version, while resolved study UUID and retrieval time remain in
each record for auditability.

Internal-reference channels are excluded before evidence records are created. Matrix aliquot UUIDs
are retained as `sample_id`; submitter IDs are used only as an explicit fallback join and both join
identifiers and the join method are recorded. Case UUIDs, rather than submitter labels, define pairs.

## Build provenance

`manifest.json` records SHA-256 hashes for the input specification and generated artifacts, exact
source releases and URLs, retrieval times, package version, Git commit, and build time. HPA downloads
use the requested release's archived major-version host, preventing an unversioned current endpoint
from being silently labeled as an older release. Evidence records also carry SHA-256 hashes of the
source API responses or downloadable archives used to create them, and the manifest consolidates
those hashes by source and release. Git dirty state is explicit so a locally modified build cannot be
mistaken for an exact committed-code reproduction.
