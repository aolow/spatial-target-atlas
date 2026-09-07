"""Cross-source tissue-rank reproducibility for mass-spectrometry evidence."""

from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Any

from .concordance import _pearson, _ranks
from .models import Modality, ProteinEvidenceRecord, SpatialScale


def summarize_cross_source(records: list[ProteinEvidenceRecord]) -> list[dict[str, Any]]:
    values: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    for record in records:
        if (
            record.modality == Modality.MASS_SPECTROMETRY
            and record.spatial_scale == SpatialScale.TISSUE
            and record.tissue
            and record.value is not None
            and record.value > 0
        ):
            values[(record.gene_symbol, record.source, record.tissue.casefold())].append(
                record.value
            )
    results = []
    for gene in sorted({key[0] for key in values}):
        hpa = {
            tissue: statistics.median(measurements)
            for (row_gene, source, tissue), measurements in values.items()
            if row_gene == gene and source == "Human Protein Atlas"
        }
        proteomicsdb = {
            tissue: statistics.median(measurements)
            for (row_gene, source, tissue), measurements in values.items()
            if row_gene == gene and source == "ProteomicsDB"
        }
        common = sorted(hpa.keys() & proteomicsdb.keys())
        hpa_ranks = _ranks([hpa[tissue] for tissue in common])
        pdb_ranks = _ranks([proteomicsdb[tissue] for tissue in common])
        rows: list[dict[str, Any]] = [
            {
                "tissue": tissue,
                "hpa_rank": hpa_rank,
                "proteomicsdb_rank": pdb_rank,
                "absolute_rank_difference": abs(hpa_rank - pdb_rank),
            }
            for tissue, hpa_rank, pdb_rank in zip(common, hpa_ranks, pdb_ranks, strict=True)
        ]
        results.append(
            {
                "gene": gene,
                "common_tissues": len(common),
                "spearman": _pearson(hpa_ranks, pdb_ranks),
                "largest_rank_disagreements": sorted(
                    rows,
                    key=lambda row: float(row["absolute_rank_difference"]),
                    reverse=True,
                )[:5],
                "interpretation": "Within-source tissue ranks; raw intensities are not combined.",
            }
        )
    return results
