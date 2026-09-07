from types import SimpleNamespace

from spatial_target_atlas.sources.cellxgene import _expression_records


class _Frame:
    def __init__(self, rows: list[tuple[object, ...]], columns: list[str]) -> None:
        self.rows = rows
        self.columns = columns

    def __getitem__(self, columns: list[str]) -> "_Frame":
        indices = [self.columns.index(column) for column in columns]
        return _Frame([tuple(row[index] for index in indices) for row in self.rows], columns)

    def itertuples(self, index: bool = False, name: object = None):  # noqa: ANN201
        return iter(self.rows)


class _Sparse:
    def tocoo(self) -> SimpleNamespace:
        return SimpleNamespace(row=[0, 1], col=[0, 0], data=[2, 1])


def test_expression_summary_distinguishes_absent_feature_from_zero() -> None:
    columns = [
        "dataset_id", "assay", "tissue", "disease", "donor_id", "development_stage",
        "sex", "self_reported_ethnicity", "cell_type", "is_primary_data",
    ]
    observations = _Frame([
        ("dataset-1", "Visium", "lung", "normal", "D1", "59-year-old stage",
         "female", "unknown", "spot", True),
        ("dataset-1", "Visium", "lung", "normal", "D1", "59-year-old stage",
         "female", "unknown", "spot", True),
    ], columns)
    variables = _Frame([
        ("ENSG1", "GENE1"), ("ENSG2", "GENE2"),
    ], ["feature_id", "feature_name"])
    data = SimpleNamespace(obs=observations, var=variables, X=_Sparse())

    records = _expression_records(data, {("dataset-1", "ENSG1")}, "2025-11-08")

    assert records[0].detection_state == "assayed_detected"
    assert records[0].positive_spot_fraction == 1
    assert records[0].mean_raw_count == 1.5
    assert records[0].reference_context == "source_labeled_normal_adult_or_unspecified"
    assert records[1].detection_state == "not_assayed"
    assert "zero is not interpreted" in records[1].note
