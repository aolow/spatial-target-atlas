from pathlib import Path

import yaml

from .models import AtlasSpec


def load_spec(path: Path) -> AtlasSpec:
    return AtlasSpec.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
