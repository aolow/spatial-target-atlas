from spatial_target_atlas.concordance import summarize_concordance
from spatial_target_atlas.models import (
    EvidenceOrigin,
    Modality,
    ProteinEvidenceRecord,
    SpatialScale,
)


def _record(cell_type: str, modality: Modality, value: float) -> ProteinEvidenceRecord:
    return ProteinEvidenceRecord(
        gene_symbol="G",
        source="Human Protein Atlas",
        source_release="1",
        evidence_origin=EvidenceOrigin.MEASURED,
        modality=modality,
        spatial_scale=SpatialScale.CELL_TYPE,
        cell_type=cell_type,
        value=value,
        detection_state="detected",
        citation_url="https://example.test",
        source_url="https://example.test",
    )


def test_reports_rank_concordance_and_discordance() -> None:
    records = []
    for cell_type, rna, protein in [("a", 1.0, 3.0), ("b", 2.0, 2.0), ("c", 3.0, 1.0)]:
        records.extend(
            [
                _record(cell_type, Modality.TRANSCRIPTOMICS, rna),
                _record(cell_type, Modality.MASS_SPECTROMETRY, protein),
            ]
        )
    result = summarize_concordance(records)[0]
    assert result["spearman"] == -1.0
    assert result["contexts"] == 3
    assert result["complete_detected_contexts"] == 3
    assert result["detection_concordance"]["both_detected"] == 3
    assert result["largest_discordances"][0]["absolute_rank_difference"] == 2.0


def test_detection_quadrants_use_source_detection_state() -> None:
    rna = _record("a", Modality.TRANSCRIPTOMICS, 0.6)
    rna.detection_state = "not_detected"
    protein = _record("a", Modality.MASS_SPECTROMETRY, 1.0)
    result = summarize_concordance([rna, protein])[0]
    assert result["detection_concordance"]["protein_only"] == 1
    assert result["complete_detected_contexts"] == 0
