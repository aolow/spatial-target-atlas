"""Spatial overlay payloads and self-contained SVG/HTML rendering."""

from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from .anatomy import (
    DEFAULT_ANATOMY_ATTRIBUTION,
    DEFAULT_ANATOMY_LICENSE_URL,
    DEFAULT_ANATOMY_SOURCE_URL,
    cell_category,
    render_radial_atlas,
    render_subcellular,
    render_tissue_comparison,
)
from .radial_layout import TISSUE_DISPLAY_NAMES, TISSUE_ORDER

CHANNELS = {
    "C": {
        "label": "Human Protein Atlas protein",
        "description": "Human Protein Atlas tissue protein evidence",
        "color": "#00b7d8",
    },
    "M": {
        "label": "ProteomicsDB protein",
        "description": "ProteomicsDB tissue protein evidence",
        "color": "#d946ef",
    },
    "Y": {
        "label": "Spatial RNA",
        "description": "CELLxGENE spatial transcriptomic positivity",
        "color": "#facc15",
    },
    "K": {
        "label": "HuBMAP spatial protein",
        "description": "HuBMAP per-cell protein positivity",
        "color": "#111827",
    },
}

# Schematic, deliberately simple body coordinates rather than anatomical claims.
BODY_REGIONS: dict[str, dict[str, Any]] = {
    "brain": {"x": 150, "y": 58, "shape": "ellipse", "rx": 28, "ry": 18},
    "thyroid": {"x": 150, "y": 112, "shape": "ellipse", "rx": 14, "ry": 8},
    "lung": {"x": 150, "y": 170, "shape": "lungs"},
    "heart": {"x": 150, "y": 193, "shape": "heart"},
    "liver": {"x": 176, "y": 234, "shape": "ellipse", "rx": 31, "ry": 18},
    "stomach": {"x": 128, "y": 242, "shape": "ellipse", "rx": 19, "ry": 14},
    "pancreas": {"x": 151, "y": 258, "shape": "ellipse", "rx": 26, "ry": 7},
    "kidney": {"x": 150, "y": 273, "shape": "kidneys"},
    "spleen": {"x": 111, "y": 236, "shape": "ellipse", "rx": 11, "ry": 16},
    "colon": {"x": 150, "y": 307, "shape": "colon"},
    "bladder": {"x": 150, "y": 350, "shape": "ellipse", "rx": 13, "ry": 11},
    "breast": {"x": 150, "y": 176, "shape": "breast"},
    "skin": {"x": 225, "y": 210, "shape": "skin"},
}

_TISSUE_ALIASES = {
    "vasculature": ("vasculature", "blood vessel", "artery", "vein", "vascular"),
    "bone_marrow": ("bone marrow", "marrow"),
    "lymph_node": ("lymph node", "lymphoid node"),
    "small_intestine": ("small intestine", "ileum", "jejunum", "duodenum"),
    "salivary_gland": ("salivary gland", "parotid", "submandibular"),
    "brain": ("brain", "cerebr", "cerebral cortex"),
    "thyroid": ("thyroid",),
    "trachea": ("trachea",),
    "lung": ("lung", "bronch", "alveol"),
    "heart": ("heart", "cardiac", "myocard"),
    "liver": ("liver", "hepatic"),
    "stomach": ("stomach", "gastric"),
    "pancreas": ("pancrea",),
    "kidney": ("kidney", "renal"),
    "spleen": ("spleen",),
    "thymus": ("thymus",),
    "colon": ("colon", "large intestine", "rectum", "colorectal"),
    "bladder": ("bladder", "urothel"),
    "breast": ("breast", "mammary"),
    "skin": ("skin", "epiderm", "dermis"),
    "fat": ("adipose", "fat"),
    "muscle": ("skeletal muscle", "muscle"),
    "ovary": ("ovary", "ovarian"),
    "prostate": ("prostate",),
    "testis": ("testis", "testicular"),
    "tongue": ("tongue",),
    "uterus": ("uterus", "uterine", "endometrium"),
}

_POSITIVE_STATES = {
    "detected",
    "quantified",
    "specific_expression",
    "assayed",
    "assayed_detected",
}


def build_overlay_from_files(
    core_dir: Path,
    hubmap_cells_dir: Path | None = None,
    spatial_census_dir: Path | None = None,
) -> dict[str, Any]:
    """Build an overlay payload from saved Spatial Target Atlas outputs."""
    evidence = _read_list(core_dir / "evidence.json")
    paired = _read_list(core_dir / "paired_tumor_normal.json")
    cells = (
        _read_list(hubmap_cells_dir / "hubmap_cell_protein_summary.json")
        if hubmap_cells_dir is not None
        else []
    )
    census = (
        _read_list(spatial_census_dir / "census_spatial_expression.json")
        if spatial_census_dir is not None
        else []
    )
    status = _read_object(core_dir / "source_status.json")
    failures = status.get("failures")
    source_failures = failures if isinstance(failures, list) else []
    return build_overlay_payload(evidence, cells, census, paired, source_failures)


def build_overlay_payload(
    evidence: list[dict[str, Any]],
    cell_summary: list[dict[str, Any]],
    census: list[dict[str, Any]],
    paired: list[dict[str, Any]],
    source_failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a source-aware spatial visualization payload.

    Cross-source overlays use categorical positivity only. Quantitative values are
    retained in dataset-specific views and are never pooled across assays.
    """
    failures = {
        str(item.get("stage"))
        for item in (source_failures or [])
        if isinstance(item, dict) and item.get("stage")
    }
    targets = sorted({
        str(row.get("gene_symbol"))
        for rows in (evidence, cell_summary, census, paired)
        for row in rows
        if row.get("gene_symbol")
    })
    return {
        "schema_version": "4.0",
        "overlay_semantics": {
            "C": CHANNELS["C"],
            "M": CHANNELS["M"],
            "Y": CHANNELS["Y"],
            "K": CHANNELS["K"],
            "mixing": (
                "C/M/Y are rendered as transparent source-colored organ layers with "
                "multiply blending; K is a dark outline so spatial-protein support "
                "does not erase the other channels."
            ),
            "strength_rule": (
                "HPA and ProteomicsDB opacity uses within-target, within-source "
                "relative tissue intensity. Spatial RNA uses positive-spot fraction. "
                "HuBMAP spatial protein uses positive-cell fraction. Strengths are "
                "never compared numerically across source families."
            ),
            "context_rule": (
                "The body and radial tissue atlas use normal/reference spatial context. "
                "Tumor-labeled spatial RNA is rendered separately in the tumor tissue panel. "
                "PDC paired tumor-versus-adjacent evidence remains bulk context and is never "
                "mapped onto specific cell compartments."
            ),
            "quantitative_rule": (
                "Dataset-resolved intensity is shown only within a dataset/source-specific "
                "view and is never normalized across datasets."
            ),
        },
        "targets": [
            _target_payload(target, evidence, cell_summary, census, paired, failures)
            for target in targets
        ],
    }


def _target_payload(
    target: str,
    evidence: list[dict[str, Any]],
    cell_summary: list[dict[str, Any]],
    census: list[dict[str, Any]],
    paired: list[dict[str, Any]],
    failures: set[str],
) -> dict[str, Any]:
    target_evidence = [row for row in evidence if row.get("gene_symbol") == target]
    target_cells = [row for row in cell_summary if row.get("gene_symbol") == target]
    target_census = [row for row in census if row.get("gene_symbol") == target]
    reference_census = [
        row for row in target_census if _is_reference_census_row(row)
    ]
    tumor_census = [
        row for row in target_census if _is_tumor_census_row(row)
    ]
    hpa_strengths = _relative_region_strength(
        target_evidence,
        source="Human Protein Atlas",
        scale="tissue",
        modality="mass_spectrometry",
    )
    pdb_strengths = _relative_region_strength(
        target_evidence,
        source="ProteomicsDB",
        scale="tissue",
        modality="mass_spectrometry",
    )
    rna_strengths = _fraction_region_strength(
        reference_census,
        numerator="positive_spot_count",
        denominator="spot_count",
    )
    protein_strengths = _fraction_region_strength(
        target_cells,
        numerator="positive_cell_count",
        denominator="cell_count",
        fallback_fraction="positive_cell_fraction",
    )
    regions = []
    for region in BODY_REGIONS:
        channels = {
            "C": _hpa_state(target_evidence, region, failures),
            "M": _proteomicsdb_state(target_evidence, region, failures),
            "Y": _census_state(reference_census, region),
            "K": _hubmap_state(target_cells, region),
        }
        if any(state != "unknown" for state in channels.values()):
            regions.append(
                {
                    "region": region,
                    "channels": channels,
                    "strengths": {
                        "C": hpa_strengths.get(region),
                        "M": pdb_strengths.get(region),
                        "Y": rna_strengths.get(region),
                        "K": protein_strengths.get(region),
                    },
                    "fill": overlay_color(channels),
                    "k_outline": channels["K"] == "positive",
                    "evidence_count": _region_evidence_count(
                        target_evidence, target_cells, reference_census, region
                    ),
                }
            )

    reference_cell_types = _cell_type_overlay(
        target_evidence,
        target_cells,
        reference_census,
    )
    tumor_cell_types = _cell_type_overlay([], [], tumor_census)
    subcellular = _subcellular_locations(target_evidence)
    disease = [
        {
            "study_id": row.get("study_id"),
            "paired_case_count": row.get("paired_case_count"),
            "median_tumor_minus_adjacent": row.get(
                "median_paired_tumor_minus_adjacent_log2_ratio"
            ),
            "tumor_higher_fraction": row.get("tumor_higher_fraction"),
        }
        for row in paired
        if row.get("gene_symbol") == target
    ]
    radial_tissues = _radial_tissue_payload(
        target_evidence,
        target_cells,
        reference_census,
        failures,
        hpa_strengths,
        pdb_strengths,
        rna_strengths,
        protein_strengths,
    )
    reference_microenvironment = _microenvironment_payload(reference_cell_types)
    tumor_microenvironment = _microenvironment_payload(tumor_cell_types)
    microenvironments = {
        "normal_reference": {
            "label": "Normal / reference tissue",
            "available": bool(reference_cell_types),
            "dataset_count": len({
                str(row.get("dataset_id"))
                for row in reference_census
                if row.get("dataset_id")
            }),
            "disease_labels": sorted({
                str(row.get("disease"))
                for row in reference_census
                if row.get("disease")
            }),
            "compartments": reference_microenvironment,
        },
        "tumor": {
            "label": "Tumor tissue",
            "available": bool(tumor_cell_types),
            "dataset_count": len({
                str(row.get("dataset_id"))
                for row in tumor_census
                if row.get("dataset_id")
            }),
            "disease_labels": sorted({
                str(row.get("disease"))
                for row in tumor_census
                if row.get("disease")
            }),
            "compartments": tumor_microenvironment,
            "bulk_paired": disease,
        },
    }
    return {
        "gene_symbol": target,
        "regions": regions,
        "radial_tissues": radial_tissues,
        "cell_types": reference_cell_types,
        "microenvironment": reference_microenvironment,
        "microenvironments": microenvironments,
        "subcellular": subcellular,
        "disease_context": disease,
        "dataset_views": {
            "hubmap_protein": _hubmap_dataset_views(target_cells),
            "spatial_rna": _census_dataset_views(target_census),
        },
    }


_TUMOR_TERMS = (
    "cancer",
    "carcinoma",
    "tumor",
    "tumour",
    "malignan",
    "adenocarcinoma",
    "melanoma",
    "sarcoma",
    "lymphoma",
    "leukemia",
    "glioma",
    "neoplasm",
)


def _is_reference_census_row(row: dict[str, Any]) -> bool:
    context = str(row.get("reference_context") or "").casefold()
    disease = str(row.get("disease") or "").casefold()
    return context != "disease_tissue" and disease in {"", "normal", "healthy"}


def _is_tumor_census_row(row: dict[str, Any]) -> bool:
    context = str(row.get("reference_context") or "").casefold()
    disease = str(row.get("disease") or "").casefold()
    return context == "disease_tissue" and any(term in disease for term in _TUMOR_TERMS)


def canonical_region(value: Any) -> str | None:
    text = str(value or "").strip().casefold()
    if not text:
        return None
    if text in {"ll", "rl"}:
        return "lung"
    if text in {"blood", "whole blood", "peripheral blood"}:
        return "blood"
    for region, aliases in _TISSUE_ALIASES.items():
        if any(alias in text for alias in aliases):
            return region
    return None


def overlay_color(channels: dict[str, str]) -> str:
    """Return the C/M/Y categorical mix; K is rendered separately as outline."""
    c = channels.get("C") == "positive"
    m = channels.get("M") == "positive"
    y = channels.get("Y") == "positive"
    key = (c, m, y)
    return {
        (False, False, False): "#e5e7eb",
        (True, False, False): "#00b7d8",
        (False, True, False): "#d946ef",
        (False, False, True): "#facc15",
        (True, True, False): "#2563eb",
        (True, False, True): "#22c55e",
        (False, True, True): "#ef4444",
        (True, True, True): "#334155",
    }[key]


def render_spatial_vignette(
    target_payload: dict[str, Any],
    anatomy_data_uri: str | None = None,
) -> str:
    target = _e(target_payload.get("gene_symbol") or "target")
    region_map = {
        str(item.get("region")): item
        for item in target_payload.get("regions", [])
        if isinstance(item, dict)
    }
    radial_tissues = [
        item
        for item in target_payload.get("radial_tissues", [])
        if isinstance(item, dict)
    ]
    raw_microenvironments = target_payload.get("microenvironments")
    microenvironments = (
        raw_microenvironments if isinstance(raw_microenvironments, dict) else {}
    )
    colors = {key: str(value["color"]) for key, value in CHANNELS.items()}
    radial = render_radial_atlas(
        region_map,
        radial_tissues,
        colors,
        anatomy_data_uri=anatomy_data_uri,
    )
    tissue = render_tissue_comparison(microenvironments, colors)
    legend = _legend_html()
    subcellular = render_subcellular(target_payload.get("subcellular", []))
    datasets = _dataset_views_html(target_payload.get("dataset_views", {}))
    disease = _disease_html(target_payload.get("disease_context", []))
    return (
        f'<div class="spatial-vignette spatial-v4"><div class="spatial-head">'
        f"<div><h3>{target} spatial atlas</h3>"
        '<p class="note">Body orientation sits in the center; radial tracks carry '
        "source-specific tissue evidence. Opacity remains source-local.</p></div>"
        f"{legend}</div>"
        f'<div class="radial-panel">{radial}{disease}'
        + (
            '<p class="anatomy-credit">'
            f'{_e(DEFAULT_ANATOMY_ATTRIBUTION)} '
            f'<a href="{_e(DEFAULT_ANATOMY_SOURCE_URL)}">Source</a> · '
            f'<a href="{_e(DEFAULT_ANATOMY_LICENSE_URL)}">License</a>'
            "</p>"
            if anatomy_data_uri is not None
            else ""
        )
        + "</div>"
        '<div class="hierarchy-grid">'
        f'<div class="tissue-panel"><h4>Normal versus tumor tissue context</h4>{tissue}</div>'
        f'<div class="subcellular-panel"><h4>Subcellular localization</h4>{subcellular}</div>'
        "</div>"
        f"{datasets}</div>"
    )


def render_overlay_gallery(
    payload: dict[str, Any],
    anatomy_data_uri: str | None = None,
) -> str:
    return "".join(
        render_spatial_vignette(target, anatomy_data_uri=anatomy_data_uri)
        for target in payload.get("targets", [])
        if isinstance(target, dict)
    )


def _state_from_records(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "unknown"
    if any(_row_positive(row) for row in rows):
        return "positive"
    if any(
        str(row.get("detection_state") or "") in {"not_detected", "assayed_not_detected"}
        for row in rows
    ):
        return "negative"
    return "unknown"


def _row_positive(row: dict[str, Any]) -> bool:
    state = str(row.get("detection_state") or "")
    if state in _POSITIVE_STATES:
        return True
    value = row.get("value")
    return isinstance(value, (int, float)) and value > 0


def _region_rows(rows: list[dict[str, Any]], region: str) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if canonical_region(row.get("tissue") or row.get("organ")) == region
    ]


def _hpa_state(
    evidence: list[dict[str, Any]], region: str, failures: set[str]
) -> str:
    if "hpa.tissue" in failures:
        return "unknown"
    rows = [
        row
        for row in _region_rows(evidence, region)
        if str(row.get("source") or "") == "Human Protein Atlas"
        and str(row.get("spatial_scale") or "") == "tissue"
    ]
    return _state_from_records(rows)


def _proteomicsdb_state(
    evidence: list[dict[str, Any]], region: str, failures: set[str]
) -> str:
    if "proteomicsdb" in failures:
        return "unknown"
    rows = [
        row
        for row in _region_rows(evidence, region)
        if str(row.get("source") or "") == "ProteomicsDB"
    ]
    # ProteomicsDB connector records quantified evidence; absence is not a negative.
    return "positive" if any(_row_positive(row) for row in rows) else "unknown"


def _census_state(rows: list[dict[str, Any]], region: str) -> str:
    subset = _region_rows(rows, region)
    if not subset:
        return "unknown"
    assayed = [row for row in subset if row.get("detection_state") != "not_assayed"]
    if not assayed:
        return "unknown"
    if any(float(row.get("positive_spot_fraction") or 0) > 0 for row in assayed):
        return "positive"
    return "negative"


def _hubmap_state(rows: list[dict[str, Any]], region: str) -> str:
    subset = _region_rows(rows, region)
    if not subset:
        return "unknown"
    if any(float(row.get("positive_cell_fraction") or 0) > 0 for row in subset):
        return "positive"
    return "negative"


def _region_evidence_count(
    evidence: list[dict[str, Any]],
    cells: list[dict[str, Any]],
    census: list[dict[str, Any]],
    region: str,
) -> int:
    return (
        len(_region_rows(evidence, region))
        + len(_region_rows(cells, region))
        + len(_region_rows(census, region))
    )


def _cell_type_overlay(
    evidence: list[dict[str, Any]],
    cells: list[dict[str, Any]],
    census: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    names = sorted({
        str(row.get("cell_type"))
        for rows in (evidence, cells, census)
        for row in rows
        if row.get("cell_type")
    })
    output: list[dict[str, Any]] = []
    for name in names:
        hpa = [
            row for row in evidence
            if row.get("cell_type") == name
            and row.get("source") == "Human Protein Atlas"
            and row.get("spatial_scale") == "cell_type"
            and row.get("modality") == "mass_spectrometry"
        ]
        spatial_rna = [row for row in census if row.get("cell_type") == name]
        spatial_protein = [row for row in cells if row.get("cell_type") == name]
        channels = {
            "C": _state_from_records(hpa),
            "M": "unknown",
            "Y": (
                "positive"
                if any(float(row.get("positive_spot_fraction") or 0) > 0 for row in spatial_rna)
                else ("negative" if spatial_rna else "unknown")
            ),
            "K": (
                "positive"
                if any(float(row.get("positive_cell_fraction") or 0) > 0 for row in spatial_protein)
                else ("negative" if spatial_protein else "unknown")
            ),
        }
        hpa_values = [
            float(row["value"])
            for row in hpa
            if isinstance(row.get("value"), (int, float))
            and float(row["value"]) > 0
        ]
        hpa_strength = median(hpa_values) if hpa_values else None
        y_strength = _weighted_fraction(
            spatial_rna,
            numerator="positive_spot_count",
            denominator="spot_count",
            fallback_fraction="positive_spot_fraction",
        )
        k_strength = _weighted_fraction(
            spatial_protein,
            numerator="positive_cell_count",
            denominator="cell_count",
            fallback_fraction="positive_cell_fraction",
        )
        if any(state != "unknown" for state in channels.values()):
            output.append({
                "cell_type": name,
                "channels": channels,
                "strengths": {
                    "C": hpa_strength,
                    "M": None,
                    "Y": y_strength,
                    "K": k_strength,
                },
                "fill": overlay_color(channels),
                "k_outline": channels["K"] == "positive",
            })
    c_values = [
        float(row["strengths"]["C"])
        for row in output
        if isinstance(row.get("strengths"), dict)
        and isinstance(row["strengths"].get("C"), (int, float))
    ]
    if c_values:
        low = min(c_values)
        high = max(c_values)
        for row in output:
            strengths = row.get("strengths")
            if not isinstance(strengths, dict):
                continue
            value = strengths.get("C")
            if not isinstance(value, (int, float)):
                continue
            strengths["C"] = (
                1.0
                if high <= low
                else 0.25 + 0.75 * ((float(value) - low) / (high - low))
            )
    return output[:24]


def _radial_tissue_payload(
    evidence: list[dict[str, Any]],
    cells: list[dict[str, Any]],
    census: list[dict[str, Any]],
    failures: set[str],
    hpa_strengths: dict[str, float],
    pdb_strengths: dict[str, float],
    rna_strengths: dict[str, float],
    protein_strengths: dict[str, float],
) -> list[dict[str, Any]]:
    output = []
    for tissue in TISSUE_ORDER:
        tracks = {
            "hpa_protein": {
                "state": _hpa_state(evidence, tissue, failures),
                "strength": hpa_strengths.get(tissue),
            },
            "proteomicsdb_protein": {
                "state": _proteomicsdb_state(evidence, tissue, failures),
                "strength": pdb_strengths.get(tissue),
            },
            "spatial_rna": {
                "state": _census_state(census, tissue),
                "strength": rna_strengths.get(tissue),
            },
            "hubmap_spatial_protein": {
                "state": _hubmap_state(cells, tissue),
                "strength": protein_strengths.get(tissue),
            },
        }
        output.append({
            "tissue": tissue,
            "display_name": TISSUE_DISPLAY_NAMES[tissue],
            "tracks": tracks,
            "has_evidence": any(
                str(track.get("state")) != "unknown" for track in tracks.values()
            ),
        })
    return output


def _microenvironment_payload(
    cell_types: list[dict[str, Any]],
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in cell_types:
        grouped[cell_category(str(row.get("cell_type") or ""))].append(row)

    output: dict[str, Any] = {}
    for category in ("epithelial", "fibroblast", "endothelial", "immune", "other"):
        rows = grouped.get(category, [])
        if not rows:
            output[category] = {
                "channels": {key: "unknown" for key in CHANNELS},
                "strengths": {key: None for key in CHANNELS},
                "cell_types": [],
            }
            continue

        channels: dict[str, str] = {}
        strengths: dict[str, float | None] = {}
        for channel in CHANNELS:
            states = [
                str(row.get("channels", {}).get(channel) or "unknown")
                for row in rows
                if isinstance(row.get("channels"), dict)
            ]
            channels[channel] = (
                "positive"
                if "positive" in states
                else ("negative" if "negative" in states else "unknown")
            )
            values = [
                float(row["strengths"][channel])
                for row in rows
                if isinstance(row.get("strengths"), dict)
                and isinstance(row["strengths"].get(channel), (int, float))
            ]
            strengths[channel] = median(values) if values else None

        output[category] = {
            "channels": channels,
            "strengths": strengths,
            "cell_types": sorted({
                str(row.get("cell_type"))
                for row in rows
                if row.get("cell_type")
            }),
        }
    return output


def _relative_region_strength(
    rows: list[dict[str, Any]],
    *,
    source: str,
    scale: str,
    modality: str,
) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if (
            row.get("source") != source
            or row.get("spatial_scale") != scale
            or row.get("modality") != modality
        ):
            continue
        region = canonical_region(row.get("tissue") or row.get("organ"))
        value = row.get("value")
        if region is None or not isinstance(value, (int, float)) or float(value) <= 0:
            continue
        grouped[region].append(float(value))

    medians = {region: median(values) for region, values in grouped.items()}
    if not medians:
        return {}
    low = min(medians.values())
    high = max(medians.values())
    if high <= low:
        return {region: 1.0 for region in medians}
    return {
        region: 0.25 + 0.75 * ((value - low) / (high - low))
        for region, value in medians.items()
    }


def _fraction_region_strength(
    rows: list[dict[str, Any]],
    *,
    numerator: str,
    denominator: str,
    fallback_fraction: str | None = None,
) -> dict[str, float]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        region = canonical_region(row.get("tissue") or row.get("organ"))
        if region is not None:
            grouped[region].append(row)
    output: dict[str, float] = {}
    for region, subset in grouped.items():
        value = _weighted_fraction(
            subset,
            numerator=numerator,
            denominator=denominator,
            fallback_fraction=fallback_fraction,
        )
        if value is not None:
            output[region] = value
    return output


def _weighted_fraction(
    rows: list[dict[str, Any]],
    *,
    numerator: str,
    denominator: str,
    fallback_fraction: str | None = None,
) -> float | None:
    numerator_total = 0.0
    denominator_total = 0.0
    weighted_fraction = 0.0
    weight_total = 0.0
    for row in rows:
        num = row.get(numerator)
        den = row.get(denominator)
        if isinstance(num, (int, float)) and isinstance(den, (int, float)) and float(den) > 0:
            numerator_total += float(num)
            denominator_total += float(den)
            continue
        if fallback_fraction is not None:
            fraction = row.get(fallback_fraction)
            weight = row.get(denominator)
            if isinstance(fraction, (int, float)):
                numeric_weight = (
                    float(weight)
                    if isinstance(weight, (int, float)) and float(weight) > 0
                    else 1.0
                )
                weighted_fraction += float(fraction) * numeric_weight
                weight_total += numeric_weight
    if denominator_total > 0:
        return max(0.0, min(1.0, numerator_total / denominator_total))
    if weight_total > 0:
        return max(0.0, min(1.0, weighted_fraction / weight_total))
    return None


def _subcellular_locations(evidence: list[dict[str, Any]]) -> list[str]:
    values = {
        str(row.get("subcellular_location")).strip()
        for row in evidence
        if row.get("spatial_scale") == "subcellular"
        and row.get("subcellular_location")
    }
    return sorted(values)


def _hubmap_dataset_views(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("dataset_id") or row.get("dataset_uuid") or "unknown")].append(row)
    output = []
    for dataset, subset in sorted(grouped.items()):
        values = [float(row.get("median_source_scale_intensity") or 0) for row in subset]
        low, high = (min(values), max(values)) if values else (0.0, 0.0)
        contexts = []
        for row in sorted(subset, key=lambda item: str(item.get("cell_type") or "")):
            value = float(row.get("median_source_scale_intensity") or 0)
            contexts.append({
                "label": row.get("cell_type") or "unannotated",
                "positive_fraction": float(row.get("positive_cell_fraction") or 0),
                "intensity": value,
                "relative_intensity": _within_dataset_scale(value, low, high),
            })
        output.append({
            "dataset": dataset,
            "assay": subset[0].get("assay"),
            "unit": "source_scale_intensity",
            "contexts": contexts,
        })
    return output


def _census_dataset_views(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("dataset_id") or "unknown")].append(row)
    output = []
    for dataset, subset in sorted(grouped.items()):
        values = [float(row.get("mean_raw_count") or 0) for row in subset]
        low, high = (min(values), max(values)) if values else (0.0, 0.0)
        contexts = []
        for row in sorted(subset, key=lambda item: str(item.get("cell_type") or "")):
            value = float(row.get("mean_raw_count") or 0)
            contexts.append({
                "label": row.get("cell_type") or row.get("reference_context") or "all spots",
                "positive_fraction": float(row.get("positive_spot_fraction") or 0),
                "intensity": value,
                "relative_intensity": _within_dataset_scale(value, low, high),
            })
        output.append({
            "dataset": dataset,
            "assay": subset[0].get("assay"),
            "unit": subset[0].get("unit") or "raw count",
            "contexts": contexts,
        })
    return output


def _within_dataset_scale(value: float, low: float, high: float) -> float:
    if high <= low:
        return 1.0 if high > 0 else 0.0
    return (value - low) / (high - low)


def _body_svg(regions: dict[str, dict[str, Any]]) -> str:
    shapes = []
    labels = []
    for region, spec in BODY_REGIONS.items():
        data = regions.get(region)
        fill = str(data.get("fill")) if data else "#f3f4f6"
        stroke = "#111827" if data and data.get("k_outline") else "#9ca3af"
        width = "4" if data and data.get("k_outline") else "1.5"
        shapes.append(_region_shape(spec, fill, stroke, width, region))
        if data:
            labels.append(
                f'<text x="{spec["x"] + 42}" y="{spec["y"] + 4}" '
                f'class="organ-label">{_e(region.title())}</text>'
            )
    return (
        '<svg class="body-map" viewBox="0 0 300 455" role="img" '
        'aria-label="Schematic body evidence map">'
        '<g class="silhouette" fill="#fafafa" stroke="#cbd5e1" stroke-width="2">'
        '<circle cx="150" cy="52" r="39"/><rect x="114" y="89" width="72" height="205" rx="34"/>'
        '<rect x="76" y="102" width="38" height="205" rx="19"/>'
        '<rect x="186" y="102" width="38" height="205" rx="19"/>'
        '<rect x="116" y="280" width="31" height="160" rx="15"/>'
        '<rect x="153" y="280" width="31" height="160" rx="15"/></g>'
        + "".join(shapes)
        + "".join(labels)
        + "</svg>"
    )


def _region_shape(
    spec: dict[str, Any], fill: str, stroke: str, width: str, region: str
) -> str:
    x, y, kind = spec["x"], spec["y"], spec["shape"]
    attrs = (
        f'fill="{fill}" stroke="{stroke}" stroke-width="{width}" '
        f'data-region="{_e(region)}"'
    )
    title = f"<title>{_e(region.title())}</title>"
    if kind == "ellipse":
        return (
            f'<g {attrs}>{title}<ellipse cx="{x}" cy="{y}" '
            f'rx="{spec["rx"]}" ry="{spec["ry"]}"/></g>'
        )
    if kind == "lungs":
        return (
            f'<g {attrs}>{title}<ellipse cx="{x - 21}" cy="{y}" rx="20" ry="35"/>'
            f'<ellipse cx="{x + 21}" cy="{y}" rx="20" ry="35"/></g>'
        )
    if kind == "kidneys":
        return (
            f'<g {attrs}>{title}<ellipse cx="{x - 23}" cy="{y}" rx="11" ry="18"/>'
            f'<ellipse cx="{x + 23}" cy="{y}" rx="11" ry="18"/></g>'
        )
    if kind == "heart":
        return (
            f'<g {attrs}>{title}<path d="M{x},{y + 20} C{x - 32},{y - 2} '
            f'{x - 20},{y - 25} {x},{y - 9} C{x + 20},{y - 25} '
            f'{x + 32},{y - 2} {x},{y + 20}Z"/></g>'
        )
    if kind == "colon":
        return (
            f'<g {attrs}>{title}<rect x="{x - 32}" y="{y - 20}" width="64" '
            f'height="40" rx="15" fill="{fill}" fill-opacity=".72"/>'
            '<path d="M128,294 C140,306 160,306 172,294 M128,320 '
            'C140,308 160,308 172,320" fill="none"/></g>'
        )
    if kind == "breast":
        return (
            f'<g {attrs}>{title}<circle cx="{x - 28}" cy="{y}" r="10"/>'
            f'<circle cx="{x + 28}" cy="{y}" r="10"/></g>'
        )
    return (
        f'<g {attrs}>{title}<rect x="{x - 18}" y="{y - 18}" '
        'width="36" height="36" rx="8"/></g>'
    )


def _legend_html() -> str:
    items = "".join(
        f'<span class="legend-item"><span class="swatch" style="background:{data["color"]}">'
        f'</span>{_e(data["label"])}</span>'
        for data in CHANNELS.values()
    )
    return f'<div class="overlay-legend">{items}</div>'


def _organ_cards(regions: dict[str, dict[str, Any]]) -> str:
    if not regions:
        return '<p class="empty">No mappable organ-level evidence.</p>'
    cards = []
    for region, row in sorted(regions.items()):
        chips = "".join(
            f'<span class="channel-chip state-{_e(state)}">'
            f'<span class="channel-chip-dot" style="background:{CHANNELS[key]["color"]}"></span>'
            f'{_e(CHANNELS[key]["label"])}</span>'
            for key, state in row.get("channels", {}).items()
        )
        cards.append(
            f'<div class="organ-card"><span class="organ-dot" '
            f'style="background:{_e(row.get("fill"))};'
            f'outline:{"3px solid #111827" if row.get("k_outline") else "none"}"></span>'
            f'<div><strong>{_e(region.title())}</strong><div>{chips}</div>'
            f'<small>{int(row.get("evidence_count") or 0)} evidence rows</small></div></div>'
        )
    return '<div class="organ-cards">' + "".join(cards) + "</div>"


def _cell_type_html(rows: Any) -> str:
    if not isinstance(rows, list) or not rows:
        return '<p class="empty">No cell-context overlay available.</p>'
    bubbles = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        style = (
            f'background:{_e(row.get("fill"))};'
            + ("outline:3px solid #111827;" if row.get("k_outline") else "")
        )
        bubbles.append(
            f'<div class="cell-bubble" style="{style}" title="{_e(row.get("channels"))}">'
            f'{_e(row.get("cell_type"))}</div>'
        )
    return '<div class="cell-bubbles">' + "".join(bubbles) + "</div>"


def _subcellular_html(locations: Any) -> str:
    values = [str(value) for value in locations] if isinstance(locations, list) else []
    text = " ".join(values).casefold()
    states = {
        "membrane": any(word in text for word in ("membrane", "cell junction", "plasma")),
        "cytoplasm": any(word in text for word in ("cytoplas", "cytosol", "vesicle")),
        "nucleus": any(word in text for word in ("nucle", "chromatin")),
        "secreted / extracellular": any(word in text for word in ("secret", "extracellular")),
    }
    boxes = "".join(
        f'<div class="subcell-box {"active" if active else ""}">{_e(label)}</div>'
        for label, active in states.items()
    )
    raw = ", ".join(values) if values else "No HPA subcellular annotation in this build."
    return f'<div class="subcell-grid">{boxes}</div><p class="note">{_e(raw)}</p>'


def _dataset_views_html(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    protein = value.get("hubmap_protein")
    rna = value.get("spatial_rna")
    sections = []
    if isinstance(protein, list) and protein:
        sections.append(_dataset_family("HuBMAP protein", protein))
    if isinstance(rna, list) and rna:
        sections.append(_dataset_family("Spatial RNA", rna))
    if not sections:
        return ""
    return (
        '<div class="dataset-section"><h4>Dataset-resolved views</h4>'
        '<p class="note">Bars are normalized only within each dataset. '
        'Numbers retain the source unit.</p>'
        + "".join(sections)
        + "</div>"
    )


def _dataset_family(title: str, datasets: list[Any]) -> str:
    cards = []
    for dataset in datasets[:8]:
        if not isinstance(dataset, dict):
            continue
        rows = []
        for context in dataset.get("contexts", [])[:16]:
            if not isinstance(context, dict):
                continue
            width = round(100 * float(context.get("relative_intensity") or 0), 1)
            positive = round(100 * float(context.get("positive_fraction") or 0), 1)
            rows.append(
                f'<div class="dataset-row"><span>{_e(context.get("label"))}</span>'
                f'<div class="intensity-track"><span style="width:{width}%"></span></div>'
                f'<span>{_e(_number(context.get("intensity")))}</span>'
                f'<span>{positive}% +</span></div>'
            )
        cards.append(
            f'<details class="dataset-card"><summary><strong>{_e(dataset.get("dataset"))}</strong>'
            f' · {_e(dataset.get("assay") or title)}</summary>'
            f'<div class="dataset-rows">{"".join(rows)}</div>'
            f'<small>Intensity unit: {_e(dataset.get("unit"))}</small></details>'
        )
    return f'<div class="dataset-family"><h5>{_e(title)}</h5>{"".join(cards)}</div>'


def _disease_html(rows: Any) -> str:
    if not isinstance(rows, list) or not rows:
        return ""
    cards = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        fraction = row.get("tumor_higher_fraction")
        frac_text = (
            f"{100 * float(fraction):.0f}% pairs tumor-higher"
            if isinstance(fraction, (int, float))
            else "pair direction unavailable"
        )
        cards.append(
            f'<div class="disease-badge"><strong>PDC tumor vs adjacent</strong><br>'
            f'{_e(row.get("study_id"))} · {frac_text}<br>'
            f'Δ median {_e(_number(row.get("median_tumor_minus_adjacent")))}</div>'
        )
    return "".join(cards)


def _number(value: Any) -> str:
    return f"{float(value):.3g}" if isinstance(value, (int, float)) else "—"


def _read_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []
    return [
        {str(key): value for key, value in row.items()}
        for row in raw
        if isinstance(row, dict)
    ]


def _read_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items()}


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)
