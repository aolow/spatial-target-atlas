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
        hpa: HPAClient,
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
        ensembl_payload_hash: str | None = None
        ensembl_url: str | None = None
        if match:
            ensembl_id = match.group(1).upper()
        else:
            ensembl_url = (
                f"{ENSEMBL_REST}/lookup/symbol/homo_sapiens/{quote(target, safe='')}"
            )
            response = self.client.get(
                ensembl_url,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            )
            if response.status_code == 404:
                raise ValueError(f"Human gene symbol not found in Ensembl: {target}") from None
            response.raise_for_status()
            ensembl_payload_hash = hashlib.sha256(response.content).hexdigest()
            payload = response.json()
            ensembl_id = str(payload.get("id") or "")
            object_type = str(payload.get("object_type") or "")
            if not _ENSEMBL_GENE.fullmatch(ensembl_id) or object_type.casefold() != "gene":
                raise ValueError(
                    f"Ensembl symbol lookup did not resolve {target!r} to one human gene."
                )
            ensembl_id = ensembl_id.upper()

        gene_symbol, uniprot_id = self.hpa.resolve_uniprot(ensembl_id)
        hpa_url = f"{self.hpa.base_url}/{ensembl_id}.json"
        hashes = []
        urls = []
        sources = []
        if ensembl_url is not None:
            urls.append(ensembl_url)
            sources.append("Ensembl REST")
        if ensembl_payload_hash is not None:
            hashes.append(ensembl_payload_hash)
        urls.append(hpa_url)
        sources.append("Human Protein Atlas")
        hpa_hash = self.hpa.payload_hashes.get(hpa_url)
        if hpa_hash:
            hashes.append(hpa_hash)

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
