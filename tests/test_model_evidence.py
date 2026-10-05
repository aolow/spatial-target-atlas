import json

from spatial_target_atlas.model_evidence import (
    import_pinnacle_contexts,
    load_model_evidence,
)


def test_imports_only_requested_pinnacle_target_contexts(tmp_path) -> None:
    identities = tmp_path / "target_identities.json"
    identities.write_text(json.dumps([
        {
            "input_id": "EPCAM",
            "ensembl_id": "ENSG1",
            "gene_symbol": "EPCAM",
            "uniprot_id": "P16422",
            "resolution_sources": ["Ensembl REST"],
            "source_urls": ["https://example.test"],
            "source_payload_sha256": [],
            "retrieved_at": "2026-10-05T00:00:00Z",
        },
        {
            "input_id": "MSLN",
            "ensembl_id": "ENSG2",
            "gene_symbol": "MSLN",
            "uniprot_id": "Q13421",
            "resolution_sources": ["Ensembl REST"],
            "source_urls": ["https://example.test"],
            "source_payload_sha256": [],
            "retrieved_at": "2026-10-05T00:00:00Z",
        },
    ]), encoding="utf-8")
    labels = tmp_path / "pinnacle_labels_dict.txt"
    labels.write_text(str({
        "Cell Type": [
            "lung epithelial cell", "fibroblast", "CCI_lung epithelial cell", "BTO:0000763",
        ],
        "Name": ["EPCAM", "P16422", "EPCAM", "MSLN"],
    }), encoding="utf-8")
    embedding = tmp_path / "pinnacle_protein_embed.pth"
    embedding.write_bytes(b"not-loaded-by-spatial-target-atlas")

    records, summary = import_pinnacle_contexts(labels, identities, embedding)

    assert len(records) == 2
    assert {record.context for record in records} == {"lung epithelial cell", "fibroblast"}
    assert all(record.gene_symbol == "EPCAM" for record in records)
    assert all(record.score is None for record in records)
    assert all(record.evidence_origin == "model_derived" for record in records)
    assert summary["matched_targets"] == ["EPCAM"]
    assert summary["unmatched_targets"] == ["MSLN"]
    assert summary["embedding_sha256"]


def test_model_evidence_round_trip_validation(tmp_path) -> None:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps([{
        "model_name": "SPATIA",
        "model_version": "example",
        "evidence_origin": "model_derived",
        "evidence_kind": "downstream_target_score",
        "gene_symbol": "EPCAM",
        "ensembl_id": "ENSG1",
        "uniprot_id": "P16422",
        "context_type": "niche",
        "context": "tumor_epithelial_niche",
        "tissue": "lung",
        "score_name": "example_score",
        "score": 0.8,
        "representation_ref": None,
        "source_url": "https://example.test/model",
        "citation_url": "https://example.test/paper",
        "source_payload_sha256": [],
        "note": "Externally computed target-level downstream score.",
    }]), encoding="utf-8")

    records = load_model_evidence(path)

    assert records[0].model_name == "SPATIA"
    assert records[0].score == 0.8
    assert records[0].evidence_origin == "model_derived"
