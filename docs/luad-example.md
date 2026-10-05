# LUAD validation snapshot

**Run date:** September 7, 2026

This document preserves results from a live validation run of the v0.1 pipeline. The external sources include live APIs, so these values should be treated as a dated snapshot rather than expected permanent output.

Configuration: [`examples/luad_targets.yaml`](../examples/luad_targets.yaml)

Targets:

- CEACAM5
- EPCAM
- MSLN

## Human Protein Atlas

The body-wide HPA v25.1 build emitted 328 records across the three targets.

Across 24 matched DVP cell-type groups:

- EPCAM had 11 contexts detected by both RNA and protein, with Spearman rho 0.336.
- CEACAM5 and MSLN each had only one jointly detected context, so no correlation was reported.

The pipeline retained RNA-only and protein-only contexts separately rather than converting missing modality support into zero.

## ProteomicsDB replication

The live ProteomicsDB run returned:

- CEACAM5: 13 tissues
- EPCAM: 36 tissues
- MSLN: 22 tissues

Across exact matched tissue labels with joint detection, HPA vs ProteomicsDB rank correlations were:

| Target | Matched tissues | Spearman rho |
| --- | ---: | ---: |
| CEACAM5 | 4 | 1.0 |
| EPCAM | 8 | 0.643 |
| MSLN | 5 | 0.3 |

The small overlap counts were retained explicitly. No ontology synonym expansion was applied.

## PDC/CPTAC LUAD

The example queried PDC study `PDC000153`.

The live build contained 639 biological target measurements:

- 112 tumor samples per gene
- 101 adjacent-normal samples per gene
- 101 patient-matched tumor/adjacent pairs

Internal reference channels were excluded.

Median paired tumor-minus-adjacent log2-ratio differences were:

| Target | Median delta | Tumor higher |
| --- | ---: | ---: |
| CEACAM5 | +0.584 | 68% |
| EPCAM | +0.516 | 79% |
| MSLN | -0.701 | 29% |

These are within-study descriptive effects. Adjacent tissue is not interpreted as a healthy population reference.

## HuBMAP

The lung registry found 11 public spatial-proteomic datasets:

- eight PhenoCycler acquisitions
- three DeepCell/SPRM-derived datasets

Donor covariates were retained rather than collapsed into one "normal" label.

The three DeepCell/SPRM datasets used 39- or 45-antibody panels that did not include CEACAM5, EPCAM, or MSLN. The targets were therefore reported as `not_assayed`, not as negative protein evidence.

## CELLxGENE Census

The pinned `2025-11-08` spatial release contained 22 lung spatial datasets and 275,274 spots in the validation query.

The apparent reference pool was heterogeneous:

- 11 source-labeled-normal donors were fetal, 12–20 weeks post-fertilization.
- Two source-labeled-normal donors were adults.
- Seven Slide-seqV2 datasets represented lung metastasis tissue from a donor with renal cell carcinoma.

The reference audit therefore separated developmental normal, adult/unspecified normal, and disease tissue.

## Reference audit

The audit used an explicit categorical rule:

- adult source-labeled normal: primary candidate
- cancer-patient adjacent normal: sensitivity reference
- developmental normal: sensitivity reference
- disease tissue: comparator only

Low donor depth remained visible as a caveat.

Spatial raw counts and proteomic ratios were summarized separately and were never combined into one numeric score.

## Reproducibility note

Every build writes `manifest.json` with input, artifact, source, software, and Git provenance.

Because several upstream services are live APIs, rerunning the same workflow later may yield different record counts or metadata even when the software is unchanged.
