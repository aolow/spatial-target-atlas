"""The DBCLS anatomy asset must be bundled and preferred over network access."""

from importlib.resources import files

import pytest

import spatial_target_atlas.anatomy as anatomy


def test_dbcls_anatomy_asset_is_bundled() -> None:
    asset = files("spatial_target_atlas").joinpath(
        "assets", "dbcls_human_anatomy_organs.svg"
    )
    assert asset.is_file()
    data = asset.read_bytes()
    assert data.startswith(b"<")
    assert b"svg" in data[:200].lower()


def test_fetch_default_anatomy_uses_bundled_asset_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network fetch attempted despite bundled asset")

    monkeypatch.setattr(anatomy, "import_module", boom)

    uri = anatomy.fetch_default_anatomy_data_uri()

    assert uri.startswith("data:image/svg+xml;base64,")
