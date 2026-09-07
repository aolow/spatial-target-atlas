import hashlib

from spatial_target_atlas.models import (
    EvidenceOrigin,
    Modality,
    ProteinEvidenceRecord,
    SpatialScale,
)
from spatial_target_atlas.provenance import build_manifest


def test_manifest_hashes_inputs_outputs_and_records_source_release(tmp_path) -> None:
    spec = tmp_path / "spec.yaml"
    artifact = tmp_path / "evidence.json"
    spec.write_text("name: test\n", encoding="utf-8")
    artifact.write_text("[]", encoding="utf-8")
    record = ProteinEvidenceRecord(
        gene_symbol="EPCAM", source="source", source_release="release",
        source_payload_sha256=["abc123"],
        evidence_origin=EvidenceOrigin.MEASURED, modality=Modality.MASS_SPECTROMETRY,
        spatial_scale=SpatialScale.TISSUE, citation_url="https://example.org",
        source_url="https://example.org/data",
    )

    manifest = build_manifest(spec, [record], [artifact])

    assert manifest["input_spec"]["sha256"] == hashlib.sha256(b"name: test\n").hexdigest()
    assert manifest["artifacts"][0]["sha256"] == hashlib.sha256(b"[]").hexdigest()
    assert manifest["sources"][0]["release"] == "release"
    assert manifest["sources"][0]["source_payload_sha256"] == ["abc123"]
