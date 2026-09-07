"""Human Protein Atlas v25.1 measured-protein connector."""

from __future__ import annotations

import csv
import hashlib
import io
import re
import zipfile
from datetime import UTC, datetime
from typing import Any

import httpx

from ..models import EvidenceOrigin, Modality, ProteinEvidenceRecord, SpatialScale

HPA_CITATION = "https://www.proteinatlas.org/humanproteome/tissue/method"
HPA_LICENSE = "https://www.proteinatlas.org/about/licence"


class HPAClient:
    def __init__(self, client: httpx.Client | None = None, release: str = "25.1") -> None:
        if re.fullmatch(r"[1-9][0-9]*(?:\.[0-9]+)?", release) is None:
            raise ValueError(f"Invalid HPA release: {release}")
        self.client = client or httpx.Client(timeout=60, follow_redirects=True)
        self.release = release
        self.base_url = f"https://v{release.split('.', 1)[0]}.proteinatlas.org"
        self.download_url = f"{self.base_url}/download/tsv"
        self.retrieved_at = datetime.now(UTC).isoformat()
        self.payload_hashes: dict[str, str] = {}

    def fetch_gene(self, ensembl_id: str, tissues: list[str]) -> list[ProteinEvidenceRecord]:
        url = f"{self.base_url}/{ensembl_id}.json"
        response = self.client.get(url)
        response.raise_for_status()
        self.payload_hashes[url] = hashlib.sha256(response.content).hexdigest()
        return self.normalize(response.json(), url, tissues)

    def fetch_complete(
        self, ensembl_ids: list[str], tissues: list[str]
    ) -> list[ProteinEvidenceRecord]:
        """Fetch complete DVP matched RNA/protein and sample-level tissue MS records."""
        selected_genes = set(ensembl_ids)
        selected_tissues = {tissue.casefold() for tissue in tissues}
        cell_tissues = {
            row["Cell type group"]: row["Tissue name"]
            for row in self._archive("dvp_cell_types.tsv.zip")
        }
        cell_types_url = f"{self.download_url}/dvp_cell_types.tsv.zip"
        records: list[ProteinEvidenceRecord] = []
        for row in self._archive("dvp_cell_type_group_data.tsv.zip"):
            if row["Gene"] not in selected_genes:
                continue
            cell_type = row["Cell type name"]
            tissue = cell_tissues.get(cell_type)
            if selected_tissues and (tissue is None or tissue.casefold() not in selected_tissues):
                continue
            common = self._row_common(row, "dvp_cell_type_group_data.tsv.zip")
            common["source_payload_sha256"].append(self.payload_hashes[cell_types_url])
            common["supporting_source_urls"] = [cell_types_url]
            protein_value = _float(row["Intensity"])
            rna_value = _float(row["Matched nCPM"])
            records.extend(
                [
                    ProteinEvidenceRecord(
                        **common,
                        modality=Modality.MASS_SPECTROMETRY,
                        spatial_scale=SpatialScale.CELL_TYPE,
                        tissue=tissue,
                        cell_type=cell_type,
                        value=protein_value,
                        unit="HPA DVP intensity",
                        detection_state=(
                            "detected" if protein_value is not None else "not_detected"
                        ),
                        donor_count=1,
                        sex="female",
                        healthy_status="healthy donor",
                        metadata={
                            "platform": "Deep Visual Proteomics",
                            "license_url": HPA_LICENSE,
                        },
                    ),
                    ProteinEvidenceRecord(
                        **common,
                        modality=Modality.TRANSCRIPTOMICS,
                        spatial_scale=SpatialScale.CELL_TYPE,
                        tissue=tissue,
                        cell_type=cell_type,
                        value=rna_value,
                        unit="matched nCPM",
                        detection_state=(
                            "detected"
                            if rna_value is not None and rna_value >= 1
                            else "not_detected"
                        ),
                        donor_count=1,
                        sex="female",
                        healthy_status="healthy donor",
                        metadata={
                            "paired_modality": "Deep Visual Proteomics",
                            "license_url": HPA_LICENSE,
                        },
                    ),
                ]
            )
        for row in self._archive("ms_tissue_sample_data.tsv.zip"):
            if row["Gene"] not in selected_genes:
                continue
            if selected_tissues and row["Tissue"].casefold() not in selected_tissues:
                continue
            intensity = _float(row["Intensity"])
            records.append(
                ProteinEvidenceRecord(
                    **self._row_common(row, "ms_tissue_sample_data.tsv.zip"),
                    modality=Modality.MASS_SPECTROMETRY,
                    spatial_scale=SpatialScale.TISSUE,
                    tissue=row["Tissue"],
                    value=intensity,
                    unit="HPA MS intensity",
                    detection_state=(
                        "detected" if intensity is not None and intensity > 0 else "not_detected"
                    ),
                    sample_id=row["sample_name"],
                    replicate=row["replicate_nr"],
                    sample_count=1,
                    donor_count=1,
                    sex="female",
                    healthy_status="healthy donor",
                    metadata={
                        "donor_scope": "single donor; three tissue replicates",
                        "license_url": HPA_LICENSE,
                    },
                )
            )
        return records

    def fetch_annotations(self, ensembl_id: str) -> list[ProteinEvidenceRecord]:
        return [
            record
            for record in self.fetch_gene(ensembl_id, [])
            if record.spatial_scale == SpatialScale.SUBCELLULAR
        ]

    def resolve_uniprot(self, ensembl_id: str) -> tuple[str, str | None]:
        url = f"{self.base_url}/{ensembl_id}.json"
        response = self.client.get(url)
        response.raise_for_status()
        self.payload_hashes[url] = hashlib.sha256(response.content).hexdigest()
        payload = response.json()
        return str(payload["Gene"]), _first(payload.get("Uniprot"))

    def _archive(self, name: str) -> list[dict[str, str]]:
        url = f"{self.download_url}/{name}"
        response = self.client.get(url)
        response.raise_for_status()
        self.payload_hashes[url] = hashlib.sha256(response.content).hexdigest()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            member = archive.namelist()[0]
            text = io.TextIOWrapper(archive.open(member), encoding="utf-8")
            return list(csv.DictReader(text, delimiter="\t"))

    def _row_common(self, row: dict[str, str], archive: str) -> dict[str, Any]:
        return {
            "gene_symbol": row["Gene name"],
            "ensembl_id": row["Gene"],
            "source": "Human Protein Atlas",
            "source_release": self.release,
            "retrieved_at": self.retrieved_at,
            "source_payload_sha256": [
                self.payload_hashes[f"{self.download_url}/{archive}"]
            ],
            "evidence_origin": EvidenceOrigin.MEASURED,
            "citation_url": HPA_CITATION,
            "source_url": f"{self.download_url}/{archive}",
        }

    def normalize(
        self, payload: dict[str, Any], source_url: str, tissues: list[str]
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
            "source_release": self.release,
            "retrieved_at": self.retrieved_at,
            "source_payload_sha256": (
                [self.payload_hashes[source_url]] if source_url in self.payload_hashes else []
            ),
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
                    metadata={
                        "license_url": HPA_LICENSE,
                        "selection": "HPA gene-level specificity summary",
                    },
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
                        "license_url": HPA_LICENSE,
                        "platform": "Deep Visual Proteomics",
                        "selection": "HPA gene-level specificity summary",
                    },
                )
            )
        for location in _as_list(payload.get("Subcellular main location")):
            records.append(
                ProteinEvidenceRecord(
                    **common,
                    modality=Modality.IMMUNOFLUORESCENCE,
                    spatial_scale=SpatialScale.SUBCELLULAR,
                    subcellular_location=str(location),
                    metadata={
                        "license_url": HPA_LICENSE,
                        "reliability": payload.get("Reliability (IF)"),
                        "assay": "indirect immunofluorescence and confocal microscopy",
                    },
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


def _float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None
