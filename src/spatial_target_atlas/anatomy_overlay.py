"""Expression overlays for the DBCLS central anatomy illustration."""

from __future__ import annotations

import html
from typing import Any

from .anatomy_regions import REGIONS, SourcePath

CHANNEL_PRIORITY = ("C", "Y", "M", "K")


def select_anatomy_source(regions: dict[str, dict[str, Any]]) -> str | None:
    """Choose one informative source for the center anatomy.

    The radial ring still shows every source. The center uses one source at a
    time to avoid muddy color mixing over the grayscale anatomy.
    """
    scores: dict[str, tuple[int, float]] = {}
    for channel in CHANNEL_PRIORITY:
        positive = 0
        summed_strength = 0.0
        for region in REGIONS:
            payload = regions.get(region)
            if not isinstance(payload, dict):
                continue
            states = payload.get("channels", {})
            strengths = payload.get("strengths", {})
            if not isinstance(states, dict) or states.get(channel) != "positive":
                continue
            positive += 1
            strength = _strength(
                strengths.get(channel) if isinstance(strengths, dict) else None
            )
            summed_strength += strength if strength is not None else 1.0
        scores[channel] = (positive, summed_strength)

    if not any(score[0] for score in scores.values()):
        return None
    return max(
        CHANNEL_PRIORITY,
        key=lambda channel: (
            scores[channel][0],
            scores[channel][1],
            -CHANNEL_PRIORITY.index(channel),
        ),
    )


def render_dbcls_expression_overlay(
    regions: dict[str, dict[str, Any]],
    colors: dict[str, str],
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    active_source: str | None = None,
) -> str:
    """Render one source of tissue evidence over the grayscale DBCLS anatomy."""
    source = active_source or select_anatomy_source(regions)
    if source is None:
        return (
            '<g class="dbcls-expression-overlay" role="group" '
            'aria-label="No mapped expression on central anatomy"></g>'
        )

    parts = [
        f'<g class="dbcls-expression-overlay active-source-{_e(source)}" role="group" '
        'aria-label="Expression mapped onto central anatomy">'
    ]

    for region, shapes in REGIONS.items():
        payload = regions.get(region)
        if not isinstance(payload, dict):
            continue
        states = payload.get("channels", {})
        strengths = payload.get("strengths", {})
        if not isinstance(states, dict) or states.get(source) != "positive":
            continue
        strength_map = strengths if isinstance(strengths, dict) else {}
        value = _strength(strength_map.get(source))
        strength = value if value is not None else 1.0

        if source == "K":
            fill = "none"
            fill_opacity = 0.0
            stroke = colors["K"]
            stroke_width = 0.9 + 1.8 * strength
            stroke_opacity = 0.22 + 0.45 * strength
            blend = False
        else:
            fill = colors[source]
            fill_opacity = 0.05 + 0.23 * strength
            stroke = colors[source]
            stroke_width = 0.45 + 0.55 * strength
            stroke_opacity = 0.16 + 0.24 * strength
            blend = True

        for shape in shapes:
            parts.append(
                _shape_svg(
                    shape,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    fill=fill,
                    fill_opacity=fill_opacity,
                    stroke=stroke,
                    stroke_width=stroke_width,
                    stroke_opacity=stroke_opacity,
                    blend=blend,
                    region=region,
                    channel=source,
                )
            )

    parts.append("</g>")
    return "".join(parts)


def _shape_svg(
    shape: SourcePath,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    fill: str,
    fill_opacity: float,
    stroke: str,
    stroke_width: float,
    stroke_opacity: float,
    blend: bool,
    region: str,
    channel: str,
) -> str:
    style = ' style="mix-blend-mode:multiply"' if blend else ""
    metadata = (
        f' class="anatomy-expression anatomy-expression-{_e(region)} '
        f'anatomy-expression-source-{_e(channel)}"'
    )
    scale_x = width / 600.0
    scale_y = height / 1000.0
    return (
        f'<path{metadata} d="{shape.d}" '
        f'transform="translate({x:.2f} {y:.2f}) scale({scale_x:.6f} {scale_y:.6f})" '
        f'fill="{fill}" fill-opacity="{fill_opacity:.3f}" '
        f'stroke="{stroke}" stroke-width="{stroke_width / max(scale_x, scale_y):.3f}" '
        f'stroke-opacity="{stroke_opacity:.3f}"{style}/>'
    )


def _strength(value: Any) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    return max(0.0, min(1.0, float(value)))


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)
