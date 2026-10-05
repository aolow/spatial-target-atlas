"""Import cohort definitions from Open Cohort Factory without a package dependency."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .models import CohortContextRecord, CohortReferencePanelRecord


def load_open_cohort_context(path: Path) -> CohortContextRecord:
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes)
    if not isinstance(raw, dict):
        raise ValueError("Open Cohort Factory manifest must be a JSON object.")

    specification = _object(raw.get("specification"), "specification")
    disease = _object(specification.get("disease_cohort"), "specification.disease_cohort")
    panels_raw = specification.get("reference_panels", [])
    samples_raw = raw.get("samples", [])
    warnings_raw = raw.get("warnings", [])

    if not isinstance(panels_raw, list):
        raise ValueError("specification.reference_panels must be a list.")
    if not isinstance(samples_raw, list):
        raise ValueError("samples must be a list.")
    if not isinstance(warnings_raw, list):
        raise ValueError("warnings must be a list.")

    panels = [
        CohortReferencePanelRecord(
            name=_text(panel, "name"),
            source=_text(panel, "source"),
            tissue=_text(panel, "tissue"),
            context=_text(panel, "context"),
            resolution=_text(panel, "resolution"),
            age=_optional_object(panel.get("age")),
            notes=_optional_text(panel.get("notes")),
        )
        for item in panels_raw
        if isinstance(item, dict)
        for panel in [{str(key): value for key, value in item.items()}]
    ]

    disease_donors = {
        str(sample.get("case_id"))
        for sample in samples_raw
        if isinstance(sample, dict)
        and sample.get("cohort_role") == "disease"
        and sample.get("case_id")
    }
    reference_donors: dict[str, set[str]] = {}
    for sample in samples_raw:
        if not isinstance(sample, dict) or sample.get("cohort_role") != "reference":
            continue
        cohort_name = str(sample.get("cohort_name") or "unnamed_reference")
        case_id = sample.get("case_id")
        if case_id:
            reference_donors.setdefault(cohort_name, set()).add(str(case_id))

    disease_population: dict[str, Any] = {
        "projects": _string_list(disease.get("projects")),
        "primary_sites": _string_list(disease.get("primary_sites")),
        "age": _optional_object(disease.get("age")),
        "sex_at_birth": _string_list(disease.get("sex_at_birth")),
        "sample_types": _string_list(disease.get("sample_types")),
        "materialized_donor_count": len(disease_donors),
    }
    return CohortContextRecord(
        source="open-cohort-factory",
        project_name=_text(specification, "name"),
        description=_optional_text(specification.get("description")),
        disease_population=disease_population,
        reference_panels=panels,
        reference_donor_counts={
            name: len(donors) for name, donors in sorted(reference_donors.items())
        },
        warnings=[str(value) for value in warnings_raw],
        source_manifest_sha256=hashlib.sha256(raw_bytes).hexdigest(),
    )


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object.")
    return {str(key): child for key, child in value.items()}


def _optional_object(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("Expected an object.")
    return {str(key): child for key, child in value.items()}


def _text(value: dict[str, Any], field: str) -> str:
    text = str(value.get(field) or "").strip()
    if not text:
        raise ValueError(f"Missing required Open Cohort Factory field: {field}")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("Expected a list.")
    return [str(item) for item in value]
