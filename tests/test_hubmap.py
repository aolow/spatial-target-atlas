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


def test_target_coverage_separates_assayed_from_not_assayed() -> None:
    dataset = {
        "hubmap_id": "HBM123.ABCD.456", "uuid": "derived-uuid",
        "dataset_type": "PhenoCycler [DeepCell + SPRM]", "status": "Published",
        "data_access_level": "public", "origin_samples": [], "donor": {},
        "ancestors": [],
    }
    panel = (
        "channel_id\thgnc_symbol\tantibody_rrid\tuniprot_accession_number\n"
        "EPCAM\tHGNC:11529\tAB_123\tP16422\n"
        "CD45\tHGNC:9666\tAB_456\tP08575\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            if "derived-uuid" in request.read().decode():
                return httpx.Response(200, json={"hits": {"hits": [{"_source": {
                    "ancestors": [{
                        "entity_type": "Dataset", "dataset_type": "PhenoCycler",
                        "uuid": "raw-uuid",
                    }]
                }}]}})
            return httpx.Response(200, json={"hits": {"hits": [{"_source": {
                "metadata": {"antibodies_path": "extras/panel.tsv"}
            }}]}})
        if request.url.host == "assets.hubmapconsortium.org":
            assert request.headers["referer"] == "https://portal.hubmapconsortium.org/"
            return httpx.Response(200, text=panel)
        if request.url.params.get("dataset_type") == "PhenoCycler [DeepCell + SPRM]":
            return httpx.Response(200, json=[dataset])
        return httpx.Response(200, json=[])

    client = HuBMAPClient(httpx.Client(transport=httpx.MockTransport(handler)))
    datasets = client.fetch_spatial_registry(["LL"])
    coverage = client.fetch_target_coverage(
        datasets,
        [("ENSG00000119888", "EPCAM", "P16422"),
         ("ENSG00000146648", "EGFR", "P00533")],
    )

    assert [record.coverage_state for record in coverage] == ["assayed", "not_assayed"]
    assert coverage[0].matched_channels[0]["antibody_rrid"] == "AB_123"
    assert coverage[1].note.endswith("not evidence of non-detection.")
    assert coverage[0].panel_size == 2
    assert coverage[0].panel_sha256
