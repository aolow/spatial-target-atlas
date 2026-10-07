"""Expression overlays for the DBCLS central anatomy illustration."""

from __future__ import annotations

import html
from typing import Any

from .anatomy_regions import Ellipse, Polygon, REGIONS


def render_dbcls_expression_overlay(
    regions: dict[str, dict[str, Any]],
    colors: dict[str, str],
    *,
    x: float,
    y: float,
    width: float,
    height: float,
) -> str:
    """Render source-aware tissue evidence over the DBCLS anatomy image.

    C/M/Y use transparent source-colored fills with multiply blending, matching
    the atlas' existing cross-source semantics. K remains a dark outline.
    Only tissues with explicit masks in REGIONS are drawn.
    """
    parts = [
        '<g class="dbcls-expression-overlay" role="group" '
        'aria-label="Expression mapped onto central anatomy">'
    ]

    for region, shapes in REGIONS.items():
        payload = regions.get(region)
        if not isinstance(payload, dict):
            continue
        states = payload.get("channels", {})
        strengths = payload.get("strengths", {})
        if not isinstance(states, dict):
            continue
        strength_map = strengths if isinstance(strengths, dict) else {}

        for channel in ("C", "M", "Y"):
            if states.get(channel) != "positive":
                continue
            value = _strength(strength_map.get(channel))
            opacity = 0.12 + 0.48 * (value if value is not None else 1.0)
            for shape in shapes:
                parts.append(
                    _shape_svg(
                        shape,
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        fill=colors[channel],
                        fill_opacity=opacity,
                        stroke="none",
                        stroke_width=0.0,
                        stroke_opacity=0.0,
                        blend=True,
                        region=region,
                        channel=channel,
                    )
                )

        if states.get("K") == "positive":
            value = _strength(strength_map.get("K"))
            strength = value if value is not None else 1.0
            for shape in shapes:
                parts.append(
                    _shape_svg(
                        shape,
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        fill="none",
                        fill_opacity=0.0,
                        stroke=colors["K"],
                        stroke_width=1.4 + 2.8 * strength,
                        stroke_opacity=0.30 + 0.60 * strength,
                        blend=False,
                        region=region,
                        channel="K",
                    )
                )

    parts.append("</g>")
    return "".join(parts)


def _shape_svg(
    shape: Ellipse | Polygon,
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

    if isinstance(shape, Ellipse):
        return (
            f'<ellipse{metadata} cx="{x + shape.cx * width:.2f}" '
            f'cy="{y + shape.cy * height:.2f}" '
            f'rx="{shape.rx * width:.2f}" ry="{shape.ry * height:.2f}" '
            f'fill="{fill}" fill-opacity="{fill_opacity:.3f}" '
            f'stroke="{stroke}" stroke-width="{stroke_width:.2f}" '
            f'stroke-opacity="{stroke_opacity:.3f}"{style}/>'
        )

    points = " ".join(
        f"{x + px * width:.2f},{y + py * height:.2f}"
        for px, py in shape.points
    )
    return (
        f'<polygon{metadata} points="{points}" '
        f'fill="{fill}" fill-opacity="{fill_opacity:.3f}" '
        f'stroke="{stroke}" stroke-width="{stroke_width:.2f}" '
        f'stroke-opacity="{stroke_opacity:.3f}"{style}/>'
    )


def _strength(value: Any) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    return max(0.0, min(1.0, float(value)))


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)
