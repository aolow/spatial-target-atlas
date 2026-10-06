from spatial_target_atlas.overlay import (
    build_overlay_payload,
    canonical_region,
    overlay_color,
    render_overlay_gallery,
)


def test_cmy_overlay_mix_and_k_outline_are_separate() -> None:
    assert (
        overlay_color({"C": "positive", "M": "unknown", "Y": "unknown", "K": "unknown"})
        == "#00b7d8"
    )
    assert (
        overlay_color({"C": "positive", "M": "positive", "Y": "unknown", "K": "unknown"})
        == "#2563eb"
    )
    assert (
        overlay_color({"C": "unknown", "M": "positive", "Y": "positive", "K": "positive"})
        == "#ef4444"
    )


def test_region_normalization_handles_lung_and_renal_labels() -> None:
    assert canonical_region("Bronchus and lung") == "lung"
    assert canonical_region("LL") == "lung"
    assert canonical_region("renal cortex") == "kidney"


def test_overlay_preserves_failed_source_as_unknown() -> None:
    evidence = [
        {
            "gene_symbol": "EPCAM",
            "source": "Human Protein Atlas",
            "spatial_scale": "tissue",
            "tissue": "lung",
            "detection_state": "detected",
            "value": 4.0,
        },
        {
            "gene_symbol": "EPCAM",
            "source": "ProteomicsDB",
            "spatial_scale": "tissue",
            "tissue": "lung",
            "detection_state": "quantified",
            "value": 3.0,
        },
    ]
    payload = build_overlay_payload(
        evidence,
        [],
        [],
        [],
        [{"stage": "proteomicsdb", "error_type": "ConnectError", "error": "x"}],
    )
    target = payload["targets"][0]
    lung = next(row for row in target["regions"] if row["region"] == "lung")

    assert lung["channels"]["C"] == "positive"
    assert lung["channels"]["M"] == "unknown"
    assert lung["fill"] == "#00b7d8"


def test_overlay_builds_dataset_resolved_views() -> None:
    cells = [
        {
            "gene_symbol": "EPCAM",
            "dataset_id": "HBM1",
            "dataset_uuid": "d1",
            "assay": "PhenoCycler",
            "organ": "LL",
            "cell_type": "epithelial",
            "positive_cell_fraction": 0.8,
            "median_source_scale_intensity": 8.0,
        },
        {
            "gene_symbol": "EPCAM",
            "dataset_id": "HBM1",
            "dataset_uuid": "d1",
            "assay": "PhenoCycler",
            "organ": "LL",
            "cell_type": "immune",
            "positive_cell_fraction": 0.2,
            "median_source_scale_intensity": 2.0,
        },
    ]
    payload = build_overlay_payload([], cells, [], [])
    views = payload["targets"][0]["dataset_views"]["hubmap_protein"]

    assert len(views) == 1
    assert views[0]["contexts"][0]["relative_intensity"] == 1.0
    assert views[0]["contexts"][1]["relative_intensity"] == 0.0

    rendered = render_overlay_gallery(payload)
    assert "Dataset-resolved views" in rendered
    assert "HBM1" in rendered
    assert "K" in rendered


def test_overlay_strengths_are_source_local() -> None:
    evidence = [
        {
            "gene_symbol": "EPCAM",
            "source": "Human Protein Atlas",
            "spatial_scale": "tissue",
            "modality": "mass_spectrometry",
            "tissue": "lung",
            "detection_state": "detected",
            "value": 100.0,
        },
        {
            "gene_symbol": "EPCAM",
            "source": "Human Protein Atlas",
            "spatial_scale": "tissue",
            "modality": "mass_spectrometry",
            "tissue": "liver",
            "detection_state": "detected",
            "value": 10.0,
        },
        {
            "gene_symbol": "EPCAM",
            "source": "ProteomicsDB",
            "spatial_scale": "tissue",
            "modality": "mass_spectrometry",
            "tissue": "lung",
            "detection_state": "detected",
            "value": 5.0,
        },
        {
            "gene_symbol": "EPCAM",
            "source": "ProteomicsDB",
            "spatial_scale": "tissue",
            "modality": "mass_spectrometry",
            "tissue": "liver",
            "detection_state": "detected",
            "value": 20.0,
        },
    ]
    census = [
        {
            "gene_symbol": "EPCAM",
            "tissue": "lung",
            "detection_state": "assayed_detected",
            "positive_spot_count": 5,
            "spot_count": 10,
            "positive_spot_fraction": 0.5,
        },
        {
            "gene_symbol": "EPCAM",
            "tissue": "liver",
            "detection_state": "assayed_detected",
            "positive_spot_count": 2,
            "spot_count": 20,
            "positive_spot_fraction": 0.1,
        },
    ]
    cells = [
        {
            "gene_symbol": "EPCAM",
            "organ": "lung",
            "positive_cell_count": 8,
            "cell_count": 10,
            "positive_cell_fraction": 0.8,
        },
        {
            "gene_symbol": "EPCAM",
            "organ": "liver",
            "positive_cell_count": 1,
            "cell_count": 10,
            "positive_cell_fraction": 0.1,
        },
    ]

    payload = build_overlay_payload(evidence, cells, census, [])
    regions = {
        row["region"]: row
        for row in payload["targets"][0]["regions"]
    }

    assert regions["lung"]["strengths"]["C"] == 1.0
    assert regions["liver"]["strengths"]["C"] == 0.25
    assert regions["lung"]["strengths"]["M"] == 0.25
    assert regions["liver"]["strengths"]["M"] == 1.0
    assert regions["lung"]["strengths"]["Y"] == 0.5
    assert regions["liver"]["strengths"]["Y"] == 0.1
    assert regions["lung"]["strengths"]["K"] == 0.8
    assert regions["liver"]["strengths"]["K"] == 0.1


def test_hpa_transcript_does_not_light_protein_cell_channel() -> None:
    evidence = [
        {
            "gene_symbol": "EPCAM",
            "source": "Human Protein Atlas",
            "spatial_scale": "cell_type",
            "modality": "transcriptomics",
            "cell_type": "epithelial cell",
            "detection_state": "detected",
            "value": 10.0,
        }
    ]

    payload = build_overlay_payload(evidence, [], [], [])

    assert payload["targets"][0]["cell_types"] == []
