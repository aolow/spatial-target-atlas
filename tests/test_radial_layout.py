from spatial_target_atlas.radial_layout import (
    TISSUE_ORDER,
    annular_sector_path,
    render_radial_tracks,
)


COLORS = {
    "C": "#00b7d8",
    "M": "#d946ef",
    "Y": "#facc15",
    "K": "#111827",
}


def test_radial_layout_has_stable_broad_tissue_coverage() -> None:
    assert len(TISSUE_ORDER) >= 24
    assert len(TISSUE_ORDER) == len(set(TISSUE_ORDER))
    assert "lung" in TISSUE_ORDER
    assert "kidney" in TISSUE_ORDER
    assert "lymph_node" in TISSUE_ORDER
    assert "vasculature" in TISSUE_ORDER


def test_annular_sector_path_is_closed_and_finite() -> None:
    path = annular_sector_path(500, 500, 330, 355, -90, -78)

    assert path.startswith("M ")
    assert path.endswith(" Z")
    assert "nan" not in path.casefold()
    assert "inf" not in path.casefold()


def test_radial_tracks_render_plain_source_names_and_states() -> None:
    tissues = [
        {
            "tissue": "lung",
            "tracks": {
                "hpa_protein": {"state": "positive", "strength": 0.8},
                "proteomicsdb_protein": {"state": "negative", "strength": None},
                "spatial_rna": {"state": "positive", "strength": 0.4},
                "hubmap_spatial_protein": {"state": "unknown", "strength": None},
            },
        }
    ]

    rendered = render_radial_tracks(tissues, COLORS)

    assert "Human Protein Atlas protein" in rendered
    assert "ProteomicsDB protein" in rendered
    assert "Spatial RNA" in rendered
    assert "HuBMAP spatial protein" in rendered
    assert "Lung" in rendered
    assert "state-positive" in rendered
    assert "state-negative" in rendered
    assert "state-unknown" in rendered
    assert "strength 80%" in rendered
