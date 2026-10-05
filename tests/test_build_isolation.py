"""Per-source failure isolation in the build pipeline."""

from typing import Any

from spatial_target_atlas.cli import _collect
from spatial_target_atlas.provenance import build_manifest


def test_collect_isolates_failure_and_records_it() -> None:
    failures: list[dict[str, Any]] = []

    good = _collect("hpa.tissue", lambda: [1, 2, 3], failures)
    assert good == [1, 2, 3]
    assert failures == []

    def _boom() -> list[int]:
        raise ConnectionError("self-signed certificate")

    bad = _collect("proteomicsdb", _boom, failures)
    assert bad == []
    assert len(failures) == 1
    assert failures[0]["stage"] == "proteomicsdb"
    assert failures[0]["error_type"] == "ConnectionError"
    assert "self-signed certificate" in failures[0]["error"]


def test_manifest_records_source_failures(tmp_path) -> None:  # noqa: ANN001
    spec = tmp_path / "spec.yaml"
    artifact = tmp_path / "evidence.json"
    spec.write_text("name: test\n", encoding="utf-8")
    artifact.write_text("[]", encoding="utf-8")

    failures = [
        {
            "stage": "hubmap.spatial_registry",
            "error_type": "ConnectError",
            "error": "x",
        }
    ]
    manifest = build_manifest(spec, [], [artifact], source_failures=failures)

    assert manifest["source_failures"] == failures


def test_manifest_source_failures_defaults_empty(tmp_path) -> None:  # noqa: ANN001
    spec = tmp_path / "spec.yaml"
    artifact = tmp_path / "evidence.json"
    spec.write_text("name: test\n", encoding="utf-8")
    artifact.write_text("[]", encoding="utf-8")

    manifest = build_manifest(spec, [], [artifact])

    assert manifest["source_failures"] == []
