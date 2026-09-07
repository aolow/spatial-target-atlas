"""Shared evidence contract for measured and model-derived target evidence."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EvidenceOrigin(StrEnum):
    MEASURED = "measured"
    MODEL_DERIVED = "model_derived"


class Modality(StrEnum):
    MASS_SPECTROMETRY = "mass_spectrometry"
    IMAGING_MASS_SPECTROMETRY = "imaging_mass_spectrometry"
    IMMUNOHISTOCHEMISTRY = "immunohistochemistry"
    SPATIAL_TRANSCRIPTOMICS = "spatial_transcriptomics"
    TRANSCRIPTOMICS = "transcriptomics"
    FOUNDATION_MODEL = "foundation_model"


class SpatialScale(StrEnum):
    BODY = "body"
    TISSUE = "tissue"
    REGION = "region"
    CELL_TYPE = "cell_type"
    SUBCELLULAR = "subcellular"


class ProteinEvidenceRecord(BaseModel):
    gene_symbol: str
    ensembl_id: str | None = None
    uniprot_id: str | None = None
    source: str
    source_release: str
    retrieved_at: str | None = None
    evidence_origin: EvidenceOrigin
    modality: Modality
    spatial_scale: SpatialScale
    tissue: str | None = None
    cell_type: str | None = None
    anatomical_region: str | None = None
    subcellular_location: str | None = None
    value: float | None = None
    unit: str | None = None
    detection_state: str = "measured"
    donor_count: int | None = Field(default=None, ge=0)
    sample_count: int | None = Field(default=None, ge=0)
    sample_id: str | None = None
    replicate: str | None = None
    sex: str | None = None
    healthy_status: str | None = None
    citation_url: str
    source_url: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AtlasSpec(BaseModel):
    name: str
    genes: list[str] = Field(min_length=1)
    tissues: list[str] = Field(default_factory=list)
    hpa_release: str = "25.1"
