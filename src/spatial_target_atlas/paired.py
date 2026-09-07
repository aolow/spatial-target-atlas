"""Paired tumor/adjacent-normal summaries for PDC target evidence."""

from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Any

from .models import ProteinEvidenceRecord


def summarize_paired(records: list[ProteinEvidenceRecord]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for record in records:
        if (
            record.source != "NCI Proteomic Data Commons"
            or record.value is None
            or record.case_id is None
            or record.specimen_context not in {"tumor", "adjacent_normal"}
        ):
            continue
        grouped[(record.source_release, record.gene_symbol)][record.case_id][
            record.specimen_context
        ].append(record.value)

    summaries = []
    for (study_id, gene), cases in sorted(grouped.items()):
        deltas = []
        for contexts in cases.values():
            if contexts["tumor"] and contexts["adjacent_normal"]:
                deltas.append(median(contexts["tumor"]) - median(contexts["adjacent_normal"]))
        summaries.append(
            {
                "source": "NCI Proteomic Data Commons",
                "study_id": study_id,
                "gene_symbol": gene,
                "paired_case_count": len(deltas),
                "median_paired_tumor_minus_adjacent_log2_ratio": median(deltas) if deltas else None,
                "tumor_higher_fraction": (
                    sum(delta > 0 for delta in deltas) / len(deltas) if deltas else None
                ),
                "interpretation": (
                    "Within-study paired effect; adjacent normal is patient-matched, "
                    "not healthy tissue."
                ),
            }
        )
    return summaries
