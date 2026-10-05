"""Self-contained local HTML summary for Spatial Target Atlas outputs."""

from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def render_atlas_html(
    core_dir: Path,
    hubmap_cells_dir: Path | None = None,
    spatial_census_dir: Path | None = None,
    reference_audit_path: Path | None = None,
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

    reference_audit: dict[str, Any] | None = None
    if reference_audit_path is not None and reference_audit_path.exists():
        value = json.loads(reference_audit_path.read_text(encoding="utf-8"))
        if isinstance(value, dict):
            reference_audit = value

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
) -> str:
    target_evidence = [row for row in evidence if row.get("gene_symbol") == target]
    parts = [f"<section><h2>{_e(target)}</h2>"]
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
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


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
</style>
</head>
<body>
<h1>Spatial Target Atlas</h1>
<p class="subtitle">Local evidence report. Measurements remain in source-specific scales.</p>
""" + content + """
</body>
</html>
"""
