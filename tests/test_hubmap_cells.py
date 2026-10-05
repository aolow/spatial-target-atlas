from urllib.parse import parse_qs

import httpx

from spatial_target_atlas.hubmap_cells import HuBMAPCellsClient, summarize_cell_measurements
from spatial_target_atlas.models import SpatialDatasetRecord, TargetIdentityRecord


def dataset() -> SpatialDatasetRecord:
    return SpatialDatasetRecord(
        dataset_id="HBM123.ABCD.456",
        dataset_uuid="dataset-uuid",
        source="HuBMAP",
        source_release="Search API v3 live",
        retrieved_at="2026-10-05T00:00:00Z",
        assay="PhenoCycler [DeepCell + SPRM]",
        organ="LL",
        donor_id="donor-1",
        access_level="public",
        status="Published",
        citation_url="https://doi.org/example",
        source_url="https://portal.hubmapconsortium.org/browse/dataset/dataset-uuid",
    )


def identity() -> TargetIdentityRecord:
    return TargetIdentityRecord(
        input_id="EPCAM",
        ensembl_id="ENSG00000119888",
        gene_symbol="EPCAM",
        uniprot_id="P16422",
        resolution_sources=["Ensembl REST", "Human Protein Atlas"],
        source_urls=["https://example.test"],
        retrieved_at="2026-10-05T00:00:00Z",
    )


def form(request: httpx.Request) -> dict[str, list[str]]:
    return parse_qs(request.content.decode())


def test_fetches_per_cell_target_values_and_preserves_zeros() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/cell/"):
            assert form(request)["input_set"] == ["dataset-uuid"]
            return httpx.Response(200, json={"results": [{"query_handle": "handle"}]})
        if request.url.path.endswith("/count/"):
            return httpx.Response(200, json={"results": [{"count": 2}]})
        if request.url.path.endswith("/celldetailevaluation/"):
            assert form(request)["values_included"] == ["EPCAM"]
            return httpx.Response(200, json={
                "count": 2,
                "results": [
                    {
                        "cell_id": "cell-1",
                        "modality": "codex",
                        "dataset": "dataset-uuid",
                        "organ": "Lung",
                        "cell_type": "epithelial cell",
                        "clusters": ["cluster-a"],
                        "values": {"EPCAM": 4.5},
                    },
                    {
                        "cell_id": "cell-2",
                        "modality": "codex",
                        "dataset": "dataset-uuid",
                        "organ": "Lung",
                        "cell_type": "epithelial cell",
                        "clusters": [],
                        "values": {"EPCAM": 0.0},
                    },
                ],
            })
        raise AssertionError(str(request.url))

    client = HuBMAPCellsClient(
        httpx.Client(transport=httpx.MockTransport(handler))
    )
    records, status = client.fetch_target(dataset(), identity(), "EPCAM", page_size=100)

    assert status["status"] == "complete"
    assert status["cell_count"] == 2
    assert [record.value for record in records] == [4.5, 0.0]
    assert [record.detection_state for record in records] == [
        "detected", "assayed_not_detected"
    ]

    summary = summarize_cell_measurements(records)
    assert len(summary) == 1
    assert summary[0]["cell_count"] == 2
    assert summary[0]["positive_cell_fraction"] == 0.5
    assert summary[0]["median_source_scale_intensity"] == 2.25


def test_cell_guard_prevents_large_download_without_truncating() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/cell/"):
            return httpx.Response(200, json={"results": [{"query_handle": "handle"}]})
        if request.url.path.endswith("/count/"):
            return httpx.Response(200, json={"results": [{"count": 200001}]})
        raise AssertionError("Detailed cell endpoint should not be called")

    client = HuBMAPCellsClient(
        httpx.Client(transport=httpx.MockTransport(handler))
    )
    records, status = client.fetch_target(
        dataset(), identity(), "EPCAM", max_cells=200000
    )

    assert records == []
    assert status["status"] == "guard_exceeded"
    assert "Raise --max-cells-per-dataset" in status["message"]


def test_unindexed_dataset_becomes_explicit_status() -> None:
    client = HuBMAPCellsClient(
        httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(400, json={"message": "No dataset found"})
            )
        )
    )
    records, status = client.fetch_target(dataset(), identity(), "EPCAM")

    assert records == []
    assert status["status"] == "unavailable"
    assert "HTTP 400" in status["message"]
