"""Resolve human gene symbols and Ensembl IDs into auditable target identities."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from urllib.parse import quote

import httpx

from .models import TargetIdentityRecord
from .sources.hpa import HPAClient

ENSEMBL_REST = "https://rest.ensembl.org"
_ENSEMBL_GENE = re.compile(r"^(ENSG\d+)(?:\.\d+)?$", re.IGNORECASE)


class TargetResolver:
    """Resolve configured targets without guessing ambiguous identifiers."""

    def __init__(
        self,
        hpa: HPAClient | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.hpa = hpa
        self.client = client or httpx.Client(timeout=30, follow_redirects=True)

    def resolve(self, targets: list[str]) -> list[TargetIdentityRecord]:
        resolved = [self._resolve_one(target.strip()) for target in targets]
        by_ensembl: dict[str, str] = {}
        for identity in resolved:
            previous = by_ensembl.get(identity.ensembl_id)
            if previous is not None:
                raise ValueError(
                    "Targets resolve to the same Ensembl gene: "
                    f"{previous!r} and {identity.input_id!r} -> {identity.ensembl_id}"
                )
            by_ensembl[identity.ensembl_id] = identity.input_id
        return resolved

    def _resolve_one(self, target: str) -> TargetIdentityRecord:
        if not target:
            raise ValueError("Target identifiers must be non-empty.")

        match = _ENSEMBL_GENE.fullmatch(target)
        hashes: list[str] = []
        urls: list[str] = []
        sources: list[str] = []
        gene_symbol: str | None = None
        if match:
            ensembl_id = match.group(1).upper()
            if self.hpa is None:
                payload, url, digest = self._ensembl_lookup_id(ensembl_id)
                gene_symbol = str(payload.get("display_name") or "") or None
                urls.append(url)
                hashes.append(digest)
                sources.append("Ensembl REST")
        else:
            payload, url, digest = self._ensembl_lookup_symbol(target)
            ensembl_id = str(payload.get("id") or "").upper()
            gene_symbol = str(payload.get("display_name") or "") or target
            urls.append(url)
            hashes.append(digest)
            sources.append("Ensembl REST")

        uniprot_id: str | None = None
        if self.hpa is not None:
            gene_symbol, uniprot_id = self.hpa.resolve_uniprot(ensembl_id)
            hpa_url = f"{self.hpa.base_url}/{ensembl_id}.json"
            urls.append(hpa_url)
            sources.append("Human Protein Atlas")
            hpa_hash = self.hpa.payload_hashes.get(hpa_url)
            if hpa_hash:
                hashes.append(hpa_hash)
        if not gene_symbol:
            raise ValueError(f"Could not resolve a gene symbol for {target!r}.")

        return TargetIdentityRecord(
            input_id=target,
            ensembl_id=ensembl_id,
            gene_symbol=gene_symbol,
            uniprot_id=uniprot_id,
            resolution_sources=sources,
            source_urls=urls,
            source_payload_sha256=hashes,
            retrieved_at=datetime.now(UTC).isoformat(),
        )

    def _ensembl_lookup_symbol(
        self, symbol: str
    ) -> tuple[dict[str, object], str, str]:
        url = f"{ENSEMBL_REST}/lookup/symbol/homo_sapiens/{quote(symbol, safe='')}"
        return self._ensembl_request(url, f"Human gene symbol not found in Ensembl: {symbol}")

    def _ensembl_lookup_id(
        self, ensembl_id: str
    ) -> tuple[dict[str, object], str, str]:
        url = f"{ENSEMBL_REST}/lookup/id/{quote(ensembl_id, safe='')}"
        return self._ensembl_request(url, f"Ensembl gene not found: {ensembl_id}")

    def _ensembl_request(
        self, url: str, not_found: str
    ) -> tuple[dict[str, object], str, str]:
        response = self.client.get(
            url,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        if response.status_code == 404:
            raise ValueError(not_found) from None
        response.raise_for_status()
        raw_payload = response.json()
        if not isinstance(raw_payload, dict):
            raise ValueError("Ensembl lookup returned an invalid response.")
        payload: dict[str, object] = raw_payload
        ensembl_id = str(payload.get("id") or "")
        object_type = str(payload.get("object_type") or "")
        if not _ENSEMBL_GENE.fullmatch(ensembl_id) or object_type.casefold() != "gene":
            raise ValueError("Ensembl lookup did not resolve to one human gene.")
        return payload, url, hashlib.sha256(response.content).hexdigest()
