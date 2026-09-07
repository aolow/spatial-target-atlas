import json

import httpx

from spatial_target_atlas.sources.pdc import PDCClient


def test_pdc_maps_biospecimens_and_excludes_reference_channels() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        query = json.loads(request.content)["query"]
        if " study(" in query:
            data = {"study": [{
                "study_id": "uuid", "pdc_study_id": "PDC000153", "study_name": "LUAD",
                "analytical_fraction": "Proteome", "experiment_type": "TMT10",
                "disease_type": "LUAD", "primary_site": "Lung",
            }]}
        elif "biospecimenPerStudy" in query:
            data = {"biospecimenPerStudy": [
                {"case_id": "case-uuid", "case_submitter_id": "CASE-1",
                 "case_is_ref": "No", "sample_id": "s1",
                 "sample_submitter_id": "sample-t", "sample_type": "Primary Tumor",
                 "aliquot_id": "a1", "aliquot_submitter_id": "TUMOR",
                 "disease_type": "LUAD", "primary_site": "Lung"},
                {"case_id": "case-uuid", "case_submitter_id": "CASE-1",
                 "case_is_ref": "No", "sample_id": "s2",
                 "sample_submitter_id": "sample-n", "sample_type": "Solid Tissue Normal",
                 "aliquot_id": "a2", "aliquot_submitter_id": "NORMAL",
                 "disease_type": "LUAD", "primary_site": "Lung"},
                {"case_id": "ref-uuid", "case_submitter_id": "Pooled IR",
                 "case_is_ref": None, "sample_id": "s3",
                 "sample_submitter_id": "Pooled IR", "sample_type": "Not Reported",
                 "aliquot_id": "a3", "aliquot_submitter_id": "Pooled IR",
                 "disease_type": "Other", "primary_site": "Lung"},
            ]}
        else:
            data = {"quantDataMatrix": [
                ["Gene/Aliquot", "matrix-t:TUMOR", "matrix-n:NORMAL", "matrix-ref:Pooled IR"],
                ["EPCAM", "2.0", "0.5", "0.0"],
                ["OTHER", "9.0", "9.0", "9.0"],
            ]}
        return httpx.Response(200, json={"data": data})

    client = PDCClient(httpx.Client(transport=httpx.MockTransport(handler)))
    records = client.fetch("PDC000153", {"EPCAM": ("ENSG1", "P1")})

    assert len(records) == 2
    assert {record.specimen_context for record in records} == {"tumor", "adjacent_normal"}
    assert {record.case_id for record in records} == {"case-uuid"}
    assert {record.sample_id for record in records} == {"matrix-t", "matrix-n"}
    assert all(
        record.metadata["biospecimen_join_key"] == "aliquot_submitter_id"
        for record in records
    )
    assert all(record.unit == "log2 ratio to pooled reference" for record in records)
