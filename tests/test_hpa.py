from spatial_target_atlas.sources.hpa import HPAClient


def test_normalizes_measured_modalities_without_combining_scales() -> None:
    payload = {
        "Gene": "MSLN",
        "Ensembl": "ENSG1",
        "Uniprot": ["Q13421"],
        "Protein tissue specific Intensity": [{"Tissue": "lung", "Intensity": 12.0}],
        "Protein cell type specific Intensity": [{"Cell type": "mesothelial", "Intensity": 8.0}],
        "Subcellular main location": ["Plasma membrane"],
        "Reliability (IF)": "Approved",
    }
    records = HPAClient.normalize(payload, "https://example.test", ["lung"])
    assert len(records) == 3
    assert {record.spatial_scale.value for record in records} == {
        "tissue",
        "cell_type",
        "subcellular",
    }
    cell = next(record for record in records if record.spatial_scale.value == "cell_type")
    assert cell.donor_count == 1
    assert cell.metadata["platform"] == "Deep Visual Proteomics"


def test_measurement_dicts_retain_quantitative_intensity() -> None:
    payload = {
        "Gene": "EPCAM",
        "Ensembl": "ENSG1",
        "Uniprot": "P16422",
        "Protein tissue specific Intensity": {"lung": "12.5"},
        "Protein cell type specific Intensity": {"alveolar cells": "7.5"},
    }
    records = HPAClient.normalize(payload, "https://example.test", ["lung"])
    assert [record.value for record in records] == [12.5, 7.5]
