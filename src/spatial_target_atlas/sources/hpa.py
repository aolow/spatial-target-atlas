"""Human Protein Atlas v25.1 measured-protein connector."""

from __future__ import annotations

from typing import Any

import httpx

from ..models import EvidenceOrigin, Modality, ProteinEvidenceRecord, SpatialScale

HPA_RELEASE = "25.1"
HPA_CITATION = "https://www.proteinatlas.org/about/licence"


class HPAClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=60, follow_redirects=True)

    def fetch_gene(self, ensembl_id: str, tissues: list[str]) -> list[ProteinEvidenceRecord]:
        url = f"https://www.proteinatlas.org/{ensembl_id}.json"
        response = self.client.get(url)
        response.raise_for_status()
        return self.normalize(response.json(), url, tissues)

    @staticmethod
    def normalize(
        payload: dict[str, Any], source_url: str, tissues: list[str]
    ) -> list[ProteinEvidenceRecord]:
        gene = str(payload["Gene"])
        ensembl = str(payload["Ensembl"])
        uniprot = _first(payload.get("Uniprot"))
        selected = {value.casefold() for value in tissues}
        common: dict[str, Any] = {
            "gene_symbol": gene,
            "ensembl_id": ensembl,
            "uniprot_id": uniprot,
            "source": "Human Protein Atlas",
            "source_release": HPA_RELEASE,
            "evidence_origin": EvidenceOrigin.MEASURED,
            "citation_url": HPA_CITATION,
            "source_url": source_url,
        }
        records = []
        for tissue, value in _measurements(payload.get("Protein tissue specific Intensity")):
            if selected and tissue.casefold() not in selected:
                continue
            records.append(
                ProteinEvidenceRecord(
                    **common,
                    modality=Modality.MASS_SPECTROMETRY,
                    spatial_scale=SpatialScale.TISSUE,
                    tissue=tissue,
                    value=value,
                    unit="HPA MS intensity",
                    detection_state="specific_expression",
                    metadata={"selection": "HPA gene-level specificity summary"},
                )
            )
        for cell_type, value in _measurements(payload.get("Protein cell type specific Intensity")):
            records.append(
                ProteinEvidenceRecord(
                    **common,
                    modality=Modality.MASS_SPECTROMETRY,
                    spatial_scale=SpatialScale.CELL_TYPE,
                    cell_type=cell_type,
                    value=value,
                    unit="HPA DVP intensity",
                    detection_state="specific_expression",
                    donor_count=1,
                    sex="female",
                    healthy_status="healthy donor",
                    metadata={
                        "platform": "Deep Visual Proteomics",
                        "selection": "HPA gene-level specificity summary",
                    },
                )
            )
        for location in _as_list(payload.get("Subcellular main location")):
            records.append(
                ProteinEvidenceRecord(
                    **common,
                    modality=Modality.IMMUNOHISTOCHEMISTRY,
                    spatial_scale=SpatialScale.SUBCELLULAR,
                    subcellular_location=str(location),
                    metadata={"reliability": payload.get("Reliability (IF)")},
                )
            )
        return records


def _first(value: Any) -> str | None:
    values = _as_list(value)
    return str(values[0]) if values else None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _named_value(item: Any) -> tuple[str, float | None]:
    if isinstance(item, dict):
        name = item.get("Cell type") or item.get("Tissue") or item.get("name")
        value: Any = item.get("Intensity") if "Intensity" in item else item.get("value")
        return str(name), float(value) if value is not None and value != "" else None
    if isinstance(item, str) and ":" in item:
        name, value = item.rsplit(":", 1)
        try:
            return name.strip(), float(value.strip())
        except ValueError:
            return item, None
    return str(item), None


def _measurements(value: Any) -> list[tuple[str, float | None]]:
    if isinstance(value, dict):
        return [(str(name), float(intensity)) for name, intensity in value.items()]
    return [_named_value(item) for item in _as_list(value)]
