"""Normalized overlay masks aligned to the DBCLS anatomy illustration.

These masks are intentionally approximate spatial guides for expression overlays.
They are not diagnostic segmentations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True)
class Ellipse:
    cx: float
    cy: float
    rx: float
    ry: float


@dataclass(frozen=True)
class Polygon:
    points: tuple[tuple[float, float], ...]


Shape: TypeAlias = Ellipse | Polygon


# Coordinates are normalized to the DBCLS anatomy image placement box.
# V1 starts with the clearest high-value organs and can be refined independently
# without changing rendering code.
REGIONS: dict[str, tuple[Shape, ...]] = {
    "brain": (
        Ellipse(0.50, 0.105, 0.105, 0.055),
    ),
    "lung": (
        Ellipse(0.425, 0.305, 0.085, 0.120),
        Ellipse(0.575, 0.305, 0.085, 0.120),
    ),
    "liver": (
        Polygon(
            (
                (0.48, 0.395),
                (0.68, 0.390),
                (0.715, 0.455),
                (0.62, 0.495),
                (0.47, 0.465),
            )
        ),
    ),
    "kidney": (
        Ellipse(0.405, 0.515, 0.042, 0.062),
        Ellipse(0.595, 0.515, 0.042, 0.062),
    ),
}
