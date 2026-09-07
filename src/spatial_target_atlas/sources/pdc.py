"""NCI Proteomic Data Commons quantitative proteomics connector."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import httpx

from ..models import EvidenceOrigin, Modality, ProteinEvidenceRecord, SpatialScale

API_URL = "https://pdc.cancer.gov/graphql"
API_DOCS = "https://pdc.cancer.gov/pdc-docs/api-documentation"


class PDCClient:
    """Fetch target-level aliquot values with authoritative biospecimen labels."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=120, follow_redirects=True)
        self.payload_hashes: list[str] = []

    def fetch(
        self,
        study_id: str,
        genes: Mapping[str, tuple[str | None, str | None]],
    ) -> list[ProteinEvidenceRecord]:
        self.payload_hashes = []
        study_rows = self._query(
            """query($id: String!){ study(pdc_study_id:$id, acceptDUA:true){
              study_id pdc_study_id study_name analytical_fraction experiment_type
              disease_type primary_site
            }}""",
            {"id": study_id},
        )["study"]
        if not study_rows:
            raise ValueError(f"PDC study not found: {study_id}")
        study = study_rows[0]
        biospecimens = self._query(
            """query($id: String!){ biospecimenPerStudy(pdc_study_id:$id, acceptDUA:true){
              case_id case_submitter_id case_is_ref sample_id sample_submitter_id
              sample_type aliquot_id
              aliquot_submitter_id disease_type primary_site
            }}""",
            {"id": study_id},
        )["biospecimenPerStudy"]
        matrix = self._query(
            """query($id: String!){ quantDataMatrix(
              pdc_study_id:$id, data_type:"log2_ratio", acceptDUA:true
            ) }""",
            {"id": study_id},
        )["quantDataMatrix"]
        return self._records(study, biospecimens, matrix, genes)

    def _query(self, query: str, variables: dict[str, Any]) -> Any:
        response = self.client.post(API_URL, json={"query": query, "variables": variables})
        response.raise_for_status()
        self.payload_hashes.append(hashlib.sha256(response.content).hexdigest())
        payload = response.json()
        if payload.get("errors"):
            raise ValueError(f"PDC GraphQL error: {payload['errors'][0]['message']}")
        return payload["data"]

    def _records(
        self,
        study: dict[str, Any],
        biospecimens: list[dict[str, Any]],
        matrix: list[list[Any]],
        genes: Mapping[str, tuple[str | None, str | None]],
    ) -> list[ProteinEvidenceRecord]:
        if not matrix:
            return []
        sample_by_id = {
            str(row["aliquot_id"]): row for row in biospecimens if row.get("aliquot_id")
        }
        samples_by_submitter: dict[str, list[dict[str, Any]]] = {}
        for biospecimen in biospecimens:
            submitter = biospecimen.get("aliquot_submitter_id")
            if submitter:
                samples_by_submitter.setdefault(str(submitter), []).append(biospecimen)
        headers = [str(value) for value in matrix[0][1:]]
        retrieved_at = datetime.now(UTC).isoformat()
        records: list[ProteinEvidenceRecord] = []
        for row in matrix[1:]:
            gene_symbol = str(row[0])
            if gene_symbol not in genes:
                continue
            ensembl_id, uniprot_id = genes[gene_symbol]
            for header, raw_value in zip(headers, row[1:], strict=True):
                matrix_aliquot_id, separator, aliquot_submitter_id = header.partition(":")
                if not separator:
                    matrix_aliquot_id = header
                    aliquot_submitter_id = header
                sample: dict[str, Any] | None = sample_by_id.get(matrix_aliquot_id)
                join_key = "aliquot_id"
                if sample is None:
                    sample = _unique_submitter_match(
                        samples_by_submitter.get(aliquot_submitter_id, [])
                    )
                    join_key = "aliquot_submitter_id"
                value = _float(raw_value)
                if sample is None or value is None or _is_reference(sample):
                    continue
                sample_type = str(sample.get("sample_type") or "Unknown")
                context = _specimen_context(sample_type)
                records.append(
                    ProteinEvidenceRecord(
                        gene_symbol=gene_symbol,
                        ensembl_id=ensembl_id,
                        uniprot_id=uniprot_id,
                        source="NCI Proteomic Data Commons",
                        source_release=str(study["pdc_study_id"]),
                        retrieved_at=retrieved_at,
                        source_payload_sha256=sorted(set(self.payload_hashes)),
                        evidence_origin=EvidenceOrigin.MEASURED,
                        modality=Modality.MASS_SPECTROMETRY,
                        spatial_scale=SpatialScale.TISSUE,
                        tissue=str(sample.get("primary_site") or study.get("primary_site") or ""),
                        value=value,
                        unit="log2 ratio to pooled reference",
                        detection_state="quantified",
                        sample_count=1,
                        sample_id=matrix_aliquot_id,
                        healthy_status=_healthy_status(context),
                        specimen_context=context,
                        case_id=str(sample.get("case_id") or "") or None,
                        citation_url=f"https://pdc.cancer.gov/pdc/study/{study['pdc_study_id']}",
                        source_url=f"https://pdc.cancer.gov/pdc/study/{study['pdc_study_id']}",
                        supporting_source_urls=[API_URL],
                        metadata={
                            "study_name": study.get("study_name"),
                            "study_uuid": study.get("study_id"),
                            "sample_id": sample.get("sample_id"),
                            "sample_submitter_id": sample.get("sample_submitter_id"),
                            "aliquot_submitter_id": aliquot_submitter_id,
                            "biospecimen_aliquot_id": sample.get("aliquot_id"),
                            "matrix_aliquot_id": matrix_aliquot_id,
                            "biospecimen_join_key": join_key,
                            "case_submitter_id": sample.get("case_submitter_id"),
                            "sample_type": sample_type,
                            "disease_type": sample.get("disease_type"),
                            "analytical_fraction": study.get("analytical_fraction"),
                            "experiment_type": study.get("experiment_type"),
                            "comparison_scope": "within_study_only",
                            "api_documentation": API_DOCS,
                        },
                    )
                )
        return records


def _specimen_context(sample_type: str) -> str:
    normalized = sample_type.casefold()
    if "tumor" in normalized:
        return "tumor"
    if "normal" in normalized:
        return "adjacent_normal"
    return "other"


def _healthy_status(context: str) -> str:
    if context == "tumor":
        return "disease"
    if context == "adjacent_normal":
        return "not_healthy_reference"
    return "unknown"


def _unique_submitter_match(samples: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not samples:
        return None
    identities = {(row.get("case_id"), row.get("sample_id")) for row in samples}
    if len(identities) != 1:
        return None
    return samples[0]


def _is_reference(sample: dict[str, Any]) -> bool:
    if str(sample.get("case_is_ref") or "").casefold() == "yes":
        return True
    identifiers = " ".join(
        str(sample.get(field) or "")
        for field in ("case_submitter_id", "sample_submitter_id", "aliquot_submitter_id")
    ).casefold()
    return "internal reference" in identifiers or identifiers.endswith(" ir")


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
