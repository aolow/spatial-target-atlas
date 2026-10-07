import json

from spatial_target_atlas.visualization import render_atlas_html


def write_json(path, value) -> None:  # noqa: ANN001
    path.write_text(json.dumps(value), encoding="utf-8")


def test_render_atlas_html_combines_core_and_optional_outputs(tmp_path) -> None:
    core = tmp_path / "core"
    cells = tmp_path / "cells"
    census = tmp_path / "census"
    core.mkdir()
    cells.mkdir()
    census.mkdir()

    write_json(core / "target_identities.json", [{
        "gene_symbol": "EPCAM", "ensembl_id": "ENSG1",
    }])
    write_json(core / "evidence.json", [{
        "gene_symbol": "EPCAM", "source": "Human Protein Atlas",
        "modality": "mass_spectrometry", "spatial_scale": "tissue",
        "tissue": "lung", "cell_type": None, "detection_state": "detected",
    }])
    write_json(core / "concordance.json", [{
        "gene": "EPCAM", "contexts": 10, "complete_detected_contexts": 6,
        "spearman": 0.5,
        "detection_concordance": {"rna_only": 2, "protein_only": 1},
    }])
    write_json(core / "cross_source_concordance.json", [{
        "gene": "EPCAM", "common_tissues": 5, "spearman": 0.4,
        "interpretation": "Within-source ranks",
    }])
    write_json(core / "paired_tumor_normal.json", [{
        "gene_symbol": "EPCAM", "study_id": "PDC1", "paired_case_count": 20,
        "median_paired_tumor_minus_adjacent_log2_ratio": 0.7,
        "tumor_higher_fraction": 0.8, "interpretation": "paired only",
    }])
    write_json(core / "spatial_target_coverage.json", [{
        "gene_symbol": "EPCAM", "dataset_uuid": "d1", "coverage_state": "assayed",
    }])

    write_json(cells / "hubmap_cell_protein_summary.json", [{
        "dataset_uuid": "d1", "dataset_id": "HBM1", "assay": "PhenoCycler",
        "organ": "lung", "donor_id": "D1", "gene_symbol": "EPCAM",
        "ensembl_id": "ENSG1", "uniprot_id": "P1", "protein_id": "EPCAM",
        "cell_type": "epithelial", "cell_count": 100, "positive_cell_count": 75,
        "positive_cell_fraction": 0.75, "mean_source_scale_intensity": 2.0,
        "median_source_scale_intensity": 1.5,
    }])
    write_json(cells / "hubmap_cell_query_status.json", [{
        "dataset_id": "HBM1", "gene_symbol": "EPCAM", "protein_id": "EPCAM",
        "status": "complete", "cell_count": 100, "records": 100, "message": "ok",
    }])
    write_json(census / "census_spatial_expression.json", [{
        "gene_symbol": "EPCAM", "reference_context": "source_labeled_normal_adult_or_unspecified",
        "dataset_id": "c1", "donor_id": "D2", "spot_count": 50,
        "positive_spot_count": 25, "detection_state": "assayed_detected",
    }])
    model_evidence = tmp_path / "model_evidence.json"
    write_json(model_evidence, [{
        "model_name": "PINNACLE", "model_version": "published",
        "evidence_origin": "model_derived",
        "evidence_kind": "contextual_representation_available",
        "gene_symbol": "EPCAM", "ensembl_id": "ENSG1", "uniprot_id": "P1",
        "context_type": "cell_type", "context": "epithelial cell", "tissue": None,
        "score_name": None, "score": None, "representation_ref": "embed.pth",
        "source_url": "https://example.test", "citation_url": "https://example.test/paper",
        "source_payload_sha256": [], "note": "Representation availability only.",
    }])
    audit = tmp_path / "audit.json"
    write_json(audit, {"candidates": [{
        "reference_context": "source_labeled_normal_adult_or_unspecified",
        "role": "primary_candidate", "rank": 1, "donor_count": 2,
        "dataset_count": 2, "caveats": ["low donor depth"],
    }]})

    rendered = render_atlas_html(
        core,
        cells,
        census,
        audit,
        model_evidence,
        anatomy_data_uri="data:image/png;base64,AAAA",
    )

    assert "<h2>EPCAM</h2>" in rendered
    assert "EPCAM spatial atlas" in rendered
    assert "Normal versus tumor tissue context" in rendered
    assert "Normal / reference tissue" in rendered
    assert "Tumor tissue" in rendered
    assert "radial-tissue-tracks" in rendered
    assert "professional-anatomy" in rendered
    assert "DataBase Center for Life Science" in rendered
    assert "Human Protein Atlas protein" in rendered
    assert "Dataset-resolved views" in rendered
    assert "HuBMAP per-cell protein summaries" in rendered
    assert "Spatial transcriptomic reference contexts" in rendered
    assert "Reference context audit" in rendered
    assert "Model-derived context" in rendered
    assert "Representation availability only." in rendered
    assert "0.75" in rendered


def test_render_escapes_untrusted_labels(tmp_path) -> None:
    core = tmp_path / "core"
    core.mkdir()
    write_json(core / "target_identities.json", [{"gene_symbol": "<script>alert(1)</script>"}])
    write_json(core / "evidence.json", [])
    write_json(core / "concordance.json", [])
    write_json(core / "cross_source_concordance.json", [])
    write_json(core / "paired_tumor_normal.json", [])
    write_json(core / "spatial_target_coverage.json", [])

    rendered = render_atlas_html(core)

    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered
