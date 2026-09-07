"""CELLxGENE Census spatial-transcriptomics connector (optional dependency)."""

from __future__ import annotations

from collections import defaultdict
from importlib import import_module
from typing import Any

from ..models import SpatialTranscriptomicDatasetRecord, SpatialTranscriptomicSummaryRecord

SOURCE = "CZ CELLxGENE Census"
MODALITY = "census_spatial_sequencing"


class CensusSpatialClient:
    def __init__(self, census_version: str = "stable") -> None:
        self.census_version = census_version

    def fetch(
        self, ensembl_ids: list[str], tissue_general: str
    ) -> tuple[list[SpatialTranscriptomicDatasetRecord], list[SpatialTranscriptomicSummaryRecord]]:
        try:
            cellxgene_census = import_module("cellxgene_census")
        except ImportError as error:  # pragma: no cover - environment-dependent guidance
            raise RuntimeError(
                "CELLxGENE support requires: pip install -e '.[spatial]'"
            ) from error

        with cellxgene_census.open_soma(census_version=self.census_version) as census:
            release = _release(census)
            obs_filter = f"tissue_general == '{tissue_general}'"
            obs_columns = [
                "dataset_id", "assay", "cell_type", "disease", "donor_id",
                "development_stage", "sex", "self_reported_ethnicity", "tissue",
                "is_primary_data",
            ]
            data = cellxgene_census.get_anndata(
                census,
                "Homo sapiens",
                X_name="raw",
                obs_value_filter=obs_filter,
                var_value_filter=f"feature_id in {ensembl_ids!r}",
                obs_column_names=obs_columns,
                var_column_names=["soma_joinid", "feature_id", "feature_name"],
                modality=MODALITY,
            )
            dataset_ids = sorted(set(data.obs["dataset_id"].astype(str)))
            dataset_table = census["census_info"]["datasets"].read(
                value_filter=f"dataset_id in {dataset_ids!r}"
            ).concat().to_pandas()
            presence = _feature_presence(census, dataset_table, data.var)
            datasets = _dataset_records(dataset_table, data.obs, release)
            summaries = _expression_records(data, presence, release)
        return datasets, summaries


def _release(census: Any) -> str:
    summary = census["census_info"]["summary"].read().concat().to_pandas()
    values = dict(zip(summary["label"], summary["value"], strict=True))
    return str(values["census_build_date"])


def _feature_presence(census: Any, datasets: Any, variables: Any) -> set[tuple[str, str]]:
    dataset_by_joinid = {
        int(row.soma_joinid): str(row.dataset_id) for row in datasets.itertuples()
    }
    gene_by_joinid = {
        int(row.soma_joinid): str(row.feature_id) for row in variables.itertuples()
    }
    matrix = census[MODALITY]["homo_sapiens"].ms["RNA"][
        "feature_dataset_presence_matrix"
    ]
    table = matrix.read(
        coords=(list(dataset_by_joinid), list(gene_by_joinid))
    ).tables().concat().to_pandas()
    return {
        (dataset_by_joinid[int(row.soma_dim_0)], gene_by_joinid[int(row.soma_dim_1)])
        for row in table.itertuples()
        if row.soma_data
    }


def _dataset_records(
    dataset_table: Any, observations: Any, release: str
) -> list[SpatialTranscriptomicDatasetRecord]:
    results = []
    for row in dataset_table.itertuples():
        subset = observations[observations["dataset_id"].astype(str) == str(row.dataset_id)]
        context_columns = [
            "donor_id", "development_stage", "sex", "self_reported_ethnicity", "disease",
        ]
        contexts = subset[context_columns].astype(str).drop_duplicates().to_dict("records")
        results.append(SpatialTranscriptomicDatasetRecord(
            dataset_id=str(row.dataset_id), source=SOURCE, source_release=release,
            dataset_title=str(row.dataset_title), collection_id=str(row.collection_id),
            collection_name=str(row.collection_name),
            collection_doi=str(row.collection_doi) or None, citation=str(row.citation),
            spot_count=len(subset), assays=sorted(set(subset["assay"].astype(str))),
            donor_contexts=contexts,
        ))
    return results


def _expression_records(
    data: Any, presence: set[tuple[str, str]], release: str
) -> list[SpatialTranscriptomicSummaryRecord]:
    group_columns = [
        "dataset_id", "assay", "tissue", "disease", "donor_id", "development_stage",
        "sex", "self_reported_ethnicity", "cell_type", "is_primary_data",
    ]
    keys: list[tuple[Any, ...]] = []
    totals: dict[tuple[Any, ...], int] = defaultdict(int)
    for row in data.obs[group_columns].itertuples(index=False, name=None):
        key = tuple(row)
        keys.append(key)
        totals[key] += 1

    sums: dict[tuple[tuple[Any, ...], int], float] = defaultdict(float)
    positives: dict[tuple[tuple[Any, ...], int], int] = defaultdict(int)
    matrix = data.X.tocoo()
    for row_index, column_index, value in zip(matrix.row, matrix.col, matrix.data, strict=True):
        if value > 0:
            key = (keys[int(row_index)], int(column_index))
            sums[key] += float(value)
            positives[key] += 1

    variables = list(data.var[["feature_id", "feature_name"]].itertuples(index=False, name=None))
    results = []
    for key, spot_count in totals.items():
        for column_index, (ensembl_id, gene_symbol) in enumerate(variables):
            assayed = (str(key[0]), str(ensembl_id)) in presence
            positive = positives[(key, column_index)] if assayed else 0
            detection_state = "not_assayed" if not assayed else (
                "assayed_detected" if positive else "assayed_not_detected"
            )
            results.append(SpatialTranscriptomicSummaryRecord(
                dataset_id=str(key[0]), source=SOURCE, source_release=release,
                gene_symbol=str(gene_symbol), ensembl_id=str(ensembl_id), assay=str(key[1]),
                tissue=str(key[2]), disease=str(key[3]), donor_id=str(key[4]),
                development_stage=str(key[5]), sex=str(key[6]),
                self_reported_ethnicity=str(key[7]), cell_type=str(key[8]),
                is_primary_data=bool(key[9]), spot_count=spot_count,
                positive_spot_count=positive,
                positive_spot_fraction=positive / spot_count if assayed else 0.0,
                mean_raw_count=sums[(key, column_index)] / spot_count if assayed else 0.0,
                detection_state=detection_state,
                reference_context=_reference_context(str(key[3]), str(key[5])),
                note=("Feature absent from this dataset's matrix; zero is not interpreted as "
                      "non-detection." if not assayed else
                      "Descriptive raw-count summary; no cross-dataset normalization applied."),
            ))
    return results


def _reference_context(disease: str, development_stage: str) -> str:
    if disease != "normal":
        return "disease_tissue"
    if "post-fertilization" in development_stage.casefold():
        return "source_labeled_normal_developmental"
    return "source_labeled_normal_adult_or_unspecified"
