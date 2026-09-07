"""Within-source RNA–protein concordance without cross-assay scale merging."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .models import Modality, ProteinEvidenceRecord, SpatialScale


def summarize_concordance(records: list[ProteinEvidenceRecord]) -> list[dict[str, Any]]:
    paired: defaultdict[tuple[str, str], dict[Modality, float | None]] = defaultdict(dict)
    for record in records:
        if record.spatial_scale == SpatialScale.CELL_TYPE and record.cell_type:
            paired[(record.gene_symbol, record.cell_type)][record.modality] = record.value
    results = []
    for gene in sorted({gene for gene, _ in paired}):
        all_rows: list[dict[str, Any]] = [
            {
                "cell_type": cell_type,
                "rna": values.get(Modality.TRANSCRIPTOMICS),
                "protein": values.get(Modality.MASS_SPECTROMETRY),
            }
            for (row_gene, cell_type), values in paired.items()
            if row_gene == gene
        ]
        rows = [
            row
            for row in all_rows
            if row["rna"] is not None
            and float(row["rna"]) > 0
            and row["protein"] is not None
            and float(row["protein"]) > 0
        ]
        rna_ranks = _ranks([float(row["rna"]) for row in rows])
        protein_ranks = _ranks([float(row["protein"]) for row in rows])
        for row, rna_rank, protein_rank in zip(rows, rna_ranks, protein_ranks, strict=True):
            row["rna_rank"] = rna_rank
            row["protein_rank"] = protein_rank
            row["absolute_rank_difference"] = abs(rna_rank - protein_rank)
        results.append(
            {
                "gene": gene,
                "contexts": len(all_rows),
                "complete_detected_contexts": len(rows),
                "detection_concordance": {
                    "both_detected": _quadrant(all_rows, True, True),
                    "rna_only": _quadrant(all_rows, True, False),
                    "protein_only": _quadrant(all_rows, False, True),
                    "neither_detected": _quadrant(all_rows, False, False),
                },
                "spearman": _pearson(rna_ranks, protein_ranks),
                "largest_discordances": sorted(
                    rows,
                    key=lambda row: float(row["absolute_rank_difference"]),
                    reverse=True,
                )[:5],
            }
        )
    return results


def _quadrant(rows: list[dict[str, Any]], rna_detected: bool, protein_detected: bool) -> int:
    return sum(
        (row["rna"] is not None and float(row["rna"]) > 0) == rna_detected
        and (row["protein"] is not None and float(row["protein"]) > 0) == protein_detected
        for row in rows
    )


def _ranks(values: list[float]) -> list[float]:
    ordered = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][0] == ordered[start][0]:
            end += 1
        rank = (start + end - 1) / 2 + 1
        for _, index in ordered[start:end]:
            ranks[index] = rank
        start = end
    return ranks


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) < 3:
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True))
    left_ss = sum((x - left_mean) ** 2 for x in left)
    right_ss = sum((y - right_mean) ** 2 for y in right)
    if left_ss == 0 or right_ss == 0:
        return None
    return float(round(numerator / (left_ss * right_ss) ** 0.5, 3))
