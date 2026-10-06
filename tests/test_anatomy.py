from spatial_target_atlas.anatomy import (
    cell_category,
    render_body,
    render_cell_contexts,
    render_small_multiples,
    render_subcellular,
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

    assert "C</strong> HPA protein" in rendered
    assert "M</strong> ProteomicsDB" in rendered
    assert "Y</strong> spatial RNA" in rendered
    assert "K</strong> spatial protein" in rendered


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
    assert "cell-context-icon" in rendered
    assert "epithelial" in rendered
    assert "C 0.60" in rendered
    assert "K 0.70" in rendered


def test_subcellular_schematic_highlights_supported_compartments() -> None:
    rendered = render_subcellular(["Plasma membrane", "Cytosol"])

    assert "Subcellular localization schematic" in rendered
    assert 'stroke="#2563eb"' in rendered
    assert 'fill="#dbeafe"' in rendered
