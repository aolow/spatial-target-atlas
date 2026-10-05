import hashlib
import json

import pytest

from spatial_target_atlas.cohort_adapter import load_open_cohort_context


def test_imports_open_cohort_manifest_context(tmp_path) -> None:
    payload = {
        "specification": {
            "name": "Older adults with LUAD",
            "description": "Explicit reference populations",
            "disease_cohort": {
                "projects": ["TCGA-LUAD"],
                "primary_sites": ["Bronchus and lung"],
                "age": {"minimum": 60, "maximum": None},
                "sex_at_birth": [],
                "sample_types": ["Primary Tumor"],
            },
            "reference_panels": [
                {
                    "name": "GTEx lung",
                    "source": "gtex",
                    "tissue": "Lung",
                    "context": "postmortem_reference",
                    "age": {"minimum": 60, "maximum": 70},
                    "resolution": "bulk",
                    "notes": "Postmortem reference",
                }
            ],
        },
        "samples": [
            {"cohort_role": "disease", "cohort_name": "disease", "case_id": "D1"},
            {"cohort_role": "disease", "cohort_name": "disease", "case_id": "D2"},
            {"cohort_role": "reference", "cohort_name": "GTEx lung", "case_id": "R1"},
            {"cohort_role": "reference", "cohort_name": "GTEx lung", "case_id": "R2"},
            {"cohort_role": "reference", "cohort_name": "GTEx lung", "case_id": "R2"},
        ],
        "provenance": [],
        "warnings": ["Age metadata incomplete for one source."],
    }
    path = tmp_path / "manifest.json"
    encoded = json.dumps(payload).encode()
    path.write_bytes(encoded)

    context = load_open_cohort_context(path)

    assert context.project_name == "Older adults with LUAD"
    assert context.disease_population["materialized_donor_count"] == 2
    assert context.disease_population["projects"] == ["TCGA-LUAD"]
    assert context.reference_donor_counts == {"GTEx lung": 2}
    assert context.reference_panels[0].context == "postmortem_reference"
    assert context.source_manifest_sha256 == hashlib.sha256(encoded).hexdigest()


def test_rejects_non_manifest_shape(tmp_path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"samples": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="specification"):
        load_open_cohort_context(path)
