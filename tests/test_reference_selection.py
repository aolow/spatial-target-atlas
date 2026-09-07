from spatial_target_atlas.models import (
    EvidenceOrigin,
    Modality,
    ProteinEvidenceRecord,
    SpatialScale,
    SpatialTranscriptomicSummaryRecord,
)
from spatial_target_atlas.reference_selection import build_reference_audit


def _spatial(
    context: str, donor: str, stage: str, positive: int
) -> SpatialTranscriptomicSummaryRecord:
    return SpatialTranscriptomicSummaryRecord(
        dataset_id=f"dataset-{donor}", source="Census", source_release="2025-11-08",
        gene_symbol="EPCAM", ensembl_id="ENSG1", assay="Visium", tissue="lung",
        disease="normal" if context != "disease_tissue" else "carcinoma", donor_id=donor,
        development_stage=stage, sex="female", self_reported_ethnicity="unknown",
        cell_type="spot", is_primary_data=True, spot_count=10,
        positive_spot_count=positive, positive_spot_fraction=positive / 10,
        mean_raw_count=0.5,
        detection_state="assayed_detected" if positive else "assayed_not_detected",
        reference_context=context, note="test",
    )


def test_reference_audit_ranks_roles_and_keeps_modalities_separate() -> None:
    spatial = [
        _spatial("source_labeled_normal_adult_or_unspecified", "adult", "59-year-old", 5),
        _spatial("source_labeled_normal_developmental", "fetal", "16th week", 1),
        _spatial("disease_tissue", "disease", "61-year-old", 8),
    ]
    protein = [ProteinEvidenceRecord(
        gene_symbol="EPCAM", source="PDC", source_release="1",
        evidence_origin=EvidenceOrigin.MEASURED, modality=Modality.MASS_SPECTROMETRY,
        spatial_scale=SpatialScale.TISSUE, value=2.0, unit="log2 ratio", case_id="case-1",
        specimen_context="adjacent_normal", citation_url="https://example.org",
        source_url="https://example.org/data",
    )]

    audit = build_reference_audit(spatial, protein, {"disease": "LUAD", "life_stage": "adult"})

    assert audit["candidates"][0]["role"] == "primary_candidate"
    assert audit["candidates"][0]["donor_count"] == 1
    assert "underpowered" in audit["candidates"][0]["caveats"][-1]
    assert audit["candidates"][1]["reference_context"] == "cancer_patient_adjacent_normal"
    assert audit["spatial_sensitivity"][0]["metric"] == "raw_count_positive_spot_fraction"
    assert audit["proteomic_sensitivity"][0]["metric"] == "within_source_median_only"
