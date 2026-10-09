"""Geometry and rendering helpers for the radial tissue atlas."""

from __future__ import annotations

import html
import math
from typing import Any

TISSUE_ORDER = [
    "blood",
    "bone_marrow",
    "brain",
    "thyroid",
    "trachea",
    "lung",
    "heart",
    "vasculature",
    "breast",
    "liver",
    "stomach",
    "pancreas",
    "kidney",
    "bladder",
    "colon",
    "small_intestine",
    "skin",
    "fat",
    "muscle",
    "lymph_node",
    "spleen",
    "thymus",
    "salivary_gland",
    "tongue",
    "ovary",
    "uterus",
    "prostate",
    "testis",
]

TISSUE_DISPLAY_NAMES = {
    "blood": "Blood",
    "bone_marrow": "Bone marrow",
    "brain": "Brain",
    "thyroid": "Thyroid",
    "trachea": "Trachea",
    "lung": "Lung",
    "heart": "Heart",
    "vasculature": "Vasculature",
    "breast": "Breast",
    "liver": "Liver",
    "stomach": "Stomach",
    "pancreas": "Pancreas",
    "kidney": "Kidney",
    "bladder": "Bladder",
    "colon": "Large intestine",
    "small_intestine": "Small intestine",
    "skin": "Skin",
    "fat": "Adipose",
    "muscle": "Muscle",
    "lymph_node": "Lymph node",
    "spleen": "Spleen",
    "thymus": "Thymus",
    "salivary_gland": "Salivary gland",
    "tongue": "Tongue",
    "ovary": "Ovary",
    "uterus": "Uterus",
    "prostate": "Prostate",
    "testis": "Testis",
}

_REQUIRED_CHANNELS = ("C", "M", "Y", "K")

TRACKS = [
    ("hpa_protein", "Human Protein Atlas protein"),
    ("proteomicsdb_protein", "ProteomicsDB protein"),
    ("spatial_rna", "Spatial RNA"),
    ("hubmap_spatial_protein", "HuBMAP spatial protein"),
]


def render_radial_tracks(
    tissues: list[dict[str, Any]],
    colors: dict[str, str],
    *,
    cx: float = 500,
    cy: float = 500,
) -> str:
    """Render radial tissue tracks around a center body."""
    _validate_colors(colors)
    by_name = {
        str(row.get("tissue")): row
        for row in tissues
        if isinstance(row, dict) and row.get("tissue")
    }
    segment = 360.0 / len(TISSUE_ORDER)
    gap = min(1.8, segment * 0.18)
    radii = {
        "hpa_protein": (330.0, 355.0),
        "proteomicsdb_protein": (360.0, 385.0),
        "spatial_rna": (390.0, 415.0),
        "hubmap_spatial_protein": (420.0, 445.0),
    }
    source_colors = {
        "hpa_protein": colors["C"],
        "proteomicsdb_protein": colors["M"],
        "spatial_rna": colors["Y"],
        "hubmap_spatial_protein": colors["K"],
    }

    parts: list[str] = [
        '<g class="radial-tissue-tracks" role="group" '
        'aria-label="Tissue evidence tracks">'
    ]
    for index, tissue in enumerate(TISSUE_ORDER):
        midpoint = -90.0 + index * segment
        start = midpoint - segment / 2 + gap / 2
        end = midpoint + segment / 2 - gap / 2
        row = by_name.get(tissue, {})
        tracks = row.get("tracks", {})
        if not isinstance(tracks, dict):
            tracks = {}

        for track_key, track_label in TRACKS:
            track = tracks.get(track_key, {})
            if not isinstance(track, dict):
                track = {}
            state = str(track.get("state") or "unknown")
            strength = _strength(track.get("strength"))
            inner, outer = radii[track_key]
            fill, opacity, stroke = _track_style(
                state,
                strength,
                source_colors[track_key],
            )
            title = _track_title(
                TISSUE_DISPLAY_NAMES[tissue],
                track_label,
                state,
                strength,
            )
            parts.append(
                f'<path class="radial-track state-{_e(state)}" '
                f'd="{annular_sector_path(cx, cy, inner, outer, start, end)}" '
                f'fill="{fill}" fill-opacity="{opacity:.3f}" '
                f'stroke="{stroke}" stroke-width=".8"><title>{_e(title)}</title></path>'
            )

        parts.append(_label(tissue, midpoint, cx, cy, radius=472.0))
    parts.append("</g>")
    return "".join(parts)


def _validate_colors(colors: dict[str, str]) -> None:
    missing = [channel for channel in _REQUIRED_CHANNELS if channel not in colors]
    if missing:
        raise ValueError(f"colors is missing channel(s): {', '.join(missing)}")


def annular_sector_path(
    cx: float,
    cy: float,
    inner_radius: float,
    outer_radius: float,
    start_degrees: float,
    end_degrees: float,
) -> str:
    """Return an SVG path for one annular sector."""
    outer_start = _polar(cx, cy, outer_radius, start_degrees)
    outer_end = _polar(cx, cy, outer_radius, end_degrees)
    inner_end = _polar(cx, cy, inner_radius, end_degrees)
    inner_start = _polar(cx, cy, inner_radius, start_degrees)
    large_arc = 1 if (end_degrees - start_degrees) > 180 else 0
    return (
        f"M {outer_start[0]:.3f} {outer_start[1]:.3f} "
        f"A {outer_radius:.3f} {outer_radius:.3f} 0 {large_arc} 1 "
        f"{outer_end[0]:.3f} {outer_end[1]:.3f} "
        f"L {inner_end[0]:.3f} {inner_end[1]:.3f} "
        f"A {inner_radius:.3f} {inner_radius:.3f} 0 {large_arc} 0 "
        f"{inner_start[0]:.3f} {inner_start[1]:.3f} Z"
    )


def _label(
    tissue: str,
    angle_degrees: float,
    cx: float,
    cy: float,
    *,
    radius: float,
) -> str:
    x, y = _polar(cx, cy, radius, angle_degrees)
    rotation = angle_degrees + 90.0
    anchor = "start"
    if 90.0 < (angle_degrees % 360.0) < 270.0:
        rotation += 180.0
        anchor = "end"
    return (
        f'<text class="radial-label" x="{x:.2f}" y="{y:.2f}" '
        f'text-anchor="{anchor}" dominant-baseline="middle" '
        f'transform="rotate({rotation:.2f} {x:.2f} {y:.2f})">'
        f'{_e(TISSUE_DISPLAY_NAMES[tissue])}</text>'
    )


def _track_style(
    state: str,
    strength: float | None,
    color: str,
) -> tuple[str, float, str]:
    if state == "positive":
        value = 1.0 if strength is None else strength
        return color, 0.22 + 0.73 * value, color
    if state == "negative":
        return color, 0.08, color
    return "#f8fafc", 1.0, "#e2e8f0"


def _track_title(
    tissue: str,
    source: str,
    state: str,
    strength: float | None,
) -> str:
    if strength is None:
        return f"{tissue} · {source} · {state}"
    return f"{tissue} · {source} · {state} · strength {strength:.0%}"


def _strength(value: Any) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    return max(0.0, min(1.0, float(value)))


def _polar(
    cx: float,
    cy: float,
    radius: float,
    angle_degrees: float,
) -> tuple[float, float]:
    angle = math.radians(angle_degrees)
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)
