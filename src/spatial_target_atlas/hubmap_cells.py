"""Per-cell HuBMAP protein measurements through the public Cells API."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import UTC, datetime
from statistics import mean, median
from typing import Any

import httpx

from .models import (
    HuBMAPCellMeasurementRecord,
    SpatialDatasetRecord,
    TargetIdentityRecord,
)

CELLS_API = "https://cells.api.hubmapconsortium.org/api"


class HuBMAPCellsError(RuntimeError):
    pass


class HuBMAPCellsClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=120, follow_redirects=True)
        self.payload_hashes: set[str] = set()

    def fetch_target(
        self,
        dataset: SpatialDatasetRecord,
        identity: TargetIdentityRecord,
        protein_id: str,
        *,
        page_size: int = 5000,
        max_cells: int = 200000,
    ) -> tuple[list[HuBMAPCellMeasurementRecord], dict[str, Any]]:
        if page_size < 1 or page_size > 10000:
            raise ValueError("page_size must be between 1 and 10000.")
        if max_cells < 1:
            raise ValueError("max_cells must be positive.")

        base_status: dict[str, Any] = {
            "dataset_id": dataset.dataset_id,
            "dataset_uuid": dataset.dataset_uuid,
            "assay": dataset.assay,
            "gene_symbol": identity.gene_symbol,
            "protein_id": protein_id,
        }
        try:
            handle = self._query_handle(dataset.dataset_uuid)
            cell_count = self._count(handle)
            if cell_count > max_cells:
                return [], {
                    **base_status,
                    "status": "guard_exceeded",
                    "cell_count": cell_count,
                    "records": 0,
                    "message": (
                        f"Dataset has {cell_count} indexed cells, above the local guard "
                        f"of {max_cells}. Raise --max-cells-per-dataset explicitly."
                    ),
                }
            records: list[HuBMAPCellMeasurementRecord] = []
            retrieved_at = datetime.now(UTC).isoformat()
            for offset in range(0, cell_count, page_size):
                rows = self._cell_page(handle, protein_id, page_size, offset)
                for row in rows:
                    values = row.get("values")
                    if not isinstance(values, dict) or protein_id not in values:
                        continue
                    value = _float(values.get(protein_id))
                    if value is None:
                        continue
                    records.append(
                        HuBMAPCellMeasurementRecord(
                            dataset_id=dataset.dataset_id,
                            dataset_uuid=dataset.dataset_uuid,
                            assay=dataset.assay,
                            organ=dataset.organ,
                            donor_id=dataset.donor_id,
                            cell_id=str(row.get("cell_id") or ""),
                            cell_type=_optional_text(row.get("cell_type")),
                            clusters=_string_list(row.get("clusters")),
                            modality=str(row.get("modality") or "codex"),
                            gene_symbol=identity.gene_symbol,
                            ensembl_id=identity.ensembl_id,
                            uniprot_id=identity.uniprot_id,
                            protein_id=protein_id,
                            value=value,
                            detection_state="detected" if value > 0 else "assayed_not_detected",
                            source="HuBMAP Cells API",
                            source_release="live",
                            source_url=CELLS_API,
                            retrieved_at=retrieved_at,
                            unit="source_scale_intensity",
                        )
                    )
            return records, {
                **base_status,
                "status": "complete",
                "cell_count": cell_count,
                "records": len(records),
                "message": (
                    "Per-cell source-scale values retrieved; no cross-dataset "
                    "normalization or comparability is implied."
                ),
            }
        except (HuBMAPCellsError, httpx.HTTPError) as exc:
            return [], {
                **base_status,
                "status": "unavailable",
                "cell_count": None,
                "records": 0,
                "message": str(exc),
            }

    def _query_handle(self, dataset_uuid: str) -> str:
        payload = self._post(
            "cell/",
            {"input_type": "dataset", "input_set": dataset_uuid},
        )
        try:
            return str(payload["results"][0]["query_handle"])
        except (KeyError, IndexError, TypeError):
            raise HuBMAPCellsError(
                "HuBMAP Cells API did not return a cell query handle for this dataset."
            ) from None

    def _count(self, handle: str) -> int:
        payload = self._post("count/", {"key": handle, "set_type": "cell"})
        try:
            return int(payload["results"][0]["count"])
        except (KeyError, IndexError, TypeError, ValueError):
            raise HuBMAPCellsError(
                "HuBMAP Cells API did not return a valid cell count."
            ) from None

    def _cell_page(
        self,
        handle: str,
        protein_id: str,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        payload = self._post(
            "celldetailevaluation/",
            {
                "key": handle,
                "set_type": "cell",
                "limit": str(limit),
                "offset": str(offset),
                "values_included": protein_id,
            },
        )
        rows = payload.get("results") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise HuBMAPCellsError(
                "HuBMAP Cells API returned an invalid detailed cell response."
            )
        return [row for row in rows if isinstance(row, dict)]

    def _post(self, path: str, data: dict[str, str]) -> Any:
        response = self.client.post(f"{CELLS_API}/{path}", data=data)
        self.payload_hashes.add(hashlib.sha256(response.content).hexdigest())
        if response.status_code >= 400:
            raise HuBMAPCellsError(
                f"HuBMAP Cells API returned HTTP {response.status_code} for {path}"
            )
        try:
            return response.json()
        except ValueError:
            raise HuBMAPCellsError(
                f"HuBMAP Cells API returned invalid JSON for {path}"
            ) from None


def summarize_cell_measurements(
    records: list[HuBMAPCellMeasurementRecord],
) -> list[dict[str, Any]]:
    grouped: dict[
        tuple[str, str, str, str | None],
        list[HuBMAPCellMeasurementRecord],
    ] = defaultdict(list)
    for record in records:
        grouped[
            (
                record.dataset_uuid,
                record.gene_symbol,
                record.protein_id,
                record.cell_type,
            )
        ].append(record)

    summaries: list[dict[str, Any]] = []
    for (dataset_uuid, gene, protein_id, cell_type), subset in sorted(
        grouped.items(),
        key=lambda item: (
            item[0][0],
            item[0][1],
            item[0][2],
            item[0][3] or "",
        ),
    ):
        values = [record.value for record in subset]
        positive = sum(value > 0 for value in values)
        summaries.append(
            {
                "dataset_uuid": dataset_uuid,
                "dataset_id": subset[0].dataset_id,
                "assay": subset[0].assay,
                "organ": subset[0].organ,
                "donor_id": subset[0].donor_id,
                "gene_symbol": gene,
                "ensembl_id": subset[0].ensembl_id,
                "uniprot_id": subset[0].uniprot_id,
                "protein_id": protein_id,
                "cell_type": cell_type,
                "cell_count": len(values),
                "positive_cell_count": positive,
                "positive_cell_fraction": positive / len(values),
                "mean_source_scale_intensity": mean(values),
                "median_source_scale_intensity": median(values),
                "unit": "source_scale_intensity",
                "interpretation": (
                    "Within-dataset descriptive summary only; intensity values are "
                    "not normalized for comparison across datasets."
                ),
            }
        )
    return summaries


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value:
        return [item for item in value.split(",") if item]
    return []
