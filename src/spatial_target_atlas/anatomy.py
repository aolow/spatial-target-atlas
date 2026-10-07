"""Repo-owned SVG anatomy primitives for spatial evidence rendering.

The drawings are schematic masks designed for data overlays, not diagnostic anatomy.
They are original project artwork so their fill/opacity can be controlled directly.
"""

from __future__ import annotations

import base64
import html
from importlib import import_module
from importlib.resources import files
from typing import Any

from .anatomy_overlay import render_dbcls_expression_overlay
from .radial_layout import render_radial_tracks

BODY_VIEWBOX = "0 0 320 560"

BODY_SILHOUETTE = """
<path d="M160 18
 C134 18 115 39 115 66
 C115 84 124 100 139 110
 L136 126
 C111 132 91 145 78 166
 C66 187 59 220 55 258
 L45 353
 C43 372 54 379 65 366
 L85 288
 L90 246
 L100 329
 L111 399
 L110 534
 C110 550 126 553 133 538
 L154 408
 L160 363
 L166 408
 L187 538
 C194 553 210 550 210 534
 L209 399
 L220 329
 L230 246
 L235 288
 L255 366
 C266 379 277 372 275 353
 L265 258
 C261 220 254 187 242 166
 C229 145 209 132 184 126
 L181 110
 C196 100 205 84 205 66
 C205 39 186 18 160 18 Z"/>
"""

ORGAN_PATHS: dict[str, str] = {
    "brain": """
      <path d="M132 57 C132 41 143 30 158 30
       C173 25 190 34 192 48
       C204 55 202 72 192 78
       C190 91 174 97 163 91
       C151 99 134 91 134 79
       C122 73 122 62 132 57 Z"/>
      <path d="M160 34 L160 91 M144 39 C153 48 149 57 141 63
       M178 39 C169 49 174 59 184 64" fill="none"/>
    """,
    "thyroid": """
      <path d="M148 121 C140 116 136 123 139 131
       C142 139 150 138 156 132 L160 128 L164 132
       C170 138 178 139 181 131 C184 123 180 116 172 121
       L164 124 L160 131 L156 124 Z"/>
    """,
    "lung": """
      <path d="M151 146 C135 148 120 160 116 177
       L111 219 C111 238 125 246 143 237
       C151 228 153 207 153 184 L153 153 Z"/>
      <path d="M169 146 C185 148 200 160 204 177
       L209 219 C209 238 195 246 177 237
       C169 228 167 207 167 184 L167 153 Z"/>
      <path d="M160 143 L160 190 M160 166 L142 181 M160 166 L178 181"
       fill="none"/>
    """,
    "heart": """
      <path d="M160 199
       C147 184 127 191 129 208
       C131 224 145 237 160 251
       C175 237 189 224 191 208
       C193 191 173 184 160 199 Z"/>
      <path d="M159 192 C155 179 158 168 166 159
       M169 194 C173 179 183 172 192 171" fill="none"/>
    """,
    "liver": """
      <path d="M150 240
       C164 225 199 224 222 238
       C229 246 222 262 207 268
       C189 274 169 270 145 261
       C137 255 140 247 150 240 Z"/>
      <path d="M174 237 C171 247 174 258 184 267" fill="none"/>
    """,
    "stomach": """
      <path d="M137 245
       C120 247 111 260 115 276
       C120 291 136 295 146 286
       C153 280 148 269 156 258
       C162 250 154 242 147 245 Z"/>
    """,
    "pancreas": """
      <path d="M132 283
       C145 276 169 273 193 279
       C204 283 205 291 194 295
       C170 301 145 299 129 292
       C123 289 125 285 132 283 Z"/>
    """,
    "kidney": """
      <path d="M127 287 C113 284 105 297 108 312
       C111 327 124 334 134 325
       C141 318 137 307 143 299
       C139 292 134 289 127 287 Z"/>
      <path d="M193 287 C207 284 215 297 212 312
       C209 327 196 334 186 325
       C179 318 183 307 177 299
       C181 292 186 289 193 287 Z"/>
    """,
    "spleen": """
      <path d="M105 266 C93 268 88 280 92 294
       C96 307 107 311 114 301
       C120 291 117 275 110 269 Z"/>
    """,
    "colon": """
      <path d="M124 318
       C109 323 105 340 110 352
       L110 383 C111 399 123 408 137 401
       L183 401 C197 408 209 399 210 383
       L210 352 C215 340 211 323 196 318
       C187 315 179 321 178 331
       L178 370 L142 370 L142 331
       C141 321 133 315 124 318 Z"/>
      <path d="M142 343 C151 336 169 336 178 343
       M142 384 C153 390 167 390 178 384" fill="none"/>
    """,
    "bladder": """
      <path d="M147 421 C147 408 154 401 160 401
       C166 401 173 408 173 421
       C173 437 168 447 160 447
       C152 447 147 437 147 421 Z"/>
    """,
    "breast": """
      <path d="M116 181 C123 170 138 170 146 180
       C139 192 123 195 116 181 Z"/>
      <path d="M204 181 C197 170 182 170 174 180
       C181 192 197 195 204 181 Z"/>
    """,
    "skin": """
      <path d="M160 19
       C124 19 94 47 94 85
       C94 112 105 132 124 145
       C93 154 73 181 68 220
       L51 356
       M269 356 L252 220
       C247 181 227 154 196 145
       C215 132 226 112 226 85
       C226 47 196 19 160 19" fill="none"/>
    """,
}

ANATOMY_SCAFFOLD = """
<g class="anatomy-airway" fill="none" stroke="#94a3b8" stroke-width="3"
 stroke-linecap="round" stroke-linejoin="round">
  <path d="M160 112 L160 154 M160 151 L141 170 M160 151 L179 170"/>
  <path d="M141 170 L128 190 M141 170 L148 199 M179 170 L192 190 M179 170 L172 199"
   stroke-width="1.6"/>
</g>
<g class="anatomy-vessels" fill="none" stroke-linecap="round" stroke-linejoin="round">
  <path d="M169 185 C181 207 178 235 174 263 L172 340 C172 373 181 408 190 444"
   stroke="#ef6b6b" stroke-width="4"/>
  <path d="M151 184 C142 207 145 235 148 263 L149 340 C148 373 139 408 130 444"
   stroke="#5b8def" stroke-width="4"/>
  <path d="M170 225 C192 219 208 206 226 188 M149 225 C126 219 111 206 94 188"
   stroke="#ef6b6b" stroke-width="2"/>
  <path d="M172 290 C190 286 202 291 212 301 M149 290 C130 286 118 291 108 301"
   stroke="#ef6b6b" stroke-width="2"/>
  <path d="M148 294 C131 291 120 297 111 307 M173 294 C190 291 201 297 210 307"
   stroke="#5b8def" stroke-width="2"/>
</g>
<g class="anatomy-lymph" fill="none" stroke="#7abf77" stroke-width="1.5" opacity=".72">
  <path d="M143 129 C131 148 126 177 130 205 C134 235 137 263 142 292"/>
  <path d="M177 129 C189 148 194 177 190 205 C186 235 183 263 178 292"/>
  <circle cx="136" cy="145" r="3" fill="#7abf77"/><circle cx="127" cy="181" r="3" fill="#7abf77"/>
  <circle cx="184" cy="145" r="3" fill="#7abf77"/><circle cx="193" cy="181" r="3" fill="#7abf77"/>
  <circle cx="142" cy="276" r="3" fill="#7abf77"/><circle cx="178" cy="276" r="3" fill="#7abf77"/>
</g>
<path d="M110 244 Q160 258 210 244" fill="none" stroke="#cbd5e1" stroke-width="2"/>
<g class="anatomy-small-intestine" fill="none" stroke="#9ca3af" stroke-width="1.5">
  <path d="M132 336 C149 326 170 326 188 337 C169 347 149 347 132 358
   C151 368 171 368 188 379 C170 389 149 389 132 400"/>
</g>
"""

ORGAN_LABEL_POINTS: dict[str, tuple[int, int]] = {
    "brain": (204, 59),
    "thyroid": (204, 125),
    "lung": (225, 181),
    "heart": (225, 221),
    "liver": (235, 251),
    "stomach": (73, 270),
    "pancreas": (224, 289),
    "kidney": (225, 313),
    "spleen": (55, 292),
    "colon": (225, 360),
    "bladder": (215, 433),
    "breast": (225, 191),
    "skin": (254, 145),
}

SOURCE_LABELS = {
    "C": "Human Protein Atlas protein",
    "M": "ProteomicsDB protein",
    "Y": "Spatial RNA",
    "K": "HuBMAP spatial protein",
}


DEFAULT_ANATOMY_ASSET_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/0/00/"
    "202403_human_anatomy_organs.svg"
)
DEFAULT_ANATOMY_SOURCE_URL = (
    "https://commons.wikimedia.org/wiki/File:202403_human_anatomy_organs.svg"
)
DEFAULT_ANATOMY_LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
DEFAULT_ANATOMY_ATTRIBUTION = (
    "Human anatomy organs by DataBase Center for Life Science (DBCLS), "
    "CC BY 4.0. Used as the central orientation illustration; "
    "Spatial Target Atlas adds surrounding evidence tracks."
)


def fetch_default_anatomy_data_uri(timeout_seconds: float = 15.0) -> str:
    """Load the bundled DBCLS anatomy and inline it into self-contained HTML.

    The atlas vendors the DBCLS SVG so normal rendering never depends on
    Wikimedia availability. A network fetch is retained only as a compatibility
    fallback for unusual package installations where the bundled asset is absent.
    """
    try:
        content = (
            files("spatial_target_atlas")
            .joinpath("assets", "dbcls_human_anatomy_organs.svg")
            .read_bytes()
        )
        content_type = "image/svg+xml"
    except (FileNotFoundError, OSError):
        httpx = import_module("httpx")
        response = httpx.get(
            DEFAULT_ANATOMY_ASSET_URL,
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "spatial-target-atlas/0.9.2"},
        )
        response.raise_for_status()
        content = response.content
        content_type = str(response.headers.get("content-type") or "image/svg+xml").split(";")[0]

    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def render_body(
    regions: dict[str, dict[str, Any]],
    colors: dict[str, str],
    *,
    source: str | None = None,
    mini: bool = False,
) -> str:
    """Render the composite or a single-source small multiple."""
    classes = "anatomy-map anatomy-mini" if mini else "anatomy-map"
    content = [
        f'<svg class="{classes}" viewBox="{BODY_VIEWBOX}" role="img" '
        'aria-label="Schematic human anatomy evidence map">',
        '<g class="body-silhouette" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2">',
        BODY_SILHOUETTE,
        "</g>",
        ANATOMY_SCAFFOLD,
    ]
    for region, paths in ORGAN_PATHS.items():
        data = regions.get(region)
        if data is None:
            content.append(
                f'<g class="organ organ-{_e(region)}" fill="#f1f5f9" '
                'stroke="#cbd5e1" stroke-width="1.2" opacity=".9">'
                f"{paths}</g>"
            )
            continue
        strengths = data.get("strengths", {})
        states = data.get("channels", {})
        if source is not None:
            state = states.get(source)
            strength = _number(strengths.get(source))
            opacity = _source_opacity(state, strength)
            fill = colors[source] if state == "positive" else "#f1f5f9"
            stroke = colors[source] if state in {"positive", "negative"} else "#cbd5e1"
            content.append(_organ_layer(region, paths, fill, opacity, stroke, 1.5, source))
        else:
            for channel in ("C", "M", "Y"):
                state = states.get(channel)
                strength = _number(strengths.get(channel))
                if state != "positive":
                    continue
                content.append(
                    _organ_layer(
                        region,
                        paths,
                        colors[channel],
                        _source_opacity(state, strength),
                        "none",
                        0,
                        channel,
                        blend=True,
                    )
                )
            k_state = states.get("K")
            k_strength = _number(strengths.get("K"))
            outline_opacity = _source_opacity(k_state, k_strength)
            if k_state == "positive":
                width = 1.5 + 4.5 * (k_strength if k_strength is not None else 1.0)
                content.append(
                    _organ_layer(
                        region,
                        paths,
                        "none",
                        1.0,
                        colors["K"],
                        width,
                        "K",
                        stroke_opacity=outline_opacity,
                    )
                )
            if not any(
                states.get(channel) == "positive" for channel in ("C", "M", "Y", "K")
            ):
                content.append(
                    _organ_layer(region, paths, "#f1f5f9", 1.0, "#94a3b8", 1.2, "none")
                )

        if not mini:
            x, y = ORGAN_LABEL_POINTS[region]
            content.append(
                f'<text class="anatomy-label" x="{x}" y="{y}">{_e(region.title())}</text>'
            )
    content.append("</svg>")
    return "".join(content)


def render_small_multiples(
    regions: dict[str, dict[str, Any]], colors: dict[str, str]
) -> str:
    cards = []
    for channel in ("C", "M", "Y", "K"):
        cards.append(
            '<div class="source-mini">'
            f'<div class="source-mini-head"><span class="source-dot" '
            f'style="background:{colors[channel]}"></span>'
            f'<strong>{_e(SOURCE_LABELS[channel])}</strong></div>'
            f'{render_body(regions, colors, source=channel, mini=True)}'
            "</div>"
        )
    return '<div class="source-multiples">' + "".join(cards) + "</div>"


def render_cell_contexts(rows: Any, colors: dict[str, str]) -> str:
    """Render cell contexts as small tissue microenvironment scenes."""
    if not isinstance(rows, list) or not rows:
        return '<p class="empty">No cell-context evidence available.</p>'
    cards = []
    for row in rows[:18]:
        if not isinstance(row, dict):
            continue
        name = str(row.get("cell_type") or "unannotated")
        category = cell_category(name)
        states = row.get("channels", {})
        strengths = row.get("strengths", {})
        scene = _cell_scene(category, states, strengths, colors)
        cards.append(
            '<div class="cell-context-card cell-scene-card">'
            f'{scene}<div class="cell-scene-copy"><strong>{_e(name)}</strong>'
            f'<small>{_e(_cell_category_label(category))}</small>'
            f'{_channel_badges(states, strengths, colors)}</div></div>'
        )
    return '<div class="cell-context-grid cell-scene-grid">' + "".join(cards) + "</div>"


def _cell_scene(
    category: str,
    states: Any,
    strengths: Any,
    colors: dict[str, str],
) -> str:
    layers = _scene_signal_layers(states, strengths, colors)
    if category == "epithelial":
        biology = _epithelial_scene()
        aria = "Epithelial tissue scene"
    elif category == "endothelial":
        biology = _endothelial_scene()
        aria = "Endothelial vessel scene"
    elif category == "fibroblast":
        biology = _fibroblast_scene()
        aria = "Fibroblast extracellular matrix scene"
    elif category == "immune":
        biology = _immune_scene()
        aria = "Immune microenvironment scene"
    else:
        biology = _generic_tissue_scene()
        aria = "Generic tissue scene"
    return (
        f'<svg viewBox="0 0 220 128" class="cell-context-scene" role="img" '
        f'aria-label="{aria}">{layers}{biology}</svg>'
    )


def _scene_signal_layers(states: Any, strengths: Any, colors: dict[str, str]) -> str:
    if not isinstance(states, dict):
        return ""
    strength_map = strengths if isinstance(strengths, dict) else {}
    parts = []
    if states.get("C") == "positive":
        strength = _number(strength_map.get("C"))
        parts.append(
            f'<rect x="5" y="8" width="210" height="112" rx="18" fill="{colors["C"]}" '
            f'fill-opacity="{0.08 + 0.25 * (strength or 1.0):.3f}"/>'
        )
    if states.get("Y") == "positive":
        strength = _number(strength_map.get("Y"))
        parts.append(
            f'<ellipse cx="110" cy="66" rx="92" ry="45" fill="{colors["Y"]}" '
            f'fill-opacity="{0.06 + 0.22 * (strength or 1.0):.3f}"/>'
        )
    if states.get("K") == "positive":
        strength = _number(strength_map.get("K"))
        width = 1.5 + 3.5 * (strength or 1.0)
        parts.append(
            f'<rect x="8" y="10" width="204" height="108" rx="17" fill="none" '
            f'stroke="{colors["K"]}" stroke-width="{width:.2f}" '
            f'stroke-opacity="{0.25 + 0.65 * (strength or 1.0):.3f}"/>'
        )
    return "".join(parts)


def _epithelial_scene() -> str:
    cells = []
    x_positions = (22, 50, 78, 106, 134, 162, 190)
    for index, x in enumerate(x_positions):
        top = 39 + (index % 2) * 3
        cells.append(
            f'<path d="M{x - 12} {top} L{x + 12} {top} L{x + 10} 93 '
            f'Q{x} 101 {x - 10} 93 Z" fill="#fff" stroke="#64748b" '
            'stroke-width="1.2"/>'
            f'<ellipse cx="{x}" cy="72" rx="6.5" ry="9" fill="#cbd5e1" '
            'stroke="#64748b" stroke-width=".8"/>'
        )
    return (
        '<path d="M10 27 Q45 14 78 25 T145 23 T210 26" fill="none" '
        'stroke="#93c5fd" stroke-width="3"/>'
        '<text x="16" y="20" class="scene-label">lumen</text>'
        + "".join(cells)
        + '<path d="M12 101 C50 96 83 106 111 100 C145 93 175 105 208 99" '
        'fill="none" stroke="#a78bfa" stroke-width="3"/>'
        '<text x="137" y="116" class="scene-label">basement membrane</text>'
    )


def _endothelial_scene() -> str:
    rbc = "".join(
        f'<ellipse cx="{x}" cy="{y}" rx="9" ry="4.5" fill="#fecaca" '
        'stroke="#ef4444" stroke-width=".8"/>'
        for x, y in ((70, 58), (107, 50), (144, 64))
    )
    return (
        '<ellipse cx="110" cy="62" rx="90" ry="37" fill="#eff6ff" '
        'stroke="#94a3b8" stroke-width="1.2"/>'
        '<ellipse cx="110" cy="62" rx="75" ry="25" fill="#fff" '
        'stroke="#cbd5e1" stroke-width="1"/>'
        + rbc
        + '<path d="M34 45 C48 33 62 31 79 35 M86 33 C104 26 124 28 141 35 '
        'M148 36 C167 38 180 45 190 54" fill="none" stroke="#475569" '
        'stroke-width="6" stroke-linecap="round"/>'
        '<path d="M34 79 C48 91 62 93 79 89 M86 91 C104 98 124 96 141 89 '
        'M148 88 C167 86 180 79 190 70" fill="none" stroke="#475569" '
        'stroke-width="6" stroke-linecap="round"/>'
        '<circle cx="57" cy="37" r="4" fill="#bfdbfe"/><circle cx="116" cy="31" r="4" '
        'fill="#bfdbfe"/><circle cx="164" cy="43" r="4" fill="#bfdbfe"/>'
        '<text x="82" y="116" class="scene-label">vascular lumen</text>'
    )


def _fibroblast_scene() -> str:
    fibers = "".join(
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" '
        'stroke-linecap="round"/>'
        for path, color in (
            ("M12 27 C48 12 85 39 122 24 S184 19 210 34", "#d6b98c"),
            ("M8 55 C47 39 82 68 118 51 S178 45 212 61", "#c4a77d"),
            ("M12 87 C52 70 91 98 130 80 S184 73 210 88", "#d6b98c"),
            ("M16 108 C55 91 99 117 139 102 S185 96 208 106", "#c4a77d"),
        )
    )
    fibroblasts = "".join(
        (
            f'<g transform="translate({x} {y}) rotate({angle})">'
            '<path d="M-28 0 C-13 -8 -9 -16 0 -5 C9 -16 13 -8 28 0 '
            'C13 8 9 16 0 5 C-9 16 -13 8 -28 0Z" fill="#fff" '
            'stroke="#6b7280" stroke-width="1.1"/>'
            '<ellipse cx="0" cy="0" rx="7" ry="4" fill="#fed7aa" stroke="#ea580c"/>'
            "</g>"
        )
        for x, y, angle in ((62, 47, -12), (145, 74, 18), (102, 101, -7))
    )
    return (
        fibers
        + fibroblasts
        + '<text x="14" y="118" class="scene-label">collagen-rich ECM</text>'
    )


def _immune_scene() -> str:
    macrophage = (
        '<path d="M122 66 C117 51 128 40 143 45 C157 42 169 54 165 68 '
        'C169 82 156 91 144 87 C131 92 119 80 122 66Z" fill="#fff" '
        'stroke="#64748b" stroke-width="1.2"/>'
        '<path d="M134 64 C135 53 151 51 154 62 C157 72 147 79 139 75 '
        'C135 73 133 69 134 64Z" fill="#c4b5fd" stroke="#7c3aed"/>'
    )
    lymphocytes = "".join(
        f'<g><circle cx="{x}" cy="{y}" r="13" fill="#fff" stroke="#64748b"/>'
        f'<circle cx="{x}" cy="{y}" r="8" fill="#bfdbfe" stroke="#2563eb"/></g>'
        for x, y in ((45, 47), (79, 84), (181, 45), (176, 91))
    )
    return (
        '<path d="M12 108 C44 92 78 115 112 100 S175 92 208 108" fill="none" '
        'stroke="#d1d5db" stroke-width="2"/>'
        + lymphocytes
        + macrophage
        + '<text x="13" y="22" class="scene-label">mixed immune field</text>'
    )


def _generic_tissue_scene() -> str:
    cells = "".join(
        f'<g><circle cx="{x}" cy="{y}" r="15" fill="#fff" stroke="#64748b"/>'
        f'<circle cx="{x}" cy="{y}" r="6" fill="#dbeafe" stroke="#2563eb"/></g>'
        for x, y in ((47, 46), (91, 79), (137, 44), (174, 83))
    )
    return (
        '<path d="M8 109 C43 93 75 113 108 101 S172 92 212 107" fill="none" '
        'stroke="#d1d5db" stroke-width="2"/>'
        + cells
    )


def _cell_category_label(category: str) -> str:
    return {
        "epithelial": "epithelial compartment",
        "endothelial": "vascular compartment",
        "fibroblast": "stromal / ECM compartment",
        "immune": "immune compartment",
        "other": "other cell context",
    }[category]


def render_radial_atlas(
    regions: dict[str, dict[str, Any]],
    radial_tissues: list[dict[str, Any]],
    colors: dict[str, str],
    anatomy_data_uri: str | None = None,
) -> str:
    """Render a central anatomy map surrounded by source-specific tissue tracks."""
    parts = [
        '<svg class="radial-atlas" viewBox="0 0 1000 1000" role="img" '
        'aria-label="Radial body and tissue evidence atlas">',
        render_radial_tracks(radial_tissues, colors),
    ]
    if anatomy_data_uri is not None:
        anatomy_x = 340.0
        anatomy_y = 205.0
        anatomy_width = 320.0
        anatomy_height = 533.0
        parts.append(
            f'<image class="professional-anatomy" href="{_e(anatomy_data_uri)}" '
            f'x="{anatomy_x:.0f}" y="{anatomy_y:.0f}" '
            f'width="{anatomy_width:.0f}" height="{anatomy_height:.0f}" '
            'preserveAspectRatio="xMidYMid meet"/>'
        )
        parts.append(
            render_dbcls_expression_overlay(
                regions,
                colors,
                x=anatomy_x,
                y=anatomy_y,
                width=anatomy_width,
                height=anatomy_height,
            )
        )
        parts.append(
            '<text x="500" y="765" text-anchor="middle" class="radial-center-label">'
            "professional anatomy orientation + expression overlay</text>"
        )
    else:
        parts.extend([
            '<g class="radial-center-body" transform="translate(357 288) scale(.58)">',
            '<g fill="#fbfcfe" stroke="#94a3b8" stroke-width="2.2">',
            BODY_SILHOUETTE,
            "</g>",
        ])
        for region, paths in ORGAN_PATHS.items():
            data = regions.get(region)
            parts.append(
                f'<g class="center-organ center-organ-{_e(region)}" fill="#f1f5f9" '
                'stroke="#94a3b8" stroke-width="1.2">'
                f"{paths}</g>"
            )
            if data is None:
                continue
            states = data.get("channels", {})
            strengths = data.get("strengths", {})
            if not isinstance(states, dict):
                continue
            strength_map = strengths if isinstance(strengths, dict) else {}
            for channel in ("C", "M", "Y"):
                if states.get(channel) != "positive":
                    continue
                strength = _number(strength_map.get(channel))
                parts.append(
                    _organ_layer(
                        region,
                        paths,
                        colors[channel],
                        0.10 + 0.42 * (strength if strength is not None else 1.0),
                        "none",
                        0,
                        channel,
                        blend=True,
                    )
                )
            if states.get("K") == "positive":
                strength = _number(strength_map.get("K"))
                value = strength if strength is not None else 1.0
                parts.append(
                    _organ_layer(
                        region,
                        paths,
                        "none",
                        1.0,
                        colors["K"],
                        1.8 + 3.5 * value,
                        "K",
                        stroke_opacity=0.3 + 0.6 * value,
                    )
                )
    if anatomy_data_uri is None:
        parts.extend(
            [
                "</g>",
                '<text x="500" y="505" text-anchor="middle" class="radial-center-label">'
                "body orientation</text>",
            ]
        )
    parts.append("</svg>")
    return "".join(parts)


def render_tissue_microenvironment(
    microenvironment: dict[str, Any],
    colors: dict[str, str],
) -> str:
    """Render epithelial, stromal, vascular, and immune evidence in one tissue scene."""
    epithelial = _compartment(microenvironment, "epithelial")
    stromal = _compartment(microenvironment, "fibroblast")
    endothelial = _compartment(microenvironment, "endothelial")
    immune = _compartment(microenvironment, "immune")

    return (
        '<div class="microenvironment-view">'
        '<svg class="microenvironment-scene" viewBox="0 0 760 360" role="img" '
        'aria-label="Integrated tissue microenvironment evidence view">'
        '<rect x="8" y="8" width="744" height="344" rx="22" fill="#fcfcfd" '
        'stroke="#e2e8f0"/>'
        + _micro_signal(stromal, colors, 20, 24, 720, 316, 28)
        + _ecm_background()
        + _micro_signal(epithelial, colors, 34, 166, 345, 158, 22)
        + _epithelial_nest()
        + _micro_signal(endothelial, colors, 438, 36, 282, 126, 28)
        + _vessel_scene()
        + _micro_signal(immune, colors, 390, 176, 330, 150, 28)
        + _immune_infiltrate()
        + _fibroblasts_in_stroma()
        + '<text x="42" y="342" class="micro-label">stromal / ECM compartment</text>'
        '<text x="52" y="189" class="micro-label">epithelial compartment</text>'
        '<text x="500" y="59" class="micro-label">vascular compartment</text>'
        '<text x="532" y="205" class="micro-label">immune infiltrate</text>'
        "</svg>"
        + _microenvironment_summary(microenvironment)
        + "</div>"
    )


def _compartment(microenvironment: dict[str, Any], name: str) -> dict[str, Any]:
    value = microenvironment.get(name)
    return value if isinstance(value, dict) else {}


def _micro_signal(
    compartment: dict[str, Any],
    colors: dict[str, str],
    x: float,
    y: float,
    width: float,
    height: float,
    radius: float,
) -> str:
    states = compartment.get("channels", {})
    strengths = compartment.get("strengths", {})
    if not isinstance(states, dict):
        return ""
    strength_map = strengths if isinstance(strengths, dict) else {}
    layers = []
    for channel in ("C", "M", "Y"):
        if states.get(channel) != "positive":
            continue
        strength = _number(strength_map.get(channel))
        value = strength if strength is not None else 1.0
        layers.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" '
            f'fill="{colors[channel]}" fill-opacity="{0.05 + 0.20 * value:.3f}" '
            'style="mix-blend-mode:multiply"/>'
        )
    if states.get("K") == "positive":
        strength = _number(strength_map.get("K"))
        value = strength if strength is not None else 1.0
        layers.append(
            f'<rect x="{x + 3}" y="{y + 3}" width="{width - 6}" height="{height - 6}" '
            f'rx="{max(radius - 3, 1)}" fill="none" stroke="{colors["K"]}" '
            f'stroke-width="{1.5 + 3.5 * value:.2f}" '
            f'stroke-opacity="{0.25 + 0.65 * value:.3f}"/>'
        )
    return "".join(layers)


def _ecm_background() -> str:
    fibers = [
        ("M22 74 C118 39 187 102 286 61 S468 44 738 91", "#d8c7aa"),
        ("M18 124 C99 89 201 153 297 113 S511 85 742 137", "#cbb693"),
        ("M24 276 C112 231 213 297 320 257 S539 229 738 284", "#d8c7aa"),
        ("M36 319 C139 281 241 342 353 302 S562 283 721 318", "#cbb693"),
        ("M302 179 C374 138 452 183 527 155 S650 145 733 171", "#ddceb6"),
    ]
    return "".join(
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.2" '
        'stroke-linecap="round" opacity=".72"/>'
        for path, color in fibers
    )


def _epithelial_nest() -> str:
    cells = []
    for row, y in enumerate((210, 252, 294)):
        offset = 0 if row % 2 == 0 else 18
        for x in range(64 + offset, 350, 38):
            cells.append(
                f'<path d="M{x - 15} {y - 18} Q{x} {y - 28} {x + 15} {y - 18} '
                f'L{x + 13} {y + 14} Q{x} {y + 23} {x - 13} {y + 14} Z" '
                'fill="#fff" fill-opacity=".93" stroke="#64748b" stroke-width="1"/>'
                f'<ellipse cx="{x}" cy="{y}" rx="6.5" ry="8.5" '
                'fill="#cbd5e1" stroke="#64748b" stroke-width=".7"/>'
            )
    return (
        '<path d="M44 190 C127 159 251 166 365 194" fill="none" '
        'stroke="#a78bfa" stroke-width="3"/>'
        + "".join(cells)
        + '<path d="M43 317 C139 329 270 331 365 314" fill="none" '
        'stroke="#a78bfa" stroke-width="3"/>'
    )


def _vessel_scene() -> str:
    return (
        '<ellipse cx="578" cy="111" rx="117" ry="43" fill="#f8fbff" '
        'stroke="#64748b" stroke-width="7"/>'
        '<ellipse cx="578" cy="111" rx="91" ry="28" fill="#fff" '
        'stroke="#cbd5e1" stroke-width="1.2"/>'
        '<ellipse cx="536" cy="105" rx="13" ry="6" fill="#fecaca" stroke="#ef4444"/>'
        '<ellipse cx="582" cy="118" rx="13" ry="6" fill="#fecaca" stroke="#ef4444"/>'
        '<ellipse cx="625" cy="102" rx="13" ry="6" fill="#fecaca" stroke="#ef4444"/>'
        '<circle cx="491" cy="91" r="4.5" fill="#bfdbfe"/>'
        '<circle cx="553" cy="72" r="4.5" fill="#bfdbfe"/>'
        '<circle cx="639" cy="77" r="4.5" fill="#bfdbfe"/>'
    )


def _immune_infiltrate() -> str:
    lymphocytes = "".join(
        f'<g><circle cx="{x}" cy="{y}" r="13" fill="#fff" stroke="#64748b"/>'
        f'<circle cx="{x}" cy="{y}" r="8" fill="#bfdbfe" stroke="#2563eb"/></g>'
        for x, y in ((425, 240), (474, 291), (529, 226), (646, 263), (690, 306))
    )
    macrophages = "".join(
        (
            f'<g transform="translate({x} {y})"><path d="M-20 0 C-24 -16 -10 -26 5 -21 '
            'C19 -25 31 -11 26 4 C31 18 16 29 3 24 C-11 30 -24 16 -20 0Z" '
            'fill="#fff" stroke="#64748b"/>'
            '<path d="M-6 -2 C-5 -13 11 -15 15 -4 C19 7 9 16 -1 12 '
            'C-6 10 -8 5 -6 -2Z" fill="#c4b5fd" stroke="#7c3aed"/></g>'
        )
        for x, y in ((588, 292), (705, 220))
    )
    return lymphocytes + macrophages


def _fibroblasts_in_stroma() -> str:
    return "".join(
        (
            f'<g transform="translate({x} {y}) rotate({angle})">'
            '<path d="M-25 0 C-11 -8 -8 -15 0 -5 C8 -15 11 -8 25 0 '
            'C11 8 8 15 0 5 C-8 15 -11 8 -25 0Z" fill="#fff" '
            'stroke="#6b7280" stroke-width="1"/>'
            '<ellipse cx="0" cy="0" rx="6" ry="4" fill="#fed7aa" stroke="#ea580c"/>'
            "</g>"
        )
        for x, y, angle in ((135, 94, -12), (324, 115, 14), (398, 304, -7))
    )


def _microenvironment_summary(microenvironment: dict[str, Any]) -> str:
    rows = []
    labels = {
        "epithelial": "Epithelial",
        "fibroblast": "Stromal / ECM",
        "endothelial": "Endothelial",
        "immune": "Immune",
    }
    for key, label in labels.items():
        compartment = _compartment(microenvironment, key)
        names = compartment.get("cell_types", [])
        if not isinstance(names, list) or not names:
            continue
        rows.append(
            f'<span class="micro-summary-item"><strong>{label}:</strong> '
            f'{_e(", ".join(str(name) for name in names[:4]))}</span>'
        )
    if not rows:
        return '<p class="note">No cell-type evidence was mappable to tissue compartments.</p>'
    return '<div class="micro-summary">' + "".join(rows) + "</div>"


def render_tissue_comparison(
    microenvironments: dict[str, Any],
    colors: dict[str, str],
) -> str:
    """Render normal/reference and tumor tissue as separate spatial contexts."""
    normal = microenvironments.get("normal_reference")
    tumor = microenvironments.get("tumor")
    normal_context = normal if isinstance(normal, dict) else {}
    tumor_context = tumor if isinstance(tumor, dict) else {}
    return (
        '<div class="tissue-context-pair">'
        + _render_reference_tissue_panel(normal_context, colors)
        + _render_tumor_tissue_panel(tumor_context, colors)
        + "</div>"
    )


def _render_reference_tissue_panel(
    context: dict[str, Any],
    colors: dict[str, str],
) -> str:
    compartments = context.get("compartments")
    data = compartments if isinstance(compartments, dict) else {}
    available = bool(context.get("available"))
    scene = (
        '<svg class="context-tissue-scene" viewBox="0 0 520 330" role="img" '
        'aria-label="Normal or reference tissue microenvironment">'
        '<rect x="7" y="7" width="506" height="316" rx="20" fill="#fbfcfd" '
        'stroke="#dbe2ea"/>'
        + _micro_signal(_compartment(data, "fibroblast"), colors, 18, 20, 484, 292, 24)
        + _reference_ecm()
        + _micro_signal(_compartment(data, "epithelial"), colors, 30, 145, 270, 148, 18)
        + _reference_epithelium()
        + _micro_signal(_compartment(data, "endothelial"), colors, 322, 35, 174, 105, 22)
        + _reference_vessel()
        + _micro_signal(_compartment(data, "immune"), colors, 330, 166, 160, 126, 22)
        + _reference_immune_cells()
        + _reference_fibroblasts()
        + '<text x="36" y="169" class="micro-label">organized epithelium</text>'
        '<text x="345" y="55" class="micro-label">vessel</text>'
        '<text x="358" y="190" class="micro-label">immune cells</text>'
        '<text x="33" y="309" class="micro-label">stromal ECM</text>'
        "</svg>"
    )
    note = _context_note(context, "Reference cell/spatial evidence", available)
    return (
        '<div class="tissue-context-card reference-context">'
        '<div class="tissue-context-head"><strong>Normal / reference tissue</strong>'
        '<span>reference-oriented sources</span></div>'
        + scene
        + note
        + "</div>"
    )


def _render_tumor_tissue_panel(
    context: dict[str, Any],
    colors: dict[str, str],
) -> str:
    compartments = context.get("compartments")
    data = compartments if isinstance(compartments, dict) else {}
    available = bool(context.get("available"))
    opacity = "1" if available else ".34"
    scene = (
        f'<svg class="context-tissue-scene tumor-scene" viewBox="0 0 520 330" role="img" '
        f'aria-label="Tumor tissue microenvironment" opacity="{opacity}">'
        '<rect x="7" y="7" width="506" height="316" rx="20" fill="#fffafb" '
        'stroke="#eadfe3"/>'
        + _micro_signal(_compartment(data, "fibroblast"), colors, 18, 20, 484, 292, 24)
        + _tumor_ecm()
        + _micro_signal(_compartment(data, "epithelial"), colors, 28, 102, 300, 193, 20)
        + _tumor_nests()
        + _micro_signal(_compartment(data, "endothelial"), colors, 330, 32, 170, 112, 20)
        + _tumor_vessel()
        + _micro_signal(_compartment(data, "immune"), colors, 320, 155, 177, 145, 22)
        + _tumor_immune_cells()
        + _tumor_fibroblasts()
        + '<text x="40" y="122" class="micro-label">irregular tumor nests</text>'
        '<text x="353" y="54" class="micro-label">abnormal vessel</text>'
        '<text x="346" y="181" class="micro-label">immune infiltrate</text>'
        '<text x="33" y="309" class="micro-label">desmoplastic stroma</text>'
        "</svg>"
    )
    note = _context_note(context, "Tumor-resolved spatial evidence", available)
    bulk = _bulk_paired_note(context.get("bulk_paired"))
    if not available:
        note += (
            '<p class="context-unavailable">No tumor-resolved cell/spatial evidence '
            "in this build. The morphology is a muted schematic placeholder.</p>"
        )
    return (
        '<div class="tissue-context-card tumor-context">'
        '<div class="tissue-context-head"><strong>Tumor tissue</strong>'
        '<span>tumor-context evidence only</span></div>'
        + scene
        + note
        + bulk
        + "</div>"
    )


def _reference_ecm() -> str:
    return "".join(
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" '
        'stroke-linecap="round" opacity=".62"/>'
        for path, color in (
            ("M18 72 C90 51 154 83 225 59 S385 46 501 78", "#dbcdb7"),
            ("M16 108 C89 86 158 122 232 96 S395 83 503 113", "#ccb99d"),
            ("M24 283 C111 258 181 296 265 272 S416 256 501 286", "#dbcdb7"),
        )
    )


def _reference_epithelium() -> str:
    cells = []
    for x in range(50, 288, 34):
        cells.append(
            f'<path d="M{x - 14} 184 L{x + 14} 184 L{x + 12} 266 '
            f'Q{x} 277 {x - 12} 266 Z" fill="#fff" stroke="#64748b"/>'
            f'<ellipse cx="{x}" cy="230" rx="6" ry="9" fill="#cbd5e1" '
            'stroke="#64748b" stroke-width=".7"/>'
        )
    return (
        '<path d="M35 171 C104 157 211 158 296 173" fill="none" '
        'stroke="#93c5fd" stroke-width="3"/>'
        + "".join(cells)
        + '<path d="M32 281 C112 288 216 288 302 280" fill="none" '
        'stroke="#a78bfa" stroke-width="3"/>'
    )


def _reference_vessel() -> str:
    return (
        '<ellipse cx="410" cy="96" rx="74" ry="31" fill="#f8fbff" '
        'stroke="#64748b" stroke-width="6"/>'
        '<ellipse cx="410" cy="96" rx="55" ry="19" fill="#fff" stroke="#cbd5e1"/>'
        '<ellipse cx="382" cy="94" rx="10" ry="4.5" fill="#fecaca" stroke="#ef4444"/>'
        '<ellipse cx="419" cy="102" rx="10" ry="4.5" fill="#fecaca" stroke="#ef4444"/>'
        '<ellipse cx="446" cy="90" rx="10" ry="4.5" fill="#fecaca" stroke="#ef4444"/>'
    )


def _reference_immune_cells() -> str:
    return "".join(
        f'<g><circle cx="{x}" cy="{y}" r="11" fill="#fff" stroke="#64748b"/>'
        f'<circle cx="{x}" cy="{y}" r="7" fill="#bfdbfe" stroke="#2563eb"/></g>'
        for x, y in ((363, 224), (423, 255), (468, 208))
    )


def _reference_fibroblasts() -> str:
    return "".join(
        (
            f'<g transform="translate({x} {y}) rotate({angle})">'
            '<path d="M-22 0 C-10 -7 -7 -13 0 -4 C7 -13 10 -7 22 0 '
            'C10 7 7 13 0 4 C-7 13 -10 7 -22 0Z" fill="#fff" stroke="#6b7280"/>'
            '<ellipse rx="5.5" ry="3.5" fill="#fed7aa" stroke="#ea580c"/></g>'
        )
        for x, y, angle in ((103, 91, -9), (267, 76, 13), (310, 292, -5))
    )


def _tumor_ecm() -> str:
    return "".join(
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3" '
        'stroke-linecap="round" opacity=".78"/>'
        for path, color in (
            ("M18 69 C81 23 159 96 224 50 S380 35 503 94", "#c9a982"),
            ("M15 114 C87 63 160 144 232 91 S405 67 504 133", "#b9956d"),
            ("M19 265 C97 214 177 302 264 242 S414 219 502 278", "#c9a982"),
            ("M30 302 C111 261 207 323 301 281 S429 269 497 302", "#b9956d"),
        )
    )


def _tumor_nests() -> str:
    nests = []
    nests_spec = (
        (92, 183, 55, 43),
        (198, 207, 67, 53),
        (120, 266, 60, 38),
        (253, 270, 48, 34),
    )
    for cx, cy, rx, ry in nests_spec:
        nests.append(
            f'<path d="M{cx-rx} {cy} C{cx-rx+8} {cy-ry} {cx-18} {cy-ry-8} '
            f'{cx} {cy-ry} C{cx+33} {cy-ry-4} {cx+rx-6} {cy-22} {cx+rx} {cy} '
            f'C{cx+rx-9} {cy+ry} {cx+22} {cy+ry+7} {cx} {cy+ry} '
            f'C{cx-34} {cy+ry+3} {cx-rx+5} {cy+22} {cx-rx} {cy}Z" '
            'fill="#fff" fill-opacity=".92" stroke="#7f1d1d" stroke-width="1.1"/>'
        )
        for dx, dy in ((-18, -9), (8, -12), (-5, 13), (22, 9)):
            nests.append(
                f'<ellipse cx="{cx+dx}" cy="{cy+dy}" rx="6" ry="8" '
                'fill="#d8b4b4" stroke="#7f1d1d" stroke-width=".6"/>'
            )
    return "".join(nests)


def _tumor_vessel() -> str:
    return (
        '<path d="M344 101 C361 55 405 50 432 76 C459 49 497 71 488 111 '
        'C482 142 445 154 416 133 C384 153 350 137 344 101Z" '
        'fill="#f8fbff" stroke="#64748b" stroke-width="6"/>'
        '<path d="M365 104 C385 82 407 84 421 99 C440 81 466 94 467 113 '
        'C447 126 386 128 365 104Z" fill="#fff" stroke="#cbd5e1"/>'
        '<ellipse cx="398" cy="107" rx="10" ry="4.5" fill="#fecaca" stroke="#ef4444"/>'
        '<ellipse cx="445" cy="112" rx="10" ry="4.5" fill="#fecaca" stroke="#ef4444"/>'
    )


def _tumor_immune_cells() -> str:
    lymphocytes = "".join(
        f'<g><circle cx="{x}" cy="{y}" r="11" fill="#fff" stroke="#64748b"/>'
        f'<circle cx="{x}" cy="{y}" r="7" fill="#bfdbfe" stroke="#2563eb"/></g>'
        for x, y in ((348, 212), (390, 254), (438, 216), (475, 263), (453, 298))
    )
    macrophage = (
        '<path d="M352 282 C347 266 360 254 376 259 C392 254 405 269 400 285 '
        'C404 301 390 312 376 307 C362 313 349 299 352 282Z" fill="#fff" '
        'stroke="#64748b"/>'
        '<path d="M365 280 C366 268 383 267 387 278 C391 290 380 297 371 293 '
        'C366 291 364 286 365 280Z" fill="#c4b5fd" stroke="#7c3aed"/>'
    )
    return lymphocytes + macrophage


def _tumor_fibroblasts() -> str:
    return "".join(
        (
            f'<g transform="translate({x} {y}) rotate({angle})">'
            '<path d="M-25 0 C-11 -8 -8 -15 0 -5 C8 -15 11 -8 25 0 '
            'C11 8 8 15 0 5 C-8 15 -11 8 -25 0Z" fill="#fff" '
            'stroke="#6b7280" stroke-width="1.2"/>'
            '<ellipse rx="6" ry="4" fill="#fed7aa" stroke="#ea580c"/></g>'
        )
        for x, y, angle in ((82, 77, -17), (263, 77, 18), (320, 155, -8), (314, 294, 12))
    )


def _context_note(context: dict[str, Any], prefix: str, available: bool) -> str:
    diseases = context.get("disease_labels")
    labels = diseases if isinstance(diseases, list) else []
    datasets = context.get("dataset_count")
    count = int(datasets) if isinstance(datasets, int) else 0
    if not available:
        return f'<p class="note">{_e(prefix)}: unavailable.</p>'
    suffix = f" · {count} spatial dataset(s)"
    if labels:
        suffix += " · " + ", ".join(str(label) for label in labels[:3])
    return f'<p class="note">{_e(prefix + suffix)}</p>'


def _bulk_paired_note(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return ""
    rows = [row for row in value if isinstance(row, dict)]
    if not rows:
        return ""
    fragments = []
    for row in rows[:3]:
        paired = row.get("paired_case_count")
        delta = row.get("median_tumor_minus_adjacent")
        fraction = row.get("tumor_higher_fraction")
        detail = f'{_e(row.get("study_id") or "PDC")} · {int(paired or 0)} paired cases'
        if isinstance(delta, (int, float)):
            detail += f" · median tumor-adjacent Δ {float(delta):.2g}"
        if isinstance(fraction, (int, float)):
            detail += f" · {100 * float(fraction):.0f}% tumor-higher"
        fragments.append(f"<li>{detail}</li>")
    return (
        '<div class="bulk-tumor-note"><strong>Paired bulk tumor evidence</strong>'
        '<ul>' + "".join(fragments) + "</ul>"
        '<small>Bulk paired evidence is not mapped onto specific cell compartments.</small>'
        "</div>"
    )


def render_subcellular(locations: Any) -> str:
    values = [str(value) for value in locations] if isinstance(locations, list) else []
    text = " ".join(values).casefold()
    membrane = any(word in text for word in ("membrane", "cell junction", "plasma"))
    cytoplasm = any(word in text for word in ("cytoplas", "cytosol", "vesicle", "golgi"))
    nucleus = any(word in text for word in ("nucle", "chromatin"))
    extracellular = any(word in text for word in ("secret", "extracellular"))
    return (
        '<div class="subcellular-figure">'
        '<svg viewBox="0 0 260 220" role="img" aria-label="Subcellular localization schematic">'
        f'<circle cx="130" cy="110" r="92" fill="{"#fef3c7" if extracellular else "#f8fafc"}" '
        'stroke="#d1d5db" stroke-dasharray="5 5"/>'
        f'<circle cx="130" cy="110" r="72" fill="{"#dbeafe" if cytoplasm else "#f8fafc"}" '
        f'stroke="{"#2563eb" if membrane else "#94a3b8"}" '
        f'stroke-width="{7 if membrane else 2}"/>'
        f'<circle cx="130" cy="110" r="31" fill="{"#ddd6fe" if nucleus else "#e5e7eb"}" '
        'stroke="#7c3aed" stroke-width="2"/>'
        '<circle cx="95" cy="82" r="8" fill="#fca5a5"/>'
        '<circle cx="162" cy="139" r="7" fill="#fca5a5"/>'
        '<text x="130" y="113" text-anchor="middle" class="subcell-label">nucleus</text>'
        '<text x="130" y="55" text-anchor="middle" class="subcell-label">cytoplasm</text>'
        '<text x="130" y="202" text-anchor="middle" class="subcell-label">extracellular</text>'
        "</svg>"
        '<p class="note">'
        f'{_e(", ".join(values) if values else "No HPA subcellular annotation.")}'
        "</p>"
        "</div>"
    )


def cell_category(name: str) -> str:
    text = name.casefold()
    if any(
        token in text
        for token in ("t cell", "b cell", "lymph", "macroph", "monocyte", "immune")
    ):
        return "immune"
    if "endothelial" in text:
        return "endothelial"
    if any(token in text for token in ("fibroblast", "stromal", "mesenchymal")):
        return "fibroblast"
    if any(token in text for token in ("epithelial", "epitheli", "carcinoma", "tumor")):
        return "epithelial"
    return "other"


def _organ_layer(
    region: str,
    paths: str,
    fill: str,
    opacity: float,
    stroke: str,
    stroke_width: float,
    channel: str,
    *,
    blend: bool = False,
    stroke_opacity: float = 1.0,
) -> str:
    style = ' style="mix-blend-mode:multiply"' if blend else ""
    return (
        f'<g class="organ organ-{_e(region)} source-{_e(channel)}" '
        f'fill="{fill}" fill-opacity="{opacity:.3f}" stroke="{stroke}" '
        f'stroke-width="{stroke_width:.2f}" stroke-opacity="{stroke_opacity:.3f}"{style}>'
        f"{paths}</g>"
    )


def _source_opacity(state: Any, strength: float | None) -> float:
    if state != "positive":
        return 0.0 if state == "unknown" else 0.18
    value = 1.0 if strength is None else max(0.0, min(1.0, strength))
    return 0.20 + 0.75 * value


def _channel_badges(states: Any, strengths: Any, colors: dict[str, str]) -> str:
    if not isinstance(states, dict):
        return ""
    badges = []
    for channel in ("C", "M", "Y", "K"):
        state = str(states.get(channel) or "unknown")
        strength = _number(strengths.get(channel)) if isinstance(strengths, dict) else None
        label = SOURCE_LABELS[channel]
        text = label if strength is None else f"{label} {strength:.0%}"
        badges.append(
            f'<span class="cell-source-badge state-{_e(state)}" '
            f'style="--source-color:{colors[channel]}">{_e(text)}</span>'
        )
    return '<div class="cell-source-badges">' + "".join(badges) + "</div>"


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)
