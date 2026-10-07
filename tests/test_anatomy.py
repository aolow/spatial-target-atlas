import spatial_target_atlas.anatomy as anatomy_module
import base64

from spatial_target_atlas import anatomy
from spatial_target_atlas.anatomy import (
    cell_category,
    fetch_default_anatomy_data_uri,
    fetch_default_anatomy_data_uri,
    render_body,
    render_cell_contexts,
    render_radial_atlas,
    render_small_multiples,
    render_subcellular,
    render_tissue_comparison,
    render_tissue_microenvironment,
)

COLORS = {
    "C": "#00b7d8",
    "M": "#d946ef",
    "Y": "#facc15",
    "K": "#111827",
}


def test_composite_anatomy_uses_alpha_layers_and_multiply_blending() -> None:
    regions = {
        "lung": {
            "channels": {
                "C": "positive",
                "M": "positive",
                "Y": "positive",
                "K": "positive",
            },
            "strengths": {"C": 1.0, "M": 0.5, "Y": 0.25, "K": 0.8},
        }
    }

    rendered = render_body(regions, COLORS)

    assert "mix-blend-mode:multiply" in rendered
    assert 'fill="#00b7d8"' in rendered
    assert 'fill="#d946ef"' in rendered
    assert 'fill="#facc15"' in rendered
    assert 'stroke="#111827"' in rendered
    assert 'fill-opacity="0.950"' in rendered


def test_small_multiples_render_each_source_separately() -> None:
    regions = {
        "liver": {
            "channels": {
                "C": "positive",
                "M": "unknown",
                "Y": "negative",
                "K": "unknown",
            },
            "strengths": {"C": 0.4, "M": None, "Y": 0.0, "K": None},
        }
    }

    rendered = render_small_multiples(regions, COLORS)

    assert "Human Protein Atlas protein" in rendered
    assert "ProteomicsDB protein" in rendered
    assert "Spatial RNA" in rendered
    assert "HuBMAP spatial protein" in rendered
    assert "<strong>C</strong>" not in rendered


def test_cell_icons_use_biological_categories() -> None:
    assert cell_category("lung microvascular endothelial cell") == "endothelial"
    assert cell_category("fibroblast of breast") == "fibroblast"
    assert cell_category("CD4-positive T cell") == "immune"
    assert cell_category("kidney epithelial cell") == "epithelial"

    rendered = render_cell_contexts(
        [
            {
                "cell_type": "kidney epithelial cell",
                "channels": {
                    "C": "positive",
                    "M": "unknown",
                    "Y": "positive",
                    "K": "positive",
                },
                "strengths": {"C": 0.6, "M": None, "Y": 0.3, "K": 0.7},
            }
        ],
        COLORS,
    )
    assert "cell-context-scene" in rendered
    assert "Epithelial tissue scene" in rendered
    assert "epithelial compartment" in rendered
    assert "Human Protein Atlas protein 60%" in rendered
    assert "HuBMAP spatial protein 70%" in rendered


def test_subcellular_schematic_highlights_supported_compartments() -> None:
    rendered = render_subcellular(["Plasma membrane", "Cytosol"])

    assert "Subcellular localization schematic" in rendered
    assert 'stroke="#2563eb"' in rendered
    assert 'fill="#dbeafe"' in rendered


def test_cell_contexts_render_distinct_tissue_scenes() -> None:
    rows = [
        {
            "cell_type": "capillary endothelial cell",
            "channels": {"C": "positive", "M": "unknown", "Y": "unknown", "K": "unknown"},
            "strengths": {"C": 0.4, "M": None, "Y": None, "K": None},
        },
        {
            "cell_type": "activated fibroblast",
            "channels": {"C": "positive", "M": "unknown", "Y": "positive", "K": "unknown"},
            "strengths": {"C": 0.5, "M": None, "Y": 0.2, "K": None},
        },
        {
            "cell_type": "CD8-positive T cell",
            "channels": {"C": "unknown", "M": "unknown", "Y": "positive", "K": "positive"},
            "strengths": {"C": None, "M": None, "Y": 0.6, "K": 0.8},
        },
    ]

    rendered = render_cell_contexts(rows, COLORS)

    assert "Endothelial vessel scene" in rendered
    assert "vascular lumen" in rendered
    assert "Fibroblast extracellular matrix scene" in rendered
    assert "collagen-rich ECM" in rendered
    assert "Immune microenvironment scene" in rendered
    assert "mixed immune field" in rendered


def test_radial_atlas_places_body_inside_tissue_tracks() -> None:
    regions = {
        "lung": {
            "channels": {"C": "positive", "M": "unknown", "Y": "unknown", "K": "positive"},
            "strengths": {"C": 0.8, "M": None, "Y": None, "K": 0.7},
        }
    }
    radial_tissues = [
        {
            "tissue": "lung",
            "tracks": {
                "hpa_protein": {"state": "positive", "strength": 0.8},
                "proteomicsdb_protein": {"state": "unknown", "strength": None},
                "spatial_rna": {"state": "unknown", "strength": None},
                "hubmap_spatial_protein": {"state": "positive", "strength": 0.7},
            },
        }
    ]

    rendered = render_radial_atlas(regions, radial_tissues, COLORS)

    assert "radial-tissue-tracks" in rendered
    assert "radial-center-body" in rendered
    assert "Radial body and tissue evidence atlas" in rendered
    assert "Lung" in rendered


def test_integrated_microenvironment_contains_all_major_compartments() -> None:
    microenvironment = {
        "epithelial": {
            "channels": {"C": "positive", "M": "unknown", "Y": "positive", "K": "positive"},
            "strengths": {"C": 0.7, "M": None, "Y": 0.4, "K": 0.6},
            "cell_types": ["alveolar epithelial cell"],
        },
        "fibroblast": {
            "channels": {"C": "positive", "M": "unknown", "Y": "unknown", "K": "unknown"},
            "strengths": {"C": 0.3, "M": None, "Y": None, "K": None},
            "cell_types": ["fibroblast"],
        },
        "endothelial": {
            "channels": {"C": "unknown", "M": "unknown", "Y": "positive", "K": "unknown"},
            "strengths": {"C": None, "M": None, "Y": 0.5, "K": None},
            "cell_types": ["capillary endothelial cell"],
        },
        "immune": {
            "channels": {"C": "unknown", "M": "unknown", "Y": "positive", "K": "positive"},
            "strengths": {"C": None, "M": None, "Y": 0.6, "K": 0.8},
            "cell_types": ["CD8-positive T cell"],
        },
    }

    rendered = render_tissue_microenvironment(microenvironment, COLORS)

    assert "Integrated tissue microenvironment evidence view" in rendered
    assert "epithelial compartment" in rendered
    assert "stromal / ECM compartment" in rendered
    assert "vascular compartment" in rendered
    assert "immune infiltrate" in rendered
    assert "alveolar epithelial cell" in rendered
    assert "capillary endothelial cell" in rendered


def test_radial_atlas_uses_v4_schematic_fallback() -> None:
    rendered = render_radial_atlas({}, [], COLORS)

    assert "radial-center-body" in rendered
    assert "professional-anatomy" not in rendered
    assert "body orientation" in rendered


def test_radial_atlas_uses_professional_anatomy_when_inlined() -> None:
    rendered = render_radial_atlas(
        {},
        [{"tissue": "lung", "tracks": {}}],
        COLORS,
        anatomy_data_uri="data:image/png;base64,AAAA",
    )

    assert "professional-anatomy" in rendered
    assert 'href="data:image/png;base64,AAAA"' in rendered
    assert "radial-center-body" not in rendered
    assert "Lung" in rendered


def test_fetch_default_anatomy_returns_data_uri(monkeypatch) -> None:  # noqa: ANN001
    class FakeResponse:
        content = b"png-bytes"
        headers = {"content-type": "image/png"}

        def raise_for_status(self) -> None:
            return None

    class FakeHttpx:
        @staticmethod
        def get(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            return FakeResponse()

    monkeypatch.setattr(anatomy_module, "import_module", lambda _name: FakeHttpx)

    uri = fetch_default_anatomy_data_uri()

    assert uri.startswith("data:image/png;base64,")
    assert "cG5nLWJ5dGVz" in uri


def test_normal_and_tumor_tissue_contexts_are_rendered_separately() -> None:
    microenvironments = {
        "normal_reference": {
            "available": True,
            "dataset_count": 1,
            "disease_labels": ["normal"],
            "compartments": {
                "epithelial": {
                    "channels": {"C": "positive", "M": "unknown", "Y": "positive", "K": "unknown"},
                    "strengths": {"C": 0.5, "M": None, "Y": 0.4, "K": None},
                    "cell_types": ["alveolar epithelial cell"],
                }
            },
        },
        "tumor": {
            "available": True,
            "dataset_count": 1,
            "disease_labels": ["lung adenocarcinoma"],
            "compartments": {
                "epithelial": {
                    "channels": {"C": "unknown", "M": "unknown", "Y": "positive", "K": "unknown"},
                    "strengths": {"C": None, "M": None, "Y": 0.8, "K": None},
                    "cell_types": ["malignant epithelial cell"],
                }
            },
            "bulk_paired": [
                {
                    "study_id": "PDC1",
                    "paired_case_count": 12,
                    "median_tumor_minus_adjacent": 1.2,
                    "tumor_higher_fraction": 0.75,
                }
            ],
        },
    }

    rendered = render_tissue_comparison(microenvironments, COLORS)

    assert "Normal / reference tissue" in rendered
    assert "Tumor tissue" in rendered
    assert "organized epithelium" in rendered
    assert "irregular tumor nests" in rendered
    assert "abnormal vessel" in rendered
    assert "lung adenocarcinoma" in rendered
    assert "Paired bulk tumor evidence" in rendered
    assert "not mapped onto specific cell compartments" in rendered


def test_tumor_panel_marks_missing_tumor_resolved_data() -> None:
    rendered = render_tissue_comparison(
        {
            "normal_reference": {"available": False, "compartments": {}},
            "tumor": {
                "available": False,
                "compartments": {},
                "bulk_paired": [],
            },
        },
        COLORS,
    )

    assert "No tumor-resolved cell/spatial evidence in this build" in rendered


def test_professional_anatomy_preserves_radial_categories() -> None:
    rendered = render_radial_atlas(
        {},
        [],
        COLORS,
        anatomy_data_uri="data:image/svg+xml;base64,PHN2Zy8+",
    )

    assert "professional-anatomy" in rendered
    assert "data:image/svg+xml;base64,PHN2Zy8+" in rendered
    assert "Brain" in rendered
    assert "Lung" in rendered
    assert "Kidney" in rendered
    assert "Large intestine" in rendered
    assert "radial-center-body" not in rendered


def test_radial_atlas_falls_back_to_v4_schematic() -> None:
    rendered = render_radial_atlas({}, [], COLORS)

    assert "radial-center-body" in rendered
    assert "professional-anatomy" not in rendered
    assert "M160 18" in rendered
    assert "M160 14" not in rendered


def test_fetch_default_anatomy_data_uri_inlines_vector(monkeypatch) -> None:  # noqa: ANN001
    class FakeResponse:
        content = b"<svg viewBox='0 0 600 1000'></svg>"
        headers = {"content-type": "image/svg+xml; charset=utf-8"}

        def raise_for_status(self) -> None:
            return None

    class FakeHttpx:
        @staticmethod
        def get(*args, **kwargs):  # noqa: ANN002, ANN003, ANN201
            return FakeResponse()

    monkeypatch.setattr(anatomy, "import_module", lambda name: FakeHttpx)

    uri = fetch_default_anatomy_data_uri()

    assert uri.startswith("data:image/svg+xml;base64,")
    decoded = base64.b64decode(uri.split(",", 1)[1]).decode("utf-8")
    assert "viewBox='0 0 600 1000'" in decoded
