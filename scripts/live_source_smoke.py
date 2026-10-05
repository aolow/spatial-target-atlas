"""Small live-source compatibility smoke test for scheduled/manual GitHub Actions."""

from __future__ import annotations

import json

import httpx

from spatial_target_atlas.identifiers import TargetResolver
from spatial_target_atlas.sources.hpa import HPAClient
from spatial_target_atlas.sources.hubmap import HuBMAPClient
from spatial_target_atlas.sources.pdc import API_URL as PDC_API
from spatial_target_atlas.sources.proteomicsdb import ProteomicsDBClient


def main() -> None:
    hpa = HPAClient(release="25.1")
    identity = TargetResolver(hpa=hpa).resolve(["EPCAM"])[0]
    if identity.gene_symbol != "EPCAM" or identity.uniprot_id != "P16422":
        raise RuntimeError("EPCAM identity resolution changed unexpectedly.")

    proteomics = ProteomicsDBClient().fetch(
        identity.gene_symbol,
        identity.ensembl_id,
        identity.uniprot_id,
        [],
    )
    if not proteomics:
        raise RuntimeError("ProteomicsDB returned no EPCAM tissue records.")

    hubmap = HuBMAPClient().fetch_spatial_registry(["LL"])
    if not hubmap:
        raise RuntimeError("HuBMAP returned no published left-lung spatial datasets.")

    pdc_response = httpx.post(
        PDC_API,
        json={
            "query": (
                "query($id:String!){study(pdc_study_id:$id,acceptDUA:true)"
                "{pdc_study_id study_name}}"
            ),
            "variables": {"id": "PDC000153"},
        },
        timeout=30,
    )
    pdc_response.raise_for_status()
    payload = pdc_response.json()
    study = (payload.get("data") or {}).get("study") or []
    if not study:
        raise RuntimeError("PDC could not resolve validation study PDC000153.")

    print(json.dumps({
        "status": "ok",
        "identity": {
            "gene_symbol": identity.gene_symbol,
            "ensembl_id": identity.ensembl_id,
            "uniprot_id": identity.uniprot_id,
        },
        "proteomicsdb_tissue_records": len(proteomics),
        "hubmap_left_lung_spatial_datasets": len(hubmap),
        "pdc_validation_study": study[0].get("pdc_study_id"),
    }, indent=2))


if __name__ == "__main__":
    main()
