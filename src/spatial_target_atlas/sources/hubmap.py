"""HuBMAP spatial-dataset registry connector."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

import httpx

from ..models import SpatialDatasetRecord

API_ROOT = "https://search.api.hubmapconsortium.org/v3/param-search/datasets"
API_DOCS = "https://docs.hubmapconsortium.org/apis.html"
SPATIAL_ASSAYS = (
    "Visium (no probes)",
    "Visium (with probes)",
    "Visium HD",
    "Xenium",
    "MERFISH",
    "CosMx Transcriptomics",
    "CosMx Proteomics",
    "MALDI",
    "MIBI",
    "2D Imaging Mass Cytometry",
    "CODEX",
    "PhenoCycler",
    "PhenoCycler [DeepCell + SPRM]",
)


class HuBMAPClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=120, follow_redirects=True)

    def fetch_spatial_registry(self, organ_codes: list[str]) -> list[SpatialDatasetRecord]:
        retrieved_at = datetime.now(UTC).isoformat()
        records = []
        for organ in organ_codes:
            for assay in SPATIAL_ASSAYS:
                rows, payload_hashes = self._datasets(organ, assay)
                for row in rows:
                    records.append(self._record(row, organ, assay, retrieved_at, payload_hashes))
        return records

    @staticmethod
    def _record(
        row: dict[str, Any],
        organ: str,
        assay: str,
        retrieved_at: str,
        payload_hashes: list[str],
    ) -> SpatialDatasetRecord:
        dataset_uuid = str(row["uuid"])
        origins = row.get("origin_samples") or []
        protocols = {
            str(item["protocol_url"])
            for item in origins
            if item.get("protocol_url")
        }
        if row.get("protocol_url"):
            protocols.add(str(row["protocol_url"]))
        return SpatialDatasetRecord(
            dataset_id=str(row["hubmap_id"]),
            dataset_uuid=dataset_uuid,
            source="HuBMAP",
            source_release="Search API v3 live",
            retrieved_at=retrieved_at,
            source_payload_sha256=payload_hashes,
            assay=assay,
            organ=organ,
            donor_id=str((row.get("donor") or {}).get("uuid") or "") or None,
            access_level=str(row.get("data_access_level") or "unknown"),
            status=str(row.get("status") or "unknown"),
            citation_url=str(row.get("doi_url") or API_DOCS),
            source_url="https://portal.hubmapconsortium.org/browse/dataset/" + dataset_uuid,
            protocol_urls=sorted(protocols),
            donor_covariates=_donor_covariates(row.get("donor") or {}),
            metadata={
                "group_name": row.get("group_name"),
                "description": row.get("description"),
                "registered_doi": row.get("registered_doi"),
                "api_documentation": API_DOCS,
            },
        )

    def _datasets(self, organ: str, assay: str) -> tuple[list[dict[str, Any]], list[str]]:
        response = self.client.get(
            API_ROOT,
            params={
                "status": "Published",
                "origin_samples.organ": organ,
                "dataset_type": assay,
            },
        )
        response.raise_for_status()
        hashes = [hashlib.sha256(response.content).hexdigest()]
        if response.text.strip().startswith("https://"):
            response = self.client.get(response.text.strip())
            response.raise_for_status()
            hashes.append(hashlib.sha256(response.content).hexdigest())
        payload: list[dict[str, Any]] = response.json()
        return payload, hashes


def _donor_covariates(donor: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for group, values in (donor.get("metadata") or {}).items():
        if not group.endswith("_donor_data") or not isinstance(values, list):
            continue
        for item in values:
            name = str(item.get("grouping_concept_preferred_term") or item.get("preferred_term"))
            result.setdefault(name, []).append(
                {
                    "value": item.get("data_value"),
                    "units": item.get("units") or None,
                    "ontology": item.get("sab"),
                    "code": item.get("code"),
                }
            )
    return result
