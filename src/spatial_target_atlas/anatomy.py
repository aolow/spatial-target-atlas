"""Repo-owned SVG anatomy primitives for spatial evidence rendering.

The drawings are schematic masks designed for data overlays, not diagnostic anatomy.
They are original project artwork so their fill/opacity can be controlled directly.
"""

from __future__ import annotations

import html
from typing import Any

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
    "C": "HPA protein",
    "M": "ProteomicsDB",
    "Y": "spatial RNA",
    "K": "spatial protein",
}


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
            f'<strong>{channel}</strong> {_e(SOURCE_LABELS[channel])}</div>'
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
        text = channel if strength is None else f"{channel} {strength:.2f}"
        badges.append(
            f'<span class="cell-source-badge state-{_e(state)}" '
            f'style="--source-color:{colors[channel]}">{_e(text)}</span>'
        )
    return '<div class="cell-source-badges">' + "".join(badges) + "</div>"


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)
