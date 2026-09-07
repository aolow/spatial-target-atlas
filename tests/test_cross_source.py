from spatial_target_atlas.cross_source import summarize_cross_source
from spatial_target_atlas.models import (
    EvidenceOrigin,
    Modality,
    ProteinEvidenceRecord,
    SpatialScale,
)


def _record(source: str, tissue: str, value: float) -> ProteinEvidenceRecord:
    return ProteinEvidenceRecord(
        gene_symbol="G",
        source=source,
        source_release="1",
        evidence_origin=EvidenceOrigin.MEASURED,
        modality=Modality.MASS_SPECTROMETRY,
        spatial_scale=SpatialScale.TISSUE,
        tissue=tissue,
        value=value,
        citation_url="https://example.test",
        source_url="https://example.test",
    )


def test_cross_source_uses_ranks_not_raw_intensities() -> None:
    records = []
    for tissue, hpa, pdb in [("a", 10, 1), ("b", 20, 2), ("c", 30, 3)]:
        records.extend(
            [_record("Human Protein Atlas", tissue, hpa), _record("ProteomicsDB", tissue, pdb)]
        )
    result = summarize_cross_source(records)[0]
    assert result["common_tissues"] == 3
    assert result["spearman"] == 1.0
