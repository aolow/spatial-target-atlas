"""Transparent reference eligibility and target-sensitivity analysis."""

from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Any

from .models import ProteinEvidenceRecord, SpatialTranscriptomicSummaryRecord


def build_reference_audit(
    spatial: list[SpatialTranscriptomicSummaryRecord],
    protein: list[ProteinEvidenceRecord],
    target_population: dict[str, Any],
    cohort_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidates = _spatial_candidates(spatial)
    if any(record.specimen_context == "adjacent_normal" for record in protein):
        candidates.append({
            "reference_context": "cancer_patient_adjacent_normal",
            "role": "sensitivity_reference",
            "rank": 2,
            "tissue_match": True,
            "life_stage_match": "likely_adult_not_explicitly_scored",
            "disease_context_match": True,
            "healthy_reference": False,
            "donor_count": len({
                record.case_id for record in protein
                if record.specimen_context == "adjacent_normal" and record.case_id
            }),
            "caveats": [
                "Cancer-bearing donor context and possible field effects.",
                "Adjacent tissue is not a population healthy control.",
            ],
        })
    return {
        "schema_version": "1.0",
        "target_population": target_population,
        "cohort_context": cohort_context,
        "decision_rule": (
            "Ranks express reference role, not a composite biological score. Primary eligibility "
            "requires source-labeled normal adult tissue; limited donor depth remains explicit."
        ),
        "candidates": sorted(
            candidates, key=lambda item: (item["rank"], item["reference_context"])
        ),
        "spatial_sensitivity": _spatial_sensitivity(spatial),
        "proteomic_sensitivity": _protein_sensitivity(protein),
        "cross_modality_warning": (
            "Spatial raw-count prevalence and proteomic abundance are never compared numerically."
        ),
    }


def _spatial_candidates(
    records: list[SpatialTranscriptomicSummaryRecord],
) -> list[dict[str, Any]]:
    definitions = {
        "source_labeled_normal_adult_or_unspecified": (
            "primary_candidate", 1, True, "adult_or_unspecified", False,
            ["Source label alone does not establish absence of comorbidity."],
        ),
        "source_labeled_normal_developmental": (
            "sensitivity_reference", 3, True, "mismatch", False,
            ["Fetal developmental biology is not an adult cancer reference."],
        ),
        "disease_tissue": (
            "comparator_only", 4, True, "context_dependent", True,
            ["Disease tissue cannot serve as a normal reference."],
        ),
    }
    candidates = []
    for context in sorted({record.reference_context for record in records}):
        role, rank, tissue_match, life_stage_match, disease_match, caveats = definitions.get(
            context,
            ("review_required", 99, False, "unknown", False, ["Unrecognized reference context."]),
        )
        subset = [record for record in records if record.reference_context == context]
        donors = {record.donor_id for record in subset}
        candidate_caveats = list(caveats)
        if role == "primary_candidate" and len(donors) < 5:
            candidate_caveats.append(
                "Fewer than five independent donors; underpowered as a reference."
            )
        candidates.append({
            "reference_context": context,
            "role": role,
            "rank": rank,
            "tissue_match": tissue_match,
            "life_stage_match": life_stage_match,
            "disease_context_match": disease_match,
            "healthy_reference": context.startswith("source_labeled_normal"),
            "dataset_count": len({record.dataset_id for record in subset}),
            "donor_count": len(donors),
            "development_stages": sorted({record.development_stage for record in subset}),
            "diseases": sorted({record.disease for record in subset}),
            "caveats": candidate_caveats,
        })
    return candidates


def _spatial_sensitivity(
    records: list[SpatialTranscriptomicSummaryRecord],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[SpatialTranscriptomicSummaryRecord]] = defaultdict(list)
    for record in records:
        groups[(record.gene_symbol, record.reference_context)].append(record)
    output = []
    for (gene, context), subset in sorted(groups.items()):
        assayed = [record for record in subset if record.detection_state != "not_assayed"]
        spots = sum(record.spot_count for record in assayed)
        positive = sum(record.positive_spot_count for record in assayed)
        output.append({
            "gene_symbol": gene,
            "reference_context": context,
            "assayed_spot_count": spots,
            "positive_spot_count": positive,
            "positive_spot_fraction": positive / spots if spots else None,
            "dataset_count": len({record.dataset_id for record in assayed}),
            "donor_count": len({record.donor_id for record in assayed}),
            "metric": "raw_count_positive_spot_fraction",
        })
    return output


def _protein_sensitivity(records: list[ProteinEvidenceRecord]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[ProteinEvidenceRecord]] = defaultdict(list)
    for record in records:
        if record.specimen_context in {"tumor", "adjacent_normal"} and record.value is not None:
            groups[(record.gene_symbol, record.source, record.specimen_context)].append(record)
    return [{
        "gene_symbol": gene,
        "source": source,
        "reference_context": context,
        "sample_count": len(subset),
        "donor_count": len({record.case_id for record in subset if record.case_id}),
        "median_value": median(record.value for record in subset if record.value is not None),
        "unit": subset[0].unit,
        "metric": "within_source_median_only",
    } for (gene, source, context), subset in sorted(groups.items())]
