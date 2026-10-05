"""Model-derived target context records kept separate from measured evidence."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from .models import ModelDerivedEvidenceRecord, TargetIdentityRecord

PINNACLE_URL = "https://github.com/mims-harvard/PINNACLE"
PINNACLE_PAPER = "https://doi.org/10.1038/s41592-024-02341-3"


def import_pinnacle_contexts(
    labels_path: Path,
    identities_path: Path,
    embedding_path: Path | None = None,
) -> tuple[list[ModelDerivedEvidenceRecord], dict[str, Any]]:
    identities = _load_identities(identities_path)
    labels = _load_pinnacle_labels(labels_path)
    contexts = labels.get("Cell Type")
    names = labels.get("Name")
    if not isinstance(contexts, list) or not isinstance(names, list):
        raise ValueError("PINNACLE labels must contain list fields 'Cell Type' and 'Name'.")
    if len(contexts) != len(names):
        raise ValueError("PINNACLE label arrays have different lengths.")

    targets: dict[str, TargetIdentityRecord] = {}
    for identity in identities:
        targets[identity.gene_symbol.casefold()] = identity
        if identity.uniprot_id:
            targets[identity.uniprot_id.casefold()] = identity

    label_hash = _sha256(labels_path)
    embedding_hash = _sha256(embedding_path) if embedding_path is not None else None
    records: list[ModelDerivedEvidenceRecord] = []
    matched_targets: set[str] = set()
    seen: set[tuple[str, str]] = set()
    for raw_context, raw_name in zip(contexts, names, strict=True):
        context = str(raw_context)
        name = str(raw_name)
        if context.startswith("CCI_") or context.startswith("BTO"):
            continue
        identity = targets.get(name.casefold())
        if identity is None:
            continue
        key = (identity.ensembl_id, context)
        if key in seen:
            continue
        seen.add(key)
        matched_targets.add(identity.gene_symbol)
        records.append(
            ModelDerivedEvidenceRecord(
                model_name="PINNACLE",
                model_version="published_pretrained_representation",
                evidence_origin="model_derived",
                evidence_kind="contextual_representation_available",
                gene_symbol=identity.gene_symbol,
                ensembl_id=identity.ensembl_id,
                uniprot_id=identity.uniprot_id,
                context_type="cell_type",
                context=context,
                tissue=None,
                score_name=None,
                score=None,
                representation_ref=(
                    embedding_path.name if embedding_path is not None else None
                ),
                source_url=PINNACLE_URL,
                citation_url=PINNACLE_PAPER,
                source_payload_sha256=[
                    digest for digest in (label_hash, embedding_hash) if digest is not None
                ],
                note=(
                    "A PINNACLE context-specific protein representation is available for "
                    "this target and cell-type label. Availability is not a therapeutic "
                    "target score, abundance measurement, or evidence of causal relevance."
                ),
            )
        )

    requested = sorted({identity.gene_symbol for identity in identities})
    summary: dict[str, Any] = {
        "model": "PINNACLE",
        "evidence_kind": "contextual_representation_available",
        "requested_targets": requested,
        "matched_targets": sorted(matched_targets),
        "unmatched_targets": sorted(set(requested) - matched_targets),
        "representation_records": len(records),
        "cell_type_contexts": len({record.context for record in records}),
        "labels_sha256": label_hash,
        "embedding_sha256": embedding_hash,
        "interpretation": (
            "Records indicate representation coverage only. No embedding geometry, "
            "downstream prediction, or target prioritization score is inferred."
        ),
    }
    return records, summary


def load_model_evidence(path: Path) -> list[ModelDerivedEvidenceRecord]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Model evidence file must contain a JSON list.")
    return [ModelDerivedEvidenceRecord.model_validate(item) for item in raw]


def _load_identities(path: Path) -> list[TargetIdentityRecord]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("target_identities.json must contain a list.")
    return [TargetIdentityRecord.model_validate(item) for item in raw]


def _load_pinnacle_labels(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        raw = ast.literal_eval(text)
    if not isinstance(raw, dict):
        raise ValueError("PINNACLE labels file must contain a dictionary.")
    return {str(key): value for key, value in raw.items()}


def _sha256(path: Path | None) -> str | None:
    if path is None:
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
