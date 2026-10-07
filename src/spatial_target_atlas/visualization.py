"""Self-contained local HTML summary for Spatial Target Atlas outputs."""

from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .overlay import build_overlay_from_files, render_spatial_vignette


def render_atlas_html(
    core_dir: Path,
    hubmap_cells_dir: Path | None = None,
    spatial_census_dir: Path | None = None,
    reference_audit_path: Path | None = None,
    model_evidence_path: Path | None = None,
    anatomy_data_uri: str | None = None,
) -> str:
    identities = _read_list(core_dir / "target_identities.json")
    evidence = _read_list(core_dir / "evidence.json")
    concordance = _read_list(core_dir / "concordance.json")
    cross_source = _read_list(core_dir / "cross_source_concordance.json")
    paired = _read_list(core_dir / "paired_tumor_normal.json")
    coverage = _read_list(core_dir / "spatial_target_coverage.json")

    cell_summary: list[dict[str, Any]] = []
    query_status: list[dict[str, Any]] = []
    if hubmap_cells_dir is not None:
        cell_summary = _read_list(hubmap_cells_dir / "hubmap_cell_protein_summary.json")
        query_status = _read_list(hubmap_cells_dir / "hubmap_cell_query_status.json")

    census: list[dict[str, Any]] = []
    if spatial_census_dir is not None:
        census = _read_list(spatial_census_dir / "census_spatial_expression.json")

    model_evidence: list[dict[str, Any]] = []
    if model_evidence_path is not None:
        model_evidence = _read_list(model_evidence_path)

    reference_audit: dict[str, Any] | None = None
    if reference_audit_path is not None and reference_audit_path.exists():
        raw_audit = json.loads(reference_audit_path.read_text(encoding="utf-8"))
        if isinstance(raw_audit, dict) and all(isinstance(key, str) for key in raw_audit):
            reference_audit = {str(key): value for key, value in raw_audit.items()}

    overlay_payload = build_overlay_from_files(core_dir, hubmap_cells_dir, spatial_census_dir)
    overlay_by_target = {
        str(item.get("gene_symbol")): item
        for item in overlay_payload.get("targets", [])
        if isinstance(item, dict) and item.get("gene_symbol")
    }

    targets = _target_names(identities, evidence, cell_summary, census)
    sections = [
        _overview(targets, evidence, coverage, cell_summary, census),
        *[
            _target_section(
                target,
                evidence,
                concordance,
                cross_source,
                paired,
                coverage,
                cell_summary,
                census,
                model_evidence,
                overlay_by_target.get(target),
                anatomy_data_uri,
            )
            for target in targets
        ],
    ]
    if reference_audit is not None:
        sections.append(_reference_section(reference_audit))
    if query_status:
        sections.append(_query_status_section(query_status))

    return _page("\n".join(sections))


def _target_names(
    identities: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    cell_summary: list[dict[str, Any]],
    census: list[dict[str, Any]],
) -> list[str]:
    names = {
        str(row.get("gene_symbol"))
        for rows in (identities, evidence, cell_summary, census)
        for row in rows
        if row.get("gene_symbol")
    }
    return sorted(names)


def _overview(
    targets: list[str],
    evidence: list[dict[str, Any]],
    coverage: list[dict[str, Any]],
    cell_summary: list[dict[str, Any]],
    census: list[dict[str, Any]],
) -> str:
    rows = []
    for target in targets:
        target_evidence = [row for row in evidence if row.get("gene_symbol") == target]
        target_coverage = [row for row in coverage if row.get("gene_symbol") == target]
        target_cells = [row for row in cell_summary if row.get("gene_symbol") == target]
        target_census = [row for row in census if row.get("gene_symbol") == target]
        rows.append({
            "Target": target,
            "Evidence records": len(target_evidence),
            "Sources": len({str(row.get("source")) for row in target_evidence}),
            "Modalities": len({str(row.get("modality")) for row in target_evidence}),
            "HuBMAP assayed datasets": len({
                str(row.get("dataset_uuid"))
                for row in target_coverage
                if row.get("coverage_state") == "assayed"
            }),
            "HuBMAP cell groups": len(target_cells),
            "Spatial transcriptomic groups": len(target_census),
        })
    return (
        "<section><h2>At a glance</h2>"
        "<p>Counts describe available evidence, not a target quality or safety score.</p>"
        + _table(rows)
        + "</section>"
    )


def _target_section(
    target: str,
    evidence: list[dict[str, Any]],
    concordance: list[dict[str, Any]],
    cross_source: list[dict[str, Any]],
    paired: list[dict[str, Any]],
    coverage: list[dict[str, Any]],
    cell_summary: list[dict[str, Any]],
    census: list[dict[str, Any]],
    model_evidence: list[dict[str, Any]],
    overlay_target: dict[str, Any] | None,
    anatomy_data_uri: str | None,
) -> str:
    target_evidence = [row for row in evidence if row.get("gene_symbol") == target]
    parts = [f"<section><h2>{_e(target)}</h2>"]
    if overlay_target is not None:
        parts.append(
            render_spatial_vignette(
                overlay_target,
                anatomy_data_uri=anatomy_data_uri,
            )
        )
    parts.append("<h3>Measured evidence footprint</h3>")
    parts.append(_table(_evidence_footprint(target_evidence)))

    within = [row for row in concordance if row.get("gene") == target]
    if within:
        parts.append("<h3>HPA RNA/protein concordance</h3>")
        parts.append(_table([{
            "Contexts": row.get("contexts"),
            "Jointly detected": row.get("complete_detected_contexts"),
            "Spearman rho": row.get("spearman"),
            "RNA only": (row.get("detection_concordance") or {}).get("rna_only"),
            "Protein only": (row.get("detection_concordance") or {}).get("protein_only"),
        } for row in within]))

    cross = [row for row in cross_source if row.get("gene") == target]
    if cross:
        parts.append("<h3>HPA vs ProteomicsDB tissue ranks</h3>")
        parts.append(_table([{
            "Matched tissues": row.get("common_tissues"),
            "Spearman rho": row.get("spearman"),
            "Interpretation": row.get("interpretation"),
        } for row in cross]))

    paired_rows = [row for row in paired if row.get("gene_symbol") == target]
    if paired_rows:
        parts.append("<h3>Paired tumor vs adjacent tissue</h3>")
        parts.append(_table([{
            "Study": row.get("study_id"),
            "Paired cases": row.get("paired_case_count"),
            "Median tumor-adjacent delta": row.get(
                "median_paired_tumor_minus_adjacent_log2_ratio"
            ),
            "Tumor higher fraction": row.get("tumor_higher_fraction"),
            "Interpretation": row.get("interpretation"),
        } for row in paired_rows]))

    coverage_rows = [row for row in coverage if row.get("gene_symbol") == target]
    if coverage_rows:
        parts.append("<h3>HuBMAP targeted-panel coverage</h3>")
        counts: dict[str, int] = defaultdict(int)
        for row in coverage_rows:
            counts[str(row.get("coverage_state") or "unknown")] += 1
        parts.append(_table([
            {"Coverage state": state, "Dataset count": count}
            for state, count in sorted(counts.items())
        ]))

    cells = [row for row in cell_summary if row.get("gene_symbol") == target]
    if cells:
        parts.append("<h3>HuBMAP per-cell protein summaries</h3>")
        selected = sorted(
            cells,
            key=lambda row: (
                -(float(row.get("positive_cell_fraction") or 0)),
                -int(row.get("cell_count") or 0),
                str(row.get("cell_type") or ""),
            ),
        )[:30]
        parts.append(_table([{
            "Dataset": row.get("dataset_id"),
            "Cell type": row.get("cell_type") or "unannotated",
            "Cells": row.get("cell_count"),
            "Positive fraction": row.get("positive_cell_fraction"),
            "Median intensity": row.get("median_source_scale_intensity"),
            "Protein channel": row.get("protein_id"),
        } for row in selected]))
        parts.append(
            "<p class=\"note\">Source-scale intensity is comparable only within the "
            "dataset unless separately calibrated.</p>"
        )

    spatial = [row for row in census if row.get("gene_symbol") == target]
    if spatial:
        parts.append("<h3>Spatial transcriptomic reference contexts</h3>")
        parts.append(_table(_census_summary(spatial)))

    modeled = [row for row in model_evidence if row.get("gene_symbol") == target]
    if modeled:
        parts.append("<h3>Model-derived context</h3>")
        parts.append(_table([{
            "Model": row.get("model_name"),
            "Evidence kind": row.get("evidence_kind"),
            "Context type": row.get("context_type"),
            "Context": row.get("context"),
            "Score": row.get("score"),
            "Score name": row.get("score_name"),
            "Note": row.get("note"),
        } for row in modeled[:50]]))
        parts.append(
            "<p class=\"note\">Model-derived records are displayed separately from "
            "measured evidence and are not included in assay counts.</p>"
        )

    parts.append("</section>")
    return "".join(parts)


def _evidence_footprint(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        groups[(
            str(row.get("source") or ""),
            str(row.get("modality") or ""),
            str(row.get("spatial_scale") or ""),
        )].append(row)
    output = []
    for (source, modality, scale), subset in sorted(groups.items()):
        tissues = {str(row.get("tissue")) for row in subset if row.get("tissue")}
        cell_types = {str(row.get("cell_type")) for row in subset if row.get("cell_type")}
        states = {str(row.get("detection_state")) for row in subset}
        output.append({
            "Source": source,
            "Modality": modality,
            "Scale": scale,
            "Records": len(subset),
            "Tissues": len(tissues),
            "Cell types": len(cell_types),
            "Detection states": ", ".join(sorted(states)),
        })
    return output


def _census_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        groups[str(row.get("reference_context") or "unknown")].append(row)
    output = []
    for context, subset in sorted(groups.items()):
        assayed = [row for row in subset if row.get("detection_state") != "not_assayed"]
        spots = sum(int(row.get("spot_count") or 0) for row in assayed)
        positive = sum(int(row.get("positive_spot_count") or 0) for row in assayed)
        output.append({
            "Reference context": context,
            "Datasets": len({str(row.get("dataset_id")) for row in assayed}),
            "Donors": len({str(row.get("donor_id")) for row in assayed}),
            "Assayed spots": spots,
            "Positive fraction": positive / spots if spots else None,
        })
    return output


def _reference_section(audit: dict[str, Any]) -> str:
    candidates = audit.get("candidates")
    rows = candidates if isinstance(candidates, list) else []
    return (
        "<section><h2>Reference context audit</h2>"
        "<p>Reference roles are categorical and auditable, not a composite score.</p>"
        + _table([{
            "Context": row.get("reference_context"),
            "Role": row.get("role"),
            "Rank": row.get("rank"),
            "Donors": row.get("donor_count"),
            "Datasets": row.get("dataset_count"),
            "Caveats": "; ".join(str(x) for x in row.get("caveats", [])),
        } for row in rows if isinstance(row, dict)])
        + "</section>"
    )


def _query_status_section(rows: list[dict[str, Any]]) -> str:
    return (
        "<section><h2>HuBMAP Cells API query status</h2>"
        + _table([{
            "Dataset": row.get("dataset_id"),
            "Target": row.get("gene_symbol"),
            "Protein channel": row.get("protein_id"),
            "Status": row.get("status"),
            "Indexed cells": row.get("cell_count"),
            "Records": row.get("records"),
            "Message": row.get("message"),
        } for row in rows])
        + "</section>"
    )


def _read_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []
    output: list[dict[str, Any]] = []
    for row in raw:
        if isinstance(row, dict) and all(isinstance(key, str) for key in row):
            output.append({str(key): value for key, value in row.items()})
    return output


def _table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p class=\"empty\">No data available.</p>"
    columns = list(rows[0])
    head = "".join(f"<th>{_e(column)}</th>" for column in columns)
    body = []
    for row in rows:
        body.append(
            "<tr>"
            + "".join(f"<td>{_e(_format(row.get(column)))}</td>" for column in columns)
            + "</tr>"
        )
    return (
        "<div class=\"table-wrap\"><table><thead><tr>"
        + head
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def _format(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3g}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _page(content: str) -> str:
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Spatial Target Atlas</title>
<style>
body { font-family: system-ui, -apple-system, sans-serif; max-width: 1180px; margin: 0 auto;
       padding: 32px 20px 80px; line-height: 1.45; color: #1f2328; }
h1 { margin-bottom: 4px; }
h2 { margin-top: 42px; border-bottom: 1px solid #d0d7de; padding-bottom: 8px; }
h3 { margin-top: 28px; }
.subtitle, .note, .empty { color: #57606a; }
.table-wrap { overflow-x: auto; margin: 12px 0 20px; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { border: 1px solid #d8dee4; padding: 7px 9px; text-align: left; vertical-align: top; }
th { background: #f6f8fa; }
section { scroll-margin-top: 16px; }
.spatial-vignette { margin: 18px 0 34px; padding: 20px; border: 1px solid #d8dee4;
  border-radius: 16px; background: #fbfcfe; }
.spatial-head { display:flex; gap:18px; align-items:flex-start; justify-content:space-between;
  flex-wrap:wrap; }
.spatial-head h3 { margin:0; }
.overlay-legend { display:flex; gap:9px 14px; flex-wrap:wrap; font-size:12px; max-width:580px; }
.legend-item { display:flex; align-items:center; gap:5px; }
.swatch { width:13px; height:13px; border-radius:3px; border:1px solid #64748b;
  display:inline-block; }
.spatial-grid { display:grid; grid-template-columns:minmax(270px,.8fr) minmax(300px,1.2fr);
  gap:22px; align-items:start; margin-top:16px; }
.body-panel { background:white; border:1px solid #e5e7eb; border-radius:14px; padding:12px; }
.body-map { width:100%; max-width:360px; margin:auto; display:block; }
.anatomy-map { width:100%; max-width:390px; margin:auto; display:block; overflow:visible; }
.anatomy-mini { max-width:155px; }
.anatomy-map .organ { transition:opacity .15s ease; }
.anatomy-map .anatomy-label { font:11px system-ui,sans-serif; fill:#475569;
  paint-order:stroke; stroke:white; stroke-width:3px; }
.source-multiples { display:grid; grid-template-columns:repeat(2,minmax(130px,1fr)); gap:10px;
  margin-bottom:18px; }
.source-mini { background:white; border:1px solid #e5e7eb; border-radius:12px; padding:8px; }
.source-mini-head { display:flex; align-items:center; gap:5px; font-size:11px; color:#475569; }
.source-dot { display:inline-block; width:10px; height:10px; border-radius:50%; }
.cell-context-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:12px; }
.cell-context-card { display:flex; flex-direction:column; gap:6px; padding:10px;
  border:1px solid #e5e7eb; border-radius:12px; background:white; text-align:left; }
.cell-context-card small { color:#64748b; }
.cell-context-scene { width:100%; min-height:120px; display:block; border-radius:10px;
  background:#fcfcfd; }
.cell-scene-copy { display:flex; flex-direction:column; gap:2px; }
.scene-label { font:9px system-ui,sans-serif; fill:#64748b; }
.cell-source-badges { display:flex; flex-wrap:wrap; justify-content:flex-start; gap:3px;
  margin-top:4px; }
.cell-source-badge { font-size:8px; border-radius:999px; padding:1px 5px;
  border:1px solid #cbd5e1; }
.cell-source-badge.state-positive { background:color-mix(in srgb,var(--source-color) 24%,white);
  border-color:var(--source-color); color:#111827; }
.cell-source-badge.state-negative { background:white; color:#94a3b8; text-decoration:line-through; }
.cell-source-badge.state-unknown { background:#f8fafc; color:#cbd5e1; }
.subcellular-figure svg { width:100%; max-width:280px; display:block; margin:auto; }
.subcell-label { font:10px system-ui,sans-serif; fill:#475569; }
.organ-label { font: 12px system-ui, sans-serif; fill:#475569; }
.organ-cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(175px,1fr)); gap:9px; }
.organ-card { display:flex; align-items:center; gap:10px; padding:9px; background:white;
  border:1px solid #e5e7eb; border-radius:10px; }
.organ-dot { width:25px; height:25px; border-radius:50%; flex:0 0 auto; }
.channel-chip { display:inline-flex; align-items:center; gap:4px; padding:1px 5px;
  margin:3px 3px 0 0; border-radius:5px; font-size:9px; font-weight:650;
  border:1px solid #cbd5e1; }
.channel-chip-dot { width:7px; height:7px; border-radius:50%; display:inline-block; }
.state-positive { background:#111827; color:white; }
.state-negative { background:white; color:#64748b; text-decoration:line-through; }
.state-unknown { background:#f1f5f9; color:#94a3b8; }
.lower-grid { display:grid; grid-template-columns:1.2fr .8fr; gap:20px; margin-top:18px; }
.cell-bubbles { display:flex; gap:8px; flex-wrap:wrap; }
.cell-bubble { min-width:72px; max-width:150px; padding:9px 11px; border:1px solid #94a3b8;
  border-radius:999px; font-size:12px; text-align:center; color:#111827; }
.subcell-grid { display:grid; grid-template-columns:1fr 1fr; gap:7px; }
.subcell-box { padding:10px; border-radius:9px; border:1px solid #cbd5e1; background:#f8fafc;
  color:#94a3b8; font-size:12px; }
.subcell-box.active { background:#dbeafe; border-color:#60a5fa; color:#1e3a8a; font-weight:700; }
.disease-badge { margin:10px 0 0; padding:9px 11px; border-left:4px solid #fb7185;
  background:#fff1f2; font-size:12px; border-radius:6px; }
.radial-panel { margin-top:18px; background:white; border:1px solid #e5e7eb;
  border-radius:16px; padding:12px 14px 16px; }
.radial-atlas { display:block; width:100%; max-width:980px; margin:0 auto; overflow:visible; }
.radial-label { font:11px system-ui,sans-serif; fill:#334155; }
.radial-center-label { font:10px system-ui,sans-serif; fill:#94a3b8; letter-spacing:.04em; }
.radial-track { transition:opacity .15s ease; }
.hierarchy-grid { display:grid; grid-template-columns:minmax(0,1.7fr) minmax(260px,.7fr);
  gap:18px; margin-top:18px; align-items:start; }
.tissue-panel, .subcellular-panel { background:white; border:1px solid #e5e7eb;
  border-radius:14px; padding:14px; }
.tissue-panel h4, .subcellular-panel h4 { margin-top:0; }
.tissue-context-pair { display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
  gap:14px; }
.tissue-context-card { border:1px solid #e5e7eb; border-radius:12px; background:#fcfcfd;
  padding:10px; min-width:0; }
.tissue-context-card.tumor-context { background:#fffafb; border-color:#eadfe3; }
.tissue-context-head { display:flex; justify-content:space-between; align-items:baseline;
  gap:8px; margin-bottom:7px; }
.tissue-context-head strong { font-size:13px; }
.tissue-context-head span { font-size:10px; color:#64748b; }
.context-tissue-scene { display:block; width:100%; min-height:250px; }
.context-unavailable { margin:8px 0 0; padding:7px 9px; border-radius:8px;
  background:#f8fafc; color:#64748b; font-size:11px; }
.bulk-tumor-note { margin-top:8px; padding:8px 10px; border-left:4px solid #fb7185;
  background:#fff1f2; border-radius:7px; font-size:11px; }
.bulk-tumor-note ul { margin:5px 0; padding-left:18px; }
.microenvironment-scene { display:block; width:100%; min-height:300px; }
.micro-label { font:10px system-ui,sans-serif; fill:#475569; paint-order:stroke;
  stroke:white; stroke-width:3px; }
.micro-summary { display:grid; gap:5px; margin-top:8px; }
.micro-summary-item { font-size:11px; color:#475569; }
.dataset-section { margin-top:20px; }
.dataset-family { margin:12px 0 18px; }
.dataset-card { background:white; border:1px solid #e5e7eb; border-radius:10px; padding:8px 11px;
  margin:7px 0; }
.dataset-rows { margin:9px 0; }
.dataset-row { display:grid; grid-template-columns:minmax(120px,1fr) minmax(120px,2fr) 70px 64px;
  gap:8px; align-items:center; font-size:11px; padding:4px 0; }
.intensity-track { height:10px; background:#eef2f7; border-radius:7px; overflow:hidden; }
.intensity-track span { display:block; height:100%;
  background:linear-gradient(90deg,#00b7d8,#d946ef); }
@media (max-width:760px) {
  .spatial-grid, .lower-grid, .hierarchy-grid, .tissue-context-pair { grid-template-columns:1fr; }
  .source-multiples { grid-template-columns:repeat(2,1fr); }
  .radial-label { font-size:9px; }
  .dataset-row { grid-template-columns:1fr; gap:3px; }
}
</style>
</head>
<body>
<h1>Spatial Target Atlas</h1>
<p class="subtitle">Local evidence report. Measurements remain in source-specific scales.</p>
""" + content + """
</body>
</html>
"""
