from spatial_target_atlas.models import (
    EvidenceOrigin,
    Modality,
    ProteinEvidenceRecord,
    SpatialScale,
)


def test_evidence_origin_is_explicit() -> None:
    record = ProteinEvidenceRecord(
        gene_symbol="EPCAM",
        source="test",
        source_release="1",
        evidence_origin=EvidenceOrigin.MEASURED,
        modality=Modality.MASS_SPECTROMETRY,
        spatial_scale=SpatialScale.TISSUE,
        citation_url="https://example.test/citation",
        source_url="https://example.test/data",
    )
    assert record.evidence_origin != EvidenceOrigin.MODEL_DERIVED
