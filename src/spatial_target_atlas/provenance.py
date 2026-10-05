"""Build-level provenance manifest generation."""

from __future__ import annotations

import hashlib
import subprocess
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .models import ProteinEvidenceRecord


def build_manifest(
    spec_path: Path,
    records: list[ProteinEvidenceRecord],
    artifact_paths: list[Path],
    extra_sources: list[dict[str, Any]] | None = None,
    source_failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source_details: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"retrieved_at": set(), "source_urls": set(), "source_payload_sha256": set()}
    )
    counts = Counter((record.source, record.source_release) for record in records)
    for record in records:
        details = source_details[(record.source, record.source_release)]
        if record.retrieved_at:
            details["retrieved_at"].add(record.retrieved_at)
        details["source_urls"].add(record.source_url)
        details["source_urls"].update(record.supporting_source_urls)
        details["source_payload_sha256"].update(record.source_payload_sha256)
    sources = []
    for key in sorted(source_details):
        details = source_details[key]
        sources.append(
            {
                "source": key[0],
                "release": key[1],
                "record_count": counts[key],
                "retrieved_at": sorted(details["retrieved_at"]),
                "source_urls": sorted(details["source_urls"]),
                "source_payload_sha256": sorted(details["source_payload_sha256"]),
            }
        )
    sources.extend(extra_sources or [])
    return {
        "manifest_schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "software": {
            "name": "spatial-target-atlas",
            "version": __version__,
            "git_commit": _git_commit(),
            "git_dirty": _git_dirty(),
        },
        "input_spec": {"path": str(spec_path), "sha256": _sha256(spec_path)},
        "source_failures": source_failures or [],
        "sources": sorted(sources, key=lambda source: (source["source"], source["release"])),
        "artifacts": [
            {"path": path.name, "sha256": _sha256(path), "bytes": path.stat().st_size}
            for path in artifact_paths
        ],
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


def _git_dirty() -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    return bool(result.stdout.strip())
