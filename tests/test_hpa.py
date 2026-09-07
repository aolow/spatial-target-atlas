import io
import zipfile

import httpx
import pytest

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
    records = HPAClient().normalize(payload, "https://example.test", ["lung"])
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
    records = HPAClient().normalize(payload, "https://example.test", ["lung"])
    assert [record.value for record in records] == [12.5, 7.5]


def _zip_tsv(contents: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("data.tsv", contents)
    return buffer.getvalue()


def test_complete_data_uses_hpa_detection_rules_and_donor_metadata() -> None:
    archives = {
        "dvp_cell_types.tsv.zip": _zip_tsv(
            "Cell type group\tTissue name\nalveolar cell types\tlung\n"
        ),
        "dvp_cell_type_group_data.tsv.zip": _zip_tsv(
            "Gene\tGene name\tCell type name\tIntensity\tMatched nCPM\n"
            "ENSG1\tEPCAM\talveolar cell types\t0\t0.6\n"
        ),
        "ms_tissue_sample_data.tsv.zip": _zip_tsv(
            "Gene\tGene name\tTissue\tIntensity\tsample_name\treplicate_nr\n"
            "ENSG1\tEPCAM\tlung\t5\tlung_1\t1\n"
        ),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=archives[request.url.path.rsplit("/", 1)[-1]])

    client = HPAClient(httpx.Client(transport=httpx.MockTransport(handler)), release="25.1")
    records = client.fetch_complete(["ENSG1"], [])
    rna = next(record for record in records if record.modality.value == "transcriptomics")
    protein = next(
        record for record in records if record.spatial_scale.value == "cell_type" and record != rna
    )
    bulk = next(record for record in records if record.spatial_scale.value == "tissue")

    assert rna.detection_state == "not_detected"
    assert protein.detection_state == "detected"
    assert (bulk.donor_count, bulk.sex, bulk.healthy_status) == (1, "female", "healthy donor")
    assert "v25.proteinatlas.org" in bulk.source_url


def test_subcellular_assay_is_immunofluorescence() -> None:
    payload = {
        "Gene": "EPCAM", "Ensembl": "ENSG1",
        "Subcellular main location": ["Plasma membrane"], "Reliability (IF)": "Approved",
    }
    record = HPAClient().normalize(payload, "https://example.test", [])[0]
    assert record.modality.value == "immunofluorescence"


def test_invalid_release_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid HPA release"):
        HPAClient(release="latest")
