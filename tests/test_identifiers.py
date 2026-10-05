import httpx
import pytest

from spatial_target_atlas.identifiers import TargetResolver
from spatial_target_atlas.sources.hpa import HPAClient

ENSEMBL = "ENSG00000119888"


def test_gene_symbol_resolves_to_canonical_hpa_identity() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "/lookup/symbol/homo_sapiens/EPCAM" in str(request.url):
            return httpx.Response(
                200,
                json={"id": ENSEMBL, "object_type": "Gene", "display_name": "EPCAM"},
            )
        if request.url.path.endswith(f"/{ENSEMBL}.json"):
            return httpx.Response(
                200,
                json={"Gene": "EPCAM", "Ensembl": ENSEMBL, "Uniprot": ["P16422"]},
            )
        raise AssertionError(str(request.url))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    identity = TargetResolver(
        hpa=HPAClient(client=client, release="25.1"),
        client=client,
    ).resolve(["EPCAM"])[0]

    assert identity.input_id == "EPCAM"
    assert identity.ensembl_id == ENSEMBL
    assert identity.gene_symbol == "EPCAM"
    assert identity.uniprot_id == "P16422"
    assert identity.resolution_sources == ["Ensembl REST", "Human Protein Atlas"]
    assert len(identity.source_payload_sha256) == 2


def test_ensembl_input_uses_hpa_without_extra_ensembl_lookup() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "v25.proteinatlas.org"
        return httpx.Response(
            200,
            json={"Gene": "EPCAM", "Ensembl": ENSEMBL, "Uniprot": "P16422"},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    identity = TargetResolver(
        hpa=HPAClient(client=client, release="25.1"),
        client=client,
    ).resolve([ENSEMBL + ".12"])[0]

    assert identity.ensembl_id == ENSEMBL
    assert identity.gene_symbol == "EPCAM"
    assert identity.resolution_sources == ["Human Protein Atlas"]


def test_ensembl_only_resolution_supports_spatial_census() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/lookup/id/{ENSEMBL}"
        return httpx.Response(
            200,
            json={"id": ENSEMBL, "object_type": "Gene", "display_name": "EPCAM"},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    identity = TargetResolver(client=client).resolve([ENSEMBL])[0]

    assert identity.gene_symbol == "EPCAM"
    assert identity.uniprot_id is None
    assert identity.resolution_sources == ["Ensembl REST"]


def test_duplicate_targets_after_resolution_are_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "rest.ensembl.org":
            return httpx.Response(
                200,
                json={"id": ENSEMBL, "object_type": "Gene", "display_name": "EPCAM"},
            )
        return httpx.Response(
            200,
            json={"Gene": "EPCAM", "Ensembl": ENSEMBL, "Uniprot": "P16422"},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    resolver = TargetResolver(
        hpa=HPAClient(client=client, release="25.1"),
        client=client,
    )
    with pytest.raises(ValueError, match="same Ensembl gene"):
        resolver.resolve(["EPCAM", ENSEMBL])


def test_unknown_symbol_is_rejected() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(404))
    )
    with pytest.raises(ValueError, match="not found"):
        TargetResolver(client=client).resolve(["NOT_A_REAL_GENE"])
