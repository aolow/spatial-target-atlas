"""HuBMAP spatial-dataset registry connector."""

from __future__ import annotations

import csv
import hashlib
import io
from datetime import UTC, datetime
from typing import Any

import httpx

from ..models import SpatialDatasetRecord, SpatialTargetCoverageRecord

API_ROOT = "https://search.api.hubmapconsortium.org/v3/param-search/datasets"
API_DOCS = "https://docs.hubmapconsortium.org/apis.html"
PORTAL_SEARCH = "https://search.api.hubmapconsortium.org/v3/portal/search"
ASSETS_ROOT = "https://assets.hubmapconsortium.org"
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

    def fetch_target_coverage(
        self,
        datasets: list[SpatialDatasetRecord],
        identities: list[tuple[str, str, str | None]],
    ) -> list[SpatialTargetCoverageRecord]:
        """Audit whether configured targets were actually present in targeted panels."""
        retrieved_at = datetime.now(UTC).isoformat()
        results: list[SpatialTargetCoverageRecord] = []
        for dataset in datasets:
            parent_uuid = dataset.metadata.get("raw_ancestor_uuid")
            if not parent_uuid and dataset.assay == "PhenoCycler [DeepCell + SPRM]":
                parent_uuid = self._raw_parent_uuid(dataset.dataset_uuid)
            if not parent_uuid:
                continue
            panel = self._antibody_panel(str(parent_uuid))
            if panel is None:
                for ensembl_id, gene_symbol, uniprot_id in identities:
                    results.append(
                        _coverage_record(
                            dataset,
                            ensembl_id,
                            gene_symbol,
                            uniprot_id,
                            [],
                            None,
                            None,
                            retrieved_at,
                        )
                    )
                continue
            rows, url, digest = panel
            for ensembl_id, gene_symbol, uniprot_id in identities:
                matches = [row for row in rows if _panel_matches(row, gene_symbol, uniprot_id)]
                results.append(
                    _coverage_record(
                        dataset,
                        ensembl_id,
                        gene_symbol,
                        uniprot_id,
                        matches,
                        url,
                        digest,
                        retrieved_at,
                        panel_size=len(rows),
                    )
                )
        return results

    def _raw_parent_uuid(self, derived_uuid: str) -> str | None:
        response = self.client.post(
            PORTAL_SEARCH,
            json={
                "_source": ["ancestors"],
                "query": {"term": {"uuid.keyword": derived_uuid}},
                "size": 1,
            },
        )
        response.raise_for_status()
        hits = response.json().get("hits", {}).get("hits", [])
        if not hits:
            return None
        return _raw_ancestor_uuid(hits[0].get("_source", {}))

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
                "raw_ancestor_uuid": _raw_ancestor_uuid(row),
            },
        )

    def _antibody_panel(
        self, raw_uuid: str
    ) -> tuple[list[dict[str, str]], str, str] | None:
        response = self.client.post(
            PORTAL_SEARCH,
            json={
                "_source": ["metadata.antibodies_path"],
                "query": {"term": {"uuid.keyword": raw_uuid}},
                "size": 1,
            },
        )
        response.raise_for_status()
        hits = response.json().get("hits", {}).get("hits", [])
        if not hits:
            return None
        path = hits[0].get("_source", {}).get("metadata", {}).get("antibodies_path")
        if not path:
            return None
        url = f"{ASSETS_ROOT}/{raw_uuid}/{path}"
        response = self.client.get(
            url,
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://portal.hubmapconsortium.org/"},
        )
        response.raise_for_status()
        rows = list(csv.DictReader(io.StringIO(response.text), delimiter="\t"))
        return rows, url, hashlib.sha256(response.content).hexdigest()

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


def _raw_ancestor_uuid(row: dict[str, Any]) -> str | None:
    for ancestor in reversed(row.get("ancestors") or []):
        if ancestor.get("entity_type") == "Dataset" and ancestor.get("dataset_type"):
            return str(ancestor["uuid"])
    return None


def _panel_matches(row: dict[str, str], gene_symbol: str, uniprot_id: str | None) -> bool:
    channel = row.get("channel_id", "").strip().casefold().replace("-", "")
    symbol = gene_symbol.casefold().replace("-", "")
    accessions = {value.strip() for value in row.get("uniprot_accession_number", "").split(",")}
    return channel == symbol or bool(uniprot_id and uniprot_id in accessions)


def _coverage_record(
    dataset: SpatialDatasetRecord,
    ensembl_id: str,
    gene_symbol: str,
    uniprot_id: str | None,
    matches: list[dict[str, str]],
    panel_url: str | None,
    panel_sha256: str | None,
    retrieved_at: str,
    panel_size: int | None = None,
) -> SpatialTargetCoverageRecord:
    if panel_url is None:
        state = "unknown"
        note = "Panel metadata unavailable; no statement about target detection is possible."
    elif matches:
        state = "assayed"
        note = (
            "Target is represented in this targeted antibody panel; "
            "detection is not inferred here."
        )
    else:
        state = "not_assayed"
        note = (
            "Target is absent from this targeted antibody panel; "
            "this is not evidence of non-detection."
        )
    return SpatialTargetCoverageRecord(
        dataset_id=dataset.dataset_id,
        dataset_uuid=dataset.dataset_uuid,
        source=dataset.source,
        gene_symbol=gene_symbol,
        ensembl_id=ensembl_id,
        uniprot_id=uniprot_id,
        coverage_state=state,
        matched_channels=matches,
        panel_size=panel_size,
        panel_url=panel_url,
        panel_sha256=panel_sha256,
        retrieved_at=retrieved_at,
        note=note,
    )
