"""ProteomicsDB tissue-level mass-spectrometry connector."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from ..models import EvidenceOrigin, Modality, ProteinEvidenceRecord, SpatialScale

API_ROOT = "https://www.proteomicsdb.org/proteomicsdb/logic/api"
API_DOCS = "https://www.proteomicsdb.org/api"


class ProteomicsDBClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=60, follow_redirects=True)

    def fetch(
        self,
        gene_symbol: str,
        ensembl_id: str,
        uniprot_id: str,
        tissues: list[str],
    ) -> list[ProteinEvidenceRecord]:
        endpoint = (
            f"{API_ROOT}/proteinexpression.xsodata/InputParams(PROTEINFILTER='{uniprot_id}',"
            "MS_LEVEL=1,TISSUE_ID_SELECTION='',TISSUE_CATEGORY_SELECTION='tissue',"
            "SCOPE_SELECTION=1,GROUP_BY_TISSUE=1,CALCULATION_METHOD=0,EXP_ID=-1)/Results"
        )
        response = self.client.get(endpoint, params={"$format": "json"})
        response.raise_for_status()
        rows: list[dict[str, Any]] = response.json()["d"]["results"]
        selected = {tissue.casefold() for tissue in tissues}
        records = []
        for row in rows:
            tissue = str(row["TISSUE_NAME"])
            if selected and tissue.casefold() not in selected:
                continue
            value = _float(row.get("NORMALIZED_INTENSITY"))
            records.append(
                ProteinEvidenceRecord(
                    gene_symbol=gene_symbol,
                    ensembl_id=ensembl_id,
                    uniprot_id=uniprot_id,
                    source="ProteomicsDB",
                    source_release="API v1.1 live",
                    retrieved_at=datetime.now(UTC).isoformat(),
                    evidence_origin=EvidenceOrigin.MEASURED,
                    modality=Modality.MASS_SPECTROMETRY,
                    spatial_scale=SpatialScale.TISSUE,
                    tissue=tissue,
                    anatomical_region=str(row.get("TISSUE_ID") or "") or None,
                    value=value,
                    unit="ProteomicsDB normalized intensity",
                    detection_state=(
                        "detected" if value is not None and value > 0 else "not_detected"
                    ),
                    sample_count=int(row.get("SAMPLES") or 0),
                    citation_url=API_DOCS,
                    source_url=str(response.url),
                    metadata={
                        "unnormalized_intensity": _float(row.get("UNNORMALIZED_INTENSITY")),
                        "minimum_normalized_intensity": _float(row.get("MIN_NORMALIZED_INTENSITY")),
                        "maximum_normalized_intensity": _float(row.get("MAX_NORMALIZED_INTENSITY")),
                        "aggregation": "grouped_by_tissue",
                        "calculation_method": "iBAQ",
                    },
                )
            )
        return records


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
