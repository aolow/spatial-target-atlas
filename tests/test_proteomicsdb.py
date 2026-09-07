import httpx

from spatial_target_atlas.sources.proteomicsdb import ProteomicsDBClient


def test_normalizes_grouped_tissue_expression() -> None:
    payload = {
        "d": {
            "results": [
                {
                    "TISSUE_ID": "BTO:1",
                    "TISSUE_NAME": "lung",
                    "NORMALIZED_INTENSITY": "3.5",
                    "UNNORMALIZED_INTENSITY": "5.0",
                    "MIN_NORMALIZED_INTENSITY": "2.0",
                    "MAX_NORMALIZED_INTENSITY": "4.0",
                    "SAMPLES": 4,
                }
            ]
        }
    }
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=payload, request=request)
    )
    records = ProteomicsDBClient(httpx.Client(transport=transport)).fetch(
        "EPCAM", "ENSG1", "P16422", ["lung"]
    )
    assert records[0].value == 3.5
    assert records[0].sample_count == 4
    assert records[0].anatomical_region == "BTO:1"
