import httpx

from spatial_target_atlas.sources.hubmap import HuBMAPClient


def test_spatial_registry_follows_large_response_and_preserves_covariates() -> None:
    dataset = {
        "hubmap_id": "HBM123.ABCD.456", "uuid": "dataset-uuid",
        "dataset_type": "Xenium", "status": "Published", "data_access_level": "public",
        "doi_url": "https://doi.org/example", "registered_doi": "example",
        "origin_samples": [{"organ": "LL", "protocol_url": "https://protocol.example"}],
        "donor": {"uuid": "donor-uuid", "metadata": {"organ_donor_data": [
            {"grouping_concept_preferred_term": "Age", "preferred_term": "Age",
             "data_value": "72", "units": "years", "sab": "SNOMEDCT_US", "code": "1"},
            {"grouping_concept_preferred_term": "Medical History",
             "preferred_term": "Diabetes", "data_value": "Diabetes", "units": "",
             "sab": "SNOMEDCT_US", "code": "2"},
        ]}},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "search.api.hubmapconsortium.org":
            if request.url.params.get("dataset_type") == "Xenium":
                return httpx.Response(200, text="https://objects.example/result.json")
            return httpx.Response(200, json=[])
        return httpx.Response(200, json=[dataset])

    client = HuBMAPClient(httpx.Client(transport=httpx.MockTransport(handler)))
    records = client.fetch_spatial_registry(["LL"])

    assert len(records) == 1
    assert records[0].assay == "Xenium"
    assert records[0].donor_covariates["Age"][0]["value"] == "72"
    assert records[0].donor_covariates["Medical History"][0]["value"] == "Diabetes"
    assert len(records[0].source_payload_sha256) == 2
