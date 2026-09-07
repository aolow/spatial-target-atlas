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
    IMMUNOFLUORESCENCE = "immunofluorescence"
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
    source_payload_sha256: list[str] = Field(default_factory=list)
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
    specimen_context: str | None = None
    case_id: str | None = None
    citation_url: str
    source_url: str
    supporting_source_urls: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AtlasSpec(BaseModel):
    name: str
    genes: list[str] = Field(min_length=1)
    tissues: list[str] = Field(default_factory=list)
    hpa_release: str = "25.1"
    pdc_studies: list[str] = Field(default_factory=list)
    hubmap_organs: list[str] = Field(default_factory=list)


class SpatialDatasetRecord(BaseModel):
    dataset_id: str
    dataset_uuid: str
    source: str
    source_release: str
    retrieved_at: str
    source_payload_sha256: list[str] = Field(default_factory=list)
    assay: str
    organ: str
    donor_id: str | None = None
    access_level: str
    status: str
    citation_url: str
    source_url: str
    protocol_urls: list[str] = Field(default_factory=list)
    donor_covariates: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SpatialTargetCoverageRecord(BaseModel):
    dataset_id: str
    dataset_uuid: str
    source: str
    gene_symbol: str
    ensembl_id: str
    uniprot_id: str | None = None
    coverage_state: str
    matched_channels: list[dict[str, Any]] = Field(default_factory=list)
    panel_size: int | None = Field(default=None, ge=0)
    panel_url: str | None = None
    panel_sha256: str | None = None
    retrieved_at: str
    note: str


class SpatialTranscriptomicDatasetRecord(BaseModel):
    dataset_id: str
    source: str
    source_release: str
    dataset_title: str
    collection_id: str
    collection_name: str
    collection_doi: str | None = None
    citation: str
    spot_count: int = Field(ge=0)
    assays: list[str]
    donor_contexts: list[dict[str, Any]]


class SpatialTranscriptomicSummaryRecord(BaseModel):
    dataset_id: str
    source: str
    source_release: str
    gene_symbol: str
    ensembl_id: str
    assay: str
    tissue: str
    disease: str
    donor_id: str
    development_stage: str
    sex: str
    self_reported_ethnicity: str
    cell_type: str
    is_primary_data: bool
    spot_count: int = Field(ge=0)
    positive_spot_count: int = Field(ge=0)
    positive_spot_fraction: float = Field(ge=0, le=1)
    mean_raw_count: float = Field(ge=0)
    detection_state: str
    reference_context: str
    unit: str = "raw_UMI_or_read_count_per_spot"
    note: str
