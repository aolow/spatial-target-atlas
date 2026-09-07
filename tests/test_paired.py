from spatial_target_atlas.models import (
    EvidenceOrigin,
    Modality,
    ProteinEvidenceRecord,
    SpatialScale,
)
from spatial_target_atlas.paired import summarize_paired


def _record(case: str, context: str, value: float) -> ProteinEvidenceRecord:
    return ProteinEvidenceRecord(
        gene_symbol="EPCAM",
        source="NCI Proteomic Data Commons",
        source_release="PDC000153",
        evidence_origin=EvidenceOrigin.MEASURED,
        modality=Modality.MASS_SPECTROMETRY,
        spatial_scale=SpatialScale.TISSUE,
        value=value,
        specimen_context=context,
        case_id=case,
        citation_url="https://example.org",
        source_url="https://example.org",
    )


def test_paired_summary_uses_within_case_differences() -> None:
    records = [
        _record("A", "tumor", 2.0),
        _record("A", "adjacent_normal", 0.5),
        _record("B", "tumor", 0.0),
        _record("B", "adjacent_normal", 1.0),
        _record("UNPAIRED", "tumor", 5.0),
    ]

    result = summarize_paired(records)[0]
    assert result["paired_case_count"] == 2
    assert result["median_paired_tumor_minus_adjacent_log2_ratio"] == 0.25
    assert result["tumor_higher_fraction"] == 0.5
