import warnings

from spatial_target_atlas.models import ModelDerivedEvidenceRecord


def test_model_derived_record_emits_no_protected_namespace_warning() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        record = ModelDerivedEvidenceRecord(
            model_name="PINNACLE",
            model_version="published",
            evidence_kind="contextual_representation_available",
            gene_symbol="EPCAM",
            ensembl_id="ENSG00000119888",
            context_type="cell_type",
            context="epithelial cell",
            source_url="https://example.test/model",
            citation_url="https://example.test/paper",
            note="Representation availability only.",
        )

    assert record.model_name == "PINNACLE"
    assert not [
        warning
        for warning in caught
        if "protected namespace" in str(warning.message).casefold()
    ]
